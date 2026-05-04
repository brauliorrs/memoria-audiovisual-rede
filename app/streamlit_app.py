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
from memoria_audiovisual.dashboard_data import (
    DASHBOARD_SOURCE_KEYS,
    build_dashboard_base_data,
    build_dashboard_overview_data,
)
from memoria_audiovisual.output_files import APE_OUTPUT_FILES, list_ape_output_filenames

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


def build_summary_display_df(dataframe):
    if dataframe is None or dataframe.empty:
        return pd.DataFrame()

    display_df = dataframe.copy()
    if "status" in display_df.columns:
        display_df["status_tecnico_display"] = display_df["status"].map(format_technical_status)
    if "integrity_status" in display_df.columns:
        display_df["integridade_display"] = display_df["integrity_status"].map(format_integrity_status)
    if "website_available" in display_df.columns:
        display_df["website_available_display"] = display_df["website_available"].map(format_yes_no)
    if "content_available_in_ape" in display_df.columns:
        display_df["content_available_display"] = display_df["content_available_in_ape"].map(format_yes_no)
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
        "ape_detail_url",
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
            "content_available_display": "conteúdo publicado no APE",
            "website_available_display": "webpage no APE",
            "availability_group": "categoria",
            "availability_reason": "subcategoria",
            "audiovisual_visibility": "situação metodológica do audiovisual",
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
            "ape_detail_url": "ficha da instituição no APE",
        }
    )


def build_video_catalog_display_df(dataframe):
    if dataframe is None or dataframe.empty:
        return pd.DataFrame()

    display_df = dataframe.copy()
    if "website_available" in display_df.columns:
        display_df["website_available_display"] = display_df["website_available"].map(format_yes_no)
    if "content_available_in_ape" in display_df.columns:
        display_df["content_available_display"] = display_df["content_available_in_ape"].map(format_yes_no)
    if "continent" in display_df.columns:
        display_df["continent"] = display_df["continent"].fillna("Não classificado").replace("", "Não classificado")

    preferred_columns = [
        "institution",
        "archive_type",
        "country",
        "continent",
        "platform",
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
        "ape_detail_url",
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
            "video_theme": "tema",
            "video_title_display": "título do vídeo",
            "video_date_display": "data do vídeo",
            "video_subject": "assunto do vídeo",
            "video_description": "descrição do vídeo",
            "website_available_display": "webpage no APE",
            "content_available_display": "conteúdo publicado no APE",
            "partner_site": "site externo informado",
            "video_link": "link do vídeo",
            "repository_code": "código do repositório",
            "ape_detail_url": "ficha da instituição no APE",
        }
    )


def get_summary_total(dataframe, label_column, label_value):
    if dataframe is None or dataframe.empty or label_column not in dataframe.columns or "total" not in dataframe.columns:
        return 0
    filtered = dataframe.loc[dataframe[label_column] == label_value, "total"]
    if filtered.empty:
        return 0
    return int(pd.to_numeric(filtered, errors="coerce").fillna(0).sum())


dashboard_sources = {
    key: load_csv(APE_OUTPUT_FILES[key])
    for key in DASHBOARD_SOURCE_KEYS
}

summary_df = dashboard_sources["summary"]
snapshot_metadata = load_json(APE_OUTPUT_FILES["snapshot_metadata"])

st.title("Plataforma aberta de curadoria e acesso à memória audiovisual em rede")
st.caption(
    "Versão focada no Archives Portal Europe (APE), a partir da lista oficial de instituições "
    "com conteúdo publicado e da verificação dos sites externos de cada instituição."
)
if snapshot_metadata:
    source_status_date = normalize_optional_text(snapshot_metadata.get("source_status_date")) or "-"
    analytic_updated_at = (
        format_snapshot_timestamp(snapshot_metadata.get("analytic_outputs_last_modified_at")) or "-"
    )
    metadata_generated_at = (
        format_snapshot_timestamp(snapshot_metadata.get("generated_at")) or "-"
    )
    st.caption(
        f"Fonte-base do APE com status de {source_status_date}. "
        f"Camada analítica atualizada em {analytic_updated_at}. "
        f"Metadados da rodada gerados em {metadata_generated_at}."
    )

