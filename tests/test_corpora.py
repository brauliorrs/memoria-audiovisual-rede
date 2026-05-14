import unittest

from memoria_audiovisual.corpora import (
    CORPORA,
    CORPUS_CATEGORIES,
    OBSERVATORY_PROFILE,
    list_active_corpora,
    list_corpora_by_category,
)


class CorporaDefinitionsTests(unittest.TestCase):
    def test_every_corpus_declares_a_valid_category(self):
        for corpus_def in CORPORA.values():
            self.assertIn("category_code", corpus_def)
            self.assertIn(corpus_def["category_code"], CORPUS_CATEGORIES)
            self.assertIn("coverage_level", corpus_def)
            self.assertIn("expansion_priority", corpus_def)
            self.assertIn("expansion_rationale", corpus_def)
            self.assertIn("observatory_role", corpus_def)
            self.assertIn("audiovisual_scope_note", corpus_def)
            self.assertIn("zero_result_policy", corpus_def)
            self.assertIn("run_script_path", corpus_def)
            self.assertIn("check_script_path", corpus_def)
            self.assertIn("organism_active", corpus_def)
            self.assertIn("monthly_refresh_enabled", corpus_def)

    def test_category_listing_returns_only_matching_corpora(self):
        for category_code in CORPUS_CATEGORIES:
            corpora = list_corpora_by_category(category_code)
            self.assertTrue(corpora)
            self.assertTrue(
                all(corpus_def["category_code"] == category_code for corpus_def in corpora)
            )

    def test_categories_declare_expansion_policy(self):
        for category_def in CORPUS_CATEGORIES.values():
            self.assertIn("expansion_priority", category_def)
            self.assertIn("expansion_stage_label", category_def)
            self.assertIn("expansion_rule", category_def)
            self.assertIn("inclusion_criterion", category_def)
            self.assertIn("audiovisual_entry_rule", category_def)

    def test_observatory_profile_declares_growth_model(self):
        self.assertIn("role", OBSERVATORY_PROFILE)
        self.assertIn("description", OBSERVATORY_PROFILE)
        self.assertIn("expansion_strategy", OBSERVATORY_PROFILE)
        self.assertIn("audiovisual_rule", OBSERVATORY_PROFILE)
        self.assertIn("refresh_cadence", OBSERVATORY_PROFILE)

    def test_list_active_corpora_returns_sorted_active_entries(self):
        active_corpora = list_active_corpora(monthly_only=True)
        self.assertTrue(active_corpora)
        self.assertTrue(all(corpus_def["organism_active"] for corpus_def in active_corpora))
        self.assertTrue(all(corpus_def["monthly_refresh_enabled"] for corpus_def in active_corpora))


if __name__ == "__main__":
    unittest.main()
