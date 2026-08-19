"""Sonda temporária para materializar a primeira fila cega M3 em GitHub Actions.

Este teste é propositalmente efêmero: executa a exploração pública real do MAR e
falha ao final apenas para tornar a fila cega visível nos logs do workflow. Não
expõe previsões automáticas e não deve permanecer após a captura da amostra.
"""

from __future__ import annotations

import json

from memoria_audiovisual.corpora import CORPORA
from memoria_audiovisual.digital_infrastructure.ai_surface_discovery import (
    SurfaceDiscoveryPolicy,
    discover_and_materialize_public_surfaces,
)
from scripts.build_surface_type_review_queue import build_surface_type_artifacts


def test_emit_first_real_m3_blind_queue(tmp_path):
    run_id = "m3-live-probe-v1"
    output_dir = tmp_path / "data" / "output"
    policy = SurfaceDiscoveryPolicy(
        max_depth=1,
        max_pages=4,
        timeout_seconds=8.0,
        respect_robots_txt=True,
    )
    entities = ("ina", "ecpad", "archipop", "bfi", "europeana")
    summary = []

    for entity_id in entities:
        root_url = str(CORPORA[entity_id].get("source_url") or "").strip()
        try:
            report, _report_path, _classifier_path = discover_and_materialize_public_surfaces(
                root_url,
                output_dir=output_dir,
                run_id=run_id,
                entity_id=entity_id,
                policy=policy,
            )
            summary.append({
                "entity_id": entity_id,
                "root_url": root_url,
                "status": "completed",
                "pages_total": len(report.pages),
                "fetched_pages": report.fetched_pages,
                "errors": list(report.errors),
            })
        except Exception as exc:
            summary.append({
                "entity_id": entity_id,
                "root_url": root_url,
                "status": "execution_error",
                "error_type": type(exc).__name__,
                "error": str(exc),
            })

    _predictions, review = build_surface_type_artifacts(
        output_dir / "_ai_surface_discovery" / run_id,
        max_units=20,
    )
    compact_units = []
    for unit in review.get("units", []):
        compact_units.append({
            "review_unit_id": unit.get("review_unit_id"),
            "entity_id": unit.get("entity_id"),
            "root_url": unit.get("root_url"),
            "page_url": unit.get("page_url"),
            "parent_url": unit.get("parent_url"),
            "depth": unit.get("depth"),
            "title": unit.get("title"),
            "fetch_status": unit.get("fetch_status"),
            "content_type": unit.get("content_type"),
            "media_urls": list(unit.get("media_urls") or [])[:3],
            "model_prediction_blinded": True,
            "human_surface_type": None,
            "human_is_item_level": None,
        })

    payload = {
        "probe": "M3_LIVE_BLIND_QUEUE_V1",
        "does_not_modify_official_baseline": True,
        "model_prediction_blinded": True,
        "summary": summary,
        "units_total": len(compact_units),
        "units": compact_units,
    }
    raise AssertionError("M3_LIVE_BLIND_QUEUE=" + json.dumps(payload, ensure_ascii=False))
