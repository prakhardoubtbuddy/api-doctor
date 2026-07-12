# Minimal test skeleton for acquire module
import unittest
import os
from modules.acquire import clone, StackReport

class TestAcquire(unittest.TestCase):
    def test_clone_bad_url(self):
        with self.assertRaises(Exception):
            clone("https://github.com/no-such-org/no-such-repo-abcdefg")

    # More tests will be added once detect is implemented

if __name__ == "__main__":
    unittest.main()
