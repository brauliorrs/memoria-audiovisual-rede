"""Pre-registered I1-I14 tests: cross-epoch reconciliation WITHOUT publishing.

The impact matrix and this test module precede the implementation commit.
No HTTP, cursor replay, content download, media rights or corpus promotion.
"""
from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.corpora import CORPORA
from memoria_audiovisual.kavi_finna_incremental_plan import (
    PlanRejected, candidate_rows_sha256, plan_incremental_proposal,
)
from memoria_audiovisual.kavi_finna_public_catalog import (
    CATALOG_FILENAME, MANIFEST_FILENAME, PublicationRejected,
    load_published_kavi_rows,
)

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "data" / "output"


def sample_records(n: int = 2):
    rows, _ = load_published_kavi_rows(BASELINE)
    return copy.deepcopy(rows[:n])


def evidence(rows, *, epoch_id="epoch-20261020-0001",
             status="partial", expected=138399):
    _, baseline = load_published_kavi_rows(BASELINE)
    return {
        "schema_version": "kavi-finna-reconciliation-candidate-1.0",
        "unit_id": "fiaf-kavi",
        "source_service": "finna_api",
        "source_scope_sha256": baseline["source_scope_sha256"],
        "epoch_id": epoch_id,
        "observed_on": "2026-10-20",
        "stage_status": status,
        "page_count": 1,
        "record_count": len(rows),
        "expected_total_api_index": expected,
        "source_rows_sha256": candidate_rows_sha256(rows),
        "source_run_url": (
            "https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/"
            "39346643735"
        ),
        "offline_integrity_verified": True,
        "api_snapshot_freshness_verified": False,
        "media_downloaded": False,
        "promotion_authorized": False,
    }


def add_record(rows, *, identity="kavi.elonet_elokuva_999999"):
    cloned = copy.deepcopy(rows[0])
    cloned["source_record_id"] = identity
    cloned["source_record_url"] = "https://www.finna.fi/Record/" + identity
    cloned["video_link"] = cloned["source_record_url"]
    cloned["partner_site"] = cloned["source_record_url"]
    cloned["video_title"] = "Outra obra pública do catálogo"
    return cloned


