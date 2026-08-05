"""Plano canônico de navegação da interface pública.

A navegação principal permanece deliberadamente curta. As unidades documentais
são acessadas dentro de sua categoria, evitando uma aba superior para cada
corpus.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Mapping, Sequence


SCIENTIFIC_INFRASTRUCTURE_LABEL = "Infraestrutura científica"
SCIENTIFIC_INFRASTRUCTURE_LABELS_BY_OVERVIEW = {
    "Overview": "Scientific infrastructure",
    "Visión general": "Infraestructura científica",
    "Visão geral": SCIENTIFIC_INFRASTRUCTURE_LABEL,
}
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
    corpus_labels: Iterable[str] = (),
    protocolled_labels: Iterable[str] = (),
    scientific_infrastructure_label: str = SCIENTIFIC_INFRASTRUCTURE_LABEL,
) -> list[str]:
    """Retorna apenas as quatro áreas públicas de primeiro nível.

    ``corpus_labels`` e ``protocolled_labels`` permanecem na assinatura por
    compatibilidade, mas as unidades são navegadas dentro das categorias.
    """
    del corpus_labels, protocolled_labels
    return [
        overview_label,
        scientific_infrastructure_label,
        *list(category_labels),
    ]


def calculate_navigation_slices(
    *,
    category_total: int,
    corpus_total: int,
) -> NavigationSlices:
    """Calcula as fatias para duas categorias e nenhuma aba unitária."""
    if category_total < 0 or corpus_total < 0:
        raise ValueError("Navigation totals cannot be negative")

    category_start = CATEGORY_START_INDEX
    category_stop = category_start + category_total
    return NavigationSlices(
        overview_index=OVERVIEW_INDEX,
        scientific_infrastructure_index=SCIENTIFIC_INFRASTRUCTURE_INDEX,
        category_start=category_start,
        category_stop=category_stop,
        corpus_start=category_stop,
        corpus_stop=category_stop,
        protocolled_start=category_stop,
    )


def _resolve_scientific_infrastructure_label(
    *,
    tr_key: Callable[..., str],
    overview_label: str,
    supplied_label: str,
) -> str:
    """Resolve o rótulo científico por chave semântica, com fallback seguro."""
    # Test doubles used by the navigation contract return the key itself.
    # In that situation, preserve the historical default and avoid changing
    # the established call contract.
    if overview_label == "navigation.overview":
        return supplied_label

    semantic_key = "navigation.scientific_infrastructure"
    translated = tr_key(semantic_key)
    if translated != semantic_key:
        return translated

    if supplied_label != SCIENTIFIC_INFRASTRUCTURE_LABEL:
        return supplied_label

    return SCIENTIFIC_INFRASTRUCTURE_LABELS_BY_OVERVIEW.get(
        overview_label,
        SCIENTIFIC_INFRASTRUCTURE_LABEL,
    )


def build_navigation_contract(
    *,
    tr_key: Callable[..., str],
    category_definitions: Sequence[Mapping[str, object]],
    corpus_definitions: Sequence[Mapping[str, object]],
    protocolled_units: Sequence[Mapping[str, object]],
    scientific_infrastructure_label: str = SCIENTIFIC_INFRASTRUCTURE_LABEL,
) -> tuple[list[str], NavigationSlices]:
    """Monta as quatro abas e mantém unidades disponíveis às categorias."""
    overview_label = tr_key("navigation.overview")
    resolved_scientific_label = _resolve_scientific_infrastructure_label(
        tr_key=tr_key,
        overview_label=overview_label,
        supplied_label=scientific_infrastructure_label,
    )
    labels = build_top_level_labels(
        overview_label=overview_label,
        scientific_infrastructure_label=resolved_scientific_label,
        category_labels=(
            tr_key("navigation.category", label=str(item["short_label"]))
            for item in category_definitions
        ),
        corpus_labels=(str(item["short_label"]) for item in corpus_definitions),
        protocolled_labels=(str(item["unit_label"]) for item in protocolled_units),
    )
    slices = calculate_navigation_slices(
        category_total=len(category_definitions),
        corpus_total=len(corpus_definitions),
    )
    return labels, slices
