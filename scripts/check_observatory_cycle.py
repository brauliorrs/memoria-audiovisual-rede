import json
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.corpora import OBSERVATORY_PROFILE, list_active_corpora
from memoria_audiovisual.archivegrid_protocol import ARCHIVEGRID_PROTOCOL_FILENAME
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
from memoria_audiovisual.europe_closure import (
    EUROPE_CLOSURE_DOSSIER_FILENAME,
    EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
    EUROPE_CLOSURE_GAP_AUDIT_FILENAME,
    EUROPE_CLOSURE_MATRIX_FILENAME,
    EUROPE_CLOSURE_QUEUE_FILENAME,
    EUROPE_CLOSURE_SUMMARY_FILENAME,
)
from memoria_audiovisual.europe_research import (
    EUROPE_RESEARCH_QUEUE_FILENAME,
    EUROPE_RESEARCH_REGISTRY_FILENAME,
    EUROPE_RESEARCH_SUMMARY_FILENAME,
)
from memoria_audiovisual.european_protocols import (
    ARCHIVESHUB_PROTOCOL_FILENAME,
    EUROPEAN_FILM_GATEWAY_PROTOCOL_FILENAME,
    EUROPEANA_PROTOCOL_FILENAME,
    FRANCEARCHIVES_PROTOCOL_FILENAME,
)
from memoria_audiovisual.iberarchivos_protocol import IBERARCHIVOS_PROTOCOL_FILENAME
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


def normalize_scope_text(value):
    text = unicodedata.normalize("NFKD", str(value or "").lower())
    return "".join(char for char in text if not unicodedata.combining(char))


