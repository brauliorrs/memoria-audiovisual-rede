import unittest

from memoria_audiovisual.image_est_probe import (
    IMAGE_EST_FILMS_FILTER_URL,
    parse_archive_html,
    parse_detail_html,
    parse_sitemap,
    robots_allowed,
)


class ImageEstProbeTests(unittest.TestCase):
    def test_archive_parser_discovers_video_filter_count_pages_and_details(self):
        html = f"""
        <html><head><title>Nos archives</title></head><body>
          <div>3 040 résultat(s)</div>
          <a href="{IMAGE_EST_FILMS_FILTER_URL}">Films</a>
          <a href="/fiche-documentaire-film-a-1284-744-3-0.html">Film A</a>
          <a href="/fiche-documentaire-film-b-1284-745-3-0.html">Film B</a>
          <a href="/nos-archives-1283-0-0-2.html?ref=abc">2</a>
          <a href="/nos-archives-1283-0-0-190.html?ref=abc">&gt;I</a>
        </body></html>
        """
        parsed = parse_archive_html(
            html,
            "https://www.image-est.fr/nos-archives-1283-0-0-0.html?ref=abc",
        )
        self.assertEqual(parsed["result_count"], 3040)
        self.assertEqual(parsed["detail_links_count"], 2)
        self.assertEqual(parsed["max_page_number"], 190)
        self.assertIn(IMAGE_EST_FILMS_FILTER_URL, parsed["films_filter_links"])
        self.assertEqual(
            [row["page_number"] for row in parsed["pagination_links"]],
            [2, 190],
        )

    def test_detail_parser_requires_film_metadata_and_embedded_player(self):
        html = """
        <html><body>
          <h1>Noël à Chaumont</h1>
          <dl>
            <dt>Année</dt><dd>1985</dd>
            <dt>Durée</dt><dd>00:03:18:00</dd>
            <dt>Format</dt><dd>Film 16 mm</dd>
            <dt>Son</dt><dd>Muet</dd>
            <dt>Fonds</dt><dd>Pascal MICHAUT</dd>
          </dl>
          <iframe src="https://diazie.oembed.diazinteregio.org/player/744"></iframe>
        </body></html>
        """
        parsed = parse_detail_html(
            html,
            "https://www.image-est.fr/fiche-documentaire-film-1284-744-3-0.html",
        )
        self.assertTrue(parsed["film_semantics_confirmed"])
        self.assertGreaterEqual(parsed["label_count"], 3)
        self.assertEqual(len(parsed["iframe_urls"]), 1)

    def test_robots_longest_rule_wins_and_ajax_can_be_blocked(self):
        robots = """
        User-agent: *
        Disallow: /js/
        Allow: /js/public/
        """
        self.assertFalse(
            robots_allowed(
                robots,
                "MemoriaAudiovisualRede",
                IMAGE_EST_FILMS_FILTER_URL,
            )
        )
        self.assertTrue(
            robots_allowed(
                robots,
                "MemoriaAudiovisualRede",
                "https://www.image-est.fr/js/public/catalogue",
            )
        )

    def test_sitemap_parser_separates_video_details_from_mixed_records(self):
        xml = """
        <urlset>
          <url><loc>https://www.image-est.fr/fiche-documentaire-film-a-1284-744-3-0.html</loc></url>
          <url><loc>https://www.image-est.fr/fiche-documentaire-1284-0-0-2453.html</loc></url>
          <url><loc>https://www.image-est.fr/archive_content.xml</loc></url>
        </urlset>
        """
        parsed = parse_sitemap(xml)
        self.assertEqual(parsed["url_count"], 3)
        self.assertEqual(parsed["detail_candidate_count"], 2)
        self.assertEqual(parsed["video_detail_candidate_count"], 1)
        self.assertEqual(parsed["typed_detail_counts"], {"2": 1, "3": 1})
        self.assertEqual(parsed["untyped_detail_candidate_count"], 0)
        self.assertEqual(
            parsed["video_detail_candidate_samples"],
            [
                "https://www.image-est.fr/fiche-documentaire-film-a-1284-744-3-0.html"
            ],
        )
        self.assertEqual(
            parsed["nested_sitemaps"],
            ["https://www.image-est.fr/archive_content.xml"],
        )

    def test_film_metadata_can_confirm_audiovisual_without_embedded_player(self):
        html = """
        <html><body>
          <h1>Des gestes et des mots</h1>
          <dl>
            <dt>Année</dt><dd>2003</dd>
            <dt>Durée</dt><dd>00:13:10</dd>
            <dt>Son</dt><dd>Sonore</dd>
            <dt>Fonds</dt><dd>Alain RIES</dd>
          </dl>
        </body></html>
        """
        parsed = parse_detail_html(
            html,
            "https://www.image-est.fr/fiche-documentaire-film-1284-1858-1-0.html",
        )
        self.assertTrue(parsed["film_semantics_confirmed"])
        self.assertFalse(parsed["embedded_player_present"])

    def test_invalid_detail_without_iframe_does_not_confirm_semantics(self):
        parsed = parse_detail_html(
            "<h1>Photo</h1><p>Année 1950 Format négatif Fonds X</p>",
            "https://www.image-est.fr/item",
        )
        self.assertFalse(parsed["film_semantics_confirmed"])


if __name__ == "__main__":
    unittest.main()
