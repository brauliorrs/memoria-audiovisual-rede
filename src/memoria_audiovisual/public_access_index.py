from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd

from .atresmedia_protocol import ATRESMEDIA_ACCESS_CATEGORY
from .config import OUTPUT_DIR
from .corpora import CORPUS_CATEGORIES, list_active_corpora
from .europe_closure import EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME
from .restricted_access_audit import (
    COMMERCIAL_LICENSING_CATEGORY,
    ONSITE_AUTHORIZED_MEDIA_CATEGORY,
    PAID_AUTHENTICATED_STREAMING_CATEGORY,
    RESTRICTED_ACCESS_AUDIT_FILENAME,
    build_restricted_access_audit,
)


PUBLIC_ACCESS_INDEX_FILENAME = "observatorio_indice_dados_publicos.csv"
PUBLIC_ACCESS_INDEX_BY_CORPUS_FILENAME = "observatorio_indice_dados_publicos_por_corpus.csv"
PUBLIC_ACCESS_RESTRICTED_UNITS_FILENAME = "observatorio_unidades_acesso_restrito_indice.csv"
PUBLIC_ACCESS_INDEX_RULE_VERSION = "2026-06-indice-dados-publicos-v2"

PUBLIC_RECORD_STATUS = "publico_materializado"
RESTRICTED_RECORD_STATUS = "restrito_autorizacao_cadastro_pagamento"
NON_QUANTIFIED_RESTRICTED_STATUS = "restrito_sem_catalogo_publico_quantificavel"

RESTRICTED_ACCESS_SURFACES = {
    "Catálogo comercial de licenciamento",
    "Streaming pago/autenticado em plataforma externa",
    "Streaming com login/cadastro obrigatório",
    "Streaming institucional com acesso pago ou por ingresso",
    "Streaming institucional com restrição territorial",
    "Metadados audiovisuais públicos com mídia local/autorizada",
}

RESTRICTED_ACCESS_CATEGORIES = {
    COMMERCIAL_LICENSING_CATEGORY,
    ONSITE_AUTHORIZED_MEDIA_CATEGORY,
    PAID_AUTHENTICATED_STREAMING_CATEGORY,
}

EXCLUDED_RESTRICTED_ACCESS_INDEX_CATEGORIES = {
    ATRESMEDIA_ACCESS_CATEGORY,
}

PUBLIC_ACCESS_INDEX_COLUMNS = [
    "scope_level",
    "scope",
    "public_records",
    "restricted_records",
    "materialized_records_total",
    "public_records_percent",
    "restricted_records_percent",
    "active_corpora_with_records",
    "corpora_with_public_records",
    "corpora_with_restricted_records",
    "restricted_units_total",
    "restricted_units_with_quantified_records",
    "restricted_units_without_public_catalog",
    "restricted_unit_codes",
    "denominator_note",
    "interpretation",
    "rule_version",
]

PUBLIC_ACCESS_CORPUS_COLUMNS = [
    "corpus_code",
    "corpus",
    "short_label",
    "category_code",
    "category_label",
    "continent",
    "public_records",
    "restricted_records",
    "materialized_records_total",
    "public_records_percent",
    "restricted_records_percent",
    "has_public_records",
    "has_restricted_records",
    "denominator_note",
    "rule_version",
]

PUBLIC_ACCESS_RESTRICTED_UNIT_COLUMNS = [
    "unit_code",
    "unit_label",
    "continent",
    "corpus_status",
    "access_category",
    "category_label",
    "restricted_records",
    "restricted_volume_status",
    "requires_authorization_registration_or_payment",
    "source_file",
    "evidence",
    "rule_version",
]


def _read_csv(path):
    path = Path(path)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def _normalize_text(value):
    text = unicodedata.normalize("NFKD", str(value or "").strip().lower())
    return "".join(char for char in text if not unicodedata.combining(char))


def _normalize_continent(value):
    text = str(value or "").strip()
    if not text:
        return "Nao classificado"
    if text in {"Nao classificado", "Não classificado"}:
        return "Nao classificado"
    return text


def _infer_continent_from_scope(value):
    text = _normalize_text(value)
    if not text:
        return "Nao classificado"
    if any(token in text for token in ["europa", "europe", "espanha", "franca", "alemanha", "portugal", "italia", "romenia"]):
        return "Europe"
    if any(token in text for token in ["america do norte", "north america", "estados unidos", "united states", "eua"]):
        return "North America"
    if any(token in text for token in ["america do sul", "south america", "brasil", "argentina", "chile"]):
        return "South America"
    if any(token in text for token in ["africa"]):
        return "Africa"
    if any(token in text for token in ["asia"]):
        return "Asia"
    if any(token in text for token in ["oceania"]):
        return "Oceania"
    return "Nao classificado"


