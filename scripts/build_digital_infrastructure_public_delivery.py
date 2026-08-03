from __future__ import annotations

import argparse
import json
from pathlib import Path

from memoria_audiovisual.digital_infrastructure.public_delivery import build_public_delivery


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Materializa a projeção estável das publicações vigentes."
    )
    parser.add_argument(
        "--public-root",
        default="data/digital_infrastructure/public",
        help="Diretório que contém active_publications.json e as versões públicas.",
    )
    parser.add_argument(
        "--output-root",
        default=None,
        help="Diretório de saída; por padrão usa <public-root>/delivery.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest = build_public_delivery(
        Path(args.public_root),
        output_root=Path(args.output_root) if args.output_root else None,
    )
    print(json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
