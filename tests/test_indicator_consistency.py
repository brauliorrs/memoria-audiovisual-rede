import json
import unittest
from pathlib import Path

from memoria_audiovisual.scientific_infrastructure.indicator_consistency import (
    assert_consolidated_identity,
    compare_indicator_sources,
)


ROOT = Path(__file__).resolve().parents[1]


class IndicatorConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.canonical = json.loads(
            (ROOT / "data/templates/analytics/indicator_registry.json").read_text(
                encoding="utf-8"
            )
        )
        cls.legacy = json.loads(
            (ROOT / "data/templates/analytics/indicator_catalog.json").read_text(
                encoding="utf-8"
            )
        )
        cls.methodology = json.loads(
            (ROOT / "data/templates/analytics/methodology_registry.json").read_text(
                encoding="utf-8"
            )
        )

    def _report(self):
        return compare_indicator_sources(
            self.canonical["indicators"],
            self.legacy["indicators"],
            self.methodology["methodologies"],
        )

    def test_canonical_identity_matches_legacy_catalog(self):
        report = self._report()
        self.assertTrue(report.identity_is_consolidated)
        self.assertEqual(report.identity_divergences, ())
        assert_consolidated_identity(report)

    def test_nine_indicator_ids_are_preserved(self):
        report = self._report()
        self.assertEqual(len(report.canonical_ids), 9)
        self.assertEqual(report.canonical_ids, report.legacy_ids)

    def test_methodology_gap_is_explicit_and_not_silently_filled(self):
        report = self._report()
        self.assertEqual(
            report.missing_methodologies,
            ("audiovisual_archive_access_index",),
        )
        self.assertFalse(report.methodology_is_complete)
        self.assertEqual(report.orphan_methodologies, ())

    def test_identity_divergence_is_blocking(self):
        canonical = [dict(self.canonical["indicators"][0])]
        legacy = [dict(self.legacy["indicators"][0])]
        canonical[0]["title"] = "Título divergente"
        report = compare_indicator_sources(canonical, legacy, [])
        with self.assertRaisesRegex(ValueError, "divergência de identidade"):
            assert_consolidated_identity(report)


if __name__ == "__main__":
    unittest.main()
