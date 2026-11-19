"""Production B2 source projector: frozen historical parity, staging and curation."""
import tempfile
import unittest
from pathlib import Path

from scripts.build_mar_site_projections_b2 import (
    ROOT, BundleError, CURATED, PROJECTOR_SCHEMA, generated_documents,
    project_research_pilot, semantic_parity, stage,
)

class RealMARProjectionReviewTests(unittest.TestCase):
    def test_every_current_scientific_projection_reconstructs_semantically(self):
        self.assertEqual(semantic_parity(ROOT), [])
        objects, codes = generated_documents(ROOT)
        self.assertEqual(len(codes), 62)
        self.assertEqual(len(objects), 34)
        self.assertTrue(all(f in objects for f in CURATED))
        self.assertTrue(all(f"site/data/research-slices-{i}.json" in objects for i in range(16)))
        self.assertEqual(len(objects["site/data/research-0.json"]), 4)

    def test_stage_is_atomic_outside_repo_and_preserves_all_curated_data(self):
        with tempfile.TemporaryDirectory(prefix="mar-real-b2-") as base:
            target = Path(base) / "candidate"
            before = (ROOT / "site/data/kavi-public.json").read_bytes()
            result = stage(ROOT, target)
            self.assertEqual(result["schema"], PROJECTOR_SCHEMA)
            self.assertFalse(result["publicationAuthorized"])
            self.assertFalse(result["publicAccessAuthorized"])
            self.assertEqual(len(result["epochSha256"]), 64)
            self.assertEqual(len(result["outputSha256"]), 34)
            self.assertTrue((target / "manifest.json").exists())
            self.assertTrue((target / "site/data/title-wordcloud.json").exists())
            self.assertTrue((target / "site/data/kavi-public.json").exists())
            self.assertEqual(before, (ROOT / "site/data/kavi-public.json").read_bytes())

    def test_cannot_write_review_bundle_into_site_or_overwrite_existing(self):
        with self.assertRaises(BundleError):
            stage(ROOT, ROOT / "site/data/unreviewed-candidate")
        with tempfile.TemporaryDirectory(prefix="mar-real-b2-") as base:
            with self.assertRaises(BundleError):
                stage(ROOT, Path(base))

    def test_pilot_editorial_topic_order_is_preserved(self):
        slice_ = {
            "tema_pais":{"rows":[{"tema":"B","pais":"Portugal","total":"2"},
                                   {"tema":"A","pais":"Portugal","total":"3"}]},
            "tema_plataforma":{"rows":[{"tema":"B","plataforma":"Arquivo","total":"2"},
                                        {"tema":"A","plataforma":"Arquivo","total":"3"}]},
            "linha_do_tempo_corpus":{"rows":[{"snapshot_generated_at":"2026-11-19T12:00:00Z",
                "observation_key":"fixture:2026-11-19T12:00:00Z",
                "video_links_total":"5","institutions":"1",
                "videos_in_curatorial_catalog":"5"}]},
        }
        reviewed={"themes":[{"theme":"A"},{"theme":"B"}]}
        generated=project_research_pilot("fixture",slice_,reviewed)
        self.assertEqual([x["theme"] for x in generated["themes"]],["A","B"])
        self.assertEqual([x["value"] for x in generated["themes"]],[3,2])
        self.assertEqual(generated["timeline"][0]["videoLinks"],5)
        with self.assertRaisesRegex(BundleError,"Reviewed pilot topics"):
            project_research_pilot("fixture",slice_,{"themes":[{"theme":"C"}]})

if __name__=="__main__":
    unittest.main()
