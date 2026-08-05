from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.i18n import (
    DEFAULT_LANGUAGE,
    LANGUAGE_OPTIONS,
    language_code_from_label,
)
from memoria_audiovisual.organism import (
    ORGANISM_ACTIVE_CORPORA_FILENAME,
    ORGANISM_MONTHLY_CYCLE_FILENAME,
)

OUTPUT_DIR = BASE_DIR / "data" / "output"
PAGE_SIZE = 12

COPY = {
    "pt": {
        "page_title": "Visão Geral — protótipo vertical",
        "eyebrow": "Memória Audiovisual em Rede",
        "title": "Visão Geral",
        "caption": "Protótipo de navegação vertical, responsiva e orientada ao detalhamento progressivo.",
        "prototype": "Protótipo em validação. A Visão Geral atual permanece disponível durante a comparação.",
        "active_corpora": "Corpora ativos",
        "categories": "Categorias",
        "latest_scope": "Escopo da última rodada",
        "latest_status": "Estado da última rodada",
        "not_available": "Não disponível",
        "corpus_state": "Estado do corpus",
        "corpus_state_caption": "Resumo primeiro; detalhes e bases completas somente quando solicitados.",
        "search": "Buscar corpus ou instituição",
        "category": "Categoria",
        "all": "Todas",
        "results": "corpora encontrados",
        "previous": "Anterior",
        "next": "Próxima",
        "page": "Página",
        "of": "de",
        "coverage": "Cobertura",
        "scope": "Escopo",
        "cadence": "Periodicidade",
        "status": "Situação",
        "details": "Ver detalhes",
        "code": "Código",
        "selection": "Critério de seleção",
        "completeness": "Completude",
        "latest_cycle": "Última rodada",
        "full_table": "Abrir tabela técnica completa",
        "full_table_help": "A tabela completa é carregada apenas quando esta seção é aberta.",
        "no_results": "Nenhum corpus corresponde aos filtros selecionados.",
        "missing": "O registro de corpora ativos não está disponível.",
        "method": "Princípios deste protótipo",
        "method_text": "Fluxo de cima para baixo; no máximo duas colunas de métricas; filtros antes dos dados; um corpus por bloco; detalhes e tabela técnica sob demanda.",
    },
    "en": {
        "page_title": "Overview — vertical prototype",
        "eyebrow": "Networked Audiovisual Memory",
        "title": "Overview",
        "caption": "Prototype for vertical, responsive navigation with progressive disclosure.",
        "prototype": "Prototype under validation. The current Overview remains available for comparison.",
        "active_corpora": "Active corpora",
        "categories": "Categories",
        "latest_scope": "Latest cycle scope",
        "latest_status": "Latest cycle status",
        "not_available": "Not available",
        "corpus_state": "Corpus status",
        "corpus_state_caption": "Summary first; details and complete datasets only on request.",
        "search": "Search corpus or institution",
        "category": "Category",
        "all": "All",
        "results": "corpora found",
        "previous": "Previous",
        "next": "Next",
        "page": "Page",
        "of": "of",
        "coverage": "Coverage",
        "scope": "Scope",
        "cadence": "Cadence",
        "status": "Status",
        "details": "View details",
        "code": "Code",
        "selection": "Selection criterion",
        "completeness": "Completeness",
        "latest_cycle": "Latest cycle",
        "full_table": "Open complete technical table",
        "full_table_help": "The complete table is loaded only when this section is opened.",
        "no_results": "No corpus matches the selected filters.",
        "missing": "The active corpus registry is not available.",
        "method": "Prototype principles",
        "method_text": "Top-to-bottom flow; no more than two metric columns; filters before data; one corpus per block; details and technical table on demand.",
    },
    "es": {
        "page_title": "Vista general — prototipo vertical",
        "eyebrow": "Memoria Audiovisual en Red",
        "title": "Vista general",
        "caption": "Prototipo de navegación vertical, adaptable y orientada al detalle progresivo.",
        "prototype": "Prototipo en validación. La Vista general actual permanece disponible para comparación.",
        "active_corpora": "Corpus activos",
        "categories": "Categorías",
        "latest_scope": "Alcance de la última ronda",
        "latest_status": "Estado de la última ronda",
        "not_available": "No disponible",
        "corpus_state": "Estado del corpus",
        "corpus_state_caption": "Primero el resumen; detalles y bases completas solo cuando se solicitan.",
        "search": "Buscar corpus o institución",
        "category": "Categoría",
        "all": "Todas",
        "results": "corpus encontrados",
        "previous": "Anterior",
        "next": "Siguiente",
        "page": "Página",
        "of": "de",
        "coverage": "Cobertura",
        "scope": "Alcance",
        "cadence": "Periodicidad",
        "status": "Situación",
        "details": "Ver detalles",
        "code": "Código",
        "selection": "Criterio de selección",
        "completeness": "Completitud",
        "latest_cycle": "Última ronda",
        "full_table": "Abrir tabla técnica completa",
        "full_table_help": "La tabla completa se carga solamente al abrir esta sección.",
        "no_results": "Ningún corpus coincide con los filtros seleccionados.",
        "missing": "El registro de corpus activos no está disponible.",
        "method": "Principios del prototipo",
        "method_text": "Flujo de arriba abajo; máximo dos columnas de métricas; filtros antes de los datos; un corpus por bloque; detalles y tabla técnica bajo demanda.",
    },
}

