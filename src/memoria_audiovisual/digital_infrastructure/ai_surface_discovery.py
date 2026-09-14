"""Exploração pública e controlada de superfícies institucionais para o T2A.

O protocolo amplia a unidade de observação para além da homepage sem transformar
o observatório em um crawler irrestrito. A coleta permanece experimental, respeita
robots.txt, limita domínio, profundidade, volume e tamanho de resposta e nunca usa
autenticação ou contorna barreiras de acesso.
"""

from __future__ import annotations

import hashlib
import heapq
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

SURFACE_PROTOCOL_VERSION = "1.0.0"
DEFAULT_USER_AGENT = "MemoriaAudiovisualRede-T2A/1.0 (+public-research-crawler)"

# Vocabulário de descoberta, não evidência suficiente por si só.
DISCOVERY_TERMS = (
    "artificial intelligence",
    "intelligence artificielle",
    "inteligência artificial",
    "inteligencia artificial",
    "machine learning",
    "deep learning",
    "traitements-ia",
    "ia",
    "ai",
    "archive",
    "archives",
    "arquivo",
    "acervo",
    "collection",
    "collections",
    "fonds",
    "audiovisual",
    "moving image",
    "film",
    "filme",
    "película",
    "video",
    "vídeo",
    "metadata",
    "metadados",
    "métadonnées",
    "metadatos",
    "catalog",
    "catalogue",
    "catálogo",
    "recherche",
    "research",
    "pesquisa",
    "investigación",
    "transcription",
    "transcrição",
    "transcripción",
    "recognition",
    "reconnaissance",
    "reconhecimento",
    "reconocimiento",
    "restoration",
    "restauration",
    "restauração",
    "restauración",
    "preservation",
    "préservation",
    "preservação",
    "preservación",
    "api",
    "technology",
    "technologie",
    "tecnologia",
    "innovation",
    "inovação",
    "innovación",
)

_ALLOWED_CONTENT_TYPES = (
    "text/html",
    "application/xhtml+xml",
    "application/json",
    "application/ld+json",
    "text/plain",
)

_SKIP_EXTENSIONS = {
    ".7z",
    ".avi",
    ".doc",
    ".docx",
    ".gif",
    ".gz",
    ".jpeg",
    ".jpg",
    ".m4a",
    ".mkv",
    ".mov",
    ".mp3",
    ".mp4",
    ".mpeg",
    ".mpg",
    ".pdf",
    ".png",
    ".rar",
    ".tar",
    ".tif",
    ".tiff",
    ".wav",
    ".webm",
    ".webp",
    ".xls",
    ".xlsx",
    ".zip",
}


@dataclass(frozen=True, slots=True)
class SurfaceDiscoveryPolicy:
    max_depth: int = 2
    max_pages: int = 24
    timeout_seconds: float = 12.0
    max_response_bytes: int = 1_500_000
    max_text_chars: int = 120_000
    user_agent: str = DEFAULT_USER_AGENT
    respect_robots_txt: bool = True

    def __post_init__(self) -> None:
        if self.max_depth < 0:
            raise ValueError("max_depth não pode ser negativo")
        if self.max_pages < 1:
            raise ValueError("max_pages deve ser maior ou igual a 1")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds deve ser positivo")
        if self.max_response_bytes < 1 or self.max_text_chars < 1:
            raise ValueError("limites de tamanho devem ser positivos")


@dataclass(frozen=True, slots=True)
class SurfacePage:
    url: str
    parent_url: str | None
    depth: int
    status_code: int | None
    content_type: str | None
    content_sha256: str | None
    title: str | None
    text: str
    metadata_text: str
    structured_text: str
    media_urls: tuple[str, ...] = ()
    discovered_links: int = 0
    fetched_at: str = ""
    truncated: bool = False
    fetch_status: str = "fetched"

    def classifier_payload(self) -> dict[str, object]:
        return {
            "url": self.url,
            "depth": self.depth,
            "title": self.title,
            "text": self.text,
            "metadata_text": self.metadata_text,
            "structured_text": self.structured_text,
            "media_urls": list(self.media_urls),
            "content_sha256": self.content_sha256,
            "fetched_at": self.fetched_at,
        }


