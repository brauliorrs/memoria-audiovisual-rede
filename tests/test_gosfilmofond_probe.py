import json
import unittest

from memoria_audiovisual.gosfilmofond_probe import (
    GOSFILMOFOND_AJAX_URL,
    GOSFILMOFOND_CATALOG_URL,
    GOSFILMOFOND_HOME_URL,
    GOSFILMOFOND_REST_ROOT,
    GOSFILMOFOND_ROBOTS_URL,
    GOSFILMOFOND_SITEMAP_CANDIDATES,
    parse_ajax_response,
    parse_catalog_html,
    parse_sitemap_xml,
    robots_allowed_rfc9309,
    run_gosfilmofond_probe,
    summarize_rest_root,
)


CATALOG_HTML = """
<html>
<head>
<title>Каталог фильмов</title>
<script src="/wp-content/themes/gff/catalog.js"></script>
<script>
var ajaxurl = '/wp-admin/admin-ajax.php';
var config = {action: 'load_more_films', paged: 1};
</script>
</head>
<body>
<form action="/films/" method="get">
  <input name="search" value="">
  <input name="year" value="">
  <select name="genre"><option value="">all</option></select>
</form>
<a href="/films/240363/">ФОНТАН</a>
<a href="/films/240658/">ГОСПОДИН ОФОРМИТЕЛЬ</a>
<a class="next page-numbers" href="/films/page/2/">Далее</a>
<div class="page-count"><select><option value="10">10</option><option value="50">50</option></select></div>
<div data-action="filter-films" data-page="2"></div>
</body>
</html>
"""

SITEMAP_XML = """<?xml version="1.0"?>
<urlset>
  <url><loc>https://gosfilmofond.ru/films/240363/</loc></url>
  <url><loc>https://gosfilmofond.ru/films/240658/</loc></url>
  <url><loc>https://gosfilmofond.ru/news/example/</loc></url>
</urlset>
"""

SITEMAP_INDEX_XML = """<?xml version="1.0"?>
<sitemapindex>
  <sitemap><loc>https://gosfilmofond.ru/post-sitemap.xml</loc></sitemap>
  <sitemap><loc>https://gosfilmofond.ru/films-sitemap.xml</loc></sitemap>
</sitemapindex>
"""

REST_JSON = json.dumps(
    {
        "namespaces": ["wp/v2", "gff/v1"],
        "routes": {
            "/wp/v2/posts": {},
            "/gff/v1/films": {},
            "/gff/v1/film-search": {},
        },
    }
)

ROBOTS = """User-agent: *
Allow: /
"""

QUERY_ROBOTS = """User-agent: *
Disallow: /wp-
Disallow: /?
Disallow: /*?
Disallow: /&
Disallow: /*&
Disallow: /page/
Allow: /wp-admin/admin-ajax.php
"""


class FakeResponse:
    def __init__(self, url, text="", status_code=200, content_type="text/html"):
        self.url = url
        self.text = text
        self.status_code = status_code
        self.headers = {"content-type": content_type}


class FakeSession:
    def __init__(self, responses, post_responses=None):
        self.responses = responses
        self.post_responses = post_responses or {}
        self.headers = {"User-Agent": "MAR-Test-Agent"}

    def get(self, url, **_kwargs):
        if url not in self.responses:
            return FakeResponse(url, "", 404)
        return self.responses[url]

    def post(self, url, data=None, **_kwargs):
        key = (url, str((data or {}).get("paged", "")))
        if key in self.post_responses:
            return self.post_responses[key]
        if url in self.post_responses:
            return self.post_responses[url]
        return FakeResponse(url, "", 404)