st.set_page_config(page_title="Visão Geral", layout="centered")


def text(language: str, key: str) -> str:
    return COPY.get(language, COPY[DEFAULT_LANGUAGE]).get(key, key)


@st.cache_data(show_spinner=False)
def load_active_corpora() -> pd.DataFrame:
    path = OUTPUT_DIR / ORGANISM_ACTIVE_CORPORA_FILENAME
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_cycle_manifest() -> dict:
    path = OUTPUT_DIR / ORGANISM_MONTHLY_CYCLE_FILENAME
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


def first_value(row: pd.Series, *columns: str, default: str = "—") -> str:
    for column in columns:
        if column in row.index:
            value = row.get(column)
            if pd.notna(value) and str(value).strip():
                return str(value)
    return default


labels = list(LANGUAGE_OPTIONS.values())
selected_label = st.sidebar.selectbox(
    "Idioma / Language / Idioma",
    options=labels,
    index=labels.index(LANGUAGE_OPTIONS.get(DEFAULT_LANGUAGE, labels[0])),
    key="vertical_overview_language",
)
language = language_code_from_label(selected_label)

st.markdown(
    """
    <style>
    .block-container {max-width: 920px; padding-top: 2rem; padding-bottom: 4rem;}
    .overview-eyebrow {font-size: .78rem; letter-spacing: .08em; text-transform: uppercase; opacity: .72;}
    .corpus-card {border: 1px solid rgba(128,128,128,.25); border-radius: .8rem; padding: 1rem 1.05rem; margin: .65rem 0;}
    .corpus-card h4 {margin: 0 0 .35rem 0;}
    .corpus-meta {opacity: .78; font-size: .9rem;}
    @media (max-width: 700px) {
      .block-container {padding-left: 1rem; padding-right: 1rem;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(f'<div class="overview-eyebrow">{text(language, "eyebrow")}</div>', unsafe_allow_html=True)
st.title(text(language, "title"))
st.caption(text(language, "caption"))
st.info(text(language, "prototype"))

corpora_df = load_active_corpora()
cycle = load_cycle_manifest()

if corpora_df.empty:
    st.warning(text(language, "missing"))
    st.stop()

category_column = "category_label" if "category_label" in corpora_df.columns else "category_code"
category_count = int(corpora_df[category_column].dropna().nunique()) if category_column in corpora_df.columns else 0
cycle_scope = str(cycle.get("cycle_scope") or cycle.get("scope") or text(language, "not_available"))
cycle_status = str(cycle.get("status") or cycle.get("cycle_status") or text(language, "not_available"))

metric_left, metric_right = st.columns(2)
metric_left.metric(text(language, "active_corpora"), len(corpora_df))
metric_right.metric(text(language, "categories"), category_count)
metric_left, metric_right = st.columns(2)
metric_left.metric(text(language, "latest_scope"), cycle_scope)
metric_right.metric(text(language, "latest_status"), cycle_status)

st.divider()
st.subheader(text(language, "corpus_state"))
st.caption(text(language, "corpus_state_caption"))

filter_left, filter_right = st.columns(2)
with filter_left:
    search_term = st.text_input(text(language, "search"), key="vertical_overview_search")
with filter_right:
    categories = sorted(
        str(value) for value in corpora_df.get(category_column, pd.Series(dtype=str)).dropna().unique()
    )
    selected_category = st.selectbox(
        text(language, "category"),
        options=[text(language, "all"), *categories],
        key="vertical_overview_category",
    )

filtered = corpora_df.copy()
if selected_category != text(language, "all") and category_column in filtered.columns:
    filtered = filtered.loc[filtered[category_column].astype(str) == selected_category]
if search_term.strip():
    searchable_columns = [
        column
        for column in ("corpus", "label", "short_label", "institution", "code", "scope")
        if column in filtered.columns
    ]
    if searchable_columns:
        mask = pd.Series(False, index=filtered.index)
        for column in searchable_columns:
            mask = mask | filtered[column].fillna("").astype(str).str.contains(search_term, case=False, regex=False)
        filtered = filtered.loc[mask]

filtered = filtered.reset_index(drop=True)
st.caption(f"{len(filtered)} {text(language, 'results')}")

if filtered.empty:
    st.info(text(language, "no_results"))
else:
    total_pages = max(1, (len(filtered) + PAGE_SIZE - 1) // PAGE_SIZE)
    current_page = min(int(st.session_state.get("vertical_overview_page", 1)), total_pages)
    start = (current_page - 1) * PAGE_SIZE
    page_df = filtered.iloc[start : start + PAGE_SIZE]

    for _, row in page_df.iterrows():
        title = first_value(row, "corpus", "label", "short_label", "code")
        category = first_value(row, category_column)
        coverage = first_value(row, "coverage_level", "coverage")
        scope = first_value(row, "scope")
        cadence = first_value(row, "refresh_cadence")
        status = first_value(row, "refresh_state", "status")
        st.markdown(
            f"""
            <div class="corpus-card">
              <h4>{title}</h4>
              <div class="corpus-meta">{category} · {text(language, 'coverage')}: {coverage}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander(f"{text(language, 'details')} — {title}", expanded=False):
            st.markdown(f"**{text(language, 'code')}:** `{first_value(row, 'code')}`")
            st.markdown(f"**{text(language, 'scope')}:** {scope}")
            st.markdown(f"**{text(language, 'cadence')}:** {cadence}")
            st.markdown(f"**{text(language, 'status')}:** {status}")
            st.markdown(
                f"**{text(language, 'selection')}:** "
                f"{first_value(row, 'selection_criterion', 'selection_limit')}"
            )
            st.markdown(
                f"**{text(language, 'completeness')}:** "
                f"{first_value(row, 'collection_completeness', 'completeness_note')}"
            )
            st.markdown(
                f"**{text(language, 'latest_cycle')}:** "
                f"{first_value(row, 'last_successful_cycle_at', 'last_snapshot_generated_at')}"
            )

    nav_left, nav_center, nav_right = st.columns([1, 2, 1])
    with nav_left:
        if st.button(text(language, "previous"), disabled=current_page <= 1, use_container_width=True):
            st.session_state["vertical_overview_page"] = current_page - 1
            st.rerun()
    with nav_center:
        st.markdown(
            f"<div style='text-align:center;padding:.45rem'>{text(language, 'page')} {current_page} {text(language, 'of')} {total_pages}</div>",
            unsafe_allow_html=True,
        )
    with nav_right:
        if st.button(text(language, "next"), disabled=current_page >= total_pages, use_container_width=True):
            st.session_state["vertical_overview_page"] = current_page + 1
            st.rerun()

with st.expander(text(language, "full_table"), expanded=False):
    st.caption(text(language, "full_table_help"))
    essential_columns = [
        column
        for column in ("code", "corpus", "category_label", "coverage_level", "scope", "refresh_state")
        if column in corpora_df.columns
    ]
    st.dataframe(
        corpora_df[essential_columns] if essential_columns else corpora_df,
        use_container_width=True,
        hide_index=True,
    )

st.divider()
st.subheader(text(language, "method"))
st.write(text(language, "method_text"))
