#!/usr/bin/env python3
"""Fail-closed OFFLINE audit of known VAL-009 development exposures.

Checks historical files at the exact pinned commit. Does not visit any site,
calculate model predictions, change frozen results or approve a scientific seal.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

EXPECTED_SOURCE_COUNT = 4
EXPECTED_REVIEW_COUNT = 117
EXPECTED_REPORT_COUNT = 17
EXPECTED_REPORT_PAGES = 122
EXPECTED_HISTORICAL_EXTRAS = 20
EXPECTED_FIXTURE_CANDIDATES = 22
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_HEX40 = re.compile(r"[0-9a-f]{40}\Z")


class AuditError(ValueError):
    """Reject edited, incomplete, inconsistent or speculative exposure evidence."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def url_identity(url: str) -> str:
    """Normalize authority only; NEVER reorder/decode the path or query."""
    if not isinstance(url, str) or not url or any(ch.isspace() for ch in url):
        raise AuditError("Missing/invalid URL")
    try:
        parsed = urlsplit(url)
        scheme, host, port = parsed.scheme.lower(), parsed.hostname, parsed.port
        if scheme not in {"https", "http"} or not host:
            raise AuditError("Expected absolute HTTP(S) URL")
        if parsed.username is not None or parsed.password is not None:
            raise AuditError("Credential-bearing URLs cannot enter inventory")
        authority = f"[{host.lower()}]" if ":" in host else host.lower()
        if port is not None and (scheme, port) not in {("http", 80), ("https", 443)}:
            authority += f":{port}"
        return urlunsplit((scheme, authority, parsed.path, parsed.query, ""))
    except ValueError as exc:
        raise AuditError("Malformed HTTP(S) URL") from exc


def require_sha(value: Any, *, label: str, size: int = 64) -> None:
    pattern = _HEX40 if size == 40 else _HEX64
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise AuditError(f"Invalid {label} SHA-{size * 4}")


def validate_inventory(doc: dict[str, Any]) -> dict[str, Any]:
    if doc.get("status") != "draft_not_frozen" or doc.get("no_new_site_visits") is not True:
        raise AuditError("Unexpected inventory scientific status")
    require_sha(doc.get("historical_repository_revision"), label="historical commit", size=40)
    base = doc["original_exclusion_manifest"]
    require_sha(base["sha256"], label="baseline exclusion file")
    sources = base["source_files"]
    if len(sources) != EXPECTED_SOURCE_COUNT or sum(x["units"] for x in sources) != 117:
        raise AuditError("Missing or changed historical source counts")
    if len({x["path"] for x in sources}) != EXPECTED_SOURCE_COUNT:
        raise AuditError("Repeated historical source path")
    for src in sources:
        require_sha(src["sha256"], label=src["path"])
    if base["declared_units_total"] != 117 or base["declared_url_count"] != 117:
        raise AuditError("Incorrect legacy baseline total")
    reports = doc["historical_discovery_reports"]
    if len(reports) != EXPECTED_REPORT_COUNT or sum(r["pages_total"] for r in reports) != 122:
        raise AuditError("Wrong number of pinned historical discovery reports/pages")
    report_map = {}
    for rep in reports:
        require_sha(rep["sha256"], label=rep["path"])
        if rep["path"] in report_map:
            raise AuditError("Duplicated discovery report path")
        report_map[rep["path"]] = rep
    extras = doc["additional_confirmed_historical_pages"]
    if len(extras) != EXPECTED_HISTORICAL_EXTRAS:
        raise AuditError("Missing supplemental historical pages")
    urls = []
    seen_positions = set()
    for row in extras:
        source, index = row["source_report_path"], row["source_page_index"]
        if source not in report_map or type(index) is not int or not 0 <= index < report_map[source]["pages_total"]:
            raise AuditError("Invalid source report or page index")
        require_sha(row["source_report_sha256"], label="row source report")
        require_sha(row["reported_page_content_sha256"], label="reported page content")
        if row["source_report_sha256"] != report_map[source]["sha256"]:
            raise AuditError("Wrong source report digest on row")
        if (source, index) in seen_positions:
            raise AuditError("Duplicated source page reference")
        seen_positions.add((source, index))
        if (row["evidence_kind"] != "historical_discovery_page"
                or row["review_status"] != "confirmed_in_pinned_report"
                or row["exclusion_reason"] != "historically_captured_not_in_original_117"
                or row["redirect_alias_asserted"] is not False
                or row["requested_url"] is not None
                or row["final_url"] is not None):
            raise AuditError("Invented provenance or promoted aliases")
        url_identity(row["url"])
        if row["parent_url"] is not None:
            url_identity(row["parent_url"])
        if not isinstance(row["observed_at"], str) or not row["observed_at"].endswith("Z"):
            raise AuditError("Missing observation time")
        urls.append(row["url"])
    if len(set(urls)) != EXPECTED_HISTORICAL_EXTRAS or len({url_identity(x) for x in urls}) != 20:
        raise AuditError("Supplement collision or duplicate")
    fixtures = doc["nonvalidated_fixture_literals"]
    if len(fixtures) != EXPECTED_FIXTURE_CANDIDATES:
        raise AuditError("Unaccounted test URL literal")
    fixture_keys = set()
    for row in fixtures:
        if row.get("review_status") != "human_review_required" or row.get("auto_exclusion") is not False:
            raise AuditError("Fixture promoted to proven live capture")
        key = (row["source_path"], row["url"])
        if key in fixture_keys:
            raise AuditError("Repeated test literal")
        fixture_keys.add(key)
        url_identity(row["url"])
        require_sha(row["source_git_blob_sha"], label="fixture Git blob", size=40)
        require_sha(row["source_sha256"], label="fixture SHA-256")
    if len(doc["proposed_validation_entrypoints_not_evidence_of_independent_exposure"]) != 6:
        raise AuditError("Unreviewed draft target list")
    if doc["verified_count_claims"] != {
        "prior_reviewed_unique_urls": 117,
        "historical_discovery_reports": 17,
        "historical_report_page_observations": 122,
        "additional_unreviewed_historical_page_urls": 20,
        "distinct_confirmed_exact_urls": 137,
        "distinct_confirmed_conservative_identity_keys": 137,
        "nonvalidated_fixture_literals_pending_review": 22,
    }:
        raise AuditError("Unexpected summary count claim")
    return {"mode": "structure_only", "status": "draft_verified_not_sealed",
            "baseline_reviewed_units": 117, "additional_observed_pages": 20,
            "fixture_literals_require_review": 22}


