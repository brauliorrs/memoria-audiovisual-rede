from .analysis_exports import build_analysis_extra_sheets
from .analysis_exports import write_analysis_outputs
from .output_files import CSC_CINETECA_OUTPUT_FILES


def write_csc_cineteca_analysis_outputs(output_dir, summary_df, links_df):
    return write_analysis_outputs(output_dir, CSC_CINETECA_OUTPUT_FILES, summary_df, links_df)


def build_csc_cineteca_analysis_extra_sheets(analysis_frames):
    return build_analysis_extra_sheets(analysis_frames)


__all__ = [
    "build_csc_cineteca_analysis_extra_sheets",
    "write_csc_cineteca_analysis_outputs",
]
