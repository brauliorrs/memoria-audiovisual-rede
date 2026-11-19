"""End-to-end synthetic corpus inclusion rehearsal: no real sources or publication."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_mar_site_bundle_b2 import BundleError, atomic_stage_files
from scripts.mar_b2_synthetic_integration import (
    BASE_COUNT, KAVI_COUNT, NEW_CODE, NEW_TITLE_MARKER,
    build_fixture_epoch, populate_fake_sources, stage_fixture, validate_fixture_epoch,
)

VALID = {
    "scientificAdmissionApproved": True,
    "aggregateDisplayApproved": True,
    "accessEvidenceReviewed": True,
    "individualMetadataApproved": False,
    "mediaRightsApproved": False,
}


def load(stage: Path, name: str):
    return json.loads((stage / "site/data" / name).read_text(encoding="utf-8"))


class MARB2FullSyntheticRehearsal(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory(prefix="mar-b2-synthetic-")
        self.addCleanup(self.dir.cleanup)
        self.area = Path(self.dir.name)
        self.base = self.area / "baseline"
        self.changed = self.area / "admitted"
        populate_fake_sources(self.base, False)
        populate_fake_sources(self.changed, True)

    def test_positive_admission_updates_every_affected_surface_with_one_epoch(self):
        before = stage_fixture(self.base, self.area / "staged-before", VALID, False)
        after = stage_fixture(self.changed, self.area / "staged-after", VALID, True)
        staged_before, staged_after = self.area / "staged-before", self.area / "staged-after"
        self.assertEqual(before["corpusReportCount"], BASE_COUNT)
        self.assertEqual(after["corpusReportCount"], BASE_COUNT + 1)
        self.assertNotEqual(before["epochSha256"], after["epochSha256"])
        self.assertFalse(before["publicationAuthorized"])
        self.assertFalse(after["publicAccessAuthorized"])
        self.assertEqual(after["individuallyApprovedKaviMetadataRecords"], KAVI_COUNT)
        self.assertEqual(json.loads((staged_after / "manifest.json").read_text()), after)
        self.assertTrue((staged_before / "manifest.json").is_file())

        analytics = []
        for name in sorted(n for n in after["staticProjectionSha256"] if "/analytics-" in n):
            analytics.extend(json.loads((staged_after / name).read_text()))
        self.assertEqual(len(analytics), BASE_COUNT + 1)
        fresh_report = next(r for r in analytics if r["code"] == NEW_CODE)
        self.assertEqual(fresh_report["platforms"]["Repositório fictício"], 21)
        self.assertNotIn("private-raw-film.mp4", json.dumps(analytics))

        slices = {}
        profiles = {}
        for name in sorted(after["staticProjectionSha256"]):
            if "/research-slices-" in name:
                slices.update(json.loads((staged_after / name).read_text()))
            if "/institution-profiles-" in name:
                profiles.update(json.loads((staged_after / name).read_text()))
        self.assertIn(NEW_CODE, slices)
        self.assertIn(NEW_CODE, profiles)
        self.assertEqual(slices[NEW_CODE]["tema_pais"]["rows"][0]["pais"], "Portugal")
        self.assertEqual(slices[NEW_CODE]["tema_plataforma"]["rows"][0]["total"], "21")
        self.assertEqual(slices[NEW_CODE]["linha_do_tempo_corpus"]["rows"][0]["video_links_total"], "21")
        self.assertEqual(profiles[NEW_CODE]["rows"][0]["country"], "Portugal")

        research = load(staged_after, "research-0.json")
        self.assertEqual(len(research), BASE_COUNT + 1)
        new = next(x for x in research if x["code"] == NEW_CODE)
        self.assertEqual(new["themes"][0]["value"], 21)
        self.assertEqual(new["countries"][0]["value"], 21)
        self.assertEqual(new["countries"][0]["country"], "Portugal")
        self.assertEqual(new["platforms"][0]["value"], 21)
        self.assertEqual(new["timeline"][0]["videoLinks"], 21)
        countries = {}
        for x in research:
            for country in x["countries"]:
                countries[country["country"]] = countries.get(country["country"], 0) + country["value"]
        self.assertEqual(countries["Portugal"], 21)
        self.assertEqual(countries["France"], BASE_COUNT * 21)

        before_index = load(staged_before, "public-access-observatory.json")
        index = load(staged_after, "public-access-observatory.json")
        self.assertEqual(len(index["corpora"]), len(before_index["corpora"]) + 1)
        self.assertEqual(index["summary"]["historicalMaterializedTotal"],
                         before_index["summary"]["historicalMaterializedTotal"] + 21)
        self.assertTrue(index["publicationOfIndividualRecordsNotAuthorizedByThisFile"])
        self.assertTrue(all(c["recordDisplay"] == "not_authorized_for_new_site" for c in index["corpora"]))

        before_cloud = load(staged_before, "title-wordcloud.json")
        cloud = load(staged_after, "title-wordcloud.json")
        self.assertEqual(cloud["corporaProcessed"], before_cloud["corporaProcessed"] + 1)
        self.assertEqual(cloud["titlesExamined"], before_cloud["titlesExamined"] + 21)
        before_terms = {w["text"]: w for w in before_cloud["words"]}
        new_terms = {w["text"]: w for w in cloud["words"]}
        self.assertGreater(new_terms["memoria"]["count"], before_terms["memoria"]["count"])
        self.assertNotIn(NEW_TITLE_MARKER, new_terms)
        self.assertFalse(cloud["rawTitlesPublished"])
        self.assertFalse(cloud["individualRecordsPublished"])

        # The already reviewed KAVI and documentary decisions are not derivatives.
        self.assertEqual(load(staged_before, "kavi-public.json"), load(staged_after, "kavi-public.json"))
        self.assertEqual(load(staged_before, "documented-cases.json"), load(staged_after, "documented-cases.json"))
        self.assertFalse(load(staged_after, "documented-cases.json")["publicationAuthorized"])

    def test_unreviewed_incorporation_stays_hold_without_any_staging(self):
        for missing in ("scientificAdmissionApproved", "aggregateDisplayApproved", "accessEvidenceReviewed"):
            with self.subTest(missing=missing):
                target = self.area / f"refused-{missing}"
                approvals = dict(VALID, **{missing: False})
                with self.assertRaisesRegex(BundleError, "HOLD"):
                    stage_fixture(self.changed, target, approvals, True)
                self.assertFalse(target.exists())

    def test_no_automatic_rights_promotion_or_raw_media(self):
        for permission in ("individualMetadataApproved", "mediaRightsApproved"):
            with self.subTest(permission=permission):
                target = self.area / f"bad-{permission}"
                with self.assertRaisesRegex(BundleError, "HOLD"):
                    stage_fixture(self.changed, target, dict(VALID, **{permission: True}), True)
                self.assertFalse(target.exists())

    def test_divergent_geographic_source_fails_without_changing_prior_epoch(self):
        old = stage_fixture(self.base, self.area / "safe-last-good", VALID, False)
        prior = (self.area / "safe-last-good/manifest.json").read_bytes()
        source = self.changed / f"data/output/{NEW_CODE}_tema_pais.csv"
        source.write_text("tema,pais,total\nMemória comunitária,Portugal,999\n", encoding="utf-8")
        with self.assertRaisesRegex(BundleError, "Country distribution"):
            stage_fixture(self.changed, self.area / "bad-epoch", VALID, True)
        self.assertFalse((self.area / "bad-epoch").exists())
        self.assertEqual((self.area / "safe-last-good/manifest.json").read_bytes(), prior)
        self.assertEqual(old["corpusReportCount"], BASE_COUNT)

    def test_stale_panel_with_updated_file_hash_is_rejected(self):
        # Checking only a manifest checksum would miss this if re-signed.
        build_fixture_epoch(self.changed, VALID, True)
        path = self.changed / "site/data/research-0.json"
        previous = json.loads(path.read_text(encoding="utf-8"))
        row = next(x for x in previous if x["code"] == NEW_CODE)
        row["countries"][0]["value"] = 900
        path.write_text(json.dumps(previous), encoding="utf-8")
        with self.assertRaisesRegex(BundleError, "research map/series stale"):
            validate_fixture_epoch(self.changed, [f"fixture_{i:03d}" for i in range(BASE_COUNT)] + [NEW_CODE])

    def test_failed_atomic_stage_does_not_publish_partial_new_snapshot(self):
        old = stage_fixture(self.base, self.area / "last-good", VALID, False)
        old_manifest = (self.area / "last-good/manifest.json").read_bytes()
        candidate = build_fixture_epoch(self.changed, VALID, True)
        candidate["staticProjectionSha256"]["site/data/research-0.json"] = "0" * 64
        with self.assertRaisesRegex(BundleError, "Staged output hash drift"):
            atomic_stage_files(
                self.changed, self.area / "partial-new", sorted(candidate["staticProjectionSha256"]),
                candidate,
            )
        self.assertFalse((self.area / "partial-new").exists())
        self.assertEqual((self.area / "last-good/manifest.json").read_bytes(), old_manifest)
        self.assertEqual(old["corpusReportCount"], BASE_COUNT)

    def test_repeat_build_is_deterministic_and_never_rewrites_real_site(self):
        a = build_fixture_epoch(self.changed, VALID, True)
        b = build_fixture_epoch(self.changed, VALID, True)
        self.assertEqual(a, b)
        self.assertEqual(len(a["epochSha256"]), 64)
        self.assertGreaterEqual(len(a["staticProjectionSha256"]), 8)


if __name__ == "__main__":
    unittest.main()
