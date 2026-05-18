import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.european_protocols import (
    ARCHIVESHUB_PROTOCOL_FILENAME,
    EUROPEAN_FILM_GATEWAY_PROTOCOL_FILENAME,
    EUROPEANA_PROTOCOL_FILENAME,
    FRANCEARCHIVES_PROTOCOL_FILENAME,
    build_archiveshub_protocol_probe,
    build_european_film_gateway_protocol_probe,
    build_europeana_protocol_probe,
    build_francearchives_protocol_probe,
    detect_dump_url,
    detect_js_redirect,
    parse_api_observation,
    parse_efg_observation,
    parse_europeana_observation,
    write_archiveshub_protocol_probe,
    write_european_film_gateway_protocol_probe,
    write_europeana_protocol_probe,
    write_francearchives_protocol_probe,
)


class EuropeanProtocolsTests(unittest.TestCase):
    def test_detect_js_redirect_matches_francearchives_redirect_page(self):
        text = "<script>window.location.href='/redirect_ABC123'</script>"

        self.assertTrue(detect_js_redirect(text))

    def test_detect_dump_url_extracts_zip_from_dataset_page(self):
        text = (
            "<a href=\"https://data-dump.francearchives.gouv.fr/ape-ead-eac/"
            "francearchives_ape_ead.zip\">download</a>"
        )

        self.assertEqual(
            detect_dump_url(text),
            "https://data-dump.francearchives.gouv.fr/ape-ead-eac/francearchives_ape_ead.zip",
        )

    def test_parse_api_observation_summarizes_empty_payload(self):
        observation = parse_api_observation('{"total_count": 0, "results": []}')

        self.assertEqual(observation, "total_count=0; sample_records=0")

    def test_parse_efg_observation_detects_video_result_count(self):
        observation = parse_efg_observation("Videos (1 Results) Vater ist im Kriege")

        self.assertEqual(observation, "video_results=1")

    def test_parse_europeana_observation_detects_api_documentation(self):
        observation = parse_europeana_observation("Europeana APIs provide access to data.")

        self.assertEqual(observation, "api_documentation_detected")

    def test_build_francearchives_protocol_probe_classifies_routes(self):
        def fake_fetcher(url, method="GET"):
            if "explore/dataset" in url:
                text = (
                    "Dataset page https://data-dump.francearchives.gouv.fr/ape-ead-eac/"
                    "francearchives_ape_ead.zip"
                )
                return {
                    "http_status": 200,
                    "final_url": url,
                    "content_type": "text/html",
                    "content_length": str(len(text)),
                    "text": text,
                    "tls_verification_failed": False,
                    "error": "",
                }
            if "api/explore" in url:
                return {
                    "http_status": 200,
                    "final_url": url,
                    "content_type": "application/json",
                    "content_length": "33",
                    "text": '{"total_count": 0, "results": []}',
                    "tls_verification_failed": False,
                    "error": "",
                }
            if "data-dump" in url:
                return {
                    "http_status": 200,
                    "final_url": url,
                    "content_type": "application/zip",
                    "content_length": "1000000",
                    "text": "",
                    "tls_verification_failed": False,
                    "error": "",
                }
            return {
                "http_status": 200,
                "final_url": url,
                "content_type": "text/html",
                "content_length": "10",
                "text": "Open Data",
                "tls_verification_failed": False,
                "error": "",
            }

        protocol_df = build_francearchives_protocol_probe(
            fetcher=fake_fetcher,
            evaluated_at="2026-05-15T00:00:00Z",
        )

        self.assertEqual(len(protocol_df), 4)
        self.assertIn(
            "dump_publico_documentado_na_ficha_do_dataset",
            set(protocol_df["protocol_conclusion"]),
        )
        self.assertIn(
            "api_acessivel_sem_registros_na_amostra",
            set(protocol_df["protocol_conclusion"]),
        )
        self.assertIn(
            "dump_zip_parece_baixavel",
            set(protocol_df["protocol_conclusion"]),
        )

    def test_build_archiveshub_protocol_probe_classifies_blocked_routes(self):
        def fake_fetcher(url, method="GET"):
            return {
                "http_status": 403,
                "final_url": url,
                "content_type": "text/html",
                "content_length": "128",
                "text": "Forbidden",
                "tls_verification_failed": False,
                "error": "",
            }

        protocol_df = build_archiveshub_protocol_probe(
            fetcher=fake_fetcher,
            evaluated_at="2026-05-15T00:00:00Z",
        )

        self.assertEqual(len(protocol_df), 5)
        self.assertIn(
            "sru_documentado_mas_bloqueado_na_sondagem_simples",
            set(protocol_df["protocol_conclusion"]),
        )
        self.assertIn(
            "oaipmh_documentado_mas_bloqueado_na_sondagem_simples",
            set(protocol_df["protocol_conclusion"]),
        )

    def test_build_archiveshub_protocol_probe_recognizes_accessible_api_reference(self):
        def fake_fetcher(url, method="GET"):
            return {
                "http_status": 200,
                "final_url": url,
                "content_type": "text/html",
                "content_length": "128",
                "text": "The Archives Hub APIs include SRU and OAI-PMH.",
                "tls_verification_failed": False,
                "error": "",
            }

        protocol_df = build_archiveshub_protocol_probe(
            fetcher=fake_fetcher,
            evaluated_at="2026-05-15T00:00:00Z",
        )
        reference_row = protocol_df.loc[protocol_df["probe"] == "api_reference_page"].iloc[0]

        self.assertEqual(
            reference_row["protocol_conclusion"],
            "documentacao_publica_confirma_sru_e_oaipmh",
        )

    def test_build_european_film_gateway_protocol_probe_classifies_public_search(self):
        def fake_fetcher(url, method="GET"):
            return {
                "http_status": 200,
                "final_url": url,
                "content_type": "text/html",
                "content_length": "128",
                "text": "European Film Gateway Videos (1 Results) film archives across Europe",
                "tls_verification_failed": False,
                "error": "",
            }

        protocol_df = build_european_film_gateway_protocol_probe(
            fetcher=fake_fetcher,
            evaluated_at="2026-05-15T00:00:00Z",
        )

        self.assertEqual(len(protocol_df), 3)
        self.assertIn(
            "busca_publica_responde_com_categoria_de_video",
            set(protocol_df["protocol_conclusion"]),
        )

    def test_build_europeana_protocol_probe_classifies_api_reference(self):
        def fake_fetcher(url, method="GET"):
            return {
                "http_status": 200,
                "final_url": url,
                "content_type": "text/html",
                "content_length": "128",
                "text": "Europeana APIs provide access to data and media search.",
                "tls_verification_failed": False,
                "error": "",
            }

        protocol_df = build_europeana_protocol_probe(
            fetcher=fake_fetcher,
            evaluated_at="2026-05-15T00:00:00Z",
        )
        api_row = protocol_df.loc[protocol_df["probe"] == "api_reference_page"].iloc[0]

        self.assertEqual(api_row["protocol_conclusion"], "documentacao_publica_confirma_apis")

    def test_write_francearchives_protocol_probe_creates_csv(self):
        def fake_fetcher(url, method="GET"):
            return {
                "http_status": 200,
                "final_url": url,
                "content_type": "application/json",
                "content_length": "33",
                "text": '{"total_count": 0, "results": []}',
                "tls_verification_failed": False,
                "error": "",
            }

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            protocol_df = write_francearchives_protocol_probe(output_dir, fetcher=fake_fetcher)

            self.assertTrue((output_dir / FRANCEARCHIVES_PROTOCOL_FILENAME).exists())
            self.assertFalse(protocol_df.empty)

    def test_write_archiveshub_protocol_probe_creates_csv(self):
        def fake_fetcher(url, method="GET"):
            return {
                "http_status": 403,
                "final_url": url,
                "content_type": "text/html",
                "content_length": "128",
                "text": "Forbidden",
                "tls_verification_failed": False,
                "error": "",
            }

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            protocol_df = write_archiveshub_protocol_probe(output_dir, fetcher=fake_fetcher)

            self.assertTrue((output_dir / ARCHIVESHUB_PROTOCOL_FILENAME).exists())
            self.assertFalse(protocol_df.empty)

    def test_write_european_film_gateway_protocol_probe_creates_csv(self):
        def fake_fetcher(url, method="GET"):
            return {
                "http_status": 200,
                "final_url": url,
                "content_type": "text/html",
                "content_length": "128",
                "text": "European Film Gateway Videos (1 Results) film archives across Europe",
                "tls_verification_failed": False,
                "error": "",
            }

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            protocol_df = write_european_film_gateway_protocol_probe(output_dir, fetcher=fake_fetcher)

            self.assertTrue((output_dir / EUROPEAN_FILM_GATEWAY_PROTOCOL_FILENAME).exists())
            self.assertFalse(protocol_df.empty)

    def test_write_europeana_protocol_probe_creates_csv(self):
        def fake_fetcher(url, method="GET"):
            return {
                "http_status": 200,
                "final_url": url,
                "content_type": "text/html",
                "content_length": "128",
                "text": "Europeana APIs provide access to data and media search.",
                "tls_verification_failed": False,
                "error": "",
            }

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            protocol_df = write_europeana_protocol_probe(output_dir, fetcher=fake_fetcher)

            self.assertTrue((output_dir / EUROPEANA_PROTOCOL_FILENAME).exists())
            self.assertFalse(protocol_df.empty)


if __name__ == "__main__":
    unittest.main()
