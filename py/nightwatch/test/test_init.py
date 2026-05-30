import nightwatch
import unittest

class TestInit(unittest.TestCase):
    def test_version_exists(self):
        self.assertTrue(hasattr(nightwatch, '__version__'))
