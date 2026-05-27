from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests
import urllib3
from bs4 import BeautifulSoup
from requests.exceptions import SSLError

from .config import HEADERS, OUTPUT_DIR, REQUEST_TIMEOUT


EUROPEAN_AGGREGATOR_EVALUATION_FILENAME = "observatorio_avaliacao_agregadores_europa.csv"
EUROPEAN_AGGREGATOR_ACCESS_ROUTES_FILENAME = "observatorio_rotas_acesso_agregadores_europa.csv"
EUROPEAN_AGGREGATOR_PROBES_FILENAME = "observatorio_probes_agregadores_europa.csv"
EUROPEAN_AGGREGATOR_PROTOCOLS_FILENAME = "observatorio_protocolos_agregadores_europa.csv"
EUROPEAN_AGGREGATOR_SUMMARY_FILENAME = "observatorio_resumo_agregadores_europa.csv"
EUROPEAN_AGGREGATOR_RULE_VERSION = "2026-05-fechamento-europa-v1"

EVALUATION_COLUMNS = [
    "code",
    "label",
    "country_scope",
    "coverage_level",
    "source_url",
    "evaluation_stage",
    "access_model",
    "candidate_status",
    "audiovisual_probe_terms",
    "probe_attempts",
    "accessible_probe_count",
    "blocked_probe_count",
    "failed_probe_count",
    "search_result_count_total",
    "successful_probe_terms",
    "blocked_probe_terms",
    "best_probe_url",
    "ingestion_recommendation",
    "next_step",
    "evaluated_at",
    "rule_version",
]

PROBE_COLUMNS = [
    "code",
    "label",
    "probe_type",
    "query",
    "url",
    "http_status",
    "final_url",
    "content_type",
    "title",
    "access_status",
    "js_cookie_required",
    "cloudflare_challenge",
    "tls_verification_failed",
    "result_count",
    "audiovisual_evidence_signal_count",
    "methodological_note",
    "error",
]

SUMMARY_COLUMNS = [
    "status",
    "total",
    "recommended_next_step",
]

PROTOCOL_COLUMNS = [
    "code",
    "label",
    "country_scope",
    "candidate_status",
    "access_model",
    "protocol_needed",
    "protocol_status",
    "evidence_summary",
    "methodological_risk",
    "recommended_protocol",
    "incorporation_decision",
    "priority",
    "next_review_trigger",
    "evaluated_at",
    "rule_version",
]

ACCESS_ROUTE_COLUMNS = [
    "code",
    "label",
    "country_scope",
    "route_type",
    "route_url",
    "source_reference_url",
    "source_reference_note",
    "http_status",
    "final_url",
    "content_type",
    "access_status",
    "route_viability",
    "audiovisual_use",
    "methodological_note",
    "evaluated_at",
    "rule_version",
    "error",
]


@dataclass(frozen=True)
class AggregatorCandidate:
    code: str
    label: str
    country_scope: str
    coverage_level: str
    source_url: str
    search_url_template: str
    query_terms: tuple[str, ...]
    methodological_note: str


@dataclass(frozen=True)
class AggregatorAccessRoute:
    code: str
    label: str
    country_scope: str
    route_type: str
    route_url: str
    source_reference_url: str
    source_reference_note: str
    audiovisual_use: str
    methodological_note: str


