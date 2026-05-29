from .analysis_exports import ANALYTIC_SHEET_TITLES
from .analysis_exports import build_analysis_extra_sheets
from .analysis_exports import build_analysis_frames
from .analysis_exports import write_analysis_outputs
from .output_files import AAMOD_OUTPUT_FILES


AAMOD_ANALYTIC_SHEET_TITLES = ANALYTIC_SHEET_TITLES


def write_aamod_analysis_outputs(output_dir, summary_df, links_df):
    return write_analysis_outputs(output_dir, AAMOD_OUTPUT_FILES, summary_df, links_df)


def build_aamod_analysis_extra_sheets(analysis_frames):
    return build_analysis_extra_sheets(analysis_frames, AAMOD_ANALYTIC_SHEET_TITLES)


def build_aamod_analysis_frames(summary_df, links_df):
    return build_analysis_frames(summary_df, links_df)


__all__ = [
    "AAMOD_ANALYTIC_SHEET_TITLES",
    "build_aamod_analysis_extra_sheets",
    "build_aamod_analysis_frames",
    "write_aamod_analysis_outputs",
]
