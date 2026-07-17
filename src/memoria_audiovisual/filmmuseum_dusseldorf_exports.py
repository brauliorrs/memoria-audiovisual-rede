from .analysis_exports import build_analysis_extra_sheets
from .analysis_exports import write_analysis_outputs
from .output_files import FILMMUSEUM_DUSSELDORF_OUTPUT_FILES


def write_filmmuseum_dusseldorf_analysis_outputs(output_dir, summary_df, links_df):
    return write_analysis_outputs(output_dir, FILMMUSEUM_DUSSELDORF_OUTPUT_FILES, summary_df, links_df)


def build_filmmuseum_dusseldorf_analysis_extra_sheets(analysis_frames):
    return build_analysis_extra_sheets(analysis_frames)


__all__ = [
    "build_filmmuseum_dusseldorf_analysis_extra_sheets",
    "write_filmmuseum_dusseldorf_analysis_outputs",
]
