import unittest

from memoria_audiovisual.jean_vigo_probe import (
    ProbeResponse,
    classify_public_url,
    parse_sitemap,
    parse_surface_html,
    robots_allowed,
    run_jean_vigo_probe,
)


class JeanVigoProbeTests(unittest.TestCase):
    def test_surface_parser_separates_same_host_and_external_archive_links(self):
        html = """
        <html><head><title>Collections</title></head><body>
          <a href="/collections-cinematheque-perpignan-institut-jean-vigo/les-films">Films</a>
          <a href="https://memoirefilmiquedusud.eu/">Mémoire Filmique</a>
          <form action="/" method="get"><input name="s"></form>
        </body></html>
        """
        parsed = parse_surface_html(html, "https://www.inst-jeanvigo.eu/")
        self.assertEqual(parsed["title"], "Collections")
        self.assertEqual(len(parsed["same_host_links"]), 1)
        self.assertIn(
            "https://memoirefilmiquedusud.eu/",
            parsed["external_links"],
        )
        self.assertIn("s", parsed["forms"][0]["input_names"])

    def test_sitemap_parser_keeps_pages_and_nested_sitemaps(self):
        xml = """
        <sitemapindex>
          <sitemap><loc>https://www.inst-jeanvigo.eu/post-sitemap.xml</loc></sitemap>
          <url><loc>https://www.inst-jeanvigo.eu/agenda/example</loc></url>
          <url><loc>https://other.example/record/1</loc></url>
        </sitemapindex>
        """
        parsed = parse_sitemap(xml)
        self.assertEqual(
            parsed["nested_sitemaps"],
            ["https://www.inst-jeanvigo.eu/post-sitemap.xml"],
        )
        self.assertEqual(
            parsed["same_host_pages"],
            ["https://www.inst-jeanvigo.eu/agenda/example"],
        )
        self.assertEqual(len(parsed["rejected_urls"]), 1)

    def test_classification_does_not_treat_agenda_as_collection(self):
        self.assertEqual(
            classify_public_url("https://www.inst-jeanvigo.eu/agenda/film-x"),
            "agenda_or_programming",
        )
        self.assertEqual(
            classify_public_url(
                "https://www.inst-jeanvigo.eu/"
                "collections-cinematheque-perpignan-institut-jean-vigo/les-films"
            ),
            "institutional_collection_page",
        )

    def test_robots_longest_rule_wins(self):
        robots = """
        User-agent: *
        Disallow: /private/
        Allow: /private/public/
        """
        self.assertFalse(
            robots_allowed(
                robots,
                "MemoriaAudiovisualRede",
                "https://www.inst-jeanvigo.eu/private/x",
            )
        )
        self.assertTrue(
            robots_allowed(
                robots,
                "MemoriaAudiovisualRede",
                "https://www.inst-jeanvigo.eu/private/public/x",
            )
        )

    def test_probe_holds_when_robots_is_unverifiable(self):
        class Session:
            def get(self, url, **_kwargs):
                class Response:
                    status_code = 500
                    headers = {"content-type": "text/plain"}
                    text = "error"
                return Response()

        payload = run_jean_vigo_probe(Session())
        self.assertEqual(
            payload["gate_assessment"],
            "hold_robots_unverifiable",
        )

    def test_probe_does_not_promote_agenda_only_sitemap(self):
        robots = "User-agent: *\nAllow: /\nSitemap: https://www.inst-jeanvigo.eu/sitemap.xml\n"
        sitemap = """
        <urlset>
          <url><loc>https://www.inst-jeanvigo.eu/agenda/film-a</loc></url>
          <url><loc>https://www.inst-jeanvigo.eu/agenda/film-b</loc></url>
        </urlset>
        """
        page = """
        <html><body>
          <a href="https://memoirefilmiquedusud.eu/">films amateurs</a>
        </body></html>
        """

        class Session:
            def get(self, url, **_kwargs):
                class Response:
                    status_code = 200
                    headers = {"content-type": "text/html"}
                    text = page
                response = Response()
                if url.endswith("robots.txt"):
                    response.text = robots
                    response.headers = {"content-type": "text/plain"}
                elif url.endswith("sitemap.xml"):
                    response.text = sitemap
                    response.headers = {"content-type": "application/xml"}
                return response

        payload = run_jean_vigo_probe(Session())
        self.assertEqual(
            payload["classification_counts"]["agenda_or_programming"],
            2,
        )
        self.assertNotEqual(
            payload["gate_assessment"],
            "staged_collector_authorized",
        )
        self.assertEqual(
            payload["gate_assessment"],
            "hold_primary_site_points_to_external_archive",
        )


if __name__ == "__main__":
    unittest.main()
