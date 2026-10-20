"""Network-free tests for bounded, audited KAVI/Finna staging resumes."""
from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from memoria_audiovisual.kavi_finna_adapter import VERSION as KAVI_FINNA_ADAPTER_VERSION
from memoria_audiovisual.metadata_staging import MetadataPage, StageRejected
from scripts.kavi_finna_batch_gate import (
    execute_verified_batch, verify_resume_expiration,
)
from scripts.run_kavi_finna_metadata_staging import main

EVIDENCE = "a" * 64
NOW = datetime(2026, 10, 12, 8, 0, tzinfo=timezone.utc)
EXPIRY = "2030-01-01T00:00:00Z"


def normalized(record_id):
    return {
        "id": record_id, "title": "Example",
        "formats": [{"value": "0/Video/"}],
        "provider_index_code": "0/KAVI/",
        "custody_status": "not_established",
        "media_rights_status": "not_verified",
        "media_downloaded": False,
        "film_semantics": (
            "film_candidate" if record_id.startswith("kavi.elonet_elokuva_")
            else "unverified_audiovisual_record"
        ),
    }


def sample_page(records, token=None, *, expires=EXPIRY, source_token=None):
    payload = None if token is None else {
        "token": token if source_token is None else source_token,
        "expires": expires,
    }
    return MetadataPage(
        tuple(records), 3, token,
        {"status": "OK", "resultCount": 3,
         "records": [
             {"id": r["id"], "title": r["title"]} for r in records
         ],
         "resumptionToken": payload},
    )


class FakeSource:
    def __init__(self, *, expires=EXPIRY, source_token=None):
        self.scope = {
            "building_code": "0/KAVI/",
            "format_code": "0/Video/",
            "evidence_sha256": EVIDENCE,
            "institution_code": "fiaf-kavi",
            "schema_version": "1.0.0",
            "adapter_version": KAVI_FINNA_ADAPTER_VERSION,
        }
        self.pages = {
            None: sample_page([
                normalized("kavi.elonet_elokuva_1"),
                normalized("kavi.elonet_elokuva_2"),
            ], "secret-next-token", expires=expires, source_token=source_token),
            "secret-next-token": sample_page([normalized("other-video-3")]),
        }
        self.fetches = []
        self.preflights = 0
        self.total = 3

    def preflight(self):
        self.preflights += 1
        return self.total

    def fetch_page(self, token):
        self.fetches.append(token)
        return self.pages[token]


def run(source, directory, **kwargs):
    return execute_verified_batch(
        source, directory, now_fn=lambda: NOW, **kwargs,
    )


