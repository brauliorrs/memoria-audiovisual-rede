from .analysis_exports import build_analysis_extra_sheets, write_analysis_outputs
from .output_files import LUCE_OUTPUT_FILES


def write_luce_analysis_outputs(output_dir, summary_df, links_df):
    return write_analysis_outputs(output_dir, LUCE_OUTPUT_FILES, summary_df, links_df)


def build_luce_analysis_extra_sheets(analysis_frames):
    return build_analysis_extra_sheets(analysis_frames)


__all__ = [
    "build_luce_analysis_extra_sheets",
    "write_luce_analysis_outputs",
]
