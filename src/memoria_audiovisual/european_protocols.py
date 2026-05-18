from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests
import urllib3
from requests.exceptions import SSLError

from .config import HEADERS, OUTPUT_DIR, REQUEST_TIMEOUT
from .european_aggregators import classify_probe_access_status, detect_js_cookie_requirement


ARCHIVESHUB_PROTOCOL_FILENAME = "observatorio_protocolo_archiveshub.csv"
ARCHIVESHUB_PROTOCOL_RULE_VERSION = "2026-05-archiveshub-protocol-v1"

FRANCEARCHIVES_PROTOCOL_FILENAME = "observatorio_protocolo_francearchives.csv"
FRANCEARCHIVES_PROTOCOL_RULE_VERSION = "2026-05-francearchives-protocol-v1"

EUROPEAN_FILM_GATEWAY_PROTOCOL_FILENAME = "observatorio_protocolo_european_film_gateway.csv"
EUROPEAN_FILM_GATEWAY_PROTOCOL_RULE_VERSION = "2026-05-european-film-gateway-protocol-v1"

EUROPEANA_PROTOCOL_FILENAME = "observatorio_protocolo_europeana.csv"
EUROPEANA_PROTOCOL_RULE_VERSION = "2026-05-europeana-protocol-v1"

ARCHIVESHUB_API_REFERENCE_URL = "https://blog.archiveshub.jisc.ac.uk/category/apis/"
ARCHIVESHUB_SRU_BASE_URL = "https://archiveshub.jisc.ac.uk/sru/"
ARCHIVESHUB_SRU_SAMPLE_URL = (
    "https://archiveshub.jisc.ac.uk/sru/"
    "?version=1.2&operation=searchRetrieve&query=film&maximumRecords=1"
)
ARCHIVESHUB_OAIPMH_BASE_URL = "https://archiveshub.jisc.ac.uk/oaipmh/"
ARCHIVESHUB_OAIPMH_IDENTIFY_URL = "https://archiveshub.jisc.ac.uk/oaipmh/?verb=Identify"

FRANCEARCHIVES_OPEN_DATA_URL = "https://francearchives.gouv.fr/fr/open_data"
FRANCEARCHIVES_DATASET_PAGE_URL = (
    "https://data.culture.gouv.fr/explore/dataset/"
    "inventaires-des-archives-publiques-francearchives/"
)
FRANCEARCHIVES_DATASET_API_URL = (
    "https://data.culture.gouv.fr/api/explore/v2.1/catalog/datasets/"
    "inventaires-des-archives-publiques-francearchives/records?limit=1"
)
FRANCEARCHIVES_DUMP_URL = (
    "https://data-dump.francearchives.gouv.fr/ape-ead-eac/francearchives_ape_ead.zip"
)

EUROPEAN_FILM_GATEWAY_HOME_URL = "https://www.europeanfilmgateway.eu/"
EUROPEAN_FILM_GATEWAY_SEARCH_FILM_URL = "https://www.europeanfilmgateway.eu/search-efg?searchString=film"
EUROPEAN_FILM_GATEWAY_SEARCH_VIDEO_URL = "https://www.europeanfilmgateway.eu/search-efg?searchString=video"

EUROPEANA_HOME_URL = "https://www.europeana.eu/"
EUROPEANA_MEDIA_SEARCH_URL = "https://www.europeana.eu/en/search?query=film&media=true"
EUROPEANA_API_REFERENCE_URL = "https://pro.europeana.eu/page/apis"

FRANCEARCHIVES_PROTOCOL_COLUMNS = [
    "code",
    "label",
    "probe",
    "probe_label",
    "method",
    "url",
    "http_status",
    "final_url",
    "content_type",
    "content_length",
    "access_status",
    "evidence_signal",
    "observed_value",
    "protocol_conclusion",
    "next_step",
    "methodological_note",
    "evaluated_at",
    "rule_version",
    "error",
]

