"""Subordinate EFG1914 access/provenance probe for Jugoslovenska Kinoteka #81."""
from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import HEADERS, REQUEST_TIMEOUT
from .jean_vigo_probe import robots_allowed

EFG1914 = "https://www.europeanfilmgateway.eu/search-efg/efg1914"
HOSTS = frozenset({"www.europeanfilmgateway.eu", "europeanfilmgateway.eu"})
CRAWLER = "MemoriaAudiovisualRede"
VERSION = "2026-10-jugoslovenska-efg1914-v1"
CHALLENGE_TOKENS = (
    "/validate-browser", "verify you are human", "checking your browser",
    "enable javascript and cookies", "captcha", "access denied",
)


def _allowed_origin(url: str) -> bool:
    parsed = urlparse(url)
    try:
        port = parsed.port
    except ValueError:
        return False
    return bool(
        parsed.scheme == "https"
        and parsed.hostname in HOSTS
        and port in (None, 443)
        and parsed.username is None
        and parsed.password is None
        and not parsed.fragment
    )


def parse_efg1914_facet(html: str, url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    match = re.search(r"Jugoslovenska\s+Kinoteka\s*\(\s*(\d+)\s*\)", text, re.I)
    provider_links = []
    for a in soup.find_all("a", href=True):
        label = a.get_text(" ", strip=True)
        if "jugoslovenska kinoteka" not in label.lower():
            continue
        target = urljoin(url, a["href"])
        if _allowed_origin(target) and target not in provider_links:
            provider_links.append(target)
    forms = []
    for form in soup.find_all("form"):
        action = urljoin(url, form.get("action", ""))
        if not _allowed_origin(action):
            continue
        forms.append({
            "method": str(form.get("method", "get")).upper(),
            "action": action,
            "field_names": sorted({
                str(tag.get("name")) for tag in form.select("[name]")
                if tag.get("name")
            })[:30],
        })
    return {
        "provider_facet_visible": bool(match),
        "provider_facet_count": int(match.group(1)) if match else None,
        "provider_links_discovered": provider_links[:10],
        "forms": forms[:10],
        "page_title": (
            soup.title.get_text(" ", strip=True)[:200] if soup.title else ""
        ),
        "detail_links_visible": len({
            urljoin(url, a["href"]) for a in soup.find_all("a", href=True)
            if "/detail/" in urlparse(urljoin(url, a["href"])).path
            and _allowed_origin(urljoin(url, a["href"]))
        }),
    }


def run_efg1914_probe(session: requests.Session | None = None) -> dict[str, Any]:
    if session is None:
        session = requests.Session()
        session.headers.update({
            **HEADERS,
            "User-Agent": f"{CRAWLER}/1.0 (+public-provenance-probe)",
        })
    robots_cache: dict[str, tuple[str, str]] = {}
    robots_evidence: dict[str, dict[str, Any]] = {}

    def check_robots(host: str) -> bool:
        if host in robots_evidence:
            return robots_evidence[host]["mode"] != "unverifiable"
        robots_url = f"https://{host}/robots.txt"
        evidence: dict[str, Any] = {
            "url": robots_url, "mode": "unverifiable",
            "status_code": None, "error": None,
        }
        robots_evidence[host] = evidence
        try:
            response = session.get(
                robots_url, timeout=(8, REQUEST_TIMEOUT),
                allow_redirects=False,
            )
        except requests.RequestException as exc:
            evidence["error"] = f"{type(exc).__name__}: {exc}"
            return False
        evidence["status_code"] = response.status_code
        if response.status_code in {404, 410}:
            evidence["mode"] = "absent"
            return True
        if response.status_code != 200:
            evidence["error"] = "robots_unverifiable_status_or_redirect"
            return False
        text = response.text or ""
        if not text.strip() or "<html" in text.lower():
            evidence["error"] = "robots_invalid_payload"
            return False
        evidence["mode"] = "evaluated"
        robots_cache[host] = (text, robots_url)
        return True

    payload: dict[str, Any] = {
        "version": VERSION, "source": EFG1914,
        "robots": robots_evidence, "status_code": None, "final_url": None,
        "redirect_chain": [], "provider_facet_visible": False,
        "provider_facet_count": None, "provider_links_discovered": [],
        "detail_links_visible": 0, "forms": [],
        "gate_assessment": "hold_robots_unverifiable",
        "staged_collector_authorized": False,
        "records_enumerated": 0,
        "notes": [
            "No validation-browser request, no captcha bypass, no guessed filter",
            "Any facet count is a provider UI claim, not enumerated records",
        ],
    }

    target = EFG1914
    for _ in range(5):
        if not _allowed_origin(target):
            payload["gate_assessment"] = "hold_redirect_outside_authorized_https"
            return payload
        if any(token in target.lower() for token in CHALLENGE_TOKENS):
            payload["gate_assessment"] = "hold_browser_challenge"
            return payload
        host = urlparse(target).hostname or ""
        if not check_robots(host):
            return payload
        policy = robots_evidence[host]
        if policy["mode"] == "evaluated" and not robots_allowed(
            robots_cache[host][0], CRAWLER, target
        ):
            payload["gate_assessment"] = "hold_blocked_by_robots"
            return payload
        try:
            response = session.get(
                target, timeout=(8, REQUEST_TIMEOUT),
                allow_redirects=False,
            )
        except requests.RequestException as exc:
            payload["gate_assessment"] = "hold_unverifiable_public_route"
            payload["error"] = f"{type(exc).__name__}: {exc}"
            return payload
        payload["status_code"] = response.status_code
        payload["final_url"] = target
        if response.status_code in {301, 302, 303, 307, 308}:
            location = response.headers.get("location", "")
            if not location:
                payload["gate_assessment"] = "hold_invalid_redirect"
                return payload
            new_target = urljoin(target, location)
            payload["redirect_chain"].append(new_target)
            target = new_target
            continue
        if response.status_code in {401, 403, 429, 503}:
            payload["gate_assessment"] = "hold_access_blocked"
            return payload
        if response.status_code != 200:
            payload["gate_assessment"] = "hold_unverifiable_public_route"
            return payload
        text = response.text or ""
        if any(token in text[:15000].lower() for token in CHALLENGE_TOKENS):
            payload["gate_assessment"] = "hold_browser_challenge"
            return payload
        if "html" not in response.headers.get("content-type", "").lower():
            payload["gate_assessment"] = "hold_unexpected_response_type"
            return payload
        parsed = parse_efg1914_facet(text, target)
        payload.update(parsed)
        payload["gate_assessment"] = (
            "investigate_explicit_provider_filter_link"
            if parsed["provider_links_discovered"]
            else "hold_no_reproducible_provider_enumeration"
        )
        return payload

    payload["gate_assessment"] = "hold_redirect_limit"
    return payload


def dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
