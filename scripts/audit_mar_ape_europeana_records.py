#!/usr/bin/env python3
"""Audit EVERY historical Europeana and APE row without accessing the network.

Two different entities must never be conflated:
* Europeana item metadata (CC0 general policy), versus rights in linked objects.
* APE archival institutional metadata (CC BY-SA default), versus videos hosted by
  third-party services found on institutional websites.

The output is a private documentary review artifact, NOT a publication manifest.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "europeana": "data/output/europeana_catalogo_videos_analitico.csv",
    "ape": "data/output/ape_catalogo_videos_analitico.csv",
}
EXPECTED_ROWS = {"europeana": 20, "ape": 412}
GENERIC_TITLES = {"", "youtube", "- youtube", "video", "moving", "audiovisual.", "- video -, film, video", "- video -, video"}


def host(url: str) -> str:
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in {"https", "http"} or not parsed.hostname:
            return ""
        return parsed.hostname.lower()
    except ValueError:
        return ""


def european_item_id(url: str) -> str | None:
    if host(url) != "www.europeana.eu":
        return None
    path = urlsplit(url).path
    match = re.fullmatch(r"/(?:[a-z]{2}/)?item/([^/]+)/(.+?)/?", path)
    return "/".join(match.groups()) if match else None


def ape_repository_code(row: dict[str, str]) -> str | None:
    code = row.get("repository_code", "").strip()
    link = row.get("ape_detail_url", "")
    if not code or host(link) not in {"www.archivesportaleurope.net", "archivesportaleurope.net"}:
        return None
    query_code = parse_qs(urlsplit(link).query).get("repositoryCode", [None])[0]
    return code if query_code == code else None


def video_identity(url: str) -> str | None:
    """Only identifies candidate external video identity; never authorizes playback."""
    parsed = urlsplit(url)
    domain = (parsed.hostname or "").lower()
    path = parsed.path.strip("/")
    if domain in {"youtube.com", "www.youtube.com", "youtube-nocookie.com", "www.youtube-nocookie.com"}:
        parts = path.split("/")
        if len(parts) == 2 and parts[0] in {"embed", "shorts", "watch"}:
            return "youtube:" + parts[-1]
        q = parse_qs(parsed.query).get("v", [])
        return "youtube:" + q[0] if q else None
    if domain == "youtu.be":
        return "youtube:" + path.split("/")[0] if path else None
    if domain in {"player.vimeo.com", "vimeo.com", "www.vimeo.com"}:
        parts = path.split("/")
        if parts and parts[-1].isdigit():
            return "vimeo:" + parts[-1]
        if len(parts) == 2 and parts[-2] == "video" and parts[-1].isdigit():
            return "vimeo:" + parts[-1]
    return None


def rights_category(description: str) -> str:
    match = re.search(r"direitos:\s*(.*)$", description or "", re.IGNORECASE)
    value = match.group(1).strip() if match else ""
    if not value:
        return "object_rights_not_recorded"
    lower = value.lower()
    if "creativecommons.org/licenses/by-sa/" in lower:
        return "object_cc_by_sa_claim_in_snapshot"
    if any(word in lower for word in ("ickekommersiell", "noncommercial", "inga bearbetningar", "no derivatives")):
        return "object_restrictive_cc_claim_in_snapshot"
    if any(word in lower for word in ("copyright", "all rights reserved", "©", "απαγορεύεται")):
        return "object_copyright_or_restriction_claim"
    return "object_rights_other_unverified"


def audit(code: str, root: Path = ROOT) -> dict:
    if code not in SOURCES:
        raise ValueError("unknown corpus")
    path = root / SOURCES[code]
    data = path.read_bytes()
    if len(data) > 3_000_000:
        raise ValueError("input too large")
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required = {"institution", "repository_code", "video_link", "video_title", "video_description", "partner_site"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("missing expected columns")
        rows = list(reader)
    if len(rows) != EXPECTED_ROWS[code] and root == ROOT:
        raise ValueError("unexpected source row count; freeze and investigate")
    records = []
    link_occurrences = defaultdict(list)
    identity_occurrences = defaultdict(list)
    for line, row in enumerate(rows, start=2):
        if None in row or any(not isinstance(v, str) for v in row.values()):
            raise ValueError(f"malformed CSV row at {line}")
        url = row["video_link"].strip()
        title = (row.get("video_title_display") or row["video_title"]).strip()
        provider = (row["partner_site"] or "").strip()
        issues = []
        if not title or title.casefold() in GENERIC_TITLES:
            issues.append("missing_or_generic_title")
        if not provider:
            issues.append("missing_provider")
        if not host(url):
            issues.append("invalid_media_or_item_url")
        if code == "europeana":
            item = european_item_id(url)
            kind = "europeana_item_page" if item else "not_europeana_item_page"
            if not item:
                issues.append("missing_europeana_item_identifier")
            description = row.get("video_description", "")
            declared_type = (re.search(r"tipo Europeana:\s*([^;]*);", description) or [None, ""])[1].strip()
            if not any(word in declared_type.casefold() for word in ("video", "moving", "audiovisual", "vídeo")):
                issues.append("audiovisual_type_not_proven")
            rights = rights_category(description)
            # Even a rights statement that appears permissive in a historical
            # description is an unverified claim about an object, not approval.
            issues.append("object_rights_require_independent_review")
            identifier = item
            licence = "CC0 general metadata policy; individual object rights distinct"
        else:
            identifier = ape_repository_code(row)
            kind = "third_party_media_link"
            declared_type = row.get("platform", "").strip()
            rights = "third_party_object_rights_unverified"
            licence = "APE CC BY-SA applies to APE-hosted archival metadata only"
            issues.append("third_party_media_not_ape_metadata")
            if not identifier:
                issues.append("ape_institution_identifier_unverified")
            # APE institution search links and repository codes are NOT archival item IDs.
            issues.append("no_ape_archival_item_identifier")
        link_occurrences[url].append(line)
        vid = video_identity(url)
        if vid:
            identity_occurrences[vid].append(line)
        records.append({
            "csvLine": line,
            "sourceInstitution": row["institution"].strip(),
            "provider": provider,
            "repositoryCode": row["repository_code"].strip(),
            "sourceInstitutionPage": row.get("ape_detail_url", "").strip() if code == "ape" else None,
            "title": title,
            "itemOrMediaUrl": url,
            "urlHost": host(url),
            "sourceItemIdentifier": identifier if code == "europeana" else None,
            "institutionIdentifier": identifier if code == "ape" else None,
            "thirdPartyMediaIdentity": vid if code == "ape" else None,
            "recordKind": kind,
            "declaredType": declared_type,
            "objectRightsFlag": rights,
            "metadataLicencePolicy": licence,
            "issues": issues,
            "currentPageVerified": False,
            "mediaRightsVerified": False,
            "scientificallyApproved": False,
            "publicationApproved": False,
        })
    for record in records:
        if len(link_occurrences[record["itemOrMediaUrl"]]) > 1:
            record["issues"].append("duplicate_exact_link")
        if record["thirdPartyMediaIdentity"] and len(identity_occurrences[record["thirdPartyMediaIdentity"]]) > 1:
            record["issues"].append("duplicate_third_party_media_identity")
    count = Counter(issue for record in records for issue in record["issues"])
    hosts = Counter(record["urlHost"] for record in records)
    rights = Counter(record["objectRightsFlag"] for record in records)
    return {
        "corpus": code,
        "sourcePath": SOURCES[code],
        "sourceSha256": hashlib.sha256(data).hexdigest(),
        "rowsAudited": len(records),
        "uniqueExactLinks": len(link_occurrences),
        "duplicatesExactExtraRows": sum(len(v) - 1 for v in link_occurrences.values() if len(v) > 1),
        "uniqueThirdPartyMediaIdentities": len(identity_occurrences),
        "issues": dict(sorted(count.items())),
        "hosts": dict(sorted(hosts.items())),
        "objectRightsFlags": dict(sorted(rights.items())),
        "records": records,
        "publicationAllowed": False,
        "inspectionLimitations": [
            "current live individual-page HTTP access not checked by this offline audit",
            "source claims in historical description are not current verified object licences",
            "scientific review and attribution verification not performed",
            "institutional metadata licence is not a licence to third-party media",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="evidence JSON outside site and historical data")
    args = parser.parse_args()
    report = {
        "schema": "mar-ape-europeana-item-audit-v1",
        "generatedBy": "offline deterministic row review",
        "corpora": [audit(c) for c in ("europeana", "ape")],
        "publicationAllowed": False,
    }
    content = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        target = args.output.resolve()
        for protected in (ROOT / "site", ROOT / "data"):
            p = protected.resolve()
            if target == p or p in target.parents:
                parser.error("do not write review artifacts into site/ or data/")
        if target.exists():
            parser.error("do not overwrite preexisting audit evidence")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    for corpus in report["corpora"]:
        print(json.dumps({k: v for k, v in corpus.items() if k != "records"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
