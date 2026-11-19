#!/usr/bin/env python3
"""Fail-closed, offline consistency gate for the historical MAR site.

The frontend is a static, versioned research projection. Report summaries,
research CSV slices and institutional profiles must agree with their ORIGINAL
versioned sources. This tool does not admit corpora or approve item publication.

--write updates ONLY derived aggregate/profile JSON shards. Human-reviewed
access evidence and case narratives must be reconciled independently.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
REPORT_SUFFIX = "_relatorio.json"
SLICES = ("tema_pais", "tema_plataforma", "linha_do_tempo_corpus")
FIELDS = {
    "totalInstitutions": "total_institutions",
    "institutionsWithVideo": "with_video_count",
    "withEmbeds": "with_embeds_count",
    "siteStatus": "status_summary",
    "integrity": "integrity_summary",
    "platforms": "platform_summary",
    "continents": "continent_summary",
    "videoContinents": "video_continent_summary",
}
PROFILE_FIELDS = {
    "name": "institution",
    "country": "country",
    "continent": "continent",
    "type": "archive_type",
    "repositoryCode": "repository_code",
}


class SnapshotDrift(RuntimeError):
    pass


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise SnapshotDrift(f"invalid CSV headers: {path.name}")
        return list(reader)


def shards(site: Path, stem: str):
    files = sorted(
        (site / "data").glob(f"{stem}-*.json"),
        key=lambda path: int(path.stem.removeprefix(stem + "-")),
    )
    if not files:
        raise SnapshotDrift(f"missing {stem} projection shards")
    output = []
    for path in files:
        output.append((path, read_json(path)))
    return output


def flatten(parts, kind: str):
    result = {}
    for _, content in parts:
        if kind == "analytics":
            if not isinstance(content, list):
                raise SnapshotDrift("analytics shard is not a list")
            records = [(row["code"], row) for row in content]
        else:
            if not isinstance(content, dict):
                raise SnapshotDrift(f"{kind} shard is not an object")
            records = list(content.items())
        for code, item in records:
            if code in result:
                raise SnapshotDrift(f"duplicate {kind} corpus: {code}")
            result[code] = item
    return result


def report_projection(code: str, report: dict):
    if any(raw not in report for raw in FIELDS.values()):
        raise SnapshotDrift(f"required report fields missing: {code}")
    row = {"code": code, "source": f"data/output/{code}_relatorio.json"}
    for target, original in FIELDS.items():
        row[target] = report[original]
    return row


def slices_projection(code: str, outputs: Path):
    result = {}
    for suffix in SLICES:
        file = outputs / f"{code}_{suffix}.csv"
        if not file.is_file():
            raise SnapshotDrift(f"missing research source: {file.name}")
        result[suffix] = {"source": f"data/output/{file.name}", "rows": read_csv(file)}
    return result


def original_origin(row: dict):
    candidate = row.get("external_url", "")
    if candidate:
        return candidate
    for key, value in row.items():
        if key.endswith("_detail_url") and value:
            return value
    return ""


def profile_projection(code: str, outputs: Path, previous: dict | None):
    file = outputs / f"{code}_instituicoes.csv"
    if not file.is_file():
        raise SnapshotDrift(f"missing institutional source: {file.name}")
    source_rows = read_csv(file)
    current_by_id = {row["id"]: row for row in (previous or {}).get("rows", [])}
    projected = []
    for number, original in enumerate(source_rows, 1):
        record_id = f"{code}:{number}"
        item = {"id": record_id}
        for target, field in PROFILE_FIELDS.items():
            item[target] = original.get(field, "")
        origin = original_origin(original)
        if not origin and record_id in current_by_id:
            origin = current_by_id[record_id].get("originUrl", "")
        if not origin or urlsplit(origin).scheme not in ("http", "https"):
            raise SnapshotDrift(f"invalid institutional origin: {record_id}")
        item["originUrl"] = origin
        projected.append(item)
    if previous and previous.get("sampled") is True:
        raise SnapshotDrift(f"sampled source requires independent review: {code}")
    result = {"source": f"data/output/{file.name}", "sampled": False, "rows": projected}
    for key in ("licencePolicy", "attribution"):
        if previous and key in previous:
            result[key] = previous[key]
    return result


def verify_access_inventory(outputs: Path, site: Path):
    """Never overwrite human G0/G1 evidence, licence assessments or HOLDs."""
    inventory = read_json(site / "data/public-access-observatory.json")
    if inventory.get("publicationOfIndividualRecordsNotAuthorizedByThisFile") is not True:
        raise SnapshotDrift("access inventory may not authorize item publication")
    rows = read_csv(outputs / "observatorio_indice_dados_publicos_por_corpus.csv")
    extras = read_csv(outputs / "observatorio_unidades_acesso_restrito_indice.csv")
    corpus_codes = [row["corpus_code"] for row in rows]
    restricted_codes = [row["unit_code"] for row in extras]
    # The restricted-unit inventory includes existing active corpora AND 3
    # separately identified units. This overlap is expected, not duplication.
    if len(set(corpus_codes)) != len(corpus_codes) or len(set(restricted_codes)) != len(restricted_codes):
        raise SnapshotDrift("duplicate codes within access source")
    source_codes = set(corpus_codes) | set(restricted_codes)
    additional_units = set(restricted_codes) - set(corpus_codes)
    items = inventory["corpora"]
    site_codes = [item["code"] for item in items]
    if len(set(site_codes)) != len(site_codes) or set(site_codes) != source_codes:
        raise SnapshotDrift("access inventory needs human reconciliation (corpus coverage)")
    published = {item["code"]: item for item in items}
    for row in rows:
        item = published[row["corpus_code"]]
        if item.get("recordDisplay") != "not_authorized_for_new_site":
            raise SnapshotDrift("historical source illicitly promoted to public records")
        checks = {
            "historicalPublicSurfaceRecords": int(row["public_records"]),
            "historicalRestrictedRecords": int(row["restricted_records"]),
            "historicalTotal": int(row["materialized_records_total"]),
        }
        if any(item.get(name) != value for name, value in checks.items()):
            raise SnapshotDrift(f"access index drift: {row['corpus_code']}")
    for row in extras:
        if published[row["unit_code"]].get("recordDisplay") != "not_authorized_for_new_site":
            raise SnapshotDrift("restricted unit illicitly exposed")
    summary = inventory["summary"]
    expected_public = sum(int(row["public_records"]) for row in rows)
    expected_restricted = sum(int(row["restricted_records"]) for row in rows)
    if (
        summary["historicalPublicSurfaceRecords"] != expected_public
        or summary["historicalRestrictedRecords"] != expected_restricted
        or summary["historicalMaterializedTotal"] != expected_public + expected_restricted
        or summary["historicalCorpusRows"] != len(rows)
        or summary["additionalIdentifiedRestrictedUnits"] != len(additional_units)
    ):
        raise SnapshotDrift("public access summary drift; requires human-reviewed update")
    cases = read_json(site / "data/documented-cases.json")
    if cases.get("publicationAuthorized") is not False:
        raise SnapshotDrift("documented cases cannot approve publication")
    excluded = outputs / "observatorio_unidades_identificadas_nao_incorporadas.csv"
    if excluded.is_file():
        source = {row["unit_code"] for row in read_csv(excluded)}
        if not all(item["code"] in source for item in cases["cases"]):
            raise SnapshotDrift("documented case no longer present in source register")


def compare(actual: dict, expected: dict, label: str):
    if actual.keys() != expected.keys():
        missing = sorted(expected.keys() - actual.keys())
        extra = sorted(actual.keys() - expected.keys())
        raise SnapshotDrift(f"{label} corpus mismatch; missing={missing}, extra={extra}")
    for code in expected:
        if actual[code] != expected[code]:
            raise SnapshotDrift(f"{label} stale at {code}; regenerate and review")


def regenerate(parts, projection, kind, write: bool):
    actual = flatten(parts, kind)
    if not write:
        compare(actual, projection, kind)
        return 0
    if kind == "analytics":
        for _, items in parts:
            items[:] = [projection[item["code"]] for item in items if item["code"] in projection]
    else:
        for _, items in parts:
            for code in list(items):
                if code in projection:
                    items[code] = projection[code]
                else:
                    del items[code]
    existing = flatten(parts, kind)
    missing = sorted(projection.keys() - existing.keys())
    _, final = parts[-1]
    for code in missing:
        if kind == "analytics":
            final.append(projection[code])
        else:
            final[code] = projection[code]
    for path, content in parts:
        if read_json(path) != content:
            path.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(missing)


def run(root: Path, write: bool = False):
    outputs = root / "data/output"
    site = root / "site"
    report_files = sorted(outputs.glob(f"*{REPORT_SUFFIX}"))
    if not report_files:
        raise SnapshotDrift("no scientific source reports")
    expected_reports = {}
    expected_slices = {}
    expected_profiles = {}
    actual_profiles = flatten(shards(site, "institution-profiles"), "institution-profiles")
    for file in report_files:
        code = file.name.removesuffix(REPORT_SUFFIX)
        expected_reports[code] = report_projection(code, read_json(file))
        expected_slices[code] = slices_projection(code, outputs)
        expected_profiles[code] = profile_projection(code, outputs, actual_profiles.get(code))

    # Verify human-curated access gates BEFORE any file is written.
    # New corpus inclusion must be reviewed independently, never synthesized here.
    verify_access_inventory(outputs, site)

    regenerate(shards(site, "analytics"), expected_reports, "analytics", write)
    regenerate(shards(site, "research-slices"), expected_slices, "research-slices", write)
    regenerate(shards(site, "institution-profiles"), expected_profiles, "institution-profiles", write)
    print(f"MAR static projections verified: {len(expected_reports)} corpora; "
          f"access inventory still human-gated; write={write}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="regenerate derived projections; never change curator evidence")
    args = parser.parse_args()
    try:
        run(ROOT, write=args.write)
    except (SnapshotDrift, ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        parser.exit(1, f"MAR snapshot coherence HOLD: {exc}\n")


if __name__ == "__main__":
    main()
