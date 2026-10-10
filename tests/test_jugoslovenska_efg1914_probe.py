"""Fail-closed regression tests for subordinate Jugoslovenska EFG1914 probe."""
import unittest

from memoria_audiovisual.jugoslovenska_efg1914_probe import (
    EFG1914,
    parse_efg1914_facet,
    run_efg1914_probe,
)


class Response:
    def __init__(self, status=200, text="", headers=None):
        self.status_code = status
        self.text = text
        self.headers = headers or {"content-type": "text/html"}


class Session:
    def __init__(self, mapping):
        self.mapping = mapping
        self.visited = []

    def get(self, url, **_kwargs):
        self.visited.append(url)
        return self.mapping.get(url, Response(status=404))


class JugoslovenskaEfgProbeTests(unittest.TestCase):
    def test_facet_count_is_not_a_record_enumeration(self):
        html = (
            "<html><body>"
            "<label>Jugoslovenska Kinoteka (67)</label>"
            '<a href="/detail/example">Other provider item</a>'
            "</body></html>"
        )
        parsed = parse_efg1914_facet(html, EFG1914)
        self.assertTrue(parsed["provider_facet_visible"])
        self.assertEqual(parsed["provider_facet_count"], 67)
        self.assertEqual(parsed["provider_links_discovered"], [])
        result = run_efg1914_probe(Session({
            "https://www.europeanfilmgateway.eu/robots.txt": Response(
                status=200, text="User-agent: *\nAllow: /\n",
            ),
            EFG1914: Response(status=200, text=html),
        }))
        self.assertEqual(result["provider_facet_count"], 67)
        self.assertEqual(result["records_enumerated"], 0)
        self.assertFalse(result["staged_collector_authorized"])
        self.assertEqual(
            result["gate_assessment"], "hold_no_reproducible_provider_enumeration",
        )

    def test_access_denied_is_hold_not_retry_or_bypass(self):
        s = Session({
            "https://www.europeanfilmgateway.eu/robots.txt": Response(
                status=200, text="User-agent: *\nAllow: /\n",
            ),
            EFG1914: Response(status=403, text="Forbidden"),
        })
        result = run_efg1914_probe(s)
        self.assertEqual(result["gate_assessment"], "hold_access_blocked")
        self.assertEqual(s.visited.count(EFG1914), 1)

    def test_browser_validation_redirect_is_never_followed(self):
        s = Session({
            "https://www.europeanfilmgateway.eu/robots.txt": Response(
                status=200, text="User-agent: *\nAllow: /\n",
            ),
            EFG1914: Response(
                status=302, headers={
                    "location": "/validate-browser", "content-type": "text/html",
                },
            ),
        })
        result = run_efg1914_probe(s)
        self.assertEqual(result["gate_assessment"], "hold_browser_challenge")
        self.assertFalse(any("validate-browser" in url for url in s.visited))

    def test_robots_unverifiable_prevents_fetching_any_efg_page(self):
        s = Session({
            "https://www.europeanfilmgateway.eu/robots.txt": Response(
                status=403, text="Forbidden",
            ),
        })
        result = run_efg1914_probe(s)
        self.assertEqual(result["gate_assessment"], "hold_robots_unverifiable")
        self.assertNotIn(EFG1914, s.visited)

    def test_explicit_facet_link_is_candidate_only(self):
        html = (
            "<html><body>"
            "<a href='/search-efg/explicit-filter'>"
            "Jugoslovenska Kinoteka (67)</a>"
            "</body></html>"
        )
        result = run_efg1914_probe(Session({
            "https://www.europeanfilmgateway.eu/robots.txt": Response(
                status=200, text="User-agent: *\nAllow: /\n",
            ),
            EFG1914: Response(status=200, text=html),
        }))
        self.assertEqual(
            result["gate_assessment"], "investigate_explicit_provider_filter_link",
        )
        self.assertEqual(result["records_enumerated"], 0)
        self.assertFalse(result["staged_collector_authorized"])


if __name__ == "__main__":
    unittest.main()
