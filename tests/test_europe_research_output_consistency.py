from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

from memoria_audiovisual.corpora import list_active_corpora
from memoria_audiovisual.europe_research import (
    EUROPE_RESEARCH_SUMMARY_FILENAME,
    _is_european_corpus,
    build_europe_research_registry,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
SYNC_SCRIPT = ROOT_DIR / "scripts" / "sync_europe_research_outputs.py"


def test_european_denominator_is_a_geographic_subset_of_global_active_corpus():
    global_active = tuple(list_active_corpora(monthly_only=True))
    european_active = tuple(item for item in global_active if _is_european_corpus(item))
    extraeuropean_codes = {
        str(item["code"])
        for item in global_active
        if not _is_european_corpus(item)
    }

    registry = build_europe_research_registry()
    active_registry_codes = set(
        registry.loc[
            (registry["organism_status"] == "ativo")
            & (registry["queue_layer"] == "corpus_ativo"),
            "unit_code",
        ].astype(str)
    )

    assert len(global_active) > len(european_active)
    assert "aapb" in extraeuropean_codes
    assert active_registry_codes == {str(item["code"]) for item in european_active}
    assert active_registry_codes.isdisjoint(extraeuropean_codes)


def test_sync_script_writes_outputs_that_pass_its_own_check(tmp_path):
    write_result = subprocess.run(
        [sys.executable, str(SYNC_SCRIPT), "--output-dir", str(tmp_path)],
        cwd=ROOT_DIR,
        check=False,
        capture_output=True,
        text=True,
    )
    assert write_result.returncode == 0, write_result.stderr
    assert "European research products are current" in write_result.stdout

    check_result = subprocess.run(
        [sys.executable, str(SYNC_SCRIPT), "--check", "--output-dir", str(tmp_path)],
        cwd=ROOT_DIR,
        check=False,
        capture_output=True,
        text=True,
    )
    assert check_result.returncode == 0, check_result.stderr


def test_sync_script_rejects_a_stale_european_denominator(tmp_path):
    subprocess.run(
        [sys.executable, str(SYNC_SCRIPT), "--output-dir", str(tmp_path)],
        cwd=ROOT_DIR,
        check=True,
        capture_output=True,
        text=True,
    )

    summary_path = tmp_path / EUROPE_RESEARCH_SUMMARY_FILENAME
    summary = pd.read_csv(summary_path, encoding="utf-8-sig")
    active_mask = (
        (summary["camada"] == "corpus_ativo")
        & (summary["categoria"] == "corpus_ativo")
        & (summary["decisao"] == "monitoramento_mensal")
    )
    summary.loc[active_mask, "total"] = summary.loc[active_mask, "total"] + 1
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")

    result = subprocess.run(
        [sys.executable, str(SYNC_SCRIPT), "--check", "--output-dir", str(tmp_path)],
        cwd=ROOT_DIR,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "observatorio_resumo_pesquisa_europa.csv" in result.stderr
