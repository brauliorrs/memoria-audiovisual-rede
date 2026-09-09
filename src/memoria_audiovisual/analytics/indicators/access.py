"""Índice simples de acesso aberto preservado da plataforma anterior."""

from __future__ import annotations

import unicodedata
from typing import Any, Mapping

from ..base import Indicator, IndicatorContext, IndicatorResult

_EVALUABLE = {"detected", "not_detected", "unknown"}
_BARRIERS = (
    "cadastro",
    "cadastro obrigatorio",
    "registro",
    "login",
    "autenticacao",
    "solicitacao formal",
    "solicitacao por email",
    "formulario de acesso",
    "autorizacao institucional",
    "paid access",
    "pagamento",
    "assinatura",
)


def _normalize_text(value: Any) -> str:
    normalized = unicodedata.normalize("NFKD", str(value).casefold())
    without_accents = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return " ".join(without_accents.replace("-", " ").split())


def _normalized_values(row: Mapping[str, Any]) -> tuple[str, ...]:
    values = row.get("detected_values", ())
    if not isinstance(values, (list, tuple)):
        raise ValueError("detected_values deve ser uma lista")
    return tuple(_normalize_text(value) for value in values)


class AudiovisualArchiveAccessIndex(Indicator):
    """Percentual de arquivos elegíveis abertos sem cadastro ou solicitação."""

    indicator_id = "audiovisual_archive_access_index"
    version = "1.0.0"
    methodology_version = "1.0.0"
    # Rótulo técnico do motor. O título científico pertence exclusivamente ao
    # indicator_registry.json e é associado na camada de apresentação.
    title = indicator_id
    category = "access"
    unit = "percent"

    def calculate(self, context: IndicatorContext) -> IndicatorResult:
        eligible = set(context.metadata.get("eligible_corpus_codes") or context.corpus_codes)
        rows = {
            str(row.get("corpus_code") or "").strip(): row
            for row in context.coverage_rows
            if str(row.get("detector_group") or "") == "restriction"
            and str(row.get("corpus_code") or "").strip() in eligible
        }
        evaluable = {
            corpus: row for corpus, row in rows.items()
            if str(row.get("status") or "") in _EVALUABLE
        }
        open_corpora: list[str] = []
        restricted_corpora: list[str] = []
        for corpus, row in evaluable.items():
            values = _normalized_values(row)
            has_barrier = str(row.get("status") or "") == "detected" and any(
                barrier in value for barrier in _BARRIERS for value in values
            )
            if has_barrier:
                restricted_corpora.append(corpus)
            else:
                open_corpora.append(corpus)

        denominator = len(evaluable)
        numerator = len(open_corpora)
        value = round(100 * numerator / denominator, 4) if denominator else None
        excluded_non_corpus = sorted(set(context.corpus_codes) - eligible)
        excluded_not_assessable = sorted(eligible - set(evaluable))
        return self.result(
            context,
            value=value,
            numerator=numerator,
            denominator=denominator,
            status="calculated" if denominator else "insufficient_data",
            notes=(
                "Mede somente arquivos integrantes do corpus científico.",
                "Bancos comerciais pagos são catalogados, mas excluídos do corpus e do denominador.",
                "Acesso aberto significa ausência observada de cadastro, login, pagamento ou solicitação formal.",
            ),
            dimensions={
                "eligible_corpus_codes": sorted(eligible),
                "open_corpora": sorted(open_corpora),
                "restricted_corpora": sorted(restricted_corpora),
                "excluded_non_corpus": excluded_non_corpus,
                "excluded_not_assessable": excluded_not_assessable,
                "barriers": list(_BARRIERS),
            },
        )