ARCHIVESHUB_PROTOCOL_COLUMNS = FRANCEARCHIVES_PROTOCOL_COLUMNS
EUROPEAN_FILM_GATEWAY_PROTOCOL_COLUMNS = FRANCEARCHIVES_PROTOCOL_COLUMNS
EUROPEANA_PROTOCOL_COLUMNS = FRANCEARCHIVES_PROTOCOL_COLUMNS


@dataclass(frozen=True)
class FranceArchivesProbe:
    probe: str
    probe_label: str
    method: str
    url: str
    methodological_note: str


@dataclass(frozen=True)
class ArchivesHubProbe:
    probe: str
    probe_label: str
    method: str
    url: str
    methodological_note: str


@dataclass(frozen=True)
class EuropeanFilmGatewayProbe:
    probe: str
    probe_label: str
    method: str
    url: str
    methodological_note: str


@dataclass(frozen=True)
class EuropeanaProbe:
    probe: str
    probe_label: str
    method: str
    url: str
    methodological_note: str


ARCHIVESHUB_PROTOCOL_PROBES = [
    ArchivesHubProbe(
        probe="api_reference_page",
        probe_label="Referência pública sobre APIs",
        method="GET",
        url=ARCHIVESHUB_API_REFERENCE_URL,
        methodological_note=(
            "Verifica se a página pública do Archives Hub sobre APIs é acessível por requisição simples."
        ),
    ),
    ArchivesHubProbe(
        probe="sru_base",
        probe_label="Endpoint SRU base",
        method="GET",
        url=ARCHIVESHUB_SRU_BASE_URL,
        methodological_note=(
            "Testa a rota SRU documentada como interface de busca do Archives Hub."
        ),
    ),
    ArchivesHubProbe(
        probe="sru_search_sample",
        probe_label="Consulta SRU audiovisual mínima",
        method="GET",
        url=ARCHIVESHUB_SRU_SAMPLE_URL,
        methodological_note=(
            "Testa uma consulta SRU leve pelo termo film, sem tentar colher registros em massa."
        ),
    ),
    ArchivesHubProbe(
        probe="oaipmh_base",
        probe_label="Endpoint OAI-PMH base",
        method="GET",
        url=ARCHIVESHUB_OAIPMH_BASE_URL,
        methodological_note=(
            "Testa a rota OAI-PMH documentada como alternativa de colheita de metadados."
        ),
    ),
    ArchivesHubProbe(
        probe="oaipmh_identify",
        probe_label="Verbo OAI-PMH Identify",
        method="GET",
        url=ARCHIVESHUB_OAIPMH_IDENTIFY_URL,
        methodological_note=(
            "Testa o verbo Identify como sondagem mínima de conformidade OAI-PMH."
        ),
    ),
]


FRANCEARCHIVES_PROTOCOL_PROBES = [
    FranceArchivesProbe(
        probe="open_data_policy_page",
        probe_label="Página oficial de dados abertos",
        method="GET",
        url=FRANCEARCHIVES_OPEN_DATA_URL,
        methodological_note=(
            "Verifica se a política oficial de dados abertos é acessível por requisição simples."
        ),
    ),
    FranceArchivesProbe(
        probe="dataset_landing_page",
        probe_label="Ficha pública do dataset",
        method="GET",
        url=FRANCEARCHIVES_DATASET_PAGE_URL,
        methodological_note=(
            "Procura, sem baixar o pacote, sinais de dump público e metadados reutilizáveis."
        ),
    ),
    FranceArchivesProbe(
        probe="dataset_api_sample",
        probe_label="Amostra leve da API do dataset",
        method="GET",
        url=FRANCEARCHIVES_DATASET_API_URL,
        methodological_note=(
            "Testa se a API pública oferece registros consultáveis antes de acionar download pesado."
        ),
    ),
    FranceArchivesProbe(
        probe="ape_ead_zip_head",
        probe_label="Cabeçalho do ZIP APE-EAD",
        method="HEAD",
        url=FRANCEARCHIVES_DUMP_URL,
        methodological_note=(
            "Confirma se o pacote XML APE-EAD parece baixável sem executar a ingestão."
        ),
    ),
]


