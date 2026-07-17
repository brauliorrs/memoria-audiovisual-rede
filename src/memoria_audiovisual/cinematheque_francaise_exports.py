from .analysis_exports import build_analysis_extra_sheets
from .analysis_exports import write_analysis_outputs
from .output_files import CINEMATHEQUE_FRANCAISE_OUTPUT_FILES


def write_cinematheque_francaise_analysis_outputs(output_dir, summary_df, links_df):
    return write_analysis_outputs(output_dir, CINEMATHEQUE_FRANCAISE_OUTPUT_FILES, summary_df, links_df)


def build_cinematheque_francaise_analysis_extra_sheets(analysis_frames):
    return build_analysis_extra_sheets(analysis_frames)


__all__ = [
    "build_cinematheque_francaise_analysis_extra_sheets",
    "write_cinematheque_francaise_analysis_outputs",
]
