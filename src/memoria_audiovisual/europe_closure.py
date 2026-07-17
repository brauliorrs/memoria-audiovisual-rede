from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import CINEMATHEQUE_SUISSE_MEMOBASE_RECORDSET_URL, OUTPUT_DIR
from .corpora import CORPORA, CORPUS_CATEGORIES, list_active_corpora
from .european_aggregators import (
    EUROPEAN_AGGREGATOR_EVALUATION_FILENAME,
    EUROPEAN_AGGREGATOR_PROTOCOLS_FILENAME,
)
from .european_protocols import (
    ARCHIVESHUB_PROTOCOL_FILENAME,
    EUROPEAN_FILM_GATEWAY_PROTOCOL_FILENAME,
    EUROPEANA_PROTOCOL_FILENAME,
    FRANCEARCHIVES_PROTOCOL_FILENAME,
)


EUROPE_CLOSURE_MATRIX_FILENAME = "observatorio_fechamento_europa.csv"
EUROPE_CLOSURE_SUMMARY_FILENAME = "observatorio_resumo_fechamento_europa.csv"
EUROPE_CLOSURE_DOSSIER_FILENAME = "observatorio_dossie_fechamento_europa.md"
EUROPE_CLOSURE_QUEUE_FILENAME = "observatorio_fila_fechamento_europa.csv"
EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME = "observatorio_unidades_identificadas_nao_incorporadas.csv"
EUROPE_CLOSURE_GAP_AUDIT_FILENAME = "observatorio_auditoria_lacunas_europa.csv"
EUROPE_CLOSURE_RULE_VERSION = "2026-05-fechamento-europa-v1"
CINEMATHEQUE_SUISSE_NON_INCORPORATION_CATEGORY = "metadados_publicos_midia_local_autorizada_sem_video_publico"
CINEMATHEQUE_SUISSE_NON_INCORPORATION_DECISION = "nao_incorporar_como_corpus_ativo_sem_video_publico_incorporavel"
FILMMUSEUM_MUNCHEN_NON_INCORPORATION_CATEGORY = "arquivo_filmico_com_acervo_confirmado_sem_catalogo_publico_de_video"
CINETECA_ITALIANA_NON_INCORPORATION_CATEGORY = (
    "arquivo_filmico_com_streaming_protegido_sem_catalogo_publico_de_video"
)

EUROPE_CLOSURE_MATRIX_COLUMNS = [
    "unit_code",
    "unit_label",
    "unit_type",
    "category",
    "territorial_scope",
    "methodological_status",
    "evidence_status",
    "audiovisual_interpretation",
    "protocol_status",
    "incorporation_decision",
    "next_step",
    "can_open_next_continent",
    "rule_version",
]

EUROPE_CLOSURE_SUMMARY_COLUMNS = [
    "criterion",
    "status",
    "evidence",
    "interpretation",
    "next_step",
    "rule_version",
]

EUROPE_CLOSURE_QUEUE_COLUMNS = [
    "priority",
    "unit_code",
    "unit_label",
    "unit_type",
    "territorial_scope",
    "queue_status",
    "queue_reason",
    "evidence_status",
    "protocol_status",
    "next_step",
    "blocks_expansion",
    "rule_version",
]

EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS = [
    "unit_code",
    "unit_label",
    "unit_type",
    "territorial_scope",
    "access_category",
    "public_status",
    "methodological_decision",
    "negative_reason",
    "collection_route_attempted",
    "attempt_summary",
    "methodological_explanation",
    "evidence_status",
    "protocol_status",
    "next_step",
    "blocks_expansion",
    "rule_version",
]

EUROPE_CLOSURE_GAP_AUDIT_COLUMNS = [
    "unit_code",
    "unit_label",
    "unit_type",
    "territorial_scope",
    "audit_status",
    "relation_to_active_corpus",
    "corpus_decision",
    "methodological_reason",
    "source_url",
    "evidence_reference",
    "next_step",
    "blocks_expansion",
    "rule_version",
]

