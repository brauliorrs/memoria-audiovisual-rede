from .analysis_exports import build_analysis_extra_sheets
from .analysis_exports import write_analysis_outputs
from .output_files import IFI_ARCHIVE_PLAYER_OUTPUT_FILES


def write_ifi_archive_player_analysis_outputs(output_dir, summary_df, links_df):
    return write_analysis_outputs(
        output_dir,
        IFI_ARCHIVE_PLAYER_OUTPUT_FILES,
        summary_df,
        links_df,
    )


def build_ifi_archive_player_analysis_extra_sheets(analysis_frames):
    return build_analysis_extra_sheets(analysis_frames)


__all__ = [
    "build_ifi_archive_player_analysis_extra_sheets",
    "write_ifi_archive_player_analysis_outputs",
]
