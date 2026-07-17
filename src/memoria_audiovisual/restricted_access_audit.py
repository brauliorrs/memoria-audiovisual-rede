from __future__ import annotations

from pathlib import Path

import pandas as pd

from .atresmedia_protocol import ATRESMEDIA_ACCESS_CATEGORY
from .config import OUTPUT_DIR
from .corpora import list_active_corpora
from .europe_closure import CINEMATHEQUE_SUISSE_NON_INCORPORATION_CATEGORY, EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME


RESTRICTED_ACCESS_AUDIT_FILENAME = "observatorio_auditoria_acesso_pago_restrito.csv"
RESTRICTED_ACCESS_SUMMARY_FILENAME = "observatorio_resumo_acesso_pago_restrito.csv"
RESTRICTED_ACCESS_AUDIT_RULE_VERSION = "2026-06-acesso-pago-restrito-v1"

COMMERCIAL_LICENSING_CATEGORY = "catalogo_comercial_de_licenciamento_em_corpus_ativo"
PAID_AUTHENTICATED_STREAMING_CATEGORY = "streaming_pago_autenticado_em_corpus_ativo"
ONSITE_AUTHORIZED_MEDIA_CATEGORY = "midia_local_autorizada_em_corpus_ativo"
GENERIC_UNSTABLE_CATEGORY = "rota_publica_nao_estavel_ou_nao_coletavel"

RESTRICTED_ACCESS_AUDIT_COLUMNS = [
    "unit_code",
    "unit_label",
    "corpus_status",
    "access_category",
    "category_label",
    "total_records",
    "evidence",
    "methodological_decision",
    "include_in_private_paid_bank_category",
    "source_file",
    "example_titles",
    "rule_version",
]

RESTRICTED_ACCESS_SUMMARY_COLUMNS = [
    "access_category",
    "category_label",
    "units",
    "records",
    "interpretation",
    "rule_version",
]


def _read_csv(path):
    if not Path(path).exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _example_titles(df, limit=3):
    if df.empty:
        return ""
    title_columns = ["video_title_display", "title", "video_title"]
    examples = []
    for _, row in df.head(limit).iterrows():
        title = next((str(row.get(column, "")).strip() for column in title_columns if str(row.get(column, "")).strip()), "")
        platform = str(row.get("platform", "")).strip()
        access_surface = str(row.get("access_surface", "")).strip()
        label = " / ".join(value for value in [platform, access_surface, title] if value)
        if label:
            examples.append(label)
    return " || ".join(examples)


def _add_excluded_private_bank_rows(rows, output_dir):
    excluded_df = _read_csv(Path(output_dir) / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME)
    if excluded_df.empty or "access_category" not in excluded_df.columns:
        return
    private_df = excluded_df.loc[excluded_df["access_category"].astype(str) == ATRESMEDIA_ACCESS_CATEGORY]
    for _, row in private_df.iterrows():
        rows.append(
            {
                "unit_code": row.get("unit_code", ""),
                "unit_label": row.get("unit_label", ""),
                "corpus_status": "fora_do_corpus_ativo",
                "access_category": ATRESMEDIA_ACCESS_CATEGORY,
                "category_label": "Banco privado de imagens e vídeos com acesso restrito e pagamento",
                "total_records": "",
                "evidence": row.get("attempt_summary", ""),
                "methodological_decision": (
                    "Categoria estrita: portal/banco privado com fluxo comercial, autenticação e pagamento, "
                    "sem catálogo público completo coletável."
                ),
                "include_in_private_paid_bank_category": True,
                "source_file": EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
                "example_titles": "",
                "rule_version": RESTRICTED_ACCESS_AUDIT_RULE_VERSION,
            }
        )


