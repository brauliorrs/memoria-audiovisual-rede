from dataclasses import dataclass

import pandas as pd

from . import analysis as analysis_utils


DASHBOARD_SOURCE_KEYS = (
    "institutions",
    "summary",
    "video_links",
    "internal_pages",
    "analytic_summary",
    "analytic_video_catalog",
    "availability_summary",
    "availability_reasons",
    "archive_type_summary",
    "visibility_summary",
    "access_surface_summary",
    "access_regime_summary",
    "theme_summary",
    "theme_country",
    "theme_platform",
    "theme_archive_type",
    "visibility_archive_type",
)

_BASE_FRAME_DEFAULTS = {
    "archive_type": "",
    "ape_detail_url": "",
    "ina_detail_url": "",
    "ppa_detail_url": "",
    "website_available": False,
    "content_available_in_ape": False,
    "content_available_in_source": False,
    "country": "",
    "continent": "Não classificado",
    "warning": "",
    "video_title": "",
    "video_subject": "",
    "video_description": "",
    "video_published_at": "",
}

_EMPTY_LINKS_COLUMNS = ["institution", "slug", "platform", "video_link"]


@dataclass
class DashboardBaseData:
    catalog_df: pd.DataFrame
    summary_df: pd.DataFrame
    links_df: pd.DataFrame
    internal_df: pd.DataFrame
    summary_analysis_df: pd.DataFrame
    video_catalog_df: pd.DataFrame
    segmented_summary_df: pd.DataFrame
    available_slugs: list[str]


@dataclass
class DashboardOverviewData:
    total_institutions: int
    institutions_with_video: int
    integral_count: int
    unavailable_count: int
    website_count: int
    available_with_video_count: int
    availability_groups: pd.DataFrame
    availability_reasons: pd.DataFrame
    archive_type_counts: pd.DataFrame
    visibility_counts: pd.DataFrame
    access_surface_counts: pd.DataFrame
    access_regime_counts: pd.DataFrame
    detected_sites_df: pd.DataFrame
    continent_counts: pd.DataFrame
    country_counts: pd.DataFrame
    platform_counts: pd.DataFrame
    theme_counts: pd.DataFrame
    theme_country_counts: pd.DataFrame
    theme_country_matrix: pd.DataFrame
    theme_platform_counts: pd.DataFrame
    theme_archive_type_counts: pd.DataFrame
    theme_archive_type_matrix: pd.DataFrame
    visibility_archive_type_counts: pd.DataFrame
    visibility_archive_type_matrix: pd.DataFrame
    availability_reference_df: pd.DataFrame


def _copy_or_empty(frame, columns=None):
    if frame is None:
        if columns is None:
            return pd.DataFrame()
        return pd.DataFrame(columns=columns)
    return frame.copy()


def _ensure_base_columns(frame):
    prepared = frame.copy()
    for column, default_value in _BASE_FRAME_DEFAULTS.items():
        if column not in prepared.columns:
            prepared[column] = default_value
    return prepared


def _prefer_precomputed(precomputed_df, builder, required_columns=None, validator=None):
    if precomputed_df is not None:
        candidate = precomputed_df.copy()
        if not required_columns or all(column in candidate.columns for column in required_columns):
            if validator is None or validator(candidate):
                return candidate
    return builder()


def _video_count_series(summary_df):
    if "video_links_found_total" not in summary_df.columns:
        return pd.Series(dtype="int64")
    return pd.to_numeric(summary_df["video_links_found_total"], errors="coerce").fillna(0)


def _frame_total(frame):
    if frame is None or frame.empty or "total" not in frame.columns:
        return 0
    return int(pd.to_numeric(frame["total"], errors="coerce").fillna(0).sum())


def _value_count_signature(frame, columns):
    if frame is None or frame.empty or any(column not in frame.columns for column in columns):
        return pd.Series(dtype="int64")
    normalized = frame.loc[:, columns].fillna("").astype(str)
    return normalized.value_counts().sort_index()


def _summary_analysis_is_consistent(candidate, summary_df):
    if len(candidate) != len(summary_df):
        return False
    if "slug" in candidate.columns and "slug" in summary_df.columns:
        return _value_count_signature(candidate, ["slug"]).equals(
            _value_count_signature(summary_df, ["slug"])
        )
    return True


def _video_catalog_is_consistent(candidate, links_df):
    comparable_columns = ["slug", "platform", "video_link"]
    expected_links_df = analysis_utils.filter_in_scope_video_links_df(links_df)
    if len(candidate) != len(expected_links_df):
        return False
    if all(column in candidate.columns for column in comparable_columns) and all(
        column in expected_links_df.columns for column in comparable_columns
    ):
        return _value_count_signature(candidate, comparable_columns).equals(
            _value_count_signature(expected_links_df, comparable_columns)
        )
    return True


