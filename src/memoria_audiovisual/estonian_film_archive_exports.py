from .analysis_exports import build_analysis_extra_sheets
from .analysis_exports import write_analysis_outputs
from .output_files import ESTONIAN_FILM_ARCHIVE_OUTPUT_FILES


def write_estonian_film_archive_analysis_outputs(output_dir, summary_df, links_df):
    return write_analysis_outputs(output_dir, ESTONIAN_FILM_ARCHIVE_OUTPUT_FILES, summary_df, links_df)


def build_estonian_film_archive_analysis_extra_sheets(analysis_frames):
    return build_analysis_extra_sheets(analysis_frames)


__all__ = [
    "build_estonian_film_archive_analysis_extra_sheets",
    "write_estonian_film_archive_analysis_outputs",
]