EUROPE_GAP_AUDIT_ROWS = [
    {
        "unit_code": "filmarchives-online",
        "unit_label": "FilmArchives Online / MIDAS",
        "unit_type": "gateway_legado_de_filmes",
        "territorial_scope": "Europa",
        "audit_status": "legado_coberto_por_efg",
        "relation_to_active_corpus": "coberto metodologicamente pelo European Film Gateway",
        "corpus_decision": "não abrir corpus próprio no MVP",
        "methodological_reason": (
            "É um gateway histórico de catálogo de filmes; o fechamento atual usa o EFG como "
            "agregador fílmico europeu ativo e mais aderente ao organismo."
        ),
        "source_url": "https://ace-film.eu/projects/midas/",
        "evidence_reference": "ACE descreve o MIDAS/FilmArchives Online como gateway de acesso a coleções fílmicas europeias.",
        "next_step": "manter_como_referência_legada_e_reavaliar_se_o_efg_perder_rota_pública",
        "blocks_expansion": False,
    },
    {
        "unit_code": "efg-special-collections",
        "unit_label": "EFG1914 e VICTOR-E",
        "unit_type": "colecoes_especiais",
        "territorial_scope": "Europa",
        "audit_status": "coberto_por_corpus_ativo",
        "relation_to_active_corpus": "coleções especiais internas do European Film Gateway",
        "corpus_decision": "não abrir corpus próprio no MVP",
        "methodological_reason": (
            "São recortes temáticos dentro do EFG, não agregadores autônomos para a arquitetura "
            "atual do observatório."
        ),
        "source_url": "https://www.europeanfilmgateway.eu/content/about-european-film-gateway",
        "evidence_reference": "A página do EFG apresenta EFG1914 e VICTOR-E como coleções especiais do próprio portal.",
        "next_step": "usar_como_recorte_temático_quando_a_análise_de_temas_fílmicos_avançar",
        "blocks_expansion": False,
    },
    {
        "unit_code": "european-audiovisual-observatory",
        "unit_label": "European Audiovisual Observatory",
        "unit_type": "observatorio_de_politicas_e_mercado",
        "territorial_scope": "Europa",
        "audit_status": "fonte_teorica_e_de_contexto",
        "relation_to_active_corpus": "não é agregador de acervo arquivístico",
        "corpus_decision": "não incorporar como corpus de acervo",
        "methodological_reason": (
            "Produz dados, relatórios e bases sobre indústria, política e regulação audiovisual; "
            "serve ao enquadramento teórico, não à coleta de acervos."
        ),
        "source_url": "https://www.obs.coe.int/",
        "evidence_reference": "O Observatory se apresenta como fonte de informação sobre o setor audiovisual europeu.",
        "next_step": "usar_como_fonte_bibliográfica_e_contextual_do_projeto",
        "blocks_expansion": False,
    },
    {
        "unit_code": "ace",
        "unit_label": "Association des Cinémathèques Européennes",
        "unit_type": "rede_institucional",
        "territorial_scope": "Europa",
        "audit_status": "fonte_de_radar_institucional",
        "relation_to_active_corpus": "rede que ajuda a localizar arquivos fílmicos, não corpus agregador autônomo",
        "corpus_decision": "não incorporar como corpus no MVP",
        "methodological_reason": (
            "Funciona como rede e memória de projetos europeus de cinema; é útil para radar, "
            "mas não substitui EFG, Europeana ou APE como infraestrutura de metadados."
        ),
        "source_url": "https://ace-film.eu/",
        "evidence_reference": "A ACE documenta projetos e redes de cinematecas europeias.",
        "next_step": "usar_como_radar_de_instituicoes_filmicas_na_etapa_de_arquivos_individuais",
        "blocks_expansion": False,
    },
    {
        "unit_code": "archivportal-d",
        "unit_label": "Archivportal-D / Deutsche Digitale Bibliothek",
        "unit_type": "agregador_nacional_geral",
        "territorial_scope": "Alemanha",
        "audit_status": "candidato_nacional_futuro_nao_bloqueante",
        "relation_to_active_corpus": "potencialmente coberto de forma parcial por APE e Europeana",
        "corpus_decision": "adiar para etapa de agregadores nacionais",
        "methodological_reason": (
            "É um agregador nacional geral relevante, mas o MVP europeu não pretende exaurir "
            "todos os agregadores nacionais após Portugal e Espanha; entra como candidato futuro."
        ),
        "source_url": "https://www.archivportal-d.de/",
        "evidence_reference": "O portal agrega informações arquivísticas nacionais alemãs.",
        "next_step": "avaliar_quando_a_expansao_nacional_europeia_for_reaberta",
        "blocks_expansion": False,
    },
]


def _load_csv_if_exists(output_dir, filename):
    path = Path(output_dir) / filename
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _active_corpus_rows():
    rows = []
    for corpus_def in list_active_corpora(monthly_only=True):
        coverage_level = str(corpus_def.get("coverage_level", "")).lower()
        is_european = (
            corpus_def["code"] in {"ape", "euscreen", "pares", "ina"}
            or "europe" in coverage_level
            or "europeu" in coverage_level
        )
        if not is_european:
            continue

        category_def = CORPUS_CATEGORIES[corpus_def["category_code"]]
        rows.append(
            {
                "unit_code": corpus_def["code"],
                "unit_label": corpus_def["label"],
                "unit_type": "corpus_ativo",
                "category": category_def["label"],
                "territorial_scope": corpus_def["coverage_level"],
                "methodological_status": "incorporado_ao_organismo",
                "evidence_status": "saidas_do_corpus_materializadas_no_observatorio",
                "audiovisual_interpretation": corpus_def["audiovisual_scope_note"],
                "protocol_status": "pipeline_ativo",
                "incorporation_decision": "permanece_no_fechamento_europeu",
                "next_step": corpus_def["check_script"],
                "can_open_next_continent": True,
                "rule_version": EUROPE_CLOSURE_RULE_VERSION,
            }
        )
    return rows


