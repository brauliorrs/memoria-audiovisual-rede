from .analysis_exports import ANALYTIC_SHEET_TITLES
from .analysis_exports import build_analysis_extra_sheets
from .analysis_exports import build_analysis_frames
from .analysis_exports import dataframe_to_rows
from .analysis_exports import write_analysis_outputs
from .output_files import PPA_OUTPUT_FILES


PPA_ANALYTIC_SHEET_TITLES = ANALYTIC_SHEET_TITLES


def build_ppa_analysis_frames(summary_df, links_df):
    return build_analysis_frames(summary_df, links_df)


def write_ppa_analysis_outputs(output_dir, summary_df, links_df):
    return write_analysis_outputs(output_dir, PPA_OUTPUT_FILES, summary_df, links_df)


def build_ppa_analysis_extra_sheets(analysis_frames):
    return build_analysis_extra_sheets(analysis_frames, PPA_ANALYTIC_SHEET_TITLES)


__all__ = [
    "PPA_ANALYTIC_SHEET_TITLES",
    "build_ppa_analysis_extra_sheets",
    "build_ppa_analysis_frames",
    "dataframe_to_rows",
    "write_ppa_analysis_outputs",
]
