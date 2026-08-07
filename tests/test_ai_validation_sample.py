import json

from memoria_audiovisual.corpora import CORPORA
from memoria_audiovisual.digital_infrastructure.ai_validation import (
    AI_VALIDATION_SAMPLE_ID,
    build_initial_validation_sample,
)
from scripts.build_ai_validation_sample import check_sample, write_sample


def test_initial_sample_uses_only_active_canonical_corpora():
    payload = build_initial_validation_sample(CORPORA)
    assert payload["sample"]["sample_id"] == AI_VALIDATION_SAMPLE_ID
    assert payload["sample"]["is_gold_standard"] is False
    assert payload["sample"]["does_not_activate_indicators"] is True
    assert payload["summary"]["entities"] == 6
    assert {"Europe", "North America"} == set(payload["summary"]["geographic_groups"])
    for entry in payload["entries"]:
        assert CORPORA[entry["entity_code"]]["organism_active"] is True
        assert entry["annotation_status"] == "pending_annotation"


def test_materialized_sample_is_reproducible(tmp_path):
    output = tmp_path / "sample.json"
    write_sample(output)
    check_sample(output)
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert len(payload["entries"]) == 6
