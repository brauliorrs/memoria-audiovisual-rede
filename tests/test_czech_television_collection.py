import json
import unittest
from unittest.mock import Mock, patch

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.crawler import classify_platform, is_probably_video_link
from memoria_audiovisual.czech_television import (
    CZECH_TELEVISION_INSTITUTION_NAME,
    collect_czech_television_dataset,
    collect_czech_television_institutions,
    parse_czech_television_catalog_page,
    parse_czech_television_episode_page,
    parse_czech_television_show_page,
)


def next_data_html(data):
    return f'<html><head><script id="__NEXT_DATA__" type="application/json">{json.dumps(data)}</script></head></html>'


class CzechTelevisionCollectionTests(unittest.TestCase):
    def test_collect_institutions_declares_czech_public_broadcaster(self):
        institutions = collect_czech_television_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["institution"], CZECH_TELEVISION_INSTITUTION_NAME)
        self.assertEqual(institutions[0]["country"], "Czech Republic")
        self.assertEqual(institutions[0]["continent"], "Europe")
        self.assertTrue(institutions[0]["content_available_in_source"])

    def test_parse_catalog_page_keeps_playable_shows(self):
        html = next_data_html(
            {
                "props": {
                    "pageProps": {
                        "data": {
                            "category": {
                                "programmeFind": {
                                    "items": [
                                        {
                                            "id": "151",
                                            "slug": "151-kultura",
                                            "title": "Kulturní pořad",
                                            "isPlayable": True,
                                            "flatGenres": [{"title": "Kultura"}],
                                        },
                                        {"id": "999", "slug": "999-nehratelne", "title": "Sem vídeo", "isPlayable": False},
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        )

        records = parse_czech_television_catalog_page(html, "Cultura")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["show_slug"], "151-kultura")
        self.assertIn("Kultura", records[0]["genres"])

    def test_parse_show_page_extracts_episode_urls(self):
        html = '<a href="/porady/151-kultura/226411033400703/">episódio</a>'

        urls = parse_czech_television_show_page(html, "151-kultura")

        self.assertEqual(urls, ["https://www.ceskatelevize.cz/porady/151-kultura/226411033400703/"])

    def test_parse_episode_page_requires_playable_media(self):
        html = next_data_html(
            {
                "props": {
                    "pageProps": {
                        "data": {
                            "mediaMeta": {
                                "id": "226411033400703",
                                "title": "Zahájení festivalu",
                                "description": "Cobertura cultural",
                                "durationText": "137 min",
                                "year": "2026",
                                "uploadDate": "2026-07-07T07:45:01.000Z",
                                "isPlayable": True,
                                "countriesOfOrigin": [{"title": "Česko"}],
                                "show": {
                                    "title": "ČT na MFF Karlovy Vary",
                                    "flatGenres": [{"title": "Kultura"}, {"title": "Festival"}],
                                },
                            }
                        }
                    }
                }
            }
        )

        record = parse_czech_television_episode_page(
            html,
            "https://www.ceskatelevize.cz/porady/151-kultura/226411033400703/",
            {"category_label": "Cultura"},
        )

        self.assertEqual(record["record_id"], "226411033400703")
        self.assertEqual(record["date"], "2026-07-07")
        self.assertIn("mediaMeta.isPlayable=True", record["description"])
        self.assertTrue(record["embedded"])

    def test_current_public_episode_schema_requires_true_and_identifier(self):
        episode_url = "https://www.ceskatelevize.cz/porady/12701251153-kultura/226411033400703/"

        def html_for(episode, legacy=None):
            data = {"episode": episode}
            if legacy is not None:
                data["mediaMeta"] = legacy
            return next_data_html({"props": {"pageProps": {"data": data}}})

        observed = {
            "id": "episode-2026",
            "idec": "226411033400703",
            "title": "Kulturní archiv",
            "description": "Public description",
            "year": "2026",
            "uploadDate": "2026-11-11T10:00:00Z",
            "durationText": "42 min",
            "isPlayable": True,
            "show": {"title": "Kultura"},
        }
        record = parse_czech_television_episode_page(
            html_for(observed), episode_url, {"category_label": "Cultura"}
        )
        self.assertEqual(record["record_id"], "episode-2026")
        self.assertEqual(record["title"], "Kulturní archiv")
        self.assertEqual(record["date"], "2026-11-11")
        self.assertEqual(record["page_url"], episode_url)
        self.assertIn("episode.isPlayable=True", record["description"])
        self.assertNotIn("mediaMeta.isPlayable=True", record["description"])

        invalid = [
            {**observed, "isPlayable": False},
            {k: v for k, v in observed.items() if k != "isPlayable"},
            {**observed, "isPlayable": "true"},
            {**observed, "id": "", "idec": ""},
        ]
        for sample in invalid:
            with self.subTest(episode=sample):
                self.assertEqual(
                    parse_czech_television_episode_page(html_for(sample), episode_url), {}
                )

        # Conflicting public availability signals must fail closed.
        self.assertEqual(
            parse_czech_television_episode_page(
                html_for(observed, {"id": "legacy", "isPlayable": False}),
                episode_url,
            ),
            {},
        )

    def test_collect_dataset_with_mocked_fetch_materializes_episode(self):
        catalog_html = next_data_html(
            {
                "props": {
                    "pageProps": {
                        "data": {
                            "category": {
                                "programmeFind": {
                                    "items": [
                                        {
                                            "id": "151",
                                            "slug": "151-kultura",
                                            "title": "Kulturní pořad",
                                            "isPlayable": True,
                                            "flatGenres": [{"title": "Kultura"}],
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        )
        episode_html = next_data_html(
            {
                "props": {
                    "pageProps": {
                        "data": {
                            "mediaMeta": {
                                "id": "226411033400703",
                                "title": "Zahájení festivalu",
                                "description": "Cobertura cultural",
                                "durationText": "137 min",
                                "year": "2026",
                                "isPlayable": True,
                                "show": {"title": "Kulturní pořad", "flatGenres": [{"title": "Kultura"}]},
                            }
                        }
                    }
                }
            }
        )

        def fake_fetch(url):
            if "/kategorie/" in url:
                return Mock(status_code=200, url=url, text=catalog_html)
            if url.endswith("/151-kultura/"):
                return Mock(
                    status_code=200,
                    url=url,
                    text='<a href="/porady/151-kultura/226411033400703/">episódio</a>',
                )
            if url.endswith("/226411033400703/"):
                return Mock(status_code=200, url=url, text=episode_html)
            return Mock(status_code=200, url=url, text="<html></html>")

        with patch("memoria_audiovisual.czech_television._fetch", side_effect=fake_fetch):
            institutions, summary, video_links, internal_pages = collect_czech_television_dataset()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(len(video_links), 1)
        self.assertEqual(summary[0]["integrity_status"], "instavel")
        self.assertEqual(summary[0]["coverage_scope"], "bounded_mvp")
        self.assertEqual(summary[0]["accessible_records_count"], 1)
        self.assertEqual(summary[0]["validated_sample_count"], 0)
        self.assertFalse(summary[0]["corpus_complete"])
        self.assertFalse(summary[0]["enumeration_complete"])
        self.assertEqual(summary[0]["video_links_found_total"], 1)
        self.assertTrue(any(page["embedded_signals"] == 1 for page in internal_pages))

    def test_collect_dataset_with_current_public_episode_shape(self):
        catalogue = '<a href="/porady/12701251153-kultura/">Kultura</a>'
        show_page = '<a href="/porady/12701251153-kultura/226411033400703/">Episódio</a>'
        episode_html = next_data_html({
            "props": {"pageProps": {"data": {
                "episode": {
                    "id": "episode-public-id",
                    "idec": "226411033400703",
                    "title": "Kulturní archiv",
                    "isPlayable": True,
                    "show": {"title": "Kultura"},
                }
            }}}
        })

        def fake_fetch(url):
            if "/kategorie/" in url:
                return Mock(status_code=200, url=url, text=catalogue)
            if url.endswith("/12701251153-kultura/"):
                return Mock(status_code=200, url=url, text=show_page)
            if url.endswith("/226411033400703/"):
                return Mock(status_code=200, url=url, text=episode_html)
            return Mock(status_code=200, url=url, text="<html></html>")

        with patch("memoria_audiovisual.czech_television._fetch", side_effect=fake_fetch):
            _, _, links, pages = collect_czech_television_dataset()
        self.assertEqual(len(links), 1)
        self.assertEqual(
            links[0]["video_link"],
            "https://www.ceskatelevize.cz/porady/12701251153-kultura/226411033400703/",
        )
        self.assertIn("episode.isPlayable=True", links[0]["video_description"])
        self.assertTrue(any(p["embedded_signals"] == 1 for p in pages))

    def test_html_catalog_fallback_only_discovers_candidates(self):
        html = """
        <main>
          <a href="/porady/151-kultura/">Cultural archive</a>
          <a href="/porady/151-kultura/">Duplicate</a>
          <a href="/porady/261-filmovy-archiv/">Film archive</a>
          <a href="https://external.example/porady/1234-foreign">External</a>
          <a href="/porady/not-valid/">Invalid</a>
        </main>
        """
        candidates = parse_czech_television_catalog_page(html, "Cultura")
        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0]["show_slug"], "151-kultura")
        self.assertEqual(candidates[1]["show_slug"], "261-filmovy-archiv")
        self.assertTrue(all(not c["is_playable"] for c in candidates))
        self.assertTrue(all(c["discovery_only"] for c in candidates))

    def test_catalog_fallback_does_not_materialize_unverified_video(self):
        html = '<a href="/porady/151-kultura/">Cultura</a>'

        def fake_fetch(url):
            if "/kategorie/" in url:
                return Mock(status_code=200, url=url, text=html)
            if url.endswith("/151-kultura/"):
                return Mock(status_code=200, url=url,
                            text='<a href="/porady/151-kultura/226411033400703/">Episode</a>')
            # mediaMeta.isPlayable must be explicitly true; plain HTML is not enough
            return Mock(status_code=200, url=url, text="<main>Unverified episode</main>")

        with patch("memoria_audiovisual.czech_television._fetch", side_effect=fake_fetch):
            _, summary, video_links, _ = collect_czech_television_dataset()
        self.assertEqual(video_links, [])
        self.assertEqual(summary[0]["integrity_status"], "instavel")

    def test_platform_theme_and_access_are_classified(self):
        url = "https://www.ceskatelevize.cz/porady/151-kultura/226411033400703/"
        row = {"platform": "Česká televize iVysílání", "video_link": url, "video_subject": "Kultura; Festival"}

        self.assertEqual(classify_platform(url), "Česká televize iVysílání")
        self.assertTrue(is_probably_video_link(url, "Česká televize iVysílání"))
        self.assertEqual(classify_access_surface(row), "Arquivo televisivo público em iVysílání")
        self.assertEqual(infer_video_theme(row), "Cultura, artes e memória pública")


if __name__ == "__main__":
    unittest.main()
