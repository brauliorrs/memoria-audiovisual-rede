"""Tests for three separate one-page staging executions, without network."""
from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from memoria_audiovisual.metadata_staging import MetadataPage, StageRejected
from scripts.probe_kavi_finna_three_batch_resume import main, verify_three_batches

NOW = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)
EXPIRY = "2030-01-01T00:00:00Z"


def film(identifier):
    return {
        "id": identifier, "title": "Film example",
        "formats": [{"value": "0/Video/"}],
        "provider_index_code": "0/KAVI/",
        "custody_status": "not_established",
        "media_rights_status": "not_verified",
        "media_downloaded": False,
        "film_semantics": (
            "film_candidate" if identifier.startswith("kavi.elonet_elokuva_")
            else "unverified_audiovisual_record"
        ),
    }


def page(ids, next_token, total=5, expiry=EXPIRY):
    records = [film(i) for i in ids]
    return MetadataPage(
        tuple(records), total, next_token,
        {"status": "OK", "resultCount": total,
         "records": [{"id": item["id"], "title": item["title"]} for item in records],
         "resumptionToken": (
             {"token": next_token, "expires": expiry}
             if next_token is not None else None
         )},
    )


class FakeSource:
    def __init__(self, *, expiry=EXPIRY, drift_on_call=None):
        self.scope = {
            "building_code": "0/KAVI/", "format_code": "0/Video/",
            "institution_code": "fiaf-kavi",
            "schema_version": "1.0.0",
            "adapter_version": "kavi-finna-adapter-1.0.0",
            "evidence_sha256": "a" * 64,
        }
        self.responses = {
            None: page(["kavi.elonet_elokuva_01", "kavi.elonet_elokuva_02"], "opaque-1", expiry=expiry),
            "opaque-1": page(["kavi.elonet_elokuva_03", "kavi.elonet_elokuva_04"], "opaque-2", expiry=expiry),
            "opaque-2": page(["other-video-05"], None, expiry=expiry),
        }
        self.preflight_count = 0
        self.requests = []
        self.drift_on_call = drift_on_call

    def preflight(self):
        self.preflight_count += 1
        return 6 if self.preflight_count == self.drift_on_call else 5

    def fetch_page(self, cursor):
        self.requests.append(cursor)
        return self.responses[cursor]


class ThreeBatchProbeTests(unittest.TestCase):
    def probe(self, source, folder, sleeps=None):
        if sleeps is None:
            sleeps = []
        result = verify_three_batches(
            source, folder,
            now_fn=lambda: NOW,
            sleep_fn=sleeps.append,
        )
        return result, sleeps

    def test_three_resumed_calls_and_local_audits(self):
        source = FakeSource()
        with tempfile.TemporaryDirectory() as folder:
            result, sleeps = self.probe(source, folder)
            self.assertEqual(source.requests, [None, "opaque-1", "opaque-2"])
            self.assertEqual(source.preflight_count, 3)
            self.assertEqual(sleeps, [1.0, 1.0])
            self.assertEqual(
                [x["record_count"] for x in result["batch_summaries"]],
                [2, 4, 5],
            )
            self.assertEqual(
                [x["status"] for x in result["batch_summaries"]],
                ["partial", "partial", "complete"],
            )
            self.assertEqual(result["verified_page_count"], 3)
            self.assertEqual(result["final_record_count"], 5)
            self.assertEqual(result["film_id_candidates"], 4)
            self.assertEqual(result["other_video_records"], 1)
            self.assertEqual(result["video_format_unconfirmed_records"], 0)
            self.assertTrue(result["resumption_verified_across_batches"])
            self.assertFalse(result["api_snapshot_freshness_verified"])
            self.assertFalse(result["promotion_authorized"])
            self.assertFalse(result["media_downloaded"])
            public = json.dumps(result, sort_keys=True)
            self.assertNotIn("opaque-1", public)
            self.assertNotIn("opaque-2", public)
            self.assertNotIn("kavi.elonet_elokuva_01", public)
            self.assertFalse((Path(folder) / "run.lock").exists())

    def test_expired_next_cursor_causes_hold_without_second_request(self):
        source = FakeSource(expiry="2020-01-01T00:00:00Z")
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(
                StageRejected, "resume_cursor_expired_or_too_close"
            ):
                self.probe(source, folder)
            self.assertEqual(source.requests, [None])
            self.assertEqual(source.preflight_count, 1)

    def test_count_drift_aborts_without_fetching_second_page(self):
        source = FakeSource(drift_on_call=2)
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(StageRejected, "checkpoint_total_drift"):
                self.probe(source, folder)
            self.assertEqual(source.requests, [None])
            self.assertEqual(source.preflight_count, 2)

    def test_repeated_ids_across_pages_rejected(self):
        source = FakeSource()
        source.responses["opaque-1"] = page(
            ["kavi.elonet_elokuva_01", "kavi.elonet_elokuva_04"],
            "opaque-2",
        )
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(StageRejected, "duplicate_ids_across_pages"):
                self.probe(source, folder)
            self.assertEqual(source.requests, [None, "opaque-1"])

    def test_dry_run_does_not_fetch(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["--evidence-sha256", "a" * 64])
        self.assertEqual(code, 0)
        self.assertIn("DRY RUN", out.getvalue())


if __name__ == "__main__":
    unittest.main()
