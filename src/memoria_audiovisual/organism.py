import json
from datetime import UTC, datetime

import pandas as pd

from .config import OUTPUT_DIR
from .corpora import CORPUS_CATEGORIES, OBSERVATORY_PROFILE, list_active_corpora


ORGANISM_MONTHLY_CYCLE_FILENAME = "observatorio_ciclo_mensal.json"
ORGANISM_ACTIVE_CORPORA_FILENAME = "observatorio_corpora_ativos.csv"
ORGANISM_CYCLE_TIMELINE_FILENAME = "observatorio_linha_do_tempo_ciclos.csv"
ORGANISM_CYCLE_RESULTS_FILENAME = "observatorio_resultados_ciclos.csv"
REFRESH_CADENCE_DAYS = {
    "mensal": 31,
}

CYCLE_TIMELINE_COLUMNS = [
    "generated_at",
    "started_at",
    "finished_at",
    "cycle_type",
    "cycle_scope",
    "refresh_cadence",
    "active_corpora_total",
    "selected_corpora_total",
    "selected_corpora_codes",
    "successful_corpora_total",
    "failed_corpora_total",
]

CYCLE_RESULTS_COLUMNS = [
    "generated_at",
    "cycle_scope",
    "code",
    "label",
    "short_label",
    "category_code",
    "coverage_level",
    "status",
    "refresh_started_at",
    "refresh_finished_at",
    "snapshot_generated_at",
    "observation_key",
    "source_status_date",
    "institutions",
    "video_links_total",
    "videos_in_curatorial_catalog",
    "error",
]

CORPUS_REFRESH_STATUS_COLUMNS = [
    "code",
    "corpus",
    "short_label",
    "category_code",
    "category_label",
    "coverage_level",
    "scope",
    "collection_completeness",
    "selection_criterion",
    "selection_limit",
    "completeness_note",
    "monthly_refresh_enabled",
    "refresh_cadence",
    "included_in_latest_cycle",
    "latest_cycle_scope",
    "latest_cycle_status",
    "last_successful_cycle_at",
    "last_snapshot_generated_at",
    "source_status_date",
    "observation_key",
    "days_since_last_observation",
    "refresh_state",
    "refresh_state_reason",
]


def _utcnow_iso():
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_utc_timestamp(value):
    if not value:
        return None
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        return None
    return parsed


def _coerce_bool(value):
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "sim", "yes"}:
            return True
        if normalized in {"false", "0", "não", "nao", "no", ""}:
            return False
    return bool(value)


def load_snapshot_metadata(corpus_def, output_dir=OUTPUT_DIR):
    snapshot_path = output_dir / corpus_def["output_files"]["snapshot_metadata"]
    if not snapshot_path.exists():
        return {}
    with snapshot_path.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def build_active_corpora_registry():
    rows = []
    for corpus_def in list_active_corpora():
        category_label = CORPUS_CATEGORIES[corpus_def["category_code"]]["label"]
        rows.append(
            {
                "code": corpus_def["code"],
                "corpus": corpus_def["label"],
                "short_label": corpus_def["short_label"],
                "category_code": corpus_def["category_code"],
                "category_label": category_label,
                "entity_level": corpus_def["entity_level"],
                "coverage_level": corpus_def["coverage_level"],
                "scope": corpus_def["scope"],
                "collection_completeness": corpus_def["collection_completeness"],
                "selection_criterion": corpus_def["selection_criterion"],
                "selection_limit": corpus_def["selection_limit"],
                "completeness_note": corpus_def["completeness_note"],
                "monthly_refresh_enabled": corpus_def.get("monthly_refresh_enabled", False),
                "run_script": corpus_def["run_script"],
                "check_script": corpus_def["check_script"],
            }
        )
    return pd.DataFrame(rows)


def write_active_corpora_registry(output_dir=OUTPUT_DIR):
    output_dir.mkdir(parents=True, exist_ok=True)
    registry_df = build_active_corpora_registry()
    registry_df.to_csv(
        output_dir / ORGANISM_ACTIVE_CORPORA_FILENAME,
        index=False,
        encoding="utf-8-sig",
    )
    return registry_df


