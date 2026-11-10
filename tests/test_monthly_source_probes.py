"""Offline tests for bounded, allowlisted, per-source availability checks."""
from __future__ import annotations

import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from scripts.probe_monthly_sources import (
    MAX_BYTES, SOURCES, classify_http, probe_one,
)


class FakeResponse:
    def __init__(self, html: bytes, status=200, content_type="text/html"):
        self.status = status
        self.headers = {"Content-Type": content_type}
        self.content = io.BytesIO(html)

    def read(self, max_bytes):
        return self.content.read(max_bytes)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.content.close()


class FakeOpener:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def open(self, request, *, timeout):
        self.calls.append((request.full_url, timeout))
        if self.error:
            raise self.error
        return self.response


class MonthlySourceProbeTests(unittest.TestCase):
    def test_all_seven_sources_are_allowlisted_individually(self):
        self.assertEqual(set(SOURCES), {
            "ape", "asim", "barch", "bnfa", "ciclic", "czech_tv", "eye"
        })
        self.assertTrue(all(url.startswith("https://") for url, _ in SOURCES.values()))

    def test_one_html_get_only_and_never_claim_validated_corpus(self):
        for source, (url, marker) in SOURCES.items():
            with self.subTest(source=source):
                opener = FakeOpener(FakeResponse(
                    ("<html>" + marker + "</html>").encode("utf-8")
                ))
                record = probe_one(source, opener=opener)
                self.assertEqual(len(opener.calls), 1)
                self.assertEqual(opener.calls[0][0], url)
                self.assertEqual(opener.calls[0][1], 12)
                self.assertEqual(record["http_code"], 200)
                self.assertTrue(record["marker_found"])
                self.assertEqual(record["result"], "http_ok_not_proof_of_corpus")
                self.assertFalse(record["corpus_validated"])

    def test_rate_limit_and_forbidden_do_not_get_bypassed(self):
        for status, expected in ((403, "source_access_forbidden"),
                                 (429, "source_rate_limited"),
                                 (302, "source_redirect_requires_review")):
            with self.subTest(status=status):
                opener = FakeOpener(error=HTTPError(
                    "https://www.archivesportaleurope.net", status, "Denied",
                    {}, None
                ))
                answer = probe_one("ape", opener=opener)
                self.assertEqual(answer["result"], expected)
                self.assertEqual(len(opener.calls), 1)
                self.assertEqual(answer["bytes_sampled"], 0)

    def test_oversize_or_non_html_fails_closed(self):
        for response, expected in (
            (FakeResponse(b"x" * (MAX_BYTES + 1)), "oversize_html_sample"),
            (FakeResponse(b"%PDF-1.7", content_type="application/pdf"),
             "unexpected_content_type"),
            (FakeResponse(b"<html>unknown</html>"),
             "html_marker_absent_needs_parser_review"),
        ):
            with self.subTest(expected=expected):
                answer = probe_one("ciclic", opener=FakeOpener(response))
                self.assertEqual(answer["result"], expected)
                self.assertFalse(answer["corpus_validated"])

    def test_unknown_source_rejected_before_network(self):
        with self.assertRaises(ValueError):
            probe_one("evil https://example.net")


if __name__ == "__main__":
    unittest.main()
