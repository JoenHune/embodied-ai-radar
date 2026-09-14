import json
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from collect_hardware_sources import (Collector, arxiv_identity, assess_html, digest,
                                      fetch_html, fetch_html_curl, load_targets, read_queue,
                                      retry_after_seconds, utc_timestamp)


TARGET = {"work_id": "arxiv:2407.02648", "arxiv_id": "2407.02648", "version": "v1",
          "source_url": "https://arxiv.org/html/2407.02648v1"}


def html(aid="2407.02648v1", *, long=True, proof=True):
    paragraph = "We use a Franka Panda robot and an Intel RealSense D435 camera for manipulation experiments. "
    text = paragraph * (12 if long else 1)
    identity_tag = f'<meta name="citation_arxiv_id" content="{aid}">' if proof else ""
    return (f'<html><head>{identity_tag}</head>'
            '<body><nav>Site navigation GPU cards</nav><article class="ltx_document">'
            '<h1>Robot paper</h1><div class="ltx_abstract">Abstract only XArm</div>'
            '<section id="S1"><h2>1 Methods</h2><p>' + text + '</p><cite class="ltx_cite">[99 A100]</cite>'
            '<section id="S1.1"><h3>1.1 Sensors</h3><p>D435 calibration.</p></section></section>'
            '<section id="S2"><h2>II Related Work</h2><p>Unitree Go2 used by others</p>'
            '<section><h3>Past results</h3><p>Other robots</p></section></section>'
            '<section id="S3"><h2>3 Experiments</h2><p>' + text + '</p>'
            '<figure><figcaption>Figure 1: Allegro Hand camera placement.</figcaption></figure></section>'
            '<section id="A1" class="ltx_appendix"><h2>Appendix A Details</h2><p>Two NVIDIA A100 GPUs.</p></section>'
            '<section id="bib"><h2>References</h2><ol><li>Bibliographic Jetson Orin</li></ol></section>'
            '</article><footer>arXiv copyright</footer></body></html>').encode()


class Clock:
    def __init__(self):
        self.now = 1750000000.0
        self.waits = []

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.waits.append(seconds)
        self.now += seconds