EUROPEAN_AGGREGATOR_CANDIDATES = [
    AggregatorCandidate(
        code="archives-hub",
        label="Archives Hub",
        country_scope="Reino Unido",
        coverage_level="agregador nacional",
        source_url="https://archiveshub.jisc.ac.uk/",
        search_url_template="https://archiveshub.jisc.ac.uk/search/?terms={query}",
        query_terms=("audiovisual", "film", "video", "moving image"),
        methodological_note=(
            "Agregador nacional geral. A avaliação verifica se a busca pública permite "
            "sondar materiais audiovisuais antes da incorporação como corpus."
        ),
    ),
    AggregatorCandidate(
        code="francearchives",
        label="FranceArchives",
        country_scope="França",
        coverage_level="agregador nacional",
        source_url="https://francearchives.gouv.fr/",
        search_url_template="https://francearchives.gouv.fr/fr/search?es_escategory=archives&q={query}",
        query_terms=("audiovisuel", "film", "vidéo"),
        methodological_note=(
            "Agregador nacional geral. A avaliação verifica a superfície pública de busca "
            "e registra quando a fonte exige navegação com JavaScript ou cookies."
        ),
    ),
    AggregatorCandidate(
        code="pares",
        label="PARES",
        country_scope="Espanha",
        coverage_level="agregador nacional",
        source_url="https://pares.cultura.gob.es/",
        search_url_template="https://pares.mcu.es/ParesBusquedas20/catalogo/find?nm=&texto={query}",
        query_terms=("audiovisual", "film", "video"),
        methodological_note=(
            "Agregador nacional geral. A avaliação usa a busca pública do PARES para "
            "identificar sinais preliminares de materiais audiovisuais."
        ),
    ),
    AggregatorCandidate(
        code="portal-portugues-arquivos",
        label="Portal Português de Arquivos",
        country_scope="Portugal",
        coverage_level="agregador nacional",
        source_url="https://portal.arquivos.pt/",
        search_url_template="https://portal.arquivos.pt/search?q={query}",
        query_terms=("audiovisual", "video", "vídeo", "filme"),
        methodological_note=(
            "Agregador nacional português. Entra no mapeamento europeu para reduzir lacuna "
            "ibérica e testar sinais audiovisuais antes de qualquer pipeline próprio."
        ),
    ),
    AggregatorCandidate(
        code="european-film-gateway",
        label="European Film Gateway",
        country_scope="Europa",
        coverage_level="agregador audiovisual europeu",
        source_url="https://www.europeanfilmgateway.eu/",
        search_url_template="https://www.europeanfilmgateway.eu/search-efg?searchString={query}",
        query_terms=("film", "video", "war", "newsreel"),
        methodological_note=(
            "Agregador temático cinematográfico europeu. A avaliação verifica se a busca pública "
            "oferece evidência comparável antes da incorporação como corpus."
        ),
    ),
    AggregatorCandidate(
        code="europeana",
        label="Europeana",
        country_scope="Europa",
        coverage_level="agregador cultural europeu",
        source_url="https://www.europeana.eu/",
        search_url_template="https://www.europeana.eu/en/search?query={query}&media=true",
        query_terms=("film", "video", "audiovisual", "moving image"),
        methodological_note=(
            "Agregador cultural europeu amplo. Entra na Europa 1.5 como fonte geral com "
            "superfícies audiovisuais, exigindo separação entre patrimônio cultural amplo e audiovisual."
        ),
    ),
]

