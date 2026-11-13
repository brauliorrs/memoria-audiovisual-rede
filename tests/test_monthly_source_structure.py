"""Offline checks for Eye/Czech public INDEX structure; no media fetched."""
from __future__ import annotations

import io
import unittest

from scripts.probe_monthly_structure import structure_one


class Response:
    def __init__(self, body: bytes, type_="text/html"):
        self.status = 200
        self.headers = {"Content-Type": type_}
        self._file = io.BytesIO(body)
    def read(self, n):
        return self._file.read(n)
    def __enter__(self):
        return self
    def __exit__(self, *_):
        self._file.close()


class Opener:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []
    def open(self, request, *, timeout):
        self.calls.append((request.full_url, timeout))
        if not self.responses:
            raise AssertionError("Extra network call")
        return self.responses.pop(0)


def robots_ok():
    return Response(b"User-agent: *\nAllow: /\n", "text/plain")


class PublicStructureTests(unittest.TestCase):
    def test_eye_requires_declared_fragment_filter_and_detail_links(self):
        html = b"""
        <div>with film fragment 630</div>
        <a href="/en/collection/film-history/film/test-film">Test film</a>
        <a href="/en/collection/film-history/film/test-film">duplicate</a>
        <a href="https://evil.example/en/collection/film-history/film/bad">ignore</a>
        """
        opener = Opener(robots_ok(), Response(html))
        result = structure_one("eye", opener=opener)
        self.assertEqual(result["result"], "fragment_index_candidates_only")
        self.assertEqual(result["filter_declared_total"], 630)
        self.assertEqual(result["index_detail_candidates"], 1)
        self.assertFalse(result["corpus_validated"])
        self.assertEqual(len(opener.calls), 2)

    def test_eye_no_filter_is_hold_even_if_film_cards_exist(self):
        html = b'<a href="/en/collection/film-history/film/test-film">Film</a>'
        result = structure_one("eye", opener=Opener(robots_ok(), Response(html)))
        self.assertEqual(result["result"], "filter_or_index_unconfirmed")
        self.assertEqual(result["filter_declared_total"], 0)
        self.assertFalse(result["corpus_validated"])

    def test_czech_public_programmes_are_discovery_only(self):
        html = b"""
        <a href="/porady/151-kultura/">Kultura</a>
        <a href="/porady/151-kultura/">duplicate</a>
        <a href="https://evil.example/porady/123-other/">external</a>
        <a href="/ivysilani/api/anything">not a program</a>
        """
        opener = Opener(robots_ok(), Response(html))
        result = structure_one("czech_tv", opener=opener)
        self.assertEqual(result["result"], "catalogue_programme_candidates_only")
        self.assertEqual(result["index_detail_candidates"], 1)
        self.assertFalse(result["corpus_validated"])
        self.assertEqual(len(opener.calls), 2)

    def test_robots_disallowed_never_reaches_html(self):
        deny = Response(b"User-agent: *\nDisallow: /\n", "text/plain")
        opener = Opener(deny)
        result = structure_one("eye", opener=opener)
        self.assertEqual(result["result"], "robots_disallowed")
        self.assertEqual(len(opener.calls), 1)
        self.assertFalse(result["corpus_validated"])

    def test_not_approved_source_cannot_probe(self):
        with self.assertRaises(ValueError):
            structure_one("ape", opener=Opener())


if __name__ == "__main__":
    unittest.main()