def _add_excluded_restricted_rows(rows, output_dir):
    excluded_df = _read_csv(Path(output_dir) / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME)
    if excluded_df.empty or "access_category" not in excluded_df.columns:
        return
    restricted_df = excluded_df.loc[
        excluded_df["access_category"].astype(str) == CINEMATHEQUE_SUISSE_NON_INCORPORATION_CATEGORY
    ]
    for _, row in restricted_df.iterrows():
        rows.append(
            {
                "unit_code": row.get("unit_code", ""),
                "unit_label": row.get("unit_label", ""),
                "corpus_status": "fora_do_corpus_ativo",
                "access_category": CINEMATHEQUE_SUISSE_NON_INCORPORATION_CATEGORY,
                "category_label": "Metadados públicos com mídia local/autorizada, sem vídeo público incorporável",
                "total_records": "",
                "evidence": row.get("attempt_summary", ""),
                "methodological_decision": row.get("methodological_explanation", ""),
                "include_in_private_paid_bank_category": False,
                "source_file": EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
                "example_titles": "",
                "rule_version": RESTRICTED_ACCESS_AUDIT_RULE_VERSION,
            }
        )


def _add_active_corpus_rows(rows, output_dir):
    corpus_by_catalog = {
        corpus_def["output_files"].get("analytic_video_catalog"): corpus_def
        for corpus_def in list_active_corpora(monthly_only=True)
    }
    for catalog_filename, corpus_def in sorted(corpus_by_catalog.items()):
        if not catalog_filename:
            continue
        catalog_path = Path(output_dir) / catalog_filename
        df = _read_csv(catalog_path)
        if df.empty:
            continue
        corpus_code = corpus_def.get("code", catalog_path.name.replace("_catalogo_videos_analitico.csv", ""))
        corpus_label = corpus_def.get("label", corpus_code)
        if "access_surface" in df.columns:
            licensing_df = df.loc[df["access_surface"].astype(str) == "Catálogo comercial de licenciamento"]
            if not licensing_df.empty:
                rows.append(
                    {
                        "unit_code": corpus_code,
                        "unit_label": corpus_label,
                        "corpus_status": "corpus_ativo",
                        "access_category": COMMERCIAL_LICENSING_CATEGORY,
                        "category_label": "Catálogo comercial de licenciamento em corpus ativo",
                        "total_records": int(len(licensing_df)),
                        "evidence": "Registros classificados como Catálogo comercial de licenciamento.",
                        "methodological_decision": (
                            "Não é banco privado fora do corpus: há registros públicos suficientes para análise, "
                            "mas a modalidade de acesso é comercial/licenciamento."
                        ),
                        "include_in_private_paid_bank_category": False,
                        "source_file": catalog_path.name,
                        "example_titles": _example_titles(licensing_df),
                        "rule_version": RESTRICTED_ACCESS_AUDIT_RULE_VERSION,
                    }
                )
            onsite_df = df.loc[df["access_surface"].astype(str) == "Metadados audiovisuais públicos com mídia local/autorizada"]
            if not onsite_df.empty:
                rows.append(
                    {
                        "unit_code": corpus_code,
                        "unit_label": corpus_label,
                        "corpus_status": "corpus_ativo",
                        "access_category": ONSITE_AUTHORIZED_MEDIA_CATEGORY,
                        "category_label": "Mídia local/autorizada em corpus ativo",
                        "total_records": int(len(onsite_df)),
                        "evidence": "Registros com metadados públicos e mídia indicada como acesso onsite/autorizado.",
                        "methodological_decision": (
                            "Há corpus público quantificável, mas o acesso à mídia não é streaming aberto; "
                            "entra no índice como restrito por autorização ou consulta local."
                        ),
                        "include_in_private_paid_bank_category": False,
                        "source_file": catalog_path.name,
                        "example_titles": _example_titles(onsite_df),
                        "rule_version": RESTRICTED_ACCESS_AUDIT_RULE_VERSION,
                    }
                )

        text = df.fillna("").astype(str).agg(" | ".join, axis=1)
        paid_streaming_mask = text.str.contains(
            r"compra/login|login/cadastro|Regime de acesso indicado|\b\d+\s*(?:RON|EUR|USD|BRL)\b",
            case=False,
            regex=True,
            na=False,
        )
        paid_streaming_df = df.loc[paid_streaming_mask]
        if not paid_streaming_df.empty:
            rows.append(
                {
                    "unit_code": corpus_code,
                    "unit_label": corpus_label,
                    "corpus_status": "corpus_ativo",
                    "access_category": PAID_AUTHENTICATED_STREAMING_CATEGORY,
                    "category_label": "Streaming pago/autenticado em corpus ativo",
                    "total_records": int(len(paid_streaming_df)),
                    "evidence": "Registros com preço, compra/login ou acesso autenticado indicado na descrição.",
                    "methodological_decision": (
                        "Não é banco privado de imagens: é uma superfície de exibição/streaming paga ou autenticada "
                        "já materializada no corpus ativo."
                    ),
                    "include_in_private_paid_bank_category": False,
                    "source_file": catalog_path.name,
                    "example_titles": _example_titles(paid_streaming_df),
                    "rule_version": RESTRICTED_ACCESS_AUDIT_RULE_VERSION,
                }
            )


