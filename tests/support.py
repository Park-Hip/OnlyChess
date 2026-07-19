"""Loading the shipped mods together with a test fixture.

Two mods live outside `mods/` on purpose: the walking skeleton and the Prism Arena proof mod are
verification apparatus, not content a player should be offered. Core cannot filter them out at
discovery — that would mean naming a mod, which the prime directive forbids — so the only place the
shipped/not-shipped distinction can live is the directory, and a test that wants one has to say so.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures"


class WithFixtureMods(unittest.TestCase):
    """A `mods` directory holding everything shipped plus the named fixtures."""

    fixtures: tuple[str, ...] = ()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._staging = tempfile.TemporaryDirectory()
        cls.mods_dir = Path(cls._staging.name) / "mods"
        shutil.copytree(REPO_ROOT / "mods", cls.mods_dir)
        for name in cls.fixtures:
            shutil.copytree(FIXTURES / name, cls.mods_dir / name)

    @classmethod
    def tearDownClass(cls):
        cls._staging.cleanup()
        super().tearDownClass()
