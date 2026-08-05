"""Localized, progressively loaded scientific-infrastructure interface."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from memoria_audiovisual.scientific_infrastructure import (
    ScientificInfrastructureLoader,
    build_default_registry,
)


COPY = {
    "pt": {
        "title": "Infraestrutura científica",
        "caption": "Consulte o que a plataforma mede, como calcula, os resultados materializados e a proveniência dos artefatos.",
        "section": "Escolha a seção",
        "indicators": "Indicadores",
        "methodology": "Metodologia",
        "status": "Estado operacional",
        "results": "Resultados e snapshots",
        "provenance": "Proveniência e integridade",
        "loading": "Carregando a seção selecionada...",
        "registered": "Indicadores registrados",
        "dimensions": "Dimensões analíticas",
        "version": "Versão",
        "state": "Situação",
        "question": "Pergunta científica",
        "rationale": "Fundamentação científica",
        "interpretation": "Interpretação",
        "not_measure": "O que não mede",
        "evidence_requirements": "Requisitos de evidência",
        "methodology_reference": "Referência metodológica",
        "expected_range": "Intervalo esperado",
        "formula": "Fórmula",
        "definition": "Definição",
        "source": "Fonte de dados",
        "limitations": "Limitações",
        "indicator": "Indicador",
        "method_available": "Metodologia disponível",
        "result_available": "Resultado materializado",
        "value": "Valor",
        "available": "Disponível",
        "unavailable": "Ausente ou inválido",
        "product": "Produto",
        "path": "Caminho",
        "error": "Erro",
        "no_data": "Os artefatos desta seção não estão disponíveis nesta execução.",
        "snapshot": "Snapshot analítico",
        "ledger": "Transações no ledger",
        "record_types": "Tipos de registro",
        "records": "Registros",
        "language_note": "A interface lê os registros científicos existentes e não recalcula indicadores.",
    },
    "en": {
        "title": "Scientific infrastructure",
        "caption": "Explore what the platform measures, how calculations are defined, materialized results, and artifact provenance.",
        "section": "Choose a section",
        "indicators": "Indicators",
        "methodology": "Methodology",
        "status": "Operational status",
        "results": "Results and snapshots",
        "provenance": "Provenance and integrity",
        "loading": "Loading the selected section...",
        "registered": "Registered indicators",
        "dimensions": "Analytical dimensions",
        "version": "Version",
        "state": "Status",
        "question": "Scientific question",
        "rationale": "Scientific rationale",
        "interpretation": "Interpretation",
        "not_measure": "What it does not measure",
        "evidence_requirements": "Evidence requirements",
        "methodology_reference": "Methodology reference",
        "expected_range": "Expected range",
        "formula": "Formula",
        "definition": "Definition",
        "source": "Data source",
        "limitations": "Limitations",
        "indicator": "Indicator",
        "method_available": "Methodology available",
        "result_available": "Materialized result",
        "value": "Value",
        "available": "Available",
        "unavailable": "Missing or invalid",
        "product": "Product",
        "path": "Path",
        "error": "Error",
        "no_data": "The artifacts for this section are not available in this run.",
        "snapshot": "Analytical snapshot",
        "ledger": "Ledger transactions",
        "record_types": "Record types",
        "records": "Records",
        "language_note": "The interface reads existing scientific records and does not recalculate indicators.",
    },
    "es": {
        "title": "Infraestructura científica",
        "caption": "Consulte qué mide la plataforma, cómo se calculan los indicadores, los resultados materializados y la procedencia de los artefactos.",
        "section": "Elija una sección",
        "indicators": "Indicadores",
        "methodology": "Metodología",
        "status": "Estado operativo",
        "results": "Resultados y snapshots",
        "provenance": "Procedencia e integridad",
        "loading": "Cargando la sección seleccionada...",
        "registered": "Indicadores registrados",
        "dimensions": "Dimensiones analíticas",
        "version": "Versión",
        "state": "Estado",
        "question": "Pregunta científica",
        "rationale": "Fundamentación científica",
        "interpretation": "Interpretación",
        "not_measure": "Lo que no mide",
        "evidence_requirements": "Requisitos de evidencia",
        "methodology_reference": "Referencia metodológica",
        "expected_range": "Intervalo esperado",
        "formula": "Fórmula",
        "definition": "Definición",
        "source": "Fuente de datos",
        "limitations": "Limitaciones",
        "indicator": "Indicador",
        "method_available": "Metodología disponible",
        "result_available": "Resultado materializado",
        "value": "Valor",
        "available": "Disponible",
        "unavailable": "Ausente o inválido",
        "product": "Producto",
        "path": "Ruta",
        "error": "Error",
        "no_data": "Los artefactos de esta sección no están disponibles en esta ejecución.",
        "snapshot": "Snapshot analítico",
        "ledger": "Transacciones en el ledger",
        "record_types": "Tipos de registro",
        "records": "Registros",
        "language_note": "La interfaz lee los registros científicos existentes y no recalcula indicadores.",
    },
}


def _lang(language: str) -> str:
    code = (language or "pt").lower()
    if code.startswith("en"):
        return "en"
    if code.startswith("es"):
        return "es"
    return "pt"


def _copy(language: str) -> dict[str, str]:
    return COPY[_lang(language)]


def _as_list(value: object) -> list[Any]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _format_list(value: object) -> str:
    values = [str(item) for item in _as_list(value) if str(item).strip()]
    return "; ".join(values) if values else "—"


def _results(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    content = payload.get("content")
    if isinstance(content, dict):
        nested = _results(content)
        if nested:
            return nested
    for key in ("indicators", "results", "indicator_results"):
        rows = payload.get(key)
        if isinstance(rows, list):
            return [item for item in rows if isinstance(item, dict)]
    run = payload.get("run")
    return _results(run) if isinstance(run, dict) else []


def _artifact_table(artifacts: dict[str, Any], text: dict[str, str]) -> pd.DataFrame:
    return pd.DataFrame([
        {
            text["product"]: key,
            text["state"]: text["available"] if artifact.available else text["unavailable"],
            text["path"]: str(artifact.path),
            text["error"]: artifact.error or "—",
        }
        for key, artifact in artifacts.items()
    ])


def _loader(base_dir: str | Path) -> ScientificInfrastructureLoader:
    return ScientificInfrastructureLoader(build_default_registry(Path(base_dir)))


def _render_indicators(base_dir: str | Path, text: dict[str, str]) -> None:
    artifact = _loader(base_dir).load_static()["indicator_registry"]
    payload = artifact.payload if isinstance(artifact.payload, dict) else {}
    indicators = [item for item in payload.get("indicators", []) if isinstance(item, dict)]
    if not indicators:
        st.warning(text["no_data"])
        return
    dimensions = {str(item.get("dimension", "")) for item in indicators if item.get("dimension")}
    cols = st.columns(2)
    cols[0].metric(text["registered"], len(indicators))
    cols[1].metric(text["dimensions"], len(dimensions))
    for item in indicators:
        title = str(item.get("title") or item.get("indicator_id") or text["indicator"])
        with st.expander(title, expanded=False):
            st.markdown(f"**{text['version']}:** {item.get('indicator_version', '—')}")
            st.markdown(f"**{text['state']}:** {item.get('status', '—')}")
            st.markdown(f"**{text['expected_range']}:** {item.get('expected_range', '—')}")
            st.markdown(f"**{text['question']}:** {item.get('scientific_question', '—')}")
            st.markdown(f"**{text['rationale']}:** {item.get('scientific_rationale', '—')}")
            st.markdown(f"**{text['interpretation']}:** {item.get('interpretation', '—')}")
            st.markdown(f"**{text['not_measure']}:** {_format_list(item.get('does_not_measure'))}")
            st.markdown(
                f"**{text['evidence_requirements']}:** "
                f"{_format_list(item.get('evidence_requirements'))}"
            )
            st.caption(
                f"{text['methodology_reference']}: "
                f"{item.get('methodology_reference', '—')}"
            )


def _render_methodology(base_dir: str | Path, text: dict[str, str]) -> None:
    artifact = _loader(base_dir).load_static()["methodology_registry"]
    payload = artifact.payload if isinstance(artifact.payload, dict) else {}
    rows = [item for item in payload.get("methodologies", []) if isinstance(item, dict)]
    if not rows:
        st.warning(text["no_data"])
        return
    for item in rows:
        with st.expander(str(item.get("indicator_id", text["indicator"])), expanded=False):
            st.markdown(f"**{text['definition']}:** {item.get('definition', '—')}")
            st.markdown(f"**{text['formula']}**")
            st.code(str(item.get("formula", "—")), language=None)
            st.markdown(f"**{text['source']}:** `{item.get('source', '—')}`")
            st.markdown(f"**{text['limitations']}:** {_format_list(item.get('limitations'))}")


def _render_status(base_dir: str | Path, text: dict[str, str]) -> None:
    loader = _loader(base_dir)
    static = loader.load_static()
    catalog = static["indicator_registry"].payload
    methods = static["methodology_registry"].payload
    indicators = catalog.get("indicators", []) if isinstance(catalog, dict) else []
    methodologies = methods.get("methodologies", []) if isinstance(methods, dict) else []
    method_ids = {str(item.get("indicator_id")) for item in methodologies if isinstance(item, dict)}
    result_artifact = static.get("indicator_results_registry")
    result_rows = _results(result_artifact.payload) if result_artifact and result_artifact.available else []
    result_ids = {str(item.get("indicator_id") or item.get("id")) for item in result_rows}
    rows = [{
        text["indicator"]: item.get("title") or item.get("indicator_id"),
        text["method_available"]: text["available"] if str(item.get("indicator_id")) in method_ids else text["unavailable"],
        text["result_available"]: text["available"] if str(item.get("indicator_id")) in result_ids else text["unavailable"],
    } for item in indicators if isinstance(item, dict)]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_results(base_dir: str | Path, text: dict[str, str]) -> None:
    loader = _loader(base_dir)
    static = loader.load_static()
    artifact = static.get("indicator_results_registry")
    result_rows = _results(artifact.payload) if artifact and artifact.available else []
    if result_rows:
        rows = [{
            text["indicator"]: item.get("title") or item.get("indicator_id"),
            text["value"]: item.get("value", "—"),
            text["state"]: item.get("status", "—"),
            text["version"]: item.get("indicator_version", "—"),
        } for item in result_rows]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        return
    snapshot = loader.load_latest_analytics_snapshot()
    if not snapshot:
        st.warning(text["no_data"])
        return
    st.dataframe(_artifact_table(snapshot, text), use_container_width=True, hide_index=True)


def _render_provenance(base_dir: str | Path, text: dict[str, str]) -> None:
    loader = _loader(base_dir)
    governance = loader.load_governance()
    if not governance:
        st.warning(text["no_data"])
        return
    st.dataframe(_artifact_table(governance, text), use_container_width=True, hide_index=True)
    ledger = governance.get("ledger")
    if ledger and ledger.available and isinstance(ledger.payload, list):
        record_types = set()
        for row in ledger.payload:
            if isinstance(row, dict):
                record_types.add(str(row.get("record_type", "—")))
        cols = st.columns(2)
        cols[0].metric(text["ledger"], len(ledger.payload))
        cols[1].metric(text["record_types"], len(record_types))


def render_scientific_infrastructure_lazy(base_dir: str | Path, language: str = "pt") -> None:
    """Render only the selected scientific-infrastructure section."""
    text = _copy(language)
    st.markdown(f"## {text['title']}")
    st.caption(text["caption"])

    section_keys = ["indicators", "methodology", "status", "results", "provenance"]
    selected_label = st.radio(
        text["section"],
        options=[text[key] for key in section_keys],
        horizontal=False,
        key=f"scientific-infrastructure-section-{_lang(language)}",
    )
    selected = section_keys[[text[key] for key in section_keys].index(selected_label)]

    with st.spinner(text["loading"]):
        if selected == "indicators":
            _render_indicators(base_dir, text)
        elif selected == "methodology":
            _render_methodology(base_dir, text)
        elif selected == "status":
            _render_status(base_dir, text)
        elif selected == "results":
            _render_results(base_dir, text)
        else:
            _render_provenance(base_dir, text)
    st.caption(text["language_note"])