EUROPEAN_AGGREGATOR_ACCESS_ROUTES = [
    AggregatorAccessRoute(
        code="archives-hub",
        label="Archives Hub",
        country_scope="Reino Unido",
        route_type="SRU",
        route_url="https://archiveshub.jisc.ac.uk/sru/",
        source_reference_url="https://blog.archiveshub.jisc.ac.uk/category/apis/",
        source_reference_note=(
            "O blog do Archives Hub registra SRU como interface de busca usada pela API do Hub."
        ),
        audiovisual_use=(
            "Sondar descrições EAD por termos audiovisuais e, depois, procurar sinais como dao, "
            "digital object, film, video e moving image."
        ),
        methodological_note=(
            "Rota documentada, mas a disponibilidade deve ser confirmada antes de promover o "
            "Archives Hub a corpus ativo."
        ),
    ),
    AggregatorAccessRoute(
        code="archives-hub",
        label="Archives Hub",
        country_scope="Reino Unido",
        route_type="OAI-PMH",
        route_url="https://archiveshub.jisc.ac.uk/oaipmh/",
        source_reference_url="https://blog.archiveshub.jisc.ac.uk/category/apis/",
        source_reference_note=(
            "O blog do Archives Hub registra OAI-PMH como uma das interfaces para acesso às descrições."
        ),
        audiovisual_use=(
            "Avaliar colheita incremental de metadados e filtrar descrições com sinais "
            "audiovisuais sem depender da busca pública bloqueada."
        ),
        methodological_note=(
            "Rota útil para protocolo de ingestão estável caso a interface responda sem bloqueio."
        ),
    ),
    AggregatorAccessRoute(
        code="francearchives",
        label="FranceArchives",
        country_scope="França",
        route_type="Open Data",
        route_url="https://francearchives.gouv.fr/fr/open_data",
        source_reference_url="https://francearchives.gouv.fr/fr/open_data",
        source_reference_note=(
            "A página oficial de dados abertos informa que inventários do portal são oferecidos "
            "para reutilização em formatos abertos."
        ),
        audiovisual_use=(
            "Mapear conjuntos de metadados reutilizáveis antes de buscar evidência audiovisual "
            "em registros descritivos."
        ),
        methodological_note=(
            "Rota institucional de referência; não equivale, por si só, a acesso direto a vídeos."
        ),
    ),
    AggregatorAccessRoute(
        code="francearchives",
        label="FranceArchives",
        country_scope="França",
        route_type="Dataset XML APE-EAD",
        route_url="https://data-dump.francearchives.gouv.fr/ape-ead-eac/francearchives_ape_ead.zip",
        source_reference_url=(
            "https://data.culture.gouv.fr/explore/dataset/"
            "inventaires-des-archives-publiques-francearchives/"
        ),
        source_reference_note=(
            "A ficha de dados do Ministério da Cultura descreve os inventários FranceArchives "
            "convertidos em XML APE-EAD."
        ),
        audiovisual_use=(
            "Baixar em etapa posterior, indexar XML APE-EAD localmente e separar registros com "
            "vocabulário audiovisual, objetos digitais e links externos."
        ),
        methodological_note=(
            "Rota mais promissora para FranceArchives, mas deve entrar como protótipo próprio "
            "para evitar coleta pesada no ciclo mensal."
        ),
    ),
    AggregatorAccessRoute(
        code="francearchives",
        label="FranceArchives",
        country_scope="França",
        route_type="API de dataset",
        route_url=(
            "https://data.culture.gouv.fr/api/explore/v2.1/catalog/datasets/"
            "inventaires-des-archives-publiques-francearchives/records?limit=1"
        ),
        source_reference_url=(
            "https://data.culture.gouv.fr/explore/dataset/"
            "inventaires-des-archives-publiques-francearchives/"
        ),
        source_reference_note=(
            "A plataforma data.culture.gouv.fr expõe aba/API do dataset usado como referência."
        ),
        audiovisual_use=(
            "Testar se a API pública oferece metadados suficientes para triagem leve antes "
            "de baixar o pacote XML."
        ),
        methodological_note=(
            "Rota auxiliar: uma API acessível com retorno vazio ainda pode coexistir com pacote "
            "XML disponível para download."
        ),
    ),
    AggregatorAccessRoute(
        code="portal-portugues-arquivos",
        label="Portal Português de Arquivos",
        country_scope="Portugal",
        route_type="Busca pública",
        route_url="https://portal.arquivos.pt/search?q=video",
        source_reference_url="https://portal.arquivos.pt/",
        source_reference_note=(
            "O portal oficial descreve o PPA como agregador de metainformação e, quando possível, "
            "imagens das entidades aderentes à Rede Portuguesa de Arquivos."
        ),
        audiovisual_use=(
            "Sondar termos audiovisuais em descrições portuguesas e separar fotografia, som, filme e vídeo "
            "antes de promover o portal a corpus ativo definitivo."
        ),
        methodological_note=(
            "Rota nacional prioritária para fechar a lacuna Portugal sem confundir descrição arquivística "
            "com reprodução audiovisual acessível."
        ),
    ),
    AggregatorAccessRoute(
        code="european-film-gateway",
        label="European Film Gateway",
        country_scope="Europa",
        route_type="Busca pública",
        route_url="https://www.europeanfilmgateway.eu/search-efg?searchString=film",
        source_reference_url="https://www.europeanfilmgateway.eu/",
        source_reference_note=(
            "O portal se apresenta como ponto único de acesso a filmes, imagens e textos de "
            "coleções selecionadas de arquivos cinematográficos europeus."
        ),
        audiovisual_use=(
            "Testar se a busca pública oferece registros audiovisuais suficientes para um "
            "corpus europeu temático de cinema."
        ),
        methodological_note=(
            "Rota prioritária da Europa 1.5 por ser agregador audiovisual europeu especializado."
        ),
    ),
    AggregatorAccessRoute(
        code="europeana",
        label="Europeana",
        country_scope="Europa",
        route_type="Busca pública com filtro de mídia",
        route_url="https://www.europeana.eu/en/search?query=film&media=true",
        source_reference_url="https://www.europeana.eu/",
        source_reference_note=(
            "Europeana é agregador europeu amplo de patrimônio cultural digital; a avaliação usa "
            "busca pública com filtro de mídia."
        ),
        audiovisual_use=(
            "Verificar a utilidade de Europeana como agregador geral para objetos audiovisuais, "
            "sem confundi-la com um arquivo audiovisual especializado."
        ),
        methodological_note=(
            "Rota obrigatória da Europa 1.5, mas exige protocolo para separar audiovisual de acervo cultural geral."
        ),
    ),
    AggregatorAccessRoute(
        code="europeana",
        label="Europeana",
        country_scope="Europa",
        route_type="Documentação de API",
        route_url="https://pro.europeana.eu/page/apis",
        source_reference_url="https://pro.europeana.eu/page/apis",
        source_reference_note=(
            "A documentação oficial da Europeana apresenta APIs para acesso e reutilização de dados."
        ),
        audiovisual_use=(
            "Avaliar se a API pode sustentar triagem controlada por mídia, tipo de objeto e termos audiovisuais."
        ),
        methodological_note=(
            "Rota técnica potencial para corpus futuro, sujeita a chave, limites e condições de uso."
        ),
    ),
]


