from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import OUTPUT_DIR
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
EUROPE_CLOSURE_RULE_VERSION = "2026-05-fechamento-europa-v1"

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


def _protocol_count(protocol_df):
    return int(len(protocol_df)) if protocol_df is not None and not protocol_df.empty else 0


def _protocol_status_for_candidate(code, specific_protocol_df, protocol_row=None):
    if specific_protocol_df is None or specific_protocol_df.empty:
        if protocol_row is None:
            return "sem_prototipo_especifico_materializado"
        decision = str(protocol_row.get("incorporation_decision", ""))
        if decision == "pode_ser_tratado_como_corpus_experimental":
            return "protocolo_generico_indica_pipeline_experimental"
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
            if incorporation_decision == "pode_ser_tratado_como_corpus_experimental" and protocol_row is not None
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

    active_european_corpora = int((matrix_df["unit_type"] == "corpus_ativo").sum()) if not matrix_df.empty else 0
    pending_candidates = int((matrix_df["unit_type"] == "agregador_candidato").sum()) if not matrix_df.empty else 0
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
            "evidence": f"{len(queue_df)} unidades ordenadas na fila europeia",
            "interpretation": (
                "A fila explicita o que deve virar pipeline, o que permanece protocolado e o que "
                "segue apenas em monitoramento mensal."
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
                "mas não devem ser tratados como corpora ativos sem rota técnica estável."
            ),
            "next_step": "testar_rotas_controladas_sem_misturar_com_corpora_ativos",
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
    ]
    summary_df = pd.DataFrame(summary_rows, columns=EUROPE_CLOSURE_SUMMARY_COLUMNS)
    return {
        "matrix": matrix_df,
        "queue": queue_df,
        "summary": summary_df,
    }


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
            priority = 9
            queue_status = "monitoramento_mensal"
            queue_reason = "Corpus europeu já incorporado; precisa apenas permanecer no ciclo mensal."
        elif protocol_status == "sem_prototipo_especifico_materializado":
            priority = 1
            queue_status = "protocolar_antes_da_expansao"
            queue_reason = "Candidato europeu sem protocolo suficiente para fechamento continental."
        elif incorporation_decision == "pode_ser_tratado_como_corpus_experimental":
            priority = 2
            queue_status = "preparar_pipeline_experimental"
            queue_reason = "A sondagem indica rota pública suficiente para corpus experimental."
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


def build_europe_closure_dossier(matrix_df, summary_df):
    active_df = matrix_df[matrix_df["unit_type"] == "corpus_ativo"] if not matrix_df.empty else pd.DataFrame()
    candidate_df = (
        matrix_df[matrix_df["unit_type"] == "agregador_candidato"] if not matrix_df.empty else pd.DataFrame()
    )
    queue_df = build_europe_closure_queue(matrix_df)
    opening_status = summary_df.loc[
        summary_df["criterion"] == "abertura_do_proximo_continente",
        "status",
    ].iloc[0]

    lines = [
        "# Dossiê MVP de fechamento europeu",
        "",
        "## Status do corpus continental",
        f"- Status de abertura: `{opening_status}`.",
        f"- Corpora europeus ativos: `{len(active_df)}`.",
        f"- Candidatos europeus documentados fora do corpus ativo: `{len(candidate_df)}`.",
        "- Escopo: Europa como corpus continental fechado para artigo e projeto de pós-doutorado.",
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

    lines.extend(["", "## Fila europeia"])
    for _, row in queue_df.loc[queue_df["priority"] < 9].head(5).iterrows():
        lines.append(
            f"- Prioridade {row['priority']} | `{row['unit_code']}`: {row['queue_status']} | {row['next_step']}."
        )

    lines.extend(
        [
            "",
            "## Regra metodológica",
            "- Retorno zero, falha técnica ou rota instável não equivalem à ausência de acervo audiovisual.",
            "- Agregadores e arquivos permanecem separados para preservar rigor científico.",
            "- A expansão continental seguinte só deve ocorrer sem apagar o monitoramento europeu mensal.",
        ]
    )
    return "\n".join(lines) + "\n"


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
    outputs["dossier"] = build_europe_closure_dossier(outputs["matrix"], outputs["summary"])
    (output_dir / EUROPE_CLOSURE_DOSSIER_FILENAME).write_text(outputs["dossier"], encoding="utf-8")
    return outputs


__all__ = [
    "EUROPE_CLOSURE_DOSSIER_FILENAME",
    "EUROPE_CLOSURE_MATRIX_COLUMNS",
    "EUROPE_CLOSURE_MATRIX_FILENAME",
    "EUROPE_CLOSURE_QUEUE_COLUMNS",
    "EUROPE_CLOSURE_QUEUE_FILENAME",
    "EUROPE_CLOSURE_RULE_VERSION",
    "EUROPE_CLOSURE_SUMMARY_COLUMNS",
    "EUROPE_CLOSURE_SUMMARY_FILENAME",
    "build_europe_closure_dossier",
    "build_europe_closure_queue",
    "build_europe_closure_outputs",
    "write_europe_closure_outputs",
]
