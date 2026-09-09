"""Gate verificável entre ingestão técnica e incorporação científica.

Este módulo não altera ``CORPORA`` nem ativa unidades automaticamente. Ele avalia
um candidato já ingerido e devolve uma decisão explicável: aprovação automática
restrita, rejeição por bloqueio objetivo ou revisão humana.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal, Mapping, Sequence

GateStatus = Literal["approved", "rejected", "requires_human_review"]
CriterionStatus = Literal["passed", "failed", "unknown"]

_REQUIRED_ROLES = {"aggregator", "institution"}
_REQUIRED_ARCHIVE_TYPES = {
    "audiovisual_archive",
    "film_archive",
    "broadcast_archive",
    "general_archive_with_audiovisual",
    "aggregator",
}


@dataclass(frozen=True, slots=True)
class EligibilityCriterion:
    code: str
    label: str
    status: CriterionStatus
    evidence_ids: tuple[str, ...] = ()
    note: str = ""
    hard_blocker: bool = False

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["evidence_ids"] = list(self.evidence_ids)
        return payload


@dataclass(frozen=True, slots=True)
class IncorporationCandidate:
    candidate_id: str
    label: str
    source_url: str
    audiovisual_relevance: bool | None
    institutional_identity_confirmed: bool | None
    observable_surface: bool | None
    evidence_ids: tuple[str, ...]
    territory_code: str | None
    institutional_role: str | None
    archive_type: str | None
    duplicate_entity_ids: tuple[str, ...] = ()
    curator_decision: Literal["approved", "rejected", "pending", "not_required"] = "pending"
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EligibilityResult:
    candidate_id: str
    status: GateStatus
    criteria: tuple[EligibilityCriterion, ...]
    automatic: bool
    rationale: str

    @property
    def failed_codes(self) -> tuple[str, ...]:
        return tuple(item.code for item in self.criteria if item.status == "failed")

    @property
    def unknown_codes(self) -> tuple[str, ...]:
        return tuple(item.code for item in self.criteria if item.status == "unknown")

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "status": self.status,
            "automatic": self.automatic,
            "rationale": self.rationale,
            "failed_codes": list(self.failed_codes),
            "unknown_codes": list(self.unknown_codes),
            "criteria": [item.to_dict() for item in self.criteria],
        }


def _boolean_criterion(
    *,
    code: str,
    label: str,
    value: bool | None,
    evidence_ids: Sequence[str] = (),
    hard_blocker: bool = False,
    failed_note: str,
    unknown_note: str,
) -> EligibilityCriterion:
    if value is True:
        return EligibilityCriterion(code, label, "passed", tuple(evidence_ids))
    if value is False:
        return EligibilityCriterion(
            code,
            label,
            "failed",
            tuple(evidence_ids),
            failed_note,
            hard_blocker,
        )
    return EligibilityCriterion(
        code,
        label,
        "unknown",
        tuple(evidence_ids),
        unknown_note,
        hard_blocker,
    )


def evaluate_scientific_incorporation(
    candidate: IncorporationCandidate,
    *,
    minimum_evidence_count: int = 2,
) -> EligibilityResult:
    """Avalia elegibilidade sem promover o candidato ao corpus.

    Aprovação automática só ocorre quando todos os critérios verificáveis passam,
    não há possível duplicidade e a decisão curatorial foi marcada como
    ``not_required``. Qualquer ambiguidade ou decisão pendente exige revisão humana.
    Bloqueios objetivos produzem rejeição.
    """
    if minimum_evidence_count < 1:
        raise ValueError("minimum_evidence_count deve ser positivo")
    if not candidate.candidate_id.strip():
        raise ValueError("candidate_id não pode ser vazio")

    evidence_ids = tuple(dict.fromkeys(item for item in candidate.evidence_ids if item))
    criteria: list[EligibilityCriterion] = [
        _boolean_criterion(
            code="audiovisual_relevance",
            label="Aderência ao objeto audiovisual",
            value=candidate.audiovisual_relevance,
            evidence_ids=evidence_ids,
            hard_blocker=True,
            failed_note="Não há aderência verificável ao objeto audiovisual.",
            unknown_note="A aderência audiovisual ainda não foi demonstrada.",
        ),
        _boolean_criterion(
            code="institutional_identity",
            label="Identidade institucional confirmada",
            value=candidate.institutional_identity_confirmed,
            evidence_ids=evidence_ids,
            hard_blocker=True,
            failed_note="A identidade institucional foi refutada ou não corresponde à unidade proposta.",
            unknown_note="A identidade institucional requer confirmação.",
        ),
        _boolean_criterion(
            code="observable_surface",
            label="Superfície digital observável",
            value=candidate.observable_surface,
            evidence_ids=evidence_ids,
            hard_blocker=True,
            failed_note="Não existe superfície pública observável para a unidade.",
            unknown_note="A superfície pública ainda não foi validada.",
        ),
    ]

    evidence_ok = len(evidence_ids) >= minimum_evidence_count
    criteria.append(
        EligibilityCriterion(
            "sufficient_evidence",
            "Evidências suficientes",
            "passed" if evidence_ok else "unknown",
            evidence_ids,
            "" if evidence_ok else f"São exigidas ao menos {minimum_evidence_count} evidências independentes.",
        )
    )

    territory_ok = bool(str(candidate.territory_code or "").strip())
    criteria.append(
        EligibilityCriterion(
            "territorial_classification",
            "Classificação territorial",
            "passed" if territory_ok else "unknown",
            note="Território ainda não classificado." if not territory_ok else "",
        )
    )

    role_ok = candidate.institutional_role in _REQUIRED_ROLES
    criteria.append(
        EligibilityCriterion(
            "institutional_role",
            "Papel institucional",
            "passed" if role_ok else "unknown",
            note=(
                "Papel deve ser classificado como aggregator ou institution."
                if not role_ok
                else ""
            ),
        )
    )

    archive_type_ok = candidate.archive_type in _REQUIRED_ARCHIVE_TYPES
    criteria.append(
        EligibilityCriterion(
            "archive_type",
            "Tipo de arquivo ou agregador",
            "passed" if archive_type_ok else "unknown",
            note="Tipo documental/institucional ainda não classificado." if not archive_type_ok else "",
        )
    )

    duplicate_ids = tuple(dict.fromkeys(candidate.duplicate_entity_ids))
    criteria.append(
        EligibilityCriterion(
            "non_duplicate_unit",
            "Unidade de análise não duplicada",
            "unknown" if duplicate_ids else "passed",
            note=(
                "Possíveis duplicidades: " + ", ".join(duplicate_ids)
                if duplicate_ids
                else ""
            ),
        )
    )

    decision = candidate.curator_decision
    criteria.append(
        EligibilityCriterion(
            "curatorial_decision",
            "Decisão curatorial registrada",
            "failed" if decision == "rejected" else (
                "passed" if decision in {"approved", "not_required"} else "unknown"
            ),
            note=(
                "Decisão curatorial rejeitou a incorporação."
                if decision == "rejected"
                else "Decisão curatorial pendente."
                if decision == "pending"
                else ""
            ),
            hard_blocker=decision == "rejected",
        )
    )

    hard_failures = [
        item for item in criteria if item.status == "failed" and item.hard_blocker
    ]
    if hard_failures:
        return EligibilityResult(
            candidate.candidate_id,
            "rejected",
            tuple(criteria),
            False,
            "Candidato rejeitado por bloqueio objetivo: "
            + ", ".join(item.label for item in hard_failures),
        )

    unresolved = [item for item in criteria if item.status != "passed"]
    if unresolved:
        return EligibilityResult(
            candidate.candidate_id,
            "requires_human_review",
            tuple(criteria),
            False,
            "Incorporação condicionada à revisão dos critérios: "
            + ", ".join(item.label for item in unresolved),
        )

    automatic = decision == "not_required"
    return EligibilityResult(
        candidate.candidate_id,
        "approved",
        tuple(criteria),
        automatic,
        (
            "Candidato aprovado automaticamente por regras estritas e evidências completas."
            if automatic
            else "Candidato aprovado com decisão curatorial explícita."
        ),
    )
