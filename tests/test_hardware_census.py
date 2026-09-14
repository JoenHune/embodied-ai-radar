import copy
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from catalog_store import fingerprint
from hardware_census import build_census, detect_mentions, dictionary_hash, export_census, load_catalog, main
from test_equipment_radar import fixture, make_work

AS_OF = "2026-09-14"
OBSERVED = "2026-09-14T01:00:00Z"


def dictionary_fixture():
    def entry(did, name, aliases, category="robot_platform", contexts=None):
        return {"dictionary_id": did, "name": name, "category": category, "identity_level": "model_specified",
                "aliases": aliases, "context_terms": contexts or [], "source_urls": ["https://example.com/"],
                "hardware_ids": []}
    return {"schema_version": 1, "version": "1", "entries": [
        entry("unitree-g1", "Unitree G1", ["G1", "Unitree-G1"], contexts=["Unitree", "robot", "humanoid"]),
        entry("unitree-h1", "Unitree H1", ["H1"], contexts=["Unitree", "humanoid"]),
        entry("unitree-h1-2", "Unitree H1-2", ["H1-2"], contexts=["Unitree", "humanoid"]),
        entry("apple-m1", "Apple M1", ["M1"], "compute_platform", ["Apple", "Mac", "processor"]),
        entry("rtx-4090", "NVIDIA RTX 4090", ["RTX 4090", "4090"], "compute_platform"),
        entry("ur5", "Universal Robots UR5", ["UR5"], "robot_arm", ["robot", "arm"]),
        entry("ur5e", "Universal Robots UR5e", ["UR5e"], "robot_arm"),
        entry("spot", "Boston Dynamics Spot", ["Spot"], contexts=["Boston Dynamics", "quadruped", "robot"]),
    ]}


def empty_authority():
    return {key: [] for key in ("devices", "usage-evidence", "loco-reviews", "loco-observations")}


def observation(work_id, status="full_text_available", text_hash="body-v1", **values):
    return {"work_id": work_id, "source_url": "https://arxiv.org/html/2608.00001v1",
            "effective_url": "https://arxiv.org/html/2608.00001v1", "observed_at": OBSERVED,
            "status": status, "text_sha256": text_hash, "raw_sha256": "raw-v1", "version": "v1",
            "cache_ref": ".research/hardware/body-v1.txt", "body_characters": 8000, **values}


def scan(obs, dictionary, text="Unitree G1 robot in experiments.", **values):
    return {"work_id": obs["work_id"], "source_url": obs["source_url"], "observed_at": OBSERVED,
            "scope": "body", "status": "scanned", "dictionary_hash": dictionary_hash(dictionary),
            "content_hash": obs["text_sha256"], "matches": detect_mentions(text, dictionary, "Experiments"), **values}


