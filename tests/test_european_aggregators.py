import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.european_aggregators import (
    EUROPEAN_AGGREGATOR_CANDIDATES,
    EUROPEAN_AGGREGATOR_EVALUATION_FILENAME,
    EUROPEAN_AGGREGATOR_PROBES_FILENAME,
    EUROPEAN_AGGREGATOR_PROTOCOLS_FILENAME,
    EUROPEAN_AGGREGATOR_SUMMARY_FILENAME,
    build_european_aggregator_evaluation,
    detect_js_cookie_requirement,
    parse_result_count,
    write_european_aggregator_evaluation,
)


class EuropeanAggregatorEvaluationTests(unittest.TestCase):
    def test_parse_result_count_accepts_pares_result_text(self):
        text = "Resultados 1 - 25 de 571 1 2 3 4 5"

        self.assertEqual(parse_result_count(text), 571)

    def test_detect_js_cookie_requirement_accepts_common_blocking_text(self):
        self.assertTrue(detect_js_cookie_requirement("This website requires JS enabled and cookies"))
        self.assertTrue(detect_js_cookie_requirement("", "Just a moment..."))

    def test_build_evaluation_classifies_access_models_from_probe_rows(self):
        def fake_fetcher(url):
            if "pares" in url and "texto=" in url:
                return {
                    "http_status": 200,
                    "final_url": url,
                    "content_type": "text/html",
                    "title": "PARES | Archivos Españoles",
                    "text": "Resultados 1 - 25 de 32",
                    "tls_verification_failed": False,
                    "error": "",
                }
            if "archiveshub" in url or "francearchives" in url:
                return {
                    "http_status": 403,
                    "final_url": url,
                    "content_type": "text/html",
                    "title": "Just a moment...",
                    "text": "Enable JavaScript and cookies to continue",
                    "tls_verification_failed": False,
                    "error": "",
                }
            return {
                "http_status": 200,
                "final_url": url,
                "content_type": "text/html",
                "title": "PARES",
                "text": "Portal de Archivos Españoles",
                "tls_verification_failed": False,
                "error": "",
            }

        outputs = build_european_aggregator_evaluation(
            fetcher=fake_fetcher,
            evaluated_at="2026-05-14T00:00:00Z",
        )
        evaluation_df = outputs["evaluation"]

        self.assertEqual(len(evaluation_df), len(EUROPEAN_AGGREGATOR_CANDIDATES))
        pares_row = evaluation_df.loc[evaluation_df["code"] == "pares"].iloc[0]
        archives_hub_row = evaluation_df.loc[evaluation_df["code"] == "archives-hub"].iloc[0]

        self.assertEqual(pares_row["candidate_status"], "pronto_para_pipeline_experimental")
        self.assertGreater(int(pares_row["search_result_count_total"]), 0)
        self.assertEqual(archives_hub_row["candidate_status"], "requer_protocolo_de_acesso")

        protocols_df = outputs["protocols"]
        archives_hub_protocol = protocols_df.loc[protocols_df["code"] == "archives-hub"].iloc[0]
        pares_protocol = protocols_df.loc[protocols_df["code"] == "pares"].iloc[0]

        self.assertTrue(bool(archives_hub_protocol["protocol_needed"]))
        self.assertEqual(
            archives_hub_protocol["incorporation_decision"],
            "nao_incorporar_como_corpus_ativo_ate_haver_rota_estavel",
        )
        self.assertFalse(bool(pares_protocol["protocol_needed"]))
        self.assertEqual(
            pares_protocol["incorporation_decision"],
            "pode_ser_tratado_como_corpus_experimental",
        )

    def test_write_evaluation_materializes_expected_files(self):
        def fake_fetcher(url):
            return {
                "http_status": 200,
                "final_url": url,
                "content_type": "text/html",
                "title": "Fonte",
                "text": "Resultados 1 - 25 de 1",
                "tls_verification_failed": False,
                "error": "",
            }

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            outputs = write_european_aggregator_evaluation(output_dir, fetcher=fake_fetcher)

            self.assertTrue((output_dir / EUROPEAN_AGGREGATOR_EVALUATION_FILENAME).exists())
            self.assertTrue((output_dir / EUROPEAN_AGGREGATOR_PROBES_FILENAME).exists())
            self.assertTrue((output_dir / EUROPEAN_AGGREGATOR_PROTOCOLS_FILENAME).exists())
            self.assertTrue((output_dir / EUROPEAN_AGGREGATOR_SUMMARY_FILENAME).exists())
            self.assertFalse(outputs["evaluation"].empty)
            self.assertFalse(outputs["probes"].empty)
            self.assertFalse(outputs["protocols"].empty)
            self.assertFalse(outputs["summary"].empty)


if __name__ == "__main__":
    unittest.main()
