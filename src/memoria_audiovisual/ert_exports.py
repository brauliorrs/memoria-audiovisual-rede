from .analysis_exports import ANALYTIC_SHEET_TITLES, build_analysis_extra_sheets, build_analysis_frames, write_analysis_outputs
from .output_files import ERT_OUTPUT_FILES


ERT_ANALYTIC_SHEET_TITLES = ANALYTIC_SHEET_TITLES


def write_ert_analysis_outputs(output_dir, summary_df, links_df):
    return write_analysis_outputs(output_dir, ERT_OUTPUT_FILES, summary_df, links_df)


def build_ert_analysis_extra_sheets(analysis_frames):
    return build_analysis_extra_sheets(analysis_frames, ERT_ANALYTIC_SHEET_TITLES)


def build_ert_analysis_frames(summary_df, links_df):
    return build_analysis_frames(summary_df, links_df)


__all__ = [
    "ERT_ANALYTIC_SHEET_TITLES",
    "build_ert_analysis_extra_sheets",
    "build_ert_analysis_frames",
    "write_ert_analysis_outputs",
]
