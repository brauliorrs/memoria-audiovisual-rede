"""Opt-in Neon/PostgreSQL checkpoint persistence for metadata staging (Gate P0).

This module never calls a collector or publishes MAR data. Its only inputs are
already staged, locally validated JSON files or a verified database snapshot.
A psycopg connection factory must target an explicitly selected TEST branch.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from .digital_infrastructure.locking import FileWriteLock
from .digital_infrastructure.raw_artifacts import canonical_json_bytes
from .metadata_staging import StageRejected, _digest, _restore


class PersistenceRejected(StageRejected):
    """Fail closed without exposing opaque provider tokens or database secrets."""


# sequence, sha, record count, ids hash, input cursor hash, next cursor hash, bytes
PageRow = tuple[int, str, int, str, str, str | None, bytes]


@dataclass(frozen=True, repr=False)
class StoredCheckpoint:
    revision: int
    scope_sha256: str
    expected_total: int
    manifest_bytes: bytes
    manifest_sha256: str
    status: str
    record_count: int
    pages: tuple[PageRow, ...]


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _page_row(entry: Mapping[str, Any], raw: bytes) -> PageRow:
    return (
        entry["sequence"],
        entry["artifact_sha256"],
        entry["record_count"],
        entry["ids_sha256"],
        entry["input_cursor_sha256"],
        entry["next_cursor_sha256"],
        raw,
    )


def _validate(state: StoredCheckpoint) -> dict[str, Any]:
    """Replay original MAR invariants on *bytes*, never reconstructed JSONB."""
    if state.revision < 1 or _sha(state.manifest_bytes) != state.manifest_sha256:
        raise PersistenceRejected("checkpoint_digest_invalid")
    try:
        manifest = json.loads(state.manifest_bytes)
    except (TypeError, ValueError) as exc:
        raise PersistenceRejected("checkpoint_invalid_json") from exc
    if not isinstance(manifest, dict):
        raise PersistenceRejected("checkpoint_invalid_shape")
    if canonical_json_bytes(manifest) + b"\n" != state.manifest_bytes:
        raise PersistenceRejected("checkpoint_noncanonical_bytes")
    if (
        manifest.get("scope_sha256") != state.scope_sha256
        or manifest.get("expected_total") != state.expected_total
        or manifest.get("status") != state.status
        or manifest.get("record_count") != state.record_count
    ):
        raise PersistenceRejected("checkpoint_metadata_mismatch")
    entries = manifest.get("pages")
    if not isinstance(entries, list) or len(entries) != len(state.pages):
        raise PersistenceRejected("checkpoint_page_rows_mismatch")
    with tempfile.TemporaryDirectory(prefix="mar-p0-verify-") as temp:
        root = Path(temp)
        for entry, row in zip(entries, state.pages):
            if not isinstance(entry, dict) or row[:6] != _page_row(entry, row[6])[:6]:
                raise PersistenceRejected("checkpoint_page_rows_mismatch")
            if _sha(row[6]) != row[1]:
                raise PersistenceRejected("checkpoint_artifact_digest_invalid")
            path = root / "raw" / row[1][:2] / f"{row[1]}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(row[6])
        _restore(root, manifest, state.scope_sha256, state.expected_total)
    return manifest


def _local_snapshot(directory: Path) -> StoredCheckpoint:
    if (directory / "epoch-aborted.json").exists():
        raise PersistenceRejected("staging_epoch_aborted")
    try:
        content = (directory / "checkpoint.json").read_bytes()
        manifest = json.loads(content)
        if not isinstance(manifest, dict):
            raise ValueError("not_an_object")
        entries = manifest["pages"]
        if not isinstance(entries, list):
            raise ValueError("pages_not_list")
        rows = []
        for entry in entries:
            sha = entry["artifact_sha256"]
            # Avoid constructing unsafe paths from a corrupted checkpoint.
            if not isinstance(sha, str) or len(sha) != 64 or any(
                ch not in "0123456789abcdef" for ch in sha
            ):
                raise ValueError("invalid_artifact_digest")
            raw = (directory / "raw" / sha[:2] / f"{sha}.json").read_bytes()
            rows.append(_page_row(entry, raw))
        state = StoredCheckpoint(
            1, manifest["scope_sha256"], manifest["expected_total"], content,
            _sha(content), manifest["status"], manifest["record_count"],
            tuple(rows),
        )
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise PersistenceRejected("local_checkpoint_invalid") from exc
    _validate(state)
    return state


def _fetch(conn: Any, run_key: str, *, lock: bool) -> StoredCheckpoint | None:
    query = (
        "SELECT revision, scope_sha256, expected_total, manifest, "
        "manifest_sha256, status, record_count "
        "FROM mar_p0.checkpoints WHERE run_key = %s"
    )
    if lock:
        query += " FOR UPDATE"
    row = conn.execute(query, (run_key,)).fetchone()
    if row is None:
        return None
    entries = conn.execute(
        "SELECT p.sequence, p.artifact_sha256, p.record_count, p.ids_sha256, "
        "p.input_cursor_sha256, p.next_cursor_sha256, a.payload "
        "FROM mar_p0.checkpoint_pages p "
        "LEFT JOIN mar_p0.raw_artifacts a ON a.sha256 = p.artifact_sha256 "
        "WHERE p.run_key = %s ORDER BY p.sequence",
        (run_key,),
    ).fetchall()
    if any(item[6] is None for item in entries):
        raise PersistenceRejected("checkpoint_raw_artifact_missing")
    try:
        return StoredCheckpoint(
            int(row[0]), row[1], int(row[2]), bytes(row[3]), row[4],
            row[5], int(row[6]),
            tuple((r[0], r[1], r[2], r[3], r[4], r[5], bytes(r[6]))
                  for r in entries),
        )
    except (TypeError, ValueError, IndexError) as exc:
        raise PersistenceRejected("checkpoint_db_shape_invalid") from exc


class PostgresCheckpointStore:
    """Explicitly invoked storage adapter; it does not alter stage_metadata."""

    def __init__(self, connect: Callable[[], Any]) -> None:
        self._connect = connect

    def save(
        self, directory: str | Path, run_key: str, *,
        expected_revision: int | None = None,
    ) -> int:
        if not isinstance(run_key, str) or not 1 <= len(run_key) <= 200:
            raise PersistenceRejected("run_key_invalid")
        staging_root = Path(directory)
        # Share the original staging lock: never snapshot a partially written
        # checkpoint while stage_metadata is appending another page.
        with FileWriteLock(staging_root / "run", timeout=10):
            new = _local_snapshot(staging_root)
        # Connection context commits on success and rolls back any exception.
        with self._connect() as conn:
            old = _fetch(conn, run_key, lock=True)
            if old is None:
                if expected_revision is not None:
                    raise PersistenceRejected("checkpoint_write_conflict")
                revision = 1
                new_pages = new.pages
            else:
                _validate(old)
                # Safe to repeat a committed write whose ACK was lost.
                if (
                    old.manifest_bytes == new.manifest_bytes
                    and old.pages == new.pages
                ):
                    return old.revision
                if expected_revision != old.revision:
                    raise PersistenceRejected("checkpoint_write_conflict")
                if (
                    old.scope_sha256 != new.scope_sha256
                    or old.expected_total != new.expected_total
                    or len(new.pages) < len(old.pages)
                    or new.pages[:len(old.pages)] != old.pages
                ):
                    raise PersistenceRejected("checkpoint_not_append_only")
                if len(new.pages) == len(old.pages) or old.status == "complete":
                    raise PersistenceRejected("checkpoint_not_append_only")
                revision = old.revision + 1
                new_pages = new.pages[len(old.pages):]
            for page in new_pages:
                conn.execute(
                    "INSERT INTO mar_p0.raw_artifacts (sha256, payload) "
                    "VALUES (%s, %s) ON CONFLICT (sha256) DO NOTHING",
                    (page[1], page[6]),
                )
            if old is None:
                conn.execute(
                    "INSERT INTO mar_p0.checkpoints "
                    "(run_key, scope_sha256, revision, manifest, "
                    "manifest_sha256, status, expected_total, record_count) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        run_key, new.scope_sha256, revision, new.manifest_bytes,
                        new.manifest_sha256, new.status, new.expected_total,
                        new.record_count,
                    ),
                )
            else:
                result = conn.execute(
                    "UPDATE mar_p0.checkpoints SET "
                    "revision = %s, manifest = %s, manifest_sha256 = %s, "
                    "status = %s, record_count = %s, updated_at = now() "
                    "WHERE run_key = %s AND revision = %s",
                    (
                        revision, new.manifest_bytes, new.manifest_sha256,
                        new.status, new.record_count, run_key, expected_revision,
                    ),
                )
                if result.rowcount != 1:
                    raise PersistenceRejected("checkpoint_write_conflict")
            for page in new_pages:
                conn.execute(
                    "INSERT INTO mar_p0.checkpoint_pages "
                    "(run_key, sequence, artifact_sha256, record_count, "
                    "ids_sha256, input_cursor_sha256, next_cursor_sha256) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (run_key, *page[:6]),
                )
        return revision

    def restore(
        self, directory: str | Path, run_key: str, *,
        expected_scope: Mapping[str, str], expected_total: int,
    ) -> int:
        """Restore into a non-existent directory; never overwrite local work."""
        if not isinstance(run_key, str) or not 1 <= len(run_key) <= 200:
            raise PersistenceRejected("run_key_invalid")
        with self._connect() as conn:
            state = _fetch(conn, run_key, lock=False)
        if state is None:
            raise PersistenceRejected("checkpoint_not_found")
        payload = _validate(state)
        if (
            not isinstance(expected_total, int)
            or isinstance(expected_total, bool)
            or expected_total != state.expected_total
            or _digest(dict(expected_scope)) != state.scope_sha256
            or payload["scope"] != dict(expected_scope)
        ):
            raise PersistenceRejected("checkpoint_scope_or_total_mismatch")
        destination = Path(directory)
        destination.parent.mkdir(parents=True, exist_ok=True)
        lock = destination.parent / (destination.name + ".postgres-restore")
        with FileWriteLock(lock, timeout=10):
            if destination.exists():
                raise PersistenceRejected("restore_destination_exists")
            temp = Path(tempfile.mkdtemp(prefix=".mar-p0-", dir=destination.parent))
            try:
                for page in state.pages:
                    path = temp / "raw" / page[1][:2] / f"{page[1]}.json"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(page[6])
                (temp / "checkpoint.json").write_bytes(state.manifest_bytes)
                _restore(temp, payload, state.scope_sha256, state.expected_total)
                os.rename(temp, destination)
            finally:
                if temp.exists():
                    shutil.rmtree(temp)
        return state.revision
