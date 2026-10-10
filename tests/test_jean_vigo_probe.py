import gzip
import unittest

from memoria_audiovisual.jean_vigo_probe import (
    ProbeResponse,
    audit_collection_pages,
    classify_public_url,
    decode_sitemap_response,
    parse_collection_page_semantics,
    parse_sitemap,
    parse_surface_html,
    resolve_declared_sitemap_url,
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


    def test_gzip_sitemap_body_is_decompressed_before_parsing(self):
        xml = (
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            '<url><loc>https://www.inst-jeanvigo.eu/agenda/example</loc></url>'
            '</urlset>'
        )
        response = ProbeResponse(
            requested_url="https://www.inst-jeanvigo.eu/child.xml.gz",
            final_url="https://www.inst-jeanvigo.eu/child.xml.gz",
            status_code=200,
            content_type="application/gzip",
            text="",
            error=None,
            body=gzip.compress(xml.encode("utf-8")),
        )
        decoded, error = decode_sitemap_response(response)
        self.assertIsNone(error)
        self.assertEqual(decoded, xml)
        parsed = parse_sitemap(decoded or "")
        self.assertFalse(parsed["parse_error"])
        self.assertEqual(
            parsed["same_host_pages"],
            ["https://www.inst-jeanvigo.eu/agenda/example"],
        )

    def test_gzip_sitemap_decompression_is_size_bounded(self):
        response = ProbeResponse(
            requested_url="https://www.inst-jeanvigo.eu/child.xml.gz",
            final_url="https://www.inst-jeanvigo.eu/child.xml.gz",
            status_code=200,
            content_type="application/gzip",
            text="",
            error=None,
            body=gzip.compress(b"x" * 64),
        )
        decoded, error = decode_sitemap_response(
            response,
            max_decompressed_bytes=16,
        )
        self.assertIsNone(decoded)
        self.assertEqual(error, "gzip_decompressed_too_large")

    def test_sitemap_parser_detects_nested_by_xml_structure_not_suffix(self):
        xml = """
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <sitemap>
            <loc>https://www.inst-jeanvigo.eu/sitemap-feed?part=1</loc>
          </sitemap>
          <sitemap>
            <loc>https://www.inst-jeanvigo.eu/post-sitemap.xml.gz</loc>
          </sitemap>
        </sitemapindex>
        """
        parsed = parse_sitemap(xml)
        self.assertEqual(
            parsed["nested_sitemaps"],
            [
                "https://www.inst-jeanvigo.eu/post-sitemap.xml.gz",
                "https://www.inst-jeanvigo.eu/sitemap-feed?part=1",
            ],
        )
        self.assertEqual(parsed["same_host_pages"], [])
        self.assertFalse(parsed["parse_error"])


    def test_sitemap_parser_recovers_malformed_xml_by_container_structure(self):
        xml = """
        <sitemapindex>
          <sitemap>
            <loc>https://inst-jeanvigo.eu/post-sitemap.xml?part=1&lang=fr</loc>
          </sitemap>
          <sitemap>
            <loc>https://inst-jeanvigo.eu/page-sitemap.xml.gz</loc>
          </sitemap>
        </sitemapindex>
        """
        parsed = parse_sitemap(xml)
        self.assertEqual(parsed["parse_mode"], "tolerant_structural")
        self.assertEqual(parsed["root_kind"], "sitemapindex")
        self.assertTrue(parsed["root_valid"])
        self.assertFalse(parsed["parse_error"])
        self.assertEqual(parsed["raw_loc_count"], 2)
        self.assertEqual(parsed["attributed_loc_count"], 2)
        self.assertEqual(parsed["ambiguous_loc_count"], 0)
        self.assertEqual(
            parsed["nested_sitemaps"],
            [
                "https://inst-jeanvigo.eu/page-sitemap.xml.gz",
                "https://inst-jeanvigo.eu/post-sitemap.xml?part=1&lang=fr",
            ],
        )


    def test_nested_http_sitemap_is_preserved_for_transport_validation(self):
        xml = """
        <sitemapindex>
          <sitemap>
            <loc>http://inst-jeanvigo.eu/child-sitemap</loc>
          </sitemap>
        </sitemapindex>
        """
        parsed = parse_sitemap(xml)
        self.assertFalse(parsed["parse_error"])
        self.assertEqual(
            parsed["nested_sitemaps"],
            ["http://inst-jeanvigo.eu/child-sitemap"],
        )
        self.assertEqual(parsed["rejected_urls"], [])

    def test_sitemap_parser_fails_closed_on_unattributed_loc(self):
        xml = """
        <sitemapindex>
          <sitemap>
            <loc>https://inst-jeanvigo.eu/post-sitemap.xml</loc>
          </sitemap>
          <loc>https://inst-jeanvigo.eu/ambiguous</loc>
        </sitemapindex>
        """
        parsed = parse_sitemap(xml)
        self.assertTrue(parsed["parse_error"])
        self.assertEqual(parsed["raw_loc_count"], 2)
        self.assertEqual(parsed["attributed_loc_count"], 1)
        self.assertEqual(parsed["ambiguous_loc_count"], 1)



    def test_sitemap_loc_count_ignores_comment_markup(self):
        xml = """
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <!-- <loc>https://www.inst-jeanvigo.eu/not-a-real-loc</loc> -->
          <url>
            <loc>https://www.inst-jeanvigo.eu/agenda/example</loc>
          </url>
        </urlset>
        """
        parsed = parse_sitemap(xml)
        self.assertFalse(parsed["parse_error"])
        self.assertEqual(parsed["raw_loc_count"], 1)
        self.assertEqual(parsed["attributed_loc_count"], 1)
        self.assertEqual(parsed["ambiguous_loc_count"], 0)

    def test_prefixed_unattributed_loc_is_counted_and_fails_closed(self):
        xml = """
        <sm:sitemapindex xmlns:sm="http://www.sitemaps.org/schemas/sitemap/0.9">
          <sm:sitemap>
            <sm:loc>https://inst-jeanvigo.eu/post-sitemap.xml</sm:loc>
          </sm:sitemap>
          <sm:loc>https://inst-jeanvigo.eu/ambiguous</sm:loc>
        </sm:sitemapindex>
        """
        parsed = parse_sitemap(xml)
        self.assertTrue(parsed["parse_error"])
        self.assertEqual(parsed["raw_loc_count"], 2)
        self.assertEqual(parsed["attributed_loc_count"], 1)
        self.assertEqual(parsed["ambiguous_loc_count"], 1)

    def test_urlset_parser_keeps_pages_and_rejects_external_urls(self):
        xml = """
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://www.inst-jeanvigo.eu/agenda/example</loc></url>
          <url><loc>https://other.example/record/1</loc></url>
        </urlset>
        """
        parsed = parse_sitemap(xml)
        self.assertEqual(
            parsed["same_host_pages"],
            ["https://www.inst-jeanvigo.eu/agenda/example"],
        )
        self.assertEqual(len(parsed["rejected_urls"]), 1)


    def test_sitemap_parser_rejects_html_even_when_loc_tags_exist(self):
        xml = """
        <html><body>
          <div><loc>https://inst-jeanvigo.eu/fake-record</loc></div>
        </body></html>
        """
        parsed = parse_sitemap(xml)
        self.assertTrue(parsed["parse_error"])
        self.assertFalse(parsed["root_valid"])
        self.assertEqual(parsed["same_host_pages"], [])
        self.assertEqual(parsed["nested_sitemaps"], [])


    def test_collection_semantics_requires_archival_identifier_for_confirmation(self):
        html = """
        <html><body><h1>Film X</h1>
          <dl>
            <dt>Réalisation</dt><dd>A. Auteur</dd>
            <dt>Année</dt><dd>1952</dd>
            <dt>Durée</dt><dd>12 min</dd>
          </dl>
        </body></html>
        """
        parsed = parse_collection_page_semantics(
            html,
            "https://www.inst-jeanvigo.eu/"
            "collections-cinematheque-perpignan-institut-jean-vigo/film-x",
        )
        self.assertEqual(
            parsed["semantic_class"],
            "individual_archival_record_candidate",
        )

    def test_collection_semantics_confirms_structured_archival_film_record(self):
        html = """
        <html><body><h1>Film X</h1>
          <table>
            <tr><th>Cote</th><td>JV-42</td></tr>
            <tr><th>Réalisation</th><td>A. Auteur</td></tr>
            <tr><th>Année</th><td>1952</td></tr>
            <tr><th>Durée</th><td>12 min</td></tr>
          </table>
        </body></html>
        """
        parsed = parse_collection_page_semantics(
            html,
            "https://www.inst-jeanvigo.eu/"
            "collections-cinematheque-perpignan-institut-jean-vigo/film-x",
        )
        self.assertEqual(
            parsed["semantic_class"],
            "individual_archival_record_confirmed",
        )
        self.assertIn("cote", parsed["identifier_labels"])

    def test_collection_semantics_distinguishes_hub_and_external_pointer(self):
        hub = """
        <html><body><h1>Collection</h1>
          <a href="/collections-cinematheque-perpignan-institut-jean-vigo/a">A</a>
          <a href="/collections-cinematheque-perpignan-institut-jean-vigo/b">B</a>
          <a href="/collections-cinematheque-perpignan-institut-jean-vigo/c">C</a>
        </body></html>
        """
        parsed = parse_collection_page_semantics(
            hub,
            "https://www.inst-jeanvigo.eu/"
            "collections-cinematheque-perpignan-institut-jean-vigo",
        )
        self.assertEqual(parsed["semantic_class"], "collection_index_or_hub")

        pointer = """
        <html><body><h1>Films amateurs</h1>
          <a href="https://www.memoirefilmiquedusud.eu/">Catalogue</a>
        </body></html>
        """
        parsed = parse_collection_page_semantics(
            pointer,
            "https://www.inst-jeanvigo.eu/"
            "collections-cinematheque-perpignan-institut-jean-vigo/amateur",
        )
        self.assertEqual(parsed["semantic_class"], "external_archive_pointer")

    def test_collection_audit_reports_truncation_instead_of_partial_hold(self):
        class Session:
            def get(self, url, **_kwargs):
                class Response:
                    status_code = 200
                    headers = {"content-type": "text/html"}
                    text = "<html><body><h1>Collection</h1></body></html>"
                    content = text.encode("utf-8")
                return Response()

        urls = [
            "https://www.inst-jeanvigo.eu/"
            f"collections-cinematheque-perpignan-institut-jean-vigo/{index}"
            for index in range(3)
        ]
        reports, truncated = audit_collection_pages(
            Session(),
            urls,
            "User-agent: *\nAllow: /\n",
            max_pages=2,
        )
        self.assertTrue(truncated)
        self.assertEqual(len(reports), 2)

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


    def test_probe_resolves_relative_links_against_final_redirect_url(self):
        robots = "User-agent: *\nAllow: /\n"
        page = '<html><body><a href="record/1">record</a></body></html>'

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
                elif url == "https://www.inst-jeanvigo.eu/":
                    response.status_code = 301
                    response.headers = {"location": "/canonical/"}
                    response.text = ""
                return response

        payload = run_jean_vigo_probe(Session())
        home = payload["surfaces"][0]
        self.assertIn(
            "https://www.inst-jeanvigo.eu/canonical/record/1",
            home["same_host_links"],
        )
        self.assertNotIn(
            "https://www.inst-jeanvigo.eu/record/1",
            home["same_host_links"],
        )


    def test_declared_http_sitemap_only_accepts_same_host_https_redirect(self):
        class Session:
            def get(self, url, **_kwargs):
                class Response:
                    status_code = 301
                    headers = {
                        "location": "https://www.inst-jeanvigo.eu/sitemap_index.xml"
                    }
                    text = "SHOULD NOT BE USED"
                return Response()

        resolved, evidence = resolve_declared_sitemap_url(
            Session(),
            "http://www.inst-jeanvigo.eu/sitemap_index.xml",
        )
        self.assertEqual(
            resolved,
            "https://www.inst-jeanvigo.eu/sitemap_index.xml",
        )
        self.assertEqual(
            evidence["status"],
            "http_redirected_to_authorized_https",
        )


    def test_declared_http_sitemap_accepts_canonical_apex_https_redirect(self):
        class Session:
            def get(self, url, **_kwargs):
                class Response:
                    status_code = 301
                    headers = {
                        "location": "https://inst-jeanvigo.eu/sitemap_index.xml"
                    }
                    text = ""
                return Response()

        resolved, evidence = resolve_declared_sitemap_url(
            Session(),
            "http://www.inst-jeanvigo.eu/sitemap_index.xml",
        )
        self.assertEqual(
            resolved,
            "https://inst-jeanvigo.eu/sitemap_index.xml",
        )
        self.assertEqual(
            evidence["status"],
            "http_redirected_to_authorized_https",
        )

    def test_declared_http_sitemap_rejects_http_content_without_redirect(self):
        class Session:
            def get(self, url, **_kwargs):
                class Response:
                    status_code = 200
                    headers = {"content-type": "application/xml"}
                    text = "<urlset></urlset>"
                return Response()

        resolved, evidence = resolve_declared_sitemap_url(
            Session(),
            "http://www.inst-jeanvigo.eu/sitemap_index.xml",
        )
        self.assertIsNone(resolved)
        self.assertEqual(evidence["status"], "http_content_not_accepted")

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


    def test_probe_advances_to_staged_only_for_complete_confirmed_records(self):
        robots = (
            "User-agent: *\nAllow: /\n"
            "Sitemap: https://www.inst-jeanvigo.eu/sitemap.xml\n"
        )
        record_url = (
            "https://www.inst-jeanvigo.eu/"
            "collections-cinematheque-perpignan-institut-jean-vigo/film-x"
        )
        sitemap = (
            "<urlset><url><loc>"
            + record_url
            + "</loc></url></urlset>"
        )
        record = """
        <html><body><h1>Film X</h1>
          <dl>
            <dt>Cote</dt><dd>JV-1</dd>
            <dt>Réalisation</dt><dd>Auteur</dd>
            <dt>Année</dt><dd>1950</dd>
          </dl>
        </body></html>
        """

        class Session:
            def get(self, url, **_kwargs):
                class Response:
                    status_code = 200
                    headers = {"content-type": "text/html"}
                    text = record
                    content = record.encode("utf-8")

                response = Response()
                if url.endswith("robots.txt"):
                    response.text = robots
                    response.content = robots.encode("utf-8")
                    response.headers = {"content-type": "text/plain"}
                elif url.endswith("sitemap.xml"):
                    response.text = sitemap
                    response.content = sitemap.encode("utf-8")
                    response.headers = {"content-type": "application/xml"}
                return response

        payload = run_jean_vigo_probe(Session())
        self.assertEqual(
            payload["gate_assessment"],
            "bounded_public_record_enumeration_confirmed_staged_required",
        )
        self.assertEqual(
            payload["collection_semantic_counts"][
                "individual_archival_record_confirmed"
            ],
            1,
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
