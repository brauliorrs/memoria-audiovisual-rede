"""Read-only MAR corpus admin queries and explicitly operated registry mirroring.

Postgres is a provenance/audit *projection*, not the scientific approval
authority or the source that enables PR #95 publication. No network calls
occur on module import; a caller must supply its own scoped PG connection.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from .corpus_admission_engine import REGISTRY, ConnectorSpec

MAX_PAGE_SIZE = 50


class RegistryDrift(RuntimeError):
    """Database registry diverged from the immutable reviewed code contract."""


def connector_digest(spec: ConnectorSpec) -> str:
    payload = {
        "corpus_code": spec.corpus_code,
        "institution": spec.institution,
        "adapter_module": spec.adapter_module,
        "record_hosts": sorted(spec.record_hosts),
        "source_kind": spec.source_kind,
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True,
                     separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def sync_registered_connectors(conn: Any) -> dict[str, int]:
    """Operator-only, idempotent insert of reviewed code definitions.

    Reject a changed spec instead of altering existing database history.
    Does not advance validation states, register scientific approvals, or
    import any fiches. The connection must be an independently scoped writer.
    """
    inserted = 0
    unchanged = 0
    with conn.transaction():
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT pg_has_role(current_user, 'mar_corpora_ingester', 'member')"
            )
            proof = cursor.fetchone()
            if not proof or proof[0] is not True:
                raise PermissionError("dedicated_ingester_role_required")
            for code, spec in sorted(REGISTRY.items()):
                digest = connector_digest(spec)
                cursor.execute(
                    "SELECT spec_sha256 FROM mar_corpora.connector_registry "
                    "WHERE corpus_code = %s",
                    (code,),
                )
                existing = cursor.fetchone()
                if existing is not None:
                    if existing[0] != digest:
                        raise RegistryDrift("registry_spec_changed_requires_review:" + code)
                    unchanged += 1
                    continue
                cursor.execute(
                    "INSERT INTO mar_corpora.connector_registry "
                    "(corpus_code, institution, adapter_module, record_hosts, "
                    "source_kind, spec_sha256) VALUES (%s, %s, %s, %s, %s, %s)",
                    (
                        code, spec.institution, spec.adapter_module,
                        sorted(spec.record_hosts), spec.source_kind, digest,
                    ),
                )
                cursor.execute(
                    "INSERT INTO mar_corpora.audit_events "
                    "(corpus_code, event_kind, actor_ref, evidence_sha256, "
                    "evidence_ref, note) "
                    "VALUES (%s, 'registered', 'registry-sync', %s, %s, "
                    "'Code connector registration only; no publication approval')",
                    (code, digest, "code:corpus_admission_engine.REGISTRY"),
                )
                inserted += 1
    return {"inserted": inserted, "unchanged": unchanged, "total": len(REGISTRY)}


def _validated_page(page: int, page_size: int) -> tuple[int, int]:
    if (type(page) is not int or page < 1 or type(page_size) is not int
            or not 1 <= page_size <= MAX_PAGE_SIZE):
        raise ValueError("invalid_page")
    return page_size, (page - 1) * page_size


def list_corpora(conn: Any, *, page: int = 1, page_size: int = 25,
                 search: str = "", stage: str = "") -> dict[str, Any]:
    """Paginated read from audit projection; no authorization decisions."""
    limit, offset = _validated_page(page, page_size)
    if not isinstance(search, str) or len(search) > 120:
        raise ValueError("invalid_search")
    if not isinstance(stage, str) or len(stage) > 64:
        raise ValueError("invalid_stage")
    where = (
        " WHERE (%s = '' OR corpus_code ILIKE %s OR institution ILIKE %s)"
        " AND (%s = '' OR COALESCE(last_reported_stage, '') = %s)"
    )
    term = "%" + search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    # ESCAPE is applied to all user-supplied LIKE patterns.
    where = where.replace(" ILIKE %s", " ILIKE %s ESCAPE '\\'")
    parameters = (search, term, term, stage, stage)
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT count(*) FROM mar_corpora.current_status" + where,
            parameters,
        )
        total = cursor.fetchone()[0]
        cursor.execute(
            "SELECT corpus_code, institution, source_kind, record_hosts, "
            "last_reported_stage, last_event_id, last_event_at, "
            "publication_authorized, scientific_validation_proven_by_database "
            "FROM mar_corpora.current_status" + where +
            " ORDER BY corpus_code LIMIT %s OFFSET %s",
            parameters + (limit, offset),
        )
        rows = cursor.fetchall()
    return {"total": total, "page": page, "page_size": page_size,
            "rows": rows}


def list_corpus_events(conn: Any, corpus_code: str, *, limit: int = 30) -> list[Any]:
    if corpus_code not in REGISTRY:
        raise ValueError("unregistered_corpus")
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("invalid_limit")
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT event_id, event_kind, actor_ref, evidence_sha256, "
            "evidence_ref, note, recorded_at "
            "FROM mar_corpora.audit_events WHERE corpus_code = %s "
            "ORDER BY event_id DESC LIMIT %s",
            (corpus_code, limit),
        )
        return cursor.fetchall()


def read_only_role_assertion(conn: Any) -> None:
    """Fail closed unless connection uses reader role and not owner privileges."""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT pg_has_role(current_user, 'mar_corpora_reader', 'member'), "
            "has_table_privilege(current_user, 'mar_corpora.audit_events', 'INSERT'), "
            "has_table_privilege(current_user, 'mar_corpora.audit_events', 'UPDATE'), "
            "has_table_privilege(current_user, 'mar_corpora.audit_events', 'DELETE')"
        )
        row = cursor.fetchone()
    if row is None or row[0] is not True or any(row[1:]):
        raise PermissionError("scoped_read_only_role_required")
