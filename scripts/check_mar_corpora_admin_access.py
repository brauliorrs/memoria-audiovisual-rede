"""Operator-only, read-only preflight for the PRIVATE MAR admin dashboard.

Run with MAR_CORPORA_READONLY_DATABASE_URL in an isolated/approved environment:
  python -m scripts.check_mar_corpora_admin_access

No secrets, actor IDs, URLs or archival metadata are printed. No DML.
This checks database grants and read-only data access, NOT OIDC.
"""
from __future__ import annotations

import json
import os

from memoria_audiovisual.corpus_registry_pg import (
    list_corpora, read_only_role_assertion,
)


def main() -> int:
    dsn = os.environ.get("MAR_CORPORA_READONLY_DATABASE_URL")
    if not dsn:
        print(json.dumps({"status": "HOLD", "reason": "no_read_only_credential"}))
        return 2
    try:
        import psycopg
        with psycopg.connect(
            dsn, connect_timeout=7,
            options="-c default_transaction_read_only=on -c statement_timeout=5000",
            autocommit=True,
        ) as conn:
            read_only_role_assertion(conn)
            catalog = list_corpora(conn, page=1, page_size=25)
            # Administrative projection cannot grant scientific approval.
            if any(row[7] is not False or row[8] is not False
                   for row in catalog["rows"]):
                raise PermissionError("database_is_not_publication_authority")
            count = catalog["total"]
    except Exception:
        print(json.dumps({"status": "HOLD", "reason": "read_only_preflight_failed"}))
        return 2
    print(json.dumps({
        "status": "DB_READ_ONLY_PASS",
        "registered_corpora": count,
        "authorization_tested": False,
        "publication_authorized": False,
        "ready_for_production": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
