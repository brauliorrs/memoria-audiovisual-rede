import unittest

from memoria_audiovisual.analysis import classify_access_regime, classify_access_surface
from memoria_audiovisual.config import PPA_HOME_URL
from memoria_audiovisual.crawler import classify_platform, is_probably_video_link
from memoria_audiovisual.ppa import (
    _extract_record_id,
    collect_ppa_institutions,
    parse_ppa_search_results,
)


class PpaCollectionTests(unittest.TestCase):
    def test_collect_ppa_institutions_declares_single_aggregator(self):
        institutions = collect_ppa_institutions()

        self.assertEqual(len(institutions), 1)
        record = institutions[0]
        self.assertEqual(record["institution"], "Portal Português de Arquivos")
        self.assertEqual(record["external_url"], PPA_HOME_URL)
        self.assertEqual(record["ppa_detail_url"], PPA_HOME_URL)
        self.assertTrue(record["content_available_in_source"])
        self.assertEqual(record["archive_type"], "National archival aggregator")

    def test_extract_record_id_accepts_ppa_record_urls(self):
        self.assertEqual(
            _extract_record_id("record?id=oai%3APT%2FMVFX-ARQ%3A303127&s='abc'"),
            "oai:PT/MVFX-ARQ:303127",
        )
        self.assertEqual(
            _extract_record_id("record;jsessionid=ABC?id=oai%3Ax-arq.cm-cascais.pt%3A58129&s=abc"),
            "oai:x-arq.cm-cascais.pt:58129",
        )

    def test_parse_search_results_detects_records_and_original_source_links(self):
        html = """
        <html><body>
        You search for audiovisual and 81 records were found.
        <div class="row-fluid record">
          <div class="span12 title">
            <h2><a href="record?id=oai%3APT%2FMVFX-ARQ%3A303127&s='abc'">Arquivo Audiovisual da RTP</a></h2>
          </div>
          <div class="span12 subjects">Divulga filmes e reportagens. Dates: 1957-</div>
          <div class="span12 archiveLink"><span>Data source:</span>
            <a href="https://arquivo.cm-vfxira.pt/">Câmara Municipal de Vila Franca de Xira</a>
          </div>
          <div class="originalLink"><a href="https://arquivo.cm-vfxira.pt/details?id=303127">Original record</a></div>
        </div>
        </body></html>
        """

        records, result_count = parse_ppa_search_results(
            html,
            "https://portal.arquivos.pt/search?q=audiovisual",
            "audiovisual",
        )

        self.assertEqual(result_count, 81)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["record_id"], "oai:PT/MVFX-ARQ:303127")
        self.assertEqual(records[0]["data_source"], "Câmara Municipal de Vila Franca de Xira")
        self.assertTrue(records[0]["external_source_detected"])
        self.assertEqual(records[0]["date"], "1957-")

    def test_ppa_urls_are_classified_as_national_aggregator_surface(self):
        item_url = "https://portal.arquivos.pt/record?id=oai%3APT%2FMVFX-ARQ%3A303127"

        self.assertEqual(classify_platform(item_url), "Portal Português de Arquivos")
        self.assertTrue(is_probably_video_link(item_url, "Portal Português de Arquivos"))
        self.assertEqual(
            classify_access_surface(
                {
                    "platform": "Portal Português de Arquivos",
                    "video_link": item_url,
                    "video_description": "registro descritivo com ligação à fonte original detectada",
                }
            ),
            "Registro descritivo em agregador arquivístico nacional",
        )
        self.assertEqual(
            classify_access_regime(
                ["Registro descritivo em agregador arquivístico nacional"],
                "Evidência pública detectável de audiovisual",
            ),
            "Acesso descritivo por agregador arquivístico nacional",
        )


if __name__ == "__main__":
    unittest.main()
