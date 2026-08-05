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
from memoria_audiovisual.arsenal_protocol import write_arsenal_protocol_probe
from memoria_audiovisual.archivegrid_protocol import write_archivegrid_protocol_probe
from memoria_audiovisual.atresmedia_protocol import write_atresmedia_protocol_probe
from memoria_audiovisual.bnfa_protocol import write_bnfa_protocol_probe
from memoria_audiovisual.cineteca_bologna_protocol import write_cineteca_bologna_protocol_probe
from memoria_audiovisual.cineteca_italiana_protocol import write_cineteca_italiana_protocol_probe
from memoria_audiovisual.cinematheque_corse_protocol import write_cinematheque_corse_protocol_probe
from memoria_audiovisual.cinematheque_luxembourg_protocol import write_cinematheque_luxembourg_protocol_probe
from memoria_audiovisual.cnc_aff_protocol import write_cnc_aff_protocol_probe
from memoria_audiovisual.digital_infrastructure.ai_contracts import AIExperimentRunManifest
from memoria_audiovisual.digital_infrastructure.ai_cycle import collect_entity_shadow_signals
from memoria_audiovisual.digital_infrastructure.ai_flags import AIExperimentFlags
from memoria_audiovisual.digital_infrastructure.ai_storage import AIExperimentStore
from memoria_audiovisual.discovery import write_discovery_outputs
from memoria_audiovisual.filmmuseum_munchen_protocol import write_filmmuseum_munchen_protocol_probe
from memoria_audiovisual.filmoteca_vaticana_protocol import write_filmoteca_vaticana_protocol_probe
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
from memoria_audiovisual.prise2_protocol import write_prise2_protocol_probe
from memoria_audiovisual.public_access_index import write_public_access_index
from memoria_audiovisual.restricted_access_audit import write_restricted_access_audit


AI_EXPERIMENT_ROOT = ROOT_DIR / "data" / "digital_infrastructure" / "ai_experiments"
DEFAULT_CORPUS_TIMEOUT_SECONDS = 900


def utcnow_iso():
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_python_script(relative_path, *, timeout_seconds):
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
        timeout=timeout_seconds,
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
    parser.add_argument(
        "--skip-global-prelude",
        action="store_true",
        help=(
            "Ignora sondagens e produtos globais anteriores aos corpora. "
            "Uso restrito a validações controladas; o ciclo integral deve manter o prelude."
        ),
    )
    parser.add_argument(
        "--corpus-timeout",
        type=int,
        default=DEFAULT_CORPUS_TIMEOUT_SECONDS,
        help=(
            "Tempo máximo em segundos para cada script de coleta e verificação de um corpus. "
            f"Padrão: {DEFAULT_CORPUS_TIMEOUT_SECONDS}."
        ),
    )
    args = parser.parse_args()
    if args.corpus_timeout < 1:
        parser.error("--corpus-timeout deve ser maior ou igual a 1")
    return args


def run_global_prelude(output_dir):
    """Materializa produtos globais que antecedem o ciclo integral dos corpora."""

    write_discovery_outputs(output_dir)
    write_european_aggregator_evaluation(output_dir)
    write_archiveshub_protocol_probe(output_dir)
    write_francearchives_protocol_probe(output_dir)
    write_european_film_gateway_protocol_probe(output_dir)
    write_europeana_protocol_probe(output_dir)
    write_adlibitum_protocol_probe(output_dir)
    write_arsenal_protocol_probe(output_dir)
    write_prise2_protocol_probe(output_dir)
    write_atresmedia_protocol_probe(output_dir)
    write_bnfa_protocol_probe(output_dir)
    write_cnc_aff_protocol_probe(output_dir)
    write_cineteca_italiana_protocol_probe(output_dir)
    write_cinematheque_corse_protocol_probe(output_dir)
    write_cinematheque_luxembourg_protocol_probe(output_dir)
    write_filmmuseum_munchen_protocol_probe(output_dir)
    write_filmoteca_vaticana_protocol_probe(output_dir)
    write_archivegrid_protocol_probe(output_dir)
    write_iberarchivos_protocol_probe(output_dir)
    write_europe_closure_outputs(output_dir)
    write_cineteca_bologna_protocol_probe(output_dir)
    write_europe_research_outputs(output_dir)
    write_restricted_access_audit(output_dir)
    write_public_access_index(output_dir)


