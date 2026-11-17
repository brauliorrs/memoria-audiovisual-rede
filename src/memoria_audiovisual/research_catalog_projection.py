"""Safe presentation projection for the public MAR cross-corpus catalogue.

Only call this with rows/manifest returned by load_published_kavi_rows().
No collection, network, media playback, credential access or database writes.
Publication of an index is not per-record scientific/rights verification.
"""
from __future__ import annotations

KAVI_PARTIAL_STATUS = "Índice KAVI/Finna publicado · parcial · ficha não revisada"
APPROVED_METADATA_STATUS = "Metadados aprovados para publicação · mídia não verificada"
LEGACY_STATUS = "Catálogo histórico · revisão por ficha não informada"


def project_kavi_search_records(
    rows: list[dict], manifest: dict, *, corpus_label: str,
    institution_label: str, category_label: str,
) -> list[dict]:
    """Show origin-record links once, only when the partial index was admitted.

    The cryptographic verification and link-level checks belong to
    load_published_kavi_rows(). This formatter is an additional fail-closed
    guard, NOT an alternate publication path.
    """
    if not rows:
        return []
    if (
        not isinstance(manifest, dict)
        or manifest.get("status") != "published_partial_metadata"
        or manifest.get("coverage_status") != "partial"
        or manifest.get("metadata_publication_approved") is not True
        or manifest.get("corpus_activation") is not False
        or manifest.get("media_downloaded") is not False
        or manifest.get("viewing_at_origin_only") is not True
        or manifest.get("record_count") != len(rows)
    ):
        return []

    projected = []
    ids = set()
    links = set()
    for row in rows:
        rid = row.get("source_record_id", "")
        origin = row.get("source_record_url", "")
        if (
            not isinstance(rid, str) or not rid
            or not isinstance(origin, str) or not origin
            or rid in ids or origin in links
            or row.get("video_link") != origin
            or row.get("record_review_status") != "unreviewed"
            or row.get("media_access_status") != "unverified"
            or row.get("media_rights_status") != "not_verified"
            or row.get("source_service") != "finna_api"
        ):
            # A repeated or inconsistent row means the entire candidate
            # projection is rejected, rather than hiding anomalies.
            return []
        ids.add(rid)
        links.add(origin)
        r = dict(row)
        r.update({
            "institution": institution_label,
            "corpus": corpus_label + " (índice parcial)",
            "unidade": institution_label,
            "slug": "fiaf-kavi",
            "categoria_analitica": category_label + " · metadados",
            "country": "Finland",
            "continent": "Europe",
            "platform": "Finna / Elonet",
            "video_title_display": row.get("video_title", ""),
            "video_date_display": row.get("year", ""),
            "video_theme": row.get("genres") or row.get("subjects", ""),
            "access_surface": "Ficha institucional externa; reprodução não verificada",
            "access_regime": "Metadados públicos; mídia/direitos não avaliados",
            "source_page_url": origin,
            "catalog_coverage": "partial",
            "catalog_observed_on": manifest.get("observed_on", ""),
            "documentary_status": KAVI_PARTIAL_STATUS,
            "scientific_corpus_validated": False,
        })
        projected.append(r)
    return projected


def only_verified_public_playback(frame):
    """Filter only independently declared verified public playback, not links.

    An HTTPS source record URL by itself never asserts film playability.
    """
    if "media_access_status" not in frame.columns or "video_link" not in frame.columns:
        return frame.iloc[0:0].copy()
    valid = (
        frame["media_access_status"].fillna("").eq("verified_public_playback")
        & frame["video_link"].fillna("").astype(str).str.strip().ne("")
    )
    return frame.loc[valid].copy()
