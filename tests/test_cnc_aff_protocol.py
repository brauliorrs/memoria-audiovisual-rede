import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.cnc_aff_protocol import (
    CNCAFF_PROTOCOL_FILENAME,
    build_cnc_aff_non_incorporated_register,
    build_cnc_aff_protocol_probe,
    write_cnc_aff_protocol_probe,
)
from memoria_audiovisual.europe_closure import EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME


def fake_fetcher(url, method="GET"):
    if "direction-du-patrimoine" in url:
        return {
            "http_status": 200,
            "final_url": url,
            "content_type": "text/html",
            "content_length": "",
            "text": (
                "<html><body><h1>Direction du patrimoine cinématographique</h1>"
                "<p>Archives françaises du film, conservation, restauration, catalogage.</p>"
                "<p>Plus de 110 000 titres et catalogue en ligne.</p></body></html>"
            ),
            "error": "",
        }
    if "content/archives" in url:
        return {
            "http_status": 200,
            "final_url": url,
            "content_type": "text/html",
            "content_length": "",
            "text": "<html><body><p>View CNC collections on EFG.</p></body></html>",
            "error": "",
        }
    if "page=1" in url:
        return {
            "http_status": "",
            "final_url": url,
            "content_type": "",
            "content_length": "",
            "text": "",
            "error": "RemoteDisconnected",
        }
    if "search-efg" in url:
        return {
            "http_status": 200,
            "final_url": url,
            "content_type": "text/html",
            "content_length": "",
            "text": (
                "<html><body><h2>Videos (141 Results)</h2>"
                "<a href='/detail/Centre nationale du cinéma CNC/cnc::123'>Actuality film</a>"
                "</body></html>"
            ),
            "error": "",
        }
    if "cnc-aff.fr" in url:
        return {
            "http_status": "",
            "final_url": url,
            "content_type": "",
            "content_length": "",
            "text": "",
            "error": "NameResolutionError",
        }
    if "lise.cnc.fr" in url:
        return {
            "http_status": 503,
            "final_url": url,
            "content_type": "text/html",
            "content_length": "",
            "text": "<html><body><h1>Service Unavailable</h1></body></html>",
            "error": "",
        }
    return {
        "http_status": "",
        "final_url": url,
        "content_type": "",
        "content_length": "",
        "text": "",
        "error": "unexpected url",
    }


class CncAffProtocolTests(unittest.TestCase):
    def test_build_cnc_aff_protocol_documents_unstable_mediated_route(self):
        protocol_df = build_cnc_aff_protocol_probe(fetcher=fake_fetcher, evaluated_at="2026-06-17T00:00:00Z")

        self.assertEqual(len(protocol_df), 6)
        self.assertIn("pagina_oficial_confirma_arquivo_filmico", protocol_df["protocol_conclusion"].tolist())
        self.assertIn(
            "colecao_efg_identificada_com_resultados_video",
            protocol_df["protocol_conclusion"].tolist(),
        )
        self.assertIn("paginacao_efg_instavel_na_coleta_estatica", protocol_df["protocol_conclusion"].tolist())
        self.assertIn("dominio_legado_indisponivel_na_rodada", protocol_df["protocol_conclusion"].tolist())
        self.assertIn("catalogo_lise_indisponivel_na_rodada", protocol_df["protocol_conclusion"].tolist())

    def test_build_cnc_aff_non_incorporated_register_explains_negative_decision(self):
        protocol_df = build_cnc_aff_protocol_probe(fetcher=fake_fetcher, evaluated_at="2026-06-17T00:00:00Z")
        excluded_df = build_cnc_aff_non_incorporated_register(protocol_df)

        self.assertEqual(excluded_df.iloc[0]["unit_code"], "fiaf-cnc-aff")
        self.assertEqual(excluded_df.iloc[0]["access_category"], "rota_publica_mediada_instavel")
        self.assertIn("não incorporar", excluded_df.iloc[0]["methodological_decision"])
        self.assertIn("141 resultados", excluded_df.iloc[0]["attempt_summary"])
        self.assertIn("não ontológica", excluded_df.iloc[0]["methodological_explanation"])

    def test_write_cnc_aff_protocol_updates_excluded_register(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            pd.DataFrame(
                [
                    {
                        "unit_code": "archives-hub",
                        "unit_label": "Archives Hub",
                    }
                ]
            ).to_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME, index=False)

            protocol_df = write_cnc_aff_protocol_probe(output_dir, fetcher=fake_fetcher)
            excluded_df = pd.read_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME)

            self.assertFalse(protocol_df.empty)
            self.assertTrue((output_dir / CNCAFF_PROTOCOL_FILENAME).exists())
            self.assertIn("fiaf-cnc-aff", excluded_df["unit_code"].tolist())
            self.assertIn("archives-hub", excluded_df["unit_code"].tolist())


if __name__ == "__main__":
    unittest.main()