def _pinned_file(historical_root: Path, relative: str) -> bytes:
    try:
        root = historical_root.resolve(strict=True)
    except OSError as exc:
        raise AuditError("Historical checkout inaccessible") from exc
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise AuditError("Source path escapes historical checkout")
    try:
        file = (root / path).resolve(strict=True)
    except OSError as exc:
        raise AuditError(f"Missing historical file: {relative}") from exc
    if not file.is_relative_to(root) or not file.is_file():
        raise AuditError("Missing or unsafe source file")
    return file.read_bytes()


def audit_historical_checkout(
    doc: dict[str, Any], historical_root: Path, *,
    allow_unversioned_synthetic: bool = False,
) -> dict[str, Any]:
    """Verify actual original source bytes, not content copied from manifest."""
    validate_inventory(doc)
    root = historical_root.resolve(strict=True)
    if (root / ".git").exists():
        try:
            p = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                               check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            raise AuditError("Cannot verify historical commit") from exc
        if p.stdout.strip() != doc["historical_repository_revision"]:
            raise AuditError("Historical checkout moved from pinned SHA")
    elif not allow_unversioned_synthetic:
        raise AuditError("Full audit requires Git checkout at pinned commit")
    base = doc["original_exclusion_manifest"]
    braw = _pinned_file(root, base["path"])
    if sha256(braw) != base["sha256"]:
        raise AuditError("Baseline exclusion source was modified")
    b = json.loads(braw)
    if b["status"] != "draft_not_frozen" or b["units_total"] != 117 or b["urls_total"] != 117:
        raise AuditError("Changed historical exclusion manifest")
    reviewed_urls = []
    for src in base["source_files"]:
        raw = _pinned_file(root, src["path"])
        if sha256(raw) != src["sha256"]:
            raise AuditError(f"Source bytes changed: {src['path']}")
        data = json.loads(raw)
        units = data.get("reviewed_units", data.get("units", []))
        if len(units) != src["units"]:
            raise AuditError("Historical review unit count changed")
        reviewed_urls.extend(row.get("page_url", row.get("url")) for row in units)
    if len(reviewed_urls) != 117 or len(set(reviewed_urls)) != 117 or set(reviewed_urls) != set(b["urls"]):
        raise AuditError("117 pinned URLs are not the exact union of original sources")
    extras, report_content = [], {}
    observed_count = 0
    for rep in doc["historical_discovery_reports"]:
        raw = _pinned_file(root, rep["path"])
        if sha256(raw) != rep["sha256"]:
            raise AuditError(f"Discovery report changed: {rep['path']}")
        data = json.loads(raw)
        if len(data["pages"]) != rep["pages_total"]:
            raise AuditError(f"Discovery report page count differs: {rep['path']}")
        report_content[rep["path"]] = data
        for index, page in enumerate(data["pages"]):
            observed_count += 1
            if page["url"] not in b["urls"]:
                extras.append((rep["path"], index, page["url"]))
    if observed_count != 122:
        raise AuditError("Incomplete 122 historical page observations")
    listed = [(x["source_report_path"], x["source_page_index"], x["url"])
              for x in doc["additional_confirmed_historical_pages"]]
    if sorted(extras) != sorted(listed):
        raise AuditError("Unreviewed original observations differ from supplement")
    for row in doc["additional_confirmed_historical_pages"]:
        page = report_content[row["source_report_path"]]["pages"][row["source_page_index"]]
        for own, historical in (("observed_at", "fetched_at"), ("parent_url", "parent_url"),
                                ("reported_page_content_sha256", "content_sha256")):
            if row[own] != page[historical]:
                raise AuditError("Historical observation metadata mismatch")
        if page["fetch_status"] != "fetched":
            raise AuditError("Supplement reported non-fetched as fetched")
    fixtures_by_path = {}
    for row in doc["nonvalidated_fixture_literals"]:
        fixtures_by_path.setdefault(row["source_path"], []).append(row)
    for path, rows in fixtures_by_path.items():
        raw = _pinned_file(root, path)
        digest = sha256(raw)
        git_blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
        for item in rows:
            if item["source_sha256"] != digest or item["source_git_blob_sha"] != git_blob:
                raise AuditError("Fixture source checksum mismatch")
            if item["url"].encode("utf-8") not in raw:
                raise AuditError("Fixture literal not found in pinned source")
    combined = reviewed_urls + [row[2] for row in extras]
    if len(set(combined)) != 137 or len({url_identity(url) for url in combined}) != 137:
        raise AuditError("Wrong conservative union of 117+20")
    return {
        "mode": "historical_checkout_reverified",
        "status": "draft_verified_not_sealed",
        "pinned_repository_revision": doc["historical_repository_revision"],
        "source_review_units": 117,
        "historical_source_reports": 17,
        "historical_report_pages": 122,
        "additional_confirmed_historical_pages": 20,
        "distinct_exact_exclusions": 137,
        "distinct_conservative_identity_keys": 137,
        "test_literals_still_require_manual_review": 22,
        "aliases_proven_from_legacy_requested_final": 0,
        "old_reports_raw_http_bytes_verified": False,
    }


