import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.adlibitum_protocol import (
    ADLIBITUM_PROTOCOL_FILENAME,
    build_adlibitum_non_incorporated_register,
    build_adlibitum_protocol_probe,
    write_adlibitum_protocol_probe,
)
from memoria_audiovisual.europe_closure import EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME


def fake_fetcher(url, method="GET"):
    if "saintmarcellin" in url:
        return {
            "http_status": "",
            "final_url": url,
            "content_type": "",
            "content_length": "",
            "text": "",
            "error": "Connection timed out",
        }
    if "online-archives" in url:
        return {
            "http_status": 200,
            "final_url": url,
            "content_type": "text/html",
            "content_length": "",
            "text": "<html><body><h1>Online Archives</h1><p>Other film archives online.</p></body></html>",
            "error": "",
        }
    return {
        "http_status": 200,
        "final_url": url,
        "content_type": "text/html",
        "content_length": "",
        "text": (
            "<html><body><h1>Ad Libitum Workshop</h1>"
            "<p>collect, preserve, restore and promote public and private films and audiovisual archives</p>"
            "</body></html>"
        ),
        "error": "",
    }


class AdLibitumProtocolTests(unittest.TestCase):
    def test_build_adlibitum_protocol_documents_unstable_route(self):
        protocol_df = build_adlibitum_protocol_probe(fetcher=fake_fetcher, evaluated_at="2026-05-29T00:00:00Z")

        self.assertEqual(len(protocol_df), 5)
        self.assertIn("site_oficial_indisponivel_na_rodada", protocol_df["protocol_conclusion"].tolist())
        self.assertIn(
            "referencia_institucional_confirma_arquivo_sem_catalogo_publico",
            protocol_df["protocol_conclusion"].tolist(),
        )
        self.assertIn("indice_inedits_acessivel_sem_adlibitum", protocol_df["protocol_conclusion"].tolist())

    def test_build_adlibitum_non_incorporated_register_explains_decision(self):
        protocol_df = build_adlibitum_protocol_probe(fetcher=fake_fetcher, evaluated_at="2026-05-29T00:00:00Z")
        excluded_df = build_adlibitum_non_incorporated_register(protocol_df)

        self.assertEqual(excluded_df.iloc[0]["unit_code"], "inedits-ad-libitum")
        self.assertIn("não incluído", excluded_df.iloc[0]["public_status"])
        self.assertIn("catálogo público", excluded_df.iloc[0]["negative_reason"])
        self.assertIn("não equivale à ausência", excluded_df.iloc[0]["methodological_explanation"])

    def test_write_adlibitum_protocol_updates_excluded_register(self):
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

            protocol_df = write_adlibitum_protocol_probe(output_dir, fetcher=fake_fetcher)
            excluded_df = pd.read_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME)

            self.assertFalse(protocol_df.empty)
            self.assertTrue((output_dir / ADLIBITUM_PROTOCOL_FILENAME).exists())
            self.assertIn("inedits-ad-libitum", excluded_df["unit_code"].tolist())
            self.assertIn("archives-hub", excluded_df["unit_code"].tolist())


if __name__ == "__main__":
    unittest.main()
