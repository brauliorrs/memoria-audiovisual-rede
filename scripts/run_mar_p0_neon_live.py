"""Explicit, interactive P0 Neon live-test runner; never saves a database password.

Run only from a trusted workstation. Never invoke from a public PR workflow.
The database role must be SQL-native and limited to the validation branch.
"""
from __future__ import annotations

import getpass
import os
import sys
import unittest


TEST_ENDPOINT = "ep-damp-term-b8wqhmz0.c-14.us-east-1.aws.neon.tech"


def main() -> int:
    if os.environ.get("MAR_P0_TEST_DATABASE_URL"):
        print(
            "REFUSED: clear MAR_P0_TEST_DATABASE_URL; this runner prompts "
            "for the isolated test credential.",
            file=sys.stderr,
        )
        return 2
    if any(os.environ.get(key) for key in (
        "PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE", "PGOPTIONS",
    )):
        print("REFUSED: libpq environment override is present.", file=sys.stderr)
        return 2
    try:
        from psycopg.conninfo import make_conninfo
    except ImportError:
        print("Install the optional driver: pip install -e '.[postgres]'",
              file=sys.stderr)
        return 2

    secret = getpass.getpass("Password for mar_p0_limited on Neon test branch: ")
    if not secret:
        print("REFUSED: empty password.", file=sys.stderr)
        return 2

    try:
        # All connection coordinates are explicit; only password is prompted.
        # The unittest validates host/user/DB/SSL before opening any connection.
        dsn = make_conninfo(
            "",
            host=TEST_ENDPOINT,
            dbname="neondb",
            user="mar_p0_limited",
            password=secret,
            sslmode="require",
            connect_timeout=10,
            application_name="mar-gate-p0-live-check",
        )
    finally:
        del secret

    try:
        os.environ["MAR_P0_TEST_DATABASE_URL"] = dsn
        os.environ["MAR_P0_TEST_LIVE"] = "1"
        suite = unittest.defaultTestLoader.discover(
            "tests", pattern="test_neon_checkpoint_live.py"
        )
        result = unittest.TextTestRunner(
            verbosity=2, buffer=True
        ).run(suite)
        return 0 if result.wasSuccessful() else 1
    finally:
        os.environ.pop("MAR_P0_TEST_DATABASE_URL", None)
        os.environ.pop("MAR_P0_TEST_LIVE", None)
        del dsn


if __name__ == "__main__":
    raise SystemExit(main())