if summary_df is None:
    st.warning("Nenhum relatório do APE foi gerado ainda. Execute `python scripts/run_pipeline.py` primeiro.")
    st.stop()

if summary_df.empty:
    st.warning(
        "O relatório do APE foi gerado, mas veio sem instituições. Revise a execução do "
        "`scripts/run_pipeline.py` e confira o arquivo `data/output/ape_relatorio.txt`."
    )
    st.stop()

base_data = build_dashboard_base_data(
    catalog_df=dashboard_sources["institutions"],
    summary_df=summary_df,
    links_df=dashboard_sources["video_links"],
    internal_df=dashboard_sources["internal_pages"],
    summary_analysis_source_df=dashboard_sources["analytic_summary"],
    video_catalog_source_df=dashboard_sources["analytic_video_catalog"],
)

catalog_df = base_data.catalog_df
summary_df = base_data.summary_df
links_df = base_data.links_df
internal_df = base_data.internal_df
summary_analysis_df = base_data.summary_analysis_df
video_catalog_base_df = base_data.video_catalog_df
available_slugs = base_data.available_slugs

query_params = st.query_params
requested_slug = query_params.get("instituicao")
if not available_slugs:
    st.warning(
        "O relatório do APE não trouxe slugs de instituição. Revise o CSV "
        "`data/output/ape_resumo_instituicoes.csv` antes de abrir a interface."
    )
    st.stop()
segmented_summary_df = base_data.segmented_summary_df.copy()


def format_institution_label(slug):
    label_series = summary_df.loc[summary_df["slug"].astype(str) == str(slug), "institution"]
    if label_series.empty:
        return str(slug)
    label = normalize_optional_text(label_series.iloc[0])
    return label or str(slug)


def format_segment_label(segment_name):
    total = int(
        segmented_summary_df["institution_segment"]
        .astype(str)
        .map(coerce_segment_label)
        .eq(segment_name)
        .sum()
    )
    return f"{segment_name} ({total})"

sidebar_mode = st.sidebar.radio(
    "Modo",
    options=["Visão geral", "Página da instituição"],
)

st.sidebar.subheader("Instituição")
st.sidebar.caption(
    "A lista separa instituições com vídeos clicáveis, instituições disponíveis sem vídeos "
    "e instituições indisponíveis."
)
segment_options = [
    SEGMENT_AVAILABLE_WITH_VIDEOS,
    SEGMENT_AVAILABLE_WITHOUT_VIDEOS,
    SEGMENT_UNAVAILABLE,
]

default_segment = SEGMENT_AVAILABLE_WITH_VIDEOS
if requested_slug in available_slugs:
    requested_segment_series = segmented_summary_df.loc[
        segmented_summary_df["slug"].astype(str) == str(requested_slug),
        "institution_segment",
    ]
    if not requested_segment_series.empty:
        requested_segment = coerce_segment_label(requested_segment_series.iloc[0])
        if requested_segment in segment_options:
            default_segment = requested_segment

selected_segment = st.sidebar.radio(
    "Recorte da lista",
    options=segment_options,
    index=segment_options.index(default_segment),
    format_func=format_segment_label,
)

filtered_summary_df = segmented_summary_df.loc[
    segmented_summary_df["institution_segment"]
    .astype(str)
    .map(coerce_segment_label)
    == selected_segment
].sort_values("institution")
filtered_slugs = filtered_summary_df["slug"].astype(str).tolist()

if not filtered_slugs:
    st.sidebar.info("Nenhuma instituição se enquadra neste recorte.")
    filtered_slugs = available_slugs

default_slug = requested_slug if requested_slug in filtered_slugs else filtered_slugs[0]

selected_slug = st.sidebar.selectbox(
    "Selecione uma instituição do APE",
    options=filtered_slugs,
    index=filtered_slugs.index(default_slug),
    format_func=format_institution_label,
)
query_params["instituicao"] = selected_slug