def _mode_or_default(series, default="Nao classificado"):
    if series is None or series.empty:
        return default
    values = [str(value).strip() for value in series.dropna().tolist() if str(value).strip()]
    if not values:
        return default
    return pd.Series(values).mode().iloc[0]


def _percent(part, total):
    total = int(total or 0)
    if total <= 0:
        return 0.0
    return round((int(part or 0) * 100) / total, 2)


def _private_paid_bank_mask(dataframe):
    if dataframe is None or dataframe.empty:
        return pd.Series(dtype=bool)
    mask = dataframe.get("access_category", pd.Series("", index=dataframe.index)).astype(str).isin(
        EXCLUDED_RESTRICTED_ACCESS_INDEX_CATEGORIES
    )
    if "include_in_private_paid_bank_category" in dataframe.columns:
        private_bank_values = (
            dataframe["include_in_private_paid_bank_category"]
            .astype(str)
            .str.strip()
            .str.lower()
            .isin({"true", "1", "sim", "yes"})
        )
        mask = mask | private_bank_values
    return mask


def classify_record_public_access(row):
    access_surface = str(row.get("access_surface", "")).strip()
    row_text = " | ".join(str(value) for value in row.fillna("").tolist())
    if access_surface in RESTRICTED_ACCESS_SURFACES:
        return RESTRICTED_RECORD_STATUS
    if re.search(
        r"compra/login|autenticad|autoriza|onsite|licenciamento|catálogo comercial|catalogo comercial|ingresso|georrestri[cç][aã]o|\b\d+\s*(?:RON|EUR|USD|BRL)\b",
        row_text,
        flags=re.IGNORECASE,
    ):
        return RESTRICTED_RECORD_STATUS
    return PUBLIC_RECORD_STATUS


def build_public_access_record_frame(output_dir=OUTPUT_DIR):
    rows = []
    for corpus_def in list_active_corpora(monthly_only=True):
        catalog_filename = corpus_def["output_files"].get("analytic_video_catalog")
        if not catalog_filename:
            continue
        catalog_df = _read_csv(Path(output_dir) / catalog_filename)
        if catalog_df.empty:
            continue
        category_def = CORPUS_CATEGORIES[corpus_def["category_code"]]
        working_df = catalog_df.copy()
        if "continent" not in working_df.columns:
            working_df["continent"] = "Nao classificado"
        working_df["continent"] = working_df["continent"].apply(_normalize_continent)
        working_df["corpus_code"] = corpus_def["code"]
        working_df["corpus"] = corpus_def["label"]
        working_df["short_label"] = corpus_def["short_label"]
        working_df["category_code"] = corpus_def["category_code"]
        working_df["category_label"] = category_def["label"]
        working_df["public_access_status"] = working_df.apply(classify_record_public_access, axis=1)
        working_df["source_file"] = catalog_filename
        rows.append(working_df)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def build_public_access_restricted_units(record_df=None, output_dir=OUTPUT_DIR):
    record_df = record_df if record_df is not None else build_public_access_record_frame(output_dir)
    audit_path = Path(output_dir) / RESTRICTED_ACCESS_AUDIT_FILENAME
    audit_df = _read_csv(audit_path)
    if audit_df.empty:
        audit_df = build_restricted_access_audit(output_dir)
    if audit_df.empty:
        return pd.DataFrame(columns=PUBLIC_ACCESS_RESTRICTED_UNIT_COLUMNS)
    audit_df = audit_df.loc[~_private_paid_bank_mask(audit_df)].copy()
    if audit_df.empty:
        return pd.DataFrame(columns=PUBLIC_ACCESS_RESTRICTED_UNIT_COLUMNS)

    excluded_df = _read_csv(Path(output_dir) / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME)
    excluded_by_code = {
        str(row.get("unit_code", "")): row
        for _, row in excluded_df.iterrows()
        if str(row.get("unit_code", "")).strip()
    }

    rows = []
    for _, row in audit_df.iterrows():
        unit_code = str(row.get("unit_code", "")).strip()
        total_records = pd.to_numeric(row.get("total_records", 0), errors="coerce")
        restricted_records = int(total_records) if pd.notna(total_records) else 0
        if restricted_records > 0 and record_df is not None and not record_df.empty:
            continent = _mode_or_default(record_df.loc[record_df["corpus_code"] == unit_code, "continent"])
        else:
            excluded_row = excluded_by_code.get(unit_code, {})
            continent = _infer_continent_from_scope(excluded_row.get("territorial_scope", ""))
        rows.append(
            {
                "unit_code": unit_code,
                "unit_label": row.get("unit_label", ""),
                "continent": continent,
                "corpus_status": row.get("corpus_status", ""),
                "access_category": row.get("access_category", ""),
                "category_label": row.get("category_label", ""),
                "restricted_records": restricted_records,
                "restricted_volume_status": (
                    "quantificado_em_corpus_ativo"
                    if restricted_records > 0
                    else NON_QUANTIFIED_RESTRICTED_STATUS
                ),
                "requires_authorization_registration_or_payment": True,
                "source_file": row.get("source_file", ""),
                "evidence": row.get("evidence", ""),
                "rule_version": PUBLIC_ACCESS_INDEX_RULE_VERSION,
            }
        )
    return pd.DataFrame(rows, columns=PUBLIC_ACCESS_RESTRICTED_UNIT_COLUMNS)