def build_restricted_access_audit(output_dir: Path = OUTPUT_DIR):
    rows = []
    _add_excluded_private_bank_rows(rows, output_dir)
    _add_excluded_restricted_rows(rows, output_dir)
    _add_active_corpus_rows(rows, output_dir)
    return pd.DataFrame(rows, columns=RESTRICTED_ACCESS_AUDIT_COLUMNS)


def build_restricted_access_summary(audit_df):
    if audit_df is None or audit_df.empty:
        return pd.DataFrame(columns=RESTRICTED_ACCESS_SUMMARY_COLUMNS)

    summary_df = (
        audit_df.assign(total_records_numeric=pd.to_numeric(audit_df["total_records"], errors="coerce").fillna(0))
        .groupby(["access_category", "category_label"], dropna=False)
        .agg(units=("unit_code", "nunique"), records=("total_records_numeric", "sum"))
        .reset_index()
    )
    summary_df["records"] = summary_df["records"].astype(int)
    interpretations = {
        ATRESMEDIA_ACCESS_CATEGORY: (
            "Categoria estrita para bancos privados de imagens/vídeos com acesso restrito, monetizado e sem corpus público coletável."
        ),
        COMMERCIAL_LICENSING_CATEGORY: (
            "Modalidade comercial dentro de corpus ativo; não impede análise, mas precisa ser separada de streaming aberto."
        ),
        PAID_AUTHENTICATED_STREAMING_CATEGORY: (
            "Superfície de exibição paga/autenticada dentro de corpus ativo; não equivale a banco privado de licenciamento."
        ),
        ONSITE_AUTHORIZED_MEDIA_CATEGORY: (
            "Registros com metadados públicos e mídia local/autorizada; contam como corpus ativo restrito, não como acesso aberto."
        ),
        CINEMATHEQUE_SUISSE_NON_INCORPORATION_CATEGORY: (
            "Unidade identificada fora do corpus ativo: há metadados públicos, mas não vídeo público incorporável."
        ),
    }
    summary_df["interpretation"] = summary_df["access_category"].map(interpretations).fillna("")
    summary_df["rule_version"] = RESTRICTED_ACCESS_AUDIT_RULE_VERSION
    return summary_df[RESTRICTED_ACCESS_SUMMARY_COLUMNS]


def write_restricted_access_audit(output_dir: Path = OUTPUT_DIR):
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_df = build_restricted_access_audit(output_dir)
    summary_df = build_restricted_access_summary(audit_df)
    audit_df.to_csv(output_dir / RESTRICTED_ACCESS_AUDIT_FILENAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / RESTRICTED_ACCESS_SUMMARY_FILENAME, index=False, encoding="utf-8-sig")
    return {"audit": audit_df, "summary": summary_df}


__all__ = [
    "COMMERCIAL_LICENSING_CATEGORY",
    "CINEMATHEQUE_SUISSE_NON_INCORPORATION_CATEGORY",
    "ONSITE_AUTHORIZED_MEDIA_CATEGORY",
    "PAID_AUTHENTICATED_STREAMING_CATEGORY",
    "RESTRICTED_ACCESS_AUDIT_FILENAME",
    "RESTRICTED_ACCESS_AUDIT_RULE_VERSION",
    "RESTRICTED_ACCESS_SUMMARY_FILENAME",
    "build_restricted_access_audit",
    "build_restricted_access_summary",
    "write_restricted_access_audit",
]