def build_corpus_refresh_status(
    registry_df,
    *,
    cycle_manifest=None,
    cycle_results_df=None,
    snapshot_metadata_by_code=None,
    reference_timestamp=None,
):
    if registry_df is None or registry_df.empty:
        return pd.DataFrame(columns=CORPUS_REFRESH_STATUS_COLUMNS)

    cycle_results_df = cycle_results_df.copy() if cycle_results_df is not None else pd.DataFrame()
    snapshot_metadata_by_code = snapshot_metadata_by_code or {}
    reference_timestamp = _parse_utc_timestamp(reference_timestamp) or pd.Timestamp.now(tz="UTC")

    latest_cycle_results = {
        result.get("code", ""): result
        for result in (cycle_manifest or {}).get("cycle_results", [])
        if result.get("code")
    }
    latest_selected_codes = set((cycle_manifest or {}).get("selected_corpora_codes", []))
    latest_cycle_scope = (cycle_manifest or {}).get("cycle_scope", "")
    refresh_cadence = (cycle_manifest or {}).get("refresh_cadence", OBSERVATORY_PROFILE["refresh_cadence"])

    successful_history_map = {}
    if not cycle_results_df.empty and "code" in cycle_results_df.columns:
        normalized_results_df = cycle_results_df.copy()
        normalized_results_df["generated_at"] = pd.to_datetime(
            normalized_results_df.get("generated_at"),
            errors="coerce",
            utc=True,
        )
        normalized_results_df = normalized_results_df.sort_values("generated_at")
        for code, group_df in normalized_results_df.groupby("code", dropna=False):
            code_text = str(code).strip()
            if not code_text:
                continue
            success_group_df = group_df[group_df["status"] == "success"]
            if not success_group_df.empty:
                successful_history_map[code_text] = success_group_df.iloc[-1].to_dict()

    rows = []
    for _, registry_row in registry_df.iterrows():
        code = str(registry_row.get("code", "")).strip()
        snapshot_metadata = snapshot_metadata_by_code.get(code, {})
        latest_cycle_result = latest_cycle_results.get(code, {})
        latest_success_result = successful_history_map.get(code, {})

        snapshot_generated_at = (
            snapshot_metadata.get("generated_at")
            or latest_cycle_result.get("snapshot_generated_at")
            or latest_success_result.get("snapshot_generated_at")
            or latest_success_result.get("generated_at")
            or ""
        )
        last_successful_cycle_at = latest_success_result.get("generated_at", "")
        source_status_date = (
            snapshot_metadata.get("source_status_date")
            or latest_cycle_result.get("source_status_date")
            or latest_success_result.get("source_status_date")
            or ""
        )
        observation_key = (
            snapshot_metadata.get("observation_key")
            or latest_cycle_result.get("observation_key")
            or latest_success_result.get("observation_key")
            or ""
        )

        included_in_latest_cycle = code in latest_selected_codes if cycle_manifest else False
        latest_cycle_status = latest_cycle_result.get("status", "")
        last_observation_ts = _parse_utc_timestamp(snapshot_generated_at) or _parse_utc_timestamp(
            last_successful_cycle_at
        )
        days_since_last_observation = None
        if last_observation_ts is not None:
            days_since_last_observation = int((reference_timestamp - last_observation_ts).total_seconds() // 86400)

        cadence_days = REFRESH_CADENCE_DAYS.get(refresh_cadence, 31)
        if last_observation_ts is None:
            refresh_state = "Sem histórico materializado"
            refresh_state_reason = (
                "O organismo ainda não materializou observações anteriores para este corpus."
            )
        elif included_in_latest_cycle and latest_cycle_status == "success":
            refresh_state = "Atualizado no último ciclo"
            refresh_state_reason = (
                "O corpus participou do ciclo mais recente do organismo e concluiu a atualização com sucesso."
            )
        elif included_in_latest_cycle and latest_cycle_status and latest_cycle_status != "success":
            refresh_state = "Falha no último ciclo"
            refresh_state_reason = (
                "O corpus participou do ciclo mais recente, mas a atualização não foi concluída com sucesso."
            )
        elif latest_cycle_scope == "parcial" and latest_selected_codes and code not in latest_selected_codes:
            refresh_state = "Pendente no ciclo parcial mais recente"
            refresh_state_reason = (
                "O ciclo mais recente do organismo foi parcial e este corpus ficou fora da rodada."
            )
        elif days_since_last_observation <= cadence_days + 9:
            refresh_state = "Em dia"
            refresh_state_reason = (
                "A última observação materializada permanece dentro da margem esperada para a cadência mensal."
            )
        elif days_since_last_observation <= (cadence_days * 2) + 9:
            refresh_state = "Atenção"
            refresh_state_reason = (
                "A última observação começa a se afastar da cadência mensal e merece nova atualização."
            )
        else:
            refresh_state = "Atualização atrasada"
            refresh_state_reason = (
                "A última observação ultrapassou o intervalo esperado para a cadência mensal do organismo."
            )

        rows.append(
            {
                "code": code,
                "corpus": registry_row.get("corpus", ""),
                "short_label": registry_row.get("short_label", ""),
                "category_code": registry_row.get("category_code", ""),
                "category_label": registry_row.get("category_label", ""),
                "coverage_level": registry_row.get("coverage_level", ""),
                "scope": registry_row.get("scope", ""),
                "collection_completeness": registry_row.get("collection_completeness", ""),
                "selection_criterion": registry_row.get("selection_criterion", ""),
                "selection_limit": registry_row.get("selection_limit", ""),
                "completeness_note": registry_row.get("completeness_note", ""),
                "monthly_refresh_enabled": _coerce_bool(
                    registry_row.get("monthly_refresh_enabled", False)
                ),
                "refresh_cadence": refresh_cadence,
                "included_in_latest_cycle": included_in_latest_cycle,
                "latest_cycle_scope": latest_cycle_scope,
                "latest_cycle_status": latest_cycle_status,
                "last_successful_cycle_at": last_successful_cycle_at,
                "last_snapshot_generated_at": snapshot_generated_at,
                "source_status_date": source_status_date,
                "observation_key": observation_key,
                "days_since_last_observation": days_since_last_observation,
                "refresh_state": refresh_state,
                "refresh_state_reason": refresh_state_reason,
            }
        )

    refresh_status_df = pd.DataFrame(rows, columns=CORPUS_REFRESH_STATUS_COLUMNS)
    if not refresh_status_df.empty:
        state_order = {
            "Falha no último ciclo": 0,
            "Atualização atrasada": 1,
            "Pendente no ciclo parcial mais recente": 2,
            "Atenção": 3,
            "Sem histórico materializado": 4,
            "Em dia": 5,
            "Atualizado no último ciclo": 6,
        }
        refresh_status_df["_sort_order"] = refresh_status_df["refresh_state"].map(state_order).fillna(99)
        refresh_status_df = refresh_status_df.sort_values(
            ["_sort_order", "category_label", "short_label"],
            ascending=[True, True, True],
        ).drop(columns="_sort_order")
    return refresh_status_df


def build_monthly_cycle_manifest(*, started_at, finished_at, cycle_results, selected_corpora=None):
    selected_corpora = selected_corpora or []
    active_corpora = list_active_corpora()
    return {
        "organism": OBSERVATORY_PROFILE["label"],
        "role": OBSERVATORY_PROFILE["role"],
        "refresh_cadence": OBSERVATORY_PROFILE["refresh_cadence"],
        "generated_at": _utcnow_iso(),
        "started_at": started_at,
        "finished_at": finished_at,
        "cycle_type": "mensal",
        "cycle_scope": "parcial" if selected_corpora and len(selected_corpora) != len(active_corpora) else "completo",
        "active_corpora_total": len(active_corpora),
        "selected_corpora_total": len(selected_corpora) if selected_corpora else len(active_corpora),
        "selected_corpora_codes": selected_corpora if selected_corpora else [corpus_def["code"] for corpus_def in active_corpora],
        "successful_corpora_total": sum(1 for result in cycle_results if result["status"] == "success"),
        "failed_corpora_total": sum(1 for result in cycle_results if result["status"] != "success"),
        "cycle_results": cycle_results,
    }


def write_monthly_cycle_manifest(
    *,
    started_at,
    finished_at,
    cycle_results,
    selected_corpora=None,
    output_dir=OUTPUT_DIR,
):
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_monthly_cycle_manifest(
        started_at=started_at,
        finished_at=finished_at,
        cycle_results=cycle_results,
        selected_corpora=selected_corpora,
    )
    path = output_dir / ORGANISM_MONTHLY_CYCLE_FILENAME
    with path.open("w", encoding="utf-8") as file_handle:
        json.dump(manifest, file_handle, ensure_ascii=False, indent=2)
    return manifest


def _load_csv_if_exists(path, columns):
    if not path.exists():
        return pd.DataFrame(columns=columns)
    dataframe = pd.read_csv(path)
    for column in columns:
        if column not in dataframe.columns:
            dataframe[column] = ""
    return dataframe


def build_cycle_timeline_entry(manifest):
    return pd.DataFrame(
        [
            {
                "generated_at": manifest.get("generated_at", ""),
                "started_at": manifest.get("started_at", ""),
                "finished_at": manifest.get("finished_at", ""),
                "cycle_type": manifest.get("cycle_type", ""),
                "cycle_scope": manifest.get("cycle_scope", ""),
                "refresh_cadence": manifest.get("refresh_cadence", ""),
                "active_corpora_total": manifest.get("active_corpora_total", 0),
                "selected_corpora_total": manifest.get("selected_corpora_total", 0),
                "selected_corpora_codes": ", ".join(manifest.get("selected_corpora_codes", [])),
                "successful_corpora_total": manifest.get("successful_corpora_total", 0),
                "failed_corpora_total": manifest.get("failed_corpora_total", 0),
            }
        ],
        columns=CYCLE_TIMELINE_COLUMNS,
    )


def build_cycle_results_entries(manifest):
    rows = []
    for result in manifest.get("cycle_results", []):
        rows.append(
            {
                "generated_at": manifest.get("generated_at", ""),
                "cycle_scope": manifest.get("cycle_scope", ""),
                "code": result.get("code", ""),
                "label": result.get("label", ""),
                "short_label": result.get("short_label", ""),
                "category_code": result.get("category_code", ""),
                "coverage_level": result.get("coverage_level", ""),
                "status": result.get("status", ""),
                "refresh_started_at": result.get("refresh_started_at", ""),
                "refresh_finished_at": result.get("refresh_finished_at", ""),
                "snapshot_generated_at": result.get("snapshot_generated_at", ""),
                "observation_key": result.get("observation_key", ""),
                "source_status_date": result.get("source_status_date", ""),
                "institutions": result.get("institutions", 0),
                "video_links_total": result.get("video_links_total", 0),
                "videos_in_curatorial_catalog": result.get("videos_in_curatorial_catalog", 0),
                "error": result.get("error", ""),
            }
        )
    return pd.DataFrame(rows, columns=CYCLE_RESULTS_COLUMNS)


def write_cycle_history(manifest, output_dir=OUTPUT_DIR):
    output_dir.mkdir(parents=True, exist_ok=True)
    timeline_path = output_dir / ORGANISM_CYCLE_TIMELINE_FILENAME
    results_path = output_dir / ORGANISM_CYCLE_RESULTS_FILENAME

    timeline_history_df = _load_csv_if_exists(timeline_path, CYCLE_TIMELINE_COLUMNS)
    results_history_df = _load_csv_if_exists(results_path, CYCLE_RESULTS_COLUMNS)

    current_timeline_df = build_cycle_timeline_entry(manifest)
    current_results_df = build_cycle_results_entries(manifest)

    timeline_history_df = pd.concat([timeline_history_df, current_timeline_df], ignore_index=True)
    timeline_history_df = timeline_history_df.drop_duplicates(subset=["generated_at"], keep="last")
    timeline_history_df.to_csv(timeline_path, index=False, encoding="utf-8-sig")

    results_history_df = pd.concat([results_history_df, current_results_df], ignore_index=True)
    if not results_history_df.empty:
        results_history_df = results_history_df.drop_duplicates(
            subset=["generated_at", "code"],
            keep="last",
        )
    results_history_df.to_csv(results_path, index=False, encoding="utf-8-sig")

    return {
        "cycle_timeline": timeline_history_df,
        "cycle_results": results_history_df,
    }


__all__ = [
    "ORGANISM_ACTIVE_CORPORA_FILENAME",
    "CORPUS_REFRESH_STATUS_COLUMNS",
    "ORGANISM_CYCLE_RESULTS_FILENAME",
    "ORGANISM_CYCLE_TIMELINE_FILENAME",
    "ORGANISM_MONTHLY_CYCLE_FILENAME",
    "build_active_corpora_registry",
    "build_corpus_refresh_status",
    "build_cycle_results_entries",
    "build_cycle_timeline_entry",
    "build_monthly_cycle_manifest",
    "load_snapshot_metadata",
    "write_active_corpora_registry",
    "write_cycle_history",
    "write_monthly_cycle_manifest",
]
