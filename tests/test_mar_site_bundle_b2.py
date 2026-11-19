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
    project_research_slices,
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

    def test_synthetic_approved_aggregate_change_refreshes_research_dimensions(self):
        # Positive no-network prototype: only aggregate research dimensions
        # are rebuilt. This is not a new public corpus nor the final full B2.
        out = self.root / "data/output"
        out.mkdir(parents=True, exist_ok=True)
        headers = {
            "tema_pais": ["tema", "pais", "total"],
            "tema_plataforma": ["tema", "plataforma", "total"],
            "linha_do_tempo_corpus": ["dataset", "observation_key", "snapshot_generated_at", "video_links_total"],
        }
        records = {
            "tema_pais": ["Memória", "Portugal", "2"],
            "tema_plataforma": ["Memória", "Arquivo institucional", "2"],
            "linha_do_tempo_corpus": ["fixture_lab", "fixture_lab:2026-11-01T12:00:00Z", "2026-11-01T12:00:00Z", "2"],
        }
        for dim, names in headers.items():
            path = out / f"fixture_lab_{dim}.csv"
            path.write_text(",".join(names) + "\n" + ",".join(records[dim]) + "\n", encoding="utf-8")
        from scripts.build_mar_site_analytics import project_report
        report_path = out / "fixture_lab_relatorio.json"
        scientific = {
            "total_institutions": 1, "with_video_count": 2, "with_embeds_count": 0,
            "status_summary": {"ok": 1}, "integrity_summary": {"integro": 1},
            "platform_summary": {"Arquivo institucional": 2},
            "continent_summary": {"Europe": 1}, "video_continent_summary": {"Europe": 1},
            "top_institutions": [{"video_url": "https://example.test/hidden-film.mp4"}],
        }
        report_path.write_text(json.dumps(scientific), encoding="utf-8")
        before_agg = project_report(report_path, self.root)
        self.assertEqual(before_agg["institutionsWithVideo"], 2)
        self.assertNotIn("hidden-film", json.dumps(before_agg))
        before = project_research_slices(self.root, "fixture_lab")
        self.assertEqual(before["tema_pais"]["rows"][0]["total"], "2")
        self.assertEqual(before["tema_plataforma"]["rows"][0]["total"], "2")
        self.assertEqual(before["linha_do_tempo_corpus"]["rows"][0]["video_links_total"], "2")
        for dim, names in headers.items():
            path = out / f"fixture_lab_{dim}.csv"
            path.write_text(",".join(names) + "\n" + ",".join(records[dim][:-1] + ["3"]) + "\n", encoding="utf-8")
        after = project_research_slices(self.root, "fixture_lab")
        scientific["with_video_count"] = 3
        scientific["platform_summary"]["Arquivo institucional"] = 3
        report_path.write_text(json.dumps(scientific), encoding="utf-8")
        after_agg = project_report(report_path, self.root)
        self.assertEqual(after_agg["institutionsWithVideo"], 3)
        self.assertEqual(after_agg["platforms"]["Arquivo institucional"], 3)
        for dim, count in (
            ("tema_pais", "total"), ("tema_plataforma", "total"),
            ("linha_do_tempo_corpus", "video_links_total")
        ):
            self.assertEqual(after[dim]["rows"][0][count], "3")
        self.assertNotEqual(before, after)
        self.assertNotIn("records", after)
        self.assertEqual(self.source.read_bytes(), self.original)

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