def _protocolled_individual_rows():
    return [
        {
            "unit_code": "cinematheque-suisse",
            "unit_label": "Cinémathèque suisse",
            "unit_type": "arquivo_individual_protocolado",
            "category": "Arquivos audiovisuais individuais protocolados",
            "territorial_scope": "Suíça / instituição individual europeia",
            "methodological_status": "identificado_com_metadados_publicos_sem_video_publico_incorporavel",
            "evidence_status": "API Memobase retorna registros Film, mas mídia local/autorizada",
            "audiovisual_interpretation": (
                "A instituição é explicitamente audiovisual, mas o recorte do organismo exige vídeo público "
                "ou rota audiovisual incorporável. A rota Memobase confirma metadados públicos, não acesso "
                "público aos vídeos."
            ),
            "protocol_status": "protocolo_de_nao_incorporacao_por_acesso_restrito",
            "incorporation_decision": CINEMATHEQUE_SUISSE_NON_INCORPORATION_DECISION,
            "next_step": "monitorar_se_memobase_ou_site_institucional_passam_a_expor_video_publico",
            "can_open_next_continent": True,
            "rule_version": EUROPE_CLOSURE_RULE_VERSION,
        },
        {
            "unit_code": "fiaf-filmmuseum-munchen",
            "unit_label": "Filmmuseum München",
            "unit_type": "arquivo_individual_protocolado",
            "category": "Arquivos audiovisuais individuais protocolados",
            "territorial_scope": "Munique / Alemanha / instituição individual europeia",
            "methodological_status": "arquivo_filmico_confirmado_sem_catalogo_publico_de_video_coletavel",
            "evidence_status": "site oficial confirma acervo fílmico, mas expõe programação e páginas institucionais",
            "audiovisual_interpretation": (
                "A instituição é explicitamente audiovisual e possui acervo fílmico. Nesta rodada, porém, as rotas "
                "públicas verificadas não expõem catálogo público de vídeos de acervo nem metadados audiovisuais "
                "coletáveis de forma reprodutível."
            ),
            "protocol_status": "acervo_preservado_e_programacao_publica_sem_rota_de_video_de_acervo",
            "incorporation_decision": "nao_incorporar_como_corpus_ativo_ate_haver_rota_estavel",
            "next_step": "retestar_site_oficial_sammlung_online_e_eventuais_catalogos_digitais_em_ciclos_futuros",
            "can_open_next_continent": True,
            "rule_version": EUROPE_CLOSURE_RULE_VERSION,
        },
        {
            "unit_code": "fiaf-cineteca-italiana",
            "unit_label": "Fondazione Cineteca Italiana",
            "unit_type": "arquivo_individual_protocolado",
            "category": "Arquivos audiovisuais individuais protocolados",
            "territorial_scope": "Milão / Itália / instituição individual europeia",
            "methodological_status": "arquivo_filmico_confirmado_com_streaming_protegido_sem_catalogo_publico_de_video",
            "evidence_status": (
                "site oficial confirma acervo fílmico; streaming aparece protegido; canal YouTube público "
                "não equivale a catálogo de acervo"
            ),
            "audiovisual_interpretation": (
                "A instituição é explicitamente audiovisual e possui acervo fílmico. Nesta rodada, porém, as rotas "
                "públicas verificadas expõem programação, visita presencial, streaming protegido, plataforma educativa "
                "com registro e canal institucional recente, não um catálogo público de vídeos de acervo."
            ),
            "protocol_status": "acervo_preservado_programacao_publica_streaming_protegido_e_canal_publico_nao_catalografico",
            "incorporation_decision": "nao_incorporar_como_corpus_ativo_ate_haver_rota_estavel",
            "next_step": "retestar_site_oficial_streaming_youtube_vimeo_e_eventual_catalogo_publico_de_acervo_em_ciclos_futuros",
            "can_open_next_continent": True,
            "rule_version": EUROPE_CLOSURE_RULE_VERSION,
        }
    ]


def _protocol_count(protocol_df):
    return int(len(protocol_df)) if protocol_df is not None and not protocol_df.empty else 0


def _protocol_status_for_candidate(code, specific_protocol_df, protocol_row=None):
    if specific_protocol_df is None or specific_protocol_df.empty:
        if protocol_row is None:
            return "sem_prototipo_especifico_materializado"
        decision = str(protocol_row.get("incorporation_decision", ""))
        if decision == "validar_totalmente_antes_de_incorporar_como_corpus_ativo":
            return "protocolo_generico_indica_validacao_total"
        if decision == "nao_incorporar_como_corpus_ativo_ate_haver_rota_estavel":
            return "protocolo_generico_indica_rota_pendente"
        return "protocolo_generico_materializado"

    conclusions = specific_protocol_df.get("protocol_conclusion", pd.Series(dtype="object")).astype(str)
    if code == "archives-hub":
        if conclusions.str.contains("bloqueado", case=False, na=False).any():
            return "prototipo_leve_indica_bloqueio_em_sru_ou_oaipmh"
    if code == "francearchives":
        if conclusions.str.contains("dump_publico_documentado", case=False, na=False).any():
            return "prototipo_leve_indica_dump_documentado_mas_download_a_validar"
    if code == "european-film-gateway":
        if conclusions.str.contains("falha_tecnica", case=False, na=False).all():
            return "prototipo_leve_indica_falha_tecnica_na_rodada"
        if conclusions.str.contains("busca_publica_responde_com_categoria_de_video", case=False, na=False).any():
            return "prototipo_leve_confirma_busca_publica_audiovisual"
    if code == "europeana":
        has_media_search = conclusions.str.contains(
            "busca_publica_com_filtro_de_midia_confirmada",
            case=False,
            na=False,
        ).any()
        has_api_block = conclusions.str.contains(
            "rota_publica_bloqueada_na_sondagem_simples",
            case=False,
            na=False,
        ).any()
        if has_media_search and has_api_block:
            return "prototipo_leve_confirma_busca_publica_mas_api_bloqueada"
        if has_media_search:
            return "prototipo_leve_confirma_busca_publica_com_midia"
    return "prototipo_leve_materializado"


