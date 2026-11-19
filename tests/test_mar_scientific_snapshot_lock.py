"""Offline mutation tests for the fail-closed MAR snapshot lock."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_mar_scientific_snapshot_lock import git_blob_sha, verify


class ScientificSnapshotLockTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "data/output").mkdir(parents=True)
        (self.root / "site/data").mkdir(parents=True)
        self.source = self.root / "data/output/example_relatorio.json"
        self.projection = self.root / "site/data/analytics-0.json"
        self.source.write_text('{"count": 2}', encoding="utf-8")
        self.projection.write_text('[{"count": 2}]', encoding="utf-8")
        self.lock = {
            "schema": "mar-scientific-snapshot-lock-v1",
            "status": "historical_baseline_only_not_a_regeneration_or_publication_approval",
            "policy": "fail_closed_until_full_reproducible_aggregate_bundle_and_scientific_approval",
            "inputs": {"data/output/example_relatorio.json": git_blob_sha(self.source)},
            "outputs": {"site/data/analytics-0.json": git_blob_sha(self.projection)},
        }

    def test_unchanged_baseline_passes_without_claiming_regeneration(self):
        self.assertEqual(verify(self.root, self.lock), [])
        self.assertIn("not_a_regeneration", self.lock["status"])

    def test_changed_source_fails_even_when_projection_is_unchanged(self):
        self.source.write_text('{"count": 3}', encoding="utf-8")
        self.assertTrue(any("Changed scientific source" in x for x in verify(self.root, self.lock)))

    def test_new_corpus_source_fails_closed(self):
        (self.root / "data/output/new_corpus_relatorio.json").write_text("{}", encoding="utf-8")
        self.assertTrue(any("New scientific source" in x for x in verify(self.root, self.lock)))

    def test_removed_source_fails_closed(self):
        self.source.unlink()
        self.assertTrue(any("Missing scientific source" in x for x in verify(self.root, self.lock)))

    def test_partial_projection_update_fails(self):
        self.projection.write_text('[{"count": 3}]', encoding="utf-8")
        self.assertTrue(any("Changed site projection" in x for x in verify(self.root, self.lock)))

    def test_untracked_new_panel_fails(self):
        (self.root / "site/data/analytics-1.json").write_text("[]", encoding="utf-8")
        self.assertTrue(any("New site projection" in x for x in verify(self.root, self.lock)))

    def test_manual_status_upgrade_does_not_claim_validated_generator(self):
        self.lock["status"] = "regenerated"
        self.assertTrue(any("cannot be presented" in x for x in verify(self.root, self.lock)))

    def test_wordcloud_and_geometry_remain_separately_managed(self):
        (self.root / "site/data/title-wordcloud.json").write_text("{}", encoding="utf-8")
        (self.root / "site/data/world-110m-geometry.json").write_text("{}", encoding="utf-8")
        self.assertEqual(verify(self.root, self.lock), [])


if __name__ == "__main__":
    unittest.main()
