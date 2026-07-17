import unittest

from memoria_audiovisual.csc_cineteca import (
    extract_csc_cineteca_catalog_links,
    normalize_csc_cineteca_media_url,
    parse_csc_cineteca_video_page,
)


class CscCinetecaCollectionTests(unittest.TestCase):
    def test_extract_catalog_links_keeps_unique_public_film_pages(self):
        html = """
        <a href="/film/uno/">Uno</a>
        <a href="https://www.fondazionecsc.it/film/uno/">Uno repetido</a>
        <a href="/en/film/two/">EN</a>
        <a href="/film/">Arquivo geral</a>
        <a href="/film/tre/?utm=x">Tre</a>
        """

        links = extract_csc_cineteca_catalog_links(html)

        self.assertEqual(
            links,
            [
                "https://www.fondazionecsc.it/film/uno/",
                "https://www.fondazionecsc.it/film/tre/",
            ],
        )

    def test_normalize_media_urls_to_public_watch_pages(self):
        self.assertEqual(
            normalize_csc_cineteca_media_url("https://www.youtube.com/embed/fXkw7xE1woM?feature=oembed"),
            "https://www.youtube.com/watch?v=fXkw7xE1woM",
        )
        self.assertEqual(
            normalize_csc_cineteca_media_url("https://player.vimeo.com/video/509807804?badge=0"),
            "https://vimeo.com/509807804",
        )

    def test_parse_video_page_extracts_title_date_and_embed(self):
        html = """
        <html>
          <head>
            <title>Effetto notte 2023. Intervista a Roberto Perpignani - Centro Sperimentale di Cinematografia</title>
            <script type="application/ld+json">{"datePublished":"2023-08-02T17:14:16+00:00"}</script>
          </head>
          <body>
            <main><p>Intervista realizzata per il Catalogo video.</p></main>
            <iframe src="https://www.youtube.com/embed/fXkw7xE1woM"></iframe>
          </body>
        </html>
        """

        parsed = parse_csc_cineteca_video_page(
            html,
            "https://www.fondazionecsc.it/film/effetto-notte-2023-intervista-a-roberto-perpignani-2/",
        )

        self.assertEqual(parsed["record_id"], "effetto-notte-2023-intervista-a-roberto-perpignani-2")
        self.assertEqual(parsed["video_link"], "https://www.youtube.com/watch?v=fXkw7xE1woM")
        self.assertEqual(parsed["platform"], "YouTube")
        self.assertEqual(parsed["date"], "2023-08-02")
        self.assertIn("Roberto Perpignani", parsed["title"])
        self.assertTrue(parsed["embedded"])


if __name__ == "__main__":
    unittest.main()