def utcnow_iso():
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_space(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def parse_result_count(text):
    normalized = _normalize_space(text)
    patterns = [
        r"Resultados\s+\d+\s*-\s*\d+\s+de\s+([\d\.]+)",
        r"Résultats?\s+\d+\s*-\s*\d+\s+sur\s+([\d\s]+)",
        r"([\d\s]+)\s+résultats?",
        r"You search for .+ and ([\d,\.]+) records were found",
        r"Videos?\s*\(([\d,\.]+)\s+Results?\)",
        r"([\d,]+)\s+results?",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match:
            return int(re.sub(r"\D", "", match.group(1)) or 0)
    return 0


def detect_js_cookie_requirement(text, title=""):
    normalized = f"{title} {text}".lower()
    return (
        "requires js enabled and cookies" in normalized
        or "enable javascript and cookies" in normalized
        or "just a moment" in normalized
    )


def detect_cloudflare_challenge(text, title=""):
    normalized = f"{title} {text}".lower()
    return "cloudflare" in normalized or "cf-browser-verification" in normalized


def classify_probe_access_status(http_status, js_cookie_required, error):
    if error:
        return "falha_tecnica"
    if js_cookie_required:
        return "bloqueado_por_js_ou_cookies"
    if http_status in {401, 403}:
        return "restrito_ou_bloqueado"
    if http_status and 200 <= int(http_status) < 300:
        return "acessivel"
    if http_status:
        return f"resposta_http_{http_status}"
    return "sem_resposta"


def fetch_probe(url):
    tls_verification_failed = False
    error = ""
    response = None
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
    except SSLError as exc:
        tls_verification_failed = True
        error = str(exc)
        try:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
                verify=False,
            )
            error = ""
        except Exception as retry_error:
            error = str(retry_error)
    except Exception as exc:
        error = str(exc)

    if response is None:
        return {
            "http_status": "",
            "final_url": url,
            "content_type": "",
            "title": "",
            "text": "",
            "tls_verification_failed": tls_verification_failed,
            "error": error,
        }

    soup = BeautifulSoup(response.text, "html.parser")
    title = _normalize_space(soup.title.get_text(" ", strip=True) if soup.title else "")
    text = _normalize_space(soup.get_text(" ", strip=True))
    return {
        "http_status": int(response.status_code),
        "final_url": response.url,
        "content_type": response.headers.get("content-type", ""),
        "title": title,
        "text": text,
        "tls_verification_failed": tls_verification_failed,
        "error": error,
    }


def fetch_route_probe(url, sample_bytes=65536):
    tls_verification_failed = False
    error = ""
    response = None
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
            stream=True,
        )
    except SSLError as exc:
        tls_verification_failed = True
        error = str(exc)
        try:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
                verify=False,
                stream=True,
            )
            error = ""
        except Exception as retry_error:
            error = str(retry_error)
    except Exception as exc:
        error = str(exc)

    if response is None:
        return {
            "http_status": "",
            "final_url": url,
            "content_type": "",
            "title": "",
            "text": "",
            "tls_verification_failed": tls_verification_failed,
            "error": error,
        }

    text = ""
    title = ""
    try:
        content_type = response.headers.get("content-type", "")
        if "text" in content_type or "html" in content_type or "json" in content_type or "xml" in content_type:
            sample = response.raw.read(sample_bytes, decode_content=True)
            text = sample.decode(response.encoding or "utf-8", errors="replace")
            soup = BeautifulSoup(text, "html.parser")
            title = _normalize_space(soup.title.get_text(" ", strip=True) if soup.title else "")
    finally:
        response.close()

    return {
        "http_status": int(response.status_code),
        "final_url": response.url,
        "content_type": response.headers.get("content-type", ""),
        "title": title,
        "text": _normalize_space(text),
        "tls_verification_failed": tls_verification_failed,
        "error": error,
    }


