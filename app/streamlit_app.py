import sys
import json
from importlib.util import find_spec
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual import analysis as analysis_utils
from memoria_audiovisual.corpora import (
    CORPORA,
    CORPUS_CATEGORIES,
    OBSERVATORY_PROFILE,
    list_corpora_by_category,
)
from memoria_audiovisual.discovery import (
    DISCOVERY_QUEUE_FILENAME,
    DISCOVERY_REGISTRY_FILENAME,
    DISCOVERY_SUMMARY_FILENAME,
    build_discovery_registry,
    build_discovery_summary,
    build_expansion_queue,
)
from memoria_audiovisual.dashboard_data import (
    DASHBOARD_SOURCE_KEYS,
    build_dashboard_base_data,
    build_dashboard_overview_data,
)
from memoria_audiovisual.output_files import list_output_filenames
from memoria_audiovisual.organism import (
    ORGANISM_ACTIVE_CORPORA_FILENAME,
    ORGANISM_CYCLE_RESULTS_FILENAME,
    ORGANISM_CYCLE_TIMELINE_FILENAME,
    ORGANISM_MONTHLY_CYCLE_FILENAME,
    build_active_corpora_registry,
    build_corpus_refresh_status,
)

OUTPUT_DIR = BASE_DIR / "data" / "output"

st.set_page_config(page_title="Memória Audiovisual em Rede", layout="wide")


