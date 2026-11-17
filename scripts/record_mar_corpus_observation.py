"""Manually append a technical MAR corpus audit event using scoped DB identity.

Only 'probed', 'HOLD', 'note' are supported. Curatorial decisions and
publication stay in reviewed evidence and independent PRs, NEVER this CLI.
"""
from __future__ import annotations

import argparse
import json
import os

from memoria_audiovisual.corpus_registry_pg import record_technical_observation


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus_code")
    parser.add_argument("event_kind", choices=["probed", "HOLD", "note"])
    parser.add_argument("--evidence-sha256", default="")
    parser.add_argument("--evidence-ref", default="")
    parser.add_argument("--note", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    dsn = os.environ.get("MAR_CORPORA_INGESTER_DATABASE_URL", "")
    if not args.apply or not dsn:
        print(json.dumps({"status": "HOLD", "publication_authorized": False}))
        return 2
    try:
        import psycopg
        with psycopg.connect(dsn, connect_timeout=7) as conn:
            result = record_technical_observation(
                conn, corpus_code=args.corpus_code,
                event_kind=args.event_kind, note=args.note,
                evidence_sha256=args.evidence_sha256,
                evidence_ref=args.evidence_ref,
            )
    except Exception:
        print(json.dumps({"status": "HOLD", "publication_authorized": False}))
        return 2
    print(json.dumps({"status": "technical_event_recorded", **result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
