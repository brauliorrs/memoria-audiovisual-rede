#!/usr/bin/env python3
"""Offline MAR B2 real-corpus replay: historical ARCHIPOP, never a new admission.

Rebuilds ALL 34 current site projections from the actual, frozen MAR sources
into an isolated review directory, cross-checks the archived 57 -> 58
ARCHIPOP observations against analytics, topic/country/platform totals,
institution metadata, historical access decisions and title-cloud provenance.

The historical observations are real; this does NOT reconstruct an older 57-
item full site bundle, nor grant permission to publish item-level records.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_mar_site_bundle_b2 import BundleError, ROOT, sha256_file
from scripts.build_mar_site_projections_b2 import stage

CODE = "archipop"
FIRST_SNAPSHOT = "2026-05-29T16:48:33Z"
LAST_SNAPSHOT = "2026-05-29T16:52:58Z"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _merged_chunks(folder: Path, prefix: str) -> dict:
    merged: dict = {}
    for path in sorted(folder.glob(prefix + "-*.json")):
        data = _json(path)
        if isinstance(data, list):
            for row in data:
                if row["code"] in merged:
                    raise BundleError(f"Duplicate report in {prefix}: {row['code']}")
                merged[row["code"]] = row
        elif isinstance(data, dict):
            if set(merged) & set(data):
                raise BundleError(f"Duplicate code in {prefix}")
            merged.update(data)
        else:
            raise BundleError(f"Invalid static projection family: {prefix}")
    return merged


def review_archipop(root: Path, target: Path) -> dict:
    """Review-only stage of the ACTUAL frozen baseline, no original writes."""
    root, target = root.resolve(), target.resolve()
    if root == target or root in target.parents:
        raise BundleError("Isolated staging cannot write into the repository")
    if target.exists():
        raise BundleError("Immutable staging directory already exists")
    before = {
        rel: sha256_file(root / rel)
        for rel in (
            "site/data/kavi-public.json",
            "site/data/public-access-observatory.json",
            "site/data/documented-cases.json",
            "site/data/title-wordcloud.json",
            "data/output/archipop_relatorio.json",
            "data/output/archipop_linha_do_tempo_corpus.csv",
        )
    }

    info = stage(root, target)
    staged = target / "site/data"
    if info.get("status") != "REVIEW_ONLY_NOT_PUBLICATION_AUTHORIZATION":
        raise BundleError("Scientific review stage was unexpectedly approved")
    if info.get("publicationAuthorized") is not False or info.get("publicAccessAuthorized") is not False:
        raise BundleError("A scientific rehearsal cannot grant publication")
    if info.get("corpusCount") != 62 or len(info.get("outputSha256", {})) != 34:
        raise BundleError("Scientific baseline or projection roster unexpectedly changed")
    if _json(target / "manifest.json") != info:
        raise BundleError("Staged scientific manifest differs from the produced epoch")
    for rel, checksum in info["outputSha256"].items():
        if sha256_file(target / rel) != checksum:
            raise BundleError(f"Unverified output checksum: {rel}")
    for rel, checksum in before.items():
        if sha256_file(root / rel) != checksum:
            raise BundleError(f"Source was modified during review: {rel}")

    reports = _merged_chunks(staged, "analytics")
    slices = _merged_chunks(staged, "research-slices")
    groups = _merged_chunks(staged, "institution-profiles")
    inventory = _json(staged / "public-access-observatory.json")
    cloud = _json(staged / "title-wordcloud.json")
    kavi = _json(staged / "kavi-public.json")
    cases = _json(staged / "documented-cases.json")
    if not set(reports) == set(slices) == set(groups) or CODE not in reports:
        raise BundleError("Corpus missing from static analytic/research/institution rosters")

    report = reports[CODE]
    dimensions = slices[CODE]
    institution_group = groups[CODE]
    case = next((x for x in inventory["corpora"] if x["code"] == CODE), None)
    provenance = next((x for x in cloud["sourceProvenance"] if x["code"] == CODE), None)
    if case is None or provenance is None:
        raise BundleError("ARCHIPOP is missing in access/cloud provenance")

    observations = dimensions["linha_do_tempo_corpus"]["rows"]
    values = [(r["snapshot_generated_at"], int(r["video_links_total"]),
               int(r["videos_in_curatorial_catalog"])) for r in observations]
    if values != [(FIRST_SNAPSHOT, 57, 57), (LAST_SNAPSHOT, 58, 58)]:
        raise BundleError("Actual versioned ARCHIPOP 57->58 trajectory is not reproducible")

    country_rows = dimensions["tema_pais"]["rows"]
    platform_rows = dimensions["tema_plataforma"]["rows"]
    country_count = sum(int(r["total"]) for r in country_rows)
    platform_count = sum(int(r["total"]) for r in platform_rows)
    latest = values[-1][1]
    if not (country_count == platform_count == latest == 58):
        raise BundleError("Latest country/platform totals do not reconcile with real trajectory")
    if {r["pais"] for r in country_rows} != {"France"}:
        raise BundleError("Territorial map input differs from ARCHIPOP scientific CSV")
    if {r["plataforma"] for r in platform_rows} != {"Archipop"}:
        raise BundleError("Platform comparison input differs from report")
    if report["platforms"].get("Archipop") != latest:
        raise BundleError("B1 report not updated to match the latest real observation")
    if report["totalInstitutions"] != 1 or report["institutionsWithVideo"] != 1:
        raise BundleError("Institution counts contradict the source scientific report")
    if len(institution_group["rows"]) != 1 or institution_group["rows"][0]["country"] != "France":
        raise BundleError("Institution registry disagrees with scientific territory")
    if case["historicalTotal"] != latest or case["historicalPublicSurfaceRecords"] != latest:
        raise BundleError("Historical access counts differ from the scientific observation")
    if case.get("recordDisplay") != "not_authorized_for_new_site":
        raise BundleError("Historical access index was promoted to individual publication")
    if provenance["rows"] != 58 or cloud["rawTitlesPublished"] is not False:
        raise BundleError("Title-cloud corpus provenance differs or leaks raw titles")
    if cloud["individualRecordsPublished"] is not False or cases["publicationAuthorized"] is not False:
        raise BundleError("Human documentary rights were promoted without authorization")
    if kavi.get("total") != 200 or kavi.get("mediaPlaybackVerified") is not False:
        raise BundleError("Individual approved KAVI manifest was changed")
    # Curated materials are carried forward semantically without being
    # recalculated from catalogue item-level material.
    for rel in ("kavi-public.json", "public-access-observatory.json", "documented-cases.json"):
        if _json(staged / rel) != _json(root / "site/data" / rel):
            raise BundleError(f"Human curated data was rewritten: {rel}")

    return {
        "status": "REPLAY_APPROVED_FOR_ENGINEERING_REVIEW_ONLY",
        "corpus": CODE,
        "historicalObservations": 2,
        "historicalVideoCounts": [57, 58],
        "currentVideoCount": latest,
        "institutions": 1,
        "country": "France",
        "countryAggregates": country_count,
        "platformAggregates": platform_count,
        "historicalAccessRecords": case["historicalTotal"],
        "wordcloudSourceRows": provenance["rows"],
        "stagedCorpora": info["corpusCount"],
        "stagedStaticFiles": len(info["outputSha256"]),
        "epochSha256": info["epochSha256"],
        "publicationAuthorized": False,
        "sourceFilesUnchanged": True,
        "mediaDownloaded": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage-dir", type=Path, help="Optional NEW directory outside the repository")
    args = parser.parse_args()
    try:
        if args.stage_dir is not None:
            outcome = review_archipop(ROOT, args.stage_dir)
        else:
            with tempfile.TemporaryDirectory(prefix="mar-archipop-replay-") as temp:
                outcome = review_archipop(ROOT, Path(temp) / "review")
    except (OSError, ValueError, TypeError, KeyError, BundleError) as exc:
        print(f"MAR real ARCHIPOP replay HOLD: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(outcome, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
