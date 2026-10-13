"""Offline epoch recovery must never mix or silently discard KAVI pages."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.kavi_finna_adapter import FinnaScope
from memoria_audiovisual.metadata_staging import (
    MetadataPage, StageRejected, stage_metadata,
)
from scripts.kavi_finna_epoch_recovery import (
    ABORT_MARKER, initialize_epoch_workspace, inspect_epoch_workspace,
    restart_after_confirmed_expiry,
)

EVIDENCE = "a" * 64
PROOF = "b" * 64
CONTRACT = "c" * 64


def normalized(identifier: str) -> dict:
    return {
        "id": identifier, "title": "Metadata only",
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


class SyntheticSource:
    def __init__(self, *, terminal: bool = False, identity: str = "kavi.elonet_elokuva_001"):
        self.scope = FinnaScope("0/KAVI/", "0/Video/", EVIDENCE).to_dict()
        self.identity = identity
        self.terminal = terminal
        self.preflights = 0
        self.requests = []

    def preflight(self):
        self.preflights += 1
        return 1 if self.terminal else 2

    def fetch_page(self, token):
        self.requests.append(token)
        record = normalized(self.identity)
        cursor = None if self.terminal else "opaque-next"
        return MetadataPage(
            (record,), self.preflight_total,
            cursor,
            {
                "status": "OK",
                "resultCount": self.preflight_total,
                "records": [{"id": self.identity, "title": record["title"]}],
                "resumptionToken": (
                    {"token": cursor, "expires": "2030-01-01T00:00:00Z"}
                    if cursor is not None else None
                ),
            },
        )

    @property
    def preflight_total(self):
        return 1 if self.terminal else 2


def restart(root: Path, **changes):
    args = {
        "evidence_sha256": EVIDENCE,
        "expected_total": 2,
        "failure_reason": "provider_confirmed_token_expired",
        "provider_response_sha256": PROOF,
        "provider_contract_sha256": CONTRACT,
        "operator_authorized": True,
    }
    args.update(changes)
    return restart_after_confirmed_expiry(root, **args)


class EpochRecoveryTests(unittest.TestCase):
    def prepare_partial(self, root):
        started = initialize_epoch_workspace(root, evidence_sha256=EVIDENCE)
        self.assertEqual(started["active_epoch"], 1)
        self.assertEqual(started["restart_budget"], 1)
        source = SyntheticSource()
        report = stage_metadata(source, root / "epochs" / "epoch-0001", max_pages=1)
        self.assertEqual(report["status"], "partial")
        self.assertEqual(report["record_count"], 1)
        return source

    def test_init_is_offline_and_cannot_clobber_workspace(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "kavi-epochs"
            report = initialize_epoch_workspace(root, evidence_sha256=EVIDENCE)
            self.assertEqual(report["network_requests_performed"], 0)
            self.assertEqual(report["active_epoch"], 1)
            self.assertFalse(report["promotion_authorized"])
            self.assertFalse(report["media_downloaded"])
            with self.assertRaisesRegex(StageRejected, "workspace_already_exists"):
                initialize_epoch_workspace(root, evidence_sha256=EVIDENCE)
            self.assertEqual(
                inspect_epoch_workspace(root, evidence_sha256=EVIDENCE)["active_epoch"], 1,
            )

    def test_recovery_freezes_old_epoch_and_creates_isolated_successor(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "kavi-epochs"
            old_source = self.prepare_partial(root)
            old = root / "epochs" / "epoch-0001"
            old_checkpoint = (old / "checkpoint.json").read_bytes()
            result = restart(root)
            self.assertEqual(result["active_epoch"], 2)
            self.assertEqual(result["restart_count"], 1)
            self.assertEqual(result["network_requests_performed"], 0)
            self.assertFalse(result["media_downloaded"])
            self.assertFalse(result["promotion_authorized"])
            self.assertEqual(
                result["prior_epochs"],
                [
                    {"number": 1, "state": "aborted_confirmed_expiration"},
                    {"number": 2, "state": "active"},
                ],
            )
            self.assertEqual((old / "checkpoint.json").read_bytes(), old_checkpoint)
            tombstone = json.loads((old / ABORT_MARKER).read_text())
            self.assertEqual(tombstone["provider_response_sha256"], PROOF)
            self.assertEqual(tombstone["expected_total"], 2)
            self.assertEqual(tombstone["record_count"], 1)
            self.assertFalse(tombstone["promotion_authorized"])
            self.assertFalse(tombstone["media_downloaded"])
            self.assertNotIn("opaque-next", json.dumps(result))
            self.assertNotIn("opaque-next", json.dumps(tombstone))
            self.assertFalse((root / "epochs" / "epoch-0002" / "checkpoint.json").exists())

            # A discarded epoch must stop BEFORE any HTTP preflight or fetch.
            with self.assertRaisesRegex(StageRejected, "staging_epoch_aborted"):
                stage_metadata(old_source, old, resume=True)
            self.assertEqual(old_source.preflights, 1)
            self.assertEqual(old_source.requests, [None])

            # The successor is a separate epoch with a fresh page cursor.
            new_source = SyntheticSource(terminal=True, identity="other-video-002")
            report = stage_metadata(new_source, root / "epochs" / "epoch-0002")
            self.assertEqual(report["status"], "complete")
            self.assertEqual(new_source.requests, [None])
            self.assertNotIn("opaque-next", json.dumps(report["pages"]))
            self.assertEqual(
                inspect_epoch_workspace(root, evidence_sha256=EVIDENCE)["restart_count"], 1,
            )

    def test_unconfirmed_failures_never_rollover(self):
        for reason in (
            "resume_cursor_expiration_timezone_missing",
            "resume_cursor_expired_or_too_close",
            "finna_http_status_400",
            "finna_http_status_429",
            "finna_http_status_500",
            "finna_guard_transport_unverifiable",
            "checkpoint_total_drift",
        ):
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / "kavi-epochs"
                self.prepare_partial(root)
                with self.assertRaisesRegex(StageRejected, "expiration_not_confirmed"):
                    restart(root, failure_reason=reason)
                self.assertFalse(
                    (root / "epochs" / "epoch-0001" / ABORT_MARKER).exists()
                )
                self.assertFalse((root / "epochs" / "epoch-0002").exists())

    def test_operator_and_independent_proofs_required(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "kavi-epochs"
            self.prepare_partial(root)
            with self.assertRaisesRegex(StageRejected, "operator_approval"):
                restart(root, operator_authorized=False)
            with self.assertRaisesRegex(StageRejected, "evidence_unverified"):
                restart(root, provider_response_sha256="not-a-digest")
            with self.assertRaisesRegex(StageRejected, "evidence_unverified"):
                restart(root, provider_contract_sha256="")
            with self.assertRaisesRegex(StageRejected, "scope_evidence_mismatch"):
                restart(root, evidence_sha256="d" * 64)
            with self.assertRaisesRegex(StageRejected, "checkpoint_total_drift"):
                restart(root, expected_total=3)
            self.assertFalse((root / "epochs" / "epoch-0002").exists())

    def test_complete_checkpoint_cannot_be_abandoned_as_expired(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "kavi-epochs"
            initialize_epoch_workspace(root, evidence_sha256=EVIDENCE)
            source = SyntheticSource(terminal=True)
            stage_metadata(source, root / "epochs" / "epoch-0001")
            with self.assertRaisesRegex(StageRejected, "cannot_restart_complete"):
                restart(root, expected_total=1)
            self.assertFalse((root / "epochs" / "epoch-0002").exists())

    def test_restarts_strictly_limited_to_one(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "kavi-epochs"
            self.prepare_partial(root)
            restart(root)
            with self.assertRaisesRegex(StageRejected, "restart_budget_exhausted"):
                restart(root)
            self.assertEqual(
                inspect_epoch_workspace(root, evidence_sha256=EVIDENCE)["active_epoch"], 2,
            )

    def test_tampering_with_controller_and_tombstone_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "kavi-epochs"
            self.prepare_partial(root)
            restart(root)
            marker = root / "epochs" / "epoch-0001" / ABORT_MARKER
            marker.unlink()
            with self.assertRaisesRegex(StageRejected, "abort_marker_missing"):
                inspect_epoch_workspace(root, evidence_sha256=EVIDENCE)

    def test_no_alternative_directory_when_rollback_incomplete(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "kavi-epochs"
            self.prepare_partial(root)
            (root / "epochs" / "epoch-0002").mkdir()
            with self.assertRaisesRegex(StageRejected, "successor_already_exists"):
                restart(root)
            self.assertFalse((root / "epochs" / "epoch-0001" / ABORT_MARKER).exists())


if __name__ == "__main__":
    unittest.main()
