#!/usr/bin/env python3
"""Gera candidatos para a Porta 2 exclusivamente a partir de outputs reais do MAR.

O script aplica a Porta 1 (detecção terminológica/contextual) a registros já
materializados em ``data/output``. O resultado NÃO declara uso de IA no acervo:
é apenas uma fila para validar unidade audiovisual, pertencimento, acesso público
e vínculo da evidência.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Iterator

from memoria_audiovisual.corpora import CORPORA
from memoria_audiovisual.digital_infrastructure.ai_content_production import (
    classify_ai_content_usage,
)

SUPPORTED_SUFFIXES = {".csv", ".json", ".jsonl"}
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
SKIP_PARTS = {
    "analytics",
    "_ai_surface_discovery",
    "operational-baseline",
    "scientific-coverage",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path("data/output"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/output/ai_archive_candidate_queue_v1.json"),
    )
    parser.add_argument("--max-candidates", type=int, default=40)
    return parser.parse_args()


def active_codes() -> tuple[str, ...]:
    codes = [
        str(code)
        for code, meta in CORPORA.items()
        if bool(meta.get("organism_active")) and bool(meta.get("monthly_refresh_enabled"))
    ]
    return tuple(sorted(codes, key=len, reverse=True))


def entity_for_path(path: Path, *, root: Path, codes: tuple[str, ...]) -> str | None:
    relative = path.relative_to(root)
    parts = [part.lower().replace("-", "_") for part in relative.parts]
    stem = path.stem.lower().replace("-", "_")
    for code in codes:
        norm = code.lower().replace("-", "_")
        if stem == norm or stem.startswith(norm + "_") or norm in parts[:-1]:
            return code
    return None


def scalar_texts(record: dict[str, object]) -> list[str]:
    texts: list[str] = []
    for value in record.values():
        if isinstance(value, str) and value.strip():
            texts.append(value.strip())
        elif isinstance(value, (int, float, bool)):
            texts.append(str(value))
        elif isinstance(value, list):
            texts.extend(str(item) for item in value if isinstance(item, (str, int, float)))
    return texts


def record_url(record: dict[str, object]) -> str | None:
    preferred: list[str] = []
    fallback: list[str] = []
    for key, value in record.items():
        if not isinstance(value, str):
            continue
        urls = URL_RE.findall(value)
        if not urls:
            continue
        key_norm = key.lower()
        if any(token in key_norm for token in ("item", "video", "record", "detail", "url", "link")):
            preferred.extend(urls)
        else:
            fallback.extend(urls)
    return (preferred or fallback or [None])[0]


def record_title(record: dict[str, object]) -> str | None:
    for key in ("title", "titulo", "titre", "name", "label", "heading"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def iter_json_dicts(value: object) -> Iterator[dict[str, object]]:
    if isinstance(value, dict):
        if record_url(value):
            yield value
        for child in value.values():
            if isinstance(child, (dict, list)):
                yield from iter_json_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_json_dicts(child)


def iter_records(path: Path) -> Iterator[tuple[int, dict[str, object]]]:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for index, row in enumerate(csv.DictReader(handle), start=1):
                yield index, dict(row)
        return

    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8") as handle:
            for index, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    yield index, value
        return

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return
    for index, record in enumerate(iter_json_dicts(value), start=1):
        yield index, record


def candidate_id(entity_id: str, source_file: str, index: int, item_url: str) -> str:
    digest = hashlib.sha256(
        f"{entity_id}\n{source_file}\n{index}\n{item_url}".encode("utf-8")
    ).hexdigest()[:16]
    return f"{entity_id}-archive-ai-{digest}"


def build_candidates(output_root: Path, *, max_candidates: int) -> list[dict[str, object]]:
    codes = active_codes()
    candidates: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()

    files = sorted(
        path
        for path in output_root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_SUFFIXES
        and not any(part in SKIP_PARTS for part in path.parts)
        and not path.name.startswith("ai_archive_candidate_queue")
    )

    for path in files:
        entity_id = entity_for_path(path, root=output_root, codes=codes)
        if entity_id is None:
            continue
        relative = path.relative_to(output_root).as_posix()
        for index, record in iter_records(path):
            item_url = record_url(record)
            if not item_url:
                continue
            dedupe = (entity_id, item_url)
            if dedupe in seen:
                continue
            observation = classify_ai_content_usage(
                entity_id=entity_id,
                item_id=candidate_id(entity_id, relative, index, item_url),
                texts=scalar_texts(record),
                source_url=item_url,
            )
            if not observation.is_ai_positive:
                continue
            seen.add(dedupe)
            candidates.append(
                {
                    "review_unit_id": observation.item_id,
                    "entity_id": entity_id,
                    "source_output_file": relative,
                    "source_record_index": index,
                    "item_url": item_url,
                    "title": record_title(record),
                    "gate1_terminology_context_positive": True,
                    "gate1_evidence_strength": observation.evidence_strength,
                    "gate1_matched_evidence": observation.excerpt,
                    "gate2_prediction_blinded": True,
                    "human_is_item_level_observation": None,
                    "human_item_in_observed_corpus": None,
                    "human_public_surface_accessible": None,
                    "human_evidence_linked_to_item": None,
                    "human_archive_ai_label": None,
                    "review_status": "pending",
                }
            )
            if len(candidates) >= max_candidates:
                return candidates
    return candidates


def main() -> int:
    args = parse_args()
    candidates = build_candidates(args.output_root, max_candidates=args.max_candidates)
    payload = {
        "schema_version": "1.1.0",
        "queue_id": "ai-archive-two-gate-candidates-v1",
        "stage": "t2a_ai_archive_gate2_validation",
        "status": "pending_human_review" if candidates else "no_candidates_found",
        "is_prevalence_sample": False,
        "does_not_modify_official_baseline": True,
        "source_rule": "candidates originate only from materialized records under data/output associated with active MAR corpora",
        "public_access_rule": "publicly observable item surface is required, consistent with the MAR incorporation eligibility gate",
        "decision_rule": "archive positive only if gate1 terminology/context is positive AND observation is an audiovisual item/version/segment AND item belongs to observed corpus AND public item surface is accessible AND evidence is linked to that item",
        "gate2_prediction_blinding": True,
        "candidates_total": len(candidates),
        "units": candidates,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "queue_id": payload["queue_id"],
        "status": payload["status"],
        "candidates_total": len(candidates),
        "preview": [
            {
                "review_unit_id": row["review_unit_id"],
                "entity_id": row["entity_id"],
                "title": row["title"],
                "item_url": row["item_url"],
                "source_output_file": row["source_output_file"],
                "gate1_matched_evidence": row["gate1_matched_evidence"],
            }
            for row in candidates[:12]
        ],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
