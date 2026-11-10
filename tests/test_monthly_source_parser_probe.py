"""Strict offline bounds for one-page source parser probes."""
import io
import unittest
from scripts.probe_monthly_parser import parser_one


class FakeResponse:
    def __init__(self, data, content_type="text/html"):
        self.status = 200
        self.headers = {"Content-Type": content_type}
        self.io = io.BytesIO(data)
    def read(self, count):
        return self.io.read(count)
    def __enter__(self):
        return self
    def __exit__(self, *_):
        self.io.close()


class FakeOpener:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []
    def open(self, req, *, timeout):
        self.calls.append(req.full_url)
        if not self.responses:
            raise AssertionError("Unauthorized second page/media request")
        return self.responses.pop(0)


def allowed_robots():
    return FakeResponse(b"User-agent: *\nAllow: /\n", "text/plain")


class ParserProbeTests(unittest.TestCase):
    def test_eye_one_page_parser_passes_but_corpus_remains_unvalidated(self):
        html = b"""
        <div>with film fragment 630</div>
        <div class="view-content">
          <li class="packery-item">
           <h2><a href="/en/collection/film-history/film/test-film">Test film</a></h2>
          </li>
        </div>
        """
        source = FakeOpener(allowed_robots(), FakeResponse(html))
        r = parser_one("eye", opener=source)
        self.assertEqual(r["declared_total"], 630)
        self.assertEqual(r["parser_records"], 1)
        self.assertEqual(r["result"], "eye_one_page_parser_pass")
        self.assertEqual(len(source.calls), 2)
        self.assertFalse(r["corpus_validated"])
        self.assertFalse(r["media_downloaded"])

    def test_unfiltered_eye_page_never_claims_a_valid_item(self):
        html = b'<div class="view-content"><li class="packery-item"><h2><a href="/en/collection/film-history/film/test">Film</a></h2></li></div>'
        r = parser_one("eye", opener=FakeOpener(allowed_robots(), FakeResponse(html)))
        self.assertEqual(r["parser_records"], 0)
        self.assertEqual(r["result"], "eye_fragment_filter_not_proven")

    def test_czech_public_programmes_only_candidates(self):
        html = b'<main><a href="/porady/151-kultura/">Kultura</a></main>'
        source = FakeOpener(allowed_robots(), FakeResponse(html))
        r = parser_one("czech_tv", opener=source)
        self.assertEqual(r["parser_records"], 1)
        self.assertEqual(r["result"], "czech_programme_candidates_only")
        self.assertEqual(len(source.calls), 2)
        self.assertFalse(r["corpus_validated"])

    def test_unapproved_source_cannot_run_parser(self):
        with self.assertRaises(ValueError):
            parser_one("ape", opener=FakeOpener())

    def test_disallowed_robots_prevents_any_index_fetch(self):
        robots = FakeResponse(b"User-agent: *\nDisallow: /\n", "text/plain")
        opener = FakeOpener(robots)
        r = parser_one("eye", opener=opener)
        self.assertEqual(r["result"], "robots_disallowed")
        self.assertEqual(len(opener.calls), 1)


if __name__ == "__main__":
    unittest.main()
