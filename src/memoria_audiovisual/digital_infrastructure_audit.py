"""Auditoria heurística de infraestruturas digitais de arquivos audiovisuais.

O módulo observa somente superfícies públicas e registra evidências técnicas sem
contornar autenticação, robots.txt, paywalls ou outras restrições de acesso.
Os resultados são sinais reprodutíveis, não afirmações definitivas sobre a
arquitetura interna das instituições.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

DEFAULT_TIMEOUT = 20
USER_AGENT = (
    "MemoriaAudiovisualEmRede/1.0 "
    "(+https://github.com/brauliorrs/memoria-audiovisual-rede; research audit)"
)


@dataclass
class InfrastructureAudit:
    corpus_code: str
    institution: str
    source_url: str
    final_url: str
    checked_at_utc: str
    http_status: int | None
    reachable: bool
    cms: str
    api_open_detected: bool
    api_types: str
    api_evidence: str
    metadata_formats: str
    interoperability_protocols: str
    search_mechanisms: str
    access_restrictions: str
    ai_cataloguing_status: str
    ai_cataloguing_evidence: str
    evidence_urls: str
    error: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value.strip() for value in values if value and value.strip()))


def _join(values: Iterable[str]) -> str:
    return " | ".join(_unique(values))


def _text_snippet(text: str, pattern: re.Pattern[str], radius: int = 90) -> str:
    match = pattern.search(text)
    if not match:
        return ""
    start = max(0, match.start() - radius)
    end = min(len(text), match.end() + radius)
    return re.sub(r"\s+", " ", text[start:end]).strip()


def detect_cms(html: str, soup: BeautifulSoup, headers: dict[str, str]) -> str:
    generator = soup.find("meta", attrs={"name": re.compile("generator", re.I)})
    if generator and generator.get("content"):
        return str(generator["content"]).strip()

    haystack = " ".join([html[:300_000], json.dumps(headers, ensure_ascii=False)]).lower()
    signatures = {
        "WordPress": ("wp-content", "wp-includes", "wordpress"),
        "Drupal": ("drupal-settings-json", "/sites/default/files/", "x-generator: drupal"),
        "Joomla": ("/media/system/js/", "joomla"),
        "Omeka": ("omeka", "/items/browse", "omeka-s"),
        "AtoM": ("atom application", "qubit", "/index.php/"),
        "ArchivesSpace": ("archivesspace", "public interface | archivesspace"),
        "CollectiveAccess": ("collectiveaccess", "pawtucket"),
        "DSpace": ("dspace", "/server/api/core/", "repository software dspace"),
        "Islandora": ("islandora",),
        "Blacklight": ("blacklight", "blacklight-search"),
        "VuFind": ("vufind",),
        "CONTENTdm": ("contentdm", "digital/api/singleitem"),
        "Tainacan": ("tainacan", "/wp-json/tainacan/"),
    }
    for name, markers in signatures.items():
        if any(marker in haystack for marker in markers):
            return name
    return "Não identificado"


def detect_apis(html: str, soup: BeautifulSoup, base_url: str) -> tuple[list[str], list[str], list[str]]:
    types: list[str] = []
    evidence: list[str] = []
    urls: list[str] = []
    lower = html.lower()

    patterns = {
        "IIIF": ("iiif.io/api", "iiif manifest", '"@context":"http://iiif.io', '"type":"manifest"'),
        "OAI-PMH": ("oai-pmh", "verb=identify", "verb=listrecords"),
        "OpenAPI/Swagger": ("openapi.json", "swagger.json", "swagger-ui", '"openapi":"3.'),
        "GraphQL": ("/graphql", "graphql endpoint"),
        "REST/JSON": ("/api/", "wp-json", "application/vnd.api+json", "api endpoint"),
        "SPARQL": ("sparql",),
    }
    for api_type, markers in patterns.items():
        if any(marker in lower for marker in markers):
            types.append(api_type)
            evidence.append(next(marker for marker in markers if marker in lower))

    for tag in soup.find_all(["a", "link", "script"]):
        candidate = tag.get("href") or tag.get("src")
        if not candidate:
            continue
        absolute = urljoin(base_url, candidate)
        candidate_lower = absolute.lower()
        if any(token in candidate_lower for token in ("/api/", "openapi", "swagger", "graphql", "oai", "iiif", "manifest")):
            urls.append(absolute)

    return _unique(types), _unique(evidence), _unique(urls)[:20]


def detect_metadata(html: str, soup: BeautifulSoup) -> list[str]:
    formats: list[str] = []
    lower = html.lower()

    if soup.find("script", attrs={"type": re.compile("ld\+json", re.I)}):
        formats.append("JSON-LD / Schema.org")
    if soup.find("meta", attrs={"property": re.compile(r"^og:", re.I)}):
        formats.append("Open Graph")
    if soup.find(attrs={"typeof": True}) or "rdfa" in lower:
        formats.append("RDFa")
    if soup.find("meta", attrs={"name": re.compile(r"^(dc\.|dcterms\.)", re.I)}):
        formats.append("Dublin Core")
    marker_map = {
        "IIIF Presentation API": ("iiif.io/api/presentation", "iiif manifest"),
        "EAD": ("ead2002", "ead3", "encoded archival description"),
        "METS": ("mets:mets", "loc.gov/mets"),
        "MODS": ("mods:mods", "loc.gov/mods"),
        "MARC": ("marcxml", "marc 21"),
        "EDM": ("europeana data model", "edm:providedcho"),
        "PBCore": ("pbcore",),
        "EBUCore": ("ebucore",),
    }
    for label, markers in marker_map.items():
        if any(marker in lower for marker in markers):
            formats.append(label)
    return _unique(formats)


def detect_interoperability(html: str, soup: BeautifulSoup) -> list[str]:
    protocols: list[str] = []
    lower = html.lower()
    marker_map = {
        "IIIF": ("iiif.io", "iiif manifest"),
        "OAI-PMH": ("oai-pmh", "verb=listrecords"),
        "Schema.org": ("schema.org", "application/ld+json"),
        "Dublin Core": ("dc.title", "dcterms."),
        "OpenSearch": ("application/opensearchdescription+xml",),
        "RSS/Atom": ("application/rss+xml", "application/atom+xml"),
        "Sitemap XML": ("sitemap.xml",),
        "Linked Open Data": ("linked open data", "void:dataset", "skos:"),
    }
    for label, markers in marker_map.items():
        if any(marker in lower for marker in markers):
            protocols.append(label)

    for link in soup.find_all("link"):
        mime = str(link.get("type", "")).lower()
        if "opensearch" in mime:
            protocols.append("OpenSearch")
        if "rss" in mime or "atom" in mime:
            protocols.append("RSS/Atom")
    return _unique(protocols)


def detect_search(soup: BeautifulSoup, html: str) -> list[str]:
    mechanisms: list[str] = []
    for form in soup.find_all("form"):
        fields = form.find_all(["input", "select"])
        names = " ".join(str(field.get("name", "")) for field in fields).lower()
        action = str(form.get("action", "")).lower()
        if any(token in names or token in action for token in ("search", "query", "keyword", "q", "termo", "recherche")):
            mechanisms.append("Formulário de busca HTML")
            break

    lower = html.lower()
    if "elasticsearch" in lower:
        mechanisms.append("Elasticsearch")
    if "solr" in lower:
        mechanisms.append("Apache Solr")
    if "algolia" in lower:
        mechanisms.append("Algolia")
    if any(token in lower for token in ("faceted search", "search facets", "filtros de busca", "facettes")):
        mechanisms.append("Busca facetada")
    if "application/opensearchdescription+xml" in lower:
        mechanisms.append("OpenSearch")
    return _unique(mechanisms)


def detect_restrictions(soup: BeautifulSoup, text: str) -> list[str]:
    restrictions: list[str] = []
    lower = text.lower()
    robots = soup.find("meta", attrs={"name": re.compile("robots", re.I)})
    if robots and any(token in str(robots.get("content", "")).lower() for token in ("noindex", "nofollow")):
        restrictions.append("Restrição de indexação (robots meta)")

    markers = {
        "Autenticação/login": ("sign in", "log in", "login required", "iniciar sessão", "connexion requise"),
        "Acesso por assinatura/pagamento": ("paywall", "subscribe to access", "subscription required", "acesso pago"),
        "Restrição geográfica": ("not available in your country", "geo-block", "geoblock", "indisponível no seu país"),
        "Direitos autorais condicionam o acesso": ("rights reserved", "copyright restrictions", "consultation sur place", "uso restrito"),
        "Cadastro obrigatório": ("registration required", "create an account to access", "cadastro obrigatório"),
    }
    for label, phrases in markers.items():
        if any(phrase in lower for phrase in phrases):
            restrictions.append(label)
    return _unique(restrictions)


def detect_ai_cataloguing(text: str) -> tuple[str, str]:
    patterns = [
        re.compile(r"(?:artificial intelligence|intelig[eê]ncia artificial|intelligence artificielle).{0,120}(?:catalog|metadata|index|description|archive)", re.I),
        re.compile(r"(?:machine learning|aprendizado de m[aá]quina|apprentissage automatique).{0,120}(?:catalog|metadata|index|description|archive)", re.I),
        re.compile(r"(?:automatic|automated|autom[aá]tic[oa]).{0,80}(?:speech recognition|transcription|tagging|classification|indexing|cataloguing|cataloging)", re.I),
        re.compile(r"(?:computer vision|reconhecimento facial|face recognition|speech-to-text).{0,120}(?:archive|catalog|metadata|index)", re.I),
    ]
    normalized = re.sub(r"\s+", " ", text)
    for pattern in patterns:
        snippet = _text_snippet(normalized, pattern)
        if snippet:
            return "Evidência pública textual detectada", snippet
    return "Não identificado na superfície observada", ""


def audit_url(
    source_url: str,
    *,
    corpus_code: str = "",
    institution: str = "",
    timeout: int = DEFAULT_TIMEOUT,
    session: requests.Session | None = None,
) -> InfrastructureAudit:
    checked_at = datetime.now(timezone.utc).isoformat()
    client = session or requests.Session()
    client.headers.setdefault("User-Agent", USER_AGENT)
    try:
        response = client.get(source_url, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        visible_text = soup.get_text(" ", strip=True)

        api_types, api_evidence, evidence_urls = detect_apis(html, soup, response.url)
        ai_status, ai_evidence = detect_ai_cataloguing(visible_text)
        metadata = detect_metadata(html, soup)
        interoperability = detect_interoperability(html, soup)

        return InfrastructureAudit(
            corpus_code=corpus_code,
            institution=institution,
            source_url=source_url,
            final_url=response.url,
            checked_at_utc=checked_at,
            http_status=response.status_code,
            reachable=True,
            cms=detect_cms(html, soup, dict(response.headers)),
            api_open_detected=bool(api_types or evidence_urls),
            api_types=_join(api_types),
            api_evidence=_join(api_evidence),
            metadata_formats=_join(metadata),
            interoperability_protocols=_join(interoperability),
            search_mechanisms=_join(detect_search(soup, html)),
            access_restrictions=_join(detect_restrictions(soup, visible_text)),
            ai_cataloguing_status=ai_status,
            ai_cataloguing_evidence=ai_evidence,
            evidence_urls=_join(evidence_urls),
            error="",
        )
    except requests.RequestException as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        return InfrastructureAudit(
            corpus_code=corpus_code,
            institution=institution,
            source_url=source_url,
            final_url="",
            checked_at_utc=checked_at,
            http_status=status,
            reachable=False,
            cms="",
            api_open_detected=False,
            api_types="",
            api_evidence="",
            metadata_formats="",
            interoperability_protocols="",
            search_mechanisms="",
            access_restrictions="",
            ai_cataloguing_status="Não avaliado",
            ai_cataloguing_evidence="",
            evidence_urls="",
            error=str(exc),
        )