class HardwareSourceTests(unittest.TestCase):
    def test_identity_is_strict(self):
        self.assertEqual(arxiv_identity("https://arxiv.org/abs/2407.02648v2"), ("2407.02648", "v2"))
        self.assertEqual(arxiv_identity("hep-th/9901001v1"), ("hep-th/9901001", "v1"))
        self.assertIsNone(arxiv_identity("https://example.org/abs/2407.02648v2"))
        self.assertIsNone(arxiv_identity("Read paper 2407.02648"))

    def test_full_body_keeps_methods_experiments_appendix_captions(self):
        observation, blocks = assess_html(html(), TARGET, TARGET["source_url"])
        self.assertEqual(observation["status"], "full_text_available")
        self.assertFalse(observation["manual_reviewed"])
        self.assertEqual(observation["version"], "v1")
        self.assertEqual(observation["section_count"], 4)
        body = " ".join(row["text"] for row in blocks)
        for phrase in ("Franka Panda", "D435 calibration", "Allegro Hand", "NVIDIA A100"):
            self.assertIn(phrase, body)
        for phrase in ("navigation", "Abstract only", "Unitree", "Past results", "Jetson Orin", "[99", "copyright"):
            self.assertNotIn(phrase, body)
        self.assertEqual(sum(row["text"].count("D435 calibration") for row in blocks), 1)

    def test_v2_excludes_abstract_and_numbered_related_works_sections(self):
        for heading in ('Abstract', 'ABSTRACT', '2 Related Works', 'II. Related Works',
                        '3.2 Prior Work', 'Appendix A: Literature Review'):
            with self.subTest(heading=heading):
                omitted = ('<section><h2>' + heading + '</h2><p>ONLY_EXCLUDED_DEVICE</p>'
                           '<section><h3>Nested survey</h3><p>EXCLUDED_NESTED_DEVICE</p></section></section>')
                raw = html().replace(b'</article>', omitted.encode() + b'</article>')
                observation, blocks = assess_html(raw, TARGET, TARGET['source_url'])
                body = ' '.join(block['text'] for block in blocks)
                self.assertEqual(observation['parser_version'], 'arxiv-html-body-v2')
                self.assertIn('abstract', observation['excluded_sections'])
                self.assertNotIn('ONLY_EXCLUDED_DEVICE', body)
                self.assertNotIn('EXCLUDED_NESTED_DEVICE', body)
                self.assertIn('Franka Panda', body)
                self.assertEqual(observation['status'], 'full_text_available')

    def test_mismatch_and_missing_proof_cannot_be_fulltext(self):
        for raw, reason in ((html("2407.11111v1"), "page_identity_mismatch"),
                            (html("2407.02648v2"), "page_version_mismatch"),
                            (html(proof=False), "missing_page_identity_proof")):
            observation, blocks = assess_html(raw, TARGET, TARGET["source_url"])
            self.assertEqual(observation["status"], "identity_mismatch")
            self.assertEqual(observation["error"], reason)
            self.assertEqual(blocks, [])

    def test_bibliography_abs_link_is_not_identity_proof(self):
        raw = html(proof=False).replace(b"<p>", b'<p><a href="https://arxiv.org/abs/2407.02648v1">citation</a>', 1)
        observation, _ = assess_html(raw, TARGET, TARGET["source_url"])
        self.assertEqual(observation["status"], "identity_mismatch")

    def test_canonical_abs_proof_and_versionless_response(self):
        raw = html(proof=False).replace(b"<head>", b'<head><link rel="canonical" href="https://arxiv.org/abs/2407.02648v1">')
        observation, _ = assess_html(raw, TARGET, TARGET["source_url"])
        self.assertEqual(observation["status"], "full_text_available")
        latest = {**TARGET, "version": None, "source_url": "https://arxiv.org/html/2407.02648"}
        observation, _ = assess_html(html("2407.02648"), latest, latest["source_url"])
        self.assertEqual(observation["status"], "partial_text")
        self.assertIn("version_unresolved", observation["error"])

    def test_summary_error_and_short_pages_never_fulltext(self):
        raw = b'<meta name="citation_arxiv_id" content="2407.02648v1"><h1>Abstract</h1><blockquote>Franka robot</blockquote>'
        observation, _ = assess_html(raw, TARGET, TARGET["source_url"])
        self.assertEqual(observation["status"], "unavailable")
        observation, _ = assess_html(html(), TARGET, "https://arxiv.org/abs/2407.02648v1")
        self.assertEqual(observation["status"], "unavailable")
        observation, _ = assess_html(html(long=False), TARGET, TARGET["source_url"])
        self.assertEqual(observation["status"], "partial_text")
        self.assertIn("body_below_character_threshold", observation["error"])
        observation, _ = assess_html(b"<title>Access Denied</title>", TARGET, TARGET["source_url"])
        self.assertEqual(observation["status"], "blocked")

    def test_severe_conversion_errors_are_partial(self):
        raw = html().replace(b"</article>", b'<span class="ltx_ERROR">conversion error</span>' * 5 + b"</article>")
        observation, _ = assess_html(raw, TARGET, TARGET["source_url"])
        self.assertEqual(observation["status"], "partial_text")
        self.assertEqual(observation["conversion_error_markers"], 5)

    def test_caption_only_body_fails_section_threshold(self):
        raw = b'<meta name="citation_arxiv_id" content="2407.02648v1"><article><figure><figcaption>' + b"Franka " * 500 + b"</figcaption></figure></article>"
        observation, _ = assess_html(raw, TARGET, TARGET["source_url"])
        self.assertEqual(observation["status"], "partial_text")
        self.assertIn("body_below_section_threshold", observation["error"])

    def test_canonical_mapping_versions_and_queue_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "works.jsonl").write_text(json.dumps({"work_id": TARGET["work_id"], "identifiers": {"arxiv": TARGET["arxiv_id"]}}) + "\n")
            snapshots = [{"work_id": TARGET["work_id"], "source_url": f"https://arxiv.org/abs/2407.02648v{version}", "version": f"v{version}"} for version in (1, 2)]
            (root / "text-snapshots.jsonl").write_text("\n".join(map(json.dumps, snapshots)))
            resolved = load_targets(root, [TARGET["work_id"], TARGET["work_id"]])
            self.assertEqual(len(resolved), 1)
            self.assertEqual(resolved[0]["version"], "v2")
            self.assertEqual(load_targets(root, [TARGET])[0]["version"], "v1")
            for queue in (["arxiv:made-up"], [{**TARGET, "arxiv_id": "2407.11111"}], [{**TARGET, "version": "v3"}]):
                with self.assertRaises(ValueError):
                    load_targets(root, queue)

    def test_non_arxiv_identity_is_explicit_unavailable_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "works.jsonl").write_text(json.dumps({"work_id": "doi:10.1/test", "identifiers": {"doi": "10.1/test"}}))
            row = load_targets(root, ["doi:10.1/test"])[0]
            self.assertIsNone(row["arxiv_id"])
            self.assertEqual(row["resolution_error"], "no_canonical_arxiv_identity")

    def test_queue_shapes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "queue.json"
            for value in ([TARGET], {"queue": [TARGET]}, TARGET):
                path.write_text(json.dumps(value))
                self.assertEqual(read_queue(path), [TARGET])
            path.write_text(json.dumps(TARGET) + "\n" + json.dumps(TARGET))
            self.assertEqual(read_queue(path), [TARGET, TARGET])

    def test_cache_resume_hashes_and_export_idempotence(self):
        with tempfile.TemporaryDirectory() as directory:
            clock, calls = Clock(), []
            def fetch(url, timeout):
                calls.append((url, timeout))
                return {"http_status": 200, "effective_url": url, "raw": html(), "headers": {}}
            cache, output = Path(directory) / "cache", Path(directory) / "observations.jsonl"
            collector = Collector(cache, output, fetcher=fetch, clock=clock.time, sleeper=clock.sleep)
            row, fresh = collector.collect(TARGET)
            self.assertTrue(fresh)
            self.assertEqual(row["raw_sha256"], digest(Path(row["cache_ref"]).read_bytes()))
            self.assertEqual(row["text_sha256"], digest(Path(row["body_cache_ref"]).read_bytes()))
            self.assertIsInstance(json.loads(Path(row["blocks_ref"]).read_text()), list)
            self.assertNotIn("Franka Panda", output.read_text())
            self.assertEqual(collector.collect(TARGET), (row, False))
            resumed = Collector(cache, output, fetcher=fetch, clock=clock.time, sleeper=clock.sleep)
            self.assertEqual(resumed.collect(TARGET), (row, False))
            recovered_output = Path(directory) / "recovered.jsonl"
            recovered = Collector(cache, recovered_output, fetcher=fetch, clock=clock.time, sleeper=clock.sleep)
            self.assertEqual(recovered.collect(TARGET), (row, False))
            self.assertEqual(len(calls), 1)
            self.assertEqual(len(output.read_text().splitlines()), 1)
            self.assertEqual(recovered_output.read_text(), output.read_text())

    def test_pacing_is_persistent_between_instances(self):
        with tempfile.TemporaryDirectory() as directory:
            clock, call_times = Clock(), []
            def fetch(url, timeout):
                call_times.append(clock.time())
                return {"http_status": 200, "effective_url": url, "raw": html(), "headers": {}}
            cache, output = Path(directory) / "cache", Path(directory) / "out.jsonl"
            Collector(cache, output, fetcher=fetch, clock=clock.time, sleeper=clock.sleep).collect(TARGET)
            Collector(cache, output, fetcher=fetch, clock=clock.time, sleeper=clock.sleep).collect({**TARGET, "work_id": "second"})
            self.assertGreaterEqual(call_times[1] - call_times[0], 3)
            with self.assertRaises(ValueError):
                Collector(cache, output, interval=0)

    def test_interrupted_export_tail_is_preserved_and_resumed(self):
        with tempfile.TemporaryDirectory() as directory:
            calls = []
            def fetch(url, timeout):
                calls.append(url)
                return {"http_status": 200, "effective_url": url, "raw": html(), "headers": {}}
            cache, output = Path(directory) / "cache", Path(directory) / "out.jsonl"
            row, _ = Collector(cache, output, fetcher=fetch).collect(TARGET)
            output.write_bytes(output.read_bytes() + b'{"observation_id":"interrupted')
            collector = Collector(cache, output, fetcher=fetch)
            self.assertEqual(collector.collect(TARGET), (row, False))
            self.assertEqual(len(output.read_text().splitlines()), 1)
            self.assertEqual(len(list(Path(directory).glob("out.jsonl.interrupted-tail.*"))), 1)
            self.assertEqual(len(calls), 1)

    def test_resume_does_not_consume_new_observation_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            clock, calls = Clock(), []
            def fetch(url, timeout):
                calls.append(url)
                return {"http_status": 200, "effective_url": url, "raw": html(), "headers": {}}
            collector = Collector(Path(directory) / "cache", Path(directory) / "out.jsonl", fetcher=fetch, clock=clock.time, sleeper=clock.sleep)
            collector.collect(TARGET)
            result = collector.run([TARGET, {**TARGET, "work_id": "second"}, {**TARGET, "work_id": "third"}], limit=1)
            self.assertEqual(result["attempted"], 1)
            self.assertEqual(result["resumed"], 1)
            self.assertEqual(len(calls), 2)

    def test_blocked_stops_batch_retry_after_and_resume_cannot_bypass(self):
        with tempfile.TemporaryDirectory() as directory:
            clock, calls = Clock(), []
            def fetch(url, timeout):
                calls.append(url)
                return {"http_status": 429, "effective_url": url, "raw": b"Too Many Requests", "headers": {"Retry-After": "120"}}
            collector = Collector(Path(directory) / "cache", Path(directory) / "out.jsonl", fetcher=fetch, clock=clock.time, sleeper=clock.sleep)
            result = collector.run([TARGET, {**TARGET, "work_id": "second"}])
            self.assertEqual(result["attempted"], 1)
            row, fresh = collector.collect(TARGET, retry_failed=True)
            self.assertFalse(fresh)
            self.assertEqual(row["status"], "blocked")
            self.assertEqual(len(calls), 1)
            self.assertIsNone(row["text_sha256"])
            self.assertEqual(json.loads(collector.pacing_file.read_text())["next_request_at"], clock.time() + 120)

    def test_403_and_404_are_not_negative_hardware_findings(self):
        for code, expected in ((403, "blocked"), (404, "unavailable")):
            with tempfile.TemporaryDirectory() as directory:
                def fetch(url, timeout):
                    return {"http_status": code, "effective_url": url, "raw": b"error", "headers": {}}
                collector = Collector(Path(directory) / "cache", Path(directory) / "out.jsonl", fetcher=fetch)
                row, _ = collector.collect(TARGET)
                self.assertEqual(row["status"], expected)
                self.assertNotIn("matches", row)
                self.assertNotIn("hardware_absent", row)

    def test_retry_after_parses_seconds_and_date(self):
        self.assertEqual(retry_after_seconds({"Retry-After": "120"}, 0), 120)
        self.assertEqual(retry_after_seconds({"retry-after": "Thu, 01 Jan 1970 00:02:00 GMT"}, 0), 120)
        self.assertEqual(retry_after_seconds({"Retry-After": "invalid"}, 0), 0)

    def test_curl_200_nonzero_exit_is_not_an_available_body(self):
        for returncode in (18, 28, 63):
            with self.subTest(returncode=returncode), tempfile.TemporaryDirectory() as directory:
                def fake_run(command, **kwargs):
                    self.assertNotIn('--location', command)
                    Path(command[command.index('--output') + 1]).write_bytes(html())
                    Path(command[command.index('--dump-header') + 1]).write_text(
                        'HTTP/1.1 200 Connection established\r\nProxy-Header: ignored\r\n\r\n'
                        'HTTP/2 200\r\nContent-Type: text/html\r\n\r\n')
                    return SimpleNamespace(returncode=returncode, stdout='200', stderr='partial transfer')
                clock = Clock()
                with patch('collect_hardware_sources.subprocess.run', side_effect=fake_run) as runner:
                    response = fetch_html_curl(TARGET['source_url'])
                self.assertEqual(response['http_status'], 200)
                self.assertEqual(response['transport_returncode'], returncode)
                self.assertEqual(response['error'], f'curl_transport_error:{returncode}')
                self.assertEqual(response['truncated'], returncode == 63)
                self.assertNotIn('Proxy-Header', response['headers'])
                runner.assert_called_once()
                collector = Collector(Path(directory) / 'cache', Path(directory) / 'observations.jsonl',
                                      fetcher=lambda *args, **kwargs: response, clock=clock.time, sleeper=clock.sleep)
                row, fresh = collector.collect(TARGET)
                self.assertTrue(fresh)
                self.assertEqual(row['status'], 'unavailable')
                self.assertEqual(row['error'], f'curl_transport_error:{returncode}')
                self.assertIsNone(row['text_sha256'])
                self.assertIsNone(row['blocks_ref'])
                self.assertTrue(Path(row['cache_ref']).is_file())
                self.assertEqual(collector.collect(TARGET, retry_failed=True), (row, False))

    def test_successful_curl_body_and_process_failures(self):
        def fake_run(command, **kwargs):
            Path(command[command.index('--output') + 1]).write_bytes(html())
            Path(command[command.index('--dump-header') + 1]).write_text('HTTP/2 200\nContent-Type: text/html\n')
            return SimpleNamespace(returncode=0, stdout='200', stderr='')
        with patch('collect_hardware_sources.subprocess.run', side_effect=fake_run):
            response = fetch_html_curl(TARGET['source_url'])
        self.assertIsNone(response['error'])
        self.assertFalse(response['truncated'])
        self.assertEqual(assess_html(response['raw'], TARGET, TARGET['source_url'])[0]['status'], 'full_text_available')
        with patch('collect_hardware_sources.subprocess.run', side_effect=OSError('private details')):
            failed = fetch_html_curl(TARGET['source_url'])
        self.assertIsNone(failed['http_status'])
        self.assertEqual(failed['raw'], b'')
        self.assertEqual(failed['error'], 'OSError')


