import unittest
import tempfile
import os
from modules import triage

class TestTriage(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="triage_test_")
        # Unsafe code sample generating two findings (eval + hardcoded password)
        self.code = """
def foo():
    password = "secret123"  # hardcoded password
    eval("print('bad idea')")
    return True
"""
        self.fpath = os.path.join(self.test_dir, "danger.py")
        with open(self.fpath, "w") as f:
            f.write(self.code)
    
    def tearDown(self):
        try:
            os.remove(self.fpath)
            os.rmdir(self.test_dir)
        except Exception:
            pass

    def test_triage_basic_findings(self):
        findings = triage.triage(self.test_dir)
        patterns = set(f.pattern for f in findings)
        found_eval = any('eval' in f.pattern for f in findings)
        found_password = any('hard' in f.signal.lower() for f in findings)
        self.assertTrue(found_eval, "Should flag eval usage")
        self.assertTrue(found_password, "Should flag hardcoded password")
        self.assertGreaterEqual(len(findings), 2)

if __name__ == '__main__':
    unittest.main()
