import json
import unittest

from memoria_audiovisual.ifi_archive_player_probe import (
    IFI_PLAYER_BROWSE_URL,
    IFI_PLAYER_COLLECTIONS_URL,
    IFI_PLAYER_HOME_URL,
    IFI_PLAYER_REST_ROOT,
    IFI_PLAYER_ROBOTS_URL,
    parse_sitemap,
    parse_surface_html,
    robots_allowed,
    run_ifi_archive_player_probe,
)


ROBOTS_ALLOW = "User-agent: *\nAllow: /\n"
BROWSE_HTML = """
<html><head><title>Browse</title></head><body>
<form action="/" method="get">
  <input name="s" placeholder="Search ..." />
  <button>Search</button>
</form>
<a class="film-card" href="/keep-watching-the-skies/">Keep Watching the Skies</a>
<a class="film-card" href="/another-film/">Another Film</a>
<a class="next page-numbers" href="/browse/page/2/">Next</a>
<a href="/legal/">Legal</a>
</body></html>
"""
REST_JSON = json.dumps(
    {
        "namespaces": ["wp/v2"],
        "routes": {
            "/wp/v2/posts": {},
            "/wp/v2/search": {},
            "/wp/v2/types": {},
        },
    }
)


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
        return self.responses.get(
            url,
            FakeResponse(url, "", 404, "text/plain"),
        )


