import unittest

import pandas as pd

from memoria_audiovisual.locale_catalog import translate_key
from memoria_audiovisual.ui.refresh_table import prepare_refresh_display_dataframe


class RefreshTableDisplayContractTest(unittest.TestCase):
    def test_values_are_formatted_before_localized_rename(self):
        source = pd.DataFrame({
            "corpus": ["example"],
            "included_in_latest_cycle": [True],
            "latest_cycle_status": ["success"],
            "last_successful_cycle_at": ["2026-08-04T12:00:00Z"],
            "last_snapshot_generated_at": ["2026-08-04T12:30:00Z"],
        })
        labels = {
            "corpus": "Documentary unit",
            "included_in_latest_cycle": "Included in latest cycle",
            "latest_cycle_status": "Latest cycle status",
            "last_successful_cycle_at": "Last successful cycle",
            "last_snapshot_generated_at": "Last recorded observation",
        }
        result = prepare_refresh_display_dataframe(
            source,
            column_labels=labels,
            format_yes_no=lambda value: "yes" if value else "no",
            format_cycle_status=lambda value: f"status:{value}",
            format_timestamp=lambda value: f"time:{value}",
        )
        self.assertEqual(result.columns.tolist(), list(labels.values()))
        self.assertEqual(result.loc[0, "Included in latest cycle"], "yes")
        self.assertEqual(result.loc[0, "Latest cycle status"], "status:success")
        self.assertEqual(result.loc[0, "Last successful cycle"], "time:2026-08-04T12:00:00Z")

    def test_missing_optional_columns_do_not_raise_key_error(self):
        source = pd.DataFrame({"corpus": ["example"]})
        result = prepare_refresh_display_dataframe(
            source,
            column_labels={"corpus": "Unidad documental", "included_in_latest_cycle": "Incluida"},
            format_yes_no=str,
            format_cycle_status=str,
            format_timestamp=str,
        )
        self.assertEqual(result.columns.tolist(), ["Unidad documental"])

    def test_translation_catalogue_is_not_overridden_by_legacy_labels(self):
        key = "overview.table.column.incluida_na_ultima_rodada"
        self.assertNotEqual(translate_key(key, "pt"), translate_key(key, "en"))
        self.assertNotEqual(translate_key(key, "pt"), translate_key(key, "es"))


if __name__ == "__main__":
    unittest.main()
