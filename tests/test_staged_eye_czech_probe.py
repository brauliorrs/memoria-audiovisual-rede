"""Offline contract: Eye exactly 3 pages; Czech exactly 1 show + 1 episode."""
from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError

from scripts.probe_staged_eye_czech import _canonical, _digest, run


class Reply:
    def __init__(self, html, content_type="text/html", status=200):
        self.status = status
        self.headers = {"Content-Type": content_type}
        self.data = io.BytesIO(html.encode() if isinstance(html, str) else html)
    def read(self, limit):
        return self.data.read(limit)
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.data.close()


class SequentialOpener:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.urls = []
    def open(self, request, *, timeout):
        self.urls.append(request.full_url)
        if not self.replies:
            raise AssertionError("Extra network request not permitted")
        response = self.replies.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def robots():
    return Reply("User-agent: *\nAllow: /\nCrawl-delay: 2\n", "text/plain")


def eye_page(*record_ids, total=630):
    items = "".join(
        '<li class="packery-item"><h2><a href="/en/collection/film-history/film/'
        + identifier + '">Film ' + identifier + '</a></h2></li>'
        for identifier in record_ids
    )
    return '<html><div>with film fragment ' + str(total) + '</div>' \
        '<div class="view-content">' + items + '</div></html>'


def next_data(data):
    return ('<script id="__NEXT_DATA__" type="application/json">'
            + json.dumps({"props": {"pageProps": {"data": data}}})
            + '</script>')


class StagedEyeCzechTests(unittest.TestCase):
    def run_in_dir(self, source, opener):
        sleeps = []
        with tempfile.TemporaryDirectory() as folder:
            passed = run(source, folder, opener=opener, sleep_fn=sleeps.append)
            document = json.loads((Path(folder) / (source + ".json")).read_text())
        return passed, document, sleeps

    def test_eye_fetches_exact_three_pages_and_deduplicates_with_checkpoints(self):
        opener = SequentialOpener(
            robots(),
            Reply(eye_page("a", "b")),
            Reply(eye_page("b", "c")),
            Reply(eye_page("d", "e")),
        )
        passed, doc, sleeps = self.run_in_dir("eye", opener)
        self.assertTrue(passed)
        self.assertEqual(doc["status"], "STAGED_PASS")
        self.assertFalse(doc["corpus_validated"])
        self.assertFalse(doc["media_downloaded"])
        self.assertEqual(len(opener.urls), 4)  # robots + page 0 + page 1 + page 2
        self.assertEqual(len(sleeps), 2)
        self.assertEqual(sleeps, [2, 2])
        self.assertIn("page=1", opener.urls[2])
        self.assertIn("page=2", opener.urls[3])
        pages = [e for e in doc["stages"] if e["stage"].startswith("eye_page_")]
        self.assertEqual([p["cumulative_unique"] for p in pages], [2, 3, 5])
        self.assertEqual([p["duplicates_across_pages"] for p in pages], [0, 1, 0])
        self.assertEqual([p["declared_total"] for p in pages], [630] * 3)
        self.assertEqual(
            doc["stages"][-1]["globally_complete"], False
        )
        chain = _digest(b"")
        for event in doc["stages"]:
            chain = _digest((chain + _canonical(event)).encode("utf-8"))
        self.assertEqual(doc["chain_sha256"], chain)

    def test_eye_changed_filter_fails_closed_after_checkpoint(self):
        opener = SequentialOpener(
            robots(),
            Reply(eye_page("a")),
            Reply(eye_page("b", total=3000)),
        )
        passed, doc, _ = self.run_in_dir("eye", opener)
        self.assertFalse(passed)
        self.assertEqual(doc["reason"], "eye_fragment_filter_inconsistent")
        self.assertEqual(len(opener.urls), 3)
        self.assertEqual(len([x for x in doc["stages"] if x["stage"].startswith("eye_page_")]), 1)

    def test_eye_forbidden_page_has_no_retry_or_third_page(self):
        opener = SequentialOpener(
            robots(),
            Reply(eye_page("a")),
            HTTPError("https://example.com", 403, "Forbidden", {}, None),
        )
        passed, doc, _ = self.run_in_dir("eye", opener)
        self.assertFalse(passed)
        self.assertEqual(doc["reason"], "source_access_forbidden")
        self.assertEqual(len(opener.urls), 3)

    def test_czech_checks_one_programme_and_one_playable_episode(self):
        catalog = '<a href="/porady/151-kultura/">Kultura</a><a href="/porady/222-other/">Other</a>'
        show = '<a href="/porady/151-kultura/226411033400703/">Episode</a>'
        episode = next_data({"mediaMeta": {
            "isPlayable": True, "id": "ep-123", "title": "Archive episode",
            "show": {"title": "Kultura"},
        }})
        opener = SequentialOpener(robots(), Reply(catalog), Reply(show), Reply(episode))
        passed, doc, sleeps = self.run_in_dir("czech_tv", opener)
        self.assertTrue(passed)
        self.assertEqual(doc["status"], "STAGED_PASS")
        self.assertFalse(doc["corpus_validated"])
        self.assertEqual(len(opener.urls), 4)
        self.assertEqual(sleeps, [2, 2])
        self.assertIn("/porady/151-kultura/", opener.urls[2])
        self.assertIn("226411033400703", opener.urls[3])
        self.assertEqual(doc["stages"][-1]["media_meta_is_playable"], True)
        self.assertEqual(doc["stages"][-1]["actual_stream_playback_verified"], False)

    def test_czech_unplayable_episode_stays_hold_without_other_attempts(self):
        catalog = '<a href="/porady/151-kultura/">Kultura</a>'
        show = '<a href="/porady/151-kultura/226411033400703/">Episode</a>'
        episode = next_data({"mediaMeta": {"id": "ep", "isPlayable": False}})
        opener = SequentialOpener(robots(), Reply(catalog), Reply(show), Reply(episode))
        passed, doc, _ = self.run_in_dir("czech_tv", opener)
        self.assertFalse(passed)
        self.assertEqual(doc["reason"], "czech_episode_not_playable_in_public_metadata")
        self.assertEqual(len(opener.urls), 4)

    def test_robots_disallow_blocks_all_catalogue_requests(self):
        opener = SequentialOpener(Reply("User-agent: *\nDisallow: /\n", "text/plain"))
        passed, doc, _ = self.run_in_dir("eye", opener)
        self.assertFalse(passed)
        self.assertEqual(doc["reason"], "robots_disallowed")
        self.assertEqual(len(opener.urls), 1)

    def test_nonallowlisted_source_is_rejected_without_network(self):
        with self.assertRaises(ValueError):
            run("ape", opener=SequentialOpener())


if __name__ == "__main__":
    unittest.main()
