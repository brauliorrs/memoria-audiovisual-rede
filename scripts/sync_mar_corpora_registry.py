"""Manual, non-scheduled sync of vetted code registry into Neon.

Requires a dedicated member of mar_corpora_ingester, an explicit --apply flag
and the scoped MAR_CORPORA_INGESTER_DATABASE_URL. Does not approve corpora.
"""
from __future__ import annotations

import argparse
import json
import os

from memoria_audiovisual.corpus_registry_pg import (
    RegistryDrift, sync_registered_connectors,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="Explicitly permit insert-only synchronization")
    args = parser.parse_args(argv)
    if not args.apply:
        print(json.dumps({
            "status": "HOLD", "reason": "explicit_apply_required",
            "publication_authorized": False,
        }))
        return 2
    dsn = os.environ.get("MAR_CORPORA_INGESTER_DATABASE_URL", "")
    if not dsn:
        print(json.dumps({
            "status": "HOLD", "reason": "scoped_ingester_credentials_missing",
            "publication_authorized": False,
        }))
        return 2
    try:
        import psycopg
        with psycopg.connect(dsn, connect_timeout=7) as connection:
            summary = sync_registered_connectors(connection)
    except (ImportError, RegistryDrift, PermissionError, OSError, Exception):
        # Never echo credentials, driver details, SQL or hostnames to stdout.
        print(json.dumps({
            "status": "HOLD", "reason": "registry_sync_rejected",
            "publication_authorized": False,
        }))
        return 2
    print(json.dumps({
        "status": "registered_only", **summary,
        "publication_authorized": False, "corpus_activation": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