sidebar_video_catalog_df = video_catalog_base_df.copy()
sidebar_theme_options = []
if not sidebar_video_catalog_df.empty:
    sidebar_theme_options = sorted(
        [
            theme
            for theme in sidebar_video_catalog_df["video_theme"].dropna().unique().tolist()
            if theme != NOISE_THEME_LABEL
        ]
    )

st.sidebar.subheader("Tema")
selected_sidebar_theme = st.sidebar.selectbox(
    "Selecione o tema",
    options=["Todos os temas"] + sidebar_theme_options,
)

selected_summary = summary_df.loc[summary_df["slug"].astype(str) == str(selected_slug)].iloc[0]
selected_links = (
    links_df.loc[links_df["slug"].astype(str) == str(selected_slug)]
    .drop_duplicates(subset=["platform", "video_link"])
    .sort_values(["platform", "video_link"])
    .copy()
)

if sidebar_mode == "Visão geral":
    overview_data = build_dashboard_overview_data(
        base_data,
        availability_groups_source_df=dashboard_sources["availability_summary"],
        availability_reasons_source_df=dashboard_sources["availability_reasons"],
        archive_type_counts_source_df=dashboard_sources["archive_type_summary"],
        visibility_counts_source_df=dashboard_sources["visibility_summary"],
        theme_counts_source_df=dashboard_sources["theme_summary"],
        theme_country_counts_source_df=dashboard_sources["theme_country"],
        theme_platform_counts_source_df=dashboard_sources["theme_platform"],
        theme_archive_type_counts_source_df=dashboard_sources["theme_archive_type"],
        visibility_archive_type_counts_source_df=dashboard_sources["visibility_archive_type"],
    )

    total = overview_data.total_institutions
    with_video = overview_data.institutions_with_video
    integral_count = overview_data.integral_count
    available_df = summary_analysis_df.copy()
    availability_groups = overview_data.availability_groups
    availability_reasons = overview_data.availability_reasons
    archive_type_counts = overview_data.archive_type_counts
    visibility_counts = overview_data.visibility_counts
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
    metric_cols[0].metric("Instituições APE", total)
    metric_cols[1].metric("Instituições com webpage externa", website_count)
    metric_cols[2].metric("Sites íntegros", integral_count)
    metric_cols[3].metric("Instituições com links de vídeo", with_video)

    visibility_metric_cols = st.columns(5)
    visibility_metric_cols[0].metric("Evidência pública detectável", visible_audiovisual_count)
    visibility_metric_cols[1].metric("Evidência indireta", indirect_audiovisual_count)
    visibility_metric_cols[2].metric("Potencial em navegação interna", internal_navigation_count)
    visibility_metric_cols[3].metric("Sem evidência pública detectável", no_public_evidence_count)
    visibility_metric_cols[4].metric("Site indisponível para verificação", unavailable_verification_count)

    available_with_video_count = overview_data.available_with_video_count

    st.info(
        "Nesta etapa, o APE funciona como base institucional principal e como corpus "
        "predominantemente de arquivos gerais. A aplicação verifica a ficha da instituição no "
        "portal e depois testa o site externo informado em `Webpage`."
    )
    st.caption(
        f"Nesta interface, toda instituição com link de vídeo detectado entra em `Disponíveis com vídeos` "
        f"({available_with_video_count} no total), mesmo quando o site atual exige ressalva de integridade."
    )

    tab_project, tab_dashboard, tab_sites, tab_videos, tab_geo, tab_data, tab_base = st.tabs(
        [
            "Projeto",
            "Painel",
            f"Instituições com links de vídeo ({with_video})",
            f"Catálogo curatorial de vídeos ({curatorial_video_total})",
            "Geografia",
            "Quadros analíticos",
            "Base consolidada",
        ]
    )

    with tab_project:
        st.subheader("Sobre o projeto")
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

            **O que a plataforma afirma com maior segurança**

            - quando há evidência pública detectável de audiovisual;
            - quando há apenas evidência pública indireta;
            - quando não foi encontrada evidência pública detectável de audiovisual;
            - quando o site não pôde ser verificado.

            **O que a plataforma evita afirmar**

            - que a ausência de evidência pública detectável equivale à inexistência de acervo audiovisual;
            - que todo arquivo geral deva colocar o audiovisual em destaque na sua mediação institucional;
            - que classificações institucionais inferidas a partir do nome substituam a tipologia declarada na fonte.

            **Fonte institucional utilizada**

            Sempre que possível, a caracterização institucional é baseada no campo `Type of archive` declarado
            no próprio APE. Isso preserva maior rigor do que classificações heurísticas construídas apenas a
            partir do nome da instituição.
            """
        )

    with tab_dashboard:
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
            webpage_ape=unavailable_df["website_available"].map(format_yes_no),
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
                for filename in list_ape_output_filenames()
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
                st.caption(
                    "Em um portal geral como o APE, esta leitura distingue evidência pública detectável, "
                    "evidência indireta, ausência de evidência pública e casos em que o site não pôde ser verificado."
                )
                if not visibility_counts.empty:
                    st.dataframe(visibility_counts, use_container_width=True, hide_index=True)
                else:
                    st.info("Ainda não há dados suficientes para analisar a visibilidade do audiovisual.")

                st.subheader("Tipo institucional declarado no APE")
                st.caption(
                    "Distribuição baseada no campo `Type of archive` informado pela própria fonte institucional."
                )
                if not archive_type_counts.empty:
                    st.dataframe(archive_type_counts, use_container_width=True, hide_index=True)
                else:
                    st.info("Ainda não há dados suficientes para resumir o tipo institucional declarado no APE.")

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
                st.caption("Este cruzamento exclui, por padrão, ruído de plataforma ou incorporação externa.")
                if not theme_platform_counts.empty:
                    st.dataframe(theme_platform_counts, use_container_width=True, hide_index=True)
                else:
                    st.info("Ainda não há dados suficientes para cruzar temas e plataformas.")

            with analysis_right:
                st.subheader("Temas por país")
                st.caption(
                    "Matriz com os principais países e os temas mais frequentes, excluindo ruído de plataforma."
                )
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
                st.caption("Matriz entre temas dos vídeos e o `Type of archive` declarado no APE.")
                st.caption(
                    "Leitura: as linhas representam tipos institucionais e as colunas representam temas; "
                    "valores mais altos indicam maior concentração relativa naquele cruzamento."
                )
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
                st.caption(
                    "Matriz entre a situação metodológica do audiovisual e o tipo institucional declarado no APE."
                )
                st.caption(
                    "Leitura: as linhas representam tipos institucionais e as colunas representam situações "
                    "metodológicas; isso ajuda a comparar onde o audiovisual aparece, se torna opaco ou não pôde ser verificado."
                )
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
            st.caption(
                "Dentro de `quebrado`, a aplicação distingue erro explícito e página suspeita."
            )

            st.subheader("Casos indisponíveis")
            st.dataframe(
                unavailable_df[
                    [
                        "institution",
                        "archive_type",
                        "availability_reason",
                        "integridade",
                        "status_tecnico",
                        "webpage_ape",
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
                        "webpage_ape": "webpage no APE",
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
                st.caption(
                    "Esta categoria inclui dois tipos de indisponibilidade: "
                    "`quebrado (erro explícito)`, quando o site retorna falha clara como 404/410/5xx, "
                    "e `quebrado (página suspeita)`, quando o site responde, mas cai em página genérica, "
                    "suspensa, placeholder ou erro disfarçado."
                )
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
                st.caption(
                    "Instável reúne casos em que não houve resposta confiável do site, mesmo sem erro HTTP explícito."
                )
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

    with tab_sites:
        st.subheader(f"Instituições com links de vídeo detectados ({with_video})")
        st.caption(
            "Esta aba reúne as instituições em cujos sites a coleta encontrou ao menos um link explícito de vídeo."
        )
        if detected_sites_df.empty:
            st.info("Nenhum link de vídeo foi detectado ainda nos sites das instituições do APE.")
        else:
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
                    if row["platforms_detectadas"]:
                        st.write(f"Plataformas detectadas: {row['platforms_detectadas']}")
                    if pd.notna(row.get("warning")) and str(row.get("warning")).strip():
                        st.warning(str(row["warning"]))
                    if pd.notna(row.get("ape_detail_url")) and str(row.get("ape_detail_url")).strip():
                        st.markdown(f"[Abrir ficha no APE]({row['ape_detail_url']})")
                    st.markdown(f"[Abrir site institucional]({row['final_url']})")

    with tab_videos:
        st.subheader("Catálogo curatorial de vídeos")
        if video_catalog_df.empty:
            st.info("Nenhum link de vídeo foi detectado ainda nos sites das instituições do APE.")
        else:
            st.markdown(
                "Este catálogo organiza o recorte curatorial de vídeos a partir de metadados básicos e de uma "
                "classificação temática baseada em título, assunto e descrição, excluindo por padrão o ruído "
                "de plataforma ou incorporação externa."
            )

            overview_cols = st.columns(4)
            overview_cols[0].metric("Vídeos no recorte curatorial", curatorial_video_total)
            overview_cols[1].metric("Links de vídeo detectados", len(video_catalog_df))
            overview_cols[2].metric("Temas identificados", len(theme_counts))
            overview_cols[3].metric("Plataformas", int(video_catalog_df["platform"].nunique()))

            st.markdown("#### Distribuição temática")
            if not theme_counts.empty:
                st.dataframe(theme_counts, use_container_width=True, hide_index=True)

            filter_cols = st.columns(2)
            video_platforms = sorted(video_catalog_df["platform"].dropna().unique().tolist())
            with filter_cols[0]:
                selected_platforms = st.multiselect(
                    "Plataformas",
                    options=video_platforms,
                    default=video_platforms,
                )
            available_continents = sorted(
                video_catalog_df["continent"].fillna("Não classificado").replace("", "Não classificado").unique().tolist()
            )
            with filter_cols[1]:
                selected_continents = st.multiselect(
                    "Continentes",
                    options=available_continents,
                    default=available_continents,
                )

            if selected_sidebar_theme == "Todos os temas":
                selected_themes = [
                    theme
                    for theme in video_catalog_df["video_theme"].dropna().unique().tolist()
                    if theme != NOISE_THEME_LABEL
                ]
            else:
                selected_themes = [selected_sidebar_theme]

            filtered_videos = video_catalog_df[
                video_catalog_df["platform"].isin(selected_platforms)
                & video_catalog_df["continent"].fillna("Não classificado").replace("", "Não classificado").isin(selected_continents)
                & video_catalog_df["video_theme"].isin(selected_themes)
            ].copy()

            st.caption(f"Tema selecionado na barra lateral: {selected_sidebar_theme}.")
            st.caption(f"{len(filtered_videos)} vídeos no recorte atual.")

            video_view_mode = st.radio(
                "Organização dos vídeos",
                options=["Por tema", "Tabela"],
                horizontal=True,
            )

            if video_view_mode == "Tabela":
                st.dataframe(
                    filtered_videos[
                        [
                            "institution",
                            "platform",
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
                )
            else:
                if filtered_videos.empty:
                    st.info("Nenhum vídeo corresponde ao tema e aos filtros selecionados.")
                else:
                    theme_order = filtered_videos["video_theme"].value_counts().index.tolist()
                    expand_selected_theme = selected_sidebar_theme != "Todos os temas"
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
                                st.markdown(f"[Abrir vídeo]({row['video_link']})")
                                st.code(row["video_link"], language=None)

            with st.expander("Ver distribuição temática", expanded=False):
                st.caption("A distribuição temática apresentada aqui exclui o ruído de plataforma da análise.")
                if not theme_counts.empty:
                    st.dataframe(theme_counts, use_container_width=True, hide_index=True)
                else:
                    st.info("Ainda não há temas classificados para os vídeos.")

    with tab_geo:
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

        continent_filter = st.multiselect(
            "Filtrar continentes",
            options=continent_counts["continent"].tolist(),
            default=continent_counts["continent"].tolist(),
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
        )

    with tab_data:
        st.subheader("Quadros analíticos do observatório")
        st.caption(
            "Esta aba reúne os principais quadros analíticos derivados da base do APE e permite "
            "baixá-los em CSV para uso em pesquisa, redação, revisão metodológica e documentação do corpus."
        )

        st.markdown("#### Conjuntos analíticos para download")
        download_col_1, download_col_2 = st.columns(2)
        with download_col_1:
            render_csv_download(
                "Baixar quadro institucional analítico",
                available_df,
                APE_OUTPUT_FILES["analytic_summary"],
                "Inclui disponibilidade, segmento institucional e situação metodológica do audiovisual por instituição.",
            )
            render_csv_download(
                "Baixar catálogo curatorial de vídeos",
                video_catalog_df,
                APE_OUTPUT_FILES["analytic_video_catalog"],
                "Inclui tema sugerido, data formatada e metadados básicos dos vídeos detectados.",
            )
            render_csv_download(
                "Baixar síntese temática",
                theme_counts,
                APE_OUTPUT_FILES["theme_summary"],
                "Síntese da classificação temática, excluindo ruído de plataforma.",
            )
        with download_col_2:
            render_csv_download(
                "Baixar síntese de visibilidade",
                visibility_counts,
                APE_OUTPUT_FILES["visibility_summary"],
                "Distribuição das situações metodológicas do audiovisual no corpus.",
            )
            render_csv_download(
                "Baixar quadro temas por país",
                theme_country_counts,
                APE_OUTPUT_FILES["theme_country"],
                "Tabela analítica dos temas por país no recorte curatorial.",
            )
            render_csv_download(
                "Baixar quadro temas por tipo de arquivo",
                theme_archive_type_counts,
                APE_OUTPUT_FILES["theme_archive_type"],
                "Tabela analítica dos temas por tipo institucional declarado no APE.",
            )

        st.markdown("#### Visualização dos quadros")
        analytic_view = st.radio(
            "Selecione o quadro analítico",
            options=[
                "Quadro institucional analítico",
                "Catálogo curatorial de vídeos",
                "Síntese de visibilidade",
                "Síntese temática",
                "Temas por país",
                "Temas por tipo de arquivo",
                "Visibilidade por tipo de arquivo",
            ],
            horizontal=True,
        )

        if analytic_view == "Quadro institucional analítico":
            st.dataframe(build_summary_display_df(available_df), use_container_width=True)
        elif analytic_view == "Catálogo curatorial de vídeos":
            st.dataframe(build_video_catalog_display_df(video_catalog_df), use_container_width=True)
        elif analytic_view == "Síntese de visibilidade":
            st.dataframe(visibility_counts, use_container_width=True, hide_index=True)
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
        else:
            if not visibility_archive_type_matrix.empty:
                st.dataframe(
                    style_matrix_display(prepare_matrix_display(visibility_archive_type_matrix)),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.dataframe(visibility_archive_type_counts, use_container_width=True, hide_index=True)

    with tab_base:
        st.subheader("Base consolidada do APE")
        st.caption(
            "Cada linha representa uma instituição listada no APE com conteúdo publicado, complementada "
            "pela verificação do site externo informado na ficha do portal."
        )
        st.caption(
            "Os filtros abaixo permitem construir recortes analíticos da base, sem perder o vínculo "
            "com a tipologia institucional, a integridade do site e a visibilidade pública do audiovisual."
        )

        base_source_df = available_df.copy()
        base_source_df["continente_display"] = (
            base_source_df["continent"].fillna("Não classificado").astype(str).str.strip().replace("", "Não classificado")
        )
        base_source_df["tipo_arquivo_display"] = (
            base_source_df["archive_type"].fillna("Não informado no APE").astype(str).str.strip().replace("", "Não informado no APE")
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
            )
        with filter_row_1[1]:
            visibility_filter = st.multiselect(
                "Situação metodológica do audiovisual",
                options=visibility_filter_options,
                default=visibility_filter_options,
            )
        with filter_row_1[2]:
            segment_filter = st.multiselect(
                "Segmento institucional",
                options=segment_filter_options,
                default=segment_filter_options,
            )
        with filter_row_1[3]:
            continent_filter = st.multiselect(
                "Continente",
                options=continent_filter_options,
                default=continent_filter_options,
            )

        filter_row_2 = st.columns([1.3, 1, 1])
        archive_type_filter_options = ["Todos"] + sorted(base_source_df["tipo_arquivo_display"].dropna().unique().tolist())
        with filter_row_2[0]:
            archive_type_filter = st.selectbox(
                "Tipo de arquivo",
                options=archive_type_filter_options,
            )
        with filter_row_2[1]:
            only_with_videos = st.checkbox("Somente com links de vídeo", value=False)
        with filter_row_2[2]:
            text_filter = st.text_input("Busca textual", placeholder="Instituição, país, domínio ou código")

        filtered = base_source_df[
            base_source_df["integrity_status"].isin(integrity_filter)
            & base_source_df["audiovisual_visibility"].isin(visibility_filter)
            & base_source_df["institution_segment"].isin(segment_filter)
            & base_source_df["continente_display"].isin(continent_filter)
        ].copy()

        if archive_type_filter != "Todos":
            filtered = filtered.loc[filtered["tipo_arquivo_display"] == archive_type_filter].copy()

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
        filtered_display_df = build_summary_display_df(filtered)

        filtered_total = len(filtered)
        filtered_website_total = int(filtered["website_available"].fillna(False).astype(bool).sum()) if not filtered.empty else 0
        filtered_visible_total = int(
            (filtered["audiovisual_visibility"] == "Evidência pública detectável de audiovisual").sum()
        ) if not filtered.empty else 0
        filtered_unavailable_total = int((filtered["availability_group"] == "Indisponível").sum()) if not filtered.empty else 0

        base_metric_cols = st.columns(4)
        base_metric_cols[0].metric("Instituições no recorte", filtered_total)
        base_metric_cols[1].metric("Com webpage externa", filtered_website_total)
        base_metric_cols[2].metric("Com evidência pública detectável", filtered_visible_total)
        base_metric_cols[3].metric("Indisponíveis no recorte", filtered_unavailable_total)

        render_csv_download(
            "Baixar recorte atual da base consolidada",
            filtered_display_df,
            "ape_base_consolidada_filtrada.csv",
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
                "segmento institucional",
                "links de vídeo",
                "sinais embutidos",
                "páginas internas",
                "webpage no APE",
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

else:
    st.subheader(selected_summary["institution"])
    selected_internal = pd.DataFrame()
    if not internal_df.empty:
        selected_internal = internal_df.loc[internal_df["slug"].astype(str) == str(selected_slug)].copy()

    institution_video_count = int(selected_summary["video_links_found_total"])
    institution_embedded_count = int(selected_summary["embedded_video_signals_total"])
    institution_internal_count = int(selected_summary["candidate_internal_pages"])
    institution_visibility = classify_audiovisual_visibility(selected_summary)
    institution_category = classify_availability_group(selected_summary["integrity_status"])
    institution_subcategory = classify_availability_reason(selected_summary)

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
    geo_cols[3].metric("Webpage no APE", format_yes_no(selected_summary.get("website_available")))

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
        st.warning("A ficha no APE não informa uma webpage externa para esta instituição.")
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
                    {"eixo": "Conteúdo publicado no APE", "valor": format_yes_no(selected_summary.get("content_available_in_ape"))},
                    {"eixo": "Webpage informada no APE", "valor": format_yes_no(selected_summary.get("website_available"))},
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
                    {
                        "recurso": "Ficha da instituição no APE",
                        "endereço": normalize_optional_text(selected_summary.get("ape_detail_url")) or "-",
                    },
                    {
                        "recurso": "Site externo informado",
                        "endereço": normalize_optional_text(selected_summary.get("partner_site")) or "-",
                    },
                    {
                        "recurso": "URL final verificada",
                        "endereço": normalize_optional_text(selected_summary.get("final_url")) or "-",
                    },
                    {
                        "recurso": "Domínio",
                        "endereço": normalize_optional_text(selected_summary.get("partner_domain")) or "-",
                    },
                    {
                        "recurso": "Código do repositório",
                        "endereço": normalize_optional_text(selected_summary.get("repository_code")) or "-",
                    },
                ]
            )
            st.dataframe(source_links, use_container_width=True, hide_index=True)

            if pd.notna(selected_summary.get("ape_detail_url")) and str(selected_summary.get("ape_detail_url")).strip():
                st.link_button("Abrir ficha da instituição no APE", selected_summary["ape_detail_url"], use_container_width=True)
            if pd.notna(selected_summary.get("final_url")) and str(selected_summary.get("final_url")).strip():
                st.link_button("Abrir site institucional verificado", selected_summary["final_url"], use_container_width=True)

    with institution_tab_videos:
        st.subheader("Vídeos detectados na instituição")
        st.caption(
            "Esta seção reúne os links de vídeo detectados automaticamente pela coleta para a instituição selecionada."
        )
        if selected_links.empty:
            st.info("Nenhum link de vídeo foi detectado automaticamente para esta instituição.")
        else:
            selected_links = selected_links.copy()
            selected_links["tema_sugerido"] = selected_links.apply(infer_video_theme, axis=1)
            selected_links["data_publicacao"] = selected_links["video_published_at"].apply(format_video_date)

            video_overview_cols = st.columns(3)
            video_overview_cols[0].metric("Links detectados", len(selected_links))
            video_overview_cols[1].metric("Plataformas", int(selected_links["platform"].nunique()))
            video_overview_cols[2].metric(
                "Temas sugeridos",
                int(selected_links["tema_sugerido"].replace(NOISE_THEME_LABEL, pd.NA).dropna().nunique()),
            )

            video_table_df = selected_links[
                [
                    "platform",
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
                    ["platform", "tema_sugerido", "titulo_display", "data_publicacao", "video_link"]
                ].rename(
                    columns={
                        "platform": "plataforma",
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
                expander_label = f"{index + 1}. {title}"
                with st.expander(expander_label, expanded=False):
                    meta_cols = st.columns(3)
                    meta_cols[0].caption(f"Plataforma: {normalize_text(row['platform'])}")
                    meta_cols[1].caption(f"Tema sugerido: {theme_label}")
                    meta_cols[2].caption(f"Data de publicação: {published_at or '-'}")
                    description = normalize_optional_text(row.get("video_description"))
                    if description:
                        st.write(description)
                    st.link_button("Abrir vídeo", row["video_link"], key=f"video-link-{selected_slug}-{index}", use_container_width=True)
                    if "youtube.com" in row["video_link"] or "youtu.be" in row["video_link"]:
                        st.video(row["video_link"])
                    else:
                        vimeo_embed = get_vimeo_embed_url(row["video_link"])
                        if vimeo_embed:
                            components.iframe(vimeo_embed, height=360)
                    st.code(row["video_link"], language=None)

    with institution_tab_internal:
        st.subheader("Páginas internas analisadas")
        st.caption(
            "Esta seção apresenta páginas internas visitadas automaticamente a partir do site institucional, "
            "úteis para identificar potencial audiovisual não imediatamente visível na página principal."
        )
        if selected_internal.empty:
            st.info("Nenhuma página interna foi analisada para esta instituição.")
        else:
            selected_internal = selected_internal.copy()
            selected_internal["status_tecnico"] = selected_internal["status"].map(format_technical_status)
            selected_internal["webpage_ape"] = selected_internal["website_available"].map(format_yes_no)

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
