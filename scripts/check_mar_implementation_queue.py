#!/usr/bin/env python3
"""Fail-closed structural gate for MAR's serial implementation queue.

It verifies evidence metadata; only an independent human review can establish
that referenced evidence is authentic and that a scientific decision is valid.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/engineering/mar-implementation-stage-gates.json"
STAGES = tuple(f"F{i:02d}" for i in range(14))
SHA = re.compile(r"^[0-9a-f]{40}$")
CONTROL_LINE = re.compile(r"(?i)^MAR-(?:STAGE|QUEUE|TRANSITION)\s*:")
REPO_URL = "https://github.com/brauliorrs/memoria-audiovisual-rede/"
ISSUE = REPO_URL + "issues/128"
BASE_GATES = (
    "impact", "contracts", "tests", "negative_tests",
    "functional_acceptance", "rollback", "review",
)
EXTRA_GATES = {
    "F01": ("migration_matrix",),
    "F02": ("security_review", "restore_test"),
    "F03": ("security_review", "database_permissions_review"),
    "F04": ("scientific_scope_review", "audit_integrity"),
    "F05": ("scientific_scope_review", "bundle_integrity"),
    "F06": ("scientific_scope_review", "release_separation"),
    "F07": ("security_review", "authz_tests"),
    "F08": ("observability_test",),
    "F09": ("accessibility_review", "multilingual_review"),
    "F10": ("scientific_scope_review", "curatorial_review"),
    "F11": ("scientific_scope_review", "security_review", "deployment_review"),
    "F12": ("scientific_scope_review", "migration_matrix", "recovery_readiness"),
    "F13": (
        "explicit_owner_approval", "security_review",
        "publication_rights_review", "deployment_review",
    ),
}
MANUAL_GATES = {
    "functional_acceptance", "review", "security_review",
    "scientific_scope_review", "curatorial_review", "publication_rights_review",
    "explicit_owner_approval", "migration_matrix", "accessibility_review",
    "multilingual_review", "deployment_review", "recovery_readiness",
    "database_permissions_review",
}
AUTOMATED_ACTORS = {"ci", "automation", "github-actions", "bot", "auto"}


def _valid_evidence(item: object, gate: str) -> bool:
    if not isinstance(item, dict):
        return False
    ref = item.get("reference")
    commit = item.get("commit_sha")
    actor = item.get("reviewed_by")
    decision = item.get("result")
    if not isinstance(ref, str) or not ref.startswith(REPO_URL):
        return False
    if not isinstance(commit, str) or SHA.fullmatch(commit) is None:
        return False
    if not isinstance(actor, str) or not actor.strip():
        return False
    if not isinstance(decision, str) or decision not in {"accepted", "passed"}:
        return False
    if gate in MANUAL_GATES:
        if actor.strip().lower() in AUTOMATED_ACTORS or decision != "accepted":
            return False
    return True


def validate_manifest(doc: object) -> list[str]:
    """Validate queue order and evidence structure, not human decisions."""
    errors: list[str] = []
    if not isinstance(doc, dict):
        return ["manifest must be an object"]
    if doc.get("schema") != "mar.engineering.stage-gate.v1":
        errors.append("unsupported manifest schema")
    if doc.get("queue_issue") != ISSUE:
        errors.append("queue issue must be #128")
    stages = doc.get("stages")
    if not isinstance(stages, list) or len(stages) != len(STAGES):
        return errors + ["stage list must contain exactly F00 through F13"]
    ids = [s.get("id") if isinstance(s, dict) else None for s in stages]
    if ids != list(STAGES):
        errors.append("stages must be ordered and uniquely identified F00..F13")
    statuses: list[str] = []
    for index, stage in enumerate(stages):
        if not isinstance(stage, dict):
            errors.append(f"stage {index} must be an object")
            statuses.append("invalid")
            continue
        sid = STAGES[index]
        status = stage.get("status")
        statuses.append(status)
        if status not in {"completed", "active", "hold", "blocked"}:
            errors.append(f"{sid}: invalid status")
        if not isinstance(stage.get("title"), str) or not stage["title"].strip():
            errors.append(f"{sid}: title required")
        evidence = stage.get("evidence")
        if not isinstance(evidence, dict):
            errors.append(f"{sid}: evidence object required")
            continue
        if status == "blocked" and evidence:
            errors.append(f"{sid}: blocked stage cannot accumulate evidence")
        permitted = set(BASE_GATES + EXTRA_GATES.get(sid, ()))
        if sid == "F00":
            permitted = set()
        unexpected = set(evidence) - permitted
        if unexpected:
            errors.append(f"{sid}: unknown evidence gates {sorted(unexpected)}")
        for gate, value in evidence.items():
            if gate in permitted and not _valid_evidence(value, gate):
                errors.append(f"{sid}: invalid or non-human evidence for {gate}")
        if status == "completed" and sid != "F00":
            missing = permitted - set(evidence)
            if missing:
                errors.append(f"{sid}: completion missing independent gates {sorted(missing)}")
    pending = next((i for i, status in enumerate(statuses) if status != "completed"), len(statuses))
    if statuses[0] != "completed":
        errors.append("F00 must remain completed")
    if pending < len(STAGES):
        expected = [*("completed" for _ in range(pending)),
                    statuses[pending],
                    *("blocked" for _ in range(pending + 1, len(STAGES)))]
        if statuses[pending] not in {"active", "hold"} or statuses != expected:
            errors.append("exactly the earliest unfinished stage must be active/hold; later stages blocked")
        if doc.get("active_stage") != STAGES[pending]:
            errors.append("active_stage must identify earliest unfinished stage")
    elif doc.get("active_stage") is not None:
        errors.append("active_stage must be null after all stages complete")
    if pending < len(STAGES) and doc.get("new_features_frozen") is not True:
        errors.append("feature freeze must remain enabled until queue completion")
    if doc.get("public_access_authorized") is not False:
        if statuses[-1] != "completed" or doc.get("public_access_authorized") is not True:
            errors.append("public access requires completed F13 and explicit authorization")
    if statuses[-1] == "completed" and doc.get("public_access_authorized") is not True:
        errors.append("completed F13 requires explicit public authorization")
    return errors


def validate_pull_request(
    body: str, active_stage: str | None, manifest: dict | None = None
) -> list[str]:
    """Require exact scope markers for normal PRs and controlled queue closing.

    A transition PR closes one stage and opens the immediately following
    stage; it must name BOTH the outgoing and incoming stages explicitly.
    The manifest still needs independently reviewed evidence and a human
    GitHub approval. This checker verifies structure, not the review's merit.
    """
    controls = [
        line.strip() for line in body.splitlines()
        if CONTROL_LINE.match(line.strip())
    ]
    if active_stage is None:
        if controls in (["MAR-STAGE: F13"], ["MAR-QUEUE: COMPLETE"]):
            return []
        return ["completed queue requires exactly MAR-STAGE: F13 (closing PR) "
                "or MAR-QUEUE: COMPLETE (later PR), never both"]

    if controls == [f"MAR-STAGE: {active_stage}"]:
        return []

    if active_stage in STAGES[2:]:
        incoming = STAGES.index(active_stage)
        outgoing = STAGES[incoming - 1]
        expected = [
            f"MAR-STAGE: {outgoing}",
            f"MAR-TRANSITION: {outgoing}->{active_stage}",
        ]
        if controls == expected:
            if not isinstance(manifest, dict):
                return ["transition PR requires the complete queue manifest"]
            stages = manifest.get("stages")
            if not isinstance(stages, list) or len(stages) != len(STAGES):
                return ["transition PR has incomplete stage manifest"]
            if (stages[incoming - 1].get("status") == "completed"
                    and stages[incoming].get("status") in ("active", "hold")
                    and manifest.get("active_stage") == active_stage
                    and not validate_manifest(manifest)):
                return []

    return [f"PR must declare MAR-STAGE: {active_stage}, or use a valid "
            "MAR-STAGE / MAR-TRANSITION pair for the immediately previous "
            "completed stage; no extra markers"]

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--check-pr", action="store_true")
    args = parser.parse_args(argv)
    try:
        doc = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"MAR ENGINEERING GATE: HOLD reading manifest: {exc}", file=sys.stderr)
        return 1
    errors = validate_manifest(doc)
    if args.check_pr and os.getenv("GITHUB_EVENT_NAME") == "pull_request":
        try:
            event_path = Path(os.environ["GITHUB_EVENT_PATH"])
            event = json.loads(event_path.read_text(encoding="utf-8"))
            pr = event["pull_request"]
            errors.extend(validate_pull_request(pr.get("body") or "", doc["active_stage"], doc))
        except (KeyError, OSError, ValueError, TypeError) as exc:
            errors.append(f"cannot verify pull request stage: {exc}")
    for err in errors:
        print(f"MAR ENGINEERING GATE: HOLD: {err}", file=sys.stderr)
    if errors:
        return 1
    print("MAR ENGINEERING GATE: structural checks PASS; NOT functional or scientific approval")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
