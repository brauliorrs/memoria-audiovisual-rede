from .analysis_exports import build_analysis_extra_sheets
from .analysis_exports import write_analysis_outputs
from .output_files import FILMOTECA_VASCA_OUTPUT_FILES


def write_filmoteca_vasca_analysis_outputs(output_dir, summary_df, links_df):
    return write_analysis_outputs(output_dir, FILMOTECA_VASCA_OUTPUT_FILES, summary_df, links_df)


def build_filmoteca_vasca_analysis_extra_sheets(analysis_frames):
    return build_analysis_extra_sheets(analysis_frames)


__all__ = [
    "build_filmoteca_vasca_analysis_extra_sheets",
    "write_filmoteca_vasca_analysis_outputs",
]
