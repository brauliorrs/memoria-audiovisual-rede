"""Offline tests: per-source robots preflight and one bounded public HTML GET."""
from __future__ import annotations

import io
import unittest
from urllib.error import HTTPError

from scripts.probe_monthly_sources import (
    MAX_BYTES, SOURCES, probe_one,
)


class FakeResponse:
    def __init__(self, body: bytes, status=200, content_type="text/html"):
        self.status = status
        self.headers = {"Content-Type": content_type}
        self.content = io.BytesIO(body)

    def read(self, max_bytes):
        return self.content.read(max_bytes)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.content.close()


def robots_allow():
    return FakeResponse(b"User-agent: *\nAllow: /\n", content_type="text/plain")


class FakeOpener:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def open(self, request, *, timeout):
        self.calls.append((request.full_url, timeout))
        if not self.responses:
            raise AssertionError("Unexpected network request")
        reply = self.responses.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def http_error(status):
    return HTTPError("https://example.org/page", status, "Denied", {}, None)


class MonthlySourceProbeTests(unittest.TestCase):
    def test_all_seven_sources_are_allowlisted_individually(self):
        self.assertEqual(set(SOURCES), {
            "ape", "asim", "barch", "bnfa", "ciclic", "czech_tv", "eye"
        })
        self.assertTrue(all(url.startswith("https://") for url, _ in SOURCES.values()))

    def test_robots_then_single_html_get_never_prove_corpus(self):
        for source, (url, marker) in SOURCES.items():
            with self.subTest(source=source):
                opener = FakeOpener(
                    robots_allow(),
                    FakeResponse(("<html>" + marker + "</html>").encode()),
                )
                record = probe_one(source, opener=opener)
                self.assertEqual(len(opener.calls), 2)
                self.assertTrue(opener.calls[0][0].endswith("/robots.txt"))
                self.assertEqual(opener.calls[1][0], url)
                self.assertTrue(all(timeout == 12 for _, timeout in opener.calls))
                self.assertEqual(record["robots_status"], "robots_allowed")
                self.assertEqual(record["http_code"], 200)
                self.assertTrue(record["marker_found"])
                self.assertEqual(record["result"], "http_ok_not_proof_of_corpus")
                self.assertFalse(record["corpus_validated"])

    def test_denied_robots_or_unavailable_is_hold_without_catalog_get(self):
        for robots, expected in (
            (FakeResponse(b"User-agent: *\nDisallow: /\n", content_type="text/plain"),
             "robots_disallowed"),
            (http_error(403), "robots_unavailable"),
            (http_error(404), "robots_unavailable"),
            (FakeResponse(b"x" * 65537, content_type="text/plain"),
             "robots_unusable"),
        ):
            with self.subTest(expected=expected):
                opener = FakeOpener(robots)
                answer = probe_one("ape", opener=opener)
                self.assertEqual(answer["result"], expected)
                self.assertEqual(answer["http_code"], None)
                self.assertEqual(len(opener.calls), 1)
                self.assertFalse(answer["corpus_validated"])

    def test_catalog_forbidden_rate_limit_and_redirect_never_bypassed(self):
        for status, expected in (
            (403, "source_access_forbidden"),
            (429, "source_rate_limited"),
            (302, "source_redirect_requires_review"),
        ):
            with self.subTest(status=status):
                opener = FakeOpener(robots_allow(), http_error(status))
                answer = probe_one("ape", opener=opener)
                self.assertEqual(answer["result"], expected)
                self.assertEqual(answer["http_code"], status)
                self.assertEqual(len(opener.calls), 2)
                self.assertEqual(answer["bytes_sampled"], 0)

    def test_oversize_or_non_html_and_marker_absence_fail_closed(self):
        for response, expected in (
            (FakeResponse(b"x" * (MAX_BYTES + 1)), "oversize_html_sample"),
            (FakeResponse(b"%PDF-1.7", content_type="application/pdf"),
             "unexpected_content_type"),
            (FakeResponse(b"<html>unknown</html>"),
             "html_marker_absent_needs_parser_review"),
        ):
            with self.subTest(expected=expected):
                answer = probe_one("ciclic", opener=FakeOpener(robots_allow(), response))
                self.assertEqual(answer["result"], expected)
                self.assertFalse(answer["corpus_validated"])

    def test_unknown_source_rejected_before_network(self):
        with self.assertRaises(ValueError):
            probe_one("evil https://example.net")


if __name__ == "__main__":
    unittest.main()