@dataclass(frozen=True, slots=True)
class SurfaceDiscoveryReport:
    root_url: str
    institutional_base_host: str
    pages: tuple[SurfacePage, ...]
    policy: SurfaceDiscoveryPolicy
    started_at: str
    finished_at: str
    protocol_version: str = SURFACE_PROTOCOL_VERSION
    errors: tuple[str, ...] = ()

    @property
    def fetched_pages(self) -> int:
        return sum(page.fetch_status == "fetched" for page in self.pages)

    def to_dict(self) -> dict[str, object]:
        return {
            "protocol_version": self.protocol_version,
            "root_url": self.root_url,
            "institutional_base_host": self.institutional_base_host,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "policy": asdict(self.policy),
            "pages_total": len(self.pages),
            "fetched_pages": self.fetched_pages,
            "errors": list(self.errors),
            "pages": [asdict(page) for page in self.pages],
        }


@dataclass(order=True)
class _QueueItem:
    priority: int
    sequence: int
    url: str = field(compare=False)
    parent_url: str | None = field(compare=False)
    depth: int = field(compare=False)


def _utcnow_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _institutional_base_host(url: str) -> str:
    host = (urlsplit(url).hostname or "").lower().strip(".")
    if host.startswith("www."):
        host = host[4:]
    return host


def _host_in_scope(host: str, base_host: str) -> bool:
    host = host.lower().strip(".")
    base_host = base_host.lower().strip(".")
    return bool(base_host) and (host == base_host or host.endswith("." + base_host))


def canonicalize_public_url(url: str) -> str | None:
    """Normaliza apenas URLs HTTP(S) públicas sem credenciais ou fragmentos."""
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return None
    if parts.scheme.lower() not in {"http", "https"}:
        return None
    if not parts.hostname or parts.username or parts.password:
        return None
    path_lower = parts.path.lower()
    if any(path_lower.endswith(ext) for ext in _SKIP_EXTENSIONS):
        return None
    query = urlencode(sorted(parse_qsl(parts.query, keep_blank_values=True)), doseq=True)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", query, ""))


def is_url_in_institutional_scope(url: str, root_url: str) -> bool:
    canonical = canonicalize_public_url(url)
    if canonical is None:
        return False
    host = urlsplit(canonical).hostname or ""
    return _host_in_scope(host, _institutional_base_host(root_url))


def _link_priority(url: str, anchor_text: str) -> int:
    haystack = f"{url} {anchor_text}".lower()
    score = 0
    for term in DISCOVERY_TERMS:
        if term in haystack:
            score += 10 if term in {"ai", "ia"} else 6
    # Menor valor = maior prioridade no heap.
    return -score


def _extract_html_payload(html: str, *, base_url: str, max_text_chars: int) -> tuple[
    str,
    str | None,
    str,
    str,
    tuple[str, ...],
    tuple[tuple[str, str], ...],
]:
    soup = BeautifulSoup(html, "html.parser")
    for node in soup(["script", "style", "noscript", "template"]):
        if node.name == "script" and str(node.get("type") or "").lower() == "application/ld+json":
            continue
        node.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else None
    visible_text = " ".join(soup.stripped_strings)[:max_text_chars]

    metadata_chunks: list[str] = []
    for meta in soup.find_all("meta"):
        name = str(meta.get("name") or meta.get("property") or "").strip()
        content = str(meta.get("content") or "").strip()
        if content:
            metadata_chunks.append(f"{name}: {content}" if name else content)
    metadata_text = "\n".join(metadata_chunks)[:max_text_chars]

    structured_chunks: list[str] = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        value = script.string or script.get_text(" ", strip=True)
        if value:
            structured_chunks.append(value)
    structured_text = "\n".join(structured_chunks)[:max_text_chars]

    media_urls: list[str] = []
    for tag in soup.find_all(["video", "audio", "source", "iframe"]):
        value = str(tag.get("src") or "").strip()
        if value:
            media_urls.append(urljoin(base_url, value))

    links: list[tuple[str, str]] = []
    for anchor in soup.find_all("a", href=True):
        href = str(anchor.get("href") or "").strip()
        if not href:
            continue
        links.append((urljoin(base_url, href), anchor.get_text(" ", strip=True)))

    return (
        visible_text,
        title,
        metadata_text,
        structured_text,
        tuple(dict.fromkeys(media_urls)),
        tuple(links),
    )


def _extract_non_html_payload(text: str, *, max_text_chars: int) -> tuple[str, str | None, str, str]:
    body = text[:max_text_chars]
    return body, None, "", ""


