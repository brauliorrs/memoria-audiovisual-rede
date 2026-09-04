"""Sondagem técnica verificável de candidatos da fila europeia.

A sondagem preenche somente fatos observáveis. Ela não registra decisão curatorial,
não promove candidatos e não altera ``CORPORA``.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse

from memoria_audiovisual.digital_infrastructure_audit import audit_url


@dataclass(frozen=True, slots=True)
class QueueTechnicalProbe:
    unit_code: str
    source_url: str
    final_url: str
    checked_at_utc: str
    http_status: int | None
    reachable: bool
    observable_surface_confirmed: bool
    institutional_identity_confirmed: bool | None
    audiovisual_relevance_confirmed: bool | None
    evidence_ids: tuple[str, ...]
    technical_signals: tuple[str, ...]
    error: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["evidence_ids"] = list(self.evidence_ids)
        payload["technical_signals"] = list(self.technical_signals)
        return payload


def _host(value: str) -> str:
    return (urlparse(value).hostname or "").casefold().removeprefix("www.")


def _signals(record: Mapping[str, object]) -> tuple[str, ...]:
    fields = (
        "api_types",
        "api_evidence",
        "metadata_formats",
        "interoperability_protocols",
        "search_mechanisms",
        "evidence_urls",
    )
    text = " | ".join(str(record.get(field) or "") for field in fields).casefold()
    markers = {
        "iiif": ("iiif", "manifest"),
        "video": ("video", "mp4", "m3u8", "dash", "stream"),
        "film": ("film", "cinema", "cinemate"),
        "broadcast": ("broadcast", "televis", "radio"),
        "audiovisual_metadata": ("pbcore", "ebucore", "audiovisual"),
    }
    return tuple(name for name, tokens in markers.items() if any(token in text for token in tokens))


def probe_queue_candidate(row: Mapping[str, str], *, timeout: int = 20) -> QueueTechnicalProbe:
    unit_code = str(row.get("unit_code") or "").strip()
    source_url = str(row.get("source_url") or "").strip()
    label = str(row.get("unit_label") or unit_code).strip()
    if not unit_code:
        raise ValueError("candidato sem unit_code")
    if not source_url:
        raise ValueError(f"candidato {unit_code} sem source_url")

    audit = audit_url(source_url, corpus_code=unit_code, institution=label, timeout=timeout)
    record = audit.to_dict()
    reachable = bool(record.get("reachable"))
    status = record.get("http_status")
    observable = reachable and isinstance(status, int) and 200 <= status < 400
    final_url = str(record.get("final_url") or "")
    same_host = bool(_host(source_url)) and _host(source_url) == _host(final_url)
    identity: bool | None = True if observable and same_host else None
    signals = _signals(record)
    audiovisual: bool | None = True if signals else None

    evidence: list[str] = []
    if status is not None:
        evidence.append(f"probe:{unit_code}:http-status")
    if final_url:
        evidence.append(f"probe:{unit_code}:final-url")
    evidence.extend(f"probe:{unit_code}:signal:{signal}" for signal in signals)

    return QueueTechnicalProbe(
        unit_code=unit_code,
        source_url=source_url,
        final_url=final_url,
        checked_at_utc=str(record.get("checked_at_utc") or ""),
        http_status=status if isinstance(status, int) else None,
        reachable=reachable,
        observable_surface_confirmed=observable,
        institutional_identity_confirmed=identity,
        audiovisual_relevance_confirmed=audiovisual,
        evidence_ids=tuple(dict.fromkeys(evidence)),
        technical_signals=signals,
        error=str(record.get("error") or ""),
    )


def load_probe_results(path: str | Path | None) -> dict[str, dict[str, object]]:
    if path is None:
        return {}
    source = Path(path)
    if not source.exists():
        return {}
    payload = json.loads(source.read_text(encoding="utf-8"))
    items = payload.get("items", payload) if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise ValueError("resultado de sondagem deve conter uma lista")
    return {
        str(item["unit_code"]): dict(item)
        for item in items
        if isinstance(item, dict) and item.get("unit_code")
    }


def apply_probe_to_row(row: Mapping[str, str], probe: Mapping[str, object] | None) -> dict[str, str]:
    merged = {str(key): str(value or "") for key, value in row.items()}
    if not probe:
        return merged
    for field in (
        "audiovisual_relevance_confirmed",
        "institutional_identity_confirmed",
        "observable_surface_confirmed",
    ):
        value = probe.get(field)
        if value is not None:
            merged[field] = "true" if bool(value) else "false"
    evidence = [str(item) for item in probe.get("evidence_ids", []) if item]
    merged["technical_evidence_ids"] = "|".join(evidence)
    merged["technical_probe_checked_at"] = str(probe.get("checked_at_utc") or "")
    merged["technical_probe_error"] = str(probe.get("error") or "")
    return merged
