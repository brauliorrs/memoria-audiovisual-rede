"""Contract and failure-path tests for KAVI/Finna research probe (#82)."""
from __future__ import annotations

import json
import unittest

import requests

from memoria_audiovisual.kavi_elonet_probe import (
    API_ROOT, ELONET_FAQ, FACET_QUERY, HOME, SAMPLE_QUERY,
    SURFACES, _build_verified_facet_query, _build_verified_video_query,
    _kavi_building_candidates, _video_format_candidates,
    parse_finna_response, parse_public_page, run_probe,
)


class FakeResponse:
    def __init__(self, *, status=200, text="", mime="text/html",
                 location=None):
        self.status_code = status
        self.text = text
        self.headers = {"content-type": mime}
        if location:
            self.headers["location"] = location
        self.encoding = "utf-8"
        self.closed = False

    def iter_content(self, size):
        raw = self.text.encode("utf-8")
        for index in range(0, len(raw), size):
            yield raw[index:index+size]

    def close(self):
        self.closed = True


class FakeSession:
    def __init__(self, routes):
        self.routes = routes
        self.urls = []

    def get(self, url, **_kwargs):
        self.urls.append(url)
        return self.routes.get(url, FakeResponse(status=404))


class BrokenStream(FakeResponse):
    def iter_content(self, _size):
        raise requests.exceptions.ChunkedEncodingError("stream interrupted")
        yield b""


ROBOTS = "User-agent: *\nAllow: /\n"
BASE_ROUTES = {
    "https://kavi.fi/robots.txt": FakeResponse(
        text=ROBOTS, mime="text/plain",
    ),
    "https://elonet.finna.fi/robots.txt": FakeResponse(
        text=ROBOTS, mime="text/plain",
    ),
    "https://api.finna.fi/robots.txt": FakeResponse(
        text=ROBOTS, mime="text/plain",
    ),
}


def valid_routes():
    items = dict(BASE_ROUTES)
    for _label, url in SURFACES:
        items[url] = FakeResponse(text="<html><title>Elonet</title>"
                                      "<a href='/Content/filmography'>Browse</a></html>")
    items[FACET_QUERY] = FakeResponse(
        mime="application/json", text=json.dumps({
            "status": "OK", "resultCount": 100,
            "facets": {"building": [
                {"value": "0/KAVI/", "translated": "KAVI", "count": 50},
            ]}, "records": [],
        }),
    )
    items[_build_verified_video_query("0/KAVI/", "0/Video/")] = FakeResponse(
        mime="application/json", text=json.dumps({
            "status": "OK", "resultCount": 12490,
            "records": [
                {"id": "kavi.elonet_elokuva_117150", "title": "Test Film",
                 "formats": [{"value": "0/Video/", "translated": "Video"}]},
            ],
        }),
    )
    items[_build_verified_facet_query("0/KAVI/")] = FakeResponse(
        mime="application/json", text=json.dumps({
            "status": "OK", "resultCount": 85,
            "records": [
                {"id": "kavi.elonet_elokuva_117150", "title": "Film"},
            ],
        }),
    )
    items[SAMPLE_QUERY] = FakeResponse(
        mime="application/json", text=json.dumps({
            "status": "OK", "resultCount": 1,
            "records": [{"id": "kavi.elonet_elokuva_test",
                         "title": "Film test",
                         "institutions": [{"value": "KAVI"}],
                         "formats": [{"value": "0/Video/",
                                      "translated": "Video"}]}],
        }),
    )
    return items


