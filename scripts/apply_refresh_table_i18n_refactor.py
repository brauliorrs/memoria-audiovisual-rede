from __future__ import annotations

from pathlib import Path
import re


APP_PATH = Path("app/streamlit_app.py")
MODULE_PATH = Path("src/memoria_audiovisual/ui/refresh_table.py")
LOCALE_PATH = Path("src/memoria_audiovisual/locale_catalog.py")
TEST_PATH = Path("tests/test_refresh_table_locale_compatibility.py")


def refactor_app() -> None:
    app = APP_PATH.read_text(encoding="utf-8")
    import_anchor = "from memoria_audiovisual.ui.navigation import build_navigation_contract\n"
    import_line = "from memoria_audiovisual.ui.refresh_table import prepare_refresh_display_dataframe\n"
    if import_line not in app:
        if import_anchor not in app:
            raise RuntimeError("Navigation import anchor not found")
        app = app.replace(import_anchor, import_line + import_anchor, 1)

    pattern = re.compile(
        r"        refresh_display_df = refresh_status_df\.rename\(.*?"
        r"        st\.dataframe\(refresh_display_df, use_container_width=True, hide_index=True\)",
        re.DOTALL,
    )
    replacement = '''        refresh_column_labels = {
            "corpus": tr_key('overview.table.column.unidade_documental'),
            "category_label": tr_key('overview.table.column.categoria_analitica'),
            "coverage_level": tr_key('overview.table.column.escala_de_cobertura'),
            "scope": tr_key('overview.table.column.escopo'),
            "collection_completeness": tr_key('overview.table.column.completude_da_coleta'),
            "selection_limit": tr_key('overview.table.column.limite_tecnico'),
            "completeness_note": tr_key('overview.table.column.nota_de_completude'),
            "included_in_latest_cycle": tr_key('overview.table.column.incluida_na_ultima_rodada'),
            "latest_cycle_scope": tr_key('overview.table.column.escopo_da_ultima_rodada'),
            "latest_cycle_status": tr_key('overview.table.column.situacao_na_ultima_rodada'),
            "last_successful_cycle_at": tr_key('overview.table.column.ultima_rodada_bem_sucedida'),
            "last_snapshot_generated_at": tr_key('overview.table.column.ultima_observacao_registrada'),
            "source_status_date": tr_key('overview.table.column.status_da_fonte'),
            "observation_key": tr_key('overview.table.column.chave_de_observacao'),
            "days_since_last_observation": tr_key('overview.table.column.dias_desde_a_ultima_observacao'),
            "refresh_state": tr_key('overview.table.column.estado_de_atualizacao'),
            "refresh_state_reason": tr_key('overview.table.column.justificativa_metodologica'),
        }
        refresh_display_df = prepare_refresh_display_dataframe(
            refresh_status_df,
            column_labels=refresh_column_labels,
            format_yes_no=format_yes_no,
            format_cycle_status=format_cycle_status,
            format_timestamp=format_snapshot_timestamp,
        )
        st.dataframe(refresh_display_df, use_container_width=True, hide_index=True)'''

    app, count = pattern.subn(replacement, app, count=1)
    if count != 1:
        raise RuntimeError(f"Expected one refresh table block, replaced {count}")
    APP_PATH.write_text(app, encoding="utf-8")


def write_helper_module() -> None:
    MODULE_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODULE_PATH.write_text(
        '''from __future__ import annotations

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
''',
        encoding="utf-8",
    )


def restore_locale_catalog() -> None:
    LOCALE_PATH.write_text(
        '''from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DEFAULT_LANGUAGE = "pt"
SUPPORTED_LANGUAGES = ("pt", "en", "es")
LOCALE_DIR = Path(__file__).resolve().parent / "locales"


@lru_cache(maxsize=None)
def load_locale(language: str = DEFAULT_LANGUAGE) -> dict[str, str]:
    language = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    path = LOCALE_DIR / f"{language}.json"
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in payload.items()):
        raise ValueError(f"Invalid locale catalogue: {path}")
    return payload


def translate_key(key: str, language: str = DEFAULT_LANGUAGE, **kwargs) -> str:
    catalogue = load_locale(language)
    text = catalogue.get(key, key)
    return text.format(**kwargs) if kwargs else text


def validate_catalogues() -> dict[str, set[str]]:
    """Return missing keys for every active translation catalogue."""
    canonical = set(load_locale(DEFAULT_LANGUAGE))
    return {
        language: canonical - set(load_locale(language))
        for language in SUPPORTED_LANGUAGES
        if language != DEFAULT_LANGUAGE
    }
''',
        encoding="utf-8",
    )


def write_tests() -> None:
    TEST_PATH.write_text(
        '''import unittest

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
''',
        encoding="utf-8",
    )


def main() -> None:
    refactor_app()
    write_helper_module()
    restore_locale_catalog()
    write_tests()


if __name__ == "__main__":
    main()
