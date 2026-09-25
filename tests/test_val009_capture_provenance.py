"""Synthetic capture, redirect, exclusion and fail-before-metrics tests.

Never accesses real websites, real predictions or frozen scientific results.
"""

import json
import tempfile
import unittest
from dataclasses import replace
from hashlib import sha256

from memoria_audiovisual.digital_infrastructure.val009_capture_provenance import (
    CaptureProvenanceError,
    CaptureStore,
    CapturedPage,
    build_capture_bundle,
    guarded_capture_development_evaluate,
    url_identity,
    verify_capture_bundle,
)
from test_val009_preflight import COMMIT, encode, digest, make_fixture, repin


CAPTURED_AT = "2026-09-20T10:01:00+00:00"
SELECTED_AT = "2026-09-20T10:02:00+00:00"


def sample_protocol():
    return {
        "entities": [
            {"entity_id": f"entity-{i}",
             "root_url": f"https://example.org/collection/{i}"}
            for i in range(5)
        ],
        "sampling": {
            "max_pages_per_entity": 3,
            "max_review_units_per_entity": 6,
            "max_review_units": 36,
            "minimum_review_units": 5,
            "minimum_entities": 5,
        },
    }


def sample_pages():
    return [
        CapturedPage(
            entity_id=f"entity-{i}",
            root_url=f"https://example.org/collection/{i}",
            requested_url=f"https://EXAMPLE.org/requested/{i}",
            final_url=f"https://example.org/final/{i}",
            discovery_index=0,
            captured_at=CAPTURED_AT,
            capture_state="fetched",
            raw_body=f"<html>synthetic page {i}</html>".encode(),
            http_status_code=200,
            media_type="text/html",
        )
        for i in range(5)
    ]


def synthetic_preflight_inputs(bundle):
    """Adapt existing synthetic sealed fixture; NOT an actual trusted seal."""
    payloads, seal = make_fixture()
    payloads.update(bundle.preflight_payloads())
    protocol = json.loads(payloads["protocol"])
    protocol["entities"] = sample_protocol()["entities"]
    protocol["sampling"].update(sample_protocol()["sampling"])
    payloads["protocol"] = encode(protocol)

    rows = json.loads(bundle.selection)["units"]

    def identity(row):
        return {key: row[key] for key in
                ("review_unit_id", "entity_id", "page_url", "snapshot_reference")}

    payloads["predictions"] = encode({
        "units": [
            {**identity(row),
             "predicted_surface_type": "audiovisual_item",
             "predicted_item_level": True,
             "predicted_access_state": "accessible"}
            for row in rows
        ]
    })
    payloads["human_reviews"] = encode({
        "units": [
            {**identity(row),
             "human_surface_type": "audiovisual_item",
             "human_is_item_level": True,
             "human_access_state": "accessible",
             "human_review_note": "Synthetic review only",
             "reviewer_id": "reviewer-1",
             "reviewed_at": "2026-09-20T10:05:00+00:00",
             "review_status": "complete"}
            for row in rows
        ]
    })
    prediction_freeze = json.loads(payloads["prediction_freeze"])
    prediction_freeze.update({
        "predictions_sha256": digest(payloads["predictions"]),
        "selection_sha256": digest(payloads["selection"]),
        "protocol_sha256": digest(payloads["protocol"]),
    })
    payloads["prediction_freeze"] = encode(prediction_freeze)
    human_freeze = json.loads(payloads["human_freeze"])
    human_freeze.update({
        "reviews_sha256": digest(payloads["human_reviews"]),
        "selection_sha256": digest(payloads["selection"]),
    })
    payloads["human_freeze"] = encode(human_freeze)
    disclosure = json.loads(payloads["disclosure"])
    disclosure.update({
        "human_freeze_sha256": digest(payloads["human_freeze"]),
        "predictions_sha256": digest(payloads["predictions"]),
    })
    payloads["disclosure"] = encode(disclosure)
    # Synthetic legacy snapshots are not part of the NEW deterministic sample.
    for name in list(payloads):
        if name.startswith("snapshot/") and name not in bundle.selected_snapshots:
            del payloads[name]
    return payloads, repin(payloads, seal)


class CaptureProvenanceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.store = CaptureStore(temporary.name)

    def build(self, pages=None, exclusions=()):
        return build_capture_bundle(
            sample_pages() if pages is None else pages,
            store=self.store, protocol=sample_protocol(),
            excluded_urls=exclusions, selected_at=SELECTED_AT,
        )

    def closed(self, bundle, payloads, seal):
        calls = []

        def forbidden(*args, **kwargs):
            calls.append("metrics")
            return {"should_not_exist": True}

        with self.assertRaises(CaptureProvenanceError):
            guarded_capture_development_evaluate(
                payloads, bundle=bundle, store=self.store, trusted=seal,
                observed_commit=COMMIT, evaluator=forbidden,
            )
        self.assertEqual(calls, [], "No metric call after failed provenance")

    def test_redirect_preserves_both_urls_and_runs_only_after_preflight(self):
        bundle = self.build()
        selection = json.loads(bundle.selection)
        evidence = json.loads(bundle.evidence_manifest)
        self.assertEqual(selection["status"], "sufficient")
        self.assertEqual(len(evidence["audit"]), 5)
        self.assertEqual(evidence["units"][0]["requested_url"],
                         "https://EXAMPLE.org/requested/0")
        self.assertEqual(evidence["units"][0]["final_url"],
                         "https://example.org/final/0")
        self.assertEqual(evidence["units"][0]["page_url"],
                         evidence["units"][0]["final_url"])
        self.assertEqual([row["global_discovery_order"] for row in evidence["audit"]],
                         list(range(5)))
        self.assertNotIn(b"predicted_surface_type", bundle.blind_queue)
        payloads, seal = synthetic_preflight_inputs(bundle)
        calls = []

        def evaluator(*args, **kwargs):
            calls.append(True)
            return {"synthetic": True}

        result = guarded_capture_development_evaluate(
            payloads, bundle=bundle, store=self.store, trusted=seal,
            observed_commit=COMMIT, evaluator=evaluator,
        )
        self.assertEqual(calls, [True])
        self.assertEqual(result["mode"], "development_dry_run_only")
        self.assertFalse(result["independent_validation"])
        self.assertFalse(result["m4_scaling_allowed"])

    def test_http_error_and_missing_response_have_verifiable_raw_evidence(self):
        pages = sample_pages()
        pages[0] = replace(
            pages[0], capture_state="http_error", http_status_code=404,
            raw_body=b"not found",
        )
        pages[1] = replace(
            pages[1], capture_state="request_error", http_status_code=None,
            final_url=None, raw_body=b"",
        )
        bundle = self.build(pages)
        evidence = json.loads(bundle.evidence_manifest)["units"]
        self.assertEqual(evidence[0]["capture_state"], "http_error")
        self.assertEqual(evidence[0]["payload_kind"], "raw_response_bytes")
        self.assertEqual(evidence[1]["final_url"], None)
        self.assertEqual(evidence[1]["page_url"], evidence[1]["requested_url"])
        self.assertEqual(evidence[1]["payload_kind"], "no_response_envelope")
        error_bytes = bundle.selected_snapshots[evidence[1]["snapshot_reference"]]
        self.assertEqual(json.loads(error_bytes)["raw_body_sha256"],
                         sha256(b"").hexdigest())
        verify_capture_bundle(
            bundle, self.store, payloads=bundle.preflight_payloads(),
        )

    def test_exclusion_matches_requested_and_redirected_urls(self):
        bundle = self.build(exclusions=[
            "HTTPS://EXAMPLE.ORG/final/0#ignored",
            "https://example.org/requested/1",
        ])
        evidence = json.loads(bundle.evidence_manifest)
        self.assertEqual([row["reason"] for row in evidence["audit"][:2]],
                         ["known_url", "known_url"])
        self.assertEqual(len(evidence["units"]), 3)
        self.assertEqual(json.loads(bundle.selection)["status"],
                         "insufficient_sample")
        self.assertEqual(json.loads(bundle.blind_queue)["units"], [])
        for receipt in bundle.all_receipts:
            self.assertTrue(self.store.load(receipt))

    def test_duplicate_requested_url_is_audited_not_silently_discarded(self):
        pages = sample_pages()
        pages.append(replace(
            pages[0], discovery_index=1,
            final_url="https://example.org/a-different-final",
        ))
        bundle = self.build(pages)
        audit = json.loads(bundle.evidence_manifest)["audit"]
        self.assertEqual(len(audit), 6)
        self.assertEqual(audit[1]["reason"], "duplicate")
        self.assertEqual(len(json.loads(bundle.selection)["units"]), 5)

    def test_url_normalization_does_not_destroy_path_or_query_identity(self):
        self.assertEqual(
            url_identity("HTTPS://EXAMPLE.ORG:443/Path?a=1&b=2#fragment"),
            "https://example.org/Path?a=1&b=2",
        )
        self.assertNotEqual(url_identity("https://example.org/A"),
                            url_identity("https://example.org/a"))
        self.assertNotEqual(url_identity("https://example.org/?a=1&b=2"),
                            url_identity("https://example.org/?b=2&a=1"))

    def test_invalid_source_urls_bytes_and_timestamps_are_rejected(self):
        cases = [
            {"requested_url": ""}, {"root_url": "not-a-url"},
            {"final_url": None}, {"raw_body": b""},
            {"captured_at": "2026-09-20T10:01:00"},
            {"captured_at": "2026-09-20T10:04:00+00:00"},
            {"discovery_index": True},
        ]
        for update in cases:
            with self.subTest(update=update):
                with self.assertRaises(CaptureProvenanceError):
                    self.build([replace(sample_pages()[0], **update)])

    def test_invalid_discovery_indices_abort(self):
        pages = sample_pages()
        for extra in (
            replace(pages[0], discovery_index=0),
            replace(pages[0], discovery_index=3),
        ):
            with self.subTest(discovery_index=extra.discovery_index):
                with self.assertRaises(CaptureProvenanceError):
                    self.build([*pages, extra])

    def test_missing_snapshot_aborts_before_metrics(self):
        bundle = self.build()
        payloads, seal = synthetic_preflight_inputs(bundle)
        receipt = bundle.all_receipts[0]
        self.store._path("snapshots", receipt.snapshot_sha256).unlink()
        self.closed(bundle, payloads, seal)

    def test_changed_raw_snapshot_aborts_before_metrics(self):
        bundle = self.build()
        payloads, seal = synthetic_preflight_inputs(bundle)
        receipt = bundle.all_receipts[0]
        self.store._path("snapshots", receipt.snapshot_sha256).write_bytes(
            b"tampered",
        )
        self.closed(bundle, payloads, seal)

    def test_changed_excluded_snapshot_also_aborts_before_metrics(self):
        pages = sample_pages()
        pages.append(replace(
            pages[0], discovery_index=1,
            requested_url="https://example.org/never-selected",
            final_url="https://example.org/never-selected",
        ))
        bundle = self.build(
            pages, exclusions=["https://example.org/never-selected"],
        )
        payloads, seal = synthetic_preflight_inputs(bundle)
        excluded = next(
            receipt for receipt in bundle.all_receipts
            if receipt.requested_url.endswith("never-selected")
        )
        self.store._path("snapshots", excluded.snapshot_sha256).write_bytes(
            b"tampered-excluded",
        )
        self.closed(bundle, payloads, seal)

    def test_payload_substitution_blocks_even_after_synthetic_repin(self):
        bundle = self.build()
        payloads, seal = synthetic_preflight_inputs(bundle)
        payloads["selection"] = payloads["selection"].replace(
            b"val009-", b"val008-", 1,
        )
        self.closed(bundle, payloads, repin(payloads, seal))

    def test_receipts_are_idempotent_but_reject_replacement(self):
        first = self.store.persist(sample_pages()[0])
        self.assertEqual(first, self.store.persist(sample_pages()[0]))
        document = json.dumps(
            first.document(), sort_keys=True, ensure_ascii=False,
            separators=(",", ":"), allow_nan=False,
        ).encode()
        path = self.store._path("receipts", sha256(document).hexdigest())
        path.write_bytes(b"changed-receipt")
        with self.assertRaises(CaptureProvenanceError):
            self.store.persist(sample_pages()[0])


if __name__ == "__main__":
    unittest.main()
