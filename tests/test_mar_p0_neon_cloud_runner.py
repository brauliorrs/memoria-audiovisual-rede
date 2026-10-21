"""Offline fail-closed checks for Gate P0 GitHub cloud executor."""
from __future__ import annotations

import unittest

from scripts.run_mar_p0_neon_cloud import CloudGateRejected, validate_cloud_context


APPROVED = "a" * 40


def allowed():
    return {
        "GITHUB_ACTIONS": "true",
        "GITHUB_EVENT_NAME": "pull_request",
        "GITHUB_REPOSITORY": "brauliorrs/memoria-audiovisual-rede",
        "MAR_P0_CLOUD_ENVIRONMENT": "mar-p0-neon-isolated",
        "MAR_P0_CLOUD_RUN_ALLOWED": "reviewed",
        "MAR_P0_CLOUD_PR_NUMBER": "90",
        "GITHUB_EVENT_ACTION": "labeled",
        "MAR_P0_TRIGGER_LABEL": "mar-p0-cloud-run",
        "GITHUB_HEAD_SHA": APPROVED,
        "MAR_P0_APPROVED_SHA": APPROVED,
        "MAR_P0_TEST_PASSWORD": "fake-test-value-never-used",
    }


class CloudP0GuardTests(unittest.TestCase):
    def test_explicit_matching_approved_context(self):
        self.assertEqual(
            validate_cloud_context(allowed()), "fake-test-value-never-used"
        )

    def test_required_controls_fail_closed(self):
        for key in (
            "GITHUB_ACTIONS", "GITHUB_EVENT_NAME", "GITHUB_REPOSITORY",
            "MAR_P0_CLOUD_ENVIRONMENT", "MAR_P0_CLOUD_RUN_ALLOWED",
            "MAR_P0_CLOUD_PR_NUMBER", "GITHUB_EVENT_ACTION",
            "MAR_P0_TRIGGER_LABEL", "GITHUB_HEAD_SHA",
            "MAR_P0_APPROVED_SHA", "MAR_P0_TEST_PASSWORD",
        ):
            with self.subTest(key=key):
                env = allowed()
                env.pop(key)
                with self.assertRaises(CloudGateRejected):
                    validate_cloud_context(env)

    def test_untrusted_pull_request_and_wrong_commit(self):
        for key, value in (
            ("GITHUB_EVENT_NAME", "pull_request_target"),
            ("GITHUB_REPOSITORY", "untrusted/fork"),
            ("MAR_P0_CLOUD_RUN_ALLOWED", "true"),
            ("MAR_P0_CLOUD_PR_NUMBER", "91"),
            ("GITHUB_EVENT_ACTION", "synchronize"),
            ("MAR_P0_TRIGGER_LABEL", "unapproved-label"),
            ("GITHUB_HEAD_SHA", "b" * 40),
            ("GITHUB_HEAD_SHA", "../other"),
            ("MAR_P0_APPROVED_SHA", "b" * 40),
        ):
            with self.subTest(key=key, value=value):
                env = allowed()
                env[key] = value
                with self.assertRaises(CloudGateRejected):
                    validate_cloud_context(env)

    def test_reject_postgres_env_overrides_including_generic_dsn(self):
        for key in (
            "MAR_P0_TEST_DATABASE_URL", "PGHOST", "PGHOSTADDR", "PGPORT",
            "PGDATABASE", "PGUSER", "PGPASSWORD", "PGSERVICE",
            "PGSERVICEFILE", "PGOPTIONS", "PGSSLMODE", "PGSSLROOTCERT",
            "PGCHANNELBINDING",
        ):
            with self.subTest(key=key):
                env = allowed()
                env[key] = "rogue"
                with self.assertRaisesRegex(
                    CloudGateRejected, "unapproved_postgres_configuration"
                ):
                    validate_cloud_context(env)


if __name__ == "__main__":
    unittest.main()