def _candidate_rows(
    evaluation_df,
    protocols_df,
    archiveshub_protocol_df,
    francearchives_protocol_df,
    european_film_gateway_protocol_df,
    europeana_protocol_df,
):
    if evaluation_df is None or evaluation_df.empty:
        return []

    protocol_lookup = {}
    if protocols_df is not None and not protocols_df.empty:
        for _, row in protocols_df.iterrows():
            protocol_lookup[str(row.get("code", ""))] = row

    rows = []
    for _, evaluation_row in evaluation_df.iterrows():
        code = str(evaluation_row.get("code", ""))
        if code in CORPORA and CORPORA[code].get("organism_active", False):
            continue

        protocol_row = protocol_lookup.get(code)
        specific_protocol_df = (
            archiveshub_protocol_df
            if code == "archives-hub"
            else francearchives_protocol_df
            if code == "francearchives"
            else european_film_gateway_protocol_df
            if code == "european-film-gateway"
            else europeana_protocol_df
            if code == "europeana"
            else pd.DataFrame()
        )
        protocol_status = _protocol_status_for_candidate(code, specific_protocol_df, protocol_row)
        can_open_next_continent = protocol_status != "sem_prototipo_especifico_materializado"
        incorporation_decision = (
            protocol_row.get("incorporation_decision", "")
            if protocol_row is not None
            else "aguardar_protocolo_estavel"
        )
        next_step = (
            protocol_row.get("recommended_protocol", "")
            if (
                incorporation_decision == "validar_totalmente_antes_de_incorporar_como_corpus_ativo"
                and protocol_row is not None
            )
            else protocol_row.get("next_review_trigger", "")
            if protocol_row is not None
            else "materializar_prototipo_de_protocolo"
        )

        rows.append(
            {
                "unit_code": code,
                "unit_label": evaluation_row.get("label", ""),
                "unit_type": "agregador_candidato",
                "category": "Agregadores arquivísticos candidatos",
                "territorial_scope": evaluation_row.get("coverage_level", ""),
                "methodological_status": evaluation_row.get("candidate_status", ""),
                "evidence_status": evaluation_row.get("access_model", ""),
                "audiovisual_interpretation": (
                    "Fonte relevante para o fechamento europeu, mas ainda sem rota estável "
                    "para coleta comparável. Retorno zero preliminar não equivale a ausência "
                    "de acervo audiovisual."
                ),
                "protocol_status": protocol_status,
                "incorporation_decision": incorporation_decision,
                "next_step": next_step,
                "can_open_next_continent": can_open_next_continent,
                "rule_version": EUROPE_CLOSURE_RULE_VERSION,
            }
        )
    return rows


def build_europe_closure_outputs(
    *,
    evaluation_df=None,
    protocols_df=None,
    archiveshub_protocol_df=None,
    francearchives_protocol_df=None,
    european_film_gateway_protocol_df=None,
    europeana_protocol_df=None,
):
    evaluation_df = evaluation_df if evaluation_df is not None else pd.DataFrame()
    protocols_df = protocols_df if protocols_df is not None else pd.DataFrame()
    archiveshub_protocol_df = archiveshub_protocol_df if archiveshub_protocol_df is not None else pd.DataFrame()
    francearchives_protocol_df = francearchives_protocol_df if francearchives_protocol_df is not None else pd.DataFrame()
    european_film_gateway_protocol_df = (
        european_film_gateway_protocol_df if european_film_gateway_protocol_df is not None else pd.DataFrame()
    )
    europeana_protocol_df = europeana_protocol_df if europeana_protocol_df is not None else pd.DataFrame()

    matrix_rows = _active_corpus_rows()
    matrix_rows.extend(_protocolled_individual_rows())
    matrix_rows.extend(
        _candidate_rows(
            evaluation_df,
            protocols_df,
            archiveshub_protocol_df,
            francearchives_protocol_df,
            european_film_gateway_protocol_df,
            europeana_protocol_df,
        )
    )
    matrix_df = pd.DataFrame(matrix_rows, columns=EUROPE_CLOSURE_MATRIX_COLUMNS)
    queue_df = build_europe_closure_queue(matrix_df)
    excluded_units_df = build_europe_excluded_units_register(matrix_df, queue_df)
    gap_audit_df = build_europe_gap_audit()

    active_european_corpora = int((matrix_df["unit_type"] == "corpus_ativo").sum()) if not matrix_df.empty else 0
    pending_candidates = int((matrix_df["unit_type"] == "agregador_candidato").sum()) if not matrix_df.empty else 0
    audited_gaps = len(gap_audit_df)
    blocking_candidates = (
        int((matrix_df["can_open_next_continent"].astype(str).str.lower() != "true").sum())
        if not matrix_df.empty and "can_open_next_continent" in matrix_df.columns
        else 0
    )
    protocol_rows = (
        _protocol_count(archiveshub_protocol_df)
        + _protocol_count(francearchives_protocol_df)
        + _protocol_count(european_film_gateway_protocol_df)
        + _protocol_count(europeana_protocol_df)
    )

    summary_rows = [
        {
            "criterion": "corpora_europeus_ativos",
            "status": "materializado" if active_european_corpora else "pendente",
            "evidence": f"{active_european_corpora} corpora europeus ativos no organismo",
            "interpretation": (
                "A etapa europeia possui base operacional para comparação entre agregadores "
                "gerais, agregador audiovisual, agregador nacional e arquivo especializado."
            ),
            "next_step": "validar_novas_rodadas_mensais",
            "rule_version": EUROPE_CLOSURE_RULE_VERSION,
        },
        {
            "criterion": "fila_europeia_organizada",
            "status": "materializado" if not queue_df.empty else "pendente",
            "evidence": f"{len(queue_df)} pendências ordenadas na fila europeia",
            "interpretation": (
                "A fila explicita apenas pendências operacionais: o que deve virar pipeline, "
                "o que permanece protocolado e o que ainda exige decisão. Corpora ativos ficam "
                "na matriz e no ciclo mensal, fora da fila."
            ),
            "next_step": "executar_prioridades_europeias_antes_de_novo_continente",
            "rule_version": EUROPE_CLOSURE_RULE_VERSION,
        },
        {
            "criterion": "agregadores_candidatos_com_protocolo",
            "status": "materializado" if protocol_rows else "pendente",
            "evidence": f"{protocol_rows} sondagens leves em protótipos de protocolo",
            "interpretation": (
                "Archives Hub e FranceArchives permanecem como candidatos europeus relevantes, "
                "mas estão protocolados fora do MVP ativo enquanto não houver rota técnica estável."
            ),
            "next_step": "manter_monitoramento_protocolado_sem_misturar_com_corpora_ativos",
            "rule_version": EUROPE_CLOSURE_RULE_VERSION,
        },
        {
            "criterion": "abertura_do_proximo_continente",
            "status": (
                "autorizada_com_cautela"
                if active_european_corpora and protocol_rows and blocking_candidates == 0
                else "nao_autorizada"
            ),
            "evidence": (
                f"{active_european_corpora} corpora ativos; {pending_candidates} candidatos europeus "
                f"mantidos como protocolo pendente; {blocking_candidates} candidatos sem fechamento suficiente"
            ),
            "interpretation": (
                "A Europa só pode abrir a próxima etapa continental quando os candidatos europeus "
                "prioritários estiverem incorporados, protocolados ou justificados como inviáveis."
            ),
            "next_step": (
                "abrir_america_do_sul_sem_encerrar_monitoramento_europeu"
                if blocking_candidates == 0
                else "protocolar_european_film_gateway_e_europeana_antes_da_expansao"
            ),
            "rule_version": EUROPE_CLOSURE_RULE_VERSION,
        },
        {
            "criterion": "auditoria_de_lacunas_europeias",
            "status": "materializado" if audited_gaps else "pendente",
            "evidence": f"{audited_gaps} unidades ou classes de unidade auditadas fora do corpus ativo",
            "interpretation": (
                "O fechamento europeu nao afirma exaustividade absoluta de arquivos individuais. "
                "Ele separa agregadores centrais, unidades cobertas por corpora ativos, legados, "
                "fontes de radar e candidatos nacionais futuros."
            ),
            "next_step": "manter_auditoria_como_limite_publico_da_afirmacao_de_fechamento",
            "rule_version": EUROPE_CLOSURE_RULE_VERSION,
        },
    ]
    summary_df = pd.DataFrame(summary_rows, columns=EUROPE_CLOSURE_SUMMARY_COLUMNS)
    return {
        "matrix": matrix_df,
        "queue": queue_df,
        "excluded_units": excluded_units_df,
        "gap_audit": gap_audit_df,
        "summary": summary_df,
    }


