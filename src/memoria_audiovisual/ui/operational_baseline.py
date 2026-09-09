"""Apresentação localizada do baseline operacional oficial."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import pandas as pd
import streamlit as st

from memoria_audiovisual.scientific_infrastructure import (
    ArtifactState,
    LoadedArtifact,
    ScientificInfrastructureLoader,
    build_default_registry,
)


COPY = {
    "pt": {
        "results_section": "Resultados e snapshots",
        "title": "Baseline operacional oficial",
        "caption": (
            "Resultados produzidos pela execução operacional dos 55 corpora ativos, "
            "separados do snapshot científico de referência."
        ),
        "pending": (
            "O baseline operacional ainda não foi materializado nesta versão. "
            "Essa ausência não constitui resultado empírico negativo."
        ),
        "invalid": (
            "O ponteiro ou o manifesto do baseline operacional está ausente ou inválido. "
            "Os resultados operacionais não serão apresentados."
        ),
        "snapshot": "Snapshot",
        "corpora": "Corpora ativos",
        "indicators": "Indicadores",
        "t1_failures": "Ocorrências no T1",
        "indicator": "Indicador",
        "value": "Valor",
        "status": "Situação",
        "version": "Versão",
        "integrity": "Integridade e proveniência",
        "manifest": "Manifesto imutável",
        "manifest_hash": "Hash do manifesto",
        "pipeline_commit": "Commit do pipeline",
        "generated_at": "Gerado em",
        "ai_note": (
            "Este baseline foi calculado com as tarefas experimentais de IA desligadas; "
            "a IA não integra seus numeradores, denominadores ou resultados oficiais."
        ),
        "no_results": "O manifesto existe, mas os resultados analíticos não estão utilizáveis.",
    },
    "en": {
        "results_section": "Results and snapshots",
        "title": "Official operational baseline",
        "caption": (
            "Results produced by the operational run of the 55 active corpora, "
            "kept separate from the scientific reference snapshot."
        ),
        "pending": (
            "The operational baseline has not yet been materialized in this version. "
            "Its absence is not an empirical negative result."
        ),
        "invalid": (
            "The operational baseline pointer or manifest is missing or invalid. "
            "Operational results will not be displayed."
        ),
        "snapshot": "Snapshot",
        "corpora": "Active corpora",
        "indicators": "Indicators",
        "t1_failures": "T1 occurrences",
        "indicator": "Indicator",
        "value": "Value",
        "status": "Status",
        "version": "Version",
        "integrity": "Integrity and provenance",
        "manifest": "Immutable manifest",
        "manifest_hash": "Manifest hash",
        "pipeline_commit": "Pipeline commit",
        "generated_at": "Generated at",
        "ai_note": (
            "This baseline was calculated with experimental AI tasks disabled; "
            "AI is not part of its official numerators, denominators, or results."
        ),
        "no_results": "The manifest exists, but the analytical results are not usable.",
    },
    "es": {
        "results_section": "Resultados y snapshots",
        "title": "Baseline operativo oficial",
        "caption": (
            "Resultados producidos por la ejecución operativa de los 55 corpus activos, "
            "separados del snapshot científico de referencia."
        ),
        "pending": (
            "El baseline operativo todavía no se ha materializado en esta versión. "
            "Esta ausencia no constituye un resultado empírico negativo."
        ),
        "invalid": (
            "El puntero o el manifiesto del baseline operativo está ausente o no es válido. "
            "No se mostrarán resultados operativos."
        ),
        "snapshot": "Snapshot",
        "corpora": "Corpus activos",
        "indicators": "Indicadores",
        "t1_failures": "Incidencias en T1",
        "indicator": "Indicador",
        "value": "Valor",
        "status": "Estado",
        "version": "Versión",
        "integrity": "Integridad y procedencia",
        "manifest": "Manifiesto inmutable",
        "manifest_hash": "Hash del manifiesto",
        "pipeline_commit": "Commit del pipeline",
        "generated_at": "Generado en",
        "ai_note": (
            "Este baseline fue calculado con las tareas experimentales de IA desactivadas; "
            "la IA no integra sus numeradores, denominadores ni resultados oficiales."
        ),
        "no_results": "El manifiesto existe, pero los resultados analíticos no son utilizables.",
    },
}


def _lang(language: str) -> str:
    code = (language or "pt").lower()
    if code.startswith("en"):
        return "en"
    if code.startswith("es"):
        return "es"
    return "pt"


def _results(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("results", "indicators", "indicator_results"):
        rows = payload.get(key)
        if isinstance(rows, list):
            return [item for item in rows if isinstance(item, dict)]
    content = payload.get("content")
    return _results(content) if isinstance(content, (dict, list)) else []


def _usable(artifact: object) -> bool:
    return isinstance(artifact, LoadedArtifact) and artifact.state is ArtifactState.FOUND


def build_operational_baseline_view_model(
    loaded: Mapping[str, LoadedArtifact],
    *,
    language: str = "pt",
) -> dict[str, Any]:
    """Converte artefatos carregados em um estado seguro para apresentação."""
    text = COPY[_lang(language)]
    pointer = loaded.get("pointer")
    if not isinstance(pointer, LoadedArtifact) or pointer.state is ArtifactState.MISSING:
        return {"state": "pending", "message": text["pending"]}
    if pointer.state is not ArtifactState.FOUND or not isinstance(pointer.payload, dict):
        return {
            "state": "invalid",
            "message": text["invalid"],
            "error": pointer.error if isinstance(pointer, LoadedArtifact) else "",
        }

    snapshot = loaded.get("snapshot")
    manifest_artifact = loaded.get("operational_manifest")
    indicators_artifact = loaded.get("indicators")
    if not _usable(snapshot) or not _usable(manifest_artifact):
        errors = [
            artifact.error
            for artifact in (snapshot, manifest_artifact)
            if isinstance(artifact, LoadedArtifact) and artifact.error
        ]
        return {
            "state": "invalid",
            "message": text["invalid"],
            "error": "; ".join(errors),
        }

    manifest = manifest_artifact.payload
    if not isinstance(manifest, dict):
        return {"state": "invalid", "message": text["invalid"], "error": "manifest"}
    ai = manifest.get("ai") or {}
    if (
        manifest.get("status") != "completed"
        or manifest.get("official_baseline") is not True
        or not isinstance(ai, dict)
        or ai.get("is_official_baseline_dependency") is not False
    ):
        return {
            "state": "invalid",
            "message": text["invalid"],
            "error": "baseline não concluído, não oficial ou dependente da IA",
        }

    counts = manifest.get("counts") or {}
    results = _results(indicators_artifact.payload) if _usable(indicators_artifact) else []
    pointer_payload = pointer.payload
    snapshot_payload = snapshot.payload if isinstance(snapshot.payload, dict) else {}
    return {
        "state": "completed",
        "snapshot_id": snapshot_payload.get("snapshot_id") or manifest.get("baseline_id"),
        "active_corpora": counts.get("active_corpora", "—"),
        "indicator_count": counts.get("indicators", len(results)),
        "t1_occurrences": counts.get("non_successful_t1_corpora", "—"),
        "results": results,
        "manifest_path": pointer_payload.get("manifest_path") or str(manifest_artifact.path),
        "manifest_sha256": pointer_payload.get("manifest_sha256") or "—",
        "pipeline_commit": manifest.get("pipeline_commit") or "—",
        "generated_at": manifest.get("generated_at") or pointer_payload.get("updated_at") or "—",
        "ai_independent": True,
    }


def _selected_results_section(language: str) -> bool:
    code = _lang(language)
    selected = st.session_state.get(f"scientific-infrastructure-section-{code}")
    return selected == COPY[code]["results_section"]


def render_operational_baseline_panel(
    base_dir: str | Path,
    *,
    language: str = "pt",
) -> None:
    """Mostra o baseline operacional somente na seção de resultados."""
    if not _selected_results_section(language):
        return

    text = COPY[_lang(language)]
    loader = ScientificInfrastructureLoader(build_default_registry(Path(base_dir)))
    view = build_operational_baseline_view_model(
        loader.load_operational_baseline(), language=language
    )

    st.divider()
    st.markdown(f"### {text['title']}")
    st.caption(text["caption"])

    if view["state"] == "pending":
        st.info(view["message"])
        return
    if view["state"] != "completed":
        detail = str(view.get("error") or "").strip()
        st.warning(view["message"] + (f" ({detail})" if detail else ""))
        return

    cols = st.columns(3)
    cols[0].metric(text["corpora"], view["active_corpora"])
    cols[1].metric(text["indicators"], view["indicator_count"])
    cols[2].metric(text["t1_failures"], view["t1_occurrences"])
    st.caption(f"{text['snapshot']}: `{view['snapshot_id']}`")
    st.info(text["ai_note"])

    results = view["results"]
    if results:
        rows = [
            {
                text["indicator"]: item.get("title") or item.get("indicator_id") or "—",
                text["value"]: item.get("value", "—"),
                text["status"]: item.get("status", "—"),
                text["version"]: item.get("indicator_version", "—"),
            }
            for item in results
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.warning(text["no_results"])

    with st.expander(text["integrity"], expanded=False):
        st.markdown(f"**{text['manifest']}:** `{view['manifest_path']}`")
        st.markdown(f"**{text['manifest_hash']}:** `{view['manifest_sha256']}`")
        st.markdown(f"**{text['pipeline_commit']}:** `{view['pipeline_commit']}`")
        st.markdown(f"**{text['generated_at']}:** {view['generated_at']}")


__all__ = [
    "build_operational_baseline_view_model",
    "render_operational_baseline_panel",
]
