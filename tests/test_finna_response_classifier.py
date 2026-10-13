"""Finna REST failure taxonomy: offline and explicitly NOT an expiry oracle."""
from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

import requests

from memoria_audiovisual.finna_response_classifier import (
    classify_api_payload, classify_http_status, classify_stage_rejection,
    classify_provider_token_response,
)
from memoria_audiovisual.kavi_finna_adapter import FinnaMetadataSource, FinnaScope
from memoria_audiovisual.metadata_staging import StageRejected


def fail_closed(assessment):
    self_report = assessment.public_dict()
    assert self_report["token_expiration_confirmed"] is False
    assert self_report["restart_authorized"] is False
    assert self_report["promotion_authorized"] is False
    assert self_report["media_downloaded"] is False
    assert "opaque" not in json.dumps(self_report)
    return self_report


class FailureClassificationTests(unittest.TestCase):
    def test_distinguish_http_codes_without_expiration_claims(self):
        expected = [
            (400, "client_error_unverified", False),
            (404, "client_error_unverified", False),
            (403, "access_denied", False),
            (408, "http_timeout_or_too_early", True),
            (429, "rate_limited", True),
            (500, "upstream_failure", True),
            (503, "upstream_failure", True),
            (302, "unexpected_redirect", False),
            (201, "unexpected_http_status", False),
        ]
        for status, category, retry_candidate in expected:
            with self.subTest(status=status):
                report = fail_closed(classify_http_status(status))
                self.assertEqual(report["failure_category"], category)
                self.assertEqual(report["manual_retry_candidate"], retry_candidate)
                self.assertEqual(report["reason"], f"finna_http_status_{status}")

    def test_success_and_unexpected_status_are_distinct(self):
        self.assertIsNone(classify_http_status(200))
        for bad in (None, True, False, "400", 900, -1):
            with self.subTest(bad=bad):
                report = fail_closed(classify_http_status(bad))
                self.assertEqual(report["reason"], "finna_http_status_unknown")

    def test_free_text_expired_alone_cannot_prove_expiration(self):
        for payload in (
            {"status": "ERROR", "statusMessage": "resumptionToken expired"},
            {"status": "ERROR", "error": "expired", "code": "token_expired"},
            {"status": "ERROR", "statusMessage": "badResumptionToken"},
            {"status": "ERROR", "statusMessage": "opaque-secret-token"},
            {"status": "FAIL", "message": "expired"},
            [],
            None,
        ):
            with self.subTest(payload_type=type(payload).__name__):
                report = fail_closed(classify_api_payload(payload))
                self.assertEqual(report["reason"], "finna_api_status_invalid")
                self.assertEqual(report["failure_category"], "api_rejection_unverified")
                self.assertNotIn("expired", report["reason"])
        self.assertIsNone(classify_api_payload({"status": "OK"}))
        self.assertIsNone(classify_api_payload({"status": "ok"}))

    def test_upstream_invalid_or_expired_signature_is_ambiguous(self):
        exact = json.dumps({
            "status": "ERROR", "statusMessage": "Invalid or expired token",
        })
        result = classify_provider_token_response(
            http_status=400, mime="application/json; charset=utf-8",
            body=exact, continuation=True,
        )
        self.assertIsNotNone(result)
        summary = fail_closed(result)
        self.assertEqual(
            summary["failure_category"], "token_invalid_or_expired_unresolved"
        )
        self.assertEqual(
            summary["reason"], "finna_token_invalid_or_expired_unresolved"
        )
        self.assertEqual(
            fail_closed(classify_stage_rejection(summary["reason"])),
            summary,
        )

    def test_upstream_signature_requires_exact_request_and_body(self):
        exact = json.dumps({
            "status": "ERROR", "statusMessage": "Invalid or expired token",
        })
        negative = (
            (200, "application/json", exact, True),
            (429, "application/json", exact, True),
            (503, "application/json", exact, True),
            (400, "text/html", exact, True),
            (400, "application/json", exact, False),
            (400, "application/json", '{"status":"ERROR","statusMessage":"expired"}', True),
            (400, "application/json", '{"status":"ERROR","statusMessage":"Invalid or expired token!"}', True),
            (400, "application/json", '{"status":"OK","statusMessage":"Invalid or expired token"}', True),
            (400, "application/json", '{"statusMessage":"Invalid or expired token"}', True),
            (400, "application/json", "not-json", True),
            (400, "application/json", " " * 8193, True),
        )
        for status, mime, body, continuation in negative:
            with self.subTest(status=status, mime=mime, body=body[:40]):
                self.assertIsNone(classify_provider_token_response(
                    http_status=status, mime=mime,
                    body=body, continuation=continuation,
                ))

    def test_local_expiry_flags_are_not_provider_confirmation(self):
        for code in (
            "resume_cursor_expiration_timezone_missing",
            "resume_cursor_expired_or_too_close",
            "resume_cursor_expiration_missing",
            "resume_source_cursor_mismatch",
        ):
            with self.subTest(code=code):
                report = fail_closed(classify_stage_rejection(code))
                self.assertEqual(report["failure_category"], "local_expiry_unverified")

    def test_drift_transport_access_integrity_categories(self):
        inputs = [
            ("checkpoint_total_drift", "snapshot_drift"),
            ("result_total_drift", "snapshot_drift"),
            ("finna_guard_transport_unverifiable", "transport_or_response_unverifiable"),
            ("finna_invalid_json", "transport_or_response_unverifiable"),
            ("finna_robots_or_origin_block", "access_denied"),
            ("checkpoint_raw_artifact_tampered", "integrity_failure"),
            ("staging_epoch_aborted", "integrity_failure"),
            ("finna_api_status_invalid", "api_rejection_or_shape_unverified"),
        ]
        for code, cat in inputs:
            with self.subTest(code=code):
                report = fail_closed(classify_stage_rejection(code))
                self.assertEqual(report["failure_category"], cat)

    def test_existing_checkpoint_corruption_is_not_undifferentiated(self):
        codes = (
            "checkpoint_scope_payload_tampered",
            "checkpoint_ids_hash_mismatch",
            "checkpoint_page_sequence_invalid",
            "checkpoint_record_count_mismatch",
            "checkpoint_total_records_mismatch",
            "checkpoint_false_complete",
            "checkpoint_next_cursor_mismatch",
            "checkpoint_raw_artifact_missing",
            "checkpoint_promotion_gate_tampered",
        )
        for code in codes:
            with self.subTest(code=code):
                report = fail_closed(classify_stage_rejection(code))
                self.assertEqual(report["failure_category"], "integrity_failure")
                self.assertEqual(report["reason"], code)

    def test_offline_audit_and_resume_codes_preserve_diagnostics(self):
        codes = [
            "offline_checkpoint_missing",
            "offline_checkpoint_invalid",
            "offline_checkpoint_not_object",
            "audit_source_to_normalized_ids_mismatch",
            "audit_provenance_or_rights_violation",
            "audit_record_count_mismatch",
            "resume_checkpoint_unreadable",
            "resume_source_cursor_unverifiable",
            "resume_invalid_artifact_sha256",
            "resume_raw_artifact_tampered",
            "batch_audit_record_count_mismatch",
        ]
        for code in codes:
            with self.subTest(code=code):
                report = fail_closed(classify_stage_rejection(code))
                self.assertEqual(report["failure_category"], "integrity_failure")
                self.assertEqual(report["reason"], code)

    def test_all_static_rejections_in_relevant_executors_are_classified(self):
        # Contract coverage: adding a new stable local StageRejected code
        # requires explicit categorization rather than silently erasing it.
        root = Path(__file__).resolve().parents[1]
        paths = (
            "src/memoria_audiovisual/metadata_staging.py",
            "src/memoria_audiovisual/kavi_finna_adapter.py",
            "scripts/audit_kavi_finna_staging.py",
            "scripts/probe_kavi_finna_two_page_resume.py",
            "scripts/kavi_finna_batch_gate.py",
        )
        missing = []
        for path in paths:
            tree = ast.parse((root / path).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Raise):
                    continue
                exc = node.exc
                if (
                    isinstance(exc, ast.Call)
                    and isinstance(exc.func, ast.Name)
                    and exc.func.id == "StageRejected"
                    and exc.args
                    and isinstance(exc.args[0], ast.Constant)
                    and isinstance(exc.args[0].value, str)
                ):
                    code = exc.args[0].value
                    result = classify_stage_rejection(code)
                    if result.reason != code:
                        missing.append((path, code))
        self.assertEqual(missing, [])

    def test_unknown_rejections_are_redacted_not_echoed(self):
        for reason in (
            "token expired opaque-123",
            "https://api.finna.fi/v1/search?resumptionToken=opaque",
            "finna_http_status_999",
            "finna_http_status_429; secret token",
            None,
        ):
            with self.subTest(reason=reason):
                report = fail_closed(classify_stage_rejection(reason))
                self.assertEqual(report["reason"], "finna_unclassified_failure")
                self.assertEqual(report["failure_category"], "unknown_rejection")

    def test_status_code_in_stage_exception_maps_to_same_taxonomy(self):
        for status in (400, 403, 429, 503):
            raw = classify_http_status(status)
            mapped = classify_stage_rejection(raw.reason)
            self.assertEqual(raw, mapped)


