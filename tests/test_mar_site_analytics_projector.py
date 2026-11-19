"""Architecture B/B1: no-network reconstruction of approved aggregate report snapshots."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_mar_site_analytics import (
    ProjectionError,
    compile_projection,
    project_report,
    reviewed_analytics,
    stage,
    verify,
)

ROOT = Path(__file__).resolve().parents[1]


def example_report(total=2):
    return {
        "source": "https://example.org/catalogue",
        "total_institutions": total,
        "with_video_count": 1,
        "with_embeds_count": 0,
        "status_summary": {"ok": total},
        "integrity_summary": {"integro": total},
        "platform_summary": {"Example": 3},
        "continent_summary": {"Europe": total},
        "video_continent_summary": {"Europe": 1},
        "top_institutions": [
            {"institution": "private not for aggregate output", "video_url": "https://example.org/video.mp4"}
        ],
    }


def snapshot_root(root: Path):
    data = root / "data" / "output"
    output = root / "site" / "data"
    data.mkdir(parents=True)
    output.mkdir(parents=True)
    report = data / "sample_relatorio.json"
    report.write_text(json.dumps(example_report()), encoding="utf-8")
    projection = project_report(report, root)
    (output / "analytics-0.json").write_text(json.dumps([projection]), encoding="utf-8")
    return report, output / "analytics-0.json"


class AnalyticsProjectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "mar"
        self.root.mkdir()
        self.report, self.projection = snapshot_root(self.root)

    def test_existing_projected_aggregates_match_source(self):
        self.assertEqual(verify(self.root), [])
        self.assertEqual(list(compile_projection(self.root)[2]), ["analytics-0.json"])

    def test_source_change_cannot_leave_old_site_snapshots(self):
        self.report.write_text(json.dumps(example_report(3)), encoding="utf-8")
        self.assertTrue(any("drift" in error.lower() for error in verify(self.root)))

    def test_new_corpus_cannot_silently_join_site(self):
        (self.root / "data/output/new_relatorio.json").write_text(
            json.dumps(example_report()), encoding="utf-8"
        )
        self.assertTrue(any("new_unreviewed" in error for error in verify(self.root)))

    def test_missing_scientific_corpus_blocks(self):
        self.report.unlink()
        self.assertNotEqual(verify(self.root), [])

    def test_incorrect_counter_is_rejected(self):
        bad = example_report()
        bad["platform_summary"]["Example"] = -1
        self.report.write_text(json.dumps(bad), encoding="utf-8")
        self.assertNotEqual(verify(self.root), [])

    def test_bad_input_json_blocks(self):
        self.report.write_text("{", encoding="utf-8")
        self.assertNotEqual(verify(self.root), [])

    def test_unreviewed_individual_fields_are_excluded(self):
        row = project_report(self.report, self.root)
        dump = json.dumps(row)
        self.assertNotIn("top_institutions", dump)
        self.assertNotIn("video.mp4", dump)
        self.assertNotIn("https://example.org/catalogue", dump)

    def test_stage_manifest_is_not_publication_and_does_not_touch_site(self):
        outside = Path(self.tmp.name) / "candidate"
        before = self.projection.read_bytes()
        manifest = stage(self.root, outside)
        self.assertFalse(manifest["publicationAuthorized"])
        self.assertEqual(manifest["corpusCount"], 1)
        self.assertEqual(set(manifest["outputSha256"]), {"analytics-0.json"})
        self.assertEqual(before, self.projection.read_bytes())
        self.assertEqual(json.loads((outside / "manifest.json").read_text()), manifest)
        self.assertEqual(json.loads((outside / "analytics-0.json").read_text())[0]["code"], "sample")

    def test_staging_inside_repository_or_overwriting_is_forbidden(self):
        with self.assertRaises(ProjectionError):
            stage(self.root, self.root / "site/data/candidate")
        candidate = Path(self.tmp.name) / "candidate"
        candidate.mkdir()
        with self.assertRaises(ProjectionError):
            stage(self.root, candidate)

    def test_existing_real_mar_baseline_has_semantic_parity(self):
        self.assertEqual(verify(ROOT), [])
        paths, rows = reviewed_analytics(ROOT)
        self.assertEqual(len(rows), 62)
        self.assertEqual(len(paths), 6)
        self.assertEqual({row["code"] for row in rows}, {row["code"] for chunk in compile_projection(ROOT)[2].values() for row in chunk})


if __name__ == "__main__":
    unittest.main()
