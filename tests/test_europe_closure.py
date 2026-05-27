import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.europe_closure import (
    EUROPE_CLOSURE_DOSSIER_FILENAME,
    EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
    EUROPE_CLOSURE_GAP_AUDIT_FILENAME,
    EUROPE_CLOSURE_MATRIX_FILENAME,
    EUROPE_CLOSURE_QUEUE_FILENAME,
    EUROPE_CLOSURE_SUMMARY_FILENAME,
    build_europe_closure_dossier,
    build_europe_closure_queue,
    build_europe_closure_outputs,
    build_europe_excluded_units_register,
    build_europe_gap_audit,
    write_europe_closure_outputs,
)
from memoria_audiovisual.european_aggregators import (
    EUROPEAN_AGGREGATOR_EVALUATION_FILENAME,
    EUROPEAN_AGGREGATOR_PROTOCOLS_FILENAME,
)
from memoria_audiovisual.european_protocols import (
    ARCHIVESHUB_PROTOCOL_FILENAME,
    FRANCEARCHIVES_PROTOCOL_FILENAME,
)


class EuropeClosureTests(unittest.TestCase):
    def test_build_europe_closure_outputs_keeps_pending_protocols_separate(self):
        evaluation_df = pd.DataFrame(
            [
                {
                    "code": "archives-hub",
                    "label": "Archives Hub",
                    "coverage_level": "agregador nacional",
                    "candidate_status": "requer_protocolo_de_acesso",
                    "access_model": "exige_js_cookies_ou_superficie_bloqueada",
                },
                {
                    "code": "francearchives",
                    "label": "FranceArchives",
                    "coverage_level": "agregador nacional",
                    "candidate_status": "requer_protocolo_de_acesso",
                    "access_model": "exige_js_cookies_ou_superficie_bloqueada",
                },
                {
                    "code": "pares",
                    "label": "PARES",
                    "coverage_level": "agregador nacional",
                    "candidate_status": "pronto_para_validacao_total",
                    "access_model": "busca_publica_com_resultados",
                },
            ]
        )
        protocols_df = pd.DataFrame(
            [
                {
                    "code": "archives-hub",
                    "incorporation_decision": "nao_incorporar_como_corpus_ativo_ate_haver_rota_estavel",
                    "next_review_trigger": "identificacao_de_api_exportacao_sitemap_ou_rota_publica_estavel",
                },
                {
                    "code": "francearchives",
                    "incorporation_decision": "nao_incorporar_como_corpus_ativo_ate_haver_rota_estavel",
                    "next_review_trigger": "identificacao_de_api_exportacao_sitemap_ou_rota_publica_estavel",
                },
            ]
        )
        archiveshub_protocol_df = pd.DataFrame(
            [{"protocol_conclusion": "sru_documentado_mas_bloqueado_na_sondagem_simples"}]
        )
        francearchives_protocol_df = pd.DataFrame(
            [{"protocol_conclusion": "dump_publico_documentado_na_ficha_do_dataset"}]
        )

        outputs = build_europe_closure_outputs(
            evaluation_df=evaluation_df,
            protocols_df=protocols_df,
            archiveshub_protocol_df=archiveshub_protocol_df,
            francearchives_protocol_df=francearchives_protocol_df,
        )
        matrix_df = outputs["matrix"]
        summary_df = outputs["summary"]

        self.assertIn("corpus_ativo", set(matrix_df["unit_type"]))
        self.assertEqual(
            set(matrix_df.loc[matrix_df["unit_type"] == "agregador_candidato", "unit_code"]),
            {"archives-hub", "francearchives"},
        )
        self.assertIn(
            "autorizada_com_cautela",
            set(summary_df.loc[summary_df["criterion"] == "abertura_do_proximo_continente", "status"]),
        )
        self.assertEqual(
            set(
                outputs["queue"].loc[
                    outputs["queue"]["unit_code"].isin({"archives-hub", "francearchives"}),
                    "queue_status",
                ]
            ),
            {"monitoramento_protocolado_sem_incorporacao_mvp"},
        )
        self.assertEqual(
            set(outputs["excluded_units"]["unit_code"]),
            {"archives-hub", "francearchives"},
        )
        self.assertFalse(outputs["gap_audit"]["unit_type"].astype(str).str.contains("sonoro", case=False).any())
        self.assertIn("corpus continental", build_europe_closure_dossier(matrix_df, summary_df).lower())
        self.assertFalse(outputs["queue"].empty)

    def test_write_europe_closure_outputs_materializes_csv_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            pd.DataFrame(
                [
                    {
                        "code": "archives-hub",
                        "label": "Archives Hub",
                        "coverage_level": "agregador nacional",
                        "candidate_status": "requer_protocolo_de_acesso",
                        "access_model": "exige_js_cookies_ou_superficie_bloqueada",
                    }
                ]
            ).to_csv(output_dir / EUROPEAN_AGGREGATOR_EVALUATION_FILENAME, index=False)
            pd.DataFrame(
                [
                    {
                        "code": "archives-hub",
                        "incorporation_decision": "nao_incorporar_como_corpus_ativo_ate_haver_rota_estavel",
                        "next_review_trigger": "identificacao_de_api_exportacao_sitemap_ou_rota_publica_estavel",
                    }
                ]
            ).to_csv(output_dir / EUROPEAN_AGGREGATOR_PROTOCOLS_FILENAME, index=False)
            pd.DataFrame(
                [{"protocol_conclusion": "sru_documentado_mas_bloqueado_na_sondagem_simples"}]
            ).to_csv(output_dir / ARCHIVESHUB_PROTOCOL_FILENAME, index=False)
            pd.DataFrame(
                [{"protocol_conclusion": "dump_publico_documentado_na_ficha_do_dataset"}]
            ).to_csv(output_dir / FRANCEARCHIVES_PROTOCOL_FILENAME, index=False)

            outputs = write_europe_closure_outputs(output_dir)

            self.assertTrue((output_dir / EUROPE_CLOSURE_MATRIX_FILENAME).exists())
            self.assertTrue((output_dir / EUROPE_CLOSURE_SUMMARY_FILENAME).exists())
            self.assertTrue((output_dir / EUROPE_CLOSURE_DOSSIER_FILENAME).exists())
            self.assertTrue((output_dir / EUROPE_CLOSURE_QUEUE_FILENAME).exists())
            self.assertTrue((output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME).exists())
            self.assertTrue((output_dir / EUROPE_CLOSURE_GAP_AUDIT_FILENAME).exists())
            self.assertFalse(outputs["matrix"].empty)
            self.assertFalse(outputs["queue"].empty)
            self.assertFalse(outputs["excluded_units"].empty)
            self.assertFalse(outputs["gap_audit"].empty)
            self.assertFalse(outputs["summary"].empty)
            self.assertIn("Dossiê MVP", outputs["dossier"])

    def test_build_europe_gap_audit_documents_non_blocking_missing_units(self):
        gap_audit_df = build_europe_gap_audit()
        row_by_code = {row["unit_code"]: row for _, row in gap_audit_df.iterrows()}

        self.assertIn("filmarchives-online", row_by_code)
        self.assertEqual(
            row_by_code["filmarchives-online"]["audit_status"],
            "legado_coberto_por_efg",
        )

    def test_build_europe_closure_queue_prioritizes_validation_candidates(self):
        matrix_df = pd.DataFrame(
            [
                {
                    "unit_code": "portal-portugues-arquivos",
                    "unit_label": "Portal Português de Arquivos",
                    "unit_type": "agregador_candidato",
                    "territorial_scope": "agregador nacional",
                    "evidence_status": "busca_publica_com_resultados",
                    "protocol_status": "protocolo_generico_indica_validacao_total",
                    "incorporation_decision": "validar_totalmente_antes_de_incorporar_como_corpus_ativo",
                    "next_step": "executar_validacao_total_e_somente_entao_incorporar",
                    "can_open_next_continent": True,
                }
            ]
        )

        queue_df = build_europe_closure_queue(matrix_df)

        self.assertEqual(queue_df.iloc[0]["queue_status"], "validar_totalmente_para_incorporacao")
        self.assertFalse(bool(queue_df.iloc[0]["blocks_expansion"]))

    def test_build_europe_closure_queue_documents_non_incorporated_mvp_candidates(self):
        matrix_df = pd.DataFrame(
            [
                {
                    "unit_code": "archives-hub",
                    "unit_label": "Archives Hub",
                    "unit_type": "agregador_candidato",
                    "territorial_scope": "agregador nacional",
                    "evidence_status": "exige_js_cookies_ou_superficie_bloqueada",
                    "protocol_status": "prototipo_leve_indica_bloqueio_em_sru_ou_oaipmh",
                    "incorporation_decision": "nao_incorporar_como_corpus_ativo_ate_haver_rota_estavel",
                    "next_step": "identificacao_de_api_exportacao_sitemap_ou_rota_publica_estavel",
                    "can_open_next_continent": True,
                }
            ]
        )

        queue_df = build_europe_closure_queue(matrix_df)

        self.assertEqual(queue_df.iloc[0]["priority"], 8)
        self.assertEqual(queue_df.iloc[0]["queue_status"], "monitoramento_protocolado_sem_incorporacao_mvp")
        self.assertFalse(bool(queue_df.iloc[0]["blocks_expansion"]))

    def test_build_europe_excluded_units_register_explains_negative_route(self):
        matrix_df = pd.DataFrame(
            [
                {
                    "unit_code": "archives-hub",
                    "unit_label": "Archives Hub",
                    "unit_type": "agregador_candidato",
                    "territorial_scope": "agregador nacional",
                    "evidence_status": "exige_js_cookies_ou_superficie_bloqueada",
                    "protocol_status": "prototipo_leve_indica_bloqueio_em_sru_ou_oaipmh",
                    "incorporation_decision": "nao_incorporar_como_corpus_ativo_ate_haver_rota_estavel",
                    "next_step": "testar_rota_sru_com_sessao_controlada",
                    "can_open_next_continent": True,
                },
                {
                    "unit_code": "ape",
                    "unit_label": "Archives Portal Europe",
                    "unit_type": "corpus_ativo",
                    "territorial_scope": "agregador continental",
                    "evidence_status": "saidas_do_corpus_materializadas_no_observatorio",
                    "protocol_status": "pipeline_ativo",
                    "incorporation_decision": "permanece_no_fechamento_europeu",
                    "next_step": "python scripts/check_ape_outputs.py",
                    "can_open_next_continent": True,
                },
            ]
        )
        queue_df = build_europe_closure_queue(matrix_df)

        excluded_df = build_europe_excluded_units_register(matrix_df, queue_df)

        self.assertEqual(len(excluded_df), 1)
        self.assertEqual(excluded_df.iloc[0]["unit_code"], "archives-hub")
        self.assertIn("não incluída no corpus", excluded_df.iloc[0]["public_status"])
        self.assertIn("SRU", excluded_df.iloc[0]["collection_route_attempted"])
        self.assertIn("negativa é técnica e metodológica", excluded_df.iloc[0]["methodological_explanation"])

    def test_build_europe_closure_blocks_next_continent_for_unprotocolled_candidate(self):
        evaluation_df = pd.DataFrame(
            [
                {
                    "code": "european-film-gateway",
                    "label": "European Film Gateway",
                    "coverage_level": "agregador audiovisual europeu",
                    "candidate_status": "pronto_para_validacao_total",
                    "access_model": "busca_publica_com_resultados",
                }
            ]
        )
        outputs = build_europe_closure_outputs(evaluation_df=evaluation_df)
        summary_df = outputs["summary"]
        status = summary_df.loc[
            summary_df["criterion"] == "abertura_do_proximo_continente",
            "status",
        ].iloc[0]

        self.assertEqual(status, "nao_autorizada")

    def test_build_europe_closure_accepts_protocolled_efg_and_europeana_candidates(self):
        evaluation_df = pd.DataFrame(
            [
                {
                    "code": "european-film-gateway",
                    "label": "European Film Gateway",
                    "coverage_level": "agregador audiovisual europeu",
                    "candidate_status": "monitoramento_tecnico",
                    "access_model": "busca_publica_com_resultados",
                },
                {
                    "code": "europeana",
                    "label": "Europeana",
                    "coverage_level": "agregador cultural europeu",
                    "candidate_status": "pronto_para_validacao_total",
                    "access_model": "busca_publica_com_resultados",
                },
            ]
        )
        archiveshub_protocol_df = pd.DataFrame(
            [{"protocol_conclusion": "sru_documentado_mas_bloqueado_na_sondagem_simples"}]
        )
        francearchives_protocol_df = pd.DataFrame(
            [{"protocol_conclusion": "dump_publico_documentado_na_ficha_do_dataset"}]
        )
        european_film_gateway_protocol_df = pd.DataFrame(
            [{"protocol_conclusion": "busca_publica_responde_com_categoria_de_video"}]
        )
        europeana_protocol_df = pd.DataFrame(
            [{"protocol_conclusion": "documentacao_publica_confirma_apis"}]
        )

        outputs = build_europe_closure_outputs(
            evaluation_df=evaluation_df,
            archiveshub_protocol_df=archiveshub_protocol_df,
            francearchives_protocol_df=francearchives_protocol_df,
            european_film_gateway_protocol_df=european_film_gateway_protocol_df,
            europeana_protocol_df=europeana_protocol_df,
        )
        summary_df = outputs["summary"]
        status = summary_df.loc[
            summary_df["criterion"] == "abertura_do_proximo_continente",
            "status",
        ].iloc[0]

        self.assertEqual(status, "autorizada_com_cautela")

        matrix_df = outputs["matrix"]
        status_by_code = dict(zip(matrix_df["unit_code"], matrix_df["protocol_status"]))
        self.assertEqual(
            status_by_code["european-film-gateway"],
            "pipeline_ativo",
        )
        self.assertEqual(
            status_by_code["europeana"],
            "pipeline_ativo",
        )


if __name__ == "__main__":
    unittest.main()
