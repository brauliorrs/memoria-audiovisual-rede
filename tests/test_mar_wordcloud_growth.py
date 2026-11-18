"""The title cloud must follow new and updated source catalogues, not frozen counts."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import build_mar_title_wordcloud as cloud

VOCABULARY = (
    "memoria patrimonio infancia comunidade cultura historia territorio "
    "escola trabalho viagem paisagem comunidade fotografia musica patrimonio "
    "festival movimento cidade natureza familia comunidade pesquisa arquitetura "
    "sociedade politica educacao"
).split()
UNIQUE_TERMS = list(dict.fromkeys(VOCABULARY))


class WordCloudGrowthTests(unittest.TestCase):
    def write_catalog(self, root: Path, code: str, size: int):
        path = root / "data" / "output" / f"{code}_catalogo_videos_analitico.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["video_title", "video_title_display"])
            writer.writeheader()
            for n in range(size):
                writer.writerow({
                    "video_title": " ".join(UNIQUE_TERMS) + f" observacao {n:03d}",
                    "video_title_display": "",
                })
        return path

    def test_new_source_and_more_titles_change_the_aggregate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "site" / "data").mkdir(parents=True)
            (root / "site" / "data" / "kavi-public.json").write_text(
                json.dumps({
                    "approvedMetadataPublication": True, "total": 1,
                    "records": [{"title": "Memoria do cinema documental"}],
                }), encoding="utf-8",
            )
            for n in range(60):
                self.write_catalog(root, f"fixture{n:02d}", 21)
            with patch.object(cloud, "ROOT", root):
                initial = cloud.build()
                self.assertEqual(initial["corporaProcessed"], 61)
                self.assertEqual(initial["titlesExamined"], 60 * 21 + 1)
                self.assertGreaterEqual(len(initial["words"]), 18)
                base = next(w for w in initial["words"] if w["text"] == "memoria")

                self.write_catalog(root, "additional", 21)
                grown = cloud.build()
                added = next(w for w in grown["words"] if w["text"] == "memoria")
                self.assertEqual(grown["corporaProcessed"], 62)
                self.assertEqual(grown["titlesExamined"], initial["titlesExamined"] + 21)
                self.assertEqual(added["count"], base["count"] + 21)
                self.assertEqual(added["corpora"], base["corpora"] + 1)
                self.assertIn("additional", {s["code"] for s in grown["sourceProvenance"]})
                self.assertFalse(grown["individualRecordsPublished"])
                self.assertFalse(grown["rawTitlesPublished"])

                updated_path = self.write_catalog(root, "additional", 29)
                updated = cloud.build()
                appended = next(w for w in updated["words"] if w["text"] == "memoria")
                self.assertEqual(updated["corporaProcessed"], grown["corporaProcessed"])
                self.assertEqual(updated["titlesExamined"], grown["titlesExamined"] + 8)
                self.assertEqual(appended["count"], added["count"] + 8)
                self.assertTrue(updated_path.exists())
                self.assertNotIn("records", updated)
                self.assertNotIn("video_title", json.dumps(updated))


if __name__ == "__main__":
    unittest.main()
