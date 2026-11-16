"""Universal, offline contract for institutional corpus admission in MAR.

Connector registration != source approval != scientific validation != publication.
A static vetted allowlist stays separate from the complete scientific CORPORA
registry. No dynamic imports, HTTP, media downloads or database writes.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, replace
from enum import Enum
from types import MappingProxyType
from typing import Mapping

SCHEMA_VERSION = "mar-institutional-metadata-v1"
COMMON_FIELDS = (
    "source_record_id", "source_record_url", "video_title", "year",
    "authors", "subjects", "languages", "genres", "video_description",
    "media_access_status", "media_rights_status", "record_review_status",
)
HOST = re.compile(r"(?=.{4,253}\Z)[a-z0-9](?:[a-z0-9.-]*[a-z0-9])\Z")
CODE = re.compile(r"[a-z][a-z0-9-]{1,63}\Z")
SAFE_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9:_./@-]{3,240}\Z")


class ContractRejected(ValueError):
    """Invalid connector contract or unverifiable state transition."""


class SourceState(str, Enum):
    REGISTERED = "registered"
    PROBED = "probed"
    EVIDENCE_VALIDATED = "evidence_validated"
    CURATOR_REVIEWED = "curator_reviewed"
    ADMISSION_READY = "admission_ready"
    HOLD = "HOLD"


STEPS = (
    SourceState.REGISTERED,
    SourceState.PROBED,
    SourceState.EVIDENCE_VALIDATED,
    SourceState.CURATOR_REVIEWED,
    SourceState.ADMISSION_READY,
)


@dataclass(frozen=True)
class ConnectorSpec:
    corpus_code: str
    institution: str
    adapter_module: str
    record_hosts: frozenset[str]
    source_kind: str
    onboarding_state: SourceState = SourceState.REGISTERED

    def __post_init__(self) -> None:
        if not CODE.fullmatch(self.corpus_code):
            raise ContractRejected("invalid_corpus_code")
        if not isinstance(self.institution, str) or not self.institution.strip():
            raise ContractRejected("missing_institution")
        if not isinstance(self.adapter_module, str) or not self.adapter_module.startswith(
            "memoria_audiovisual."
        ) or not re.fullmatch(r"memoria_audiovisual\.[a-z][a-z0-9_]*", self.adapter_module):
            raise ContractRejected("invalid_adapter_reference")
        if not isinstance(self.record_hosts, frozenset) or not self.record_hosts:
            raise ContractRejected("empty_allowed_record_hosts")
        if any(not isinstance(host, str) or not HOST.fullmatch(host)
               or ".." in host or "." not in host for host in self.record_hosts):
            raise ContractRejected("invalid_record_host")
        if self.source_kind not in {"institutional_record", "aggregated_institutional_record"}:
            raise ContractRejected("invalid_source_kind")
        if self.onboarding_state != SourceState.REGISTERED:
            raise ContractRejected("onboarding_requires_registered_state")


# Explicitly vetted URLs from PR #95, unchanged. A new source must receive a
# reviewed code change and independent admission evidence before publication.
_REGISTRY = {
    "eye": ConnectorSpec(
        "eye", "Eye Filmmuseum", "memoria_audiovisual.eye",
        frozenset({"filmdatabase.eyefilm.nl", "www.eyefilm.nl"}),
        "institutional_record",
    ),
    "czech-television": ConnectorSpec(
        "czech-television", "Czech Television", "memoria_audiovisual.czech_television",
        frozenset({"www.ceskatelevize.cz", "ceskatelevize.cz"}),
        "institutional_record",
    ),
    "ciclic": ConnectorSpec(
        "ciclic", "CICLIC - Centre-Val-de-Loire", "memoria_audiovisual.ciclic",
        frozenset({"memoire.ciclic.fr"}), "institutional_record",
    ),
    "asim": ConnectorSpec(
        "asim", "Arxiu del So i de la Imatge de Mallorca",
        "memoria_audiovisual.asim",
        frozenset({"www.europeanfilmgateway.eu", "europeanfilmgateway.eu"}),
        "aggregated_institutional_record",
    ),
    "bnfa": ConnectorSpec(
        "bnfa", "Bulgarian National Film Archive", "memoria_audiovisual.bnfa",
        frozenset({"www.europeanfilmgateway.eu", "europeanfilmgateway.eu"}),
        "aggregated_institutional_record",
    ),
}
REGISTRY: Mapping[str, ConnectorSpec] = MappingProxyType(_REGISTRY)


def connector_for(code: str) -> ConnectorSpec:
    """Only registered source codes are eligible for the PR #95 admission gate."""
    if not isinstance(code, str) or code not in REGISTRY:
        raise ContractRejected("unregistered_or_blocked_source")
    return REGISTRY[code]