def has_out_of_scope_audio_reference(value):
    text = normalize_scope_text(value)
    return any(
        re.search(pattern, text)
        for pattern in (
            r"\bdismarc\b",
            r"\beuropeana-sounds\b",
            r"\baudio\b",
            r"\bpodcast\b",
            r"\bsonor[ao]s?\b",
            r"\bmusical\b",
        )
    )


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
    archiveshub_protocol_path = OUTPUT_DIR / ARCHIVESHUB_PROTOCOL_FILENAME
    francearchives_protocol_path = OUTPUT_DIR / FRANCEARCHIVES_PROTOCOL_FILENAME
    european_film_gateway_protocol_path = OUTPUT_DIR / EUROPEAN_FILM_GATEWAY_PROTOCOL_FILENAME
    europeana_protocol_path = OUTPUT_DIR / EUROPEANA_PROTOCOL_FILENAME
    archivegrid_protocol_path = OUTPUT_DIR / ARCHIVEGRID_PROTOCOL_FILENAME
    iberarchivos_protocol_path = OUTPUT_DIR / IBERARCHIVOS_PROTOCOL_FILENAME
    europe_closure_matrix_path = OUTPUT_DIR / EUROPE_CLOSURE_MATRIX_FILENAME
    europe_closure_queue_path = OUTPUT_DIR / EUROPE_CLOSURE_QUEUE_FILENAME
    europe_closure_summary_path = OUTPUT_DIR / EUROPE_CLOSURE_SUMMARY_FILENAME
    europe_closure_dossier_path = OUTPUT_DIR / EUROPE_CLOSURE_DOSSIER_FILENAME
    europe_excluded_units_path = OUTPUT_DIR / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME
    europe_gap_audit_path = OUTPUT_DIR / EUROPE_CLOSURE_GAP_AUDIT_FILENAME
    europe_research_registry_path = OUTPUT_DIR / EUROPE_RESEARCH_REGISTRY_FILENAME
    europe_research_queue_path = OUTPUT_DIR / EUROPE_RESEARCH_QUEUE_FILENAME
    europe_research_summary_path = OUTPUT_DIR / EUROPE_RESEARCH_SUMMARY_FILENAME

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
        (archiveshub_protocol_path, "Prototipo de protocolo Archives Hub"),
        (francearchives_protocol_path, "Prototipo de protocolo FranceArchives"),
        (european_film_gateway_protocol_path, "Prototipo de protocolo European Film Gateway"),
        (europeana_protocol_path, "Prototipo de protocolo Europeana"),
        (archivegrid_protocol_path, "Prototipo de protocolo ArchiveGrid"),
        (iberarchivos_protocol_path, "Prototipo de protocolo Iberarchivos"),
        (europe_closure_matrix_path, "Matriz de fechamento europeu"),
        (europe_closure_queue_path, "Fila de fechamento europeu"),
        (europe_closure_summary_path, "Resumo de fechamento europeu"),
        (europe_closure_dossier_path, "Dossiê MVP de fechamento europeu"),
        (europe_excluded_units_path, "Unidades identificadas fora do corpus ativo"),
        (europe_gap_audit_path, "Auditoria de lacunas europeias"),
        (europe_research_registry_path, "Registro ampliado de pesquisa europeia"),
        (europe_research_queue_path, "Fila ampliada de pesquisa europeia"),
        (europe_research_summary_path, "Resumo da pesquisa europeia"),
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
    archiveshub_protocol_df = pd.read_csv(archiveshub_protocol_path)
    francearchives_protocol_df = pd.read_csv(francearchives_protocol_path)
    european_film_gateway_protocol_df = pd.read_csv(european_film_gateway_protocol_path)
    europeana_protocol_df = pd.read_csv(europeana_protocol_path)
    archivegrid_protocol_df = pd.read_csv(archivegrid_protocol_path)
    iberarchivos_protocol_df = pd.read_csv(iberarchivos_protocol_path)
    europe_closure_matrix_df = pd.read_csv(europe_closure_matrix_path)
    europe_closure_queue_df = pd.read_csv(europe_closure_queue_path)
    europe_closure_summary_df = pd.read_csv(europe_closure_summary_path)
    europe_excluded_units_df = pd.read_csv(europe_excluded_units_path)
    europe_gap_audit_df = pd.read_csv(europe_gap_audit_path)
    europe_research_registry_df = pd.read_csv(europe_research_registry_path)
    europe_research_queue_df = pd.read_csv(europe_research_queue_path)
    europe_research_summary_df = pd.read_csv(europe_research_summary_path)
    europe_closure_dossier_text = europe_closure_dossier_path.read_text(encoding="utf-8")
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
    if "audiovisual_probe_status" in discovery_registry_df.columns:
        probed_total = int((discovery_registry_df["audiovisual_probe_status"] != "sondagem_nao_realizada").sum())
        audiovisual_probe_hits = int(
            (discovery_registry_df["audiovisual_probe_status"] == "evidencia_audiovisual_detectada").sum()
        )
        print(f"- candidatos com sondagem audiovisual: {probed_total}")
        print(f"- candidatos com evidencia audiovisual preliminar: {audiovisual_probe_hits}")
    print(f"- rotas oficiais europeias registradas: {len(european_aggregator_access_routes_df)}")
    print(f"- agregadores europeus avaliados: {len(european_aggregator_evaluation_df)}")
    print(f"- sondagens europeias registradas: {len(european_aggregator_probes_df)}")
    print(f"- protocolos europeus registrados: {len(european_aggregator_protocols_df)}")
    print(f"- estados europeus sumarizados: {len(european_aggregator_summary_df)}")
    print(f"- sondagens do protocolo Archives Hub: {len(archiveshub_protocol_df)}")
    print(f"- sondagens do protocolo FranceArchives: {len(francearchives_protocol_df)}")
    print(f"- sondagens do protocolo European Film Gateway: {len(european_film_gateway_protocol_df)}")
    print(f"- sondagens do protocolo Europeana: {len(europeana_protocol_df)}")
    print(f"- sondagens do protocolo ArchiveGrid: {len(archivegrid_protocol_df)}")
    print(f"- sondagens do protocolo Iberarchivos: {len(iberarchivos_protocol_df)}")
    print(f"- unidades na matriz de fechamento europeu: {len(europe_closure_matrix_df)}")
    print(f"- unidades na fila de fechamento europeu: {len(europe_closure_queue_df)}")
    print(f"- unidades identificadas fora do corpus ativo: {len(europe_excluded_units_df)}")
    print(f"- lacunas europeias auditadas: {len(europe_gap_audit_df)}")
    print(f"- unidades no registro ampliado europeu: {len(europe_research_registry_df)}")
    print(f"- unidades na fila ampliada europeia: {len(europe_research_queue_df)}")
    print(f"- decisões na pesquisa europeia: {len(europe_research_summary_df)}")
    print(f"- criterios de fechamento europeu: {len(europe_closure_summary_df)}")
    print(f"- caracteres no dossiê MVP europeu: {len(europe_closure_dossier_text)}")

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

    if "audiovisual_probe_status" not in discovery_registry_df.columns:
        print("- o registro de descoberta nao materializou a sondagem audiovisual")
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

    if archiveshub_protocol_df.empty:
        print("- o prototipo de protocolo Archives Hub esta vazio")
        return 1

    if francearchives_protocol_df.empty:
        print("- o prototipo de protocolo FranceArchives esta vazio")
        return 1

    if european_film_gateway_protocol_df.empty:
        print("- o prototipo de protocolo European Film Gateway esta vazio")
        return 1

    if europeana_protocol_df.empty:
        print("- o prototipo de protocolo Europeana esta vazio")
        return 1

    if archivegrid_protocol_df.empty:
        print("- o prototipo de protocolo ArchiveGrid esta vazio")
        return 1

    if iberarchivos_protocol_df.empty:
        print("- o prototipo de protocolo Iberarchivos esta vazio")
        return 1

    if europe_closure_matrix_df.empty or europe_closure_queue_df.empty or europe_closure_summary_df.empty:
        print("- o fechamento europeu nao foi materializado corretamente")
        return 1

    if europe_excluded_units_df.empty:
        print("- o registro de unidades identificadas fora do corpus ativo esta vazio")
        return 1

    if europe_gap_audit_df.empty:
        print("- a auditoria de lacunas europeias esta vazia")
        return 1

    if europe_research_registry_df.empty or europe_research_queue_df.empty:
        print("- a pesquisa europeia ampliada nao foi materializada corretamente")
        return 1

    europe_research_codes = europe_research_registry_df.get("unit_code", pd.Series(dtype="object")).astype(str).tolist()
    for required_source_code in (
        "ace-members",
        "efg-contributing-archives",
        "fiaf-europe-members",
        "fiat-ifta-members",
        "inedits-members",
        "ebu-public-service-media-members",
    ):
        if required_source_code not in europe_research_codes:
            print(f"- a pesquisa europeia nao registrou a fonte {required_source_code}")
            return 1

    if "video_location_candidate_url" not in europe_research_queue_df.columns:
        print("- a fila europeia nao materializou o campo de localizacao inicial dos videos")
        return 1

    scope_text = " ".join(
        europe_research_registry_df.get(column, pd.Series(dtype="object")).astype(str).str.cat(sep=" ")
        for column in ("unit_code", "unit_type", "audiovisual_relevance", "queue_decision")
    )
    if has_out_of_scope_audio_reference(scope_text):
        print("- a pesquisa europeia registrou fonte fora do escopo audiovisual")
        return 1

    if "public_status" not in europe_excluded_units_df.columns:
        print("- o registro de unidades fora do corpus nao materializou o status publico")
        return 1

    if not europe_excluded_units_df["public_status"].astype(str).str.contains("não incluída no corpus").any():
        print("- o registro de unidades fora do corpus nao explicita a nao inclusao metodologica")
        return 1

    if "corpus continental" not in europe_closure_dossier_text.lower():
        print("- o dossiê MVP europeu não explicita o corpus continental")
        return 1

    print("- todos os corpora ativos aparecem no manifesto do ciclo")
    print("- a fila automatica de expansao foi materializada com sucesso")
    print("- a avaliacao e os protocolos dos agregadores europeus foram materializados com sucesso")
    print("- o prototipo de protocolo Archives Hub foi materializado com sucesso")
    print("- o prototipo de protocolo FranceArchives foi materializado com sucesso")
    print("- o prototipo de protocolo European Film Gateway foi materializado com sucesso")
    print("- o prototipo de protocolo Europeana foi materializado com sucesso")
    print("- o prototipo de protocolo ArchiveGrid foi materializado com sucesso")
    print("- o prototipo de protocolo Iberarchivos foi materializado com sucesso")
    print("- o fechamento europeu foi materializado com sucesso")
    print("- o registro de unidades fora do corpus ativo foi materializado com sucesso")
    print("- a auditoria de lacunas europeias foi materializada com sucesso")
    print("- a pesquisa europeia ampliada foi materializada com sucesso")
    print("- o dossiê MVP europeu foi materializado com sucesso")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
