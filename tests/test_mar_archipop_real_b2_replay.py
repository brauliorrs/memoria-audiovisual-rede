"""MAR B2: real ARCHIPOP replay, isolated source-drift and atomic rollback."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.build_mar_site_bundle_b2 import (
    BundleError, atomic_stage_files, project_research_slices, sha256_file,
)
from scripts.check_mar_scientific_snapshot_lock import git_blob_sha, verify as verify_source_lock
from scripts.rehearse_mar_archipop_real_b2 import ROOT, review_archipop


class RealArchipopEngineeringRehearsal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="mar-real-archipop-tests-")
        cls.place = Path(cls.tmp.name)
        cls.last_good = cls.place / "last-good"
        cls.result = review_archipop(ROOT, cls.last_good)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_rebuilds_all_real_projections_and_reconciles_historical_shift(self):
        r = self.result
        self.assertEqual(r["corpus"], "archipop")
        self.assertEqual(r["historicalVideoCounts"], [57, 58])
        self.assertEqual(r["historicalObservations"], 2)
        self.assertEqual(r["countryAggregates"], 58)
        self.assertEqual(r["platformAggregates"], 58)
        self.assertEqual(r["historicalAccessRecords"], 58)
        self.assertEqual(r["wordcloudSourceRows"], 58)
        self.assertEqual(r["institutions"], 1)
        self.assertEqual(r["country"], "France")
        self.assertEqual(r["stagedCorpora"], 62)
        self.assertEqual(r["stagedStaticFiles"], 34)
        self.assertFalse(r["publicationAuthorized"])
        self.assertFalse(r["mediaDownloaded"])
        self.assertTrue(r["sourceFilesUnchanged"])
        self.assertEqual(len(r["epochSha256"]), 64)

    def test_every_staged_output_matches_single_manifest_epoch(self):
        m = json.loads((self.last_good / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(m["epochSha256"], self.result["epochSha256"])
        self.assertEqual(len(m["outputSha256"]), 34)
        for rel, checksum in m["outputSha256"].items():
            self.assertEqual(sha256_file(self.last_good / rel), checksum)
        for name in ("kavi-public.json", "public-access-observatory.json", "documented-cases.json"):
            staged = json.loads((self.last_good / "site/data" / name).read_text(encoding="utf-8"))
            historical = json.loads((ROOT / "site/data" / name).read_text(encoding="utf-8"))
            self.assertEqual(staged, historical)

    def test_corrupt_latest_candidate_fails_atomically_and_retains_last_good(self):
        manifest_file = self.last_good / "manifest.json"
        before = manifest_file.read_bytes()
        before_data = (self.last_good / "site/data/analytics-0.json").read_bytes()
        bad = self.place / "tampered-unapproved"
        shutil.copytree(self.last_good, bad)
        cloud = bad / "site/data/title-wordcloud.json"
        cloud.write_bytes(cloud.read_bytes() + b"\n")
        reviewed = json.loads(before)
        dest = self.place / "new-candidate-should-not-exist"
        with self.assertRaisesRegex(BundleError, "Staged output hash drift"):
            atomic_stage_files(
                bad, dest, sorted(reviewed["outputSha256"]),
                {"staticProjectionSha256": reviewed["outputSha256"],
                 "publicationAuthorized": False},
            )
        self.assertFalse(dest.exists())
        self.assertEqual(manifest_file.read_bytes(), before)
        self.assertEqual((self.last_good / "site/data/analytics-0.json").read_bytes(), before_data)

    def test_real_archipop_source_drift_is_detected_without_mutating_repository(self):
        root = self.place / "corrupted-real-source-copy"
        out = root / "data/output"
        out.mkdir(parents=True)
        site = root / "site/data"
        site.mkdir(parents=True)
        suffixes = (
            "_relatorio.json", "_instituicoes.csv", "_tema_pais.csv",
            "_tema_plataforma.csv", "_linha_do_tempo_corpus.csv",
            "_catalogo_videos_analitico.csv",
        )
        inputs = {}
        for suffix in suffixes:
            rel = "data/output/archipop" + suffix
            shutil.copyfile(ROOT / rel, root / rel)
            inputs[rel] = git_blob_sha(root / rel)
        rel_out = "site/data/analytics-0.json"
        shutil.copyfile(ROOT / rel_out, root / rel_out)
        lock = {
            "schema": "mar-scientific-snapshot-lock-v1",
            "status": "historical_baseline_only_not_a_regeneration_or_publication_approval",
            "policy": "fail_closed_until_full_reproducible_aggregate_bundle_and_scientific_approval",
            "inputs": inputs,
            "outputs": {rel_out: git_blob_sha(root / rel_out)},
        }
        self.assertEqual(verify_source_lock(root, lock), [])
        dims = project_research_slices(root, "archipop")
        self.assertEqual(sum(int(x["total"]) for x in dims["tema_pais"]["rows"]), 58)
        corrupted = out / "archipop_tema_pais.csv"
        historical = corrupted.read_text(encoding="utf-8")
        # Deliberate fake scientific mismatch ONLY inside a temporary copy.
        corrupted.write_text(historical.replace("France,19", "France,999", 1), encoding="utf-8")
        self.assertTrue(any(
            "Changed scientific source" in issue for issue in verify_source_lock(root, lock)
        ))
        self.assertEqual((ROOT / "data/output/archipop_tema_pais.csv").read_text(encoding="utf-8"),
                         historical)
        self.assertTrue((self.last_good / "manifest.json").exists())
        self.assertEqual(self.result["currentVideoCount"], 58)


if __name__ == "__main__":
    unittest.main()
