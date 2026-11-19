"""Offline fail-closed contracts for Streamlit -> static Next.js research projections."""
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_mar_site_research_projections import SnapshotDrift, run  # noqa: E402


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def write_csv(path, headers, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(records)


class CoherenceContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        out = self.root / "data/output"
        web = self.root / "site/data"
        report = {
            "total_institutions": 1, "with_video_count": 1, "with_embeds_count": 0,
            "status_summary": {"ok": 1}, "integrity_summary": {"integro": 1},
            "platform_summary": {"Catalog": 1}, "continent_summary": {"Europe": 1},
            "video_continent_summary": {"Europe": 1},
        }
        write_json(out / "sample_relatorio.json", report)
        self.report = out / "sample_relatorio.json"
        self.projection = {
            "code": "sample", "source": "data/output/sample_relatorio.json",
            "totalInstitutions": 1, "institutionsWithVideo": 1, "withEmbeds": 0,
            "siteStatus": {"ok": 1}, "integrity": {"integro": 1},
            "platforms": {"Catalog": 1}, "continents": {"Europe": 1},
            "videoContinents": {"Europe": 1},
        }
        write_json(web / "analytics-0.json", [self.projection])
        for name, keys in [
            ("tema_pais", ["tema", "pais", "total"]),
            ("tema_plataforma", ["tema", "plataforma", "total"]),
            ("linha_do_tempo_corpus", ["dataset", "observation_key", "snapshot_generated_at"]),
        ]:
            row = {key: "1" for key in keys}
            write_csv(out / f"sample_{name}.csv", keys, [row])
        write_json(web / "research-slices-0.json", {
            "sample": {
                name: {
                    "source": f"data/output/sample_{name}.csv",
                    "rows": [{key: "1" for key in keys}],
                }
                for name, keys in [
                    ("tema_pais", ["tema", "pais", "total"]),
                    ("tema_plataforma", ["tema", "plataforma", "total"]),
                    ("linha_do_tempo_corpus", ["dataset", "observation_key", "snapshot_generated_at"]),
                ]
            }
        })
        write_csv(
            out / "sample_instituicoes.csv",
            ["institution", "country", "continent", "archive_type", "repository_code", "external_url"],
            [{"institution": "Sample", "country": "France", "continent": "Europe",
              "archive_type": "Film archive", "repository_code": "FR-S", "external_url": "https://example.org/archive"}],
        )
        write_json(web / "institution-profiles-0.json", {
            "sample": {"source": "data/output/sample_instituicoes.csv", "sampled": False,
                       "rows": [{"id": "sample:1", "name": "Sample", "country": "France",
                                 "continent": "Europe", "type": "Film archive",
                                 "repositoryCode": "FR-S", "originUrl": "https://example.org/archive"}]}
        })
        write_csv(
            out / "observatorio_indice_dados_publicos_por_corpus.csv",
            ["corpus_code", "public_records", "restricted_records", "materialized_records_total"],
            [{"corpus_code": "sample", "public_records": "3", "restricted_records": "2",
              "materialized_records_total": "5"}],
        )
        write_csv(out / "observatorio_unidades_acesso_restrito_indice.csv", ["unit_code"], [])
        write_csv(out / "observatorio_unidades_identificadas_nao_incorporadas.csv", ["unit_code"], [])
        write_json(web / "public-access-observatory.json", {
            "publicationOfIndividualRecordsNotAuthorizedByThisFile": True,
            "summary": {"historicalPublicSurfaceRecords": 3, "historicalRestrictedRecords": 2,
                        "historicalMaterializedTotal": 5, "historicalCorpusRows": 1,
                        "additionalIdentifiedRestrictedUnits": 0},
            "corpora": [{"code": "sample", "recordDisplay": "not_authorized_for_new_site",
                        "historicalPublicSurfaceRecords": 3, "historicalRestrictedRecords": 2,
                        "historicalTotal": 5, "humanAccessEvidence": "reviewed-source-only"}]
        })
        write_json(web / "documented-cases.json", {"publicationAuthorized": False, "cases": []})

    def test_current_projection_passes(self):
        run(self.root)

    def test_source_change_detected_then_safely_regenerated(self):
        changed = json.loads(self.report.read_text())
        changed["with_video_count"] = 0
        write_json(self.report, changed)
        with self.assertRaisesRegex(SnapshotDrift, "analytics stale"):
            run(self.root)
        run(self.root, write=True)
        run(self.root)
        snapshot = json.loads((self.root / "site/data/analytics-0.json").read_text())
        self.assertEqual(snapshot[0]["institutionsWithVideo"], 0)

    def test_access_review_never_auto_overwritten(self):
        file = self.root / "site/data/public-access-observatory.json"
        inventory = json.loads(file.read_text())
        inventory["corpora"][0]["recordDisplay"] = "published"
        write_json(file, inventory)
        original = file.read_bytes()
        with self.assertRaisesRegex(SnapshotDrift, "illicitly promoted"):
            run(self.root, write=True)
        self.assertEqual(original, file.read_bytes())

    def test_new_corpus_requires_curatorial_inventory_alignment(self):
        original = (self.root / "site/data/analytics-0.json").read_bytes()
        extra = json.loads(self.report.read_text())
        write_json(self.root / "data/output/new_relatorio.json", extra)
        for suffix in ("tema_pais", "tema_plataforma", "linha_do_tempo_corpus"):
            p = self.root / "data/output" / f"sample_{suffix}.csv"
            (self.root / "data/output" / f"new_{suffix}.csv").write_bytes(p.read_bytes())
        p = self.root / "data/output/sample_instituicoes.csv"
        (self.root / "data/output/new_instituicoes.csv").write_bytes(p.read_bytes())
        with self.assertRaisesRegex(SnapshotDrift, "corpus coverage"):
            run(self.root, write=True)
        self.assertEqual(original, (self.root / "site/data/analytics-0.json").read_bytes())

    def test_research_values_cannot_drift_silently(self):
        p = self.root / "data/output/sample_tema_pais.csv"
        write_csv(p, ["tema", "pais", "total"],
                  [{"tema": "Cinema", "pais": "France", "total": "42"}])
        with self.assertRaisesRegex(SnapshotDrift, "research-slices stale"):
            run(self.root)

    def test_institutional_source_is_immutable_authority(self):
        p = self.root / "data/output/sample_instituicoes.csv"
        write_csv(p, ["institution", "country", "continent", "archive_type", "repository_code", "external_url"],
                  [{"institution": "Changed", "country": "France", "continent": "Europe",
                    "archive_type": "Film archive", "repository_code": "FR-S",
                    "external_url": "https://example.org/archive"}])
        with self.assertRaisesRegex(SnapshotDrift, "institution-profiles stale"):
            run(self.root)


if __name__ == "__main__":
    unittest.main()