class _RobotsPolicy:
    def __init__(self, *, session: requests.Session, policy: SurfaceDiscoveryPolicy) -> None:
        self.session = session
        self.policy = policy
        self._cache: dict[str, RobotFileParser | None | bool] = {}

    def allows(self, url: str) -> bool:
        if not self.policy.respect_robots_txt:
            return True
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        cached = self._cache.get(origin)
        if cached is False:
            return False
        if isinstance(cached, RobotFileParser):
            return cached.can_fetch(self.policy.user_agent, url)
        if origin not in self._cache:
            robots_url = origin + "/robots.txt"
            try:
                response = self.session.get(
                    robots_url,
                    timeout=self.policy.timeout_seconds,
                    headers={"User-Agent": self.policy.user_agent},
                    allow_redirects=True,
                )
                if response.status_code in {401, 403}:
                    self._cache[origin] = False
                    return False
                if response.status_code == 404:
                    self._cache[origin] = None
                    return True
                if response.ok:
                    parser = RobotFileParser()
                    parser.set_url(robots_url)
                    parser.parse(response.text.splitlines())
                    self._cache[origin] = parser
                    return parser.can_fetch(self.policy.user_agent, url)
            except requests.RequestException:
                pass
            self._cache[origin] = None
        return True


def discover_public_surfaces(
    root_url: str,
    *,
    policy: SurfaceDiscoveryPolicy | None = None,
    session: requests.Session | None = None,
) -> SurfaceDiscoveryReport:
    """Explora páginas públicas internas e subdomínios da mesma instituição."""
    policy = policy or SurfaceDiscoveryPolicy()
    canonical_root = canonicalize_public_url(root_url)
    if canonical_root is None:
        raise ValueError(f"root_url inválida ou não pública: {root_url}")

    base_host = _institutional_base_host(canonical_root)
    started_at = _utcnow_iso()
    own_session = session is None
    http = session or requests.Session()
    robots = _RobotsPolicy(session=http, policy=policy)

    queue: list[_QueueItem] = []
    sequence = 0
    heapq.heappush(queue, _QueueItem(priority=-10_000, sequence=sequence, url=canonical_root, parent_url=None, depth=0))
    seen: set[str] = set()
    pages: list[SurfacePage] = []
    errors: list[str] = []

    try:
        while queue and len(pages) < policy.max_pages:
            item = heapq.heappop(queue)
            if item.url in seen or item.depth > policy.max_depth:
                continue
            seen.add(item.url)

            if not is_url_in_institutional_scope(item.url, canonical_root):
                continue
            if not robots.allows(item.url):
                pages.append(
                    SurfacePage(
                        url=item.url,
                        parent_url=item.parent_url,
                        depth=item.depth,
                        status_code=None,
                        content_type=None,
                        content_sha256=None,
                        title=None,
                        text="",
                        metadata_text="",
                        structured_text="",
                        fetched_at=_utcnow_iso(),
                        fetch_status="blocked_by_robots",
                    )
                )
                continue

            try:
                response = http.get(
                    item.url,
                    timeout=policy.timeout_seconds,
                    headers={"User-Agent": policy.user_agent, "Accept": "text/html,application/xhtml+xml,application/json,text/plain;q=0.8,*/*;q=0.1"},
                    allow_redirects=True,
                )
            except requests.RequestException as exc:
                errors.append(f"{item.url}: {type(exc).__name__}: {exc}")
                pages.append(
                    SurfacePage(
                        url=item.url,
                        parent_url=item.parent_url,
                        depth=item.depth,
                        status_code=None,
                        content_type=None,
                        content_sha256=None,
                        title=None,
                        text="",
                        metadata_text="",
                        structured_text="",
                        fetched_at=_utcnow_iso(),
                        fetch_status="request_error",
                    )
                )
                continue

            final_url = canonicalize_public_url(response.url) or item.url
            if not is_url_in_institutional_scope(final_url, canonical_root):
                pages.append(
                    SurfacePage(
                        url=item.url,
                        parent_url=item.parent_url,
                        depth=item.depth,
                        status_code=response.status_code,
                        content_type=response.headers.get("Content-Type"),
                        content_sha256=None,
                        title=None,
                        text="",
                        metadata_text="",
                        structured_text="",
                        fetched_at=_utcnow_iso(),
                        fetch_status="redirect_outside_scope",
                    )
                )
                continue

            raw = response.content[: policy.max_response_bytes]
            truncated = len(response.content) > policy.max_response_bytes
            content_hash = hashlib.sha256(raw).hexdigest()
            content_type = str(response.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
            allowed_type = not content_type or any(content_type.startswith(value) for value in _ALLOWED_CONTENT_TYPES)
            if not response.ok or not allowed_type:
                pages.append(
                    SurfacePage(
                        url=final_url,
                        parent_url=item.parent_url,
                        depth=item.depth,
                        status_code=response.status_code,
                        content_type=content_type or None,
                        content_sha256=content_hash,
                        title=None,
                        text="",
                        metadata_text="",
                        structured_text="",
                        fetched_at=_utcnow_iso(),
                        truncated=truncated,
                        fetch_status="http_error" if not response.ok else "unsupported_content_type",
                    )
                )
                continue

            encoding = response.encoding or "utf-8"
            decoded = raw.decode(encoding, errors="replace")
            links: tuple[tuple[str, str], ...] = ()
            if content_type in {"text/html", "application/xhtml+xml"} or "<html" in decoded[:500].lower():
                text, title, metadata_text, structured_text, media_urls, links = _extract_html_payload(
                    decoded,
                    base_url=final_url,
                    max_text_chars=policy.max_text_chars,
                )
            else:
                text, title, metadata_text, structured_text = _extract_non_html_payload(
                    decoded,
                    max_text_chars=policy.max_text_chars,
                )
                media_urls = ()

            pages.append(
                SurfacePage(
                    url=final_url,
                    parent_url=item.parent_url,
                    depth=item.depth,
                    status_code=response.status_code,
                    content_type=content_type or None,
                    content_sha256=content_hash,
                    title=title,
                    text=text,
                    metadata_text=metadata_text,
                    structured_text=structured_text,
                    media_urls=media_urls,
                    discovered_links=len(links),
                    fetched_at=_utcnow_iso(),
                    truncated=truncated,
                )
            )

            if item.depth >= policy.max_depth:
                continue
            ranked: list[tuple[int, str, str]] = []
            for candidate, anchor_text in links:
                canonical = canonicalize_public_url(candidate)
                if canonical is None or canonical in seen:
                    continue
                if not is_url_in_institutional_scope(canonical, canonical_root):
                    continue
                ranked.append((_link_priority(canonical, anchor_text), canonical, anchor_text))
            ranked.sort(key=lambda value: (value[0], value[1]))
            for priority, candidate, _anchor_text in ranked:
                sequence += 1
                heapq.heappush(
                    queue,
                    _QueueItem(
                        priority=priority,
                        sequence=sequence,
                        url=candidate,
                        parent_url=final_url,
                        depth=item.depth + 1,
                    ),
                )
    finally:
        if own_session:
            http.close()

    return SurfaceDiscoveryReport(
        root_url=canonical_root,
        institutional_base_host=base_host,
        pages=tuple(pages),
        policy=policy,
        started_at=started_at,
        finished_at=_utcnow_iso(),
        errors=tuple(errors),
    )


def materialize_surface_discovery(
    report: SurfaceDiscoveryReport,
    *,
    output_dir: str | Path,
    run_id: str,
    entity_id: str,
) -> tuple[Path, Path]:
    """Persiste auditoria completa e texto separado usado pelo classificador."""
    root = Path(output_dir) / "_ai_surface_discovery" / run_id / entity_id
    root.mkdir(parents=True, exist_ok=True)
    report_path = root / "surface_discovery_report.json"
    classifier_path = root / "surface_classifier_text.jsonl"

    report_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with classifier_path.open("w", encoding="utf-8") as handle:
        for page in report.pages:
            if page.fetch_status != "fetched":
                continue
            handle.write(json.dumps(page.classifier_payload(), ensure_ascii=False, sort_keys=True) + "\n")
    return report_path, classifier_path


def discover_and_materialize_public_surfaces(
    root_url: str,
    *,
    output_dir: str | Path,
    run_id: str,
    entity_id: str,
    policy: SurfaceDiscoveryPolicy | None = None,
    session: requests.Session | None = None,
) -> tuple[SurfaceDiscoveryReport, Path, Path]:
    report = discover_public_surfaces(root_url, policy=policy, session=session)
    report_path, classifier_path = materialize_surface_discovery(
        report,
        output_dir=output_dir,
        run_id=run_id,
        entity_id=entity_id,
    )
    return report, report_path, classifier_path


__all__ = [
    "DISCOVERY_TERMS",
    "SURFACE_PROTOCOL_VERSION",
    "SurfaceDiscoveryPolicy",
    "SurfaceDiscoveryReport",
    "SurfacePage",
    "canonicalize_public_url",
    "discover_and_materialize_public_surfaces",
    "discover_public_surfaces",
    "is_url_in_institutional_scope",
    "materialize_surface_discovery",
]
