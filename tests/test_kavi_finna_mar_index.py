"""MAR link-only Finna projection: deterministic offline contract and redaction."""
from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.kavi_finna_mar_index import (
    _safe_record_link, project_record, project_staged_catalog,
)
from memoria_audiovisual.kavi_finna_adapter import FinnaScope
from memoria_audiovisual.metadata_staging import (
    MetadataPage, StageRejected, stage_metadata,
)

EVIDENCE = "a" * 64
SCOPE = FinnaScope("0/KAVI/", "0/Video/", EVIDENCE).to_dict()
FILM = "kavi.elonet_elokuva_157199"
OTHER = "kavi.elonet_elokuva_117938"
VIDEO_FORMAT = [{"value": "0/Video/", "translated": "Video"}]
MEDIA_ADDRESS = "https://media.example.fi/film.mp4"


def record(identity=FILM, *, record_page=True):
    row = {
        "id": identity,
        "title": "An audiovisual film",
        "year": "1936",
        "recordPage": f"/Record/{identity}" if record_page else None,
        "formats": VIDEO_FORMAT,
        "primaryAuthors": ["Director"],
        "subjects": ["History", {"value": "Cinema"}],
        "genres": ["Documentary"],
        "languages": ["fi"],
        "summary": "Source-provided metadata",
        "onlineUrls": [{"url": MEDIA_ADDRESS}],
        "images": ["/Cover/Show?id=unsafe"],
        "accessRestrictions": [],
    }
    return row


class Source:
    scope = SCOPE

    def preflight(self):
        return 138393

    def fetch_page(self, token):
        if token is not None:
            raise AssertionError("Only the first page should be staged")
        records = [record(), record(OTHER, record_page=False)]
        normalized = [{
            "id": row["id"],
            "title": row["title"],
            "formats": row["formats"],
            "institutions": [],
            "online_url_metadata_present": True,
            "film_semantics": "film_candidate",
            "provider_index_code": "0/KAVI/",
            "custody_status": "not_established",
            "media_rights_status": "not_verified",
            "media_downloaded": False,
        } for row in records]
        return MetadataPage(
            tuple(normalized), 138393, "opaque-private-token",
            {"resultCount": 138393, "records": records, "resumptionToken": {
                "token": "opaque-private-token", "expires": "2030-01-01 00:00:00",
            }},
        )


