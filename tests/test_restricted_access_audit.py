import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.atresmedia_protocol import ATRESMEDIA_ACCESS_CATEGORY
from memoria_audiovisual.europe_closure import EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME
from memoria_audiovisual.restricted_access_audit import (
    CINEMATHEQUE_SUISSE_NON_INCORPORATION_CATEGORY,
    CINETECA_ITALIANA_NON_INCORPORATION_CATEGORY,
    COMMERCIAL_LICENSING_CATEGORY,
    PAID_AUTHENTICATED_STREAMING_CATEGORY,
    RESTRICTED_ACCESS_AUDIT_FILENAME,
    RESTRICTED_ACCESS_SUMMARY_FILENAME,
    build_restricted_access_audit,
    build_restricted_access_summary,
    write_restricted_access_audit,
)


class RestrictedAccessAuditTests(unittest.TestCase):
    def test_build_restricted_access_audit_separates_private_bank_from_active_modalities(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            pd.DataFrame(
                [
                    {
                        "unit_code": "fiat-atresmedia",
                        "unit_label": "Atresmedia",
                        "access_category": ATRESMEDIA_ACCESS_CATEGORY,
                        "attempt_summary": "Portal comercial autenticado com licenciamento pago.",
                    },
                    {
                        "unit_code": "cinematheque-suisse",
                        "unit_label": "Cinémathèque suisse",
                        "access_category": CINEMATHEQUE_SUISSE_NON_INCORPORATION_CATEGORY,
                        "attempt_summary": "Metadados públicos via Memobase, mas mídia local/autorizada.",
                        "methodological_explanation": "Não há vídeo público incorporável ao corpus ativo.",
                    },
                    {
                        "unit_code": "fiaf-cineteca-italiana",
                        "unit_label": "Fondazione Cineteca Italiana",
                        "access_category": CINETECA_ITALIANA_NON_INCORPORATION_CATEGORY,
                        "attempt_summary": "Streaming protegido e canal institucional sem catálogo público de acervo.",
                        "methodological_explanation": "Não há catálogo público quantificável de vídeo de acervo.",
                    }
                ]
            ).to_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME, index=False)
            pd.DataFrame(
                [
                    {
                        "institution": "Institut national de l'audiovisuel (INA)",
                        "platform": "Mediaclip INA",
                        "video_title_display": "Catalogue d'archives vidéos à acheter",
                        "access_surface": "Catálogo comercial de licenciamento",
                    }
                ]
            ).to_csv(output_dir / "ina_catalogo_videos_analitico.csv", index=False)
            pd.DataFrame(
                [
                    {
                        "institution": "Arhiva Nationala de Filme",
                        "platform": "Eventbook",
                        "video_title_display": "CIULEANDRA",
                        "video_description": "Regime de acesso indicado: 12 RON, com compra/login.",
                        "access_surface": "Streaming pago/autenticado em plataforma externa",
                    },
                ]
            ).to_csv(output_dir / "anf_catalogo_videos_analitico.csv", index=False)

            audit_df = build_restricted_access_audit(output_dir)
            categories = set(audit_df["access_category"])

            self.assertIn(ATRESMEDIA_ACCESS_CATEGORY, categories)
            self.assertIn(COMMERCIAL_LICENSING_CATEGORY, categories)
            self.assertIn(CINEMATHEQUE_SUISSE_NON_INCORPORATION_CATEGORY, categories)
            self.assertIn(CINETECA_ITALIANA_NON_INCORPORATION_CATEGORY, categories)
            self.assertIn(PAID_AUTHENTICATED_STREAMING_CATEGORY, categories)
            private_row = audit_df.loc[audit_df["access_category"] == ATRESMEDIA_ACCESS_CATEGORY].iloc[0]
            self.assertTrue(bool(private_row["include_in_private_paid_bank_category"]))
            suisse_row = audit_df.loc[
                audit_df["access_category"] == CINEMATHEQUE_SUISSE_NON_INCORPORATION_CATEGORY
            ].iloc[0]
            self.assertEqual(suisse_row["corpus_status"], "fora_do_corpus_ativo")

    def test_build_restricted_access_summary_counts_units_and_records(self):
        audit_df = pd.DataFrame(
            [
                {
                    "unit_code": "ina",
                    "access_category": COMMERCIAL_LICENSING_CATEGORY,
                    "category_label": "Catálogo comercial de licenciamento em corpus ativo",
                    "total_records": 31,
                },
                {
                    "unit_code": "anf",
                    "access_category": PAID_AUTHENTICATED_STREAMING_CATEGORY,
                    "category_label": "Streaming pago/autenticado em corpus ativo",
                    "total_records": 8,
                },
                {
                    "unit_code": "cinematheque-suisse",
                    "access_category": CINEMATHEQUE_SUISSE_NON_INCORPORATION_CATEGORY,
                    "category_label": "Metadados públicos com mídia local/autorizada, sem vídeo público incorporável",
                    "total_records": "",
                },
                {
                    "unit_code": "fiaf-cineteca-italiana",
                    "access_category": CINETECA_ITALIANA_NON_INCORPORATION_CATEGORY,
                    "category_label": "Arquivo fílmico com streaming protegido, sem catálogo público de vídeo coletável",
                    "total_records": "",
                },
            ]
        )

        summary_df = build_restricted_access_summary(audit_df)

        records_by_category = dict(zip(summary_df["access_category"], summary_df["records"]))
        self.assertEqual(records_by_category[COMMERCIAL_LICENSING_CATEGORY], 31)
        self.assertEqual(records_by_category[PAID_AUTHENTICATED_STREAMING_CATEGORY], 8)
        self.assertEqual(records_by_category[CINEMATHEQUE_SUISSE_NON_INCORPORATION_CATEGORY], 0)
        self.assertEqual(records_by_category[CINETECA_ITALIANA_NON_INCORPORATION_CATEGORY], 0)

    def test_write_restricted_access_audit_materializes_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            pd.DataFrame(
                [
                    {
                        "unit_code": "fiat-atresmedia",
                        "unit_label": "Atresmedia",
                        "access_category": ATRESMEDIA_ACCESS_CATEGORY,
                        "attempt_summary": "Portal comercial autenticado com licenciamento pago.",
                    }
                ]
            ).to_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME, index=False)

            outputs = write_restricted_access_audit(output_dir)

            self.assertTrue((output_dir / RESTRICTED_ACCESS_AUDIT_FILENAME).exists())
            self.assertTrue((output_dir / RESTRICTED_ACCESS_SUMMARY_FILENAME).exists())
            self.assertFalse(outputs["audit"].empty)
            self.assertFalse(outputs["summary"].empty)


if __name__ == "__main__":
    unittest.main()
