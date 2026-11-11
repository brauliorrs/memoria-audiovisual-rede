"""Offline contract: Eye exactly 3 pages; Czech exactly 1 show + 1 episode."""
from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from scripts.probe_staged_eye_czech import Checkpoints, _canonical, _digest, classify_czech_episode_metadata, map_czech_public_metadata_structure, run


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

    def test_checkpoint_records_reviewed_pr_head_separately_from_merge_sha(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict("os.environ", {
                "MAR_PROBE_HEAD_SHA": "reviewed-commit-123",
                "GITHUB_SHA": "synthetic-merge-456",
            }):
                state = Checkpoints("eye", folder)
        self.assertEqual(state.value["head_sha"], "reviewed-commit-123")
        self.assertEqual(state.value["workflow_sha"], "synthetic-merge-456")

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
        catalog = '<a href="/porady/12701251153-kultura/">Kultura</a><a href="/porady/222-other/">Other</a>'
        show = '<a href="/porady/12701251153-kultura/226411033400703/">Episode</a>'
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
        self.assertIn("/porady/12701251153-kultura/", opener.urls[2])
        self.assertIn("226411033400703", opener.urls[3])
        self.assertEqual(doc["stages"][-1]["media_meta_is_playable"], True)
        self.assertEqual(doc["stages"][-1]["actual_stream_playback_verified"], False)

    def test_czech_unplayable_episode_stays_hold_without_other_attempts(self):
        catalog = '<a href="/porady/12701251153-kultura/">Kultura</a>'
        show = '<a href="/porady/12701251153-kultura/226411033400703/">Episode</a>'
        episode = next_data({"mediaMeta": {"id": "ep", "isPlayable": False}})
        opener = SequentialOpener(robots(), Reply(catalog), Reply(show), Reply(episode))
        passed, doc, _ = self.run_in_dir("czech_tv", opener)
        self.assertFalse(passed)
        self.assertEqual(doc["reason"], "czech_is_playable_explicit_false")
        self.assertEqual(doc["stages"][-1]["playability_claim"], "false")
        self.assertTrue(doc["stages"][-1]["is_playable_field_present"])
        self.assertEqual(len(opener.urls), 4)

    def test_czech_metadata_classifier_distinguishes_missing_and_false(self):
        cases = [
            ("<html>mediaMeta</html>", "czech_next_data_absent", False),
            ('<script id="__NEXT_DATA__">{bad</script>', "czech_next_data_invalid", False),
            (next_data({}), "czech_media_meta_missing_at_expected_path", False),
            (next_data({"mediaMeta": {"id": "record"}}), "czech_is_playable_absent", False),
            (next_data({"mediaMeta": {"id": "record", "isPlayable": False}}),
             "czech_is_playable_explicit_false", False),
            (next_data({"mediaMeta": {"id": "record", "isPlayable": True}}),
             "czech_public_metadata_playable_with_id", True),
            (next_data({"mediaMeta": {"isPlayable": True}}),
             "czech_playable_without_episode_id", False),
        ]
        for html, classification, playable in cases:
            with self.subTest(classification=classification):
                result = classify_czech_episode_metadata(html)
                self.assertEqual(result["classification"], classification)
                self.assertEqual(
                    result["classification"] == "czech_public_metadata_playable_with_id",
                    playable
                )

    def test_czech_missing_next_data_is_hold_without_fallback(self):
        catalog = '<a href="/porady/12701251153-kultura/">Kultura</a>'
        show = '<a href="/porady/12701251153-kultura/226411033400703/">Episode</a>'
        opener = SequentialOpener(robots(), Reply(catalog), Reply(show), Reply("<html>video metadata unavailable</html>"))
        passed, doc, _ = self.run_in_dir("czech_tv", opener)
        self.assertFalse(passed)
        self.assertEqual(doc["reason"], "czech_next_data_absent")
        self.assertEqual(doc["stages"][-1]["next_data_present"], False)
        self.assertEqual(len(opener.urls), 4)

    def test_czech_cannot_switch_to_new_programme_silently(self):
        catalog = '<a href="/porady/9999-new-show/">New programme</a>'
        opener = SequentialOpener(robots(), Reply(catalog))
        passed, doc, _ = self.run_in_dir("czech_tv", opener)
        self.assertFalse(passed)
        self.assertEqual(doc["reason"], "czech_previously_sampled_programme_not_in_catalogue")
        self.assertEqual(len(opener.urls), 2)

    def test_czech_schema_map_records_key_names_without_values(self):
        doc = next_data({
            "episodeDetails": {"videoMetadata": {
                "isPlayable": True, "accessToken": "PRIVATE_SAMPLE",
                "videoUrl": "https://example.com/secret-stream",
            }},
            "assetList": [{"streamAvailability": {"enabled": True}}],
            "userEmail": "private@example.com",
        })
        doc += (
            '<meta property="og:video" content="https://example.com/secret-stream">'
            '<meta name="description" content="description must not be stored">'
            '<script type="application/ld+json">'
            '{"@type":"VideoObject","name":"Should not be stored"}'
            '</script>'
        )
        mapped = map_czech_public_metadata_structure(doc)
        self.assertIn("episodeDetails", mapped["next_data_page_data_keys"])
        self.assertIn("$.props.pageProps.data.episodeDetails", mapped["candidate_key_paths"])
        self.assertIn("og:video", mapped["public_meta_names"])
        self.assertEqual(mapped["jsonld_public_types"], ["VideoObject"])
        self.assertFalse(mapped["stream_playback_verified"])
        encoded = json.dumps(mapped)
        self.assertNotIn("PRIVATE_SAMPLE", encoded)
        self.assertNotIn("secret-stream", encoded)
        self.assertNotIn("private@example.com", encoded)
        self.assertNotIn("userEmail", encoded)
        self.assertNotIn("accessToken", encoded)

    def test_czech_schema_mapping_is_part_of_hold_checkpoint(self):
        catalog = '<a href="/porady/12701251153-kultura/">Kultura</a>'
        show = '<a href="/porady/12701251153-kultura/226411033400703/">Episode</a>'
        html = next_data({"episode": {"details": {"title": "Ignored"}}})
        opener = SequentialOpener(robots(), Reply(catalog), Reply(show), Reply(html))
        passed, doc, _ = self.run_in_dir("czech_tv", opener)
        self.assertFalse(passed)
        self.assertEqual(doc["reason"], "czech_media_meta_missing_at_expected_path")
        structure = [x for x in doc["stages"] if x["stage"] == "czech_public_metadata_schema"]
        self.assertEqual(len(structure), 1)
        self.assertIn("episode", structure[0]["next_data_page_data_keys"])
        self.assertFalse(doc["corpus_validated"])
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
