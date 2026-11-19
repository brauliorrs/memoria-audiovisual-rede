#!/usr/bin/env python3
"""Architecture B, phase B1: deterministic aggregate-only MAR report projection.

Rebuild the Next.js analytics-N.json dataset from versioned Python scientific
report outputs. This is deliberately NOT an ingestion or publication workflow.
No internet, Neon, collection, item-level data or direct site writes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CHUNK_SIZE = 11
ANALYTICS_NAME = re.compile(r"analytics-([0-9]+)\.json\Z")


class ProjectionError(ValueError):
    """A scientific report or the reviewed site baseline is inconsistent."""


def _nonnegative(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ProjectionError(f"Invalid nonnegative count: {field}")
    return value


def _counts(value: Any, field: str) -> dict[str, int]:
    if not isinstance(value, dict):
        raise ProjectionError(f"Invalid aggregate map: {field}")
    result: dict[str, int] = {}
    for key, amount in value.items():
        if not isinstance(key, str) or not key:
            raise ProjectionError(f"Invalid aggregate key: {field}")
        result[key] = _nonnegative(amount, f"{field}.{key}")
    return result


def _load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise ProjectionError(f"Unreadable JSON: {path.name}: {exc}") from exc


def project_report(path: Path, root: Path) -> dict[str, Any]:
    raw = _load(path)
    if not isinstance(raw, dict):
        raise ProjectionError(f"Invalid report structure: {path.name}")
    code = path.name.removesuffix("_relatorio.json")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", code):
        raise ProjectionError(f"Invalid corpus code: {code}")
    return {
        "code": code,
        "source": path.relative_to(root).as_posix(),
        "totalInstitutions": _nonnegative(raw.get("total_institutions"), f"{code}.total_institutions"),
        "institutionsWithVideo": _nonnegative(raw.get("with_video_count"), f"{code}.with_video_count"),
        "withEmbeds": _nonnegative(raw.get("with_embeds_count"), f"{code}.with_embeds_count"),
        "siteStatus": _counts(raw.get("status_summary"), f"{code}.status_summary"),
        "integrity": _counts(raw.get("integrity_summary"), f"{code}.integrity_summary"),
        "platforms": _counts(raw.get("platform_summary"), f"{code}.platform_summary"),
        "continents": _counts(raw.get("continent_summary"), f"{code}.continent_summary"),
        "videoContinents": _counts(raw.get("video_continent_summary"), f"{code}.video_continent_summary"),
    }


def reviewed_analytics(root: Path) -> tuple[list[Path], list[dict[str, Any]]]:
    directory = root / "site" / "data"
    indexed: list[tuple[int, Path]] = []
    for path in directory.glob("analytics-*.json"):
        found = ANALYTICS_NAME.fullmatch(path.name)
        if not found:
            raise ProjectionError(f"Unexpected analytics file: {path.name}")
        indexed.append((int(found.group(1)), path))
    indexed.sort()
    if not indexed or [index for index, _ in indexed] != list(range(len(indexed))):
        raise ProjectionError("Missing or discontinuous approved analytics chunks")
    paths = [path for _, path in indexed]
    rows: list[dict[str, Any]] = []
    for path in paths:
        part = _load(path)
        if not isinstance(part, list) or not part or len(part) > CHUNK_SIZE:
            raise ProjectionError(f"Invalid reviewed analytics chunk: {path.name}")
        if any(not isinstance(item, dict) or not isinstance(item.get("code"), str) for item in part):
            raise ProjectionError(f"Invalid reviewed analytics entry: {path.name}")
        rows.extend(part)
    codes = [item["code"] for item in rows]
    if len(codes) != len(set(codes)) or codes != sorted(codes):
        raise ProjectionError("Reviewed aggregate corpus codes must be unique and sorted")
    return paths, rows


def compile_projection(root: Path) -> tuple[list[Path], list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    root = root.resolve()
    paths, reviewed = reviewed_analytics(root)
    reports = sorted((root / "data" / "output").glob("*_relatorio.json"))
    if not reports:
        raise ProjectionError("No versioned source reports")
    generated = [project_report(path, root) for path in reports]
    names = [record["code"] for record in generated]
    if len(names) != len(set(names)):
        raise ProjectionError("Duplicated scientific report code")
    approved = [record["code"] for record in reviewed]
    if names != approved:
        missing = sorted(set(approved) - set(names))
        unreviewed = sorted(set(names) - set(approved))
        raise ProjectionError(
            f"Aggregate source roster changed; explicit review needed "
            f"(missing={missing}, new_unreviewed={unreviewed})"
        )
    chunks = {
        f"analytics-{index}.json": generated[index * CHUNK_SIZE:(index + 1) * CHUNK_SIZE]
        for index in range((len(generated) + CHUNK_SIZE - 1) // CHUNK_SIZE)
    }
    expected_paths = [path.name for path in paths]
    if list(chunks) != expected_paths:
        raise ProjectionError("Aggregate chunk layout changed; explicit review required")
    return reports, reviewed, chunks


def verify(root: Path) -> list[str]:
    try:
        paths, reviewed = reviewed_analytics(root.resolve())
        _, _, generated = compile_projection(root)
        actual = [item for path in paths for item in _load(path)]
        reference = [item for chunk in generated.values() for item in chunk]
        errors = []
        for old, new in zip(actual, reference, strict=True):
            if old != new:
                errors.append(f"Scientific aggregate drift: {new['code']}")
        if len(actual) != len(reference):
            errors.append("Aggregate report counts disagree")
        return errors
    except (ProjectionError, OSError) as exc:
        return [str(exc)]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage(root: Path, target: Path) -> dict[str, Any]:
    """Write a *review-only* bundle outside the repo; never touch live site/data."""
    root = root.resolve()
    target = target.resolve()
    if target == root or root in target.parents:
        raise ProjectionError("Staging destination must be outside the MAR repository")
    if target.exists():
        raise ProjectionError("Staging destination already exists; refusing overwrite")
    if not target.parent.is_dir():
        raise ProjectionError("Staging destination parent does not exist")
    reports, _, chunks = compile_projection(root)
    temp = Path(tempfile.mkdtemp(prefix=".mar-analytics-stage-", dir=target.parent))
    try:
        outputs: dict[str, str] = {}
        for filename, records in chunks.items():
            path = temp / filename
            path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            outputs[filename] = _sha256(path)
        manifest = {
            "schema": "mar-analytics-stage-v1",
            "status": "REVIEW_ONLY_NOT_PUBLICATION_AUTHORIZATION",
            "publicationAuthorized": False,
            "scope": "aggregate_reports_only",
            "corpusCount": sum(map(len, chunks.values())),
            "sourceSha256": {path.relative_to(root).as_posix(): _sha256(path) for path in reports},
            "outputSha256": outputs,
            "site": "mar-public-site",
            "note": "No item-level fiches, media, permission changes, deployment, or automated admission.",
        }
        (temp / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        os.replace(temp, target)
        return manifest
    except Exception:
        shutil.rmtree(temp, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="Compare all aggregates to scientific sources (default)")
    action.add_argument("--stage-dir", type=Path, help="Write review-only bundle OUTSIDE repository")
    args = parser.parse_args()
    try:
        if args.stage_dir is not None:
            result = stage(ROOT, args.stage_dir)
            print(f"Staged {result['corpusCount']} aggregate reports; publication NOT authorized")
        else:
            problems = verify(ROOT)
            if problems:
                for problem in problems:
                    print(f"ERROR: {problem}", file=sys.stderr)
                return 1
            print("MAR analytics projection: source-to-site semantic parity verified (aggregate-only)")
    except (ProjectionError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
