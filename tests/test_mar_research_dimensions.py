"""Validate Streamlit scientific research dimensions before publishing Next.js pages."""
import csv
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"output"
SITE=ROOT/"site"
DIMENSIONS=("resumo_temas","tema_pais","tema_plataforma","tema_tipo_arquivo","linha_do_tempo_corpus","resumo_instituicoes")

class ResearchDimensionsTests(unittest.TestCase):
 def test_each_report_has_compatible_source_tables(self):
  reports=[]
  for i in range(6):
   reports+=json.loads((SITE/f"data/analytics-{i}.json").read_text(encoding="utf-8"))
  self.assertEqual(len(reports),62)
  for report in reports:
   for dim in DIMENSIONS:
    file=DATA/f'{report["code"]}_{dim}.csv'
    self.assertTrue(file.exists(),f"Missing source {file}")
    with file.open(encoding="utf-8-sig",newline="") as handle:
     rows=csv.DictReader(handle)
     self.assertTrue(rows.fieldnames,f"Missing header {file}")
     self.assertTrue(all(rows.fieldnames),f"Unnamed field {file}")
     if dim in ("tema_pais","tema_plataforma","resumo_temas"):
      self.assertIn("total",rows.fieldnames)
     if dim=="linha_do_tempo_corpus":
      self.assertIn("snapshot_generated_at",rows.fieldnames)

 def test_no_record_level_media_or_secrets_in_research_pages(self):
  for path in ("site/lib/research-dimensions.ts","site/components/research-explorer.tsx","site/app/(pt)/pesquisa/[code]/page.tsx"):
   content=(ROOT/path).read_text(encoding="utf-8")
   for banned in ("DATABASE_URL","<video","<iframe","fetch(","NEXT_PUBLIC_SECRET"):
    self.assertNotIn(banned,content)

if __name__=="__main__":
 unittest.main()
