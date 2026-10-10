import unittest

from memoria_audiovisual.memoire_filmique_probe import (
    ProbeResponse,
    _deterministic_sample,
    parse_collection_page,
    parse_item_page,
    robots_allowed,
    run_memoire_filmique_probe,
)


class MemoireFilmiqueProbeTests(unittest.TestCase):
    def test_collection_parser_discovers_items_pagination_and_total(self):
        html = """
        <html><body>
          <p>Votre recherche a retourné 3 résultat(s)</p>
          <a href="/collection/item/10-film-a?offset=1">A</a>
          <a href="/collection/item/11-film-b">B</a>
          <a href="/collection?page=2&perpage=2&search=">Next</a>
          <select name="refine[archive][]">
            <option value="Institut Jean Vigo">Institut Jean Vigo</option>
          </select>
        </body></html>
        """
        parsed = parse_collection_page(
            html,
            "https://www.memoirefilmiquedusud.eu/collection",
        )
        self.assertEqual(parsed["reported_result_count"], 3)
        self.assertEqual(len(parsed["item_urls"]), 2)
        self.assertEqual(
            parsed["item_urls"][0],
            "https://www.memoirefilmiquedusud.eu/collection/item/10-film-a",
        )
        self.assertEqual(len(parsed["pagination_urls"]), 1)
        self.assertEqual(
            parsed["jean_vigo_filter_hints"][0]["kind"],
            "select_option",
        )

    def test_filtered_pagination_is_not_enumeration_route(self):
        html = """
        <a href="/collection?page=2&refine[archive][]=Institut+Jean+Vigo">
          filtered
        </a>
        """
        parsed = parse_collection_page(
            html,
            "https://www.memoirefilmiquedusud.eu/collection",
        )
        self.assertEqual(parsed["pagination_urls"], [])

    def test_item_parser_extracts_provider_and_film_semantics(self):
        html = """
        <html><body><h1>Film X</h1>
          <dl>
            <dt>Réalisateur/Auteur</dt><dd>Auteur</dd>
            <dt>Année</dt><dd>1952</dd>
            <dt>Type de document</dt><dd>Film</dd>
            <dt>Durée</dt><dd>00:12:00</dd>
            <dt>Lieu de conservation</dt><dd>Institut Jean Vigo</dd>
          </dl>
        </body></html>
        """
        parsed = parse_item_page(
            html,
            "https://www.memoirefilmiquedusud.eu/collection/item/42-film-x",
        )
        self.assertTrue(parsed["film_semantics_confirmed"])
        self.assertEqual(parsed["provider"], "Institut Jean Vigo")
        self.assertEqual(parsed["item_id"], "42")

    def test_sample_is_deterministic_and_spans_identifier_range(self):
        urls = [
            f"https://www.memoirefilmiquedusud.eu/collection/item/{i}-x"
            for i in range(1, 101)
        ]
        sample = _deterministic_sample(urls, 5)
        self.assertEqual(len(sample), 5)
        self.assertTrue(sample[0].endswith("/1-x"))
        self.assertTrue(sample[-1].endswith("/100-x"))

    def test_robots_longest_rule_wins(self):
        robots = """
        User-agent: *
        Disallow: /collection/private
        Allow: /collection/
        """
        self.assertFalse(
            robots_allowed(
                robots,
                "MemoriaAudiovisualRede",
                "https://www.memoirefilmiquedusud.eu/collection/private/x",
            )
        )
        self.assertTrue(
            robots_allowed(
                robots,
                "MemoriaAudiovisualRede",
                "https://www.memoirefilmiquedusud.eu/collection/item/1-x",
            )
        )

    def test_probe_holds_on_incomplete_enumeration(self):
        robots = "User-agent: *\nAllow: /\n"
        collection = """
        <html><body>
          <p>Votre recherche a retourné 2 résultat(s)</p>
          <a href="/collection/item/10-film-a">A</a>
        </body></html>
        """

        class Session:
            def get(self, url, **_kwargs):
                class Response:
                    status_code = 200
                    headers = {"content-type": "text/html"}
                    text = collection

                response = Response()
                if url.endswith("robots.txt"):
                    response.text = robots
                    response.headers = {"content-type": "text/plain"}
                return response

        payload = run_memoire_filmique_probe(Session())
        self.assertEqual(
            payload["gate_assessment"],
            "hold_external_surface_enumeration_incomplete",
        )

    def test_probe_advances_staged_only_with_complete_semantics_and_provider(self):
        robots = "User-agent: *\nAllow: /\n"
        collection = """
        <html><body>
          <p>Votre recherche a retourné 2 résultat(s)</p>
          <a href="/collection/item/10-film-a">A</a>
          <a href="/collection/item/20-film-b">B</a>
        </body></html>
        """
        item = """
        <html><body><h1>Film</h1>
          <dl>
            <dt>Réalisateur/Auteur</dt><dd>Auteur</dd>
            <dt>Année</dt><dd>1952</dd>
            <dt>Type de document</dt><dd>Film</dd>
            <dt>Durée</dt><dd>00:12:00</dd>
            <dt>Lieu de conservation</dt><dd>Institut Jean Vigo</dd>
          </dl>
        </body></html>
        """

        class Session:
            def get(self, url, **_kwargs):
                class Response:
                    status_code = 200
                    headers = {"content-type": "text/html"}
                    text = item

                response = Response()
                if url.endswith("robots.txt"):
                    response.text = robots
                    response.headers = {"content-type": "text/plain"}
                elif url.rstrip("/").endswith("collection"):
                    response.text = collection
                return response

        payload = run_memoire_filmique_probe(Session())
        self.assertEqual(
            payload["gate_assessment"],
            "shared_platform_enumeration_confirmed_staged_provenance_scan_required",
        )
        self.assertEqual(payload["semantic_confirmed_count"], 2)
        self.assertEqual(payload["provider_present_count"], 2)


if __name__ == "__main__":
    unittest.main()