def _build_scope_row(scope_level, scope, scoped_records_df, scoped_restricted_units_df):
    public_records = int((scoped_records_df.get("public_access_status", pd.Series(dtype=str)) == PUBLIC_RECORD_STATUS).sum())
    restricted_records = int((scoped_records_df.get("public_access_status", pd.Series(dtype=str)) == RESTRICTED_RECORD_STATUS).sum())
    total_records = public_records + restricted_records
    corpora_with_records = int(scoped_records_df["corpus_code"].nunique()) if not scoped_records_df.empty else 0
    corpora_with_public = (
        int(scoped_records_df.loc[scoped_records_df["public_access_status"] == PUBLIC_RECORD_STATUS, "corpus_code"].nunique())
        if not scoped_records_df.empty
        else 0
    )
    corpora_with_restricted = (
        int(scoped_records_df.loc[scoped_records_df["public_access_status"] == RESTRICTED_RECORD_STATUS, "corpus_code"].nunique())
        if not scoped_records_df.empty
        else 0
    )
    restricted_units_total = int(scoped_restricted_units_df["unit_code"].nunique()) if not scoped_restricted_units_df.empty else 0
    restricted_units_quantified = (
        int(scoped_restricted_units_df.loc[scoped_restricted_units_df["restricted_records"] > 0, "unit_code"].nunique())
        if not scoped_restricted_units_df.empty
        else 0
    )
    restricted_units_without_public_catalog = (
        int(scoped_restricted_units_df.loc[scoped_restricted_units_df["restricted_records"] <= 0, "unit_code"].nunique())
        if not scoped_restricted_units_df.empty
        else 0
    )
    restricted_unit_codes = (
        ", ".join(sorted(scoped_restricted_units_df["unit_code"].dropna().astype(str).unique()))
        if not scoped_restricted_units_df.empty
        else ""
    )
    denominator_note = (
        "Percentual calculado somente sobre registros audiovisuais materializados no organismo."
        if total_records
        else "Sem registros audiovisuais materializados para este recorte."
    )
    if restricted_units_without_public_catalog:
        denominator_note = (
            f"{denominator_note} Há {restricted_units_without_public_catalog} unidade(s) restrita(s) sem volume "
            "quantificável porque não há catálogo público coletável."
        )
    interpretation = (
        "Índice alto indica predominância de registros materializados em superfície pública; "
        "registros pagos, autenticados ou de licenciamento ficam separados do denominador público."
    )
    return {
        "scope_level": scope_level,
        "scope": scope,
        "public_records": public_records,
        "restricted_records": restricted_records,
        "materialized_records_total": total_records,
        "public_records_percent": _percent(public_records, total_records),
        "restricted_records_percent": _percent(restricted_records, total_records),
        "active_corpora_with_records": corpora_with_records,
        "corpora_with_public_records": corpora_with_public,
        "corpora_with_restricted_records": corpora_with_restricted,
        "restricted_units_total": restricted_units_total,
        "restricted_units_with_quantified_records": restricted_units_quantified,
        "restricted_units_without_public_catalog": restricted_units_without_public_catalog,
        "restricted_unit_codes": restricted_unit_codes,
        "denominator_note": denominator_note,
        "interpretation": interpretation,
        "rule_version": PUBLIC_ACCESS_INDEX_RULE_VERSION,
    }


