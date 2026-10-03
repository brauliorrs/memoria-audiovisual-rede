import unittest

from memoria_audiovisual.iwm_film_probe import (
    IWM_FILM_SEARCH_URL,
    parse_record_html,
    parse_script_hints,
    parse_surface_html,
    robots_allowed,
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


if __name__ == "__main__":
    unittest.main()
