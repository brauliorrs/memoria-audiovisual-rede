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
        self.assertIn('st.column_config.LinkColumn("Acessar na origem")', source)
        self.assertNotIn('st.markdown(f"[Abrir vídeo]', source)
        self.assertIn("st.link_button(", source)

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
