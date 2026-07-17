import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.filmoteca_vasca import (
    collect_filmoteca_vasca_institutions,
    extract_filmoteca_vasca_vimeo_ids,
    parse_filmoteca_vasca_detail_page,
    parse_filmoteca_vasca_links,
)


class FilmotecaVascaCollectionTests(unittest.TestCase):
    def test_collect_institutions_declares_single_archive(self):
        institutions = collect_filmoteca_vasca_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["institution"], "Filmoteca Vasca")
        self.assertTrue(institutions[0]["content_available_in_source"])

    def test_parse_links_keeps_only_multimedia_scope(self):
        html = """
        <main>
          <a href="/es/coleccion/multimedia/decada-1950/acrobacias">Acrobacias</a>
          <a href="/es/coleccion/catalogo">Catálogo</a>
        </main>
        """
        links = parse_filmoteca_vasca_links(html, "https://filmoteka.eus/es/coleccion/multimedia")

        self.assertEqual(links, ["https://filmoteka.eus/es/coleccion/multimedia/decada-1950/acrobacias"])

    def test_parse_detail_extracts_vimeo_and_metadata(self):
        html = """
        <main>
          <h1>Acrobacias en bicicleta</h1>
          <span class="h3"><span>Colección:</span><span>Ciclismo</span></span>
          <div class="lazyframe lazyframe__video" data-src="https://vimeo.com/836103598"
               data-thumbnail="https://filmoteka.eus/media/uploads/fondos/general_/9897_20.jpg"></div>
          <div class="mb-4"><h2>Director</h2><span>Depósito Miguel Ángel Echeverría Ganuza</span></div>
          <div class="mb-4"><h2>Año</h2><span>1950-1959</span></div>
          <div class="mb-4"><h2>Duración</h2><span>45´´</span></div>
          <div class="mb-4"><h2>Sinopsis / descripción</h2>
            <p>Exhibición de habilidades con bicicleta en el frontón de Añorga.</p>
          </div>
        </main>
        """
        page_url = "https://filmoteka.eus/es/coleccion/multimedia/ciclismo/acrobacias_en_bicicleta_9897_20"
        record = parse_filmoteca_vasca_detail_page(html, page_url)

        self.assertEqual(extract_filmoteca_vasca_vimeo_ids(html), ["836103598"])
        self.assertEqual(record["record_id"], "836103598")
        self.assertEqual(record["title"], "Acrobacias en bicicleta")
        self.assertEqual(record["year"], "1950-1959")
        self.assertIn("bicicleta", record["description"])

    def test_theme_and_access_are_audiovisual(self):
        row = {
            "platform": "Vimeo",
            "video_link": "https://vimeo.com/836103598",
            "video_title": "Carrera ciclista",
            "video_subject": "Ciclismo; década 1950",
            "video_description": "Vídeo público da seção Multimedia: https://filmoteka.eus/es/coleccion/multimedia/ciclismo",
        }

        self.assertEqual(infer_video_theme(row), "Esporte e cultura física")
        self.assertEqual(classify_access_surface(row), "Plataforma externa de vídeo")


if __name__ == "__main__":
    unittest.main()
