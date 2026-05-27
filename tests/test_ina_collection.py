import unittest
from inspect import signature

from memoria_audiovisual.config import (
    INA_COLLECTIONS_URL,
    INA_DATA_URL,
    INA_HOME_URL,
    INA_INSTITUTION_URL,
    INA_MADELEN_URL,
    INA_MEDIACLIP_URL,
    INA_MEDIA_MAGAZINE_URL,
    INA_NEWS_URL,
)
from memoria_audiovisual.analysis import classify_access_regime, classify_access_surface
from memoria_audiovisual.crawler import classify_platform, is_probably_video_link
from memoria_audiovisual.crawler import analyze_institution
from memoria_audiovisual.ina import INA_SEED_URLS, collect_ina_institutions


class InaCollectionTests(unittest.TestCase):
    def test_collect_ina_institutions_includes_seed_urls(self):
        institutions = collect_ina_institutions()

        self.assertEqual(len(institutions), 1)
        record = institutions[0]
        self.assertEqual(record["external_url"], INA_HOME_URL)
        self.assertEqual(record["ina_detail_url"], INA_INSTITUTION_URL)
        self.assertEqual(record["seed_urls"], INA_SEED_URLS)
        self.assertIn(INA_COLLECTIONS_URL, record["seed_urls"])
        self.assertIn(INA_DATA_URL, record["seed_urls"])
        self.assertIn(INA_NEWS_URL, record["seed_urls"])
        self.assertIn(INA_MEDIA_MAGAZINE_URL, record["seed_urls"])
        self.assertIn(INA_MADELEN_URL, record["seed_urls"])
        self.assertIn(INA_MEDIACLIP_URL, record["seed_urls"])

    def test_ina_platform_domains_are_classified_as_audiovisual_surfaces(self):
        madelen_url = "https://madelen.ina.fr/content/le-pere-noel-est-une-ordure-126698"
        mediaclip_url = "https://mediaclip.ina.fr/fr/inacatalog/product/view/id/4002/"

        self.assertEqual(classify_platform(madelen_url), "Madelen")
        self.assertEqual(classify_platform(mediaclip_url), "Mediaclip INA")
        self.assertTrue(is_probably_video_link(madelen_url, "Madelen"))
        self.assertTrue(is_probably_video_link(mediaclip_url, "Mediaclip INA"))

    def test_analyze_institution_accepts_seed_urls(self):
        self.assertIn("seed_urls", signature(analyze_institution).parameters)

    def test_access_surface_distinguishes_specialized_ina_modalities(self):
        self.assertEqual(
            classify_access_surface({"platform": "Madelen", "video_link": "https://madelen.ina.fr/content/demo"}),
            "Streaming curatorial",
        )
        self.assertEqual(
            classify_access_surface(
                {"platform": "Mediaclip INA", "video_link": "https://mediaclip.ina.fr/fr/inacatalog/product/view/id/1/"}
            ),
            "Catálogo comercial de licenciamento",
        )

    def test_access_regime_distinguishes_institutional_and_mixed_access(self):
        self.assertEqual(
            classify_access_regime(["Streaming curatorial"], "Evidência pública detectável de audiovisual"),
            "Acesso aberto em streaming",
        )
        self.assertEqual(
            classify_access_regime(
                ["Streaming curatorial", "Catálogo comercial de licenciamento"],
                "Evidência pública detectável de audiovisual",
            ),
            "Acesso misto entre difusão pública e licenciamento",
        )
        self.assertEqual(
            classify_access_regime([], "Sem evidência pública detectável de audiovisual"),
            "Sem evidência suficiente",
        )


if __name__ == "__main__":
    unittest.main()
