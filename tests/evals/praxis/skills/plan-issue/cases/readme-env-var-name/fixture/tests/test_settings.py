import os
import unittest
from pathlib import Path
from unittest import mock

from podfetch import settings


class SettingsTest(unittest.TestCase):
    def test_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(settings.limit(), 3)
            self.assertEqual(settings.download_dir(), Path.home() / "podfetch")

    def test_limit_from_environment(self):
        with mock.patch.dict(os.environ, {"PODFETCH_LIMIT": "5"}):
            self.assertEqual(settings.limit(), 5)