class KaviElonetProbeTests(unittest.TestCase):
    def test_metadata_reachable_is_not_catalogue_admission(self):
        session = FakeSession(valid_routes())
        output = run_probe(session)
        self.assertEqual(
            output["gate_assessment"],
            "investigate_kavi_provider_scope_and_batch_enumeration",
        )
        self.assertFalse(output["staged_collector_authorized"])
        self.assertEqual(output["individual_film_records_enumerated"], 0)
        self.assertEqual(output["api_probes"][0]["total_claim"], 100)
        self.assertEqual(
            output["kavi_facet_resolution"], "one_facet_candidate",
        )
        self.assertEqual(
            output["api_probes"][-2]["probe"],
            "verified_building_facet_sample",
        )
        self.assertEqual(output["api_probes"][-2]["total_claim"], 85)
        self.assertEqual(
            output["api_probes"][-1]["probe"], "verified_building_and_video_sample",
        )
        self.assertEqual(output["api_probes"][-1]["total_claim"], 12490)
        self.assertNotIn("resumptionToken", " ".join(session.urls))
        self.assertTrue(all(row["error"] is None for row in output["surfaces"]))

    def test_only_discovered_exact_provider_facet_is_queryable(self):
        facet = [{"value": "0/KAVI/", "translated": "KAVI", "count": 85},
                 {"value": "0/KAVIKIRJASTO/", "translated": "Other", "count": 10},
                 {"value": "0/KUVI/", "translated": "Kuvi", "count": 20}]
        matches = _kavi_building_candidates(facet)
        self.assertEqual([v["value"] for v in matches], ["0/KAVI/", "0/KUVI/"])
        url = _build_verified_facet_query("0/KAVI/")
        self.assertIn("filter%5B%5D=building", url)
        self.assertIn("0%2FKAVI%2F", url)
        with self.assertRaisesRegex(ValueError, "unsafe_facet_code"):
            _build_verified_facet_query('KAVI" OR *')

    def test_video_filter_derives_only_from_observed_metadata(self):
        records = [{"formats": [{"translated": "Video", "value": "0/Video/"},
                                {"translated": "Film", "value": "1/Video/Film/"}]}]
        self.assertEqual(_video_format_candidates(records), ["0/Video/"])
        self.assertEqual(_video_format_candidates([{"formats": []}]), [])
        query = _build_verified_video_query("0/KAVI/", "0/Video/")
        self.assertEqual(query.count("filter%5B%5D="), 2)
        self.assertIn("format", query)
        with self.assertRaisesRegex(ValueError, "unsafe_verified_facet"):
            _build_verified_video_query("0/KAVI/", 'Video"OR*')

    def test_ambiguous_legacy_and_successor_facets_do_not_guess_a_filter(self):
        routes = valid_routes()
        routes[FACET_QUERY] = FakeResponse(
            mime="application/json", text=json.dumps({
                "status": "OK", "resultCount": 120,
                "records": [],
                "facets": {"building": [
                    {"value": "0/KAVI/", "translated": "KAVI", "count": 85},
                    {"value": "0/KUVI/", "translated": "Kuvi", "count": 35},
                ]},
            }),
        )
        session = FakeSession(routes)
        result = run_probe(session)
        self.assertEqual(result["kavi_facet_resolution"], "ambiguous_multiple")
        self.assertEqual(len(result["api_probes"]), 2)
        self.assertFalse(result["staged_collector_authorized"])

    def test_unverifiable_api_robots_fails_closed_without_api_request(self):
        routes = valid_routes()
        routes["https://api.finna.fi/robots.txt"] = FakeResponse(status=403)
        session = FakeSession(routes)
        output = run_probe(session)
        self.assertEqual(output["gate_assessment"], "hold_finna_api_unverifiable")
        self.assertNotIn(FACET_QUERY, session.urls)
        self.assertNotIn(SAMPLE_QUERY, session.urls)

    def test_disallowed_robots_does_not_fetch_catalogue(self):
        routes = valid_routes()
        routes["https://elonet.finna.fi/robots.txt"] = FakeResponse(
            text="User-agent: *\nDisallow: /Content/\n", mime="text/plain",
        )
        session = FakeSession(routes)
        output = run_probe(session)
        self.assertEqual(
            output["gate_assessment"], "hold_required_surface_unverifiable",
        )
        self.assertNotIn(ELONET_FAQ, session.urls)

    def test_cross_host_redirect_requires_independent_robots(self):
        routes = valid_routes()
        routes[HOME] = FakeResponse(
            status=302, location="https://www.kavi.fi/en/film/",
        )
        routes["https://www.kavi.fi/robots.txt"] = FakeResponse(status=403)
        session = FakeSession(routes)
        output = run_probe(session)
        self.assertEqual(
            output["gate_assessment"], "hold_required_surface_unverifiable",
        )
        self.assertNotIn("https://www.kavi.fi/en/film/", session.urls)

    def test_partial_stream_read_is_reported_and_never_promoted(self):
        routes = valid_routes()
        routes[ELONET_FAQ] = BrokenStream(text="<html></html>")
        report = run_probe(FakeSession(routes))
        faq = next(r for r in report["surfaces"]
                   if r["surface"] == "elonet_faq")
        self.assertIn("stream_read_failed", faq["error"])
        self.assertEqual(
            report["gate_assessment"], "hold_required_surface_unverifiable",
        )
        self.assertFalse(report["staged_collector_authorized"])

    def test_non_html_or_browser_challenge_is_not_an_audited_surface(self):
        routes = valid_routes()
        routes[HOME] = FakeResponse(text="OK", mime="text/plain")
        report = run_probe(FakeSession(routes))
        self.assertEqual(
            report["surfaces"][0]["error"], "required_surface_non_html",
        )
        self.assertEqual(
            report["gate_assessment"], "hold_required_surface_unverifiable",
        )
        routes[HOME] = FakeResponse(
            text="<html><title>Just a Moment</title>"
                 "<p>Checking your browser</p></html>",
        )
        report = run_probe(FakeSession(routes))
        self.assertEqual(
            report["surfaces"][0]["error"], "required_surface_browser_challenge",
        )

    def test_finna_duplicate_ids_rejected(self):
        duplicate = json.dumps({
            "status": "OK", "resultCount": 2,
            "records": [{"id": "a"}, {"id": "a"}],
        })
        with self.assertRaisesRegex(ValueError, "duplicate"):
            parse_finna_response(duplicate)

    def test_finna_error_or_html_challenge_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_finna_json"):
            parse_finna_response("<html>challenge</html>")
        with self.assertRaisesRegex(ValueError, "finna_api_not_ok"):
            parse_finna_response('{"status":"ERROR","resultCount":0}')
        with self.assertRaisesRegex(ValueError, "finna_building_facet_missing"):
            parse_finna_response(
                '{"status":"OK","resultCount":0,"records":[],"facets":{}}',
                expect_facets=True,
            )

    def test_html_parser_only_extracts_explicit_origin_links(self):
        parsed = parse_public_page(
            "<html><title>Film</title>"
            "<a href='/Content/filmography'>Browse</a>"
            "<a href='https://outside.example/a'>Other</a></html>",
            ELONET_FAQ,
        )
        self.assertEqual(parsed["title"], "Film")
        self.assertEqual(parsed["same_origin_links_count"], 1)
        self.assertTrue(parsed["same_origin_links_sample"][0].startswith(
            "https://elonet.finna.fi/"
        ))

    def test_only_documented_readonly_api_endpoint_used(self):
        self.assertTrue(FACET_QUERY.startswith(API_ROOT + "?"))
        self.assertTrue(SAMPLE_QUERY.startswith(API_ROOT + "?"))
        self.assertNotIn("filter", SAMPLE_QUERY)
        self.assertNotIn("token", FACET_QUERY)


if __name__ == "__main__":
    unittest.main()
