from __future__ import annotations

from .config import (
    CNCAFF_EFG_PAGE_URL,
    CNCAFF_EFG_SEARCH_URL,
    CNCAFF_HOME_URL,
    CNCAFF_LEGACY_URL,
    CNCAFF_LISE_URL,
)
from .efg_institutional import EfgInstitutionalCorpusConfig
from .efg_institutional import collect_efg_institutional_dataset
from .efg_institutional import collect_efg_institutional_institutions
from .efg_institutional import extract_efg_result_total
from .efg_institutional import parse_efg_detail_page
from .efg_institutional import parse_efg_search_page


CNCAFF_REPOSITORY_CODE = "FR-CNC-AFF"
CNCAFF_ARCHIVE_TYPE = "National film archive"
CNCAFF_COUNTRY = "France"
CNCAFF_INSTITUTION_NAME = "Centre national du cinéma et de l'image animée - Archives françaises du film"
CNCAFF_PLATFORM_LABEL = "European Film Gateway"
CNCAFF_DETAIL_PREFIX = "cnc::"
CNCAFF_MAX_SEARCH_PAGES = 20

CNCAFF_CONFIG = EfgInstitutionalCorpusConfig(
    code="cnc-aff",
    institution_name=CNCAFF_INSTITUTION_NAME,
    repository_code=CNCAFF_REPOSITORY_CODE,
    archive_type=CNCAFF_ARCHIVE_TYPE,
    country=CNCAFF_COUNTRY,
    detail_url_field="cnc_aff_detail_url",
    home_url=CNCAFF_HOME_URL,
    external_url=CNCAFF_EFG_PAGE_URL,
    search_url=CNCAFF_EFG_SEARCH_URL,
    detail_prefix=CNCAFF_DETAIL_PREFIX,
    context_urls=[
        (CNCAFF_HOME_URL, "Página oficial da Direction du patrimoine cinématographique do CNC."),
        (CNCAFF_EFG_PAGE_URL, "Página do CNC/AFF como arquivo contribuinte no European Film Gateway."),
        (CNCAFF_LEGACY_URL, "Domínio histórico cnc-aff.fr divulgado por fontes externas; testado para registrar indisponibilidade DNS quando ocorrer."),
        (CNCAFF_LISE_URL, "Rota LISE/CNC mencionada como catálogo histórico; testada para registrar indisponibilidade técnica quando ocorrer."),
    ],
    accept_language="fr,en;q=0.9,pt-BR;q=0.7",
    max_search_pages=CNCAFF_MAX_SEARCH_PAGES,
    request_pause=0.04,
    summary_note=(
        "Corpus incorporado como arquivo fílmico nacional francês em superfície pública mediada pelo "
        "European Film Gateway."
    ),
    scope_note=(
        "A unidade observa apenas a coleção pública CNC/AFF exposta no EFG, sem afirmar catálogo total "
        "das Archives françaises du film nem acesso direto ao domínio legado."
    ),
)


def collect_cnc_aff_institutions():
    return collect_efg_institutional_institutions(CNCAFF_CONFIG)


def collect_cnc_aff_dataset():
    return collect_efg_institutional_dataset(CNCAFF_CONFIG)


def parse_cnc_aff_search_page(html, page_url=CNCAFF_EFG_SEARCH_URL):
    return parse_efg_search_page(html, page_url, CNCAFF_DETAIL_PREFIX)


def extract_cnc_aff_result_total(html):
    return extract_efg_result_total(html)


def parse_cnc_aff_detail_page(html, page_url):
    return parse_efg_detail_page(html, page_url, CNCAFF_CONFIG)


__all__ = [
    "CNCAFF_ARCHIVE_TYPE",
    "CNCAFF_CONFIG",
    "CNCAFF_COUNTRY",
    "CNCAFF_DETAIL_PREFIX",
    "CNCAFF_INSTITUTION_NAME",
    "CNCAFF_MAX_SEARCH_PAGES",
    "CNCAFF_PLATFORM_LABEL",
    "CNCAFF_REPOSITORY_CODE",
    "collect_cnc_aff_dataset",
    "collect_cnc_aff_institutions",
    "extract_cnc_aff_result_total",
    "parse_cnc_aff_detail_page",
    "parse_cnc_aff_search_page",
]
