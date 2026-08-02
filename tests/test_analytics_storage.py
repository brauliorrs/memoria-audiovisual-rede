from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.analytics.base import IndicatorResult
from memoria_audiovisual.analytics.engine import AnalyticsRun
from memoria_audiovisual.analytics.storage import AnalyticsStore


class AnalyticsStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "analytics"
        self.store = AnalyticsStore(self.root)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    @staticmethod
    def _run(snapshot_id: str = "snapshot_2026_09") -> AnalyticsRun:
        result = IndicatorResult(
            indicator_id="api_coverage",
            indicator_version="1.0.0",
            methodology_version="1.0.0",
            snapshot_id=snapshot_id,
            title="Cobertura de APIs",
            category="infrastructure",
            value=50.0,
            unit="percent",
            numerator=1,
            denominator=2,
            corpus_count=2,
        )
        return AnalyticsRun(
            snapshot_id=snapshot_id,
            methodology_version="1.0.0",
            indicator_count=1,
            results=(result,),
        )

    def test_persiste_snapshot_manifesto_e_historico(self) -> None:
        manifest = self.store.write(self._run())
        self.assertEqual(manifest.indicator_count, 1)
        self.assertTrue((self.root / "snapshot_2026_09/snapshot_indicators.json").exists())
        self.assertTrue((self.root / "snapshot_2026_09/manifest.json").exists())
        history = (self.root / "indicator_history.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(history), 1)
        record = json.loads(history[0])
        self.assertEqual(record["indicator_id"], "api_coverage")
        self.assertTrue(record["indicators_sha256"])

    def test_bloqueia_sobrescrita_do_mesmo_snapshot(self) -> None:
        run = self._run()
        self.store.write(run)
        with self.assertRaises(FileExistsError):
            self.store.write(run)

    def test_bloqueia_execucao_com_erros(self) -> None:
        run = self._run()
        invalid = AnalyticsRun(
            snapshot_id=run.snapshot_id,
            methodology_version=run.methodology_version,
            indicator_count=run.indicator_count,
            results=run.results,
            status="completed_with_errors",
            errors=("falha",),
        )
        with self.assertRaisesRegex(ValueError, "sem erro"):
            self.store.write(invalid)

    def test_verificacao_detecta_adulteracao(self) -> None:
        self.store.write(self._run())
        path = self.root / "snapshot_2026_09/snapshot_indicators.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["results"][0]["value"] = 99.0
        path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "hash"):
            self.store.verify("snapshot_2026_09")

    def test_historico_append_only_aceita_outro_snapshot(self) -> None:
        self.store.write(self._run("snapshot_2026_09"))
        self.store.write(self._run("snapshot_2026_10"))
        history = (self.root / "indicator_history.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(history), 2)


if __name__ == "__main__":
    unittest.main()