def build_europe_gap_audit():
    rows = []
    for row in EUROPE_GAP_AUDIT_ROWS:
        rows.append({**row, "rule_version": EUROPE_CLOSURE_RULE_VERSION})
    return pd.DataFrame(rows, columns=EUROPE_CLOSURE_GAP_AUDIT_COLUMNS)


def build_europe_closure_queue(matrix_df):
    if matrix_df is None or matrix_df.empty:
        return pd.DataFrame(columns=EUROPE_CLOSURE_QUEUE_COLUMNS)

    rows = []
    for _, row in matrix_df.iterrows():
        unit_type = row.get("unit_type", "")
        protocol_status = str(row.get("protocol_status", ""))
        incorporation_decision = str(row.get("incorporation_decision", ""))
        can_open = str(row.get("can_open_next_continent", "")).lower() == "true"

        if unit_type == "corpus_ativo":
            continue
        elif protocol_status == "sem_prototipo_especifico_materializado":
            priority = 1
            queue_status = "protocolar_antes_da_expansao"
            queue_reason = "Candidato europeu sem protocolo suficiente para fechamento continental."
        elif incorporation_decision == "validar_totalmente_antes_de_incorporar_como_corpus_ativo":
            priority = 2
            queue_status = "validar_totalmente_para_incorporacao"
            queue_reason = "A sondagem indica rota pública, mas a unidade só entra após validação total."
        elif incorporation_decision in {
            "nao_incorporar_como_corpus_ativo_ate_haver_rota_estavel",
            CINEMATHEQUE_SUISSE_NON_INCORPORATION_DECISION,
        }:
            priority = 8
            queue_status = "monitoramento_protocolado_sem_incorporacao_mvp"
            if row.get("unit_code", "") == "cinematheque-suisse":
                queue_reason = (
                    "O protocolo documentou relevância e metadados públicos, mas não encontrou vídeo "
                    "público incorporável; a unidade permanece fora do corpus ativo no MVP."
                )
            elif row.get("unit_code", "") == "fiaf-filmmuseum-munchen":
                queue_reason = (
                    "O protocolo confirmou acervo fílmico, mas as rotas públicas observadas são página "
                    "institucional, história do acervo, programação, ingressos, vídeos institucionais gerais "
                    "e busca instável na Sammlung Online; não há catálogo público de vídeos de acervo coletável."
                )
            elif row.get("unit_code", "") == "fiaf-cineteca-italiana":
                queue_reason = (
                    "O protocolo confirmou acervo fílmico, mas as rotas públicas observadas são programação de sala, "
                    "streaming protegido por conta/compra/senha, visita presencial, plataforma educativa com registro "
                    "e canal institucional recente; não há catálogo público de vídeos de acervo coletável."
                )
            else:
                queue_reason = (
                    "O protocolo documentou relevância, mas também ausência de rota estável; "
                    "a unidade permanece fora do corpus ativo no MVP."
                )
        else:
            priority = 3
            queue_status = "pendencia_protocolada"
            queue_reason = "Candidato europeu documentado, mas sem rota estável para corpus ativo."

        rows.append(
            {
                "priority": priority,
                "unit_code": row.get("unit_code", ""),
                "unit_label": row.get("unit_label", ""),
                "unit_type": unit_type,
                "territorial_scope": row.get("territorial_scope", ""),
                "queue_status": queue_status,
                "queue_reason": queue_reason,
                "evidence_status": row.get("evidence_status", ""),
                "protocol_status": protocol_status,
                "next_step": row.get("next_step", ""),
                "blocks_expansion": not can_open,
                "rule_version": EUROPE_CLOSURE_RULE_VERSION,
            }
        )

    return (
        pd.DataFrame(rows, columns=EUROPE_CLOSURE_QUEUE_COLUMNS)
        .sort_values(["priority", "unit_label"])
        .reset_index(drop=True)
    )


