"""Bounded metadata-only staged probe: Eye pages 0–2 OR one Czech programme/episode.

Explicitly authorized through the PR #91 label. No multimedia is requested,
no global corpus is published, and no Neon credentials or production storage
are accessed. Checkpoints are run artifacts, not durable Gate P0 backups.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import ssl
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import HTTPSHandler, Request, build_opener
from urllib.robotparser import RobotFileParser

from memoria_audiovisual.eye import (
    _list_url, extract_eye_declared_fragment_total,
    parse_eye_fragment_list_page,
)
from memoria_audiovisual.czech_television import (
    parse_czech_television_catalog_page,
    parse_czech_television_show_page,
    parse_czech_television_episode_page,
)
from scripts.probe_monthly_sources import NoRedirect, SOURCES, USER_AGENT

SOURCES_ALLOWED = frozenset(("eye", "czech_tv"))
MAX_ROBOTS_BYTES = 65536
MAX_HTML_BYTES = 524288
MAX_CRAWL_DELAY_SECONDS = 30


class ProbeHold(RuntimeError):
    """Typed category only: never put URL, response, or credentials in logs."""


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _same_origin(url: str, host: str) -> bool:
    u = urlparse(url)
    return (u.scheme == "https" and u.hostname == host
            and u.port in (None, 443) and not u.username and not u.password)


def _policy(url, opener):
    base = urlparse(url)
    robots_url = urlunparse(("https", base.netloc, "/robots.txt", "", "", ""))
    req = Request(robots_url, headers={"User-Agent": USER_AGENT, "Accept": "text/plain"})
    try:
        with opener.open(req, timeout=12) as response:
            if response.status != 200:
                raise ProbeHold("robots_unavailable")
            if "text/plain" not in response.headers.get("Content-Type", "").lower():
                raise ProbeHold("robots_unusable")
            data = response.read(MAX_ROBOTS_BYTES + 1)
    except (HTTPError, URLError, OSError, TimeoutError) as exc:
        raise ProbeHold("robots_unavailable") from exc
    if not data or len(data) > MAX_ROBOTS_BYTES or b"\x00" in data:
        raise ProbeHold("robots_unusable")
    parser = RobotFileParser()
    parser.parse(data.decode("utf-8", "replace").splitlines())
    delay = parser.crawl_delay(USER_AGENT) or 0
    if delay > MAX_CRAWL_DELAY_SECONDS:
        raise ProbeHold("crawl_delay_exceeds_probe_budget")
    if not parser.can_fetch(USER_AGENT, url):
        raise ProbeHold("robots_disallowed")
    return parser, max(1, delay), _digest(data)


def _html(url, host, robots, opener):
    if not _same_origin(url, host):
        raise ProbeHold("off_domain_url_rejected")
    if not robots.can_fetch(USER_AGENT, url):
        raise ProbeHold("robots_disallowed_for_stage")
    req = Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
    })
    try:
        with opener.open(req, timeout=12) as response:
            if response.status != 200:
                raise ProbeHold("source_http_unavailable")
            if "html" not in response.headers.get("Content-Type", "").lower():
                raise ProbeHold("unexpected_content_type")
            final_url = response.geturl() if hasattr(response, "geturl") else url
            if final_url != url:
                raise ProbeHold("redirected_url_rejected")
            sample = response.read(MAX_HTML_BYTES + 1)
    except HTTPError as exc:
        category = (
            "source_access_forbidden" if exc.code == 403
            else "source_rate_limited" if exc.code == 429
            else "source_http_unavailable"
        )
        raise ProbeHold(category) from exc
    except (URLError, OSError, TimeoutError) as exc:
        raise ProbeHold("source_network_unavailable") from exc
    return sample[:MAX_HTML_BYTES].decode("utf-8", "replace"), _digest(
        sample[:MAX_HTML_BYTES]
    ), len(sample) > MAX_HTML_BYTES


class Checkpoints:
    def __init__(self, source, output_dir):
        self.path = Path(output_dir) / (source + ".json")
        self.value = {
            "source": source,
            "run_id": os.environ.get("GITHUB_RUN_ID", "offline-test"),
            # PR workflows set GITHUB_SHA to the synthetic merge commit.
            # Record the reviewed PR head separately from the runner checkout.
            "head_sha": os.environ.get("MAR_PROBE_HEAD_SHA", os.environ.get("GITHUB_SHA", "offline-test")),
            "workflow_sha": os.environ.get("GITHUB_SHA", "offline-test"),
            "started_at_utc": datetime.now(timezone.utc).isoformat(),
            "purpose": "bounded_synthetic_free_metadata_probe",
            "media_downloaded": False,
            "production_writes": False,
            "corpus_validated": False,
            "checkpoint_storage": "github_artifact_retention_30_days",
            "status": "HOLD",
            "reason": "not_started",
            "stages": [],
            "chain_sha256": _digest(b""),
        }
        self.write()

    def write(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = _canonical(self.value) + "\n"
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(data, encoding="utf-8")
        os.replace(temporary, self.path)

    def stage(self, name, **fields):
        step = {"stage": name, **fields}
        current = self.value["chain_sha256"]
        self.value["chain_sha256"] = _digest(
            (current + _canonical(step)).encode("utf-8")
        )
        self.value["stages"].append(step)
        self.write()

    def finish(self, status, reason):
        self.value["status"] = status
        self.value["reason"] = reason
        self.write()


def _run_eye(state, opener, sleep_fn):
    source_url = SOURCES["eye"][0]
    host = urlparse(source_url).hostname
    robots, pause, robots_sha = _policy(source_url, opener)
    state.stage("robots", robots_sha256=robots_sha, crawl_delay_seconds=pause)
    seen = set()
    declared = None
    for index in (0, 1, 2):
        if index:
            sleep_fn(pause)
        url = _list_url(index)
        if not _same_origin(url, host):
            raise ProbeHold("eye_page_url_rejected")
        html, digest, truncated = _html(url, host, robots, opener)
        if truncated:
            raise ProbeHold("eye_page_sample_oversize")
        total = extract_eye_declared_fragment_total(html)
        if total <= 0 or (declared is not None and total != declared):
            raise ProbeHold("eye_fragment_filter_inconsistent")
        declared = total
        rows = parse_eye_fragment_list_page(html, url)
        if not 1 <= len(rows) <= 20:
            raise ProbeHold("eye_page_records_outside_bounds")
        current = set()
        for record in rows:
            dest = record.get("page_url", "")
            path = urlparse(dest).path
            if not (_same_origin(dest, host)
                    and (path.startswith("/en/collection/film-history/film/")
                         or re.fullmatch(r"/en/node/\d+", path))
                    and record.get("record_id")):
                raise ProbeHold("eye_detail_candidate_invalid")
            current.add(record["record_id"])
        duplicate = current.intersection(seen)
        new_ids = current - seen
        seen.update(current)
        state.stage(
            "eye_page_" + str(index), page_index=index, html_sha256=digest,
            declared_total=declared, parsed_records=len(rows),
            unique_this_page=len(current), new_records=len(new_ids),
            duplicates_across_pages=len(duplicate), cumulative_unique=len(seen),
            record_ids=sorted(current),
        )
    state.stage("eye_staged_summary", pages_checked=3, cumulative_unique=len(seen),
                declared_total=declared, globally_complete=False)
    state.finish("STAGED_PASS", "three_limited_index_pages_with_dedup_only")


def _run_czech(state, opener, sleep_fn):
    source_url = SOURCES["czech_tv"][0]
    host = urlparse(source_url).hostname
    robots, pause, robots_sha = _policy(source_url, opener)
    state.stage("robots", robots_sha256=robots_sha, crawl_delay_seconds=pause)
    html, digest, truncated = _html(source_url, host, robots, opener)
    programmes = parse_czech_television_catalog_page(html, "Cultura")
    candidates = []
    for row in programmes:
        candidate = row.get("show_url", "")
        if (_same_origin(candidate, host) and re.fullmatch(
                r"/porady/\d{2,}-[a-z0-9-]+/?", urlparse(candidate).path, re.I
        )):
            candidates.append(row)
    state.stage("czech_catalogue", html_sha256=digest,
                truncated=truncated, programme_candidates=len(candidates))
    if not candidates:
        raise ProbeHold("czech_no_public_programme_candidates")
    show = candidates[0]  # exactly one, never try another automatically
    sleep_fn(pause)
    show_url = show["show_url"]
    show_html, show_digest, show_truncated = _html(
        show_url, host, robots, opener
    )
    if show_truncated:
        raise ProbeHold("czech_show_page_oversize")
    episodes = parse_czech_television_show_page(
        show_html, show["show_slug"]
    )
    eligible = [
        item for item in episodes
        if _same_origin(item, host)
        and re.fullmatch(
            r"/porady/" + re.escape(show["show_slug"]) + r"/\d+/?",
            urlparse(item).path, re.I
        )
    ]
    state.stage("czech_programme", programme_id=show.get("show_id", ""),
                html_sha256=show_digest, episode_candidates=len(eligible))
    if not eligible:
        raise ProbeHold("czech_no_public_episode_candidates")
    episode_url = eligible[0]  # exactly one, no fallback
    sleep_fn(pause)
    episode_html, episode_digest, episode_truncated = _html(
        episode_url, host, robots, opener
    )
    if episode_truncated:
        raise ProbeHold("czech_episode_page_oversize")
    record = parse_czech_television_episode_page(
        episode_html, episode_url, show
    )
    playable = bool(record and record.get("record_id"))
    state.stage("czech_episode", html_sha256=episode_digest,
                episode_id=record.get("record_id", "") if record else "",
                media_meta_is_playable=playable,
                actual_stream_playback_verified=False)
    if not playable:
        raise ProbeHold("czech_episode_not_playable_in_public_metadata")
    state.finish("STAGED_PASS", "one_episode_media_meta_playable_only")


def run(source, output_dir="data/probe-staged", *, opener=None, sleep_fn=time.sleep):
    if source not in SOURCES_ALLOWED:
        raise ValueError("source_not_authorized")
    state = Checkpoints(source, output_dir)
    opener = opener or build_opener(
        NoRedirect(), HTTPSHandler(context=ssl.create_default_context())
    )
    try:
        if source == "eye":
            _run_eye(state, opener, sleep_fn)
        else:
            _run_czech(state, opener, sleep_fn)
    except ProbeHold as error:
        state.finish("HOLD", str(error))
    except Exception:
        state.finish("HOLD", "unexpected_error_suppressed")
    print(_canonical({
        "source": source, "status": state.value["status"],
        "reason": state.value["reason"],
        "stages": len(state.value["stages"]),
        "chain_sha256": state.value["chain_sha256"],
        "media_downloaded": False, "corpus_validated": False,
    }))
    return state.value["status"] == "STAGED_PASS"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=sorted(SOURCES_ALLOWED), required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(_canonical({"source": args.source, "mode": "offline_plan_only"}))
        return 0
    if (os.environ.get("MAR_SOURCE_STAGED_APPROVED") != "yes"
            or os.environ.get("GITHUB_EVENT_NAME") != "pull_request"
            or os.environ.get("GITHUB_ACTOR") != "brauliorrs"):
        parser.error("explicit staged-source PR approval required")
    return 0 if run(args.source) else 2


if __name__ == "__main__":
    raise SystemExit(main())
