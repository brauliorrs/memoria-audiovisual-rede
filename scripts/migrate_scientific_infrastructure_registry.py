"""Migra a interface científica para o InfrastructureRegistry central.

A transformação é idempotente, valida os pontos estruturais e remove a antiga
camada local de caminhos e leitura. O script não executa deploy.
"""

from __future__ import annotations

import argparse
from pathlib import Path


TARGET = Path("src/memoria_audiovisual/ui/scientific_infrastructure.py")

OLD_IMPORTS = '''import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import streamlit as st
'''

NEW_IMPORTS = '''from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import streamlit as st

from memoria_audiovisual.scientific_infrastructure import (
    LoadedArtifact,
    ScientificInfrastructureLoader,
    build_default_registry,
)
'''

OLD_LOCAL_LOADERS_START = '''@dataclass(frozen=True, slots=True)
class ScientificInfrastructurePaths:
'''

LOCAL_LOADERS_END = '''def _as_list(value: object) -> list[Any]:
'''

REPLACEMENT_BOUNDARY = '''def _as_list(value: object) -> list[Any]:
'''

OLD_RENDER_SETUP = '''    paths = ScientificInfrastructurePaths(Path(base_dir))
    catalog_artifact = load_indicator_catalog(paths)
    methodology_artifact = load_methodology_registry(paths)
    snapshot = load_latest_snapshot(paths)
    coverage = load_latest_coverage(paths)
    governance = load_governance_artifacts(paths)
'''

NEW_RENDER_SETUP = '''    registry = build_default_registry(Path(base_dir))
    loader = ScientificInfrastructureLoader(registry)
    static_artifacts = loader.load_static()
    catalog_artifact = static_artifacts["indicator_registry"]
    methodology_artifact = static_artifacts["methodology_registry"]
    snapshot = loader.load_latest_analytics_snapshot()
    coverage = loader.load_latest_coverage_snapshot()
    governance = loader.load_governance()
'''


def transform(source: str) -> str:
    if NEW_IMPORTS not in source:
        if OLD_IMPORTS not in source:
            raise RuntimeError("Bloco de imports legado não localizado")
        source = source.replace(OLD_IMPORTS, NEW_IMPORTS, 1)

    if OLD_LOCAL_LOADERS_START in source:
        start = source.index(OLD_LOCAL_LOADERS_START)
        try:
            end = source.index(LOCAL_LOADERS_END, start)
        except ValueError as exc:
            raise RuntimeError("Limite final dos carregadores locais não localizado") from exc
        source = source[:start] + REPLACEMENT_BOUNDARY + source[end + len(LOCAL_LOADERS_END):]

    if NEW_RENDER_SETUP not in source:
        if OLD_RENDER_SETUP not in source:
            raise RuntimeError("Configuração legada de renderização não localizada")
        source = source.replace(OLD_RENDER_SETUP, NEW_RENDER_SETUP, 1)

    return source


def validate(source: str) -> None:
    required = (
        "ScientificInfrastructureLoader",
        "build_default_registry",
        "registry = build_default_registry(Path(base_dir))",
        'static_artifacts["indicator_registry"]',
        "loader.load_latest_analytics_snapshot()",
        "loader.load_latest_coverage_snapshot()",
        "loader.load_governance()",
    )
    missing = [fragment for fragment in required if fragment not in source]
    if missing:
        raise RuntimeError(f"Migração incompleta: {missing}")
    forbidden = (
        "class ScientificInfrastructurePaths",
        "def _read_json(",
        "def _read_jsonl(",
        "def load_indicator_catalog(",
        "def load_latest_snapshot(",
        "def load_latest_coverage(",
        "def load_governance_artifacts(",
        'static_artifacts["indicator_catalog"]',
        "data/templates/analytics/indicator_catalog.json",
    )
    remaining = [fragment for fragment in forbidden if fragment in source]
    if remaining:
        raise RuntimeError(f"Descoberta ou catálogo legado ainda presente: {remaining}")


def migrate(path: Path, *, check: bool = False) -> bool:
    source = path.read_text(encoding="utf-8")
    transformed = transform(source)
    validate(transformed)
    changed = transformed != source
    if check and changed:
        raise RuntimeError(f"{path} ainda requer migração para o registro central")
    if changed and not check:
        path.write_text(transformed, encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=TARGET)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    changed = migrate(args.path, check=args.check)
    print("interface migrada" if changed else "interface já usa o registro canônico")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
