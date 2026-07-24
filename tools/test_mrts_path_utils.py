"""Focused path-boundary tests for the MRTS runner."""

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
MRTS_DIRECTORY = ROOT / "mrts"
sys.path.insert(0, str(MRTS_DIRECTORY))

MRTS_SPEC = importlib.util.spec_from_file_location("mrts_runner", MRTS_DIRECTORY / "mrts.py")
if MRTS_SPEC is None or MRTS_SPEC.loader is None:
    raise RuntimeError("cannot load MRTS runner")
MRTS_RUNNER = importlib.util.module_from_spec(MRTS_SPEC)
MRTS_SPEC.loader.exec_module(MRTS_RUNNER)

from path_utils import path_within


class PathWithinTests(unittest.TestCase):
    def test_allows_a_regular_child_path(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.assertEqual(path_within(root, "nested/output.conf", "output"), root / "nested" / "output.conf")

    def test_rejects_traversal_and_absolute_paths(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            outside_path = root.parent / "escaped.conf"
            with self.assertRaises(ValueError):
                path_within(root, "../escaped.conf", "output")
            with self.assertRaises(ValueError):
                path_within(root, outside_path, "output")


class MrtsLoadTests(unittest.TestCase):
    def test_rejects_a_symlinked_load_file_outside_the_infrastructure_root(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            infrastructure = root / "infrastructure"
            infrastructure.mkdir()
            outside = root / "outside.load"
            outside.write_text("safe\n", encoding="utf-8")
            (infrastructure / "mrts.load").symlink_to(outside)

            with self.assertRaises(ValueError):
                MRTS_RUNNER.write_mrts_load(infrastructure, "/rules/*.conf", False)

            self.assertEqual(outside.read_text(encoding="utf-8"), "safe\n")

    def test_writes_and_removes_the_expected_load_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            infrastructure = Path(temporary_directory)

            MRTS_RUNNER.write_mrts_load(infrastructure, "/rules/*.conf", False)

            load_file = infrastructure / "mrts.load"
            self.assertEqual(load_file.read_text(encoding="utf-8"), "Include /rules/*.conf\n")
            MRTS_RUNNER.delete_mrts_load(infrastructure, False)
            self.assertFalse(load_file.exists())


if __name__ == "__main__":
    unittest.main()
