#!/usr/bin/env python3
"""Materializa ou valida a amostra inicial de experimentos de IA."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from memoria_audiovisual.corpora import CORPORA
from memoria_audiovisual.digital_infrastructure.ai_validation import (
    build_initial_validation_sample,
)

DEFAULT_OUTPUT = Path(
    "data/digital_infrastructure/ai_experiments/validation_sample_v1.json"
)


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_sample(output: Path = DEFAULT_OUTPUT) -> Path:
    payload = build_initial_validation_sample(CORPORA)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(canonical_json(payload), encoding="utf-8")
    return output


def check_sample(output: Path = DEFAULT_OUTPUT) -> None:
    expected = canonical_json(build_initial_validation_sample(CORPORA))
    if not output.exists():
        raise SystemExit(f"Amostra de IA ausente: {output}")
    actual = output.read_text(encoding="utf-8")
    if actual != expected:
        raise SystemExit(
            "A amostra inicial de IA diverge do corpus canônico. "
            "Execute scripts/build_ai_validation_sample.py."
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.check:
        check_sample(args.output)
        print("Amostra inicial de IA sincronizada com o corpus canônico.")
    else:
        path = write_sample(args.output)
        print(f"Amostra inicial de IA materializada em {path}.")


if __name__ == "__main__":
    main()
