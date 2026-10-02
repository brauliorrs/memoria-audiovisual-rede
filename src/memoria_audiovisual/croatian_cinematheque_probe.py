"""Technical discovery probe for Croatian Cinematheque / HDA public surfaces.

This is not a corpus collector. It inspects the institutional HDA site and the
public HAIS discovery interface to determine whether audiovisual records can be
enumerated reproducibly without brute-force identifiers or media downloads.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import HEADERS, REQUEST_TIMEOUT


HDA_HOME_URL = "https://www.arhiv.hr/"
HDA_KINOTEKA_URL = "https://www.arhiv.hr/O-nama/Ustroj/Hrvatska-kinoteka"
HDA_FILM_HOLDINGS_URL = (
    "https://www.arhiv.hr/hr-hr/Istra%C5%BEite-gradivo/%C5%A0to-%C4%8Duvamo/"
    "Kako-je-gradivo-organizirano/Filmsko-gradivo"
)
HAIS_HOME_URL = "https://hais.arhiv.hr/"
HDA_ROBOTS_URL = "https://www.arhiv.hr/robots.txt"
HAIS_ROBOTS_URL = "https://hais.arhiv.hr/robots.txt"
HDA_SITEMAPS = (
    "https://www.arhiv.hr/sitemap.xml",
    "https://www.arhiv.hr/sitemap_index.xml",
)
HAIS_SITEMAPS = (
    "https://hais.arhiv.hr/sitemap.xml",
    "https://hais.arhiv.hr/sitemap_index.xml",
)
PROBE_VERSION = "2026-10-croatian-cinematheque-probe-v1"
CRAWLER_TOKEN = "MemoriaAudiovisualRede"

_DISCOVERY_RE = re.compile(
    r"(?:trazilica|search|pretra|catalog|katalog|api|ajax|graphql|page|pagination|"
    r"digital|film|video|audiovizual)",
    re.I,
)
_XML_LOC_RE = re.compile(r"<loc>\s*([^<]+?)\s*</loc>", re.I)


@dataclass(frozen=True)
class ProbeResponse:
    requested_url: str
    final_url: str | None
    status_code: int | None
    content_type: str
    text: str
    error: str | None


def _clean(value: Any, *, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            **HEADERS,
            "User-Agent": f"{CRAWLER_TOKEN}/1.0 (+research; public-metadata-probe)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "hr,en;q=0.8",
        }
    )
    return session


def fetch_public_url(
    session: requests.Session,
    url: str,
    *,
    attempts: int = 3,
) -> ProbeResponse:
    response = None
    try:
        for attempt in range(attempts):
            response = session.get(
                url,
                timeout=(8, REQUEST_TIMEOUT),
                allow_redirects=True,
            )
            if response.status_code not in {429, 503}:
                break
            time.sleep(float(attempt + 1))
    except requests.RequestException as exc:
        return ProbeResponse(
            requested_url=url,
            final_url=getattr(response, "url", None),
            status_code=getattr(response, "status_code", None),
            content_type=(
                response.headers.get("content-type", "")
                if response is not None
                else ""
            ),
            text="",
            error=f"{type(exc).__name__}: {exc}",
        )
    return ProbeResponse(
        requested_url=url,
        final_url=response.url,
        status_code=response.status_code,
        content_type=response.headers.get("content-type", ""),
        text=response.text,
        error=None,
    )


def _robots_groups(text: str) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    agents: list[str] = []
    rules: list[tuple[bool, str]] = []
    saw_rule = False

    def flush() -> None:
        nonlocal agents, rules, saw_rule
        if agents:
            groups.append({"agents": tuple(agents), "rules": tuple(rules)})
        agents, rules, saw_rule = [], [], False

    for raw_line in (text or "").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key, value = key.strip().lower(), value.strip()
        if key == "user-agent":
            if saw_rule:
                flush()
            agents.append(value.lower())
        elif key in {"allow", "disallow"} and agents:
            saw_rule = True
            if value:
                rules.append((key == "allow", value))
    flush()
    return groups


def _rule_regex(pattern: str) -> re.Pattern[str]:
    anchored = pattern.endswith("$")
    body = pattern[:-1] if anchored else pattern
    expression = ".*".join(re.escape(part) for part in body.split("*"))
    return re.compile("^" + expression + ("$" if anchored else ""))


def robots_allowed(text: str, user_agent: str, url: str) -> bool:
    groups = _robots_groups(text)
    agent = str(user_agent or "*").lower()
    explicit = [
        group
        for group in groups
        if any(token and token != "*" and token in agent for token in group["agents"])
    ]
    selected = explicit or [group for group in groups if "*" in group["agents"]]
    if not selected:
        return True

    parsed = urlparse(url)
    target = parsed.path or "/"
    if parsed.query:
        target += "?" + parsed.query

    matches: list[tuple[int, bool]] = []
    for group in selected:
        for allowance, pattern in group["rules"]:
            if _rule_regex(pattern).search(target):
                specificity = len(pattern.rstrip("$").replace("*", ""))
                matches.append((specificity, allowance))
    if not matches:
        return True
    longest = max(score for score, _ in matches)
    return any(allow for score, allow in matches if score == longest)


def evaluate_robots(
    session: requests.Session,
    robots_url: str,
    targets: tuple[str, ...],
) -> dict[str, Any]:
    response = fetch_public_url(session, robots_url)
    result: dict[str, Any] = {
        "robots_url": robots_url,
        "status_code": response.status_code,
        "error": response.error,
        "mode": None,
        "targets": [],
        "robots_excerpt": _clean(response.text, limit=1800),
    }
    if response.error:
        result["mode"] = "unverifiable"
        reason = "robots_unreachable"
        allowed = False
    elif response.status_code in {404, 410}:
        result["mode"] = "absent"
        reason = "robots_absent"
        allowed = True
    elif response.status_code != 200:
        result["mode"] = "unverifiable"
        reason = f"robots_http_{response.status_code}"
        allowed = False
    else:
        stripped = (response.text or "").strip()
        if not stripped or "<html" in stripped.lower():
            result["mode"] = "unverifiable"
            reason = "robots_invalid_payload"
            allowed = False
        else:
            result["mode"] = "evaluated_rfc9309"
            reason = "robots_evaluated_rfc9309"
            allowed = None

    for url in targets:
        target_allowed = (
            robots_allowed(response.text, CRAWLER_TOKEN, url)
            if allowed is None
            else allowed
        )
        result["targets"].append(
            {"url": url, "allowed": bool(target_allowed), "reason": reason}
        )
    return result


def parse_surface_html(html_text: str, page_url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html_text or "", "html.parser")
    host = urlparse(page_url).netloc

    forms = []
    for form in soup.find_all("form"):
        controls = []
        for node in form.find_all(["input", "select", "textarea", "button"]):
            name = _clean(node.get("name") or node.get("id"))
            value = _clean(node.get("value"), limit=200)
            label = _clean(node.get_text(" ", strip=True), limit=200)
            if name or value or label:
                controls.append(
                    {
                        "name": name,
                        "type": _clean(node.get("type") or node.name),
                        "value": value,
                        "label": label,
                    }
                )
        forms.append(
            {
                "action": urljoin(page_url, form.get("action") or page_url),
                "method": _clean(form.get("method") or "get").lower(),
                "controls": controls[:100],
            }
        )

    links = []
    for anchor in soup.find_all("a", href=True):
        absolute = urljoin(page_url, anchor.get("href", ""))
        parsed = urlparse(absolute)
        text = _clean(anchor.get_text(" ", strip=True), limit=250)
        marker = f"{parsed.path} {parsed.query} {text}"
        if parsed.netloc == host and _DISCOVERY_RE.search(marker):
            links.append({"url": absolute, "text": text})

    scripts = []
    inline_hints = []
    for script in soup.find_all("script"):
        src = script.get("src")
        if src:
            scripts.append(urljoin(page_url, src))
        inline = script.string or script.get_text(" ", strip=True)
        if inline and _DISCOVERY_RE.search(inline):
            inline_hints.append(_clean(inline, limit=1200))

    data_hints = []
    for node in soup.find_all(True):
        for key, value in node.attrs.items():
            if not str(key).startswith("data-"):
                continue
            rendered = " ".join(value) if isinstance(value, list) else str(value)
            if _DISCOVERY_RE.search(f"{key} {rendered}"):
                data_hints.append(
                    {
                        "tag": node.name,
                        "attribute": str(key),
                        "value": _clean(rendered, limit=500),
                    }
                )

    return {
        "title": _clean(soup.title.get_text(" ", strip=True) if soup.title else ""),
        "forms": forms,
        "discovery_links": links[:100],
        "scripts": sorted(set(scripts)),
        "inline_hints": inline_hints[:30],
        "data_hints": data_hints[:100],
        "html_length": len(html_text or ""),
    }


def parse_sitemap(xml_text: str) -> dict[str, Any]:
    urls = [_clean(item) for item in _XML_LOC_RE.findall(xml_text or "")]
    candidates = [
        url
        for url in urls
        if _DISCOVERY_RE.search(url)
    ]
    return {
        "url_count": len(urls),
        "candidate_count": len(candidates),
        "candidate_samples": candidates[:50],
        "nested_sitemaps": [url for url in urls if url.lower().endswith(".xml")][:50],
    }


def _allowed_map(result: dict[str, Any]) -> dict[str, bool]:
    return {
        item["url"]: bool(item["allowed"])
        for item in result.get("targets", [])
        if item.get("url")
    }


def run_croatian_cinematheque_probe(
    *,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    session = session or _session()

    hda_targets = (HDA_HOME_URL, HDA_KINOTEKA_URL, HDA_FILM_HOLDINGS_URL, *HDA_SITEMAPS)
    hais_targets = (HAIS_HOME_URL, *HAIS_SITEMAPS)
    hda_robots = evaluate_robots(session, HDA_ROBOTS_URL, hda_targets)
    hais_robots = evaluate_robots(session, HAIS_ROBOTS_URL, hais_targets)
    hda_allowed = _allowed_map(hda_robots)
    hais_allowed = _allowed_map(hais_robots)

    surfaces = []
    for kind, url, allowed in (
        ("institutional_home", HDA_HOME_URL, hda_allowed.get(HDA_HOME_URL, False)),
        ("kinoteka_profile", HDA_KINOTEKA_URL, hda_allowed.get(HDA_KINOTEKA_URL, False)),
        ("film_holdings", HDA_FILM_HOLDINGS_URL, hda_allowed.get(HDA_FILM_HOLDINGS_URL, False)),
        ("hais_public_search", HAIS_HOME_URL, hais_allowed.get(HAIS_HOME_URL, False)),
    ):
        if not allowed:
            surfaces.append({"kind": kind, "url": url, "status": "blocked_by_robots"})
            continue
        response = fetch_public_url(session, url)
        parsed = (
            parse_surface_html(response.text, response.final_url or url)
            if response.status_code == 200 and not response.error
            else None
        )
        surfaces.append(
            {
                "kind": kind,
                "url": url,
                "final_url": response.final_url,
                "status_code": response.status_code,
                "content_type": response.content_type,
                "error": response.error,
                "parsed": parsed,
            }
        )

    sitemaps = []
    for robots_map, candidates in (
        (hda_allowed, HDA_SITEMAPS),
        (hais_allowed, HAIS_SITEMAPS),
    ):
        for url in candidates:
            if not robots_map.get(url, False):
                sitemaps.append({"url": url, "status": "blocked_by_robots"})
                continue
            response = fetch_public_url(session, url)
            parsed = (
                parse_sitemap(response.text)
                if response.status_code == 200 and not response.error
                else None
            )
            sitemaps.append(
                {
                    "url": url,
                    "status_code": response.status_code,
                    "content_type": response.content_type,
                    "error": response.error,
                    "parsed": parsed,
                }
            )

    hais_surface = next(
        (row for row in surfaces if row["kind"] == "hais_public_search"),
        {},
    )
    parsed_hais = hais_surface.get("parsed") or {}
    forms = parsed_hais.get("forms", [])
    discovery_links = parsed_hais.get("discovery_links", [])
    mechanisms = []
    if forms:
        mechanisms.append("hais_public_search_form")
    if discovery_links:
        mechanisms.append("hais_internal_discovery_routes")
    if any((item.get("parsed") or {}).get("candidate_count", 0) for item in sitemaps):
        mechanisms.append("sitemap_discovery_candidates")

    all_roots_allowed = (
        hda_allowed.get(HDA_HOME_URL, False)
        and hais_allowed.get(HAIS_HOME_URL, False)
    )
    if not all_roots_allowed:
        gate = "hold_robots_not_allowed_or_unverifiable"
    elif forms or discovery_links:
        gate = "public_search_surface_confirmed_enumeration_not_yet_validated"
    else:
        gate = "hold_no_reproducible_enumeration_surface_detected"

    return {
        "probe_version": PROBE_VERSION,
        "institution": "Hrvatski Državni Arhiv - Hrvatska kinoteka",
        "queue_code": "fiaf-croatian-cinematheque",
        "automatic_incorporation_authorized": False,
        "brute_force_id_scan_performed": False,
        "media_download_performed": False,
        "experimental_model_used": False,
        "custodial_title_count_context_only": 15000,
        "robots": {"hda": hda_robots, "hais": hais_robots},
        "surfaces": surfaces,
        "sitemaps": sitemaps,
        "enumeration_mechanisms": mechanisms,
        "gate_assessment": gate,
        "next_action": (
            "engineer_bounded_hais_search_probe"
            if gate == "public_search_surface_confirmed_enumeration_not_yet_validated"
            else "protocol_hold_or_retest"
        ),
    }


__all__ = [
    "HAIS_HOME_URL",
    "HAIS_ROBOTS_URL",
    "HDA_FILM_HOLDINGS_URL",
    "HDA_HOME_URL",
    "HDA_KINOTEKA_URL",
    "HDA_ROBOTS_URL",
    "parse_surface_html",
    "robots_allowed",
    "run_croatian_cinematheque_probe",
]