def _collection_route_attempted(row):
    code = str(row.get("unit_code", ""))
    if code == "cinematheque-suisse":
        return (
            "Página institucional do Film Department, endpoint Memobase da instituição csa, "
            "conjunto `csa-001` e busca API `type:Film AND *:csa-001`."
        )
    if code == "fiaf-filmmuseum-munchen":
        return (
            "Página oficial do Filmmuseum, página Geschichte, Spielplan & Tickets, Filmreihen, página geral "
            "de vídeos do Münchner Stadtmuseum, homepage da Sammlung Online e formulário público de busca "
            "da Sammlung Online com o termo Film."
        )
    if code == "fiaf-cineteca-italiana":
        return (
            "Página oficial, página Chi siamo, laboratório de restauração, seção Film, endpoint WordPress de Film, "
            "página de streaming, endpoint WordPress de streaming, visita guiada ao Arquivo Film, feed RSS do canal "
            "YouTube e The Film Corner."
        )
    if code == "archives-hub":
        return "SRU e OAI-PMH documentados; referência pública de APIs também sondada."
    if code == "francearchives":
        return "Página de dados abertos, dataset público, API do dataset e dump XML APE-EAD."
    return "Rotas públicas ou documentadas sondadas pelo protocolo europeu."


def _attempt_summary(row):
    code = str(row.get("unit_code", ""))
    if code == "cinematheque-suisse":
        return (
            "A rota Memobase retornou registros Film e metadados públicos do conjunto `csa-001`, "
            "mas os objetos digitais aparecem com acesso local/autorizado e uso sujeito a direitos. "
            "Não foi identificado vídeo público incorporável ao corpus ativo."
        )
    if code == "fiaf-filmmuseum-munchen":
        return (
            "A página Geschichte confirma arquivo com cerca de 6.000 cópias, mas não oferece catálogo público "
            "de vídeo. A programação lista sessões e ingressos. A página geral de vídeos usa YouTube para "
            "conteúdo institucional do museu inteiro. A consulta controlada à Sammlung Online não produziu "
            "rota estável de recorte Filmmuseum/Filmarchiv."
        )
    if code == "fiaf-cineteca-italiana":
        return (
            "A página institucional confirma acervo fílmico de cerca de 40.000 títulos em película. A seção Film "
            "e o endpoint `film` funcionam como programação de sala. O endpoint `streaming` expõe registros "
            "protegidos, sem conteúdo público. A visita ao Arquivo Film é presencial. O feed YouTube é público, "
            "mas representa canal institucional recente, não catálogo público integral do acervo."
        )
    if code == "archives-hub":
        return (
            "Foram testadas a referência pública sobre APIs, a rota SRU base, uma consulta SRU "
            "audiovisual mínima, a rota OAI-PMH base e o verbo Identify. As sondagens simples "
            "retornaram bloqueio por JS/cookies ou superfície não estável."
        )
    if code == "francearchives":
        return (
            "Foram testadas a página oficial de dados abertos, a ficha pública do dataset, uma "
            "amostra da API e o cabeçalho do pacote APE-EAD. A ficha aponta um dump público, "
            "mas a API retornou amostra vazia e o cabeçalho não confirmou um ZIP baixável por "
            "coleta leve."
        )
    return (
        "O protocolo registrou sinais de relevância, mas ainda não confirmou rota de coleta "
        "estável, reprodutível e comparável."
    )


def _excluded_access_category(row):
    if str(row.get("unit_code", "")) == "cinematheque-suisse":
        return CINEMATHEQUE_SUISSE_NON_INCORPORATION_CATEGORY
    if str(row.get("unit_code", "")) == "fiaf-filmmuseum-munchen":
        return FILMMUSEUM_MUNCHEN_NON_INCORPORATION_CATEGORY
    if str(row.get("unit_code", "")) == "fiaf-cineteca-italiana":
        return CINETECA_ITALIANA_NON_INCORPORATION_CATEGORY
    return "rota_publica_nao_estavel_ou_nao_coletavel"


