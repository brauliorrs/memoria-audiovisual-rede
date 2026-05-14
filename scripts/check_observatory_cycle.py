import json
import sys
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.corpora import OBSERVATORY_PROFILE, list_active_corpora
from memoria_audiovisual.discovery import (
    DISCOVERY_QUEUE_FILENAME,
    DISCOVERY_REGISTRY_FILENAME,
    DISCOVERY_SUMMARY_FILENAME,
)
from memoria_audiovisual.organism import (
    ORGANISM_ACTIVE_CORPORA_FILENAME,
    ORGANISM_CYCLE_RESULTS_FILENAME,
    ORGANISM_CYCLE_TIMELINE_FILENAME,
    ORGANISM_MONTHLY_CYCLE_FILENAME,
)


def load_json_if_exists(path):
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def main():
    cycle_manifest_path = OUTPUT_DIR / ORGANISM_MONTHLY_CYCLE_FILENAME
    active_corpora_path = OUTPUT_DIR / ORGANISM_ACTIVE_CORPORA_FILENAME
    cycle_timeline_path = OUTPUT_DIR / ORGANISM_CYCLE_TIMELINE_FILENAME
    cycle_results_path = OUTPUT_DIR / ORGANISM_CYCLE_RESULTS_FILENAME
    discovery_registry_path = OUTPUT_DIR / DISCOVERY_REGISTRY_FILENAME
    discovery_queue_path = OUTPUT_DIR / DISCOVERY_QUEUE_FILENAME
    discovery_summary_path = OUTPUT_DIR / DISCOVERY_SUMMARY_FILENAME

    required_paths = [
        (cycle_manifest_path, "Manifesto do ciclo mensal"),
        (active_corpora_path, "Registro de corpora ativos"),
        (cycle_timeline_path, "Linha do tempo dos ciclos"),
        (cycle_results_path, "Resultados historicos dos ciclos"),
        (discovery_registry_path, "Registro de candidatos a expansao"),
        (discovery_queue_path, "Fila automatica de expansao"),
        (discovery_summary_path, "Resumo da fila de expansao"),
    ]
    for path, label in required_paths:
        if not path.exists():
            print(f"{label} ausente: {path.name}")
            return 1

    manifest = load_json_if_exists(cycle_manifest_path)
    registry_df = pd.read_csv(active_corpora_path)
    cycle_timeline_df = pd.read_csv(cycle_timeline_path)
    cycle_results_df = pd.read_csv(cycle_results_path)
    discovery_registry_df = pd.read_csv(discovery_registry_path)
    discovery_queue_df = pd.read_csv(discovery_queue_path)
    discovery_summary_df = pd.read_csv(discovery_summary_path)
    active_corpora = list_active_corpora(monthly_only=True)

    print("Validacao do ciclo mensal do organismo")
    print(f"- organismo: {OBSERVATORY_PROFILE['label']}")
    print(f"- papel: {OBSERVATORY_PROFILE['role']}")
    print(f"- cadencia: {manifest.get('refresh_cadence', '-')}")
    print(f"- corpora ativos registrados: {len(registry_df)}")
    print(f"- corpora ativos esperados: {len(active_corpora)}")
    print(f"- escopo do ciclo: {manifest.get('cycle_scope', '-')}")
    print(f"- corpora selecionados no ciclo: {manifest.get('selected_corpora_total', 0)}")
    print(f"- sucessos no ultimo ciclo: {manifest.get('successful_corpora_total', 0)}")
    print(f"- falhas no ultimo ciclo: {manifest.get('failed_corpora_total', 0)}")
    print(f"- ciclos registrados na linha do tempo: {len(cycle_timeline_df)}")
    print(f"- resultados historicos registrados: {len(cycle_results_df)}")
    print(f"- candidatos registrados para expansao: {len(discovery_registry_df)}")
    print(f"- itens na fila automatica de expansao: {len(discovery_queue_df)}")
    print(f"- decisoes automaticas sumarizadas: {len(discovery_summary_df)}")

    result_codes = {result["code"] for result in manifest.get("cycle_results", [])}
    expected_codes = set(
        manifest.get("selected_corpora_codes")
        or [corpus_def["code"] for corpus_def in active_corpora]
    )
    missing_codes = sorted(expected_codes - result_codes)
    if missing_codes:
        print("- corpora ativos ausentes do manifesto:")
        for code in missing_codes:
            print(f"  - {code}")
        return 1

    if manifest.get("generated_at") not in cycle_timeline_df.get(
        "generated_at",
        pd.Series(dtype="object"),
    ).astype(str).tolist():
        print("- o ciclo atual nao foi encontrado na linha do tempo historica")
        return 1

    if discovery_queue_df.empty:
        print("- a fila automatica de expansao esta vazia")
        return 1

    print("- todos os corpora ativos aparecem no manifesto do ciclo")
    print("- a fila automatica de expansao foi materializada com sucesso")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