class KaviMarIndexTests(unittest.TestCase):
    def test_project_record_keeps_mar_descriptive_columns(self):
        item = project_record(record(), scope_sha256=EVIDENCE)
        self.assertEqual(item["source_record_id"], FILM)
        self.assertEqual(item["video_title"], "An audiovisual film")
        self.assertEqual(item["video_published_at"], "1936")
        self.assertIn("History", item["video_subject"])
        self.assertEqual(item["video_link"], f"https://www.finna.fi/Record/{FILM}")
        self.assertEqual(item["link_status"], "item_link_verified_by_source")
        self.assertEqual(item["film_semantics"], "film_candidate")
        self.assertEqual(item["custody_status"], "not_established")
        self.assertEqual(item["media_access_status"], "unverified")
        self.assertEqual(item["metadata_provider"], "0/KAVI/")
        self.assertTrue(item["online_url_metadata_present"])
        self.assertNotIn("onlineUrls", item)
        self.assertNotIn("images", item)
        self.assertNotIn(MEDIA_ADDRESS, json.dumps(item))
        self.assertNotIn("opaque", json.dumps(item))

    def test_link_missing_not_guessed_from_identifier(self):
        item = project_record(record(record_page=False), scope_sha256=EVIDENCE)
        self.assertEqual(item["video_link"], "")
        self.assertEqual(item["link_status"], "missing_source_item_link")
        self.assertEqual(item["source_record_id"], FILM)

    def test_explicit_verified_website_item_link_can_prioritize_origin(self):
        approved = f"https://elonet.finna.fi/Record/{FILM}"
        item = project_record(
            record(), scope_sha256=EVIDENCE,
            verified_origin_urls={FILM: approved},
        )
        self.assertEqual(item["video_link"], approved)

    def test_bad_override_refused_not_silently_normalized(self):
        with self.assertRaises(StageRejected):
            project_record(record(), scope_sha256=EVIDENCE,
                           verified_origin_urls={FILM: MEDIA_ADDRESS})

    def test_suspicious_or_mismatched_records_never_linked(self):
        for bad in (
            "https://media.example.fi/film.mp4",
            "https://api.finna.fi/v1/record?id=abc",
            "https://elonet.finna.fi/Record/other-id",
            "/Record/another-id", "javascript:alert(1)",
            "https://www.finna.fi/Record/kavi.elonet_elokuva_157199?download=1",
            "https://www.finna.fi/Record/kavi.elonet_elokuva_157199/extra",
            "//elonet.finna.fi/Record/kavi.elonet_elokuva_157199",
        ):
            with self.subTest(bad=bad):
                self.assertIsNone(_safe_record_link(bad, FILM))

    def test_non_video_rejected(self):
        obj = record()
        obj["formats"] = [{"value": "0/Book/"}]
        with self.assertRaises(StageRejected):
            project_record(obj, scope_sha256=EVIDENCE)

    def test_stage_projection_offline_without_promoting_media(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            stage = root / "stage"
            output = root / "review"
            original = stage_metadata(Source(), stage, max_pages=1)
            self.assertEqual(original["status"], "partial")
            summary = project_staged_catalog(
                stage, output, evidence_sha256=EVIDENCE,
                expected_total=138393,
            )
            self.assertEqual(summary["record_count"], 2)
            self.assertEqual(summary["item_links_present"], 1)
            self.assertEqual(summary["item_links_missing"], 1)
            self.assertEqual(summary["coverage_status"], "partial")
            self.assertFalse(summary["corpus_active"])
            self.assertFalse(summary["promotion_authorized"])
            self.assertFalse(summary["media_downloaded"])
            self.assertTrue(summary["viewing_at_origin_only"])

            items = json.loads(
                (output / "kavi_mar_metadata_links_PREVIEW.json").read_text()
            )
            self.assertEqual([x["source_record_id"] for x in items],
                             [FILM, OTHER])
            self.assertEqual(items[1]["video_link"], "")
            csv_path = output / "kavi_mar_metadata_links_PREVIEW.csv"
            with csv_path.open(newline="", encoding="utf-8") as handle:
                csv_items = list(csv.DictReader(handle))
            self.assertEqual(len(csv_items), 2)
            for exported in output.glob("*"):
                body = exported.read_text(encoding="utf-8")
                self.assertNotIn(MEDIA_ADDRESS, body)
                self.assertNotIn("opaque-private-token", body)
                self.assertNotIn("/Cover/Show", body)

    def test_tampering_with_staged_page_blocks_export(self):
        with tempfile.TemporaryDirectory() as folder:
            stage, output = Path(folder) / "stage", Path(folder) / "review"
            manifest = stage_metadata(Source(), stage, max_pages=1)
            sha = manifest["pages"][0]["artifact_sha256"]
            raw = stage / "raw" / sha[:2] / f"{sha}.json"
            raw.write_text('{"tampered":true}')
            with self.assertRaises(StageRejected):
                project_staged_catalog(
                    stage, output, evidence_sha256=EVIDENCE,
                    expected_total=138393,
                )
            self.assertFalse(output.exists())

    def test_refuse_reuse_of_output_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            stage, out = Path(folder) / "stage", Path(folder) / "review"
            stage_metadata(Source(), stage, max_pages=1)
            out.mkdir()
            (out / "old.txt").write_text("existing")
            with self.assertRaises(StageRejected):
                project_staged_catalog(stage, out, evidence_sha256=EVIDENCE,
                                       expected_total=138393)


if __name__ == "__main__":
    unittest.main()
