import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.europe_closure import EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME
from memoria_audiovisual.filmoteca_vaticana_protocol import (
    FILMOTECA_VATICANA_ACCESS_CATEGORY,
    FILMOTECA_VATICANA_PROTOCOL_FILENAME,
    build_filmoteca_vaticana_non_incorporated_register,
    build_filmoteca_vaticana_protocol_probe,
    write_filmoteca_vaticana_protocol_probe,
)


def fake_fetcher(probe):
    if probe.probe.startswith("official_dicastery_page"):
        text = (
            "Filmoteca Vaticana Vatican Film Library. The archive contains about 8,000 titles "
            "supported in acetate, magnetic and digital formats. Contact filmoteca.vaticana@spc.va."
        )
        status = 200
    elif probe.probe == "dicastery_video_gallery":
        text = (
            "Galleria video del Dicastero. Il Web Doc di Vatican News per il compleanno della "
            "Filmoteca Vaticana. <iframe src='https://www.youtube.com/embed/F6Nh1f_lOmY'></iframe>"
        )
        status = 200
    elif probe.probe == "vatican_news_webdoc":
        text = "Le origini della Filmoteca Vaticana. Web Doc editorial sobre a história da instituição."
        status = 200
    elif probe.probe == "youtube_playlist":
        text = "Filmoteca Vaticana - YouTube playlist Il Cinema dei Papi."
        status = 200
    else:
        text = "Search in the website 7 results found for Filmoteca Vaticana."
        status = 200
    return {
        "http_status": status,
        "final_url": probe.url,
        "content_type": "text/html",
        "content_length": "",
        "text": text,
        "error": "",
    }


class FilmotecaVaticanaProtocolTests(unittest.TestCase):
    def test_build_protocol_distinguishes_archive_from_editorial_videos(self):
        protocol_df = build_filmoteca_vaticana_protocol_probe(
            fetcher=fake_fetcher,
            evaluated_at="2026-07-16T00:00:00Z",
        )

        conclusions = protocol_df["protocol_conclusion"].tolist()
        self.assertEqual(len(protocol_df), 6)
        self.assertIn("acervo_filmico_confirmado_sem_catalogo_publico_de_video", conclusions)
        self.assertIn("videos_institucionais_sobre_a_filmoteca_nao_equivalem_ao_acervo", conclusions)
        self.assertIn("webdoc_editorial_sobre_a_filmoteca_nao_equivale_a_corpus", conclusions)
        self.assertIn("playlist_sobre_a_filmoteca_nao_equivale_a_catalogo_do_acervo", conclusions)

    def test_build_non_incorporated_register_explains_negative_decision(self):
        protocol_df = build_filmoteca_vaticana_protocol_probe(
            fetcher=fake_fetcher,
            evaluated_at="2026-07-16T00:00:00Z",
        )
        excluded_df = build_filmoteca_vaticana_non_incorporated_register(protocol_df)

        row = excluded_df.iloc[0]
        self.assertEqual(row["unit_code"], "fiaf-filmoteca-vaticana")
        self.assertEqual(row["access_category"], FILMOTECA_VATICANA_ACCESS_CATEGORY)
        self.assertIn("não incluído", row["public_status"])
        self.assertIn("8.000 títulos", row["negative_reason"])
        self.assertIn("vídeos institucionais sobre a Filmoteca", row["methodological_explanation"])
        self.assertFalse(bool(row["blocks_expansion"]))

    def test_write_protocol_updates_excluded_register(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            pd.DataFrame([{"unit_code": "archivegrid", "unit_label": "ArchiveGrid"}]).to_csv(
                output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
                index=False,
            )

            protocol_df = write_filmoteca_vaticana_protocol_probe(output_dir, fetcher=fake_fetcher)
            excluded_df = pd.read_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME)

            self.assertFalse(protocol_df.empty)
            self.assertTrue((output_dir / FILMOTECA_VATICANA_PROTOCOL_FILENAME).exists())
            self.assertIn("fiaf-filmoteca-vaticana", excluded_df["unit_code"].tolist())
            self.assertIn("archivegrid", excluded_df["unit_code"].tolist())


if __name__ == "__main__":
    unittest.main()
