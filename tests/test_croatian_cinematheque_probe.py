import unittest

from memoria_audiovisual.croatian_cinematheque_probe import (
    HAIS_HOME_URL,
    HAIS_ROBOTS_URL,
    HDA_FILM_HOLDINGS_URL,
    HDA_HOME_URL,
    HDA_KINOTEKA_URL,
    HDA_ROBOTS_URL,
    parse_surface_html,
    robots_allowed,
    run_croatian_cinematheque_probe,
)


ROBOTS_ALLOW = "User-agent: *\nAllow: /\n"
HAIS_HTML = """
<html>
  <head><title>HAIS</title></head>
  <body>
    <form action="/HDA/trazilica" method="get">
      <input name="pojam" />
      <select name="arhiv"><option value="HDA">HDA</option></select>
      <input type="checkbox" name="digitalniSadrzaj" value="true" />
      <button>Traži</button>
    </form>
    <a href="/HDA/trazilica/arhivsko-gradivo/abc">Record</a>
    <script>const apiHint = "/api/search";</script>
  </body>
</html>
"""


class FakeResponse:
    def __init__(self, url, text="", status_code=200, content_type="text/html"):
        self.url = url
        self.text = text
        self.status_code = status_code
        self.headers = {"content-type": content_type}


class FakeSession:
    def __init__(self, responses):
        self.responses = responses
        self.headers = {"User-Agent": "MemoriaAudiovisualRede/1.0"}

    def get(self, url, **_kwargs):
        return self.responses.get(url, FakeResponse(url, "", 404, "text/plain"))


class CroatianCinemathequeProbeTests(unittest.TestCase):
    def test_surface_parser_extracts_search_contract(self):
        parsed = parse_surface_html(HAIS_HTML, HAIS_HOME_URL)
        self.assertEqual(parsed["title"], "HAIS")
        self.assertEqual(len(parsed["forms"]), 1)
        self.assertEqual(parsed["forms"][0]["method"], "get")
        self.assertIn("/HDA/trazilica", parsed["forms"][0]["action"])
        self.assertEqual(len(parsed["discovery_links"]), 1)
        self.assertTrue(parsed["inline_hints"])

    def test_robots_query_and_specificity(self):
        robots = """User-agent: *
Disallow: /HDA/
Allow: /HDA/trazilica/
"""
        self.assertTrue(
            robots_allowed(
                robots,
                "MemoriaAudiovisualRede",
                "https://hais.arhiv.hr/HDA/trazilica/",
            )
        )
        self.assertFalse(
            robots_allowed(
                robots,
                "MemoriaAudiovisualRede",
                "https://hais.arhiv.hr/HDA/admin/",
            )
        )

    def test_invalid_robots_payload_fails_closed(self):
        responses = {
            HDA_ROBOTS_URL: FakeResponse(HDA_ROBOTS_URL, ROBOTS_ALLOW, 200, "text/plain"),
            HAIS_ROBOTS_URL: FakeResponse(
                HAIS_ROBOTS_URL,
                "<html>gateway</html>",
                200,
                "text/html",
            ),
        }
        payload = run_croatian_cinematheque_probe(session=FakeSession(responses))
        self.assertEqual(
            payload["gate_assessment"],
            "hold_robots_not_allowed_or_unverifiable",
        )
        self.assertFalse(payload["automatic_incorporation_authorized"])

    def test_public_hais_form_advances_only_to_bounded_probe(self):
        responses = {
            HDA_ROBOTS_URL: FakeResponse(HDA_ROBOTS_URL, ROBOTS_ALLOW, 200, "text/plain"),
            HAIS_ROBOTS_URL: FakeResponse(HAIS_ROBOTS_URL, ROBOTS_ALLOW, 200, "text/plain"),
            HDA_HOME_URL: FakeResponse(HDA_HOME_URL, "<html><body>HDA</body></html>"),
            HDA_KINOTEKA_URL: FakeResponse(
                HDA_KINOTEKA_URL,
                "<html><body>Hrvatska kinoteka</body></html>",
            ),
            HDA_FILM_HOLDINGS_URL: FakeResponse(
                HDA_FILM_HOLDINGS_URL,
                "<html><body>Filmsko gradivo</body></html>",
            ),
            HAIS_HOME_URL: FakeResponse(HAIS_HOME_URL, HAIS_HTML),
        }
        payload = run_croatian_cinematheque_probe(session=FakeSession(responses))
        self.assertEqual(
            payload["gate_assessment"],
            "public_search_surface_confirmed_enumeration_not_yet_validated",
        )
        self.assertIn(
            "hais_public_search_form",
            payload["enumeration_mechanisms"],
        )
        self.assertEqual(payload["next_action"], "engineer_bounded_hais_search_probe")
        self.assertFalse(payload["automatic_incorporation_authorized"])
        self.assertFalse(payload["brute_force_id_scan_performed"])
        self.assertFalse(payload["media_download_performed"])
        self.assertEqual(payload["custodial_title_count_context_only"], 15000)


    def test_hda_robots_outage_does_not_block_permitted_hais_search(self):
        responses = {
            HDA_ROBOTS_URL: FakeResponse(HDA_ROBOTS_URL, "", 503, "text/plain"),
            HAIS_ROBOTS_URL: FakeResponse(HAIS_ROBOTS_URL, ROBOTS_ALLOW, 200, "text/plain"),
            HAIS_HOME_URL: FakeResponse(HAIS_HOME_URL, HAIS_HTML),
        }
        payload = run_croatian_cinematheque_probe(session=FakeSession(responses))
        self.assertEqual(
            payload["gate_assessment"],
            "public_search_surface_confirmed_enumeration_not_yet_validated",
        )

    def test_unrelated_hais_form_does_not_confirm_search_surface(self):
        unrelated = """
        <html><body>
          <form action="/login" method="post">
            <input name="username" />
            <button>Login</button>
          </form>
          <a href="/page/video-help">Help page</a>
        </body></html>
        """
        responses = {
            HDA_ROBOTS_URL: FakeResponse(HDA_ROBOTS_URL, ROBOTS_ALLOW, 200, "text/plain"),
            HAIS_ROBOTS_URL: FakeResponse(HAIS_ROBOTS_URL, ROBOTS_ALLOW, 200, "text/plain"),
            HDA_HOME_URL: FakeResponse(HDA_HOME_URL, "<html><body>HDA</body></html>"),
            HDA_KINOTEKA_URL: FakeResponse(HDA_KINOTEKA_URL, "<html><body>Kinoteka</body></html>"),
            HDA_FILM_HOLDINGS_URL: FakeResponse(HDA_FILM_HOLDINGS_URL, "<html><body>Films</body></html>"),
            HAIS_HOME_URL: FakeResponse(HAIS_HOME_URL, unrelated),
        }
        payload = run_croatian_cinematheque_probe(session=FakeSession(responses))
        self.assertEqual(
            payload["gate_assessment"],
            "hold_no_reproducible_enumeration_surface_detected",
        )
        self.assertNotIn("hais_public_search_form", payload["enumeration_mechanisms"])
        self.assertNotIn("hais_internal_search_routes", payload["enumeration_mechanisms"])


if __name__ == "__main__":
    unittest.main()
