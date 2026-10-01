import unittest

from memoria_audiovisual.gosfilmofond import (
    GOSFILMOFOND_AJAX_URL,
    GOSFILMOFOND_CATALOG_URL,
    collect_gosfilmofond_dataset,
    parse_gosfilmofond_ajax_page,
)
from memoria_audiovisual.gosfilmofond_probe import GOSFILMOFOND_ROBOTS_URL


CATALOG_HTML = """
<html><body>
<div class="page-count">
  <select><option value="1">1</option><option value="2">2</option></select>
</div>
<form action="/wp-admin/admin-ajax.php" method="post">
  <input type="hidden" name="action" value="filter_films">
  <input type="hidden" name="paged" value="1">
  <input type="hidden" name="page_count" value="2">
</form>
</body></html>
"""

ROBOTS_ALLOW = """User-agent: *
Allow: /
"""


def ajax_html(page, rows, max_page=3):
    cards = "".join(
        (
            '<div class="film-card">'
            f'<a href="/films/{key}/">{title}</a>'
            f"<span>СССР {year}</span>"
            "</div>"
        )
        for key, title, year in rows
    )
    return (
        "<html><body>"
        + cards
        + "".join(
            f'<a class="page-numbers" data-page="{num}">{num}</a>'
            for num in range(1, max_page + 1)
        )
        + "</body></html>"
    )


class FakeResponse:
    def __init__(self, url, text="", status_code=200, content_type="text/html"):
        self.url = url
        self.text = text
        self.status_code = status_code
        self.headers = {"content-type": content_type}


class FakeSession:
    def __init__(self, pages, *, robots=ROBOTS_ALLOW):
        self.pages = pages
        self.robots = robots
        self.headers = {"User-Agent": "MAR-Test-Agent"}

    def get(self, url, **_kwargs):
        if url == GOSFILMOFOND_ROBOTS_URL:
            return FakeResponse(url, self.robots, 200, "text/plain")
        if url == GOSFILMOFOND_CATALOG_URL:
            return FakeResponse(url, CATALOG_HTML)
        return FakeResponse(url, "", 404)

    def post(self, url, data=None, **_kwargs):
        if url != GOSFILMOFOND_AJAX_URL:
            return FakeResponse(url, "", 404)
        page = int((data or {}).get("paged", 0))
        if page not in self.pages:
            return FakeResponse(url, "", 404)
        return FakeResponse(url, self.pages[page])


class GosfilmofondCollectionTests(unittest.TestCase):
    def test_ajax_parser_preserves_public_card_title_year_and_permalink(self):
        rows, meta = parse_gosfilmofond_ajax_page(
            ajax_html(
                1,
                [
                    ("100", "Первый фильм", "1980"),
                    ("film-slug", "Второй фильм", "1990"),
                ],
            )
        )
        self.assertEqual([row["record_key"] for row in rows], ["100", "film-slug"])
        self.assertEqual([row["date"] for row in rows], ["1980", "1990"])
        self.assertEqual(
            rows[1]["page_url"],
            "https://gosfilmofond.ru/films/film-slug/",
        )
        self.assertEqual(meta["max_page_number"], 3)

    def test_three_page_catalog_is_complete_and_deduplicated(self):
        pages = {
            1: ajax_html(
                1,
                [("100", "A", "1980"), ("101", "B", "1981")],
            ),
            2: ajax_html(
                2,
                [("102", "C", "1982"), ("103", "D", "1983")],
            ),
            3: ajax_html(
                3,
                [("104", "E", "1984")],
            ),
        }
        institutions, summary, links, internal = collect_gosfilmofond_dataset(
            session=FakeSession(pages),
            sleep_fn=lambda _seconds: None,
            request_delay=0,
        )
        self.assertEqual(institutions[0]["institution"], "Gosfilmofond of Russia")
        self.assertEqual(summary[0]["integrity_status"], "integro")
        self.assertEqual(summary[0]["video_links_found_total"], 5)
        self.assertEqual(len(links), 5)
        self.assertEqual(len({row["video_link"] for row in links}), 5)
        self.assertEqual(
            sum("admin-ajax.php#page=" in row["internal_page"] for row in internal),
            3,
        )

    def test_duplicate_across_pages_blocks_integrity(self):
        pages = {
            1: ajax_html(
                1,
                [("100", "A", "1980"), ("101", "B", "1981")],
                max_page=2,
            ),
            2: ajax_html(
                2,
                [("101", "B", "1981"), ("102", "C", "1982")],
                max_page=2,
            ),
        }
        _, summary, links, _ = collect_gosfilmofond_dataset(
            session=FakeSession(pages),
            sleep_fn=lambda _seconds: None,
            request_delay=0,
        )
        self.assertEqual(summary[0]["integrity_status"], "instavel")
        self.assertEqual(len(links), 3)
        self.assertIn("cross_page_duplicates", summary[0]["error"])

    def test_short_intermediate_page_fails_closed(self):
        pages = {
            1: ajax_html(
                1,
                [("100", "A", "1980")],
                max_page=3,
            ),
        }
        _, summary, links, internal = collect_gosfilmofond_dataset(
            session=FakeSession(pages),
            sleep_fn=lambda _seconds: None,
            request_delay=0,
        )
        self.assertEqual(summary[0]["integrity_status"], "instavel")
        self.assertEqual(links, [])
        self.assertIn("short_intermediate_page", summary[0]["error"])
        self.assertEqual(internal[-1]["status"], "erro")

    def test_robots_block_prevents_any_ajax_enumeration(self):
        blocked = """User-agent: *
Disallow: /films/
Disallow: /wp-admin/
"""
        _, summary, links, internal = collect_gosfilmofond_dataset(
            session=FakeSession({}, robots=blocked),
            sleep_fn=lambda _seconds: None,
            request_delay=0,
        )
        self.assertEqual(summary[0]["integrity_status"], "instavel")
        self.assertEqual(links, [])
        self.assertEqual(internal[0]["status"], "bloqueado_robots")


if __name__ == "__main__":
    unittest.main()
