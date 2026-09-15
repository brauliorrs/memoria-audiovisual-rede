"""VAL-009 readiness helpers. No collection, storage, freeze or promotion here.

Inputs must preserve requested AND final URLs and point to raw captured evidence.
Legacy discovery reports do not satisfy this contract: never infer a lost URL.
Selection is completed before the candidate is called. Returned predictions are
private material; this development API does not authorize an independent run.
"""

from copy import deepcopy
from hashlib import sha256
from urllib.parse import urlsplit, urlunsplit

from .surface_typing_v23_candidate import (
    SURFACE_TYPING_CANDIDATE_VERSION,
    classify_surface_type_candidate,
)


HUMAN_FIELDS = frozenset({
    "review_unit_id", "entity_id", "page_url", "root_url", "parent_url",
    "snapshot_reference", "observed_at", "human_surface_type",
    "human_is_item_level", "human_access_state", "human_review_note",
    "reviewer_id", "reviewed_at", "review_status",
})


def url_identity(url: str) -> str:
    """Conservative identity: preserve path case and query bytes/order."""
    if not isinstance(url, str) or not url or any(c.isspace() for c in url):
        raise ValueError("Expected an absolute HTTP(S) URL")
    parts = urlsplit(url)
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        raise ValueError("Expected an absolute HTTP(S) URL")
    if parts.username is not None or parts.password is not None:
        raise ValueError("Credential-bearing URLs are forbidden")
    scheme, host, port = parts.scheme.lower(), parts.hostname.lower(), parts.port
    if ":" in host:
        host = f"[{host}]"
    if port is not None and (scheme, port) not in {("http", 80), ("https", 443)}:
        host += f":{port}"
    return urlunsplit((scheme, host, parts.path, parts.query, ""))


def select_review_units(reports: dict, *, protocol: dict, exclusion: dict) -> dict:
    """Select deterministically without invoking any classifier.

    reports maps each registered entity to root_url and pages in discovery order.
    Each page requires requested_url, url (final), snapshot_reference, fetched_at.
    Empty pages are allowed, absent reports are not. Audit all records, even caps.
    """
    entities = protocol["entities"]
    ids = [entry["entity_id"] for entry in entities]
    if len(ids) != len(set(ids)) or set(reports) != set(ids):
        raise ValueError("Reports must match every registered entity exactly")
    if set(ids) & set(protocol["excluded_entities"]):
        raise ValueError("Development entity in independent sample")
    blocked = {url_identity(url) for url in exclusion["urls"]}
    sampling = protocol["sampling"]
    selected, audit, seen = [], [], set()
    for entity in entities:
        entity_id, root = entity["entity_id"], entity["root_url"]
        report = reports[entity_id]
        if url_identity(report["root_url"]) != url_identity(root):
            raise ValueError(f"Unexpected root for {entity_id}")
        pages = report["pages"]
        if not isinstance(pages, list) or len(pages) > sampling["max_pages_per_entity"]:
            raise ValueError(f"Invalid discovery page count for {entity_id}")
        count = 0
        for index, page in enumerate(pages):
            for key in ("requested_url", "url", "snapshot_reference", "fetched_at"):
                if not isinstance(page.get(key), str) or not page[key].strip():
                    raise ValueError(f"Missing {key}: {entity_id} page {index}")
            keys = {url_identity(page["requested_url"]), url_identity(page["url"])}
            duplicate = bool(keys & seen)
            seen.update(keys)
            if keys & blocked:
                reason = "known_url"
            elif duplicate:
                reason = "duplicate"
            elif count >= sampling["max_review_units_per_entity"]:
                reason = "entity_cap"
            elif len(selected) >= sampling["max_review_units"]:
                reason = "global_cap"
            else:
                reason = "selected"
                digest = sha256(f"{entity_id}\n{root}\n{url_identity(page['url'])}".encode()).hexdigest()[:16]
                selected.append({
                    "review_unit_id": f"{entity_id}-surface-{digest}",
                    "entity_id": entity_id, "root_url": root,
                    "page": deepcopy(page),
                })
                count += 1
            audit.append({"entity_id": entity_id, "discovery_index": index,
                          "requested_url": page["requested_url"],
                          "page_url": page["url"], "reason": reason})
    entity_count = len({unit["entity_id"] for unit in selected})
    sufficient = (len(selected) >= sampling["minimum_review_units"]
                  and entity_count >= sampling["minimum_entities"])
    return {"status": "sufficient" if sufficient else "insufficient_sample",
            "protocol_id": protocol["protocol_id"], "units": selected,
            "entity_count": entity_count, "audit": audit}


def build_development_artifacts(reports: dict, *, protocol: dict, exclusion: dict) -> tuple[dict, dict]:
    """Exercise readiness on synthetic/known data; never label this independent.

    Returns (blinded_queue, private_predictions). No combined file or logging.
    The caller must separately secure predictions; no publication is performed.
    """
    if protocol["candidate_version"] != SURFACE_TYPING_CANDIDATE_VERSION:
        raise ValueError("Candidate version mismatch")
    if set(protocol["blinding"]["human_queue_allowed_fields"]) != HUMAN_FIELDS:
        raise ValueError("Human queue contract mismatch")
    selection = select_review_units(reports, protocol=protocol, exclusion=exclusion)
    metadata = {
        "protocol_id": protocol["protocol_id"],
        "protocol_version": protocol["protocol_version"],
        "candidate_version": SURFACE_TYPING_CANDIDATE_VERSION,
        "sample_role": "development_readiness_only",
        "is_independent_validation_sample": False,
        "m4_scaling_allowed": False,
        "selection_status": selection["status"],
    }
    queue = {**metadata, "units": []}
    private = {**metadata, "units": [], "selection_audit": selection["audit"]}
    if selection["status"] != "sufficient":
        return queue, private
    for unit in selection["units"]:
        page = unit["page"]
        human = {
            "review_unit_id": unit["review_unit_id"], "entity_id": unit["entity_id"],
            "page_url": page["url"], "root_url": unit["root_url"],
            "parent_url": page.get("parent_url"),
            "snapshot_reference": page["snapshot_reference"],
            "observed_at": page["fetched_at"],
            "human_surface_type": None, "human_is_item_level": None,
            "human_access_state": None, "human_review_note": None,
            "reviewer_id": None, "reviewed_at": None, "review_status": "pending",
        }
        queue["units"].append(human)
        media = page.get("media_urls", ())
        if not isinstance(media, (list, tuple)):
            raise ValueError("media_urls must be a list or tuple")
        decision = classify_surface_type_candidate(
            url=page["url"], root_url=unit["root_url"], title=page.get("title"),
            text=str(page.get("text") or ""),
            metadata_text=str(page.get("metadata_text") or ""),
            structured_text=str(page.get("structured_text") or ""),
            media_urls=tuple(str(value) for value in media),
            fetch_status=str(page.get("fetch_status") or "fetched"),
        )
        private["units"].append({
            "review_unit_id": unit["review_unit_id"], "entity_id": unit["entity_id"],
            "page_url": page["url"],
            "predicted_surface_type": decision.surface_type,
            "predicted_item_level": decision.is_item_level,
            "prediction_confidence": decision.confidence,
            "prediction_evidence": decision.evidence,
            "predicted_access_state": decision.access_state,
            "predicted_access_evidence": decision.access_evidence,
        })
    return queue, private