EUROPEAN_FILM_GATEWAY_PROTOCOL_PROBES = [
    EuropeanFilmGatewayProbe(
        probe="home_page",
        probe_label="Página inicial do European Film Gateway",
        method="GET",
        url=EUROPEAN_FILM_GATEWAY_HOME_URL,
        methodological_note=(
            "Verifica se o agregador audiovisual europeu responde por requisição simples."
        ),
    ),
    EuropeanFilmGatewayProbe(
        probe="search_film_sample",
        probe_label="Busca pública pelo termo film",
        method="GET",
        url=EUROPEAN_FILM_GATEWAY_SEARCH_FILM_URL,
        methodological_note=(
            "Testa uma busca pública leve para verificar presença de resultados e categorias audiovisuais."
        ),
    ),
    EuropeanFilmGatewayProbe(
        probe="search_video_sample",
        probe_label="Busca pública pelo termo video",
        method="GET",
        url=EUROPEAN_FILM_GATEWAY_SEARCH_VIDEO_URL,
        methodological_note=(
            "Testa termo complementar para distinguir ausência de resultado de fragilidade de indexação."
        ),
    ),
]


EUROPEANA_PROTOCOL_PROBES = [
    EuropeanaProbe(
        probe="home_page",
        probe_label="Página inicial da Europeana",
        method="GET",
        url=EUROPEANA_HOME_URL,
        methodological_note=(
            "Verifica se o agregador cultural europeu responde por requisição simples."
        ),
    ),
    EuropeanaProbe(
        probe="media_search_sample",
        probe_label="Busca pública com filtro de mídia",
        method="GET",
        url=EUROPEANA_MEDIA_SEARCH_URL,
        methodological_note=(
            "Testa a superfície pública com filtro de mídia, sem confundir acervo cultural geral com audiovisual."
        ),
    ),
    EuropeanaProbe(
        probe="api_reference_page",
        probe_label="Documentação oficial de APIs",
        method="GET",
        url=EUROPEANA_API_REFERENCE_URL,
        methodological_note=(
            "Verifica se há rota técnica documentada para futura coleta controlada por API."
        ),
    ),
]


