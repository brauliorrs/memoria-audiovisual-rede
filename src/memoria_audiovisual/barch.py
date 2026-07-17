from __future__ import annotations

from .config import (
    BARCH_DIGITAL_READING_ROOM_INFO_URL,
    BARCH_DIGITAL_READING_ROOM_URL,
    BARCH_EFG_COLLECTION_URL,
    BARCH_EFG_PAGE_URL,
    BARCH_FILMS_URL,
    BARCH_HOME_URL,
    BARCH_SEARCH_SYSTEMS_URL,
)
from .efg_institutional import (
    EfgInstitutionalCorpusConfig,
    collect_efg_institutional_dataset,
    collect_efg_institutional_institutions,
    extract_efg_result_total,
    parse_efg_detail_page,
    parse_efg_search_page,
)


BARCH_CONFIG = EfgInstitutionalCorpusConfig(
    code="barch",
    institution_name="Bundesarchiv",
    repository_code="DE-BArch",
    archive_type="Federal archive with film archive holdings",
    country="Germany",
    detail_url_field="barch_detail_url",
    home_url=BARCH_FILMS_URL,
    search_url=BARCH_EFG_COLLECTION_URL,
    external_url=BARCH_EFG_COLLECTION_URL,
    detail_prefix="barch::",
    accept_language="de,en;q=0.9,pt-BR;q=0.7",
    max_search_pages=30,
    context_urls=[
        (BARCH_HOME_URL, "Site institucional do Bundesarchiv."),
        (BARCH_FILMS_URL, "Página oficial sobre acervos fílmicos do Bundesarchiv."),
        (BARCH_SEARCH_SYSTEMS_URL, "Página oficial sobre sistemas de pesquisa do Bundesarchiv."),
        (BARCH_DIGITAL_READING_ROOM_INFO_URL, "Página oficial do Digitaler Lesesaal como plataforma de pesquisa e apresentação de filmes."),
        (BARCH_DIGITAL_READING_ROOM_URL, "Aplicação pública do Digitaler Lesesaal; contexto, não rota principal desta coleta."),
        (BARCH_EFG_PAGE_URL, "Página do Bundesarchiv-Filmarchiv como arquivo contribuinte no European Film Gateway."),
    ],
    summary_note=(
        "Corpus institucional incorporado pelo recorte público do Bundesarchiv-Filmarchiv no European Film Gateway. "
        "A unidade custodial é o Bundesarchiv; o EFG é superfície agregadora de acesso."
    ),
    scope_note=(
        "A página oficial informa mais de 250.000 filmes documentais e de ficção no Film Archive e uma seleção "
        "disponível em streaming no Digitaler Lesesaal; este corpus não afirma exaustividade do acervo interno."
    ),
)


def collect_barch_institutions():
    return collect_efg_institutional_institutions(BARCH_CONFIG)


def collect_barch_dataset():
    return collect_efg_institutional_dataset(BARCH_CONFIG)


def parse_barch_search_page(html, page_url=BARCH_EFG_COLLECTION_URL):
    return parse_efg_search_page(html, page_url, BARCH_CONFIG.detail_prefix)


def extract_barch_result_total(html):
    return extract_efg_result_total(html)


def parse_barch_detail_page(html, page_url):
    return parse_efg_detail_page(html, page_url, BARCH_CONFIG)


__all__ = [
    "BARCH_CONFIG",
    "collect_barch_dataset",
    "collect_barch_institutions",
    "extract_barch_result_total",
    "parse_barch_detail_page",
    "parse_barch_search_page",
]
