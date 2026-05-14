from .config import (
    INA_COLLECTIONS_URL,
    INA_DATA_URL,
    INA_HOME_URL,
    INA_INSTITUTION_URL,
    INA_MADELEN_URL,
    INA_MEDIACLIP_URL,
    INA_MEDIA_MAGAZINE_URL,
    INA_NEWS_URL,
    INA_PODCASTS_URL,
)
from .crawler import collect_sites_dataset, slugify
from .geography import country_to_continent, normalize_country


INA_REPOSITORY_CODE = "FR-INA"
INA_ARCHIVE_TYPE = "National audiovisual archive"
INA_COUNTRY = normalize_country("France")
INA_SEED_URLS = [
    INA_INSTITUTION_URL,
    INA_COLLECTIONS_URL,
    INA_DATA_URL,
    INA_NEWS_URL,
    INA_MEDIA_MAGAZINE_URL,
    INA_MADELEN_URL,
    INA_PODCASTS_URL,
    INA_MEDIACLIP_URL,
]


def collect_ina_institutions():
    institution_name = "Institut national de l'audiovisuel (INA)"
    return [
        {
            "institution": institution_name,
            "slug": slugify(institution_name),
            "country": INA_COUNTRY,
            "continent": country_to_continent(INA_COUNTRY),
            "repository_code": INA_REPOSITORY_CODE,
            "archive_type": INA_ARCHIVE_TYPE,
            "ina_detail_url": INA_INSTITUTION_URL,
            "external_url": INA_HOME_URL,
            "seed_urls": INA_SEED_URLS,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def enrich_rows(rows, entry_lookup):
    enriched_rows = []
    for row in rows:
        extra = entry_lookup.get(row.get("slug"), {})
        merged = row.copy()
        merged["repository_code"] = extra.get("repository_code", "")
        merged["ina_detail_url"] = extra.get("ina_detail_url", "")
        merged["archive_type"] = extra.get("archive_type", "")
        merged["content_available_in_source"] = extra.get("content_available_in_source", True)
        merged["website_available"] = extra.get("website_available", False)
        enriched_rows.append(merged)
    return enriched_rows


def collect_ina_dataset():
    institutions = collect_ina_institutions()
    site_entries = []
    for record in institutions:
        site_entries.append(
            {
                "name": record["institution"],
                "slug": record["slug"],
                "country": record.get("country", ""),
                "continent": record.get("continent", ""),
                "external_url": record.get("external_url", ""),
                "detail_url": record.get("ina_detail_url", ""),
                "seed_urls": record.get("seed_urls", []),
            }
        )

    rows_summary, rows_video_links, rows_internal_pages = collect_sites_dataset(site_entries)
    entry_lookup = {
        record["slug"]: {
            "repository_code": record.get("repository_code", ""),
            "ina_detail_url": record.get("ina_detail_url", ""),
            "archive_type": record.get("archive_type", ""),
            "content_available_in_source": record.get("content_available_in_source", True),
            "website_available": record.get("website_available", False),
        }
        for record in institutions
    }

    return (
        institutions,
        enrich_rows(rows_summary, entry_lookup),
        enrich_rows(rows_video_links, entry_lookup),
        enrich_rows(rows_internal_pages, entry_lookup),
    )


__all__ = [
    "collect_ina_dataset",
    "collect_ina_institutions",
]
