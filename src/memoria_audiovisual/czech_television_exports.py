from .analysis_exports import ANALYTIC_SHEET_TITLES
from .analysis_exports import build_analysis_extra_sheets
from .analysis_exports import build_analysis_frames
from .analysis_exports import write_analysis_outputs
from .output_files import CZECH_TELEVISION_OUTPUT_FILES


CZECH_TELEVISION_ANALYTIC_SHEET_TITLES = ANALYTIC_SHEET_TITLES


def write_czech_television_analysis_outputs(output_dir, summary_df, links_df):
    return write_analysis_outputs(output_dir, CZECH_TELEVISION_OUTPUT_FILES, summary_df, links_df)


def build_czech_television_analysis_extra_sheets(analysis_frames):
    return build_analysis_extra_sheets(analysis_frames, CZECH_TELEVISION_ANALYTIC_SHEET_TITLES)


def build_czech_television_analysis_frames(summary_df, links_df):
    return build_analysis_frames(summary_df, links_df)


__all__ = [
    "CZECH_TELEVISION_ANALYTIC_SHEET_TITLES",
    "build_czech_television_analysis_extra_sheets",
    "build_czech_television_analysis_frames",
    "write_czech_television_analysis_outputs",
]
