#!/usr/bin/env python3
"""MAR Architecture B2: offline, fail-closed, immutable static-bundle staging.

This stage does NOT grant scientific admission or public publication. Source
integrity and all 33 static site projections remain tied to the frozen
reviewed baseline until the complete regenerators and release gate exist.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_mar_site_analytics import verify as verify_analytics
from scripts.check_mar_scientific_snapshot_lock import verify as verify_lock

ROOT = Path(__file__).resolve().parents[1]
LOCK_REL = Path("site/data/scientific-snapshot-lock.json")
WORDCLOUD = "site/data/title-wordcloud.json"
STAGE_SCHEMA = "mar-scientific-bundle-stage-v1"


class BundleError(ValueError):
    pass


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise BundleError(f"Unreadable JSON ({path.name}): {exc}") from exc


def sha256_file(path: Path) -> str:
    hash_ = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hash_.update(block)
    return hash_.hexdigest()


def checked_path(root: Path, rel: str, prefix: str) -> Path:
    if not isinstance(rel, str) or not rel.startswith(prefix) or ".." in Path(rel).parts:
        raise BundleError(f"Unsafe or unauthorized path: {rel!r}")
    path = (root / rel).resolve()
    if not path.is_relative_to((root / prefix).resolve()) or not path.is_file():
        raise BundleError(f"Missing or unsafe bundle input: {rel!r}")
    return path


def load_reviewed_bundle(root: Path):
    root = root.resolve()
    lock = read_json(root / LOCK_REL)
    failures = verify_lock(root, lock)
    if failures:
        raise BundleError(f"Frozen scientific source lock HOLD: {failures[:3]}")
    if verify_analytics(root):
        raise BundleError(f"B1 analytics parity HOLD: {verify_analytics(root)[:3]}")

    sources = dict(lock["inputs"])
    outputs = dict(lock["outputs"])
    if len(sources) < 1 or len(outputs) != 33:
        raise BundleError("Scientific source or 33-projection roster changed; revision required")
    if set(sources) & set(outputs):
        raise BundleError("Source and presentation namespaces overlap")
    for rel in sources:
        checked_path(root, rel, "data/output/")
    for rel in outputs:
        checked_path(root, rel, "site/data/")
    outputs[WORDCLOUD] = None

    analytics = []
    for rel in sorted(outputs):
        if re.fullmatch(r"site/data/analytics-\d+\.json", rel):
            data = read_json(root / rel)
            if not isinstance(data, list):
                raise BundleError(f"Invalid analytics chunk {rel}")
            analytics.extend(data)
    codes = {row["code"] for row in analytics}
    if len(codes) != len(analytics) or not codes:
        raise BundleError("Missing or duplicate analytics corpus")

    slices = {}
    profiles = {}
    for rel in sorted(outputs):
        if re.fullmatch(r"site/data/research-slices-\d+\.json", rel):
            chunk = read_json(root / rel)
            if not isinstance(chunk, dict) or set(slices) & set(chunk):
                raise BundleError("Duplicate or malformed research slice")
            slices.update(chunk)
        if re.fullmatch(r"site/data/institution-profiles-\d+\.json", rel):
            chunk = read_json(root / rel)
            if not isinstance(chunk, dict) or set(profiles) & set(chunk):
                raise BundleError("Duplicate or malformed institutional profile")
            profiles.update(chunk)
    if set(slices) != codes or set(profiles) != codes:
        raise BundleError("Scientific dashboard coverage differs between reports/slices/profiles")

    # Scientific snapshots use one row per CSV observation. They are not
    # evidence of permission to republish individual audiovisual records.
    dimensions = ("tema_pais", "tema_plataforma", "linha_do_tempo_corpus")
    for code, sections in slices.items():
        for dim in dimensions:
            info = sections.get(dim)
            if not isinstance(info, dict) or info.get("source") != f"data/output/{code}_{dim}.csv":
                raise BundleError(f"Unmatched scientific dimension source {code}:{dim}")
            source_path = checked_path(root, info["source"], "data/output/")
            with source_path.open(encoding="utf-8-sig", newline="") as handle:
                source_rows = list(csv.DictReader(handle))
            site_rows = info.get("rows")
            if not isinstance(site_rows, list) or len(source_rows) != len(site_rows):
                raise BundleError(f"Scientific dimension row count drift {code}:{dim}")
            for index, (row, site_row) in enumerate(zip(source_rows, site_rows)):
                if not isinstance(site_row, dict) or any(row.get(k) != v for k, v in site_row.items()):
                    raise BundleError(f"Scientific dimension value drift {code}:{dim}:{index}")

    for code, group in profiles.items():
        if not isinstance(group, dict) or group.get("source") != f"data/output/{code}_instituicoes.csv":
            raise BundleError(f"Institutional provenance mismatch: {code}")
        if group.get("sampled") is not False:
            raise BundleError(f"Unreviewed institutional sample: {code}")
        with checked_path(root, group["source"], "data/output/").open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        projected = group.get("rows")
        if not isinstance(projected, list) or len(rows) != len(projected):
            raise BundleError(f"Institutional row count drift: {code}")
        if len({x.get("id") for x in projected}) != len(projected):
            raise BundleError(f"Institutional ID duplication: {code}")
        if any(x.get("id") != f"{code}:{i}" for i, x in enumerate(projected, start=1)):
            raise BundleError(f"Institutional identity drift: {code}")

    research = read_json(root / "site/data/research-0.json")
    if not isinstance(research, list) or any(row.get("code") not in codes for row in research):
        raise BundleError("Unreferenced research pilot projection")

    inventory = read_json(root / "site/data/public-access-observatory.json")
    approved = read_json(root / "site/data/kavi-public.json")
    cases = read_json(root / "site/data/documented-cases.json")
    cloud = read_json(root / WORDCLOUD)
    if inventory.get("publicationOfIndividualRecordsNotAuthorizedByThisFile") is not True:
        raise BundleError("Historical access index illegally authorizes individual items")
    rows = inventory.get("corpora", [])
    if not isinstance(rows, list) or len({r.get("code") for r in rows}) != len(rows):
        raise BundleError("Access inventory lacks unique corpus identifiers")
    if any(r.get("recordDisplay") != "not_authorized_for_new_site" for r in rows):
        raise BundleError("HOLD was promoted in the historical access index")
    if inventory.get("kaviSiteApprovedRecords") != 200 or approved.get("total") != 200:
        raise BundleError("Individual KAVI publication count changed without authority")
    if approved.get("approvedMetadataPublication") is not True or approved.get("mediaPlaybackVerified") is not False:
        raise BundleError("KAVI metadata-only gate changed")
    if not isinstance(approved.get("records"), list) or len(approved["records"]) != 200:
        raise BundleError("Incomplete individually approved KAVI list")
    if cases.get("publicationAuthorized") is not False:
        raise BundleError("Documentary cases were promoted to individual publication")
    if cloud.get("rawTitlesPublished") is not False or cloud.get("individualRecordsPublished") is not False:
        raise BundleError("Title-cloud record publication boundary violated")

    return sources, outputs, len(codes)


def manifest(root: Path):
    root = root.resolve()
    sources, outputs, corpora = load_reviewed_bundle(root)
    in_hashes = {rel: sha256_file(checked_path(root, rel, "data/output/")) for rel in sorted(sources)}
    out_hashes = {rel: sha256_file(checked_path(root, rel, "site/data/")) for rel in sorted(outputs)}
    content = {"sources": in_hashes, "outputs": out_hashes}
    canonical = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    epoch = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    lock = read_json(root / LOCK_REL)
    return {
        "schema": STAGE_SCHEMA,
        "epochSha256": epoch,
        "baselineCommit": lock["baselineMainCommit"],
        "status": "REVIEW_ONLY_NOT_PUBLICATION_AUTHORIZATION",
        "publicationAuthorized": False,
        "publicAccessAuthorized": False,
        "corpusReportCount": corpora,
        "individuallyApprovedKaviMetadataRecords": 200,
        "scientificSourceSha256": in_hashes,
        "staticProjectionSha256": out_hashes,
        "releaseCondition": "human scientific review + complete generators + atomic deployment gate",
    }


def atomic_stage_files(root: Path, target: Path, relative_paths: list[str], data: dict):
    """Make all-or-nothing review output. Safe also for synthetic fixtures."""
    root, target = root.resolve(), target.resolve()
    if target == root or root in target.parents:
        raise BundleError("Staging cannot write inside the MAR repository")
    if target.exists():
        raise BundleError("Staging destination exists; refusing to overwrite")
    if not target.parent.is_dir():
        raise BundleError("Staging parent does not exist")
    temp = Path(tempfile.mkdtemp(prefix=".mar-b2-stage-", dir=target.parent))
    try:
        for rel in relative_paths:
            source = checked_path(root, rel, "site/data/")
            dest = temp / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
            if sha256_file(dest) != data["staticProjectionSha256"][rel]:
                raise BundleError(f"Staged output hash drift: {rel}")
        (temp / "manifest.json").write_text(
            json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temp, target)
    except Exception:
        shutil.rmtree(temp, ignore_errors=True)
        raise


def stage(root: Path, target: Path):
    data = manifest(root)
    atomic_stage_files(root, target, sorted(data["staticProjectionSha256"]), data)
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="Fail closed if research baseline is inconsistent")
    action.add_argument("--stage-dir", type=Path, help="Write full review-only bundle outside the repository")
    args = parser.parse_args()
    try:
        info = stage(ROOT, args.stage_dir) if args.stage_dir is not None else manifest(ROOT)
    except (BundleError, OSError, KeyError, TypeError) as exc:
        print(f"MAR B2 bundle HOLD: {exc}", file=sys.stderr)
        return 1
    print(
        f"MAR B2 {info['status']}: {info['corpusReportCount']} corpora, "
        f"{len(info['staticProjectionSha256'])} static projections, epoch={info['epochSha256']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