class GosfilmofondProbeTests(unittest.TestCase):
    def test_catalog_parser_detects_links_forms_pagination_and_ajax_hints(self):
        parsed = parse_catalog_html(CATALOG_HTML, GOSFILMOFOND_CATALOG_URL)
        self.assertEqual(parsed["film_links_count"], 2)
        self.assertEqual(
            [row["record_key"] for row in parsed["film_links"]],
            ["240363", "240658"],
        )
        self.assertTrue(
            any("/films/page/2/" in url for url in parsed["pagination_links"])
        )
        self.assertEqual(parsed["forms"][0]["method"], "get")
        names = {
            control["name"]
            for control in parsed["forms"][0]["controls"]
        }
        self.assertTrue({"search", "year", "genre"}.issubset(names))
        self.assertTrue(parsed["inline_discovery"])
        self.assertTrue(parsed["data_hints"])
        self.assertEqual(parsed["page_count_options"], [10, 50])

    def test_sitemap_parser_separates_film_urls_and_nested_sitemaps(self):
        parsed = parse_sitemap_xml(SITEMAP_XML)
        self.assertEqual(parsed["url_count"], 3)
        self.assertEqual(parsed["film_url_count"], 2)
        self.assertEqual(len(parsed["film_url_samples"]), 2)

        nested = parse_sitemap_xml(SITEMAP_INDEX_XML)
        self.assertEqual(nested["film_url_count"], 0)
        self.assertEqual(len(nested["nested_sitemaps"]), 2)

    def test_rest_summary_identifies_catalog_candidate_routes(self):
        parsed = summarize_rest_root(REST_JSON)
        self.assertTrue(parsed["json"])
        self.assertEqual(parsed["routes_count"], 3)
        self.assertEqual(
            parsed["candidate_routes"],
            ["/gff/v1/film-search", "/gff/v1/films"],
        )

    def test_ajax_response_parser_extracts_public_film_links(self):
        html = """
        <div id="films-list">
          <a href="/films/240363/">Film A</a>
          <a href="/films/240658/">Film B</a>
          <a class="page-numbers" data-page="2">2</a>
        </div>
        """
        parsed = parse_ajax_response(
            json.dumps({"success": True, "data": {"html": html, "total": 60000}}),
            GOSFILMOFOND_AJAX_URL,
        )
        self.assertTrue(parsed["json"])
        self.assertEqual(parsed["film_links_count"], 2)
        self.assertEqual(
            [row["record_key"] for row in parsed["film_links"]],
            ["240363", "240658"],
        )

    def test_live_probe_contract_is_non_invasive_and_never_authorizes_inclusion(self):
        responses = {
            GOSFILMOFOND_ROBOTS_URL: FakeResponse(
                GOSFILMOFOND_ROBOTS_URL,
                ROBOTS,
                200,
                "text/plain",
            ),
            GOSFILMOFOND_HOME_URL: FakeResponse(
                GOSFILMOFOND_HOME_URL,
                "<html><body>home</body></html>",
            ),
            GOSFILMOFOND_CATALOG_URL: FakeResponse(
                GOSFILMOFOND_CATALOG_URL,
                CATALOG_HTML,
            ),
            GOSFILMOFOND_AJAX_URL: FakeResponse(
                GOSFILMOFOND_AJAX_URL,
                "",
                200,
                "text/html",
            ),
            GOSFILMOFOND_REST_ROOT: FakeResponse(
                GOSFILMOFOND_REST_ROOT,
                REST_JSON,
                200,
                "application/json",
            ),
            GOSFILMOFOND_SITEMAP_CANDIDATES[0]: FakeResponse(
                GOSFILMOFOND_SITEMAP_CANDIDATES[0],
                SITEMAP_INDEX_XML,
                200,
                "application/xml",
            ),
            GOSFILMOFOND_SITEMAP_CANDIDATES[1]: FakeResponse(
                GOSFILMOFOND_SITEMAP_CANDIDATES[1],
                SITEMAP_XML,
                200,
                "application/xml",
            ),
            GOSFILMOFOND_SITEMAP_CANDIDATES[2]: FakeResponse(
                GOSFILMOFOND_SITEMAP_CANDIDATES[2],
                "",
                404,
                "text/plain",
            ),
        }
        post_responses = {
            (GOSFILMOFOND_AJAX_URL, "1"): FakeResponse(
                GOSFILMOFOND_AJAX_URL,
                "<div><a href=\"/films/100/\">One</a><a href=\"/films/101/\">Two</a></div>",
                200,
                "text/html",
            ),
            (GOSFILMOFOND_AJAX_URL, "2"): FakeResponse(
                GOSFILMOFOND_AJAX_URL,
                "<div><a href=\"/films/102/\">Three</a><a href=\"/films/103/\">Four</a></div>",
                200,
                "text/html",
            ),
        }
        payload = run_gosfilmofond_probe(
            session=FakeSession(responses, post_responses=post_responses)
        )
        self.assertFalse(payload["automatic_incorporation_authorized"])
        self.assertFalse(payload["brute_force_id_scan_performed"])
        self.assertFalse(payload["experimental_model_used"])
        self.assertEqual(payload["robots"]["mode"], "evaluated_rfc9309")
        self.assertIn(
            "sitemap_film_urls",
            payload["enumeration_mechanisms"],
        )
        self.assertIn(
            "wordpress_rest_candidate_routes",
            payload["enumeration_mechanisms"],
        )
        self.assertEqual(payload["ajax_probe"]["page_count"], 50)
        self.assertEqual(
            payload["ajax_probe"]["declared_page_count_options"],
            [10, 50],
        )
        self.assertTrue(
            payload["ajax_probe"]["reproducible_pagination_candidate"]
        )
        self.assertEqual(payload["ajax_probe"]["unique_records_observed"], 4)
        self.assertIn(
            "allowed_ajax_reproducible_pagination",
            payload["enumeration_mechanisms"],
        )
        self.assertEqual(
            payload["gate_assessment"],
            "ajax_pagination_validated_for_bounded_collector_engineering",
        )

    def test_rfc9309_matcher_does_not_collapse_query_rules_to_root(self):
        self.assertTrue(
            robots_allowed_rfc9309(
                QUERY_ROBOTS,
                "MAR-Test-Agent",
                "https://gosfilmofond.ru/",
            )
        )
        self.assertTrue(
            robots_allowed_rfc9309(
                QUERY_ROBOTS,
                "MAR-Test-Agent",
                "https://gosfilmofond.ru/films/",
            )
        )
        self.assertFalse(
            robots_allowed_rfc9309(
                QUERY_ROBOTS,
                "MAR-Test-Agent",
                "https://gosfilmofond.ru/films/?year=1988",
            )
        )
        self.assertFalse(
            robots_allowed_rfc9309(
                QUERY_ROBOTS,
                "MAR-Test-Agent",
                "https://gosfilmofond.ru/wp-json/",
            )
        )
        self.assertTrue(
            robots_allowed_rfc9309(
                QUERY_ROBOTS,
                "MAR-Test-Agent",
                "https://gosfilmofond.ru/wp-admin/admin-ajax.php",
            )
        )
        self.assertFalse(
            robots_allowed_rfc9309(
                QUERY_ROBOTS,
                "MAR-Test-Agent",
                "https://gosfilmofond.ru/page/2/",
            )
        )

    def test_unverifiable_robots_holds_without_catalog_fetch(self):
        responses = {
            GOSFILMOFOND_ROBOTS_URL: FakeResponse(
                GOSFILMOFOND_ROBOTS_URL,
                "",
                503,
                "text/plain",
            )
        }
        payload = run_gosfilmofond_probe(session=FakeSession(responses))
        self.assertEqual(
            payload["gate_assessment"],
            "hold_robots_not_allowed_or_unverifiable",
        )
        self.assertIsNone(payload["catalog"])
        self.assertFalse(payload["automatic_incorporation_authorized"])


if __name__ == "__main__":
    unittest.main()
