#!/usr/bin/env python3
"""MAR B2: rebuild every source-derived static research projection OFFLINE.

Scientific aggregation != scientific admission != item-publication permission.
Curated access, documentary cases and the 200 individually reviewed KAVI
metadata entries are *reviewed inputs*, never silently reconstructed from CSVs.
Output is a review candidate outside this repository. No deployment or writes
to site/data are permitted.
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
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.build_mar_site_analytics import ProjectionError, project_report
from scripts.build_mar_site_bundle_b2 import (
    BundleError, ROOT, checked_path, load_reviewed_bundle, read_json, sha256_file,
)
from scripts.build_mar_site_bundle_b2 import project_research_slices
from scripts import build_mar_title_wordcloud as wordcloud

PROJECTOR_SCHEMA = "mar-static-scientific-projection-review-v1"
CURATED = (
    "site/data/kavi-public.json",
    "site/data/public-access-observatory.json",
    "site/data/documented-cases.json",
)
STATIC_GEOMETRY = "site/data/world-110m-geometry.json"


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or any(not name for name in reader.fieldnames):
            raise BundleError(f"Missing institutional CSV header: {path.name}")
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise BundleError(f"Duplicated institutional CSV column: {path.name}")
        result = list(reader)
    if any(None in row for row in result):
        raise BundleError(f"Broken institutional CSV column count: {path.name}")
    return result


def _baseline_group(root: Path) -> dict[str, dict]:
    groups: dict[str, dict] = {}
    for path in sorted((root / "site/data").glob("institution-profiles-*.json")):
        chunk = read_json(path)
        if not isinstance(chunk, dict) or set(groups) & set(chunk):
            raise BundleError(f"Unreviewed institutional chunk: {path.name}")
        groups.update(chunk)
    return groups


def _source_or_reviewed(raw: str | None, reviewed: str | None, field: str, code: str, i: int) -> str:
    """Keep an old, reviewed editorial fallback only where source is empty.

    A fresh external identifier/URL may need a rights review; never replace an
    already reviewed value by silently accepting an unexplained difference.
    """
    raw = (raw or "").strip()
    previous = reviewed if isinstance(reviewed, str) else ""
    if raw and previous and raw != previous:
        raise BundleError(f"Institutional curated/source drift {code}:{i}.{field}")
    # Historical 'Nao classificado' source labels were deliberately hidden
    # in reviewed institutional pages. Do not silently expose them as places.
    if raw in ("Nao classificado", "Não classificado") and previous == "":
        return previous
    return raw or previous


def project_institutions(root: Path, code: str, approved: dict | None) -> dict:
    rel = f"data/output/{code}_instituicoes.csv"
    raw = _csv_rows(checked_path(root, rel, "data/output/"))
    if approved is None:
        raise BundleError(f"Human-reviewed institutional presentation absent: {code}")
    if approved.get("source") != rel or approved.get("sampled") is not False:
        raise BundleError(f"Institution provenance/sampling was changed: {code}")
    approved_rows = approved.get("rows")
    if not isinstance(approved_rows, list) or len(raw) != len(approved_rows):
        raise BundleError(f"Institution membership changed; human review required: {code}")
    rows = []
    for index, (source, reviewed) in enumerate(zip(raw, approved_rows), 1):
        if not isinstance(reviewed, dict) or reviewed.get("id") != f"{code}:{index}":
            raise BundleError(f"Institution row identity changed: {code}:{index}")
        # Editorial fields for APE and other exceptional sources are allowed
        # only as explicitly reviewed fallbacks, never synthesized.
        row = {
            "id": f"{code}:{index}",
            "name": _source_or_reviewed(source.get("institution"), reviewed.get("name"), "name", code, index),
            "country": _source_or_reviewed(source.get("country"), reviewed.get("country"), "country", code, index),
            "continent": _source_or_reviewed(source.get("continent"), reviewed.get("continent"), "continent", code, index),
            "type": _source_or_reviewed(source.get("archive_type"), reviewed.get("type"), "type", code, index),
            "repositoryCode": _source_or_reviewed(source.get("repository_code"), reviewed.get("repositoryCode"), "repositoryCode", code, index),
            "originUrl": _source_or_reviewed(source.get("external_url"), reviewed.get("originUrl"), "originUrl", code, index),
        }
        # Some historical APE source records contain genuinely empty fields.
        # Preserve the reviewed blank instead of inventing an institution or
        # country. Admission/new publication must separately resolve these.
        if not row["name"] and (source.get("institution") or reviewed.get("name")):
            raise BundleError(f"Institution name unexpectedly missing: {code}:{index}")
        rows.append(row)
    result = {key: approved[key] for key in ("source", "sampled", "licencePolicy", "attribution") if key in approved}
    result["rows"] = rows
    return result


def _int(row: dict, key: str) -> int:
    try:
        n = int(row.get(key, ""))
        if n < 0 or str(n) != str(row.get(key)):
            raise ValueError()
    except (ValueError, TypeError) as exc:
        raise BundleError(f"Invalid nonnegative timeline count: {key}") from exc
    return n


def project_research_pilot(code: str, slice_: dict) -> dict:
    countries = [{
        "theme": row["tema"], "country": row["pais"], "value": _int(row, "total")
    } for row in slice_["tema_pais"]["rows"]]
    platforms = [{
        "theme": row["tema"], "platform": row["plataforma"], "value": _int(row, "total")
    } for row in slice_["tema_plataforma"]["rows"]]
    # The original Streamlit-derived pilot orders topics by platform rows.
    # Deriving order from country CSVs changes the historical chart order.
    themes: dict[str, int] = {}
    for row in platforms:
        themes[row["theme"]] = themes.get(row["theme"], 0) + row["value"]
    if not themes:
        for row in countries:
            themes[row["theme"]] = themes.get(row["theme"], 0) + row["value"]
    timeline = [{
        "date": r["snapshot_generated_at"],
        "observationKey": r["observation_key"],
        "videoLinks": _int(r, "video_links_total"),
        "institutions": _int(r, "institutions"),
        "curatorialCount": _int(r, "videos_in_curatorial_catalog"),
    } for r in slice_["linha_do_tempo_corpus"]["rows"]]
    # Historical order is significant in the original presentation.
    return {
        "code": code, "themes": [{"theme": k, "value": v} for k, v in themes.items()],
        "countries": countries, "platforms": platforms, "timeline": timeline,
    }


def generated_documents(root: Path) -> tuple[dict[str, object], list[str]]:
    """Compute the candidate on CURRENT real scientific sources; no writes."""
    root = root.resolve()
    _, _, expected_count = load_reviewed_bundle(root)
    originals = _baseline_group(root)
    report_sources = sorted((root / "data/output").glob("*_relatorio.json"))
    codes = [p.name.removesuffix("_relatorio.json") for p in report_sources]
    if len(codes) != expected_count or len(codes) != len(set(codes)):
        raise BundleError("Scientific corpus membership changed: review new admissions first")
    if set(codes) != set(originals):
        raise BundleError("Institutional roster does not match scientific sources")
    payload: dict[str, object] = {}
    analytics: list[dict] = []
    slices: dict[str, dict] = {}
    groups: dict[str, dict] = {}
    for path in report_sources:
        code = path.name.removesuffix("_relatorio.json")
        if not re.fullmatch(r"[a-z][a-z0-9_]*", code):
            raise BundleError(f"Invalid corpus code: {code}")
        analytics.append(project_report(path, root))
        slices[code] = project_research_slices(root, code)
        groups[code] = project_institutions(root, code, originals[code])
    for n in range(0, len(analytics), 11):
        payload[f"site/data/analytics-{n//11}.json"] = analytics[n:n+11]
    for n in range(0, len(codes), 4):
        keys = codes[n:n+4]
        payload[f"site/data/research-slices-{n//4}.json"] = {c: slices[c] for c in keys}
    for n in range(0, len(codes), 10):
        keys = codes[n:n+10]
        payload[f"site/data/institution-profiles-{n//10}.json"] = {c: groups[c] for c in keys}
    # The historical site uses a four-corpus pilot, distinct from the
    # broader 62-corpus dashboard. Preserve its reviewed membership for now.
    pilot = read_json(root / "site/data/research-0.json")
    if not isinstance(pilot, list) or len({p["code"] for p in pilot}) != len(pilot):
        raise BundleError("Duplicate or invalid research pilot")
    payload["site/data/research-0.json"] = [
        project_research_pilot(p["code"], slices[p["code"]]) for p in pilot
    ]

    # Human-curated publication decisions remain byte-preserved dependencies.
    for rel in CURATED:
        payload[rel] = read_json(root / rel)
    with patch.object(wordcloud, "ROOT", root):
        payload["site/data/title-wordcloud.json"] = wordcloud.build()

    expected = {
        f"site/data/{p.name}" for p in (root / "site/data").glob("*.json")
        if p.name not in ("scientific-snapshot-lock.json", "world-110m-geometry.json")
    }
    if set(payload) != expected:
        raise BundleError(
            f"Projection roster incomplete; missing={sorted(expected-set(payload))}, "
            f"unexpected={sorted(set(payload)-expected)}"
        )
    return payload, codes



def first_difference(expected, observed, location="root"):
    if type(expected) is not type(observed):
        return f"{location}: type {type(expected).__name__} vs {type(observed).__name__}"
    if isinstance(expected, dict):
        if set(expected) != set(observed):
            return f"{location}: keys expected-only={list(set(expected)-set(observed))[:4]} observed-only={list(set(observed)-set(expected))[:4]}"
        for key in expected:
            if expected[key] != observed[key]:
                return first_difference(expected[key], observed[key], f"{location}.{key}")
    if isinstance(expected, list):
        if len(expected) != len(observed):
            return f"{location}: list sizes {len(expected)} vs {len(observed)}"
        for i, (e, o) in enumerate(zip(expected, observed)):
            if e != o:
                return first_difference(e, o, f"{location}[{i}]")
    return f"{location}: generator={str(expected)[:70]!r}, historical={str(observed)[:70]!r}"


def semantic_parity(root: Path) -> list[str]:
    """Unlike file formatting checks, report exact scientific value drift."""
    generated, _ = generated_documents(root)
    issues = []
    for rel, expected in generated.items():
        observed = read_json(root / rel)
        if expected != observed:
            issues.append(f"Stale scientific JSON: {rel}: {first_difference(expected, observed)}")
    return issues


def _serialized(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def stage(root: Path, target: Path) -> dict:
    root, target = root.resolve(), target.resolve()
    if target == root or root in target.parents or target.exists() or not target.parent.is_dir():
        raise BundleError("Staging requires a new directory outside the repository")
    if semantic_parity(root):
        raise BundleError(f"Scientific projection drift HOLD: {semantic_parity(root)[:5]}")
    generated, codes = generated_documents(root)
    temp = Path(tempfile.mkdtemp(prefix=".mar-full-projection-", dir=target.parent))
    try:
        sources = sorted(p for p in (root / "data/output").iterdir()
                         if p.is_file() and p.name.endswith((
                             "_relatorio.json", "_instituicoes.csv", "_tema_pais.csv",
                             "_tema_plataforma.csv", "_linha_do_tempo_corpus.csv",
                             "_catalogo_videos_analitico.csv"
                         )))
        input_hashes = {p.relative_to(root).as_posix(): sha256_file(p) for p in sources}
        output_hashes = {}
        for rel, obj in generated.items():
            file = temp / rel
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(_serialized(obj))
            output_hashes[rel] = sha256_file(file)
        # All current reviewed materialized data are part of this one epoch;
        # source and output digests never authorize publication on their own.
        canonical = json.dumps({"inputs": input_hashes, "outputs": output_hashes},
                               ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        epoch = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        result = {
            "schema": PROJECTOR_SCHEMA,
            "status": "REVIEW_ONLY_NOT_PUBLICATION_AUTHORIZATION",
            "publicationAuthorized": False,
            "publicAccessAuthorized": False,
            "corpusCount": len(codes),
            "epochSha256": epoch,
            "inputSha256": input_hashes,
            "outputSha256": output_hashes,
            "curatedFrozen": list(CURATED),
            "staticGeometryExcluded": STATIC_GEOMETRY,
            "baselineCommit": read_json(root / "site/data/scientific-snapshot-lock.json")["baselineMainCommit"],
            "note": "This is a protected historical baseline review, NOT an independent scientific admission.",
        }
        (temp / "manifest.json").write_bytes(_serialized(result))
        os.replace(temp, target)
        return result
    except Exception:
        shutil.rmtree(temp, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true", help="Fail on any stale derived static projection (default)")
    modes.add_argument("--stage-dir", type=Path, help="Review-only, atomic output outside the repository")
    args = parser.parse_args()
    try:
        if args.stage_dir:
            report = stage(ROOT, args.stage_dir)
            print(f"MAR derived bundle staged for review only: {report['corpusCount']} corpora")
        else:
            errors = semantic_parity(ROOT)
            if errors:
                for issue in errors[:20]:
                    print(f"HOLD: {issue}", file=sys.stderr)
                return 1
            print("MAR B2 full source-derived projections: semantic parity OK; NOT publication authority")
    except (OSError, ValueError, BundleError, ProjectionError, KeyError, TypeError) as exc:
        print(f"HOLD: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
