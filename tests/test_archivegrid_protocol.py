import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.archivegrid_protocol import (
    ARCHIVEGRID_PROTOCOL_FILENAME,
    build_archivegrid_non_incorporated_register,
    build_archivegrid_protocol_probe,
    write_archivegrid_protocol_probe,
)
from memoria_audiovisual.europe_closure import EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME


class ArchiveGridProtocolTests(unittest.TestCase):
    def test_build_archivegrid_protocol_probe_classifies_blocked_search(self):
        def fake_fetcher(url, method="GET"):
            if "oclc.org/research" in url:
                return {
                    "http_status": 200,
                    "final_url": url,
                    "content_type": "text/html",
                    "content_length": "",
                    "text": "ArchiveGrid is a collection of millions of archival material descriptions.",
                    "error": "",
                }
            return {
                "http_status": 403,
                "final_url": url,
                "content_type": "text/html; charset=UTF-8",
                "content_length": "",
                "text": "Just a moment... enable JavaScript and cookies",
                "error": "",
            }

        protocol_df = build_archivegrid_protocol_probe(fetcher=fake_fetcher, evaluated_at="2026-05-20T00:00:00Z")

        self.assertFalse(protocol_df.empty)
        self.assertIn("busca_publica_bloqueada_na_sondagem_simples", protocol_df["protocol_conclusion"].tolist())
        self.assertIn(
            "referencia_institucional_confirma_agregador_mundial",
            protocol_df["protocol_conclusion"].tolist(),
        )

    def test_build_archivegrid_non_incorporated_register_explains_decision(self):
        protocol_df = build_archivegrid_protocol_probe(
            fetcher=lambda url, method="GET": {
                "http_status": 403,
                "final_url": url,
                "content_type": "text/html",
                "content_length": "",
                "text": "Just a moment...",
                "error": "",
            },
            evaluated_at="2026-05-20T00:00:00Z",
        )

        excluded_df = build_archivegrid_non_incorporated_register(protocol_df)

        self.assertEqual(excluded_df.iloc[0]["unit_code"], "archivegrid")
        self.assertIn("não incluída no corpus", excluded_df.iloc[0]["public_status"])
        self.assertIn("agregador mundial", excluded_df.iloc[0]["territorial_scope"])
        self.assertFalse(bool(excluded_df.iloc[0]["blocks_expansion"]))

    def test_write_archivegrid_protocol_probe_updates_protocol_and_register(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)

            write_archivegrid_protocol_probe(
                output_dir,
                fetcher=lambda url, method="GET": {
                    "http_status": 403,
                    "final_url": url,
                    "content_type": "text/html",
                    "content_length": "",
                    "text": "Just a moment...",
                    "error": "",
                },
            )

            self.assertTrue((output_dir / ARCHIVEGRID_PROTOCOL_FILENAME).exists())
            self.assertTrue((output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME).exists())


if __name__ == "__main__":
    unittest.main()
