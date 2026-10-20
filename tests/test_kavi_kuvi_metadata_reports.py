"""Pre-registered A1–A13 KAVI metadata-only report acceptance tests.

This test module was committed AFTER the impact/test plan and BEFORE
implementation. It intentionally fails import until the report code exists.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.corpora import CORPORA, list_active_corpora
from memoria_audiovisual.europe_research import (
    analyzed_corpora_total, build_europe_research_registry,
)
from memoria_audiovisual.kavi_finna_metadata_reports import (
    REPORT_FILES, build_kavi_metadata_reports,
    serialize_kavi_metadata_reports, write_kavi_metadata_reports,
)
from memoria_audiovisual.kavi_finna_public_catalog import (
    CATALOG_FILENAME, MANIFEST_FILENAME, PublicationRejected,
    load_published_kavi_rows,
)
from memoria_audiovisual.kavi_finna_registry import load_kavi_metadata_index_summary
from memoria_audiovisual.output_files import KAVI_KUVI_OUTPUT_FILES

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "output"


def toy_rows():
    basis = {
        "corpus": "fiaf-kavi",
        "source_service": "finna_api",
        "metadata_provider": "0/KAVI/",
        "metadata_license": "CC0-1.0_API_metadata_only",
        "link_status": "item_link_verified_by_source",
        "media_access_status": "unverified",
        "media_rights_status": "not_verified",
        "custody_status": "not_established",
        "record_review_status": "unreviewed",
        "scope_sha256": "a" * 64,
    }
    one = dict(basis, source_record_id="kavi.elonet_elokuva_101",
               video_title="First film", video_link="https://www.finna.fi/Record/kavi.elonet_elokuva_101",
               source_record_url="https://www.finna.fi/Record/kavi.elonet_elokuva_101",
               film_semantics="film_candidate", year="1936", subjects="Cinema",
               authors="Writer", genres="", languages="fi",
               video_description="Metadata only", online_url_metadata_present="True")
    two = dict(basis, source_record_id="kavi.video_202",
               video_title="Another video", video_link="https://www.finna.fi/Record/kavi.video_202",
               source_record_url="https://www.finna.fi/Record/kavi.video_202",
               film_semantics="unverified_audiovisual_record", year="",
               subjects="", online_url_metadata_present="False")
    return [one, two]


def toy_manifest():
    return {
        "unit_id": "fiaf-kavi", "status": "published_partial_metadata",
        "coverage_status": "partial", "record_count": 2,
        "item_links_present": 2, "expected_total_api_index": 1000,
        "observed_on": "2026-10-19",
        "catalog_sha256": "b" * 64,
        "source_scope_sha256": "a" * 64,
        "source_run_url": "https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/39346643735",
        "metadata_license": "CC0-1.0_API_metadata_only",
        "metadata_publication_approved": True,
        "media_downloaded": False, "corpus_activation": False,
    }


class KaviDocumentaryReportTests(unittest.TestCase):
    def test_a1_approved_snapshot_counts_and_coverage(self):
        rows, manifest = load_published_kavi_rows(OUTPUT_DIR)
        report = build_kavi_metadata_reports(rows, manifest)
        summary = report["summary"]
        self.assertEqual(summary["indexed_metadata_records"], 200)
        self.assertEqual(summary["source_record_links"], 200)
        self.assertEqual(summary["reference_total_api_video_index"], 138399)
        self.assertEqual(summary["coverage_status"], "partial")
        self.assertEqual(summary["reference_observed_on"], "2026-10-19")
        self.assertGreater(summary["coverage_percent_of_api_snapshot"], 0)
        self.assertLess(summary["coverage_percent_of_api_snapshot"], 1)
        self.assertEqual(report["provenance"]["catalog_sha256"],
                         manifest["catalog_sha256"])
        self.assertEqual(report["provenance"]["source_scope_sha256"],
                         manifest["source_scope_sha256"])
        self.assertEqual(sum(row["total"] for row in report["semantics"]), 200)

    def test_a2_a5_coverage_with_optional_fields_absent(self):
        report = build_kavi_metadata_reports(toy_rows(), toy_manifest())
        d = {row["field"]: row for row in report["field_coverage"]}
        self.assertEqual(d["video_title"]["present"], 2)
        self.assertEqual(d["video_title"]["missing"], 0)
        self.assertEqual(d["authors"]["present"], 1)
        self.assertEqual(d["authors"]["missing"], 1)
        self.assertEqual(d["genres"]["present"], 0)
        self.assertEqual(d["genres"]["missing"], 2)
        self.assertEqual(d["languages"]["present"], 1)
        self.assertEqual(d["video_description"]["present"], 1)
        self.assertEqual(d["subjects"]["present"], 1)
        self.assertEqual(d["year"]["present"], 1)
        for item in d.values():
            self.assertEqual(item["present"] + item["missing"], 2)
        self.assertEqual(d["genres"]["percent_present"], 0)
        self.assertEqual(d["video_title"]["percent_present"], 100)

    def test_a6_a7_unreviewed_candidates_do_not_become_playable_or_curated(self):
        rows = toy_rows()
        report = build_kavi_metadata_reports(rows, toy_manifest())
        summary = report["summary"]
        self.assertEqual(summary["film_candidate_records"], 1)
        self.assertEqual(summary["curatorially_reviewed_records"], 0)
        self.assertEqual(summary["verified_playback_records"], 0)
        self.assertEqual(summary["verified_media_rights_records"], 0)
        self.assertEqual(summary["verified_custody_records"], 0)
        self.assertEqual(summary["playback_evidence_status"], "unverified")
        self.assertFalse(report["provenance"]["media_downloaded"])
        self.assertFalse(report["provenance"]["corpus_activation"])

    def test_a8_deterministic_json_and_csv_without_generated_clock(self):
        a = serialize_kavi_metadata_reports(build_kavi_metadata_reports(
            toy_rows(), toy_manifest()))
        b = serialize_kavi_metadata_reports(build_kavi_metadata_reports(
            toy_rows(), toy_manifest()))
        self.assertEqual(a, b)
        self.assertEqual(set(a), set(REPORT_FILES.values()))
        for name, data in a.items():
            self.assertIsInstance(data, bytes)
            self.assertNotIn(b"generated_at", data)
            self.assertNotIn(b"media.example", data)
            self.assertNotIn(b".mp4", data)

    def test_a3_a9_export_guard_invalid_source_no_files_and_unchanged_source(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            out = Path(temp) / "reporting"
            source.mkdir()
            for name in (CATALOG_FILENAME, MANIFEST_FILENAME):
                shutil.copyfile(OUTPUT_DIR / name, source / name)
            original = {
                name: hashlib.sha256((source / name).read_bytes()).hexdigest()
                for name in (CATALOG_FILENAME, MANIFEST_FILENAME)
            }
            result = write_kavi_metadata_reports(source, out)
            self.assertEqual(result["summary"]["indexed_metadata_records"], 200)
            self.assertEqual({x.name for x in out.iterdir()},
                             set(REPORT_FILES.values()))
            self.assertNotIn(KAVI_KUVI_OUTPUT_FILES["analytic_video_catalog"],
                             {x.name for x in out.iterdir()})
            self.assertEqual(original, {
                name: hashlib.sha256((source / name).read_bytes()).hexdigest()
                for name in (CATALOG_FILENAME, MANIFEST_FILENAME)
            })
            # Removing the approved digest must fail before creating any new
            # outputs, including in a second unrelated destination.
            (source / CATALOG_FILENAME).write_bytes(
                (source / CATALOG_FILENAME).read_bytes() + b"tamper"
            )
            other = Path(temp) / "no-output"
            with self.assertRaises(PublicationRejected):
                write_kavi_metadata_reports(source, other)
            self.assertFalse(other.exists())

    def test_a3_missing_or_invalid_observation_date_rejected(self):
        for value in (None, "", "yesterday", "2026-02-31", "2026-10-19T00:00"):
            with self.subTest(value=value):
                m = toy_manifest()
                if value is None:
                    del m["observed_on"]
                else:
                    m["observed_on"] = value
                with self.assertRaises(PublicationRejected):
                    build_kavi_metadata_reports(toy_rows(), m)

    def test_a4_unsafe_record_rejected_by_existing_publication_gate(self):
        # Verify that the builder entrypoint cannot bypass the source check:
        # even an apparently plausible record with an extra identity fails.
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            out = Path(temp) / "out"
            source.mkdir()
            for name in (CATALOG_FILENAME, MANIFEST_FILENAME):
                shutil.copyfile(OUTPUT_DIR / name, source / name)
            manifest = json.loads((source / MANIFEST_FILENAME).read_text())
            manifest["record_count"] = manifest["record_count"] + 1
            (source / MANIFEST_FILENAME).write_text(json.dumps(manifest))
            with self.assertRaises(PublicationRejected):
                write_kavi_metadata_reports(source, out)
            self.assertFalse(out.exists())

    def test_a11_a12_a13_global_scientific_and_scheduler_contract_unchanged(self):
        definition = CORPORA["kavi_kuvi"]
        self.assertNotEqual(definition["code"], CORPORA["fina"]["code"])
        self.assertFalse(definition["counts_as_analyzed_corpus"])
        self.assertFalse(definition["organism_active"])
        self.assertFalse(definition["monthly_refresh_enabled"])
        self.assertNotIn(definition, list_active_corpora())
        self.assertEqual(analyzed_corpora_total(build_europe_research_registry()), 81)
        report = build_kavi_metadata_reports(toy_rows(), toy_manifest())
        self.assertEqual(report["summary"]["verified_playback_records"], 0)
        self.assertNotIn("video_links", REPORT_FILES)
        self.assertNotIn("analytic_video_catalog", REPORT_FILES)


if __name__ == "__main__":
    unittest.main()
