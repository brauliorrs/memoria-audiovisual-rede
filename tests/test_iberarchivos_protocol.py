import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.europe_closure import EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME
from memoria_audiovisual.iberarchivos_protocol import (
    IBERARCHIVOS_PROTOCOL_FILENAME,
    build_iberarchivos_non_incorporated_register,
    build_iberarchivos_protocol_probe,
    write_iberarchivos_protocol_probe,
)


class IberarchivosProtocolTests(unittest.TestCase):
    def test_build_iberarchivos_protocol_detects_contextual_audiovisual_signals(self):
        def fake_fetcher(url, method="GET"):
            return {
                "http_status": 200,
                "final_url": url,
                "content_type": "text/html",
                "content_length": "",
                "text": "Observatorio de políticas archivísticas con projeto audiovisual e acervo de video.",
                "error": "",
            }

        protocol_df = build_iberarchivos_protocol_probe(
            fetcher=fake_fetcher,
            evaluated_at="2026-05-20T00:00:00Z",
        )

        self.assertFalse(protocol_df.empty)
        self.assertIn(
            "observatorio_de_politicas_confirmado_sem_catalogo_audiovisual_coletavel",
            protocol_df["protocol_conclusion"].tolist(),
        )
        self.assertIn(
            "sinais_audiovisuais_contextuais_detectados_sem_rota_de_acervo",
            protocol_df["protocol_conclusion"].tolist(),
        )

    def test_build_iberarchivos_non_incorporated_register_keeps_radar_separate(self):
        protocol_df = build_iberarchivos_protocol_probe(
            fetcher=lambda url, method="GET": {
                "http_status": 200,
                "final_url": url,
                "content_type": "text/html",
                "content_length": "",
                "text": "audiovisual video",
                "error": "",
            },
            evaluated_at="2026-05-20T00:00:00Z",
        )

        excluded_df = build_iberarchivos_non_incorporated_register(protocol_df)

        self.assertEqual(excluded_df.iloc[0]["unit_code"], "iberarchivos")
        self.assertEqual(excluded_df.iloc[0]["unit_type"], "fonte_de_radar")
        self.assertIn("fonte estratégica", excluded_df.iloc[0]["public_status"])
        self.assertFalse(bool(excluded_df.iloc[0]["blocks_expansion"]))

    def test_write_iberarchivos_protocol_probe_updates_protocol_and_register(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)

            write_iberarchivos_protocol_probe(
                output_dir,
                fetcher=lambda url, method="GET": {
                    "http_status": 200,
                    "final_url": url,
                    "content_type": "text/html",
                    "content_length": "",
                    "text": "audiovisual video",
                    "error": "",
                },
            )

            self.assertTrue((output_dir / IBERARCHIVOS_PROTOCOL_FILENAME).exists())
            self.assertTrue((output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME).exists())


if __name__ == "__main__":
    unittest.main()