def utcnow_iso():
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_space(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def detect_js_redirect(text):
    normalized = str(text or "").lower()
    return "window.location.href" in normalized and "/redirect_" in normalized


def detect_dump_url(text):
    match = re.search(
        r"https://data-dump\.francearchives\.gouv\.fr/[^\"'\s<>]+?\.zip",
        str(text or ""),
    )
    return match.group(0) if match else ""


def parse_api_observation(text):
    try:
        payload = json.loads(text or "{}")
    except json.JSONDecodeError:
        return "json_invalido"

    total_count = payload.get("total_count", payload.get("nhits", ""))
    results = payload.get("results", payload.get("records", []))
    result_count = len(results) if isinstance(results, list) else 0
    return f"total_count={total_count}; sample_records={result_count}"


def parse_efg_observation(text):
    normalized_text = _normalize_space(text)
    video_match = re.search(r"Videos?\s*\(([\d,\.]+)\s+Results?\)", normalized_text, re.IGNORECASE)
    if video_match:
        return f"video_results={video_match.group(1)}"
    if "your single access point" in normalized_text.lower() and "film archives across europe" in normalized_text.lower():
        return "portal_declares_european_film_archive_aggregation"
    return "sem_contagem_publica_detectada"


def parse_europeana_observation(text):
    normalized_text = _normalize_space(text)
    result_match = re.search(r"([\d,\.]+)\s+results?", normalized_text, re.IGNORECASE)
    if result_match:
        return f"public_search_results={result_match.group(1)}"
    lowered = normalized_text.lower()
    if "api" in lowered and "europeana" in lowered:
        return "api_documentation_detected"
    if "media" in lowered or "film" in lowered:
        return "media_surface_detected"
    return "sem_sinal_especifico_detectado"


def fetch_protocol_probe(url, method="GET", sample_bytes=524288):
    method = str(method or "GET").upper()
    tls_verification_failed = False
    error = ""
    response = None
    try:
        if method == "HEAD":
            response = requests.head(
                url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
            )
        else:
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
            request_fn = requests.head if method == "HEAD" else requests.get
            response = request_fn(
                url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
                verify=False,
                stream=(method != "HEAD"),
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
            "content_length": "",
            "text": "",
            "tls_verification_failed": tls_verification_failed,
            "error": error,
        }

    text = ""
    try:
        content_type = response.headers.get("content-type", "")
        if method != "HEAD" and (
            "text" in content_type
            or "html" in content_type
            or "json" in content_type
            or "xml" in content_type
        ):
            sample = response.raw.read(sample_bytes, decode_content=True)
            text = sample.decode(response.encoding or "utf-8", errors="replace")
    finally:
        response.close()

    return {
        "http_status": int(response.status_code),
        "final_url": response.url,
        "content_type": response.headers.get("content-type", ""),
        "content_length": response.headers.get("content-length", ""),
        "text": text,
        "tls_verification_failed": tls_verification_failed,
        "error": error,
    }


def _build_protocol_conclusion(probe, access_status, content_type, text, observed_value):
    normalized_content_type = str(content_type or "").lower()
    if probe.probe == "dataset_landing_page" and observed_value:
        return "dump_publico_documentado_na_ficha_do_dataset", "prototipar_indexacao_xml_ape_ead_em_amostra_controlada"
    if probe.probe == "dataset_api_sample" and access_status == "acessivel":
        if "total_count=0" in observed_value:
            return "api_acessivel_sem_registros_na_amostra", "usar_api_apenas_como_rota_auxiliar_e_priorizar_dump_xml"
        return "api_acessivel_com_registros", "testar_busca_vocabular_audiovisual_na_api"
    if probe.probe == "ape_ead_zip_head":
        if "zip" in normalized_content_type:
            return "dump_zip_parece_baixavel", "planejar_download_controlado_fora_do_ciclo_mensal"
        if "html" in normalized_content_type:
            return "cabecalho_nao_confirma_zip_baixavel", "validar_download_em_sessao_controlada_antes_da_ingestao"
        if detect_js_redirect(text) or access_status != "acessivel":
            return "download_exige_validacao_por_browser_ou_sessao", "testar_download_manual_controlado_antes_da_ingestao"
    if detect_js_redirect(text) or access_status == "bloqueado_por_js_ou_cookies":
        return "pagina_responde_com_redirecionamento_ou_desafio", "manter_como_evidencia_de_protocolo_pendente"
    if access_status == "acessivel":
        return "rota_acessivel_para_documentacao", "manter_rota_como_referencia_metodologica"
    return "rota_sem_confirmacao_estavel", "retestar_em_rodada_posterior"


def _build_archiveshub_protocol_conclusion(probe, access_status, content_type, text, observed_value):
    normalized_text = str(text or "").lower()
    if access_status == "acessivel":
        if probe.probe == "api_reference_page":
            if "sru" in normalized_text and "oai-pmh" in normalized_text:
                return "documentacao_publica_confirma_sru_e_oaipmh", "manter_sru_e_oaipmh_como_rotas_candidatas"
            return "pagina_publica_acessivel_sem_sinal_api_suficiente", "revisar_referencia_documental"
        if probe.probe.startswith("sru"):
            if "searchretrieveresponse" in normalized_text or "numberofrecords" in normalized_text:
                return "sru_responde_com_estrutura_de_busca", "prototipar_consulta_vocabular_audiovisual_controlada"
            return "sru_acessivel_sem_resposta_sru_confirmada", "revisar_parametros_sru_antes_de_ingestao"
        if probe.probe.startswith("oaipmh"):
            if "oai-pmh" in normalized_text or "identif" in normalized_text:
                return "oaipmh_responde_com_estrutura_de_colheita", "prototipar_identificacao_de_formatos_e_sets"
            return "oaipmh_acessivel_sem_resposta_oaipmh_confirmada", "revisar_parametros_oaipmh_antes_de_ingestao"
        return "rota_acessivel_para_documentacao", "manter_rota_como_referencia_metodologica"

    if access_status in {"bloqueado_por_js_ou_cookies", "restrito_ou_bloqueado"}:
        if probe.probe == "api_reference_page":
            return "referencia_publica_nao_acessivel_por_requisicao_simples", "registrar_dependencia_de_navegacao_ou_validar_por_browser"
        if probe.probe.startswith("sru"):
            return "sru_documentado_mas_bloqueado_na_sondagem_simples", "testar_rota_sru_com_sessao_controlada_ou_contato_tecnico"
        if probe.probe.startswith("oaipmh"):
            return "oaipmh_documentado_mas_bloqueado_na_sondagem_simples", "testar_rota_oaipmh_com_sessao_controlada_ou_contato_tecnico"
        return "rota_documentada_bloqueada_na_sondagem_simples", "manter_como_protocolo_pendente"

    if access_status == "falha_tecnica":
        return "rota_documentada_com_falha_tecnica_na_rodada", "retestar_e_separar_timeout_de_bloqueio"

    return "rota_sem_confirmacao_estavel", "retestar_em_rodada_posterior"


def _build_european_film_gateway_protocol_conclusion(probe, access_status, content_type, text, observed_value):
    normalized_text = str(text or "").lower()
    if access_status == "acessivel":
        if probe.probe == "home_page":
            if "film archives across europe" in normalized_text or "european film gateway" in normalized_text:
                return "portal_audiovisual_europeu_confirmado", "manter_como_agregador_audiovisual_prioritario"
            return "pagina_inicial_acessivel_sem_autodeclaracao_suficiente", "revisar_evidencia_institucional"
        if probe.probe.startswith("search_"):
            if "video_results=" in observed_value:
                return "busca_publica_responde_com_categoria_de_video", "prototipar_extracao_controlada_de_resultados"
            return "busca_publica_acessivel_sem_contagem_detectada", "validar_parseamento_por_browser_ou_html_alternativo"
        return "rota_acessivel_para_documentacao", "manter_rota_como_referencia_metodologica"

    if access_status in {"bloqueado_por_js_ou_cookies", "restrito_ou_bloqueado"}:
        return "rota_publica_bloqueada_na_sondagem_simples", "validar_por_browser_antes_de_decidir_ingestao"
    if access_status == "falha_tecnica":
        return "rota_publica_com_falha_tecnica_na_rodada", "retestar_e_separar_timeout_de_bloqueio"
    return "rota_sem_confirmacao_estavel", "retestar_em_rodada_posterior"


def _build_europeana_protocol_conclusion(probe, access_status, content_type, text, observed_value):
    normalized_text = str(text or "").lower()
    if access_status == "acessivel":
        if probe.probe == "api_reference_page":
            if "api" in normalized_text and "europeana" in normalized_text:
                return "documentacao_publica_confirma_apis", "prototipar_consulta_controlada_por_midia_e_tipo_de_objeto"
            return "pagina_api_acessivel_sem_sinal_suficiente", "revisar_referencia_documental"
        if probe.probe == "media_search_sample":
            if "public_search_results=" in observed_value or "media_surface_detected" in observed_value:
                return "busca_publica_com_filtro_de_midia_confirmada", "separar_corpus_cultural_amplo_de_recorte_audiovisual"
            return "busca_publica_acessivel_sem_sinal_de_midia_detectado", "validar_parseamento_por_browser_ou_api"
        if probe.probe == "home_page":
            return "portal_europeu_amplo_confirmado", "manter_como_agregador_supranacional_a_protocolar"
        return "rota_acessivel_para_documentacao", "manter_rota_como_referencia_metodologica"

    if access_status in {"bloqueado_por_js_ou_cookies", "restrito_ou_bloqueado"}:
        return "rota_publica_bloqueada_na_sondagem_simples", "validar_por_browser_ou_api_documentada"
    if access_status == "falha_tecnica":
        return "rota_publica_com_falha_tecnica_na_rodada", "retestar_e_separar_timeout_de_bloqueio"
    return "rota_sem_confirmacao_estavel", "retestar_em_rodada_posterior"


def _build_archiveshub_protocol_row(probe, evaluated_at, fetcher=fetch_protocol_probe):
    fetched = fetcher(probe.url, probe.method)
    text = fetched.get("text", "")
    access_status = classify_probe_access_status(
        fetched.get("http_status"),
        detect_js_cookie_requirement(text) or detect_js_redirect(text),
        fetched.get("error", ""),
    )

    if probe.probe == "api_reference_page":
        evidence_signal = "api_reference"
        observed_value = "sru_oaipmh_mencionados" if "sru" in text.lower() and "oai-pmh" in text.lower() else access_status
    elif probe.probe.startswith("sru"):
        evidence_signal = "sru_response"
        observed_value = _normalize_space(
            f"type={fetched.get('content_type', '')}; status={access_status}"
        )
    elif probe.probe.startswith("oaipmh"):
        evidence_signal = "oaipmh_response"
        observed_value = _normalize_space(
            f"type={fetched.get('content_type', '')}; status={access_status}"
        )
    else:
        evidence_signal = "page_access"
        observed_value = access_status

    protocol_conclusion, next_step = _build_archiveshub_protocol_conclusion(
        probe,
        access_status,
        fetched.get("content_type", ""),
        text,
        observed_value,
    )

    return {
        "code": "archives-hub",
        "label": "Archives Hub",
        "probe": probe.probe,
        "probe_label": probe.probe_label,
        "method": probe.method,
        "url": probe.url,
        "http_status": fetched.get("http_status", ""),
        "final_url": fetched.get("final_url", probe.url),
        "content_type": fetched.get("content_type", ""),
        "content_length": fetched.get("content_length", ""),
        "access_status": access_status,
        "evidence_signal": evidence_signal,
        "observed_value": observed_value,
        "protocol_conclusion": protocol_conclusion,
        "next_step": next_step,
        "methodological_note": probe.methodological_note,
        "evaluated_at": evaluated_at,
        "rule_version": ARCHIVESHUB_PROTOCOL_RULE_VERSION,
        "error": fetched.get("error", ""),
    }


def _build_francearchives_protocol_row(probe, evaluated_at, fetcher=fetch_protocol_probe):
    fetched = fetcher(probe.url, probe.method)
    text = fetched.get("text", "")
    access_status = classify_probe_access_status(
        fetched.get("http_status"),
        detect_js_cookie_requirement(text) or detect_js_redirect(text),
        fetched.get("error", ""),
    )

    if probe.probe == "dataset_landing_page":
        evidence_signal = "dump_url_detectado"
        observed_value = detect_dump_url(text)
    elif probe.probe == "dataset_api_sample":
        evidence_signal = "api_payload"
        observed_value = parse_api_observation(text)
    elif probe.probe == "ape_ead_zip_head":
        evidence_signal = "zip_header"
        observed_value = _normalize_space(
            f"type={fetched.get('content_type', '')}; length={fetched.get('content_length', '')}"
        )
    else:
        evidence_signal = "page_access"
        observed_value = "js_redirect_detectado" if detect_js_redirect(text) else access_status

    protocol_conclusion, next_step = _build_protocol_conclusion(
        probe,
        access_status,
        fetched.get("content_type", ""),
        text,
        observed_value,
    )

    return {
        "code": "francearchives",
        "label": "FranceArchives",
        "probe": probe.probe,
        "probe_label": probe.probe_label,
        "method": probe.method,
        "url": probe.url,
        "http_status": fetched.get("http_status", ""),
        "final_url": fetched.get("final_url", probe.url),
        "content_type": fetched.get("content_type", ""),
        "content_length": fetched.get("content_length", ""),
        "access_status": access_status,
        "evidence_signal": evidence_signal,
        "observed_value": observed_value,
        "protocol_conclusion": protocol_conclusion,
        "next_step": next_step,
        "methodological_note": probe.methodological_note,
        "evaluated_at": evaluated_at,
        "rule_version": FRANCEARCHIVES_PROTOCOL_RULE_VERSION,
        "error": fetched.get("error", ""),
    }


def _build_european_film_gateway_protocol_row(probe, evaluated_at, fetcher=fetch_protocol_probe):
    fetched = fetcher(probe.url, probe.method)
    text = fetched.get("text", "")
    access_status = classify_probe_access_status(
        fetched.get("http_status"),
        detect_js_cookie_requirement(text) or detect_js_redirect(text),
        fetched.get("error", ""),
    )

    evidence_signal = "efg_public_search" if probe.probe.startswith("search_") else "page_access"
    observed_value = parse_efg_observation(text) if access_status == "acessivel" else access_status
    protocol_conclusion, next_step = _build_european_film_gateway_protocol_conclusion(
        probe,
        access_status,
        fetched.get("content_type", ""),
        text,
        observed_value,
    )

    return {
        "code": "european-film-gateway",
        "label": "European Film Gateway",
        "probe": probe.probe,
        "probe_label": probe.probe_label,
        "method": probe.method,
        "url": probe.url,
        "http_status": fetched.get("http_status", ""),
        "final_url": fetched.get("final_url", probe.url),
        "content_type": fetched.get("content_type", ""),
        "content_length": fetched.get("content_length", ""),
        "access_status": access_status,
        "evidence_signal": evidence_signal,
        "observed_value": observed_value,
        "protocol_conclusion": protocol_conclusion,
        "next_step": next_step,
        "methodological_note": probe.methodological_note,
        "evaluated_at": evaluated_at,
        "rule_version": EUROPEAN_FILM_GATEWAY_PROTOCOL_RULE_VERSION,
        "error": fetched.get("error", ""),
    }


def _build_europeana_protocol_row(probe, evaluated_at, fetcher=fetch_protocol_probe):
    fetched = fetcher(probe.url, probe.method)
    text = fetched.get("text", "")
    access_status = classify_probe_access_status(
        fetched.get("http_status"),
        detect_js_cookie_requirement(text) or detect_js_redirect(text),
        fetched.get("error", ""),
    )

    if probe.probe == "api_reference_page":
        evidence_signal = "api_reference"
    elif probe.probe == "media_search_sample":
        evidence_signal = "media_search"
    else:
        evidence_signal = "page_access"
    observed_value = parse_europeana_observation(text) if access_status == "acessivel" else access_status
    protocol_conclusion, next_step = _build_europeana_protocol_conclusion(
        probe,
        access_status,
        fetched.get("content_type", ""),
        text,
        observed_value,
    )

    return {
        "code": "europeana",
        "label": "Europeana",
        "probe": probe.probe,
        "probe_label": probe.probe_label,
        "method": probe.method,
        "url": probe.url,
        "http_status": fetched.get("http_status", ""),
        "final_url": fetched.get("final_url", probe.url),
        "content_type": fetched.get("content_type", ""),
        "content_length": fetched.get("content_length", ""),
        "access_status": access_status,
        "evidence_signal": evidence_signal,
        "observed_value": observed_value,
        "protocol_conclusion": protocol_conclusion,
        "next_step": next_step,
        "methodological_note": probe.methodological_note,
        "evaluated_at": evaluated_at,
        "rule_version": EUROPEANA_PROTOCOL_RULE_VERSION,
        "error": fetched.get("error", ""),
    }


def build_archiveshub_protocol_probe(fetcher=fetch_protocol_probe, evaluated_at=None):
    evaluated_at = evaluated_at or utcnow_iso()
    rows = [
        _build_archiveshub_protocol_row(probe, evaluated_at, fetcher=fetcher)
        for probe in ARCHIVESHUB_PROTOCOL_PROBES
    ]
    return pd.DataFrame(rows, columns=ARCHIVESHUB_PROTOCOL_COLUMNS)


def write_archiveshub_protocol_probe(output_dir: Path = OUTPUT_DIR, fetcher=fetch_protocol_probe):
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol_df = build_archiveshub_protocol_probe(fetcher=fetcher)
    protocol_df.to_csv(
        output_dir / ARCHIVESHUB_PROTOCOL_FILENAME,
        index=False,
        encoding="utf-8-sig",
    )
    return protocol_df


def build_francearchives_protocol_probe(fetcher=fetch_protocol_probe, evaluated_at=None):
    evaluated_at = evaluated_at or utcnow_iso()
    rows = [
        _build_francearchives_protocol_row(probe, evaluated_at, fetcher=fetcher)
        for probe in FRANCEARCHIVES_PROTOCOL_PROBES
    ]
    return pd.DataFrame(rows, columns=FRANCEARCHIVES_PROTOCOL_COLUMNS)


def write_francearchives_protocol_probe(output_dir: Path = OUTPUT_DIR, fetcher=fetch_protocol_probe):
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol_df = build_francearchives_protocol_probe(fetcher=fetcher)
    protocol_df.to_csv(
        output_dir / FRANCEARCHIVES_PROTOCOL_FILENAME,
        index=False,
        encoding="utf-8-sig",
    )
    return protocol_df


def build_european_film_gateway_protocol_probe(fetcher=fetch_protocol_probe, evaluated_at=None):
    evaluated_at = evaluated_at or utcnow_iso()
    rows = [
        _build_european_film_gateway_protocol_row(probe, evaluated_at, fetcher=fetcher)
        for probe in EUROPEAN_FILM_GATEWAY_PROTOCOL_PROBES
    ]
    return pd.DataFrame(rows, columns=EUROPEAN_FILM_GATEWAY_PROTOCOL_COLUMNS)


def write_european_film_gateway_protocol_probe(output_dir: Path = OUTPUT_DIR, fetcher=fetch_protocol_probe):
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol_df = build_european_film_gateway_protocol_probe(fetcher=fetcher)
    protocol_df.to_csv(
        output_dir / EUROPEAN_FILM_GATEWAY_PROTOCOL_FILENAME,
        index=False,
        encoding="utf-8-sig",
    )
    return protocol_df


def build_europeana_protocol_probe(fetcher=fetch_protocol_probe, evaluated_at=None):
    evaluated_at = evaluated_at or utcnow_iso()
    rows = [
        _build_europeana_protocol_row(probe, evaluated_at, fetcher=fetcher)
        for probe in EUROPEANA_PROTOCOL_PROBES
    ]
    return pd.DataFrame(rows, columns=EUROPEANA_PROTOCOL_COLUMNS)


def write_europeana_protocol_probe(output_dir: Path = OUTPUT_DIR, fetcher=fetch_protocol_probe):
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol_df = build_europeana_protocol_probe(fetcher=fetcher)
    protocol_df.to_csv(
        output_dir / EUROPEANA_PROTOCOL_FILENAME,
        index=False,
        encoding="utf-8-sig",
    )
    return protocol_df


__all__ = [
    "ARCHIVESHUB_PROTOCOL_COLUMNS",
    "ARCHIVESHUB_PROTOCOL_FILENAME",
    "ARCHIVESHUB_PROTOCOL_PROBES",
    "ARCHIVESHUB_PROTOCOL_RULE_VERSION",
    "EUROPEAN_FILM_GATEWAY_PROTOCOL_COLUMNS",
    "EUROPEAN_FILM_GATEWAY_PROTOCOL_FILENAME",
    "EUROPEAN_FILM_GATEWAY_PROTOCOL_PROBES",
    "EUROPEAN_FILM_GATEWAY_PROTOCOL_RULE_VERSION",
    "EUROPEANA_PROTOCOL_COLUMNS",
    "EUROPEANA_PROTOCOL_FILENAME",
    "EUROPEANA_PROTOCOL_PROBES",
    "EUROPEANA_PROTOCOL_RULE_VERSION",
    "FRANCEARCHIVES_PROTOCOL_COLUMNS",
    "FRANCEARCHIVES_PROTOCOL_FILENAME",
    "FRANCEARCHIVES_PROTOCOL_PROBES",
    "FRANCEARCHIVES_PROTOCOL_RULE_VERSION",
    "build_archiveshub_protocol_probe",
    "build_european_film_gateway_protocol_probe",
    "build_europeana_protocol_probe",
    "build_francearchives_protocol_probe",
    "detect_dump_url",
    "detect_js_redirect",
    "parse_api_observation",
    "parse_efg_observation",
    "parse_europeana_observation",
    "write_archiveshub_protocol_probe",
    "write_european_film_gateway_protocol_probe",
    "write_europeana_protocol_probe",
    "write_francearchives_protocol_probe",
]
