from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import analysis as analysis_utils


CORPUS_TIMELINE_COLUMNS = [
    "dataset",
    "observation_key",
    "snapshot_generated_at",
    "source_status_date",
    "raw_outputs_last_modified_at",
    "analytic_outputs_last_modified_at",
    "generated_by",
    "institutions",
    "institutions_with_website",
    "institutions_with_video_links",
    "video_links_total",
    "videos_in_curatorial_catalog",
    "visibility_categories",
    "theme_categories",
    "archive_type_categories",
    "platforms_detected",
    "countries_with_videos",
]

INSTITUTION_TIMELINE_COLUMNS = [
    "dataset",
    "observation_key",
    "snapshot_generated_at",
    "source_status_date",
    "generated_by",
    "institution",
    "slug",
    "repository_code",
    "country",
    "continent",
    "archive_type",
    "website_available",
    "partner_site",
    "partner_domain",
    "status",
    "http_code",
    "integrity_status",
    "availability_group",
    "audiovisual_visibility",
    "access_regime",
    "video_links_found_total",
    "embedded_video_signals_total",
    "candidate_internal_pages",
    "final_url",
]

EXTINCTION_SIGNALS_COLUMNS = [
    "dataset",
    "observation_key",
    "snapshot_generated_at",
    "institution",
    "slug",
    "repository_code",
    "signal_type",
    "signal_level",
    "first_seen_at",
    "last_seen_at",
    "rounds_since_last_seen",
    "consecutive_unavailable_observations",
    "previous_integrity_status",
    "current_integrity_status",
    "previous_video_links",
    "current_video_links",
    "note",
]

UNAVAILABLE_INTEGRITY_STATUSES = {"suspeito", "restrito", "quebrado", "instavel", "sem_site"}


