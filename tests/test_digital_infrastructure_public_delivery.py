from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.digital_infrastructure.public_delivery import build_public_delivery


class PublicDeliveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "public"
        self.root.mkdir(parents=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _write_json(self, path: Path, payload) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def test_builds_stable_delivery_from_active_registry(self) -> None:
        events_path = self.root / "snapshot_1/revisions/revision_0001/events.json"
        self._write_json(
            events_path,
            [{"event_id": "event_1", "snapshot_id": "snapshot_1", "corpus_code": "ina"}],
        )
        self._write_json(
            self.root / "active_publications.json",
            {
                "snapshot_1": {
                    "snapshot_id": "snapshot_1",
                    "publication_id": "snapshot_1:publication_revision:1",
                    "publication_kind": "publication_revision",
                    "publication_revision": 1,
                    "events_path": str(events_path),
                    "event_count": 1,
                    "activated_at": "2026-08-01T20:00:00+00:00",
                }
            },
        )

        manifest = build_public_delivery(self.root)

        self.assertEqual(manifest.item_count, 1)
        self.assertEqual(manifest.total_event_count, 1)
        events = json.loads((self.root / "delivery/events.json").read_text(encoding="utf-8"))
        self.assertEqual(events[0]["active_publication_id"], "snapshot_1:publication_revision:1")
        delivery_manifest = json.loads(
            (self.root / "delivery/manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(delivery_manifest["publications"][0]["content_sha256"]), 64)

    def test_missing_source_blocks_delivery(self) -> None:
        self._write_json(
            self.root / "active_publications.json",
            {
                "snapshot_1": {
                    "snapshot_id": "snapshot_1",
                    "publication_id": "snapshot_1:initial",
                    "publication_kind": "initial",
                    "publication_revision": None,
                    "events_path": str(self.root / "missing/events.json"),
                    "event_count": 0,
                    "activated_at": "2026-08-01T20:00:00+00:00",
                }
            },
        )
        with self.assertRaises(FileNotFoundError):
            build_public_delivery(self.root)

    def test_count_mismatch_blocks_delivery(self) -> None:
        events_path = self.root / "snapshot_1/events.json"
        self._write_json(events_path, [{"event_id": "event_1", "snapshot_id": "snapshot_1"}])
        self._write_json(
            self.root / "active_publications.json",
            {
                "snapshot_1": {
                    "snapshot_id": "snapshot_1",
                    "publication_id": "snapshot_1:initial",
                    "publication_kind": "initial",
                    "publication_revision": None,
                    "events_path": str(events_path),
                    "event_count": 2,
                    "activated_at": "2026-08-01T20:00:00+00:00",
                }
            },
        )
        with self.assertRaisesRegex(ValueError, "contagem divergente"):
            build_public_delivery(self.root)


if __name__ == "__main__":
    unittest.main()
