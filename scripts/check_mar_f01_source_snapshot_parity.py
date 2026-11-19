#!/usr/bin/env python3
"""F01: independent source-to-site data parity for historical approved snapshots.

This is *not* interface parity, independent scientific review, or authorization
to republish third-party records. It never writes project files or goes online.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError(f"Invalid CSV schema: {path.name}")
        rows = list(reader)
    if any(None in row for row in rows):
        raise ValueError(f"Malformed source CSV rows: {path.name}")
    return rows


def _unique(items: list[dict], key: str, where: str) -> tuple[dict[str, dict], list[str]]:
    errors: list[str] = []
    index: dict[str, dict] = {}
    for row in items:
        code = row.get(key)
        if not isinstance(code, str) or not code.strip():
            errors.append(f"{where}: empty identifier")
        elif code in index:
            errors.append(f"{where}: duplicate identifier {code}")
        else:
            index[code] = row
    return index, errors


def _count(row: dict, field: str) -> int:
    value = int(row[field])
    if value < 0:
        raise ValueError(f"Negative count: {field}")
    return value


def audit_access_index(
    world_rows: list[dict], corpus_rows: list[dict], public: dict,
) -> list[str]:
    """Compare historical CSVs and the static index at every corpus code."""
    errors: list[str] = []
    try:
        world = [r for r in world_rows if r.get("scope_level") == "world"]
        if len(world) != 1 or world[0].get("scope") != "World":
            return ["M03: world index not uniquely identified"]
        world = world[0]
        summary = public["summary"]
        for src, dest in (
            ("public_records", "historicalPublicSurfaceRecords"),
            ("restricted_records", "historicalRestrictedRecords"),
            ("materialized_records_total", "historicalMaterializedTotal"),
            ("active_corpora_with_records", "activeCorporaWithRecords"),
            ("restricted_units_total", "restrictedUnits"),
        ):
            if _count(world, src) != summary[dest]:
                errors.append(f"M03: summary mismatch {dest}")
        if public.get("observedRuleVersion") != world["rule_version"]:
            errors.append("M03: rule version mismatch")
        rows_by_code, problems = _unique(corpus_rows, "corpus_code", "M03 source")
        errors.extend(problems)
        site_by_code, problems = _unique(public["corpora"], "code", "M03 site")
        errors.extend(problems)
        if len(rows_by_code) != 60 or len(site_by_code) != 63:
            errors.append("M03: expected 60 historical corpus rows + 3 reviewed restricted additions")
        if len(rows_by_code) != summary["historicalCorpusRows"]:
            errors.append("M03: inconsistent corpus source count")
        if len(set(site_by_code) - set(rows_by_code)) != summary["additionalIdentifiedRestrictedUnits"]:
            errors.append("M03: unexpected extra restricted units")
        for code, row in rows_by_code.items():
            if code not in site_by_code:
                errors.append(f"M03: missing site corpus {code}")
                continue
            site = site_by_code[code]
            for src, dest in (
                ("public_records", "historicalPublicSurfaceRecords"),
                ("restricted_records", "historicalRestrictedRecords"),
                ("materialized_records_total", "historicalTotal"),
            ):
                if _count(row, src) != site.get(dest):
                    errors.append(f"M03: source/site drift {code}.{dest}")
            if row.get("rule_version") != public.get("observedRuleVersion"):
                errors.append(f"M03: source rule version drift {code}")
        if sum(int(r["public_records"]) for r in corpus_rows) != summary["historicalPublicSurfaceRecords"]:
            errors.append("M03: source public sum mismatch")
        if sum(int(r["restricted_records"]) for r in corpus_rows) != summary["historicalRestrictedRecords"]:
            errors.append("M03: source restricted sum mismatch")
        for code, site in site_by_code.items():
            if site.get("recordDisplay") != "not_authorized_for_new_site":
                errors.append(f"M03: unauthorized record display {code}")
            if code not in rows_by_code and site.get("historicalTotal") != 0:
                errors.append(f"M03: additional restricted unit has unsupported total {code}")
        if public.get("notLive") is not True:
            errors.append("M03: snapshot wrongly described as live")
        if public.get("publicationOfIndividualRecordsNotAuthorizedByThisFile") is not True:
            errors.append("M03: index cannot grant record publication")
        if public.get("publicAccessIsNotLicense") is not True:
            errors.append("M03: public access must not be interpreted as media license")
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(f"M03: malformed input: {exc}")
    return errors


def audit_kavi(source: list[dict], source_bytes: bytes, manifest: dict, public: dict) -> list[str]:
    """Compare each permitted KAVI metadata field and ensure media stays blocked."""
    errors: list[str] = []
    try:
        if hashlib.sha256(source_bytes).hexdigest() != manifest.get("catalog_sha256"):
            errors.append("M02: source CSV hash drift")
        if manifest.get("catalog_sha256") != public.get("sourceCatalogSha256"):
            errors.append("M02: projected source hash drift")
        rows, problems = _unique(source, "source_record_id", "M02 source")
        errors.extend(problems)
        site, problems = _unique(public["records"], "id", "M02 site")
        errors.extend(problems)
        if len(source) != 200 or len(site) != 200:
            errors.append("M02: 200-item reviewed metadata scope changed")
        if set(rows) != set(site):
            errors.append("M02: source/site identifier membership drift")
        if len(site) != public.get("total") or len(site) != manifest.get("record_count"):
            errors.append("M02: count mismatch across manifest, source, site")
        for code, raw in rows.items():
            record = site.get(code)
            if record is None:
                continue
            for field, mapped in (
                ("source_record_url", "sourceUrl"),
                ("video_title", "title"),
                ("genres", "genres"),
                ("subjects", "subjects"),
                ("languages", "languages"),
                ("year", "year"),
            ):
                if (raw.get(field) or "") != (record.get(mapped) or ""):
                    errors.append(f"M02: altered metadata for {code}.{mapped}")
            if record.get("sourceUrl") != "https://www.finna.fi/Record/" + code:
                errors.append(f"M02: unexpected source origin {code}")
            if any(key in record for key in ("video_url", "video_description", "mediaUrl", "media_file")):
                errors.append(f"M02: unapproved media/description field {code}")
        if manifest.get("metadata_publication_approved") is not True:
            errors.append("M02: missing metadata-only approval")
        for flag, required in (
            ("media_downloaded", False), ("corpus_activation", False),
            ("viewing_at_origin_only", True),
        ):
            if manifest.get(flag) is not required:
                errors.append(f"M02: unsafe manifest flag {flag}")
        for flag, required in (
            ("approvedMetadataPublication", True), ("individualReview", False),
            ("mediaPlaybackVerified", False), ("mediaRightsVerified", False),
        ):
            if public.get(flag) is not required:
                errors.append(f"M02: unsafe public flag {flag}")
        if public.get("scope") != "partial_metadata_only":
            errors.append("M02: publication scope expanded")
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(f"M02: malformed input: {exc}")
    return errors


def audit_cases(source: list[dict], public: dict) -> list[str]:
    """Cases are a reviewed subset, not permission to add a source to corpora."""
    errors: list[str] = []
    try:
        original, problems = _unique(source, "unit_code", "M19 source")
        errors.extend(problems)
        cases, problems = _unique(public["cases"], "code", "M19 site")
        errors.extend(problems)
        if len(cases) != 17:
            errors.append("M19: 17 reviewed cases expected")
        for code, item in cases.items():
            raw = original.get(code)
            if raw is None:
                errors.append(f"M19: missing source case {code}")
                continue
            for dest, source_key in (
                ("name", "unit_label"),
                ("reason", "negative_reason"),
                ("nextStep", "next_step"),
                ("category", "access_category"),
            ):
                if item.get(dest) != raw.get(source_key):
                    errors.append(f"M19: changed source decision {code}.{dest}")
        if public.get("publicationAuthorized") is not False:
            errors.append("M19: cases publication authorization changed")
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(f"M19: malformed input: {exc}")
    return errors


def check(root: Path = ROOT) -> dict[str, list[str]]:
    data = root / "data/output"
    site = root / "site/data"
    kavi_path = data / "kavi_mar_metadata_links.csv"
    return {
        "M02": audit_kavi(
            read_csv(kavi_path), kavi_path.read_bytes(),
            json.loads((data / "kavi_mar_metadata_links_manifest.json").read_text(encoding="utf-8")),
            json.loads((site / "kavi-public.json").read_text(encoding="utf-8")),
        ),
        "M03": audit_access_index(
            read_csv(data / "observatorio_indice_dados_publicos.csv"),
            read_csv(data / "observatorio_indice_dados_publicos_por_corpus.csv"),
            json.loads((site / "public-access-observatory.json").read_text(encoding="utf-8")),
        ),
        "M19": audit_cases(
            read_csv(data / "observatorio_unidades_identificadas_nao_incorporadas.csv"),
            json.loads((site / "documented-cases.json").read_text(encoding="utf-8")),
        ),
    }


def main() -> int:
    try:
        results = check()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"F01 DATA PARITY: HOLD input error: {exc}")
        return 1
    for flow, issues in results.items():
        print(f"F01 {flow} source-to-site: {'PASS' if not issues else 'HOLD'}")
        for issue in issues:
            print(f"  {issue}")
    if any(results.values()):
        return 1
    print("F01 data equivalence only; no interface/scientific/publication sign-off")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
