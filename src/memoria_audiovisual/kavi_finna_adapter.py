"""Finna/Elonet source adapter for the generic metadata-only staging runner.

The prior #82 probe discovered the institutional code and Video format code.
At runtime, preflight re-verifies both against public facets, then uses the
documented resumptionToken protocol. Never retrieves audiovisual media.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import requests

from .kavi_elonet_probe import (
    API_ROOT, FACET_QUERY, Guard, _kavi_building_candidates,
)
from .metadata_staging import MetadataPage, StageRejected

FORMAT_FACET_URL = API_ROOT + "?" + urlencode([
    ("lookfor", ""), ("limit", "0"), ("facet[]", "format"),
])
VERSION = "kavi-finna-adapter-1.0.0"


def _facet_values(entries: Any) -> set[str]:
    if not isinstance(entries, list):
        raise StageRejected("facet_entries_not_list")
    found: set[str] = set()
    stack: list[Any] = list(entries)
    while stack:
        item = stack.pop()
        if not isinstance(item, dict):
            raise StageRejected("facet_item_not_object")
        value = item.get("value")
        if isinstance(value, str):
            found.add(value)
        children = item.get("children")
        if children is not None:
            if not isinstance(children, list):
                raise StageRejected("facet_children_not_list")
            stack.extend(children)
    return found


@dataclass(frozen=True)
class FinnaScope:
    building_code: str
    format_code: str
    evidence_sha256: str
    institution_code: str = "fiaf-kavi"
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if (
            self.institution_code != "fiaf-kavi"
            or self.building_code != "0/KAVI/"
            or self.format_code != "0/Video/"
        ):
            raise ValueError("unapproved_finna_scope")
        if not (
            isinstance(self.evidence_sha256, str)
            and len(self.evidence_sha256) == 64
            and all(c in "0123456789abcdef" for c in self.evidence_sha256)
        ):
            raise ValueError("scope_evidence_sha256_required")

    def to_dict(self) -> dict[str, str]:
        return {
            "building_code": self.building_code,
            "format_code": self.format_code,
            "evidence_sha256": self.evidence_sha256,
            "institution_code": self.institution_code,
            "schema_version": self.schema_version,
            "adapter_version": VERSION,
        }


class FinnaMetadataSource:
    """Public metadata only; no media fetch and no downstream publication."""

    def __init__(self, session: requests.Session, scope: FinnaScope):
        self.guard = Guard(session)
        self._scope = scope
        self._total: int | None = None

    @property
    def scope(self) -> dict[str, str]:
        return self._scope.to_dict()

    def _json(self, url: str) -> dict[str, Any]:
        response = self.guard.get(url)
        if response.error or response.status != 200:
            raise StageRejected("finna_http_or_robots_unverifiable")
        if "json" not in response.mime.lower():
            raise StageRejected("finna_unexpected_content_type")
        try:
            data = json.loads(response.text)
        except (TypeError, ValueError) as ex:
            raise StageRejected("finna_invalid_json") from ex
        if not isinstance(data, dict) or data.get("status") not in ("OK", "ok"):
            raise StageRejected("finna_api_status_invalid")
        return data

    @staticmethod
    def _count(data: dict[str, Any]) -> int:
        count = data.get("resultCount")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise StageRejected("finna_invalid_result_count")
        return count

    def _verified_query(self, *, token: str | None = None, count_only: bool = False) -> str:
        if token is not None:
            if not token or len(token) > 4096:
                raise StageRejected("invalid_resumption_token")
            # Finna ignores filters on continuation; pass ONLY the token.
            return API_ROOT + "?" + urlencode({"resumptionToken": token})
        params = [
            ("lookfor", ""),
            ("filter[]", f'building:"{self._scope.building_code}"'),
            ("filter[]", f'format:"{self._scope.format_code}"'),
        ]
        if count_only:
            params.append(("limit", "0"))
        else:
            # Initial '*' request preserves filters; no page/limit/facet allowed.
            params.append(("resumptionToken", "*"))
        return API_ROOT + "?" + urlencode(params)

    def preflight(self) -> int:
        buildings = self._json(FACET_QUERY)
        facets = buildings.get("facets")
        if not isinstance(facets, dict):
            raise StageRejected("building_facets_missing")
        matches = _kavi_building_candidates(facets.get("building", []))
        if (
            len(matches) != 1
            or matches[0]["value"] != self._scope.building_code
        ):
            raise StageRejected("kavi_building_facet_drift_or_ambiguity")
        formats = self._json(FORMAT_FACET_URL)
        ff = formats.get("facets")
        if not isinstance(ff, dict):
            raise StageRejected("format_facets_missing")
        if self._scope.format_code not in _facet_values(ff.get("format", [])):
            raise StageRejected("video_format_facet_drift")
        filtered = self._json(self._verified_query(count_only=True))
        count = self._count(filtered)
        if filtered.get("records") not in ([], None):
            raise StageRejected("finna_count_response_not_empty")
        self._total = count
        return count

    def fetch_page(self, token: str | None) -> MetadataPage:
        if self._total is None:
            raise StageRejected("preflight_required")
        data = self._json(self._verified_query(token=token))
        count = self._count(data)
        records = data.get("records")
        if not isinstance(records, list):
            raise StageRejected("finna_records_not_list")
        cursor = data.get("resumptionToken")
        if cursor is None:
            next_token = None
        elif isinstance(cursor, dict):
            # Finna returns {"token": "...", "expires": ...}, not a scalar.
            if "token" not in cursor:
                raise StageRejected("resumption_token_object_missing_token")
            candidate = cursor["token"]
            if candidate is None or candidate == "":
                next_token = None
            elif isinstance(candidate, str) and len(candidate) <= 4096:
                next_token = candidate
            else:
                raise StageRejected("invalid_resumption_token_value")
        else:
            raise StageRejected("invalid_resumption_token_object")
        normalized: list[dict[str, Any]] = []
        for raw in records:
            if not isinstance(raw, dict):
                raise StageRejected("non_object_record")
            rid = raw.get("id")
            title = raw.get("title")
            if not isinstance(rid, str) or not rid:
                raise StageRejected("record_without_id")
            if not isinstance(title, str) or not title.strip():
                raise StageRejected("record_without_title")
            formats = raw.get("formats", [])
            if not isinstance(formats, list):
                raise StageRejected("record_formats_invalid")
            normalized.append({
                "id": rid,
                "title": title,
                "formats": formats,
                "institutions": raw.get("institutions", []),
                "online_url_metadata_present": bool(raw.get("onlineUrls")),
                "film_semantics": (
                    "film_candidate"
                    if rid.startswith("kavi.elonet_elokuva_")
                    else "unverified_audiovisual_record"
                ),
                "provider_index_code": self._scope.building_code,
                "custody_status": "not_established",
                "media_rights_status": "not_verified",
                "media_downloaded": False,
            })
        return MetadataPage(tuple(normalized), count, next_token, data)
