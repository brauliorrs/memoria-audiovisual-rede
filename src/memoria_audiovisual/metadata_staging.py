"""Reusable metadata-only staging runner, isolated from corpus promotion.

Reuses the existing content-addressed RawArtifactStore and FileWriteLock.
Does NOT call the digital-infrastructure IngestionCoordinator, whose entity
contract/commit semantics do not describe audiovisual film records.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .digital_infrastructure.locking import FileWriteLock
from .digital_infrastructure.raw_artifacts import RawArtifactStore, canonical_json_bytes

STAGING_SCHEMA = "1.0.0"


class StageRejected(ValueError):
    """The batch is incomplete, inconsistent, or cannot be resumed safely."""


@dataclass(frozen=True)
class MetadataPage:
    records: tuple[dict[str, Any], ...]
    total: int
    next_token: str | None
    raw: dict[str, Any]


class MetadataPageSource(Protocol):
    """Source-specific API adapter; every record must have a stable string id."""

    @property
    def scope(self) -> dict[str, str]: ...

    def preflight(self) -> int: ...

    def fetch_page(self, token: str | None) -> MetadataPage: ...


def _digest(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    data = canonical_json_bytes(value) + b"\n"
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _valid_page(page: MetadataPage, expected_total: int) -> tuple[str, ...]:
    if not isinstance(page.total, int) or isinstance(page.total, bool):
        raise StageRejected("invalid_result_total")
    if page.total != expected_total:
        raise StageRejected("result_total_drift")
    if page.next_token is not None and (
        not isinstance(page.next_token, str)
        or not page.next_token
        or len(page.next_token) > 4096
    ):
        raise StageRejected("invalid_resumption_token")
    if not isinstance(page.raw, dict) or not isinstance(page.records, tuple):
        raise StageRejected("invalid_page_shape")
    ids: list[str] = []
    for record in page.records:
        if not isinstance(record, dict):
            raise StageRejected("non_object_record")
        identifier = record.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            raise StageRejected("record_without_id")
        ids.append(identifier)
    if len(set(ids)) != len(ids):
        raise StageRejected("duplicate_ids_within_page")
    if not ids and page.next_token is not None:
        raise StageRejected("empty_intermediate_page")
    return tuple(ids)


def _restore(
    root: Path, payload: dict[str, Any], scope_digest: str, total: int,
) -> tuple[set[str], set[str], str | None]:
    if payload.get("schema_version") != STAGING_SCHEMA:
        raise StageRejected("checkpoint_schema_mismatch")
    if payload.get("scope_sha256") != scope_digest:
        raise StageRejected("checkpoint_scope_mismatch")
    if not isinstance(payload.get("scope"), dict) or (
        _digest(payload["scope"]) != payload["scope_sha256"]
    ):
        raise StageRejected("checkpoint_scope_payload_tampered")
    if payload.get("expected_total") != total:
        raise StageRejected("checkpoint_total_drift")
    pages = payload.get("pages")
    if not isinstance(pages, list):
        raise StageRejected("checkpoint_pages_invalid")
    seen: set[str] = set()
    cursors: set[str] = set()
    token: str | None = None
    for index, entry in enumerate(pages):
        if not isinstance(entry, dict) or entry.get("sequence") != index + 1:
            raise StageRejected("checkpoint_page_sequence_invalid")
        digest = entry.get("artifact_sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            raise StageRejected("checkpoint_artifact_invalid")
        path = root / "raw" / digest[:2] / f"{digest}.json"
        try:
            data = path.read_bytes()
        except OSError as ex:
            raise StageRejected("checkpoint_raw_artifact_missing") from ex
        if hashlib.sha256(data).hexdigest() != digest:
            raise StageRejected("checkpoint_raw_artifact_tampered")
        try:
            raw = json.loads(data)
            page = raw["page"]
            records = tuple(page["records"])
            next_token = page.get("next_token")
            source_raw = page["source_response"]
        except (ValueError, TypeError, KeyError) as ex:
            raise StageRejected("checkpoint_raw_artifact_invalid") from ex
        ids = _valid_page(
            MetadataPage(records, page["total"], next_token, source_raw),
            total,
        )
        if len(ids) != entry.get("record_count"):
            raise StageRejected("checkpoint_record_count_mismatch")
        if _digest(list(ids)) != entry.get("ids_sha256"):
            raise StageRejected("checkpoint_ids_hash_mismatch")
        input_hash = _digest(token if token is not None else "*")
        if input_hash != entry.get("input_cursor_sha256"):
            raise StageRejected("checkpoint_cursor_chain_mismatch")
        if seen.intersection(ids):
            raise StageRejected("checkpoint_duplicate_cross_page")
        seen.update(ids)
        token = next_token
        if token is not None:
            h = _digest(token)
            if h in cursors:
                raise StageRejected("checkpoint_cursor_cycle")
            cursors.add(h)
    if payload.get("record_count") != len(seen):
        raise StageRejected("checkpoint_total_records_mismatch")
    if payload.get("next_token_sha256") != (
        _digest(token) if token is not None else None
    ):
        raise StageRejected("checkpoint_next_cursor_mismatch")
    if payload.get("status") == "complete":
        if token is not None or len(seen) != total:
            raise StageRejected("checkpoint_false_complete")
    elif payload.get("status") == "partial":
        if token is None:
            raise StageRejected("checkpoint_false_partial")
    else:
        raise StageRejected("checkpoint_not_resumable")
    return seen, cursors, token


def stage_metadata(
    source: MetadataPageSource,
    root: str | Path,
    *,
    max_pages: int = 1,
    resume: bool = False,
) -> dict[str, Any]:
    """Stage bounded pages; never publish, merge into MAR, or download media.

    Run lock is held across preflight/fetch/checkpoint. Partial checkpoints are
    resumable only after replaying and verifying every immutable raw artifact.
    """
    if not isinstance(max_pages, int) or isinstance(max_pages, bool) or max_pages < 1:
        raise ValueError("max_pages_must_be_positive")
    directory = Path(root)
    directory.mkdir(parents=True, exist_ok=True)
    with FileWriteLock(directory / "run", timeout=10):
        expected_total = source.preflight()
        if (not isinstance(expected_total, int) or isinstance(expected_total, bool)
            or expected_total < 0):
            raise StageRejected("invalid_preflight_total")
        scope = dict(source.scope)
        scope_digest = _digest(scope)
        checkpoint = directory / "checkpoint.json"
        if checkpoint.exists():
            if not resume:
                raise StageRejected("checkpoint_exists_resume_required")
            try:
                payload = json.loads(checkpoint.read_text(encoding="utf-8"))
            except (OSError, ValueError) as ex:
                raise StageRejected("checkpoint_invalid") from ex
            ids, cursors, token = _restore(
                directory, payload, scope_digest, expected_total,
            )
        else:
            if resume:
                raise StageRejected("checkpoint_missing_on_resume")
            payload = {
                "schema_version": STAGING_SCHEMA, "scope": scope,
                "scope_sha256": scope_digest,
                "expected_total": expected_total, "record_count": 0,
                "pages": [], "next_token_sha256": None,
                "status": "partial", "promotion_authorized": False,
                "media_downloaded": False,
            }
            ids, cursors, token = set(), set(), None
        if payload["status"] == "complete":
            return payload
        artifacts = RawArtifactStore(directory / "raw")
        for _ in range(max_pages):
            incoming = token
            page = source.fetch_page(token)
            new_ids = _valid_page(page, expected_total)
            if ids.intersection(new_ids):
                raise StageRejected("duplicate_ids_across_pages")
            if len(ids) + len(new_ids) > expected_total:
                raise StageRejected("records_exceed_preflight_total")
            if page.next_token is not None:
                next_digest = _digest(page.next_token)
                if page.next_token == incoming or next_digest in cursors:
                    raise StageRejected("resumption_token_cycle")
            elif len(ids) + len(new_ids) != expected_total:
                raise StageRejected("terminal_total_mismatch")
            # First validate; then preserve immutable page before checkpoint.
            artifact = artifacts.preserve({
                "page": {
                    "records": list(page.records),
                    "total": page.total,
                    "next_token": page.next_token,
                    "source_response": page.raw,
                }
            })
            payload["pages"].append({
                "sequence": len(payload["pages"]) + 1,
                "artifact_sha256": artifact.sha256,
                "record_count": len(new_ids),
                "ids_sha256": _digest(list(new_ids)),
                "input_cursor_sha256": _digest(incoming if incoming is not None else "*"),
                "next_cursor_sha256": (
                    _digest(page.next_token) if page.next_token is not None else None
                ),
            })
            ids.update(new_ids)
            token = page.next_token
            if token is not None:
                cursors.add(_digest(token))
            payload["record_count"] = len(ids)
            payload["next_token_sha256"] = (
                _digest(token) if token is not None else None
            )
            payload["status"] = "complete" if token is None else "partial"
            _atomic_json(checkpoint, payload)
            if token is None:
                break
        return payload


def public_stage_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    """Redacted summary safe to include in CI; raw cursor never exported."""
    return {
        "scope_sha256": manifest["scope_sha256"],
        "schema_version": manifest["schema_version"],
        "expected_total": manifest["expected_total"],
        "record_count": manifest["record_count"],
        "page_count": len(manifest["pages"]),
        "status": manifest["status"],
        "promotion_authorized": False,
        "media_downloaded": False,
    }
