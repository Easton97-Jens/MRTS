"""Focused path-boundary tests for the MRTS runner."""

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


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


class ExecuteTestSetTests(unittest.TestCase):
    @staticmethod
    def successful_process():
        process = mock.Mock()
        process.stdout = [b"\xf0\x9f\x8e\x89\n"]
        return process

    def test_preserves_shell_metacharacters_as_single_argv_operands(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            configuration = root / "config;$(not-executed) --value.yaml"
            configuration.write_text("{}\n", encoding="utf-8")
            generated_tests = root / "tests $(not-executed); 'quoted'"
            generated_tests.mkdir()
            process = self.successful_process()

            with mock.patch.object(MRTS_RUNNER.shutil, "which", return_value="/usr/bin/go-ftw"), mock.patch.object(
                MRTS_RUNNER.subprocess, "Popen", return_value=process
            ) as popen:
                MRTS_RUNNER.execute_test_set(configuration, root, generated_tests, False)

            popen.assert_called_once_with(
                [
                    "go-ftw",
                    "run",
                    "--config",
                    str(configuration.resolve()),
                    "--dir",
                    str(generated_tests.resolve()),
                    "--wait-for-expect-status-code",
                    "200",
                    "--fail-fast",
                ],
                stdout=MRTS_RUNNER.subprocess.PIPE,
                shell=False,
            )

    def test_uses_the_validated_default_configuration(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            infrastructure = root / "infrastructure"
            infrastructure.mkdir()
            configuration = infrastructure / "ftw.mrts.config.yaml"
            configuration.write_text("{}\n", encoding="utf-8")
            generated_tests = root / "tests"
            generated_tests.mkdir()
            process = self.successful_process()

            with mock.patch.object(MRTS_RUNNER.shutil, "which", return_value="/usr/bin/go-ftw"), mock.patch.object(
                MRTS_RUNNER.subprocess, "Popen", return_value=process
            ) as popen:
                MRTS_RUNNER.execute_test_set(None, infrastructure, generated_tests, False)

            popen.assert_called_once_with(
                [
                    "go-ftw",
                    "run",
                    "--config",
                    str(configuration.resolve()),
                    "--dir",
                    str(generated_tests.resolve()),
                    "--wait-for-expect-status-code",
                    "200",
                    "--fail-fast",
                ],
                stdout=MRTS_RUNNER.subprocess.PIPE,
                shell=False,
            )

    def test_rejects_a_missing_configuration_before_starting_go_ftw(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            generated_tests = root / "tests"
            generated_tests.mkdir()

            with mock.patch.object(MRTS_RUNNER.shutil, "which", return_value="/usr/bin/go-ftw"), mock.patch.object(
                MRTS_RUNNER.subprocess, "Popen"
            ) as popen:
                with self.assertRaisesRegex(ValueError, "go-ftw configuration does not resolve"):
                    MRTS_RUNNER.execute_test_set(root / "missing.yaml", root, generated_tests, False)

            popen.assert_not_called()

    def test_rejects_a_missing_test_directory_before_starting_go_ftw(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            configuration = root / "ftw.mrts.config.yaml"
            configuration.write_text("{}\n", encoding="utf-8")

            with mock.patch.object(MRTS_RUNNER.shutil, "which", return_value="/usr/bin/go-ftw"), mock.patch.object(
                MRTS_RUNNER.subprocess, "Popen"
            ) as popen:
                with self.assertRaisesRegex(ValueError, "tests export directory does not resolve"):
                    MRTS_RUNNER.execute_test_set(configuration, root, root / "missing-tests", False)

            popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
