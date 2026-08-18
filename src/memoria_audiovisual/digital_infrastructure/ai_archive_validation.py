"""Validação sequencial de IA no conteúdo observado pelo MAR.

A identificação terminológica/contextual é apenas a Porta 1. Uma ocorrência só
pode ser publicada como uso de IA no acervo quando também passa pela Porta 2:
o item pertence ao corpus/acervo efetivamente observado e a evidência está
inequivocamente vinculada à produção ou modificação daquele item.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from .ai_content_production import AIContentUsageObservation

AI_ARCHIVE_VALIDATION_PROTOCOL_VERSION = "1.0.0"

AIArchiveGateStatus = Literal[
    "confirmed_ai_use_in_observed_archive",
    "gate1_terminology_not_positive",
    "item_outside_observed_corpus",
    "evidence_not_linked_to_item",
    "not_assessable",
]


@dataclass(frozen=True, slots=True)
class AIArchiveUsageValidation:
    entity_id: str
    item_id: str
    terminology_gate_positive: bool
    item_in_observed_corpus: bool | None
    evidence_linked_to_item: bool | None
    status: AIArchiveGateStatus
    protocol_version: str = AI_ARCHIVE_VALIDATION_PROTOCOL_VERSION

    @property
    def is_archive_ai_positive(self) -> bool:
        return self.status == "confirmed_ai_use_in_observed_archive"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def validate_ai_use_in_observed_archive(
    terminology_observation: AIContentUsageObservation,
    *,
    item_in_observed_corpus: bool | None,
    evidence_linked_to_item: bool | None,
) -> AIArchiveUsageValidation:
    """Aplica as duas portas sequenciais do protocolo MAR.

    Porta 1: evidência terminológica/contextual de participação de IA na produção.
    Porta 2: pertencimento do item ao corpus observado + vínculo da evidência ao item.

    Um positivo científico no acervo exige as duas portas positivas. Fontes externas
    podem sustentar o vínculo da evidência, mas não substituem a comprovação de que o
    item integra o corpus/acervo efetivamente observado.
    """

    gate1 = terminology_observation.is_ai_positive
    if not gate1:
        status: AIArchiveGateStatus = "gate1_terminology_not_positive"
    elif item_in_observed_corpus is None or evidence_linked_to_item is None:
        status = "not_assessable"
    elif not item_in_observed_corpus:
        status = "item_outside_observed_corpus"
    elif not evidence_linked_to_item:
        status = "evidence_not_linked_to_item"
    else:
        status = "confirmed_ai_use_in_observed_archive"

    return AIArchiveUsageValidation(
        entity_id=terminology_observation.entity_id,
        item_id=terminology_observation.item_id,
        terminology_gate_positive=gate1,
        item_in_observed_corpus=item_in_observed_corpus,
        evidence_linked_to_item=evidence_linked_to_item,
        status=status,
    )


__all__ = [
    "AI_ARCHIVE_VALIDATION_PROTOCOL_VERSION",
    "AIArchiveGateStatus",
    "AIArchiveUsageValidation",
    "validate_ai_use_in_observed_archive",
]
