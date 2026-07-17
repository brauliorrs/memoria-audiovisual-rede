import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.cinematheque_luxembourg_protocol import (
    CINEMATHEQUE_LUXEMBOURG_ACCESS_CATEGORY,
    CINEMATHEQUE_LUXEMBOURG_PROTOCOL_FILENAME,
    build_cinematheque_luxembourg_non_incorporated_register,
    build_cinematheque_luxembourg_protocol_probe,
    write_cinematheque_luxembourg_protocol_probe,
)
from memoria_audiovisual.europe_closure import EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME


def fake_fetcher(url, method="GET"):
    if "/api/film" in url:
        text = (
            '[{"title":"Leçon 06 - ÉCRANS","projection_date":"29/06/2026",'
            '"projection_time":"19:00","ticket_url":"https://shop.utick.net/?module=CATALOGUE",'
            '"location":"theatredescapucins"}]'
        )
        content_type = "application/json"
    elif "archives-collections" in url:
        text = (
            "Cinémathèque de la Ville de Luxembourg archives collections FIAF. "
            "20.038 copies de film conservées. Projecteur. "
            '<video><source src="https://tickets.cinematheque.lu/sites/default/files/2025-11/FRIGO.mp4" '
            'type="video/mp4"></video>'
        )
        content_type = "text/html"
    elif "programme" in url:
        text = "Programme projections billetterie ticket séances Théâtre des Capucins."
        content_type = "text/html"
    elif "search" in url:
        text = "Rechercher archives film programme."
        content_type = "text/html"
    elif "vdl.lu" in url:
        text = "La Cinémathèque préserve et valorise le patrimoine cinématographique international."
        content_type = "text/html"
    else:
        text = "Cinémathèque de la Ville de Luxembourg FIAF archives programmation cinéma."
        content_type = "text/html"
    return {
        "http_status": 200,
        "final_url": url,
        "content_type": content_type,
        "content_length": "",
        "text": text,
        "error": "",
    }


class CinemathequeLuxembourgProtocolTests(unittest.TestCase):
    def test_build_protocol_distinguishes_archive_from_screening_programme(self):
        protocol_df = build_cinematheque_luxembourg_protocol_probe(
            fetcher=fake_fetcher,
            evaluated_at="2026-06-19T00:00:00Z",
        )

        conclusions = protocol_df["protocol_conclusion"].tolist()
        self.assertEqual(len(protocol_df), 7)
        self.assertIn("acervo_filmico_confirmado_sem_catalogo_publico_de_video", conclusions)
        self.assertIn("api_publica_de_programacao_nao_equivale_a_catalogo_de_acervo", conclusions)
        self.assertIn("programacao_e_bilheteria_nao_equivalem_a_corpus_audiovisual", conclusions)
        self.assertIn("busca_do_site_nao_equivale_a_catalogo_arquivistico", conclusions)

    def test_build_non_incorporated_register_explains_programming_route(self):
        protocol_df = build_cinematheque_luxembourg_protocol_probe(
            fetcher=fake_fetcher,
            evaluated_at="2026-06-19T00:00:00Z",
        )
        excluded_df = build_cinematheque_luxembourg_non_incorporated_register(protocol_df)

        row = excluded_df.iloc[0]
        self.assertEqual(row["unit_code"], "fiaf-cinematheque-luxembourg")
        self.assertEqual(row["access_category"], CINEMATHEQUE_LUXEMBOURG_ACCESS_CATEGORY)
        self.assertIn("não incluído", row["public_status"])
        self.assertIn("programação pública", row["negative_reason"])
        self.assertIn("não nega a existência", row["methodological_explanation"])
        self.assertFalse(bool(row["blocks_expansion"]))

    def test_write_protocol_updates_excluded_register(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            pd.DataFrame([{"unit_code": "archivegrid", "unit_label": "ArchiveGrid"}]).to_csv(
                output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
                index=False,
            )

            protocol_df = write_cinematheque_luxembourg_protocol_probe(output_dir, fetcher=fake_fetcher)
            excluded_df = pd.read_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME)

            self.assertFalse(protocol_df.empty)
            self.assertTrue((output_dir / CINEMATHEQUE_LUXEMBOURG_PROTOCOL_FILENAME).exists())
            self.assertIn("fiaf-cinematheque-luxembourg", excluded_df["unit_code"].tolist())
            self.assertIn("archivegrid", excluded_df["unit_code"].tolist())


if __name__ == "__main__":
    unittest.main()
