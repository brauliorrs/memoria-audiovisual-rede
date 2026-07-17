from .analysis_exports import ANALYTIC_SHEET_TITLES, build_analysis_extra_sheets, build_analysis_frames, write_analysis_outputs
from .output_files import EAFA_OUTPUT_FILES


EAFA_ANALYTIC_SHEET_TITLES = ANALYTIC_SHEET_TITLES


def write_eafa_analysis_outputs(output_dir, summary_df, links_df):
    return write_analysis_outputs(output_dir, EAFA_OUTPUT_FILES, summary_df, links_df)


def build_eafa_analysis_extra_sheets(analysis_frames):
    return build_analysis_extra_sheets(analysis_frames, EAFA_ANALYTIC_SHEET_TITLES)


def build_eafa_analysis_frames(summary_df, links_df):
    return build_analysis_frames(summary_df, links_df)


__all__ = [
    "EAFA_ANALYTIC_SHEET_TITLES",
    "build_eafa_analysis_extra_sheets",
    "build_eafa_analysis_frames",
    "write_eafa_analysis_outputs",
]
