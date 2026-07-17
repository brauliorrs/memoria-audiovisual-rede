from .analysis_exports import ANALYTIC_SHEET_TITLES
from .analysis_exports import build_analysis_extra_sheets
from .analysis_exports import build_analysis_frames
from .analysis_exports import write_analysis_outputs
from .output_files import BARCH_OUTPUT_FILES


BARCH_ANALYTIC_SHEET_TITLES = ANALYTIC_SHEET_TITLES


def write_barch_analysis_outputs(output_dir, summary_df, links_df):
    return write_analysis_outputs(output_dir, BARCH_OUTPUT_FILES, summary_df, links_df)


def build_barch_analysis_extra_sheets(analysis_frames):
    return build_analysis_extra_sheets(analysis_frames, BARCH_ANALYTIC_SHEET_TITLES)


def build_barch_analysis_frames(summary_df, links_df):
    return build_analysis_frames(summary_df, links_df)


__all__ = [
    "BARCH_ANALYTIC_SHEET_TITLES",
    "build_barch_analysis_extra_sheets",
    "build_barch_analysis_frames",
    "write_barch_analysis_outputs",
]
