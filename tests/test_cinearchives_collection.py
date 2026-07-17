import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.cinearchives import (
    collect_cinearchives_institutions,
    extract_cinearchives_declared_pages,
    extract_cinearchives_declared_total,
    parse_cinearchives_detail_page,
    parse_cinearchives_list_page,
)


class CineArchivesCollectionTests(unittest.TestCase):
    def test_collect_cinearchives_institutions_declares_single_archive(self):
        institutions = collect_cinearchives_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["institution"], "Ciné-Archives")
        self.assertTrue(institutions[0]["content_available_in_source"])

    def test_parse_cinearchives_list_page_extracts_public_records(self):
        html = """
        <main>
          <p>1020 résultat(s)</p>
          <a href="catalogue-1104-0-0-43.html?">43</a>
          <article class="diaListItem">
            <a href="catalogue-reflets-1104-239-1-0.html?">REFLETS</a>
            <div>1964 | Collectif | 00:15:00 | Sonore</div>
            <p>Magazine communiste.</p>
          </article>
          <article class="diaListItem">
            <a href="catalogue-vie-est-a-nous-la-1104-16-1-0.html?">LA VIE EST A NOUS</a>
            <div>1936 | Jean Renoir | 01:04:00 | Sonore</div>
          </article>
        </main>
        """
        records = parse_cinearchives_list_page(html, "https://www.cinearchives.org/catalogue-1104-0-0-0.html")

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["record_id"], "239")
        self.assertEqual(records[0]["title"], "REFLETS")
        self.assertEqual(records[0]["date"], "1964")
        self.assertEqual(records[0]["subject"], "Collectif; Sonore")
        self.assertEqual(records[0]["platform"], "Ciné-Archives")
        self.assertEqual(extract_cinearchives_declared_total(html), 1020)
        self.assertEqual(extract_cinearchives_declared_pages(html), 43)

    def test_parse_cinearchives_detail_page_extracts_embed_and_metadata(self):
        html = """
        <html>
          <body>
            <h1>REFLETS</h1>
            <iframe src="https://diazcinearchives.oembed.diazinteregio.org/embed/CineA-1964-Reflets-210-1_1?feature=oembed"></iframe>
            <ul>
              <li class="val"><strong>Année(s)</strong><span>1964</span></li>
              <li class="val"><strong>Réalisateur.ice.s</strong><span>Collectif</span></li>
              <li class="val"><strong>Lieu(x)</strong><span>Paris</span></li>
              <li class="val"><strong>Durée</strong><span>00:15:00</span></li>
            </ul>
            <div class="diaKeywords">PCF | mouvement ouvrier</div>
            <div class="diaMain">Magazine d'actualités et de mémoire politique.</div>
          </body>
        </html>
        """
        record = parse_cinearchives_detail_page(
            html,
            "https://www.cinearchives.org/catalogue-reflets-1104-239-1-0.html",
        )

        self.assertEqual(record["record_id"], "239")
        self.assertEqual(record["video_link"], "https://diazcinearchives.oembed.diazinteregio.org/embed/CineA-1964-Reflets-210-1_1?feature=oembed")
        self.assertEqual(record["date"], "1964")
        self.assertTrue(record["embedded"])
        self.assertIn("Collectif", record["subject"])
        self.assertIn("mouvement ouvrier", record["subject"])

    def test_cinearchives_theme_and_access_are_specific(self):
        row = {
            "platform": "Ciné-Archives",
            "video_link": "https://diazcinearchives.oembed.diazinteregio.org/embed/CineA-1964-Reflets",
            "video_title": "Manifestation du PCF et de la CGT",
            "video_subject": "mouvement ouvrier",
            "video_description": "Archives politiques du mouvement communiste.",
        }

        self.assertEqual(infer_video_theme(row), "Vida pública, política e história")
        self.assertEqual(classify_access_surface(row), "Arquivo audiovisual institucional")


if __name__ == "__main__":
    unittest.main()
