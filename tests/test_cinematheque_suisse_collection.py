import unittest

import pandas as pd

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.cinematheque_suisse import (
    build_cinematheque_suisse_search_url,
    collect_cinematheque_suisse_dataset,
    collect_cinematheque_suisse_institutions,
    memobase_record_to_video_row,
)
from memoria_audiovisual.public_access_index import RESTRICTED_RECORD_STATUS, classify_record_public_access


def fake_record(record_id="mbr:csa-001-1", title="Film de fiction suisse"):
    return {
        "@id": record_id,
        "@type": "rico:Record",
        "type": "Film",
        "title": title,
        "abstract": ["Un film de fiction conservé par la Cinémathèque suisse."],
        "issued": {"@type": "rico:DateRange", "normalizedDateValue": "1957"},
        "hasGenre": [{"prefLabel": "film de fiction"}],
        "hasInstantiation": [
            {
                "@id": "mbdo:csa-001-1-1",
                "@type": "rico:Instantiation",
                "type": "digitalObject",
                "mediaLocation": "remote",
                "locator": "https://prod.media.memobase.ch/memo/csa-001-1-1",
                "isOrWasRegulatedBy": [
                    {"type": "access", "name": "onsite"},
                    {"type": "usage", "name": "In Copyright (InC)"},
                ],
            },
            {
                "@id": "mbdo:csa-001-1-1/derived",
                "@type": "rico:Instantiation",
                "type": "digitalObject",
                "locator": "https://prod.media.memobase.ch/memo/csa-001-1-1-poster",
            },
        ],
    }


def fake_fetcher(url):
    if "institution/csa" in url:
        return {"@id": "https://memobase.ch/institution/csa", "nameFr": "Cinémathèque suisse"}
    if "recordSet/csa-001" in url:
        return {"@id": "https://memobase.ch/recordSet/csa-001", "titleFr": "Collection film de la Cinémathèque suisse"}
    if "advancedSearch" in url:
        return {
            "hydra:totalItems": 2,
            "hydra:member": [
                fake_record("mbr:csa-001-1", "Film de fiction suisse"),
                fake_record("mbr:csa-001-2", "Deuxième film suisse"),
            ],
        }
    raise AssertionError(f"URL inesperada: {url}")


class CinemathequeSuisseCollectionTests(unittest.TestCase):
    def test_collect_institutions_declares_single_archive(self):
        institutions = collect_cinematheque_suisse_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["institution"], "Cinémathèque suisse")
        self.assertTrue(institutions[0]["content_available_in_source"])

    def test_search_url_targets_memobase_film_recordset(self):
        url = build_cinematheque_suisse_search_url(offset=40)

        self.assertIn("record/advancedSearch", url)
        self.assertIn("type%3AFilm", url)
        self.assertIn("csa-001", url)
        self.assertIn("offset=40", url)

    def test_record_row_marks_onsite_authorized_access(self):
        institution = collect_cinematheque_suisse_institutions()[0]
        row = memobase_record_to_video_row(institution, fake_record())

        self.assertEqual(row["platform"], "Memobase LOD API")
        self.assertIn("onsite", row["video_description"])
        self.assertIn("In Copyright", row["video_description"])
        self.assertEqual(infer_video_theme(row), "Ficção cinematográfica")
        self.assertEqual(
            classify_access_surface(row),
            "Metadados audiovisuais públicos com mídia local/autorizada",
        )
        self.assertEqual(classify_record_public_access(pd.Series(row)), RESTRICTED_RECORD_STATUS)

    def test_collect_dataset_materializes_records_without_mixing_aggregator_category(self):
        institutions, summary, links, internal_pages = collect_cinematheque_suisse_dataset(fetcher=fake_fetcher)

        self.assertEqual(len(institutions), 1)
        self.assertEqual(len(links), 2)
        self.assertEqual(summary[0]["video_links_found_total"], 2)
        self.assertIn("Memobase", summary[0]["warning"])
        self.assertGreaterEqual(len(internal_pages), 3)


if __name__ == "__main__":
    unittest.main()
