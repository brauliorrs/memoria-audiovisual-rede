"""Offline proposals for Eye Filmmuseum and Czech Television archival fiches.

Never opens network connections, writes catalog files, infers media rights,
publishes records, or interprets absence in a partial probe as deletion.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from urllib.parse import urlsplit

EYE_HOST = "filmdatabase.eyefilm.nl"
CZECH_HOST = "www.ceskatelevize.cz"
METADATA_FIELDS = ("title", "subject", "description", "date")
MAX_CANDIDATES = 100
HEX_SHA = re.compile(r"[0-9a-f]{64}\Z")


class ReconciliationRejected(ValueError):
    """A source assertion or validation condition was not met."""


def _url(value: object, *, corpus: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value or "\\" in value:
        raise ReconciliationRejected("invalid_record_url")
    try:
        p = urlsplit(value)
        host, port = p.hostname, p.port
    except ValueError as exc:
        raise ReconciliationRejected("invalid_record_url") from exc
    target = EYE_HOST if corpus == "eye" else CZECH_HOST
    if (
        p.scheme != "https" or host != target or port not in (None, 443)
        or p.username or p.password or p.query or p.fragment
        or not p.path or any(ord(c) < 32 for c in value)
        or re.search(r"\.(mp4|mov|mkv|webm|m3u8|mpd|ts)$", p.path, flags=re.I)
    ):
        raise ReconciliationRejected("non_institutional_record_url")
    if corpus == "eye":
        if not (p.path.startswith("/en/collection/film-history/film/")
                or re.fullmatch(r"/en/node/[0-9]+/?", p.path)):
            raise ReconciliationRejected("not_eye_record_page")
    elif not re.fullmatch(r"/porady/[^/]+/[0-9]+/?", p.path):
        raise ReconciliationRejected("not_czech_episode_page")
    return value


def _normalize_record(row: Mapping, *, corpus: str) -> dict:
    if not isinstance(row, Mapping):
        raise ReconciliationRejected("record_not_mapping")
    url_key = "video_link" if "video_link" in row else "page_url"
    url = _url(row.get(url_key), corpus=corpus)
    if row.get("page_url") and row.get("video_link") and row["page_url"] != row["video_link"]:
        raise ReconciliationRejected("record_page_mismatch")
    fields = {
        "title": row.get("video_title") if "video_title" in row else row.get("title"),
        "subject": row.get("video_subject") if "video_subject" in row else row.get("subject"),
        "description": row.get("video_description") if "video_description" in row else row.get("description"),
        "date": row.get("video_published_at") if "video_published_at" in row else row.get("date"),
    }
    for k, v in fields.items():
        if v is None:
            fields[k] = ""
        elif not isinstance(v, str) or len(v) > 2400:
            raise ReconciliationRejected("invalid_record_descriptor")
    if not fields["title"] or not fields["title"].strip():
        raise ReconciliationRejected("record_title_missing")
    return {"origin_url": url, **fields}


def _fingerprint(record: Mapping) -> str:
    # Never hash the full source HTML, image URLs or media addresses.
    payload = {key: record[key] for key in METADATA_FIELDS}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=True,
                                      separators=(",", ":")).encode("utf-8")).hexdigest()


def reconcile_eye(
    baseline: Sequence[Mapping], candidates: Sequence[Mapping], *,
    evidence_sha256: str, evidence_verified: bool, sample_complete: bool = False,
) -> dict:
    """Classify candidate Eye institutional fiches without deletion decisions."""
    if not evidence_verified or not isinstance(evidence_sha256, str) or not HEX_SHA.fullmatch(evidence_sha256):
        raise ReconciliationRejected("independent_evidence_required")
    if not isinstance(sample_complete, bool) or not isinstance(candidates, list) or not 0 < len(candidates) <= MAX_CANDIDATES:
        raise ReconciliationRejected("bounded_sample_required")
    originals: dict[str, dict] = {}
    for row in baseline:
        rec = _normalize_record(row, corpus="eye")
        if rec["origin_url"] in originals:
            raise ReconciliationRejected("baseline_duplicate_url")
        originals[rec["origin_url"]] = rec
    proposed: dict[str, dict] = {}
    source_ids: set[str] = set()
    for row in candidates:
        rec = _normalize_record(row, corpus="eye")
        rid = row.get("record_id")
        if not isinstance(rid, str) or not rid or len(rid) > 220 or rid in source_ids:
            raise ReconciliationRejected("candidate_duplicate_or_missing_id")
        if rec["origin_url"] in proposed:
            raise ReconciliationRejected("candidate_duplicate_url")
        source_ids.add(rid)
        proposed[rec["origin_url"]] = {"source_record_id": rid, **rec}
    changes = []
    for url, rec in sorted(proposed.items()):
        old = originals.get(url)
        status = ("new" if old is None else "unchanged"
                  if _fingerprint(old) == _fingerprint(rec) else "changed")
        changes.append({
            "status": status, "source_record_id": rec["source_record_id"],
            "origin_url": url, "title": rec["title"],
            "metadata_sha256": _fingerprint(rec),
            "changed_fields": ([k for k in METADATA_FIELDS if old[k] != rec[k]]
                               if old is not None and status == "changed" else []),
        })
    # Not observed means never removed, regardless of declared completeness.
    unseen = sorted(set(originals) - set(proposed))
    return {
        "corpus": "eye", "status": "review_preview_only",
        "evidence_sha256": evidence_sha256, "evidence_verified": True,
        "baseline_count": len(originals), "sample_count": len(candidates),
        "sample_complete_claim": sample_complete, "not_observed_count": len(unseen),
        "not_observed_meaning": "absence_not_deletion",
        "changes": changes,
        "counts": {s: sum(x["status"] == s for x in changes)
                   for s in ("new", "changed", "unchanged")},
        "publication_authorized": False, "media_downloaded": False,
        "corpus_activation": False, "production_gate": "HOLD",
    }


def screen_czech_episode(
    parsed_episode: Mapping, *, evidence_sha256: str,
    evidence_verified: bool,
) -> dict:
    """Screen ONE already-parsed episode; never affirm current playback."""
    if not evidence_verified or not isinstance(evidence_sha256, str) or not HEX_SHA.fullmatch(evidence_sha256):
        raise ReconciliationRejected("independent_evidence_required")
    if not isinstance(parsed_episode, Mapping) or not parsed_episode:
        return {
            "corpus": "czech-television", "status": "HOLD",
            "reason": "episode_not_observed_or_not_parseable",
            "publication_authorized": False, "production_gate": "HOLD",
        }
    if parsed_episode.get("embedded") is not True:
        raise ReconciliationRejected("czech_episode_not_confirmed_in_source_evidence")
    rec = _normalize_record(parsed_episode, corpus="czech")
    rid = parsed_episode.get("record_id")
    if not isinstance(rid, str) or not rid or len(rid) > 220:
        raise ReconciliationRejected("invalid_czech_episode_id")
    return {
        "corpus": "czech-television", "status": "candidate_for_review",
        "source_record_id": rid, "origin_url": rec["origin_url"],
        "title": rec["title"], "metadata_sha256": _fingerprint(rec),
        "evidence_sha256": evidence_sha256,
        "playback_currently_verified": False, "media_rights_verified": False,
        "publication_authorized": False, "media_downloaded": False,
        "corpus_activation": False, "production_gate": "HOLD",
    }
