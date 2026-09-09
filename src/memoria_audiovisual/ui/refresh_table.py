from __future__ import annotations

from collections.abc import Callable, Mapping

import pandas as pd


def prepare_refresh_display_dataframe(
    refresh_status_df: pd.DataFrame,
    *,
    column_labels: Mapping[str, str],
    format_yes_no: Callable[[object], object],
    format_cycle_status: Callable[[object], object],
    format_timestamp: Callable[[object], object],
) -> pd.DataFrame:
    """Format stable internal columns, then apply localized display labels.

    Translated labels are presentation metadata only. They are never used to
    identify source columns. Missing optional columns are ignored so historical
    or partial snapshots remain displayable without raising ``KeyError``.
    """
    if refresh_status_df is None:
        return pd.DataFrame()

    display_df = refresh_status_df.copy()
    formatters = {
        "included_in_latest_cycle": format_yes_no,
        "latest_cycle_status": format_cycle_status,
        "last_successful_cycle_at": format_timestamp,
        "last_snapshot_generated_at": format_timestamp,
    }
    for column, formatter in formatters.items():
        if column in display_df.columns:
            display_df[column] = display_df[column].map(formatter)

    applicable_labels = {
        internal_name: display_label
        for internal_name, display_label in column_labels.items()
        if internal_name in display_df.columns
    }
    return display_df.rename(columns=applicable_labels)
