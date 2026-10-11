"""Finna adapter contract: sourced facets, token semantics and metadata isolation."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from memoria_audiovisual.kavi_elonet_probe import API_ROOT, FACET_QUERY
from memoria_audiovisual.kavi_finna_adapter import (
    FORMAT_FACET_URL, FinnaMetadataSource, FinnaScope,
)
from memoria_audiovisual.metadata_staging import StageRejected, stage_metadata


class Response:
    def __init__(self, data=None, *, status=200, mime="application/json"):
        self.status_code = status
        self.text = json.dumps(data) if data is not None else "Not found"
        self.headers = {"content-type": mime}
        self.encoding = "utf-8"

    def iter_content(self, limit):
        raw = self.text.encode("utf-8")
        for i in range(0, len(raw), limit):
            yield raw[i:i+limit]

    def close(self):
        pass


class Session:
    def __init__(self, routes):
        self.routes = routes
        self.urls = []

    def get(self, url, **_kwargs):
        self.urls.append(url)
        return self.routes.get(url, Response(status=404))


def scope():
    return FinnaScope(
        building_code="0/KAVI/",
        format_code="0/Video/",
        evidence_sha256="4" * 64,
    )


def film(identifier):
    return {
        "id": identifier,
        "title": "Example Film",
        "formats": [{"value": "0/Video/", "translated": "Video"}],
        "institutions": [{"value": "KAVI"}],
        "onlineUrls": [{"url": "https://elonet.finna.fi/Record/example"}],
    }


def routes():
    r = {
        "https://api.finna.fi/robots.txt": Response(
            data=None, status=200, mime="text/plain",
        ),
    }
    r["https://api.finna.fi/robots.txt"].text = "User-agent: *\nAllow: /\n"
    r[FACET_QUERY] = Response({
        "status": "OK", "resultCount": 200000,
        "facets": {"building": [
            {"value": "0/KAVI/", "translated": "Taide- ja kulttuurivirasto",
             "count": 3},
        ]}, "records": [],
    })
    r[FORMAT_FACET_URL] = Response({
        "status": "OK", "resultCount": 200000,
        "facets": {"format": [
            {"value": "0/Video/", "translated": "Video", "count": 3},
        ]}, "records": [],
    })
    source = FinnaMetadataSource(Session(r), scope())
    count_url = source._verified_query(count_only=True)
    first_url = source._verified_query()
    continuation = source._verified_query(token="opaque-next")
    r[count_url] = Response({
        "status": "OK", "resultCount": 3, "records": [],
    })
    r[first_url] = Response({
        "status": "OK", "resultCount": 3,
        "records": [film("kavi.elonet_elokuva_1"), film("kavi.elonet_elokuva_2")],
        "resumptionToken": "opaque-next",
    })
    r[continuation] = Response({
        "status": "OK", "resultCount": 3,
        "records": [film("kavi.elonet_elokuva_3")],
    })
    return r


class FinnaAdapterTests(unittest.TestCase):
    def test_finna_stages_metadata_only_with_documented_token_semantics(self):
        s = Session(routes())
        adapter = FinnaMetadataSource(s, scope())
        with tempfile.TemporaryDirectory() as root:
            first = stage_metadata(adapter, root, max_pages=1)
            self.assertEqual(first["status"], "partial")
            final = stage_metadata(adapter, root, max_pages=1, resume=True)
            self.assertEqual(final["status"], "complete")
            self.assertEqual(final["record_count"], 3)
            first_url = adapter._verified_query()
            self.assertEqual(parse_qs(urlparse(first_url).query)["resumptionToken"], ["*"])
            self.assertEqual(
                len(parse_qs(urlparse(first_url).query)["filter[]"]), 2
            )
            self.assertNotIn("limit", parse_qs(urlparse(first_url).query))
            next_url = adapter._verified_query(token="opaque-next")
            self.assertEqual(
                parse_qs(urlparse(next_url).query), {"resumptionToken": ["opaque-next"]}
            )
            self.assertEqual(s.urls.count("https://api.finna.fi/robots.txt"), 1)
            artifacts = list((Path(root) / "raw").rglob("*.json"))
            self.assertEqual(len(artifacts), 2)
            evidence = json.loads(artifacts[0].read_text())
            row = evidence["page"]["records"][0]
            self.assertEqual(row["custody_status"], "not_established")
            self.assertEqual(row["media_rights_status"], "not_verified")
            self.assertFalse(row["media_downloaded"])
            self.assertNotIn("onlineUrls", row)
            self.assertTrue(row["online_url_metadata_present"])

    def test_scope_from_preregistration_is_required(self):
        with self.assertRaisesRegex(ValueError, "unapproved_finna_scope"):
            FinnaScope("0/OTHER/", "0/Video/", "4" * 64)
        with self.assertRaisesRegex(ValueError, "scope_evidence"):
            FinnaScope("0/KAVI/", "0/Video/", "not-a-digest")

    def test_robots_disallow_aborts_before_api_facets(self):
        r = routes()
        r["https://api.finna.fi/robots.txt"].text = (
            "User-agent: *\nDisallow: /v1/\n"
        )
        s = Session(r)
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(StageRejected, "robots_unverifiable"):
                stage_metadata(FinnaMetadataSource(s, scope()), root)
        self.assertNotIn(FACET_QUERY, s.urls)

    def test_building_drift_blocks_batch(self):
        r = routes()
        r[FACET_QUERY] = Response({
            "status": "OK", "resultCount": 3,
            "facets": {"building": [
                {"value": "0/KUVI/", "translated": "Kuvi", "count": 3},
            ]}, "records": [],
        })
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(StageRejected, "facet_drift_or_ambiguity"):
                stage_metadata(FinnaMetadataSource(Session(r), scope()), root)

    def test_multiple_provider_facets_fail_closed(self):
        r = routes()
        r[FACET_QUERY] = Response({
            "status": "OK", "resultCount": 3,
            "facets": {"building": [
                {"value": "0/KAVI/", "translated": "KAVI", "count": 2},
                {"value": "0/KUVI/", "translated": "Kuvi", "count": 1},
            ]}, "records": [],
        })
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(StageRejected, "facet_drift_or_ambiguity"):
                stage_metadata(FinnaMetadataSource(Session(r), scope()), root)

    def test_format_drift_blocks_batch(self):
        r = routes()
        r[FORMAT_FACET_URL] = Response({
            "status": "OK", "resultCount": 3,
            "facets": {"format": [
                {"value": "0/Book/", "translated": "Book", "count": 3},
            ]}, "records": [],
        })
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(StageRejected, "video_format_facet_drift"):
                stage_metadata(FinnaMetadataSource(Session(r), scope()), root)

    def test_duplicate_records_or_missing_title_block_batch(self):
        for records, expected in [
            ([film("a"), film("a")], "duplicate_ids_within_page"),
            ([{"id": "abc", "title": ""}], "record_without_title"),
        ]:
            with self.subTest(expected=expected):
                r = routes()
                probe = FinnaMetadataSource(Session(r), scope())
                r[probe._verified_query()] = Response({
                    "status": "OK", "resultCount": 2,
                    "records": records, "resumptionToken": None,
                })
                r[probe._verified_query(count_only=True)] = Response({
                    "status": "OK", "resultCount": 2, "records": [],
                })
                with tempfile.TemporaryDirectory() as root:
                    with self.assertRaisesRegex(StageRejected, expected):
                        stage_metadata(probe, root)

    def test_record_without_film_id_is_staged_but_not_falsely_film(self):
        r = routes()
        sample = film("kavi_other_video_42")
        probe = FinnaMetadataSource(Session(r), scope())
        r[probe._verified_query(count_only=True)] = Response({
            "status": "OK", "resultCount": 1, "records": [],
        })
        r[probe._verified_query()] = Response({
            "status": "OK", "resultCount": 1, "records": [sample],
        })
        with tempfile.TemporaryDirectory() as root:
            report = stage_metadata(probe, root)
            self.assertEqual(report["status"], "complete")
            artifact = next((Path(root) / "raw").rglob("*.json"))
            data = json.loads(artifact.read_text())
            self.assertEqual(
                data["page"]["records"][0]["film_semantics"],
                "unverified_audiovisual_record",
            )


if __name__ == "__main__":
    unittest.main()
