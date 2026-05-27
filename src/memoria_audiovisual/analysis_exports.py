import pandas as pd

from .analysis import build_analysis_exports
from .analysis import build_access_regime_summary
from .analysis import build_access_surface_summary
from .analysis import build_archive_type_summary
from .analysis import build_availability_summary
from .analysis import build_theme_archive_type_summary
from .analysis import build_theme_platform_summary
from .analysis import build_visibility_archive_type_summary
from .reporting import save_csv


ANALYTIC_SHEET_TITLES = {
    "analytic_summary": "Analytical Summary",
    "analytic_video_catalog": "Video Catalog",
    "visibility_summary": "Visibility Summary",
    "access_surface_summary": "Access Surface Summary",
    "access_regime_summary": "Access Regime Summary",
    "theme_summary": "Theme Summary",
    "theme_country": "Theme by Country",
    "availability_summary": "Availability Summary",
    "availability_reasons": "Availability Reasons",
    "archive_type_summary": "Archive Type Summary",
    "theme_platform": "Theme by Platform",
    "theme_archive_type": "Theme by Archive Type",
    "visibility_archive_type": "Visibility by Archive Type",
}


def dataframe_to_rows(dataframe):
    if dataframe.empty:
        return [], list(dataframe.columns)
    rows = dataframe.where(pd.notna(dataframe), "").to_dict(orient="records")
    return rows, list(dataframe.columns)


def build_analysis_frames(summary_df, links_df):
    analysis_exports = build_analysis_exports(summary_df, links_df)
    _, availability_group_df, availability_reason_df = build_availability_summary(summary_df)
    archive_type_summary_df = build_archive_type_summary(summary_df)
    access_surface_summary_df = build_access_surface_summary(
        analysis_exports["video_catalog"],
    )
    access_regime_summary_df = build_access_regime_summary(
        summary_df,
        analysis_exports["video_catalog"],
    )
    theme_platform_summary_df = build_theme_platform_summary(
        analysis_exports["video_catalog"],
        top_n=None,
    )
    theme_archive_type_summary_df = build_theme_archive_type_summary(
        analysis_exports["video_catalog"],
        summary_df,
        top_n=None,
    )
    visibility_archive_type_summary_df = build_visibility_archive_type_summary(
        analysis_exports["summary_analysis"],
        top_n=None,
    )

    return {
        "analytic_summary": analysis_exports["summary_analysis"],
        "analytic_video_catalog": analysis_exports["video_catalog"],
        "visibility_summary": analysis_exports["visibility_summary"],
        "access_surface_summary": access_surface_summary_df,
        "access_regime_summary": access_regime_summary_df,
        "theme_summary": analysis_exports["theme_summary"],
        "theme_country": analysis_exports["theme_country_summary"],
        "availability_summary": availability_group_df,
        "availability_reasons": availability_reason_df,
        "archive_type_summary": archive_type_summary_df,
        "theme_platform": theme_platform_summary_df,
        "theme_archive_type": theme_archive_type_summary_df,
        "visibility_archive_type": visibility_archive_type_summary_df,
    }


def write_analysis_outputs(output_dir, output_files, summary_df, links_df):
    output_dir.mkdir(parents=True, exist_ok=True)
    analysis_frames = build_analysis_frames(summary_df, links_df)
    for key, dataframe in analysis_frames.items():
        rows, fieldnames = dataframe_to_rows(dataframe)
        save_csv(output_dir / output_files[key], rows, fieldnames)
    return analysis_frames


def build_analysis_extra_sheets(analysis_frames, sheet_titles=None):
    effective_titles = sheet_titles or ANALYTIC_SHEET_TITLES
    extra_sheets = []
    for key, title in effective_titles.items():
        dataframe = analysis_frames[key]
        rows, fieldnames = dataframe_to_rows(dataframe)
        extra_sheets.append(
            {
                "title": title,
                "rows": rows,
                "fieldnames": fieldnames,
            }
        )
    return extra_sheets


__all__ = [
    "ANALYTIC_SHEET_TITLES",
    "build_analysis_extra_sheets",
    "build_analysis_frames",
    "dataframe_to_rows",
    "write_analysis_outputs",
]