class NetworkSchedulingTests(unittest.TestCase):
    """Temporary caches and deterministic time only; never perform network I/O."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.cache = Path(temporary.name) / 'cache'
        self.output = Path(temporary.name) / 'observations.jsonl'
        self.clock = Clock()
        self.started_at = self.clock.time()
        self.calls = []
        self.responses = []

    @staticmethod
    def response(code=200, *, returncode=0, headers=None, elapsed=0):
        return {'http_status': code, 'effective_url': TARGET['source_url'],
                'headers': headers or {}, 'raw': html() if code == 200 else b'',
                'transport_returncode': returncode,
                'error': f'curl_transport_error:{returncode}' if returncode else None,
                'elapsed': elapsed}

    def fetch(self, url, timeout):
        self.calls.append((url, self.clock.time()))
        response = self.responses.pop(0)
        self.clock.now += response.get('elapsed', 0)
        return response

    def collector(self, **kwargs):
        return Collector(self.cache, self.output, fetcher=self.fetch,
                         clock=self.clock.time, sleeper=self.clock.sleep, **kwargs)

    def target(self, index):
        return {**TARGET, 'work_id': f'fixture:{index}'}

    def pacing(self):
        return json.loads((self.cache / 'pacing.json').read_text())

    def test_isolated_timeout_continues_queue_after_minimum_interval(self):
        self.responses = [self.response(None, returncode=28, elapsed=20),
                          self.response(), self.response()]
        collector = self.collector()
        result = collector.run([self.target(i) for i in range(3)])
        self.assertEqual(result['attempted'], 3)
        self.assertEqual([at - self.started_at for _, at in self.calls], [0, 23, 26])
        self.assertEqual(sum(self.clock.waits), 6)
        row = json.loads(collector.state_path(self.target(0)).read_text())
        self.assertEqual(row['status'], 'unavailable')
        self.assertIsNone(row['text_sha256'])
        self.assertEqual(utc_timestamp(row['next_retry_at']), self.started_at + 20 + 3600)
        self.assertEqual(collector.collect(self.target(0), retry_failed=True), (row, False))
        self.assertEqual(len(self.calls), 3)

    def test_timeout_after_http_200_retains_raw_without_available_body(self):
        self.responses = [self.response(200, returncode=28), self.response()]
        collector = self.collector()
        row, _ = collector.collect(self.target(0))
        self.assertEqual(row['status'], 'unavailable')
        self.assertFalse(row['transport_complete'])
        self.assertIsNone(row['text_sha256'])
        self.assertIsNone(row['blocks_ref'])
        self.assertEqual(Path(row['cache_ref']).read_bytes(), html())
        collector.collect(self.target(1))
        self.assertEqual(self.calls[1][1] - self.calls[0][1], 3)

    def test_consecutive_timeouts_persist_and_open_capped_global_circuit(self):
        delays = [3, 60, 120, 240, 480, 960, 1920, 3840, 3840]
        self.responses = [self.response(None, returncode=28) for _ in delays]
        for index, delay in enumerate(delays):
            # Every request uses a fresh instance: restarting cannot reset the
            # circuit or remove the prior request's global deadline.
            self.collector().collect(self.target(index))
            state = self.pacing()
            self.assertEqual(state['consecutive_network_failures'], index + 1)
            self.assertEqual(state['next_request_at'] - self.clock.time(), delay)
        self.assertEqual(sum(self.clock.waits), sum(delays[:-1]))
        self.assertTrue(all(wait <= 30 for wait in self.clock.waits))

    def test_mixed_connection_failures_trip_circuit_and_success_resets_it(self):
        self.responses = [self.response(None, returncode=28), self.response(None, returncode=7),
                          self.response(None, returncode=6), self.response(),
                          self.response(None, returncode=28), self.response()]
        for index, expected_count in enumerate([1, 2, 3, 0, 1, 0]):
            self.collector().collect(self.target(index))
            self.assertEqual(self.pacing()['consecutive_network_failures'], expected_count)
        self.assertEqual([at - self.started_at for _, at in self.calls], [0, 3, 63, 183, 186, 189])

    def test_first_connection_error_keeps_global_backoff(self):
        self.responses = [self.response(None, returncode=7), self.response()]
        collector = self.collector()
        collector.collect(self.target(0))
        collector.collect(self.target(1))
        self.assertEqual(sum(self.clock.waits), 60)

    def test_complete_404_resets_connectivity_counter_without_promoting_body(self):
        self.responses = [self.response(None, returncode=28), self.response(404),
                          self.response(None, returncode=28)]
        collector = self.collector()
        collector.collect(self.target(0))
        row, _ = collector.collect(self.target(1))
        self.assertEqual(row['status'], 'unavailable')
        self.assertEqual(self.pacing()['consecutive_network_failures'], 0)
        collector.collect(self.target(2))
        self.assertEqual(self.pacing()['next_request_at'] - self.clock.time(), 3)

    def test_retry_after_stays_global_even_on_success_or_isolated_timeout(self):
        self.responses = [self.response(None, returncode=28, headers={'Retry-After': '120'}),
                          self.response(headers={'retry-after': '75'}), self.response()]
        collector = self.collector()
        for index in range(3):
            collector.collect(self.target(index))
        self.assertEqual([at - self.started_at for _, at in self.calls], [0, 120, 195])

    def test_server_errors_override_isolated_timeout_optimization(self):
        self.responses = [self.response(500), self.response(),
                          self.response(503, returncode=28, headers={'Retry-After': '90'}), self.response()]
        collector = self.collector()
        for index in range(4):
            collector.collect(self.target(index))
        self.assertEqual([at - self.started_at for _, at in self.calls], [0, 60, 63, 153])

    def test_403_and_429_stop_batch_even_with_timeout_and_keep_retry_after(self):
        for index, (code, header, expected_delay) in enumerate([(403, '1200', 1200), (429, '120', 120)]):
            with self.subTest(code=code):
                self.responses = [self.response(code, returncode=28, headers={'Retry-After': header})]
                collector = self.collector()
                before_calls = len(self.calls)
                result = collector.run([self.target(2 * index), self.target(2 * index + 1)])
                self.assertEqual(result['attempted'], 1)
                self.assertEqual(len(self.calls), before_calls + 1)
                self.assertEqual(self.pacing()['next_request_at'] - self.clock.time(), expected_delay)
                row, fresh = collector.collect(self.target(2 * index), retry_failed=True)
                self.assertFalse(fresh)
                self.assertEqual(row['status'], 'blocked')
                self.assertEqual(len(self.calls), before_calls + 1)

    def test_html_access_challenge_still_stops_batch(self):
        response = self.response()
        response['raw'] = b'<title>Access Denied</title>'
        self.responses = [response]
        result = self.collector().run([self.target(0), self.target(1)])
        self.assertEqual(result['attempted'], 1)
        self.assertEqual(result['statuses'], {'blocked': 1})
        self.assertEqual(self.pacing()['next_request_at'] - self.clock.time(), 900)

    def test_denial_without_retry_after_retains_default_floor(self):
        for index, (code, expected_delay) in enumerate([(403, 900), (429, 60)]):
            self.responses = [self.response(code)]
            self.collector().collect(self.target(index))
            self.assertEqual(self.pacing()['next_request_at'] - self.clock.time(), expected_delay)

    def test_long_retry_after_preserves_target_cooldown(self):
        self.responses = [self.response(None, returncode=28, headers={'Retry-After': '7200'})]
        collector = self.collector()
        row, _ = collector.collect(self.target(0))
        self.assertEqual(utc_timestamp(row['next_retry_at']), self.started_at + 7200)
        self.assertEqual(collector.collect(self.target(0), retry_failed=True), (row, False))
        self.assertEqual(len(self.calls), 1)

    def test_legacy_pacing_file_deadline_is_honored(self):
        self.cache.mkdir()
        (self.cache / 'pacing.json').write_text(json.dumps({'next_request_at': self.started_at + 45}))
        self.responses = [self.response(None, returncode=28)]
        self.collector().collect(self.target(0))
        self.assertEqual(sum(self.clock.waits), 45)
        self.assertEqual(self.pacing()['consecutive_network_failures'], 1)
        self.assertEqual(self.pacing()['next_request_at'] - self.clock.time(), 3)

    def test_interruption_preserves_reservation_and_releases_single_collector_lock(self):
        def interrupted(url, timeout):
            self.clock.now += 10
            raise KeyboardInterrupt()
        collector = Collector(self.cache, self.output, fetcher=interrupted,
                              clock=self.clock.time, sleeper=self.clock.sleep)
        with self.assertRaises(KeyboardInterrupt):
            collector.run([self.target(0)])
        self.assertEqual(self.pacing()['next_request_at'], self.started_at + 28)
        self.responses = [self.response()]
        self.assertEqual(self.collector().run([self.target(1)])['attempted'], 1)
        self.assertEqual(self.calls[0][1] - self.started_at, 28)
        self.assertEqual(sum(self.clock.waits), 18)

    def test_kernel_lock_rejects_second_collector_without_fetch(self):
        import fcntl
        collector = self.collector()
        with (self.cache / 'collector.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(RuntimeError, 'concurrent arXiv collection is prohibited'):
                collector.run([self.target(0)])
        self.assertEqual(self.calls, [])

    def test_interrupted_reservation_does_not_reset_prior_network_failures(self):
        self.responses = [self.response(None, returncode=28)]
        self.collector().collect(self.target(0))
        def interrupted(url, timeout):
            raise KeyboardInterrupt()
        collector = Collector(self.cache, self.output, fetcher=interrupted,
                              clock=self.clock.time, sleeper=self.clock.sleep)
        with self.assertRaises(KeyboardInterrupt):
            collector.collect(self.target(1))
        self.assertEqual(self.pacing()['consecutive_network_failures'], 1)
        self.responses = [self.response(None, returncode=28)]
        self.collector().collect(self.target(2))
        self.assertEqual(self.pacing()['consecutive_network_failures'], 2)
        self.assertEqual(self.pacing()['next_request_at'] - self.clock.time(), 60)

    def test_urllib_timeouts_are_structured_not_guessed_from_error_text(self):
        for exception, expected in [(TimeoutError('timed out'), 'timeout'),
                                    (urllib.error.URLError(TimeoutError('timed out')), 'timeout'),
                                    (urllib.error.URLError(OSError('connection refused')), 'connection')]:
            with self.subTest(exception=exception), patch('collect_hardware_sources.urllib.request.build_opener') as build:
                build.return_value.open.side_effect = exception
                response = fetch_html(TARGET['source_url'])
                self.assertEqual(response['transport_failure_kind'], expected)
                self.responses = [response]
                self.collector().collect(self.target(len(self.calls)))
                self.assertEqual(self.pacing()['consecutive_network_failures'], len(self.calls))

    def test_curl_wrapper_timeout_uses_isolated_timeout_policy(self):
        with patch('collect_hardware_sources.subprocess.run', side_effect=subprocess.TimeoutExpired(['curl'], 25)):
            response = fetch_html_curl(TARGET['source_url'])
        self.assertEqual(response['transport_failure_kind'], 'timeout')
        self.responses = [response, self.response()]
        collector = self.collector()
        collector.collect(self.target(0))
        collector.collect(self.target(1))
        self.assertEqual(sum(self.clock.waits), 3)

    def test_curl_process_timeout_preserves_received_denial_and_backoff_headers(self):
        for index, code in enumerate([403, 429, 503, 200]):
            with self.subTest(code=code):
                def timed_out(command, **kwargs):
                    Path(command[command.index('--dump-header') + 1]).write_text(
                        f'HTTP/2 {code}\nRetry-After: 1200\n')
                    Path(command[command.index('--output') + 1]).write_bytes(b'partial response')
                    raise subprocess.TimeoutExpired(command, 25)
                with patch('collect_hardware_sources.subprocess.run', side_effect=timed_out):
                    response = fetch_html_curl(TARGET['source_url'])
                self.assertEqual(response['http_status'], code)
                self.assertEqual(response['headers']['Retry-After'], '1200')
                self.assertEqual(response['raw'], b'partial response')
                self.responses = [response]
                result = self.collector().run([self.target(index)], limit=1)
                self.assertEqual(result['statuses'], {'blocked' if code in {403, 429} else 'unavailable': 1})
                self.assertEqual(self.pacing()['next_request_at'] - self.clock.time(), 1200)

    def test_urllib_read_timeout_preserves_retry_after(self):
        with patch('collect_hardware_sources.urllib.request.build_opener') as build:
            opened = build.return_value.open.return_value.__enter__.return_value
            opened.status, opened.url, opened.headers = 200, TARGET['source_url'], {'Retry-After': '120'}
            opened.read.side_effect = TimeoutError('body timed out')
            response = fetch_html(TARGET['source_url'])
        self.assertEqual(response['http_status'], 200)
        self.assertEqual(response['headers']['Retry-After'], '120')
        self.responses = [response, self.response()]
        collector = self.collector()
        collector.collect(self.target(0))
        collector.collect(self.target(1))
        self.assertEqual(sum(self.clock.waits), 120)

    def test_curl_missing_writeout_does_not_hide_received_429(self):
        def timed_out(command, **kwargs):
            Path(command[command.index('--dump-header') + 1]).write_text('HTTP/2 429\nRetry-After: 120\n')
            return SimpleNamespace(returncode=28, stdout='000', stderr='timed out')
        with patch('collect_hardware_sources.subprocess.run', side_effect=timed_out):
            response = fetch_html_curl(TARGET['source_url'])
        self.responses = [response]
        result = self.collector().run([self.target(0), self.target(1)])
        self.assertEqual(result['attempted'], 1)
        self.assertEqual(result['statuses'], {'blocked': 1})
        self.assertEqual(self.pacing()['next_request_at'] - self.clock.time(), 120)


if __name__ == "__main__":
    unittest.main()
