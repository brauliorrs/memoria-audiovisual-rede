"""Synthetic contract tests; no independent run, live URLs, or real predictions."""

import json
import unittest
from dataclasses import replace
from hashlib import sha256

from memoria_audiovisual.digital_infrastructure.val009_preflight import (
    PreflightFailure,
    TrustedSeal,
    guarded_development_evaluate,
    verify_preflight,
)

COMMIT = "b" * 40
BASE_TIME = "2026-09-20T10:00:00+00:00"
LABELS = {
    "surface_types": [
        "homepage", "institutional_landing_page", "archive_landing_page",
        "search_or_index", "news_or_editorial", "item_record", "audiovisual_item",
        "restricted_or_unavailable", "unknown",
    ],
    "access_states": ["accessible", "geo_restricted", "collector_blocked"],
    "item_positive": ["item_record", "audiovisual_item"],
}


def encode(value):
    return json.dumps(value, sort_keys=True).encode("utf-8")


def digest(value):
    return sha256(value).hexdigest()


def make_fixture():
    """A fully synthetic, internally coherent bundle; not a historical seal."""
    protocol = {
        "protocol_id": "MAR-T2A-M3-VAL-009-PROTOCOL",
        "experiment_id": "MAR-T2A-M3-VAL-009", "protocol_version": "2.3.0",
        "candidate_version": "2.3.0-dev", "candidate_commit": COMMIT,
        "candidate_reference_is_freeze": True, "status": "sealed",
        "sampling": {"minimum_review_units": 5, "minimum_entities": 5,
                     "max_review_units": 36, "max_review_units_per_entity": 6},
        "labels": LABELS,
        "blinding": {"human_queue_allowed_fields": [
            "review_unit_id", "entity_id", "page_url", "root_url", "parent_url",
            "snapshot_reference", "observed_at", "human_surface_type",
            "human_is_item_level", "human_access_state", "human_review_note",
            "reviewer_id", "reviewed_at", "review_status",
        ]},
    }
    units = [
        {"review_unit_id": f"unit-{i}", "entity_id": f"entity-{i}",
         "page_url": f"https://example.org/{i}",
         "snapshot_reference": f"snapshot/{i}",
         "requested_url": f"https://example.org/requested/{i}"}
        for i in range(5)
    ]
    selection = {"status": "sufficient", "selected_at": "2026-09-20T10:02:00+00:00", "units": units}
    evidence = {"units": [
        {**row, "captured_at": "2026-09-20T10:01:00+00:00",
         "snapshot_sha256": digest(f"<html>synthetic snapshot {i}</html>".encode())}
        for i, row in enumerate(units)
    ]}
    queue = {"units": [{**{key: value for key, value in row.items()
                         if key != "requested_url"}, "review_status": "pending"}
                       for row in units]}
    predictions = {"units": [{**row, "predicted_surface_type": "audiovisual_item",
                              "predicted_item_level": True, "predicted_access_state": "accessible"}
                             for row in units]}
    human = {"units": [{**row, "human_surface_type": "audiovisual_item",
                        "human_is_item_level": True, "human_access_state": "accessible",
                        "human_review_note": "Synthetic evidence check", "reviewer_id": "reviewer-1",
                        "reviewed_at": "2026-09-20T10:05:00+00:00", "review_status": "complete"}
                       for row in units]}
    payloads = {
        "protocol": encode(protocol), "selection": encode(selection),
        "evidence_manifest": encode(evidence), "blind_queue": encode(queue),
        "predictions": encode(predictions), "human_reviews": encode(human),
    }
    for name in (
        "candidate_wrapper", "base_classifier", "collector", "config", "selector",
        "evaluator", "dependencies", "exclusions", "codebook",
    ):
        payloads[name] = f"FAKE TEST CONTENT FOR {name}".encode()
    for i in range(5):
        payloads[f"snapshot/{i}"] = f"<html>synthetic snapshot {i}</html>".encode()
    payloads["prediction_freeze"] = encode({
        "predictions_sha256": digest(payloads["predictions"]),
        "selection_sha256": digest(payloads["selection"]),
        "protocol_sha256": digest(payloads["protocol"]),
        "candidate_commit": COMMIT, "custodian_id": "custodian-1",
        "frozen_at": "2026-09-20T10:03:00+00:00",
    })
    payloads["human_freeze"] = encode({
        "reviews_sha256": digest(payloads["human_reviews"]),
        "selection_sha256": digest(payloads["selection"]),
        "reviewer_id": "reviewer-1",
        "review_started_at": "2026-09-20T10:04:00+00:00",
        "frozen_at": "2026-09-20T10:06:00+00:00",
    })
    payloads["disclosure"] = encode({
        "predictions_sha256": digest(payloads["predictions"]),
        "human_freeze_sha256": digest(payloads["human_freeze"]),
        "custodian_id": "custodian-1",
        "opened_at": "2026-09-20T10:07:00+00:00",
    })
    trusted = TrustedSeal(
        protocol_id="MAR-T2A-M3-VAL-009-PROTOCOL", experiment_id="MAR-T2A-M3-VAL-009",
        protocol_version="2.3.0", candidate_version="2.3.0-dev",
        commit_sha=COMMIT, sealed_at=BASE_TIME, witness_reference="synthetic-offline-witness",
        custodian_id="custodian-1", reviewer_id="reviewer-1",
        restricted_store_reference="restricted://synthetic-vault",
        pins={name: digest(data) for name, data in payloads.items()},
    )
    return payloads, trusted


