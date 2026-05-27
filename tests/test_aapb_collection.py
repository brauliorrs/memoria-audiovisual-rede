import unittest

from memoria_audiovisual.aapb import (
    AAPB_API_URL_TEMPLATE,
    collect_aapb_institutions,
    parse_aapb_api_payload,
)
from memoria_audiovisual.analysis import classify_access_surface
from memoria_audiovisual.crawler import classify_platform, is_probably_video_link


SAMPLE_XML = """
<pbcoreDescriptionDocument xmlns="http://www.pbcore.org/PBCore/PBCoreNamespace.html">
  <pbcoreTitle titleType="Title">Illustrated Daily; Video on Video</pbcoreTitle>
  <pbcoreDescription>Episode about video art and television.</pbcoreDescription>
  <pbcoreSubject>Television</pbcoreSubject>
  <pbcoreCreator><creator>KNME-TV</creator></pbcoreCreator>
  <pbcorePublisher><publisher>KNME-TV</publisher></pbcorePublisher>
  <pbcoreAssetDate>1983-06-14</pbcoreAssetDate>
  <pbcoreInstantiation>
    <instantiationMediaType>Moving Image</instantiationMediaType>
    <instantiationDuration>00:30:00</instantiationDuration>
  </pbcoreInstantiation>
</pbcoreDescriptionDocument>
"""

SOUND_ONLY_XML = """
<pbcoreDescriptionDocument xmlns="http://www.pbcore.org/PBCore/PBCoreNamespace.html">
  <pbcoreTitle titleType="Title">Film Discussion</pbcoreTitle>
  <pbcoreDescription>Radio discussion about cinema.</pbcoreDescription>
  <pbcoreInstantiation>
    <instantiationMediaType>Sound</instantiationMediaType>
  </pbcoreInstantiation>
</pbcoreDescriptionDocument>
"""


class AapbCollectionTests(unittest.TestCase):
    def test_collect_aapb_institutions_declares_single_aggregator(self):
        institutions = collect_aapb_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["institution"], "American Archive of Public Broadcasting")
        self.assertEqual(institutions[0]["archive_type"], "National audiovisual aggregator")

    def test_parse_aapb_api_payload_extracts_pbcore_fields(self):
        payload = {
            "response": {
                "numFound": 1,
                "docs": [
                    {
                        "id": "cpb-aacip-test",
                        "title": "Illustrated Daily; Video on Video",
                        "timestamp": "2019-01-01T00:00:00Z",
                        "xml": SAMPLE_XML,
                    }
                ],
            }
        }

        records, total = parse_aapb_api_payload(payload, "video")

        self.assertEqual(total, 1)
        self.assertEqual(records[0]["record_id"], "cpb-aacip-test")
        self.assertEqual(records[0]["media_types"], "Moving Image")
        self.assertEqual(records[0]["date"], "1983-06-14")

    def test_parse_aapb_api_payload_discards_sound_only_records(self):
        payload = {
            "response": {
                "numFound": 1,
                "docs": [
                    {
                        "id": "cpb-aacip-sound-only",
                        "title": "Film Discussion",
                        "xml": SOUND_ONLY_XML,
                    }
                ],
            }
        }

        records, total = parse_aapb_api_payload(payload, "film")

        self.assertEqual(total, 1)
        self.assertEqual(records, [])

    def test_aapb_urls_are_classified_as_audiovisual_surface(self):
        item_url = "https://americanarchive.org/catalog/cpb-aacip-test"

        self.assertEqual(classify_platform(item_url), "American Archive of Public Broadcasting")
        self.assertTrue(is_probably_video_link(item_url, "American Archive of Public Broadcasting"))
        self.assertEqual(
            classify_access_surface(
                {
                    "platform": "American Archive of Public Broadcasting",
                    "video_link": item_url,
                }
            ),
            "acesso em agregador audiovisual",
        )

    def test_api_url_template_keeps_rows_parameter(self):
        url = AAPB_API_URL_TEMPLATE.format(query="video", rows=2)

        self.assertIn("api.json", url)
        self.assertIn("rows=2", url)


if __name__ == "__main__":
    unittest.main()
