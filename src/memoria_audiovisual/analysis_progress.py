"""Cumulative corpus-analysis progress for the MAR engine.

The user-facing analysis number is not a queue rank. It counts unique corpus-
level analyses that already reached a documented decision in the engine.

A unit counts as analyzed when either:
- it has a definition in CORPORA (active or inactive); or
- the European research registry marks it as protocolado.

Canonical aliases are used before counting, so an inactive CORPORA definition
and its protocol row count once.
"""
from __future__ import annotations

import json
from pathlib import Path

from .config import OUTPUT_DIR
from .corpora import CORPORA
from .europe_research import (
    _active_european_code_aliases,
    build_europe_research_registry,
)

ANALYSIS_PROGRESS_FILENAME = "observatorio_contador_analises.json"


def build_analysis_progress(registry_df=None) -> dict:
    registry_df = build_europe_research_registry() if registry_df is None else registry_df
    aliases = _active_european_code_aliases()

    corpus_codes = {
        str(corpus_def["code"]).strip()
        for corpus_def in CORPORA.values()
        if str(corpus_def.get("code", "")).strip()
    }
    active_codes = {
        str(corpus_def["code"]).strip()
        for corpus_def in CORPORA.values()
        if corpus_def.get("organism_active", False)
        and str(corpus_def.get("code", "")).strip()
    }

    protocolled_rows = registry_df.loc[
        registry_df["organism_status"].astype(str) == "protocolado",
        "unit_code",
    ].astype(str)
    protocolled_codes = {
        aliases.get(code.strip(), code.strip())
        for code in protocolled_rows
        if code.strip()
    }

    overlap = corpus_codes & protocolled_codes
    analyzed_codes = corpus_codes | protocolled_codes
    analyzed_total = len(analyzed_codes)

    return {
        "schema_version": "1.0.0",
        "counting_rule": (
            "unique canonical corpus-level units with a CORPORA definition or "
            "organism_status=protocolado; active/inactive definitions and protocol "
            "aliases are deduplicated"
        ),
        "corpora_defined_total": len(corpus_codes),
        "active_corpora_total": len(active_codes),
        "inactive_corpora_total": len(corpus_codes - active_codes),
        "protocolled_units_total": len(protocolled_codes),
        "protocolled_already_in_corpora_total": len(overlap),
        "protocolled_outside_corpora_total": len(protocolled_codes - corpus_codes),
        "analyzed_corpora_total": analyzed_total,
        "next_analysis_number": analyzed_total + 1,
        "analyzed_corpus_codes": sorted(analyzed_codes),
    }


def write_analysis_progress(output_dir: Path = OUTPUT_DIR) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = build_analysis_progress()
    (output_dir / ANALYSIS_PROGRESS_FILENAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


__all__ = [
    "ANALYSIS_PROGRESS_FILENAME",
    "build_analysis_progress",
    "write_analysis_progress",
]
