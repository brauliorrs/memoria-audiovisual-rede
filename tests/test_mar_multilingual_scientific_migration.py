"""Contract tests for scientific thematics, snapshot time series, and institution facts."""
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"site"

def load(prefix,count):
    chunks=[json.loads((SITE/f"data/{prefix}-{i}.json").read_text(encoding="utf-8")) for i in range(count)]
    result={}
    for c in chunks:
        assert result.keys().isdisjoint(c.keys()), "duplicate source across batches"
        result.update(c)
    return result

RESEARCH=load("research-slices",16)
INSTITUTIONS=load("institution-profiles",7)
ANALYTICS={}
for i in range(6):
    for row in json.loads((SITE/f"data/analytics-{i}.json").read_text(encoding="utf-8")):
        ANALYTICS[row["code"]]=row


class MultilingualScienceMigrationTests(unittest.TestCase):
    def test_all_62_source_files_reviewed(self):
        self.assertEqual(set(RESEARCH),set(ANALYTICS))
        self.assertEqual(set(INSTITUTIONS),set(ANALYTICS))
        self.assertEqual(len(RESEARCH),62)
        self.assertTrue(all(c["linha_do_tempo_corpus"]["rows"] for c in RESEARCH.values()))
        self.assertTrue(all(c["tema_pais"]["source"].endswith("_tema_pais.csv") for c in RESEARCH.values()))

    def test_cross_tabulations_not_individual_media(self):
        for code,data in RESEARCH.items():
            for field,header in (("tema_pais",("tema","pais","total")),
                                 ("tema_plataforma",("tema","plataforma","total"))):
                for row in data[field]["rows"]:
                    self.assertTrue(set(row)>=set(header),f"{code} {field}")
                    self.assertTrue(row["total"].isdigit(),f"invalid occurrence at {code} {field}")
                    self.assertGreaterEqual(int(row["total"]),0)
                    self.assertFalse(any(x in row for x in ("video_link","video_description","media_url","creator_email")))

    def test_time_series_are_observations_not_film_dates(self):
        for code,data in RESEARCH.items():
            for item in data["linha_do_tempo_corpus"]["rows"]:
                self.assertTrue(item["snapshot_generated_at"])
                self.assertIn("observation_key",item)
                self.assertIn("video_links_total",item)
                self.assertNotIn("video_link",item)
        self.assertGreaterEqual(len(RESEARCH["eye"]["linha_do_tempo_corpus"]["rows"]),4)

    def test_all_institutional_facts_and_source_attribution(self):
        self.assertEqual(len(INSTITUTIONS),62)
        self.assertEqual(sum(len(g["rows"]) for g in INSTITUTIONS.values()),1314)
        self.assertEqual(len(INSTITUTIONS["ape"]["rows"]),1253)
        self.assertFalse(INSTITUTIONS["ape"]["sampled"])
        self.assertIn("archivesportaleurope.net",INSTITUTIONS["ape"]["licencePolicy"])
        self.assertTrue(any("sem nome" in row["name"].lower() for row in INSTITUTIONS["ape"]["rows"]))
        for code,group in INSTITUTIONS.items():
            self.assertTrue(group["source"].startswith("data/output/"))
            for row in group["rows"]:
                self.assertTrue(row["name"])
                self.assertRegex(row["id"],r"^"+re.escape(code)+r":[0-9]+$")
                self.assertFalse(any(k in row for k in ("video_link","video_description","embed_url","personal_email")))

    def test_routes_translation_and_data_boundaries(self):
        locale=(SITE/"components/site-locale.tsx").read_text(encoding="utf-8")
        header=(SITE/"components/site-header.tsx").read_text(encoding="utf-8")
        layout=(SITE/"components/site-shell.tsx").read_text(encoding="utf-8")
        self.assertIn("LocaleProvider",layout)
        for key in ('pt:', 'en:', 'es:', '"mar-ui-lang"'):
            self.assertIn(key,locale)
        for path in ('"/temas/"','"/series/"','"/instituicoes/pesquisa/"'):
            self.assertIn(path,header)
        for p in ("site/app/(pt)/temas/page.tsx","site/app/(pt)/series/page.tsx",
                  "site/app/(pt)/instituicoes/pesquisa/page.tsx",
                  "site/app/(pt)/instituicoes/pesquisa/[source]/[entry]/page.tsx"):
            code=(ROOT/p).read_text(encoding="utf-8")
            for forbidden in ("fetch(", "<iframe", "<video", "DATABASE_URL", "api.finna.fi"):
                self.assertNotIn(forbidden,code)
        profiles=(SITE/"app/(pt)/instituicoes/pesquisa/[source]/[entry]/page.tsx").read_text(encoding="utf-8")
        self.assertIn("generateStaticParams",profiles)
        self.assertIn("institutionalProfiles.map",profiles)
        workbench=(SITE/"components/research-workbench.tsx").read_text(encoding="utf-8")
        self.assertIn("independentFacets",workbench)
        self.assertIn("chronologicalObservations",workbench)


if __name__=="__main__":unittest.main()
