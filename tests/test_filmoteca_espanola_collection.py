import unittest

from memoria_audiovisual.filmoteca_espanola import (
    collect_filmoteca_espanola_dataset,
    parse_filmoteca_espanola_video,
)


VIDEO_FILMOTECA = {
    "_id": "INV001",
    "title": "Las dos memorias",
    "description": "Documental sobre memoria histórica.",
    "shortDescription": "Película conservada por Filmoteca Española.",
    "duration": 1200,
    "date": -1072915200000,
    "slug": "las-dos-memorias",
    "access": "register",
    "itemType": "Video",
    "layout": {
        "genre": [{"value": "No ficción"}],
        "subgenre": [{"value": "Documental"}],
        "topic": [{"value": "Guerra Civil"}],
        "label": [{"title": "Etiqueta", "value": "Memoria"}],
        "other": [
            {"title": "Titular de los derechos", "value": "Filmoteca Española"},
            {"title": "País", "value": "España"},
            {"title": "Idioma original", "value": "Español"},
            {"title": "Formato de la obra original", "value": "35 mm"},
        ],
    },
}

VIDEO_OTHER_RIGHTS = {
    **VIDEO_FILMOTECA,
    "_id": "CAT001",
    "title": "Spagna 68",
    "slug": "spagna-68",
    "layout": {
        **VIDEO_FILMOTECA["layout"],
        "other": [{"title": "Titular de los derechos", "value": "Filmoteca de Catalunya"}],
    },
}


class FilmotecaEspanolaCollectionTests(unittest.TestCase):
    def test_parse_video_preserves_access_and_rights_context(self):
        record = parse_filmoteca_espanola_video(VIDEO_FILMOTECA)

        self.assertEqual(record["record_id"], "INV001")
        self.assertEqual(record["date"], "1936")
        self.assertIn("Filmoteca Española", record["description"])
        self.assertIn("login/cadastro obrigatório", record["description"])
        self.assertIn("filmo.platfo.es/content/las-dos-memorias", record["video_link"])

    def test_collect_dataset_filters_out_other_platfo_rights_holders(self):
        payloads = {
            "https://galgo-filmoteca.galgo.tv/catalogs": ([{"name": "Filmo"}, {"name": "Play"}], 200),
            "https://galgo-filmoteca.galgo.tv/search/filters?image-format=webp": (
                [
                    {
                        "param": "copyright",
                        "values": [{"_id": "23723", "name": "Filmoteca Española"}],
                    }
                ],
                200,
            ),
            (
                "https://galgo-filmoteca.galgo.tv/container?containerType=Collection&version=2&"
                "image-format=webp&size=10000&page=1"
            ): ({"videos": [VIDEO_FILMOTECA, VIDEO_OTHER_RIGHTS]}, 200),
            (
                "https://galgo-filmoteca.galgo.tv/search?copyright=23723&version=2&image-format=webp&"
                "size=10000&page=1"
            ): ({"videos": [VIDEO_FILMOTECA, VIDEO_OTHER_RIGHTS, VIDEO_FILMOTECA]}, 200),
        }

        def fetch_json(url):
            payload, status = payloads[url]
            return payload, url, status

        institutions, summary, links, internal_pages = collect_filmoteca_espanola_dataset(fetch_json)

        self.assertEqual(len(institutions), 1)
        self.assertEqual(summary[0]["video_links_found_total"], 1)
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["platform"], "PLATFO FILMO")
        self.assertIn("Las dos memorias", links[0]["video_title"])
        self.assertEqual(len(internal_pages), 4)


if __name__ == "__main__":
    unittest.main()
