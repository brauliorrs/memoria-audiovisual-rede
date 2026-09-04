#!/usr/bin/env python3
"""Materializa e valida a amostra item a item de IA na produção audiovisual."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from memoria_audiovisual.digital_infrastructure.ai_content_validation import (
    build_ai_content_validation_sample,
    evaluate_ai_content_validation_sample,
)

DEFAULT_SAMPLE = Path(
    "data/digital_infrastructure/ai_experiments/ai_content_validation_sample_v1.json"
)
DEFAULT_REPORT = Path(
    "data/digital_infrastructure/ai_experiments/ai_content_validation_report_v1.json"
)


def _json_text(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_products(sample_path: Path, report_path: Path) -> None:
    sample_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    sample_path.write_text(_json_text(build_ai_content_validation_sample()), encoding="utf-8")
    report_path.write_text(_json_text(evaluate_ai_content_validation_sample()), encoding="utf-8")


def check_products(sample_path: Path, report_path: Path) -> None:
    expected_sample = _json_text(build_ai_content_validation_sample())
    expected_report = _json_text(evaluate_ai_content_validation_sample())
    if not sample_path.exists() or sample_path.read_text(encoding="utf-8") != expected_sample:
        raise SystemExit(
            "A amostra de IA no conteúdo diverge do protocolo canônico. "
            "Execute scripts/build_ai_content_validation_sample.py."
        )
    if not report_path.exists() or report_path.read_text(encoding="utf-8") != expected_report:
        raise SystemExit(
            "O relatório de calibração de IA no conteúdo diverge do protocolo canônico. "
            "Execute scripts/build_ai_content_validation_sample.py."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check_products(args.sample, args.report)
    else:
        write_products(args.sample, args.report)
        print(args.sample)
        print(args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
