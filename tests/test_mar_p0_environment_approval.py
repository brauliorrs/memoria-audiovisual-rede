"""Offline regression tests of manually approved solo-maintainer Gate P0."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.check_mar_p0_environment_approval import (
    main,
    valid_owner_approval,
)


def approved(login="brauliorrs", env="mar-p0-neon-isolated", state="approved",
             type_="User"):
    return {
        "state": state,
        "user": {"login": login, "type": type_},
        "environments": [{"name": env}],
    }


class EnvironmentApprovalTests(unittest.TestCase):
    def test_explicit_owner_self_approval_allowed(self):
        self.assertTrue(valid_owner_approval(
            [approved()], actor="brauliorrs"
        ))
        self.assertTrue(valid_owner_approval(
            [approved(login="BraUlioRrs")], actor="brauliorrs"
        ))

    def test_missing_review_and_other_reviewer_rejected(self):
        self.assertFalse(valid_owner_approval([], actor="brauliorrs"))
        self.assertFalse(valid_owner_approval(
            [approved(login="reviewer2")], actor="brauliorrs"
        ))
        self.assertFalse(valid_owner_approval(
            [approved()], actor="someone-else"
        ))

    def test_wrong_environment_unapproved_and_bypass_rejected(self):
        for review in (
            approved(env="production"),
            approved(state="rejected"),
            approved(state="bypassed"),
            approved(type_="Bot"),
        ):
            with self.subTest(review=review):
                self.assertFalse(valid_owner_approval(
                    [review], actor="brauliorrs"
                ))

    def test_malformed_record_rejected(self):
        for review in (
            {},
            {"state": "approved", "user": {}, "environments": []},
            {"state": "approved", "user": "not-object", "environments": []},
            {"state": "approved", "user": {"login": "brauliorrs", "type": "User"},
             "environments": "not-list"},
        ):
            with self.subTest(review=review):
                self.assertFalse(valid_owner_approval(
                    [review], actor="brauliorrs"
                ))

    def test_bad_execution_context_never_queries_github(self):
        trusted = {
            "GITHUB_ACTIONS": "true",
            "GITHUB_REPOSITORY": "brauliorrs/memoria-audiovisual-rede",
            "GITHUB_RUN_ATTEMPT": "1",
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_REF": "refs/pull/90/merge",
            "GITHUB_HEAD_REF": "feature/mar-p0-neon-storage-20261021",
            "GITHUB_ACTOR": "brauliorrs",
            "GITHUB_RUN_ID": "123456789",
            "GH_TOKEN": "synthetic-only-no-access",
        }
        for mutation in (
            {"GITHUB_RUN_ATTEMPT": "2"},
            {"GITHUB_ACTOR": "another-user"},
            {"GITHUB_REF": "refs/heads/main"},
            {"GITHUB_EVENT_NAME": "push"},
            {"GH_TOKEN": ""},
        ):
            with self.subTest(mutation=mutation):
                with patch.dict("os.environ", {**trusted, **mutation}, clear=True):
                    with patch(
                        "scripts.check_mar_p0_environment_approval.urlopen",
                        side_effect=AssertionError("must never contact GitHub"),
                    ):
                        self.assertEqual(main(), 2)


if __name__ == "__main__":
    unittest.main()
