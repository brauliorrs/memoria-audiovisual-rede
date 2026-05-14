from .analysis_exports import ANALYTIC_SHEET_TITLES
from .analysis_exports import build_analysis_extra_sheets
from .analysis_exports import build_analysis_frames
from .analysis_exports import dataframe_to_rows
from .analysis_exports import write_analysis_outputs
from .output_files import APE_OUTPUT_FILES


APE_ANALYTIC_SHEET_TITLES = ANALYTIC_SHEET_TITLES


def build_ape_analysis_frames(summary_df, links_df):
    return build_analysis_frames(summary_df, links_df)


def write_ape_analysis_outputs(output_dir, summary_df, links_df):
    return write_analysis_outputs(output_dir, APE_OUTPUT_FILES, summary_df, links_df)


def build_ape_analysis_extra_sheets(analysis_frames):
    return build_analysis_extra_sheets(analysis_frames, APE_ANALYTIC_SHEET_TITLES)


__all__ = [
    "APE_ANALYTIC_SHEET_TITLES",
    "build_ape_analysis_extra_sheets",
    "build_ape_analysis_frames",
    "dataframe_to_rows",
    "write_ape_analysis_outputs",
]
