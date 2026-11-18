#!/usr/bin/env python3
"""Offline, read-only complete integrity audit of historical MAR Eye/Czech CSVs.

Checks *syntax and consistency* of every row, never tests whether HTTP links
currently work. Only an explicit, separate live review can establish that.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote, urlsplit

from import_mar_multicorpus import CORPORA, ROOT, MAX_INPUT_BYTES

REQUIRED = {"institution", "video_link", "video_title"}
EXAMPLE_LIMIT = 12


def inspect_url(value: str, corpus: str):
    try:
        p = urlsplit(value)
        if (p.scheme != "https" or p.hostname not in CORPORA[corpus]["url_hosts"]
            or p.username or p.password or p.port or not p.path.strip("/")
            or p.fragment or any(ch.isspace() for ch in value)):
            return None, "invalid_or_nonofficial_url"
        # URL identifiers are opaque for publication, but a syntactically
        # equivalent URL is useful to detect collision due to trailing slash.
        normalized_path = unquote(p.path).rstrip("/")
        canonical = "https://" + p.hostname.lower() + normalized_path
        if p.query:
            canonical += "?" + p.query
        return canonical, None
    except (ValueError, UnicodeError):
        return None, "invalid_or_nonofficial_url"


def audit(corpus: str, root: Path = ROOT):
    if corpus not in CORPORA:
        raise ValueError("unsupported corpus")
    relative = CORPORA[corpus]["path"]
    path = root / relative
    if not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("source absent or too large")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    issues = Counter()
    examples = defaultdict(list)
    urls, canonical_urls, ids = {}, {}, {}
    titles_by_url = defaultdict(set)
    identity_by_url = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
            raise ValueError("unrecognized CSV schema")
        rows = 0
        for line, row in enumerate(reader, start=2):
            rows += 1
            if None in row:  # malformed column count
                issues["malformed_row"] += 1
                if len(examples["malformed_row"]) < EXAMPLE_LIMIT:
                    examples["malformed_row"].append({"line": line})
                continue
            value = (row.get("video_link") or "").strip()
            title = (row.get("video_title_display") or row.get("video_title") or "").strip()
            if not title:
                issues["blank_title"] += 1
                if len(examples["blank_title"]) < EXAMPLE_LIMIT:
                    examples["blank_title"].append({"line": line})
            if (row.get("institution") or "").strip() != CORPORA[corpus]["institution"]:
                issues["institution_mismatch"] += 1
                if len(examples["institution_mismatch"]) < EXAMPLE_LIMIT:
                    examples["institution_mismatch"].append({"line": line})
            canonical, error = inspect_url(value, corpus)
            if error:
                issues[error] += 1
                if len(examples[error]) < EXAMPLE_LIMIT:
                    examples[error].append({"line": line, "url": value[:200]})
                continue
            identity = corpus + "." + hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]
            for name, table, key in (
                ("duplicate_exact_url", urls, value),
                ("duplicate_canonical_url", canonical_urls, canonical),
                ("duplicate_generated_identifier", ids, identity),
            ):
                if key in table:
                    issues[name] += 1
                    if len(examples[name]) < EXAMPLE_LIMIT:
                        examples[name].append({"first_line": table[key], "line": line, "url": value[:200]})
                else:
                    table[key] = line
            previous = identity_by_url.get(identity)
            if previous is not None and previous != value:
                issues["identifier_hash_collision"] += 1
                if len(examples["identifier_hash_collision"]) < EXAMPLE_LIMIT:
                    examples["identifier_hash_collision"].append({"first_url": previous[:200], "line": line})
            identity_by_url[identity] = value
            titles_by_url[canonical].add(title)
    for canonical, titles in titles_by_url.items():
        if len(titles) > 1:
            issues["conflicting_titles_same_url"] += 1
            if len(examples["conflicting_titles_same_url"]) < EXAMPLE_LIMIT:
                examples["conflicting_titles_same_url"].append({"url": canonical[:200], "titles": sorted(titles)[:4]})
    return {
        "schema": "mar-historical-corpus-integrity-audit-v1",
        "corpus": corpus,
        "source": relative,
        "sourceSha256": digest,
        "sourceRows": rows,
        "validOfficialUrlRows": rows - issues["invalid_or_nonofficial_url"] - issues["malformed_row"],
        "uniqueExactURLs": len(urls),
        "uniqueCanonicalURLs": len(canonical_urls),
        "uniqueGeneratedIdentifiers": len(ids),
        "issues": dict(sorted(issues.items())),
        "issueExamples": dict(examples),
        "checks": ["row schema", "source institution", "title", "official HTTPS syntax",
                   "exact URL uniqueness", "canonical URL uniqueness", "generated ID uniqueness",
                   "identifier hash collision", "conflicting titles"],
        "notChecked": ["live HTTP reachability", "redirect chains", "robots", "rights or licences",
                       "source availability", "scientific admission", "playback"],
        "publicationAllowed": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="optional report outside public site and historical data")
    args = parser.parse_args()
    results = [audit(corpus) for corpus in ("eye", "czech")]
    report = {"schema": "mar-integrity-audit-report-v1",
              "publicationAllowed": False, "corpora": results}
    data = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        target = args.output.resolve()
        for protected in (ROOT / "site", ROOT / "data"):
            protected = protected.resolve()
            if target == protected or protected in target.parents:
                parser.error("audit reports must not be written into site/ or data/")
        if target.exists():
            parser.error("existing audit report cannot be overwritten")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data, encoding="utf-8")
    print(data)


if __name__ == "__main__":
    main()