def _prepare_ai_shadow_run(started_at):
    errors = []
    try:
        flags = AIExperimentFlags.from_env()
    except Exception as exc:
        errors.append(f"flags: {type(exc).__name__}: {exc}")
        return AIExperimentFlags(), None, None, errors

    if not flags.enabled_tasks:
        return flags, None, None, errors

    run_id = "ai-shadow-" + started_at.replace(":", "").replace("-", "")
    try:
        store = AIExperimentStore(AI_EXPERIMENT_ROOT)
        store.append_run_manifest(
            AIExperimentRunManifest(
                run_id=run_id,
                official_cycle_id=None,
                corpus_version="active-corpora-current",
                enabled_tasks=flags.enabled_tasks,
                feature_flags=flags.to_dict(),
                status="running",
                started_at=started_at,
                notes="Coleta experimental em modo sombra; sem dependência do baseline.",
            )
        )
        return flags, store, run_id, errors
    except Exception as exc:
        errors.append(f"setup: {type(exc).__name__}: {exc}")
        return flags, None, run_id, errors


def _finish_ai_shadow_run(
    *,
    store,
    run_id,
    flags,
    official_manifest,
    started_at,
    finished_at,
    records_total,
    errors,
):
    if store is None or run_id is None:
        return
    status = "partial" if errors else "completed"
    official_cycle_id = (
        official_manifest.get("cycle_id")
        or official_manifest.get("manifest_id")
        or official_manifest.get("observation_key")
        or started_at
    )
    notes = (
        f"records_total={records_total}; errors_total={len(errors)}. "
        "Resultados experimentais não integram o baseline oficial."
    )
    try:
        store.append_run_manifest(
            AIExperimentRunManifest(
                run_id=run_id,
                official_cycle_id=str(official_cycle_id),
                corpus_version=str(
                    official_manifest.get("corpus_version") or "active-corpora-current"
                ),
                enabled_tasks=flags.enabled_tasks,
                feature_flags=flags.to_dict(),
                status=status,
                started_at=started_at,
                completed_at=finished_at,
                notes=notes,
            )
        )
    except Exception as exc:
        errors.append(f"finalize: {type(exc).__name__}: {exc}")


def _failed_cycle_result(corpus_def, refresh_started_at, exc):
    if isinstance(exc, subprocess.TimeoutExpired):
        error = (
            f"Timeout após {exc.timeout} segundos: "
            f"{' '.join(str(part) for part in exc.cmd)}"
        )
    else:
        error = str(exc)
    return {
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
        "error": error,
    }


def main():
    args = parse_args()
    started_at = utcnow_iso()
    ai_flags, ai_store, ai_run_id, ai_errors = _prepare_ai_shadow_run(started_at)
    ai_records_total = 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_active_corpora_registry(OUTPUT_DIR)
    if not args.skip_global_prelude:
        run_global_prelude(OUTPUT_DIR)
    else:
        print("Validação controlada: sondagem global anterior aos corpora foi ignorada.")

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
            run_python_script(
                corpus_def["run_script_path"],
                timeout_seconds=args.corpus_timeout,
            )
            run_python_script(
                corpus_def["check_script_path"],
                timeout_seconds=args.corpus_timeout,
            )
            snapshot_metadata = load_snapshot_metadata(corpus_def, OUTPUT_DIR)

            if ai_store is not None and ai_run_id is not None:
                ai_report = collect_entity_shadow_signals(
                    run_id=ai_run_id,
                    corpus_definition=corpus_def,
                    snapshot_metadata=snapshot_metadata,
                    output_dir=OUTPUT_DIR,
                    flags=ai_flags,
                    store=ai_store,
                )
                ai_records_total += len(ai_report.records)
                if ai_report.error:
                    ai_errors.append(f"{corpus_def['code']}: {ai_report.error}")

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
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            failures += 1
            cycle_results.append(_failed_cycle_result(corpus_def, refresh_started_at, exc))

    finished_at = utcnow_iso()
    manifest = write_monthly_cycle_manifest(
        started_at=started_at,
        finished_at=finished_at,
        cycle_results=cycle_results,
        selected_corpora=sorted(selected_codes),
        output_dir=OUTPUT_DIR,
    )
    write_cycle_history(manifest, OUTPUT_DIR)
    _finish_ai_shadow_run(
        store=ai_store,
        run_id=ai_run_id,
        flags=ai_flags,
        official_manifest=manifest,
        started_at=started_at,
        finished_at=finished_at,
        records_total=ai_records_total,
        errors=ai_errors,
    )

    print("Ciclo mensal do organismo concluído.")
    print(f"- corpora ativos: {manifest['active_corpora_total']}")
    print(f"- sucessos: {manifest['successful_corpora_total']}")
    print(f"- falhas: {manifest['failed_corpora_total']}")
    if ai_flags.enabled_tasks:
        print(f"- registros experimentais de IA: {ai_records_total}")
        print(f"- falhas isoladas de IA: {len(ai_errors)}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