class IfiArchivePlayerProbeTests(unittest.TestCase):
    def test_surface_parser_distinguishes_films_from_editorial_pages(self):
        parsed = parse_surface_html(BROWSE_HTML, IFI_PLAYER_BROWSE_URL)
        self.assertEqual(parsed["title"], "Browse")
        self.assertEqual(parsed["film_links_count"], 2)
        self.assertEqual(
            [row["url"] for row in parsed["film_links"]],
            [
                "https://ifiarchiveplayer.ie/keep-watching-the-skies/",
                "https://ifiarchiveplayer.ie/another-film/",
            ],
        )
        self.assertEqual(len(parsed["search_forms"]), 1)
        self.assertEqual(
            parsed["pagination_links"],
            ["https://ifiarchiveplayer.ie/browse/page/2/"],
        )

    def test_robots_longest_match_semantics(self):
        robots = """User-agent: *
Disallow: /browse/
Allow: /browse/public/
"""
        self.assertFalse(
            robots_allowed(
                robots,
                "MemoriaAudiovisualRede",
                "https://ifiarchiveplayer.ie/browse/",
            )
        )
        self.assertTrue(
            robots_allowed(
                robots,
                "MemoriaAudiovisualRede",
                "https://ifiarchiveplayer.ie/browse/public/",
            )
        )

    def test_invalid_robots_fails_closed_without_browse_fetch(self):
        responses = {
            IFI_PLAYER_ROBOTS_URL: FakeResponse(
                IFI_PLAYER_ROBOTS_URL,
                "<html>challenge</html>",
                200,
                "text/html",
            )
        }
        payload = run_ifi_archive_player_probe(
            session=FakeSession(responses)
        )
        self.assertEqual(
            payload["gate_assessment"],
            "hold_robots_not_allowed_or_unverifiable",
        )
        self.assertFalse(payload["automatic_incorporation_authorized"])
        self.assertFalse(payload["media_download_performed"])

    def test_realistic_browse_contract_advances_only_to_bounded_probe(self):
        responses = {
            IFI_PLAYER_ROBOTS_URL: FakeResponse(
                IFI_PLAYER_ROBOTS_URL,
                ROBOTS_ALLOW,
                200,
                "text/plain",
            ),
            IFI_PLAYER_HOME_URL: FakeResponse(
                IFI_PLAYER_HOME_URL,
                "<html><body>Home</body></html>",
            ),
            IFI_PLAYER_BROWSE_URL: FakeResponse(
                IFI_PLAYER_BROWSE_URL,
                BROWSE_HTML,
            ),
            IFI_PLAYER_COLLECTIONS_URL: FakeResponse(
                IFI_PLAYER_COLLECTIONS_URL,
                "<html><body>Collections</body></html>",
            ),
            IFI_PLAYER_REST_ROOT: FakeResponse(
                IFI_PLAYER_REST_ROOT,
                REST_JSON,
                200,
                "application/json",
            ),
        }
        payload = run_ifi_archive_player_probe(
            session=FakeSession(responses)
        )
        self.assertEqual(
            payload["gate_assessment"],
            "public_enumeration_candidate_detected_bounded_probe_required",
        )
        self.assertIn(
            "browse_public_film_permalink_candidates",
            payload["enumeration_mechanisms"],
        )
        self.assertIn(
            "browse_public_search_form",
            payload["enumeration_mechanisms"],
        )
        self.assertIn(
            "browse_pagination_links",
            payload["enumeration_mechanisms"],
        )
        self.assertEqual(
            payload["next_action"],
            "engineer_bounded_two_page_or_partition_probe",
        )
        self.assertFalse(payload["automatic_incorporation_authorized"])
        self.assertFalse(payload["brute_force_id_scan_performed"])
        self.assertFalse(payload["media_download_performed"])

    def test_links_without_enumeration_mechanism_do_not_advance(self):
        html = """
        <html><body>
          <a href="/film-one/">Film one</a>
          <a href="/film-two/">Film two</a>
        </body></html>
        """
        responses = {
            IFI_PLAYER_ROBOTS_URL: FakeResponse(
                IFI_PLAYER_ROBOTS_URL,
                ROBOTS_ALLOW,
                200,
                "text/plain",
            ),
            IFI_PLAYER_HOME_URL: FakeResponse(
                IFI_PLAYER_HOME_URL,
                "<html><body>Home</body></html>",
            ),
            IFI_PLAYER_BROWSE_URL: FakeResponse(
                IFI_PLAYER_BROWSE_URL,
                html,
            ),
            IFI_PLAYER_COLLECTIONS_URL: FakeResponse(
                IFI_PLAYER_COLLECTIONS_URL,
                "<html><body>Collections</body></html>",
            ),
        }
        payload = run_ifi_archive_player_probe(
            session=FakeSession(responses)
        )
        self.assertEqual(
            payload["gate_assessment"],
            "hold_no_reproducible_enumeration_candidate_detected",
        )


    def test_sitemap_index_xml_is_not_misclassified_as_film(self):
        parsed = parse_sitemap(
            """<sitemapindex>
            <sitemap><loc>https://ifiarchiveplayer.ie/post-sitemap.xml</loc></sitemap>
            <sitemap><loc>https://ifiarchiveplayer.ie/post-sitemap2.xml</loc></sitemap>
            </sitemapindex>"""
        )
        self.assertEqual(parsed["film_candidate_count"], 0)
        self.assertEqual(len(parsed["nested_sitemaps"]), 2)

    def test_two_post_sitemaps_validate_bounded_enumeration(self):
        index_xml = """<sitemapindex>
          <sitemap><loc>https://ifiarchiveplayer.ie/post-sitemap.xml</loc></sitemap>
          <sitemap><loc>https://ifiarchiveplayer.ie/post-sitemap2.xml</loc></sitemap>
        </sitemapindex>"""
        shard1 = """<urlset>
          <url><loc>https://ifiarchiveplayer.ie/film-a/</loc></url>
          <url><loc>https://ifiarchiveplayer.ie/film-b/</loc></url>
        </urlset>"""
        shard2 = """<urlset>
          <url><loc>https://ifiarchiveplayer.ie/film-c/</loc></url>
          <url><loc>https://ifiarchiveplayer.ie/film-d/</loc></url>
        </urlset>"""
        detail = """<html><body><h1>Film</h1>
          <p>Category: Documentary</p><p>Year: 1975</p>
          <p>Duration: 10 mins</p>
        </body></html>"""
        responses = {
            IFI_PLAYER_ROBOTS_URL: FakeResponse(
                IFI_PLAYER_ROBOTS_URL, ROBOTS_ALLOW, 200, "text/plain"
            ),
            IFI_PLAYER_HOME_URL: FakeResponse(
                IFI_PLAYER_HOME_URL, "<html><body>Home</body></html>"
            ),
            IFI_PLAYER_BROWSE_URL: FakeResponse(
                IFI_PLAYER_BROWSE_URL, BROWSE_HTML
            ),
            IFI_PLAYER_COLLECTIONS_URL: FakeResponse(
                IFI_PLAYER_COLLECTIONS_URL, "<html><body>Collections</body></html>"
            ),
            "https://ifiarchiveplayer.ie/wp-sitemap.xml": FakeResponse(
                "https://ifiarchiveplayer.ie/wp-sitemap.xml", index_xml, 200, "text/xml"
            ),
            "https://ifiarchiveplayer.ie/sitemap_index.xml": FakeResponse(
                "https://ifiarchiveplayer.ie/sitemap_index.xml", index_xml, 200, "text/xml"
            ),
            "https://ifiarchiveplayer.ie/sitemap.xml": FakeResponse(
                "https://ifiarchiveplayer.ie/sitemap.xml", index_xml, 200, "text/xml"
            ),
            "https://ifiarchiveplayer.ie/post-sitemap.xml": FakeResponse(
                "https://ifiarchiveplayer.ie/post-sitemap.xml", shard1, 200, "text/xml"
            ),
            "https://ifiarchiveplayer.ie/post-sitemap2.xml": FakeResponse(
                "https://ifiarchiveplayer.ie/post-sitemap2.xml", shard2, 200, "text/xml"
            ),
            "https://ifiarchiveplayer.ie/film-a/": FakeResponse(
                "https://ifiarchiveplayer.ie/film-a/", detail
            ),
            "https://ifiarchiveplayer.ie/film-c/": FakeResponse(
                "https://ifiarchiveplayer.ie/film-c/", detail
            ),
        }
        payload = run_ifi_archive_player_probe(session=FakeSession(responses))
        self.assertEqual(
            payload["gate_assessment"],
            "bounded_post_sitemap_enumeration_validated_for_collector_engineering",
        )
        bounded = payload["bounded_post_sitemap_probe"]
        self.assertTrue(bounded["reproducible_bounded_enumeration"])
        self.assertTrue(bounded["all_discovered_post_sitemaps_covered"])
        self.assertEqual(bounded["unique_film_permalink_candidates"], 4)
        self.assertEqual(
            payload["next_action"],
            "engineer_staged_collector_from_post_sitemaps",
        )


if __name__ == "__main__":
    unittest.main()