def build_draft_exclusions(doc: dict[str, Any], historical_root: Path) -> dict[str, Any]:
    """Produce unsealed 137-URL preview, not an authorized scientific freeze."""
    audit_historical_checkout(doc, historical_root)
    old = json.loads(_pinned_file(historical_root, doc["original_exclusion_manifest"]["path"]))["urls"]
    combined = sorted(set(old + [r["url"] for r in doc["additional_confirmed_historical_pages"]]))
    if len(combined) != 137 or len({url_identity(url) for url in combined}) != 137:
        raise AuditError("Unsafe or incomplete consolidated draft")
    return {
        "status": "draft_pending_manual_fixture_and_alias_review",
        "source_historical_commit": doc["historical_repository_revision"],
        "source_original_exclusion_sha256": doc["original_exclusion_manifest"]["sha256"],
        "units_from_original_review_sources": 117,
        "additional_confirmed_historical_pages": 20,
        "urls_total": 137,
        "urls": combined,
        "excluded_fixture_literal_candidates": False,
        "unresolved_fixture_literals": 22,
        "independent_validation_executed": False,
        "scientific_seal_authorized": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inventory", type=Path,
        default=Path(__file__).resolve().parents[1] / "data" /
                "digital_infrastructure" / "ai_experiments" /
                "m3_surface_type_exposure_inventory_v2_3_draft.json",
    )
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--structure-only", action="store_true")
    modes.add_argument("--historical-root", type=Path)
    parser.add_argument("--write-preview", type=Path,
                        help="Only with --historical-root; output remains an unsealed draft")
    args = parser.parse_args()
    if args.write_preview and args.historical_root is None:
        parser.error("--write-preview requires --historical-root")
    data = json.loads(args.inventory.read_text(encoding="utf-8"))
    result = (validate_inventory(data) if args.structure_only else
              audit_historical_checkout(data, args.historical_root))
    if args.write_preview:
        preview = build_draft_exclusions(data, args.historical_root)
        args.write_preview.write_text(
            json.dumps(preview, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        result["preview_written"] = str(args.write_preview)
        result["preview_status"] = preview["status"]
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
