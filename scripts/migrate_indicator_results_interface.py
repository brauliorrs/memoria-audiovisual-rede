#!/usr/bin/env python3
"""Integra o registro materializado dos indicadores à interface científica."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "src/memoria_audiovisual/scientific_infrastructure/registry.py"
INTERFACE = ROOT / "src/memoria_audiovisual/ui/scientific_infrastructure.py"


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"âncora não localizada: {label}")
    return text.replace(old, new, 1)


def migrate_registry(text: str) -> str:
    anchor = '''        ArtifactSpec(
            key="snapshot_indicators",
'''
    addition = '''        ArtifactSpec(
            key="indicator_results_registry",
            label="Registro científico de resultados",
            relative_path="data/reference_corpus/snapshots/indicator_results_v1.0.json",
            format=ArtifactFormat.JSON,
            scope=ArtifactScope.STATIC,
            required=True,
            description="Nove resultados oficiais materializados pelo motor analítico.",
        ),
        ArtifactSpec(
            key="snapshot_indicators",
'''
    return replace_once(text, anchor, addition, label="registro de resultados")


def migrate_interface(text: str) -> str:
    parser_anchor = '''    if not isinstance(payload, dict):
        return []
    for key in ("indicators", "results", "indicator_results"):
'''
    parser_replacement = '''    if not isinstance(payload, dict):
        return []
    content = payload.get("content")
    if isinstance(content, dict):
        nested = _indicator_results(content)
        if nested:
            return nested
    for key in ("indicators", "results", "indicator_results"):
'''
    text = replace_once(text, parser_anchor, parser_replacement, label="parser content.results")

    render_anchor = '''def _record_type_counts(rows: list[dict[str, Any]]) -> pd.DataFrame:
'''
    render_function = '''def _render_materialized_indicator_results(artifact: LoadedArtifact) -> None:
    st.subheader("Resultados científicos materializados")
    payload = artifact.payload if isinstance(artifact.payload, dict) else {}
    results = _indicator_results(payload)
    content = payload.get("content") if isinstance(payload.get("content"), dict) else {}
    provenance = payload.get("provenance") if isinstance(payload.get("provenance"), dict) else {}

    if not results:
        st.warning("O registro científico existe, mas não contém resultados reconhecíveis.")
        return

    metrics = st.columns(4)
    metrics[0].metric("Indicadores", len(results))
    metrics[1].metric("Status", content.get("execution_status", "—"))
    metrics[2].metric("Coverage Snapshot", provenance.get("coverage_snapshot_id", "—"))
    metrics[3].metric("Corpus", results[0].get("corpus_count", "—"))

    rows = []
    for item in results:
        value = item.get("value")
        unit = str(item.get("unit") or "")
        rendered_value = f"{value:.4f}%" if isinstance(value, (int, float)) and unit == "percent" else value
        rows.append({
            "Indicador": item.get("title") or item.get("indicator_id"),
            "ID": item.get("indicator_id"),
            "Valor": rendered_value,
            "Numerador": item.get("numerator"),
            "Denominador": item.get("denominator"),
            "Status": item.get("status"),
            "Versão": item.get("indicator_version"),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(
        "Valores lidos diretamente do Scientific Indicator Results Registry; "
        "a interface não recalcula indicadores."
    )


''' + render_anchor
    text = replace_once(text, render_anchor, render_function, label="render dos resultados")

    load_anchor = '''    methodology_artifact = static_artifacts["methodology_registry"]
    snapshot = loader.load_latest_analytics_snapshot()
'''
    load_replacement = '''    methodology_artifact = static_artifacts["methodology_registry"]
    indicator_results_artifact = static_artifacts.get("indicator_results_registry")
    snapshot = loader.load_latest_analytics_snapshot()
'''
    text = replace_once(text, load_anchor, load_replacement, label="carregamento do registro")

    results_anchor = '''    result_rows: list[dict[str, Any]] = []
    indicators_artifact = snapshot.get("indicators") if snapshot else None
    if indicators_artifact and indicators_artifact.available:
        result_rows = _indicator_results(indicators_artifact.payload)
'''
    results_replacement = '''    result_rows: list[dict[str, Any]] = []
    if indicator_results_artifact and indicator_results_artifact.available:
        result_rows = _indicator_results(indicator_results_artifact.payload)
    else:
        indicators_artifact = snapshot.get("indicators") if snapshot else None
        if indicators_artifact and indicators_artifact.available:
            result_rows = _indicator_results(indicators_artifact.payload)
'''
    text = replace_once(text, results_anchor, results_replacement, label="fonte prioritária dos resultados")

    tab_anchor = '''    with results_tab:
        _render_results_and_snapshots(snapshot, coverage)
'''
    tab_replacement = '''    with results_tab:
        if indicator_results_artifact and indicator_results_artifact.available:
            _render_materialized_indicator_results(indicator_results_artifact)
        else:
            _render_results_and_snapshots(snapshot, coverage)
'''
    return replace_once(text, tab_anchor, tab_replacement, label="aba de resultados")


def main() -> int:
    registry_text = REGISTRY.read_text(encoding="utf-8")
    interface_text = INTERFACE.read_text(encoding="utf-8")
    REGISTRY.write_text(migrate_registry(registry_text), encoding="utf-8")
    INTERFACE.write_text(migrate_interface(interface_text), encoding="utf-8")
    print("Interface científica conectada ao registro oficial de resultados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