def _build_probe_row(candidate, probe_type, query, url, fetcher=fetch_probe):
    fetched = fetcher(url)
    text = fetched.get("text", "")
    title = fetched.get("title", "")
    js_cookie_required = detect_js_cookie_requirement(text, title)
    cloudflare_challenge = detect_cloudflare_challenge(text, title)
    result_count = parse_result_count(text)
    evidence_signal_count = sum(
        text.lower().count(term.lower())
        for term in candidate.query_terms
        if term
    )
    access_status = classify_probe_access_status(
        fetched.get("http_status"),
        js_cookie_required,
        fetched.get("error", ""),
    )

    return {
        "code": candidate.code,
        "label": candidate.label,
        "probe_type": probe_type,
        "query": query,
        "url": url,
        "http_status": fetched.get("http_status", ""),
        "final_url": fetched.get("final_url", url),
        "content_type": fetched.get("content_type", ""),
        "title": title,
        "access_status": access_status,
        "js_cookie_required": js_cookie_required,
        "cloudflare_challenge": cloudflare_challenge,
        "tls_verification_failed": bool(fetched.get("tls_verification_failed", False)),
        "result_count": result_count,
        "audiovisual_evidence_signal_count": evidence_signal_count,
        "methodological_note": candidate.methodological_note,
        "error": fetched.get("error", ""),
    }


def _classify_route_viability(route, access_status, content_type):
    normalized_content_type = str(content_type or "").lower()
    if access_status == "acessivel":
        if route.route_type == "Dataset XML APE-EAD":
            return "rota_de_download_documentada_e_acessivel"
        if "json" in normalized_content_type:
            return "rota_api_acessivel_para_teste_controlado"
        return "rota_publica_acessivel"
    if route.code == "archives-hub" and access_status in {"bloqueado_por_js_ou_cookies", "restrito_ou_bloqueado"}:
        return "rota_documentada_mas_bloqueada_na_sondagem_simples"
    if access_status == "falha_tecnica":
        return "rota_documentada_com_falha_tecnica_na_rodada"
    return "rota_documentada_sem_confirmacao_de_acesso"


def _build_access_route_row(route, evaluated_at, fetcher=fetch_route_probe):
    fetched = fetcher(route.route_url)
    text = fetched.get("text", "")
    title = fetched.get("title", "")
    js_cookie_required = detect_js_cookie_requirement(text, title)
    access_status = classify_probe_access_status(
        fetched.get("http_status"),
        js_cookie_required,
        fetched.get("error", ""),
    )
    route_viability = _classify_route_viability(
        route,
        access_status,
        fetched.get("content_type", ""),
    )

    return {
        "code": route.code,
        "label": route.label,
        "country_scope": route.country_scope,
        "route_type": route.route_type,
        "route_url": route.route_url,
        "source_reference_url": route.source_reference_url,
        "source_reference_note": route.source_reference_note,
        "http_status": fetched.get("http_status", ""),
        "final_url": fetched.get("final_url", route.route_url),
        "content_type": fetched.get("content_type", ""),
        "access_status": access_status,
        "route_viability": route_viability,
        "audiovisual_use": route.audiovisual_use,
        "methodological_note": route.methodological_note,
        "evaluated_at": evaluated_at,
        "rule_version": EUROPEAN_AGGREGATOR_RULE_VERSION,
        "error": fetched.get("error", ""),
    }


def build_european_aggregator_access_routes(fetcher=fetch_route_probe, evaluated_at=None):
    evaluated_at = evaluated_at or utcnow_iso()
    rows = [
        _build_access_route_row(route, evaluated_at=evaluated_at, fetcher=fetcher)
        for route in EUROPEAN_AGGREGATOR_ACCESS_ROUTES
    ]
    return pd.DataFrame(rows, columns=ACCESS_ROUTE_COLUMNS)


