from __future__ import annotations

import json
import re
from pathlib import Path


LOCALE_DIR = Path(__file__).resolve().parents[1] / "src" / "memoria_audiovisual" / "locales"
TOKEN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", re.UNICODE)

PORTUGUESE_MARKERS = {
    "ainda", "arquivos", "atualização", "avaliação", "categoria", "coleta",
    "completude", "dados", "evidência", "institucional", "instituições",
    "metodológica", "metodológico", "nenhum", "nenhuma", "não", "observação",
    "pesquisa", "público", "pública", "relatório", "restrição", "rodada",
    "situação", "unidade", "unidades", "verificação", "vídeo", "vídeos",
}

TARGET_MARKERS = {
    "en": {
        "archive", "archives", "assessment", "category", "collection", "data",
        "evidence", "institution", "institutions", "methodological", "no", "not",
        "observation", "public", "report", "restriction", "round", "status",
        "unit", "units", "verification", "video", "videos", "yet",
    },
    "es": {
        "archivo", "archivos", "evaluación", "categoría", "colección", "datos",
        "evidencia", "institución", "instituciones", "metodológica", "ningún",
        "ninguna", "no", "observación", "público", "pública", "informe",
        "restricción", "ronda", "situación", "unidad", "unidades", "verificación",
        "vídeo", "vídeos", "todavía",
    },
}


def tokens(value: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(value)}


def audit_language(language: str) -> list[dict[str, object]]:
    path = LOCALE_DIR / f"{language}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    findings: list[dict[str, object]] = []

    for key, value in payload.items():
        value_tokens = tokens(value)
        portuguese_hits = sorted(value_tokens & PORTUGUESE_MARKERS)
        target_hits = sorted(value_tokens & TARGET_MARKERS[language])

        # One isolated shared or borrowed word is not sufficient. Findings require
        # at least two distinctive Portuguese markers, or one Portuguese marker
        # with no target-language evidence in a substantive string.
        substantive = len(value_tokens) >= 5
        residual = len(portuguese_hits) >= 2 or (
            substantive and len(portuguese_hits) == 1 and not target_hits
        )
        if not residual:
            continue

        findings.append(
            {
                "language": language,
                "key": key,
                "value": value,
                "portuguese_markers": portuguese_hits,
                "target_markers": target_hits,
                "severity": "high" if len(portuguese_hits) >= 2 else "review",
            }
        )

    return findings


def main() -> int:
    findings = audit_language("en") + audit_language("es")
    print(json.dumps(findings, ensure_ascii=False, indent=2))
    # This audit is initially report-only so the existing public deployment is
    # not blocked before the residual catalogue values have been reviewed.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
