import unittest

from memoria_audiovisual.analysis import classify_access_regime, classify_access_surface
from memoria_audiovisual.config import PARES_HOME_URL
from memoria_audiovisual.crawler import classify_platform, is_probably_video_link
from memoria_audiovisual.pares import (
    _extract_record_id,
    collect_pares_institutions,
    parse_pares_search_results,
)


class ParesCollectionTests(unittest.TestCase):
    def test_collect_pares_institutions_declares_single_aggregator(self):
        institutions = collect_pares_institutions()

        self.assertEqual(len(institutions), 1)
        record = institutions[0]
        self.assertEqual(record["institution"], "PARES")
        self.assertEqual(record["external_url"], PARES_HOME_URL)
        self.assertEqual(record["pares_detail_url"], PARES_HOME_URL)
        self.assertTrue(record["content_available_in_source"])
        self.assertEqual(record["archive_type"], "National archival aggregator")

    def test_extract_record_id_accepts_description_and_show_urls(self):
        self.assertEqual(
            _extract_record_id("/ParesBusquedas20/catalogo/description/2122299?nm"),
            "2122299",
        )
        self.assertEqual(
            _extract_record_id("/ParesBusquedas20/catalogo/show/2122299?nm"),
            "2122299",
        )

    def test_parse_search_results_detects_description_and_digital_object_links(self):
        html = """
        <html><body>
        Resultados 1 - 25 de 32
        <a href="/ParesBusquedas20/catalogo/show/2122299?nm"></a>
        <a href="/ParesBusquedas20/catalogo/description/2122299?nm">Archivo audiovisual del Partido Carlista</a>
        <a href="/ParesBusquedas20/catalogo/description/13341008?nm">Expediente relativo a la venta de material audiovisual</a>
        </body></html>
        """

        records, result_count = parse_pares_search_results(
            html,
            "https://pares.mcu.es/ParesBusquedas20/catalogo/find?nm=&texto=audiovisual",
            "audiovisual",
        )

        self.assertEqual(result_count, 32)
        self.assertEqual(len(records), 2)
        self.assertTrue(records[0]["digital_object_detected"])
        self.assertFalse(records[1]["digital_object_detected"])

    def test_pares_urls_are_classified_as_national_aggregator_surface(self):
        item_url = "https://pares.mcu.es/ParesBusquedas20/catalogo/description/2122299?nm"

        self.assertEqual(classify_platform(item_url), "PARES")
        self.assertTrue(is_probably_video_link(item_url, "PARES"))
        self.assertEqual(
            classify_access_surface({"platform": "PARES", "video_link": item_url}),
            "Agregador arquivístico nacional",
        )
        self.assertEqual(
            classify_access_surface(
                {
                    "platform": "PARES",
                    "video_link": item_url,
                    "video_description": "objeto digital detectado; registro PARES 2122299",
                }
            ),
            "Objeto digital em agregador arquivístico nacional",
        )
        self.assertEqual(
            classify_access_surface(
                {
                    "platform": "PARES",
                    "video_link": item_url,
                    "video_description": "registro descritivo recuperado; registro PARES 2122299",
                }
            ),
            "Registro descritivo em agregador arquivístico nacional",
        )
        self.assertEqual(
            classify_access_regime(
                ["Agregador arquivístico nacional"],
                "Evidência pública detectável de audiovisual",
            ),
            "Acesso por agregador arquivístico nacional",
        )
        self.assertEqual(
            classify_access_regime(
                [
                    "Objeto digital em agregador arquivístico nacional",
                    "Registro descritivo em agregador arquivístico nacional",
                ],
                "Evidência pública detectável de audiovisual",
            ),
            "Acesso misto descritivo/digital em agregador arquivístico nacional",
        )


if __name__ == "__main__":
    unittest.main()
