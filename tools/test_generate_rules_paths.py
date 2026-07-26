"""Regression tests for generated-file path containment."""

import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parent.parent
MRTS_DIRECTORY = ROOT / "mrts"
GENERATOR = MRTS_DIRECTORY / "generate-rules.py"
sys.path.insert(0, str(MRTS_DIRECTORY))

GENERATOR_SPEC = importlib.util.spec_from_file_location("mrts_generate_rules", GENERATOR)
if GENERATOR_SPEC is None or GENERATOR_SPEC.loader is None:
    raise RuntimeError("cannot load MRTS rule generator")
GENERATOR_MODULE = importlib.util.module_from_spec(GENERATOR_SPEC)
GENERATOR_SPEC.loader.exec_module(GENERATOR_MODULE)


class GenerateRulesPathTests(unittest.TestCase):
    def run_generator(self, definition, rules_dir, tests_dir):
        return subprocess.run(
            [
                sys.executable,
                str(GENERATOR),
                "-r",
                str(definition),
                "-e",
                str(rules_dir),
                "-t",
                str(tests_dir),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    def write_definition(self, directory, rulefile):
        definition = directory / "definition.yaml"
        definition.write_text(
            textwrap.dedent(
                """\
                rulefile: {rulefile}
                testfile: null
                objects:
                - object: secaction
                  actions:
                    id: 1
                    phase: 1
                    pass: null
                """
            ).format(rulefile=rulefile),
            encoding="utf-8",
        )
        return definition

    def test_rejects_rulefile_that_escapes_rules_directory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            rules_dir = root / "rules"
            tests_dir = root / "tests"
            rules_dir.mkdir()
            tests_dir.mkdir()
            for unsafe_rulefile in ("../escaped.conf", str(root / "escaped.conf")):
                with self.subTest(rulefile=unsafe_rulefile):
                    definition = self.write_definition(root, unsafe_rulefile)

                    result = self.run_generator(definition, rules_dir, tests_dir)

                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse((root / "escaped.conf").exists())

    def test_allows_rulefile_inside_rules_directory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            rules_dir = root / "rules"
            tests_dir = root / "tests"
            rules_dir.mkdir()
            tests_dir.mkdir()
            definition = self.write_definition(root, "allowed.conf")

            result = self.run_generator(definition, rules_dir, tests_dir)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((rules_dir / "allowed.conf").is_file())

    def test_rejects_testfile_that_escapes_tests_directory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            rules_dir = root / "rules"
            tests_dir = root / "tests"
            rules_dir.mkdir()
            tests_dir.mkdir()
            definition = self.write_definition(root, "allowed.conf")
            with contextlib.redirect_stdout(io.StringIO()):
                generator = GENERATOR_MODULE.RuleGenerator([definition], rules_dir, tests_dir)
                with self.assertRaises(SystemExit):
                    generator.writetest("../escaped.yaml", {"tests": []})

            self.assertFalse((root / "escaped.yaml").exists())


if __name__ == "__main__":
    unittest.main()
