from .analysis_exports import build_analysis_extra_sheets, write_analysis_outputs
from .output_files import CCMA_OUTPUT_FILES


def write_ccma_analysis_outputs(output_dir, summary_df, links_df):
    return write_analysis_outputs(output_dir, CCMA_OUTPUT_FILES, summary_df, links_df)


def build_ccma_analysis_extra_sheets(analysis_frames):
    return build_analysis_extra_sheets(analysis_frames)


__all__ = [
    "build_ccma_analysis_extra_sheets",
    "write_ccma_analysis_outputs",
]