def build_public_access_index(output_dir=OUTPUT_DIR):
    record_df = build_public_access_record_frame(output_dir)
    restricted_units_df = build_public_access_restricted_units(record_df, output_dir)

    index_rows = [
        _build_scope_row("world", "World", record_df, restricted_units_df),
    ]
    continents = sorted(
        set(record_df.get("continent", pd.Series(dtype=str)).dropna().astype(str).tolist())
        | set(restricted_units_df.get("continent", pd.Series(dtype=str)).dropna().astype(str).tolist())
    )
    for continent in [continent for continent in continents if continent]:
        index_rows.append(
            _build_scope_row(
                "continent",
                continent,
                record_df.loc[record_df["continent"] == continent] if not record_df.empty else record_df,
                restricted_units_df.loc[restricted_units_df["continent"] == continent] if not restricted_units_df.empty else restricted_units_df,
            )
        )

    corpus_rows = []
    for corpus_def in list_active_corpora(monthly_only=True):
        scoped_df = record_df.loc[record_df["corpus_code"] == corpus_def["code"]] if not record_df.empty else pd.DataFrame()
        public_records = int((scoped_df.get("public_access_status", pd.Series(dtype=str)) == PUBLIC_RECORD_STATUS).sum())
        restricted_records = int((scoped_df.get("public_access_status", pd.Series(dtype=str)) == RESTRICTED_RECORD_STATUS).sum())
        total_records = public_records + restricted_records
        corpus_rows.append(
            {
                "corpus_code": corpus_def["code"],
                "corpus": corpus_def["label"],
                "short_label": corpus_def["short_label"],
                "category_code": corpus_def["category_code"],
                "category_label": CORPUS_CATEGORIES[corpus_def["category_code"]]["label"],
                "continent": _mode_or_default(scoped_df.get("continent", pd.Series(dtype=str))),
                "public_records": public_records,
                "restricted_records": restricted_records,
                "materialized_records_total": total_records,
                "public_records_percent": _percent(public_records, total_records),
                "restricted_records_percent": _percent(restricted_records, total_records),
                "has_public_records": public_records > 0,
                "has_restricted_records": restricted_records > 0,
                "denominator_note": (
                    "Percentual calculado sobre registros materializados do corpus."
                    if total_records
                    else "Corpus sem registros audiovisuais materializados neste snapshot."
                ),
                "rule_version": PUBLIC_ACCESS_INDEX_RULE_VERSION,
            }
        )

    return {
        "index": pd.DataFrame(index_rows, columns=PUBLIC_ACCESS_INDEX_COLUMNS),
        "by_corpus": pd.DataFrame(corpus_rows, columns=PUBLIC_ACCESS_CORPUS_COLUMNS),
        "restricted_units": restricted_units_df,
    }


def write_public_access_index(output_dir=OUTPUT_DIR):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_public_access_index(output_dir)
    outputs["index"].to_csv(output_dir / PUBLIC_ACCESS_INDEX_FILENAME, index=False, encoding="utf-8-sig")
    outputs["by_corpus"].to_csv(output_dir / PUBLIC_ACCESS_INDEX_BY_CORPUS_FILENAME, index=False, encoding="utf-8-sig")
    outputs["restricted_units"].to_csv(output_dir / PUBLIC_ACCESS_RESTRICTED_UNITS_FILENAME, index=False, encoding="utf-8-sig")
    return outputs


__all__ = [
    "EXCLUDED_RESTRICTED_ACCESS_INDEX_CATEGORIES",
    "NON_QUANTIFIED_RESTRICTED_STATUS",
    "PUBLIC_ACCESS_INDEX_BY_CORPUS_FILENAME",
    "PUBLIC_ACCESS_INDEX_COLUMNS",
    "PUBLIC_ACCESS_INDEX_FILENAME",
    "PUBLIC_ACCESS_INDEX_RULE_VERSION",
    "PUBLIC_ACCESS_RESTRICTED_UNITS_FILENAME",
    "PUBLIC_RECORD_STATUS",
    "RESTRICTED_RECORD_STATUS",
    "build_public_access_index",
    "build_public_access_record_frame",
    "build_public_access_restricted_units",
    "classify_record_public_access",
    "write_public_access_index",
]
