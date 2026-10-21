"""Gate P0 cloud executor: guarded, synthetic-only Neon integration on GitHub Actions.

Never load credentials from a PR artifact, general DATABASE_URL, or source file.
The environment-scoped credential is present only for this reviewed job.
"""
from __future__ import annotations

import io
import os
import sys
import unittest
from collections.abc import Mapping

TEST_ENDPOINT = "ep-damp-term-b8wqhmz0.c-14.us-east-1.aws.neon.tech"
TEST_ROLE = "mar_p0_limited"
REQUIRED_CONTEXT = "mar-p0-neon-isolated"
FORBIDDEN_ENV = (
    "MAR_P0_TEST_DATABASE_URL",
    "PGHOST", "PGHOSTADDR", "PGPORT", "PGDATABASE", "PGUSER",
    "PGPASSWORD", "PGSERVICE", "PGSERVICEFILE", "PGOPTIONS",
    "PGSSLMODE", "PGSSLROOTCERT", "PGCHANNELBINDING",
)


class CloudGateRejected(ValueError):
    """A cloud test must never fall back to a production database."""


def validate_cloud_context(env: Mapping[str, str]) -> str:
    """Fail before imports/network if any cloud execution precondition is unmet."""
    if (
        env.get("GITHUB_ACTIONS") != "true"
        or env.get("GITHUB_EVENT_NAME") != "pull_request"
        or env.get("GITHUB_REPOSITORY") != "brauliorrs/memoria-audiovisual-rede"
        or env.get("MAR_P0_CLOUD_ENVIRONMENT") != REQUIRED_CONTEXT
        or env.get("MAR_P0_CLOUD_RUN_ALLOWED") != "reviewed"
        or env.get("MAR_P0_CLOUD_PR_NUMBER") != "90"
        or env.get("GITHUB_EVENT_ACTION") != "labeled"
        or env.get("MAR_P0_TRIGGER_LABEL") != "mar-p0-cloud-run"
    ):
        raise CloudGateRejected("untrusted_cloud_execution_context")
    sha = env.get("GITHUB_HEAD_SHA", "")
    approved = env.get("MAR_P0_APPROVED_SHA", "")
    if not sha or len(sha) != 40 or sha != approved or any(
        char not in "0123456789abcdef" for char in sha
    ):
        raise CloudGateRejected("commit_not_approved")
    if any(env.get(key) for key in FORBIDDEN_ENV):
        raise CloudGateRejected("unapproved_postgres_configuration")
    secret = env.get("MAR_P0_TEST_PASSWORD")
    if not secret:
        raise CloudGateRejected("limited_role_credential_missing")
    return secret


def main() -> int:
    try:
        password = validate_cloud_context(os.environ)
    except CloudGateRejected as exc:
        print(f"Gate P0 CLOUD HOLD: {exc}", file=sys.stderr)
        return 2

    try:
        from psycopg.conninfo import make_conninfo
    except ImportError:
        print("Gate P0 CLOUD HOLD: psycopg_unavailable", file=sys.stderr)
        return 2

    # Avoid inheriting the original secret name in test subprocesses.
    # The explicit, guarded DSN exists only in this ephemeral runner process.
    dsn = make_conninfo(
        "",
        host=TEST_ENDPOINT,
        dbname="neondb",
        user=TEST_ROLE,
        password=password,
        sslmode="verify-full",
        sslrootcert="system",
        channel_binding="require",
        connect_timeout=12,
        application_name="mar-gate-p0-synthetic-cloud",
    )
    del password
    os.environ.pop("MAR_P0_TEST_PASSWORD", None)
    os.environ["MAR_P0_TEST_DATABASE_URL"] = dsn
    os.environ["MAR_P0_TEST_LIVE"] = "1"

    try:
        # Prevent database error text from leaking password-bearing DSNs into
        # CI logs. Report only numbers and a safe status, not tracebacks.
        output = io.StringIO()
        suite = unittest.defaultTestLoader.discover(
            "tests", pattern="test_neon_checkpoint_live.py"
        )
        result = unittest.TextTestRunner(
            stream=output, verbosity=0, buffer=True
        ).run(suite)
        if not result.wasSuccessful() or result.testsRun < 3:
            print(
                f"Gate P0 CLOUD FAIL: tests={result.testsRun}, "
                f"failures={len(result.failures)}, errors={len(result.errors)}, "
                f"skipped={len(result.skipped)}"
            )
            return 1
        print(
            f"Gate P0 CLOUD PASS: tests={result.testsRun}, "
            "synthetic-only, isolated role and branch"
        )
        return 0
    finally:
        os.environ.pop("MAR_P0_TEST_DATABASE_URL", None)
        os.environ.pop("MAR_P0_TEST_LIVE", None)
        del dsn


if __name__ == "__main__":
    raise SystemExit(main())
