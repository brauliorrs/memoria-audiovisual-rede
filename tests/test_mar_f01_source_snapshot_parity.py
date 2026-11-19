"""F01 historical source-vs-site parity with adversarial drift injection."""
import copy
import unittest
from pathlib import Path

from scripts.check_mar_f01_source_snapshot_parity import (
    ROOT, audit_access_index, audit_cases, audit_kavi, check, read_csv
)
import json

DATA = ROOT / "data/output"
SITE = ROOT / "site/data"


def load(name):
    return json.loads((SITE / name).read_text(encoding="utf-8"))


class F01SourceSnapshotParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = read_csv(DATA / "observatorio_indice_dados_publicos.csv")
        cls.by_corpus = read_csv(DATA / "observatorio_indice_dados_publicos_por_corpus.csv")
        cls.site_index = load("public-access-observatory.json")
        cls.kavi_path = DATA / "kavi_mar_metadata_links.csv"
        cls.kavi_bytes = cls.kavi_path.read_bytes()
        cls.kavi_rows = read_csv(cls.kavi_path)
        cls.kavi_manifest = json.loads(
            (DATA / "kavi_mar_metadata_links_manifest.json").read_text(encoding="utf-8")
        )
        cls.site_kavi = load("kavi-public.json")
        cls.cases_rows = read_csv(DATA / "observatorio_unidades_identificadas_nao_incorporadas.csv")
        cls.site_cases = load("documented-cases.json")

    def test_three_existing_snapshot_contracts_match_sources(self):
        self.assertEqual(check(), {"M02": [], "M03": [], "M19": []})

    def test_every_historical_corpus_checked_against_source(self):
        self.assertEqual(
            audit_access_index(self.index, self.by_corpus, self.site_index), []
        )
        self.assertEqual(len(self.by_corpus), 60)
        self.assertEqual(len(self.site_index["corpora"]), 63)

    def test_single_historical_corpus_count_drift_fails(self):
        altered = copy.deepcopy(self.site_index)
        item = next(x for x in altered["corpora"] if x["code"] == "archipop")
        item["historicalTotal"] += 1
        self.assertTrue(audit_access_index(self.index, self.by_corpus, altered))

    def test_missing_corpus_fails(self):
        altered = copy.deepcopy(self.site_index)
        altered["corpora"].pop()
        self.assertTrue(audit_access_index(self.index, self.by_corpus, altered))

    def test_duplicate_corpus_fails(self):
        altered = copy.deepcopy(self.site_index)
        altered["corpora"].append(copy.deepcopy(altered["corpora"][0]))
        self.assertTrue(audit_access_index(self.index, self.by_corpus, altered))

    def test_historical_public_access_is_never_publication_approval(self):
        altered = copy.deepcopy(self.site_index)
        altered["publicationOfIndividualRecordsNotAuthorizedByThisFile"] = False
        self.assertTrue(audit_access_index(self.index, self.by_corpus, altered))

    def test_historical_record_cannot_be_promoted_from_hold(self):
        altered = copy.deepcopy(self.site_index)
        altered["corpora"][0]["recordDisplay"] = "published"
        self.assertTrue(audit_access_index(self.index, self.by_corpus, altered))

    def test_kavi_hash_tamper_is_rejected(self):
        altered = copy.deepcopy(self.kavi_manifest)
        altered["catalog_sha256"] = "0" * 64
        self.assertTrue(audit_kavi(self.kavi_rows, self.kavi_bytes, altered, self.site_kavi))

    def test_kavi_title_tamper_is_rejected(self):
        altered = copy.deepcopy(self.site_kavi)
        altered["records"][0]["title"] += " forged"
        self.assertTrue(audit_kavi(self.kavi_rows, self.kavi_bytes, self.kavi_manifest, altered))

    def test_kavi_unreviewed_media_added_is_rejected(self):
        altered = copy.deepcopy(self.site_kavi)
        altered["records"][0]["video_url"] = "https://example.org/movie"
        self.assertTrue(audit_kavi(self.kavi_rows, self.kavi_bytes, self.kavi_manifest, altered))

    def test_kavi_media_rights_auto_promotion_is_rejected(self):
        altered = copy.deepcopy(self.site_kavi)
        altered["mediaRightsVerified"] = True
        self.assertTrue(audit_kavi(self.kavi_rows, self.kavi_bytes, self.kavi_manifest, altered))

    def test_case_editorial_decision_tamper_is_rejected(self):
        altered = copy.deepcopy(self.site_cases)
        altered["cases"][0]["reason"] = "There is no audiovisual collection"
        self.assertTrue(audit_cases(self.cases_rows, altered))

    def test_case_cannot_automatically_authorize_publication(self):
        altered = copy.deepcopy(self.site_cases)
        altered["publicationAuthorized"] = True
        self.assertTrue(audit_cases(self.cases_rows, altered))

    def test_missing_case_source_is_rejected(self):
        source = copy.deepcopy(self.cases_rows)
        source = [x for x in source if x["unit_code"] != self.site_cases["cases"][0]["code"]]
        self.assertTrue(audit_cases(source, self.site_cases))


if __name__ == "__main__":
    unittest.main()