def propose_connector(spec: ConnectorSpec, registry: Mapping[str, ConnectorSpec] = REGISTRY) -> dict:
    """Validate a new connector definition without registering/activating it.

    The output is a reviewer-facing proposal only, never a runtime allowlist
    extension. A code review must explicitly update REGISTRY.
    """
    if not isinstance(spec, ConnectorSpec):
        raise ContractRejected("invalid_connector_definition")
    if spec.corpus_code in registry or spec.corpus_code == "ape":
        raise ContractRejected("source_existing_or_on_hold")
    return {
        "corpus_code": spec.corpus_code,
        "institution": spec.institution,
        "adapter_reference": spec.adapter_module,
        "allowed_record_hosts": sorted(spec.record_hosts),
        "review_status": "pending_independent_review",
        "registry_updated": False,
        "publication_authorized": False,
        "corpus_activation": False,
    }


@dataclass(frozen=True)
class SourceReview:
    corpus_code: str
    state: SourceState = SourceState.REGISTERED
    history: tuple[tuple[str, str, str], ...] = ()
    observer: str = ""
    evidence_id: str = ""
    curator: str = ""

    def __post_init__(self) -> None:
        connector_for(self.corpus_code)
        if not isinstance(self.state, SourceState):
            raise ContractRejected("unknown_source_state")
        # A manually constructed advanced snapshot without a matching audit
        # trail is never treated as an operationally reviewed source.
        if self.state != SourceState.REGISTERED and (
            not self.history or self.history[-1][0] != self.state.value
        ):
            raise ContractRejected("review_state_requires_audit_trail")
        if self.history and self.history[-1][0] != self.state.value:
            raise ContractRejected("review_history_state_mismatch")


def transition(
    review: SourceReview, target: SourceState, *,
    actor: str, evidence_id: str = "", override_hold: bool = False,
) -> SourceReview:
    """Pure, append-only review state machine; NEVER grants publication."""
    if not isinstance(review, SourceReview) or not isinstance(target, SourceState):
        raise ContractRejected("invalid_transition")
    if not isinstance(actor, str) or not SAFE_TOKEN.fullmatch(actor):
        raise ContractRejected("identified_actor_required")
    if target == review.state:
        raise ContractRejected("self_transition_disallowed")
    if target == SourceState.HOLD:
        return replace(review, state=target,
                       history=review.history + ((target.value, actor, evidence_id),))
    if review.state == SourceState.HOLD:
        if not override_hold or target != SourceState.REGISTERED:
            raise ContractRejected("hold_requires_explicit_restart")
        return replace(review, state=target, observer="", evidence_id="", curator="",
                       history=review.history + ((target.value, actor, "reopened"),))
    index = STEPS.index(review.state)
    if index + 1 >= len(STEPS) or STEPS[index + 1] != target:
        raise ContractRejected("review_steps_cannot_be_skipped")
    if target in {
        SourceState.PROBED, SourceState.EVIDENCE_VALIDATED,
        SourceState.CURATOR_REVIEWED, SourceState.ADMISSION_READY,
    } and (not isinstance(evidence_id, str) or not SAFE_TOKEN.fullmatch(evidence_id)):
        raise ContractRejected("audit_evidence_required")
    if target == SourceState.CURATOR_REVIEWED and actor == review.observer:
        raise ContractRejected("curator_must_be_independent_of_observer")
    if target == SourceState.ADMISSION_READY and actor == review.curator:
        raise ContractRejected("admission_review_must_be_independent_of_curator")
    return replace(
        review, state=target,
        observer=(actor if target == SourceState.PROBED else review.observer),
        evidence_id=(evidence_id if target == SourceState.EVIDENCE_VALIDATED else review.evidence_id),
        curator=(actor if target == SourceState.CURATOR_REVIEWED else review.curator),
        history=review.history + ((target.value, actor, evidence_id),),
    )


def admission_assessment(review: SourceReview) -> dict:
    """Status is advisory: PR #95 still independently validates files/manifest."""
    connector_for(review.corpus_code)
    return {
        "corpus_code": review.corpus_code,
        "source_state": review.state.value,
        "can_submit_to_admission_gate": review.state == SourceState.ADMISSION_READY,
        "publication_authorized": False,
        "scientific_corpus_validated": False,
        "media_rights_verified": False,
        "next_gate": "independent_manifest_and_PR_review",
    }


def registry_inventory() -> list[dict]:
    """Scalable administrative view, without claiming operational activation."""
    return [
        {
            "corpus_code": spec.corpus_code,
            "institution": spec.institution,
            "adapter_reference": spec.adapter_module,
            "record_hosts": sorted(spec.record_hosts),
            "source_kind": spec.source_kind,
            "onboarding_state": spec.onboarding_state.value,
            "scientific_corpus_validated": False,
            "publication_authorized": False,
        }
        for spec in sorted(REGISTRY.values(), key=lambda x: x.corpus_code)
    ]
