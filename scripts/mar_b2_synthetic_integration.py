#!/usr/bin/env python3
"""B2 offline end-to-end synthetic admission rehearsal (NEVER production data).

Exercises the actual B1 analytics projector, B2 CSV-slice projector, and
MAR word-cloud generator against *fully fabricated*, mutually consistent
scientific inputs. Derives all affected static surfaces and stages the whole
bundle atomically. No network, Neon, live corpus or public deployment.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import tempfile
from pathlib import Path
from unittest.mock import patch

from scripts import build_mar_title_wordcloud as cloud
from scripts.build_mar_site_analytics import project_report
from scripts.build_mar_site_bundle_b2 import (
    BundleError, STAGE_SCHEMA, atomic_stage_files, project_research_slices,
)

BASE_COUNT = 62
KAVI_COUNT = 200
NEW_CODE = "fixture_new"
NEW_TITLE_MARKER = "zzconfidentialsourceword"
WORDS = (
    "memoria patrimonio infancia comunidade cultura historia territorio escola "
    "trabalho viagem paisagem fotografia musica festival movimento cidade natureza "
    "familia pesquisa arquitetura sociedade politica educacao"
)


def dump(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, names: list[str], records: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=names, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def corpus_codes(include_new: bool) -> list[str]:
    codes = [f"fixture_{n:03d}" for n in range(BASE_COUNT)]
    if include_new:
        codes.append(NEW_CODE)
    return codes


def populate_fake_sources(root: Path, include_new: bool) -> None:
    """Create a source tree from scratch. All values and organizations are fake."""
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / ".mar-synthetic-only").write_text("NO-PRODUCTION-PUBLICATION\n", encoding="utf-8")
    output = root / "data/output"
    output.mkdir(parents=True, exist_ok=True)
    dump(root / "site/data/kavi-public.json", {
        "schema": "synthetic-kavi-only",
        "approvedMetadataPublication": True,
        "mediaPlaybackVerified": False,
        "mediaRightsVerified": False,
        "total": KAVI_COUNT,
        "records": [{"title": f"Arquivo memorial imaginário {i}"} for i in range(KAVI_COUNT)],
    })

    for code in corpus_codes(include_new):
        count = 21
        country = "Portugal" if code == NEW_CODE else "France"
        record = {
            "total_institutions": 1,
            "with_video_count": 1,
            "with_embeds_count": 0,
            "status_summary": {"ok": 1},
            "integrity_summary": {"integro": 1},
            "platform_summary": {"Repositório fictício": count},
            "continent_summary": {"Europe": 1},
            "video_continent_summary": {"Europe": 1},
            # Deliberately excluded by real aggregate-only projection.
            "top_institutions": [{
                "video_url": "https://example.test/private-raw-film.mp4"
            }],
        }
        dump(output / f"{code}_relatorio.json", record)
        write_csv(
            output / f"{code}_instituicoes.csv",
            ["institution", "country", "continent", "archive_type", "repository_code", "external_url"],
            [{
                "institution": f"Instituição sintética {code}",
                "country": country,
                "continent": "Europe",
                "archive_type": "Arquivo fictício",
                "repository_code": f"FIX-{code}",
                "external_url": "https://example.test/institution",
            }],
        )
        write_csv(
            output / f"{code}_tema_pais.csv",
            ["tema", "pais", "total"],
            [{"tema": "Memória comunitária", "pais": country, "total": str(count)}],
        )
        write_csv(
            output / f"{code}_tema_plataforma.csv",
            ["tema", "plataforma", "total"],
            [{"tema": "Memória comunitária", "plataforma": "Repositório fictício", "total": str(count)}],
        )
        write_csv(
            output / f"{code}_linha_do_tempo_corpus.csv",
            ["dataset", "observation_key", "snapshot_generated_at", "video_links_total",
             "institutions", "institutions_with_video_links", "videos_in_curatorial_catalog",
             "countries_with_videos", "platforms_detected"],
            [{
                "dataset": code,
                "observation_key": f"{code}:2026-11-19T12:00:00Z",
                "snapshot_generated_at": "2026-11-19T12:00:00Z",
                "video_links_total": str(count),
                "institutions": "1",
                "institutions_with_video_links": "1",
                "videos_in_curatorial_catalog": str(count),
                "countries_with_videos": "1",
                "platforms_detected": "1",
            }],
        )
        write_csv(
            output / f"{code}_catalogo_videos_analitico.csv",
            ["video_title", "video_title_display"],
            [
                {
                    "video_title": f"{WORDS} {NEW_TITLE_MARKER if code == NEW_CODE else 'colecao'} {n:04d}",
                    "video_title_display": "",
                }
                for n in range(count)
            ],
        )


def assert_isolated(root: Path) -> None:
    if not (root / ".mar-synthetic-only").is_file():
        raise BundleError("Synthetic-only marker missing: refusing real-site mutation")
    if (root / "src/memoria_audiovisual").exists() or (root / ".git").exists():
        raise BundleError("Real MAR repository detected: fixture-only operation refused")


def profile_from_csv(root: Path, code: str) -> dict:
    rel = f"data/output/{code}_instituicoes.csv"
    with (root / rel).open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    return {
        "source": rel,
        "sampled": False,
        "rows": [{
            "id": f"{code}:{i}",
            "name": r["institution"],
            "country": r["country"],
            "continent": r["continent"],
            "type": r["archive_type"],
            "repositoryCode": r["repository_code"],
            "originUrl": r["external_url"],
        } for i, r in enumerate(rows, start=1)],
    }


def scientific_approval(approval: dict, include_new: bool) -> None:
    if include_new and not approval.get("scientificAdmissionApproved"):
        raise BundleError("HOLD: synthetic corpus lacks separate scientific admission")
    if include_new and not approval.get("aggregateDisplayApproved"):
        raise BundleError("HOLD: synthetic corpus lacks aggregate-display review")
    if include_new and not approval.get("accessEvidenceReviewed"):
        raise BundleError("HOLD: synthetic corpus lacks human access-evidence review")
    if approval.get("individualMetadataApproved") or approval.get("mediaRightsApproved"):
        raise BundleError("HOLD: aggregate admission cannot authorize individual records or media")


def build_fixture_epoch(root: Path, approval: dict, include_new: bool) -> dict:
    assert_isolated(root)
    scientific_approval(approval, include_new)
    codes = corpus_codes(include_new)
    out = root / "site/data"
    analytics, slices, profiles, research, inventory = [], {}, {}, [], []
    for code in codes:
        scientific_report = project_report(root / f"data/output/{code}_relatorio.json", root)
        source_slice = project_research_slices(root, code)
        profile = profile_from_csv(root, code)
        # The source scientific observations and platform / geographic
        # distributions must reconcile before any site snapshot is created.
        n = scientific_report["platforms"]["Repositório fictício"]
        country = profile["rows"][0]["country"]
        if scientific_report["totalInstitutions"] != len(profile["rows"]):
            raise BundleError(f"Inconsistent institution denominator: {code}")
        if int(source_slice["tema_pais"]["rows"][0]["total"]) != n:
            raise BundleError(f"Country distribution does not match report: {code}")
        if source_slice["tema_pais"]["rows"][0]["pais"] != country:
            raise BundleError(f"Inconsistent geographic provenance: {code}")
        if int(source_slice["tema_plataforma"]["rows"][0]["total"]) != n:
            raise BundleError(f"Platform distribution does not match report: {code}")
        if int(source_slice["linha_do_tempo_corpus"]["rows"][0]["video_links_total"]) != n:
            raise BundleError(f"Time series does not match report: {code}")
        analytics.append(scientific_report)
        slices[code] = source_slice
        profiles[code] = profile
        inventory.append({
            "code": code, "name": f"Corpus sintético {code}",
            "shortLabel": code, "continent": "Europe",
            "category": "Arquivo de teste",
            "historicalPublicSurfaceRecords": n,
            "historicalRestrictedRecords": 0, "historicalTotal": n,
            "inventoryStatus": "synthetic_aggregate_approved_no_item_rights",
            "recordDisplay": "not_authorized_for_new_site",
            "humanAccessEvidence": "synthetic_human_review_fixture",
        })
        research.append({
            "code": code,
            "themes": [{"theme": "Memória comunitária", "value": n}],
            "countries": [{"theme": "Memória comunitária", "country": country, "value": n}],
            "platforms": [{"theme": "Memória comunitária", "platform": "Repositório fictício", "value": n}],
            "timeline": [{
                "date": "2026-11-19T12:00:00Z",
                "observationKey": f"{code}:2026-11-19T12:00:00Z",
                "videoLinks": n, "institutions": 1, "curatorialCount": n,
            }],
        })

    # Preserve the exact families read by the current Next.js modules:
    # analytics-N, research-slices-N, institution-profiles-N, research-0.
    for offset in range(0, len(analytics), 11):
        dump(out / f"analytics-{offset//11}.json", analytics[offset:offset + 11])
    for offset in range(0, len(codes), 4):
        names = codes[offset:offset + 4]
        dump(out / f"research-slices-{offset//4}.json", {name: slices[name] for name in names})
    for offset in range(0, len(codes), 10):
        names = codes[offset:offset + 10]
        dump(out / f"institution-profiles-{offset//10}.json", {name: profiles[name] for name in names})
    dump(out / "research-0.json", research)
    total = sum(row["historicalTotal"] for row in inventory)
    dump(out / "public-access-observatory.json", {
        "schema": "mar-synthetic-public-access-v1", "notLive": True,
        "publicAccessIsNotLicense": True,
        "publicationOfIndividualRecordsNotAuthorizedByThisFile": True,
        "kaviSiteApprovedRecords": KAVI_COUNT,
        "summary": {
            "historicalPublicSurfaceRecords": total,
            "historicalRestrictedRecords": 0, "historicalMaterializedTotal": total,
            "activeCorporaWithRecords": len(codes), "restrictedUnits": 0,
            "historicalCorpusRows": len(codes), "additionalIdentifiedRestrictedUnits": 0,
        },
        "corpora": inventory,
    })
    # Cases are human decisions, NOT derivatives of a collector. Keep frozen.
    dump(out / "documented-cases.json", {
        "schema": "mar-synthetic-cases-v1", "publicationAuthorized": False,
        "cases": [{"code": "case-on-hold", "decision": "HOLD",
                   "reason": "fictitious restricted rights"}],
    })
    with patch.object(cloud, "ROOT", root):
        cloud_result = cloud.build()
    dump(out / "title-wordcloud.json", cloud_result)
    if any(NEW_TITLE_MARKER in item["text"] for item in cloud_result["words"]):
        raise BundleError("Single-corpus private token leaked into public word cloud")
    validate_fixture_epoch(root, codes)
    inputs = sorted(p for p in (root / "data/output").iterdir() if p.is_file())
    outputs = sorted(p for p in out.glob("*.json") if p.is_file())
    input_hashes = {p.relative_to(root).as_posix(): sha(p) for p in inputs}
    output_hashes = {p.relative_to(root).as_posix(): sha(p) for p in outputs}
    canonical = json.dumps({"sources": input_hashes, "outputs": output_hashes},
                           sort_keys=True, separators=(",", ":"))
    epoch = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {
        "schema": STAGE_SCHEMA,
        "epochSha256": epoch,
        "status": "SYNTHETIC_REHEARSAL_ONLY_NOT_PUBLICATION_AUTHORIZATION",
        "publicationAuthorized": False,
        "publicAccessAuthorized": False,
        "corpusReportCount": len(codes),
        "individuallyApprovedKaviMetadataRecords": KAVI_COUNT,
        "scientificSourceSha256": input_hashes,
        "staticProjectionSha256": output_hashes,
        "releaseCondition": "Not a production release. Requires scientific admission, review and full real generator.",
    }


def validate_fixture_epoch(root: Path, codes: list[str]) -> None:
    """Fail on a stale or internally inconsistent panel even with an updated hash."""
    out = root / "site/data"
    analytics = []
    for p in sorted(out.glob("analytics-*.json")):
        analytics.extend(json.loads(p.read_text(encoding="utf-8")))
    slices, profiles = {}, {}
    for p in sorted(out.glob("research-slices-*.json")):
        items = json.loads(p.read_text(encoding="utf-8"))
        if set(slices) & set(items):
            raise BundleError("Duplicate research slices")
        slices.update(items)
    for p in sorted(out.glob("institution-profiles-*.json")):
        items = json.loads(p.read_text(encoding="utf-8"))
        if set(profiles) & set(items):
            raise BundleError("Duplicate institution profiles")
        profiles.update(items)
    invent = json.loads((out / "public-access-observatory.json").read_text(encoding="utf-8"))
    research = json.loads((out / "research-0.json").read_text(encoding="utf-8"))
    kavi = json.loads((out / "kavi-public.json").read_text(encoding="utf-8"))
    cases = json.loads((out / "documented-cases.json").read_text(encoding="utf-8"))
    cloud_staged = json.loads((out / "title-wordcloud.json").read_text(encoding="utf-8"))
    roster = set(codes)
    if len(analytics) != len(codes) or {r["code"] for r in analytics} != roster:
        raise BundleError("HOLD: analytics missing or extra corpus")
    if set(slices) != roster or set(profiles) != roster or {r["code"] for r in research} != roster:
        raise BundleError("HOLD: cross-panel roster mismatch")
    if len(invent["corpora"]) != len(codes) or {r["code"] for r in invent["corpora"]} != roster:
        raise BundleError("HOLD: access index roster mismatch")
    if any(r["recordDisplay"] != "not_authorized_for_new_site" for r in invent["corpora"]):
        raise BundleError("HOLD: source was individually published")
    if cases["publicationAuthorized"] or kavi["total"] != KAVI_COUNT or \
       not kavi["approvedMetadataPublication"] or kavi["mediaRightsVerified"]:
        raise BundleError("HOLD: individual rights or human decisions changed")
    if cloud_staged["rawTitlesPublished"] or cloud_staged["individualRecordsPublished"]:
        raise BundleError("HOLD: source title leaked")
    with patch.object(cloud, "ROOT", root):
        expected_cloud = cloud.build()
    if expected_cloud != cloud_staged:
        raise BundleError("HOLD: word cloud is stale relative to source catalogues")
    by_code = {row["code"]: row for row in analytics}
    by_research = {row["code"]: row for row in research}
    access_by_code = {row["code"]: row for row in invent["corpora"]}
    total = 0
    countries: dict[str, int] = {}
    for code in codes:
        report = project_report(root / f"data/output/{code}_relatorio.json", root)
        dims = project_research_slices(root, code)
        prof = profile_from_csv(root, code)
        if report != by_code[code] or dims != slices[code] or prof != profiles[code]:
            raise BundleError(f"HOLD: stale scientific projection: {code}")
        n = report["platforms"]["Repositório fictício"]
        country = prof["rows"][0]["country"]
        total += n
        countries[country] = countries.get(country, 0) + n
        research_row = by_research[code]
        if research_row["themes"][0]["value"] != n \
           or research_row["countries"][0]["value"] != n \
           or research_row["platforms"][0]["value"] != n \
           or research_row["timeline"][0]["videoLinks"] != n:
            raise BundleError(f"HOLD: research map/series stale: {code}")
        if research_row["countries"][0]["country"] != country:
            raise BundleError(f"HOLD: research map provenance mismatch: {code}")
        if access_by_code[code]["historicalTotal"] != n:
            raise BundleError(f"HOLD: access inventory count stale: {code}")
    if invent["summary"]["historicalMaterializedTotal"] != total or \
       sum(r["historicalTotal"] for r in invent["corpora"]) != total:
        raise BundleError("HOLD: global denominator mismatch")
    # The Next.js map and comparison compute these aggregations at build/use
    # time from slices; verifying source-derived totals tests their inputs.
    mapped = {}
    compared = {}
    for code in codes:
        country_row = slices[code]["tema_pais"]["rows"][0]
        platform_row = slices[code]["tema_plataforma"]["rows"][0]
        mapped[country_row["pais"]] = mapped.get(country_row["pais"], 0) + int(country_row["total"])
        compared[code] = sum(int(row["total"]) for row in slices[code]["tema_plataforma"]["rows"])
        if compared[code] != by_code[code]["platforms"]["Repositório fictício"]:
            raise BundleError("HOLD: comparative denominator mismatch")
    if countries != mapped or sum(compared.values()) != total:
        raise BundleError("HOLD: map/comparison total mismatch")


def stage_fixture(root: Path, target: Path, approval: dict, include_new: bool):
    assert_isolated(root)
    manifest = build_fixture_epoch(root, approval, include_new)
    atomic_stage_files(root, target, sorted(manifest["staticProjectionSha256"]), manifest)
    return manifest
