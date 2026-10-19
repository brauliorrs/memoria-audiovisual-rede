"""Project independently audited Finna staging into MAR's link-only catalog schema.

Reads existing metadata artifacts only. Never contacts Finna, downloads media,
infers ownership from provider, guesses a record URL, or activates a corpus.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

from .digital_infrastructure.locking import FileWriteLock
from .external_links import choose_origin_destination, public_external_url
from .kavi_finna_adapter import FinnaScope
from .metadata_staging import StageRejected, _digest, _restore

VERSION = "kavi-finna-mar-link-index-1.0"
FINNA_ORIGIN = "https://www.finna.fi/"
FINNA_HOSTS = frozenset({"www.finna.fi", "finna.fi", "elonet.finna.fi"})
SOURCE_FIELD_NAMES = (
    "title", "year", "publicationDate", "originalPublicationDate",
    "authors", "primaryAuthors", "genres", "subjects", "languages",
    "summary", "description", "formats", "institutions",
)
INDEX_FIELDS = (
    "corpus", "institution", "country", "continent", "platform",
    "source_record_id", "source_record_url", "source_service",
    "metadata_provider", "custodian", "video_link", "partner_site",
    "video_title", "video_subject", "video_description",
    "video_published_at", "year", "authors", "genres", "subjects",
    "languages", "format", "metadata_license", "rights_status",
    "media_access_status", "media_rights_status", "custody_status",
    "film_semantics", "online_url_metadata_present",
    "link_status", "record_review_status", "scope_sha256",
)


def _safe_record_link(value: object, record_id: str) -> str | None:
    """Resolve only API-advertised recordPage; never manufacture from an ID."""
    if not isinstance(value, str) or not value or value != value.strip():
        return None
    if value.startswith("//") or "\\" in value or "#" in value:
        return None
    raw = urlsplit(value)
    if raw.scheme or raw.netloc:
        if raw.scheme != "https" or raw.hostname not in FINNA_HOSTS:
            return None
        candidate = value
    else:
        if not value.startswith(("/Record/", "Record/")):
            return None
        candidate = urljoin(FINNA_ORIGIN, value)
    candidate = public_external_url(candidate)
    if candidate is None:
        return None
    parts = urlsplit(candidate)
    if (parts.hostname not in FINNA_HOSTS or parts.path.count("/") != 2
            or not parts.path.startswith("/Record/")
            or unquote(parts.path.split("/")[2]) != record_id
            or parts.query or parts.fragment or parts.username or parts.password):
        return None
    dest = choose_origin_destination(candidate)
    return candidate if dest.url == candidate and dest.kind == "record_or_platform" else None


def _str_value(value: object, limit: int = 600) -> str:
    if isinstance(value, str):
        return " ".join(value.split())[:limit]
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)[:limit]
    return ""


def _flatten(value: object, *, limit: int = 750) -> str:
    """Narrowly display descriptive values, not arbitrary serialized blobs."""
    if isinstance(value, (str, int, float)) and not isinstance(value, bool):
        return _str_value(value, limit)
    if isinstance(value, dict):
        return _str_value(value.get("name") or value.get("value")
                          or value.get("translated") or "", limit)
    if isinstance(value, list):
        values = [_flatten(item, limit=limit) for item in value[:40]]
        return "; ".join(x for x in values if x)[:limit]
    return ""


def project_record(
    raw: dict, *, scope_sha256: str,
    verified_origin_urls: dict[str, str] | None = None,
) -> dict:
    """Emit one MAR record, unknowns explicit; links must be source-evidenced."""
    if not isinstance(raw, dict):
        raise StageRejected("mar_source_record_not_object")
    rid = raw.get("id")
    title = raw.get("title")
    if not isinstance(rid, str) or not rid or not isinstance(title, str) or not title.strip():
        raise StageRejected("mar_source_id_title_invalid")
    formats = raw.get("formats")
    if not isinstance(formats, list) or not any(
        isinstance(f, dict) and f.get("value") == "0/Video/" for f in formats
    ):
        raise StageRejected("mar_non_video_record")
    # recordPage is a documented API-provided relative link to the Finna
    # human record, while verified origin links can prefer Elonet specifically.
    record_page = _safe_record_link(raw.get("recordPage"), rid)
    if verified_origin_urls and rid in verified_origin_urls:
        origin = _safe_record_link(verified_origin_urls[rid], rid)
        if origin is None:
            raise StageRejected("mar_verified_origin_link_invalid")
        record_page = origin
    # This row remains discoverable by ID even when the source didn't return
    # recordPage. Never synthesize '/Record/' + ID from an index prefix.
    link_status = "item_link_verified_by_source" if record_page else "missing_source_item_link"
    year = _str_value(raw.get("year") or raw.get("publicationDate")
                      or raw.get("originalPublicationDate"), 64)
    desc = _flatten(raw.get("summary") or raw.get("description"), limit=1600)
    subjects = _flatten(raw.get("subjects"))
    return {
        "corpus": "fiaf-kavi",
        "institution": "Kuvi (KAVI historical provider)",
        "country": "Finland",
        "continent": "Europe",
        "platform": "Finna / Elonet",
        "source_record_id": rid,
        "source_record_url": record_page or "",
        "source_service": "finna_api",
        "metadata_provider": "0/KAVI/",
        "custodian": "unknown",
        "video_link": record_page or "",
        "partner_site": record_page or "",
        "video_title": _str_value(title, 600),
        "video_subject": subjects,
        "video_description": desc,
        "video_published_at": year,
        "year": year,
        "authors": _flatten(raw.get("primaryAuthors") or raw.get("authors")),
        "genres": _flatten(raw.get("genres")),
        "subjects": subjects,
        "languages": _flatten(raw.get("languages")),
        "format": "0/Video/",
        "metadata_license": "CC0-1.0_API_metadata_only",
        "rights_status": "media_rights_unverified",
        "media_access_status": "unverified",
        "media_rights_status": "not_verified",
        "custody_status": "not_established",
        "film_semantics": (
            "film_candidate" if rid.startswith("kavi.elonet_elokuva_")
            else "unverified_audiovisual_record"
        ),
        # Never export raw onlineUrls, media stream addresses or image bytes.
        "online_url_metadata_present": bool(raw.get("onlineUrls")),
        "link_status": link_status,
        "record_review_status": "unreviewed",
        "scope_sha256": scope_sha256,
    }


def project_staged_catalog(
    directory: str | Path, output_dir: str | Path, *,
    evidence_sha256: str, expected_total: int,
    verified_origin_urls: dict[str, str] | None = None,
) -> dict:
    """Create an OFFLINE non-publication preview from audited staged pages.

    No dependency on total completeness: a partial snapshot is accurately
    labeled. Caller must use an output directory outside MAR's active data/.
    """
    from scripts.audit_kavi_finna_staging import audit_finna_staging

    folder, destination = Path(directory), Path(output_dir)
    if folder.resolve() == destination.resolve() or folder.resolve() in destination.resolve().parents:
        raise StageRejected("mar_output_inside_staging_prohibited")
    if destination.exists() and any(destination.iterdir()):
        raise StageRejected("mar_output_directory_not_empty")
    audit = audit_finna_staging(
        folder, evidence_sha256=evidence_sha256, expected_total=expected_total,
    )
    scope = FinnaScope("0/KAVI/", "0/Video/", evidence_sha256).to_dict()
    rows = []
    seen = set()
    with FileWriteLock(folder / "run", timeout=10):
        manifest = json.loads((folder / "checkpoint.json").read_text(encoding="utf-8"))
        _restore(folder, manifest, _digest(scope), expected_total)
        if manifest["record_count"] != audit["record_count"]:
            raise StageRejected("mar_audit_checkpoint_changed")
        for entry in manifest["pages"]:
            sha = entry["artifact_sha256"]
            raw_path = folder / "raw" / sha[:2] / f"{sha}.json"
            blob = raw_path.read_bytes()
            if hashlib.sha256(blob).hexdigest() != sha:
                raise StageRejected("mar_raw_artifact_changed")
            page = json.loads(blob)["page"]
            source_rows = page["source_response"]["records"]
            normalized_ids = [rec["id"] for rec in page["records"]]
            if [rec.get("id") for rec in source_rows] != normalized_ids:
                raise StageRejected("mar_source_normalized_ids_mismatch")
            for raw in source_rows:
                row = project_record(
                    raw, scope_sha256=manifest["scope_sha256"],
                    verified_origin_urls=verified_origin_urls,
                )
                identity = row["source_record_id"]
                if identity in seen:
                    raise StageRejected("mar_duplicate_identity")
                seen.add(identity)
                rows.append(row)
    if len(rows) != audit["record_count"]:
        raise StageRejected("mar_row_count_mismatch")
    # Partial coverage is allowed for a REVIEW PREVIEW, but is never silently
    # published as a completed MAR corpus.
    destination.mkdir(parents=True, exist_ok=True)
    csv_file = destination / "kavi_mar_metadata_links_PREVIEW.csv"
    json_file = destination / "kavi_mar_metadata_links_PREVIEW.json"
    with csv_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=INDEX_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    json_file.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    report = {
        "schema_version": VERSION,
        "unit_id": "fiaf-kavi",
        "status": "review_preview_only",
        "source_staging_status": manifest["status"],
        "coverage_status": "partial" if manifest["status"] == "partial" else "complete_api_scope",
        "expected_total_api_index": expected_total,
        "record_count": len(rows),
        "item_links_present": sum(bool(r["video_link"]) for r in rows),
        "item_links_missing": sum(not bool(r["video_link"]) for r in rows),
        "record_ids_unique": len(rows) == len(seen),
        "source_scope_sha256": manifest["scope_sha256"],
        "metadata_license": "CC0-1.0_API_metadata_only",
        "media_downloaded": False,
        "promotion_authorized": False,
        "corpus_active": False,
        "viewing_at_origin_only": True,
    }
    (destination / "kavi_mar_projection_manifest.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report