def _excluded_methodological_explanation(row):
    if str(row.get("unit_code", "")) == "cinematheque-suisse":
        return (
            "A negativa não indica ausência de acervo audiovisual. Ela registra que, nesta rodada, "
            "o organismo encontrou apenas metadados públicos e mídia local/autorizada; como não há "
            "vídeo público incorporável, a unidade fica fora do corpus ativo."
        )
    if str(row.get("unit_code", "")) == "fiaf-filmmuseum-munchen":
        return (
            "A negativa não indica ausência nem irrelevância do acervo audiovisual. Ela impede que programação "
            "de sala, bilheteria, vídeos institucionais gerais ou busca instável em coleção museológica ampla "
            "sejam tratados como corpus de arquivo fílmico."
        )
    if str(row.get("unit_code", "")) == "fiaf-cineteca-italiana":
        return (
            "A negativa não indica ausência nem irrelevância do acervo audiovisual. Ela impede que programação "
            "de sala, streaming protegido, visita presencial, plataforma educativa com registro ou canal institucional "
            "recente sejam tratados como corpus público de arquivo fílmico."
        )
    return (
        "A negativa é técnica e metodológica: sem rota estável, a fonte não pode ser "
        "comparada aos corpora ativos. Isso não autoriza concluir ausência de acervo "
        "audiovisual; apenas registra que o organismo não conseguiu incorporá-la com "
        "rigor nesta rodada."
    )


def build_europe_excluded_units_register(matrix_df, queue_df=None):
    if matrix_df is None or matrix_df.empty:
        return pd.DataFrame(columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS)

    queue_df = queue_df if queue_df is not None else build_europe_closure_queue(matrix_df)
    queue_lookup = {}
    if queue_df is not None and not queue_df.empty:
        for _, queue_row in queue_df.iterrows():
            queue_lookup[str(queue_row.get("unit_code", ""))] = queue_row

    candidates_df = matrix_df.loc[
        (matrix_df["unit_type"] != "corpus_ativo")
        & (
            matrix_df["incorporation_decision"].isin(
                [
                    "nao_incorporar_como_corpus_ativo_ate_haver_rota_estavel",
                    CINEMATHEQUE_SUISSE_NON_INCORPORATION_DECISION,
                ]
            )
        )
    ].copy()
    if candidates_df.empty:
        return pd.DataFrame(columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS)

    rows = []
    for _, row in candidates_df.sort_values("unit_label").iterrows():
        unit_code = str(row.get("unit_code", ""))
        queue_row = queue_lookup.get(unit_code, {})
        negative_reason = (
            queue_row.get("queue_reason", "")
            if hasattr(queue_row, "get")
            else "Ausência de rota de coleta estável no protocolo atual."
        )
        blocks_expansion = queue_row.get("blocks_expansion", False) if hasattr(queue_row, "get") else False
        rows.append(
            {
                "unit_code": unit_code,
                "unit_label": row.get("unit_label", ""),
                "unit_type": row.get("unit_type", ""),
                "territorial_scope": row.get("territorial_scope", ""),
                "access_category": _excluded_access_category(row),
                "public_status": "Identificada, mas não incluída no corpus do organismo",
                "methodological_decision": "não incorporar ao corpus ativo no MVP",
                "negative_reason": negative_reason,
                "collection_route_attempted": _collection_route_attempted(row),
                "attempt_summary": _attempt_summary(row),
                "methodological_explanation": _excluded_methodological_explanation(row),
                "evidence_status": row.get("evidence_status", ""),
                "protocol_status": row.get("protocol_status", ""),
                "next_step": row.get("next_step", ""),
                "blocks_expansion": blocks_expansion,
                "rule_version": EUROPE_CLOSURE_RULE_VERSION,
            }
        )

    return pd.DataFrame(rows, columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS)


def build_europe_closure_dossier(matrix_df, summary_df, gap_audit_df=None):
    active_df = matrix_df[matrix_df["unit_type"] == "corpus_ativo"] if not matrix_df.empty else pd.DataFrame()
    candidate_df = (
        matrix_df[matrix_df["unit_type"] == "agregador_candidato"] if not matrix_df.empty else pd.DataFrame()
    )
    gap_audit_df = gap_audit_df if gap_audit_df is not None else build_europe_gap_audit()
    queue_df = build_europe_closure_queue(matrix_df)
    opening_status = summary_df.loc[
        summary_df["criterion"] == "abertura_do_proximo_continente",
        "status",
    ].iloc[0]

    lines = [
        "# Dossiê MVP de fechamento metodológico europeu",
        "",
        "## Status do corpus continental",
        f"- Status de abertura: `{opening_status}`.",
        f"- Corpora europeus ativos: `{len(active_df)}`.",
        f"- Candidatos europeus documentados fora do corpus ativo: `{len(candidate_df)}`.",
        "- Escopo: Europa como corpus continental em fechamento metodológico progressivo para artigo e projeto de pós-doutorado.",
        "",
        "## Corpus incorporado",
    ]
    for _, row in active_df.sort_values("unit_code").iterrows():
        lines.append(
            f"- `{row['unit_code']}`: {row['unit_label']} | {row['category']} | "
            f"{row['territorial_scope']} | {row['protocol_status']}."
        )

    lines.extend(["", "## Pendências documentadas"])
    for _, row in candidate_df.sort_values("unit_code").iterrows():
        lines.append(
            f"- `{row['unit_code']}`: {row['unit_label']} | {row['protocol_status']} | "
            f"decisão: {row['incorporation_decision']}."
        )

    lines.extend(["", "## Fila europeia pendente"])
    for _, row in queue_df.head(5).iterrows():
        lines.append(
            f"- Prioridade {row['priority']} | `{row['unit_code']}`: {row['queue_status']} | {row['next_step']}."
        )

    lines.extend(["", "## Lacunas auditadas sem bloqueio"])
    for _, row in gap_audit_df.sort_values("unit_code").iterrows():
        lines.append(
            f"- `{row['unit_code']}`: {row['unit_label']} | {row['audit_status']} | "
            f"decisão: {row['corpus_decision']}."
        )

    lines.extend(
        [
            "",
            "## Índice de dados públicos",
            "- O índice de dados públicos mede apenas registros audiovisuais materializados no organismo.",
            "- Registros restritos entram no índice somente quando pertencem a corpus ativo e têm volume quantificável.",
            "- Bancos privados/publicitários de imagens ficam fora do índice estatístico, mesmo quando o acervo audiovisual é confirmado.",
            "- Esses bancos permanecem documentados na auditoria de acesso pago/restrito e no registro de unidades não incorporadas.",
        ]
    )

    lines.extend(
        [
            "",
            "## Regra metodológica",
            "- Retorno zero, falha técnica ou rota instável não equivalem à ausência de acervo audiovisual.",
            "- Agregadores e arquivos permanecem separados para preservar rigor científico.",
            "- Fechamento continental não significa exaustão de todos os arquivos nacionais, regionais ou institucionais.",
            "- A identificação de arquivos individuais deve avançar por fila auditável: agregadores primeiro, diretórios especializados depois, arquivos individuais por expansão controlada.",
            "- A expansão continental seguinte só deve ocorrer sem apagar o monitoramento europeu mensal.",
        ]
    )
    return "\n".join(lines) + "\n"


