import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.cineteca_italiana_protocol import (
    CINETECA_ITALIANA_ACCESS_CATEGORY,
    CINETECA_ITALIANA_PROTOCOL_FILENAME,
    build_cineteca_italiana_non_incorporated_register,
    build_cineteca_italiana_protocol_probe,
    write_cineteca_italiana_protocol_probe,
)
from memoria_audiovisual.europe_closure import EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME


def fake_fetcher(probe):
    if probe.probe == "about_archive":
        text = "Cineteca Milano conserva un archivio di oltre 40.000 titoli di film in pellicola."
    elif probe.probe == "restoration_lab":
        text = "Laboratorio di restauro film, digitalizzazione e conservazione."
    elif probe.probe in {"film_programming_archive", "film_rest_api"}:
        text = "Archivio Film in programmazione nelle sale. Acquista biglietti per le proiezioni."
    elif probe.probe == "streaming_account_page":
        text = "Streaming - Ecco i contenuti in streaming che hai acquistato nel mio-account."
    elif probe.probe == "streaming_rest_api":
        text = '[{"type":"streaming","slug":"persepolis","content":{"protected":true,"rendered":""}}]'
    elif probe.probe == "guided_archive_visit":
        text = "Visita guidata all'Archivio Film a 15 metri sotto terra con realtà aumentata."
    elif probe.probe == "youtube_rss":
        text = "<feed><title>Cineteca Milano</title><entry><title>Trailer</title></entry></feed>"
    elif probe.probe == "the_film_corner_register":
        text = "The Film Corner register interactive film and audiovisual literacy educational platform."
    else:
        text = "Cineteca Milano Fondazione Cineteca Italiana."
    return {
        "http_status": 200,
        "final_url": probe.url,
        "content_type": "text/html",
        "content_length": "",
        "text": text,
        "error": "",
    }


class CinetecaItalianaProtocolTests(unittest.TestCase):
    def test_build_protocol_distinguishes_archive_from_protected_streaming_and_channel(self):
        protocol_df = build_cineteca_italiana_protocol_probe(
            fetcher=fake_fetcher,
            evaluated_at="2026-07-17T00:00:00Z",
        )

        conclusions = protocol_df["protocol_conclusion"].tolist()
        self.assertEqual(len(protocol_df), 10)
        self.assertIn("acervo_filmico_confirmado_sem_catalogo_publico_de_video", conclusions)
        self.assertIn("programacao_de_sala_nao_equivale_a_corpus_audiovisual", conclusions)
        self.assertIn("api_streaming_expoe_registros_protegidos_sem_conteudo_publico", conclusions)
        self.assertIn("canal_youtube_publico_detectado_sem_catalogo_de_acervo", conclusions)
        self.assertIn("plataforma_educativa_com_registro_nao_equivale_a_catalogo_publico_do_acervo", conclusions)

    def test_build_non_incorporated_register_explains_negative_decision(self):
        protocol_df = build_cineteca_italiana_protocol_probe(
            fetcher=fake_fetcher,
            evaluated_at="2026-07-17T00:00:00Z",
        )
        excluded_df = build_cineteca_italiana_non_incorporated_register(protocol_df)

        row = excluded_df.iloc[0]
        self.assertEqual(row["unit_code"], "fiaf-cineteca-italiana")
        self.assertEqual(row["access_category"], CINETECA_ITALIANA_ACCESS_CATEGORY)
        self.assertIn("não incluída", row["public_status"])
        self.assertIn("streaming protegido", row["negative_reason"])
        self.assertIn("não nega a existência", row["methodological_explanation"])
        self.assertFalse(bool(row["blocks_expansion"]))

    def test_write_protocol_updates_excluded_register(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            pd.DataFrame([{"unit_code": "archivegrid", "unit_label": "ArchiveGrid"}]).to_csv(
                output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
                index=False,
            )

            protocol_df = write_cineteca_italiana_protocol_probe(output_dir, fetcher=fake_fetcher)
            excluded_df = pd.read_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME)

            self.assertFalse(protocol_df.empty)
            self.assertTrue((output_dir / CINETECA_ITALIANA_PROTOCOL_FILENAME).exists())
            self.assertIn("fiaf-cineteca-italiana", excluded_df["unit_code"].tolist())
            self.assertIn("archivegrid", excluded_df["unit_code"].tolist())


if __name__ == "__main__":
    unittest.main()
