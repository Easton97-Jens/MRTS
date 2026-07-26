"""Focused no-write tests for the MRTS governance validator."""

from __future__ import print_function

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
VALIDATOR_PATH = ROOT / "tools" / "validate-governance.py"
SPEC = importlib.util.spec_from_file_location("mrts_validate_governance", VALIDATOR_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load governance validator")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)

SHA = "13e6aefebe1dd2179f8b44b6d9eea67e64325316"
FRAMEWORK_SHA = "77d73decd094a8f289fbe0ef2582f12430923e24"
MRTS_ROOT = "/root/git/ModSecurity-conector/modules/ModSecurity-test-Framework/tools/MRTS"


class GovernanceValidatorTests(unittest.TestCase):
    def make_policy_root(self) -> tempfile.TemporaryDirectory:
        temporary = tempfile.TemporaryDirectory()
        policy_root = Path(temporary.name)
        for relative in VALIDATOR.REQUIRED_FILES:
            if not VALIDATOR.is_local_control_file(relative):
                continue
            path = policy_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if relative == ".codex/config.toml":
                path.write_text('sandbox_mode = "workspace-write"\n', encoding="utf-8")
                continue
            markers = VALIDATOR.MARKERS.get(relative, ())
            path.write_text(
                "# Fixture\n\n" + "\n".join(markers) + "\n",
                encoding="utf-8",
            )
        return temporary

    def valid_manifest(self) -> dict:
        branch = "codex/worktree-cleanup-governance"
        worktree = str(
            VALIDATOR._approved_worktree_root("mrts") / "worktree-cleanup-governance"
        )
        return {
            "schema_version": 1,
            "task_id": "worktree-cleanup-governance",
            "repository": "mrts",
            "repository_root": MRTS_ROOT,
            "worktree_path": worktree,
            "branch": branch,
            "remote_branch": branch,
            "PR": {"state": "MERGED", "head_sha": SHA},
            "initial_sha": SHA,
            "final_task_sha": SHA,
            "default_branch": "main",
            "expected_disposition": "merged",
            "local_unique_files": [],
            "evidence_paths": ["/var/tmp/codex/evidence/worktree-cleanup/report.md"],
            "running_processes": [],
            "cleanup_steps": [
                ["git", "-C", MRTS_ROOT, "worktree", "remove", worktree],
                ["git", "-C", MRTS_ROOT, "worktree", "prune"],
                ["git", "-C", MRTS_ROOT, "branch", "-d", branch],
                ["git", "-C", MRTS_ROOT, "push", "origin", "--delete", branch],
            ],
            "cleanup_status": "cleanup_complete",
            "blocked_steps": [],
            "completed_at": "2026-07-24T18:00:00Z",
            "authorization": {
                "current_user_explicit": True,
                "action_classes": [
                    "content_edit",
                    "worktree_create",
                    "worktree_remove",
                    "branch_create",
                    "branch_delete_local",
                    "branch_delete_remote",
                    "commit",
                    "push",
                    "pr_create",
                ],
            },
            "worktree": {
                "task_owned": True,
                "registered_before": True,
                "registered_after": False,
                "clean": True,
                "path_is_symlink": False,
                "local_unique_commits": 0,
                "untracked_unique_files": [],
            },
            "remote": {
                "name": "origin",
                "fetch_url": "https://github.com/Easton97-Jens/MRTS.git",
                "push_url": "https://github.com/Easton97-Jens/MRTS.git",
                "head_sha": SHA,
                "deletion_readback": "absent",
            },
            "cleanup_history": [
                "safe_to_remove",
                "removed_local_worktree",
                "removed_local_branch",
                "removed_remote_branch",
                "cleanup_complete",
            ],
            "gitlinks": {
                "framework_mrts_before": SHA,
                "framework_mrts_after": SHA,
                "parent_framework_before": FRAMEWORK_SHA,
                "parent_framework_after": FRAMEWORK_SHA,
            },
        }

    def assert_error(self, manifest: dict, expected: str) -> None:
        errors = VALIDATOR.validate_cleanup_manifest(manifest)
        self.assertTrue(
            any(expected in error for error in errors),
            "missing {!r} from {!r}".format(expected, errors),
        )

    def test_selected_policy_root_allows_versioned_tree_validation(self) -> None:
        temporary = self.make_policy_root()
        self.addCleanup(temporary.cleanup)
        with mock.patch.object(VALIDATOR, "POLICY_ROOT", Path(temporary.name)):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(VALIDATOR.main([]), 0)
        self.assertIn("MRTS governance structure and policy markers are valid", output.getvalue())

    def test_selected_policy_root_rejects_read_only_sandbox_mode(self) -> None:
        temporary = self.make_policy_root()
        self.addCleanup(temporary.cleanup)
        policy_root = Path(temporary.name)
        (policy_root / ".codex/config.toml").write_text(
            'sandbox_mode = "read-only"\n', encoding="utf-8"
        )
        with mock.patch.object(VALIDATOR, "POLICY_ROOT", policy_root):
            self.assertEqual(
                VALIDATOR.verify_config(),
                ['.codex/config.toml must declare sandbox_mode = "workspace-write"'],
            )

    def test_valid_manifest_remains_valid_with_ci_policy_root(self) -> None:
        with mock.patch.dict(
            VALIDATOR.os.environ,
            {
                "MRTS_GOVERNANCE_POLICY_ROOT": (
                    "/home/runner/work/_temp/mrts-governance-policy"
                )
            },
            clear=True,
        ):
            self.assertEqual(VALIDATOR.validate_cleanup_manifest(self.valid_manifest()), [])

    def test_missing_authorization_marker_is_reported(self) -> None:
        temporary = self.make_policy_root()
        self.addCleanup(temporary.cleanup)
        policy_root = Path(temporary.name)
        original_read_text = VALIDATOR.read_text
        agents = policy_root / "AGENTS.md"

        def altered_read_text(path):
            text = original_read_text(path)
            if path == agents:
                return text.replace(
                    "The current user must expressly authorize each material action class.",
                    "Authorization marker removed.",
                )
            return text

        with mock.patch.object(VALIDATOR, "POLICY_ROOT", policy_root):
            with mock.patch.object(VALIDATOR, "read_text", side_effect=altered_read_text):
                errors = VALIDATOR.verify_markers()
        self.assertTrue(any("current user" in error.lower() for error in errors))

    def test_markdown_links_remain_relative_and_resolved(self) -> None:
        temporary = self.make_policy_root()
        self.addCleanup(temporary.cleanup)
        with mock.patch.object(VALIDATOR, "POLICY_ROOT", Path(temporary.name)):
            self.assertEqual(VALIDATOR.verify_markdown_structure_and_links(), [])

    def test_markdown_helper_preserves_selected_policy_root(self) -> None:
        temporary = self.make_policy_root()
        self.addCleanup(temporary.cleanup)
        policy_root = Path(temporary.name)
        agents = policy_root / "AGENTS.md"
        agents.write_text(
            agents.read_text(encoding="utf-8") + "\n[Policy README](.codex/README.md)\n",
            encoding="utf-8",
        )
        with mock.patch.object(VALIDATOR, "POLICY_ROOT", policy_root):
            self.assertEqual(VALIDATOR.verify_markdown_structure_and_links(), [])

    def test_markdown_link_helper_rejects_escape_and_missing_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "policy.md"
            path.write_text("# Fixture\n\n[Missing](missing.md)\n", encoding="utf-8")
            errors = VALIDATOR.verify_markdown_file(path, root, "policy.md")
            self.assertTrue(any("missing file" in error for error in errors))
            path.write_text("# Fixture\n\n[Escape](../outside.md)\n", encoding="utf-8")
            errors = VALIDATOR.verify_markdown_file(path, root, "policy.md")
            self.assertTrue(any("escapes its selected root" in error for error in errors))

    def test_cleanup_manifest_for_safe_merged_pr_passes(self) -> None:
        self.assertEqual(VALIDATOR.validate_cleanup_manifest(self.valid_manifest()), [])

    def test_open_pr_retains_remote_branch_after_safe_local_cleanup(self) -> None:
        manifest = self.valid_manifest()
        manifest["expected_disposition"] = "verified_pr"
        manifest["PR"] = {"state": "OPEN", "head_sha": SHA}
        manifest["remote"]["deletion_readback"] = "retained"
        manifest["cleanup_history"] = [
            "safe_to_remove",
            "removed_local_worktree",
            "removed_local_branch",
            "remote_branch_retained_for_open_pr",
            "cleanup_complete",
        ]
        self.assertEqual(VALIDATOR.validate_cleanup_manifest(manifest), [])

    def test_unique_local_work_blocks_cleanup(self) -> None:
        manifest = self.valid_manifest()
        manifest["expected_disposition"] = "local_change_not_delivered"
        manifest["PR"] = {"state": "NONE", "head_sha": SHA}
        manifest["remote_branch"] = ""
        manifest["local_unique_files"] = ["notes/unique-local-work.md"]
        manifest["worktree"]["local_unique_commits"] = 1
        manifest["worktree"]["registered_after"] = True
        manifest["cleanup_status"] = "cleanup_blocked"
        manifest["blocked_steps"] = ["cleanup_blocked_unique_local_work"]
        manifest["cleanup_steps"] = []
        manifest["cleanup_history"] = ["cleanup_blocked"]
        self.assertEqual(VALIDATOR.validate_cleanup_manifest(manifest), [])
        manifest["cleanup_status"] = "cleanup_complete"
        self.assert_error(manifest, "local_change_not_delivered must retain")

    def test_unique_local_work_cannot_record_removal(self) -> None:
        manifest = self.valid_manifest()
        manifest["expected_disposition"] = "local_change_not_delivered"
        manifest["PR"] = {"state": "NONE", "head_sha": SHA}
        manifest["remote_branch"] = ""
        manifest["local_unique_files"] = ["notes/unique-local-work.md"]
        manifest["worktree"]["registered_after"] = True
        manifest["cleanup_status"] = "cleanup_blocked"
        manifest["blocked_steps"] = ["cleanup_blocked_unique_local_work"]
        manifest["cleanup_steps"] = []
        manifest["cleanup_history"] = [
            "cleanup_blocked",
            "removed_local_worktree",
        ]
        self.assert_error(manifest, "local_change_not_delivered must not record removed")

    def test_dirty_worktree_cannot_be_reported_complete(self) -> None:
        manifest = self.valid_manifest()
        manifest["worktree"]["clean"] = False
        self.assert_error(manifest, "cleanup_complete requires a clean")

    def test_foreign_or_authoritative_worktree_is_rejected(self) -> None:
        manifest = self.valid_manifest()
        manifest["worktree"]["task_owned"] = False
        self.assert_error(manifest, "worktree.task_owned")
        manifest = self.valid_manifest()
        manifest["worktree_path"] = MRTS_ROOT
        self.assert_error(manifest, "outside the selected task-owned external root")

    def test_worktree_traversal_and_symlink_claims_are_rejected(self) -> None:
        manifest = self.valid_manifest()
        manifest["worktree_path"] = "/var/tmp/codex/worktrees/mrts/../parent/foreign"
        self.assert_error(manifest, "outside the selected task-owned external root")
        manifest = self.valid_manifest()
        manifest["worktree"]["path_is_symlink"] = True
        self.assert_error(manifest, "path_is_symlink must be false")

    def test_remote_mismatch_and_official_upstream_origin_are_rejected(self) -> None:
        manifest = self.valid_manifest()
        manifest["remote"]["push_url"] = "https://github.com/owasp-modsecurity/MRTS.git"
        self.assert_error(manifest, "effective user-fork origin")
        manifest = self.valid_manifest()
        manifest["remote"]["fetch_url"] = "https://github.com/owasp-modsecurity/MRTS.git"
        manifest["remote"]["push_url"] = "https://github.com/owasp-modsecurity/MRTS.git"
        self.assert_error(manifest, "expected user-fork origin")

    def test_upstream_push_and_destructive_cleanup_commands_are_rejected(self) -> None:
        cases = (
            (["git", "-C", MRTS_ROOT, "push", "upstream", "topic"], "upstream"),
            (["git", "-C", MRTS_ROOT, "push", "https://example.invalid/MRTS.git", "topic"], "non-origin"),
            (["git", "-C", MRTS_ROOT, "push", "origin", "HEAD:main"], "default branch"),
            (["git", "-C", MRTS_ROOT, "branch", "-D", "topic"], "git branch -D"),
            (["git", "-C", MRTS_ROOT, "branch", "--force", "topic"], "force-deletes"),
            (["git", "-C", MRTS_ROOT, "worktree", "remove", "--force", "/tmp/topic"], "worktree remove --force"),
            (["git", "-C", MRTS_ROOT, "clean", "-fd"], "git clean"),
            (["git", "-C", MRTS_ROOT, "reset", "--hard"], "git reset --hard"),
            (["git", "-C", MRTS_ROOT, "stash"], "git stash"),
            (["git", "-C", MRTS_ROOT, "remote", "set-url", "origin", "https://example.invalid/MRTS.git"], "rewrites or removes"),
            (["git", "-C", MRTS_ROOT, "config", "remote.origin.pushurl", "https://example.invalid/MRTS.git"], "rewrites remote configuration"),
            (["rtk", "run", "-c", "rm -rf /tmp/topic"], "shell wrapper"),
            (["sh", "-c", "git worktree remove --force /tmp/topic"], "shell wrapper"),
            (["rm", "-rf", "/tmp/topic"], "uses rm"),
        )
        for command, expected in cases:
            with self.subTest(command=command):
                manifest = self.valid_manifest()
                manifest["cleanup_steps"].append(command)
                self.assert_error(manifest, expected)

    def test_only_exact_task_cleanup_commands_are_allowed(self) -> None:
        cases = (
            ["git", "-C", MRTS_ROOT, "worktree", "add", "/var/tmp/codex/worktrees/mrts/other", "main"],
            ["git", "-C", MRTS_ROOT, "commit", "-m", "unrelated"],
            ["git", "-C", MRTS_ROOT, "push", "origin", "HEAD:other"],
        )
        for command in cases:
            with self.subTest(command=command):
                manifest = self.valid_manifest()
                manifest["cleanup_steps"].append(command)
                self.assert_error(manifest, "exact permitted task lifecycle")

    def test_safe_to_remove_requires_preflight_evidence(self) -> None:
        manifest = self.valid_manifest()
        manifest["expected_disposition"] = "verified_pr"
        manifest["PR"] = {"state": "OPEN", "head_sha": SHA}
        manifest["remote"]["deletion_readback"] = "retained"
        manifest["worktree"]["registered_after"] = True
        manifest["cleanup_status"] = "safe_to_remove"
        manifest["cleanup_history"] = [
            "safe_to_remove",
            "remote_branch_retained_for_open_pr",
        ]
        manifest["cleanup_steps"] = []
        self.assertEqual(VALIDATOR.validate_cleanup_manifest(manifest), [])
        manifest["worktree"]["clean"] = False
        self.assert_error(manifest, "safe_to_remove requires a clean")

    def test_cleanup_history_requires_exact_task_targets(self) -> None:
        manifest = self.valid_manifest()
        manifest["cleanup_steps"][0][-1] = "/var/tmp/codex/worktrees/mrts/other"
        self.assert_error(manifest, "exact task worktree_path")
        manifest = self.valid_manifest()
        manifest["cleanup_steps"][2][-1] = "codex/other"
        self.assert_error(manifest, "exact task branch")
        manifest = self.valid_manifest()
        manifest["cleanup_steps"][3][-1] = "codex/other"
        self.assert_error(manifest, "exact task remote branch")

    def test_changed_gitlinks_are_rejected_while_dirty_superproject_is_irrelevant(self) -> None:
        self.assertEqual(VALIDATOR.validate_cleanup_manifest(self.valid_manifest()), [])
        manifest = self.valid_manifest()
        manifest["gitlinks"]["framework_mrts_after"] = FRAMEWORK_SHA
        self.assert_error(manifest, "Framework-MRTS Gitlink changed")
        manifest = self.valid_manifest()
        manifest["gitlinks"]["parent_framework_after"] = SHA
        self.assert_error(manifest, "Parent-Framework Gitlink changed")

    def test_explicit_mrts_authorization_is_required(self) -> None:
        manifest = self.valid_manifest()
        manifest["authorization"]["current_user_explicit"] = False
        self.assert_error(manifest, "current_user_explicit")

    def test_cleanup_steps_require_matching_action_classes(self) -> None:
        manifest = self.valid_manifest()
        manifest["authorization"]["action_classes"].remove("worktree_remove")
        self.assert_error(manifest, "include 'worktree_remove'")
        manifest = self.valid_manifest()
        manifest["authorization"]["action_classes"].append("not_an_action_class")
        self.assert_error(manifest, "unsupported action")

    def test_worktree_prune_requires_worktree_remove_authorization(self) -> None:
        manifest = self.valid_manifest()
        manifest["cleanup_steps"] = [
            ["git", "-C", MRTS_ROOT, "worktree", "prune"],
        ]
        manifest["authorization"]["action_classes"].remove("worktree_remove")
        self.assert_error(manifest, "include 'worktree_remove'")

    def test_rtk_git_cleanup_argv_is_allowed(self) -> None:
        manifest = self.valid_manifest()
        manifest["cleanup_steps"] = [
            ["rtk", "git"] + step[1:] for step in manifest["cleanup_steps"]
        ]
        self.assertEqual(VALIDATOR.validate_cleanup_manifest(manifest), [])

    def test_manifest_validation_does_not_dereference_worktree_path(self) -> None:
        with mock.patch.object(VALIDATOR, "Path", side_effect=AssertionError("Path used")):
            self.assertEqual(VALIDATOR.validate_cleanup_manifest(self.valid_manifest()), [])

    def test_closed_pr_requires_known_closure_disposition(self) -> None:
        manifest = self.valid_manifest()
        manifest["expected_disposition"] = "closed_without_merge"
        manifest["PR"] = {
            "state": "CLOSED",
            "head_sha": SHA,
            "closure_disposition": "free-form reason",
        }
        self.assert_error(manifest, "PR.closure_disposition has unsupported value")

    def test_manifest_loader_rejects_non_object_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            path.write_text(json.dumps([]), encoding="utf-8")
            load_manifest = VALIDATOR.load_cleanup_manifest
            manifest_path = str(path)
            manifest_root = Path(temporary)
            with self.assertRaisesRegex(ValueError, "root must be an object"):
                load_manifest(manifest_path, manifest_root=manifest_root)

    def test_manifest_loader_requires_no_follow_directory_support(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "manifest.json"
            path.write_text(json.dumps({}), encoding="utf-8")
            load_manifest = VALIDATOR.load_cleanup_manifest
            manifest_path = str(path)
            with mock.patch.object(VALIDATOR.os, "O_NOFOLLOW", None):
                with self.assertRaisesRegex(
                    ValueError, "requires O_NOFOLLOW and O_DIRECTORY support"
                ):
                    load_manifest(manifest_path, manifest_root=root)

    def test_manifest_loader_rejects_traversal_and_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "plans"
            root.mkdir()
            outside = Path(temporary) / "outside.json"
            outside.write_text(json.dumps({}), encoding="utf-8")
            load_manifest = VALIDATOR.load_cleanup_manifest
            outside_manifest = str(outside)
            with self.assertRaisesRegex(ValueError, "below"):
                load_manifest(outside_manifest, manifest_root=root)
            link = root / "linked.json"
            link.symlink_to(outside)
            link_manifest = str(link)
            with self.assertRaisesRegex(
                ValueError, "must not traverse a symlink or non-directory component"
            ):
                load_manifest(link_manifest, manifest_root=root)
            outside_directory = Path(temporary) / "outside-directory"
            outside_directory.mkdir()
            (outside_directory / "manifest.json").write_text("{}", encoding="utf-8")
            nested = root / "nested"
            nested.symlink_to(outside_directory, target_is_directory=True)
            nested_manifest = str(nested / "manifest.json")
            with self.assertRaisesRegex(
                ValueError, "must not traverse a symlink or non-directory component"
            ):
                load_manifest(nested_manifest, manifest_root=root)
            non_directory = root / "not-a-directory"
            non_directory.write_text("not a directory", encoding="utf-8")
            non_directory_manifest = str(non_directory / "manifest.json")
            with self.assertRaisesRegex(
                ValueError, "must not traverse a symlink or non-directory component"
            ):
                load_manifest(non_directory_manifest, manifest_root=root)

    def test_manifest_loader_rejects_excessive_json_nesting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "manifest.json"
            value = {}
            for _ in range(VALIDATOR.MAX_MANIFEST_DEPTH + 1):
                value = {"nested": value}
            path.write_text(json.dumps(value), encoding="utf-8")
            load_manifest = VALIDATOR.load_cleanup_manifest
            manifest_path = str(path)
            with self.assertRaisesRegex(ValueError, "nesting limit"):
                load_manifest(manifest_path, manifest_root=root)


if __name__ == "__main__":
    unittest.main()
