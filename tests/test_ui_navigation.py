import unittest

from memoria_audiovisual.ui.navigation import (
    CATEGORY_START_INDEX,
    SCIENTIFIC_INFRASTRUCTURE_INDEX,
    SCIENTIFIC_INFRASTRUCTURE_LABEL,
    build_navigation_contract,
    build_top_level_labels,
    calculate_navigation_slices,
)


class NavigationContractTests(unittest.TestCase):
    def test_top_level_labels_include_only_overview_infrastructure_and_categories(self):
        labels = build_top_level_labels(
            overview_label="Visão geral",
            category_labels=["Agregadores", "Arquivos"],
            corpus_labels=["INA"],
            protocolled_labels=["Caso documentado"],
        )

        self.assertEqual(
            labels,
            [
                "Visão geral",
                SCIENTIFIC_INFRASTRUCTURE_LABEL,
                "Agregadores",
                "Arquivos",
            ],
        )
        self.assertNotIn("INA", labels)
        self.assertNotIn("Caso documentado", labels)

    def test_navigation_slices_end_after_category_tabs(self):
        slices = calculate_navigation_slices(category_total=3, corpus_total=5)

        self.assertEqual(slices.scientific_infrastructure_index, SCIENTIFIC_INFRASTRUCTURE_INDEX)
        self.assertEqual(slices.category_start, CATEGORY_START_INDEX)
        self.assertEqual(slices.category_stop, 5)
        self.assertEqual(slices.corpus_start, 5)
        self.assertEqual(slices.corpus_stop, 5)
        self.assertEqual(slices.protocolled_start, 5)

    def test_navigation_contract_uses_only_top_level_translation_keys(self):
        calls = []

        def tr_key(key, **kwargs):
            calls.append((key, kwargs))
            return kwargs.get("label", key)

        labels, slices = build_navigation_contract(
            tr_key=tr_key,
            category_definitions=[{"short_label": "Categoria A"}],
            corpus_definitions=[{"short_label": "Corpus A"}],
            protocolled_units=[{"unit_label": "Caso A"}],
        )

        self.assertEqual(
            labels,
            [
                "navigation.overview",
                SCIENTIFIC_INFRASTRUCTURE_LABEL,
                "Categoria A",
            ],
        )
        self.assertEqual(slices.category_start, 2)
        self.assertEqual(slices.category_stop, 3)
        self.assertEqual(slices.corpus_start, 3)
        self.assertEqual(slices.corpus_stop, 3)
        self.assertEqual(slices.protocolled_start, 3)
        self.assertEqual(
            calls,
            [
                ("navigation.overview", {}),
                ("navigation.category", {"label": "Categoria A"}),
            ],
        )

    def test_navigation_totals_cannot_be_negative(self):
        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            calculate_navigation_slices(category_total=-1, corpus_total=0)


if __name__ == "__main__":
    unittest.main()
