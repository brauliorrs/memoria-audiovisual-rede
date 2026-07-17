from .analysis_exports import ANALYTIC_SHEET_TITLES
from .analysis_exports import build_analysis_extra_sheets
from .analysis_exports import build_analysis_frames
from .analysis_exports import write_analysis_outputs
from .output_files import DEUTSCHE_KINEMATHEK_OUTPUT_FILES


DEUTSCHE_KINEMATHEK_ANALYTIC_SHEET_TITLES = ANALYTIC_SHEET_TITLES


def write_deutsche_kinemathek_analysis_outputs(output_dir, summary_df, links_df):
    return write_analysis_outputs(output_dir, DEUTSCHE_KINEMATHEK_OUTPUT_FILES, summary_df, links_df)


def build_deutsche_kinemathek_analysis_extra_sheets(analysis_frames):
    return build_analysis_extra_sheets(analysis_frames, DEUTSCHE_KINEMATHEK_ANALYTIC_SHEET_TITLES)


def build_deutsche_kinemathek_analysis_frames(summary_df, links_df):
    return build_analysis_frames(summary_df, links_df)


__all__ = [
    "DEUTSCHE_KINEMATHEK_ANALYTIC_SHEET_TITLES",
    "build_deutsche_kinemathek_analysis_extra_sheets",
    "build_deutsche_kinemathek_analysis_frames",
    "write_deutsche_kinemathek_analysis_outputs",
]
