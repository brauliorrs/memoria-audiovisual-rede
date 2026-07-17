import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.europe_closure import EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME
from memoria_audiovisual.puy_de_dome_protocol import (
    PUY_DE_DOME_ACCESS_CATEGORY,
    PUY_DE_DOME_PROTOCOL_FILENAME,
    build_puy_de_dome_non_incorporated_register,
    build_puy_de_dome_protocol_probe,
    write_puy_de_dome_protocol_probe,
)


def fake_fetcher(url, method="GET"):
    if "inedits.eu" in url:
        text = "Website unavailable - OVHcloud"
        status = 503
    elif "robots.txt" in url:
        text = "User-agent: *\nSitemap: http://www.archivesdepartementales.puydedome.fr/sitemap/contenus.xml"
        status = 200
    else:
        text = (
            "<html><head><title>Vérification que vous n'êtes pas un robot !</title>"
            "<meta name='robots' content='noindex,nofollow'><link href='/.within.website/x/xess/xess.min.css'>"
            "</head><body>Vérification que vous n'êtes pas un robot !</body></html>"
        )
        status = 200
    return {
        "http_status": status,
        "final_url": url,
        "content_type": "text/html",
        "content_length": "",
        "text": text,
        "error": "",
    }


class PuyDeDomeProtocolTests(unittest.TestCase):
    def test_build_protocol_documents_antirobot_barrier(self):
        protocol_df = build_puy_de_dome_protocol_probe(
            fetcher=fake_fetcher,
            evaluated_at="2026-07-07T00:00:00Z",
        )

        conclusions = protocol_df["protocol_conclusion"].tolist()
        self.assertEqual(len(protocol_df), 7)
        self.assertIn("rota_oficial_bloqueada_por_verificacao_antirobo", conclusions)
        self.assertIn("robots_txt_indica_sitemap_publico", conclusions)
        self.assertIn("referencia_inedits_indisponivel_na_rodada", conclusions)

    def test_build_non_incorporated_register_explains_negative(self):
        protocol_df = build_puy_de_dome_protocol_probe(
            fetcher=fake_fetcher,
            evaluated_at="2026-07-07T00:00:00Z",
        )
        excluded_df = build_puy_de_dome_non_incorporated_register(protocol_df)

        row = excluded_df.iloc[0]
        self.assertEqual(row["unit_code"], "inedits-county-archives-puy-de-dome")
        self.assertEqual(row["access_category"], PUY_DE_DOME_ACCESS_CATEGORY)
        self.assertIn("não incluído", row["public_status"])
        self.assertIn("anti-robô", row["negative_reason"])
        self.assertIn("não nega a existência", row["methodological_explanation"])
        self.assertFalse(bool(row["blocks_expansion"]))

    def test_write_protocol_updates_excluded_register(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            pd.DataFrame([{"unit_code": "archivegrid", "unit_label": "ArchiveGrid"}]).to_csv(
                output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
                index=False,
            )

            protocol_df = write_puy_de_dome_protocol_probe(output_dir, fetcher=fake_fetcher)
            excluded_df = pd.read_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME)

            self.assertFalse(protocol_df.empty)
            self.assertTrue((output_dir / PUY_DE_DOME_PROTOCOL_FILENAME).exists())
            self.assertIn("inedits-county-archives-puy-de-dome", excluded_df["unit_code"].tolist())
            self.assertIn("archivegrid", excluded_df["unit_code"].tolist())


if __name__ == "__main__":
    unittest.main()
