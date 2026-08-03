from __future__ import annotations

import argparse
import json
from pathlib import Path

from memoria_audiovisual.digital_infrastructure.active_publication import ActivePublicationRegistry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Define a versão pública vigente de um snapshot.")
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--publication-kind", choices=("initial", "revision"), required=True)
    parser.add_argument("--revision-number", type=int)
    parser.add_argument("--public-root", type=Path, default=Path("data/digital_infrastructure/public"))
    parser.add_argument("--activated-by", required=True)
    parser.add_argument("--reason", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    registry = ActivePublicationRegistry(args.public_root)
    record = registry.activate(
        snapshot_id=args.snapshot_id,
        publication_kind=args.publication_kind,
        revision_number=args.revision_number,
        activated_by=args.activated_by,
        activation_reason=args.reason,
    )
    print(json.dumps(record.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
