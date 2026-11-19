"""B2: atomic scientific bundle, source provenance and synthetic HOLD regressions."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_mar_site_bundle_b2 import (
    BundleError,
    STAGE_SCHEMA,
    atomic_stage_files,
    load_reviewed_bundle,
    manifest,
    stage,
)
from scripts.check_mar_scientific_snapshot_lock import git_blob_sha, verify as verify_source_lock

ROOT = Path(__file__).resolve().parents[1]


def digest(contents: bytes):
    return hashlib.sha256(contents).hexdigest()


class AtomicBundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "fixture-mar"
        self.source = self.root / "site/data/analytics-0.json"
        self.source.parent.mkdir(parents=True)
        self.source.write_text('[{"code":"sample","totalInstitutions":1}]', encoding="utf-8")
        self.original = self.source.read_bytes()
        self.rel = "site/data/analytics-0.json"
        self.fake_manifest = {
            "schema": STAGE_SCHEMA,
            "publicationAuthorized": False,
            "staticProjectionSha256": {self.rel: digest(self.original)},
        }
        self.target = Path(self.tmp.name) / "review-bundle"

    def test_atomic_staging_does_not_mutate_source_or_publish_items(self):
        atomic_stage_files(self.root, self.target, [self.rel], self.fake_manifest)
        self.assertTrue((self.target / self.rel).exists())
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertFalse(json.loads((self.target / "manifest.json").read_text())["publicationAuthorized"])

    def test_partial_failure_never_exposes_staging_directory(self):
        bad = dict(self.fake_manifest, staticProjectionSha256={self.rel: "0" * 64})
        with self.assertRaisesRegex(BundleError, "Staged output hash drift"):
            atomic_stage_files(self.root, self.target, [self.rel], bad)
        self.assertFalse(self.target.exists())
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_staging_cannot_write_over_existing_version(self):
        self.target.mkdir()
        with self.assertRaisesRegex(BundleError, "exists"):
            atomic_stage_files(self.root, self.target, [self.rel], self.fake_manifest)
        self.assertFalse((self.target / self.rel).exists())

    def test_staging_cannot_write_into_live_site(self):
        with self.assertRaisesRegex(BundleError, "inside"):
            atomic_stage_files(self.root, self.root / "site/data/deploy", [self.rel], self.fake_manifest)

    def test_synthetic_corpus_addition_invalidates_reviewed_source_lock(self):
        # This fixture proves fail-closed admission, not automatic authorisation.
        original = self.root / "data/output/synthetic_relatorio.json"
        original.parent.mkdir(parents=True)
        original.write_text('{"total_institutions":1}', encoding="utf-8")
        lock = {
            "schema": "mar-scientific-snapshot-lock-v1",
            "status": "historical_baseline_only_not_a_regeneration_or_publication_approval",
            "policy": "fail_closed_until_full_reproducible_aggregate_bundle_and_scientific_approval",
            "inputs": {"data/output/synthetic_relatorio.json": git_blob_sha(original)},
            "outputs": {self.rel: git_blob_sha(self.source)},
        }
        self.assertEqual(verify_source_lock(self.root, lock), [])
        # A valid-looking additional scientific corpus cannot be added to a
        # public panel until the full bundle and explicit reviews are updated.
        added = original.parent / "another_corpus_relatorio.json"
        added.write_text('{"total_institutions":99}', encoding="utf-8")
        problems = verify_source_lock(self.root, lock)
        self.assertTrue(any("New scientific source" in issue for issue in problems))
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_synthetic_scientific_change_with_old_panel_is_blocked(self):
        original = self.root / "data/output/synthetic_relatorio.json"
        original.parent.mkdir(parents=True)
        original.write_text('{"total_institutions":1}', encoding="utf-8")
        lock = {
            "schema": "mar-scientific-snapshot-lock-v1",
            "status": "historical_baseline_only_not_a_regeneration_or_publication_approval",
            "policy": "fail_closed_until_full_reproducible_aggregate_bundle_and_scientific_approval",
            "inputs": {"data/output/synthetic_relatorio.json": git_blob_sha(original)},
            "outputs": {self.rel: git_blob_sha(self.source)},
        }
        original.write_text('{"total_institutions":2}', encoding="utf-8")
        self.assertTrue(any("Changed scientific source" in issue for issue in verify_source_lock(self.root, lock)))
        self.assertEqual(self.source.read_bytes(), self.original)


class RealFrozenMARReview(unittest.TestCase):
    def test_full_static_ledger_and_scientific_coverage(self):
        sources, projected, reports = load_reviewed_bundle(ROOT)
        self.assertEqual(reports, 62)
        self.assertEqual(len(projected), 34)  # 33 scientific JSONs + title cloud
        self.assertEqual(len(sources), 563)

    def test_full_bundle_manifest_is_deterministic_and_not_publication(self):
        first = manifest(ROOT)
        second = manifest(ROOT)
        self.assertEqual(first, second)
        self.assertEqual(first["schema"], STAGE_SCHEMA)
        self.assertFalse(first["publicationAuthorized"])
        self.assertFalse(first["publicAccessAuthorized"])
        self.assertEqual(first["individuallyApprovedKaviMetadataRecords"], 200)
        self.assertEqual(len(first["epochSha256"]), 64)

    def test_full_stage_is_outside_repository_and_rollback_safe(self):
        with tempfile.TemporaryDirectory() as dest:
            target = Path(dest) / "snapshot"
            info = stage(ROOT, target)
            self.assertEqual(len(info["staticProjectionSha256"]), 34)
            self.assertTrue((target / "manifest.json").exists())
            self.assertTrue((target / "site/data/analytics-0.json").exists())
            self.assertTrue((target / "site/data/title-wordcloud.json").exists())
            self.assertFalse(info["publicationAuthorized"])


if __name__ == "__main__":
    unittest.main()
