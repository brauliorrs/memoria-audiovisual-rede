"""Integra a fila europeia ao gate de incorporação científica.

A integração é deliberadamente conservadora: a fila pode ser avaliada e priorizada,
mas nenhum candidato é promovido para ``CORPORA``. Fontes de descoberta e diretórios
são preservados como fontes de fila, enquanto apenas candidatos individuais passam
pelo gate de elegibilidade.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from .eligibility import (
    EligibilityResult,
    IncorporationCandidate,
    evaluate_scientific_incorporation,
)

SOURCE_ONLY_STATUS = "source_only"


@dataclass(frozen=True, slots=True)
class EuropeanQueueEvaluation:
    unit_code: str
    unit_label: str
    queue_rank: int | None
    queue_layer: str
    evaluation_status: str
    gate_result: EligibilityResult | None
    source_row: Mapping[str, str]

    def to_dict(self) -> dict[str, object]:
        return {
            "unit_code": self.unit_code,
            "unit_label": self.unit_label,
            "queue_rank": self.queue_rank,
            "queue_layer": self.queue_layer,
            "evaluation_status": self.evaluation_status,
            "gate_result": self.gate_result.to_dict() if self.gate_result else None,
            "source_row": dict(self.source_row),
        }


def _clean(value: object) -> str:
    return str(value or "").strip()


def _optional_bool(value: object) -> bool | None:
    normalized = _clean(value).casefold()
    if normalized in {"true", "1", "sim", "yes", "confirmed", "confirmado"}:
        return True
    if normalized in {"false", "0", "não", "nao", "no", "refuted", "refutado"}:
        return False
    return None


def _rank(value: object) -> int | None:
    try:
        return int(float(_clean(value)))
    except (TypeError, ValueError):
        return None


def _role(unit_type: str) -> str | None:
    normalized = unit_type.casefold()
    if "diretorio" in normalized or "agregador" in normalized:
        return "aggregator"
    if "individual" in normalized or "arquivo" in normalized or "institu" in normalized:
        return "institution"
    return None


def _archive_type(unit_type: str, relevance: str) -> str | None:
    text = f"{unit_type} {relevance}".casefold()
    if "diretorio" in text or "agregador" in text:
        return "aggregator"
    if "televis" in text or "broadcast" in text or "emissora" in text:
        return "broadcast_archive"
    if "film" in text or "cinemate" in text or "fílmic" in text:
        return "film_archive"
    if "audiovisual" in text or "imagem em movimento" in text:
        return "audiovisual_archive"
    if "arquivo" in text:
        return "general_archive_with_audiovisual"
    return None


def _evidence_ids(row: Mapping[str, str]) -> tuple[str, ...]:
    evidence: list[str] = []
    if _clean(row.get("evidence_reference")):
        evidence.append(f"queue:{_clean(row.get('unit_code'))}:reference")
    if _clean(row.get("video_location_candidate_url")):
        evidence.append(f"queue:{_clean(row.get('unit_code'))}:candidate-url")
    return tuple(evidence)


def is_source_only(row: Mapping[str, str]) -> bool:
    """Identifica diretórios que geram candidatos, mas não entram como corpus."""
    layer = _clean(row.get("queue_layer")).casefold()
    decision = _clean(row.get("queue_decision")).casefold()
    gate = _clean(row.get("inclusion_gate")).casefold()
    return (
        layer == "fonte_de_fila"
        or "expandir_diretorio" in decision
        or "não entra como corpus" in gate
        or "nao entra como corpus" in gate
    )


def candidate_from_queue_row(row: Mapping[str, str]) -> IncorporationCandidate:
    """Converte uma linha individual sem transformar indícios textuais em fatos."""
    unit_code = _clean(row.get("unit_code"))
    if not unit_code:
        raise ValueError("linha da fila sem unit_code")

    relevance_text = _clean(row.get("audiovisual_relevance"))
    # A descrição da fila indica pertinência temática, mas não substitui validação empírica.
    audiovisual_relevance = _optional_bool(row.get("audiovisual_relevance_confirmed"))
    identity_confirmed = _optional_bool(row.get("institutional_identity_confirmed"))
    observable_surface = _optional_bool(row.get("observable_surface_confirmed"))

    return IncorporationCandidate(
        candidate_id=unit_code,
        label=_clean(row.get("unit_label")) or unit_code,
        source_url=_clean(row.get("source_url")),
        audiovisual_relevance=audiovisual_relevance,
        institutional_identity_confirmed=identity_confirmed,
        observable_surface=observable_surface,
        evidence_ids=_evidence_ids(row),
        territory_code=_clean(row.get("territorial_scope")) or None,
        institutional_role=_role(_clean(row.get("unit_type"))),
        archive_type=_archive_type(_clean(row.get("unit_type")), relevance_text),
        duplicate_entity_ids=(),
        curator_decision="pending",
        metadata={
            "source_family": _clean(row.get("source_family")),
            "queue_reason": _clean(row.get("queue_reason")),
            "next_action": _clean(row.get("next_action")),
            "inclusion_gate": _clean(row.get("inclusion_gate")),
            "rule_version": _clean(row.get("rule_version")),
        },
    )


def evaluate_queue_rows(
    rows: Iterable[Mapping[str, str]], *, minimum_evidence_count: int = 2
) -> tuple[EuropeanQueueEvaluation, ...]:
    evaluations: list[EuropeanQueueEvaluation] = []
    for raw_row in rows:
        row = {str(key): _clean(value) for key, value in raw_row.items()}
        code = row.get("unit_code", "")
        label = row.get("unit_label", "") or code
        if is_source_only(row):
            evaluations.append(
                EuropeanQueueEvaluation(
                    unit_code=code,
                    unit_label=label,
                    queue_rank=_rank(row.get("definitive_queue_rank")),
                    queue_layer=row.get("queue_layer", ""),
                    evaluation_status=SOURCE_ONLY_STATUS,
                    gate_result=None,
                    source_row=row,
                )
            )
            continue

        candidate = candidate_from_queue_row(row)
        result = evaluate_scientific_incorporation(
            candidate, minimum_evidence_count=minimum_evidence_count
        )
        evaluations.append(
            EuropeanQueueEvaluation(
                unit_code=code,
                unit_label=label,
                queue_rank=_rank(row.get("definitive_queue_rank")),
                queue_layer=row.get("queue_layer", ""),
                evaluation_status=result.status,
                gate_result=result,
                source_row=row,
            )
        )

    return tuple(
        sorted(
            evaluations,
            key=lambda item: (
                item.queue_rank is None,
                item.queue_rank if item.queue_rank is not None else 10**9,
                item.unit_code,
            ),
        )
    )


def load_european_queue(path: str | Path) -> tuple[dict[str, str], ...]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"fila europeia inexistente: {source}")
    with source.open(encoding="utf-8-sig", newline="") as handle:
        rows = tuple(dict(row) for row in csv.DictReader(handle))
    if not rows:
        raise ValueError("fila europeia vazia")
    return rows


def write_evaluations(
    evaluations: Iterable[EuropeanQueueEvaluation], *, json_path: str | Path, csv_path: str | Path
) -> None:
    items = tuple(evaluations)
    json_target = Path(json_path)
    csv_target = Path(csv_path)
    json_target.parent.mkdir(parents=True, exist_ok=True)
    csv_target.parent.mkdir(parents=True, exist_ok=True)

    json_target.write_text(
        json.dumps([item.to_dict() for item in items], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    with csv_target.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "unit_code",
                "unit_label",
                "queue_rank",
                "queue_layer",
                "evaluation_status",
                "automatic",
                "failed_codes",
                "unknown_codes",
                "rationale",
            ),
        )
        writer.writeheader()
        for item in items:
            gate = item.gate_result
            writer.writerow(
                {
                    "unit_code": item.unit_code,
                    "unit_label": item.unit_label,
                    "queue_rank": item.queue_rank or "",
                    "queue_layer": item.queue_layer,
                    "evaluation_status": item.evaluation_status,
                    "automatic": gate.automatic if gate else False,
                    "failed_codes": "|".join(gate.failed_codes) if gate else "",
                    "unknown_codes": "|".join(gate.unknown_codes) if gate else "",
                    "rationale": gate.rationale if gate else "Fonte de descoberta; não elegível para promoção direta ao corpus.",
                }
            )
