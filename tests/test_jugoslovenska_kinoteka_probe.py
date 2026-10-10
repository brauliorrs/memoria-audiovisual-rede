"""Regression tests for the Jugoslovenska Kinoteka (#81) fail-closed probe."""
from __future__ import annotations

import gzip
import unittest

from memoria_audiovisual.jugoslovenska_kinoteka_probe import (
    HOME,
    RobotsGuard,
    Response,
    _sample,
    _xml_text,
    classify_page,
    parse_sitemap,
    parse_surface,
    run_probe,
)


class FakeResponse:
    def __init__(self, text: str = "", status: int = 200, *, headers=None, body=None):
        self.status_code = status
        self.text = text
        self.headers = headers or {"content-type": "text/html"}
        self.content = body if body is not None else text.encode("utf-8")


class FakeSession:
    def __init__(self, mapping: dict[str, FakeResponse]):
        self.mapping = mapping
        self.requests: list[str] = []

    def get(self, url: str, **_kwargs):
        self.requests.append(url)
        if url not in self.mapping:
            return FakeResponse("Not Found", 404)
        return self.mapping[url]


class JugoslovenskaKinotekaProbeTests(unittest.TestCase):
    def test_unverifiable_robots_aborts_before_any_page_or_sitemap(self):
        session = FakeSession({
            "https://www.kinoteka.org.rs/robots.txt": FakeResponse("Denied", 403),
        })
        report = run_probe(session)
        self.assertEqual(report["gate_assessment"], "hold_robots_unverifiable")
        self.assertEqual(session.requests, ["https://www.kinoteka.org.rs/robots.txt"])
        self.assertFalse(report["staged_collector_authorized"])

    def test_robots_disallow_prevents_fetching_blocked_surface(self):
        session = FakeSession({
            "https://www.kinoteka.org.rs/robots.txt": FakeResponse(
                "User-agent: *\nDisallow: /arhiv-jugoslovenske-kinoteke/\n",
                headers={"content-type": "text/plain"},
            ),
            "https://en.kinoteka.org.rs/robots.txt": FakeResponse("", 404),
        })
        report = run_probe(session)
        archive = next(x for x in report["surfaces"] if x["name"] == "film_archive")
        self.assertEqual(archive["error"], "origin_or_robots_block")
        self.assertNotIn(
            "https://www.kinoteka.org.rs/arhiv-jugoslovenske-kinoteke/",
            session.requests,
        )

    def test_nested_sitemaps_use_xml_roles_not_extension(self):
        index = (
            "<sitemapindex>"
            "<sitemap><loc>https://www.kinoteka.org.rs/child?partition=1</loc></sitemap>"
            "<sitemap><loc>https://www.kinoteka.org.rs/archive.xml.gz</loc></sitemap>"
            "</sitemapindex>"
        )
        kind, locs = parse_sitemap(index)
        self.assertEqual(kind, "sitemapindex")
        self.assertEqual(len(locs), 2)
        self.assertIn("https://www.kinoteka.org.rs/child?partition=1", locs)

    def test_image_extension_loc_does_not_count_as_missing_film_record(self):
        xml = (
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
            ' xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
            '<url><loc>https://www.kinoteka.org.rs/film-example</loc>'
            '<image:image><image:loc>https://www.kinoteka.org.rs/poster.jpg</image:loc>'
            '</image:image></url></urlset>'
        )
        kind, urls = parse_sitemap(xml)
        self.assertEqual(kind, "urlset")
        self.assertEqual(urls, ["https://www.kinoteka.org.rs/film-example"])

    def test_xml_unattributed_prefixed_loc_fails_closed(self):
        xml = (
            '<sm:urlset xmlns:sm="http://www.sitemaps.org/schemas/sitemap/0.9">'
            "<sm:url><sm:loc>https://www.kinoteka.org.rs/a</sm:loc></sm:url>"
            "<sm:loc>https://www.kinoteka.org.rs/unattributed</sm:loc>"
            "</sm:urlset>"
        )
        with self.assertRaisesRegex(ValueError, "sitemap_(unattributed_loc|unexpected_container)"):
            parse_sitemap(xml)

    def test_malformed_sitemap_and_html_challenge_never_enumerate(self):
        for xml in ("<html><loc>https://www.kinoteka.org.rs/a</loc></html>",
                    "<sitemapindex><sitemap>"):
            with self.subTest(xml=xml), self.assertRaises(ValueError):
                parse_sitemap(xml)

    def test_gzip_sitemap_decompression_is_size_bounded(self):
        xml = "<urlset><url><loc>https://www.kinoteka.org.rs/archive/</loc></url></urlset>"
        resp = Response(
            HOME, HOME, 200, "", gzip.compress(xml.encode("utf-8")),
            "application/gzip", None,
        )
        self.assertEqual(_xml_text(resp), xml)
        decoded = Response(
            HOME, HOME, 200, "", gzip.compress(b"a" * (8 * 1024 * 1024 + 5)),
            "application/gzip", None,
        )
        with self.assertRaisesRegex(ValueError, "size_limit"):
            _xml_text(decoded)

    def test_small_deterministic_candidate_sample_keeps_every_url(self):
        self.assertEqual(_sample(["a", "b"], count=12), ["a", "b"])
        self.assertEqual(_sample(["a", "b", "c"], count=2), ["a", "c"])
        self.assertEqual(_sample([], count=12), [])
        with self.assertRaisesRegex(ValueError, "sample_size_must_be_positive"):
            _sample(["a"], count=0)

    def test_heritage_100_not_treated_as_individual_catalogue(self):
        self.assertEqual(
            classify_page(
                "https://www.kinoteka.org.rs/"
                "srpski-igrani-filmovi-1911-1999-100-najboljih/"
            ),
            "heritage_designation_100_list",
        )
        self.assertEqual(
            classify_page("https://www.kinoteka.org.rs/repertoar/"),
            "screening_or_programming",
        )
        self.assertEqual(
            classify_page("https://www.kinoteka.org.rs/arhiv-jugoslovenske-kinoteke/"),
            "institutional_overview",
        )

    def test_surface_discovers_only_explicit_links_and_search_forms(self):
        html = (
            "<html><h1>Archive</h1><form method='get'>"
            "<input name='s'></form><a href='/repertoar/'>Schedule</a>"
            "<a href='https://outside.example/'>Other</a></html>"
        )
        parsed = parse_surface(html, HOME)
        self.assertEqual(parsed["title"], "Archive")
        self.assertEqual(parsed["forms"][0]["inputs"], ["s"])
        self.assertIn(
            "https://www.kinoteka.org.rs/repertoar/",
            parsed["same_host_links_sample"],
        )
        self.assertEqual(parsed["external_links_sample"], ["https://outside.example/"])

    def test_sitemap_enumeration_is_evidence_not_staged_permission(self):
        robots = (
            "User-agent: *\nAllow: /\n"
            "Sitemap: https://www.kinoteka.org.rs/siteindex\n"
        )
        index = (
            "<sitemapindex>"
            "<sitemap><loc>https://www.kinoteka.org.rs/items?part=1</loc></sitemap>"
            "</sitemapindex>"
        )
        urlset = (
            "<urlset>"
            "<url><loc>https://www.kinoteka.org.rs/repertoar/film-a</loc></url>"
            "<url><loc>https://www.kinoteka.org.rs/katalog/film-b</loc></url>"
            "</urlset>"
        )
        session = FakeSession({
            "https://www.kinoteka.org.rs/robots.txt": FakeResponse(
                robots, headers={"content-type": "text/plain"},
            ),
            "https://en.kinoteka.org.rs/robots.txt": FakeResponse("", 404),
            "https://www.kinoteka.org.rs/siteindex": FakeResponse(
                index, headers={"content-type": "application/xml"},
            ),
            "https://www.kinoteka.org.rs/items?part=1": FakeResponse(
                urlset, headers={"content-type": "application/xml"},
            ),
        })
        report = run_probe(session)
        self.assertTrue(report["traversal_complete"])
        self.assertEqual(report["enumerated_public_url_count"], 2)
        self.assertEqual(
            report["gate_assessment"], "investigate_candidate_catalogue_semantics",
        )
        self.assertFalse(report["staged_collector_authorized"])
        self.assertEqual(
            report["classification_counts"]["screening_or_programming"], 1,
        )

    def test_sitemap_fetch_failure_prohibits_complete_enumeration(self):
        robots = (
            "User-agent: *\nAllow: /\n"
            "Sitemap: https://www.kinoteka.org.rs/missing.xml\n"
        )
        session = FakeSession({
            "https://www.kinoteka.org.rs/robots.txt": FakeResponse(
                robots, headers={"content-type": "text/plain"},
            ),
            "https://en.kinoteka.org.rs/robots.txt": FakeResponse("", 404),
        })
        result = run_probe(session)
        self.assertFalse(result["traversal_complete"])
        self.assertEqual(result["gate_assessment"], "hold_public_enumeration_incomplete")


if __name__ == "__main__":
    unittest.main()
