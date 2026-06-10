import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.aqshf import collect_aqshf_institutions, parse_aqshf_motion_picture_post
from memoria_audiovisual.crawler import classify_platform, is_probably_video_link


AQSHF_POST = {
    "id": 189665,
    "date": "2026-04-13T15:27:03",
    "slug": "takim-i-rita-markos-me-shkrimtaret-dhe-artistet",
    "link": "https://aqshf.gov.al/motion_picture/takim-i-rita-markos-me-shkrimtaret-dhe-artistet/",
    "title": {"rendered": "Takim i Rita Markos me shkrimtarët dhe artistët"},
    "excerpt": {"rendered": "<p>Resumo curto.</p>"},
    "content": {
        "rendered": """
        <table>
          <tr><td>Kodi i referencës</td><td>IV/1-409</td></tr>
          <tr><td>Titulli</td><td>Takimi i Rita Markos me shkrimtaret dhe artistet, 1974</td></tr>
          <tr><td>Përshkrimi</td><td>Encontro com escritores e artistas em Tirana.</td></tr>
          <tr><td>Kategoria</td><td>Xhirime arkivore bruto</td></tr>
          <tr><td>Kroma</td><td>Bardhe e zi</td></tr>
          <tr><td>Viti i prodhimit</td><td>1974</td></tr>
          <tr><td>Kohëzgjatja (në minuta)</td><td>3:39</td></tr>
          <tr><td>Vendi i prodhimit</td><td>Shqipëri</td></tr>
          <tr><td>Producenti</td><td>Kinostudio “Shqipëria e re”</td></tr>
        </table>
        """
    },
}


class AqshfCollectionTests(unittest.TestCase):
    def test_collect_aqshf_institutions_declares_single_archive(self):
        institutions = collect_aqshf_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["repository_code"], "AL-AQSHF")
        self.assertEqual(institutions[0]["country"], "Albania")

    def test_parse_aqshf_motion_picture_post_extracts_metadata(self):
        record = parse_aqshf_motion_picture_post(AQSHF_POST)

        self.assertEqual(record["record_id"], "IV/1-409")
        self.assertEqual(record["platform"], "AQSHF")
        self.assertEqual(record["date"], "1974")
        self.assertEqual(record["subject"], "Xhirime arkivore bruto")
        self.assertIn("Registro descritivo público", record["description"])
        self.assertIn("Kinostudio", record["description"])

    def test_aqshf_urls_are_classified_as_institutional_catalog_records(self):
        url = "https://aqshf.gov.al/motion_picture/takim-i-rita-markos-me-shkrimtaret-dhe-artistet/"

        self.assertEqual(classify_platform(url), "AQSHF")
        self.assertTrue(is_probably_video_link(url, "AQSHF"))
        self.assertEqual(
            classify_access_surface({"platform": "AQSHF", "video_link": url}),
            "Catálogo descritivo audiovisual institucional",
        )

    def test_aqshf_theme_uses_catalog_metadata(self):
        theme = infer_video_theme(
            {
                "platform": "AQSHF",
                "video_title": "Takimi i Rita Markos me shkrimtaret dhe artistet",
                "video_subject": "Xhirime arkivore bruto",
                "video_description": "Registro descritivo público de imagens de arquivo.",
            }
        )

        self.assertEqual(theme, "Documentário e registro histórico")


if __name__ == "__main__":
    unittest.main()