@st.cache_data(show_spinner=False)
def load_csv(filename):
    path = OUTPUT_DIR / filename
    if not path.exists():
        return None
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_json(filename):
    path = OUTPUT_DIR / filename
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def render_integrity_badge(value):
    colors = {
        "integro": "#2f7d32",
        "acessivel": "#4c8bf5",
        "suspeito": "#8e44ad",
        "restrito": "#d97706",
        "quebrado": "#c62828",
        "instavel": "#6b7280",
        "sem_site": "#475569",
    }
    color = colors.get(str(value), "#6b7280")
    st.markdown(
        f"""
        <div style="display:inline-block;padding:0.3rem 0.7rem;border-radius:999px;
        background:{color};color:white;font-weight:600;font-size:0.9rem;">
        {format_integrity_status(value)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_vimeo_embed_url(url):
    parsed = urlparse(url)
    if parsed.netloc.lower().startswith("player.vimeo.com") and "/video/" in parsed.path:
        return url
    path_parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc.lower().endswith("vimeo.com") and path_parts and path_parts[-1].isdigit():
        return f"https://player.vimeo.com/video/{path_parts[-1]}"
    return None


def prepare_matrix_display(matrix_df):
    if matrix_df.empty:
        return matrix_df

    display_df = matrix_df.copy()
    label_col = display_df.columns[0]
    numeric_cols = [col for col in display_df.columns[1:] if pd.api.types.is_numeric_dtype(display_df[col])]
    if not numeric_cols:
        return display_df

    display_df["Total"] = display_df[numeric_cols].sum(axis=1)
    total_row = {label_col: "Total"}
    for column in numeric_cols:
        total_row[column] = display_df[column].sum()
    total_row["Total"] = display_df["Total"].sum()

    return pd.concat([display_df, pd.DataFrame([total_row])], ignore_index=True)


def style_matrix_display(matrix_df):
    if matrix_df.empty:
        return matrix_df
    if find_spec("matplotlib") is None:
        return matrix_df
    numeric_cols = matrix_df.select_dtypes(include="number").columns.tolist()
    styler = matrix_df.style
    if numeric_cols:
        styler = styler.background_gradient(subset=numeric_cols, cmap="Blues")
    return styler


def dataframe_to_csv_bytes(dataframe):
    if dataframe is None:
        return b""
    return dataframe.to_csv(index=False).encode("utf-8-sig")


def json_to_bytes(payload):
    if payload is None:
        return b""
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def render_csv_download(label, dataframe, filename, help_text):
    if dataframe is None or dataframe.empty:
        st.caption(f"{label}: ainda sem dados para exportação.")
        return
    st.download_button(
        label=label,
        data=dataframe_to_csv_bytes(dataframe),
        file_name=filename,
        mime="text/csv",
        help=help_text,
        use_container_width=True,
    )


def render_json_download(label, payload, filename, help_text):
    if not payload:
        st.caption(f"{label}: ainda sem dados para exportação.")
        return
    st.download_button(
        label=label,
        data=json_to_bytes(payload),
        file_name=filename,
        mime="application/json",
        help=help_text,
        use_container_width=True,
    )


def format_snapshot_timestamp(value):
    text = normalize_optional_text(value)
    if not text:
        return ""
    parsed = pd.to_datetime(text, errors="coerce", utc=True)
    if pd.isna(parsed):
        return text
    return parsed.tz_convert("America/Sao_Paulo").strftime("%Y-%m-%d %H:%M")


NOISE_THEME_LABEL = analysis_utils.NOISE_THEME_LABEL
classify_audiovisual_visibility = analysis_utils.classify_audiovisual_visibility
classify_availability_group = analysis_utils.classify_availability_group
classify_availability_reason = analysis_utils.classify_availability_reason
format_video_date = analysis_utils.format_video_date
infer_video_theme = analysis_utils.infer_video_theme
normalize_optional_text = analysis_utils.normalize_optional_text
normalize_text = analysis_utils.normalize_text

INTEGRITY_STATUS_LABELS = {
    "integro": "íntegro",
    "acessivel": "acessível",
    "suspeito": "suspeito",
    "restrito": "restrito",
    "quebrado": "quebrado",
    "instavel": "instável",
    "sem_site": "sem site",
}
TECHNICAL_STATUS_LABELS = {
    "ok": "ok",
    "erro": "erro",
    "http_error": "erro HTTP",
    "restrito": "restrito",
    "sem_site": "sem site",
}

SEGMENT_AVAILABLE_WITH_VIDEOS = "Dispon\u00edveis com v\u00eddeos"
SEGMENT_AVAILABLE_WITHOUT_VIDEOS = "Dispon\u00edveis sem v\u00eddeos"
SEGMENT_UNAVAILABLE = "Indispon\u00edveis"
SEGMENT_OPTIONS = [
    SEGMENT_AVAILABLE_WITH_VIDEOS,
    SEGMENT_AVAILABLE_WITHOUT_VIDEOS,
    SEGMENT_UNAVAILABLE,
]
SEGMENT_LABEL_ALIASES = {
    "Disponíveis com vídeos": SEGMENT_AVAILABLE_WITH_VIDEOS,
    "Disponíveis sem vídeos": SEGMENT_AVAILABLE_WITHOUT_VIDEOS,
    "Indisponíveis": SEGMENT_UNAVAILABLE,
}


def coerce_segment_label(value):
    text = normalize_optional_text(value)
    return SEGMENT_LABEL_ALIASES.get(text, text)


def format_integrity_status(value):
    text = normalize_optional_text(value)
    return INTEGRITY_STATUS_LABELS.get(text, text or "-")


def format_technical_status(value):
    text = normalize_optional_text(value)
    return TECHNICAL_STATUS_LABELS.get(text, text or "-")


def format_yes_no(value):
    if pd.isna(value):
        return "Não"
    if isinstance(value, str):
        normalized = normalize_optional_text(value).lower()
        if normalized in {"sim", "yes", "true", "1"}:
            return "Sim"
        if normalized in {"não", "nao", "no", "false", "0", ""}:
            return "Não"
    return "Sim" if bool(value) else "Não"


def format_cycle_status(value):
    status_labels = {
        "success": "sucesso",
        "failed": "falha",
    }
    text = normalize_optional_text(value)
    return status_labels.get(text, text or "-")


def build_cross_corpus_history_frame(output_file_key):
    frames = []
    for corpus_def in CORPORA.values():
        history_df = load_csv(corpus_def["output_files"][output_file_key])
        if history_df is None or history_df.empty:
            continue
        working_df = history_df.copy()
        working_df.insert(0, "corpus", corpus_def["short_label"])
        working_df.insert(1, "unidade", corpus_def["label"])
        working_df.insert(2, "categoria_analitica", CORPUS_CATEGORIES[corpus_def["category_code"]]["label"])
        working_df.insert(3, "escala_de_cobertura", corpus_def["coverage_level"])
        frames.append(working_df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def build_summary_display_df(
    dataframe,
    *,
    content_flag_field="content_available_in_ape",
    content_flag_label="conteúdo publicado na fonte",
    detail_url_field="ape_detail_url",
    detail_url_label="ficha da instituição na fonte",
    website_label="site informado na fonte",
):
    if dataframe is None or dataframe.empty:
        return pd.DataFrame()

    display_df = dataframe.copy()
    if "status" in display_df.columns:
        display_df["status_tecnico_display"] = display_df["status"].map(format_technical_status)
    if "integrity_status" in display_df.columns:
        display_df["integridade_display"] = display_df["integrity_status"].map(format_integrity_status)
    if "website_available" in display_df.columns:
        display_df["website_available_display"] = display_df["website_available"].map(format_yes_no)
    if content_flag_field in display_df.columns:
        display_df["content_available_display"] = display_df[content_flag_field].map(format_yes_no)
    if "continent" in display_df.columns:
        display_df["continent"] = display_df["continent"].fillna("Não classificado").replace("", "Não classificado")

    preferred_columns = [
        "institution",
        "slug",
        "country",
        "continent",
        "archive_type",
        "content_available_display",
        "website_available_display",
        "availability_group",
        "availability_reason",
        "audiovisual_visibility",
        "access_regime",
        "access_modalities_detected",
        "institution_segment",
        "integridade_display",
        "status_tecnico_display",
        "http_code",
        "video_links_found_total",
        "embedded_video_signals_total",
        "candidate_internal_pages",
        "partner_domain",
        "partner_site",
        "final_url",
        "warning",
        "error",
        "repository_code",
        detail_url_field,
    ]
    available_columns = [column for column in preferred_columns if column in display_df.columns]
    remaining_columns = [column for column in display_df.columns if column not in available_columns]

    return display_df[available_columns + remaining_columns].rename(
        columns={
            "institution": "instituição",
            "slug": "slug",
            "country": "país",
            "continent": "continente",
            "archive_type": "tipo de arquivo",
            "content_available_display": content_flag_label,
            "website_available_display": website_label,
            "availability_group": "categoria",
            "availability_reason": "subcategoria",
            "audiovisual_visibility": "situação metodológica do audiovisual",
            "access_regime": "regime de acesso audiovisual detectável",
            "access_modalities_detected": "modalidades de acesso detectadas",
            "institution_segment": "segmento institucional",
            "integridade_display": "integridade",
            "status_tecnico_display": "status técnico",
            "http_code": "HTTP",
            "video_links_found_total": "links de vídeo",
            "embedded_video_signals_total": "sinais embutidos",
            "candidate_internal_pages": "páginas internas",
            "partner_domain": "domínio",
            "partner_site": "site externo informado",
            "final_url": "URL final",
            "warning": "observação",
            "error": "erro",
            "repository_code": "código do repositório",
            detail_url_field: detail_url_label,
        }
    )


def build_video_catalog_display_df(
    dataframe,
    *,
    content_flag_field="content_available_in_ape",
    content_flag_label="conteúdo publicado na fonte",
    detail_url_field="ape_detail_url",
    detail_url_label="ficha da instituição na fonte",
    website_label="site informado na fonte",
):
    if dataframe is None or dataframe.empty:
        return pd.DataFrame()

    display_df = dataframe.copy()
    if "website_available" in display_df.columns:
        display_df["website_available_display"] = display_df["website_available"].map(format_yes_no)
    if content_flag_field in display_df.columns:
        display_df["content_available_display"] = display_df[content_flag_field].map(format_yes_no)
    if "continent" in display_df.columns:
        display_df["continent"] = display_df["continent"].fillna("Não classificado").replace("", "Não classificado")

    preferred_columns = [
        "institution",
        "archive_type",
        "country",
        "continent",
        "platform",
        "access_surface",
        "video_theme",
        "video_title_display",
        "video_date_display",
        "video_subject",
        "video_description",
        "website_available_display",
        "content_available_display",
        "partner_site",
        "video_link",
        "repository_code",
        detail_url_field,
    ]
    available_columns = [column for column in preferred_columns if column in display_df.columns]
    remaining_columns = [column for column in display_df.columns if column not in available_columns]

    return display_df[available_columns + remaining_columns].rename(
        columns={
            "institution": "instituição",
            "archive_type": "tipo de arquivo",
            "country": "país",
            "continent": "continente",
            "platform": "plataforma",
            "access_surface": "modalidade de acesso",
            "video_theme": "tema",
            "video_title_display": "título do vídeo",
            "video_date_display": "data do vídeo",
            "video_subject": "assunto do vídeo",
            "video_description": "descrição do vídeo",
            "website_available_display": website_label,
            "content_available_display": content_flag_label,
            "partner_site": "site externo informado",
            "video_link": "link do vídeo",
            "repository_code": "código do repositório",
            detail_url_field: detail_url_label,
        }
    )


def get_summary_total(dataframe, label_column, label_value):
    if dataframe is None or dataframe.empty or label_column not in dataframe.columns or "total" not in dataframe.columns:
        return 0
    filtered = dataframe.loc[dataframe[label_column] == label_value, "total"]
    if filtered.empty:
        return 0
    return int(pd.to_numeric(filtered, errors="coerce").fillna(0).sum())


@st.cache_data(show_spinner=False)
def load_dashboard_sources(output_files):
    return {
        key: load_csv(output_files[key])
        for key in DASHBOARD_SOURCE_KEYS
    }


def build_corpus_runtime(corpus_def):
    output_files = corpus_def["output_files"]
    dashboard_sources = load_dashboard_sources(output_files)
    snapshot_metadata = load_json(output_files["snapshot_metadata"])
    summary_df = dashboard_sources["summary"]

    if summary_df is None:
        return {
            "status": "missing",
            "snapshot_metadata": snapshot_metadata,
            "dashboard_sources": dashboard_sources,
        }

    if summary_df.empty:
        return {
            "status": "empty",
            "snapshot_metadata": snapshot_metadata,
            "dashboard_sources": dashboard_sources,
        }

    base_data = build_dashboard_base_data(
        catalog_df=dashboard_sources["institutions"],
        summary_df=summary_df,
        links_df=dashboard_sources["video_links"],
        internal_df=dashboard_sources["internal_pages"],
        summary_analysis_source_df=dashboard_sources["analytic_summary"],
        video_catalog_source_df=dashboard_sources["analytic_video_catalog"],
    )
    overview_data = build_dashboard_overview_data(
        base_data,
        availability_groups_source_df=dashboard_sources["availability_summary"],
        availability_reasons_source_df=dashboard_sources["availability_reasons"],
        archive_type_counts_source_df=dashboard_sources["archive_type_summary"],
        visibility_counts_source_df=dashboard_sources["visibility_summary"],
        access_surface_counts_source_df=dashboard_sources["access_surface_summary"],
        access_regime_counts_source_df=dashboard_sources["access_regime_summary"],
        theme_counts_source_df=dashboard_sources["theme_summary"],
        theme_country_counts_source_df=dashboard_sources["theme_country"],
        theme_platform_counts_source_df=dashboard_sources["theme_platform"],
        theme_archive_type_counts_source_df=dashboard_sources["theme_archive_type"],
        visibility_archive_type_counts_source_df=dashboard_sources["visibility_archive_type"],
    )

    return {
        "status": "available",
        "snapshot_metadata": snapshot_metadata,
        "dashboard_sources": dashboard_sources,
        "base_data": base_data,
        "overview_data": overview_data,
    }


def build_corpus_overview_record(corpus_def):
    category_def = CORPUS_CATEGORIES[corpus_def["category_code"]]
    runtime = build_corpus_runtime(corpus_def)
    snapshot_metadata = runtime["snapshot_metadata"] or {}
    dashboard_sources = runtime["dashboard_sources"]
    summary_df = dashboard_sources["summary"]
    theme_summary_df = dashboard_sources["theme_summary"]
    visibility_df = dashboard_sources["visibility_summary"]

    counts = snapshot_metadata.get("counts", {})
    source_status_date = normalize_optional_text(snapshot_metadata.get("source_status_date")) or "-"
    updated_at = format_snapshot_timestamp(snapshot_metadata.get("analytic_outputs_last_modified_at")) or "-"

    if summary_df is None:
        return {
            "corpus": corpus_def["short_label"],
            "label": corpus_def["label"],
            "category": category_def["label"],
            "coverage_level": corpus_def["coverage_level"],
            "expansion_stage": category_def["expansion_stage_label"],
            "entity_level": corpus_def["entity_level"],
            "scope": corpus_def["scope"],
            "source_status_date": source_status_date,
            "updated_at": updated_at,
            "institutions": 0,
            "institutions_with_video_links": 0,
            "video_links_total": 0,
            "videos_in_curatorial_catalog": 0,
            "detected_visibility": 0,
            "status": "ainda não gerado",
        }

    institutions = int(counts.get("institutions", len(summary_df)))
    institutions_with_video_links = int(
        counts.get(
            "institutions_with_video_links",
            pd.to_numeric(summary_df.get("video_links_found_total", 0), errors="coerce").fillna(0).gt(0).sum(),
        )
    )
    video_links_total = int(
        counts.get(
            "video_links_total",
            pd.to_numeric(summary_df.get("video_links_found_total", 0), errors="coerce").fillna(0).sum(),
        )
    )
    videos_in_curatorial_catalog = int(
        counts.get(
            "videos_in_curatorial_catalog",
            pd.to_numeric(theme_summary_df.get("total", 0), errors="coerce").fillna(0).sum()
            if theme_summary_df is not None
            else 0,
        )
    )
    detected_visibility = get_summary_total(
        visibility_df,
        "situacao",
        "Evidência pública detectável de audiovisual",
    )

    return {
        "corpus": corpus_def["short_label"],
        "label": corpus_def["label"],
        "category": category_def["label"],
        "coverage_level": corpus_def["coverage_level"],
        "expansion_stage": category_def["expansion_stage_label"],
        "entity_level": corpus_def["entity_level"],
        "scope": corpus_def["scope"],
        "source_status_date": source_status_date,
        "updated_at": updated_at,
        "institutions": institutions,
        "institutions_with_video_links": institutions_with_video_links,
        "video_links_total": video_links_total,
        "videos_in_curatorial_catalog": videos_in_curatorial_catalog,
        "detected_visibility": detected_visibility,
        "status": "disponível",
    }


def build_cross_corpus_breakdown(summary_key, label_column, *, category_code=None):
    rows = []
    corpora = (
        list_corpora_by_category(category_code)
        if category_code
        else list(CORPORA.values())
    )
    for corpus_def in corpora:
        dashboard_sources = load_dashboard_sources(corpus_def["output_files"])
        summary_df = dashboard_sources.get(summary_key)
        if summary_df is None or summary_df.empty:
            continue
        working_df = summary_df.copy()
        if label_column not in working_df.columns or "total" not in working_df.columns:
            continue
        working_df["corpus"] = corpus_def["short_label"]
        working_df["categoria"] = CORPUS_CATEGORIES[corpus_def["category_code"]]["label"]
        rows.append(working_df[["corpus", label_column, "total"]])

    if not rows:
        return pd.DataFrame(columns=["corpus", label_column, "total"]), pd.DataFrame()

    combined_df = pd.concat(rows, ignore_index=True)
    matrix = pd.crosstab(
        combined_df["corpus"],
        combined_df[label_column],
        values=combined_df["total"],
        aggfunc="sum",
    ).fillna(0)
    matrix.index.name = "corpus"
    return combined_df, matrix.reset_index()


def build_category_overview_record(category_def):
    overview_rows = [
        build_corpus_overview_record(corpus_def)
        for corpus_def in list_corpora_by_category(category_def["code"])
    ]
    overview_df = pd.DataFrame(overview_rows)

    if overview_df.empty:
        return {
            "category": category_def["label"],
            "corpora": 0,
            "institutions": 0,
            "institutions_with_video_links": 0,
            "video_links_total": 0,
            "videos_in_curatorial_catalog": 0,
        }

    return {
        "category": category_def["label"],
        "expansion_stage": category_def["expansion_stage_label"],
        "corpora": len(overview_df),
        "institutions": int(pd.to_numeric(overview_df["institutions"], errors="coerce").fillna(0).sum()),
        "institutions_with_video_links": int(
            pd.to_numeric(overview_df["institutions_with_video_links"], errors="coerce").fillna(0).sum()
        ),
        "video_links_total": int(pd.to_numeric(overview_df["video_links_total"], errors="coerce").fillna(0).sum()),
        "videos_in_curatorial_catalog": int(
            pd.to_numeric(overview_df["videos_in_curatorial_catalog"], errors="coerce").fillna(0).sum()
        ),
    }


def build_category_combined_frames(category_code):
    category_def = CORPUS_CATEGORIES[category_code]
    overview_rows = []
    summary_frames = []
    video_frames = []

    for corpus_def in list_corpora_by_category(category_code):
        runtime = build_corpus_runtime(corpus_def)
        overview_rows.append(build_corpus_overview_record(corpus_def))
        if runtime["status"] != "available":
            continue

        summary_df = runtime["base_data"].summary_analysis_df.copy()
        summary_df["corpus"] = corpus_def["short_label"]
        summary_df["unidade"] = corpus_def["label"]
        summary_df["categoria_analitica"] = category_def["label"]
        summary_frames.append(summary_df)

        video_df = runtime["base_data"].video_catalog_df.copy()
        video_df["corpus"] = corpus_def["short_label"]
        video_df["unidade"] = corpus_def["label"]
        video_df["categoria_analitica"] = category_def["label"]
        video_frames.append(video_df)

    overview_df = pd.DataFrame(overview_rows)
    summary_df = pd.concat(summary_frames, ignore_index=True) if summary_frames else pd.DataFrame()
    video_df = pd.concat(video_frames, ignore_index=True) if video_frames else pd.DataFrame()
    return overview_df, summary_df, video_df


def build_category_summary_display_df(dataframe):
    if dataframe is None or dataframe.empty:
        return pd.DataFrame()

    display_df = dataframe.copy()
    display_df["integridade"] = display_df["integrity_status"].map(format_integrity_status)
    display_df["status_técnico"] = display_df["status"].map(format_technical_status)
    display_df["site_informado_na_fonte"] = display_df["website_available"].map(format_yes_no)
    if "continent" in display_df.columns:
        display_df["continent"] = display_df["continent"].fillna("Não classificado").replace("", "Não classificado")

    preferred_columns = [
        "corpus",
        "unidade",
        "institution",
        "country",
        "continent",
        "archive_type",
        "audiovisual_visibility",
        "access_regime",
        "access_modalities_detected",
        "availability_group",
        "availability_reason",
        "integridade",
        "status_técnico",
        "video_links_found_total",
        "embedded_video_signals_total",
        "partner_domain",
        "partner_site",
        "final_url",
        "repository_code",
    ]
    available_columns = [column for column in preferred_columns if column in display_df.columns]

    return display_df[available_columns].rename(
        columns={
            "corpus": "corpus",
            "unidade": "unidade",
            "institution": "instituição",
            "country": "país",
            "continent": "continente",
            "archive_type": "tipo de arquivo",
            "audiovisual_visibility": "situação metodológica do audiovisual",
            "access_regime": "regime de acesso audiovisual detectável",
            "access_modalities_detected": "modalidades de acesso detectadas",
            "availability_group": "categoria",
            "availability_reason": "subcategoria",
            "integridade": "integridade",
            "status_técnico": "status técnico",
            "video_links_found_total": "links de vídeo",
            "embedded_video_signals_total": "sinais embutidos",
            "partner_domain": "domínio",
            "partner_site": "site externo informado",
            "final_url": "URL final",
            "repository_code": "código do repositório",
        }
    )


def build_category_video_display_df(dataframe):
    if dataframe is None or dataframe.empty:
        return pd.DataFrame()

    display_df = dataframe.copy()
    if "continent" in display_df.columns:
        display_df["continent"] = display_df["continent"].fillna("Não classificado").replace("", "Não classificado")

    preferred_columns = [
        "corpus",
        "unidade",
        "institution",
        "country",
        "continent",
        "platform",
        "access_surface",
        "video_theme",
        "video_title_display",
        "video_date_display",
        "video_link",
    ]
    available_columns = [column for column in preferred_columns if column in display_df.columns]

    return display_df[available_columns].rename(
        columns={
            "corpus": "corpus",
            "unidade": "unidade",
            "institution": "instituição",
            "country": "país",
            "continent": "continente",
            "platform": "plataforma",
            "access_surface": "modalidade de acesso",
            "video_theme": "tema",
            "video_title_display": "título do vídeo",
            "video_date_display": "data do vídeo",
            "video_link": "link do vídeo",
        }
    )


def render_observatory_overview_tab():
    st.markdown("## Visão geral do observatório")
    st.caption(
        "O observatório opera como um organismo agregador mundial em construção. Os corpora permanecem "
        "separados por categoria analítica e por unidade própria, mas esta visão geral permite compará-los "
        "sem misturar seus níveis de análise."
    )
    st.info(
        f"{OBSERVATORY_PROFILE['description']} "
        f"{OBSERVATORY_PROFILE['expansion_strategy']} "
        f"{OBSERVATORY_PROFILE['audiovisual_rule']}"
    )
    cycle_manifest = load_json(ORGANISM_MONTHLY_CYCLE_FILENAME)
    active_corpora_registry_df = load_csv(ORGANISM_ACTIVE_CORPORA_FILENAME)
    discovery_registry_df = load_csv(DISCOVERY_REGISTRY_FILENAME)
    discovery_queue_df = load_csv(DISCOVERY_QUEUE_FILENAME)
    discovery_summary_df = load_csv(DISCOVERY_SUMMARY_FILENAME)
    cycle_timeline_df = load_csv(ORGANISM_CYCLE_TIMELINE_FILENAME)
    cycle_results_df = load_csv(ORGANISM_CYCLE_RESULTS_FILENAME)
    global_corpus_timeline_df = build_cross_corpus_history_frame("timeline_corpus")
    global_institution_timeline_df = build_cross_corpus_history_frame("timeline_institutions")
    global_extinction_signals_df = build_cross_corpus_history_frame("extinction_signals")
    if active_corpora_registry_df is None or active_corpora_registry_df.empty:
        active_corpora_registry_df = build_active_corpora_registry()
    if discovery_registry_df is None or discovery_registry_df.empty:
        discovery_registry_df = build_discovery_registry()
    if discovery_queue_df is None or discovery_queue_df.empty:
        discovery_queue_df = build_expansion_queue(discovery_registry_df)
    if discovery_summary_df is None or discovery_summary_df.empty:
        discovery_summary_df = build_discovery_summary(discovery_registry_df)
    snapshot_metadata_by_code = {
        corpus_def["code"]: load_json(corpus_def["output_files"]["snapshot_metadata"]) or {}
        for corpus_def in CORPORA.values()
    }
    refresh_status_df = build_corpus_refresh_status(
        active_corpora_registry_df,
        cycle_manifest=cycle_manifest,
        cycle_results_df=cycle_results_df,
        snapshot_metadata_by_code=snapshot_metadata_by_code,
    )
    if cycle_manifest:
        st.caption(
            f"Ciclo {cycle_manifest.get('cycle_type', '-')} mais recente: "
            f"{cycle_manifest.get('successful_corpora_total', 0)} sucessos, "
            f"{cycle_manifest.get('failed_corpora_total', 0)} falhas, "
            f"gerado em {format_snapshot_timestamp(cycle_manifest.get('generated_at')) or '-'}."
        )

    st.markdown("### Eixo acadêmico do projeto")
    st.markdown(
        """
        Este observatório integra a formulação de um projeto de pós-doutorado a ser submetido
        à Universidade de Valência, no âmbito do **Communication and Media Culture History
        Research Group**.

        A pergunta orientadora é: **como as plataformas digitais reorganizam a circulação
        territorial e cultural do audiovisual contemporâneo?**

        As plataformas digitais não eliminam o território; elas reorganizam o território.
        No audiovisual contemporâneo, a circulação deixa de depender apenas do lugar físico
        do arquivo, da cinemateca, da emissora ou da instituição custodial, e passa a depender
        de uma combinação entre infraestrutura técnica, políticas de acesso e licenciamento,
        idioma dos metadados, formatos de indexação, regimes de visibilidade e dependência
        de plataformas externas.

        A hipótese de trabalho é que a circulação audiovisual contemporânea é cada vez menos
        determinada apenas pela localização física dos acervos e cada vez mais pela capacidade
        das instituições e plataformas de tornar esses acervos detectáveis, descritos,
        interoperáveis e acessíveis em redes digitais transnacionais.
        """
    )
    st.caption(
        "No observatório, essa pergunta é operacionalizada por variáveis como hospedagem, indexação, "
        "descrição, idioma, regime de acesso, plataforma, visibilidade pública e escala territorial."
    )

    if cycle_timeline_df is not None and not cycle_timeline_df.empty:
        cycle_metric_cols = st.columns(4)
        cycle_metric_cols[0].metric("Ciclos registrados", len(cycle_timeline_df))
        cycle_metric_cols[1].metric(
            "Último escopo",
            str(cycle_timeline_df.iloc[-1].get("cycle_scope", "-")),
        )
        cycle_metric_cols[2].metric(
            "Corpora selecionados no último ciclo",
            int(pd.to_numeric(cycle_timeline_df.iloc[-1].get("selected_corpora_total", 0), errors="coerce")),
        )
        cycle_metric_cols[3].metric(
            "Falhas no último ciclo",
            int(pd.to_numeric(cycle_timeline_df.iloc[-1].get("failed_corpora_total", 0), errors="coerce")),
        )

    if refresh_status_df is not None and not refresh_status_df.empty:
        refresh_counts = (
            refresh_status_df["refresh_state"].fillna("").value_counts().rename_axis("estado").reset_index(name="total")
        )
        latest_cycle_updates = int((refresh_status_df["refresh_state"] == "Atualizado no último ciclo").sum())
        partial_pending = int(
            (refresh_status_df["refresh_state"] == "Pendente no ciclo parcial mais recente").sum()
        )
        stale_count = int((refresh_status_df["refresh_state"] == "Atualização atrasada").sum())
        failure_count = int((refresh_status_df["refresh_state"] == "Falha no último ciclo").sum())

        st.markdown("### Estado de atualização do organismo")
        st.caption(
            "Este quadro acompanha a saúde temporal do organismo por corpus, distinguindo "
            "atualizações recentes, pendências de ciclos parciais, falhas e atrasos de cadência."
        )
        refresh_metric_cols = st.columns(4)
        refresh_metric_cols[0].metric("Atualizados no último ciclo", latest_cycle_updates)
        refresh_metric_cols[1].metric("Pendentes no ciclo parcial", partial_pending)
        refresh_metric_cols[2].metric("Atualizações atrasadas", stale_count)
        refresh_metric_cols[3].metric("Falhas no último ciclo", failure_count)

        refresh_display_df = refresh_status_df.rename(
            columns={
                "corpus": "corpus",
                "category_label": "categoria analítica",
                "coverage_level": "escala de cobertura",
                "scope": "escopo",
                "included_in_latest_cycle": "incluído no último ciclo",
                "latest_cycle_scope": "escopo do último ciclo",
                "latest_cycle_status": "status no último ciclo",
                "last_successful_cycle_at": "último ciclo bem-sucedido",
                "last_snapshot_generated_at": "última observação materializada",
                "source_status_date": "status da fonte",
                "observation_key": "chave de observação",
                "days_since_last_observation": "dias desde a última observação",
                "refresh_state": "estado de atualização",
                "refresh_state_reason": "justificativa metodológica",
            }
        ).copy()
        refresh_display_df["incluído no último ciclo"] = refresh_display_df["incluído no último ciclo"].map(
            format_yes_no
        )
        refresh_display_df["status no último ciclo"] = refresh_display_df["status no último ciclo"].map(
            format_cycle_status
        )
        refresh_display_df["último ciclo bem-sucedido"] = refresh_display_df["último ciclo bem-sucedido"].map(
            format_snapshot_timestamp
        )
        refresh_display_df["última observação materializada"] = refresh_display_df[
            "última observação materializada"
        ].map(format_snapshot_timestamp)
        st.dataframe(refresh_display_df, use_container_width=True, hide_index=True)
        with st.expander("Ver distribuição dos estados de atualização", expanded=False):
            st.dataframe(refresh_counts, use_container_width=True, hide_index=True)

    st.markdown("### Linha do tempo e retração pública do audiovisual")
    st.caption(
        "Esta camada reúne a memória histórica dos corpora e prepara o organismo para detectar "
        "ausências, indisponibilidades recorrentes e perda de evidência pública detectável de audiovisual."
    )
    global_history_cols = st.columns(4)
    global_history_cols[0].metric(
        "Observações históricas de corpus",
        len(global_corpus_timeline_df) if global_corpus_timeline_df is not None else 0,
    )
    global_history_cols[1].metric(
        "Observações históricas institucionais",
        len(global_institution_timeline_df) if global_institution_timeline_df is not None else 0,
    )
    global_history_cols[2].metric(
        "Sinais globais de possível extinção",
        len(global_extinction_signals_df) if global_extinction_signals_df is not None else 0,
    )
    global_history_cols[3].metric(
        "Corpora com histórico materializado",
        int(global_corpus_timeline_df["corpus"].nunique()) if global_corpus_timeline_df is not None and not global_corpus_timeline_df.empty else 0,
    )

    global_history_tab, global_signals_tab = st.tabs(
        ["Linha do tempo global", "Sinais globais de possível extinção"]
    )
    with global_history_tab:
        if global_corpus_timeline_df is None or global_corpus_timeline_df.empty:
            st.info("Ainda não há linha do tempo global materializada para o organismo.")
        else:
            st.caption(
                "Cada linha preserva uma observação histórica de um corpus, mantendo explícita sua "
                "categoria analítica e escala de cobertura."
            )
            st.dataframe(
                global_corpus_timeline_df.sort_values(
                    ["snapshot_generated_at", "corpus"],
                    ascending=[False, True],
                ),
                use_container_width=True,
                hide_index=True,
            )
            render_csv_download(
                "Baixar linha do tempo global dos corpora",
                global_corpus_timeline_df,
                "observatorio_linha_do_tempo_global_corpora.csv",
                "Exporta a linha do tempo combinada dos corpora do organismo.",
            )
    with global_signals_tab:
        if global_extinction_signals_df is None or global_extinction_signals_df.empty:
            st.info(
                "Ainda não há sinais globais registrados. Isso é esperado enquanto o organismo acumula "
                "mais rodadas históricas para comparação."
            )
        else:
            signal_summary_df = (
                global_extinction_signals_df.groupby(
                    ["corpus", "signal_type", "signal_level"],
                    dropna=False,
                )
                .size()
                .reset_index(name="total")
                .rename(
                    columns={
                        "corpus": "corpus",
                        "signal_type": "tipo de sinal",
                        "signal_level": "nível",
                    }
                )
            )
            st.caption(
                "Os sinais abaixo não afirmam extinção por si só. Eles indicam mudanças que merecem "
                "observação longitudinal e interpretação metodológica cuidadosa."
            )
            summary_col, detail_col = st.columns([1, 2])
            with summary_col:
                st.dataframe(signal_summary_df, use_container_width=True, hide_index=True)
            with detail_col:
                st.dataframe(
                    global_extinction_signals_df.sort_values(
                        ["snapshot_generated_at", "corpus", "institution"],
                        ascending=[False, True, True],
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
            render_csv_download(
                "Baixar sinais globais de possível extinção",
                global_extinction_signals_df,
                "observatorio_sinais_globais_possivel_extincao.csv",
                "Exporta os sinais combinados de retração e possível extinção detectados no organismo.",
            )

    overview_rows = [build_corpus_overview_record(corpus_def) for corpus_def in CORPORA.values()]
    overview_df = pd.DataFrame(overview_rows)
    category_rows = [
        build_category_overview_record(category_def)
        for category_def in CORPUS_CATEGORIES.values()
    ]
    category_overview_df = pd.DataFrame(category_rows)

    total_corpora = len(overview_df)
    total_institutions = int(pd.to_numeric(overview_df["institutions"], errors="coerce").fillna(0).sum())
    total_with_video_links = int(
        pd.to_numeric(overview_df["institutions_with_video_links"], errors="coerce").fillna(0).sum()
    )
    total_video_links = int(pd.to_numeric(overview_df["video_links_total"], errors="coerce").fillna(0).sum())
    total_curatorial_videos = int(
        pd.to_numeric(overview_df["videos_in_curatorial_catalog"], errors="coerce").fillna(0).sum()
    )

    metric_cols = st.columns(5)
    metric_cols[0].metric("Corpora ativos", total_corpora)
    metric_cols[1].metric("Instituições no observatório", total_institutions)
    metric_cols[2].metric("Instituições com links de vídeo", total_with_video_links)
    metric_cols[3].metric("Links de vídeo detectados", total_video_links)
    metric_cols[4].metric("Vídeos no recorte curatorial", total_curatorial_videos)

    comparison_df = overview_df.rename(
        columns={
            "corpus": "corpus",
            "label": "unidade",
            "category": "categoria analítica",
            "coverage_level": "escala de cobertura",
            "expansion_stage": "etapa de expansão",
            "entity_level": "nível da unidade",
            "scope": "escopo",
            "source_status_date": "status da fonte",
            "updated_at": "atualização analítica",
            "institutions": "instituições",
            "institutions_with_video_links": "instituições com links de vídeo",
            "video_links_total": "links de vídeo",
            "videos_in_curatorial_catalog": "vídeos no recorte curatorial",
            "detected_visibility": "evidência pública detectável",
            "status": "situação",
        }
    )
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)

    st.markdown("### Categorias analíticas do observatório")
    st.caption(
        "As categorias abaixo delimitam níveis diferentes de observação. Elas são comparáveis, "
        "mas não são tratadas como equivalentes do ponto de vista metodológico."
    )
    st.dataframe(
        category_overview_df.rename(
            columns={
                "category": "categoria analítica",
                "expansion_stage": "etapa de expansão",
                "corpora": "corpora",
                "institutions": "instituições",
                "institutions_with_video_links": "instituições com links de vídeo",
                "video_links_total": "links de vídeo",
                "videos_in_curatorial_catalog": "vídeos no recorte curatorial",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    strategy_df = pd.DataFrame(
        [
            {
                "etapa": category_def["expansion_stage_label"],
                "categoria": category_def["label"],
                "critério de entrada": category_def["inclusion_criterion"],
                "regra de expansão": category_def["expansion_rule"],
            }
            for category_def in sorted(
                CORPUS_CATEGORIES.values(),
                key=lambda item: item["expansion_priority"],
            )
        ]
    )
    st.markdown("### Estratégia de expansão")
    st.caption(
        "O organismo cresce primeiro por agregadores continentais e, depois, incorpora "
        "arquivos e instituições não cobertos por esses agregadores."
    )
    st.dataframe(strategy_df, use_container_width=True, hide_index=True)

    st.markdown("### Fila automática de expansão do organismo")
    st.caption(
        "A fila abaixo é gerada por regra pública e determinística. Neste momento, ela prioriza "
        "o fechamento da Europa antes da abertura sistemática de novos continentes."
    )
    queue_metric_cols = st.columns(4)
    european_av_aggregator_total = int(
        (
            discovery_queue_df.get("automatic_decision", pd.Series(dtype="object"))
            == "fechamento_europa_agregador_audiovisual"
        ).sum()
    )
    european_national_aggregator_total = int(
        (
            discovery_queue_df.get("automatic_decision", pd.Series(dtype="object"))
            == "fechamento_europa_agregador_nacional"
        ).sum()
    )
    immediate_stage_1_total = int(
        (
            discovery_queue_df.get("automatic_decision", pd.Series(dtype="object"))
            == "prioridade_imediata_etapa_1"
        ).sum()
    )
    european_gap_total = int(
        (
            discovery_queue_df.get("automatic_decision", pd.Series(dtype="object"))
            == "lacuna_ou_excecao_na_base_europa"
        ).sum()
    )
    waiting_stage_2_total = int(
        (
            discovery_queue_df.get("automatic_decision", pd.Series(dtype="object"))
            == "aguarda_etapa_2"
        ).sum()
    )
    strategic_monitoring_total = int(
        (
            discovery_queue_df.get("automatic_decision", pd.Series(dtype="object"))
            == "monitoramento_estrategico"
        ).sum()
    )
    already_active_total = int(
        (
            discovery_registry_df.get("automatic_decision", pd.Series(dtype="object"))
            == "ja_incorporado"
        ).sum()
    )
    queue_metric_cols[0].metric("Agregador audiovisual europeu", european_av_aggregator_total)
    queue_metric_cols[1].metric(
        "Agregadores nacionais europeus",
        european_national_aggregator_total,
    )
    queue_metric_cols[2].metric("Lacunas europeias", european_gap_total)
    queue_metric_cols[3].metric("Unidades já incorporadas", already_active_total)

    discovery_summary_tab, discovery_queue_tab = st.tabs(
        ["Resumo automático da fila", "Candidatos e decisões"]
    )
    with discovery_summary_tab:
        st.dataframe(discovery_summary_df, use_container_width=True, hide_index=True)
        summary_download_cols = st.columns(2)
        with summary_download_cols[0]:
            render_csv_download(
                "Baixar resumo automático da fila",
                discovery_summary_df,
                DISCOVERY_SUMMARY_FILENAME,
                "Exporta a síntese das decisões automáticas de expansão do organismo.",
            )
        with summary_download_cols[1]:
            render_csv_download(
                "Baixar fila automática de expansão",
                discovery_queue_df,
                DISCOVERY_QUEUE_FILENAME,
                "Exporta a fila atual de candidatos priorizados pelo organismo.",
            )
    with discovery_queue_tab:
        st.caption(
            "Cada linha mostra uma unidade potencial, a decisão automática aplicada e o próximo passo "
            "sugerido pelo protocolo do organismo."
        )
        st.dataframe(discovery_queue_df, use_container_width=True, hide_index=True)
        render_csv_download(
            "Baixar registro completo de candidatos",
            discovery_registry_df,
            DISCOVERY_REGISTRY_FILENAME,
            "Exporta o registro completo de candidatos e unidades já incorporadas ao organismo.",
        )

    chart_cols = st.columns(3)
    chart_base = overview_df.set_index("corpus")
    with chart_cols[0]:
        st.caption("Instituições com links de vídeo por corpus")
        st.bar_chart(chart_base[["institutions_with_video_links"]])
    with chart_cols[1]:
        st.caption("Links de vídeo detectados por corpus")
        st.bar_chart(chart_base[["video_links_total"]])
    with chart_cols[2]:
        st.caption("Vídeos no recorte curatorial por corpus")
        st.bar_chart(chart_base[["videos_in_curatorial_catalog"]])

    regime_long_df, regime_matrix_df = build_cross_corpus_breakdown(
        "access_regime_summary",
        "regime",
    )
    modality_long_df, modality_matrix_df = build_cross_corpus_breakdown(
        "access_surface_summary",
        "modalidade",
    )

    st.markdown("### Comparações transversais do observatório")
    st.caption(
        "Estes quadros mostram como os corpora diferem não apenas em volume, mas também na forma "
        "como o audiovisual se torna publicamente acessível."
    )

    compare_tab_regimes, compare_tab_modalities = st.tabs(
        ["Regimes de acesso por corpus", "Modalidades de acesso por corpus"]
    )

    with compare_tab_regimes:
        if regime_long_df.empty:
            st.info("Ainda não há dados suficientes para comparar regimes de acesso entre corpora.")
        else:
            st.caption(
                "Linhas representam corpora; colunas representam regimes institucionais de acesso audiovisual detectável."
            )
            st.dataframe(
                style_matrix_display(prepare_matrix_display(regime_matrix_df)),
                use_container_width=True,
                hide_index=True,
            )
            with st.expander("Ver tabela detalhada de regimes", expanded=False):
                st.dataframe(regime_long_df, use_container_width=True, hide_index=True)

    with compare_tab_modalities:
        if modality_long_df.empty:
            st.info("Ainda não há dados suficientes para comparar modalidades de acesso entre corpora.")
        else:
            st.caption(
                "Linhas representam corpora; colunas representam modalidades públicas de acesso encontradas nos catálogos."
            )
            st.dataframe(
                style_matrix_display(prepare_matrix_display(modality_matrix_df)),
                use_container_width=True,
                hide_index=True,
            )
            with st.expander("Ver tabela detalhada de modalidades", expanded=False):
                st.dataframe(modality_long_df, use_container_width=True, hide_index=True)

    if cycle_timeline_df is not None and not cycle_timeline_df.empty:
        st.markdown("### Memória do organismo")
        cycle_history_tab, cycle_results_tab, cycle_files_tab = st.tabs(
            ["Linha do tempo dos ciclos", "Resultados históricos por corpus", "Arquivos globais do organismo"]
        )
        with cycle_history_tab:
            st.caption(
                "Cada linha representa um ciclo do organismo, permitindo acompanhar cadência, "
                "escopo e estabilidade das atualizações ao longo do tempo."
            )
            st.dataframe(
                cycle_timeline_df.sort_values("generated_at", ascending=False),
                use_container_width=True,
                hide_index=True,
            )
        with cycle_results_tab:
            if cycle_results_df is None or cycle_results_df.empty:
                st.info("Ainda não há resultados históricos materializados por corpus.")
            else:
                st.caption(
                    "Este quadro preserva o desempenho de cada corpus em cada ciclo do organismo."
                )
                st.dataframe(
                    cycle_results_df.sort_values(["generated_at", "code"], ascending=[False, True]),
                    use_container_width=True,
                    hide_index=True,
                )
        with cycle_files_tab:
            st.caption(
                "Estes artefatos preservam a rastreabilidade global do organismo, permitindo "
                "auditar ciclos, corpora ativos e resultados históricos."
            )
            organism_files_df = pd.DataFrame(
                [
                    {
                        "arquivo": ORGANISM_MONTHLY_CYCLE_FILENAME,
                        "tipo": "manifesto do último ciclo",
                        "disponível": "Sim" if cycle_manifest else "Não",
                    },
                    {
                        "arquivo": ORGANISM_ACTIVE_CORPORA_FILENAME,
                        "tipo": "inventário de corpora ativos",
                        "disponível": "Sim"
                        if active_corpora_registry_df is not None and not active_corpora_registry_df.empty
                        else "Não",
                    },
                    {
                        "arquivo": ORGANISM_CYCLE_TIMELINE_FILENAME,
                        "tipo": "linha do tempo dos ciclos",
                        "disponível": "Sim"
                        if cycle_timeline_df is not None and not cycle_timeline_df.empty
                        else "Não",
                    },
                    {
                        "arquivo": ORGANISM_CYCLE_RESULTS_FILENAME,
                        "tipo": "resultados históricos por corpus",
                        "disponível": "Sim"
                        if cycle_results_df is not None and not cycle_results_df.empty
                        else "Não",
                    },
                ]
            )
            st.dataframe(organism_files_df, use_container_width=True, hide_index=True)
            download_cols = st.columns(2)
            with download_cols[0]:
                render_json_download(
                    "Baixar manifesto do último ciclo",
                    cycle_manifest,
                    ORGANISM_MONTHLY_CYCLE_FILENAME,
                    "Exporta o manifesto global do ciclo mais recente do organismo.",
                )
                render_csv_download(
                    "Baixar corpora ativos do organismo",
                    active_corpora_registry_df,
                    ORGANISM_ACTIVE_CORPORA_FILENAME,
                    "Exporta o inventário atual dos corpora ativos do organismo.",
                )
            with download_cols[1]:
                render_csv_download(
                    "Baixar linha do tempo dos ciclos",
                    cycle_timeline_df,
                    ORGANISM_CYCLE_TIMELINE_FILENAME,
                    "Exporta a linha do tempo global dos ciclos mensais do organismo.",
                )
                render_csv_download(
                    "Baixar resultados históricos por corpus",
                    cycle_results_df,
                    ORGANISM_CYCLE_RESULTS_FILENAME,
                    "Exporta o histórico consolidado dos resultados por corpus em cada ciclo.",
                )


def render_category_tab(category_def):
    category_code = category_def["code"]
    st.markdown(f"## {category_def['label']}")
    st.caption(category_def["description"])
    st.caption(category_def["method_note"])
    st.info(
        f"{category_def['expansion_stage_label']} da expansão. "
        f"{category_def['expansion_rule']}"
    )
    st.caption(f"Regra audiovisual desta categoria: {category_def['audiovisual_entry_rule']}")

    overview_df, combined_summary_df, combined_video_df = build_category_combined_frames(category_code)
    corpora_in_category = list_corpora_by_category(category_code)
    category_video_count_series = (
        pd.to_numeric(combined_summary_df["video_links_found_total"], errors="coerce").fillna(0)
        if not combined_summary_df.empty and "video_links_found_total" in combined_summary_df.columns
        else pd.Series(dtype="int64")
    )

    total_corpora = len(corpora_in_category)
    total_institutions = len(combined_summary_df)
    total_with_video_links = int(category_video_count_series.gt(0).sum()) if not category_video_count_series.empty else 0
    total_video_links = int(category_video_count_series.sum()) if not category_video_count_series.empty else 0
    filtered_curatorial_videos_df = (
        analysis_utils.filter_curatorial_video_catalog(combined_video_df)
        if not combined_video_df.empty
        else pd.DataFrame()
    )
    total_curatorial_videos = len(filtered_curatorial_videos_df)

    metric_cols = st.columns(5)
    metric_cols[0].metric("Corpora na categoria", total_corpora)
    metric_cols[1].metric("Instituições no recorte", total_institutions)
    metric_cols[2].metric("Instituições com links de vídeo", total_with_video_links)
    metric_cols[3].metric("Links de vídeo detectados", total_video_links)
    metric_cols[4].metric("Vídeos no recorte curatorial", total_curatorial_videos)

    category_summary_tab, category_institutions_tab, category_videos_tab = st.tabs(
        ["Síntese", "Instituições", "Vídeos"]
    )

    with category_summary_tab:
        st.markdown("### Corpora desta categoria")
        if overview_df.empty:
            st.info("Ainda não há corpora materializados nesta categoria.")
        else:
            st.dataframe(
                overview_df.rename(
                    columns={
                        "corpus": "corpus",
                        "label": "unidade",
                        "entity_level": "nível da unidade",
                        "scope": "escopo",
                        "source_status_date": "status da fonte",
                        "updated_at": "atualização analítica",
                        "institutions": "instituições",
                        "institutions_with_video_links": "instituições com links de vídeo",
                        "video_links_total": "links de vídeo",
                        "videos_in_curatorial_catalog": "vídeos no recorte curatorial",
                        "detected_visibility": "evidência pública detectável",
                        "status": "situação",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

        st.markdown("### Princípio de separação")
        st.markdown(
            f"""
            Esta categoria reúne apenas corpora classificados como **{category_def['label'].lower()}**.
            O observatório permite trabalhar com todos eles em conjunto, mas sempre preservando o mesmo
            nível analítico: **{category_def['selection_scope_label']}**.
            """
        )
        st.caption(f"Critério de entrada nesta etapa: {category_def['inclusion_criterion']}")

    with category_institutions_tab:
        st.markdown("### Instituições da categoria")
        if combined_summary_df.empty:
            st.info("Ainda não há instituições disponíveis nesta categoria.")
        else:
            filter_cols = st.columns([1.1, 1.1, 1.4])
            corpus_options = ["Todos os corpora"] + [corpus_def["short_label"] for corpus_def in corpora_in_category]
            with filter_cols[0]:
                selected_corpus = st.selectbox(
                    "Corpus",
                    options=corpus_options,
                    key=f"{category_code}-category-corpus-filter",
                )
            with filter_cols[1]:
                visibility_options = ["Todas as situações"] + sorted(
                    combined_summary_df["audiovisual_visibility"].dropna().astype(str).unique().tolist()
                )
                selected_visibility = st.selectbox(
                    "Situação metodológica",
                    options=visibility_options,
                    key=f"{category_code}-category-visibility-filter",
                )
            with filter_cols[2]:
                search_term = st.text_input(
                    "Buscar instituição, país ou domínio",
                    key=f"{category_code}-category-search",
                ).strip()

            filtered_summary_df = combined_summary_df.copy()
            if selected_corpus != "Todos os corpora":
                filtered_summary_df = filtered_summary_df.loc[filtered_summary_df["corpus"] == selected_corpus]
            if selected_visibility != "Todas as situações":
                filtered_summary_df = filtered_summary_df.loc[
                    filtered_summary_df["audiovisual_visibility"] == selected_visibility
                ]
            if search_term:
                search_lower = search_term.lower()
                filtered_summary_df = filtered_summary_df.loc[
                    filtered_summary_df[
                        ["institution", "country", "partner_domain", "repository_code"]
                    ]
                    .fillna("")
                    .astype(str)
                    .apply(lambda column: column.str.lower().str.contains(search_lower, na=False))
                    .any(axis=1)
                ]

            st.caption(
                "Este quadro reúne apenas instituições pertencentes a corpora da mesma categoria "
                "analítica, evitando mistura entre agregadores e instituições custodiais."
            )
            st.dataframe(
                build_category_summary_display_df(filtered_summary_df),
                use_container_width=True,
                hide_index=True,
            )
            render_csv_download(
                "Baixar instituições da categoria",
                build_category_summary_display_df(filtered_summary_df),
                f"{category_code}_instituicoes_categoria.csv",
                "Exporta o recorte institucional desta categoria analítica.",
            )

    with category_videos_tab:
        st.markdown("### Catálogo de vídeos da categoria")
        if filtered_curatorial_videos_df.empty:
            st.info("Ainda não há vídeos curatoriais disponíveis nesta categoria.")
        else:
            filter_cols = st.columns([1.1, 1.1, 1.3])
            corpus_options = ["Todos os corpora"] + [corpus_def["short_label"] for corpus_def in corpora_in_category]
            with filter_cols[0]:
                selected_corpus = st.selectbox(
                    "Corpus",
                    options=corpus_options,
                    key=f"{category_code}-video-corpus-filter",
                )
            with filter_cols[1]:
                theme_options = ["Todos os temas"] + sorted(
                    filtered_curatorial_videos_df["video_theme"].dropna().astype(str).unique().tolist()
                )
                selected_theme = st.selectbox(
                    "Tema",
                    options=theme_options,
                    key=f"{category_code}-video-theme-filter",
                )
            with filter_cols[2]:
                selected_access_surface = st.selectbox(
                    "Modalidade de acesso",
                    options=["Todas as modalidades"] + sorted(
                        filtered_curatorial_videos_df["access_surface"].dropna().astype(str).unique().tolist()
                    ),
                    key=f"{category_code}-video-access-filter",
                )

            filtered_video_df = filtered_curatorial_videos_df.copy()
            if selected_corpus != "Todos os corpora":
                filtered_video_df = filtered_video_df.loc[filtered_video_df["corpus"] == selected_corpus]
            if selected_theme != "Todos os temas":
                filtered_video_df = filtered_video_df.loc[filtered_video_df["video_theme"] == selected_theme]
            if selected_access_surface != "Todas as modalidades":
                filtered_video_df = filtered_video_df.loc[
                    filtered_video_df["access_surface"] == selected_access_surface
                ]

            st.dataframe(
                build_category_video_display_df(filtered_video_df),
                use_container_width=True,
                hide_index=True,
            )
            render_csv_download(
                "Baixar vídeos da categoria",
                build_category_video_display_df(filtered_video_df),
                f"{category_code}_videos_categoria.csv",
                "Exporta o recorte curatorial de vídeos desta categoria analítica.",
            )


def format_institution_label(summary_df, slug):
    label_series = summary_df.loc[summary_df["slug"].astype(str) == str(slug), "institution"]
    if label_series.empty:
        return str(slug)
    label = normalize_optional_text(label_series.iloc[0])
    return label or str(slug)


def format_segment_label(segmented_summary_df, segment_name):
    total = int(
        segmented_summary_df["institution_segment"]
        .astype(str)
        .map(coerce_segment_label)
        .eq(segment_name)
        .sum()
    )
    return f"{segment_name} ({total})"


def render_project_tab(corpus_def):
    category_def = CORPUS_CATEGORIES[corpus_def["category_code"]]
    framing_df = pd.DataFrame(
        [
            {"aspecto": "Papel no observatório", "descrição": corpus_def["observatory_role"]},
            {"aspecto": "Categoria analítica", "descrição": category_def["label"]},
            {"aspecto": "Etapa de expansão", "descrição": category_def["expansion_stage_label"]},
            {"aspecto": "Nível da unidade", "descrição": corpus_def["entity_level"]},
            {"aspecto": "Escala de cobertura", "descrição": corpus_def["coverage_level"]},
            {"aspecto": "Unidade metodológica", "descrição": corpus_def["methodological_unit"]},
            {"aspecto": "Relação com o APE", "descrição": corpus_def["ape_relationship"]},
            {"aspecto": "Justificativa de entrada", "descrição": corpus_def["expansion_rationale"]},
        ]
    )

    if corpus_def["code"] == "ape":
        st.subheader("Sobre o corpus APE")
        st.markdown(
            """
            Este observatório investiga a visibilidade pública do audiovisual em ambientes arquivísticos na web.
            Nesta etapa, o corpus é formado pelo **Archives Portal Europe (APE)**, tratado como um portal
            arquivístico geral, e não como um repositório especializado em audiovisual.

            **Objetivo**

            Examinar como o audiovisual se torna publicamente visível, detectável e acessível nos sites
            institucionais vinculados ao APE, considerando tanto a presença explícita quanto formas mais
            indiretas de evidência.

            **Princípio metodológico**

            A ausência de vídeo detectado não autoriza afirmar, por si só, ausência de acervo audiovisual.
            No contexto de um portal geral, a não detecção pode indicar pelo menos quatro situações:

            - o acervo audiovisual pode não existir;
            - o acervo pode existir, mas não estar digitalizado;
            - o acervo pode estar digitalizado, mas não público;
            - o acervo pode estar público, porém pouco visível ou não detectável com a estratégia atual de coleta.

            Neste observatório, fontes gerais como o APE podem permanecer mapeadas mesmo quando
            parte de suas instituições retorna zero audiovisual, porque esse zero também é
            analiticamente informativo para o estudo da visibilidade pública do acervo.
            """
        )
    else:
        st.subheader(f"Sobre o corpus {corpus_def['short_label']}")
        st.markdown(
            f"""
            Este corpus toma o **{corpus_def['label']}** como unidade especializada em audiovisual.
            Diferentemente do APE, que funciona como portal geral de arquivos, aqui o audiovisual
            tende a ocupar uma posição institucional central.

            **Objetivo**

            Examinar como um arquivo explicitamente audiovisual organiza a presença pública de seus vídeos,
            coleções, descrições e mediações digitais.

            **Princípio metodológico**

            Neste corpus, a questão central já não é apenas a existência de evidência pública detectável,
            mas a forma como um arquivo especializado apresenta, contextualiza e distribui seu audiovisual
            na web institucional.
            """
        )

    st.dataframe(framing_df, use_container_width=True, hide_index=True)
    st.caption(f"Política de expansão aplicável: {category_def['expansion_rule']}")
    st.caption(f"Regra audiovisual do corpus: {corpus_def['audiovisual_scope_note']}")
    st.caption(f"Leitura metodológica de retorno zero: {corpus_def['zero_result_policy']}")
    st.markdown(
        """
        **Eixo interpretativo**

        A plataforma observa a circulação audiovisual como um fenômeno territorial,
        cultural e técnico. O problema não é apenas localizar vídeos, mas compreender
        quem hospeda, quem indexa, quem descreve, em qual idioma, sob qual regime de
        acesso, por qual plataforma e em que escala territorial esse audiovisual se torna
        público.

        **O que a plataforma afirma com maior segurança**

        - quando há evidência pública detectável de audiovisual;
        - quando há apenas evidência pública indireta;
        - quando não foi encontrada evidência pública detectável de audiovisual;
        - quando o site não pôde ser verificado.

        **O que a plataforma evita afirmar**

        - que a ausência de evidência pública detectável equivale à inexistência de acervo audiovisual;
        - que a visibilidade pública esgota a complexidade do acervo;
        - que uma única coleta resolve o problema da descrição e do acesso audiovisual.
        """
    )


def render_panel_tab(corpus_def, context):
    summary_df = context["summary_df"]
    available_df = context["available_df"]
    availability_groups = context["availability_groups"]
    availability_reasons = context["availability_reasons"]
    archive_type_counts = context["archive_type_counts"]
    visibility_counts = context["visibility_counts"]
    unavailable_count = context["unavailable_count"]
    platform_counts = context["platform_counts"]
    theme_counts = context["theme_counts"]
    theme_country_counts = context["theme_country_counts"]
    theme_country_matrix = context["theme_country_matrix"]
    theme_platform_counts = context["theme_platform_counts"]
    theme_archive_type_counts = context["theme_archive_type_counts"]
    theme_archive_type_matrix = context["theme_archive_type_matrix"]
    visibility_archive_type_counts = context["visibility_archive_type_counts"]
    visibility_archive_type_matrix = context["visibility_archive_type_matrix"]
    availability_reference_df = context["availability_reference_df"]
    access_regime_counts = context["access_regime_counts"]
    access_surface_counts = context["access_surface_counts"]

    st.caption(
        "O painel organiza a leitura do observatório em três camadas: síntese institucional, "
        "análise temática e detalhamento dos casos que exigem atenção metodológica."
    )

    integrity_counts = (
        summary_df["integrity_status"]
        .value_counts()
        .rename_axis("integrity_status")
        .reset_index(name="total")
    )
    integrity_counts["integridade"] = integrity_counts["integrity_status"].map(format_integrity_status)

    unavailable_df = available_df.loc[
        available_df["availability_group"] == "Indisponível"
    ].sort_values(
        ["integrity_status", "status", "video_links_found_total", "embedded_video_signals_total"],
        ascending=[True, True, False, False],
    )
    unavailable_df = unavailable_df.assign(
        integridade=unavailable_df["integrity_status"].map(format_integrity_status),
        status_tecnico=unavailable_df["status"].map(format_technical_status),
        website_fonte=unavailable_df["website_available"].map(format_yes_no),
    )

    broken_df = summary_df.loc[
        summary_df["integrity_status"].isin(["quebrado", "suspeito"]),
        [
            "institution",
            "archive_type",
            "integrity_status",
            "final_url",
            "warning",
            "status",
            "partner_domain",
        ],
    ].copy()
    broken_df["integridade"] = broken_df["integrity_status"].map(format_integrity_status)
    broken_df["status_tecnico"] = broken_df["status"].map(format_technical_status)

    unstable_df = summary_df.loc[
        summary_df["integrity_status"] == "instavel",
        [
            "institution",
            "archive_type",
            "status",
            "error",
            "partner_domain",
            "final_url",
        ],
    ].copy()
    unstable_df["subcategoria_instavel"] = unstable_df.apply(classify_availability_reason, axis=1)
    unstable_df["status_tecnico"] = unstable_df["status"].map(format_technical_status)

    generated_files_status_df = pd.DataFrame(
        [
            {
                "arquivo": filename,
                "situação": "disponível" if (OUTPUT_DIR / filename).exists() else "ainda não gerado",
            }
            for filename in list_output_filenames(corpus_def["output_files"])
        ]
    )

    panel_summary_tab, panel_analysis_tab, panel_cases_tab = st.tabs(
        ["Síntese institucional", "Temas e cruzamentos", "Casos e rastreabilidade"]
    )

    with panel_summary_tab:
        summary_left, summary_right = st.columns([1.1, 1])

        with summary_left:
            st.subheader("Integridade dos sites institucionais")
            st.bar_chart(integrity_counts.set_index("integridade")[["total"]])

            st.subheader("Disponibilidade institucional")
            category_left, category_right = st.columns(2)
            with category_left:
                st.caption("Categorias")
                st.dataframe(availability_groups, use_container_width=True, hide_index=True)
            with category_right:
                st.caption("Subcategorias")
                st.dataframe(availability_reasons, use_container_width=True, hide_index=True)

            with st.expander("Ver referência de classificação", expanded=False):
                st.dataframe(availability_reference_df, use_container_width=True, hide_index=True)

        with summary_right:
            st.subheader("Visibilidade do audiovisual")
            if not visibility_counts.empty:
                st.dataframe(visibility_counts, use_container_width=True, hide_index=True)
            else:
                st.info("Ainda não há dados suficientes para analisar a visibilidade do audiovisual.")

            st.subheader("Regimes de acesso audiovisual detectáveis")
            if not access_regime_counts.empty:
                st.dataframe(access_regime_counts, use_container_width=True, hide_index=True)
            else:
                st.info("Ainda não há dados suficientes para resumir os regimes de acesso audiovisual.")

            st.subheader("Modalidades de acesso detectadas")
            if not access_surface_counts.empty:
                st.dataframe(access_surface_counts, use_container_width=True, hide_index=True)
            else:
                st.info("Ainda não há dados suficientes para resumir as modalidades de acesso.")

            st.subheader("Tipo institucional declarado na fonte")
            if not archive_type_counts.empty:
                st.dataframe(archive_type_counts, use_container_width=True, hide_index=True)
            else:
                st.info("Ainda não há dados suficientes para resumir o tipo institucional declarado na fonte.")

    with panel_analysis_tab:
        analysis_left, analysis_right = st.columns([0.9, 1.1])

        with analysis_left:
            st.subheader("Temas dos vídeos")
            st.caption("Esta distribuição exclui, por padrão, ruído de plataforma ou incorporação externa.")
            if not theme_counts.empty:
                st.metric("Vídeos classificados na análise temática", int(theme_counts["total"].sum()))
                st.dataframe(theme_counts, use_container_width=True, hide_index=True)
            else:
                st.info("Ainda não há temas classificados para os vídeos.")

            st.subheader("Plataformas detectadas")
            if not platform_counts.empty:
                st.bar_chart(platform_counts.set_index("platform"))
            else:
                st.info("Nenhum link de vídeo foi detectado ainda.")

            st.subheader("Temas por plataforma")
            if not theme_platform_counts.empty:
                st.dataframe(theme_platform_counts, use_container_width=True, hide_index=True)
            else:
                st.info("Ainda não há dados suficientes para cruzar temas e plataformas.")

        with analysis_right:
            st.subheader("Temas por país")
            if not theme_country_matrix.empty:
                st.dataframe(
                    style_matrix_display(prepare_matrix_display(theme_country_matrix)),
                    use_container_width=True,
                    hide_index=True,
                )
            elif not theme_country_counts.empty:
                st.dataframe(theme_country_counts, use_container_width=True, hide_index=True)
            else:
                st.info("Ainda não há dados suficientes para cruzar temas e países.")

            st.subheader("Temas por tipo de arquivo")
            if not theme_archive_type_matrix.empty:
                st.dataframe(
                    style_matrix_display(prepare_matrix_display(theme_archive_type_matrix)),
                    use_container_width=True,
                    hide_index=True,
                )
            elif not theme_archive_type_counts.empty:
                st.dataframe(theme_archive_type_counts, use_container_width=True, hide_index=True)
            else:
                st.info("Ainda não há dados suficientes para cruzar temas e tipos institucionais.")

            st.subheader("Visibilidade por tipo de arquivo")
            if not visibility_archive_type_matrix.empty:
                st.dataframe(
                    style_matrix_display(prepare_matrix_display(visibility_archive_type_matrix)),
                    use_container_width=True,
                    hide_index=True,
                )
            elif not visibility_archive_type_counts.empty:
                st.dataframe(visibility_archive_type_counts, use_container_width=True, hide_index=True)
            else:
                st.info("Ainda não há dados suficientes para cruzar visibilidade e tipos institucionais.")

    with panel_cases_tab:
        st.metric("Instituições indisponíveis", unavailable_count)
        st.caption("Dentro de `quebrado`, a aplicação distingue erro explícito e página suspeita.")

        st.subheader("Casos indisponíveis")
        st.dataframe(
            unavailable_df[
                [
                    "institution",
                    "archive_type",
                    "availability_reason",
                    "integridade",
                    "status_tecnico",
                    "website_fonte",
                    "video_links_found_total",
                    "partner_domain",
                    "warning",
                ]
            ].rename(
                columns={
                    "institution": "instituição",
                    "archive_type": "tipo de arquivo",
                    "availability_reason": "subcategoria",
                    "integridade": "integridade",
                    "status_tecnico": "status técnico",
                    "website_fonte": corpus_def["website_label"],
                    "video_links_found_total": "links de vídeo",
                    "partner_domain": "domínio",
                    "warning": "observação",
                }
            ),
            use_container_width=True,
        )

        detail_left, detail_right = st.columns(2)

        with detail_left:
            st.subheader("Detalhamento da categoria quebrado")
            if broken_df.empty:
                st.info("Nenhum caso enquadrado como quebrado foi detectado nesta rodada.")
            else:
                st.dataframe(
                    broken_df[
                        [
                            "institution",
                            "archive_type",
                            "integridade",
                            "final_url",
                            "warning",
                            "status_tecnico",
                            "partner_domain",
                        ]
                    ].rename(
                        columns={
                            "institution": "instituição",
                            "archive_type": "tipo de arquivo",
                            "integridade": "integridade",
                            "final_url": "URL final",
                            "warning": "observação",
                            "status_tecnico": "status técnico",
                            "partner_domain": "domínio",
                        }
                    ),
                    use_container_width=True,
                )

        with detail_right:
            st.subheader("Detalhamento da categoria instável")
            if unstable_df.empty:
                st.info("Nenhum caso instável foi detectado nesta rodada.")
            else:
                st.dataframe(
                    unstable_df[
                        [
                            "institution",
                            "archive_type",
                            "subcategoria_instavel",
                            "status_tecnico",
                            "error",
                            "partner_domain",
                            "final_url",
                        ]
                    ].rename(
                        columns={
                            "institution": "instituição",
                            "archive_type": "tipo de arquivo",
                            "subcategoria_instavel": "subcategoria",
                            "status_tecnico": "status técnico",
                            "error": "erro",
                            "partner_domain": "domínio",
                            "final_url": "URL final",
                        }
                    ),
                    use_container_width=True,
                )

        with st.expander("Ver inventário dos arquivos gerados", expanded=False):
            st.dataframe(generated_files_status_df, use_container_width=True, hide_index=True)


def render_sites_tab(corpus_def, context):
    with_video = context["with_video"]
    detected_sites_df = context["detected_sites_df"]
    detail_url_field = corpus_def["detail_url_field"]
    detail_url_label = corpus_def["detail_url_label"]

    st.subheader(f"Instituições com links de vídeo detectados ({with_video})")
    st.caption(
        "Esta aba reúne as instituições em cujos sites a coleta encontrou ao menos um link explícito de vídeo."
    )
    if detected_sites_df.empty:
        st.info(f"Nenhum link de vídeo foi detectado ainda no corpus {corpus_def['short_label']}.")
        if corpus_def["category_code"] == "aggregator":
            st.caption(
                "Neste caso, o corpus continua relevante como fonte geral de pesquisa. "
                "O retorno zero indica que, até aqui, não houve evidência pública detectável "
                "de audiovisual nas instituições mapeadas por esta coleta."
            )
        return

    detected_sites_display_df = detected_sites_df.assign(
        integridade=detected_sites_df["integrity_status"].map(format_integrity_status)
    )
    st.dataframe(
        detected_sites_display_df[
            [
                "institution",
                "archive_type",
                "integridade",
                "video_links_found_total",
                "embedded_video_signals_total",
                "platforms_detectadas",
                "country",
                "continent",
                "partner_domain",
                "warning",
                "final_url",
            ]
        ].rename(
            columns={
                "institution": "instituição",
                "archive_type": "tipo de arquivo",
                "integridade": "integridade",
                "video_links_found_total": "links de vídeo",
                "embedded_video_signals_total": "sinais embutidos",
                "platforms_detectadas": "plataformas detectadas",
                "country": "país",
                "continent": "continente",
                "partner_domain": "domínio",
                "warning": "observação",
                "final_url": "URL final",
            }
        ),
        use_container_width=True,
    )

    for _, row in detected_sites_df.iterrows():
        with st.expander(row["institution"]):
            render_integrity_badge(row["integrity_status"])
            st.write(f"Categoria: {classify_availability_group(row['integrity_status'])}")
            st.write(f"Subcategoria: {classify_availability_reason(row)}")
            if pd.notna(row.get("archive_type")) and str(row.get("archive_type")).strip():
                st.write(f"Tipo de arquivo: {row['archive_type']}")
            st.write(f"Domínio: {row['partner_domain']}")
            st.write(f"Status técnico: {format_technical_status(row['status'])}")
            st.write(f"Links de vídeo: {int(row['video_links_found_total'])}")
            st.write(f"Sinais embutidos: {int(row['embedded_video_signals_total'])}")
            if row.get("platforms_detectadas"):
                st.write(f"Plataformas detectadas: {row['platforms_detectadas']}")
            if pd.notna(row.get("warning")) and str(row.get("warning")).strip():
                st.warning(str(row["warning"]))
            if pd.notna(row.get(detail_url_field)) and str(row.get(detail_url_field)).strip():
                st.markdown(f"[Abrir {detail_url_label}]({row[detail_url_field]})")
            if pd.notna(row.get("final_url")) and str(row.get("final_url")).strip():
                st.markdown(f"[Abrir site institucional]({row['final_url']})")


def render_videos_tab(corpus_def, context, selected_theme):
    video_catalog_df = context["video_catalog_df"]
    theme_counts = context["theme_counts"]
    access_surface_counts = context["access_surface_counts"]
    curatorial_video_total = context["curatorial_video_total"]

    st.subheader("Catálogo curatorial de vídeos")
    if video_catalog_df.empty:
        st.info(f"Nenhum link de vídeo foi detectado ainda no corpus {corpus_def['short_label']}.")
        if corpus_def["category_code"] == "aggregator":
            st.caption(
                "Como esta é uma fonte geral de pesquisa, o retorno zero não invalida o corpus. "
                "Ele indica apenas ausência de evidência pública detectável de audiovisual nesta rodada."
            )
        return

    st.markdown(
        "Este catálogo organiza o recorte curatorial de vídeos a partir de metadados básicos e de uma "
        "classificação temática baseada em título, assunto e descrição, excluindo por padrão o ruído "
        "de plataforma ou incorporação externa."
    )

    overview_cols = st.columns(5)
    overview_cols[0].metric("Vídeos no recorte curatorial", curatorial_video_total)
    overview_cols[1].metric("Links de vídeo detectados", len(video_catalog_df))
    overview_cols[2].metric("Temas identificados", len(theme_counts))
    overview_cols[3].metric("Plataformas", int(video_catalog_df["platform"].nunique()))
    overview_cols[4].metric("Modalidades de acesso", len(access_surface_counts))

    summary_cols = st.columns(2)
    with summary_cols[0]:
        st.markdown("#### Distribuição temática")
        if not theme_counts.empty:
            st.dataframe(theme_counts, use_container_width=True, hide_index=True)
    with summary_cols[1]:
        st.markdown("#### Modalidades de acesso")
        if not access_surface_counts.empty:
            st.dataframe(access_surface_counts, use_container_width=True, hide_index=True)

    filter_cols = st.columns(2)
    video_platforms = sorted(video_catalog_df["platform"].dropna().unique().tolist())
    with filter_cols[0]:
        selected_platforms = st.multiselect(
            "Plataformas",
            options=video_platforms,
            default=video_platforms,
            key=f"{corpus_def['code']}-video-platforms",
        )
    available_continents = sorted(
        video_catalog_df["continent"].fillna("Não classificado").replace("", "Não classificado").unique().tolist()
    )
    with filter_cols[1]:
        selected_continents = st.multiselect(
            "Continentes",
            options=available_continents,
            default=available_continents,
            key=f"{corpus_def['code']}-video-continents",
        )

    if selected_theme == "Todos os temas":
        selected_themes = [
            theme
            for theme in video_catalog_df["video_theme"].dropna().unique().tolist()
            if theme != NOISE_THEME_LABEL
        ]
    else:
        selected_themes = [selected_theme]

    filtered_videos = video_catalog_df[
        video_catalog_df["platform"].isin(selected_platforms)
        & video_catalog_df["continent"].fillna("Não classificado").replace("", "Não classificado").isin(selected_continents)
        & video_catalog_df["video_theme"].isin(selected_themes)
    ].copy()

    st.caption(f"Tema selecionado: {selected_theme}.")
    st.caption(f"{len(filtered_videos)} vídeos no recorte atual.")

    video_view_mode = st.radio(
        "Organização dos vídeos",
        options=["Por tema", "Tabela"],
        horizontal=True,
        key=f"{corpus_def['code']}-video-view",
    )

    if video_view_mode == "Tabela":
        st.dataframe(
            filtered_videos[
                [
                    "institution",
                    "platform",
                    "access_surface",
                    "video_theme",
                    "video_title_display",
                    "video_date_display",
                    "country",
                    "continent",
                    "video_link",
                ]
            ].rename(
                columns={
                    "video_theme": "tema",
                    "access_surface": "modalidade de acesso",
                    "video_title_display": "título",
                    "video_date_display": "data",
                    "institution": "instituição",
                    "platform": "plataforma",
                    "country": "país",
                    "continent": "continente",
                    "video_link": "link",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        if filtered_videos.empty:
            st.info("Nenhum vídeo corresponde ao tema e aos filtros selecionados.")
        else:
            theme_order = filtered_videos["video_theme"].value_counts().index.tolist()
            expand_selected_theme = selected_theme != "Todos os temas"
            for theme_name in theme_order:
                theme_subset = filtered_videos.loc[
                    filtered_videos["video_theme"] == theme_name
                ].copy()
                theme_subset = theme_subset.sort_values(
                    ["institution", "platform", "video_date_display", "video_title_display"],
                    ascending=[True, True, False, True],
                )
                with st.expander(
                    f"{theme_name} ({len(theme_subset)})",
                    expanded=expand_selected_theme,
                ):
                    for _, row in theme_subset.iterrows():
                        st.markdown(f"**{row['video_title_display']}**")
                        st.caption(
                            f"{row['institution']} | {row['platform']} | "
                            f"{normalize_text(row['country'])} | {normalize_text(row['video_date_display'])}"
                        )
                        st.caption(f"Modalidade de acesso: {normalize_text(row['access_surface'])}")
                        st.markdown(f"[Abrir vídeo]({row['video_link']})")
                        st.code(row["video_link"], language=None)

    with st.expander("Ver quadros curatorias do catálogo", expanded=False):
        expander_cols = st.columns(2)
        with expander_cols[0]:
            if not theme_counts.empty:
                st.dataframe(theme_counts, use_container_width=True, hide_index=True)
            else:
                st.info("Ainda não há temas classificados para os vídeos.")
        with expander_cols[1]:
            if not access_surface_counts.empty:
                st.dataframe(access_surface_counts, use_container_width=True, hide_index=True)
            else:
                st.info("Ainda não há modalidades de acesso classificadas.")


def render_geo_tab(corpus_def, context):
    detected_sites_df = context["detected_sites_df"]
    continent_counts = context["continent_counts"]
    country_counts = context["country_counts"]

    st.subheader("Distribuição geográfica das instituições com evidência pública detectável de audiovisual")
    st.caption(
        "Este quadro considera as instituições nas quais a coleta encontrou ao menos um link explícito de vídeo."
    )
    geo_left, geo_right = st.columns(2)

    with geo_left:
        if not continent_counts.empty:
            st.caption("Distribuição por continente")
            st.bar_chart(continent_counts.set_index("continent"))
        else:
            st.info("Ainda não há distribuição geográfica com links de vídeo detectados.")

    with geo_right:
        if not country_counts.empty:
            st.caption("Distribuição por país")
            st.bar_chart(country_counts.set_index("country"))

    if detected_sites_df.empty or continent_counts.empty:
        return

    continent_filter = st.multiselect(
        "Filtrar continentes",
        options=continent_counts["continent"].tolist(),
        default=continent_counts["continent"].tolist(),
        key=f"{corpus_def['code']}-geo-continents",
    )
    geo_filtered = detected_sites_df[
        detected_sites_df["continent"]
        .fillna("Não classificado")
        .replace("", "Não classificado")
        .isin(continent_filter)
    ]
    geo_filtered_display_df = geo_filtered.assign(
        integridade=geo_filtered["integrity_status"].map(format_integrity_status)
    )
    st.dataframe(
        geo_filtered_display_df[
            [
                "institution",
                "archive_type",
                "continent",
                "country",
                "integridade",
                "video_links_found_total",
                "platforms_detectadas",
                "final_url",
            ]
        ].rename(
            columns={
                "institution": "instituição",
                "archive_type": "tipo de arquivo",
                "continent": "continente",
                "country": "país",
                "integridade": "integridade",
                "video_links_found_total": "links de vídeo",
                "platforms_detectadas": "plataformas detectadas",
                "final_url": "URL final",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_data_tab(corpus_def, context):
    available_df = context["available_df"]
    video_catalog_df = context["video_catalog_df"]
    visibility_counts = context["visibility_counts"]
    access_surface_counts = context["access_surface_counts"]
    access_regime_counts = context["access_regime_counts"]
    theme_counts = context["theme_counts"]
    theme_country_counts = context["theme_country_counts"]
    theme_country_matrix = context["theme_country_matrix"]
    theme_archive_type_counts = context["theme_archive_type_counts"]
    theme_archive_type_matrix = context["theme_archive_type_matrix"]
    visibility_archive_type_counts = context["visibility_archive_type_counts"]
    visibility_archive_type_matrix = context["visibility_archive_type_matrix"]

    st.subheader("Quadros analíticos do observatório")
    st.caption(
        "Esta aba reúne os principais quadros analíticos derivados da base do corpus e permite "
        "baixá-los em CSV para uso em pesquisa, redação, revisão metodológica e documentação."
    )

    output_files = corpus_def["output_files"]
    timeline_corpus_df = load_csv(output_files["timeline_corpus"])
    timeline_institutions_df = load_csv(output_files["timeline_institutions"])
    extinction_signals_df = load_csv(output_files["extinction_signals"])

    st.markdown("#### Conjuntos analíticos para download")
    download_col_1, download_col_2 = st.columns(2)
    with download_col_1:
        render_csv_download(
            "Baixar quadro institucional analítico",
            available_df,
            output_files["analytic_summary"],
            "Inclui disponibilidade, segmento institucional e situação metodológica do audiovisual por instituição.",
        )
        render_csv_download(
            "Baixar catálogo curatorial de vídeos",
            video_catalog_df,
            output_files["analytic_video_catalog"],
            "Inclui tema sugerido, data formatada e metadados básicos dos vídeos detectados.",
        )
        render_csv_download(
            "Baixar síntese temática",
            theme_counts,
            output_files["theme_summary"],
            "Síntese da classificação temática, excluindo ruído de plataforma.",
        )
        render_csv_download(
            "Baixar linha do tempo do corpus",
            timeline_corpus_df,
            output_files["timeline_corpus"],
            "Série histórica das rodadas do corpus, com contagens agregadas por observação.",
        )
    with download_col_2:
        render_csv_download(
            "Baixar síntese de visibilidade",
            visibility_counts,
            output_files["visibility_summary"],
            "Distribuição das situações metodológicas do audiovisual no corpus.",
        )
        render_csv_download(
            "Baixar modalidades de acesso",
            access_surface_counts,
            output_files["access_surface_summary"],
            "Síntese das modalidades de acesso detectadas no catálogo curatorial.",
        )
        render_csv_download(
            "Baixar regimes de acesso",
            access_regime_counts,
            output_files["access_regime_summary"],
            "Síntese institucional dos regimes de acesso audiovisual detectáveis.",
        )
        render_csv_download(
            "Baixar quadro temas por país",
            theme_country_counts,
            output_files["theme_country"],
            "Tabela analítica dos temas por país no recorte curatorial.",
        )
        render_csv_download(
            "Baixar quadro temas por tipo de arquivo",
            theme_archive_type_counts,
            output_files["theme_archive_type"],
            "Tabela analítica dos temas por tipo institucional declarado na fonte.",
        )
        render_csv_download(
            "Baixar sinais de possível extinção",
            extinction_signals_df,
            output_files["extinction_signals"],
            "Quadro de ausência, indisponibilidade reincidente e perda de evidência audiovisual entre rodadas.",
        )
        render_csv_download(
            "Baixar linha do tempo institucional",
            timeline_institutions_df,
            output_files["timeline_institutions"],
            "Série histórica por instituição, preservando os estados observados a cada rodada.",
        )

    st.markdown("#### Visualização dos quadros")
    analytic_view = st.radio(
        "Selecione o quadro analítico",
        options=[
            "Quadro institucional analítico",
            "Catálogo curatorial de vídeos",
            "Síntese de visibilidade",
            "Modalidades de acesso",
            "Regimes de acesso",
            "Síntese temática",
            "Temas por país",
            "Temas por tipo de arquivo",
            "Visibilidade por tipo de arquivo",
            "Linha do tempo do corpus",
            "Sinais de possível extinção",
            "Linha do tempo institucional",
        ],
        horizontal=True,
        key=f"{corpus_def['code']}-analytic-view",
    )

    if analytic_view == "Quadro institucional analítico":
        st.dataframe(
            build_summary_display_df(
                available_df,
                content_flag_field=corpus_def["content_flag_field"],
                content_flag_label=corpus_def["content_flag_label"],
                detail_url_field=corpus_def["detail_url_field"],
                detail_url_label=corpus_def["detail_url_label"],
                website_label=corpus_def["website_label"],
            ),
            use_container_width=True,
            hide_index=True,
        )
    elif analytic_view == "Catálogo curatorial de vídeos":
        st.dataframe(
            build_video_catalog_display_df(
                video_catalog_df,
                content_flag_field=corpus_def["content_flag_field"],
                content_flag_label=corpus_def["content_flag_label"],
                detail_url_field=corpus_def["detail_url_field"],
                detail_url_label=corpus_def["detail_url_label"],
                website_label=corpus_def["website_label"],
            ),
            use_container_width=True,
            hide_index=True,
        )
    elif analytic_view == "Síntese de visibilidade":
        st.dataframe(visibility_counts, use_container_width=True, hide_index=True)
    elif analytic_view == "Modalidades de acesso":
        st.dataframe(access_surface_counts, use_container_width=True, hide_index=True)
    elif analytic_view == "Regimes de acesso":
        st.dataframe(access_regime_counts, use_container_width=True, hide_index=True)
    elif analytic_view == "Síntese temática":
        st.dataframe(theme_counts, use_container_width=True, hide_index=True)
    elif analytic_view == "Temas por país":
        if not theme_country_matrix.empty:
            st.dataframe(
                style_matrix_display(prepare_matrix_display(theme_country_matrix)),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.dataframe(theme_country_counts, use_container_width=True, hide_index=True)
    elif analytic_view == "Temas por tipo de arquivo":
        if not theme_archive_type_matrix.empty:
            st.dataframe(
                style_matrix_display(prepare_matrix_display(theme_archive_type_matrix)),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.dataframe(theme_archive_type_counts, use_container_width=True, hide_index=True)
    elif analytic_view == "Linha do tempo do corpus":
        if timeline_corpus_df is None or timeline_corpus_df.empty:
            st.info("Ainda não há linha do tempo materializada para este corpus.")
        else:
            st.dataframe(timeline_corpus_df, use_container_width=True, hide_index=True)
    elif analytic_view == "Sinais de possível extinção":
        if extinction_signals_df is None or extinction_signals_df.empty:
            st.info(
                "Ainda não há sinais registrados nesta rodada. Isso pode significar estabilidade "
                "ou ausência de histórico suficiente para comparação."
            )
        else:
            st.dataframe(extinction_signals_df, use_container_width=True, hide_index=True)
    elif analytic_view == "Linha do tempo institucional":
        if timeline_institutions_df is None or timeline_institutions_df.empty:
            st.info("Ainda não há linha do tempo institucional materializada para este corpus.")
        else:
            st.dataframe(timeline_institutions_df, use_container_width=True, hide_index=True)
    else:
        if not visibility_archive_type_matrix.empty:
            st.dataframe(
                style_matrix_display(prepare_matrix_display(visibility_archive_type_matrix)),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.dataframe(visibility_archive_type_counts, use_container_width=True, hide_index=True)


def render_base_tab(corpus_def, context):
    available_df = context["available_df"]
    st.subheader(f"Base consolidada do {corpus_def['short_label']}")
    st.caption(
        "Cada linha representa uma unidade institucional do corpus, complementada pela verificação "
        "do site externo informado na fonte."
    )

    base_source_df = available_df.copy()
    base_source_df["continente_display"] = (
        base_source_df["continent"].fillna("Não classificado").astype(str).str.strip().replace("", "Não classificado")
    )
    base_source_df["tipo_arquivo_display"] = (
        base_source_df["archive_type"].fillna("Não informado na fonte").astype(str).str.strip().replace("", "Não informado na fonte")
    )

    filter_row_1 = st.columns(4)
    integrity_filter_options = sorted(base_source_df["integrity_status"].dropna().unique().tolist())
    visibility_filter_options = sorted(base_source_df["audiovisual_visibility"].dropna().unique().tolist())
    segment_filter_options = sorted(base_source_df["institution_segment"].dropna().unique().tolist())
    continent_filter_options = sorted(base_source_df["continente_display"].dropna().unique().tolist())

    with filter_row_1[0]:
        integrity_filter = st.multiselect(
            "Integridade",
            options=integrity_filter_options,
            default=integrity_filter_options,
            format_func=format_integrity_status,
            key=f"{corpus_def['code']}-base-integrity",
        )
    with filter_row_1[1]:
        visibility_filter = st.multiselect(
            "Situação metodológica do audiovisual",
            options=visibility_filter_options,
            default=visibility_filter_options,
            key=f"{corpus_def['code']}-base-visibility",
        )
    with filter_row_1[2]:
        segment_filter = st.multiselect(
            "Segmento institucional",
            options=segment_filter_options,
            default=segment_filter_options,
            key=f"{corpus_def['code']}-base-segment",
        )
    with filter_row_1[3]:
        continent_filter = st.multiselect(
            "Continente",
            options=continent_filter_options,
            default=continent_filter_options,
            key=f"{corpus_def['code']}-base-continent",
        )

    filter_row_2 = st.columns([1.1, 1.2, 0.9, 1.2])
    archive_type_filter_options = ["Todos"] + sorted(base_source_df["tipo_arquivo_display"].dropna().unique().tolist())
    access_regime_filter_options = ["Todos"] + sorted(
        base_source_df["access_regime"].fillna("Sem evidência suficiente").astype(str).str.strip().replace("", "Sem evidência suficiente").unique().tolist()
    )
    with filter_row_2[0]:
        archive_type_filter = st.selectbox(
            "Tipo de arquivo",
            options=archive_type_filter_options,
            key=f"{corpus_def['code']}-base-archive-type",
        )
    with filter_row_2[1]:
        access_regime_filter = st.selectbox(
            "Regime de acesso audiovisual",
            options=access_regime_filter_options,
            key=f"{corpus_def['code']}-base-access-regime",
        )
    with filter_row_2[2]:
        only_with_videos = st.checkbox("Somente com links de vídeo", value=False, key=f"{corpus_def['code']}-base-only-videos")
    with filter_row_2[3]:
        text_filter = st.text_input(
            "Busca textual",
            placeholder="Instituição, país, domínio ou código",
            key=f"{corpus_def['code']}-base-search",
        )

    filtered = base_source_df[
        base_source_df["integrity_status"].isin(integrity_filter)
        & base_source_df["audiovisual_visibility"].isin(visibility_filter)
        & base_source_df["institution_segment"].isin(segment_filter)
        & base_source_df["continente_display"].isin(continent_filter)
    ].copy()

    if archive_type_filter != "Todos":
        filtered = filtered.loc[filtered["tipo_arquivo_display"] == archive_type_filter].copy()

    if access_regime_filter != "Todos":
        filtered = filtered.loc[
            filtered["access_regime"].fillna("Sem evidência suficiente").astype(str).str.strip() == access_regime_filter
        ].copy()

    if only_with_videos:
        filtered = filtered.loc[
            pd.to_numeric(filtered["video_links_found_total"], errors="coerce").fillna(0) > 0
        ].copy()

    if text_filter.strip():
        search_text = text_filter.strip().lower()
        search_series = (
            filtered["institution"].fillna("").astype(str)
            + " "
            + filtered["country"].fillna("").astype(str)
            + " "
            + filtered["partner_domain"].fillna("").astype(str)
            + " "
            + filtered["repository_code"].fillna("").astype(str)
            + " "
            + filtered["tipo_arquivo_display"].fillna("").astype(str)
        ).str.lower()
        filtered = filtered.loc[search_series.str.contains(search_text, na=False)].copy()

    filtered = filtered.sort_values(["country", "institution"], ascending=[True, True])
    filtered_display_df = build_summary_display_df(
        filtered,
        content_flag_field=corpus_def["content_flag_field"],
        content_flag_label=corpus_def["content_flag_label"],
        detail_url_field=corpus_def["detail_url_field"],
        detail_url_label=corpus_def["detail_url_label"],
        website_label=corpus_def["website_label"],
    )

    filtered_total = len(filtered)
    filtered_website_total = int(filtered["website_available"].fillna(False).astype(bool).sum()) if not filtered.empty else 0
    filtered_visible_total = int(
        (filtered["audiovisual_visibility"] == "Evidência pública detectável de audiovisual").sum()
    ) if not filtered.empty else 0
    filtered_unavailable_total = int((filtered["availability_group"] == "Indisponível").sum()) if not filtered.empty else 0

    base_metric_cols = st.columns(4)
    base_metric_cols[0].metric("Instituições no recorte", filtered_total)
    base_metric_cols[1].metric("Com site informado na fonte", filtered_website_total)
    base_metric_cols[2].metric("Com evidência pública detectável", filtered_visible_total)
    base_metric_cols[3].metric("Indisponíveis no recorte", filtered_unavailable_total)

    render_csv_download(
        "Baixar recorte atual da base consolidada",
        filtered_display_df,
        f"{corpus_def['code']}_base_consolidada_filtrada.csv",
        "Exporta o recorte atual da base consolidada com rótulos públicos de leitura.",
    )

    st.markdown("#### Quadro sintético do recorte")
    if filtered_display_df.empty:
        st.info("Nenhuma instituição corresponde aos filtros selecionados.")
    else:
        summary_columns = [
            "instituição",
            "país",
            "continente",
            "tipo de arquivo",
            "integridade",
            "situação metodológica do audiovisual",
            "regime de acesso audiovisual detectável",
            "segmento institucional",
            "links de vídeo",
            "sinais embutidos",
            "páginas internas",
            corpus_def["website_label"],
            "domínio",
        ]
        available_summary_columns = [column for column in summary_columns if column in filtered_display_df.columns]
        st.dataframe(
            filtered_display_df[available_summary_columns],
            use_container_width=True,
            hide_index=True,
        )

        with st.expander("Ver quadro completo do recorte", expanded=False):
            st.dataframe(filtered_display_df, use_container_width=True, hide_index=True)


def render_institution_tab(corpus_def, context, selected_slug):
    summary_df = context["available_df"]
    links_df = context["links_df"]
    internal_df = context["internal_df"]
    detail_url_field = corpus_def["detail_url_field"]

    selected_summary = summary_df.loc[summary_df["slug"].astype(str) == str(selected_slug)].iloc[0]
    selected_links = (
        links_df.loc[links_df["slug"].astype(str) == str(selected_slug)]
        .drop_duplicates(subset=["platform", "video_link"])
        .sort_values(["platform", "video_link"])
        .copy()
    )
    selected_internal = pd.DataFrame()
    if not internal_df.empty:
        selected_internal = internal_df.loc[internal_df["slug"].astype(str) == str(selected_slug)].copy()

    institution_video_count = int(selected_summary["video_links_found_total"])
    institution_embedded_count = int(selected_summary["embedded_video_signals_total"])
    institution_internal_count = int(selected_summary["candidate_internal_pages"])
    institution_visibility = classify_audiovisual_visibility(selected_summary)
    institution_category = classify_availability_group(selected_summary["integrity_status"])
    institution_subcategory = classify_availability_reason(selected_summary)

    st.subheader(selected_summary["institution"])
    headline_cols = st.columns([1, 1, 2])
    with headline_cols[0]:
        st.caption("Integridade")
        render_integrity_badge(selected_summary["integrity_status"])
    with headline_cols[1]:
        st.caption("Status técnico")
        st.write(format_technical_status(selected_summary["status"]))
    with headline_cols[2]:
        st.caption("Situação metodológica do audiovisual")
        st.write(institution_visibility)

    geo_cols = st.columns(4)
    geo_cols[0].metric(
        "País",
        selected_summary["country"] if pd.notna(selected_summary["country"]) and selected_summary["country"] else "-",
    )
    geo_cols[1].metric(
        "Continente",
        selected_summary["continent"] if pd.notna(selected_summary["continent"]) and selected_summary["continent"] else "Não classificado",
    )
    geo_cols[2].metric(
        "Tipo de arquivo",
        selected_summary["archive_type"] if pd.notna(selected_summary["archive_type"]) and selected_summary["archive_type"] else "-",
    )
    geo_cols[3].metric(corpus_def["website_label"], format_yes_no(selected_summary.get("website_available")))

    evidence_cols = st.columns(4)
    evidence_cols[0].metric("HTTP", selected_summary["http_code"] if pd.notna(selected_summary["http_code"]) else "-")
    evidence_cols[1].metric("Links de vídeo", institution_video_count)
    evidence_cols[2].metric("Sinais embutidos", institution_embedded_count)
    evidence_cols[3].metric("Páginas internas", institution_internal_count)

    if selected_summary["integrity_status"] in {"integro", "acessivel"}:
        st.success("O site externo respondeu. Esta instituição pode seguir para curadoria pública.")
    elif selected_summary["integrity_status"] == "suspeito":
        st.warning("O site respondeu, mas a página final parece genérica, suspensa ou não confiável. Aqui ele entra dentro da categoria quebrado.")
    elif selected_summary["integrity_status"] == "restrito":
        st.warning("O site respondeu com restrição de acesso. Para o projeto, ele entra como não disponível.")
    elif selected_summary["integrity_status"] == "sem_site":
        st.warning("A fonte não informa um site externo para esta instituição.")
    else:
        st.error("O site institucional não respondeu de forma confiável. Para o projeto, esta instituição entra como não disponível.")

    institution_tab_overview, institution_tab_videos, institution_tab_internal = st.tabs(
        [
            "Ficha e acesso",
            f"Vídeos detectados ({len(selected_links)})",
            f"Páginas internas ({len(selected_internal)})",
        ]
    )

    with institution_tab_overview:
        overview_left, overview_right = st.columns([1, 1.2])

        with overview_left:
            st.subheader("Leitura metodológica")
            classification_df = pd.DataFrame(
                [
                    {"eixo": "Categoria", "valor": institution_category},
                    {"eixo": "Subcategoria", "valor": institution_subcategory},
                    {"eixo": "Situação metodológica do audiovisual", "valor": institution_visibility},
                    {
                        "eixo": "Regime de acesso audiovisual detectável",
                        "valor": normalize_optional_text(selected_summary.get("access_regime")) or "Sem evidência suficiente",
                    },
                    {
                        "eixo": "Modalidades de acesso detectadas",
                        "valor": normalize_optional_text(selected_summary.get("access_modalities_detected")) or "-",
                    },
                    {"eixo": corpus_def["content_flag_label"], "valor": format_yes_no(selected_summary.get(corpus_def["content_flag_field"]))},
                    {"eixo": corpus_def["website_label"], "valor": format_yes_no(selected_summary.get("website_available"))},
                ]
            )
            st.dataframe(classification_df, use_container_width=True, hide_index=True)

            if pd.notna(selected_summary.get("warning")) and str(selected_summary.get("warning")).strip():
                st.info(str(selected_summary["warning"]))

            if pd.notna(selected_summary.get("error")) and str(selected_summary.get("error")).strip():
                st.caption(f"Erro registrado na coleta: {selected_summary['error']}")

        with overview_right:
            st.subheader("Fontes e endereços")
            source_links = pd.DataFrame(
                [
                    {"recurso": corpus_def["detail_url_label"], "endereço": normalize_optional_text(selected_summary.get(detail_url_field)) or "-"},
                    {"recurso": "Site externo informado", "endereço": normalize_optional_text(selected_summary.get("partner_site")) or "-"},
                    {"recurso": "URL final verificada", "endereço": normalize_optional_text(selected_summary.get("final_url")) or "-"},
                    {"recurso": "Domínio", "endereço": normalize_optional_text(selected_summary.get("partner_domain")) or "-"},
                    {"recurso": "Código do repositório", "endereço": normalize_optional_text(selected_summary.get("repository_code")) or "-"},
                ]
            )
            st.dataframe(source_links, use_container_width=True, hide_index=True)

            if pd.notna(selected_summary.get(detail_url_field)) and str(selected_summary.get(detail_url_field)).strip():
                st.link_button(f"Abrir {corpus_def['detail_url_label']}", selected_summary[detail_url_field], use_container_width=True)
            if pd.notna(selected_summary.get("final_url")) and str(selected_summary.get("final_url")).strip():
                st.link_button("Abrir site institucional verificado", selected_summary["final_url"], use_container_width=True)

    with institution_tab_videos:
        st.subheader("Vídeos detectados na instituição")
        if selected_links.empty:
            st.info("Nenhum link de vídeo foi detectado automaticamente para esta instituição.")
        else:
            selected_links = selected_links.copy()
            selected_links["tema_sugerido"] = selected_links.apply(infer_video_theme, axis=1)
            selected_links["modalidade_acesso"] = selected_links.apply(analysis_utils.classify_access_surface, axis=1)
            selected_links["data_publicacao"] = selected_links["video_published_at"].apply(format_video_date)

            video_overview_cols = st.columns(4)
            video_overview_cols[0].metric("Links detectados", len(selected_links))
            video_overview_cols[1].metric("Plataformas", int(selected_links["platform"].nunique()))
            video_overview_cols[2].metric(
                "Temas sugeridos",
                int(selected_links["tema_sugerido"].replace(NOISE_THEME_LABEL, pd.NA).dropna().nunique()),
            )
            video_overview_cols[3].metric("Modalidades de acesso", int(selected_links["modalidade_acesso"].nunique()))

            video_table_df = selected_links[
                [
                    "platform",
                    "modalidade_acesso",
                    "tema_sugerido",
                    "video_title",
                    "video_subject",
                    "data_publicacao",
                    "video_link",
                ]
            ].copy()
            video_table_df["titulo_display"] = (
                video_table_df["video_title"].fillna("").astype(str).str.strip()
            )
            empty_title_mask = video_table_df["titulo_display"] == ""
            video_table_df.loc[empty_title_mask, "titulo_display"] = (
                video_table_df.loc[empty_title_mask, "video_subject"].fillna("").astype(str).str.strip()
            )
            empty_title_mask = video_table_df["titulo_display"] == ""
            video_table_df.loc[empty_title_mask, "titulo_display"] = video_table_df.loc[empty_title_mask, "video_link"]

            st.dataframe(
                video_table_df[
                    ["platform", "modalidade_acesso", "tema_sugerido", "titulo_display", "data_publicacao", "video_link"]
                ].rename(
                    columns={
                        "platform": "plataforma",
                        "modalidade_acesso": "modalidade de acesso",
                        "tema_sugerido": "tema sugerido",
                        "titulo_display": "título",
                        "data_publicacao": "data de publicação",
                        "video_link": "link do vídeo",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

            for index, row in selected_links.iterrows():
                title = normalize_optional_text(row.get("video_title")) or normalize_optional_text(row.get("video_subject")) or row["video_link"]
                published_at = format_video_date(row.get("video_published_at"))
                theme_label = infer_video_theme(row)
                with st.expander(f"{index + 1}. {title}", expanded=False):
                    meta_cols = st.columns(4)
                    meta_cols[0].caption(f"Plataforma: {normalize_text(row['platform'])}")
                    meta_cols[1].caption(f"Tema sugerido: {theme_label}")
                    meta_cols[2].caption(
                        f"Modalidade de acesso: {analysis_utils.classify_access_surface(row)}"
                    )
                    meta_cols[3].caption(f"Data de publicação: {published_at or '-'}")
                    description = normalize_optional_text(row.get("video_description"))
                    if description:
                        st.write(description)
                    st.markdown(f"[Abrir vídeo]({row['video_link']})")
                    if "youtube.com" in row["video_link"] or "youtu.be" in row["video_link"]:
                        st.video(row["video_link"])
                    else:
                        vimeo_embed = get_vimeo_embed_url(row["video_link"])
                        if vimeo_embed:
                            components.iframe(vimeo_embed, height=360)
                    st.code(row["video_link"], language=None)

    with institution_tab_internal:
        st.subheader("Páginas internas analisadas")
        if selected_internal.empty:
            st.info("Nenhuma página interna foi analisada para esta instituição.")
        else:
            selected_internal = selected_internal.copy()
            selected_internal["status_tecnico"] = selected_internal["status"].map(format_technical_status)

            internal_video_hits = int(pd.to_numeric(selected_internal["video_links_found"], errors="coerce").fillna(0).sum())
            internal_embedded_hits = int(pd.to_numeric(selected_internal["embedded_signals"], errors="coerce").fillna(0).sum())

            internal_metric_cols = st.columns(3)
            internal_metric_cols[0].metric("Páginas analisadas", len(selected_internal))
            internal_metric_cols[1].metric("Links encontrados nessas páginas", internal_video_hits)
            internal_metric_cols[2].metric("Sinais embutidos nessas páginas", internal_embedded_hits)

            st.dataframe(
                selected_internal[
                    [
                        "internal_page",
                        "status_tecnico",
                        "http_code",
                        "video_links_found",
                        "embedded_signals",
                        "warning",
                        "error",
                    ]
                ].rename(
                    columns={
                        "internal_page": "página interna",
                        "status_tecnico": "status técnico",
                        "http_code": "HTTP",
                        "video_links_found": "links de vídeo",
                        "embedded_signals": "sinais embutidos",
                        "warning": "observação",
                        "error": "erro",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )


def render_corpus_tab(corpus_def):
    category_def = CORPUS_CATEGORIES[corpus_def["category_code"]]
    runtime = build_corpus_runtime(corpus_def)
    dashboard_sources = runtime["dashboard_sources"]
    summary_df = dashboard_sources["summary"]
    snapshot_metadata = runtime["snapshot_metadata"]

    st.markdown(f"## {corpus_def['label']}")
    st.caption(
        f"Categoria analítica: {category_def['label']}. "
        f"Etapa de expansão: {category_def['expansion_stage_label']}. "
        f"Unidade do observatório: {corpus_def['scope']}."
    )
    if snapshot_metadata:
        source_status_date = normalize_optional_text(snapshot_metadata.get("source_status_date")) or "-"
        analytic_updated_at = format_snapshot_timestamp(snapshot_metadata.get("analytic_outputs_last_modified_at")) or "-"
        metadata_generated_at = format_snapshot_timestamp(snapshot_metadata.get("generated_at")) or "-"
        st.caption(
            f"Fonte-base com status de {source_status_date}. "
            f"Camada analítica atualizada em {analytic_updated_at}. "
            f"Metadados da rodada gerados em {metadata_generated_at}."
        )

    if summary_df is None:
        st.info(
            f"Nenhum relatório de {corpus_def['short_label']} foi gerado ainda. "
            f"Execute `{corpus_def['run_script']}` primeiro."
        )
        return

    if summary_df.empty:
        st.warning(
            f"O relatório de {corpus_def['short_label']} foi gerado, mas veio sem instituições. "
            f"Revise a execução de `{corpus_def['run_script']}`."
        )
        return

    base_data = runtime["base_data"]
    overview_data = runtime["overview_data"]

    summary_df = base_data.summary_df
    links_df = base_data.links_df
    internal_df = base_data.internal_df
    summary_analysis_df = base_data.summary_analysis_df
    video_catalog_base_df = base_data.video_catalog_df
    available_slugs = base_data.available_slugs
    segmented_summary_df = base_data.segmented_summary_df.copy()

    if not available_slugs:
        st.warning(
            f"O relatório de {corpus_def['short_label']} não trouxe slugs de instituição. "
            "Revise o CSV principal antes de abrir a interface."
        )
        return

    with st.expander("Filtros e navegação do corpus", expanded=True):
        selector_cols = st.columns([1.2, 1.4, 1.2])
        segment_options = [
            SEGMENT_AVAILABLE_WITH_VIDEOS,
            SEGMENT_AVAILABLE_WITHOUT_VIDEOS,
            SEGMENT_UNAVAILABLE,
        ]
        with selector_cols[0]:
            selected_segment = st.radio(
                "Recorte da lista",
                options=segment_options,
                format_func=lambda value: format_segment_label(segmented_summary_df, value),
                key=f"{corpus_def['code']}-segment",
            )
        filtered_summary_df = segmented_summary_df.loc[
            segmented_summary_df["institution_segment"]
            .astype(str)
            .map(coerce_segment_label)
            == selected_segment
        ].sort_values("institution")
        filtered_slugs = filtered_summary_df["slug"].astype(str).tolist()
        if not filtered_slugs:
            filtered_slugs = available_slugs
            st.info("Nenhuma instituição se enquadra neste recorte; a lista completa foi restaurada.")

        with selector_cols[1]:
            selected_slug = st.selectbox(
                "Selecione uma instituição",
                options=filtered_slugs,
                format_func=lambda slug: format_institution_label(summary_df, slug),
                key=f"{corpus_def['code']}-institution",
            )

        sidebar_theme_options = []
        if not video_catalog_base_df.empty:
            sidebar_theme_options = sorted(
                [
                    theme
                    for theme in video_catalog_base_df["video_theme"].dropna().unique().tolist()
                    if theme != NOISE_THEME_LABEL
                ]
            )
        with selector_cols[2]:
            selected_theme = st.selectbox(
                "Tema do catálogo",
                options=["Todos os temas"] + sidebar_theme_options,
                key=f"{corpus_def['code']}-theme",
            )

    total = overview_data.total_institutions
    with_video = overview_data.institutions_with_video
    integral_count = overview_data.integral_count
    available_df = summary_analysis_df.copy()
    availability_groups = overview_data.availability_groups
    availability_reasons = overview_data.availability_reasons
    archive_type_counts = overview_data.archive_type_counts
    visibility_counts = overview_data.visibility_counts
    access_surface_counts = overview_data.access_surface_counts
    access_regime_counts = overview_data.access_regime_counts
    unavailable_count = overview_data.unavailable_count
    website_count = overview_data.website_count
    detected_sites_df = overview_data.detected_sites_df
    continent_counts = overview_data.continent_counts
    country_counts = overview_data.country_counts
    platform_counts = overview_data.platform_counts
    video_catalog_df = video_catalog_base_df.copy()
    theme_counts = overview_data.theme_counts
    theme_country_counts = overview_data.theme_country_counts
    theme_country_matrix = overview_data.theme_country_matrix
    theme_platform_counts = overview_data.theme_platform_counts
    theme_archive_type_counts = overview_data.theme_archive_type_counts
    theme_archive_type_matrix = overview_data.theme_archive_type_matrix
    visibility_archive_type_counts = overview_data.visibility_archive_type_counts
    visibility_archive_type_matrix = overview_data.visibility_archive_type_matrix
    availability_reference_df = overview_data.availability_reference_df
    curatorial_video_total = int(theme_counts["total"].sum()) if not theme_counts.empty else 0

    visible_audiovisual_count = get_summary_total(
        visibility_counts,
        "situacao",
        "Evidência pública detectável de audiovisual",
    )
    indirect_audiovisual_count = get_summary_total(
        visibility_counts,
        "situacao",
        "Evidência pública indireta de audiovisual",
    )
    internal_navigation_count = get_summary_total(
        visibility_counts,
        "situacao",
        "Potencial audiovisual em navegação interna",
    )
    no_public_evidence_count = get_summary_total(
        visibility_counts,
        "situacao",
        "Sem evidência pública detectável de audiovisual",
    )
    unavailable_verification_count = get_summary_total(
        visibility_counts,
        "situacao",
        "Site indisponível para verificação",
    )

    metric_cols = st.columns(4)
    metric_cols[0].metric(f"Instituições {corpus_def['short_label']}", total)
    metric_cols[1].metric("Instituições com site informado", website_count)
    metric_cols[2].metric("Sites íntegros", integral_count)
    metric_cols[3].metric("Instituições com links de vídeo", with_video)

    visibility_metric_cols = st.columns(5)
    visibility_metric_cols[0].metric("Evidência pública detectável", visible_audiovisual_count)
    visibility_metric_cols[1].metric("Evidência indireta", indirect_audiovisual_count)
    visibility_metric_cols[2].metric("Potencial em navegação interna", internal_navigation_count)
    visibility_metric_cols[3].metric("Sem evidência pública detectável", no_public_evidence_count)
    visibility_metric_cols[4].metric("Site indisponível para verificação", unavailable_verification_count)

    context = {
        "summary_df": summary_df,
        "links_df": links_df,
        "internal_df": internal_df,
        "available_df": available_df,
        "availability_groups": availability_groups,
        "availability_reasons": availability_reasons,
        "archive_type_counts": archive_type_counts,
        "visibility_counts": visibility_counts,
        "access_surface_counts": access_surface_counts,
        "access_regime_counts": access_regime_counts,
        "unavailable_count": unavailable_count,
        "website_count": website_count,
        "detected_sites_df": detected_sites_df,
        "continent_counts": continent_counts,
        "country_counts": country_counts,
        "platform_counts": platform_counts,
        "video_catalog_df": video_catalog_df,
        "theme_counts": theme_counts,
        "theme_country_counts": theme_country_counts,
        "theme_country_matrix": theme_country_matrix,
        "theme_platform_counts": theme_platform_counts,
        "theme_archive_type_counts": theme_archive_type_counts,
        "theme_archive_type_matrix": theme_archive_type_matrix,
        "visibility_archive_type_counts": visibility_archive_type_counts,
        "visibility_archive_type_matrix": visibility_archive_type_matrix,
        "availability_reference_df": availability_reference_df,
        "curatorial_video_total": curatorial_video_total,
        "with_video": with_video,
    }

    tab_project, tab_dashboard, tab_sites, tab_videos, tab_geo, tab_data, tab_base, tab_institution = st.tabs(
        [
            "Projeto",
            "Painel",
            f"Instituições com links de vídeo ({with_video})",
            f"Catálogo curatorial de vídeos ({curatorial_video_total})",
            "Geografia",
            "Quadros analíticos",
            "Base consolidada",
            "Página da instituição",
        ]
    )

    with tab_project:
        render_project_tab(corpus_def)
    with tab_dashboard:
        render_panel_tab(corpus_def, context)
    with tab_sites:
        render_sites_tab(corpus_def, context)
    with tab_videos:
        render_videos_tab(corpus_def, context, selected_theme)
    with tab_geo:
        render_geo_tab(corpus_def, context)
    with tab_data:
        render_data_tab(corpus_def, context)
    with tab_base:
        render_base_tab(corpus_def, context)
    with tab_institution:
        render_institution_tab(corpus_def, context, selected_slug)

st.title("Plataforma aberta de curadoria e acesso à memória audiovisual em rede")
st.caption(
    "O observatório funciona como um organismo agregador mundial em construção, separando explicitamente "
    "agregadores arquivísticos e arquivos ou instituições custodiais para preservar o rigor analítico."
)

top_level_tabs = st.tabs(
    ["Observatório | visão geral"]
    + [f"Categoria | {category_def['short_label']}" for category_def in CORPUS_CATEGORIES.values()]
    + [f"{definition['short_label']} | {definition['label']}" for definition in CORPORA.values()]
)

with top_level_tabs[0]:
    render_observatory_overview_tab()

category_tabs = top_level_tabs[1 : 1 + len(CORPUS_CATEGORIES)]
corpus_tabs = top_level_tabs[1 + len(CORPUS_CATEGORIES) :]

for category_tab, category_def in zip(category_tabs, CORPUS_CATEGORIES.values()):
    with category_tab:
        render_category_tab(category_def)

for corpus_tab, corpus_def in zip(corpus_tabs, CORPORA.values()):
    with corpus_tab:
        render_corpus_tab(corpus_def)
