from .analysis_exports import ANALYTIC_SHEET_TITLES
from .analysis_exports import build_analysis_extra_sheets
from .analysis_exports import build_analysis_frames
from .analysis_exports import write_analysis_outputs
from .output_files import DHM_OUTPUT_FILES


DHM_ANALYTIC_SHEET_TITLES = ANALYTIC_SHEET_TITLES


def write_dhm_analysis_outputs(output_dir, summary_df, links_df):
    return write_analysis_outputs(output_dir, DHM_OUTPUT_FILES, summary_df, links_df)


def build_dhm_analysis_extra_sheets(analysis_frames):
    return build_analysis_extra_sheets(analysis_frames, DHM_ANALYTIC_SHEET_TITLES)


def build_dhm_analysis_frames(summary_df, links_df):
    return build_analysis_frames(summary_df, links_df)


__all__ = [
    "DHM_ANALYTIC_SHEET_TITLES",
    "build_dhm_analysis_extra_sheets",
    "build_dhm_analysis_frames",
    "write_dhm_analysis_outputs",
]
