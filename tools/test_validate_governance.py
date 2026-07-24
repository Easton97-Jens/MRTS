"""Focused no-write tests for the MRTS governance validator."""

from __future__ import print_function

import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
VALIDATOR_PATH = ROOT / "tools" / "validate-governance.py"
SPEC = importlib.util.spec_from_file_location("mrts_validate_governance", VALIDATOR_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load governance validator")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class GovernanceValidatorTests(unittest.TestCase):
    def test_current_governance_tree_passes(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(VALIDATOR.main(), 0)
        self.assertIn("MRTS governance structure and policy markers are valid", output.getvalue())

    def test_missing_authorization_marker_is_reported(self):
        original_read_text = VALIDATOR.read_text
        agents = ROOT / "AGENTS.md"

        def altered_read_text(path):
            text = original_read_text(path)
            if path == agents:
                return text.replace(
                    "The current user must expressly authorize each material action class.",
                    "Authorization marker removed.",
                )
            return text

        with mock.patch.object(VALIDATOR, "read_text", side_effect=altered_read_text):
            errors = VALIDATOR.verify_markers()
        self.assertTrue(any("current user" in error.lower() for error in errors))

    def test_markdown_links_remain_relative_and_resolved(self):
        self.assertEqual(VALIDATOR.verify_markdown_structure_and_links(), [])


if __name__ == "__main__":
    unittest.main()