def _summary_total_is_consistent(candidate, expected_total):
    return _frame_total(candidate) == int(expected_total)


def build_dashboard_base_data(
    *,
    catalog_df,
    summary_df,
    links_df,
    internal_df,
    summary_analysis_source_df=None,
    video_catalog_source_df=None,
):
    if summary_df is None:
        raise ValueError("summary_df is required to build dashboard data")

    prepared_catalog_df = _ensure_base_columns(_copy_or_empty(catalog_df))
    prepared_summary_df = _ensure_base_columns(summary_df)
    prepared_links_df = _ensure_base_columns(_copy_or_empty(links_df, columns=_EMPTY_LINKS_COLUMNS))
    prepared_internal_df = _ensure_base_columns(_copy_or_empty(internal_df))

    video_catalog_df = _prefer_precomputed(
        video_catalog_source_df,
        lambda: analysis_utils.build_video_catalog_df(prepared_links_df),
        required_columns=[
            "video_theme",
            "access_surface",
            "video_title_display",
            "video_date_display",
        ],
        validator=lambda candidate: _video_catalog_is_consistent(candidate, prepared_links_df),
    )

    summary_analysis_df = _prefer_precomputed(
        summary_analysis_source_df,
        lambda: analysis_utils.build_institution_segments(prepared_summary_df, video_catalog_df),
        required_columns=[
            "availability_group",
            "availability_reason",
            "audiovisual_visibility",
            "institution_segment",
            "access_modalities_detected",
            "access_regime",
        ],
        validator=lambda candidate: _summary_analysis_is_consistent(candidate, prepared_summary_df),
    )

    available_slugs = [
        str(slug)
        for slug in prepared_summary_df["slug"].dropna().tolist()
        if str(slug).strip()
    ]

    return DashboardBaseData(
        catalog_df=prepared_catalog_df,
        summary_df=prepared_summary_df,
        links_df=prepared_links_df,
        internal_df=prepared_internal_df,
        summary_analysis_df=summary_analysis_df,
        video_catalog_df=video_catalog_df,
        segmented_summary_df=summary_analysis_df.copy(),
        available_slugs=available_slugs,
    )


