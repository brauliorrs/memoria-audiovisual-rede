import unittest

from memoria_audiovisual.analysis import classify_access_regime, classify_access_surface, infer_video_theme
from memoria_audiovisual.anf import (
    collect_anf_institutions,
    parse_anf_eventbook_collection_page,
    parse_anf_eventbook_detail_page,
)
from memoria_audiovisual.crawler import classify_platform, is_probably_video_link


ANF_COLLECTION_HTML = """
<html><body>
  <a href="/film/bilete-cinemateca-online-istorii-industriale-munca-in-perioada-interbelica">
    Istorii industriale. Munca în perioada interbelică
  </a>
  <a href="/film/bilete-cinemateca-online-aventura-fericita">Aventura fericită</a>
  <a href="/film/bilete-alt-program">Outro programa</a>
</body></html>
"""


ANF_DETAIL_HTML = """
<html><head>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Event",
  "name": "Istorii industriale. Munca în perioada interbelică - Cinemateca Online",
  "startDate": "2026-01-10",
  "description": "România / 1930 / documentar / a/n\\nVersiune digitalizată de Arhiva Națională de Filme.",
  "offers": {"price": "12", "priceCurrency": "RON"}
}
</script>
</head><body>
  Vizionarea este disponibilă doar pe teritoriul României.
</body></html>
"""


class AnfCollectionTests(unittest.TestCase):
    def test_collect_anf_institutions_declares_single_archive(self):
        institutions = collect_anf_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["repository_code"], "RO-ANF")
        self.assertEqual(institutions[0]["country"], "Romania")

    def test_parse_anf_eventbook_collection_page_extracts_cinemateca_links(self):
        links = parse_anf_eventbook_collection_page(
            ANF_COLLECTION_HTML,
            "https://eventbook.ro/program/cinemateca-online",
        )

        self.assertEqual(len(links), 2)
        self.assertIn("Istorii industriale", links[0]["title"])
        self.assertTrue(links[0]["url"].startswith("https://eventbook.ro/film/"))

    def test_parse_anf_eventbook_detail_page_extracts_access_metadata(self):
        record = parse_anf_eventbook_detail_page(
            ANF_DETAIL_HTML,
            "https://eventbook.ro/film/bilete-cinemateca-online-istorii-industriale-munca-in-perioada-interbelica",
        )

        self.assertEqual(record["platform"], "Eventbook")
        self.assertEqual(record["title"], "Istorii industriale. Munca în perioada interbelică")
        self.assertEqual(record["date"], "1930")
        self.assertIn("documentar", record["subject"])
        self.assertIn("12 RON", record["description"])
        self.assertIn("território romeno", record["description"])

    def test_eventbook_urls_are_classified_as_external_online_exhibition(self):
        url = "https://eventbook.ro/film/bilete-cinemateca-online-aventura-fericita"

        self.assertEqual(classify_platform(url), "Eventbook")
        self.assertTrue(is_probably_video_link(url, "Eventbook"))
        self.assertEqual(
            classify_access_surface({"platform": "Eventbook", "video_link": url}),
            "Plataforma externa de exibição online",
        )
        self.assertEqual(
            classify_access_regime(["Plataforma externa de exibição online"], "Audiovisual disponível publicamente"),
            "Acesso mediado por plataforma externa de exibição online",
        )

    def test_eventbook_theme_is_not_platform_noise(self):
        theme = infer_video_theme(
            {
                "platform": "Eventbook",
                "video_title": "Istorii industriale. Munca în perioada interbelică",
                "video_subject": "documentar",
                "video_description": "Versiune digitalizată de Arhiva Națională de Filme.",
            }
        )

        self.assertEqual(theme, "Documentário e registro histórico")


if __name__ == "__main__":
    unittest.main()
