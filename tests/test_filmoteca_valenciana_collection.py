import unittest

from memoria_audiovisual.analysis import classify_access_surface
from memoria_audiovisual.filmoteca_valenciana import (
    collect_filmoteca_valenciana_dataset,
    extract_filmoteca_valenciana_vimeo_ids,
    parse_filmoteca_valenciana_detail_page,
    parse_filmoteca_valenciana_listing_links,
)


class FilmotecaValencianaCollectionTests(unittest.TestCase):
    def test_parse_listing_keeps_spanish_restoration_film_links(self):
        html = """
        <nav>
          <a href="/cine-valenciano/no-ficcion/fallas-de-valencia/">Fallas</a>
          <a href="/cine-valencia-2/no-ficcio/fallas-de-valencia/">Falles</a>
          <a href="/inicio/">Inicio</a>
        </nav>
        """
        links = parse_filmoteca_valenciana_listing_links(
            html,
            "https://www.restauracionesfilmoteca.com/inicio/",
        )

        self.assertEqual(
            links,
            ["https://www.restauracionesfilmoteca.com/cine-valenciano/no-ficcion/fallas-de-valencia/"],
        )

    def test_parse_detail_extracts_vimeo_catalog_url_and_scope_note(self):
        html = """
        <article class="post">
          <h1>[Fallas de Valencia]</h1>
          <div class="entry">
            <iframe title="[Fallas de Valencia]" src="https://player.vimeo.com/video/84018346?badge=0"></iframe>
            <p><strong>[FALLAS DE VALENCIA]. España, 1928-29. B/N. 13′</strong></p>
            <p>Fragmentos de dos reportajes sobre las Fallas de Valencia.</p>
            <p>Restaurada por la Filmoteca en 1992.</p>
            <p><a href="http://arxiu.ivac-lafilmoteca.es:8080/IVAC/BRSCGI.exe?CMD=VERDOC">Enlace a la ficha de la película</a></p>
          </div>
        </article>
        """
        page_url = "https://www.restauracionesfilmoteca.com/cine-valenciano/no-ficcion/fallas-de-valencia/"
        records = parse_filmoteca_valenciana_detail_page(html, page_url)

        self.assertEqual(extract_filmoteca_valenciana_vimeo_ids(html), ["84018346"])
        self.assertEqual(records[0]["record_id"], "84018346")
        self.assertEqual(records[0]["date"], "1928-29")
        self.assertIn("não representa o catálogo integral", records[0]["description"])
        self.assertIn("BRSCGI.exe", records[0]["catalog_record_url"])

    def test_dataset_deduplicates_by_vimeo_id(self):
        pages = {
            "https://www.restauracionesfilmoteca.com/inicio/": """
              <a href="/cine-valenciano/no-ficcion/fallas-de-valencia/">Fallas</a>
              <a href="/cine-valenciano/no-ficcion/fallas-duplicada/">Fallas duplicada</a>
            """,
            "https://www.restauracionesfilmoteca.com/cine-valenciano/no-ficcion/fallas-de-valencia/": """
              <div class="entry"><h1>Fallas</h1>
              <iframe src="https://player.vimeo.com/video/84018346"></iframe>
              <p>España, 1928. 13′</p></div>
            """,
            "https://www.restauracionesfilmoteca.com/cine-valenciano/no-ficcion/fallas-duplicada/": """
              <div class="entry"><h1>Fallas duplicada</h1>
              <iframe src="https://player.vimeo.com/video/84018346"></iframe>
              <p>España, 1928. 13′</p></div>
            """,
        }

        class Page:
            def __init__(self, url, html):
                self.url = url
                self.status = "200"
                self.html = html
                self.error = ""

        def fetch(url):
            return Page(url, pages[url])

        _, summary, links, internal_pages = collect_filmoteca_valenciana_dataset(fetch)

        self.assertEqual(len(links), 1)
        self.assertEqual(summary[0]["video_links_found"], 1)
        self.assertEqual(len(internal_pages), 3)

    def test_access_surface_is_external_video_platform(self):
        row = {
            "platform": "Vimeo / Restauraciones Filmoteca Valenciana",
            "video_link": "https://player.vimeo.com/video/84018346",
            "video_title": "Fallas de Valencia",
            "video_description": "Vídeo público no subsite Restauraciones.",
        }

        self.assertEqual(classify_access_surface(row), "Plataforma externa de vídeo")


if __name__ == "__main__":
    unittest.main()
