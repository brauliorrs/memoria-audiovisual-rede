from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.digital_infrastructure.active_publication import ActivePublicationRegistry


class ActivePublicationRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "public"
        self.snapshot = "snapshot_2026_09"
        base = self.root / self.snapshot
        base.mkdir(parents=True)
        (base / "events.json").write_text(json.dumps([{"event_id": "e1"}]), encoding="utf-8")
        (base / "manifest.json").write_text(
            json.dumps({"snapshot_id": self.snapshot, "event_count": 1}), encoding="utf-8"
        )
        self.registry = ActivePublicationRegistry(self.root)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_initial_publication_becomes_active(self) -> None:
        record = self.registry.activate(
            snapshot_id=self.snapshot,
            publication_kind="initial",
            activated_by="workflow",
            activation_reason="Publicação inicial validada.",
        )
        self.assertEqual(record.publication_revision, 0)
        self.assertEqual(record.publication_id, f"{self.snapshot}:initial")
        self.assertEqual(self.registry.read_current()[self.snapshot].publication_id, record.publication_id)
        self.assertEqual(len(self.registry.history_path.read_text(encoding="utf-8").splitlines()), 1)

    def test_revision_supersedes_initial_without_deleting_history(self) -> None:
        initial = self.registry.activate(
            snapshot_id=self.snapshot,
            publication_kind="initial",
            activated_by="workflow",
            activation_reason="Publicação inicial.",
        )
        revision = self.root / self.snapshot / "revisions" / "revision_0001"
        revision.mkdir(parents=True)
        (revision / "events.json").write_text(
            json.dumps([{"event_id": "e1"}, {"event_id": "e2"}]), encoding="utf-8"
        )
        (revision / "manifest.json").write_text(
            json.dumps({
                "snapshot_id": self.snapshot,
                "publication_revision": 1,
                "revision_id": f"{self.snapshot}:publication_revision:1",
                "event_count": 2,
            }),
            encoding="utf-8",
        )
        current = self.registry.activate(
            snapshot_id=self.snapshot,
            publication_kind="revision",
            revision_number=1,
            activated_by="curator_1",
            activation_reason="Revisão tardia aprovada.",
        )
        self.assertEqual(current.supersedes_publication_id, initial.publication_id)
        self.assertEqual(current.event_count, 2)
        self.assertTrue((self.root / self.snapshot / "events.json").exists())
        self.assertEqual(len(self.registry.history_path.read_text(encoding="utf-8").splitlines()), 2)

    def test_duplicate_activation_is_blocked(self) -> None:
        arguments = dict(
            snapshot_id=self.snapshot,
            publication_kind="initial",
            activated_by="workflow",
            activation_reason="Publicação inicial.",
        )
        self.registry.activate(**arguments)
        with self.assertRaisesRegex(ValueError, "já está vigente"):
            self.registry.activate(**arguments)

    def test_manifest_count_mismatch_is_blocked(self) -> None:
        manifest = self.root / self.snapshot / "manifest.json"
        manifest.write_text(json.dumps({"snapshot_id": self.snapshot, "event_count": 3}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "event_count"):
            self.registry.activate(
                snapshot_id=self.snapshot,
                publication_kind="initial",
                activated_by="workflow",
                activation_reason="Publicação inicial.",
            )


if __name__ == "__main__":
    unittest.main()
