import unittest

from memoria_audiovisual.analysis import infer_video_theme
from memoria_audiovisual.filmoteca_catalunya import (
    collect_filmoteca_catalunya_dataset,
    collect_filmoteca_catalunya_institutions,
)


VIDEO_CATALUNYA = {
    "_id": "CAT_001",
    "title": "Será tu tierra",
    "description": "Película del fondo catalán.",
    "shortDescription": "Registro PLATFO.",
    "duration": 1200,
    "date": -157766400000,
    "slug": "sera-tu-tierra",
    "access": "register",
    "itemType": "Video",
    "layout": {
        "genre": [{"value": "No ficción"}],
        "subgenre": [{"value": "Documental"}],
        "topic": [{"value": "Migración"}],
        "other": [
            {"title": "Titular de los derechos", "value": "Filmoteca de Catalunya"},
            {"title": "País", "value": "España"},
        ],
    },
}

VIDEO_OTHER_RIGHTS = {
    **VIDEO_CATALUNYA,
    "_id": "INV001",
    "title": "Otro fondo",
    "slug": "otro-fondo",
    "layout": {
        **VIDEO_CATALUNYA["layout"],
        "other": [{"title": "Titular de los derechos", "value": "Filmoteca Española"}],
    },
}


class FilmotecaCatalunyaCollectionTests(unittest.TestCase):
    def test_collect_institutions_declares_single_archive(self):
        institutions = collect_filmoteca_catalunya_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["institution"], "Filmoteca de Catalunya")
        self.assertTrue(institutions[0]["content_available_in_source"])

    def test_collect_dataset_filters_by_catalunya_rights_holder(self):
        payloads = {
            "https://galgo-filmoteca.galgo.tv/catalogs": ([{"name": "Filmo"}], 200),
            "https://galgo-filmoteca.galgo.tv/search/filters?image-format=webp": (
                [
                    {
                        "param": "copyright",
                        "values": [{"_id": "205985", "name": "Filmoteca de Catalunya"}],
                    }
                ],
                200,
            ),
            (
                "https://galgo-filmoteca.galgo.tv/container?containerType=Collection&version=2&"
                "image-format=webp&size=10000&page=1"
            ): ({"videos": [VIDEO_CATALUNYA, VIDEO_OTHER_RIGHTS]}, 200),
            (
                "https://galgo-filmoteca.galgo.tv/search?copyright=205985&version=2&image-format=webp&"
                "size=10000&page=1"
            ): ({"videos": [VIDEO_CATALUNYA, VIDEO_OTHER_RIGHTS, VIDEO_CATALUNYA]}, 200),
        }

        def fetch_json(url):
            payload, status = payloads[url]
            return payload, url, status

        institutions, summary, links, internal_pages = collect_filmoteca_catalunya_dataset(fetch_json)

        self.assertEqual(len(institutions), 1)
        self.assertEqual(summary[0]["video_links_found_total"], 1)
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["platform"], "PLATFO FILMO")
        self.assertIn("Será tu tierra", links[0]["video_title"])
        self.assertEqual(len(internal_pages), 4)

    def test_platfo_catalunya_records_get_content_themes(self):
        self.assertEqual(
            infer_video_theme(
                {
                    "platform": "PLATFO FILMO",
                    "video_title": "El cuarto poder",
                    "video_subject": "No ficción; Documental; Entrevistas; Prensa",
                    "video_description": "Recorrido sobre prensa escrita, censura y franquismo.",
                }
            ),
            "Mídia, censura e esfera pública",
        )
        self.assertEqual(
            infer_video_theme(
                {
                    "platform": "PLATFO FILMO",
                    "video_title": "Será tu tierra",
                    "video_subject": "No ficción; Documental; Barcelona; Urbanismo",
                    "video_description": "Ciudad de acogida y residencia de inmigrantes durante los años sesenta.",
                }
            ),
            "Migração, cidade e memória social",
        )
        self.assertEqual(
            infer_video_theme(
                {
                    "platform": "PLATFO FILMO",
                    "video_title": "A la vuelta del grito",
                    "video_subject": "No ficción; Documental; Movimiento obrero; Huelgas; Política",
                    "video_description": "Testimonios de trabajadores y fábricas de Barcelona.",
                }
            ),
            "Memória política, trabalho e conflito social",
        )
        self.assertEqual(
            infer_video_theme(
                {
                    "platform": "PLATFO FILMO",
                    "video_title": "El largo viaje hacia la ira",
                    "video_subject": "No ficción; Documental; Éxodo rural; Barcelona-Usos y costumbres",
                    "video_description": "Inmigración española procedente de Andalucía en la Barcelona de los años 60.",
                }
            ),
            "Migração, cidade e memória social",
        )


if __name__ == "__main__":
    unittest.main()
