"""Tests for fail-closed admission of MAR production analysis instruments."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.analysis_instruments import (
    InstrumentRegistryError,
    RUN_MANIFEST_FILENAME,
    load_instrument_registry,
    run_production_analysis,
    write_analysis_skipped_manifest,
)
from memoria_audiovisual.atresmedia_protocol import ATRESMEDIA_ACCESS_CATEGORY
from memoria_audiovisual.europe_closure import EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME


class AnalysisInstrumentRegistryTests(unittest.TestCase):
    def test_registry_admits_only_two_default_production_analyses(self):
        registry = load_instrument_registry()
        defaults = {
            spec.instrument_id
            for spec in registry.values()
            if spec.lifecycle == "production" and spec.default_cycle
        }
        self.assertEqual(
            defaults,
            {"restricted_access_audit", "public_access_index"},
        )
        self.assertEqual(registry["M3_surface_typing"].lifecycle, "experimental")
        self.assertEqual(
            registry["digital_infrastructure_evidence"].lifecycle,
            "evidence_capture_only",
        )

    def test_production_runner_rejects_experimental_and_unregistered_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(InstrumentRegistryError):
                run_production_analysis(
                    output_dir=Path(tmp),
                    requested=["M3_surface_typing"],
                )
            with self.assertRaises(InstrumentRegistryError):
                run_production_analysis(
                    output_dir=Path(tmp),
                    requested=["imaginary_tool"],
                )

    def test_global_analysis_requires_successful_full_refresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(InstrumentRegistryError):
                run_production_analysis(
                    output_dir=Path(tmp),
                    source_cycle_status="successful_partial_refresh",
                )

    def test_default_production_analyses_materialize_outputs_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            pd.DataFrame(
                [
                    {
                        "institution": "Synthetic Archive",
                        "continent": "Europe",
                        "access_surface": "Outra superfície de acesso",
                        "video_title_display": "Public item",
                    },
                    {
                        "institution": "Synthetic Archive",
                        "continent": "Europe",
                        "access_surface": "Catálogo comercial de licenciamento",
                        "video_title_display": "Restricted item",
                    },
                ]
            ).to_csv(output / "ina_catalogo_videos_analitico.csv", index=False)
            pd.DataFrame(
                [
                    {
                        "unit_code": "fiat-atresmedia",
                        "unit_label": "Atresmedia",
                        "territorial_scope": "Espanha",
                        "access_category": ATRESMEDIA_ACCESS_CATEGORY,
                        "attempt_summary": "Synthetic private commercial portal.",
                    }
                ]
            ).to_csv(output / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME, index=False)

            manifest = run_production_analysis(output_dir=output)

            self.assertEqual(manifest["status"], "success")
            self.assertEqual(
                [row["instrument_id"] for row in manifest["instruments"]],
                ["restricted_access_audit", "public_access_index"],
            )
            saved = json.loads((output / RUN_MANIFEST_FILENAME).read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "success")
            self.assertTrue((output / "observatorio_auditoria_acesso_pago_restrito.csv").is_file())
            self.assertTrue((output / "observatorio_indice_dados_publicos.csv").is_file())

    def test_skipped_manifest_makes_partial_cycle_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            manifest = write_analysis_skipped_manifest(
                "Partial refresh",
                output_dir=output,
                source_cycle_status="successful_partial_refresh",
            )
            self.assertEqual(manifest["status"], "skipped")
            self.assertEqual(manifest["instruments"], [])
            saved = json.loads((output / RUN_MANIFEST_FILENAME).read_text(encoding="utf-8"))
            self.assertEqual(saved["reason"], "Partial refresh")


if __name__ == "__main__":
    unittest.main()