def _load_csv_if_exists(path: Path, columns: list[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=columns)
    dataframe = pd.read_csv(path)
    for column in columns:
        if column not in dataframe.columns:
            dataframe[column] = ""
    return dataframe


def _append_unique(history_df: pd.DataFrame, new_df: pd.DataFrame, subset: list[str]) -> pd.DataFrame:
    if history_df.empty:
        combined = new_df.copy()
    else:
        combined = pd.concat([history_df, new_df], ignore_index=True)
    if combined.empty:
        return combined
    return combined.drop_duplicates(subset=subset, keep="last")


def _safe_int(value) -> int:
    parsed = pd.to_numeric(pd.Series([value]), errors="coerce").fillna(0).iloc[0]
    return int(parsed)


def build_corpus_timeline_entry(snapshot_metadata: dict) -> pd.DataFrame:
    counts = snapshot_metadata.get("counts", {})
    return pd.DataFrame(
        [
            {
                "dataset": snapshot_metadata.get("dataset", ""),
                "observation_key": snapshot_metadata.get("observation_key", ""),
                "snapshot_generated_at": snapshot_metadata.get("generated_at", ""),
                "source_status_date": snapshot_metadata.get("source_status_date", ""),
                "raw_outputs_last_modified_at": snapshot_metadata.get("raw_outputs_last_modified_at", ""),
                "analytic_outputs_last_modified_at": snapshot_metadata.get("analytic_outputs_last_modified_at", ""),
                "generated_by": snapshot_metadata.get("generated_by", ""),
                "institutions": counts.get("institutions", 0),
                "institutions_with_website": counts.get("institutions_with_website", 0),
                "institutions_with_video_links": counts.get("institutions_with_video_links", 0),
                "video_links_total": counts.get("video_links_total", 0),
                "videos_in_curatorial_catalog": counts.get("videos_in_curatorial_catalog", 0),
                "visibility_categories": counts.get("visibility_categories", 0),
                "theme_categories": counts.get("theme_categories", 0),
                "archive_type_categories": counts.get("archive_type_categories", 0),
                "platforms_detected": counts.get("platforms_detected", 0),
                "countries_with_videos": counts.get("countries_with_videos", 0),
            }
        ],
        columns=CORPUS_TIMELINE_COLUMNS,
    )


def build_institution_timeline_entries(
    snapshot_metadata: dict,
    summary_df: pd.DataFrame,
    analysis_frames: dict,
) -> pd.DataFrame:
    analytic_summary_df = analysis_frames.get("analytic_summary")
    if analytic_summary_df is None or analytic_summary_df.empty:
        analytic_summary_df = analysis_utils.build_summary_analysis_df(summary_df)

    if analytic_summary_df.empty:
        return pd.DataFrame(columns=INSTITUTION_TIMELINE_COLUMNS)

    rows = []
    for _, row in analytic_summary_df.iterrows():
        rows.append(
            {
                "dataset": snapshot_metadata.get("dataset", ""),
                "observation_key": snapshot_metadata.get("observation_key", ""),
                "snapshot_generated_at": snapshot_metadata.get("generated_at", ""),
                "source_status_date": snapshot_metadata.get("source_status_date", ""),
                "generated_by": snapshot_metadata.get("generated_by", ""),
                "institution": row.get("institution", ""),
                "slug": row.get("slug", ""),
                "repository_code": row.get("repository_code", ""),
                "country": row.get("country", ""),
                "continent": row.get("continent", ""),
                "archive_type": row.get("archive_type", ""),
                "website_available": row.get("website_available", False),
                "partner_site": row.get("partner_site", ""),
                "partner_domain": row.get("partner_domain", ""),
                "status": row.get("status", ""),
                "http_code": row.get("http_code", ""),
                "integrity_status": row.get("integrity_status", ""),
                "availability_group": row.get("availability_group", ""),
                "audiovisual_visibility": row.get("audiovisual_visibility", ""),
                "access_regime": row.get("access_regime", ""),
                "video_links_found_total": _safe_int(row.get("video_links_found_total", 0)),
                "embedded_video_signals_total": _safe_int(row.get("embedded_video_signals_total", 0)),
                "candidate_internal_pages": _safe_int(row.get("candidate_internal_pages", 0)),
                "final_url": row.get("final_url", ""),
            }
        )
    return pd.DataFrame(rows, columns=INSTITUTION_TIMELINE_COLUMNS)


def _count_consecutive_unavailable(history_rows: pd.DataFrame) -> int:
    total = 0
    for _, row in history_rows.sort_values("snapshot_generated_at", ascending=False).iterrows():
        if str(row.get("integrity_status", "")).strip() in UNAVAILABLE_INTEGRITY_STATUSES:
            total += 1
        else:
            break
    return total


def build_extinction_signals(
    corpus_timeline_df: pd.DataFrame,
    institution_timeline_df: pd.DataFrame,
    *,
    dataset: str,
    current_observation_key: str,
    current_summary_df: pd.DataFrame,
) -> pd.DataFrame:
    if corpus_timeline_df.empty:
        return pd.DataFrame(columns=EXTINCTION_SIGNALS_COLUMNS)

    corpus_history = corpus_timeline_df.loc[corpus_timeline_df["dataset"] == dataset].copy()
    if corpus_history.empty:
        return pd.DataFrame(columns=EXTINCTION_SIGNALS_COLUMNS)

    corpus_history["snapshot_generated_at"] = pd.to_datetime(
        corpus_history["snapshot_generated_at"],
        errors="coerce",
        utc=True,
    )
    corpus_history = corpus_history.sort_values("snapshot_generated_at").drop_duplicates(
        subset=["dataset", "observation_key"],
        keep="last",
    )
    observation_keys = corpus_history["observation_key"].astype(str).tolist()
    if current_observation_key not in observation_keys:
        return pd.DataFrame(columns=EXTINCTION_SIGNALS_COLUMNS)

    institution_history = institution_timeline_df.loc[
        institution_timeline_df["dataset"] == dataset
    ].copy()
    if institution_history.empty:
        return pd.DataFrame(columns=EXTINCTION_SIGNALS_COLUMNS)

    institution_history["snapshot_generated_at"] = pd.to_datetime(
        institution_history["snapshot_generated_at"],
        errors="coerce",
        utc=True,
    )
    institution_history = institution_history.sort_values("snapshot_generated_at")

    current_slugs = set(
        current_summary_df.get("slug", pd.Series(dtype="object"))
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .tolist()
    )
    current_index = observation_keys.index(current_observation_key)

    signals = []
    for slug, group in institution_history.groupby("slug", dropna=False):
        group = group.sort_values("snapshot_generated_at")
        slug_text = str(slug).strip()
        if not slug_text:
            continue

        first_row = group.iloc[0]
        last_row = group.iloc[-1]
        last_observation_key = str(last_row["observation_key"])
        last_index = observation_keys.index(last_observation_key) if last_observation_key in observation_keys else -1

        if slug_text not in current_slugs and last_observation_key != current_observation_key:
            rounds_since_last_seen = current_index - last_index
            signals.append(
                {
                    "dataset": dataset,
                    "observation_key": current_observation_key,
                    "snapshot_generated_at": corpus_history.iloc[current_index]["snapshot_generated_at"],
                    "institution": last_row.get("institution", ""),
                    "slug": slug_text,
                    "repository_code": last_row.get("repository_code", ""),
                    "signal_type": "ausencia_na_rodada_atual",
                    "signal_level": "alto" if rounds_since_last_seen >= 2 else "atencao",
                    "first_seen_at": first_row["snapshot_generated_at"],
                    "last_seen_at": last_row["snapshot_generated_at"],
                    "rounds_since_last_seen": rounds_since_last_seen,
                    "consecutive_unavailable_observations": 0,
                    "previous_integrity_status": last_row.get("integrity_status", ""),
                    "current_integrity_status": "",
                    "previous_video_links": _safe_int(last_row.get("video_links_found_total", 0)),
                    "current_video_links": 0,
                    "note": (
                        "A instituição apareceu em observações anteriores, mas não foi "
                        "encontrada na rodada atual. Isso pode indicar retirada, fusão, "
                        "reclassificação ou possível extinção do registro."
                    ),
                }
            )
            continue

        current_rows = group.loc[group["observation_key"].astype(str) == current_observation_key]
        if current_rows.empty:
            continue
        current_row = current_rows.iloc[-1]
        previous_rows = group.loc[group["observation_key"].astype(str) != current_observation_key]
        previous_row = previous_rows.iloc[-1] if not previous_rows.empty else None

        if previous_row is not None:
            current_status = str(current_row.get("integrity_status", "")).strip()
            previous_status = str(previous_row.get("integrity_status", "")).strip()
            consecutive_unavailable = _count_consecutive_unavailable(group)
            if (
                current_status in UNAVAILABLE_INTEGRITY_STATUSES
                and previous_status in UNAVAILABLE_INTEGRITY_STATUSES
                and consecutive_unavailable >= 2
            ):
                signals.append(
                    {
                        "dataset": dataset,
                        "observation_key": current_observation_key,
                        "snapshot_generated_at": current_row["snapshot_generated_at"],
                        "institution": current_row.get("institution", ""),
                        "slug": slug_text,
                        "repository_code": current_row.get("repository_code", ""),
                        "signal_type": "indisponibilidade_digital_reincidente",
                        "signal_level": "alto" if consecutive_unavailable >= 3 else "moderado",
                        "first_seen_at": first_row["snapshot_generated_at"],
                        "last_seen_at": current_row["snapshot_generated_at"],
                        "rounds_since_last_seen": 0,
                        "consecutive_unavailable_observations": consecutive_unavailable,
                        "previous_integrity_status": previous_status,
                        "current_integrity_status": current_status,
                        "previous_video_links": _safe_int(previous_row.get("video_links_found_total", 0)),
                        "current_video_links": _safe_int(current_row.get("video_links_found_total", 0)),
                        "note": (
                            "A instituição segue presente, mas acumula indisponibilidade "
                            "digital em observações consecutivas, o que merece atenção "
                            "como risco de apagamento ou retração pública."
                        ),
                    }
                )

            previous_video_links = _safe_int(previous_row.get("video_links_found_total", 0))
            current_video_links = _safe_int(current_row.get("video_links_found_total", 0))
            if previous_video_links > 0 and current_video_links == 0:
                signals.append(
                    {
                        "dataset": dataset,
                        "observation_key": current_observation_key,
                        "snapshot_generated_at": current_row["snapshot_generated_at"],
                        "institution": current_row.get("institution", ""),
                        "slug": slug_text,
                        "repository_code": current_row.get("repository_code", ""),
                        "signal_type": "perda_de_evidencia_audiovisual",
                        "signal_level": "atencao",
                        "first_seen_at": first_row["snapshot_generated_at"],
                        "last_seen_at": current_row["snapshot_generated_at"],
                        "rounds_since_last_seen": 0,
                        "consecutive_unavailable_observations": 0,
                        "previous_integrity_status": previous_status,
                        "current_integrity_status": current_row.get("integrity_status", ""),
                        "previous_video_links": previous_video_links,
                        "current_video_links": current_video_links,
                        "note": (
                            "A instituição já apresentou links de vídeo em observações "
                            "anteriores, mas deixou de apresentá-los na rodada atual."
                        ),
                    }
                )

    if not signals:
        return pd.DataFrame(columns=EXTINCTION_SIGNALS_COLUMNS)

    signals_df = pd.DataFrame(signals, columns=EXTINCTION_SIGNALS_COLUMNS)
    signals_df["snapshot_generated_at"] = (
        pd.to_datetime(signals_df["snapshot_generated_at"], errors="coerce", utc=True)
        .dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        .fillna("")
    )
    signals_df["first_seen_at"] = (
        pd.to_datetime(signals_df["first_seen_at"], errors="coerce", utc=True)
        .dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        .fillna("")
    )
    signals_df["last_seen_at"] = (
        pd.to_datetime(signals_df["last_seen_at"], errors="coerce", utc=True)
        .dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        .fillna("")
    )
    return signals_df


def write_timeline_outputs(
    output_dir: Path,
    *,
    dataset: str,
    output_files: dict,
    snapshot_metadata: dict,
    summary_df: pd.DataFrame,
    analysis_frames: dict,
) -> dict:
    corpus_timeline_path = output_dir / output_files["timeline_corpus"]
    institution_timeline_path = output_dir / output_files["timeline_institutions"]
    extinction_signals_path = output_dir / output_files["extinction_signals"]

    corpus_history_df = _load_csv_if_exists(corpus_timeline_path, CORPUS_TIMELINE_COLUMNS)
    institution_history_df = _load_csv_if_exists(institution_timeline_path, INSTITUTION_TIMELINE_COLUMNS)

    current_corpus_entry_df = build_corpus_timeline_entry(snapshot_metadata)
    current_institution_entries_df = build_institution_timeline_entries(
        snapshot_metadata,
        summary_df,
        analysis_frames,
    )

    corpus_history_df = _append_unique(
        corpus_history_df,
        current_corpus_entry_df,
        ["dataset", "observation_key"],
    )
    institution_history_df = _append_unique(
        institution_history_df,
        current_institution_entries_df,
        ["dataset", "observation_key", "slug"],
    )

    extinction_signals_df = build_extinction_signals(
        corpus_history_df,
        institution_history_df,
        dataset=dataset,
        current_observation_key=snapshot_metadata.get("observation_key", ""),
        current_summary_df=summary_df,
    )

    corpus_history_df.to_csv(corpus_timeline_path, index=False, encoding="utf-8-sig")
    institution_history_df.to_csv(institution_timeline_path, index=False, encoding="utf-8-sig")
    extinction_signals_df.to_csv(extinction_signals_path, index=False, encoding="utf-8-sig")

    return {
        "timeline_corpus": corpus_history_df,
        "timeline_institutions": institution_history_df,
        "extinction_signals": extinction_signals_df,
    }


__all__ = [
    "CORPUS_TIMELINE_COLUMNS",
    "EXTINCTION_SIGNALS_COLUMNS",
    "INSTITUTION_TIMELINE_COLUMNS",
    "build_corpus_timeline_entry",
    "build_extinction_signals",
    "build_institution_timeline_entries",
    "write_timeline_outputs",
]