def merge_existing_excluded_units(output_dir, excluded_units_df):
    existing_path = Path(output_dir) / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME
    if existing_path.exists():
        existing_df = pd.read_csv(existing_path)
    else:
        existing_df = pd.DataFrame(columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS)

    merged_df = pd.concat([existing_df, excluded_units_df], ignore_index=True)
    normalized_df = (
        merged_df.drop_duplicates(subset=["unit_code"], keep="last")
        .reindex(columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS)
        .sort_values("unit_label")
        .reset_index(drop=True)
    )
    normalized_df["access_category"] = (
        normalized_df["access_category"]
        .fillna("")
        .astype(str)
        .str.strip()
        .replace("", "rota_publica_nao_estavel_ou_nao_coletavel")
    )
    return normalized_df


def write_europe_closure_outputs(output_dir: Path = OUTPUT_DIR):
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_europe_closure_outputs(
        evaluation_df=_load_csv_if_exists(output_dir, EUROPEAN_AGGREGATOR_EVALUATION_FILENAME),
        protocols_df=_load_csv_if_exists(output_dir, EUROPEAN_AGGREGATOR_PROTOCOLS_FILENAME),
        archiveshub_protocol_df=_load_csv_if_exists(output_dir, ARCHIVESHUB_PROTOCOL_FILENAME),
        francearchives_protocol_df=_load_csv_if_exists(output_dir, FRANCEARCHIVES_PROTOCOL_FILENAME),
        european_film_gateway_protocol_df=_load_csv_if_exists(output_dir, EUROPEAN_FILM_GATEWAY_PROTOCOL_FILENAME),
        europeana_protocol_df=_load_csv_if_exists(output_dir, EUROPEANA_PROTOCOL_FILENAME),
    )
    outputs["matrix"].to_csv(
        output_dir / EUROPE_CLOSURE_MATRIX_FILENAME,
        index=False,
        encoding="utf-8-sig",
    )
    outputs["summary"].to_csv(
        output_dir / EUROPE_CLOSURE_SUMMARY_FILENAME,
        index=False,
        encoding="utf-8-sig",
    )
    outputs["queue"].to_csv(
        output_dir / EUROPE_CLOSURE_QUEUE_FILENAME,
        index=False,
        encoding="utf-8-sig",
    )
    outputs["excluded_units"] = merge_existing_excluded_units(output_dir, outputs["excluded_units"])
    outputs["excluded_units"].to_csv(
        output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
        index=False,
        encoding="utf-8-sig",
    )
    outputs["gap_audit"].to_csv(
        output_dir / EUROPE_CLOSURE_GAP_AUDIT_FILENAME,
        index=False,
        encoding="utf-8-sig",
    )
    outputs["dossier"] = build_europe_closure_dossier(
        outputs["matrix"],
        outputs["summary"],
        outputs["gap_audit"],
    )
    (output_dir / EUROPE_CLOSURE_DOSSIER_FILENAME).write_text(outputs["dossier"], encoding="utf-8")
    return outputs


__all__ = [
    "EUROPE_CLOSURE_DOSSIER_FILENAME",
    "EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS",
    "EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME",
    "EUROPE_CLOSURE_GAP_AUDIT_COLUMNS",
    "EUROPE_CLOSURE_GAP_AUDIT_FILENAME",
    "EUROPE_CLOSURE_MATRIX_COLUMNS",
    "EUROPE_CLOSURE_MATRIX_FILENAME",
    "EUROPE_CLOSURE_QUEUE_COLUMNS",
    "EUROPE_CLOSURE_QUEUE_FILENAME",
    "EUROPE_CLOSURE_RULE_VERSION",
    "EUROPE_CLOSURE_SUMMARY_COLUMNS",
    "EUROPE_CLOSURE_SUMMARY_FILENAME",
    "CINEMATHEQUE_SUISSE_NON_INCORPORATION_CATEGORY",
    "CINEMATHEQUE_SUISSE_NON_INCORPORATION_DECISION",
    "CINETECA_ITALIANA_NON_INCORPORATION_CATEGORY",
    "build_europe_closure_dossier",
    "build_europe_closure_queue",
    "build_europe_closure_outputs",
    "build_europe_excluded_units_register",
    "build_europe_gap_audit",
    "merge_existing_excluded_units",
    "write_europe_closure_outputs",
]
