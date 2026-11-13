"""Source-specific offline link discovery for ASIM, Bundesarchiv and BNFA.

Link candidates are never equivalent to verified video availability.
"""
from __future__ import annotations

import unittest

from memoria_audiovisual.asim import parse_asim_search_page
from memoria_audiovisual.barch import parse_barch_search_page
from memoria_audiovisual.bnfa import parse_bnfa_search_page

BASE = "https://www.europeanfilmgateway.eu/search-efg/example"


class ProviderSearchLinkTests(unittest.TestCase):
    def test_asim_encoded_link_is_discovered_once(self):
        html = (
            '<a href="/detail/A/asim%3A%3A123">A</a>'
            '<a href="/detail/A/asim%3A%3A123">duplicate</a>'
            '<a href="https://attacker.example/detail/asim::123">off-domain</a>'
        )
        self.assertEqual(parse_asim_search_page(html, BASE), [
            "https://www.europeanfilmgateway.eu/detail/A/asim%3A%3A123",
        ])

    def test_bnfa_encoded_id_is_only_accepted_on_efg(self):
        html = (
            '<a href="/detail/B/bnfa%3A%3A456">B</a>'
            '<a href="/detail/B/asim::456">wrong provider</a>'
            '<a href="http://www.europeanfilmgateway.eu/detail/B/bnfa::456">'
            'plain HTTP rejected</a>'
        )
        self.assertEqual(parse_bnfa_search_page(html, BASE), [
            "https://www.europeanfilmgateway.eu/detail/B/bnfa%3A%3A456",
        ])

    def test_bundesarchiv_encoded_id_and_host_restrictions(self):
        html = (
            '<a href="/detail/C/barch%3A%3A789">Bundesarchiv</a>'
            '<a href="/detail/D/bnfa::789">other provider</a>'
            '<a href="https://malicious.example/detail/C/barch::789">'
            'not source-owned</a>'
        )
        self.assertEqual(parse_barch_search_page(html, BASE), [
            "https://www.europeanfilmgateway.eu/detail/C/barch%3A%3A789",
        ])

    def test_empty_search_does_not_fabricate_media_records(self):
        for parser in (
            parse_asim_search_page,
            parse_bnfa_search_page,
            parse_barch_search_page,
        ):
            with self.subTest(parser=parser.__name__):
                self.assertEqual(parser("<html>Search unavailable</html>", BASE), [])


if __name__ == "__main__":
    unittest.main()
