#!/usr/bin/env python3
"""Regenera e valida os produtos canônicos da pesquisa europeia.

O corpus operacional ativo é global, enquanto estes produtos possuem recorte
explicitamente europeu. Por isso, o denominador europeu deve ser derivado do
mesmo predicado usado pelo gerador e não igualado ao total global de corpora.
"""

from __future__ import annotations

import argparse
import io
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.corpora import list_active_corpora
from memoria_audiovisual.europe_research import (
    EUROPE_RESEARCH_QUEUE_FILENAME,
    EUROPE_RESEARCH_REGISTRY_FILENAME,
    EUROPE_RESEARCH_RULE_VERSION,
    EUROPE_RESEARCH_SUMMARY_FILENAME,
    _is_european_corpus,
    build_europe_research_queue,
    build_europe_research_registry,
    build_europe_research_summary,
    write_europe_research_outputs,
)


DEFAULT_OUTPUT_DIR = ROOT_DIR / "data" / "output"


@dataclass(frozen=True, slots=True)
class EuropeResearchCounts:
    global_active: int
    european_active: int
    registry_rows: int
    queue_rows: int


class EuropeResearchConsistencyError(RuntimeError):
    """Indica divergência entre corpus canônico e produtos europeus."""


def _canonical_string_frame(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Normaliza tipos pela própria serialização CSV usada nos artefatos."""
    buffer = io.StringIO()
    dataframe.to_csv(buffer, index=False)
    buffer.seek(0)
    return pd.read_csv(buffer, dtype=str, keep_default_na=False)


def _load_materialized_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise EuropeResearchConsistencyError(f"produto europeu inexistente: {path}")
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def _frame_difference(name: str, expected: pd.DataFrame, actual: pd.DataFrame) -> str | None:
    expected_normalized = _canonical_string_frame(expected)
    actual_normalized = _canonical_string_frame(actual)

    if list(actual_normalized.columns) != list(expected_normalized.columns):
        return (
            f"{name}: colunas divergentes; esperado={list(expected_normalized.columns)!r}; "
            f"encontrado={list(actual_normalized.columns)!r}"
        )
    if len(actual_normalized) != len(expected_normalized):
        return (
            f"{name}: total de linhas divergente; esperado={len(expected_normalized)}; "
            f"encontrado={len(actual_normalized)}"
        )
    if not actual_normalized.equals(expected_normalized):
        differences = actual_normalized.compare(expected_normalized, keep_shape=False, keep_equal=False)
        preview = differences.head(8).to_string()
        return f"{name}: conteúdo difere do gerador canônico. Primeiras diferenças:\n{preview}"
    return None


def build_expected_outputs() -> dict[str, pd.DataFrame]:
    registry = build_europe_research_registry()
    return {
        "registry": registry,
        "queue": build_europe_research_queue(registry),
        "summary": build_europe_research_summary(registry),
    }


def validate_expected_outputs(outputs: dict[str, pd.DataFrame]) -> EuropeResearchCounts:
    registry = outputs["registry"]
    queue = outputs["queue"]
    summary = outputs["summary"]

    global_active = tuple(list_active_corpora(monthly_only=True))
    european_active = tuple(item for item in global_active if _is_european_corpus(item))
    global_codes = {str(item["code"]) for item in global_active}
    european_codes = {str(item["code"]) for item in european_active}
    extraeuropean_codes = global_codes - european_codes

    if registry.empty:
        raise EuropeResearchConsistencyError("registro europeu canônico vazio")
    if registry["unit_code"].duplicated().any():
        duplicated = sorted(registry.loc[registry["unit_code"].duplicated(), "unit_code"].astype(str).unique())
        raise EuropeResearchConsistencyError(f"códigos duplicados no registro europeu: {duplicated}")

    active_rows = registry.loc[
        (registry["organism_status"] == "ativo")
        & (registry["queue_layer"] == "corpus_ativo")
    ]
    active_registry_codes = set(active_rows["unit_code"].astype(str))
    if active_registry_codes != european_codes:
        missing = sorted(european_codes - active_registry_codes)
        unexpected = sorted(active_registry_codes - european_codes)
        raise EuropeResearchConsistencyError(
            "recorte ativo europeu divergente do corpus canônico; "
            f"ausentes={missing}; inesperados={unexpected}"
        )

    leaked_extraeuropean = sorted(active_registry_codes & extraeuropean_codes)
    if leaked_extraeuropean:
        raise EuropeResearchConsistencyError(
            f"corpora extraeuropeus entraram no denominador europeu: {leaked_extraeuropean}"
        )

    active_summary = summary.loc[
        (summary["camada"] == "corpus_ativo")
        & (summary["categoria"] == "corpus_ativo")
        & (summary["decisao"] == "monitoramento_mensal")
    ]
    if len(active_summary) != 1:
        raise EuropeResearchConsistencyError(
            "o resumo europeu deve conter exatamente uma linha para o corpus ativo"
        )
    summarized_active = int(active_summary.iloc[0]["total"])
    if summarized_active != len(european_active):
        raise EuropeResearchConsistencyError(
            "denominador ativo europeu divergente; "
            f"esperado={len(european_active)}; encontrado={summarized_active}; "
            f"total_global={len(global_active)}"
        )

    if set(registry["rule_version"].astype(str)) != {EUROPE_RESEARCH_RULE_VERSION}:
        raise EuropeResearchConsistencyError("registro europeu mistura versões de regra")
    if set(queue["rule_version"].astype(str)) != {EUROPE_RESEARCH_RULE_VERSION}:
        raise EuropeResearchConsistencyError("fila europeia mistura versões de regra")
    if set(summary["rule_version"].astype(str)) != {EUROPE_RESEARCH_RULE_VERSION}:
        raise EuropeResearchConsistencyError("resumo europeu mistura versões de regra")

    expected_ranks = list(range(1, len(queue) + 1))
    actual_ranks = [int(value) for value in queue["definitive_queue_rank"].tolist()]
    if actual_ranks != expected_ranks:
        raise EuropeResearchConsistencyError(
            "ranking da fila europeia não é contínuo; "
            f"esperado=1..{len(queue)}; encontrado={actual_ranks[:10]}..."
        )

    blocked_statuses = sorted(set(queue["organism_status"].astype(str)) & {"ativo", "protocolado"})
    if blocked_statuses:
        raise EuropeResearchConsistencyError(
            f"fila europeia contém estados que deveriam estar excluídos: {blocked_statuses}"
        )

    return EuropeResearchCounts(
        global_active=len(global_active),
        european_active=len(european_active),
        registry_rows=len(registry),
        queue_rows=len(queue),
    )


def check_materialized_outputs(output_dir: Path) -> EuropeResearchCounts:
    expected = build_expected_outputs()
    counts = validate_expected_outputs(expected)
    materialized = {
        "registry": _load_materialized_csv(output_dir / EUROPE_RESEARCH_REGISTRY_FILENAME),
        "queue": _load_materialized_csv(output_dir / EUROPE_RESEARCH_QUEUE_FILENAME),
        "summary": _load_materialized_csv(output_dir / EUROPE_RESEARCH_SUMMARY_FILENAME),
    }

    filenames = {
        "registry": EUROPE_RESEARCH_REGISTRY_FILENAME,
        "queue": EUROPE_RESEARCH_QUEUE_FILENAME,
        "summary": EUROPE_RESEARCH_SUMMARY_FILENAME,
    }
    findings = [
        finding
        for key in ("registry", "queue", "summary")
        if (finding := _frame_difference(filenames[key], expected[key], materialized[key]))
    ]
    if findings:
        raise EuropeResearchConsistencyError("\n".join(findings))
    return counts


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="não grava arquivos; falha se os produtos materializados estiverem desatualizados",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="diretório que contém ou receberá os três produtos europeus",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    output_dir = args.output_dir.resolve()
    try:
        if not args.check:
            write_europe_research_outputs(output_dir)
        counts = check_materialized_outputs(output_dir)
    except (EuropeResearchConsistencyError, OSError, ValueError) as exc:
        print(f"European research products are inconsistent: {exc}", file=sys.stderr)
        return 1

    print(
        "European research products are current: "
        f"{counts.european_active} European active corpora within "
        f"{counts.global_active} global active corpora; "
        f"{counts.registry_rows} registry rows; {counts.queue_rows} queue rows."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
