#!/usr/bin/env python3
"""MAR multicorpus documentary staging: no publication, network or media downloads.

The source CSV is read-only. Output is a quarantined *candidate* projection;
nothing produced here is automatically imported into the Next.js public index.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CORPORA = {
    "eye": {
        "path": "data/output/eye_catalogo_videos_analitico.csv",
        "url_hosts": {"filmdatabase.eyefilm.nl"},
        "institution": "Eye Filmmuseum",
        "country": "Países Baixos",
    },
    "czech": {
        "path": "data/output/czech_tv_catalogo_videos_analitico.csv",
        "url_hosts": {"www.ceskatelevize.cz"},
        "institution": "Czech Television",
        "country": "Tchéquia",
    },
}
FIELDS = ("video_link", "video_title")
MAX_INPUT_BYTES = 20_000_000


def normalize(row: dict[str, str], corpus: str) -> dict:
    cfg = CORPORA[corpus]
    url = (row.get("video_link") or "").strip()
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in cfg["url_hosts"] or parsed.username or parsed.password or parsed.port or not parsed.path.strip("/"):
        raise ValueError("origin URL not allowed")
    if parsed.fragment:
        raise ValueError("origin URL must not contain a fragment")
    title = (row.get("video_title_display") or row.get("video_title") or "").strip()
    if not title:
        raise ValueError("title missing")
    if row.get("institution", "").strip() != cfg["institution"]:
        raise ValueError("institution mismatch")
    identity = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
    date = (row.get("video_date_display") or row.get("video_published_at") or "").strip()
    return {
        "id": corpus + "." + identity,
        "corpus": corpus,
        "title": title,
        "year": None,  # Production year is not independently mapped in this CSV.
        "sourcePublishedAt": date or None,
        "genres": (row.get("video_theme") or "").strip(),
        "subjects": (row.get("video_subject") or "").strip(),
        "languages": "",
        "sourceUrl": url,
        "source": (row.get("platform") or cfg["institution"]).strip(),
        "institution": cfg["institution"],
        "country": cfg["country"],
        "status": "Candidato técnico · não homologado para publicação",
        "mediaAccess": "Não verificado pelo MAR",
        "publicationApproved": False,
        "mediaPlaybackVerified": False,
        "mediaRightsVerified": False,
    }


def stage(corpus: str, *, limit: int | None = None, root: Path = ROOT) -> dict:
    if corpus not in CORPORA:
        raise ValueError("unsupported corpus")
    path = root / CORPORA[corpus]["path"]
    if not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("source missing or oversized")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or any(k not in reader.fieldnames for k in FIELDS):
            raise ValueError("source CSV schema mismatch")
        rows = list(reader)
    if not rows:
        raise ValueError("source CSV empty")
    if limit is not None and limit < 1:
        raise ValueError("limit must be positive")
    selected = rows[:limit] if limit is not None else rows
    seen_ids, seen_urls, records = set(), set(), []
    for number, row in enumerate(selected, start=2):
        try:
            candidate = normalize(row, corpus)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"{corpus} CSV line {number}: {exc}") from exc
        if candidate["id"] in seen_ids or candidate["sourceUrl"] in seen_urls:
            raise ValueError(f"{corpus} duplicate at CSV line {number}")
        seen_ids.add(candidate["id"])
        seen_urls.add(candidate["sourceUrl"])
        records.append(candidate)
    return {
        "schema": "mar-multicorpus-staging-v1",
        "corpus": corpus,
        "status": "technical_candidate_not_publication_approved",
        "sourcePath": CORPORA[corpus]["path"],
        "sourceSha256": digest,
        "sourceRows": len(rows),
        "stagedRows": len(records),
        "coverage": "sample" if len(records) != len(rows) else "source_csv_only_not_institutional_total",
        "approvedMetadataPublication": False,
        "individualReview": False,
        "mediaPlaybackVerified": False,
        "mediaRightsVerified": False,
        "publicationBlocked": True,
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", required=True, choices=CORPORA)
    parser.add_argument("--limit", type=int, default=2, help="Pilot rows; use 0 for whole source CSV")
    parser.add_argument("--output", type=Path, help="Explicit quarantine output path outside site/data")
    args = parser.parse_args()
    payload = stage(args.corpus, limit=None if args.limit == 0 else args.limit)
    if args.output:
        destination = args.output.resolve()
        protected = (ROOT / "site").resolve()
        if destination == protected or protected in destination.parents:
            parser.error("writing into site/ is forbidden for staged corpora")
        if destination.exists():
            parser.error("output already exists; do not overwrite evidence")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "records"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