class FinnaAdapterFailureTests(unittest.TestCase):
    def setUp(self):
        self.source = FinnaMetadataSource(
            requests.Session(),
            FinnaScope("0/KAVI/", "0/Video/", "a" * 64),
        )
        # Strictly fake transport; guard never reaches network or robots.
        self.target = "https://api.finna.fi/v1/search?resumptionToken=opaque"

    def mock_reply(self, *, status=200, payload=None, raw=None, mime="application/json", error=None):
        response = SimpleNamespace(
            status=status, mime=mime, error=error,
            text=raw if raw is not None else json.dumps(payload),
        )
        self.source.guard = SimpleNamespace(get=lambda url: response)

    def test_transport_exception_without_status_is_not_http_unknown(self):
        self.mock_reply(
            status=None, error="ConnectionError: https://api.finna.fi/v1/search?"
                               "resumptionToken=opaque",
            raw="",
        )
        with self.assertRaisesRegex(
            StageRejected, "^finna_guard_transport_unverifiable$"
        ) as ctx:
            self.source._json(self.target)
        report = fail_closed(classify_stage_rejection(str(ctx.exception)))
        self.assertEqual(
            report["failure_category"], "transport_or_response_unverifiable",
        )
        self.assertNotIn("opaque", json.dumps(report))

    def test_stream_read_error_without_status_is_redacted(self):
        self.mock_reply(
            status=None,
            error="stream_read_failed: https://api.finna.fi/"
                  "v1/search?resumptionToken=opaque",
            raw="",
        )
        with self.assertRaisesRegex(
            StageRejected, "^finna_guard_stream_read_failed$"
        ) as ctx:
            self.source._json(self.target)
        report = fail_closed(classify_stage_rejection(str(ctx.exception)))
        self.assertEqual(
            report["failure_category"], "transport_or_response_unverifiable",
        )

    def test_real_upstream_400_is_recognized_only_on_continuation(self):
        payload = {
            "status": "ERROR", "statusMessage": "Invalid or expired token",
        }
        self.mock_reply(status=400, payload=payload)
        with self.assertRaisesRegex(
            StageRejected, "^finna_token_invalid_or_expired_unresolved$"
        ):
            self.source._json(self.target, continuation=True)
        with self.assertRaisesRegex(StageRejected, "^finna_http_status_400$"):
            self.source._json(self.target, continuation=False)

    def test_ambiguous_token_text_on_503_stays_upstream_failure(self):
        self.mock_reply(status=503, payload={
            "status": "ERROR", "statusMessage": "Invalid or expired token",
        })
        with self.assertRaisesRegex(StageRejected, "^finna_http_status_503$"):
            self.source._json(self.target, continuation=True)

    def test_400_expired_text_does_not_authorize_restart(self):
        self.mock_reply(
            status=400, payload={"status": "ERROR", "statusMessage": "expired opaque"}
        )
        with self.assertRaisesRegex(StageRejected, "^finna_http_status_400$") as ctx:
            self.source._json(self.target)
        self.assertNotIn("opaque", str(ctx.exception))
        report = fail_closed(classify_stage_rejection(str(ctx.exception)))
        self.assertEqual(report["failure_category"], "client_error_unverified")

    def test_http_429_and_503_are_not_expiration(self):
        for status, category in ((429, "rate_limited"), (503, "upstream_failure")):
            with self.subTest(status=status):
                self.mock_reply(status=status, payload={"message": "expired"})
                with self.assertRaises(StageRejected) as ctx:
                    self.source._json(self.target)
                report = fail_closed(classify_stage_rejection(str(ctx.exception)))
                self.assertEqual(report["failure_category"], category)
                self.assertTrue(report["manual_retry_candidate"])

    def test_200_error_payload_is_unverified(self):
        self.mock_reply(payload={
            "status": "ERROR", "statusMessage": "Token expired opaque-secret"
        })
        with self.assertRaisesRegex(StageRejected, "^finna_api_status_invalid$") as ctx:
            self.source._json(self.target)
        self.assertEqual(
            fail_closed(classify_stage_rejection(str(ctx.exception)))["failure_category"],
            "api_rejection_or_shape_unverified",
        )

    def test_unparseable_reply_fail_closed(self):
        self.mock_reply(raw="{broken")
        with self.assertRaisesRegex(StageRejected, "^finna_invalid_json$") as ctx:
            self.source._json(self.target)
        fail_closed(classify_stage_rejection(str(ctx.exception)))

    def test_success_is_unchanged(self):
        self.mock_reply(payload={"status": "OK", "resultCount": 0, "records": []})
        self.assertEqual(self.source._json(self.target)["status"], "OK")


if __name__ == "__main__":
    unittest.main()