def build_european_aggregator_probe_rows(fetcher=fetch_probe):
    rows = []
    for candidate in EUROPEAN_AGGREGATOR_CANDIDATES:
        rows.append(
            _build_probe_row(
                candidate,
                probe_type="home",
                query="",
                url=candidate.source_url,
                fetcher=fetcher,
            )
        )
        for term in candidate.query_terms:
            search_url = candidate.search_url_template.format(query=quote(term))
            rows.append(
                _build_probe_row(
                    candidate,
                    probe_type="search",
                    query=term,
                    url=search_url,
                    fetcher=fetcher,
                )
            )
    return rows


def _build_candidate_summary(candidate, candidate_probe_df, evaluated_at):
    search_probe_df = candidate_probe_df.loc[candidate_probe_df["probe_type"] == "search"].copy()
    accessible_probe_count = int((candidate_probe_df["access_status"] == "acessivel").sum())
    blocked_probe_count = int(
        candidate_probe_df["access_status"].isin(
            {"bloqueado_por_js_ou_cookies", "restrito_ou_bloqueado"}
        ).sum()
    )
    failed_probe_count = int((candidate_probe_df["access_status"] == "falha_tecnica").sum())
    result_total = int(pd.to_numeric(search_probe_df["result_count"], errors="coerce").fillna(0).sum())
    successful_terms = sorted(
        search_probe_df.loc[
            pd.to_numeric(search_probe_df["result_count"], errors="coerce").fillna(0) > 0,
            "query",
        ]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )
    blocked_terms = sorted(
        search_probe_df.loc[
            search_probe_df["access_status"].isin(
                {"bloqueado_por_js_ou_cookies", "restrito_ou_bloqueado"}
            ),
            "query",
        ]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )
    best_probe_row = (
        search_probe_df.sort_values("result_count", ascending=False).head(1)
        if not search_probe_df.empty
        else pd.DataFrame()
    )
    best_probe_url = (
        str(best_probe_row.iloc[0].get("final_url") or best_probe_row.iloc[0].get("url"))
        if not best_probe_row.empty and int(best_probe_row.iloc[0].get("result_count") or 0) > 0
        else ""
    )

    if result_total > 0:
        access_model = "busca_publica_com_resultados"
        candidate_status = "pronto_para_validacao_total"
        ingestion_recommendation = "executar_validacao_total_antes_da_incorporacao_definitiva"
        next_step = "validar_cobertura_metadados_amostras_e_rotas_antes_do_corpus"
    elif accessible_probe_count > 0 and blocked_probe_count == 0:
        access_model = "acesso_publico_sem_sinal_audiovisual_quantificado"
        candidate_status = "fonte_de_pesquisa_com_retorno_zero_preliminar"
        ingestion_recommendation = "manter_como_fonte_geral_e_testar_termos_adicionais"
        next_step = "ampliar_vocabulario_de_busca_antes_de_incorporar"
    elif blocked_probe_count > 0:
        access_model = "exige_js_cookies_ou_superficie_bloqueada"
        candidate_status = "requer_protocolo_de_acesso"
        ingestion_recommendation = "avaliar_api_exportacao_ou_navegacao_com_browser"
        next_step = "mapear_rota_tecnica_estavel_antes_do_pipeline"
    else:
        access_model = "falha_tecnica_ou_sem_resposta"
        candidate_status = "monitoramento_tecnico"
        ingestion_recommendation = "retestar_em_rodada_posterior"
        next_step = "monitorar_sem_ingestao_imediata"

    return {
        "code": candidate.code,
        "label": candidate.label,
        "country_scope": candidate.country_scope,
        "coverage_level": candidate.coverage_level,
        "source_url": candidate.source_url,
        "evaluation_stage": "fechamento_europa",
        "access_model": access_model,
        "candidate_status": candidate_status,
        "audiovisual_probe_terms": "; ".join(candidate.query_terms),
        "probe_attempts": len(candidate_probe_df),
        "accessible_probe_count": accessible_probe_count,
        "blocked_probe_count": blocked_probe_count,
        "failed_probe_count": failed_probe_count,
        "search_result_count_total": result_total,
        "successful_probe_terms": "; ".join(successful_terms),
        "blocked_probe_terms": "; ".join(blocked_terms),
        "best_probe_url": best_probe_url,
        "ingestion_recommendation": ingestion_recommendation,
        "next_step": next_step,
        "evaluated_at": evaluated_at,
        "rule_version": EUROPEAN_AGGREGATOR_RULE_VERSION,
    }


