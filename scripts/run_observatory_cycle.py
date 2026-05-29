import argparse
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.corpora import list_active_corpora
from memoria_audiovisual.adlibitum_protocol import write_adlibitum_protocol_probe
from memoria_audiovisual.archivegrid_protocol import write_archivegrid_protocol_probe
from memoria_audiovisual.discovery import write_discovery_outputs
from memoria_audiovisual.european_aggregators import write_european_aggregator_evaluation
from memoria_audiovisual.europe_closure import write_europe_closure_outputs
from memoria_audiovisual.europe_research import write_europe_research_outputs
from memoria_audiovisual.european_protocols import (
    write_archiveshub_protocol_probe,
    write_european_film_gateway_protocol_probe,
    write_europeana_protocol_probe,
    write_francearchives_protocol_probe,
)
from memoria_audiovisual.iberarchivos_protocol import write_iberarchivos_protocol_probe
from memoria_audiovisual.organism import (
    load_snapshot_metadata,
    write_active_corpora_registry,
    write_cycle_history,
    write_monthly_cycle_manifest,
)


def utcnow_iso():
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_python_script(relative_path):
    script_path = ROOT_DIR / relative_path
    env = os.environ.copy()
    playwright_dir = ROOT_DIR / ".playwright"
    if playwright_dir.exists() and "PLAYWRIGHT_BROWSERS_PATH" not in env:
        env["PLAYWRIGHT_BROWSERS_PATH"] = str(playwright_dir)
    subprocess.run(
        [sys.executable, str(script_path)],
        cwd=ROOT_DIR,
        check=True,
        env=env,
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Executa o ciclo do organismo para todos os corpora ativos ou para um subconjunto."
    )
    parser.add_argument(
        "--corpus",
        dest="corpora",
        action="append",
        default=[],
        help="Código de corpus a executar. Pode ser repetido, por exemplo: --corpus ape --corpus ina",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    started_at = utcnow_iso()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_active_corpora_registry(OUTPUT_DIR)
    write_discovery_outputs(OUTPUT_DIR)
    write_european_aggregator_evaluation(OUTPUT_DIR)
    write_archiveshub_protocol_probe(OUTPUT_DIR)
    write_francearchives_protocol_probe(OUTPUT_DIR)
    write_european_film_gateway_protocol_probe(OUTPUT_DIR)
    write_europeana_protocol_probe(OUTPUT_DIR)
    write_adlibitum_protocol_probe(OUTPUT_DIR)
    write_archivegrid_protocol_probe(OUTPUT_DIR)
    write_iberarchivos_protocol_probe(OUTPUT_DIR)
    write_europe_closure_outputs(OUTPUT_DIR)
    write_europe_research_outputs(OUTPUT_DIR)

    active_corpora = list_active_corpora(monthly_only=True)
    if args.corpora:
        selected_codes = {code.strip().lower() for code in args.corpora if code.strip()}
        active_corpora = [
            corpus_def
            for corpus_def in active_corpora
            if corpus_def["code"] in selected_codes
        ]
    else:
        selected_codes = {corpus_def["code"] for corpus_def in active_corpora}

    if not active_corpora:
        print("Nenhum corpus ativo corresponde ao recorte solicitado.")
        return 1

    cycle_results = []
    failures = 0

    for corpus_def in active_corpora:
        refresh_started_at = utcnow_iso()
        try:
            run_python_script(corpus_def["run_script_path"])
            run_python_script(corpus_def["check_script_path"])
            snapshot_metadata = load_snapshot_metadata(corpus_def, OUTPUT_DIR)
            cycle_results.append(
                {
                    "code": corpus_def["code"],
                    "label": corpus_def["label"],
                    "short_label": corpus_def["short_label"],
                    "category_code": corpus_def["category_code"],
                    "coverage_level": corpus_def["coverage_level"],
                    "status": "success",
                    "refresh_started_at": refresh_started_at,
                    "refresh_finished_at": utcnow_iso(),
                    "snapshot_generated_at": snapshot_metadata.get("generated_at", ""),
                    "observation_key": snapshot_metadata.get("observation_key", ""),
                    "source_status_date": snapshot_metadata.get("source_status_date", ""),
                    "institutions": snapshot_metadata.get("counts", {}).get("institutions", 0),
                    "video_links_total": snapshot_metadata.get("counts", {}).get("video_links_total", 0),
                    "videos_in_curatorial_catalog": snapshot_metadata.get("counts", {}).get(
                        "videos_in_curatorial_catalog",
                        0,
                    ),
                    "error": "",
                }
            )
        except subprocess.CalledProcessError as exc:
            failures += 1
            cycle_results.append(
                {
                    "code": corpus_def["code"],
                    "label": corpus_def["label"],
                    "short_label": corpus_def["short_label"],
                    "category_code": corpus_def["category_code"],
                    "coverage_level": corpus_def["coverage_level"],
                    "status": "failed",
                    "refresh_started_at": refresh_started_at,
                    "refresh_finished_at": utcnow_iso(),
                    "snapshot_generated_at": "",
                    "observation_key": "",
                    "source_status_date": "",
                    "institutions": 0,
                    "video_links_total": 0,
                    "videos_in_curatorial_catalog": 0,
                    "error": str(exc),
                }
            )

    manifest = write_monthly_cycle_manifest(
        started_at=started_at,
        finished_at=utcnow_iso(),
        cycle_results=cycle_results,
        selected_corpora=sorted(selected_codes),
        output_dir=OUTPUT_DIR,
    )
    write_cycle_history(manifest, OUTPUT_DIR)

    print("Ciclo mensal do organismo concluído.")
    print(f"- corpora ativos: {manifest['active_corpora_total']}")
    print(f"- sucessos: {manifest['successful_corpora_total']}")
    print(f"- falhas: {manifest['failed_corpora_total']}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
