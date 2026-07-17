from .analysis_exports import build_analysis_extra_sheets, write_analysis_outputs
from .output_files import CINEMEMOIRE_OUTPUT_FILES


def write_cinememoire_analysis_outputs(output_dir, summary_df, links_df):
    return write_analysis_outputs(output_dir, CINEMEMOIRE_OUTPUT_FILES, summary_df, links_df)


def build_cinememoire_analysis_extra_sheets(analysis_frames):
    return build_analysis_extra_sheets(analysis_frames)


__all__ = [
    "build_cinememoire_analysis_extra_sheets",
    "write_cinememoire_analysis_outputs",
]
