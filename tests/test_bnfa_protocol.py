import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.bnfa_protocol import (
    BNFA_PROTOCOL_FILENAME,
    build_bnfa_non_incorporated_register,
    build_bnfa_protocol_probe,
    write_bnfa_protocol_probe,
)
from memoria_audiovisual.europe_closure import EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME


def fake_fetcher(url, method="GET", payload=None):
    if url.startswith("https://bnf.bg"):
        return {
            "http_status": "",
            "final_url": url,
            "content_type": "",
            "content_length": "",
            "text": "",
            "error": "SSL wrong version number",
        }
    if "movie_fund" in url:
        text = (
            "The Bulgarian Film Archive holds the national film archive, which consists of "
            "15 000 titles with more than 40 000 copies or 300 000 film reels. "
            "The Archive also holds more than 3000 videotapes."
        )
    elif "/bg/archive/" in url:
        text = "Българска национална филмотека е-Каталог Тази страница е в процес на разработка."
    elif "/en/archive/" in url:
        text = "Bulgarian National Film Archive e-Catalogue"
    elif "/en/search/" in url:
        text = "Bulgarian National Film Archive Search The page is not available."
    elif "partners_contributors" in url:
        text = "View BNFA Collection on EFG. The Bulgarian National Film Archive is home to more than 15,000 film titles."
    elif "search-efg/bnfa" in url:
        text = "Videos (168 Results) Provider Bulgarian National Film Archive (168) Details"
    else:
        text = "Bulgarian National Film Archive film heritage film archive"
    return {
        "http_status": 200,
        "final_url": url,
        "content_type": "text/html",
        "content_length": "",
        "text": text,
        "error": "",
    }


class BnfaProtocolTests(unittest.TestCase):
    def test_build_bnfa_protocol_confirms_public_efg_video_collection(self):
        protocol_df = build_bnfa_protocol_probe(fetcher=fake_fetcher, evaluated_at="2026-06-15T00:00:00Z")

        self.assertEqual(len(protocol_df), 9)
        conclusions = protocol_df["protocol_conclusion"].tolist()
        self.assertIn("https_indisponivel_http_precisa_ser_testado", conclusions)
        self.assertIn("acervo_filmico_confirmado_sem_video_publico_coletavel", conclusions)
        self.assertIn("catalogo_publico_indisponivel_ou_em_desenvolvimento", conclusions)
        self.assertIn("colecao_publica_efg_com_resultados_video_confirmada", conclusions)
        efg_row = protocol_df.loc[protocol_df["probe"] == "efg_collection_link"].iloc[0]
        self.assertIn("efg_videos=168", efg_row["observed_value"])
        self.assertFalse(protocol_df["observed_value"].astype(str).str.contains("arquivos_video=[1-9]", regex=True).any())

    def test_build_bnfa_non_incorporated_register_stays_empty_when_efg_route_is_confirmed(self):
        protocol_df = build_bnfa_protocol_probe(fetcher=fake_fetcher, evaluated_at="2026-06-15T00:00:00Z")
        excluded_df = build_bnfa_non_incorporated_register(protocol_df)

        self.assertTrue(excluded_df.empty)

    def test_write_bnfa_protocol_updates_excluded_register(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            pd.DataFrame(
                [
                    {"unit_code": "archives-hub", "unit_label": "Archives Hub"},
                    {"unit_code": "fiaf-bulgarian-national-film-archive", "unit_label": "Bulgarian National Film Archive"},
                ]
            ).to_csv(
                output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
                index=False,
            )

            protocol_df = write_bnfa_protocol_probe(output_dir, fetcher=fake_fetcher)
            excluded_df = pd.read_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME)

            self.assertFalse(protocol_df.empty)
            self.assertTrue((output_dir / BNFA_PROTOCOL_FILENAME).exists())
            self.assertNotIn("fiaf-bulgarian-national-film-archive", excluded_df["unit_code"].tolist())
            self.assertIn("archives-hub", excluded_df["unit_code"].tolist())


if __name__ == "__main__":
    unittest.main()