class OfflineReconciliationTests(unittest.TestCase):
    def test_i1_partial_unchanged_records_and_unseen_are_not_deleted(self):
        rows = sample_records()
        plan = plan_incremental_proposal(BASELINE, rows, evidence(rows))
        self.assertEqual(plan["unchanged"], 2)
        self.assertEqual(plan["added"], 0)
        self.assertEqual(plan["changed"], 0)
        self.assertEqual(plan["not_observed"], 198)
        self.assertEqual(plan["baseline_record_count"], 200)
        self.assertEqual(plan["status"], "HOLD_FOR_REVIEW")
        self.assertFalse(plan["publication_authorized"])
        self.assertFalse(plan["deletion_authorized"])
        self.assertFalse(plan["media_downloaded"])
        self.assertEqual(plan["candidate_epoch_id"], "epoch-20261020-0001")
        self.assertEqual(plan["baseline_observed_on"], "2026-10-19")

    def test_i2_new_id_only_from_source_evidenced_link(self):
        rows = sample_records(1)
        new = add_record(rows)
        candidate = [rows[0], new]
        plan = plan_incremental_proposal(BASELINE, candidate, evidence(candidate))
        self.assertEqual(plan["added"], 1)
        self.assertEqual(plan["unchanged"], 1)
        item = next(x for x in plan["deltas"] if x["source_record_id"] == new["source_record_id"])
        self.assertEqual(item["change"], "new")
        self.assertNotIn("video_link", item)
        self.assertNotIn("source_record_url", item)

    def test_i3_same_id_update_is_changed_not_another_film(self):
        rows = sample_records(1)
        rows[0]["video_title"] = "Título atualizado no mesmo registro"
        rows[0]["subjects"] = "Assunto atualizado"
        # The Finna projection emits video_subject from subjects; both
        # fields must change together in an internally consistent preview.
        rows[0]["video_subject"] = rows[0]["subjects"]
        plan = plan_incremental_proposal(BASELINE, rows, evidence(rows))
        self.assertEqual(plan["changed"], 1)
        self.assertEqual(plan["added"], 0)
        self.assertEqual(plan["deltas"][0]["change"], "changed")
        self.assertEqual(plan["deltas"][0]["changed_fields"], ["video_title", "subjects"])

    def test_i4_duplicate_source_id_and_digest_mismatch_rejected(self):
        rows = sample_records(1)
        duplicates = rows + copy.deepcopy(rows)
        with self.assertRaises(PlanRejected):
            plan_incremental_proposal(BASELINE, duplicates, evidence(duplicates))
        wrong = evidence(rows)
        wrong["source_rows_sha256"] = "0" * 64
        with self.assertRaises(PlanRejected):
            plan_incremental_proposal(BASELINE, rows, wrong)

    def test_i5_equal_title_different_ids_are_not_deduplicated(self):
        rows = sample_records(1)
        extra = add_record(rows)
        extra["video_title"] = rows[0]["video_title"]
        candidate = [rows[0], extra]
        plan = plan_incremental_proposal(BASELINE, candidate, evidence(candidate))
        self.assertEqual(plan["candidate_record_count"], 2)
        self.assertEqual(plan["added"], 1)
        self.assertEqual(plan["unchanged"], 1)

    def test_i6_forged_link_direct_media_query_and_fragment_rejected(self):
        rows = sample_records(1)
        for link in (
            "https://attacker.example/media.mp4",
            "https://www.finna.fi/Record/kavi.elonet_elokuva_999999",
            rows[0]["video_link"] + "?download=1",
            rows[0]["video_link"] + "#player",
        ):
            with self.subTest(link=link):
                changed = copy.deepcopy(rows)
                changed[0]["video_link"] = link
                changed[0]["source_record_url"] = link
                with self.assertRaises(PlanRejected):
                    plan_incremental_proposal(BASELINE, changed, evidence(changed))

    def test_i7_complete_claim_without_freshness_does_not_delete(self):
        # Synthetic completed one-page epoch. Even complete does not prove
        # records missing from Finna disappeared from their source archive.
        rows = sample_records(1)
        plan = plan_incremental_proposal(BASELINE, rows, evidence(
            rows, status="complete", expected=1,
        ))
        self.assertEqual(plan["not_observed"], 199)
        self.assertEqual(plan["deletion_candidates"], 0)
        self.assertFalse(plan["deletion_authorized"])
        self.assertFalse(plan["publication_authorized"])

    def test_i8_reject_raw_cursors_and_unprojected_private_fields(self):
        rows = sample_records(1)
        raw = evidence(rows)
        raw["resumptionToken"] = "sensitive-opaque-token"
        with self.assertRaises(PlanRejected):
            plan_incremental_proposal(BASELINE, rows, raw)
        unexpected = copy.deepcopy(rows)
        unexpected[0]["onlineUrls"] = "https://media.example/movie.mp4"
        with self.assertRaises(PlanRejected):
            plan_incremental_proposal(BASELINE, unexpected, evidence(unexpected))

    def test_i8_projected_catalog_requires_all_fields_and_consistent_links(self):
        original = sample_records(1)
        for field, value in (
            ("partner_site", "https://media.example/stream.mp4"),
            ("rights_status", "public_domain"),
            ("format", "0/Audio/"),
            ("video_subject", "Forged topic"),
            ("video_published_at", "1800"),
            ("country", "Elsewhere"),
            ("custodian", "confirmed_owner"),
            ("film_semantics", "unverified_audiovisual_record"),
            ("online_url_metadata_present", "https://media.example/stream.mp4"),
        ):
            with self.subTest(field=field):
                rows = copy.deepcopy(original)
                rows[0][field] = value
                with self.assertRaises(PlanRejected):
                    plan_incremental_proposal(BASELINE, rows, evidence(rows))
        for missing in ("partner_site", "format", "rights_status", "languages"):
            with self.subTest(missing=missing):
                rows = copy.deepcopy(original)
                del rows[0][missing]
                with self.assertRaises(PlanRejected):
                    plan_incremental_proposal(BASELINE, rows, evidence(rows))

    def test_i9_cross_scope_provider_status_and_old_epoch_rejected(self):
        rows = sample_records(1)
        bad_evidence = (
            ("source_scope_sha256", "b" * 64),
            ("unit_id", "fina"),
            ("epoch_id", "../escape"),
            ("observed_on", "2026-10-18"),
            ("stage_status", "running"),
            ("api_snapshot_freshness_verified", True),
            ("promotion_authorized", True),
        )
        for key, value in bad_evidence:
            with self.subTest(key=key):
                modified = evidence(rows)
                modified[key] = value
                with self.assertRaises(PlanRejected):
                    plan_incremental_proposal(BASELINE, rows, modified)
        row = copy.deepcopy(rows)
        row[0]["metadata_provider"] = "other-provider"
        with self.assertRaises(PlanRejected):
            plan_incremental_proposal(BASELINE, row, evidence(row))

    def test_i10_a_claim_of_audited_preview_is_never_publication(self):
        rows = sample_records()
        plan = plan_incremental_proposal(BASELINE, rows, evidence(rows))
        self.assertEqual(plan["evidence_status"], "caller_claim_requires_independent_audit")
        self.assertFalse(plan["publication_authorized"])
        self.assertFalse(plan["corpus_activation"])
        self.assertFalse(plan["snapshot_freshness_verified"])
        self.assertNotIn("cursor", json.dumps(plan).lower())
        self.assertNotIn("sensitive", json.dumps(plan).lower())

    def test_i11_i13_preserve_flags_and_original_snapshot_bytes(self):
        rows = sample_records()
        original = {
            name: (BASELINE / name).read_bytes()
            for name in (CATALOG_FILENAME, MANIFEST_FILENAME)
        }
        plan_incremental_proposal(BASELINE, rows, evidence(rows))
        self.assertEqual(original, {
            name: (BASELINE / name).read_bytes()
            for name in original
        })
        cfg = CORPORA["kavi_kuvi"]
        self.assertFalse(cfg["organism_active"])
        self.assertFalse(cfg["monthly_refresh_enabled"])
        self.assertFalse(cfg["counts_as_analyzed_corpus"])

    def test_i12_tampered_published_source_fails_before_comparison(self):
        with tempfile.TemporaryDirectory() as folder:
            location = Path(folder)
            for filename in (CATALOG_FILENAME, MANIFEST_FILENAME):
                shutil.copyfile(BASELINE / filename, location / filename)
            (location / CATALOG_FILENAME).write_bytes(
                (location / CATALOG_FILENAME).read_bytes() + b"tamper"
            )
            records = sample_records(1)
            with self.assertRaises(PublicationRejected):
                plan_incremental_proposal(location, records, evidence(records))

    def test_incoming_missing_verified_record_url_is_held_not_published(self):
        rows = sample_records(1)
        new = add_record(rows)
        new["video_link"] = ""
        new["source_record_url"] = ""
        new["partner_site"] = ""
        new["link_status"] = "missing_source_item_link"
        candidate = [rows[0], new]
        plan = plan_incremental_proposal(BASELINE, candidate, evidence(candidate))
        self.assertEqual(plan["held_missing_links"], 1)
        self.assertEqual(plan["added"], 0)
        self.assertFalse(plan["publication_authorized"])

    def test_invalid_total_and_page_budget_rejected(self):
        rows = sample_records(1)
        for field, value in (
            ("expected_total_api_index", 0),
            ("record_count", 22),
            ("page_count", 0),
            ("page_count", 26),
        ):
            with self.subTest(field=field):
                m = evidence(rows)
                m[field] = value
                with self.assertRaises(PlanRejected):
                    plan_incremental_proposal(BASELINE, rows, m)


if __name__ == "__main__":
    unittest.main()
