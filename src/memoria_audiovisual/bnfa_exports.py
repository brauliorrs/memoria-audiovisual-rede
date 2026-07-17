from .analysis_exports import ANALYTIC_SHEET_TITLES
from .analysis_exports import build_analysis_extra_sheets
from .analysis_exports import build_analysis_frames
from .analysis_exports import write_analysis_outputs
from .output_files import BNFA_OUTPUT_FILES


BNFA_ANALYTIC_SHEET_TITLES = ANALYTIC_SHEET_TITLES


def write_bnfa_analysis_outputs(output_dir, summary_df, links_df):
    return write_analysis_outputs(output_dir, BNFA_OUTPUT_FILES, summary_df, links_df)


def build_bnfa_analysis_extra_sheets(analysis_frames):
    return build_analysis_extra_sheets(analysis_frames, BNFA_ANALYTIC_SHEET_TITLES)


def build_bnfa_analysis_frames(summary_df, links_df):
    return build_analysis_frames(summary_df, links_df)


__all__ = [
    "BNFA_ANALYTIC_SHEET_TITLES",
    "build_bnfa_analysis_extra_sheets",
    "build_bnfa_analysis_frames",
    "write_bnfa_analysis_outputs",
]
