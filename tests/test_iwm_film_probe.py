import unittest
from unittest.mock import patch

from memoria_audiovisual.iwm_film_probe import (
    IWM_FILM_SEARCH_URL,
    ProbeResponse,
    parse_record_html,
    parse_script_hints,
    parse_surface_html,
    robots_allowed,
    run_iwm_film_probe,
)


class IwmFilmProbeTests(unittest.TestCase):
    def test_surface_parser_discovers_search_form_scripts_and_records(self):
        html = """
        <html><head><title>IWM Film</title></head><body>
          <form method="get" action="/search/results">
            <input name="q">
          </form>
          <a href="/record/3186">Record A</a>
          <script src="/assets/catalogue.js"></script>
          <script>const endpoint = "/api/search/query";</script>
        </body></html>
        """
        parsed = parse_surface_html(
            html,
            "https://film.iwmcollections.org.uk/",
        )
        self.assertEqual(parsed["record_links_count"], 1)
        self.assertEqual(parsed["forms"][0]["action"], IWM_FILM_SEARCH_URL)
        self.assertIn(
            "https://film.iwmcollections.org.uk/assets/catalogue.js",
            parsed["script_urls"],
        )
        self.assertIn(
            "https://film.iwmcollections.org.uk/api/search/query",
            parsed["inline_endpoint_hints"],
        )

    def test_script_parser_reports_hints_but_does_not_enumerate_ids(self):
        parsed = parse_script_hints(
            'const search="/api/search"; const one="/record/4219";',
            "https://film.iwmcollections.org.uk/assets/app.js",
        )
        self.assertIn(
            "https://film.iwmcollections.org.uk/api/search",
            parsed["endpoint_hints"],
        )
        self.assertEqual(
            parsed["record_links"],
            ["https://film.iwmcollections.org.uk/record/4219"],
        )

    def test_record_parser_confirms_film_metadata(self):
        html = """
        <html><body>
          <h1>FIVE YEARS AGO [Main Title]</h1>
          <div>Film Number: IWM 442</div>
          <div>Digitised: Yes</div>
          <div>Production Date: 1923</div>
          <div>Production Country: GB</div>
          <div>Sound: Silent</div>
          <div>Physical Characteristics: B&amp;W</div>
          <div>Technical Details: Format: 35mm</div>
          <div>Media files</div>
        </body></html>
        """
        parsed = parse_record_html(
            html,
            "https://film.iwmcollections.org.uk/record/3186",
        )
        self.assertTrue(parsed["film_semantics_confirmed"])
        self.assertEqual(parsed["digitised"], "yes")
        self.assertIn("Media files", parsed["media_markers"])

    def test_robots_longest_user_agent_group_and_rule_win(self):
        robots = """
        User-agent: *
        Disallow: /search/
        User-agent: memoriaaudiovisualrede
        Allow: /search/results
        Disallow: /search/private
        """
        self.assertTrue(
            robots_allowed(
                robots,
                "MemoriaAudiovisualRede",
                "https://film.iwmcollections.org.uk/search/results",
            )
        )
        self.assertFalse(
            robots_allowed(
                robots,
                "MemoriaAudiovisualRede",
                "https://film.iwmcollections.org.uk/search/private",
            )
        )


    def _run_probe_with_responses(self, response_text_by_url):
        def fake_fetch(session, url, **kwargs):
            status_code, content_type, text = response_text_by_url.get(
                url,
                (404, "text/plain", ""),
            )
            return ProbeResponse(
                requested_url=url,
                final_url=url,
                status_code=status_code,
                content_type=content_type,
                text=text,
                error=None,
            )

        with patch(
            "memoria_audiovisual.iwm_film_probe.fetch_public_url",
            side_effect=fake_fetch,
        ):
            return run_iwm_film_probe(session=object())

    def test_probe_follows_nested_sitemap_and_validates_its_records(self):
        base = "https://film.iwmcollections.org.uk"
        robots = """User-agent: *
Allow: /
Sitemap: https://film.iwmcollections.org.uk/sitemap.xml
"""
        root_sitemap = """<sitemapindex>
          <sitemap><loc>https://film.iwmcollections.org.uk/sitemap-records-1.xml</loc></sitemap>
        </sitemapindex>"""
        child_sitemap = """<urlset>
          <url><loc>https://film.iwmcollections.org.uk/record/9001</loc></url>
          <url><loc>https://film.iwmcollections.org.uk/record/9002</loc></url>
        </urlset>"""
        record = """<html><body>
          <h1>Film record</h1>
          <div>Film Number: IWM 1</div>
          <div>Digitised: Yes</div>
          <div>Production Date: 1940</div>
          <div>Production Country: GB</div>
        </body></html>"""
        search = """<html><body>
          <form method="get" action="/search/results"><input name="q"></form>
        </body></html>"""
        responses = {
            f"{base}/robots.txt": (200, "text/plain", robots),
            f"{base}/": (200, "text/html", "<html></html>"),
            f"{base}/search/results": (200, "text/html", search),
            f"{base}/conflict_categories": (200, "text/html", "<html></html>"),
            f"{base}/faqs": (200, "text/html", "<html></html>"),
            f"{base}/sitemap.xml": (200, "application/xml", root_sitemap),
            f"{base}/sitemap-records-1.xml": (
                200,
                "application/xml",
                child_sitemap,
            ),
            f"{base}/record/9001": (200, "text/html", record),
            f"{base}/record/9002": (200, "text/html", record),
        }

        result = self._run_probe_with_responses(responses)

        self.assertEqual(
            result["gate_assessment"],
            "bounded_public_record_enumeration_confirmed_staged_required",
        )
        self.assertEqual(
            result["discovery_summary"]["sitemap_record_permalinks_discovered"],
            2,
        )
        self.assertTrue(
            result["discovery_summary"][
                "sitemap_sampled_record_semantics_confirmed"
            ]
        )
        self.assertIn(
            f"{base}/sitemap-records-1.xml",
            [row["url"] for row in result["sitemaps"]],
        )
        self.assertTrue(
            all(
                row.get("provenance") == "robots_declared_sitemap"
                for row in result["record_samples"]
            )
        )

    def test_probe_does_not_borrow_semantics_for_invalid_sitemap_records(self):
        base = "https://film.iwmcollections.org.uk"
        robots = """User-agent: *
Allow: /
Sitemap: https://film.iwmcollections.org.uk/sitemap.xml
"""
        root_sitemap = """<sitemapindex>
          <sitemap><loc>https://film.iwmcollections.org.uk/sitemap-records-1.xml</loc></sitemap>
        </sitemapindex>"""
        child_sitemap = """<urlset>
          <url><loc>https://film.iwmcollections.org.uk/record/9001</loc></url>
          <url><loc>https://film.iwmcollections.org.uk/record/9002</loc></url>
        </urlset>"""
        valid_record = """<html><body>
          <h1>Valid film</h1>
          <div>Film Number: IWM 10</div>
          <div>Digitised: Yes</div>
          <div>Production Date: 1941</div>
          <div>Production Country: GB</div>
        </body></html>"""
        invalid_record = "<html><body><h1>Not a film record</h1></body></html>"
        home = """<html><body>
          <a href="/record/100">Home record A</a>
          <a href="/record/101">Home record B</a>
        </body></html>"""
        search = """<html><body>
          <form method="get" action="/search/results"><input name="q"></form>
        </body></html>"""
        responses = {
            f"{base}/robots.txt": (200, "text/plain", robots),
            f"{base}/": (200, "text/html", home),
            f"{base}/search/results": (200, "text/html", search),
            f"{base}/conflict_categories": (200, "text/html", "<html></html>"),
            f"{base}/faqs": (200, "text/html", "<html></html>"),
            f"{base}/sitemap.xml": (200, "application/xml", root_sitemap),
            f"{base}/sitemap-records-1.xml": (
                200,
                "application/xml",
                child_sitemap,
            ),
            f"{base}/record/100": (200, "text/html", valid_record),
            f"{base}/record/101": (200, "text/html", valid_record),
            f"{base}/record/9001": (200, "text/html", invalid_record),
            f"{base}/record/9002": (200, "text/html", invalid_record),
        }

        result = self._run_probe_with_responses(responses)

        self.assertEqual(
            result["gate_assessment"],
            "public_search_surface_confirmed_enumeration_not_yet_validated",
        )
        self.assertFalse(
            result["discovery_summary"][
                "sitemap_sampled_record_semantics_confirmed"
            ]
        )
        self.assertEqual(
            [row["requested_url"] for row in result["record_samples"]],
            [f"{base}/record/9001", f"{base}/record/9002"],
        )
        self.assertNotIn(
            f"{base}/record/100",
            [row["requested_url"] for row in result["record_samples"]],
        )


if __name__ == "__main__":
    unittest.main()