class HardwareMentionTests(unittest.TestCase):
    def test_new_official_rx75_identity_stays_separate_from_rm75_and_optional_camera(self):
        dictionary = json.loads((ROOT / 'config/hardware-dictionary.json').read_text())
        rx = [r for r in dictionary['entries'] if r['dictionary_id'] == 'model:realman-rx75']
        self.assertEqual(len(rx), 1)
        self.assertEqual(rx[0]['hardware_ids'], ['hardware:realman-rx75'])
        observed = {r['dictionary_id'] for r in detect_mentions('The RealMan RX75 robotic arm was used.', dictionary)}
        self.assertIn('model:realman-rx75', observed)
        self.assertFalse(any('d405' in did for did in observed))
        rm = {r['dictionary_id'] for r in detect_mentions('The RealMan RM75 robotic arm was used.', dictionary)}
        self.assertNotIn('model:realman-rx75', rm)
        self.assertEqual(detect_mentions('RX75 denotes a sample label.', {'schema_version': '1', 'entries': rx}), [])

    def test_boundaries_separators_and_longest_alias_wins(self):
        text = "Unitree-G1 robot; NVIDIA RTX 4090. Universal Robots UR5e arm; humanoid Unitree H1-2."
        matches = detect_mentions(text, dictionary_fixture())
        self.assertEqual([row["dictionary_id"] for row in matches], ["unitree-g1", "rtx-4090", "ur5e", "unitree-h1-2"])
        for row in matches:
            self.assertEqual(text[row["start"]:row["end"]], row["term"])
        self.assertEqual(detect_mentions("G10 M10 RTX 40900 XUnitree G1X UR5est", dictionary_fixture()), [])

    def test_short_model_requires_local_explicit_context(self):
        dictionary = dictionary_fixture()
        self.assertEqual(detect_mentions("G1 denotes the first group. M1 is the matrix rank.", dictionary), [])
        self.assertEqual([row["dictionary_id"] for row in detect_mentions("The G1 humanoid runs on an Apple M1 processor.", dictionary)], ["unitree-g1", "apple-m1"])
        self.assertEqual(detect_mentions("Unitree " + "measurement " * 30 + "G1 is a group.", dictionary), [])

    def test_numeric_or_unqualified_short_aliases_are_ignored(self):
        dictionary = dictionary_fixture()
        dictionary["entries"][0]["context_terms"] = []
        self.assertEqual(detect_mentions("G1 robot, 4090 training iterations.", dictionary), [])
        self.assertEqual(len(detect_mentions("Unitree G1 robot.", dictionary)), 1)

    def test_ambiguous_word_names_require_context(self):
        self.assertEqual(detect_mentions("We spot the error in this paragraph.", dictionary_fixture()), [])
        self.assertEqual(detect_mentions("The Spot robot is a quadruped.", dictionary_fixture())[0]["dictionary_id"], "spot")

    def test_shared_short_alias_does_not_arbitrarily_choose_an_identity(self):
        dictionary = dictionary_fixture()
        dictionary["entries"].append({**dictionary["entries"][3], "dictionary_id": "other-m1",
                                      "name": "Other M1", "context_terms": ["processor"]})
        self.assertEqual(detect_mentions("An M1 processor.", dictionary), [])
        self.assertEqual(detect_mentions("An Apple M1 processor.", dictionary)[0]["dictionary_id"], "apple-m1")

    def test_explicit_context_applies_to_long_single_token_aliases_too(self):
        dictionary = dictionary_fixture()
        base = dictionary["entries"][0]
        dictionary["entries"] = [
            {**base, "dictionary_id": "atlas", "name": "Boston Dynamics Atlas", "aliases": ["ATLAS"], "context_terms": ["Boston Dynamics", "humanoid", "biped"]},
            {**base, "dictionary_id": "aloha", "name": "ALOHA bimanual system", "aliases": ["ALOHA"], "context_terms": ["robot", "bimanual", "teleoperation"]},
            {**base, "dictionary_id": "a100", "name": "NVIDIA A100", "aliases": ["A100"], "category": "compute_platform", "context_terms": ["NVIDIA", "GPU"]},
            {**base, "dictionary_id": "dclaw", "name": "DClaw dexterous hand", "aliases": ["D-Claw"], "category": "dexterous_hand", "context_terms": ["dexterous", "hand"]},
        ]
        for text in ("The ATLAS mathematical model proves the theorem.", "ALOHA is a random access software network protocol.",
                     "Class A100 denotes the experiment group.", "The d-claw graph property is invariant."):
            self.assertEqual(detect_mentions(text, dictionary), [])
        for text, did in (("Boston Dynamics Atlas", "atlas"), ("An ATLAS humanoid", "atlas"),
                          ("Our ALOHA bimanual robot", "aloha"), ("The NVIDIA A100 GPU", "a100"),
                          ("A D-Claw dexterous hand", "dclaw")):
            self.assertEqual(detect_mentions(text, dictionary)[0]["dictionary_id"], did)

    def test_software_and_motor_entries_or_aliases_are_not_hardware(self):
        dictionary = dictionary_fixture()
        base = dictionary["entries"][0]
        dictionary["entries"] = [{**base, "dictionary_id": "isaac", "name": "NVIDIA Isaac Lab", "aliases": ["Isaac Lab"]},
                                 {**base, "dictionary_id": "motor", "name": "Servo motor", "aliases": ["Dynamixel servo"]},
                                 {**base, "aliases": ["Isaac Gym", "joint module"]}]
        self.assertEqual(detect_mentions("NVIDIA Isaac Lab Isaac Gym Servo motor Dynamixel servo joint module", dictionary), [])

    def test_sections_are_preserved_but_reference_mentions_are_not_usage(self):
        matches = detect_mentions("[1] Unitree G1 in prior work.", dictionary_fixture(), section="References")
        self.assertEqual(matches[0]["section"], "References")
        self.assertNotIn("review_status", matches[0])


