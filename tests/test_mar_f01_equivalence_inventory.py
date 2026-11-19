"""F01 contract and adversarial checks: inventory is NOT scientific approval."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "f01_audit", ROOT / "scripts/check_mar_f01_equivalence_inventory.py"
)
audit = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(audit)
BASE = json.loads(
    (ROOT / "docs/engineering/mar-f01-functional-equivalence-inventory.json")
    .read_text(encoding="utf-8")
)


class F01InventoryTests(unittest.TestCase):
    def data(self):
        return copy.deepcopy(BASE)

    def test_exact_references_exist_without_publication(self):
        data = self.data()
        self.assertEqual(audit.check_inventory(data), [])
        self.assertEqual(len(data["flows"]), 24)
        self.assertFalse(data["release_authorized"])
        self.assertTrue(all(not x["equivalence_accepted"] for x in data["flows"]))

    def test_required_global_search_gap_remains_explicit(self):
        f = next(x for x in BASE["flows"] if x["id"] == "M01")
        self.assertEqual(f["status"], "partial")
        self.assertIn("dez dimensoes", f["gap"])
        self.assertFalse(f["scientific_release_authorized"])

    def test_operational_gaps_cannot_claim_implemented_destinations(self):
        data = self.data()
        f = next(x for x in data["flows"] if x["id"] == "M16")
        f["target"] = ["site/components/catalog-search.tsx"]
        self.assertTrue(audit.check_inventory(data))

    def test_missing_code_path_is_blocked(self):
        data = self.data()
        data["flows"][0]["target"] = ["site/app/not-a-real-page.tsx"]
        self.assertTrue(audit.check_inventory(data))

    def test_missing_streamlit_anchor_is_blocked(self):
        data = self.data()
        data["flows"][0]["anchor"] = "nonexistent_operation_no_parity"
        self.assertTrue(audit.check_inventory(data))

    def test_duplicate_flow_id_is_blocked(self):
        data = self.data()
        data["flows"][1]["id"] = data["flows"][0]["id"]
        self.assertTrue(audit.check_inventory(data))

    def test_no_release_via_audit(self):
        data = self.data()
        data["release_authorized"] = True
        self.assertTrue(audit.check_inventory(data))

    def test_cannot_claim_functional_equivalence_by_editing_json(self):
        data = self.data()
        data["flows"][0]["equivalence_accepted"] = True
        self.assertTrue(audit.check_inventory(data))

    def test_cannot_publish_media_or_hold_by_editing_json(self):
        data = self.data()
        data["flows"][0]["scientific_release_authorized"] = True
        self.assertTrue(audit.check_inventory(data))

    def test_untracked_risks_are_blocked(self):
        data = self.data()
        data["flows"][0]["gap"] = ""
        self.assertTrue(audit.check_inventory(data))

    def test_path_traversal_is_blocked(self):
        data = self.data()
        data["flows"][0]["target"] = ["../../etc/passwd"]
        self.assertTrue(audit.check_inventory(data))

    def test_all_streamlit_renderers_mapped(self):
        self.assertEqual(len(BASE["render_function_coverage"]), 20)
        self.assertEqual(len(BASE["data_helper_coverage"]), 18)

    def test_unmapped_renderer_is_blocked(self):
        data = self.data()
        del data["render_function_coverage"]["render_videos_tab"]
        self.assertTrue(audit.check_inventory(data))

    def test_unmapped_helper_is_blocked(self):
        data = self.data()
        del data["data_helper_coverage"]["build_research_video_catalog_frame"]
        self.assertTrue(audit.check_inventory(data))


if __name__ == "__main__":
    unittest.main()
