"""Registro central dos artefatos produzidos pela infraestrutura científica.

O registro é a única fonte de verdade para nomes, formatos, escopos e caminhos.
A interface e os carregadores não devem reconstruir caminhos manualmente.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable


class ArtifactFormat(str, Enum):
    JSON = "json"
    JSONL = "jsonl"


class ArtifactScope(str, Enum):
    STATIC = "static"
    ANALYTICS_ROOT = "analytics_root"
    ANALYTICS_SNAPSHOT = "analytics_snapshot"
    COVERAGE_SNAPSHOT = "coverage_snapshot"
    GOVERNANCE = "governance"


@dataclass(frozen=True, slots=True)
class ArtifactSpec:
    key: str
    label: str
    relative_path: str
    format: ArtifactFormat
    scope: ArtifactScope
    required: bool = False
    description: str = ""
    alternative_paths: tuple[str, ...] = ()

    def candidate_paths(self, root: Path) -> tuple[Path, ...]:
        return tuple(root / path for path in (self.relative_path, *self.alternative_paths))


class InfrastructureRegistry:
    """Catálogo imutável e validado de artefatos científicos."""

    def __init__(self, base_dir: str | Path, artifacts: Iterable[ArtifactSpec]):
        self.base_dir = Path(base_dir)
        specs = tuple(artifacts)
        keys = [spec.key for spec in specs]
        duplicates = sorted({key for key in keys if keys.count(key) > 1})
        if duplicates:
            raise ValueError(f"Artifact keys must be unique: {duplicates}")
        self._artifacts = {spec.key: spec for spec in specs}

    def __contains__(self, key: str) -> bool:
        return key in self._artifacts

    def get(self, key: str) -> ArtifactSpec:
        try:
            return self._artifacts[key]
        except KeyError as exc:
            raise KeyError(f"Unknown scientific infrastructure artifact: {key}") from exc

    def all(self) -> tuple[ArtifactSpec, ...]:
        return tuple(self._artifacts.values())

    def by_scope(self, scope: ArtifactScope) -> tuple[ArtifactSpec, ...]:
        return tuple(spec for spec in self._artifacts.values() if spec.scope is scope)

    @property
    def analytics_root(self) -> Path:
        return self.base_dir / "data/output/analytics"

    @property
    def coverage_root(self) -> Path:
        return self.base_dir / "data/digital_infrastructure/coverage"

    def resolve(self, key: str, *, snapshot_dir: Path | None = None) -> tuple[Path, ...]:
        spec = self.get(key)
        if spec.scope in {
            ArtifactScope.ANALYTICS_SNAPSHOT,
            ArtifactScope.COVERAGE_SNAPSHOT,
        }:
            if snapshot_dir is None:
                raise ValueError(f"snapshot_dir is required for artifact {key}")
            root = snapshot_dir
        else:
            root = self.base_dir
        return spec.candidate_paths(root)


def build_default_registry(base_dir: str | Path) -> InfrastructureRegistry:
    """Cria o registro canônico da versão atual da plataforma."""
    artifacts = (
        ArtifactSpec(
            key="indicator_registry",
            label="Registro científico de indicadores",
            relative_path="data/templates/analytics/indicator_registry.json",
            format=ArtifactFormat.JSON,
            scope=ArtifactScope.STATIC,
            required=True,
            description=(
                "Fonte operacional única para identidade, escopo e versão dos "
                "indicadores científicos."
            ),
        ),
        ArtifactSpec(
            key="methodology_registry",
            label="Registro metodológico",
            relative_path="data/templates/analytics/methodology_registry.json",
            format=ArtifactFormat.JSON,
            scope=ArtifactScope.STATIC,
            required=True,
            description="Fórmulas, componentes, pesos e políticas metodológicas.",
        ),
        ArtifactSpec(
            key="snapshot_indicators",
            label="Resultados dos indicadores",
            relative_path="snapshot_indicators.json",
            format=ArtifactFormat.JSON,
            scope=ArtifactScope.ANALYTICS_SNAPSHOT,
            description="Resultados materializados no snapshot analítico.",
        ),
        ArtifactSpec(
            key="analytics_manifest",
            label="Manifesto analítico",
            relative_path="manifest.json",
            format=ArtifactFormat.JSON,
            scope=ArtifactScope.ANALYTICS_SNAPSHOT,
            description="Composição, versões e integridade do snapshot.",
        ),
        ArtifactSpec(
            key="analytics_run",
            label="Execução analítica",
            relative_path="run.json",
            format=ArtifactFormat.JSON,
            scope=ArtifactScope.ANALYTICS_SNAPSHOT,
            description="Metadados da execução que produziu o snapshot.",
        ),
        ArtifactSpec(
            key="interoperability_sensitivity",
            label="Análise de sensibilidade",
            relative_path="interoperability_sensitivity.json",
            format=ArtifactFormat.JSON,
            scope=ArtifactScope.ANALYTICS_SNAPSHOT,
            description="Teste de sensibilidade do índice de interoperabilidade.",
        ),
        ArtifactSpec(
            key="parameter_coverage",
            label="Cobertura por parâmetro",
            relative_path="parameter_coverage.json",
            alternative_paths=("coverage.json",),
            format=ArtifactFormat.JSON,
            scope=ArtifactScope.COVERAGE_SNAPSHOT,
            description="Matriz de avaliabilidade e cobertura dos parâmetros.",
        ),
        ArtifactSpec(
            key="coverage_manifest",
            label="Manifesto de cobertura",
            relative_path="manifest.json",
            format=ArtifactFormat.JSON,
            scope=ArtifactScope.COVERAGE_SNAPSHOT,
        ),
        ArtifactSpec(
            key="coverage_changes",
            label="Alterações de cobertura",
            relative_path="changes.json",
            format=ArtifactFormat.JSON,
            scope=ArtifactScope.COVERAGE_SNAPSHOT,
        ),
        ArtifactSpec(
            key="indicator_history",
            label="Histórico dos indicadores",
            relative_path="data/output/analytics/indicator_history.jsonl",
            format=ArtifactFormat.JSONL,
            scope=ArtifactScope.ANALYTICS_ROOT,
            description="Série longitudinal dos indicadores materializados.",
        ),
        ArtifactSpec(
            key="ledger",
            label="Ledger append-only",
            relative_path="data/digital_infrastructure/ledger.jsonl",
            format=ArtifactFormat.JSONL,
            scope=ArtifactScope.GOVERNANCE,
            description="Eventos, versões, evidências e decisões preservados.",
        ),
        ArtifactSpec(
            key="ingestion_batches",
            label="Lotes de ingestão",
            relative_path="data/digital_infrastructure/ingestion_batches.jsonl",
            format=ArtifactFormat.JSONL,
            scope=ArtifactScope.GOVERNANCE,
            description="Rastreamento dos lotes técnicos de ingestão.",
        ),
    )
    return InfrastructureRegistry(base_dir, artifacts)