def _build_protocol_row(evaluation_row):
    status = str(evaluation_row.get("candidate_status", ""))
    access_model = str(evaluation_row.get("access_model", ""))
    total_results = int(evaluation_row.get("search_result_count_total") or 0)
    blocked_count = int(evaluation_row.get("blocked_probe_count") or 0)
    failed_count = int(evaluation_row.get("failed_probe_count") or 0)
    successful_terms = str(evaluation_row.get("successful_probe_terms") or "").strip()
    blocked_terms = str(evaluation_row.get("blocked_probe_terms") or "").strip()

    if status == "pronto_para_validacao_total":
        protocol_needed = False
        protocol_status = "rota_publica_suficiente_para_validacao_total"
        evidence_summary = (
            f"A busca pública retornou {total_results} resultados preliminares"
            + (f" nos termos: {successful_terms}." if successful_terms else ".")
        )
        methodological_risk = (
            "A contagem inicial indica evidência pública detectável, mas ainda exige validação "
            "qualitativa para separar registro descritivo, objeto digital e reprodução audiovisual."
        )
        recommended_protocol = "executar_validacao_total_e_somente_entao_incorporar"
        incorporation_decision = "validar_totalmente_antes_de_incorporar_como_corpus_ativo"
        priority = "alta"
        next_review_trigger = "conclusao_da_validacao_total"
    elif status == "requer_protocolo_de_acesso":
        protocol_needed = True
        protocol_status = "protocolo_tecnico_pendente"
        evidence_summary = (
            f"Foram observadas {blocked_count} sondagens bloqueadas ou dependentes de JS/cookies"
            + (f" nos termos: {blocked_terms}." if blocked_terms else ".")
        )
        methodological_risk = (
            "A coleta por requisição simples pode produzir falso retorno zero. A fonte deve "
            "permanecer como candidata, sem ser confundida com corpus ativo."
        )
        recommended_protocol = "testar_api_exportacao_sitemap_ou_navegacao_controlada_com_browser"
        incorporation_decision = "nao_incorporar_como_corpus_ativo_ate_haver_rota_estavel"
        priority = "media"
        next_review_trigger = "identificacao_de_api_exportacao_sitemap_ou_rota_publica_estavel"
    elif status == "fonte_de_pesquisa_com_retorno_zero_preliminar":
        protocol_needed = False
        protocol_status = "revisao_vocabular_pendente"
        evidence_summary = "A fonte respondeu, mas não retornou resultados quantificados na sondagem inicial."
        methodological_risk = (
            "Retorno zero em fonte geral não prova ausência de acervo audiovisual; pode indicar "
            "vocabulário inadequado, metadados pouco granulares ou baixa visibilidade pública."
        )
        recommended_protocol = "ampliar_vocabulario_multilingue_e_reexecutar_sondagem"
        incorporation_decision = "manter_como_fonte_de_pesquisa_sem_pipeline_ativo"
        priority = "baixa"
        next_review_trigger = "ampliacao_de_termos_ou_nova_evidencia_publica"
    else:
        protocol_needed = True
        protocol_status = "monitoramento_tecnico"
        evidence_summary = f"A rodada registrou {failed_count} falhas técnicas e não produziu rota confiável."
        methodological_risk = (
            "Sem resposta técnica estável, a ausência de resultados não pode ser interpretada "
            "como ausência de audiovisual."
        )
        recommended_protocol = "retestar_em_rodada_posterior_e_documentar_falhas"
        incorporation_decision = "monitorar_sem_ingestao_imediata"
        priority = "baixa"
        next_review_trigger = "normalizacao_da_resposta_http_ou_disponibilidade_da_fonte"

    return {
        "code": evaluation_row.get("code", ""),
        "label": evaluation_row.get("label", ""),
        "country_scope": evaluation_row.get("country_scope", ""),
        "candidate_status": status,
        "access_model": access_model,
        "protocol_needed": protocol_needed,
        "protocol_status": protocol_status,
        "evidence_summary": evidence_summary,
        "methodological_risk": methodological_risk,
        "recommended_protocol": recommended_protocol,
        "incorporation_decision": incorporation_decision,
        "priority": priority,
        "next_review_trigger": next_review_trigger,
        "evaluated_at": evaluation_row.get("evaluated_at", ""),
        "rule_version": evaluation_row.get("rule_version", EUROPEAN_AGGREGATOR_RULE_VERSION),
    }


