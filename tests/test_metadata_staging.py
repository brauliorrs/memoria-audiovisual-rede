"""Reusable metadata stage: immutability, replay, dedupe and fail-closed gates."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.metadata_staging import (
    MetadataPage, StageRejected, public_stage_summary, stage_metadata,
)


class FakeSource:
    def __init__(self, pages, *, total=3, evidence="a" * 64):
        self.pages = dict(pages)
        self.total = total
        self.scope = {"institution": "fiaf-kavi", "evidence": evidence}
        self.requests = []

    def preflight(self):
        return self.total

    def fetch_page(self, token):
        self.requests.append(token)
        return self.pages[token]


def page(ids, total, next_token):
    records = tuple(
        {"id": item, "title": "Film " + item, "custody_status": "not_established",
         "media_rights_status": "not_verified", "media_downloaded": False}
        for item in ids
    )
    return MetadataPage(records, total, next_token, {
        "status": "OK", "resultCount": total,
        "records": list(records), "resumptionToken": next_token,
    })


class MetadataStagingTests(unittest.TestCase):
    def test_partial_checkpoint_and_verified_resume_to_complete(self):
        source = FakeSource({
            None: page(["a", "b"], 3, "next-secret-cursor"),
            "next-secret-cursor": page(["c"], 3, None),
        })
        with tempfile.TemporaryDirectory() as directory:
            partial = stage_metadata(source, directory, max_pages=1)
            self.assertEqual(partial["status"], "partial")
            self.assertEqual(partial["record_count"], 2)
            self.assertEqual(source.requests, [None])
            summary = public_stage_summary(partial)
            self.assertFalse(summary["promotion_authorized"])
            self.assertFalse(summary["media_downloaded"])
            self.assertNotIn("next-secret-cursor", json.dumps(summary))
            self.assertNotIn(
                "next-secret-cursor",
                (Path(directory) / "checkpoint.json").read_text(),
            )
            finished = stage_metadata(source, directory, resume=True, max_pages=1)
            self.assertEqual(finished["status"], "complete")
            self.assertEqual(finished["record_count"], 3)
            self.assertEqual(source.requests, [None, "next-secret-cursor"])
            again = stage_metadata(source, directory, resume=True)
            self.assertEqual(again["status"], "complete")
            self.assertEqual(len(source.requests), 2)
            self.assertEqual(len(list((Path(directory) / "raw").rglob("*.json"))), 2)

    def test_checkpoint_exists_requires_explicit_resume(self):
        source = FakeSource({None: page(["a"], 2, "t")}, total=2)
        with tempfile.TemporaryDirectory() as root:
            stage_metadata(source, root)
            with self.assertRaisesRegex(StageRejected, "resume_required"):
                stage_metadata(source, root, resume=False)
            with self.assertRaisesRegex(StageRejected, "scope_mismatch"):
                stage_metadata(
                    FakeSource({}, total=2, evidence="b" * 64), root, resume=True,
                )

    def test_missing_checkpoint_cannot_claim_resume(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(StageRejected, "checkpoint_missing"):
                stage_metadata(FakeSource({}, total=1), root, resume=True)

    def test_duplicate_across_pages_aborts_before_second_checkpoint(self):
        source = FakeSource({
            None: page(["a", "b"], 3, "t"),
            "t": page(["b", "c"], 3, None),
        })
        with tempfile.TemporaryDirectory() as root:
            stage_metadata(source, root)
            with self.assertRaisesRegex(StageRejected, "duplicate_ids_across_pages"):
                stage_metadata(source, root, resume=True)
            saved = json.loads((Path(root) / "checkpoint.json").read_text())
            self.assertEqual(saved["record_count"], 2)
            self.assertEqual(len(saved["pages"]), 1)

    def test_duplicate_inside_page_and_overflow_rejected(self):
        for source, expected in [
            (FakeSource({None: page(["a", "a"], 2, None)}, total=2),
             "duplicate_ids_within_page"),
            (FakeSource({None: page(["a", "b"], 1, None)}, total=1),
             "records_exceed_preflight_total"),
        ]:
            with self.subTest(expected=expected):
                with tempfile.TemporaryDirectory() as root:
                    with self.assertRaisesRegex(StageRejected, expected):
                        stage_metadata(source, root)
                    self.assertFalse((Path(root) / "checkpoint.json").exists())

    def test_non_terminal_empty_page_and_cursor_cycle_abort(self):
        for source, expected in [
            (FakeSource({None: page([], 3, "t")}), "empty_intermediate_page"),
            (FakeSource({None: page(["a"], 3, "t"), "t": page(["b"], 3, "t")}),
             "resumption_token_cycle"),
        ]:
            with self.subTest(expected=expected):
                with tempfile.TemporaryDirectory() as root:
                    with self.assertRaisesRegex(StageRejected, expected):
                        stage_metadata(source, root, max_pages=2)

    def test_early_termination_or_total_drift_fails_closed(self):
        for source, expected in [
            (FakeSource({None: page(["a"], 3, None)}, total=3),
             "terminal_total_mismatch"),
            (FakeSource({None: page(["a"], 4, None)}, total=3),
             "result_total_drift"),
        ]:
            with self.subTest(expected=expected):
                with tempfile.TemporaryDirectory() as root:
                    with self.assertRaisesRegex(StageRejected, expected):
                        stage_metadata(source, root)

    def test_preflight_count_drift_prevents_resume(self):
        source = FakeSource({None: page(["a"], 2, "t")}, total=2)
        with tempfile.TemporaryDirectory() as root:
            stage_metadata(source, root)
            source.total = 3
            with self.assertRaisesRegex(StageRejected, "checkpoint_total_drift"):
                stage_metadata(source, root, resume=True)

    def test_artifact_tampering_prevents_resume(self):
        source = FakeSource({None: page(["a"], 2, "t")}, total=2)
        with tempfile.TemporaryDirectory() as root:
            report = stage_metadata(source, root)
            digest = report["pages"][0]["artifact_sha256"]
            path = Path(root) / "raw" / digest[:2] / (digest + ".json")
            path.write_text('{"spoofed":true}', encoding="utf-8")
            with self.assertRaisesRegex(StageRejected, "artifact_tampered"):
                stage_metadata(source, root, resume=True)

    def test_cursor_hash_chain_is_checked(self):
        source = FakeSource({
            None: page(["a"], 2, "t"),
            "t": page(["b"], 2, None),
        }, total=2)
        with tempfile.TemporaryDirectory() as root:
            stage_metadata(source, root, max_pages=2)
            path = Path(root) / "checkpoint.json"
            state = json.loads(path.read_text())
            state["pages"][1]["input_cursor_sha256"] = hashlib.sha256(b"fake").hexdigest()
            path.write_text(json.dumps(state))
            with self.assertRaisesRegex(StageRejected, "cursor_chain"):
                stage_metadata(source, root, resume=True)

    def test_no_media_download_in_metadata_stage(self):
        class MetadataOnlySource(FakeSource):
            def fetch_page(self, token):
                data = super().fetch_page(token)
                return data

        with tempfile.TemporaryDirectory() as root:
            report = stage_metadata(
                MetadataOnlySource({None: page(["film-1"], 1, None)}, total=1),
                root,
            )
            self.assertFalse(report["media_downloaded"])
            self.assertFalse(report["promotion_authorized"])
            self.assertEqual(report["status"], "complete")


if __name__ == "__main__":
    unittest.main()
