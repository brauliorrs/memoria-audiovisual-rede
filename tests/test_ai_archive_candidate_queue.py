import csv
from pathlib import Path

from scripts.build_ai_archive_candidate_queue import build_candidates


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_candidates_are_created_only_from_materialized_active_corpus_records(tmp_path):
    write_csv(
        tmp_path / "bfi_links_video.csv",
        [
            {
                "title": "Candidate film",
                "description": "The film used AI-assisted production for its final edit.",
                "url": "https://example.org/bfi/item-1",
            },
            {
                "title": "Historical film",
                "description": "Digitised historical film.",
                "url": "https://example.org/bfi/item-2",
            },
        ],
    )
    candidates = build_candidates(tmp_path, max_candidates=10)
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate["entity_id"] == "bfi"
    assert candidate["source_output_file"] == "bfi_links_video.csv"
    assert candidate["gate1_terminology_context_positive"] is True
    assert candidate["human_item_in_observed_corpus"] is None
    assert candidate["human_evidence_linked_to_item"] is None
    assert candidate["human_archive_ai_label"] is None


def test_unmapped_output_file_cannot_enter_gate2_queue(tmp_path):
    write_csv(
        tmp_path / "random_news.csv",
        [{
            "title": "AI story",
            "description": "This film was fully AI-generated.",
            "url": "https://example.org/story",
        }],
    )
    assert build_candidates(tmp_path, max_candidates=10) == []
