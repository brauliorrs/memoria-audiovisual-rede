"""Compatibility entry point for the scientific-infrastructure interface.

The public renderer delegates to the localized, progressively loaded module.
Small data helpers remain here because they are useful to tests and other
callers without coupling them to Streamlit rendering details.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import streamlit as st

from memoria_audiovisual.i18n import DEFAULT_LANGUAGE, language_code_from_label
from memoria_audiovisual.ui.operational_baseline import (
    render_operational_baseline_panel,
)
from memoria_audiovisual.ui.scientific_infrastructure_lazy import (
    render_scientific_infrastructure_lazy,
)
from memoria_audiovisual.ui.t2a_methodology import render_t2a_methodology_panel


def _indicator_results(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    content = payload.get("content")
    if isinstance(content, dict):
        nested = _indicator_results(content)
        if nested:
            return nested
    for key in ("indicators", "results", "indicator_results"):
        rows = payload.get(key)
        if isinstance(rows, list):
            return [item for item in rows if isinstance(item, dict)]
    run = payload.get("run")
    return _indicator_results(run) if isinstance(run, dict) else []


def _status_label(structure: bool, result: bool) -> str:
    if result:
        return "Resultado materializado"
    if structure:
        return "Resultado não disponível"
    return "Não disponível"


def _extract_result_value(row: dict[str, Any]) -> object:
    for key in ("value", "score", "percentage", "result"):
        if key in row and not isinstance(row[key], (dict, list)):
            return row[key]
    return "—"


def build_operational_status(
    indicators: Iterable[dict[str, Any]],
    methodologies: Iterable[dict[str, Any]],
    result_rows: Iterable[dict[str, Any]],
) -> pd.DataFrame:
    methodology_ids = {str(item.get("indicator_id")) for item in methodologies}
    results_by_id = {
        str(item.get("indicator_id") or item.get("id")): item
        for item in result_rows
        if item.get("indicator_id") or item.get("id")
    }
    rows = []
    for indicator in indicators:
        indicator_id = str(indicator.get("indicator_id", ""))
        result = results_by_id.get(indicator_id)
        rows.append(
            {
                "Indicador": indicator.get("title", indicator_id),
                "Versão": indicator.get("indicator_version", "—"),
                "Registro": "Disponível",
                "Metodologia": "Disponível" if indicator_id in methodology_ids else "Não localizada",
                "Resultado": "Materializado" if result else "Não disponível",
                "Valor": _extract_result_value(result) if result else "—",
                "Situação": _status_label(True, bool(result)),
            }
        )
    return pd.DataFrame(rows)


def _active_language() -> str:
    selected = st.session_state.get("interface_language")
    if isinstance(selected, str):
        try:
            return language_code_from_label(selected)
        except (KeyError, ValueError):
            pass
    return DEFAULT_LANGUAGE


def render_scientific_infrastructure(
    base_dir: str | Path,
    *,
    language: str | None = None,
) -> None:
    """Render only the selected section in the explicitly active language."""
    active_language = language or _active_language()
    render_scientific_infrastructure_lazy(
        base_dir,
        language=active_language,
    )
    render_operational_baseline_panel(
        base_dir,
        language=active_language,
    )
    render_t2a_methodology_panel(language=active_language)


__all__ = [
    "_indicator_results",
    "build_operational_status",
    "render_scientific_infrastructure",
]
