"""Czech Television evidence tiers: public access != validated sample != complete corpus."""
import json
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from memoria_audiovisual.config import CZECH_TELEVISION_IVYSILANI_URL
from memoria_audiovisual.output_files import CZECH_TELEVISION_OUTPUT_FILES
from memoria_audiovisual.snapshot_metadata import build_czech_television_snapshot_metadata
from scripts.check_czech_television_outputs import validate


PLATFORM = "Česká televize iVysílání"


def _public_link(index):
    return {
        "platform": PLATFORM,
        "video_link": (
            f"https://www.ceskatelevize.cz/porady/12701251153-kultura/"
            f"2265441604700{index:02d}/"
        ),
        "video_title": f"Episódio público {index}",
        "video_description": "ficha pública com episode.isPlayable=True; mídia não baixada",
    }


class CzechCompletenessContractTests(unittest.TestCase):
    def _fixture(self, folder, accessible=1):
        directory = Path(folder)
        # The checker requires a complete file set, but only four CSV files
        # and the snapshot are interpreted. Other files remain inert stubs.
        for filename in CZECH_TELEVISION_OUTPUT_FILES.values():
            (directory / filename).write_text("placeholder\n", encoding="utf-8")
        links = pd.DataFrame([_public_link(i) for i in range(accessible)])
        links.to_csv(directory / CZECH_TELEVISION_OUTPUT_FILES["video_links"], index=False)
        pd.DataFrame([{"institution": "Czech Television"}]).to_csv(
            directory / CZECH_TELEVISION_OUTPUT_FILES["institutions"], index=False
        )
        summary = pd.DataFrame([{
            "coverage_scope": "bounded_mvp",
            "accessible_records_count": accessible,
            "validated_sample_count": 0,
            "corpus_complete": False,
            "enumeration_complete": False,
            "integrity_status": "instavel",
            "expected_corpus_total": "",
        }])
        summary.to_csv(directory / CZECH_TELEVISION_OUTPUT_FILES["summary"], index=False)
        pd.DataFrame([{"video_link": row["video_link"]} for row in links.to_dict("records")]).to_csv(
            directory / CZECH_TELEVISION_OUTPUT_FILES["analytic_video_catalog"], index=False
        )
        snapshot = {
            "dataset": "czech-television",
            "source_url": CZECH_TELEVISION_IVYSILANI_URL,
            "counts": {
                "video_links_total": accessible,
                "videos_in_curatorial_catalog": accessible,
            },
            "coverage": {
                "contract_version": 1,
                "scope": "bounded_mvp",
                "accessible_records": accessible,
                "validated_sample_records": 0,
                "sample_validation_status": "not_attested_in_this_run",
                "sample_checkpoint_reference": None,
                "corpus_complete": False,
                "completion_status": "not_demonstrated",
                "source_declared_total": None,
                "enumerated_unique_records": None,
                "pagination_exhausted": False,
                "failed_pages": None,
                "completion_evidence": None,
            },
        }
        self._write_snapshot(directory, snapshot)
        return summary, links, snapshot

    def _write_snapshot(self, directory, snapshot):
        (directory / CZECH_TELEVISION_OUTPUT_FILES["snapshot_metadata"]).write_text(
            json.dumps(snapshot, ensure_ascii=False), encoding="utf-8"
        )

    def test_one_accessible_record_is_never_a_complete_corpus(self):
        with tempfile.TemporaryDirectory() as folder:
            self._fixture(folder, accessible=1)
            valid, result = validate(Path(folder))
        self.assertFalse(valid)
        self.assertEqual(result["accessible_records"], 1)
        self.assertEqual(result["validated_sample_records"], 0)
        self.assertFalse(result["corpus_complete"])
        self.assertEqual(result["eligibility"], "HOLD")
        self.assertTrue(any("NÃO demonstrado" in msg for msg in result["reasons"]))

    def test_ten_accessible_records_are_still_bounded_mvp(self):
        with tempfile.TemporaryDirectory() as folder:
            self._fixture(folder, accessible=10)
            valid, result = validate(Path(folder))
        self.assertFalse(valid)
        self.assertEqual(result["accessible_records"], 10)
        self.assertFalse(result["corpus_complete"])

    def test_legacy_snapshot_without_coverage_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            _, _, snapshot = self._fixture(folder)
            del snapshot["coverage"]
            self._write_snapshot(Path(folder), snapshot)
            valid, result = validate(Path(folder))
        self.assertFalse(valid)
        self.assertTrue(any("contrato explícito" in msg for msg in result["reasons"]))

    def test_unsupported_full_claim_without_provenance_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            _, _, snapshot = self._fixture(folder)
            snapshot["coverage"]["corpus_complete"] = True
            snapshot["coverage"]["completion_status"] = "verified_complete"
            self._write_snapshot(Path(folder), snapshot)
            valid, result = validate(Path(folder))
        self.assertFalse(valid)
        self.assertFalse(result["corpus_complete"])
        self.assertTrue(any("proveniência" in msg or "integral" in msg for msg in result["reasons"]))

    def test_sample_validation_requires_external_checkpoint_and_still_not_full(self):
        with tempfile.TemporaryDirectory() as folder:
            summary, _, snapshot = self._fixture(folder)
            summary["validated_sample_count"] = [1]
            summary.to_csv(
                Path(folder) / CZECH_TELEVISION_OUTPUT_FILES["summary"], index=False
            )
            snapshot["coverage"]["validated_sample_records"] = 1
            self._write_snapshot(Path(folder), snapshot)
            valid, result = validate(Path(folder))
            self.assertFalse(valid)
            self.assertTrue(any("checkpoint independente" in msg for msg in result["reasons"]))
            snapshot["coverage"]["sample_validation_status"] = "checkpoint_verified"
            snapshot["coverage"]["sample_checkpoint_reference"] = {
                "run_id": 43064659823,
                "chain_sha256": "a" * 64,
            }
            self._write_snapshot(Path(folder), snapshot)
            valid, result = validate(Path(folder))
        self.assertFalse(valid)
        # A checkpoint reference that was not independently replayed is
        # a claim, not a verified sample (even with a plausible SHA-256).
        self.assertEqual(result["validated_sample_records"], 0)
        self.assertTrue(any("auditado localmente" in msg for msg in result["reasons"]))
        self.assertFalse(result["corpus_complete"])

    def test_matching_forged_full_evidence_is_still_blocked_in_contract_v1(self):
        with tempfile.TemporaryDirectory() as folder:
            summary, _, snapshot = self._fixture(folder, accessible=1)
            summary["coverage_scope"] = ["full_public_catalogue"]
            summary["integrity_status"] = ["integro"]
            summary["corpus_complete"] = [True]
            summary["enumeration_complete"] = [True]
            summary.to_csv(
                Path(folder) / CZECH_TELEVISION_OUTPUT_FILES["summary"], index=False
            )
            coverage = snapshot["coverage"]
            coverage.update({
                "scope": "full_public_catalogue",
                "corpus_complete": True,
                "completion_status": "verified_complete",
                "source_declared_total": 1,
                "enumerated_unique_records": 1,
                "pagination_exhausted": True,
                "failed_pages": 0,
                "completion_evidence": {
                    "source_url": CZECH_TELEVISION_IVYSILANI_URL,
                    "method": "official_paginated_exhaustion",
                    "audited_pages": 1,
                    "checkpoint_chain_sha256": "b" * 64,
                },
            })
            self._write_snapshot(Path(folder), snapshot)
            valid, result = validate(Path(folder))
        self.assertFalse(valid)
        self.assertFalse(result["corpus_complete"])
        self.assertEqual(result["eligibility"], "HOLD")
        self.assertTrue(any("auditoria independente" in msg for msg in result["reasons"]))

    def test_duplicate_episode_links_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            self._fixture(folder, accessible=2)
            file = Path(folder) / CZECH_TELEVISION_OUTPUT_FILES["video_links"]
            links = pd.read_csv(file)
            links.loc[1, "video_link"] = links.loc[0, "video_link"]
            links.to_csv(file, index=False)
            valid, result = validate(Path(folder))
        self.assertFalse(valid)
        self.assertTrue(any("duplicadas" in msg for msg in result["reasons"]))

    def test_snapshot_builder_cannot_inherit_staged_probe_as_full(self):
        with tempfile.TemporaryDirectory() as folder:
            summary = pd.DataFrame([{
                "website_available": True, "video_links_found_total": 1,
            }])
            links = pd.DataFrame([_public_link(1)])
            frames = {"analytic_video_catalog": pd.DataFrame([_public_link(1)])}
            payload = build_czech_television_snapshot_metadata(
                Path(folder),
                summary_df=summary, links_df=links,
                analysis_frames=frames,
                generated_by="test-only",
            )
        coverage = payload["coverage"]
        self.assertEqual(coverage["contract_version"], 1)
        self.assertEqual(coverage["scope"], "bounded_mvp")
        self.assertEqual(coverage["accessible_records"], payload["counts"]["video_links_total"])
        self.assertEqual(coverage["validated_sample_records"], 0)
        self.assertIsNone(coverage["sample_checkpoint_reference"])
        self.assertFalse(coverage["corpus_complete"])
        self.assertFalse(coverage["pagination_exhausted"])


if __name__ == "__main__":
    unittest.main()
