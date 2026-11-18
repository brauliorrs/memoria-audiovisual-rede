"""Scientific contracts for shared research slices and verified world geographies."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
WORLD = json.loads((SITE / "data/world-110m-geometry.json").read_text(encoding="utf-8"))


class ResearchMapAndPermalinkTests(unittest.TestCase):
    def test_world_map_uses_verifiable_110m_public_geometry(self):
        self.assertEqual(WORLD["schema"], "mar-territorial-geometry-110m-v1")
        self.assertEqual(WORLD["projection"], "equirectangular")
        self.assertEqual(WORLD["viewBox"], "0 0 900 450")
        self.assertIn("Natural Earth", WORLD["origin"])
        self.assertIn("geo-boundaries-world-110m", WORLD["originRepository"])
        self.assertIn("public domain", WORLD["licence"].lower())
        self.assertRegex(WORLD["originFileSha"], r"^[a-f0-9]{40}$")
        self.assertGreaterEqual(len(WORLD["geometries"]), 170)
        self.assertEqual(len(WORLD["geometries"]), len({c["name"] for c in WORLD["geometries"]}))
        for shape in WORLD["geometries"]:
            self.assertTrue(shape["name"])
            self.assertRegex(shape["iso"], r"^[A-Z0-9-]{3}$")
            self.assertRegex(shape["d"], r"^M-?\d")
            self.assertIn("Z", shape["d"])
            for unsafe in ("<script", "onload=", "javascript:", "<iframe", "video_title"):
                self.assertNotIn(unsafe, shape["d"])

    def test_all_mapped_countries_use_observed_labels_not_invented_records(self):
        groups = {}
        for i in range(16):
            part = json.loads((SITE / f"data/research-slices-{i}.json").read_text(encoding="utf-8"))
            groups.update(part)
        observed = {
            row["pais"] for group in groups.values()
            for row in group["tema_pais"]["rows"] if row.get("pais")
        }
        rendered = {x["name"] for x in WORLD["geometries"]}
        unmapped = observed - rendered
        # Tiny countries absent in 1:110m: still listed as totals, never plotted at fake coordinates.
        self.assertEqual(unmapped, {"Isle of Man", "Monaco"})
        self.assertIn("Czech Republic", rendered)
        self.assertIn("United States", rendered)
        self.assertGreaterEqual(len(observed & rendered), 25)

    def test_map_is_nonidentifying_and_multilingual(self):
        component = (SITE / "components/territorial-map.tsx").read_text(encoding="utf-8")
        route = (SITE / "app/territorios/page.tsx").read_text(encoding="utf-8")
        self.assertIn("world.geometries.map", component)
        self.assertIn("sourceSlice.tema_pais.rows", component)
        self.assertIn("summary.unmapped", component)
        self.assertIn("historical", component.lower())
        self.assertIn("role=\"status\"", component)
        self.assertIn("PT", (SITE / "components/site-header.tsx").read_text(encoding="utf-8"))
        for lang in ("pt:", "en:", "es:"):
            self.assertIn(lang, component)
        for forbidden in ("<video", "<iframe", "fetch(", "DATABASE_URL", "api.finna.fi", "video_title"):
            self.assertNotIn(forbidden, component)
        self.assertIn("TerritorialMap", route)

    def test_reproducible_state_and_frozen_provenance_exist(self):
        helper = (SITE / "lib/research-permalink.ts").read_text(encoding="utf-8")
        ui = (SITE / "components/corpus-comparison.tsx").read_text(encoding="utf-8")
        provenance = (SITE / "lib/research-snapshot.ts").read_text(encoding="utf-8")
        self.assertIn("decodeResearchSlice", helper)
        self.assertIn("encodeResearchSlice", helper)
        self.assertIn("cleanSources", helper)
        self.assertIn("MAX_QUERY = 96", helper)
        self.assertIn("new URLSearchParams(window.location.search)", ui)
        self.assertIn("window.history.replaceState", ui)
        self.assertIn("navigator.clipboard.writeText", ui)
        self.assertIn("researchSnapshotCommit", ui)
        self.assertIn("source_snapshot_commit", ui)
        self.assertRegex(provenance, r"[a-f0-9]{40}")
        self.assertTrue((SITE / "tests/research-permalink.test.cjs").is_file())


if __name__ == "__main__":
    unittest.main()
