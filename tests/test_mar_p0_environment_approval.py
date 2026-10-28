"""Offline unit tests for independent GitHub deployment approval gate."""
from __future__ import annotations

import unittest

from scripts.check_mar_p0_environment_approval import valid_independent_approval


def approved(login="reviewer2", env="mar-p0-neon-isolated", state="approved",
             type_="User"):
    return {
        "state": state,
        "user": {"login": login, "type": type_},
        "environments": [{"name": env}],
    }


class EnvironmentReviewTests(unittest.TestCase):
    def test_valid_human_independent_approval(self):
        self.assertTrue(valid_independent_approval(
            [approved()], actor="brauliorrs"
        ))

    def test_empty_or_self_approval_is_rejected(self):
        self.assertFalse(valid_independent_approval([], actor="brauliorrs"))
        self.assertFalse(valid_independent_approval(
            [approved(login="brauliorrs")], actor="brauliorrs"
        ))
        self.assertFalse(valid_independent_approval(
            [approved(login="BrAuLiOrRs")], actor="brauliorrs"
        ))

    def test_wrong_environment_and_nonapproval_rejected(self):
        self.assertFalse(valid_independent_approval(
            [approved(env="production")], actor="brauliorrs"
        ))
        self.assertFalse(valid_independent_approval(
            [approved(state="rejected")], actor="brauliorrs"
        ))

    def test_bots_malformed_payloads_rejected(self):
        for records in (
            [approved(type_="Bot")],
            [{"state": "approved", "user": {}, "environments": []}],
            [{"state": "approved", "user": "not-object", "environments": []}],
            [{"state": "approved", "user": {"login": "reviewer2", "type": "User"},
              "environments": "not-array"}],
        ):
            with self.subTest(records=records):
                self.assertFalse(valid_independent_approval(
                    records, actor="brauliorrs"
                ))


if __name__ == "__main__":
    unittest.main()
