"""Exploração pública e controlada de superfícies institucionais para o T2A.

O protocolo amplia a unidade de observação para além da homepage sem transformar
o observatório em um crawler irrestrito. A coleta permanece experimental, respeita
robots.txt, limita domínio, profundidade, volume e tamanho de resposta e nunca usa
autenticação ou contorna barreiras de acesso.
"""

from __future__ import annotations

import base64
import hashlib
import heapq
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from .raw_artifacts import RawArtifactStore

SURFACE_PROTOCOL_VERSION = "1.0.0"
SURFACE_SNAPSHOT_SCHEMA_VERSION = "1.0.0"
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
class SurfaceCapture:
    """Evidence captured before discovery reduces a response to classifier fields."""

    requested_url: str
    final_url: str | None
    observed_at: str
    fetch_status: str
    status_code: int | None = None
    content_type: str | None = None
    response_body: bytes | None = field(default=None, repr=False, compare=False)
    response_received_bytes: int | None = None
    response_truncated: bool = False
    error_type: str | None = None
    error_message: str | None = None
    robots_evidence: dict[str, object] | None = field(
        default=None,
        repr=False,
        compare=False,
    )

    def snapshot_payload(
        self,
        *,
        report: "SurfaceDiscoveryReport",
        page: SurfacePage,
        run_id: str,
        entity_id: str,
    ) -> dict[str, object]:
        response: dict[str, object] | None = None
        if self.response_body is not None:
            response = {
                "status_code": self.status_code,
                "content_type": self.content_type,
                "received_byte_size": self.response_received_bytes,
                "captured_byte_size": len(self.response_body),
                "captured_sha256": hashlib.sha256(self.response_body).hexdigest(),
                "truncated": self.response_truncated,
                "body_base64": base64.b64encode(self.response_body).decode("ascii"),
            }

        error: dict[str, str | None] | None = None
        if self.error_type is not None or self.error_message is not None:
            error = {
                "type": self.error_type,
                "message": self.error_message,
            }

        return {
            "snapshot_schema_version": SURFACE_SNAPSHOT_SCHEMA_VERSION,
            "collector_protocol_version": report.protocol_version,
            "run_id": run_id,
            "entity_id": entity_id,
            "root_url": report.root_url,
            "requested_url": self.requested_url,
            "final_url": self.final_url,
            "parent_url": page.parent_url,
            "depth": page.depth,
            "observed_at": self.observed_at,
            "fetch_status": self.fetch_status,
            "collector_policy": asdict(report.policy),
            "response": response,
            "robots": self.robots_evidence,
            "error": error,
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
    captures: tuple[SurfaceCapture, ...] = field(
        default=(),
        repr=False,
        compare=False,
    )

    @property
    def fetched_pages(self) -> int:
        return sum(page.fetch_status == "fetched" for page in self.pages)

    def to_dict(self) -> dict[str, object]:
        # Captures deliberately remain out of this legacy view. The materializer
        # preserves them as content-addressed snapshot artifacts first.
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


def _extract_html_payload(
    html: str,
    *,
    base_url: str,
    max_text_chars: int,
) -> tuple[
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


def _extract_non_html_payload(
    text: str,
    *,
    max_text_chars: int,
) -> tuple[str, str | None, str, str]:
    body = text[:max_text_chars]
    return body, None, "", ""


class _RobotsPolicy:
    def __init__(self, *, session: requests.Session, policy: SurfaceDiscoveryPolicy) -> None:
        self.session = session
        self.policy = policy
        self._cache: dict[
            str,
            tuple[RobotFileParser | None | bool, dict[str, object]],
        ] = {}

    @staticmethod
    def _body_evidence(
        body: bytes,
        *,
        received_size: int,
        truncated: bool,
    ) -> dict[str, object]:
        return {
            "received_byte_size": received_size,
            "captured_byte_size": len(body),
            "captured_sha256": hashlib.sha256(body).hexdigest(),
            "truncated": truncated,
            "body_base64": base64.b64encode(body).decode("ascii"),
        }

    def decision(self, url: str) -> tuple[bool, dict[str, object]]:
        """Return the access decision together with evidence used to make it."""
        if not self.policy.respect_robots_txt:
            return True, {
                "checked": False,
                "allowed": True,
                "reason": "robots_check_disabled",
            }

        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        robots_url = origin + "/robots.txt"

        if origin not in self._cache:
            state: RobotFileParser | None | bool = None
            evidence: dict[str, object] = {
                "checked": True,
                "robots_url": robots_url,
                "status_code": None,
                "final_url": None,
                "response": None,
                "error": None,
            }
            try:
                response = self.session.get(
                    robots_url,
                    timeout=self.policy.timeout_seconds,
                    headers={"User-Agent": self.policy.user_agent},
                    allow_redirects=True,
                )
                full_body = response.content
                raw_body = full_body[: self.policy.max_response_bytes]
                truncated = len(full_body) > self.policy.max_response_bytes
                evidence["status_code"] = response.status_code
                evidence["final_url"] = str(response.url)
                evidence["response"] = self._body_evidence(
                    raw_body,
                    received_size=len(full_body),
                    truncated=truncated,
                )

                if response.status_code in {401, 403}:
                    state = False
                elif response.status_code == 404:
                    state = None
                elif response.ok:
                    parser = RobotFileParser()
                    parser.set_url(robots_url)
                    parser.parse(response.text.splitlines())
                    state = parser
            except requests.RequestException as exc:
                evidence["error"] = {
                    "type": type(exc).__name__,
                    "message": str(exc),
                }
                state = None
            self._cache[origin] = (state, evidence)

        state, evidence = self._cache[origin]
        if state is False:
            allowed = False
            reason = "robots_endpoint_denied"
        elif isinstance(state, RobotFileParser):
            allowed = state.can_fetch(self.policy.user_agent, url)
            reason = "robots_rule_allow" if allowed else "robots_rule_deny"
        else:
            allowed = True
            reason = "no_enforceable_robots_rule"

        current = dict(evidence)
        current["allowed"] = allowed
        current["reason"] = reason
        return allowed, current

    def allows(self, url: str) -> bool:
        """Compatibility view for callers that only need the Boolean decision."""
        return self.decision(url)[0]


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
    heapq.heappush(
        queue,
        _QueueItem(
            priority=-10_000,
            sequence=sequence,
            url=canonical_root,
            parent_url=None,
            depth=0,
        ),
    )
    seen: set[str] = set()
    pages: list[SurfacePage] = []
    captures: list[SurfaceCapture] = []
    errors: list[str] = []

    try:
        while queue and len(pages) < policy.max_pages:
            item = heapq.heappop(queue)
            if item.url in seen or item.depth > policy.max_depth:
                continue
            seen.add(item.url)

            if not is_url_in_institutional_scope(item.url, canonical_root):
                continue

            allowed, robots_evidence = robots.decision(item.url)
            if not allowed:
                observed_at = _utcnow_iso()
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
                        fetched_at=observed_at,
                        fetch_status="blocked_by_robots",
                    )
                )
                captures.append(
                    SurfaceCapture(
                        requested_url=item.url,
                        final_url=None,
                        observed_at=observed_at,
                        fetch_status="blocked_by_robots",
                        robots_evidence=robots_evidence,
                    )
                )
                continue

            try:
                response = http.get(
                    item.url,
                    timeout=policy.timeout_seconds,
                    headers={
                        "User-Agent": policy.user_agent,
                        "Accept": (
                            "text/html,application/xhtml+xml,application/json,"
                            "text/plain;q=0.8,*/*;q=0.1"
                        ),
                    },
                    allow_redirects=True,
                )
            except requests.RequestException as exc:
                observed_at = _utcnow_iso()
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
                        fetched_at=observed_at,
                        fetch_status="request_error",
                    )
                )
                captures.append(
                    SurfaceCapture(
                        requested_url=item.url,
                        final_url=None,
                        observed_at=observed_at,
                        fetch_status="request_error",
                        error_type=type(exc).__name__,
                        error_message=str(exc),
                        robots_evidence=robots_evidence,
                    )
                )
                continue

            # Preserve the HTTP response before the collector discards fields that
            # are not needed by the classifier.
            observed_at = _utcnow_iso()
            final_url_raw = str(response.url)
            final_url = canonicalize_public_url(final_url_raw) or item.url
            full_body = response.content
            raw_body = full_body[: policy.max_response_bytes]
            truncated = len(full_body) > policy.max_response_bytes
            content_hash = hashlib.sha256(raw_body).hexdigest()
            raw_content_type = str(response.headers.get("Content-Type") or "")
            content_type = raw_content_type.split(";", 1)[0].strip().lower()

            if not is_url_in_institutional_scope(final_url, canonical_root):
                pages.append(
                    SurfacePage(
                        url=item.url,
                        parent_url=item.parent_url,
                        depth=item.depth,
                        status_code=response.status_code,
                        content_type=raw_content_type or None,
                        content_sha256=content_hash,
                        title=None,
                        text="",
                        metadata_text="",
                        structured_text="",
                        fetched_at=observed_at,
                        truncated=truncated,
                        fetch_status="redirect_outside_scope",
                    )
                )
                captures.append(
                    SurfaceCapture(
                        requested_url=item.url,
                        final_url=final_url_raw,
                        observed_at=observed_at,
                        fetch_status="redirect_outside_scope",
                        status_code=response.status_code,
                        content_type=raw_content_type or None,
                        response_body=raw_body,
                        response_received_bytes=len(full_body),
                        response_truncated=truncated,
                        robots_evidence=robots_evidence,
                    )
                )
                continue

            allowed_type = not content_type or any(
                content_type.startswith(value) for value in _ALLOWED_CONTENT_TYPES
            )
            if not response.ok or not allowed_type:
                fetch_status = "http_error" if not response.ok else "unsupported_content_type"
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
                        fetched_at=observed_at,
                        truncated=truncated,
                        fetch_status=fetch_status,
                    )
                )
                captures.append(
                    SurfaceCapture(
                        requested_url=item.url,
                        final_url=final_url_raw,
                        observed_at=observed_at,
                        fetch_status=fetch_status,
                        status_code=response.status_code,
                        content_type=raw_content_type or None,
                        response_body=raw_body,
                        response_received_bytes=len(full_body),
                        response_truncated=truncated,
                        robots_evidence=robots_evidence,
                    )
                )
                continue

            encoding = response.encoding or "utf-8"
            decoded = raw_body.decode(encoding, errors="replace")
            links: tuple[tuple[str, str], ...] = ()
            if content_type in {"text/html", "application/xhtml+xml"} or "<html" in decoded[:500].lower():
                (
                    text,
                    title,
                    metadata_text,
                    structured_text,
                    media_urls,
                    links,
                ) = _extract_html_payload(
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
                    fetched_at=observed_at,
                    truncated=truncated,
                )
            )
            captures.append(
                SurfaceCapture(
                    requested_url=item.url,
                    final_url=final_url_raw,
                    observed_at=observed_at,
                    fetch_status="fetched",
                    status_code=response.status_code,
                    content_type=raw_content_type or None,
                    response_body=raw_body,
                    response_received_bytes=len(full_body),
                    response_truncated=truncated,
                    robots_evidence=robots_evidence,
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
        captures=tuple(captures),
    )


def _validate_storage_segment(value: str, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value in {".", ".."}
        or "/" in value
        or "\\" in value
    ):
        raise ValueError(f"{label} deve ser um identificador simples")
    return value


def _write_materialization_files(
    report_path: Path,
    classifier_path: Path,
    *,
    report_text: str,
    classifier_text: str,
) -> None:
    """Create both derived files without ever replacing an existing artifact."""
    if report_path.exists() or classifier_path.exists():
        raise FileExistsError("materialização existente; sobrescrita recusada")

    created: list[Path] = []
    try:
        with report_path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(report_text)
        created.append(report_path)

        with classifier_path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(classifier_text)
        created.append(classifier_path)
    except Exception:
        # Roll back only files created by this incomplete transaction. Historical
        # artifacts that predated the call are never touched.
        for path in reversed(created):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        raise


def materialize_surface_discovery(
    report: SurfaceDiscoveryReport,
    *,
    output_dir: str | Path,
    run_id: str,
    entity_id: str,
) -> tuple[Path, Path]:
    """Persist audit, classifier input and immutable evidence for each observation."""
    run_id = _validate_storage_segment(run_id, label="run_id")
    entity_id = _validate_storage_segment(entity_id, label="entity_id")
    if len(report.captures) != len(report.pages):
        raise ValueError("capturas ausentes ou desalinhadas; proveniência incompleta")

    output_root = Path(output_dir)
    root = output_root / "_ai_surface_discovery" / run_id / entity_id
    root.mkdir(parents=True, exist_ok=True)
    report_path = root / "surface_discovery_report.json"
    classifier_path = root / "surface_classifier_text.jsonl"

    if report_path.exists() or classifier_path.exists():
        raise FileExistsError("materialização existente; sobrescrita recusada")

    snapshot_store = RawArtifactStore(root / "snapshots")
    page_payloads: list[dict[str, object]] = []
    for page, capture in zip(report.pages, report.captures, strict=True):
        if page.fetch_status != capture.fetch_status or page.fetched_at != capture.observed_at:
            raise ValueError("captura e página divergentes")

        artifact = snapshot_store.preserve(
            capture.snapshot_payload(
                report=report,
                page=page,
                run_id=run_id,
                entity_id=entity_id,
            )
        )
        artifact_path = Path(artifact.path)
        snapshot_reference = artifact_path.relative_to(output_root).as_posix()

        page_payload = asdict(page)
        page_payload["requested_url"] = capture.requested_url
        page_payload["final_url"] = capture.final_url
        # VAL-009 consumes the actual final URL when a response exists. For a
        # block or request error there is no final response URL, so the unit is
        # anchored to the URL that was actually requested.
        page_payload["url"] = capture.final_url or page.url
        page_payload["snapshot_reference"] = snapshot_reference
        page_payload["snapshot_sha256"] = artifact.sha256
        page_payloads.append(page_payload)

    report_payload = report.to_dict()
    report_payload["pages"] = page_payloads
    report_payload["snapshot_schema_version"] = SURFACE_SNAPSHOT_SCHEMA_VERSION
    report_text = json.dumps(
        report_payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    classifier_text = "".join(
        json.dumps(page.classifier_payload(), ensure_ascii=False, sort_keys=True) + "\n"
        for page in report.pages
        if page.fetch_status == "fetched"
    )

    _write_materialization_files(
        report_path,
        classifier_path,
        report_text=report_text,
        classifier_text=classifier_text,
    )
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
    "SURFACE_SNAPSHOT_SCHEMA_VERSION",
    "SurfaceCapture",
    "SurfaceDiscoveryPolicy",
    "SurfaceDiscoveryReport",
    "SurfacePage",
    "canonicalize_public_url",
    "discover_and_materialize_public_surfaces",
    "discover_public_surfaces",
    "is_url_in_institutional_scope",
    "materialize_surface_discovery",
]
