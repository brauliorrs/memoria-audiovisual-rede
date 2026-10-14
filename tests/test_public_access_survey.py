"""The discovery gate must not let an API-only investigation stand for public access."""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.validate_public_access_survey import (
    KINDS, check_survey, validate_survey,
)

ROOT = Path(__file__).resolve().parents[1]
SURVEYS = ROOT / "docs" / "engineering" / "public-access-surveys"


def record(name="TEMPLATE.json"):
    return json.loads((SURVEYS / name).read_text(encoding="utf-8"))


def evidence():
    return [{
        "url": "https://example.org/film/record-1",
        "observed_on": "2026-10-13",
        "observation": "A simulated public item record in offline test data.",
    }]


def completed():
    r = record()
    r["unit_id"] = "synthetic-access-unit"
    for k in KINDS:
        r["surfaces"][k] = {
            "status": "observed_public",
            "finding": f"Synthetic public observation: {k}",
            "evidence": evidence(),
        }
    r["conclusion"] = {
        "decision": "hold_documented",
        "investigation_complete": True,
        "human_public_access": "confirmed",
        "machine_collection": "partially_verified",
    }
    return r


class PublicAccessFirstGateTests(unittest.TestCase):
    def test_template_and_real_kavi_gap_are_explicitly_incomplete(self):
        for name in ("TEMPLATE.json", "fiaf-kavi.json"):
            with self.subTest(name=name):
                survey = record(name)
                self.assertEqual(check_survey(survey), [])
                ready, reasons = validate_survey(survey)
                self.assertFalse(ready)
                self.assertEqual(reasons, ["survey_preliminary_only"])
        kavi = record("fiaf-kavi.json")
        self.assertEqual(
            kavi["surfaces"]["machine_interfaces"]["status"],
            "observed_public",
        )
        self.assertEqual(
            kavi["surfaces"]["specialized_catalog"]["status"],
            "route_identified_unverified",
        )
        self.assertEqual(kavi["surfaces"]["media_interfaces"]["status"], "not_assessed")

    def test_completed_multichannel_survey_is_ready_for_human_review_only(self):
        ready, reasons = validate_survey(completed())
        self.assertTrue(ready)
        self.assertEqual(reasons, [])

    def test_api_only_cannot_prove_human_public_access(self):
        survey = completed()
        for kind in KINDS:
            if kind != "machine_interfaces":
                survey["surfaces"][kind] = {
                    "status": "not_found_with_evidence",
                    "finding": "Synthetic investigation found no route in this scope.",
                    "evidence": evidence(),
                }
        self.assertIn(
            "survey_human_access_unsubstantiated",
            check_survey(survey),
        )

    def test_final_hold_cannot_skip_catalog_or_item_inspection(self):
        for kind in ("specialized_catalog", "individual_item_pages"):
            survey = completed()
            survey["surfaces"][kind] = {
                "status": "route_identified_unverified",
                "finding": "Link identified but page never inspected",
                "evidence": evidence(),
            }
            with self.subTest(kind=kind):
                self.assertIn("survey_discovery_not_completed", check_survey(survey))

    def test_environment_failure_must_not_be_absence_claim(self):
        survey = completed()
        survey["conclusion"]["human_public_access"] = "not_confirmed_in_scope"
        for kind in (
            "institutional_site", "specialized_catalog", "public_search",
            "individual_item_pages", "aggregator_portal",
        ):
            survey["surfaces"][kind] = {
                "status": "environment_limited",
                "finding": "Local resolver or test runner could not access this host",
                "evidence": evidence(),
            }
        self.assertIn(
            "survey_absence_claim_overreaches_evidence",
            check_survey(survey),
        )

    def test_human_access_does_not_mean_corpus_admission(self):
        survey = completed()
        survey["conclusion"]["machine_collection"] = "unverified"
        survey["conclusion"]["decision"] = "hold_documented"
        self.assertEqual(check_survey(survey), [])
        survey["conclusion"]["decision"] = "admitted"
        self.assertIn(
            "survey_admission_requires_separate_protocol",
            check_survey(survey),
        )

    def test_machine_reachability_does_not_verify_authorized_collection(self):
        survey = completed()
        survey["conclusion"]["machine_collection"] = "verified_in_scope"
        self.assertIn(
            "survey_machine_validation_missing",
            check_survey(survey),
        )
        survey["conclusion"]["machine_validation"] = {
            "authorization_evidence": evidence(),
        }
        self.assertIn(
            "survey_machine_bounded_enumeration_evidence_invalid",
            check_survey(survey),
        )
        self.assertIn(
            "survey_machine_replay_integrity_evidence_invalid",
            check_survey(survey),
        )
        self.assertIn(
            "survey_machine_provenance_evidence_invalid",
            check_survey(survey),
        )

    def test_machine_verified_requires_all_four_independent_claims(self):
        survey = completed()
        survey["conclusion"]["machine_collection"] = "verified_in_scope"
        survey["conclusion"]["machine_validation"] = {
            key: evidence() for key in (
                "authorization_evidence",
                "bounded_enumeration_evidence",
                "replay_integrity_evidence",
                "provenance_evidence",
            )
        }
        self.assertEqual(check_survey(survey), [])
        ready, errors = validate_survey(survey)
        self.assertTrue(ready)
        self.assertEqual(errors, [])
        # Even complete evidence requires a separate corpus admission.
        survey["conclusion"]["decision"] = "admitted"
        self.assertIn(
            "survey_admission_requires_separate_protocol",
            check_survey(survey),
        )

    def test_any_environment_limited_surface_blocks_final_closure(self):
        for kind in KINDS:
            survey = completed()
            survey["surfaces"][kind] = {
                "status": "environment_limited",
                "finding": "Research runner DNS was unavailable",
                "evidence": evidence(),
            }
            with self.subTest(kind=kind):
                self.assertIn(
                    "survey_discovery_not_completed",
                    check_survey(survey),
                )

    def test_final_human_access_cannot_remain_unverified(self):
        survey = completed()
        survey["conclusion"]["human_public_access"] = "unverified"
        self.assertIn(
            "survey_human_access_unresolved",
            check_survey(survey),
        )

    def test_missing_evidence_blocks_claim_of_public_route(self):
        survey = completed()
        survey["surfaces"]["individual_item_pages"]["evidence"] = []
        self.assertIn(
            "survey_individual_item_pages_evidence_missing",
            check_survey(survey),
        )

    def test_malformed_status_and_non_http_evidence_are_rejected(self):
        survey = completed()
        survey["surfaces"]["public_search"]["status"] = ["observed_public"]
        self.assertIn("survey_public_search_status_invalid", check_survey(survey))
        survey = completed()
        survey["surfaces"]["public_search"]["evidence"][0]["url"] = (
            "ftp://example.org/item"
        )
        self.assertIn("survey_public_search_evidence_invalid", check_survey(survey))

    def test_local_and_malformed_hostnames_cannot_prove_public_access(self):
        blocked = (
            "http://localhost/item",
            "https://127.0.0.1/item",
            "https://127.1/item",
            "https://0177.0.0.1/item",
            "https://0x7f.1/item",
            "https://224.0.0.1/item",
            "https://[ff02::1]/item",
            "https://192.168.1.7/item",
            "http://10.0.0.1/item",
            "https://[::1]/item",
            "https://./item",
            "https://a.local/item",
            "https://example.internal/item",
            "https://example.test/item",
            "http://intranet/item",
            "https://example.org:bad/item",
        )
        for url in blocked:
            with self.subTest(url=url):
                survey = completed()
                survey["surfaces"]["individual_item_pages"]["evidence"][0]["url"] = url
                self.assertIn(
                    "survey_individual_item_pages_evidence_invalid",
                    check_survey(survey),
                )

    def test_future_observations_cannot_precede_survey_date(self):
        survey = completed()
        survey["surfaces"]["public_search"]["evidence"][0]["observed_on"] = (
            "2026-10-14"
        )
        self.assertIn(
            "survey_public_search_evidence_after_survey_date",
            check_survey(survey),
        )
        survey = completed()
        survey["conclusion"]["machine_collection"] = "verified_in_scope"
        survey["conclusion"]["machine_validation"] = {
            key: evidence() for key in (
                "authorization_evidence",
                "bounded_enumeration_evidence",
                "replay_integrity_evidence",
                "provenance_evidence",
            )
        }
        survey["conclusion"]["machine_validation"]["authorization_evidence"][0][
            "observed_on"
        ] = "2026-10-14"
        self.assertIn(
            "survey_machine_authorization_evidence_after_survey_date",
            check_survey(survey),
        )

    def test_http_only_catalog_is_discoverable_without_approving_scrape(self):
        survey = completed()
        survey["surfaces"]["specialized_catalog"]["evidence"][0]["url"] = (
            "http://legacy-catalog.example.org/"
        )
        self.assertEqual(check_survey(survey), [])
        # The survey documents observed access only; permission to automate
        # belongs to the separate robots/access/replay admission protocol.
        self.assertEqual(survey["conclusion"]["decision"], "hold_documented")

    def test_unsupported_surfaces_do_not_silently_pass(self):
        survey = completed()
        survey["surfaces"].pop("specialized_catalog")
        self.assertIn(
            "survey_required_surfaces_missing_or_extra",
            check_survey(survey),
        )

    def test_no_network_or_auto_admission_is_ever_performed(self):
        with patch("socket.socket", side_effect=AssertionError("network banned")):
            ready, _ = validate_survey(completed())
        self.assertTrue(ready)
        # Human review remains required, including for synthetically valid data.
        self.assertEqual(completed()["conclusion"]["decision"], "hold_documented")


if __name__ == "__main__":
    unittest.main()
