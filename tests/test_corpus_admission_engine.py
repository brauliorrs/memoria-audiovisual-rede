"""Contracts for MAR's universal but fail-closed corpus admission layer."""
import csv
import hashlib
import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from memoria_audiovisual.corpus_admission_engine import (
    COMMON_FIELDS, REGISTRY, ConnectorSpec, ContractRejected,
    SourceReview, SourceState, admission_assessment, connector_for,
    propose_connector, registry_inventory, transition,
)
from memoria_audiovisual.approved_corpus_admission import (
    AdmissionRejected, CORPUS_HOSTS, FIELDS, VERSION, load_one_approved_corpus,
)

RUN = "https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/12345"


class UniversalConnectorTests(unittest.TestCase):
    def test_registry_compatibility_and_immutable_contract(self):
        expected = {"eye", "czech-television", "ciclic", "asim", "bnfa"}
        self.assertEqual(set(REGISTRY), expected)
        self.assertEqual(dict(CORPUS_HOSTS), {
            key: spec.record_hosts for key, spec in REGISTRY.items()
        })
        self.assertEqual(FIELDS, COMMON_FIELDS)
        self.assertEqual(len(COMMON_FIELDS), 12)
        with self.assertRaises(TypeError):
            REGISTRY["ape"] = REGISTRY["eye"]
        with self.assertRaises(FrozenInstanceError):
            REGISTRY["eye"].corpus_code = "other"

    def test_unknown_or_on_hold_sources_have_no_runtime_admission(self):
        for code in ("ape", "foo", "", "KAVI", "../eye"):
            with self.subTest(code=code), self.assertRaises(ContractRejected):
                connector_for(code)
            with tempfile.TemporaryDirectory() as root:
                with self.assertRaises(AdmissionRejected):
                    load_one_approved_corpus(root, code)

    def test_new_connector_proposal_is_not_registration(self):
        spec = ConnectorSpec(
            "archive-100", "Example official archive",
            "memoria_audiovisual.example_source",
            frozenset({"archive.example.org"}), "institutional_record",
        )
        plan = propose_connector(spec)
        self.assertEqual(plan["review_status"], "pending_independent_review")
        self.assertFalse(plan["registry_updated"])
        self.assertFalse(plan["publication_authorized"])
        with self.assertRaises(ContractRejected):
            connector_for("archive-100")
        with self.assertRaises(ContractRejected):
            propose_connector(REGISTRY["eye"])

    def test_bad_host_code_module_or_source_kind_rejected(self):
        cases = [
            ("A", "memoria_audiovisual.sample", frozenset({"a.example.org"}), "institutional_record"),
            ("valid", "__import__.os", frozenset({"a.example.org"}), "institutional_record"),
            ("valid", "memoria_audiovisual.sample", frozenset({"x..example.org"}), "institutional_record"),
            ("valid", "memoria_audiovisual.sample", frozenset({"a.example.org"}), "execute"),
        ]
        for code, module, hosts, kind in cases:
            with self.subTest(code=code, module=module, hosts=hosts):
                with self.assertRaises(ContractRejected):
                    ConnectorSpec(code, "Archive", module, hosts, kind)

    def test_state_machine_requires_steps_and_independent_review(self):
        review = SourceReview("eye")
        with self.assertRaises(ContractRejected):
            transition(review, SourceState.ADMISSION_READY, actor="operator-1",
                       evidence_id="sha256:abcd")
        review = transition(review, SourceState.PROBED, actor="operator-1",
                            evidence_id="sha256:probe123")
        review = transition(review, SourceState.EVIDENCE_VALIDATED,
                            actor="verifier-2", evidence_id="sha256:verified456")
        with self.assertRaises(ContractRejected):
            transition(review, SourceState.CURATOR_REVIEWED,
                       actor="operator-1", evidence_id="sha256:review789")
        review = transition(review, SourceState.CURATOR_REVIEWED,
                            actor="curator-3", evidence_id="sha256:review789")
        with self.assertRaises(ContractRejected):
            transition(review, SourceState.ADMISSION_READY,
                       actor="curator-3", evidence_id="sha256:approval10")
        review = transition(review, SourceState.ADMISSION_READY,
                            actor="reviewer-4", evidence_id="sha256:approval10")
        result = admission_assessment(review)
        self.assertTrue(result["can_submit_to_admission_gate"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["scientific_corpus_validated"])
        self.assertEqual(len(review.history), 4)

    def test_hold_blocks_until_explicit_reset(self):
        review = transition(SourceReview("eye"), SourceState.HOLD,
                            actor="safety-1", evidence_id="issue:99")
        self.assertFalse(admission_assessment(review)["can_submit_to_admission_gate"])
        with self.assertRaises(ContractRejected):
            transition(review, SourceState.PROBED, actor="operator-1", evidence_id="sha256:abc")
        with self.assertRaises(ContractRejected):
            transition(review, SourceState.REGISTERED, actor="operator-1")
        review = transition(review, SourceState.REGISTERED, actor="admin-2",
                            override_hold=True)
        self.assertEqual(review.state, SourceState.REGISTERED)
        self.assertFalse(admission_assessment(review)["can_submit_to_admission_gate"])

    def test_evidence_is_mandatory_and_no_state_skips(self):
        with self.assertRaises(ContractRejected):
            transition(SourceReview("eye"), SourceState.PROBED, actor="operator-1")
        with self.assertRaises(ContractRejected):
            transition(SourceReview("eye"), SourceState.PROBED, actor="")

    def test_inventory_is_documentary_only(self):
        inventory = registry_inventory()
        self.assertEqual(len(inventory), 5)
        self.assertTrue(all(r["onboarding_state"] == "registered" for r in inventory))
        self.assertTrue(all(not r["scientific_corpus_validated"] for r in inventory))
        self.assertTrue(all(not r["publication_authorized"] for r in inventory))

    def test_100_new_source_proposals_do_not_expand_allowlist(self):
        for n in range(100):
            proposal = propose_connector(ConnectorSpec(
                f"archive-{n}", "Synthetic",
                "memoria_audiovisual.test_adapter",
                frozenset({f"source{n}.example.org"}), "institutional_record",
            ))
            self.assertFalse(proposal["registry_updated"])
        self.assertEqual(len(REGISTRY), 5)

    def test_existing_pr95_manifest_contract_still_reads_valid_records(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / "mar_admitted"
            base.mkdir()
            url = "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/test"
            row = {
                "source_record_id": "film:test", "source_record_url": url,
                "video_title": "Documentary", "year": "1937", "authors": "",
                "subjects": "", "languages": "", "genres": "", "video_description": "",
                "media_access_status": "unverified",
                "media_rights_status": "not_verified",
                "record_review_status": "approved_metadata_only",
            }
            path = base / "eye.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerow(row)
            (base / "eye.manifest.json").write_text(json.dumps({
                "schema_version": VERSION, "corpus_code": "eye",
                "status": "approved_public_metadata", "approved_for_publication": True,
                "reviewer": "curator-1", "source_run_url": RUN,
                "observed_on": "2026-11-16", "record_count": 1,
                "catalog_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "media_downloaded": False, "viewing_at_origin_only": True,
                "corpus_activation": False,
            }), encoding="utf-8")
            rows = load_one_approved_corpus(directory, "eye")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["video_link"], url)


if __name__ == "__main__":
    unittest.main()