def change_doc(payloads, name, edit):
    data = json.loads(payloads[name])
    edit(data)
    payloads[name] = encode(data)


def repin(payloads, trusted):
    """Simulate an attacker who controls internal digests but not independent truth."""
    return replace(trusted, pins={name: digest(data) for name, data in payloads.items()})


class PreflightTests(unittest.TestCase):
    def test_valid_synthetic_inputs_are_not_a_scientific_certification(self):
        payloads, trusted = make_fixture()
        called = []

        def evaluator(expected, humans, predictions, *, protocol):
            called.append(True)
            self.assertEqual(len(expected), 5)
            self.assertEqual(len(humans), 5)
            self.assertEqual(len(predictions), 5)
            self.assertEqual(protocol["protocol_version"], "2.3.0")
            return {"synthetic": True}

        result = guarded_development_evaluate(
            payloads, trusted=trusted, observed_commit=COMMIT, evaluator=evaluator,
        )
        self.assertEqual(len(called), 1)
        self.assertEqual(result["mode"], "development_dry_run_only")
        self.assertFalse(result["independent_validation"])
        self.assertFalse(result["m4_scaling_allowed"])

    def _assert_closed(self, mutator):
        payloads, trusted = make_fixture()
        payloads, trusted = mutator(payloads, trusted)
        called = []

        def evaluator(*args, **kwargs):
            called.append(True)
            return {"illegal_metric": 1}

        with self.assertRaises(PreflightFailure):
            guarded_development_evaluate(
                payloads, trusted=trusted, observed_commit=COMMIT, evaluator=evaluator,
            )
        self.assertFalse(called, "Metrics must never run after any failed gate")

    def test_unpinned_modified_bytes_rejected(self):
        self._assert_closed(lambda p, s: (dict(p, collector=b"tampered"), s))

    def test_commit_divergence_rejected(self):
        self._assert_closed(lambda p, s: (p, replace(s, commit_sha="a" * 40)))

    def test_protocol_or_candidate_version_mismatch_rejected(self):
        def mutate(p, s):
            change_doc(p, "protocol", lambda x: x.update(candidate_version="2.3.1"))
            return p, repin(p, s)
        self._assert_closed(mutate)

    def test_draft_cannot_run_even_with_matching_hashes(self):
        def mutate(p, s):
            change_doc(p, "protocol", lambda x: x.update(status="draft"))
            return p, repin(p, s)
        self._assert_closed(mutate)

    def test_duplicated_ids_rejected_even_with_new_pins(self):
        def mutate(p, s):
            change_doc(p, "selection", lambda x: x["units"].append(x["units"][0].copy()))
            return p, repin(p, s)
        self._assert_closed(mutate)

    def test_missing_prediction_rejected(self):
        def mutate(p, s):
            change_doc(p, "predictions", lambda x: x["units"].pop())
            return p, repin(p, s)
        self._assert_closed(mutate)

    def test_extra_review_rejected(self):
        def mutate(p, s):
            change_doc(p, "human_reviews", lambda x: x["units"].append({**x["units"][0], "review_unit_id": "extra"}))
            return p, repin(p, s)
        self._assert_closed(mutate)

    def test_incomplete_human_review_rejected(self):
        def mutate(p, s):
            change_doc(p, "human_reviews", lambda x: x["units"][0].update(human_review_note=""))
            return p, repin(p, s)
        self._assert_closed(mutate)

    def test_wrong_reviewer_or_custodian_rejected(self):
        self._assert_closed(lambda p, s: (p, replace(s, reviewer_id="custodian-1")))

    def test_missing_snapshot_rejected(self):
        self._assert_closed(lambda p, s: (dict((k, v) for k, v in p.items() if k != "snapshot/4"), s))

    def test_forged_snapshot_content_rejected(self):
        def mutate(p, s):
            p["snapshot/1"] = b"other snapshot"
            return p, repin(p, s)
        self._assert_closed(mutate)

    def test_blind_queue_prediction_field_rejected(self):
        def mutate(p, s):
            change_doc(p, "blind_queue", lambda x: x["units"][0].update(predicted_surface_type="audiovisual_item"))
            return p, repin(p, s)
        self._assert_closed(mutate)

    def test_prediction_freeze_content_mismatch_rejected(self):
        def mutate(p, s):
            change_doc(p, "prediction_freeze", lambda x: x.update(predictions_sha256="0" * 64))
            return p, repin(p, s)
        self._assert_closed(mutate)

    def test_human_freeze_content_mismatch_rejected(self):
        def mutate(p, s):
            change_doc(p, "human_freeze", lambda x: x.update(reviews_sha256="0" * 64))
            return p, repin(p, s)
        self._assert_closed(mutate)

    def test_out_of_order_disclosure_rejected(self):
        def mutate(p, s):
            change_doc(p, "disclosure", lambda x: x.update(opened_at="2026-09-20T10:04:00+00:00"))
            return p, repin(p, s)
        self._assert_closed(mutate)

    def test_review_started_before_prediction_freeze_rejected(self):
        def mutate(p, s):
            change_doc(p, "human_freeze", lambda x: x.update(review_started_at="2026-09-20T10:02:00+00:00"))
            return p, repin(p, s)
        self._assert_closed(mutate)

    def test_naive_timestamp_rejected(self):
        def mutate(p, s):
            change_doc(p, "human_freeze", lambda x: x.update(frozen_at="2026-09-20T10:06:00"))
            return p, repin(p, s)
        self._assert_closed(mutate)

    def test_sample_sufficiency_rejected_even_when_declared_sufficient(self):
        def mutate(p, s):
            change_doc(p, "protocol", lambda x: x["sampling"].update(minimum_review_units=6))
            return p, repin(p, s)
        self._assert_closed(mutate)

    def test_missing_artifact_rejected(self):
        self._assert_closed(lambda p, s: (dict((k, v) for k, v in p.items() if k != "dependencies"), s))

    def test_requested_url_discrepancy_rejected(self):
        def mutate(p, s):
            change_doc(p, "evidence_manifest", lambda x: x["units"][0].update(
                requested_url="https://example.org/unexpected"))
            return p, repin(p, s)
        self._assert_closed(mutate)

    def test_blinding_contract_change_rejected(self):
        def mutate(p, s):
            change_doc(p, "protocol", lambda x: x["blinding"]["human_queue_allowed_fields"].append(
                "predicted_surface_type"))
            return p, repin(p, s)
        self._assert_closed(mutate)

    def test_verifier_only_returns_verified_rows(self):
        p, s = make_fixture()
        verified = verify_preflight(p, trusted=s, observed_commit=COMMIT)
        self.assertEqual(len(verified.expected), len(verified.humans))
        self.assertEqual(len(verified.humans), len(verified.predictions))


if __name__ == "__main__":
    unittest.main()