def build_dashboard_overview_data(
    base_data,
    *,
    availability_groups_source_df=None,
    availability_reasons_source_df=None,
    archive_type_counts_source_df=None,
    visibility_counts_source_df=None,
    access_surface_counts_source_df=None,
    access_regime_counts_source_df=None,
    theme_counts_source_df=None,
    theme_country_counts_source_df=None,
    theme_platform_counts_source_df=None,
    theme_archive_type_counts_source_df=None,
    visibility_archive_type_counts_source_df=None,
):
    summary_df = base_data.summary_df
    summary_analysis_df = base_data.summary_analysis_df.copy()
    video_catalog_df = base_data.video_catalog_df.copy()
    video_count_series = _video_count_series(summary_analysis_df)

    availability_cache = None

    def get_availability_cache():
        nonlocal availability_cache
        if availability_cache is None:
            availability_cache = analysis_utils.build_availability_summary(summary_df)
        return availability_cache

    availability_groups = _prefer_precomputed(
        availability_groups_source_df,
        lambda: get_availability_cache()[1],
        required_columns=["categoria", "total"],
        validator=lambda candidate: _summary_total_is_consistent(candidate, len(summary_df)),
    )
    availability_reasons = _prefer_precomputed(
        availability_reasons_source_df,
        lambda: get_availability_cache()[2],
        required_columns=["subcategoria", "total"],
        validator=lambda candidate: _summary_total_is_consistent(candidate, len(summary_df)),
    )
    archive_type_counts = _prefer_precomputed(
        archive_type_counts_source_df,
        lambda: analysis_utils.build_archive_type_summary(summary_df),
        required_columns=["tipo_institucional", "total"],
        validator=lambda candidate: _summary_total_is_consistent(candidate, len(summary_df)),
    )
    curatorial_video_total = len(analysis_utils.filter_curatorial_video_catalog(video_catalog_df))
    visibility_counts = _prefer_precomputed(
        visibility_counts_source_df,
        lambda: analysis_utils.build_visibility_summary(summary_df, video_catalog_df)[1],
        required_columns=["situacao", "total"],
        validator=lambda candidate: _summary_total_is_consistent(candidate, len(summary_df)),
    )
    access_surface_counts = _prefer_precomputed(
        access_surface_counts_source_df,
        lambda: analysis_utils.build_access_surface_summary(video_catalog_df),
        required_columns=["modalidade", "total"],
        validator=lambda candidate: _summary_total_is_consistent(candidate, curatorial_video_total),
    )
    access_regime_counts = _prefer_precomputed(
        access_regime_counts_source_df,
        lambda: analysis_utils.build_access_regime_summary(summary_df, video_catalog_df),
        required_columns=["regime", "total"],
        validator=lambda candidate: _summary_total_is_consistent(candidate, len(summary_df)),
    )
    theme_counts = _prefer_precomputed(
        theme_counts_source_df,
        lambda: analysis_utils.build_theme_summary(video_catalog_df),
        required_columns=["tema", "total"],
        validator=lambda candidate: _summary_total_is_consistent(candidate, curatorial_video_total),
    )
    theme_country_counts = _prefer_precomputed(
        theme_country_counts_source_df,
        lambda: analysis_utils.build_theme_country_summary(video_catalog_df),
        required_columns=["tema", "pais", "total"],
        validator=lambda candidate: _summary_total_is_consistent(candidate, curatorial_video_total),
    )
    theme_platform_counts = _prefer_precomputed(
        theme_platform_counts_source_df,
        lambda: analysis_utils.build_theme_platform_summary(video_catalog_df),
        required_columns=["tema", "plataforma", "total"],
        validator=lambda candidate: _summary_total_is_consistent(candidate, curatorial_video_total),
    )
    theme_archive_type_counts = _prefer_precomputed(
        theme_archive_type_counts_source_df,
        lambda: analysis_utils.build_theme_archive_type_summary(video_catalog_df, summary_df),
        required_columns=["tema", "tipo_institucional", "total"],
        validator=lambda candidate: _summary_total_is_consistent(candidate, curatorial_video_total),
    )
    visibility_archive_type_counts = _prefer_precomputed(
        visibility_archive_type_counts_source_df,
        lambda: analysis_utils.build_visibility_archive_type_summary(summary_analysis_df),
        required_columns=["visibilidade", "tipo_institucional", "total"],
        validator=lambda candidate: _summary_total_is_consistent(candidate, len(summary_df)),
    )

    detected_sites_df = analysis_utils.build_detected_sites_df(summary_analysis_df, video_catalog_df)
    continent_counts, country_counts = analysis_utils.build_geography_summaries(detected_sites_df)
    platform_counts = analysis_utils.build_platform_summary(video_catalog_df)
    theme_country_matrix = analysis_utils.build_theme_country_matrix(video_catalog_df)
    theme_archive_type_matrix = analysis_utils.build_theme_archive_type_matrix(video_catalog_df, summary_df)
    visibility_archive_type_matrix = analysis_utils.build_visibility_archive_type_matrix(summary_analysis_df)
    availability_reference_df = analysis_utils.build_availability_reference()

    return DashboardOverviewData(
        total_institutions=len(summary_df),
        institutions_with_video=int((video_count_series > 0).sum()),
        integral_count=int((summary_df["integrity_status"] == "integro").sum()),
        unavailable_count=int(
            (
                summary_analysis_df["availability_group"]
                != analysis_utils.classify_availability_group("integro")
            ).sum()
        ),
        website_count=int(summary_df["website_available"].fillna(False).astype(bool).sum()),
        available_with_video_count=int((video_count_series > 0).sum()),
        availability_groups=availability_groups,
        availability_reasons=availability_reasons,
        archive_type_counts=archive_type_counts,
        visibility_counts=visibility_counts,
        access_surface_counts=access_surface_counts,
        access_regime_counts=access_regime_counts,
        detected_sites_df=detected_sites_df,
        continent_counts=continent_counts,
        country_counts=country_counts,
        platform_counts=platform_counts,
        theme_counts=theme_counts,
        theme_country_counts=theme_country_counts,
        theme_country_matrix=theme_country_matrix,
        theme_platform_counts=theme_platform_counts,
        theme_archive_type_counts=theme_archive_type_counts,
        theme_archive_type_matrix=theme_archive_type_matrix,
        visibility_archive_type_counts=visibility_archive_type_counts,
        visibility_archive_type_matrix=visibility_archive_type_matrix,
        availability_reference_df=availability_reference_df,
    )


__all__ = [
    "DASHBOARD_SOURCE_KEYS",
    "DashboardBaseData",
    "DashboardOverviewData",
    "build_dashboard_base_data",
    "build_dashboard_overview_data",
]
