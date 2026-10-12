"""Regression tests for offline, independently anchored KAVI staging audit."""
from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.metadata_staging import MetadataPage, StageRejected, stage_metadata
from scripts.audit_kavi_finna_staging import audit_finna_staging, main

EVIDENCE = "a" * 64


def normalized(identifier: str, *, rights: str = "not_verified",
               provider: str = "0/KAVI/") -> dict:
    return {
        "id": identifier, "title": "Film candidate",
        "formats": [{"value": "0/Video/", "translated": "Video"}],
        "provider_index_code": provider,
        "custody_status": "not_established",
        "media_rights_status": rights,
        "media_downloaded": False,
        "film_semantics": (
            "film_candidate"
            if identifier.startswith("kavi.elonet_elokuva_")
            else "unverified_audiovisual_record"
        ),
    }


def page(records: list[dict], token: str | None,
         *, original_ids: list[str] | None = None) -> MetadataPage:
    return MetadataPage(
        tuple(records), 3, token,
        {"status": "OK", "resultCount": 3, "records": [
            {"id": ident, "title": "Film candidate"}
            for ident in (
                original_ids if original_ids is not None
                else [row["id"] for row in records]
            )
        ], "resumptionToken": (
            {"token": token, "expires": "2030-01-01T00:00:00Z"}
            if token is not None else None
        )},
    )


class OfflineSource:
    def __init__(self, *, first_override=None):
        self.scope = {
            "building_code": "0/KAVI/",
            "format_code": "0/Video/",
            "evidence_sha256": EVIDENCE,
            "institution_code": "fiaf-kavi",
            "schema_version": "1.0.0",
            "adapter_version": "kavi-finna-adapter-1.0.0",
        }
        self.pages = {
            None: first_override or page([
                normalized("kavi.elonet_elokuva_01"),
                normalized("kavi.elonet_elokuva_02"),
            ], "private-cursor-value"),
            "private-cursor-value": page([
                normalized("other_video_record")], None),
        }
        self.requests = []

    def preflight(self):
        return 3

    def fetch_page(self, token):
        self.requests.append(token)
        return self.pages[token]


class KaviOfflineAuditTests(unittest.TestCase):
    def audit(self, root, *, evidence=EVIDENCE, total=3):
        return audit_finna_staging(
            root, evidence_sha256=evidence, expected_total=total
        )

    def test_partial_and_complete_audit_without_new_network_calls(self):
        source = OfflineSource()
        with tempfile.TemporaryDirectory() as folder:
            first = stage_metadata(source, folder, max_pages=1)
            self.assertEqual(first["status"], "partial")
            requests_before = list(source.requests)
            report = self.audit(folder)
            self.assertEqual(source.requests, requests_before)
            self.assertTrue(report["offline_integrity_verified"])
            self.assertFalse(report["api_snapshot_freshness_verified"])
            self.assertEqual(report["record_count"], 2)
            self.assertEqual(report["page_count"], 1)
            self.assertEqual(report["status"], "partial")
            self.assertEqual(report["provenance_audit"]["film_id_candidates"], 2)
            self.assertEqual(report["provenance_audit"]["other_video_records"], 0)
            self.assertNotIn("private-cursor-value", json.dumps(report))
            self.assertFalse(report["promotion_authorized"])
            self.assertFalse(report["media_downloaded"])
            stage_metadata(source, folder, resume=True, max_pages=1)
            second = self.audit(folder)
            self.assertEqual(second["status"], "complete")
            self.assertEqual(second["record_count"], 3)
            self.assertEqual(second["page_count"], 2)
            self.assertEqual(second["provenance_audit"]["other_video_records"], 1)
            self.assertNotIn("private-cursor-value", json.dumps(second))
            self.assertEqual(source.requests, [None, "private-cursor-value"])

    def test_requires_external_count_and_evidence_anchor(self):
        with tempfile.TemporaryDirectory() as folder:
            stage_metadata(OfflineSource(), folder, max_pages=1)
            with self.assertRaisesRegex(StageRejected, "checkpoint_total_drift"):
                self.audit(folder, total=4)
            with self.assertRaisesRegex(StageRejected, "checkpoint_scope_mismatch"):
                self.audit(folder, evidence="b" * 64)
            with self.assertRaisesRegex(ValueError, "expected_total_must"):
                self.audit(folder, total=-1)

    def test_missing_or_corrupt_checkpoint_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(StageRejected, "offline_checkpoint_missing"):
                self.audit(folder)
            (Path(folder) / "checkpoint.json").write_text("{bad json")
            with self.assertRaisesRegex(StageRejected, "offline_checkpoint_invalid"):
                self.audit(folder)

    def test_changed_artifact_bytes_fail_integrity_replay(self):
        with tempfile.TemporaryDirectory() as folder:
            report = stage_metadata(OfflineSource(), folder, max_pages=1)
            hash_ = report["pages"][0]["artifact_sha256"]
            artifact = Path(folder) / "raw" / hash_[:2] / (hash_ + ".json")
            artifact.write_text('{"tampered":true}', encoding="utf-8")
            with self.assertRaisesRegex(
                StageRejected, "checkpoint_raw_artifact_tampered"
            ):
                self.audit(folder)

    def test_unverified_rights_cannot_be_relabelled(self):
        wrong = page([
            normalized("kavi.elonet_elokuva_01", rights="licensed"),
            normalized("kavi.elonet_elokuva_02"),
        ], "private-cursor-value")
        with tempfile.TemporaryDirectory() as folder:
            stage_metadata(OfflineSource(first_override=wrong), folder)
            with self.assertRaisesRegex(
                StageRejected, "audit_provenance_or_rights_violation"
            ):
                self.audit(folder)

    def test_source_normalized_id_mismatch_fails_closed(self):
        wrong = page([
            normalized("kavi.elonet_elokuva_01"),
            normalized("kavi.elonet_elokuva_02"),
        ], "private-cursor-value", original_ids=[
            "kavi.elonet_elokuva_01", "wrong_source_id",
        ])
        with tempfile.TemporaryDirectory() as folder:
            stage_metadata(OfflineSource(first_override=wrong), folder)
            with self.assertRaisesRegex(
                StageRejected, "audit_source_to_normalized_ids_mismatch"
            ):
                self.audit(folder)

    def test_cli_outputs_only_rejection_code(self):
        with tempfile.TemporaryDirectory() as folder:
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                code = main([
                    "--directory", folder,
                    "--evidence-sha256", EVIDENCE,
                    "--expected-total", "3",
                ])
            self.assertEqual(code, 2)
            message = json.loads(captured.getvalue())
            self.assertEqual(message["audit_status"], "rejected")
            self.assertEqual(message["reason"], "offline_checkpoint_missing")
            self.assertFalse(message["promotion_authorized"])


if __name__ == "__main__":
    unittest.main()
