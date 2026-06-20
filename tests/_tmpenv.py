"""Test helper: isolate XDG state in a temporary directory.

Every store and the config read the XDG base dirs at call time, so pointing the
environment at a temp dir gives each test a clean, throwaway state directory
without touching the developer's real ``~/.config``.
"""

from __future__ import annotations

import os
import tempfile
import unittest


class TempEnvTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp(prefix="econsole-test-")
        self._saved = {k: os.environ.get(k) for k in ("XDG_CONFIG_HOME", "XDG_DATA_HOME")}
        os.environ["XDG_CONFIG_HOME"] = os.path.join(self._tmp, "config")
        os.environ["XDG_DATA_HOME"] = os.path.join(self._tmp, "data")

    def tearDown(self) -> None:
        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)
