import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.atresmedia_protocol import ATRESMEDIA_ACCESS_CATEGORY
from memoria_audiovisual.europe_closure import EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME
from memoria_audiovisual.public_access_index import (
    PUBLIC_ACCESS_INDEX_BY_CORPUS_FILENAME,
    PUBLIC_ACCESS_INDEX_FILENAME,
    PUBLIC_ACCESS_RESTRICTED_UNITS_FILENAME,
    build_public_access_index,
    write_public_access_index,
)


class PublicAccessIndexTests(unittest.TestCase):
    def _write_fixture(self, output_dir):
        pd.DataFrame(
            [
                {
                    "institution": "INA",
                    "continent": "Europe",
                    "access_surface": "Streaming curatorial",
                    "video_title_display": "Open stream",
                },
                {
                    "institution": "INA",
                    "continent": "Europe",
                    "access_surface": "Catálogo comercial de licenciamento",
                    "video_title_display": "Licensing catalog",
                },
            ]
        ).to_csv(output_dir / "ina_catalogo_videos_analitico.csv", index=False)
        pd.DataFrame(
            [
                {
                    "institution": "ANF",
                    "continent": "Europe",
                    "access_surface": "Streaming pago/autenticado em plataforma externa",
                    "video_description": "Regime de acesso indicado: 12 RON, com compra/login.",
                }
            ]
        ).to_csv(output_dir / "anf_catalogo_videos_analitico.csv", index=False)
        pd.DataFrame(
            [
                {
                    "institution": "AAPB",
                    "continent": "North America",
                    "access_surface": "acesso em agregador audiovisual",
                    "video_title_display": "Public API item",
                }
            ]
        ).to_csv(output_dir / "aapb_catalogo_videos_analitico.csv", index=False)
        pd.DataFrame(
            [
                {
                    "unit_code": "fiat-atresmedia",
                    "unit_label": "Atresmedia",
                    "territorial_scope": "Espanha",
                    "access_category": ATRESMEDIA_ACCESS_CATEGORY,
                    "attempt_summary": "Portal comercial autenticado com licenciamento pago.",
                }
            ]
        ).to_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME, index=False)

    def test_build_public_access_index_counts_public_restricted_and_excludes_private_banks(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            self._write_fixture(output_dir)

            outputs = build_public_access_index(output_dir)
            index_df = outputs["index"]
            restricted_units_df = outputs["restricted_units"]

            world = index_df.loc[index_df["scope"] == "World"].iloc[0]
            europe = index_df.loc[index_df["scope"] == "Europe"].iloc[0]
            north_america = index_df.loc[index_df["scope"] == "North America"].iloc[0]

            self.assertEqual(world["public_records"], 2)
            self.assertEqual(world["restricted_records"], 2)
            self.assertEqual(europe["public_records"], 1)
            self.assertEqual(europe["restricted_records"], 2)
            self.assertEqual(europe["restricted_units_without_public_catalog"], 0)
            self.assertEqual(europe["restricted_units_total"], 2)
            self.assertEqual(north_america["public_records"], 1)
            self.assertNotIn("fiat-atresmedia", restricted_units_df["unit_code"].tolist())

    def test_write_public_access_index_materializes_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            self._write_fixture(output_dir)

            outputs = write_public_access_index(output_dir)

            self.assertTrue((output_dir / PUBLIC_ACCESS_INDEX_FILENAME).exists())
            self.assertTrue((output_dir / PUBLIC_ACCESS_INDEX_BY_CORPUS_FILENAME).exists())
            self.assertTrue((output_dir / PUBLIC_ACCESS_RESTRICTED_UNITS_FILENAME).exists())
            self.assertFalse(outputs["index"].empty)
            self.assertFalse(outputs["by_corpus"].empty)


if __name__ == "__main__":
    unittest.main()