class HardwareCensusTests(unittest.TestCase):
    def census(self, payload=None, authority=None, dictionary=None, scans=None, observations=None, **kwargs):
        if payload is None:
            payload = fixture()[0]
        return build_census(payload, authority if authority is not None else empty_authority(),
                            dictionary or dictionary_fixture(), scans or [], observations or [], AS_OF, **kwargs)

    def test_exactly_one_row_for_every_canonical_work_including_excluded(self):
        payload, _, _ = fixture()
        payload["works"] += [make_work(2, status="excluded"), make_work(3, status="manual_review"), make_work(4, status="candidate")]
        result = self.census(payload)
        self.assertEqual(len(result["rows"]), 4)
        self.assertEqual(result["summary"]["all_works"]["denominator"], 4)
        self.assertEqual(result["summary"]["included"]["denominator"], 1)
        self.assertEqual(result["summary"]["all_works"]["metadata_screened_work_count"], 4)
        self.assertEqual({row["relevance_status"] for row in result["rows"]}, {"included", "excluded", "manual_review", "candidate"})
        self.assertTrue(all("title" not in row and "abstract" not in row for row in result["rows"]))
        self.assertEqual(sum(group["all_works"]["denominator"] for group in result["summary"]["by_relevance"]), 4)

    def test_duplicate_work_ids_fail_instead_of_silently_collapsing(self):
        payload, _, _ = fixture()
        payload["works"].append(copy.deepcopy(payload["works"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate_or_missing_work_id"):
            self.census(payload)

    def test_metadata_no_hit_is_not_fulltext_negative(self):
        payload, _, _ = fixture()
        payload["works"][0].update(title="An algorithm", abstract="Abstract with no model names.")
        result = self.census(payload)
        row = result["rows"][0]
        self.assertEqual(row["metadata_scan"]["scope"], "metadata_only")
        self.assertEqual(row["body_source_state"], "not_attempted")
        self.assertFalse(row["full_text_screened_current_dictionary"])
        self.assertEqual(row["hardware_assessment"], "not_established")
        self.assertEqual(result["summary"]["all_works"]["full_text_scanned_no_dictionary_mentions_work_count"], 0)
        self.assertNotIn("no_hardware", json.dumps(result))

    def test_body_fetch_failures_do_not_become_absence_or_scanned(self):
        payload, _, _ = fixture()
        for status in ("unavailable", "blocked", "identity_mismatch"):
            with self.subTest(status=status):
                obs = observation(payload["works"][0]["work_id"], status=status)
                result = self.census(payload, observations=[obs], scans=[scan(obs, dictionary_fixture())])
                row = result["rows"][0]
                self.assertEqual(row["body_source_state"], status)
                self.assertFalse(row["full_text_screened_current_dictionary"])
                self.assertFalse(row["verified_usage_seen"])
                self.assertEqual(result["summary"]["all_works"]["full_text_failed_work_count"], 1)

    def test_current_body_scan_needs_both_hashes_and_available_observation(self):
        payload, _, _ = fixture()
        obs = observation(payload["works"][0]["work_id"])
        dictionary = dictionary_fixture()
        record = scan(obs, dictionary)
        result = self.census(payload, scans=[record], observations=[obs])
        row = result["rows"][0]
        self.assertTrue(row["full_text_screened_current_dictionary"])
        self.assertFalse(row["verified_usage_seen"])
        self.assertEqual(row["body_mention_count"], 1)
        self.assertEqual(self.census(payload, scans=[record])["rows"][0]["body_scan_status"], "not_attempted")
        changed = copy.deepcopy(dictionary)
        changed["entries"][0]["aliases"].append("New G1 spelling")
        stale = self.census(payload, dictionary=changed, scans=[record], observations=[obs])["rows"][0]
        self.assertEqual(stale["body_scan_status"], "pending_current_dictionary_scan")
        self.assertEqual(stale["body_mention_count"], 0)
        stale_text = self.census(payload, scans=[record], observations=[{**obs, "text_sha256": "new-body"}])["rows"][0]
        self.assertFalse(stale_text["full_text_screened_current_dictionary"])

    def test_partial_body_is_explicitly_not_full_text_screened(self):
        payload, _, _ = fixture()
        obs = observation(payload["works"][0]["work_id"], status="partial_text")
        result = self.census(payload, observations=[obs], scans=[scan(obs, dictionary_fixture())])
        row = result["rows"][0]
        self.assertFalse(row["full_text_screened_current_dictionary"])
        self.assertTrue(row["partial_text_screened_current_dictionary"])
        self.assertEqual(row["body_scan_status"], "partial_text_only_scanned")
        self.assertEqual(result["summary"]["all_works"]["full_text_screened_current_dictionary_work_count"], 0)

    def test_body_no_hit_is_dictionary_no_mention_not_no_hardware(self):
        payload, _, _ = fixture()
        obs = observation(payload["works"][0]["work_id"])
        result = self.census(payload, observations=[obs], scans=[scan(obs, dictionary_fixture(), text="No model is explicitly named.")])
        self.assertEqual(result["summary"]["all_works"]["full_text_scanned_no_dictionary_mentions_work_count"], 1)
        self.assertFalse(result["rows"][0]["verified_usage_seen"])
        self.assertTrue(all(row["candidate_kind"] != "body_mention" for row in result["candidates"]))

    def test_authority_verified_relationship_does_not_certify_fulltext_review(self):
        payload, authority, _ = fixture()
        result = self.census(payload, authority)
        row = result["rows"][0]
        self.assertTrue(row["verified_usage_seen"])
        self.assertEqual(result["summary"]["all_works"]["verified_relationship_work_count"], 1)
        self.assertEqual(row["body_source_state"], "not_attempted")
        self.assertFalse(row["full_text_screened_current_dictionary"])
        self.assertNotIn("reviewed_fulltext_count", json.dumps(result))

    def test_canonical_alias_mapping_and_purity(self):
        payload, authority, _ = fixture()
        old = payload["works"][0]["work_id"]
        payload["works"][0].update(work_id="doi:10.1234/g1", aliases=[old])
        dictionary = dictionary_fixture()
        obs = observation(old)
        scans = [scan(obs, dictionary)]
        before = copy.deepcopy((payload, authority, dictionary, scans, [obs]))
        result = self.census(payload, authority, dictionary, scans, [obs])
        self.assertEqual((payload, authority, dictionary, scans, [obs]), before)
        self.assertEqual(result["rows"][0]["work_id"], "doi:10.1234/g1")
        self.assertTrue(result["rows"][0]["verified_usage_seen"])
        self.assertTrue(all(row["work_id"] == "doi:10.1234/g1" for row in result["candidates"]))

    def test_version_or_reference_does_not_promote_candidate_authority(self):
        payload, authority, _ = fixture()
        authority["usage-evidence"][0].update(review_status="candidate", role="mentioned")
        obs = observation(payload["works"][0]["work_id"], version="v9")
        record = scan(obs, dictionary_fixture())
        record["matches"] = detect_mentions("Unitree G1 was used by a cited baseline.", dictionary_fixture(), "References")
        result = self.census(payload, authority, scans=[record], observations=[obs])
        self.assertFalse(result["rows"][0]["verified_usage_seen"])
        body = next(row for row in result["candidates"] if row["candidate_kind"] == "body_mention")
        self.assertEqual(body["section"], "References")
        self.assertEqual(body["source_version"], "v9")
        self.assertEqual(body["evidence_status"], "unverified_mention")

    def test_public_candidates_omit_excerpts_and_private_option_preserves_them(self):
        public = self.census()
        private = self.census(include_excerpts=True)
        self.assertTrue(public["candidates"])
        self.assertTrue(all("excerpt" not in row for row in public["candidates"]))
        self.assertTrue(all("excerpt" in row for row in private["candidates"]))

    def test_public_source_scans_can_omit_original_source_excerpts(self):
        payload, _, _ = fixture()
        obs = observation(payload["works"][0]["work_id"])
        record = scan(obs, dictionary_fixture())
        record["matches"] = [{key: value for key, value in match.items() if key != "excerpt"} for match in record["matches"]]
        result = self.census(payload, scans=[record], observations=[obs])
        self.assertTrue(result["rows"][0]["full_text_screened_current_dictionary"])
        self.assertTrue(all("excerpt" not in row for row in result["candidates"]))

    def test_duplicate_source_and_scan_records_do_not_inflate_mentions(self):
        payload, _, _ = fixture()
        obs = observation(payload["works"][0]["work_id"])
        record = scan(obs, dictionary_fixture())
        record["matches"] *= 2
        result = self.census(payload, scans=[record, record], observations=[obs, obs])
        self.assertEqual(result["rows"][0]["body_mention_count"], 1)
        self.assertEqual(sum(row["candidate_kind"] == "body_mention" for row in result["candidates"]), 1)

    def test_failed_refetch_and_future_observation_are_explicit(self):
        payload, _, _ = fixture()
        obs = observation(payload["works"][0]["work_id"])
        later = {**obs, "status": "blocked", "observed_at": "2026-09-14T03:00:00Z"}
        result = self.census(payload, scans=[scan(obs, dictionary_fixture())], observations=[obs, later])
        self.assertEqual(result["rows"][0]["body_source_state"], "blocked")
        self.assertEqual(result["rows"][0]["source_status_counts"], {"blocked": 1, "full_text_available": 1})
        self.assertFalse(result["rows"][0]["full_text_screened_current_dictionary"])
        future = {**later, "observed_at": "2026-09-15T01:00:00Z"}
        self.assertEqual(self.census(payload, observations=[future])["rows"][0]["body_source_state"], "not_attempted")

    def test_same_second_appended_partial_correction_supersedes_old_full_status(self):
        payload, _, _ = fixture()
        wid = payload['works'][0]['work_id']
        # Deliberately exercise a pair where fingerprint ordering would have
        # restored the older full status; ledger order must win instead.
        for seed in range(100):
            previous = observation(wid, observation_id=f'observation:old:{seed}')
            corrected = {**previous, 'status': 'partial_text', 'observation_id': f'observation:new:{seed}',
                         'parent_observation_id': previous['observation_id'],
                         'processing_basis': 'cached_raw_reparse_no_network',
                         'transport_verification': 'incomplete', 'transport_complete': False}
            if fingerprint(previous) > fingerprint(corrected):
                break
        else:
            self.fail('Fixture did not exercise reversed fingerprint ordering')
        result = self.census(payload, observations=[previous, corrected], scans=[scan(previous, dictionary_fixture())])
        row = result['rows'][0]
        self.assertEqual(row['source_observations'][0]['observation_id'], corrected['observation_id'])
        self.assertEqual(row['body_source_state'], 'partial_text')
        self.assertFalse(row['full_text_screened_current_dictionary'])
        self.assertTrue(row['partial_text_screened_current_dictionary'])
        self.assertEqual(result['summary']['all_works']['full_text_screened_current_dictionary_work_count'], 0)

    def test_missing_abstract_and_uncertain_month_are_not_filled_in(self):
        payload, _, _ = fixture()
        payload["works"][0].update(abstract=None, first_public_date_precision="year")
        result = self.census(payload)
        self.assertEqual(result["summary"]["all_works"]["metadata_missing_abstract_work_count"], 1)
        self.assertEqual(result["rows"][0]["first_public_month"], "unknown")
        self.assertEqual(result["rows"][0]["metadata_scan"]["nonempty_fields"], ["title"])

    def test_scan_without_hashes_fails_closed(self):
        payload, _, _ = fixture()
        obs = observation(payload["works"][0]["work_id"])
        record = scan(obs, dictionary_fixture())
        for key in ("dictionary_hash", "content_hash"):
            with self.subTest(key=key):
                bad = {field: value for field, value in record.items() if field != key}
                with self.assertRaisesRegex(ValueError, "scan_hashes"):
                    self.census(payload, scans=[bad], observations=[obs])

    def test_load_catalog_preserves_all_states_and_rejects_duplicate_shards(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.json").write_text("{}")
            (root / "works").mkdir()
            records = [make_work(1), make_work(2, status="excluded")]
            (root / "works/00.jsonl").write_text("\n".join(json.dumps(row) for row in records))
            self.assertEqual(len(load_catalog(root)[0]["works"]), 2)
            (root / "works/01.jsonl").write_text(json.dumps(records[0]))
            with self.assertRaisesRegex(ValueError, "duplicate_or_missing_work_id"):
                load_catalog(root)

    def test_export_is_derived_and_cli_rejects_authority_target(self):
        result = self.census()
        with tempfile.TemporaryDirectory() as directory:
            export_census(result, directory)
            self.assertEqual({path.name for path in Path(directory).iterdir()}, {"summary.json", "coverage.jsonl", "candidates.jsonl"})
            self.assertEqual(len(Path(directory, "coverage.jsonl").read_text().splitlines()), 1)
            self.assertNotIn("excerpt", Path(directory, "candidates.jsonl").read_text())
        with self.assertRaises(SystemExit), redirect_stderr(StringIO()):
            main(["--output", str(ROOT / "data/equipment"), "--as-of", AS_OF])


if __name__ == "__main__":
    unittest.main()
