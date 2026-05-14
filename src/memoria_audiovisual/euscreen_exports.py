from .analysis_exports import ANALYTIC_SHEET_TITLES
from .analysis_exports import build_analysis_extra_sheets
from .analysis_exports import build_analysis_frames
from .analysis_exports import dataframe_to_rows
from .analysis_exports import write_analysis_outputs
from .output_files import EUSCREEN_OUTPUT_FILES


EUSCREEN_ANALYTIC_SHEET_TITLES = ANALYTIC_SHEET_TITLES


def build_euscreen_analysis_frames(summary_df, links_df):
    return build_analysis_frames(summary_df, links_df)


def write_euscreen_analysis_outputs(output_dir, summary_df, links_df):
    return write_analysis_outputs(output_dir, EUSCREEN_OUTPUT_FILES, summary_df, links_df)


def build_euscreen_analysis_extra_sheets(analysis_frames):
    return build_analysis_extra_sheets(analysis_frames, EUSCREEN_ANALYTIC_SHEET_TITLES)


__all__ = [
    "EUSCREEN_ANALYTIC_SHEET_TITLES",
    "build_euscreen_analysis_extra_sheets",
    "build_euscreen_analysis_frames",
    "dataframe_to_rows",
    "write_euscreen_analysis_outputs",
]
