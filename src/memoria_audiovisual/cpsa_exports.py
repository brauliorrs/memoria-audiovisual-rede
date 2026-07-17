from .analysis_exports import build_analysis_extra_sheets
from .analysis_exports import write_analysis_outputs
from .output_files import CPSA_OUTPUT_FILES


def write_cpsa_analysis_outputs(output_dir, summary_df, links_df):
    return write_analysis_outputs(output_dir, CPSA_OUTPUT_FILES, summary_df, links_df)


def build_cpsa_analysis_extra_sheets(analysis_frames):
    return build_analysis_extra_sheets(analysis_frames)


__all__ = [
    "build_cpsa_analysis_extra_sheets",
    "write_cpsa_analysis_outputs",
]
