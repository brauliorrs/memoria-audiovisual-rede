"""Guard MAR's link-only delivery and forbid in-app audiovisual playback."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

from memoria_audiovisual.external_links import (
    choose_origin_destination,
    is_direct_media_asset,
    public_external_url,
)
from memoria_audiovisual.i18n import translate_ui_text

APP = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"


class ExternalLinkTests(unittest.TestCase):
    def test_public_http_and_https_links_are_preserved(self):
        urls = (
            "https://elonet.finna.fi/Record/kavi.elonet_elokuva_1611548",
            "https://www.finna.fi/Record/kavi.elonet_elokuva_1611548?lang=en",
            "https://www.youtube.com/watch?v=abcd",
            "https://vimeo.com/123456",
            "http://legacy.example.org/catalog/film/1",
        )
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(public_external_url(url), url)

    def test_legacy_urls_with_spaces_are_encoded_for_navigation_only(self):
        examples = (
            "https://videos.far-asso.fr/film/CREAV_02_F_01 Bis.mp4",
            "https://example.org/films/a film?lang=pt&title=meu filme",
        )
        for original in examples:
            with self.subTest(original=original):
                destination = public_external_url(original)
                self.assertIsNotNone(destination)
                self.assertEqual(destination, original.replace(" ", "%20"))
                # Source metadata has not been mutated, just a derived link.
                self.assertIn(" ", original)
                self.assertNotIn(" ", destination)

    def test_raw_media_urls_are_not_visitor_destinations(self):
        media = (
            "https://video.archive.example/film/record%20A.mp4",
            "https://video.archive.example/stream/master.m3u8?token=abc",
            "https://video.archive.example/a.MKV",
            "https://video.archive.example/clip.webm?quality=high",
        )
        home = "https://catalog.archive.example/collection"
        for raw in media:
            with self.subTest(raw=raw):
                self.assertTrue(is_direct_media_asset(raw))
                result = choose_origin_destination(raw, home)
                self.assertEqual(result.url, home)
                self.assertEqual(result.kind, "institution_home")
                no_fallback = choose_origin_destination(raw)
                self.assertIsNone(no_fallback.url)
                self.assertEqual(no_fallback.kind, "unavailable")

    def test_cna_delivery_endpoints_without_extension_are_not_record_pages(self):
        # Regression for real CNA output rows reviewed in PR #75.
        examples = (
            "https://cna.kiss.lu/getMedium/d18fac130ee9f74d2c035d491b946467",
            "https://cnasearch.public.lu/wwwopac.ashx?value=AV015929.mp4",
            "https://cnasearch.public.lu/wwwopac.ashx?value=AV015929%2Emp4",
            "https://cnasearch.public.lu/wwwopac.ashx?value=AV015929.mp4&lang=fr",
        )
        source_catalog = "https://cnasearch.public.lu/searchprofiles/run/4/film"
        for url in examples:
            with self.subTest(url=url):
                self.assertTrue(is_direct_media_asset(url))
                destination = choose_origin_destination(url, source_catalog)
                self.assertEqual(destination.url, source_catalog)
                self.assertEqual(destination.kind, "institution_home")
                self.assertIsNone(choose_origin_destination(url).url)

    def test_explicit_mime_evidence_blocks_extensionless_unknown_host(self):
        streaming_endpoint = "https://media.example.org/stream/opaque-id"
        institution_page = "https://archive.example.org/catalog"
        self.assertFalse(is_direct_media_asset(streaming_endpoint))
        self.assertTrue(is_direct_media_asset(streaming_endpoint, "video/mp4"))
        self.assertTrue(is_direct_media_asset(streaming_endpoint, "video/mp4; charset=binary"))
        self.assertTrue(is_direct_media_asset(streaming_endpoint, "application/dash+xml"))
        result = choose_origin_destination(
            streaming_endpoint,
            institution_page,
            media_type="video/mp4",
        )
        self.assertEqual(result.url, institution_page)
        self.assertEqual(result.kind, "institution_home")

    def test_search_queries_containing_media_text_are_not_files(self):
        link = "https://elonet.finna.fi/Search/Results?lookfor=example.mp4&type=AllFields"
        self.assertFalse(is_direct_media_asset(link))
        result = choose_origin_destination(link, "https://elonet.finna.fi/")
        self.assertEqual(result.url, link)
        self.assertEqual(result.kind, "record_or_platform")

    def test_infomaniak_extensionless_vod_is_not_public_item_page(self):
        raw = "https://play.vod2.infomaniak.com/single/abcdef0123456"
        home = "https://autrefois.example.org/catalogue"
        self.assertTrue(is_direct_media_asset(raw))
        dest = choose_origin_destination(raw, home)
        self.assertEqual(dest.url, home)
        self.assertEqual(dest.kind, "institution_home")

    def test_unrecognized_extensionless_urls_fail_closed(self):
        raw = "https://video.unknown.example.org/stream/opaque-token"
        fallback = "https://archive.example.org/catalog"
        self.assertFalse(is_direct_media_asset(raw))
        result = choose_origin_destination(raw, fallback)
        self.assertEqual(result.url, fallback)
        self.assertEqual(result.kind, "institution_home")
        self.assertIsNone(choose_origin_destination(raw).url)

    def test_unknown_record_path_does_not_masquerade_as_verified_web_item(self):
        raw = "https://streaming.example.org/record/opaque-media-id"
        fallback = "https://archive.example.org/catalog"
        self.assertEqual(
            choose_origin_destination(raw, fallback).url, fallback
        )

    def test_memobase_digital_object_redirects_to_original_record(self):
        # Cinémathèque suisse: a technical digitalObject is not the public
        # media page; the row's partner_site is a record URL on Memobase.
        raw = "https://prod.media.memobase.ch/memo/csa-001-1000012550-1"
        record = "https://api.memobase.ch/record/csa-001-1000012550?format=Json"
        collection = "https://api.memobase.ch/recordSet/csa-001?format=Json"
        self.assertTrue(is_direct_media_asset(raw))
        result = choose_origin_destination(
            raw, collection, record_page_url=record
        )
        self.assertEqual(
            result.url, "https://memobase.ch/object/csa-001-1000012550"
        )
        self.assertEqual(result.kind, "record_or_platform")
        # JSON API recordSet is not a visitor-facing catalog page.
        self.assertEqual(
            choose_origin_destination(raw, collection).kind, "unavailable"
        )

    def test_memobase_mapping_is_strictly_limited_to_documented_record_ids(self):
        raw = "https://prod.media.memobase.ch/memo/opaque-video-locator"
        catalog = "https://institution.example.org/catalog"
        rejected = (
            "https://api.memobase.ch/record/search?q=hello",
            "https://api.memobase.ch/recordSet/csa-001?format=Json",
            "https://evil.example.org/record/csa-001-123",
        )
        for technical in rejected:
            with self.subTest(technical=technical):
                destination = choose_origin_destination(
                    raw, catalog, record_page_url=technical
                )
                self.assertEqual(destination.url, catalog)
                self.assertEqual(destination.kind, "institution_home")

    def test_cinememoire_item_notice_takes_precedence_over_collection_page(self):
        raw = "https://cinememoire.net/streaming/cinememoire/sequences/001-011-Streaming.mp4"
        item = "https://cinememoire.net/notice?num_seq=2883"
        catalog = "https://cinememoire.net/archives-cinememoire-ligne/archives-cinememoire-ligne"
        result = choose_origin_destination(
            raw, catalog, record_page_url=item
        )
        self.assertEqual(result.url, item)
        self.assertEqual(result.kind, "record_or_platform")

    def test_generic_partner_search_page_is_not_misrepresented_as_item(self):
        raw = "https://cna.kiss.lu/getMedium/d18fac130ee9f74d2c035d491b946467"
        search = "https://cnasearch.public.lu/searchprofiles/run/4/film"
        collection = "https://cna.public.lu/en.html"
        result = choose_origin_destination(
            raw, collection, record_page_url=search
        )
        self.assertEqual(result.url, search)
        self.assertEqual(result.kind, "institution_home")

    def test_bbc_dr_and_filmoteca_item_pages_from_real_corpora(self):
        # These URLs are copied from the repository's catalogued item rows,
        # not invented generic /video/<id> examples.
        cases = (
            ("https://www.bbc.co.uk/videos/c39rz1jv9jpo",
             "https://www.bbc.co.uk/archive"),
            ("https://www.dr.dk/drtv/program/de-udstillede_593691",
             "https://www.dr.dk/drtv/gensyn"),
            ("https://filmo.platfo.es/content/apuntes-para-una-tesis-doctoral",
             "https://filmo.platfo.es/pages/home"),
        )
        for item, fallback in cases:
            with self.subTest(item=item):
                chosen = choose_origin_destination(item, fallback)
                self.assertEqual(chosen.url, item)
                self.assertEqual(chosen.kind, "record_or_platform")
                self.assertFalse(is_direct_media_asset(item))

    def test_collector_specific_paths_not_generalized_to_media_routes(self):
        cases = (
            ("https://www.bbc.co.uk/videos/c39rz1jv9jpo/stream",
             "https://www.bbc.co.uk/archive"),
            ("https://www.bbc.co.uk/videos/download",
             "https://www.bbc.co.uk/archive"),
            ("https://www.dr.dk/drtv/program/de-udstillede_593691/embed",
             "https://www.dr.dk/drtv/gensyn"),
            ("https://www.dr.dk/drtv/program/download",
             "https://www.dr.dk/drtv/gensyn"),
            ("https://filmo.platfo.es/content/download",
             "https://filmo.platfo.es/pages/home"),
            ("https://filmo.platfo.es/content/a-film/stream",
             "https://filmo.platfo.es/pages/home"),
            ("https://evil.example.org/videos/c39rz1jv9jpo",
             "https://www.bbc.co.uk/archive"),
        )
        for item, fallback in cases:
            with self.subTest(item=item):
                chosen = choose_origin_destination(item, fallback)
                self.assertEqual(chosen.kind, "institution_home")
                self.assertEqual(chosen.url, fallback)

    def test_all_saved_bbc_dr_and_filmo_work_urls_remain_visitor_pages(self):
        import csv

        examples = (
            "bbc_links_video.csv",
            "dr_links_video.csv",
            "filmoteca_espanola_links_video.csv",
        )
        root = APP.parents[0] / "data" / "output"
        for filename in examples:
            with self.subTest(corpus=filename):
                with (root / filename).open(encoding="utf-8-sig", newline="") as fh:
                    rows = list(csv.DictReader(fh))
                self.assertGreater(len(rows), 0)
                for row in rows:
                    url = row["video_link"]
                    chosen = choose_origin_destination(
                        url, row.get("partner_site")
                    )
                    self.assertEqual(
                        (chosen.url, chosen.kind),
                        (public_external_url(url), "record_or_platform"),
                        msg=f"permalink rejected for corpus {filename}",
                    )

    def test_stable_gosfilmofond_and_iwm_item_permalink(self):
        sources = (
            "https://gosfilmofond.ru/films/12345/",
            "https://film.iwmcollections.org.uk/record/12345",
        )
        for source in sources:
            with self.subTest(source=source):
                result = choose_origin_destination(
                    source, "https://institution.example.org/catalogue"
                )
                self.assertEqual(result.url, source)
                self.assertEqual(result.kind, "record_or_platform")

    def test_eye_filmarchiv_and_duesseldorf_item_pages_remain_specific(self):
        # Examples are based on archived metadata from each active collector.
        pages = (
            "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/als-het-verleden",
            "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/and-a-table",
            "https://filmdatabase.eyefilm.nl/en/node/12345",
            "https://www.filmarchiv.at/de/filmarchiv-on/video/f_0302R9oBXXu9uujZBKJCmq",
            "https://emuseum.duesseldorf.de/objects/383018/besuch-einer-dusseldorfer-delegation-bei-der-steubenparade",
        )
        for item in pages:
            with self.subTest(item=item):
                self.assertEqual(
                    choose_origin_destination(
                        item, "https://institution.example.org/collection"
                    ).url,
                    item,
                )
                self.assertEqual(
                    choose_origin_destination(item).kind,
                    "record_or_platform",
                )

    def test_eye_filmarchiv_and_duesseldorf_technical_routes_stay_blocked(self):
        invalid = (
            "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/all/all",
            "https://filmdatabase.eyefilm.nl/en/node/1234/stream",
            "https://filmdatabase.eyefilm.nl/api/records/123",
            "https://www.filmarchiv.at/de/filmarchiv-on/video/f_0302R9oBXXu9uujZBKJCmq/stream",
            "https://www.filmarchiv.at/de/filmarchiv-on/video/master.m3u8",
            "https://emuseum.duesseldorf.de/objects/383018/stream",
            "https://emuseum.duesseldorf.de/objects/383018/besuch-einer-delegation/download",
        )
        fallback = "https://institution.example.org/collection"
        for raw in invalid:
            with self.subTest(raw=raw):
                selection = choose_origin_destination(raw, fallback)
                self.assertEqual(selection.url, fallback)
                self.assertEqual(selection.kind, "institution_home")

    def test_cinemateca_portuguesa_public_ficha_preserved(self):
        ficha = (
            "https://www.cinemateca.pt/Cinemateca-Digital/"
            "Ficha.aspx?obraid=12345&type=Video"
        )
        for link in (ficha, ficha.replace("www.cinemateca.pt", "cinemateca.pt")):
            with self.subTest(link=link):
                item = choose_origin_destination(
                    link, "https://www.cinemateca.pt/Cinemateca-Digital/video.aspx"
                )
                self.assertEqual(item.url, link)
                self.assertEqual(item.kind, "record_or_platform")

    def test_cinemateca_ficha_only_if_real_video_id_is_present(self):
        fallback = "https://www.cinemateca.pt/Cinemateca-Digital/video.aspx"
        for link in (
            "https://www.cinemateca.pt/Cinemateca-Digital/Ficha.aspx?obraid=abc&type=Video",
            "https://www.cinemateca.pt/Cinemateca-Digital/Ficha.aspx?obraid=123&type=Foto",
            "https://www.cinemateca.pt/Cinemateca-Digital/Ficha.aspx?type=Video",
        ):
            with self.subTest(link=link):
                result = choose_origin_destination(link, fallback)
                self.assertEqual(result.url, fallback)
                self.assertEqual(result.kind, "institution_home")

    def test_category_catalog_fallback_never_uses_final_crawl_url(self):
        tree = ast.parse(APP.read_text(encoding="utf-8-sig"))
        fn = next(
            n for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name == "render_category_tab"
        )
        fragment = ast.unparse(fn)
        self.assertIn("detail_field_by_corpus", fragment)
        self.assertIn("detail_url_field", fragment)
        self.assertNotIn('["corpus", "slug", "final_url"]', fragment)

    def test_ecpad_and_arkaader_public_item_pages_survive_redirect_policy(self):
        item_pages = (
            "https://archives.ecpad.fr/archives/consulter-les-archives-en-ligne?detail=123456",
            "https://arkaader.ee/landing/bc/rHczO7kKnl/abcdef1234",
        )
        for item_url in item_pages:
            with self.subTest(item_url=item_url):
                result = choose_origin_destination(
                    item_url, "https://institution.example.org/catalog"
                )
                self.assertEqual(result.url, item_url)
                self.assertEqual(result.kind, "record_or_platform")

    def test_ecpad_query_and_arkaader_embed_are_not_item_pages(self):
        fallback = "https://institution.example.org/catalog"
        unknown = (
            "https://archives.ecpad.fr/archives/consulter-les-archives-en-ligne?detail=abc",
            "https://archives.ecpad.fr/archives/consulter-les-archives-en-ligne",
            "https://arkaader.ee/embed/opaque-token",
            "https://arkaader.ee/api/broadcasts",
        )
        for url in unknown:
            with self.subTest(url=url):
                destination = choose_origin_destination(url, fallback)
                self.assertEqual(destination.url, fallback)
                self.assertEqual(destination.kind, "institution_home")

    def test_generic_wordpress_json_api_cannot_override_institution(self):
        raw = "https://play.vod2.infomaniak.com/single/abcdef0123456"
        api = "https://www.autrefoisgeneve.ch/wp-json/wp/v2/aiovg_videos"
        catalog = "https://www.autrefoisgeneve.ch/"
        result = choose_origin_destination(
            raw, catalog, record_page_url=api
        )
        self.assertEqual(result.url, catalog)
        self.assertEqual(result.kind, "institution_home")

    def test_known_cna_search_page_is_labeled_catalog_not_item(self):
        raw = "https://cna.kiss.lu/getMedium/d18fac130ee9f74d2c035d491b946467"
        search = "https://cnasearch.public.lu/searchprofiles/run/4/film"
        home = "https://cna.public.lu/en.html"
        result = choose_origin_destination(
            raw, home, record_page_url=search
        )
        self.assertEqual(result.url, search)
        self.assertEqual(result.kind, "institution_home")

    def test_visitor_video_views_derive_origin_but_exports_preserve_raw(self):
        # Exercise pure display builders separately from Streamlit boot.
        import pandas as pd

        tree = ast.parse(APP.read_text(encoding="utf-8-sig"))
        functions = (
            "build_visitor_origin_column",
            "build_category_video_display_df",
            "build_research_video_display_df",
        )
        picked = [
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name in functions
        ]
        self.assertEqual(len(picked), len(functions))
        isolated = ast.fix_missing_locations(
            ast.Module(body=picked, type_ignores=[])
        )
        env = {
            "pd": pd,
            "choose_origin_destination": choose_origin_destination,
            "public_external_url": public_external_url,
        }
        exec(compile(isolated, str(APP), "exec"), env)
        raw_media = "https://cna.kiss.lu/getMedium/d18fac130ee9f74d2c035d491b946467"
        search = "https://cnasearch.public.lu/searchprofiles/run/4/film"
        rows = pd.DataFrame([{
            "corpus": "CNA", "slug": "cna-luxembourg",
            "institution": "CNA", "partner_site": search,
            "video_link": raw_media, "source_page_url": "https://cna.public.lu/en.html",
            "video_title_display": "Film A", "country": "Luxembourg",
            "continent": "Europa",
        }])
        for fun in ("build_category_video_display_df",
                    "build_research_video_display_df"):
            with self.subTest(function=fun):
                fn = env[fun]
                public = fn(rows, visitor_facing=True)
                exported = fn(rows)
                self.assertEqual(public["Acessar na origem"].iloc[0], search)
                self.assertNotIn("link do vídeo", public.columns)
                self.assertEqual(exported["link do vídeo"].iloc[0], raw_media)
                self.assertNotIn("Acessar na origem", exported.columns)

    def test_all_video_result_tables_are_visitor_safe(self):
        # Category and cross-corpus views must explicitly request derived
        # safe URLs; the default raw view exists for metadata CSV export.
        tree = ast.parse(APP.read_text(encoding="utf-8-sig"))
        for function_name, builder in (
            ("render_category_tab", "build_category_video_display_df"),
            ("render_research_tab", "build_research_video_display_df"),
        ):
            fn = next(
                node for node in tree.body
                if isinstance(node, ast.FunctionDef)
                and node.name == function_name
            )
            calls = [
                node for node in ast.walk(fn)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == builder
            ]
            self.assertGreaterEqual(len(calls), 2)
            visitor_calls = [
                call for call in calls
                if any(
                    arg.arg == "visitor_facing" and isinstance(arg.value, ast.Constant)
                    and arg.value.value is True
                    for arg in call.keywords
                )
            ]
            self.assertGreaterEqual(
                len(visitor_calls), 1 if function_name == "render_category_tab" else 2
            )
        source = APP.read_text(encoding="utf-8-sig")
        self.assertIn('st.column_config.LinkColumn(localize_ui("Acessar na origem"))', source)

    def test_untrusted_partner_record_does_not_override_safe_catalog(self):
        raw = "https://prod.media.memobase.ch/memo/csa-001-test-1"
        fallback = "https://institution.example.org/catalog"
        for partner in (
            "javascript:alert(1)",
            "https://cdn.example.org/file.mp4",
            "https://prod.media.memobase.ch/memo/another-hash",
        ):
            with self.subTest(partner=partner):
                result = choose_origin_destination(
                    raw, fallback, record_page_url=partner
                )
                self.assertEqual(result.url, fallback)
                self.assertEqual(result.kind, "institution_home")

    def test_fina_bfi_and_ifi_public_film_pages_are_preserved(self):
        cases = (
            (
                "https://ninateka.pl/movies,1/film-dokumentalny",
                "https://ninateka.pl/ogladaj",
            ),
            (
                "https://replay.bfi.org.uk/video/12345678-aaaa-4bcd-8000-1234567890ab",
                "https://replay.bfi.org.uk/",
            ),
            (
                "https://ifiarchiveplayer.ie/irish-film-reel-1952/",
                "https://ifiarchiveplayer.ie/browse/",
            ),
        )
        for page, home in cases:
            with self.subTest(page=page):
                result = choose_origin_destination(page, home)
                self.assertEqual(result.url, page)
                self.assertEqual(result.kind, "record_or_platform")

    def test_fina_bfi_and_ifi_reject_technical_or_navigation_pages(self):
        home = "https://archive.example/catalogue"
        rejected = (
            "https://ninateka.pl/api/products/vods",
            "https://ninateka.pl/movies,1/",
            "https://ninateka.pl/movies,1/test/video.mp4",
            "https://replay.bfi.org.uk/video/not-a-uuid",
            "https://replay.bfi.org.uk/video/12345678-aaaa-4bcd-8000-1234567890ab/master.m3u8",
            "https://ifiarchiveplayer.ie/wp-json/wp/v2/posts",
            "https://ifiarchiveplayer.ie/browse/",
            "https://ifiarchiveplayer.ie/post-sitemap.xml",
            "https://ifiarchiveplayer.ie/category-films/",
        )
        for url in rejected:
            with self.subTest(url=url):
                self.assertEqual(
                    choose_origin_destination(url, home).url,
                    home,
                )

    def test_aqshf_and_efg_collector_item_pages_are_preserved(self):
        examples = (
            (
                "https://aqshf.gov.al/motion_picture/filmi-historik/",
                "https://aqshf.gov.al/en/motion-pictures-listing/",
            ),
            (
                "https://aqshf.gov.al/motion_picture/23241/",
                "https://aqshf.gov.al/",
            ),
            (
                "https://www.europeanfilmgateway.eu/detail/film%20archive%20document/barch::425b123456",
                "https://www.europeanfilmgateway.eu/",
            ),
            (
                "https://www.europeanfilmgateway.eu/detail/silent-film/bnfa::3821?lang=en",
                "https://www.europeanfilmgateway.eu/",
            ),
        )
        for page, home in examples:
            with self.subTest(page=page):
                chosen = choose_origin_destination(page, home)
                self.assertEqual(chosen.url, page)
                self.assertEqual(chosen.kind, "record_or_platform")

    def test_aqshf_and_efg_technical_urls_are_not_item_pages(self):
        home = "https://archive.example/catalogue"
        rejected = (
            "https://aqshf.gov.al/wp-json/wp/v2/motion_picture",
            "https://aqshf.gov.al/motion_picture/",
            "https://aqshf.gov.al/motion_picture/sample/file.mp4",
            "https://www.europeanfilmgateway.eu/detail/",
            "https://www.europeanfilmgateway.eu/api/record/12",
            "https://www.europeanfilmgateway.eu/detail/12/stream",
            "https://www.europeanfilmgateway.eu/detail/video.mp4",
            "https://www.europeanfilmgateway.eu/detail/EFG123456",
            "https://www.europeanfilmgateway.eu/detail/film/unknown-provider",
            "https://www.europeanfilmgateway.eu/detail/film/barch::",
            "https://www.europeanfilmgateway.eu/detail/film/stream.m3u8",
        )
        for page in rejected:
            with self.subTest(page=page):
                chosen = choose_origin_destination(page, home)
                self.assertEqual(chosen.url, home)
                self.assertEqual(chosen.kind, "institution_home")

    def test_ert_wordpress_public_posts_preserve_item_permalink(self):
        # ERT collector stores WordPress 'link' as a human-facing item page.
        home = "https://archive.ert.gr/"
        for url in (
            "https://archive.ert.gr/ert-archive-12345/",
            "https://archive.ert.gr/28843/",
            "https://archive.ert.gr/%ce%b1%cf%81%cf%87%ce%b5%ce%b9%ce%bf/",
        ):
            with self.subTest(url=url):
                result = choose_origin_destination(url, home)
                self.assertEqual(result.url, url)
                self.assertEqual(result.kind, "record_or_platform")

    def test_ert_technical_paths_are_not_misidentified_as_public_posts(self):
        home = "https://archive.ert.gr/"
        for url in (
            "https://archive.ert.gr/wp-json/wp/v2/posts",
            "https://archive.ert.gr/wp-content/uploads/video.mp4",
            "https://archive.ert.gr/wp-admin/",
            "https://archive.ert.gr/category/",
            "https://archive.ert.gr/feed/",
            "https://archive.ert.gr/a/b/",
        ):
            with self.subTest(url=url):
                result = choose_origin_destination(url, home)
                self.assertEqual(result.url, home)
                self.assertEqual(result.kind, "institution_home")

    def test_murnau_and_image_est_public_fiches_are_never_downgraded(self):
        # These forms are explicitly produced by the two archive collectors,
        # where video_link means a metadata permalink, NOT a media file.
        cases = (
            (
                "https://www.murnau-stiftung.de/movie/7321",
                "https://www.murnau-stiftung.de/",
            ),
            (
                "https://www.murnau-stiftung.de/movie/32/",
                "https://www.murnau-stiftung.de/",
            ),
            (
                "https://www.image-est.fr/fiche-documentaire-mon-film-1284-3-123-0.html",
                "https://www.image-est.fr/",
            ),
            (
                "https://www.image-est.fr/fiche-documentaire-memoire-1284-1-17-0.html?lang=fr",
                "https://www.image-est.fr/",
            ),
        )
        for record, homepage in cases:
            with self.subTest(record=record):
                self.assertFalse(is_direct_media_asset(record))
                dest = choose_origin_destination(record, homepage)
                self.assertEqual(dest.url, record)
                self.assertEqual(dest.kind, "record_or_platform")

    def test_murnau_image_est_patterns_are_host_bound_and_fail_closed(self):
        cases = (
            "https://unknown.example/movie/7321",
            "https://www.murnau-stiftung.de/movie/not-a-number",
            "https://www.murnau-stiftung.de/movie/7321.mp4",
            "https://www.image-est.fr/fiche-documentaire-invalid.html.mp4",
            "https://unknown.example/fiche-documentaire-sample.html",
        )
        fallback = "https://archive.example/catalogue"
        for record in cases:
            with self.subTest(record=record):
                dest = choose_origin_destination(record, fallback)
                self.assertEqual(dest.url, fallback)
                self.assertEqual(dest.kind, "institution_home")

    def test_preserve_real_platform_watch_and_record_pages(self):
        values = (
            "https://www.youtube.com/watch?v=sample",
            "https://vimeo.com/1234567",
            "https://elonet.finna.fi/Record/kavi.elonet_elokuva_1611548",
        )
        for value in values:
            with self.subTest(value=value):
                result = choose_origin_destination(
                    value, "https://institution.example.org/"
                )
                self.assertEqual(result.url, value)
                self.assertEqual(result.kind, "record_or_platform")

    def test_legacy_raw_media_with_spaces_keeps_evidence_not_download_link(self):
        raw = "https://videos.far-asso.fr/film/CREAV_02_F_01 Bis.mp4"
        normalized = public_external_url(raw)
        self.assertEqual(normalized, raw.replace(" ", "%20"))
        selected = choose_origin_destination(
            raw, "https://far-asso.fr/catalogue"
        )
        self.assertEqual(selected.url, "https://far-asso.fr/catalogue")
        self.assertEqual(selected.kind, "institution_home")
        self.assertIn(" Bis.mp4", raw)

    def test_invalid_fallback_cannot_be_used_to_promote_media_url(self):
        result = choose_origin_destination(
            "https://example.com/media/film.mp4",
            "javascript:alert(1)",
        )
        self.assertIsNone(result.url)
        self.assertEqual(result.kind, "unavailable")

    def test_reject_code_execution_local_files_or_dangerous_urls(self):
        urls = (
            None, 23, "", "  ", "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "file:///etc/passwd", "/relative/video", "//example.org/video",
            "https://user:password@example.org/video",
            "https://example.org:bad/video",
            "https://exam ple.org/path",
            "https://example.org/path\nHeader: secret",
            "https://example.org/" + "x" * 5000,
        )
        for url in urls:
            with self.subTest(url=str(url)[:55]):
                self.assertIsNone(public_external_url(url))

    def test_streamlit_ui_has_no_embedded_video_or_iframe_calls(self):
        source = APP.read_text(encoding="utf-8-sig")
        parsed = ast.parse(source)
        banned = {
            ("st", "video"),
            ("st", "audio"),
            ("components", "iframe"),
            ("components", "html"),
        }
        invocations = []
        for node in ast.walk(parsed):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            owner = node.func.value
            if isinstance(owner, ast.Name):
                call = (owner.id, node.func.attr)
                if call in banned:
                    invocations.append((node.lineno, call))
        self.assertEqual(invocations, [])
        self.assertNotIn("streamlit.components.v1", source)
        self.assertNotIn("get_vimeo_embed_url", source)
        self.assertIn("choose_origin_destination(", source)
        self.assertIn('record_page_url=row.get("partner_site")', source)
        self.assertIn('"partner_site",', source)
        self.assertIn('if "partner_site" not in selected_links.columns:', source)
        self.assertIn('st.column_config.LinkColumn(localize_ui("Acessar na origem"))', source)
        self.assertNotIn('st.markdown(f"[Abrir vídeo]', source)
        self.assertIn("st.link_button(", source)

    def test_dataframe_link_column_config_uses_translated_header(self):
        # Execute only the pure adapter AST node, not the Streamlit app.
        # A translated DataFrame column needs the same translated config key.
        tree = ast.parse(APP.read_text(encoding="utf-8-sig"))
        function = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "localize_dataframe_arguments"
        )
        isolated = ast.fix_missing_locations(
            ast.Module(body=[function], type_ignores=[])
        )
        for lang, display_name in (
            ("es", "Abrir en la plataforma de origen"),
            ("en", "Open at source"),
        ):
            with self.subTest(language=lang):
                label = "Acessar na origem"
                env = {
                    "APP_LANGUAGE": lang,
                    "DEFAULT_LANGUAGE": "pt",
                    "localize_ui": lambda text: (
                        display_name if text == label else text
                    ),
                    "localize_dataframe_columns": lambda frame: {
                        (display_name if key == label else key): value
                        for key, value in frame.items()
                    },
                }
                exec(compile(isolated, str(APP), "exec"), env)
                original = {label: ["https://example.org/record"]}
                marker = object()
                args, kwargs = env["localize_dataframe_arguments"](
                    (original,),
                    {"column_config": {label: marker}},
                )
                self.assertIn(display_name, args[0])
                self.assertIn(display_name, kwargs["column_config"])
                self.assertIs(kwargs["column_config"][display_name], marker)
                self.assertIn(label, original)  # Never mutate source metadata

    def test_external_navigation_translated_into_supported_languages(self):
        phrases = {
            "Abrir registro ou vídeo na plataforma de origem ↗": (
                "Abrir ficha o video en la plataforma de origen ↗",
                "Open record or video on the source platform ↗",
            ),
            "O acesso ocorre na plataforma externa, conforme suas condições de disponibilidade e direitos.": (
                "El acceso se realiza en la plataforma externa, sujeto a sus condiciones de disponibilidad y derechos.",
                "Access takes place on the external platform, subject to its availability and rights conditions.",
            ),
            "Acessar na origem": (
                "Abrir en la plataforma de origen",
                "Open at source",
            ),
            "Visitar catálogo da instituição ↗": (
                "Visitar el catálogo de la institución ↗",
                "Visit the institution's catalog ↗",
            ),
            "Abrir a obra na plataforma de origem ↗": (
                "Abrir la obra en la plataforma de origen ↗",
                "Open the work on the source platform ↗",
            ),
            "Ficha específica da obra não identificada; o link leva ao catálogo da instituição.": (
                "No se ha identificado la ficha de esta obra; el enlace lleva al catálogo de la institución.",
                "An item-specific record has not been identified; the link opens the institution's catalog.",
            ),
        }
        for source, (spanish, english) in phrases.items():
            with self.subTest(source=source):
                self.assertEqual(translate_ui_text(source, "es"), spanish)
                self.assertEqual(translate_ui_text(source, "en"), english)

    def test_csv_json_downloads_remain_metadata_exports_only(self):
        source = APP.read_text(encoding="utf-8-sig")
        self.assertIn('mime="text/csv"', source)
        self.assertIn('mime="application/json"', source)
        self.assertNotIn('mime="video/', source)


if __name__ == "__main__":
    unittest.main()
