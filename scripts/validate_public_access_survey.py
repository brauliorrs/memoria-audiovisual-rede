"""Validate the public-access-first survey gate, without making HTTP requests.

A valid JSON record never proves that cited URLs exist or that observations
are true; reviewers must independently check evidence before a final decision.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

VERSION = "mar-public-access-survey-1.0"
KINDS = (
    "institutional_site",
    "specialized_catalog",
    "public_search",
    "individual_item_pages",
    "aggregator_portal",
    "machine_interfaces",
    "media_interfaces",
)
STATUSES = frozenset({
    "not_assessed",
    "route_identified_unverified",
    "observed_public",
    "source_blocked",
    "environment_limited",
    "not_found_with_evidence",
    "not_applicable_with_evidence",
})
HUMAN_KINDS = frozenset({
    "institutional_site", "specialized_catalog", "public_search",
    "individual_item_pages", "aggregator_portal",
})
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
UNIT_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,80}$")


def _date_is_valid(value: object) -> bool:
    if not isinstance(value, str) or not DATE.fullmatch(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _https_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    return (
        parsed.scheme == "https" and bool(parsed.netloc)
        and parsed.username is None and parsed.password is None
        and not any(c.isspace() for c in value)
    )


def check_survey(doc: object) -> list[str]:
    """Return stable, redacted diagnostic codes. Never echo input URLs/IDs."""
    errors: list[str] = []
    if not isinstance(doc, dict):
        return ["survey_not_object"]
    if doc.get("schema_version") != VERSION:
        errors.append("survey_schema_mismatch")
    if not isinstance(doc.get("unit_id"), str) or not UNIT_ID.fullmatch(doc["unit_id"]):
        errors.append("survey_unit_id_invalid")
    if not _date_is_valid(doc.get("survey_date")):
        errors.append("survey_date_invalid")
    surfaces = doc.get("surfaces")
    if not isinstance(surfaces, dict):
        return errors + ["survey_surfaces_not_object"]
    if set(surfaces) != set(KINDS):
        errors.append("survey_required_surfaces_missing_or_extra")
    for kind in KINDS:
        surface = surfaces.get(kind)
        if not isinstance(surface, dict):
            errors.append(f"survey_{kind}_invalid")
            continue
        status = surface.get("status")
        if status not in STATUSES:
            errors.append(f"survey_{kind}_status_invalid")
            continue
        evidence = surface.get("evidence")
        if not isinstance(evidence, list):
            errors.append(f"survey_{kind}_evidence_not_list")
            continue
        if status != "not_assessed":
            if not isinstance(surface.get("finding"), str) or not surface["finding"].strip():
                errors.append(f"survey_{kind}_finding_missing")
            if not evidence:
                errors.append(f"survey_{kind}_evidence_missing")
            for item in evidence:
                if (not isinstance(item, dict)
                    or not _https_url(item.get("url"))
                    or not _date_is_valid(item.get("observed_on"))
                    or not isinstance(item.get("observation"), str)
                    or not item["observation"].strip()):
                    errors.append(f"survey_{kind}_evidence_invalid")
                    break
        elif evidence:
            errors.append(f"survey_{kind}_unassessed_has_evidence")
    conclusion = doc.get("conclusion")
    if not isinstance(conclusion, dict):
        return errors + ["survey_conclusion_not_object"]
    decision = conclusion.get("decision")
    if decision not in ("pending", "hold_provisional", "hold_documented", "admitted"):
        errors.append("survey_decision_invalid")
        return errors
    access = conclusion.get("human_public_access")
    if access not in ("unverified", "confirmed", "not_confirmed_in_scope"):
        errors.append("survey_human_access_invalid")
    machine = conclusion.get("machine_collection")
    if machine not in ("unverified", "partially_verified", "verified_in_scope", "restricted"):
        errors.append("survey_machine_access_invalid")
    completed = conclusion.get("investigation_complete")
    if type(completed) is not bool:
        errors.append("survey_investigation_flag_invalid")
    any_human = any(
        isinstance(surfaces.get(k), dict) and surfaces[k].get("status") == "observed_public"
        for k in HUMAN_KINDS
    )
    if access == "confirmed" and not any_human:
        errors.append("survey_human_access_unsubstantiated")
    if access == "not_confirmed_in_scope" and any_human:
        errors.append("survey_human_access_contradicted")
    if machine in ("partially_verified", "verified_in_scope"):
        machine_surface = surfaces.get("machine_interfaces")
        if not isinstance(machine_surface, dict) or machine_surface.get("status") != "observed_public":
            errors.append("survey_machine_claim_unsubstantiated")
    if decision in ("hold_documented", "admitted") or completed is True:
        not_assessed = any(
            not isinstance(surfaces.get(k), dict)
            or surfaces[k].get("status") == "not_assessed"
            for k in KINDS
        )
        if not_assessed:
            errors.append("survey_discovery_not_completed")
        if completed is not True:
            errors.append("survey_final_decision_without_complete_flag")
        # Unknown, route-identified or environment-limited surfaces must be
        # explicitly retained as limitations, not recast as no access.
        if access == "not_confirmed_in_scope" and any(
            isinstance(surfaces.get(k), dict)
            and surfaces[k].get("status") in (
                "route_identified_unverified", "environment_limited"
            ) for k in HUMAN_KINDS
        ):
            errors.append("survey_absence_claim_overreaches_evidence")
    if decision == "pending" and completed is True:
        errors.append("survey_complete_but_decision_pending")
    if decision == "admitted" and machine != "verified_in_scope":
        errors.append("survey_admission_without_machine_verification")
    return errors


def validate_survey(doc: object) -> tuple[bool, list[str]]:
    errors = check_survey(doc)
    if errors:
        return False, errors
    # A template / preliminary file is never automatically a finished survey.
    if doc["conclusion"]["decision"] in ("pending", "hold_provisional"):
        return False, ["survey_preliminary_only"]
    return True, []


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit MAR surface discovery record (offline, no API).",
    )
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        record = json.loads(args.path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print(json.dumps({"status": "INCOMPLETE", "errors": ["survey_unreadable"]}))
        return 2
    ok, codes = validate_survey(record)
    print(json.dumps({
        "status": "READY_FOR_HUMAN_REVIEW" if ok else "INCOMPLETE",
        "errors": codes,
        "auto_admission_authorized": False,
        "network_calls": 0,
    }, sort_keys=True))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
