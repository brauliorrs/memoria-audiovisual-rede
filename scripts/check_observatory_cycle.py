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
from memoria_audiovisual.european_aggregators import (
    EUROPEAN_AGGREGATOR_ACCESS_ROUTES_FILENAME,
    EUROPEAN_AGGREGATOR_EVALUATION_FILENAME,
    EUROPEAN_AGGREGATOR_PROBES_FILENAME,
    EUROPEAN_AGGREGATOR_PROTOCOLS_FILENAME,
    EUROPEAN_AGGREGATOR_SUMMARY_FILENAME,
)
from memoria_audiovisual.european_protocols import FRANCEARCHIVES_PROTOCOL_FILENAME
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
    european_aggregator_access_routes_path = OUTPUT_DIR / EUROPEAN_AGGREGATOR_ACCESS_ROUTES_FILENAME
    european_aggregator_evaluation_path = OUTPUT_DIR / EUROPEAN_AGGREGATOR_EVALUATION_FILENAME
    european_aggregator_probes_path = OUTPUT_DIR / EUROPEAN_AGGREGATOR_PROBES_FILENAME
    european_aggregator_protocols_path = OUTPUT_DIR / EUROPEAN_AGGREGATOR_PROTOCOLS_FILENAME
    european_aggregator_summary_path = OUTPUT_DIR / EUROPEAN_AGGREGATOR_SUMMARY_FILENAME
    francearchives_protocol_path = OUTPUT_DIR / FRANCEARCHIVES_PROTOCOL_FILENAME

    required_paths = [
        (cycle_manifest_path, "Manifesto do ciclo mensal"),
        (active_corpora_path, "Registro de corpora ativos"),
        (cycle_timeline_path, "Linha do tempo dos ciclos"),
        (cycle_results_path, "Resultados historicos dos ciclos"),
        (discovery_registry_path, "Registro de candidatos a expansao"),
        (discovery_queue_path, "Fila automatica de expansao"),
        (discovery_summary_path, "Resumo da fila de expansao"),
        (european_aggregator_access_routes_path, "Rotas oficiais dos agregadores europeus candidatos"),
        (european_aggregator_evaluation_path, "Avaliacao dos agregadores europeus candidatos"),
        (european_aggregator_probes_path, "Sondagens dos agregadores europeus candidatos"),
        (european_aggregator_protocols_path, "Protocolos dos agregadores europeus candidatos"),
        (european_aggregator_summary_path, "Resumo dos agregadores europeus candidatos"),
        (francearchives_protocol_path, "Prototipo de protocolo FranceArchives"),
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
    european_aggregator_access_routes_df = pd.read_csv(european_aggregator_access_routes_path)
    european_aggregator_evaluation_df = pd.read_csv(european_aggregator_evaluation_path)
    european_aggregator_probes_df = pd.read_csv(european_aggregator_probes_path)
    european_aggregator_protocols_df = pd.read_csv(european_aggregator_protocols_path)
    european_aggregator_summary_df = pd.read_csv(european_aggregator_summary_path)
    francearchives_protocol_df = pd.read_csv(francearchives_protocol_path)
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
    print(f"- rotas oficiais europeias registradas: {len(european_aggregator_access_routes_df)}")
    print(f"- agregadores europeus avaliados: {len(european_aggregator_evaluation_df)}")
    print(f"- sondagens europeias registradas: {len(european_aggregator_probes_df)}")
    print(f"- protocolos europeus registrados: {len(european_aggregator_protocols_df)}")
    print(f"- estados europeus sumarizados: {len(european_aggregator_summary_df)}")
    print(f"- sondagens do protocolo FranceArchives: {len(francearchives_protocol_df)}")

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

    if european_aggregator_evaluation_df.empty:
        print("- a avaliacao dos agregadores europeus esta vazia")
        return 1

    if european_aggregator_access_routes_df.empty:
        print("- as rotas oficiais dos agregadores europeus estao vazias")
        return 1

    if european_aggregator_protocols_df.empty:
        print("- a matriz de protocolos dos agregadores europeus esta vazia")
        return 1

    if francearchives_protocol_df.empty:
        print("- o prototipo de protocolo FranceArchives esta vazio")
        return 1

    print("- todos os corpora ativos aparecem no manifesto do ciclo")
    print("- a fila automatica de expansao foi materializada com sucesso")
    print("- a avaliacao e os protocolos dos agregadores europeus foram materializados com sucesso")
    print("- o prototipo de protocolo FranceArchives foi materializado com sucesso")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
