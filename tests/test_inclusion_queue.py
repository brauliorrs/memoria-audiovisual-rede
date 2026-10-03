"""Tests for deterministic, non-automatic MAR corpus inclusion scheduling."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.inclusion_queue import (
    InclusionQueueError,
    NEXT_INCLUSION_FILENAME,
    next_inclusion_candidates,
    select_inclusion_candidates,
    write_next_inclusion_candidates,
)

ROOT = Path(__file__).resolve().parents[1]


def row(rank, code, *, status="candidato_individual", layer="fila_definitiva_um_por_um",
        decision="avaliar_arquivo_individual_um_por_um", blocked="False"):
    return {
        "unit_code": code,
        "unit_label": f"Unit {code}",
        "source_family": "Synthetic",
        "country_or_scope": "Europe",
        "source_url": f"https://example.org/{code}",
        "organism_status": status,
        "queue_layer": layer,
        "queue_decision": decision,
        "definitive_queue_rank": str(rank),
        "next_action": "probe",
        "inclusion_gate": "validate public audiovisual route",
        "video_location_status": "a_localizar",
        "video_location_candidate_url": f"https://example.org/{code}",
        "blocks_expansion": blocked,
        "evidence_reference": "synthetic fixture",
        "rule_version": "test-v1",
    }


class InclusionQueueTests(unittest.TestCase):
    def test_selector_uses_only_definitive_individual_queue_and_rank(self):
        rows = [
            row(9, "later"),
            row(4, "directory", layer="fonte_de_fila", decision="expandir_diretorio_para_fila_individual"),
            row(7, "blocked", blocked="True"),
            row(6, "first"),
            row(8, "second"),
        ]
        selected = select_inclusion_candidates(rows, limit=2)
        self.assertEqual([x.unit_code for x in selected], ["first", "second"])
        self.assertEqual([x.rank for x in selected], [6, 8])

    def test_duplicate_rank_or_code_fails_closed(self):
        with self.assertRaises(InclusionQueueError):
            select_inclusion_candidates([row(6, "a"), row(6, "b")], limit=2)
        with self.assertRaises(InclusionQueueError):
            select_inclusion_candidates([row(6, "a"), row(7, "a")], limit=2)

    def test_invalid_limit_fails_closed(self):
        with self.assertRaises(InclusionQueueError):
            select_inclusion_candidates([row(6, "a")], limit=0)

    def test_current_versioned_queue_yields_ordered_work_items(self):
        candidates = next_inclusion_candidates(
            output_dir=ROOT / "data" / "output",
            limit=3,
        )
        self.assertEqual(len(candidates), 3)
        self.assertEqual(
            [candidate.rank for candidate in candidates],
            sorted(candidate.rank for candidate in candidates),
        )
        self.assertEqual(
            [candidate.rank for candidate in candidates],
            [79, 80, 81],
        )
        self.assertEqual(
            [candidate.unit_code for candidate in candidates],
            [
                "fiaf-imperial-war-museums-film-archive",
                "inedits-jean-vigo-institute",
                "fiaf-jugoslovenska-kinoteka",
            ],
        )
        self.assertTrue(all(candidate.inclusion_gate for candidate in candidates))
        self.assertTrue(all(candidate.source_url.startswith(("http://", "https://"))
                            for candidate in candidates))

    def test_writer_never_authorizes_automatic_incorporation(self):
        source = ROOT / "data" / "output" / "observatorio_fila_pesquisa_europa.csv"
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            (output / source.name).write_bytes(source.read_bytes())
            payload = write_next_inclusion_candidates(output_dir=output, limit=3)
            self.assertFalse(payload["automatic_incorporation_authorized"])
            self.assertEqual(payload["candidate_count"], 3)
            saved = json.loads((output / NEXT_INCLUSION_FILENAME).read_text(encoding="utf-8"))
            self.assertFalse(saved["automatic_incorporation_authorized"])


if __name__ == "__main__":
    unittest.main()
