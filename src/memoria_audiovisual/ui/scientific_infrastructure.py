"""Interface pública da infraestrutura científica do observatório.

A seção expõe a arquitetura já implementada sem transformar metodologia em
resultado empírico. Os carregadores são tolerantes à ausência de artefatos e
sempre distinguem estrutura disponível, execução e materialização.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import streamlit as st


@dataclass(frozen=True, slots=True)
class ScientificInfrastructurePaths:
    base_dir: Path

    @property
    def indicator_catalog(self) -> Path:
        return self.base_dir / "data/templates/analytics/indicator_catalog.json"

    @property
    def methodology_registry(self) -> Path:
        return self.base_dir / "data/templates/analytics/methodology_registry.json"

    @property
    def analytics_root(self) -> Path:
        return self.base_dir / "data/output/analytics"

    @property
    def coverage_root(self) -> Path:
        return self.base_dir / "data/digital_infrastructure/coverage"

    @property
    def ledger(self) -> Path:
        return self.base_dir / "data/digital_infrastructure/ledger.jsonl"

    @property
    def ingestion_batches(self) -> Path:
        return self.base_dir / "data/digital_infrastructure/ingestion_batches.jsonl"


@dataclass(frozen=True, slots=True)
class LoadedArtifact:
    name: str
    path: Path
    available: bool
    payload: Any = None
    error: str = ""


def _read_json(path: Path) -> LoadedArtifact:
    if not path.exists():
        return LoadedArtifact(path.name, path, False)
    try:
        return LoadedArtifact(path.name, path, True, json.loads(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return LoadedArtifact(path.name, path, False, error=str(exc))


def _read_jsonl(path: Path) -> LoadedArtifact:
    if not path.exists():
        return LoadedArtifact(path.name, path, False)
    rows: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                item = json.loads(line)
                if isinstance(item, dict):
                    rows.append(item)
                else:
                    rows.append({"linha": line_number, "valor": item})
        return LoadedArtifact(path.name, path, True, rows)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return LoadedArtifact(path.name, path, False, error=str(exc))


def load_indicator_catalog(paths: ScientificInfrastructurePaths) -> LoadedArtifact:
    return _read_json(paths.indicator_catalog)


def load_methodology_registry(paths: ScientificInfrastructurePaths) -> LoadedArtifact:
    return _read_json(paths.methodology_registry)


def _snapshot_directories(root: Path) -> tuple[Path, ...]:
    if not root.exists():
        return ()
    return tuple(
        sorted(
            (item for item in root.iterdir() if item.is_dir()),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
    )


def load_latest_snapshot(paths: ScientificInfrastructurePaths) -> dict[str, LoadedArtifact]:
    snapshots = _snapshot_directories(paths.analytics_root)
    if not snapshots:
        return {}
    latest = snapshots[0]
    return {
        "snapshot": LoadedArtifact("snapshot", latest, True, {"snapshot_id": latest.name}),
        "indicators": _read_json(latest / "snapshot_indicators.json"),
        "manifest": _read_json(latest / "manifest.json"),
        "run": _read_json(latest / "run.json"),
        "sensitivity": _read_json(latest / "interoperability_sensitivity.json"),
    }


def load_latest_coverage(paths: ScientificInfrastructurePaths) -> dict[str, LoadedArtifact]:
    snapshots = _snapshot_directories(paths.coverage_root)
    if not snapshots:
        return {}
    latest = snapshots[0]
    candidates = (
        latest / "parameter_coverage.json",
        latest / "coverage.json",
    )
    coverage_path = next((path for path in candidates if path.exists()), candidates[0])
    return {
        "snapshot": LoadedArtifact("snapshot", latest, True, {"snapshot_id": latest.name}),
        "coverage": _read_json(coverage_path),
        "manifest": _read_json(latest / "manifest.json"),
        "changes": _read_json(latest / "changes.json"),
    }


def load_governance_artifacts(paths: ScientificInfrastructurePaths) -> dict[str, LoadedArtifact]:
    return {
        "ledger": _read_jsonl(paths.ledger),
        "ingestion_batches": _read_jsonl(paths.ingestion_batches),
        "indicator_history": _read_jsonl(paths.analytics_root / "indicator_history.jsonl"),
    }


def _as_list(value: object) -> list[Any]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _indicator_results(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("indicators", "results", "indicator_results"):
        rows = payload.get(key)
        if isinstance(rows, list):
            return [item for item in rows if isinstance(item, dict)]
    run = payload.get("run")
    if isinstance(run, dict):
        return _indicator_results(run)
    return []


def _format_list(value: object) -> str:
    values = [str(item) for item in _as_list(value) if str(item).strip()]
    return "; ".join(values) if values else "—"


def _dimension_label(value: object) -> str:
    labels = {
        "access": "Acesso",
        "digital_infrastructure": "Infraestrutura digital",
        "interoperability": "Interoperabilidade",
        "metadata": "Metadados",
        "composite_index": "Índice composto",
    }
    return labels.get(str(value), str(value) or "—")


def _status_label(structure: bool, result: bool) -> str:
    if result:
        return "Resultado materializado"
    if structure:
        return "Estrutura implementada; resultado não materializado"
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
                "Catálogo": "Disponível",
                "Metodologia": "Disponível" if indicator_id in methodology_ids else "Não localizada",
                "Resultado": "Materializado" if result else "Aguardando execução",
                "Valor": _extract_result_value(result) if result else "—",
                "Situação": _status_label(True, bool(result)),
            }
        )
    return pd.DataFrame(rows)


def _render_indicator_catalog(indicators: list[dict[str, Any]], methodologies_by_id: dict[str, dict[str, Any]]) -> None:
    st.subheader("Indicadores científicos")
    st.caption(
        "O catálogo apresenta o que a plataforma mede. A existência de uma definição ou fórmula não significa que já exista resultado empírico materializado."
    )
    if not indicators:
        st.warning("O catálogo oficial de indicadores não pôde ser carregado.")
        return

    dimension_counts = pd.Series([_dimension_label(item.get("dimension")) for item in indicators]).value_counts()
    metric_columns = st.columns(3)
    metric_columns[0].metric("Indicadores registrados", len(indicators))
    metric_columns[1].metric("Dimensões analíticas", int(dimension_counts.size))
    metric_columns[2].metric("Versão do catálogo", "1.0.0")

    for indicator in indicators:
        indicator_id = str(indicator.get("indicator_id", ""))
        methodology = methodologies_by_id.get(indicator_id, {})
        with st.expander(str(indicator.get("title", indicator_id)), expanded=False):
            st.markdown(f"**Pergunta científica:** {indicator.get('scientific_question', '—')}")
            st.markdown(f"**Dimensão:** {_dimension_label(indicator.get('dimension'))}")
            st.markdown(f"**Interpretação:** {indicator.get('interpretation', '—')}")
            st.markdown(f"**Justificativa de seleção:** {indicator.get('selection_rationale', '—')}")
            if methodology.get("formula"):
                st.code(str(methodology["formula"]), language=None)
            st.markdown(f"**O que não mede:** {_format_list(indicator.get('does_not_measure'))}")
            st.markdown(
                f"**Relação com outros indicadores:** {indicator.get('relationship_to_other_indicators', '—')}"
            )
            if indicator.get("corpus_rule"):
                st.info(str(indicator["corpus_rule"]))


def _render_methodology(methodologies: list[dict[str, Any]]) -> None:
    st.subheader("Metodologia de cálculo")
    st.caption(
        "Fórmulas, denominadores, estados incluídos e excluídos, componentes, pesos e políticas de dados ausentes são exibidos conforme o registro metodológico versionado."
    )
    if not methodologies:
        st.warning("O registro metodológico não pôde ser carregado.")
        return

    for methodology in methodologies:
        title = str(methodology.get("indicator_id", "Indicador"))
        with st.expander(title, expanded=title == "interoperability_index"):
            st.markdown(f"**Definição:** {methodology.get('definition', '—')}")
            st.markdown("**Fórmula**")
            st.code(str(methodology.get("formula", "—")), language=None)
            st.markdown(f"**Fonte de dados:** `{methodology.get('source', '—')}`")
            st.markdown(f"**Estados incluídos:** {_format_list(methodology.get('included_statuses'))}")
            st.markdown(f"**Estados excluídos:** {_format_list(methodology.get('excluded_statuses'))}")

            components = _as_list(methodology.get("components"))
            if components:
                component_df = pd.DataFrame(components).rename(columns={"name": "Componente", "weight": "Peso"})
                st.dataframe(component_df, use_container_width=True, hide_index=True)
                st.markdown(
                    f"**Mínimo de componentes avaliáveis:** {methodology.get('minimum_evaluable_components', '—')}"
                )
                st.markdown(
                    f"**Política para dados ausentes:** {methodology.get('missing_data_policy', '—')}"
                )
            st.markdown(f"**Limitações:** {_format_list(methodology.get('limitations'))}")


def _render_operational_status(status_df: pd.DataFrame, snapshot: dict[str, LoadedArtifact], coverage: dict[str, LoadedArtifact]) -> None:
    st.subheader("Estado operacional")
    st.caption(
        "Esta camada distingue a existência do catálogo e do motor metodológico da existência de resultados efetivamente materializados."
    )
    if status_df.empty:
        st.info("Não foi possível construir o quadro operacional dos indicadores.")
        return
    st.dataframe(status_df, use_container_width=True, hide_index=True)

    operational = st.columns(4)
    operational[0].metric("Indicadores no catálogo", len(status_df))
    operational[1].metric("Com metodologia", int(status_df["Metodologia"].eq("Disponível").sum()))
    operational[2].metric("Com resultado", int(status_df["Resultado"].eq("Materializado").sum()))
    operational[3].metric("Snapshot analítico", "Disponível" if snapshot else "Ausente")

    if not coverage:
        st.warning("A matriz de cobertura por parâmetro ainda não foi materializada no diretório operacional.")


def _artifact_table(artifacts: dict[str, LoadedArtifact]) -> pd.DataFrame:
    rows = []
    for key, artifact in artifacts.items():
        rows.append(
            {
                "Produto": key,
                "Situação": "Disponível" if artifact.available else "Ausente ou inválido",
                "Caminho": str(artifact.path),
                "Erro": artifact.error or "—",
            }
        )
    return pd.DataFrame(rows)


def _render_results_and_snapshots(snapshot: dict[str, LoadedArtifact], coverage: dict[str, LoadedArtifact]) -> None:
    st.subheader("Resultados e snapshots")
    if not snapshot:
        st.info(
            "A infraestrutura analítica está implementada, mas ainda não existe snapshot analítico materializado para apresentação de resultados empíricos."
        )
        st.caption(
            "Quando o pipeline for executado, esta seção carregará automaticamente resultados, manifesto, versão metodológica e análise de sensibilidade."
        )
    else:
        snapshot_id = snapshot["snapshot"].payload.get("snapshot_id", "—")
        st.success(f"Snapshot analítico localizado: {snapshot_id}")
        st.dataframe(_artifact_table(snapshot), use_container_width=True, hide_index=True)
        indicators_artifact = snapshot.get("indicators")
        if indicators_artifact and indicators_artifact.available:
            results = _indicator_results(indicators_artifact.payload)
            if results:
                result_df = pd.DataFrame(results)
                st.dataframe(result_df, use_container_width=True, hide_index=True)
            else:
                st.warning("O arquivo de indicadores existe, mas não contém resultados reconhecíveis pelo carregador.")

        sensitivity = snapshot.get("sensitivity")
        if sensitivity and sensitivity.available and isinstance(sensitivity.payload, dict):
            interpretation = sensitivity.payload.get("interpretation")
            if interpretation:
                st.markdown(f"**Interpretação da sensibilidade:** {interpretation}")

    if coverage:
        st.markdown("#### Cobertura por parâmetro")
        st.dataframe(_artifact_table(coverage), use_container_width=True, hide_index=True)


def _record_type_counts(rows: list[dict[str, Any]]) -> pd.DataFrame:
    counts: dict[str, int] = {}
    for row in rows:
        records = row.get("records")
        if isinstance(records, list):
            for envelope in records:
                if isinstance(envelope, dict):
                    record_type = str(envelope.get("record_type", "desconhecido"))
                    counts[record_type] = counts.get(record_type, 0) + 1
        else:
            record_type = str(row.get("record_type", "evento"))
            counts[record_type] = counts.get(record_type, 0) + 1
    return pd.DataFrame(
        [{"Tipo de registro": key, "Quantidade": value} for key, value in sorted(counts.items())]
    )


def _render_provenance(governance: dict[str, LoadedArtifact], snapshot: dict[str, LoadedArtifact]) -> None:
    st.subheader("Proveniência, evidências e integridade")
    st.caption(
        "Esta camada documenta por que os resultados podem ser auditados: versões, evidências, eventos append-only, manifests e hashes permanecem separados da interpretação científica."
    )

    concepts = pd.DataFrame(
        [
            {"Componente": "Ledger append-only", "Função": "Preserva eventos e versões sem reescrever o histórico."},
            {"Componente": "Evidências", "Função": "Vincula afirmações técnicas às superfícies e registros observados."},
            {"Componente": "Proveniência", "Função": "Registra origem, transformação, versão e produtos derivados."},
            {"Componente": "Snapshot", "Função": "Congela uma execução analítica identificável e comparável."},
            {"Componente": "Manifest e hash", "Função": "Permitem verificar composição e integridade dos artefatos."},
            {"Componente": "Decisões curatoriais", "Função": "Separam ingestão técnica de incorporação científica."},
        ]
    )
    st.dataframe(concepts, use_container_width=True, hide_index=True)
    st.dataframe(_artifact_table(governance), use_container_width=True, hide_index=True)

    ledger = governance.get("ledger")
    if ledger and ledger.available and isinstance(ledger.payload, list):
        metric_columns = st.columns(2)
        metric_columns[0].metric("Transações no ledger", len(ledger.payload))
        record_counts = _record_type_counts(ledger.payload)
        metric_columns[1].metric("Tipos de registro", len(record_counts))
        if not record_counts.empty:
            st.dataframe(record_counts, use_container_width=True, hide_index=True)

    manifest = snapshot.get("manifest") if snapshot else None
    if manifest and manifest.available and isinstance(manifest.payload, dict):
        with st.expander("Manifest do snapshot mais recente", expanded=False):
            st.json(manifest.payload)


def render_scientific_infrastructure(base_dir: str | Path) -> None:
    """Renderiza a seção completa na ordem de leitura científica acordada."""
    paths = ScientificInfrastructurePaths(Path(base_dir))
    catalog_artifact = load_indicator_catalog(paths)
    methodology_artifact = load_methodology_registry(paths)
    snapshot = load_latest_snapshot(paths)
    coverage = load_latest_coverage(paths)
    governance = load_governance_artifacts(paths)

    catalog_payload = catalog_artifact.payload if isinstance(catalog_artifact.payload, dict) else {}
    methodology_payload = methodology_artifact.payload if isinstance(methodology_artifact.payload, dict) else {}
    indicators = [item for item in catalog_payload.get("indicators", []) if isinstance(item, dict)]
    methodologies = [item for item in methodology_payload.get("methodologies", []) if isinstance(item, dict)]
    methodologies_by_id = {str(item.get("indicator_id")): item for item in methodologies}

    result_rows: list[dict[str, Any]] = []
    indicators_artifact = snapshot.get("indicators") if snapshot else None
    if indicators_artifact and indicators_artifact.available:
        result_rows = _indicator_results(indicators_artifact.payload)
    status_df = build_operational_status(indicators, methodologies, result_rows)

    st.markdown("## Infraestrutura científica")
    st.caption(
        "A seção apresenta o que a plataforma mede, como calcula, o que já está operacional, quais resultados foram materializados e como a integridade é verificada."
    )

    indicator_tab, methodology_tab, status_tab, results_tab, provenance_tab = st.tabs(
        [
            "Indicadores",
            "Metodologia",
            "Estado operacional",
            "Resultados e snapshots",
            "Proveniência e integridade",
        ]
    )
    with indicator_tab:
        _render_indicator_catalog(indicators, methodologies_by_id)
    with methodology_tab:
        _render_methodology(methodologies)
    with status_tab:
        _render_operational_status(status_df, snapshot, coverage)
    with results_tab:
        _render_results_and_snapshots(snapshot, coverage)
    with provenance_tab:
        _render_provenance(governance, snapshot)
