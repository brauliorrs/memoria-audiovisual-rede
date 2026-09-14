#!/usr/bin/env python3
"""Classifica a amostra cega de IA no conteúdo sem expor previsões na fila humana.

O modo padrão usa somente os metadados já materializados. Com ``--fetch-surfaces``
a ferramenta consulta a página pública de cada item com profundidade zero, respeita
robots.txt e materializa a evidência de superfície separadamente. A execução com
rede não deve ser usada como gate de CI, pois depende de fontes externas.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from memoria_audiovisual.digital_infrastructure.ai_content_production import (
    classify_ai_content_usage,
)
from memoria_audiovisual.digital_infrastructure.ai_surface_discovery import (
    SurfaceDiscoveryPolicy,
    discover_and_materialize_public_surfaces,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--surface-output-dir", type=Path, default=Path("data/output"))
    parser.add_argument("--run-id", default="t2a-content-blind-v1")
    parser.add_argument("--fetch-surfaces", action="store_true")
    return parser.parse_args()


def _metadata_text(unit: dict[str, object]) -> str:
    return "\n".join(
        str(unit.get(key) or "").strip()
        for key in ("title", "subject", "description", "published_at")
        if str(unit.get(key) or "").strip()
    )


def _item_scoped_surface_text(*, title: str, page_text: str, metadata: str, structured: str) -> str:
    """Reduz ruído de menus/recomendações ao redor do item principal.

    Metadados e JSON-LD são preservados integralmente. Do texto visível, usamos a
    vizinhança da primeira ocorrência do título quando possível. Isso reduz falsos
    positivos causados por cards de conteúdo relacionado no rodapé da página.
    """
    visible = page_text or ""
    title_norm = title.strip().lower()
    visible_lower = visible.lower()
    if title_norm and title_norm in visible_lower:
        center = visible_lower.find(title_norm)
        left = max(0, center - 2500)
        right = min(len(visible), center + len(title) + 5500)
        visible = visible[left:right]
    else:
        visible = visible[:8000]
    return "\n".join(part for part in (metadata, structured, visible) if part)


def assess_unit(
    unit: dict[str, object],
    *,
    fetch_surfaces: bool,
    surface_output_dir: Path,
    run_id: str,
) -> dict[str, object]:
    texts = [_metadata_text(unit)]
    surface_status = "not_requested"
    surface_evidence_urls: list[str] = []
    surface_report_path: str | None = None
    surface_classifier_path: str | None = None

    if fetch_surfaces:
        try:
            report, report_path, classifier_path = discover_and_materialize_public_surfaces(
                str(unit["item_url"]),
                output_dir=surface_output_dir,
                run_id=run_id,
                entity_id=str(unit["review_unit_id"]),
                policy=SurfaceDiscoveryPolicy(max_depth=0, max_pages=1),
            )
            surface_report_path = str(report_path)
            surface_classifier_path = str(classifier_path)
            fetched = [page for page in report.pages if page.fetch_status == "fetched"]
            if fetched:
                surface_status = "fetched"
                for page in fetched:
                    texts.append(
                        _item_scoped_surface_text(
                            title=str(unit.get("title") or ""),
                            page_text=page.text,
                            metadata=page.metadata_text,
                            structured=page.structured_text,
                        )
                    )
                    surface_evidence_urls.append(page.url)
            else:
                surface_status = "not_fetched"
        except Exception as exc:  # fail-open: o artefato registra a falha externa
            surface_status = f"error:{type(exc).__name__}"

    observation = classify_ai_content_usage(
        entity_id=str(unit["entity_id"]),
        item_id=str(unit["review_unit_id"]),
        texts=texts,
        source_url=str(unit["item_url"]),
        language=str(unit.get("language_group") or "") or None,
        date_bucket=str(unit.get("published_at") or "") or None,
    )
    return {
        "review_unit_id": unit["review_unit_id"],
        "entity_id": unit["entity_id"],
        "item_url": unit["item_url"],
        "assessment_stage": "item_surface" if fetch_surfaces else "metadata_triage",
        "predicted_usage_class": observation.usage_class,
        "predicted_positive": observation.is_ai_positive,
        "evidence_strength": observation.evidence_strength,
        "matched_evidence": observation.excerpt,
        "surface_status": surface_status,
        "surface_evidence_urls": surface_evidence_urls,
        "surface_report_path": surface_report_path,
        "surface_classifier_path": surface_classifier_path,
    }


def main() -> int:
    args = parse_args()
    payload = json.loads(args.queue.read_text(encoding="utf-8"))
    units = payload.get("units")
    if not isinstance(units, list) or not units:
        raise SystemExit("fila cega sem units válidas")

    predictions = [
        assess_unit(
            unit,
            fetch_surfaces=args.fetch_surfaces,
            surface_output_dir=args.surface_output_dir,
            run_id=args.run_id,
        )
        for unit in units
    ]
    class_counts = Counter(str(row["predicted_usage_class"]) for row in predictions)
    result = {
        "schema_version": "1.0.0",
        "prediction_set_id": "ai-content-blind-predictions-v1",
        "queue_id": payload.get("queue_id"),
        "run_id": args.run_id,
        "assessment_stage": "item_surface" if args.fetch_surfaces else "metadata_triage",
        "does_not_modify_official_baseline": True,
        "predictions_total": len(predictions),
        "positive_predictions": sum(bool(row["predicted_positive"]) for row in predictions),
        "class_counts": dict(sorted(class_counts.items())),
        "predictions": predictions,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
