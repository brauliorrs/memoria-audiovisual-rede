"""VAL-009 origin-capture regression: synthetic sessions and legacy origin events.

No real HTTP targets, fresh classification, independent validation or M4 promotion.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

import requests

from memoria_audiovisual.digital_infrastructure.val009_capture_provenance import (
    CaptureProvenanceError,
    CaptureStore,
    build_capture_bundle,
    guarded_capture_development_evaluate,
    verify_capture_bundle,
)
from memoria_audiovisual.digital_infrastructure.val009_origin_bridge import (
    OriginSpec,
    capture_origin_http,
    from_v23_origin_report,
)
from test_val009_capture_provenance import sample_protocol, synthetic_preflight_inputs
from test_val009_preflight import COMMIT, repin

AT = "2026-09-20T10:01:00+00:00"
SELECTED = "2026-09-20T10:02:00+00:00"
ROBOTS_ALLOW = {
    "checked": True, "allowed": True, "reason": "robots_rule_allow",
    "robots_url": "https://example.org/robots.txt",
    "response": {"status_code": 200, "body_base64": "dGVzdA=="},
}
ROBOTS_DENY = {
    "checked": True, "allowed": False, "reason": "robots_rule_deny",
    "response": {"body_base64": "RGlzYWxsb3c6IC8="},
}


class Response:
    def __init__(
        self, url, body=b"<html>synthetic</html>", *, status=200,
        media_type="text/html", fail_stream=False,
    ):
        self.url = url
        self.status_code = status
        self.headers = {"Content-Type": media_type}
        self.body = body
        self.fail_stream = fail_stream
        self.closed = False
        self.read_bytes = 0

    def iter_content(self, *, chunk_size):
        for i in range(0, len(self.body), chunk_size):
            if self.fail_stream and i:
                raise requests.Timeout("synthetic mid-stream interruption")
            chunk = self.body[i:i + chunk_size]
            self.read_bytes += len(chunk)
            yield chunk

    def close(self):
        self.closed = True


def spec(index=0, requested=None):
    return OriginSpec(
        entity_id=f"entity-{index}",
        root_url=f"https://example.org/collection/{index}",
        requested_url=requested or f"https://example.org/requested/{index}",
        discovery_index=0,
        parent_url=f"https://example.org/collection/{index}", depth=1,
    )


def scope(url, root):
    return urlsplit(url).hostname == urlsplit(root).hostname


def http_capture(specification, response=None, *, robots=None, get=None, limit=500):
    if response is None:
        response = Response("https://example.org/final")
    if get is None:
        get = lambda *_args, **_kwargs: response
    return capture_origin_http(
        specification, get=get,
        robots_decision=lambda _url: (
            (False, ROBOTS_DENY) if robots is False else (True, ROBOTS_ALLOW)
        ),
        is_in_scope=scope,
        clock=lambda: AT, max_response_bytes=limit,
    )


class OriginBridgeTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.store = CaptureStore(tmp.name)

    def test_redirect_exposes_original_requested_and_final_before_reduction(self):
        request = spec(requested="https://EXAMPLE.org/Requested?a=2&a=1")
        response = Response("https://example.org/Final?a=2&a=1")
        event = http_capture(request, response)
        self.assertEqual(event.requested_url, request.requested_url)
        self.assertEqual(event.final_url, response.url)
        self.assertNotEqual(event.requested_url, event.final_url)
        self.assertEqual(event.capture_state, "fetched")
        self.assertTrue(response.closed)
        receipt = self.store.persist(event)
        self.assertEqual(self.store.load(receipt), response.body)
        self.assertEqual(receipt.robots_evidence, ROBOTS_ALLOW)
        self.assertEqual(receipt.response_received_bytes, len(response.body))
        self.assertFalse(receipt.response_truncated)

    def test_robots_denied_never_fetches_and_keeps_robots_evidence(self):
        called = []

        def forbidden(*args, **kwargs):
            called.append(True)
            raise AssertionError("HTTP target must not be requested")

        event = http_capture(spec(), robots=False, get=forbidden)
        self.assertEqual(called, [])
        self.assertIsNone(event.final_url)
        self.assertEqual(event.capture_state, "blocked_by_robots")
        receipt = self.store.persist(event)
        self.assertEqual(receipt.payload_kind, "no_response_envelope")
        self.assertEqual(receipt.robots_evidence["allowed"], False)
        envelope = json.loads(self.store.load(receipt))
        self.assertEqual(envelope["artifact_kind"], "no_response_envelope")

    def test_connection_timeout_preserves_unknown_final_and_exception(self):
        def timeout(*args, **kwargs):
            raise requests.Timeout("synthetic timeout")

        event = http_capture(spec(), get=timeout)
        self.assertEqual(event.capture_state, "request_error")
        self.assertIsNone(event.final_url)
        self.assertEqual(event.error_type, "Timeout")
        self.assertEqual(event.response_received_bytes, 0)
        receipt = self.store.persist(event)
        self.assertEqual(receipt.error_message, "synthetic timeout")
        self.store.load(receipt)

    def test_http_error_with_and_without_body_is_not_fabricated(self):
        for body in (b"error page", b""):
            with self.subTest(body=body):
                response = Response("https://example.org/failed", body, status=503)
                event = http_capture(spec(), response)
                self.assertEqual(event.capture_state, "http_error")
                receipt = self.store.persist(event)
                self.assertEqual(
                    receipt.payload_kind,
                    "raw_response_bytes" if body else "empty_response_envelope",
                )
                stored = self.store.load(receipt)
                if not body:
                    self.assertEqual(json.loads(stored)["http_status_code"], 503)
                    self.assertEqual(receipt.raw_body_sha256, hashlib.sha256(b"").hexdigest())
                else:
                    self.assertEqual(stored, body)

    def test_successful_empty_http_204_is_explicit_not_missing(self):
        event = http_capture(
            spec(), Response("https://example.org/empty", b"", status=204)
        )
        self.assertEqual(event.capture_state, "fetched")
        receipt = self.store.persist(event)
        self.assertEqual(receipt.payload_kind, "empty_response_envelope")
        self.assertEqual(json.loads(self.store.load(receipt))["http_status_code"], 204)

    def test_unsupported_media_is_2xx_not_http_error(self):
        event = http_capture(
            spec(), Response(
                "https://example.org/download", b"\x00\x10", status=200,
                media_type="application/octet-stream",
            )
        )
        self.assertEqual(event.capture_state, "unsupported_content_type")
        receipt = self.store.persist(event)
        self.assertEqual(receipt.media_type, "application/octet-stream")
        self.assertEqual(self.store.load(receipt), b"\x00\x10")

    def test_redirect_out_of_scope_preserves_off_site_final_url(self):
        url = "https://outside.example.net/item?b=2&a=1"
        event = http_capture(spec(), Response(url, b"off-site"))
        self.assertEqual(event.capture_state, "redirect_outside_scope")
        self.assertEqual(event.final_url, url)
        self.assertEqual(self.store.persist(event).final_url, url)

    def test_stream_cap_measures_read_lower_bound_not_complete_body(self):
        response = Response("https://example.org/large", b"0123456789")
        event = http_capture(spec(), response, limit=4)
        self.assertEqual(event.raw_body, b"0123")
        self.assertTrue(event.response_truncated)
        self.assertEqual(event.response_received_bytes, 5)
        self.assertEqual(response.read_bytes, 5)
        receipt = self.store.persist(event)
        self.assertEqual(self.store.load(receipt), b"0123")
        self.assertEqual(receipt.raw_body_sha256, hashlib.sha256(b"0123").hexdigest())
        self.assertNotEqual(receipt.raw_body_sha256, hashlib.sha256(response.body).hexdigest())

    def test_interrupted_stream_never_emits_successful_capture(self):
        response = Response("https://example.org/midstream", b"012345", fail_stream=True)
        with self.assertRaises(CaptureProvenanceError):
            http_capture(spec(), response, limit=2)
        self.assertTrue(response.closed)

    def test_no_final_url_is_not_reconstructed_from_request(self):
        with self.assertRaises(CaptureProvenanceError):
            http_capture(spec(), Response(None))
        with self.assertRaises(CaptureProvenanceError):
            http_capture(spec(), Response("https://user:pass@example.org/page"))

    def test_robots_evidence_is_required_and_checked_before_fetch(self):
        visits = []

        def http(*args, **kwargs):
            visits.append(True)
            return Response("https://example.org/ok")

        with self.assertRaises(CaptureProvenanceError):
            capture_origin_http(
                spec(), get=http,
                robots_decision=lambda _url: (
                    True, {"checked": True, "allowed": False, "reason": "conflict"}
                ), is_in_scope=scope, clock=lambda: AT,
            )
        self.assertEqual(visits, [])

    def test_v23_bridge_rejects_derived_only_report(self):
        report = SimpleNamespace(
            root_url=spec().root_url, protocol_version="2.3.0-dev",
            pages=[SimpleNamespace(url=spec().requested_url)],
        )
        with self.assertRaises(CaptureProvenanceError):
            from_v23_origin_report(report, entity_id="entity-0")

    def _v23(self):
        raw = b"<html>old origin bytes</html>"
        original = "https://example.org/original?b=2&a=1"
        final = "https://example.org/final?b=2&a=1"
        capture = SimpleNamespace(
            requested_url=original, final_url=final, observed_at=AT,
            fetch_status="fetched", status_code=200, content_type="text/html",
            response_body=raw, response_received_bytes=len(raw),
            response_truncated=False, robots_evidence=ROBOTS_ALLOW,
            error_type=None, error_message=None,
        )
        # The legacy derived URL sorted query parameters: must NOT change origin.
        page = SimpleNamespace(
            url="https://example.org/final?a=1&b=2",
            fetched_at=AT, fetch_status="fetched", status_code=200,
            content_sha256=hashlib.sha256(raw).hexdigest(),
            parent_url=None, depth=0,
        )
        report = SimpleNamespace(
            root_url=spec().root_url, protocol_version="2.3.0-dev",
            captures=(capture,), pages=(page,),
        )
        return report

    def test_v23_bridge_keeps_origin_query_order_and_hash(self):
        event, = from_v23_origin_report(self._v23(), entity_id="entity-0")
        self.assertEqual(event.requested_url, "https://example.org/original?b=2&a=1")
        self.assertEqual(event.final_url, "https://example.org/final?b=2&a=1")
        self.assertEqual(event.capture_state, "fetched")
        self.assertEqual(self.store.load(self.store.persist(event)), event.raw_body)

    def test_v23_bridge_refuses_missing_count_mismatch_and_dishonest_status(self):
        report = self._v23()
        report.captures[0].response_received_bytes = None
        with self.assertRaises(CaptureProvenanceError):
            from_v23_origin_report(report, entity_id="entity-0")
        report = self._v23()
        report.pages[0].content_sha256 = "f" * 64
        with self.assertRaises(CaptureProvenanceError):
            from_v23_origin_report(report, entity_id="entity-0")
        report = self._v23()
        report.pages = ()
        with self.assertRaises(CaptureProvenanceError):
            from_v23_origin_report(report, entity_id="entity-0")

    def test_v23_block_uses_raw_robot_denial_not_derived_url(self):
        report = self._v23()
        request = report.captures[0].requested_url
        report.captures[0].final_url = None
        report.captures[0].fetch_status = "blocked_by_robots"
        report.captures[0].status_code = None
        report.captures[0].response_body = None
        report.captures[0].response_received_bytes = None
        report.captures[0].robots_evidence = ROBOTS_DENY
        report.pages[0].url = request
        report.pages[0].fetch_status = "blocked_by_robots"
        report.pages[0].status_code = None
        report.pages[0].content_sha256 = None
        event, = from_v23_origin_report(report, entity_id="entity-0")
        self.assertEqual(event.capture_state, "blocked_by_robots")
        self.assertIsNone(event.final_url)

    def test_materialization_preserves_truncation_and_all_nonselected(self):
        events = []
        for index in range(5):
            request = spec(index)
            if index == 0:
                response = Response(f"https://example.org/final/{index}", b"0123456789")
                event = http_capture(request, response, limit=4)
            elif index == 1:
                event = http_capture(request, robots=False)
            else:
                event = http_capture(
                    request, Response(f"https://example.org/final/{index}"),
                )
            events.append(event)
        first = events[0]
        events.extend([
            replace(first, discovery_index=1),
            replace(
                first, discovery_index=2,
                requested_url="https://example.org/exclude",
                final_url="https://example.org/exclude",
            ),
        ])
        bundle = build_capture_bundle(
            events, store=self.store,
            protocol=sample_protocol(),
            excluded_urls=["https://example.org/exclude"],
            selected_at=SELECTED,
        )
        audit = json.loads(bundle.evidence_manifest)["audit"]
        self.assertEqual(len(audit), 7)
        self.assertEqual([x["reason"] for x in audit[:3]],
                         ["selected", "duplicate", "known_url"])
        self.assertTrue(audit[0]["response_truncated"])
        self.assertEqual(audit[0]["response_received_bytes"], 5)
        self.assertEqual(audit[1]["snapshot_sha256"], audit[0]["snapshot_sha256"])
        self.assertEqual(json.loads(bundle.selection)["status"], "sufficient")
        self.assertEqual(len(bundle.all_receipts), len(audit))
        self.assertEqual(
            bundle.evidence_manifest,
            build_capture_bundle(
                events, store=self.store, protocol=sample_protocol(),
                excluded_urls=["https://example.org/exclude"], selected_at=SELECTED,
            ).evidence_manifest,
        )
        verify_capture_bundle(
            bundle, self.store, payloads=bundle.preflight_payloads(),
        )

    def test_excluded_bytes_tampering_aborts_before_any_metric(self):
        events = [
            http_capture(spec(i), Response(f"https://example.org/final/{i}"))
            for i in range(5)
        ]
        events.append(replace(
            events[0], discovery_index=1,
            requested_url="https://example.org/exclude",
            final_url="https://example.org/exclude",
            raw_body=b"secret excluded evidence",
            response_received_bytes=len(b"secret excluded evidence"),
        ))
        bundle = build_capture_bundle(
            events, store=self.store, protocol=sample_protocol(),
            excluded_urls=["https://example.org/exclude"], selected_at=SELECTED,
        )
        payloads, trusted = synthetic_preflight_inputs(bundle)
        excluded = next(
            r for r in bundle.all_receipts
            if r.requested_url.endswith("/exclude")
        )
        self.store._path("snapshots", excluded.snapshot_sha256).write_bytes(
            b"altered excluded bytes"
        )
        called = []

        def forbidden(*args, **kwargs):
            called.append(True)

        with self.assertRaises(CaptureProvenanceError):
            guarded_capture_development_evaluate(
                payloads, bundle=bundle, store=self.store,
                trusted=repin(payloads, trusted), observed_commit=COMMIT,
                evaluator=forbidden,
            )
        self.assertEqual(called, [])


if __name__ == "__main__":
    unittest.main()
