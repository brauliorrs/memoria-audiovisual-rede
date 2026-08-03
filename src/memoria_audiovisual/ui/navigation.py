"""Plano canônico de navegação da interface pública.

Este módulo mantém a ordem estrutural da aplicação separada do ponto de entrada
Streamlit. Ele não executa renderização por conta própria; apenas descreve o
contrato estável que o entrypoint deve consumir.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Mapping, Sequence


SCIENTIFIC_INFRASTRUCTURE_LABEL = "Infraestrutura científica"
OVERVIEW_INDEX = 0
SCIENTIFIC_INFRASTRUCTURE_INDEX = 1
CATEGORY_START_INDEX = 2


@dataclass(frozen=True, slots=True)
class NavigationSlices:
    overview_index: int
    scientific_infrastructure_index: int
    category_start: int
    category_stop: int
    corpus_start: int
    corpus_stop: int
    protocolled_start: int


def build_top_level_labels(
    *,
    overview_label: str,
    category_labels: Iterable[str],
    corpus_labels: Iterable[str],
    protocolled_labels: Iterable[str],
) -> list[str]:
    """Retorna os rótulos na ordem pública canônica."""
    return [
        overview_label,
        SCIENTIFIC_INFRASTRUCTURE_LABEL,
        *list(category_labels),
        *list(corpus_labels),
        *list(protocolled_labels),
    ]


def calculate_navigation_slices(
    *,
    category_total: int,
    corpus_total: int,
) -> NavigationSlices:
    """Calcula índices sem números mágicos espalhados pelo entrypoint."""
    if category_total < 0 or corpus_total < 0:
        raise ValueError("Navigation totals cannot be negative")

    category_start = CATEGORY_START_INDEX
    category_stop = category_start + category_total
    corpus_start = category_stop
    corpus_stop = corpus_start + corpus_total
    return NavigationSlices(
        overview_index=OVERVIEW_INDEX,
        scientific_infrastructure_index=SCIENTIFIC_INFRASTRUCTURE_INDEX,
        category_start=category_start,
        category_stop=category_stop,
        corpus_start=corpus_start,
        corpus_stop=corpus_stop,
        protocolled_start=corpus_stop,
    )


def build_navigation_contract(
    *,
    tr_key: Callable[..., str],
    category_definitions: Sequence[Mapping[str, object]],
    corpus_definitions: Sequence[Mapping[str, object]],
    protocolled_units: Sequence[Mapping[str, object]],
) -> tuple[list[str], NavigationSlices]:
    """Monta rótulos e fatias a partir das definições públicas existentes."""
    labels = build_top_level_labels(
        overview_label=tr_key("navigation.overview"),
        category_labels=(
            tr_key("navigation.category", label=str(item["short_label"]))
            for item in category_definitions
        ),
        corpus_labels=(
            tr_key("navigation.unit", label=str(item["short_label"]))
            for item in corpus_definitions
        ),
        protocolled_labels=(
            tr_key("navigation.documented_case", label=str(item["unit_label"]))
            for item in protocolled_units
        ),
    )
    slices = calculate_navigation_slices(
        category_total=len(category_definitions),
        corpus_total=len(corpus_definitions),
    )
    return labels, slices
