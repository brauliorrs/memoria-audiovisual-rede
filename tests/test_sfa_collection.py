import unittest

from memoria_audiovisual.analysis import classify_access_surface
from memoria_audiovisual.crawler import classify_platform, is_probably_video_link
from memoria_audiovisual.sfa import (
    collect_sfa_institutions,
    parse_sfa_vac_detail_page,
    parse_sfa_vac_fund_page,
)


SFA_DETAIL_HTML = """
<html><body>
<h3>SI AS 1086/1219 To so gadi, 1977 (Združeni dokumenti)</h3>
<div id="archivePlanTreePrevData">
  <ul data-id="389405" data-title="SI AS 1086/1218 Ta hiša je moja, pa vendar moja ni (1976)"></ul>
</div>
<div id="archivePlanTreeNextData">
  <ul data-id="389407" data-title="SI AS 1086/1220 Vdovstvo Karoline Žašler (1976)"></ul>
</div>
<div class="row">
  <label class="form-control-label form-control-sm">Signatura PE:</label>
  <label class="form-control-label form-control-sm">SI AS 1086/1219</label>
</div>
<div class="row">
  <label class="form-control-label form-control-sm">Naslov PE:</label>
  <label class="form-control-label form-control-sm">To so gadi</label>
</div>
<div class="row">
  <label class="form-control-label form-control-sm">Čas nastanka PE:</label>
  <label class="form-control-label form-control-sm">1977</label>
</div>
<div class="row">
  <label class="form-control-label form-control-sm">Zvrsti arhivskega gradiva:</label>
  <label class="form-control-label form-control-sm">filmsko gradivo</label>
</div>
<div class="row">
  <label class="form-control-label form-control-sm">Zvrst filma:</label>
  <label class="form-control-label form-control-sm">igrani</label>
</div>
<div class="row">
  <label class="form-control-label form-control-sm">Podzvrst filma:</label>
  <label class="form-control-label form-control-sm">mladinski</label>
</div>
<div class="row">
  <label class="form-control-label form-control-sm">Vsebina PE:</label>
  <label class="form-control-label form-control-sm">Burka iz predmestja.</label>
</div>
</body></html>
"""


SFA_FUND_HTML = """
<html><body>
<h3>SI AS 1086 Zbirka filmov, 1905-2024 (Fond/zbirka)</h3>
<div class="row">
  <label class="form-control-label form-control-sm">Signatura PE:</label>
  <label class="form-control-label form-control-sm">SI AS 1086</label>
</div>
<div class="row">
  <label class="form-control-label form-control-sm">Naslov PE:</label>
  <label class="form-control-label form-control-sm">Zbirka filmov</label>
</div>
<div class="row">
  <label class="form-control-label form-control-sm">Čas nastanka PE:</label>
  <label class="form-control-label form-control-sm">1905 - 2024</label>
</div>
<div class="row">
  <label class="form-control-label form-control-sm">Količina PE:</label>
  <label class="form-control-label form-control-sm">13.504 naslovov</label>
</div>
<div class="row">
  <label class="form-control-label form-control-sm">Zvrsti arhivskega gradiva:</label>
  <label class="form-control-label form-control-sm">filmsko gradivo</label>
</div>
</body></html>
"""


class SfaCollectionTests(unittest.TestCase):
    def test_collect_sfa_institutions_declares_single_archive(self):
        institutions = collect_sfa_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["repository_code"], "SI-AS-1086")
        self.assertEqual(institutions[0]["country"], "Slovenia")

    def test_parse_sfa_vac_detail_page_extracts_film_metadata(self):
        record = parse_sfa_vac_detail_page(
            SFA_DETAIL_HTML,
            "https://vac.sjas.gov.si/vac/search/details?id=389406",
        )

        self.assertEqual(record["platform"], "VAC")
        self.assertEqual(record["title"], "To so gadi")
        self.assertEqual(record["date"], "1977")
        self.assertIn("igrani", record["subject"])
        self.assertIn("sem player", record["description"])
        self.assertEqual(record["neighbors"], ["389405", "389407"])

    def test_parse_sfa_vac_fund_page_extracts_collection_metadata(self):
        fund = parse_sfa_vac_fund_page(SFA_FUND_HTML)

        self.assertEqual(fund["signature"], "SI AS 1086")
        self.assertEqual(fund["title"], "Zbirka filmov")
        self.assertIn("13.504", fund["quantity"])

    def test_sfa_vac_urls_are_classified_as_catalog_surface(self):
        url = "https://vac.sjas.gov.si/vac/search/details?id=389406"

        self.assertEqual(classify_platform(url), "VAC")
        self.assertTrue(is_probably_video_link(url, "VAC"))
        self.assertEqual(
            classify_access_surface({"platform": "VAC", "video_link": url}),
            "Catálogo arquivístico audiovisual institucional",
        )


if __name__ == "__main__":
    unittest.main()
