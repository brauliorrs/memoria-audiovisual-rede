"""Guard MAR's link-only delivery and forbid in-app audiovisual playback."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

from memoria_audiovisual.external_links import public_external_url
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

    def test_reject_code_execution_local_files_or_dangerous_urls(self):
        urls = (
            None, 23, "", "  ", "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "file:///etc/passwd", "/relative/video", "//example.org/video",
            "https://user:password@example.org/video",
            "https://example.org:bad/video",
            "https://example.org/with whitespace",
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
        self.assertIn("public_external_url(row[\"video_link\"])", source)
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
