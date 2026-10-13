import json
import sys
import tempfile
import subprocess
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_weekly_recovery_supervisor import run_supervised


class RecoverySupervisorTest(unittest.TestCase):
    def test_normal_and_failed_exit_are_durably_recorded(self):
        for code in (0,7):
            with tempfile.TemporaryDirectory() as folder:
                root=Path(folder);record=root/'record.json'
                self.assertEqual(run_supervised([sys.executable,'-c',f'raise SystemExit({code})'],root,record,seconds=5),code)
                data=json.loads(record.read_text());self.assertEqual(data['exit_code'],code)
                self.assertIn('finished_at',data);self.assertIn('pid',data)

    def test_timeout_terminates_own_process_and_records_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);record=root/'record.json'
            with self.assertRaises(subprocess.TimeoutExpired):
                run_supervised([sys.executable,'-c','import time;time.sleep(10)'],root,record,seconds=.05)
            data=json.loads(record.read_text());self.assertEqual(data['status'],'failed');self.assertIsNotNone(data['exit_code'])
