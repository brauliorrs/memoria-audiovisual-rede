from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.analytics.catalog import IndicatorCatalog
from memoria_audiovisual.analytics.pipeline import default_indicator_registry


class IndicatorCatalogTests(unittest.TestCase):
    def test_official_catalog_explains_all_registered_indicators(self) -> None:
        catalog = IndicatorCatalog.load(
            "data/templates/analytics/indicator_registry.json"
        )
        catalog.validate_registry(default_indicator_registry())
        self.assertEqual(len(catalog.entries), len(default_indicator_registry()))

    def test_rejects_entry_without_selection_rationale(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "registry.json"
            path.write_text(json.dumps({
                "registry_version": "1.0.0",
                "indicators": [{
                    "indicator_id": "x",
                    "indicator_version": "1.0.0",
                    "title": "X",
                    "scientific_question": "Pergunta?",
                    "selection_rationale": "",
                    "dimension": "test",
                    "interpretation": "Interpretação",
                    "does_not_measure": ["algo"],
                    "relationship_to_other_indicators": "Relação",
                    "methodology_reference": "registry#x"
                }]
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "selection_rationale"):
                IndicatorCatalog.load(path)

    def test_rejects_registered_indicator_without_catalog_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "registry.json"
            path.write_text(json.dumps({
                "registry_version": "1.0.0",
                "indicators": [{
                    "indicator_id": "api_coverage",
                    "indicator_version": "1.0.0",
                    "title": "API",
                    "scientific_question": "Pergunta?",
                    "selection_rationale": "Justificativa",
                    "dimension": "infrastructure",
                    "interpretation": "Interpretação",
                    "does_not_measure": ["qualidade"],
                    "relationship_to_other_indicators": "Relação",
                    "methodology_reference": "registry#api_coverage"
                }]
            }), encoding="utf-8")
            catalog = IndicatorCatalog.load(path)
            with self.assertRaisesRegex(ValueError, "sem explicação"):
                catalog.validate_registry(default_indicator_registry())


if __name__ == "__main__":
    unittest.main()