def build_european_aggregator_protocols(evaluation_df):
    if evaluation_df is None or evaluation_df.empty:
        return pd.DataFrame(columns=PROTOCOL_COLUMNS)
    rows = [_build_protocol_row(row) for _, row in evaluation_df.iterrows()]
    return pd.DataFrame(rows, columns=PROTOCOL_COLUMNS)


def build_european_aggregator_evaluation(fetcher=fetch_probe, route_fetcher=fetch_route_probe, evaluated_at=None):
    evaluated_at = evaluated_at or utcnow_iso()
    probe_rows = build_european_aggregator_probe_rows(fetcher=fetcher)
    probes_df = pd.DataFrame(probe_rows, columns=PROBE_COLUMNS)
    evaluation_rows = []
    for candidate in EUROPEAN_AGGREGATOR_CANDIDATES:
        candidate_probe_df = probes_df.loc[probes_df["code"] == candidate.code].copy()
        evaluation_rows.append(_build_candidate_summary(candidate, candidate_probe_df, evaluated_at))

    evaluation_df = pd.DataFrame(evaluation_rows, columns=EVALUATION_COLUMNS)
    summary_df = (
        evaluation_df.groupby(["candidate_status", "next_step"], dropna=False)
        .size()
        .reset_index(name="total")
        .rename(
            columns={
                "candidate_status": "status",
                "next_step": "recommended_next_step",
            }
        )
        .sort_values(["total", "status"], ascending=[False, True])
        .reset_index(drop=True)
    )
    protocols_df = build_european_aggregator_protocols(evaluation_df)
    access_routes_df = build_european_aggregator_access_routes(
        fetcher=route_fetcher,
        evaluated_at=evaluated_at,
    )
    return {
        "access_routes": access_routes_df,
        "evaluation": evaluation_df,
        "probes": probes_df,
        "protocols": protocols_df,
        "summary": summary_df,
    }


def write_european_aggregator_evaluation(
    output_dir: Path = OUTPUT_DIR,
    fetcher=fetch_probe,
    route_fetcher=fetch_route_probe,
):
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_european_aggregator_evaluation(
        fetcher=fetcher,
        route_fetcher=route_fetcher,
    )
    outputs["access_routes"].to_csv(
        output_dir / EUROPEAN_AGGREGATOR_ACCESS_ROUTES_FILENAME,
        index=False,
        encoding="utf-8-sig",
    )
    outputs["evaluation"].to_csv(
        output_dir / EUROPEAN_AGGREGATOR_EVALUATION_FILENAME,
        index=False,
        encoding="utf-8-sig",
    )
    outputs["probes"].to_csv(
        output_dir / EUROPEAN_AGGREGATOR_PROBES_FILENAME,
        index=False,
        encoding="utf-8-sig",
    )
    outputs["protocols"].to_csv(
        output_dir / EUROPEAN_AGGREGATOR_PROTOCOLS_FILENAME,
        index=False,
        encoding="utf-8-sig",
    )
    outputs["summary"].to_csv(
        output_dir / EUROPEAN_AGGREGATOR_SUMMARY_FILENAME,
        index=False,
        encoding="utf-8-sig",
    )
    return outputs


__all__ = [
    "ACCESS_ROUTE_COLUMNS",
    "EUROPEAN_AGGREGATOR_ACCESS_ROUTES",
    "EUROPEAN_AGGREGATOR_ACCESS_ROUTES_FILENAME",
    "EUROPEAN_AGGREGATOR_CANDIDATES",
    "EUROPEAN_AGGREGATOR_EVALUATION_FILENAME",
    "EUROPEAN_AGGREGATOR_PROBES_FILENAME",
    "EUROPEAN_AGGREGATOR_PROTOCOLS_FILENAME",
    "EUROPEAN_AGGREGATOR_RULE_VERSION",
    "EUROPEAN_AGGREGATOR_SUMMARY_FILENAME",
    "build_european_aggregator_access_routes",
    "build_european_aggregator_evaluation",
    "build_european_aggregator_probe_rows",
    "build_european_aggregator_protocols",
    "classify_probe_access_status",
    "detect_js_cookie_requirement",
    "parse_result_count",
    "write_european_aggregator_evaluation",
]