class FinnaBoundedBatchTests(unittest.TestCase):
    def test_bounded_resume_runs_audit_and_throttles_inter_invocation(self):
        source = FakeSource()
        delays = []
        with tempfile.TemporaryDirectory() as folder:
            first = run(source, folder, max_pages=1, sleep_fn=delays.append)
            self.assertEqual(first["status"], "partial")
            self.assertTrue(first["offline_integrity_verified"])
            self.assertFalse(first["api_snapshot_freshness_verified"])
            self.assertEqual(first["record_count"], 2)
            self.assertEqual(delays, [])
            self.assertFalse(first["promotion_authorized"])
            self.assertFalse(first["media_downloaded"])
            second = run(
                source, folder, resume=True, expected_total=3,
                max_pages=1, delay_seconds=1.5, sleep_fn=delays.append,
            )
            self.assertEqual(delays, [1.5])
            self.assertEqual(source.fetches, [None, "secret-next-token"])
            self.assertEqual(second["status"], "complete")
            self.assertEqual(second["record_count"], 3)
            self.assertEqual(second["provenance_audit"]["film_id_candidates"], 2)
            self.assertEqual(second["provenance_audit"]["other_video_records"], 1)
            self.assertNotIn("secret-next-token", json.dumps(second))
            # Complete batches are idempotent; no API I/O required to re-audit.
            requests_before = source.preflights
            repeated = run(
                source, folder, resume=True,
                expected_total=3, sleep_fn=delays.append,
            )
            self.assertEqual(repeated["status"], "complete")
            self.assertEqual(source.preflights, requests_before)
            self.assertEqual(delays, [1.5])

    def test_expired_cursor_aborts_before_live_preflight(self):
        source = FakeSource(expires="2020-01-01T00:00:00Z")
        with tempfile.TemporaryDirectory() as folder:
            run(source, folder)
            self.assertEqual(source.preflights, 1)
            with self.assertRaisesRegex(
                StageRejected, "resume_cursor_expired_or_too_close"
            ):
                run(source, folder, resume=True, expected_total=3)
            self.assertEqual(source.preflights, 1)
            self.assertEqual(source.fetches, [None])

    def test_too_close_to_expiry_is_rejected(self):
        source = FakeSource(expires="2026-10-12T08:00:29Z")
        with tempfile.TemporaryDirectory() as folder:
            run(source, folder)
            with self.assertRaisesRegex(StageRejected, "expired_or_too_close"):
                run(source, folder, resume=True, expected_total=3)

    def test_missing_invalid_or_naive_expiry_is_fail_closed(self):
        for expiry, expected in [
            (None, "expiration_missing"),
            ("invalid", "expiration_invalid"),
            ("2030-01-01T00:00:00", "expiration_timezone_missing"),
        ]:
            with self.subTest(expiry=expiry):
                source = FakeSource(expires=expiry)
                with tempfile.TemporaryDirectory() as folder:
                    run(source, folder)
                    with self.assertRaisesRegex(StageRejected, expected):
                        run(source, folder, resume=True, expected_total=3)
                    self.assertEqual(source.fetches, [None])

    def test_opt_in_naive_expiry_allows_server_authoritative_resume(self):
        source = FakeSource(expires="2030-01-01T00:00:00")
        with tempfile.TemporaryDirectory() as folder:
            run(source, folder, max_pages=1)
            result = run(
                source, folder, max_pages=1, resume=True, expected_total=3,
                allow_naive_server_validation=True, sleep_fn=lambda _: None,
            )
            self.assertEqual(result["status"], "complete")
            self.assertEqual(source.fetches, [None, "secret-next-token"])
            self.assertFalse(result["promotion_authorized"])
            self.assertFalse(result["media_downloaded"])

    def test_default_remains_strict_for_naive_expiry(self):
        source = FakeSource(expires="2030-01-01T00:00:00")
        with tempfile.TemporaryDirectory() as folder:
            run(source, folder)
            with self.assertRaisesRegex(
                StageRejected, "resume_cursor_expiration_timezone_missing"
            ):
                run(source, folder, resume=True, expected_total=3)
            self.assertEqual(source.fetches, [None])

    def test_opt_in_never_bypasses_known_expired_offset(self):
        source = FakeSource(expires="2020-01-01T00:00:00+00:00")
        with tempfile.TemporaryDirectory() as folder:
            run(source, folder)
            with self.assertRaisesRegex(
                StageRejected, "resume_cursor_expired_or_too_close"
            ):
                run(
                    source, folder, resume=True, expected_total=3,
                    allow_naive_server_validation=True,
                )
            self.assertEqual(source.fetches, [None])

    def test_opt_in_rejects_missing_and_malformed_expirations(self):
        for expires, expected in (
            (None, "resume_cursor_expiration_missing"),
            ("not-a-datetime", "resume_cursor_expiration_invalid"),
        ):
            with self.subTest(expires=expires):
                source = FakeSource(expires=expires)
                with tempfile.TemporaryDirectory() as folder:
                    run(source, folder)
                    with self.assertRaisesRegex(StageRejected, expected):
                        run(
                            source, folder, resume=True, expected_total=3,
                            allow_naive_server_validation=True,
                        )
                    self.assertEqual(source.fetches, [None])

    def test_opt_in_requires_one_page_batch(self):
        source = FakeSource()
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(
                ValueError, "naive_server_validation_requires_one_page"
            ):
                run(
                    source, folder, max_pages=2,
                    allow_naive_server_validation=True,
                )
            self.assertEqual(source.preflights, 0)
            self.assertEqual(source.fetches, [])

    def test_opt_in_still_checks_cursor_integrity(self):
        source = FakeSource(
            expires="2030-01-01T00:00:00", source_token="different"
        )
        with tempfile.TemporaryDirectory() as folder:
            run(source, folder)
            with self.assertRaisesRegex(StageRejected, "source_cursor_mismatch"):
                run(
                    source, folder, resume=True, expected_total=3,
                    allow_naive_server_validation=True,
                )
            self.assertEqual(source.fetches, [None])

    def test_response_cursor_must_match_normalized_cursor(self):
        source = FakeSource(source_token="substituted-value")
        with tempfile.TemporaryDirectory() as folder:
            run(source, folder)
            with self.assertRaisesRegex(StageRejected, "source_cursor_mismatch"):
                run(source, folder, resume=True, expected_total=3)
            self.assertEqual(source.fetches, [None])

    def test_external_anchors_required_before_resume(self):
        source = FakeSource()
        with tempfile.TemporaryDirectory() as folder:
            run(source, folder)
            with self.assertRaisesRegex(ValueError, "external_expected_total"):
                run(source, folder, resume=True)
            with self.assertRaisesRegex(StageRejected, "checkpoint_total_drift"):
                run(source, folder, resume=True, expected_total=4)
            self.assertEqual(source.preflights, 1)
            self.assertEqual(source.fetches, [None])

    def test_live_count_drift_rejected_without_next_fetch(self):
        source = FakeSource()
        with tempfile.TemporaryDirectory() as folder:
            run(source, folder)
            source.total = 4
            with self.assertRaisesRegex(StageRejected, "checkpoint_total_drift"):
                run(source, folder, resume=True, expected_total=3, sleep_fn=lambda _: None)
            self.assertEqual(source.fetches, [None])

    def test_between_page_delay_applies_within_one_bounded_run(self):
        source = FakeSource()
        sleeps = []
        with tempfile.TemporaryDirectory() as folder:
            result = run(
                source, folder, max_pages=2, delay_seconds=0.75,
                sleep_fn=sleeps.append,
            )
        self.assertEqual(result["status"], "complete")
        self.assertEqual(sleeps, [0.75])
        self.assertEqual(len(source.fetches), 2)

    def test_batch_limits_checked_without_io(self):
        with tempfile.TemporaryDirectory() as folder:
            source = FakeSource()
            with self.assertRaisesRegex(ValueError, "batch_pages"):
                run(source, folder, max_pages=26)
            with self.assertRaisesRegex(ValueError, "batch_delay"):
                run(source, folder, delay_seconds=0.1)
            with self.assertRaisesRegex(ValueError, "expiry_margin"):
                run(source, folder, expiry_margin_seconds=-1)
            self.assertEqual(source.preflights, 0)

    def test_unauthorized_scope_is_rejected(self):
        source = FakeSource()
        source.scope["building_code"] = "0/OTHER/"
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "unapproved_finna_batch_scope"):
                run(source, folder)

    def test_cli_remains_dry_by_default_and_requires_total_for_resume(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["--evidence-sha256", EVIDENCE])
        self.assertEqual(code, 0)
        self.assertIn("DRY RUN", output.getvalue())
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as err:
                main(["--evidence-sha256", EVIDENCE, "--resume"])
        self.assertEqual(err.exception.code, 2)


    def test_within_batch_cursor_expires_before_second_fetch(self):
        source = FakeSource(expires="2020-01-01T00:00:00Z")
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(StageRejected, "expired_or_too_close"):
                run(source, folder, max_pages=2, sleep_fn=lambda _: None)
            # The first page is saved, but an expired continuation is never used.
            self.assertEqual(source.fetches, [None])
            stored = json.loads((Path(folder) / "checkpoint.json").read_text())
            self.assertEqual(stored["record_count"], 2)
            self.assertEqual(stored["status"], "partial")

    def test_within_batch_cursor_mismatch_never_fetched(self):
        source = FakeSource(source_token="wrong-response-cursor")
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(StageRejected, "source_cursor_mismatch"):
                run(source, folder, max_pages=2, sleep_fn=lambda _: None)
            self.assertEqual(source.fetches, [None])

    def test_cursor_rechecked_after_resume_throttle_with_current_clock(self):
        source = FakeSource(expires="2026-10-12T08:01:00Z")
        with tempfile.TemporaryDirectory() as folder:
            run(source, folder)
            clocks = iter([NOW, datetime(2026, 10, 12, 8, 0, 40, tzinfo=timezone.utc)])
            with self.assertRaisesRegex(StageRejected, "expired_or_too_close"):
                execute_verified_batch(
                    source, folder, resume=True, expected_total=3,
                    now_fn=lambda: next(clocks), sleep_fn=lambda _: None,
                )
            self.assertEqual(source.fetches, [None])

    def test_changed_checkpoint_during_resume_pause_is_restored_under_lock(self):
        source = FakeSource()
        other = FakeSource()
        with tempfile.TemporaryDirectory() as folder:
            run(source, folder)

            def another_writer_during_pause(_seconds):
                # Deterministically simulate another cooperative process
                # completing the checkpoint while this runner is paused.
                from memoria_audiovisual.metadata_staging import stage_metadata
                stage_metadata(other, folder, resume=True, max_pages=1)

            result = run(
                source, folder, resume=True, expected_total=3,
                sleep_fn=another_writer_during_pause,
            )
            self.assertEqual(result["status"], "complete")
            self.assertEqual(source.fetches, [None])
            self.assertEqual(other.fetches, ["secret-next-token"])



if __name__ == "__main__":
    unittest.main()
