"""Preserve APE access restrictions as explicit HOLD, without alternative bypass."""
import unittest
from unittest.mock import Mock, patch

from memoria_audiovisual.ape import (
    ApePublicAccessHold, fetch_pdf_reader, fetch_pdf_text,
    require_ape_pdf_access,
)


class ApeAccessHoldTests(unittest.TestCase):
    def test_403_and_429_are_explicit_holds_before_pdf_parse(self):
        for status, category in (
            (403, "ape_official_pdf_access_denied_403"),
            (429, "ape_official_pdf_rate_limited_429"),
        ):
            with self.subTest(status=status):
                response = Mock(status_code=status)
                with self.assertRaisesRegex(ApePublicAccessHold, category):
                    require_ape_pdf_access(response)
                response.raise_for_status.assert_not_called()

    def test_both_pdf_entrypoints_refuse_forbidden_source_without_fallback(self):
        response = Mock(status_code=403)
        with patch("memoria_audiovisual.ape.SESSION.get", return_value=response):
            for entrypoint in (fetch_pdf_reader, fetch_pdf_text):
                with self.subTest(entrypoint=entrypoint.__name__):
                    with self.assertRaisesRegex(ApePublicAccessHold, "403"):
                        entrypoint("https://www.archivesportaleurope.net/blocked.pdf")

    def test_other_http_error_is_not_converted_into_success(self):
        response = Mock(status_code=503)
        response.raise_for_status.side_effect = RuntimeError("server error")
        with self.assertRaisesRegex(RuntimeError, "server error"):
            require_ape_pdf_access(response)


if __name__ == "__main__":
    unittest.main()
