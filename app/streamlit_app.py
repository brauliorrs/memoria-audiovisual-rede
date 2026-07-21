import sys
import json
from importlib.util import find_spec
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit.delta_generator import DeltaGenerator


BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual import analysis as analysis_utils
from memoria_audiovisual.adlibitum_protocol import ADLIBITUM_PROTOCOL_FILENAME
from memoria_audiovisual.arsenal_protocol import ARSENAL_PROTOCOL_FILENAME
from memoria_audiovisual.archivegrid_protocol import ARCHIVEGRID_PROTOCOL_FILENAME
from memoria_audiovisual.atresmedia_protocol import ATRESMEDIA_PROTOCOL_FILENAME
from memoria_audiovisual.bnfa_protocol import BNFA_PROTOCOL_FILENAME
from memoria_audiovisual.cineteca_bologna_protocol import CINETECA_BOLOGNA_PROTOCOL_FILENAME
from memoria_audiovisual.cineteca_italiana_protocol import CINETECA_ITALIANA_PROTOCOL_FILENAME
from memoria_audiovisual.cinematheque_corse_protocol import CINEMATHEQUE_CORSE_PROTOCOL_FILENAME
from memoria_audiovisual.cinematheque_luxembourg_protocol import CINEMATHEQUE_LUXEMBOURG_PROTOCOL_FILENAME
from memoria_audiovisual.cnc_aff_protocol import CNCAFF_PROTOCOL_FILENAME
from memoria_audiovisual.filmmuseum_munchen_protocol import FILMMUSEUM_MUNCHEN_PROTOCOL_FILENAME
from memoria_audiovisual.filmoteca_vaticana_protocol import FILMOTECA_VATICANA_PROTOCOL_FILENAME
from memoria_audiovisual.iberarchivos_protocol import IBERARCHIVOS_PROTOCOL_FILENAME
from memoria_audiovisual.prise2_protocol import PRISE2_PROTOCOL_FILENAME
from memoria_audiovisual.public_access_index import (
    PUBLIC_ACCESS_INDEX_BY_CORPUS_FILENAME,
    PUBLIC_ACCESS_INDEX_FILENAME,
    PUBLIC_ACCESS_RESTRICTED_UNITS_FILENAME,
)
from memoria_audiovisual.restricted_access_audit import (
    RESTRICTED_ACCESS_AUDIT_FILENAME,
    RESTRICTED_ACCESS_SUMMARY_FILENAME,
)
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
from memoria_audiovisual.european_aggregators import (
    EUROPEAN_AGGREGATOR_ACCESS_ROUTES_FILENAME,
    EUROPEAN_AGGREGATOR_EVALUATION_FILENAME,
    EUROPEAN_AGGREGATOR_PROBES_FILENAME,
    EUROPEAN_AGGREGATOR_PROTOCOLS_FILENAME,
    EUROPEAN_AGGREGATOR_SUMMARY_FILENAME,
)
from memoria_audiovisual.europe_closure import (
    EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
    EUROPE_CLOSURE_GAP_AUDIT_FILENAME,
    EUROPE_CLOSURE_MATRIX_FILENAME,
    EUROPE_CLOSURE_QUEUE_FILENAME,
    EUROPE_CLOSURE_SUMMARY_FILENAME,
)
from memoria_audiovisual.europe_research import (
    EUROPE_RESEARCH_QUEUE_FILENAME,
    EUROPE_RESEARCH_REGISTRY_FILENAME,
    EUROPE_RESEARCH_SUMMARY_FILENAME,
    build_europe_research_queue,
    build_europe_research_registry,
    build_europe_research_summary,
)
from memoria_audiovisual.european_protocols import (
    ARCHIVESHUB_PROTOCOL_FILENAME,
    FRANCEARCHIVES_PROTOCOL_FILENAME,
)
from memoria_audiovisual.i18n import (
    DEFAULT_LANGUAGE,
    LANGUAGE_OPTIONS,
    language_code_from_label,
    t,
    translate_ui_text,
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
RESEARCH_RESULT_PREVIEW_LIMIT = 500

st.set_page_config(page_title="Memória Audiovisual em Rede", layout="wide")

APP_LANGUAGE = DEFAULT_LANGUAGE


def tr(key, **kwargs):
    return t(key, APP_LANGUAGE, **kwargs)


def localize_ui(value):
    return translate_ui_text(value, APP_LANGUAGE)


def localize_format_func(format_func=None):
    def formatter(value):
        rendered = format_func(value) if format_func else str(value)
        return localize_ui(rendered)

    return formatter


def localize_dataframe_columns(data):
    if APP_LANGUAGE == DEFAULT_LANGUAGE or not isinstance(data, pd.DataFrame):
        return data
    localized = data.copy()
    localized.columns = [localize_ui(column) if isinstance(column, str) else column for column in localized.columns]
    return localized


def localize_dataframe_arguments(args, kwargs):
    args = list(args)
    kwargs = dict(kwargs)
    if args:
        args[0] = localize_dataframe_columns(args[0])
    elif "data" in kwargs:
        kwargs["data"] = localize_dataframe_columns(kwargs["data"])
    return args, kwargs


def install_streamlit_i18n(language):
    if not hasattr(st, "_memoria_i18n_originals"):
        st._memoria_i18n_originals = {}
    st._memoria_i18n_language = language

    def original_method(name):
        originals = st._memoria_i18n_originals
        if name not in originals:
            originals[name] = getattr(st, name)
        return originals[name]

    def localize_text_call(name):
        original = original_method(name)

        def wrapped(*args, **kwargs):
            args = list(args)
            if args and isinstance(args[0], str):
                args[0] = localize_ui(args[0])
            for key in ("label", "help", "placeholder"):
                if isinstance(kwargs.get(key), str):
                    kwargs[key] = localize_ui(kwargs[key])
            return original(*args, **kwargs)

        setattr(st, name, wrapped)

    for method_name in [
        "title",
        "header",
        "subheader",
        "markdown",
        "caption",
        "info",
        "warning",
        "error",
        "success",
        "write",
        "download_button",
        "link_button",
    ]:
        if hasattr(st, method_name):
            localize_text_call(method_name)

    def original_delta_method(name):
        originals = st._memoria_i18n_originals
        key = f"DeltaGenerator.{name}"
        if key not in originals:
            originals[key] = getattr(DeltaGenerator, name)
        return originals[key]

    def localize_delta_text_call(name):
        original = original_delta_method(name)

        def wrapped(self, *args, **kwargs):
            args = list(args)
            if args and isinstance(args[0], str):
                args[0] = localize_ui(args[0])
            for key in ("label", "help", "placeholder"):
                if isinstance(kwargs.get(key), str):
                    kwargs[key] = localize_ui(kwargs[key])
            return original(self, *args, **kwargs)

        setattr(DeltaGenerator, name, wrapped)

    for method_name in [
        "title",
        "header",
        "subheader",
        "markdown",
        "caption",
        "info",
        "warning",
        "error",
        "success",
        "write",
        "download_button",
        "link_button",
    ]:
        if hasattr(DeltaGenerator, method_name):
            localize_delta_text_call(method_name)

    original_metric = original_method("metric")

    def localized_metric(label, value, *args, **kwargs):
        localized_value = localize_ui(value) if isinstance(value, str) else value
        return original_metric(localize_ui(label), localized_value, *args, **kwargs)

    st.metric = localized_metric
    original_delta_metric = original_delta_method("metric")

    def localized_delta_metric(self, label, value, *args, **kwargs):
        localized_value = localize_ui(value) if isinstance(value, str) else value
        return original_delta_metric(self, localize_ui(label), localized_value, *args, **kwargs)

    DeltaGenerator.metric = localized_delta_metric

    original_dataframe = original_method("dataframe")

    def localized_dataframe(*args, **kwargs):
        args, kwargs = localize_dataframe_arguments(args, kwargs)
        return original_dataframe(*args, **kwargs)

    st.dataframe = localized_dataframe
    original_delta_dataframe = original_delta_method("dataframe")

    def localized_delta_dataframe(self, *args, **kwargs):
        args, kwargs = localize_dataframe_arguments(args, kwargs)
        return original_delta_dataframe(self, *args, **kwargs)

    DeltaGenerator.dataframe = localized_delta_dataframe

    original_tabs = original_method("tabs")

    def localized_tabs(tabs, *args, **kwargs):
        return original_tabs([localize_ui(tab) if isinstance(tab, str) else tab for tab in tabs], *args, **kwargs)

    st.tabs = localized_tabs

    original_expander = original_method("expander")

    def localized_expander(label, *args, **kwargs):
        return original_expander(localize_ui(label), *args, **kwargs)

    st.expander = localized_expander
    original_delta_expander = original_delta_method("expander")

    def localized_delta_expander(self, label, *args, **kwargs):
        return original_delta_expander(self, localize_ui(label), *args, **kwargs)

    DeltaGenerator.expander = localized_delta_expander

    for control_name in ["selectbox", "radio", "multiselect"]:
        original_control = original_method(control_name)
        original_delta_control = original_delta_method(control_name)

        def localized_control(label, *args, _original=original_control, **kwargs):
            kwargs["format_func"] = localize_format_func(kwargs.get("format_func"))
            return _original(localize_ui(label), *args, **kwargs)

        def localized_delta_control(self, label, *args, _original=original_delta_control, **kwargs):
            kwargs["format_func"] = localize_format_func(kwargs.get("format_func"))
            return _original(self, localize_ui(label), *args, **kwargs)

        setattr(st, control_name, localized_control)
        setattr(DeltaGenerator, control_name, localized_delta_control)

    original_text_input = original_method("text_input")

    def localized_text_input(label, *args, **kwargs):
        if isinstance(kwargs.get("placeholder"), str):
            kwargs["placeholder"] = localize_ui(kwargs["placeholder"])
        return original_text_input(localize_ui(label), *args, **kwargs)

    st.text_input = localized_text_input
    original_delta_text_input = original_delta_method("text_input")

    def localized_delta_text_input(self, label, *args, **kwargs):
        if isinstance(kwargs.get("placeholder"), str):
            kwargs["placeholder"] = localize_ui(kwargs["placeholder"])
        return original_delta_text_input(self, localize_ui(label), *args, **kwargs)

    DeltaGenerator.text_input = localized_delta_text_input

    original_checkbox = original_method("checkbox")

    def localized_checkbox(label, *args, **kwargs):
        return original_checkbox(localize_ui(label), *args, **kwargs)

    st.checkbox = localized_checkbox
    original_delta_checkbox = original_delta_method("checkbox")

    def localized_delta_checkbox(self, label, *args, **kwargs):
        return original_delta_checkbox(self, localize_ui(label), *args, **kwargs)

    DeltaGenerator.checkbox = localized_delta_checkbox


def render_language_selector():
    labels = list(LANGUAGE_OPTIONS.values())
    selected_label = st.sidebar.selectbox(
        "Idioma / Language / Idioma",
        options=labels,
        index=labels.index(LANGUAGE_OPTIONS.get(APP_LANGUAGE, LANGUAGE_OPTIONS[DEFAULT_LANGUAGE])),
        key="interface_language",
    )
    return language_code_from_label(selected_label)


APP_LANGUAGE = render_language_selector()
install_streamlit_i18n(APP_LANGUAGE)
st.sidebar.caption(tr("language_note"))
st.sidebar.caption(tr("raw_data_note"))


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


def format_integer_pt(value):
    try:
        return f"{int(value):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "-"


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


def select_existing_columns(dataframe, columns):
    if dataframe is None or dataframe.empty:
        return pd.DataFrame()
    return dataframe[[column for column in columns if column in dataframe.columns]].copy()


def load_protocolled_excluded_units():
    excluded_df = load_csv(EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME)
    if excluded_df is not None and not excluded_df.empty:
        return excluded_df.sort_values("unit_label").to_dict("records")

    matrix_df = load_csv(EUROPE_CLOSURE_MATRIX_FILENAME)
    if matrix_df is None or matrix_df.empty:
        return []

    candidates_df = matrix_df.loc[
        (matrix_df.get("unit_type", pd.Series(dtype="object")) != "corpus_ativo")
        & (
            matrix_df.get("incorporation_decision", pd.Series(dtype="object"))
            == "nao_incorporar_como_corpus_ativo_ate_haver_rota_estavel"
        )
    ].copy()
    if candidates_df.empty:
        return []

    candidates_df["public_status"] = "Identificada, mas não incluída na base ativa do observatório"
    candidates_df["methodological_decision"] = "não incorporar à base ativa no MVP"
    candidates_df["negative_reason"] = "Ausência de rota de coleta estável no protocolo atual."
    candidates_df["access_category"] = "rota_publica_nao_estavel_ou_nao_coletavel"
    return candidates_df.sort_values("unit_label").to_dict("records")


def load_unit_protocol_df(unit_code):
    protocol_files = {
        "inedits-ad-libitum": ADLIBITUM_PROTOCOL_FILENAME,
        "inedits-prise-2": PRISE2_PROTOCOL_FILENAME,
        "fiaf-arsenal-filminstitut": ARSENAL_PROTOCOL_FILENAME,
        "fiaf-bulgarian-national-film-archive": BNFA_PROTOCOL_FILENAME,
        "fiaf-cineteca-bologna": CINETECA_BOLOGNA_PROTOCOL_FILENAME,
        "fiaf-cineteca-italiana": CINETECA_ITALIANA_PROTOCOL_FILENAME,
        "fiaf-cinematheque-luxembourg": CINEMATHEQUE_LUXEMBOURG_PROTOCOL_FILENAME,
        "fiaf-cnc-aff": CNCAFF_PROTOCOL_FILENAME,
        "fiaf-filmmuseum-munchen": FILMMUSEUM_MUNCHEN_PROTOCOL_FILENAME,
        "fiaf-filmoteca-vaticana": FILMOTECA_VATICANA_PROTOCOL_FILENAME,
        "fiat-atresmedia": ATRESMEDIA_PROTOCOL_FILENAME,
        "inedits-cinematheque-corse": CINEMATHEQUE_CORSE_PROTOCOL_FILENAME,
        "archivegrid": ARCHIVEGRID_PROTOCOL_FILENAME,
        "archives-hub": ARCHIVESHUB_PROTOCOL_FILENAME,
        "francearchives": FRANCEARCHIVES_PROTOCOL_FILENAME,
        "iberarchivos": IBERARCHIVOS_PROTOCOL_FILENAME,
    }
    filename = protocol_files.get(unit_code)
    if not filename:
        return pd.DataFrame()
    protocol_df = load_csv(filename)
    if protocol_df is None or protocol_df.empty:
        return pd.DataFrame()
    if "code" in protocol_df.columns:
        protocol_df = protocol_df.loc[protocol_df["code"].astype(str) == unit_code].copy()
    return protocol_df


def render_protocolled_excluded_unit_tab(unit_record):
    unit_code = normalize_optional_text(unit_record.get("unit_code"))
    unit_label = normalize_optional_text(unit_record.get("unit_label")) or unit_code
    blocks_expansion = str(unit_record.get("blocks_expansion", "")).lower() == "true"

    st.header(unit_label)
    st.info("Arquivo identificado, mas não incluído na base ativa do observatório.")
    st.caption(
        "Esta aba existe justamente para não apagar a tentativa. A unidade aparece no observatório, "
        "mas fica separada das unidades ativas até que a rota de coleta seja estável, reprodutível e comparável."
    )

    access_category = normalize_optional_text(unit_record.get("access_category")) or "-"
    metric_cols = st.columns(5)
    metric_cols[0].metric("Situação", "fora da base ativa")
    metric_cols[1].metric("Escopo", normalize_optional_text(unit_record.get("territorial_scope")) or "-")
    metric_cols[2].metric("Categoria de acesso", access_category)
    metric_cols[3].metric("Bloqueia expansão?", "Sim" if blocks_expansion else "Não")
    metric_cols[4].metric("Regra", normalize_optional_text(unit_record.get("rule_version")) or "-")

    decision_df = pd.DataFrame(
        [
            {
                "campo": "categoria de acesso",
                "informação": access_category,
            },
            {
                "campo": "status público",
                "informação": normalize_optional_text(unit_record.get("public_status")),
            },
            {
                "campo": "decisão metodológica",
                "informação": normalize_optional_text(unit_record.get("methodological_decision")),
            },
            {
                "campo": "motivo da não inclusão",
                "informação": normalize_optional_text(unit_record.get("negative_reason")),
            },
            {
                "campo": "rota de coleta tentada",
                "informação": normalize_optional_text(unit_record.get("collection_route_attempted")),
            },
            {
                "campo": "tentativas registradas",
                "informação": normalize_optional_text(unit_record.get("attempt_summary")),
            },
            {
                "campo": "explicação metodológica",
                "informação": normalize_optional_text(unit_record.get("methodological_explanation")),
            },
            {
                "campo": "próximo passo",
                "informação": normalize_optional_text(unit_record.get("next_step")),
            },
        ]
    )
    st.markdown("### Decisão e negativa metodológica")
    st.dataframe(decision_df, use_container_width=True, hide_index=True)

    access_routes_df = load_csv(EUROPEAN_AGGREGATOR_ACCESS_ROUTES_FILENAME)
    if access_routes_df is not None and not access_routes_df.empty and "code" in access_routes_df.columns:
        access_routes_df = access_routes_df.loc[access_routes_df["code"].astype(str) == unit_code].copy()
    if access_routes_df is not None and not access_routes_df.empty:
        st.markdown("### Rotas candidatas avaliadas")
        routes_display_df = select_existing_columns(
            access_routes_df.rename(
                columns={
                    "route_type": "tipo de rota",
                    "route_url": "URL da rota",
                    "http_status": "resposta do site",
                    "access_status": "status de acesso",
                    "route_viability": "viabilidade",
                    "audiovisual_use": "uso audiovisual possível",
                    "methodological_note": "nota metodológica",
                    "source_reference_url": "referência",
                }
            ),
            [
                "tipo de rota",
                "resposta do site",
                "status de acesso",
                "viabilidade",
                "uso audiovisual possível",
                "nota metodológica",
                "URL da rota",
                "referência",
            ],
        )
        st.dataframe(routes_display_df, use_container_width=True, hide_index=True)

    protocol_df = load_unit_protocol_df(unit_code)
    if protocol_df is not None and not protocol_df.empty:
        st.markdown("### Tentativas de verificação")
        protocol_display_df = select_existing_columns(
            protocol_df.rename(
                columns={
                    "probe_label": "sondagem",
                    "method": "método",
                    "http_status": "resposta do site",
                    "content_type": "tipo de conteúdo",
                    "access_status": "status de acesso",
                    "evidence_signal": "sinal observado",
                    "observed_value": "valor observado",
                    "protocol_conclusion": "conclusão",
                    "next_step": "próximo passo",
                    "methodological_note": "nota metodológica",
                    "url": "URL",
                }
            ),
            [
                "sondagem",
                "método",
                "resposta do site",
                "tipo de conteúdo",
                "status de acesso",
                "sinal observado",
                "valor observado",
                "conclusão",
                "próximo passo",
                "nota metodológica",
                "URL",
            ],
        )
        st.dataframe(protocol_display_df, use_container_width=True, hide_index=True)

    st.warning(
        "Leitura correta: a não inclusão não prova inexistência de audiovisual. Ela prova apenas que, "
        "nesta rodada, o observatório não encontrou uma rota suficientemente estável para coleta com rigor."
    )


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
            "slug": "identificador",
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
            "status_tecnico_display": "situação da verificação",
            "http_code": "resposta do site",
            "video_links_found_total": "links de vídeo",
            "embedded_video_signals_total": "sinais embutidos",
            "candidate_internal_pages": "páginas analisadas",
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
            "collection_completeness": corpus_def["collection_completeness"],
            "selection_limit": corpus_def["selection_limit"],
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
        "collection_completeness": corpus_def["collection_completeness"],
        "selection_limit": corpus_def["selection_limit"],
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
            "corpus": "unidade documental",
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
            "status_técnico": "situação da verificação",
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
            "corpus": "unidade documental",
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


@st.cache_data(show_spinner=False)
def build_research_video_catalog_frame():
    frames = []
    search_columns = {
        "institution",
        "slug",
        "country",
        "continent",
        "platform",
        "video_link",
        "video_title_display",
        "video_date_display",
        "video_theme",
        "access_surface",
        "video_subject",
    }
    for corpus_def in CORPORA.values():
        output_files = corpus_def["output_files"]
        catalog_path = OUTPUT_DIR / output_files["analytic_video_catalog"]
        if not catalog_path.exists():
            continue
        catalog_df = pd.read_csv(
            catalog_path,
            usecols=lambda column: column in search_columns,
            dtype=str,
            keep_default_na=False,
        )
        catalog_df = analysis_utils.filter_curatorial_video_catalog(catalog_df)
        if catalog_df.empty:
            continue

        summary_path = OUTPUT_DIR / output_files["analytic_summary"]
        if summary_path.exists():
            regime_df = pd.read_csv(
                summary_path,
                usecols=lambda column: column in {"slug", "institution", "access_regime"},
                dtype=str,
                keep_default_na=False,
            )
            join_key = "slug" if "slug" in catalog_df.columns and "slug" in regime_df.columns else "institution"
            if join_key in catalog_df.columns and join_key in regime_df.columns and "access_regime" in regime_df.columns:
                catalog_df = catalog_df.merge(
                    regime_df[[join_key, "access_regime"]].drop_duplicates(join_key),
                    on=join_key,
                    how="left",
                )

        category_def = CORPUS_CATEGORIES[corpus_def["category_code"]]
        catalog_df["corpus"] = corpus_def["short_label"]
        catalog_df["unidade"] = corpus_def["label"]
        catalog_df["categoria_analitica"] = category_def["label"]
        frames.append(catalog_df)

    if not frames:
        return pd.DataFrame()
    catalog_df = pd.concat(frames, ignore_index=True)
    for column in [
        "categoria_analitica",
        "corpus",
        "unidade",
        "institution",
        "country",
        "continent",
        "platform",
        "access_surface",
        "access_regime",
        "video_theme",
    ]:
        if column not in catalog_df.columns:
            catalog_df[column] = ""
        catalog_df[column] = catalog_df[column].fillna("").astype(str)
    catalog_df["continent"] = catalog_df["continent"].replace("", "Não classificado")
    return catalog_df


def _select_filter_options(dataframe, column, all_label):
    if dataframe.empty or column not in dataframe.columns:
        return [all_label]
    options = sorted(value for value in dataframe[column].dropna().astype(str).unique().tolist() if value.strip())
    return [all_label] + options


def _apply_single_choice_filter(dataframe, column, selected, all_label):
    if selected == all_label or column not in dataframe.columns:
        return dataframe
    return dataframe.loc[dataframe[column].astype(str) == selected].copy()


def filter_research_catalog(
    catalog_df,
    *,
    search_term,
    selected_category,
    selected_corpus,
    selected_theme,
    selected_country,
    selected_continent,
    selected_platform,
    selected_access_surface,
    selected_access_regime,
    public_video_only,
):
    filtered_df = catalog_df.copy()
    filters = [
        ("categoria_analitica", selected_category, "Todas as categorias"),
        ("corpus", selected_corpus, "Todas as unidades"),
        ("video_theme", selected_theme, "Todos os temas"),
        ("country", selected_country, "Todos os países"),
        ("continent", selected_continent, "Todos os continentes"),
        ("platform", selected_platform, "Todas as plataformas"),
        ("access_surface", selected_access_surface, "Todas as modalidades"),
        ("access_regime", selected_access_regime, "Todos os regimes"),
    ]
    for column, selected, all_label in filters:
        filtered_df = _apply_single_choice_filter(filtered_df, column, selected, all_label)

    if public_video_only and "video_link" in filtered_df.columns:
        filtered_df = filtered_df.loc[filtered_df["video_link"].fillna("").astype(str).str.strip() != ""].copy()

    search_term = search_term.strip()
    if search_term:
        search_columns = [
            "video_title_display",
            "video_subject",
            "video_description",
            "institution",
            "unidade",
            "corpus",
            "country",
            "continent",
            "platform",
            "video_theme",
            "video_link",
        ]
        available_columns = [column for column in search_columns if column in filtered_df.columns]
        search_lower = search_term.lower()
        filtered_df = filtered_df.loc[
            filtered_df[available_columns]
            .fillna("")
            .astype(str)
            .apply(lambda column: column.str.lower().str.contains(search_lower, na=False, regex=False))
            .any(axis=1)
        ].copy()

    return filtered_df


def build_research_video_display_df(dataframe):
    if dataframe is None or dataframe.empty:
        return pd.DataFrame()
    preferred_columns = [
        "categoria_analitica",
        "corpus",
        "unidade",
        "institution",
        "country",
        "continent",
        "video_theme",
        "video_title_display",
        "video_date_display",
        "platform",
        "access_surface",
        "access_regime",
        "video_subject",
        "video_description",
        "video_link",
    ]
    available_columns = [column for column in preferred_columns if column in dataframe.columns]
    return dataframe[available_columns].rename(
        columns={
            "categoria_analitica": "categoria analítica",
            "corpus": "unidade documental",
            "unidade": "unidade",
            "institution": "instituição",
            "country": "país",
            "continent": "continente",
            "video_theme": "tema",
            "video_title_display": "título do vídeo",
            "video_date_display": "data do vídeo",
            "platform": "plataforma",
            "access_surface": "modalidade de acesso",
            "access_regime": "regime de acesso audiovisual",
            "video_subject": "assunto do vídeo",
            "video_description": "descrição do vídeo",
            "video_link": "link do vídeo",
        }
    )


def render_research_tab(initial_search_term="", show_search_input=True):
    st.markdown("## Pesquisa no catálogo audiovisual")
    st.caption(
        "Ferramenta transversal para localizar vídeos, instituições, temas, países, plataformas e regimes "
        "de acesso no catálogo curatorial consolidado do observatório."
    )
    st.info(
        "Esta ferramenta permite cruzar o conjunto do organismo sem apagar a separação metodológica: "
        "cada resultado preserva categoria analítica, unidade documental e instituição de origem."
    )

    catalog_df = build_research_video_catalog_frame()
    if catalog_df.empty:
        st.info("Ainda não há vídeos curatoriais disponíveis para pesquisa transversal.")
        return

    st.markdown("### Escopo indexado")
    metric_cols = st.columns(5)
    metric_cols[0].metric("Vídeos indexados", len(catalog_df))
    metric_cols[1].metric("Unidades documentais", int(catalog_df["corpus"].nunique()))
    metric_cols[2].metric("Instituições", int(catalog_df["institution"].nunique()))
    metric_cols[3].metric("Países", int(catalog_df["country"].nunique()))
    metric_cols[4].metric("Temas", int(catalog_df["video_theme"].nunique()))

    st.markdown("### Filtros de pesquisa")
    search_term = initial_search_term
    if show_search_input:
        search_term = st.text_input(
            "Busca textual",
            value=initial_search_term,
            placeholder="Título, assunto, descrição, instituição ou país",
            key="global-research-search",
        )
    filter_cols = st.columns(4)
    with filter_cols[0]:
        selected_category = st.selectbox(
            "Categoria analítica",
            options=_select_filter_options(catalog_df, "categoria_analitica", "Todas as categorias"),
            key="global-research-category",
        )
        selected_country = st.selectbox(
            "País",
            options=_select_filter_options(catalog_df, "country", "Todos os países"),
            key="global-research-country",
        )
    with filter_cols[1]:
        selected_corpus = st.selectbox(
            "Unidade documental",
            options=_select_filter_options(catalog_df, "corpus", "Todas as unidades"),
            key="global-research-corpus",
        )
        selected_continent = st.selectbox(
            "Continente",
            options=_select_filter_options(catalog_df, "continent", "Todos os continentes"),
            key="global-research-continent",
        )
    with filter_cols[2]:
        selected_theme = st.selectbox(
            "Tema",
            options=_select_filter_options(catalog_df, "video_theme", "Todos os temas"),
            key="global-research-theme",
        )
        selected_platform = st.selectbox(
            "Plataforma",
            options=_select_filter_options(catalog_df, "platform", "Todas as plataformas"),
            key="global-research-platform",
        )
    with filter_cols[3]:
        selected_access_surface = st.selectbox(
            "Modalidade de acesso",
            options=_select_filter_options(catalog_df, "access_surface", "Todas as modalidades"),
            key="global-research-access-surface",
        )
        selected_access_regime = st.selectbox(
            "Regime de acesso audiovisual",
            options=_select_filter_options(catalog_df, "access_regime", "Todos os regimes"),
            key="global-research-access-regime",
        )

    public_video_only = st.checkbox(
        "Somente registros com link público de vídeo",
        value=True,
        key="global-research-public-video-only",
    )

    filtered_df = filter_research_catalog(
        catalog_df,
        search_term=search_term,
        selected_category=selected_category,
        selected_corpus=selected_corpus,
        selected_theme=selected_theme,
        selected_country=selected_country,
        selected_continent=selected_continent,
        selected_platform=selected_platform,
        selected_access_surface=selected_access_surface,
        selected_access_regime=selected_access_regime,
        public_video_only=public_video_only,
    )

    st.markdown("### Resultados da consulta")
    st.caption(f"{len(filtered_df)} vídeos no recorte atual.")
    result_metric_cols = st.columns(5)
    result_metric_cols[0].metric("Resultados encontrados", len(filtered_df))
    result_metric_cols[1].metric("Unidades no recorte", int(filtered_df["corpus"].nunique()) if not filtered_df.empty else 0)
    result_metric_cols[2].metric(
        "Instituições no recorte",
        int(filtered_df["institution"].nunique()) if not filtered_df.empty else 0,
    )
    result_metric_cols[3].metric("Países no recorte", int(filtered_df["country"].nunique()) if not filtered_df.empty else 0)
    result_metric_cols[4].metric("Temas no recorte", int(filtered_df["video_theme"].nunique()) if not filtered_df.empty else 0)

    result_mode = st.radio(
        "Organização dos resultados",
        options=["Tabela", "Por tema", "Por unidade documental"],
        horizontal=True,
        key="global-research-result-mode",
    )

    if filtered_df.empty:
        st.info("Nenhum vídeo corresponde aos filtros selecionados.")
        return

    preview_df = filtered_df.head(RESEARCH_RESULT_PREVIEW_LIMIT)
    if len(filtered_df) > len(preview_df):
        st.caption(
            tr(
                "research_preview_caption",
                preview_total=len(preview_df),
                filtered_total=len(filtered_df),
            )
        )

    if result_mode == "Tabela":
        st.dataframe(
            build_research_video_display_df(preview_df),
            use_container_width=True,
            hide_index=True,
        )
    else:
        group_column = "video_theme" if result_mode == "Por tema" else "corpus"
        group_order = preview_df[group_column].fillna("").replace("", "Não classificado").value_counts().index.tolist()
        for group_name in group_order:
            group_df = preview_df.loc[
                preview_df[group_column].fillna("").replace("", "Não classificado") == group_name
            ].copy()
            group_df = group_df.sort_values(
                ["corpus", "institution", "video_date_display", "video_title_display"],
                ascending=[True, True, False, True],
            )
            with st.expander(f"{group_name} ({len(group_df)})", expanded=False):
                st.dataframe(
                    build_research_video_display_df(group_df),
                    use_container_width=True,
                    hide_index=True,
                )

    render_csv_download(
        "Exportar recorte da pesquisa",
        build_research_video_display_df(filtered_df),
        "observatorio_recorte_pesquisa_videos.csv",
        "Exporta os vídeos filtrados na ferramenta de pesquisa transversal.",
    )

def render_observatory_overview_tab():
    st.markdown(tr("overview_title"))
    st.caption(tr("overview_caption"))
    st.info(
        f"{OBSERVATORY_PROFILE['description']} "
        f"{OBSERVATORY_PROFILE['expansion_strategy']} "
        f"{OBSERVATORY_PROFILE['audiovisual_rule']}"
        if APP_LANGUAGE == DEFAULT_LANGUAGE
        else tr("observatory_profile_summary")
    )
    cycle_manifest = load_json(ORGANISM_MONTHLY_CYCLE_FILENAME)
    active_corpora_registry_df = load_csv(ORGANISM_ACTIVE_CORPORA_FILENAME)
    discovery_registry_df = load_csv(DISCOVERY_REGISTRY_FILENAME)
    discovery_queue_df = load_csv(DISCOVERY_QUEUE_FILENAME)
    discovery_summary_df = load_csv(DISCOVERY_SUMMARY_FILENAME)
    european_aggregator_access_routes_df = load_csv(EUROPEAN_AGGREGATOR_ACCESS_ROUTES_FILENAME)
    european_aggregator_evaluation_df = load_csv(EUROPEAN_AGGREGATOR_EVALUATION_FILENAME)
    european_aggregator_probes_df = load_csv(EUROPEAN_AGGREGATOR_PROBES_FILENAME)
    european_aggregator_protocols_df = load_csv(EUROPEAN_AGGREGATOR_PROTOCOLS_FILENAME)
    european_aggregator_summary_df = load_csv(EUROPEAN_AGGREGATOR_SUMMARY_FILENAME)
    europe_closure_matrix_df = load_csv(EUROPE_CLOSURE_MATRIX_FILENAME)
    europe_closure_queue_df = load_csv(EUROPE_CLOSURE_QUEUE_FILENAME)
    europe_closure_summary_df = load_csv(EUROPE_CLOSURE_SUMMARY_FILENAME)
    europe_excluded_units_df = load_csv(EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME)
    europe_gap_audit_df = load_csv(EUROPE_CLOSURE_GAP_AUDIT_FILENAME)
    europe_research_registry_df = load_csv(EUROPE_RESEARCH_REGISTRY_FILENAME)
    europe_research_queue_df = load_csv(EUROPE_RESEARCH_QUEUE_FILENAME)
    europe_research_summary_df = load_csv(EUROPE_RESEARCH_SUMMARY_FILENAME)
    restricted_access_audit_df = load_csv(RESTRICTED_ACCESS_AUDIT_FILENAME)
    restricted_access_summary_df = load_csv(RESTRICTED_ACCESS_SUMMARY_FILENAME)
    public_access_index_df = load_csv(PUBLIC_ACCESS_INDEX_FILENAME)
    public_access_by_corpus_df = load_csv(PUBLIC_ACCESS_INDEX_BY_CORPUS_FILENAME)
    public_access_restricted_units_df = load_csv(PUBLIC_ACCESS_RESTRICTED_UNITS_FILENAME)
    archiveshub_protocol_df = load_csv(ARCHIVESHUB_PROTOCOL_FILENAME)
    francearchives_protocol_df = load_csv(FRANCEARCHIVES_PROTOCOL_FILENAME)
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
    if europe_research_registry_df is None or europe_research_registry_df.empty:
        europe_research_registry_df = build_europe_research_registry()
    if europe_research_queue_df is None or europe_research_queue_df.empty:
        europe_research_queue_df = build_europe_research_queue(europe_research_registry_df)
    if europe_research_summary_df is None or europe_research_summary_df.empty:
        europe_research_summary_df = build_europe_research_summary(europe_research_registry_df)
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
            f"Rodada {cycle_manifest.get('cycle_type', '-')} mais recente: "
            f"{cycle_manifest.get('successful_corpora_total', 0)} sucessos, "
            f"{cycle_manifest.get('failed_corpora_total', 0)} pendências, "
            f"gerado em {format_snapshot_timestamp(cycle_manifest.get('generated_at')) or '-'}."
        )

    st.markdown(tr("academic_axis_title"))
    st.markdown(tr("academic_axis_text"))
    st.caption(tr("academic_axis_caption"))

    if cycle_timeline_df is not None and not cycle_timeline_df.empty:
        cycle_metric_cols = st.columns(4)
        cycle_metric_cols[0].metric("Rodadas registradas", len(cycle_timeline_df))
        cycle_metric_cols[1].metric(
            "Último escopo",
            str(cycle_timeline_df.iloc[-1].get("cycle_scope", "-")),
        )
        cycle_metric_cols[2].metric(
            "Unidades avaliadas na última rodada",
            int(pd.to_numeric(cycle_timeline_df.iloc[-1].get("selected_corpora_total", 0), errors="coerce")),
        )
        cycle_metric_cols[3].metric(
            "Pendências na última rodada",
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

        st.markdown("### Acompanhamento das atualizações")
        st.caption(
            "Este quadro acompanha a saúde temporal do observatório por unidade documental, distinguindo "
            "atualizações recentes, pendências de rodadas parciais e atrasos de acompanhamento."
        )
        refresh_metric_cols = st.columns(4)
        refresh_metric_cols[0].metric("Atualizadas na última rodada", latest_cycle_updates)
        refresh_metric_cols[1].metric("Pendentes na rodada parcial", partial_pending)
        refresh_metric_cols[2].metric("Atualizações atrasadas", stale_count)
        refresh_metric_cols[3].metric("Pendências na última rodada", failure_count)

        refresh_display_df = refresh_status_df.rename(
            columns={
                "corpus": "unidade documental",
                "category_label": "categoria analítica",
                "coverage_level": "escala de cobertura",
                "scope": "escopo",
                "collection_completeness": "completude da coleta",
                "selection_limit": "limite técnico",
                "completeness_note": "nota de completude",
                "included_in_latest_cycle": "incluída na última rodada",
                "latest_cycle_scope": "escopo da última rodada",
                "latest_cycle_status": "situação na última rodada",
                "last_successful_cycle_at": "última rodada bem-sucedida",
                "last_snapshot_generated_at": "última observação registrada",
                "source_status_date": "status da fonte",
                "observation_key": "chave de observação",
                "days_since_last_observation": "dias desde a última observação",
                "refresh_state": "estado de atualização",
                "refresh_state_reason": "justificativa metodológica",
            }
        ).copy()
        refresh_display_df["incluída na última rodada"] = refresh_display_df["incluída na última rodada"].map(
            format_yes_no
        )
        refresh_display_df["situação na última rodada"] = refresh_display_df["situação na última rodada"].map(
            format_cycle_status
        )
        refresh_display_df["última rodada bem-sucedida"] = refresh_display_df["última rodada bem-sucedida"].map(
            format_snapshot_timestamp
        )
        refresh_display_df["última observação registrada"] = refresh_display_df[
            "última observação registrada"
        ].map(format_snapshot_timestamp)
        st.dataframe(refresh_display_df, use_container_width=True, hide_index=True)
        with st.expander("Ver distribuição dos estados de atualização", expanded=False):
            st.dataframe(refresh_counts, use_container_width=True, hide_index=True)

    if public_access_index_df is not None and not public_access_index_df.empty:
        st.markdown("### Índice de dados públicos")
        st.caption(
            "O índice compara registros audiovisuais disponíveis em superfície pública com registros "
            "cujo acesso ao audiovisual exige pagamento, autenticação, cadastro ou licenciamento. "
            "Bancos privados/publicitários de imagens não entram no índice; permanecem documentados "
            "apenas na auditoria metodológica de acesso pago/restrito."
        )

        def public_access_scope_row(scope):
            matches = public_access_index_df.loc[public_access_index_df["scope"].astype(str) == scope]
            return matches.iloc[0] if not matches.empty else pd.Series(dtype="object")

        def numeric_cell(row, column):
            value = pd.to_numeric(row.get(column, 0), errors="coerce")
            return 0 if pd.isna(value) else value

        def percent_label(row, column):
            return f"{float(numeric_cell(row, column)):.2f}%"

        world_public_access_row = public_access_scope_row("World")
        europe_public_access_row = public_access_scope_row("Europe")
        access_metric_cols = st.columns(4)
        access_metric_cols[0].metric(
            "Índice público World",
            percent_label(world_public_access_row, "public_records_percent"),
        )
        access_metric_cols[1].metric(
            "Índice público Europa",
            percent_label(europe_public_access_row, "public_records_percent"),
        )
        access_metric_cols[2].metric(
            "Registros restritos quantificados",
            int(numeric_cell(world_public_access_row, "restricted_records")),
        )
        access_metric_cols[3].metric(
            "Unidades restritas no índice",
            int(numeric_cell(world_public_access_row, "restricted_units_total")),
        )

        index_tab, corpus_index_tab, restricted_units_tab = st.tabs(
            ["Mundo e continentes", "Por unidade documental", "Acesso restrito"]
        )
        with index_tab:
            index_display_df = public_access_index_df.rename(
                columns={
                    "scope_level": "nível",
                    "scope": "recorte",
                    "public_records": "registros públicos",
                    "restricted_records": "registros restritos",
                    "materialized_records_total": "registros avaliados no observatório",
                    "public_records_percent": "% público",
                    "restricted_records_percent": "% restrito",
                    "restricted_units_without_public_catalog": "unidades não quantificáveis no índice",
                    "restricted_unit_codes": "unidades restritas",
                    "denominator_note": "nota do denominador",
                }
            )
            st.dataframe(index_display_df, use_container_width=True, hide_index=True)
            render_csv_download(
                "Exportar índice de dados públicos",
                public_access_index_df,
                PUBLIC_ACCESS_INDEX_FILENAME,
                "Exporta o índice World/continentes de dados públicos e restritos.",
            )
        with corpus_index_tab:
            if public_access_by_corpus_df is None or public_access_by_corpus_df.empty:
                st.info("Ainda não há índice por unidade documental disponível.")
            else:
                corpus_display_df = public_access_by_corpus_df.rename(
                    columns={
                        "corpus_code": "código",
                        "corpus": "unidade documental",
                        "category_label": "categoria",
                        "continent": "continente",
                        "public_records": "registros públicos",
                        "restricted_records": "registros restritos",
                        "materialized_records_total": "registros avaliados no observatório",
                        "public_records_percent": "% público",
                        "restricted_records_percent": "% restrito",
                        "denominator_note": "nota do denominador",
                    }
                )
                st.dataframe(corpus_display_df, use_container_width=True, hide_index=True)
                render_csv_download(
                    "Exportar índice por unidade documental",
                    public_access_by_corpus_df,
                    PUBLIC_ACCESS_INDEX_BY_CORPUS_FILENAME,
                    "Exporta o índice de dados públicos por unidade documental ativa.",
                )
        with restricted_units_tab:
            if public_access_restricted_units_df is None or public_access_restricted_units_df.empty:
                st.info("Ainda não há unidades restritas registradas no índice.")
            else:
                st.caption(
                    "Esta tabela mostra apenas unidades restritas que fazem parte do índice. "
                    "Bancos privados/publicitários ficam fora deste recorte."
                )
                restricted_display_df = public_access_restricted_units_df.rename(
                    columns={
                        "unit_code": "código",
                        "unit_label": "unidade",
                        "continent": "continente",
                        "corpus_status": "status no organismo",
                        "category_label": "categoria de restrição",
                        "restricted_records": "registros restritos",
                        "restricted_volume_status": "status do volume",
                        "source_file": "arquivo-fonte",
                        "evidence": "evidência",
                    }
                )
                st.dataframe(restricted_display_df, use_container_width=True, hide_index=True)
                render_csv_download(
                    "Exportar unidades restritas do índice",
                    public_access_restricted_units_df,
                    PUBLIC_ACCESS_RESTRICTED_UNITS_FILENAME,
                    "Exporta unidades com acesso restrito, cadastro, pagamento ou licenciamento.",
                )

    st.markdown("### Linha do tempo e retração pública do audiovisual")
    st.caption(
        "Esta camada reúne a memória histórica das unidades documentais e prepara o observatório para detectar "
        "ausências, indisponibilidades recorrentes e perda de evidência pública detectável de audiovisual."
    )
    global_history_cols = st.columns(4)
    global_history_cols[0].metric(
        "Observações históricas das unidades",
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
        "Unidades com histórico registrado",
        int(global_corpus_timeline_df["corpus"].nunique()) if global_corpus_timeline_df is not None and not global_corpus_timeline_df.empty else 0,
    )

    global_history_tab, global_signals_tab = st.tabs(
        ["Histórico geral", "Sinais de possível extinção"]
    )
    with global_history_tab:
        if global_corpus_timeline_df is None or global_corpus_timeline_df.empty:
            st.info("Ainda não há histórico geral disponível para o observatório.")
        else:
            st.caption(
                "Cada linha preserva uma observação histórica de uma unidade documental, mantendo explícita sua "
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
                "Exportar histórico geral das unidades",
                global_corpus_timeline_df,
                "observatorio_linha_do_tempo_global_corpora.csv",
                "Exporta a linha do tempo combinada das unidades do observatório.",
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
                "Exportar sinais de possível extinção",
                global_extinction_signals_df,
                "observatorio_sinais_globais_possivel_extincao.csv",
                "Exporta os sinais combinados de retração e possível extinção detectados no observatório.",
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
    metric_cols[0].metric("Unidades documentais ativas", total_corpora)
    metric_cols[1].metric("Instituições no observatório", total_institutions)
    metric_cols[2].metric("Instituições com links de vídeo", total_with_video_links)
    metric_cols[3].metric("Links de vídeo detectados", total_video_links)
    metric_cols[4].metric("Vídeos no recorte curatorial", total_curatorial_videos)

    comparison_df = overview_df.rename(
        columns={
            "corpus": "unidade documental",
            "label": "unidade",
            "category": "categoria analítica",
            "coverage_level": "escala de cobertura",
            "expansion_stage": "etapa de expansão",
            "entity_level": "nível da unidade",
            "scope": "escopo",
            "collection_completeness": "completude da coleta",
            "selection_limit": "limite técnico",
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
                "corpora": "unidades documentais",
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

    st.markdown("### Fila de expansão do observatório")
    st.caption(
        "A fila abaixo é gerada por regra pública e reprodutível. Neste momento, ela prioriza "
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
        ["Síntese da fila", "Fontes candidatas"]
    )
    with discovery_summary_tab:
        st.dataframe(discovery_summary_df, use_container_width=True, hide_index=True)
        summary_download_cols = st.columns(2)
        with summary_download_cols[0]:
            render_csv_download(
                "Exportar síntese da fila",
                discovery_summary_df,
                DISCOVERY_SUMMARY_FILENAME,
                "Exporta a síntese das decisões de expansão do observatório.",
            )
        with summary_download_cols[1]:
            render_csv_download(
                "Exportar fila de expansão",
                discovery_queue_df,
                DISCOVERY_QUEUE_FILENAME,
                "Exporta a fila atual de fontes candidatas priorizadas pelo observatório.",
            )
    with discovery_queue_tab:
        st.caption(
            "Cada linha mostra uma unidade potencial, a decisão automática aplicada e o próximo passo "
            "sugerido pelo protocolo do organismo."
        )
        st.dataframe(discovery_queue_df, use_container_width=True, hide_index=True)
        render_csv_download(
            "Exportar registro completo de candidatos",
            discovery_registry_df,
            DISCOVERY_REGISTRY_FILENAME,
            "Exporta o registro completo de candidatos e unidades já incorporadas ao observatório.",
        )

    st.markdown("### Avaliação metodológica dos agregadores europeus")
    st.caption(
        "Esta camada não incorpora novas unidades automaticamente. Ela observa a superfície pública de "
        "Archives Hub, FranceArchives, PARES e Portal Português de Arquivos para decidir, com "
        "evidência registrada, qual fonte pode seguir para validação total e qual exige nova rota "
        "de acesso."
    )
    if european_aggregator_evaluation_df is None or european_aggregator_evaluation_df.empty:
        st.info(
            "A avaliação dos agregadores europeus ainda não está disponível nesta versão do observatório."
        )
    else:
        ready_count = int(
            (
                european_aggregator_evaluation_df.get("candidate_status", pd.Series(dtype="object"))
                == "pronto_para_validacao_total"
            ).sum()
        )
        protocol_count = int(
            (
                european_aggregator_evaluation_df.get("candidate_status", pd.Series(dtype="object"))
                == "requer_protocolo_de_acesso"
            ).sum()
        )
        result_total = int(
            pd.to_numeric(
                european_aggregator_evaluation_df.get("search_result_count_total", pd.Series(dtype="int")),
                errors="coerce",
            )
            .fillna(0)
            .sum()
        )
        blocked_probe_total = int(
            pd.to_numeric(
                european_aggregator_evaluation_df.get("blocked_probe_count", pd.Series(dtype="int")),
                errors="coerce",
            )
            .fillna(0)
            .sum()
        )
        european_eval_metric_cols = st.columns(4)
        european_eval_metric_cols[0].metric("Agregadores avaliados", len(european_aggregator_evaluation_df))
        european_eval_metric_cols[1].metric("Prontos para validação total", ready_count)
        european_eval_metric_cols[2].metric("Exigem nova rota de acesso", protocol_count)
        european_eval_metric_cols[3].metric(
            "Registros preliminares de busca",
            format_integer_pt(result_total),
        )
        st.caption(
            "Os registros preliminares de busca somam os resultados brutos retornados nas verificações "
            "dos agregadores. Eles não equivalem a vídeos incorporados ao corpus: indicam apenas volume potencial "
            "a validar, deduplicar e classificar."
        )

        evaluation_display_df = european_aggregator_evaluation_df.rename(
            columns={
                "label": "agregador",
                "country_scope": "país/escopo",
                "coverage_level": "escala",
                "access_model": "modelo de acesso observado",
                "candidate_status": "status metodológico",
                "audiovisual_probe_terms": "termos sondados",
                "search_result_count_total": "registros preliminares de busca",
                "successful_probe_terms": "termos com resultado",
                "blocked_probe_terms": "termos bloqueados",
                "ingestion_recommendation": "recomendação de ingestão",
                "next_step": "próximo passo",
                "evaluated_at": "avaliado em",
                "best_probe_url": "melhor URL de sondagem",
            }
        )
        st.dataframe(
            evaluation_display_df[
                [
                    "agregador",
                    "país/escopo",
                    "escala",
                    "modelo de acesso observado",
                    "status metodológico",
                    "termos sondados",
                    "registros preliminares de busca",
                    "termos com resultado",
                    "termos bloqueados",
                    "recomendação de ingestão",
                    "próximo passo",
                    "avaliado em",
                    "melhor URL de sondagem",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

        if european_aggregator_protocols_df is not None and not european_aggregator_protocols_df.empty:
            st.markdown("#### Matriz de decisão de incorporação")
            st.caption(
                "Esta matriz separa decisão metodológica de disponibilidade técnica: uma fonte pode "
                "ser relevante para o fechamento europeu e, ainda assim, permanecer fora das unidades "
                "ativas até existir uma rota estável de acesso."
            )
            protocol_display_df = european_aggregator_protocols_df.rename(
                columns={
                    "label": "agregador",
                    "country_scope": "país/escopo",
                    "candidate_status": "status metodológico",
                    "access_model": "modelo observado",
                    "protocol_needed": "exige nova rota",
                    "protocol_status": "estado da avaliação",
                    "evidence_summary": "evidência observada",
                    "methodological_risk": "risco metodológico",
                    "recommended_protocol": "encaminhamento recomendado",
                    "incorporation_decision": "decisão de incorporação",
                    "priority": "prioridade",
                    "next_review_trigger": "gatilho de revisão",
                }
            )
            st.dataframe(
                protocol_display_df[
                    [
                        "agregador",
                        "país/escopo",
                        "status metodológico",
                        "modelo observado",
                        "exige nova rota",
                        "estado da avaliação",
                        "evidência observada",
                        "risco metodológico",
                        "encaminhamento recomendado",
                        "decisão de incorporação",
                        "prioridade",
                        "gatilho de revisão",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

        if european_aggregator_access_routes_df is not None and not european_aggregator_access_routes_df.empty:
            with st.expander("Rotas oficiais analisadas", expanded=False):
                st.caption(
                    "Estas rotas não promovem automaticamente uma fonte a unidade ativa. Elas registram "
                    "caminhos oficiais ou documentados que podem ser testados antes da incorporação."
                )
                access_route_display_df = european_aggregator_access_routes_df.rename(
                    columns={
                        "label": "agregador",
                        "country_scope": "país/escopo",
                        "route_type": "tipo de rota",
                        "route_url": "URL da rota",
                        "source_reference_url": "referência oficial",
                        "source_reference_note": "nota da referência",
                        "http_status": "resposta do site",
                        "content_type": "tipo de conteúdo",
                        "access_status": "status de acesso",
                        "route_viability": "viabilidade da rota",
                        "audiovisual_use": "uso audiovisual possível",
                        "methodological_note": "nota metodológica",
                    }
                )
                st.dataframe(
                    access_route_display_df[
                        [
                            "agregador",
                            "país/escopo",
                            "tipo de rota",
                            "resposta do site",
                            "tipo de conteúdo",
                            "status de acesso",
                            "viabilidade da rota",
                            "uso audiovisual possível",
                            "nota metodológica",
                            "URL da rota",
                            "referência oficial",
                            "nota da referência",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

        if archiveshub_protocol_df is not None and not archiveshub_protocol_df.empty:
            with st.expander("Verificação metodológica do Archives Hub", expanded=False):
                st.caption(
                    "Este quadro testa SRU e OAI-PMH em modo mínimo, sem promover o Archives Hub "
                    "a unidade ativa enquanto a rota de acesso não estiver estável."
                )
                archiveshub_protocol_display_df = archiveshub_protocol_df.rename(
                    columns={
                        "probe_label": "sondagem",
                        "method": "método",
                        "http_status": "resposta do site",
                        "content_type": "tipo de conteúdo",
                        "content_length": "tamanho informado",
                        "access_status": "status de acesso",
                        "evidence_signal": "sinal observado",
                        "observed_value": "valor observado",
                        "protocol_conclusion": "conclusão do protocolo",
                        "next_step": "próximo passo",
                        "methodological_note": "nota metodológica",
                        "url": "URL",
                    }
                )
                st.dataframe(
                    archiveshub_protocol_display_df[
                        [
                            "sondagem",
                            "método",
                            "resposta do site",
                            "tipo de conteúdo",
                            "tamanho informado",
                            "status de acesso",
                            "sinal observado",
                            "valor observado",
                            "conclusão do protocolo",
                            "próximo passo",
                            "nota metodológica",
                            "URL",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

        if francearchives_protocol_df is not None and not francearchives_protocol_df.empty:
            with st.expander("Verificação metodológica do FranceArchives", expanded=False):
                st.caption(
                    "Este quadro testa sinais mínimos de viabilidade técnica para FranceArchives "
                    "sem transferir integralmente o pacote XML e sem transformar a fonte em unidade ativa."
                )
                francearchives_protocol_display_df = francearchives_protocol_df.rename(
                    columns={
                        "probe_label": "sondagem",
                        "method": "método",
                        "http_status": "resposta do site",
                        "content_type": "tipo de conteúdo",
                        "content_length": "tamanho informado",
                        "access_status": "status de acesso",
                        "evidence_signal": "sinal observado",
                        "observed_value": "valor observado",
                        "protocol_conclusion": "conclusão do protocolo",
                        "next_step": "próximo passo",
                        "methodological_note": "nota metodológica",
                        "url": "URL",
                    }
                )
                st.dataframe(
                    francearchives_protocol_display_df[
                        [
                            "sondagem",
                            "método",
                            "resposta do site",
                            "tipo de conteúdo",
                            "tamanho informado",
                            "status de acesso",
                            "sinal observado",
                            "valor observado",
                            "conclusão do protocolo",
                            "próximo passo",
                            "nota metodológica",
                            "URL",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

        with st.expander("Ver verificações realizadas", expanded=False):
            st.caption(
                f"As verificações registram respostas dos sites, bloqueios por JS/cookies, problemas de TLS "
                f"e contagens preliminares. Total de verificações bloqueadas: {blocked_probe_total}."
            )
            if european_aggregator_summary_df is not None and not european_aggregator_summary_df.empty:
                st.dataframe(european_aggregator_summary_df, use_container_width=True, hide_index=True)
            if european_aggregator_probes_df is not None and not european_aggregator_probes_df.empty:
                probe_display_df = european_aggregator_probes_df.rename(
                    columns={
                        "label": "agregador",
                        "probe_type": "tipo de verificação",
                        "query": "termo",
                        "http_status": "resposta do site",
                        "access_status": "status de acesso",
                        "js_cookie_required": "exige JS/cookies",
                        "tls_verification_failed": "falha TLS",
                        "result_count": "resultados",
                        "final_url": "URL final",
                        "methodological_note": "nota metodológica",
                    }
                )
                st.dataframe(probe_display_df, use_container_width=True, hide_index=True)
        european_download_cols = st.columns(7)
        with european_download_cols[0]:
            render_csv_download(
                "Exportar avaliação dos agregadores europeus",
                european_aggregator_evaluation_df,
                EUROPEAN_AGGREGATOR_EVALUATION_FILENAME,
                "Exporta a síntese metodológica por agregador europeu candidato.",
            )
        with european_download_cols[1]:
            render_csv_download(
                "Exportar verificações realizadas",
                european_aggregator_probes_df,
                EUROPEAN_AGGREGATOR_PROBES_FILENAME,
                "Exporta cada sondagem executada nas superfícies públicas dos agregadores.",
            )
        with european_download_cols[2]:
            render_csv_download(
                "Exportar rotas analisadas",
                european_aggregator_access_routes_df,
                EUROPEAN_AGGREGATOR_ACCESS_ROUTES_FILENAME,
                "Exporta rotas oficiais ou documentadas para resolver protocolos de acesso.",
            )
        with european_download_cols[3]:
            render_csv_download(
                "Exportar decisões metodológicas europeias",
                european_aggregator_protocols_df,
                EUROPEAN_AGGREGATOR_PROTOCOLS_FILENAME,
                "Exporta a matriz de protocolos e decisões metodológicas por agregador candidato.",
            )
        with european_download_cols[4]:
            render_csv_download(
                "Exportar verificação do Archives Hub",
                archiveshub_protocol_df,
                ARCHIVESHUB_PROTOCOL_FILENAME,
                "Exporta o protótipo leve de validação técnica do Archives Hub.",
            )
        with european_download_cols[5]:
            render_csv_download(
                "Exportar verificação do FranceArchives",
                francearchives_protocol_df,
                FRANCEARCHIVES_PROTOCOL_FILENAME,
                "Exporta o protótipo leve de validação técnica do FranceArchives.",
            )
        with european_download_cols[6]:
            render_csv_download(
                "Exportar síntese da avaliação europeia",
                european_aggregator_summary_df,
                EUROPEAN_AGGREGATOR_SUMMARY_FILENAME,
                "Exporta a síntese dos estados metodológicos observados.",
            )

    st.markdown("### Fechamento da etapa Europa")
    st.caption(
        "Este quadro explicita o estado metodológico da etapa Europa. Ele não afirma que todos os "
        "arquivos audiovisuais europeus foram identificados; registra o que já opera como unidade ativa, "
        "o que está protocolado e o que segue em fila auditável de expansão."
    )
    if europe_closure_summary_df is None or europe_closure_summary_df.empty:
        st.info(
            "O relatório de fechamento europeu ainda não está disponível nesta versão do observatório."
        )
    else:
        closure_status = (
            europe_closure_summary_df.loc[
                europe_closure_summary_df["criterion"] == "abertura_do_proximo_continente",
                "status",
            ]
            .astype(str)
            .head(1)
            .tolist()
        )
        active_units = 0
        pending_units = 0
        excluded_units = 0
        audited_gaps = 0
        if europe_closure_matrix_df is not None and not europe_closure_matrix_df.empty:
            active_units = int((europe_closure_matrix_df["unit_type"] == "corpus_ativo").sum())
            pending_units = int((europe_closure_matrix_df["unit_type"] == "agregador_candidato").sum())
        if europe_excluded_units_df is not None and not europe_excluded_units_df.empty:
            excluded_units = len(europe_excluded_units_df)
        if europe_gap_audit_df is not None and not europe_gap_audit_df.empty:
            audited_gaps = len(europe_gap_audit_df)

        closure_cols = st.columns(5)
        closure_cols[0].metric("Unidades europeias ativas", active_units)
        closure_cols[1].metric("Candidatos em avaliação", pending_units)
        closure_cols[2].metric("Identificados fora da base ativa", excluded_units)
        closure_cols[3].metric("Lacunas auditadas", audited_gaps)
        closure_cols[4].metric(
            "Próxima etapa",
            closure_status[0].replace("_", " ") if closure_status else "-",
        )

        closure_tab_summary, closure_tab_matrix, closure_tab_excluded, closure_tab_paid_access, closure_tab_gap_audit = st.tabs(
            [
                "Critérios de fechamento",
                "Matriz europeia",
                "Fora da base ativa",
                "Acesso pago/restrito",
                "Lacunas documentadas",
            ]
        )
        with closure_tab_summary:
            st.dataframe(europe_closure_summary_df, use_container_width=True, hide_index=True)
            render_csv_download(
                "Exportar síntese do fechamento europeu",
                europe_closure_summary_df,
                EUROPE_CLOSURE_SUMMARY_FILENAME,
                "Exporta os critérios metodológicos usados para liberar a próxima etapa continental.",
            )
        with closure_tab_matrix:
            if europe_closure_matrix_df is None or europe_closure_matrix_df.empty:
                st.info("A matriz de fechamento europeu ainda não está disponível.")
            else:
                st.dataframe(europe_closure_matrix_df, use_container_width=True, hide_index=True)
                render_csv_download(
                    "Exportar matriz de fechamento europeu",
                    europe_closure_matrix_df,
                    EUROPE_CLOSURE_MATRIX_FILENAME,
                    "Exporta a situação de cada corpus ou candidato europeu.",
                )
        with closure_tab_excluded:
            if europe_excluded_units_df is None or europe_excluded_units_df.empty:
                st.info("Ainda não há unidades europeias documentadas fora da base ativa.")
            else:
                st.caption(
                    "Essas unidades foram identificadas e preservadas no observatório, mas não entram "
                    "na base ativa enquanto a rota de coleta não for estável e reprodutível."
                )
                excluded_display_df = europe_excluded_units_df.rename(
                    columns={
                        "unit_label": "unidade",
                        "unit_type": "tipo de unidade",
                        "territorial_scope": "escopo territorial",
                        "access_category": "categoria de acesso",
                        "public_status": "status público",
                        "methodological_decision": "decisão metodológica",
                        "negative_reason": "motivo da não inclusão",
                        "collection_route_attempted": "rota tentada",
                        "attempt_summary": "tentativas registradas",
                        "methodological_explanation": "explicação metodológica",
                        "protocol_status": "estado da avaliação",
                        "next_step": "próximo passo",
                        "blocks_expansion": "bloqueia expansão",
                    }
                )
                st.dataframe(
                    select_existing_columns(
                        excluded_display_df,
                        [
                            "unidade",
                            "tipo de unidade",
                            "escopo territorial",
                            "categoria de acesso",
                            "status público",
                            "decisão metodológica",
                            "motivo da não inclusão",
                            "rota tentada",
                            "tentativas registradas",
                            "explicação metodológica",
                            "estado da avaliação",
                            "próximo passo",
                            "bloqueia expansão",
                        ],
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
                if europe_closure_queue_df is not None and not europe_closure_queue_df.empty:
                    with st.expander("Ver posição dessas unidades na fila europeia", expanded=False):
                        not_included_codes = set(europe_excluded_units_df["unit_code"].astype(str))
                        queue_display_df = europe_closure_queue_df.loc[
                            europe_closure_queue_df["unit_code"].astype(str).isin(not_included_codes)
                        ].copy()
                        st.dataframe(queue_display_df, use_container_width=True, hide_index=True)
                render_csv_download(
                    "Exportar unidades identificadas não incorporadas",
                    europe_excluded_units_df,
                    EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
                    "Exporta as unidades europeias identificadas, mas mantidas fora da base ativa.",
                )
        with closure_tab_paid_access:
            if restricted_access_audit_df is None or restricted_access_audit_df.empty:
                st.info("A auditoria de acesso pago/restrito ainda não está disponível.")
            else:
                st.caption(
                    "Esta auditoria separa bancos privados pagos, catálogos comerciais de licenciamento "
                    "e streaming pago/autenticado. Nem todo acesso comercial fica fora da base ativa: quando "
                    "há registros públicos avaliados no observatório, ele permanece como modalidade analítica própria."
                )
                if restricted_access_summary_df is not None and not restricted_access_summary_df.empty:
                    st.dataframe(restricted_access_summary_df, use_container_width=True, hide_index=True)
                paid_access_display_df = restricted_access_audit_df.rename(
                    columns={
                        "unit_label": "unidade",
                        "corpus_status": "situação no observatório",
                        "access_category": "categoria de acesso",
                        "category_label": "categoria legível",
                        "total_records": "registros",
                        "evidence": "evidência",
                        "methodological_decision": "decisão metodológica",
                        "include_in_private_paid_bank_category": "entra como banco privado pago",
                        "source_file": "arquivo-fonte",
                        "example_titles": "exemplos",
                    }
                )
                st.dataframe(
                    select_existing_columns(
                        paid_access_display_df,
                        [
                            "unidade",
                            "situação no observatório",
                            "categoria legível",
                            "registros",
                            "evidência",
                            "decisão metodológica",
                            "entra como banco privado pago",
                            "arquivo-fonte",
                            "exemplos",
                        ],
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
                render_csv_download(
                    "Exportar auditoria de acesso pago/restrito",
                    restricted_access_audit_df,
                    RESTRICTED_ACCESS_AUDIT_FILENAME,
                    "Exporta os casos auditados com categorias metodológicas de acesso pago ou restrito.",
                )
        with closure_tab_gap_audit:
            if europe_gap_audit_df is None or europe_gap_audit_df.empty:
                st.info("A auditoria de lacunas europeias ainda não está disponível.")
            else:
                st.caption(
                    "Esta auditoria impede que o fechamento europeu seja lido como exaustividade absoluta. "
                    "Ela documenta unidades cobertas por bases ativas, fontes legadas, radares e candidatos "
                    "futuros, mantendo o MVP continental aberto à expansão controlada."
                )
                gap_audit_display_df = europe_gap_audit_df.rename(
                    columns={
                        "unit_label": "unidade",
                        "unit_type": "tipo de unidade",
                        "territorial_scope": "escopo territorial",
                        "audit_status": "status da auditoria",
                        "relation_to_active_corpus": "relação com a base ativa",
                        "corpus_decision": "decisão sobre a base",
                        "methodological_reason": "justificativa metodológica",
                        "source_url": "fonte",
                        "next_step": "próximo passo",
                        "blocks_expansion": "bloqueia expansão",
                    }
                )
                st.dataframe(
                    select_existing_columns(
                        gap_audit_display_df,
                        [
                            "unidade",
                            "tipo de unidade",
                            "escopo territorial",
                            "status da auditoria",
                            "relação com a base ativa",
                            "decisão sobre a base",
                            "justificativa metodológica",
                            "fonte",
                            "próximo passo",
                            "bloqueia expansão",
                        ],
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
                render_csv_download(
                    "Exportar lacunas europeias documentadas",
                    europe_gap_audit_df,
                    EUROPE_CLOSURE_GAP_AUDIT_FILENAME,
                    "Exporta a auditoria que delimita o que ficou fora da base europeia ativa do MVP.",
                )

    st.markdown("### Mapeamento europeu ampliado")
    st.caption(
        "Este módulo separa o registro europeu completo da fila operacional de pendências. Ele identifica "
        "agregadores, redes, diretórios e arquivos "
        "audiovisuais europeus sem chute: agregadores primeiro, diretórios especializados depois, "
        "arquivos individuais por expansão controlada. A varredura de fontes oficiais inclui Europeana, "
        "FIAF, EFG, EUscreen, FIAT/IFTA, INEDITS, ACE e EBU. A presença no registro não significa "
        "incorporação automática; a presença na fila significa análise pendente."
    )
    if europe_research_registry_df is None or europe_research_registry_df.empty:
        st.info("O mapeamento europeu ampliado ainda não está disponível.")
    else:
        europe_queue_layer = europe_research_queue_df.get("queue_layer", pd.Series(dtype="object")).astype(str)
        europe_research_cols = st.columns(4)
        europe_research_cols[0].metric("Unidades europeias mapeadas", len(europe_research_registry_df))
        europe_research_cols[1].metric(
            "Próximas análises individuais",
            int((europe_queue_layer == "fila_definitiva_um_por_um").sum()),
        )
        europe_research_cols[2].metric(
            "Diretórios a expandir",
            int(
                (
                    europe_research_registry_df["queue_decision"]
                    == "expandir_diretorio_para_fila_individual"
                ).sum()
            ),
        )
        europe_research_cols[3].metric(
            "Arquivos individuais",
            int(
                (
                    europe_research_registry_df["queue_decision"]
                    == "avaliar_arquivo_individual_um_por_um"
                ).sum()
            ),
        )
        research_tab_queue, research_tab_registry, research_tab_summary = st.tabs(
            ["Próximas unidades", "Mapa europeu", "Síntese do mapeamento"]
        )
        with research_tab_queue:
            queue_display_df = europe_research_queue_df.rename(
                columns={
                    "definitive_queue_rank": "ordem",
                    "unit_label": "unidade",
                    "unit_type": "tipo",
                    "source_family": "fonte",
                    "country_or_scope": "país/escopo",
                    "queue_layer": "camada da fila",
                    "queue_decision": "decisão",
                    "video_location_status": "status do local dos vídeos",
                    "video_location_candidate_url": "URL inicial",
                    "inclusion_gate": "porta metodológica",
                    "next_action": "próxima ação",
                }
            )
            st.dataframe(
                select_existing_columns(
                    queue_display_df,
                    [
                        "ordem",
                        "unidade",
                        "tipo",
                        "fonte",
                        "país/escopo",
                        "camada da fila",
                        "decisão",
                        "status do local dos vídeos",
                        "URL inicial",
                        "porta metodológica",
                        "próxima ação",
                    ],
                ),
                use_container_width=True,
                hide_index=True,
            )
            render_csv_download(
                "Exportar fila europeia de análise",
                europe_research_queue_df,
                EUROPE_RESEARCH_QUEUE_FILENAME,
                "Exporta a fila operacional para incorporar ou documentar unidades europeias uma por uma.",
            )
        with research_tab_registry:
            st.dataframe(europe_research_registry_df, use_container_width=True, hide_index=True)
            render_csv_download(
                "Exportar mapa europeu ampliado",
                europe_research_registry_df,
                EUROPE_RESEARCH_REGISTRY_FILENAME,
                "Exporta o registro ampliado de agregadores, redes, diretórios e fontes europeias.",
            )
        with research_tab_summary:
            st.dataframe(europe_research_summary_df, use_container_width=True, hide_index=True)
            render_csv_download(
                "Exportar síntese do mapeamento europeu",
                europe_research_summary_df,
                EUROPE_RESEARCH_SUMMARY_FILENAME,
                "Exporta a síntese por categoria e decisão de fila.",
            )

    chart_cols = st.columns(3)
    chart_base = overview_df.set_index("corpus")
    with chart_cols[0]:
        st.caption("Instituições com links de vídeo por unidade")
        st.bar_chart(chart_base[["institutions_with_video_links"]])
    with chart_cols[1]:
        st.caption("Links de vídeo detectados por unidade")
        st.bar_chart(chart_base[["video_links_total"]])
    with chart_cols[2]:
        st.caption("Vídeos no recorte curatorial por unidade")
        st.bar_chart(chart_base[["videos_in_curatorial_catalog"]])

    regime_long_df, regime_matrix_df = build_cross_corpus_breakdown(
        "access_regime_summary",
        "regime",
    )
    modality_long_df, modality_matrix_df = build_cross_corpus_breakdown(
        "access_surface_summary",
        "modalidade",
    )

    st.markdown("### Comparações entre unidades documentais")
    st.caption(
        "Estes quadros mostram como as unidades diferem não apenas em volume, mas também na forma "
        "como o audiovisual se torna publicamente acessível."
    )

    compare_tab_regimes, compare_tab_modalities = st.tabs(
        ["Regimes de acesso", "Modalidades de acesso"]
    )

    with compare_tab_regimes:
        if regime_long_df.empty:
            st.info("Ainda não há dados suficientes para comparar regimes de acesso entre unidades.")
        else:
            st.caption(
                "Linhas representam unidades documentais; colunas representam regimes institucionais de acesso audiovisual detectável."
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
            st.info("Ainda não há dados suficientes para comparar modalidades de acesso entre unidades.")
        else:
            st.caption(
                "Linhas representam unidades documentais; colunas representam modalidades públicas de acesso encontradas nos catálogos."
            )
            st.dataframe(
                style_matrix_display(prepare_matrix_display(modality_matrix_df)),
                use_container_width=True,
                hide_index=True,
            )
            with st.expander("Ver tabela detalhada de modalidades", expanded=False):
                st.dataframe(modality_long_df, use_container_width=True, hide_index=True)

    if cycle_timeline_df is not None and not cycle_timeline_df.empty:
        st.markdown("### Histórico do observatório")
        cycle_history_tab, cycle_results_tab, cycle_files_tab = st.tabs(
            ["Linha do tempo das rodadas", "Resultados por unidade", "Arquivos de referência"]
        )
        with cycle_history_tab:
            st.caption(
                "Cada linha representa uma rodada do observatório, permitindo acompanhar cadência, "
                "escopo e estabilidade das atualizações ao longo do tempo."
            )
            st.dataframe(
                cycle_timeline_df.sort_values("generated_at", ascending=False),
                use_container_width=True,
                hide_index=True,
            )
        with cycle_results_tab:
            if cycle_results_df is None or cycle_results_df.empty:
                st.info("Ainda não há resultados históricos disponíveis por unidade.")
            else:
                st.caption(
                    "Este quadro preserva o desempenho de cada unidade documental em cada rodada do observatório."
                )
                st.dataframe(
                    cycle_results_df.sort_values(["generated_at", "code"], ascending=[False, True]),
                    use_container_width=True,
                    hide_index=True,
                )
        with cycle_files_tab:
            st.caption(
                "Estes arquivos preservam a rastreabilidade global do observatório, permitindo "
                "auditar rodadas, unidades ativas e resultados históricos."
            )
            organism_files_df = pd.DataFrame(
                [
                    {
                        "arquivo": ORGANISM_MONTHLY_CYCLE_FILENAME,
                        "tipo": "síntese da última rodada",
                        "disponível": "Sim" if cycle_manifest else "Não",
                    },
                    {
                        "arquivo": ORGANISM_ACTIVE_CORPORA_FILENAME,
                        "tipo": "inventário de unidades ativas",
                        "disponível": "Sim"
                        if active_corpora_registry_df is not None and not active_corpora_registry_df.empty
                        else "Não",
                    },
                    {
                        "arquivo": ORGANISM_CYCLE_TIMELINE_FILENAME,
                        "tipo": "linha do tempo das rodadas",
                        "disponível": "Sim"
                        if cycle_timeline_df is not None and not cycle_timeline_df.empty
                        else "Não",
                    },
                    {
                        "arquivo": ORGANISM_CYCLE_RESULTS_FILENAME,
                        "tipo": "resultados históricos por unidade",
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
                    "Exportar síntese da última rodada",
                    cycle_manifest,
                    ORGANISM_MONTHLY_CYCLE_FILENAME,
                    "Exporta a síntese global da rodada mais recente do observatório.",
                )
                render_csv_download(
                    "Exportar unidades ativas do observatório",
                    active_corpora_registry_df,
                    ORGANISM_ACTIVE_CORPORA_FILENAME,
                    "Exporta o inventário atual das unidades ativas do observatório.",
                )
            with download_cols[1]:
                render_csv_download(
                    "Exportar linha do tempo das rodadas",
                    cycle_timeline_df,
                    ORGANISM_CYCLE_TIMELINE_FILENAME,
                    "Exporta a linha do tempo global das rodadas mensais do observatório.",
                )
                render_csv_download(
                    "Exportar resultados históricos por unidade",
                    cycle_results_df,
                    ORGANISM_CYCLE_RESULTS_FILENAME,
                    "Exporta o histórico consolidado dos resultados por unidade em cada rodada.",
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
    metric_cols[0].metric("Unidades na categoria", total_corpora)
    metric_cols[1].metric("Instituições no recorte", total_institutions)
    metric_cols[2].metric("Instituições com links de vídeo", total_with_video_links)
    metric_cols[3].metric("Links de vídeo detectados", total_video_links)
    metric_cols[4].metric("Vídeos no recorte curatorial", total_curatorial_videos)

    category_summary_tab, category_institutions_tab, category_videos_tab = st.tabs(
        ["Síntese", "Instituições", "Vídeos"]
    )

    with category_summary_tab:
        st.markdown("### Unidades desta categoria")
        if overview_df.empty:
            st.info("Ainda não há unidades disponíveis nesta categoria.")
        else:
            st.dataframe(
                overview_df.rename(
                    columns={
                        "corpus": "unidade documental",
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
            Esta categoria reúne apenas unidades classificadas como **{category_def['label'].lower()}**.
            O observatório permite trabalhar com todas elas em conjunto, mas sempre preservando o mesmo
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
            corpus_options = ["Todas as unidades"] + [corpus_def["short_label"] for corpus_def in corpora_in_category]
            with filter_cols[0]:
                selected_corpus = st.selectbox(
                    "Unidade documental",
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
            if selected_corpus != "Todas as unidades":
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
                "Exportar instituições da categoria",
                build_category_summary_display_df(filtered_summary_df),
                f"{category_code}_instituicoes_categoria.csv",
                "Exporta o recorte institucional desta categoria analítica.",
            )

    with category_videos_tab:
        st.markdown("### Vídeos da categoria")
        if filtered_curatorial_videos_df.empty:
            st.info("Ainda não há vídeos curatoriais disponíveis nesta categoria.")
        else:
            filter_cols = st.columns([1.1, 1.1, 1.3])
            corpus_options = ["Todas as unidades"] + [corpus_def["short_label"] for corpus_def in corpora_in_category]
            with filter_cols[0]:
                selected_corpus = st.selectbox(
                    "Unidade documental",
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
            if selected_corpus != "Todas as unidades":
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
                "Exportar vídeos da categoria",
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
            {"aspecto": "Completude da coleta", "descrição": corpus_def["collection_completeness"]},
            {"aspecto": "Critério de seleção", "descrição": corpus_def["selection_criterion"]},
            {"aspecto": "Limite técnico da rodada", "descrição": corpus_def["selection_limit"]},
            {"aspecto": "Nota de completude", "descrição": corpus_def["completeness_note"]},
            {"aspecto": "Relação com o APE", "descrição": corpus_def["ape_relationship"]},
            {"aspecto": "Justificativa de entrada", "descrição": corpus_def["expansion_rationale"]},
        ]
    )

    if corpus_def["code"] == "ape":
        st.subheader("Sobre o recorte APE")
        st.markdown(
            """
            Este observatório investiga a visibilidade pública do audiovisual em ambientes arquivísticos na web.
            Nesta etapa, a unidade analisada é o **Archives Portal Europe (APE)**, tratado como um portal
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
        st.subheader(f"Sobre o recorte {corpus_def['short_label']}")
        st.markdown(
            f"""
            Este recorte toma o **{corpus_def['label']}** como unidade especializada em audiovisual.
            Diferentemente do APE, que funciona como portal geral de arquivos, aqui o audiovisual
            tende a ocupar uma posição institucional central.

            **Objetivo**

            Examinar como um arquivo explicitamente audiovisual organiza a presença pública de seus vídeos,
            coleções, descrições e mediações digitais.

            **Princípio metodológico**

            Neste recorte, a questão central já não é apenas a existência de evidência pública detectável,
            mas a forma como um arquivo especializado apresenta, contextualiza e distribui seu audiovisual
            na web institucional.
            """
        )

    st.dataframe(framing_df, use_container_width=True, hide_index=True)
    st.caption(f"Política de expansão aplicável: {category_def['expansion_rule']}")
    st.caption(f"Regra audiovisual do recorte: {corpus_def['audiovisual_scope_note']}")
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
        ["Síntese institucional", "Temas e relações", "Casos documentados"]
    )

    with panel_summary_tab:
        summary_left, summary_right = st.columns([1.1, 1])

        with summary_left:
            st.subheader("Condição dos sites institucionais")
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

            st.subheader("Locais de acesso detectados")
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
        st.caption("Dentro de 'quebrado', o observatório distingue erro explícito e página suspeita.")

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
                    "status_tecnico": "situação da verificação",
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
            st.subheader("Casos com site quebrado")
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
                            "status_tecnico": "situação da verificação",
                            "partner_domain": "domínio",
                        }
                    ),
                    use_container_width=True,
                )

        with detail_right:
            st.subheader("Casos instáveis")
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
                            "status_tecnico": "situação da verificação",
                            "error": "erro",
                            "partner_domain": "domínio",
                            "final_url": "URL final",
                        }
                    ),
                    use_container_width=True,
                )

        with st.expander("Ver arquivos de referência desta unidade", expanded=False):
            st.dataframe(generated_files_status_df, use_container_width=True, hide_index=True)


def render_sites_tab(corpus_def, context):
    with_video = context["with_video"]
    detected_sites_df = context["detected_sites_df"]
    detail_url_field = corpus_def["detail_url_field"]
    detail_url_label = corpus_def["detail_url_label"]

    st.subheader(f"Instituições com vídeo localizado ({with_video})")
    st.caption(
        "Esta aba reúne as instituições em cujos sites a coleta encontrou ao menos um link explícito de vídeo."
    )
    if detected_sites_df.empty:
        st.info(f"Nenhum link de vídeo foi localizado ainda no recorte {corpus_def['short_label']}.")
        if corpus_def["category_code"] == "aggregator":
            st.caption(
                "Neste caso, a unidade continua relevante como fonte geral de pesquisa. "
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
            st.write(f"Situação da verificação: {format_technical_status(row['status'])}")
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

    st.subheader("Vídeos e temas")
    if video_catalog_df.empty:
        st.info(f"Nenhum link de vídeo foi localizado ainda no recorte {corpus_def['short_label']}.")
        if corpus_def["category_code"] == "aggregator":
            st.caption(
                "Como esta é uma fonte geral de pesquisa, o retorno zero não invalida a unidade. "
                "Ele indica apenas ausência de evidência pública detectável de audiovisual nesta rodada."
            )
        return

    st.markdown(
        "Este catálogo organiza o recorte curatorial de vídeos a partir de metadados básicos e de uma "
        "classificação temática baseada em título, assunto e descrição, excluindo por padrão o ruído "
        "de plataforma ou incorporação externa."
    )

    overview_cols = st.columns(5)
    overview_cols[0].metric("Vídeos curatoriais", curatorial_video_total)
    overview_cols[1].metric("Instituições com vídeos", int(video_catalog_df["slug"].nunique()))
    overview_cols[2].metric("Temas identificados", len(theme_counts))
    overview_cols[3].metric("Locais de acesso", int(video_catalog_df["platform"].nunique()))
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

    with st.expander("Ver sínteses do catálogo de vídeos", expanded=False):
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

    st.subheader("Tabelas de análise")
    st.caption(
        "Esta aba reúne as principais tabelas derivadas do recorte e permite exportá-las "
        "para pesquisa, redação, revisão metodológica e documentação."
    )

    output_files = corpus_def["output_files"]
    timeline_corpus_df = load_csv(output_files["timeline_corpus"])
    timeline_institutions_df = load_csv(output_files["timeline_institutions"])
    extinction_signals_df = load_csv(output_files["extinction_signals"])

    st.markdown("#### Tabelas disponíveis para exportação")
    download_col_1, download_col_2 = st.columns(2)
    with download_col_1:
        render_csv_download(
            "Exportar quadro institucional analítico",
            available_df,
            output_files["analytic_summary"],
            "Inclui disponibilidade, segmento institucional e situação metodológica do audiovisual por instituição.",
        )
        render_csv_download(
            "Exportar catálogo de vídeos",
            video_catalog_df,
            output_files["analytic_video_catalog"],
            "Inclui tema sugerido, data formatada e metadados básicos dos vídeos detectados.",
        )
        render_csv_download(
            "Exportar síntese temática",
            theme_counts,
            output_files["theme_summary"],
            "Síntese da classificação temática, excluindo ruído de plataforma.",
        )
        render_csv_download(
            "Exportar linha do tempo do recorte",
            timeline_corpus_df,
            output_files["timeline_corpus"],
            "Série histórica das rodadas do corpus, com contagens agregadas por observação.",
        )
    with download_col_2:
        render_csv_download(
            "Exportar síntese de visibilidade",
            visibility_counts,
            output_files["visibility_summary"],
            "Distribuição das situações metodológicas do audiovisual no corpus.",
        )
        render_csv_download(
            "Exportar modalidades de acesso",
            access_surface_counts,
            output_files["access_surface_summary"],
            "Síntese das modalidades de acesso detectadas no catálogo curatorial.",
        )
        render_csv_download(
            "Exportar regimes de acesso",
            access_regime_counts,
            output_files["access_regime_summary"],
            "Síntese institucional dos regimes de acesso audiovisual detectáveis.",
        )
        render_csv_download(
            "Exportar temas por país",
            theme_country_counts,
            output_files["theme_country"],
            "Tabela analítica dos temas por país no recorte curatorial.",
        )
        render_csv_download(
            "Exportar temas por tipo de arquivo",
            theme_archive_type_counts,
            output_files["theme_archive_type"],
            "Tabela analítica dos temas por tipo institucional declarado na fonte.",
        )
        render_csv_download(
            "Exportar sinais de possível extinção",
            extinction_signals_df,
            output_files["extinction_signals"],
            "Quadro de ausência, indisponibilidade reincidente e perda de evidência audiovisual entre rodadas.",
        )
        render_csv_download(
            "Exportar linha do tempo institucional",
            timeline_institutions_df,
            output_files["timeline_institutions"],
            "Série histórica por instituição, preservando os estados observados a cada rodada.",
        )

    st.markdown("#### Consulta das tabelas")
    analytic_view = st.radio(
        "Selecione a tabela",
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
            "Linha do tempo do recorte",
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
                analysis_utils.filter_curatorial_video_catalog(video_catalog_df),
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
    elif analytic_view == "Linha do tempo do recorte":
        if timeline_corpus_df is None or timeline_corpus_df.empty:
            st.info("Ainda não há linha do tempo disponível para este recorte.")
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
            st.info("Ainda não há linha do tempo institucional disponível para este recorte.")
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
    st.subheader(f"Instituições analisadas em {corpus_def['short_label']}")
    st.caption(
        "Cada linha representa uma unidade institucional do recorte, complementada pela verificação "
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
        "Exportar recorte atual das instituições",
        filtered_display_df,
        f"{corpus_def['code']}_base_consolidada_filtrada.csv",
        "Exporta o recorte atual da base consolidada com rótulos públicos de leitura.",
    )

    st.markdown("#### Síntese do recorte")
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

        with st.expander("Ver tabela completa do recorte", expanded=False):
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
        st.caption("Situação da verificação")
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
    evidence_cols[0].metric("Resposta do site", selected_summary["http_code"] if pd.notna(selected_summary["http_code"]) else "-")
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
            f"Páginas analisadas ({len(selected_internal)})",
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
                st.caption(f"Problema registrado na verificação: {selected_summary['error']}")

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
        st.subheader("Vídeos localizados na instituição")
        if selected_links.empty:
            st.info("Nenhum link de vídeo foi localizado automaticamente para esta instituição.")
        else:
            selected_links = selected_links.copy()
            selected_links["tema_sugerido"] = selected_links.apply(infer_video_theme, axis=1)
            selected_links = selected_links.loc[selected_links["tema_sugerido"] != NOISE_THEME_LABEL].copy()
            if selected_links.empty:
                st.info("Nenhum vídeo permaneceu no recorte curatorial após a filtragem de ruído fora de escopo.")
            selected_links["modalidade_acesso"] = selected_links.apply(analysis_utils.classify_access_surface, axis=1)
            selected_links["data_publicacao"] = selected_links["video_published_at"].apply(format_video_date)

            video_overview_cols = st.columns(4)
            video_overview_cols[0].metric("Vídeos curatoriais", len(selected_links))
            video_overview_cols[1].metric("Locais de acesso", int(selected_links["platform"].nunique()))
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
        st.subheader("Páginas analisadas")
        if selected_internal.empty:
            st.info("Nenhuma página complementar foi analisada para esta instituição.")
        else:
            selected_internal = selected_internal.copy()
            selected_internal["status_tecnico"] = selected_internal["status"].map(format_technical_status)

            internal_video_hits = int(pd.to_numeric(selected_internal["video_links_found"], errors="coerce").fillna(0).sum())
            internal_embedded_hits = int(pd.to_numeric(selected_internal["embedded_signals"], errors="coerce").fillna(0).sum())

            internal_metric_cols = st.columns(3)
            internal_metric_cols[0].metric("Páginas verificadas", len(selected_internal))
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
                        "internal_page": "página analisada",
                        "status_tecnico": "situação da verificação",
                        "http_code": "resposta do site",
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
        source_status_date = normalize_optional_text(snapshot_metadata.get("source_status_date"))
        source_status_text = (
            f"Fonte-base com status de {source_status_date}."
            if source_status_date
            else "Fonte-base sem data pública de status declarada nos metadados."
        )
        analytic_updated_at = format_snapshot_timestamp(snapshot_metadata.get("analytic_outputs_last_modified_at")) or "-"
        metadata_generated_at = format_snapshot_timestamp(snapshot_metadata.get("generated_at")) or "-"
        st.caption(
            f"{source_status_text} "
            f"Camada analítica atualizada em {analytic_updated_at}. "
            f"Metadados da rodada gerados em {metadata_generated_at}."
        )

    if summary_df is None:
        st.info(
            f"Nenhum relatório de {corpus_def['short_label']} está disponível nesta versão do observatório."
        )
        return

    if summary_df.empty:
        st.warning(
            f"O relatório de {corpus_def['short_label']} está disponível, mas não trouxe instituições para análise."
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
            f"O relatório de {corpus_def['short_label']} não trouxe identificadores institucionais suficientes para navegação."
        )
        return

    with st.expander("Seleção do recorte", expanded=True):
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
                "Tema dos vídeos",
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
            "Fundamentação",
            "Síntese",
            f"Instituições com vídeo ({with_video})",
            f"Vídeos e temas ({curatorial_video_total})",
            "Territórios",
            "Tabelas",
            "Instituições",
            "Ficha institucional",
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

def close_global_research():
    st.session_state["global-research-open"] = False
    st.session_state["header-global-research"] = ""
    build_research_video_catalog_frame.clear()


header_title_col, header_search_col = st.columns([5, 3], gap="large", vertical_alignment="center")
with header_title_col:
    st.title(tr("app_title"))
    st.caption(tr("app_caption"))

with header_search_col:
    search_field_col, search_button_col = st.columns([5, 2], gap="small", vertical_alignment="bottom")
    with search_field_col:
        header_search_term = st.text_input(
            "Pesquisa global",
            placeholder="Pesquisar no acervo audiovisual",
            label_visibility="collapsed",
            key="header-global-research",
        )
    with search_button_col:
        open_research = st.button(
            "Pesquisar",
            type="primary",
            use_container_width=True,
            key="header-global-research-open",
        )

if open_research:
    st.session_state["global-research-open"] = True
if header_search_term.strip():
    st.session_state["global-research-open"] = True

if st.session_state.get("global-research-open", False):
    with st.container(border=True):
        close_col = st.columns([7, 1], vertical_alignment="center")[1]
        with close_col:
            st.button(
                "Fechar pesquisa",
                use_container_width=True,
                key="header-global-research-close",
                on_click=close_global_research,
            )
        render_research_tab(initial_search_term=header_search_term, show_search_input=False)
    st.stop()

protocolled_excluded_units = load_protocolled_excluded_units()
top_level_tabs = st.tabs(
    [localize_ui("Visão geral")]
    + [tr("category_tab", label=localize_ui(category_def["short_label"])) for category_def in CORPUS_CATEGORIES.values()]
    + [tr("unit_tab", label=definition["short_label"]) for definition in CORPORA.values()]
    + [tr("documented_case_tab", label=unit["unit_label"]) for unit in protocolled_excluded_units]
)

with top_level_tabs[0]:
    render_observatory_overview_tab()

category_start = 1
category_tabs = top_level_tabs[category_start : category_start + len(CORPUS_CATEGORIES)]
corpus_start = category_start + len(CORPUS_CATEGORIES)
corpus_tabs = top_level_tabs[corpus_start : corpus_start + len(CORPORA)]
protocolled_tabs = top_level_tabs[corpus_start + len(CORPORA) :]

for category_tab, category_def in zip(category_tabs, CORPUS_CATEGORIES.values()):
    with category_tab:
        render_category_tab(category_def)

for corpus_tab, corpus_def in zip(corpus_tabs, CORPORA.values()):
    with corpus_tab:
        render_corpus_tab(corpus_def)

for protocolled_tab, unit_record in zip(protocolled_tabs, protocolled_excluded_units):
    with protocolled_tab:
        render_protocolled_excluded_unit_tab(unit_record)
