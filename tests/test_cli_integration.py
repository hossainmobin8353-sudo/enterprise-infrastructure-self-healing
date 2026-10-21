import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class CLITests(unittest.TestCase):
    def test_end_to_end_scan_approve_plan_audit(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            env = os.environ.copy()
            env['PYTHONPATH'] = str(ROOT / 'src')
            env['SELFHEAL_APPROVAL_SECRET'] = 'integration-test-secret-very-long-value-2026'
            inc = base / 'incidents.json'
            audit = base / 'audit.jsonl'
            approval = base / 'approval.json'
            action = base / 'plan.json'
            def cli(*args):
                return subprocess.run([sys.executable, '-m', 'selfheal.cli', *args], cwd=ROOT, env=env, capture_output=True, text=True)
            result = cli('scan', '--out', str(inc), '--audit', str(audit))
            self.assertEqual(result.returncode, 0, result.stderr)
            incidents = json.loads(inc.read_text())
            self.assertEqual(len(incidents), 1)
            identifier=incidents[0]['id']
            result=cli('approve', '--incidents', str(inc), '--id', identifier, '--operator', 'test-operator', '--out', str(approval), '--audit', str(audit))
            self.assertEqual(result.returncode, 0, result.stderr)
            result=cli('plan', '--incidents', str(inc), '--id', identifier, '--approval', str(approval), '--out', str(action), '--audit', str(audit))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(action.read_text())['execution_status'], 'NOT_EXECUTED')
            result=cli('verify-audit', '--audit', str(audit))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(audit.read_text().splitlines()), 3)

if __name__ == '__main__':
    unittest.main()
