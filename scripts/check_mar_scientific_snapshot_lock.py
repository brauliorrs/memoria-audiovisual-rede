#!/usr/bin/env python3
"""Fail-closed *change detector* for MAR's currently frozen scientific site bundle.

This is NOT a generator, a scientific approval, or proof the historical baseline
was originally synchronized. A changed/added corpus source or site projection
blocks CI until a complete, reviewed projection generator replaces this lock.
No HTTP, Neon, API, media, tokens, or writes are performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = "site/data/scientific-snapshot-lock.json"
SOURCE_SUFFIXES = (
    "_relatorio.json",
    "_instituicoes.csv",
    "_tema_pais.csv",
    "_tema_plataforma.csv",
    "_linha_do_tempo_corpus.csv",
    "_snapshot_metadata.json",
    "_catalogo_videos_analitico.csv",
)
SPECIAL_SOURCES = frozenset({
    "observatorio_indice_dados_publicos_por_corpus.csv",
    "observatorio_unidades_acesso_restrito_indice.csv",
    "observatorio_unidades_identificadas_nao_incorporadas.csv",
    "kavi_mar_metadata_links.csv",
    "kavi_mar_metadata_links_manifest.json",
})
EXCLUDED_OUTPUTS = frozenset({
    "world-110m-geometry.json",
    "title-wordcloud.json",
    "scientific-snapshot-lock.json",
})


def git_blob_sha(path: Path) -> str:
    """Calculate Git's blob object ID without requiring git or loading large CSVs."""
    size = path.stat().st_size
    digest = hashlib.sha1(b"blob " + str(size).encode("ascii") + b"\0")
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def discover(root: Path) -> tuple[dict[str, Path], dict[str, Path]]:
    data = root / "data" / "output"
    site = root / "site" / "data"
    sources = {
        p.relative_to(root).as_posix(): p
        for p in data.iterdir() if p.is_file()
        and (p.name.endswith(SOURCE_SUFFIXES) or p.name in SPECIAL_SOURCES)
    }
    outputs = {
        p.relative_to(root).as_posix(): p
        for p in site.glob("*.json") if p.is_file() and p.name not in EXCLUDED_OUTPUTS
    }
    return sources, outputs


def verify(root: Path, lock: dict) -> list[str]:
    problems: list[str] = []
    if lock.get("schema") != "mar-scientific-snapshot-lock-v1":
        problems.append("Unknown or absent snapshot-lock schema")
    if lock.get("status") != "historical_baseline_only_not_a_regeneration_or_publication_approval":
        problems.append("Baseline lock cannot be presented as a validated regeneration")
    if lock.get("policy") != "fail_closed_until_full_reproducible_aggregate_bundle_and_scientific_approval":
        problems.append("Scientific fail-closed policy changed")
    sources, outputs = discover(root)
    for label, observed, recorded in (
        ("scientific source", sources, lock.get("inputs", {})),
        ("site projection", outputs, lock.get("outputs", {})),
    ):
        if not isinstance(recorded, dict):
            problems.append(f"Invalid {label} lock table")
            continue
        expected = set(recorded)
        actual = set(observed)
        for path in sorted(actual - expected):
            problems.append(f"New {label} outside reviewed baseline: {path}")
        for path in sorted(expected - actual):
            problems.append(f"Missing {label} from reviewed baseline: {path}")
        for path in sorted(actual & expected):
            if git_blob_sha(observed[path]) != recorded[path]:
                problems.append(f"Changed {label} since reviewed baseline: {path}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable gate result")
    args = parser.parse_args()
    try:
        lock = json.loads((ROOT / LOCK).read_text(encoding="utf-8"))
        problems = verify(ROOT, lock)
    except (OSError, ValueError, TypeError) as exc:
        problems = [f"Unable to verify frozen scientific baseline: {exc}"]
        lock = {}
    report = {
        "gate": "MAR scientific snapshot baseline lock",
        "status": "HOLD" if problems else "UNCHANGED_BASELINE_NOT_REGENERATION_PROOF",
        "baseline": lock.get("baselineMainCommit"),
        "problems": problems,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"{report['gate']}: {report['status']}")
        for problem in problems[:60]:
            print(f"::error::{problem}")
        if len(problems) > 60:
            print(f"::error::{len(problems) - 60} additional mismatches omitted")
        if not problems:
            print("No source or projection changed; this does NOT validate scientific parity.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
