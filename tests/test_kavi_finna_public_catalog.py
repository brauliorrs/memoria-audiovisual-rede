"""Published metadata index gate: only approved, hash-verified record links."""
from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.kavi_finna_public_catalog import (
    CATALOG_FILENAME, MANIFEST_FILENAME,
    PublicationRejected, VERSION, load_published_kavi_rows,
)

ID = "kavi.elonet_elokuva_157199"
URL = f"https://www.finna.fi/Record/{ID}"
SHA = "a" * 64


def example_row():
    return {
        "corpus": "fiaf-kavi", "source_record_id": ID, "video_title": "Film",
        "video_link": URL, "source_record_url": URL,
        "metadata_provider": "0/KAVI/",
        "metadata_license": "CC0-1.0_API_metadata_only",
        "media_rights_status": "not_verified",
        "custody_status": "not_established",
        "film_semantics": "film_candidate",
        "scope_sha256": SHA,
        "link_status": "item_link_verified_by_source",
        "record_review_status": "unreviewed",
        "genres": "documentary", "subjects": "history", "year": "1936",
    }


def write_published(root, row=None, manifest_changes=None):
    row = example_row() if row is None else row
    filename = Path(root) / CATALOG_FILENAME
    with filename.open("w", newline="", encoding="utf-8") as handle:
        out = csv.DictWriter(handle, fieldnames=list(row))
        out.writeheader()
        out.writerow(row)
    manifest = {
        "schema_version": VERSION,
        "unit_id": "fiaf-kavi",
        "status": "published_partial_metadata",
        "coverage_status": "partial",
        "metadata_license": "CC0-1.0_API_metadata_only",
        "metadata_publication_approved": True,
        "corpus_activation": False,
        "media_downloaded": False,
        "viewing_at_origin_only": True,
        "catalog_sha256": hashlib.sha256(filename.read_bytes()).hexdigest(),
        "source_scope_sha256": SHA,
        "expected_total_api_index": 138399,
        "record_count": 1,
        "item_links_present": 1,
        "source_run_url": "https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/39346643735",
        "observed_on": "2026-10-19",
    }
    manifest.update(manifest_changes or {})
    (Path(root) / MANIFEST_FILENAME).write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    return filename


class KaviPublicationTests(unittest.TestCase):
    def test_absent_index_returns_empty_without_autopublication(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(load_published_kavi_rows(folder), ([], {}))

    def test_audited_metadata_record_is_visible_but_no_media_activated(self):
        with tempfile.TemporaryDirectory() as folder:
            write_published(folder)
            rows, meta = load_published_kavi_rows(folder)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["video_link"], URL)
            self.assertFalse(meta["corpus_activation"])
            self.assertTrue(meta["metadata_publication_approved"])

    def test_reject_bytes_tampering(self):
        with tempfile.TemporaryDirectory() as folder:
            p = write_published(folder)
            p.write_bytes(p.read_bytes() + b"x")
            with self.assertRaises(PublicationRejected):
                load_published_kavi_rows(folder)

    def test_never_publish_without_explicit_metadata_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            write_published(folder, manifest_changes={
                "metadata_publication_approved": False,
            })
            with self.assertRaises(PublicationRejected):
                load_published_kavi_rows(folder)

    def test_no_corpus_activation_or_media_download(self):
        for key, val in (("corpus_activation", True), ("media_downloaded", True)):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as folder:
                write_published(folder, manifest_changes={key: val})
                with self.assertRaises(PublicationRejected):
                    load_published_kavi_rows(folder)

    def test_cannot_publish_a_direct_media_or_forged_item_link(self):
        for url in (
            "https://media.example.fi/movie.mp4",
            "https://www.finna.fi/Record/different-id",
            "https://www.finna.fi/Record/kavi.elonet_elokuva_157199?download=1",
        ):
            with self.subTest(url=url), tempfile.TemporaryDirectory() as folder:
                row = example_row()
                row["video_link"] = url
                row["source_record_url"] = url
                write_published(folder, row=row)
                with self.assertRaises(PublicationRejected):
                    load_published_kavi_rows(folder)

    def test_no_false_rights_or_custody(self):
        for key,val in (("media_rights_status","public_domain"),
                        ("custody_status","Kuvi confirmed"),
                        ("record_review_status","reviewed")):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as folder:
                row=example_row();row[key]=val
                write_published(folder,row=row)
                with self.assertRaises(PublicationRejected):
                    load_published_kavi_rows(folder)

    def test_missing_manifest_never_publishes(self):
        with tempfile.TemporaryDirectory() as folder:
            write_published(folder)
            (Path(folder) / MANIFEST_FILENAME).unlink()
            with self.assertRaises(PublicationRejected):
                load_published_kavi_rows(folder)

    def test_reject_different_provider_and_duplicate_count(self):
        with tempfile.TemporaryDirectory() as folder:
            row=example_row();row["metadata_provider"]="unrelated"
            write_published(folder,row=row)
            with self.assertRaises(PublicationRejected):
                load_published_kavi_rows(folder)
        with tempfile.TemporaryDirectory() as folder:
            write_published(folder,manifest_changes={"record_count": 2})
            with self.assertRaises(PublicationRejected):
                load_published_kavi_rows(folder)


if __name__ == "__main__":
    unittest.main()
