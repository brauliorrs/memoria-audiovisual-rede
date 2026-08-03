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
    def test_top_level_labels_keep_scientific_infrastructure_after_overview(self):
        labels = build_top_level_labels(
            overview_label="Visão geral",
            category_labels=["Agregadores"],
            corpus_labels=["INA"],
            protocolled_labels=["Caso documentado"],
        )

        self.assertEqual(
            labels,
            [
                "Visão geral",
                SCIENTIFIC_INFRASTRUCTURE_LABEL,
                "Agregadores",
                "INA",
                "Caso documentado",
            ],
        )

    def test_navigation_slices_start_categories_after_scientific_infrastructure(self):
        slices = calculate_navigation_slices(category_total=3, corpus_total=5)

        self.assertEqual(slices.scientific_infrastructure_index, SCIENTIFIC_INFRASTRUCTURE_INDEX)
        self.assertEqual(slices.category_start, CATEGORY_START_INDEX)
        self.assertEqual(slices.category_stop, 5)
        self.assertEqual(slices.corpus_start, 5)
        self.assertEqual(slices.corpus_stop, 10)
        self.assertEqual(slices.protocolled_start, 10)

    def test_navigation_contract_uses_existing_translation_keys(self):
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
                "Corpus A",
                "Caso A",
            ],
        )
        self.assertEqual(slices.category_start, 2)
        self.assertEqual(
            calls,
            [
                ("navigation.overview", {}),
                ("navigation.category", {"label": "Categoria A"}),
                ("navigation.unit", {"label": "Corpus A"}),
                ("navigation.documented_case", {"label": "Caso A"}),
            ],
        )

    def test_navigation_totals_cannot_be_negative(self):
        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            calculate_navigation_slices(category_total=-1, corpus_total=0)


if __name__ == "__main__":
    unittest.main()
