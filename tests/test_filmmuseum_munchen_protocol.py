import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.europe_closure import EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME
from memoria_audiovisual.filmmuseum_munchen_protocol import (
    FILMMUSEUM_MUNCHEN_ACCESS_CATEGORY,
    FILMMUSEUM_MUNCHEN_PROTOCOL_FILENAME,
    build_filmmuseum_munchen_non_incorporated_register,
    build_filmmuseum_munchen_protocol_probe,
    write_filmmuseum_munchen_protocol_probe,
)


def fake_fetcher(probe):
    if probe.probe == "history_page":
        text = (
            "Filmmuseum München Geschichte. Das Archiv des Filmmuseums umfasst etwa 6000 Kopien, "
            "Klassiker der Filmgeschichte und rekonstruierte Stummfilme."
        )
        status = 200
    elif probe.probe in {"current_programme", "film_series"}:
        text = "Spielplan Tickets Vorführungen Eintritt Kinokasse Musikbegleitung Retrospektiven Filmreihen."
        status = 200
    elif probe.probe == "museum_videos_page":
        text = (
            "Münchner Stadtmuseum Videos. Erst wenn Sie zustimmen, erlauben Sie uns Daten von Youtube zu laden. "
            '<iframe src="https://www.youtube-nocookie.com/embed/test"></iframe>'
        )
        status = 200
    elif probe.probe == "collection_online_home":
        text = "Sammlung Online des Münchner Stadtmuseums tx_so_displayso Objekte Fotografie Mode Reklamekunst."
        status = 200
    elif probe.probe == "collection_online_film_search":
        text = "Internal Server Error"
        status = 500
    else:
        text = "Filmmuseum München täglich wechselndes Programm Retrospektiven Filmreihen."
        status = 200
    return {
        "http_status": status,
        "final_url": probe.url,
        "content_type": "text/html",
        "content_length": "",
        "text": text,
        "error": "",
    }


class FilmmuseumMunchenProtocolTests(unittest.TestCase):
    def test_build_protocol_distinguishes_archive_from_programming_and_general_videos(self):
        protocol_df = build_filmmuseum_munchen_protocol_probe(
            fetcher=fake_fetcher,
            evaluated_at="2026-07-16T00:00:00Z",
        )

        conclusions = protocol_df["protocol_conclusion"].tolist()
        self.assertEqual(len(protocol_df), 7)
        self.assertIn("acervo_filmico_confirmado_sem_catalogo_publico_de_video", conclusions)
        self.assertIn("programacao_de_sala_nao_equivale_a_corpus_audiovisual", conclusions)
        self.assertIn("videos_institucionais_do_museu_nao_equivalem_ao_acervo_do_filmmuseum", conclusions)
        self.assertIn("busca_sammlung_online_instavel_nao_promove_corpus", conclusions)

    def test_build_non_incorporated_register_explains_negative_decision(self):
        protocol_df = build_filmmuseum_munchen_protocol_probe(
            fetcher=fake_fetcher,
            evaluated_at="2026-07-16T00:00:00Z",
        )
        excluded_df = build_filmmuseum_munchen_non_incorporated_register(protocol_df)

        row = excluded_df.iloc[0]
        self.assertEqual(row["unit_code"], "fiaf-filmmuseum-munchen")
        self.assertEqual(row["access_category"], FILMMUSEUM_MUNCHEN_ACCESS_CATEGORY)
        self.assertIn("não incluído", row["public_status"])
        self.assertIn("programação de sessões", row["negative_reason"])
        self.assertIn("não nega a existência", row["methodological_explanation"])
        self.assertFalse(bool(row["blocks_expansion"]))

    def test_write_protocol_updates_excluded_register(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            pd.DataFrame([{"unit_code": "archivegrid", "unit_label": "ArchiveGrid"}]).to_csv(
                output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
                index=False,
            )

            protocol_df = write_filmmuseum_munchen_protocol_probe(output_dir, fetcher=fake_fetcher)
            excluded_df = pd.read_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME)

            self.assertFalse(protocol_df.empty)
            self.assertTrue((output_dir / FILMMUSEUM_MUNCHEN_PROTOCOL_FILENAME).exists())
            self.assertIn("fiaf-filmmuseum-munchen", excluded_df["unit_code"].tolist())
            self.assertIn("archivegrid", excluded_df["unit_code"].tolist())


if __name__ == "__main__":
    unittest.main()
