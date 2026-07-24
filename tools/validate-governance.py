#!/usr/bin/env python3
"""Read-only structural and cleanup-manifest validation for MRTS governance.

The validator deliberately uses only the Python 3.9 standard library. It does
not invoke subprocesses, access Git or the network, create repository files,
or execute MRTS generators. A caller supplies observed cleanup facts in a
secret-free manifest; this tool validates their policy consistency and never
claims host, GitHub, or sandbox enforcement.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Iterable, List, Mapping, Sequence, Tuple


ROOT = Path(__file__).resolve().parent.parent
POLICY_ROOT = Path(os.environ.get("MRTS_GOVERNANCE_POLICY_ROOT", str(ROOT))).resolve()

REQUIRED_FILES = (
    "AGENTS.md",
    ".codex/README.md",
    ".codex/config.toml",
    ".codex/context/index.md",
    ".codex/context/project-overview.md",
    ".codex/context/architecture.md",
    ".codex/context/policy-precedence.md",
    ".codex/context/repository-boundaries.md",
    ".codex/context/goal-driven-execution.md",
    ".codex/context/rtk-policy.md",
    ".codex/context/commands.md",
    ".codex/context/testing.md",
    ".codex/context/security.md",
    ".codex/context/finding-management.md",
    ".codex/context/dependency-and-supply-chain.md",
    ".codex/context/github-actions.md",
    ".codex/context/tool-provenance.md",
    ".codex/context/documentation.md",
    ".codex/context/evidence.md",
    ".codex/context/git-policy.md",
    ".codex/context/fork-and-upstream-policy.md",
    ".codex/context/delivery-and-ci.md",
    ".codex/context/feasibility.md",
    ".codex/context/cleanup.md",
    ".codex/context/definition-of-done.md",
    ".codex/context/read-only-policy.md",
    ".codex/context/governance-validation.md",
    "templates/task-contract.md",
    "templates/change-record.md",
    "templates/validation-report.md",
    "docs/governance/rule-migration.md",
    "tools/test_validate_governance.py",
)

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")

MARKERS = {
    "AGENTS.md": (
        "Mandatory goal-driven execution",
        "read-only by default",
        "current top-level user",
        "The current user must expressly authorize each material action class.",
        "worktree_create",
        "Gitlink relationship",
        "blocked_remote_mismatch",
        "origin",
        "upstream",
    ),
    ".codex/context/policy-precedence.md": (
        "current explicit top-level user request",
        "task-scoped",
        "Gitlink",
    ),
    ".codex/context/repository-boundaries.md": (
        "read-only by default",
        "Framework may show `tools/MRTS (new commits)`",
        "task-owned worktree",
        "Gitlink",
    ),
    ".codex/context/read-only-policy.md": (
        "declared default",
        "current top-level user",
        "does not imply permission",
    ),
    ".codex/context/git-policy.md": (
        "origin/main",
        "Never commit/push directly to `main`",
        "blocked_remote_mismatch",
        "verified_pr_remote_cleanup_deferred",
        "Gitlink",
    ),
    ".codex/context/fork-and-upstream-policy.md": (
        "Easton97-Jens/MRTS",
        "git remote get-url --push origin",
        "blocked_remote_mismatch",
        "Never",
    ),
    ".codex/context/delivery-and-ci.md": (
        "Draft PR",
        "never a merge",
        "verified_pr_remote_cleanup_deferred",
        "Gitlink",
    ),
    ".codex/context/cleanup.md": (
        "task-owned external worktree",
        "worktree remove",
        "git branch -d",
        "remote_branch_retained_for_open_pr",
        "push origin --delete",
    ),
    ".codex/context/finding-management.md": (
        "FND-MRTS-",
        "concrete evidence",
        "legitimate control",
    ),
    "templates/task-contract.md": (
        "Current user authorization",
        "Framework impact and MRTS Gitlink disposition",
        "Authorized action classes",
        "Cleanup manifest",
    ),
    "templates/change-record.md": (
        "Current user authorization",
        "Parent and Framework Gitlink disposition",
        "Validation and delivery",
        "Cleanup manifest",
    ),
    "templates/validation-report.md": (
        "Default read-only negative case",
        "Explicit authorization positive case",
        "No Framework/Parent Gitlink update",
        "Remote and cleanup lifecycle",
    ),
}

MATRIX_HEADINGS = (
    "Current rule",
    "Target rule",
    "Change class",
    "Owner",
    "Authorization",
    "Behaviour impact",
    "Evidence",
    "Validator check",
    "Status",
)

SOURCE_MATRIX_HEADINGS = (
    "Quelle",
    "Regel/Zweck",
    "MRTS-relevant",
    "Entscheidung",
    "MRTS-Ziel",
    "Begründung",
)

EXPECTED_REPOSITORIES = {
    "parent": {
        "root": "/root/git/ModSecurity-conector",
        "worktree_root": "/var/tmp/codex/worktrees/parent",
        "default_branch": "master",
        "urls": {
            "https://github.com/Easton97-Jens/ModSecurity-conector.git",
            "git@github.com:Easton97-Jens/ModSecurity-conector.git",
        },
    },
    "framework": {
        "root": "/root/git/ModSecurity-conector/modules/ModSecurity-test-Framework",
        "worktree_root": "/var/tmp/codex/worktrees/framework",
        "default_branch": "master",
        "urls": {
            "https://github.com/Easton97-Jens/ModSecurity-test-Framework.git",
            "git@github.com:Easton97-Jens/ModSecurity-test-Framework.git",
        },
    },
    "mrts": {
        "root": "/root/git/ModSecurity-conector/modules/ModSecurity-test-Framework/tools/MRTS",
        "worktree_root": "/var/tmp/codex/worktrees/mrts",
        "default_branch": "main",
        "urls": {
            "https://github.com/Easton97-Jens/MRTS.git",
            "git@github.com:Easton97-Jens/MRTS.git",
        },
    },
}

LIFECYCLE_DISPOSITIONS = {
    "analysis_complete",
    "no_change",
    "local_change_not_delivered",
    "verified_pr",
    "merged",
    "closed_without_merge",
}
CLEANUP_STATUSES = {
    "pending",
    "safe_to_remove",
    "removed_local_worktree",
    "removed_local_branch",
    "remote_branch_retained_for_open_pr",
    "removed_remote_branch",
    "restored_recorded_gitlink",
    "cleanup_complete",
    "cleanup_blocked",
}
PR_STATES = {"OPEN", "MERGED", "CLOSED", "NONE"}
REQUIRED_MANIFEST_FIELDS = (
    "task_id",
    "repository",
    "repository_root",
    "worktree_path",
    "branch",
    "remote_branch",
    "PR",
    "initial_sha",
    "final_task_sha",
    "default_branch",
    "expected_disposition",
    "local_unique_files",
    "evidence_paths",
    "running_processes",
    "cleanup_steps",
    "cleanup_status",
    "blocked_steps",
    "completed_at",
)


def emit(level: str, message: str) -> None:
    print("{}: {}".format(level, message))


def is_local_control_file(relative: str) -> bool:
    return relative == "AGENTS.md" or relative.startswith(".codex/")


def root_for(relative: str) -> Path:
    return POLICY_ROOT if is_local_control_file(relative) else ROOT


def path_for(relative: str) -> Path:
    return root_for(relative) / relative


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def set_policy_root(value: Path) -> None:
    """Set the read-only local control-plane root for this process."""

    global POLICY_ROOT
    POLICY_ROOT = value.resolve()


def verify_regular_files(paths: Iterable[str]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    validated: List[str] = []
    for relative in paths:
        path = path_for(relative)
        if path.is_symlink():
            errors.append("{} must not be a symlink".format(relative))
        elif not path.is_file():
            errors.append("{} must be a regular file".format(relative))
        else:
            try:
                read_text(path)
            except UnicodeDecodeError:
                errors.append("{} is not valid UTF-8 text".format(relative))
            else:
                validated.append(relative)
    return errors, validated


def verify_markers() -> List[str]:
    errors: List[str] = []
    for relative, markers in MARKERS.items():
        text = read_text(path_for(relative))
        lowered = " ".join(text.split()).lower()
        for marker in markers:
            if " ".join(marker.split()).lower() not in lowered:
                errors.append("{} is missing marker {!r}".format(relative, marker))
    return errors


def verify_config() -> List[str]:
    config = read_text(path_for(".codex/config.toml"))
    if re.search(r'^\s*sandbox_mode\s*=\s*"read-only"\s*$', config, re.MULTILINE):
        return []
    return ['.codex/config.toml must declare sandbox_mode = "read-only"']


def verify_migration_matrix() -> List[str]:
    report = read_text(path_for("docs/governance/rule-migration.md"))
    errors: List[str] = []
    if "## Rule migration matrix" not in report:
        errors.append("migration report is missing the Rule migration matrix heading")
    header = next((line for line in report.splitlines() if line.startswith("| Current rule |")), "")
    for heading in MATRIX_HEADINGS:
        if heading not in header:
            errors.append("migration matrix header is missing {!r}".format(heading))
    return errors


def verify_source_disposition_matrix() -> List[str]:
    report = read_text(path_for("docs/governance/rule-migration.md"))
    errors: List[str] = []
    if "## Source rule disposition matrix" not in report:
        errors.append("migration report is missing the Source rule disposition matrix heading")
    header = next((line for line in report.splitlines() if line.startswith("| Quelle |")), "")
    for heading in SOURCE_MATRIX_HEADINGS:
        if heading not in header:
            errors.append("source disposition matrix header is missing {!r}".format(heading))
    return errors


def verify_markdown_structure_and_links() -> List[str]:
    errors: List[str] = []
    for relative in REQUIRED_FILES:
        if not relative.endswith(".md"):
            continue
        path = path_for(relative)
        text = read_text(path)
        if not text.lstrip().startswith("# "):
            errors.append("{} must start with a level-one Markdown heading".format(relative))
        root = root_for(relative).resolve()
        for target in MARKDOWN_LINK_RE.findall(text):
            value = target.strip().strip("<>")
            destination = value.split("#", 1)[0]
            if not destination or "://" in destination or destination.startswith("mailto:"):
                continue
            if destination.startswith("/"):
                errors.append("{} has a non-relative Markdown link {!r}".format(relative, target))
                continue
            resolved = (path.parent / destination).resolve()
            try:
                resolved.relative_to(root)
            except ValueError:
                errors.append("{} link escapes its selected root {!r}".format(relative, target))
                continue
            if not resolved.is_file():
                errors.append("{} links to missing file {!r}".format(relative, target))
    return errors


def _require_mapping(value: Any, field: str, errors: List[str]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        errors.append("{} must be an object".format(field))
        return {}
    return value


def _require_list(value: Any, field: str, errors: List[str]) -> Sequence[Any]:
    if not isinstance(value, list):
        errors.append("{} must be a list".format(field))
        return []
    return value


def _string(value: Any, field: str, errors: List[str], allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value):
        errors.append("{} must be a non-empty string".format(field))
        return ""
    return value


def _sha(value: Any, field: str, errors: List[str]) -> str:
    text = _string(value, field, errors)
    if text and not SHA_RE.fullmatch(text):
        errors.append("{} must be a 40-character lowercase Git SHA".format(field))
    return text


def _status_in(value: Any, field: str, allowed: set[str], errors: List[str]) -> str:
    text = _string(value, field, errors)
    if text and text not in allowed:
        errors.append("{} has unsupported value {!r}".format(field, text))
    return text


def _contains_unsafe_command(
    argv: Sequence[Any],
    repository_root: str,
    worktree_path: str,
    branch: str,
    remote_branch: str,
    default_branch: str,
) -> List[str]:
    if not argv or not all(isinstance(item, str) for item in argv):
        return ["cleanup_steps entries must be non-empty argv string lists"]
    raw = list(argv)
    lowered = [item.lower() for item in argv]
    violations: List[str] = []
    executable = lowered[0].rsplit("/", 1)[-1]
    shell_executables = {"sh", "bash", "dash", "ksh", "zsh", "fish"}
    git_index = 0
    direct_git = False
    if executable == "git":
        direct_git = True
        git_index = 1
    elif executable == "rtk" and len(lowered) > 1 and lowered[1] == "git":
        direct_git = True
        git_index = 2
    if executable in shell_executables and "-c" in lowered:
        violations.append("cleanup command must not hide actions behind a shell wrapper")
    if executable == "rtk" and "run" in lowered and "-c" in lowered:
        violations.append("cleanup command must not hide actions behind a shell wrapper")
    command: Sequence[str] = []
    if not direct_git:
        violations.append("cleanup command must be a direct git or rtk git argv")
    elif len(raw) < git_index + 3 or raw[git_index] != "-C":
        violations.append("cleanup command must invoke Git in the selected repository root")
    elif raw[git_index + 1] != repository_root:
        violations.append("cleanup command must invoke Git in the selected repository root")
    else:
        command = raw[git_index + 2 :]
    if any(item.rsplit("/", 1)[-1] == "rm" for item in lowered):
        violations.append("cleanup command uses rm rather than a Git-owned lifecycle action")
    if "branch" in lowered and "-D" in raw:
        violations.append("cleanup command uses git branch -D")
    if "branch" in lowered and ("--force" in lowered or "-f" in raw):
        violations.append("cleanup command force-deletes a local branch")
    if "worktree" in lowered and "remove" in lowered and (
        "--force" in lowered or "-f" in raw
    ):
        violations.append("cleanup command uses git worktree remove --force")
    if "clean" in lowered:
        violations.append("cleanup command uses git clean")
    if "reset" in lowered and "--hard" in lowered:
        violations.append("cleanup command uses git reset --hard")
    if "stash" in lowered:
        violations.append("cleanup command uses git stash")
    if "remote" in lowered and any(
        action in lowered for action in ("set-url", "rename", "remove")
    ):
        violations.append("cleanup command rewrites or removes a Git remote")
    if "config" in lowered and any(item.startswith("remote.") for item in lowered):
        violations.append("cleanup command rewrites remote configuration")
    if "push" in lowered and ("--force" in lowered or "-f" in lowered):
        violations.append("cleanup command uses force-push")
    if "push" in lowered:
        push_index = lowered.index("push")
        destination = lowered[push_index + 1] if push_index + 1 < len(lowered) else ""
        if destination != "origin":
            violations.append("cleanup command pushes or deletes through a non-origin target")
        if "upstream" in lowered:
            violations.append("cleanup command pushes or deletes through upstream")
        if any(
            item == default_branch or item.endswith(":" + default_branch)
            for item in raw[push_index + 2 :]
        ):
            violations.append("cleanup command targets the default branch")
    if "branch" in lowered and default_branch in raw:
        violations.append("cleanup command targets the default branch")
    permitted = (
        ["worktree", "remove", worktree_path],
        ["worktree", "prune"],
        ["branch", "-d", branch],
        ["push", "origin", "--delete", remote_branch],
    )
    if command and list(command) not in permitted:
        violations.append("cleanup command is not an exact permitted task lifecycle operation")
    return violations


def validate_cleanup_manifest(manifest: Mapping[str, Any]) -> List[str]:
    """Return policy violations for a secret-free, observed cleanup manifest.

    This is a semantic validation of supplied evidence. It deliberately does
    not call Git, GitHub, the network, or the filesystem beyond a caller's own
    manifest loading path.
    """

    errors: List[str] = []
    for field in REQUIRED_MANIFEST_FIELDS:
        if field not in manifest:
            errors.append("manifest is missing required field {}".format(field))
    if errors:
        return errors

    if manifest.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    task_id = _string(manifest.get("task_id"), "task_id", errors)
    if task_id and ("/" in task_id or ".." in task_id):
        errors.append("task_id must not contain a path separator or traversal")

    repository = _string(manifest.get("repository"), "repository", errors).lower()
    spec = EXPECTED_REPOSITORIES.get(repository)
    if spec is None:
        errors.append("repository must be parent, framework, or mrts")
        return errors

    repository_root = _string(manifest.get("repository_root"), "repository_root", errors)
    if repository_root and repository_root != spec["root"]:
        errors.append("repository_root does not match the selected repository")
    default_branch = _string(manifest.get("default_branch"), "default_branch", errors)
    if default_branch and default_branch != spec["default_branch"]:
        errors.append("default_branch does not match the selected repository")

    worktree_path = _string(manifest.get("worktree_path"), "worktree_path", errors)
    if worktree_path:
        candidate_worktree = Path(worktree_path)
        approved_worktree_root = Path(spec["worktree_root"]).resolve()
        if not candidate_worktree.is_absolute():
            errors.append("worktree_path must be absolute")
        else:
            resolved_worktree = candidate_worktree.resolve()
            try:
                relative_worktree = resolved_worktree.relative_to(approved_worktree_root)
            except ValueError:
                errors.append("worktree_path is outside the selected task-owned external root")
            else:
                if not relative_worktree.parts:
                    errors.append("worktree_path must be below the selected task-owned external root")
            if resolved_worktree in {
                Path(item["root"]).resolve() for item in EXPECTED_REPOSITORIES.values()
            }:
                errors.append("worktree_path must not be an authoritative repository checkout")

    _string(manifest.get("branch"), "branch", errors)
    _string(manifest.get("remote_branch"), "remote_branch", errors, allow_empty=True)
    initial_sha = _sha(manifest.get("initial_sha"), "initial_sha", errors)
    final_sha = _sha(manifest.get("final_task_sha"), "final_task_sha", errors)
    disposition = _status_in(
        manifest.get("expected_disposition"),
        "expected_disposition",
        LIFECYCLE_DISPOSITIONS,
        errors,
    )
    cleanup_status = _status_in(
        manifest.get("cleanup_status"), "cleanup_status", CLEANUP_STATUSES, errors
    )
    _string(manifest.get("completed_at"), "completed_at", errors, allow_empty=True)

    local_unique_files = _require_list(
        manifest.get("local_unique_files"), "local_unique_files", errors
    )
    evidence_paths = _require_list(manifest.get("evidence_paths"), "evidence_paths", errors)
    _require_list(manifest.get("running_processes"), "running_processes", errors)
    blocked_steps = _require_list(manifest.get("blocked_steps"), "blocked_steps", errors)
    if not evidence_paths:
        errors.append("evidence_paths must retain at least one evidence location")

    authorization = _require_mapping(manifest.get("authorization"), "authorization", errors)
    if authorization.get("current_user_explicit") is not True:
        errors.append("authorization.current_user_explicit must be true")
    action_classes = _require_list(
        authorization.get("action_classes"), "authorization.action_classes", errors
    )
    if not action_classes:
        errors.append("authorization.action_classes must not be empty")

    worktree = _require_mapping(manifest.get("worktree"), "worktree", errors)
    if worktree.get("task_owned") is not True:
        errors.append("worktree.task_owned must be true")
    if worktree.get("registered_before") is not True:
        errors.append("worktree.registered_before must be true")
    if not isinstance(worktree.get("path_is_symlink"), bool):
        errors.append("worktree.path_is_symlink must be boolean")
    elif worktree.get("path_is_symlink") is not False:
        errors.append("worktree.path_is_symlink must be false")
    if worktree_path and Path(worktree_path).exists() and Path(worktree_path).is_symlink():
        errors.append("worktree_path must not resolve through a symlink")
    if not isinstance(worktree.get("clean"), bool):
        errors.append("worktree.clean must be boolean")
    if not isinstance(worktree.get("registered_after"), bool):
        errors.append("worktree.registered_after must be boolean")
    local_unique_commits = worktree.get("local_unique_commits")
    if not isinstance(local_unique_commits, int) or local_unique_commits < 0:
        errors.append("worktree.local_unique_commits must be a non-negative integer")
        local_unique_commits = 0
    untracked_unique = _require_list(
        worktree.get("untracked_unique_files"), "worktree.untracked_unique_files", errors
    )

    remote = _require_mapping(manifest.get("remote"), "remote", errors)
    if remote.get("name") != "origin":
        errors.append("remote.name must be origin")
    fetch_url = _string(remote.get("fetch_url"), "remote.fetch_url", errors)
    push_url = _string(remote.get("push_url"), "remote.push_url", errors)
    accepted_urls = spec["urls"]
    if fetch_url and fetch_url not in accepted_urls:
        errors.append("remote.fetch_url is not the expected user-fork origin")
    if push_url and push_url not in accepted_urls:
        errors.append("remote.push_url is not the expected effective user-fork origin")
    remote_sha = _sha(remote.get("head_sha"), "remote.head_sha", errors)
    _string(remote.get("deletion_readback"), "remote.deletion_readback", errors)

    pr = _require_mapping(manifest.get("PR"), "PR", errors)
    pr_state = _status_in(pr.get("state"), "PR.state", PR_STATES, errors)
    pr_head = _sha(pr.get("head_sha"), "PR.head_sha", errors)

    history = _require_list(manifest.get("cleanup_history"), "cleanup_history", errors)
    for item in history:
        if not isinstance(item, str) or item not in CLEANUP_STATUSES:
            errors.append("cleanup_history contains an unsupported cleanup status")

    cleanup_steps = _require_list(manifest.get("cleanup_steps"), "cleanup_steps", errors)
    validated_steps: List[Sequence[str]] = []
    for step in cleanup_steps:
        argv = _require_list(step, "cleanup_steps entry", errors)
        errors.extend(
            _contains_unsafe_command(
                argv,
                repository_root,
                worktree_path,
                _string(manifest.get("branch"), "branch", errors),
                _string(manifest.get("remote_branch"), "remote_branch", errors, allow_empty=True),
                default_branch,
            )
        )
        if argv and all(isinstance(item, str) for item in argv):
            validated_steps.append(argv)

    gitlinks = _require_mapping(manifest.get("gitlinks"), "gitlinks", errors)
    for name in (
        "framework_mrts_before",
        "framework_mrts_after",
        "parent_framework_before",
        "parent_framework_after",
    ):
        _sha(gitlinks.get(name), "gitlinks." + name, errors)
    if gitlinks.get("framework_mrts_before") != gitlinks.get("framework_mrts_after"):
        errors.append("Framework-MRTS Gitlink changed without separate authorization")
    if gitlinks.get("parent_framework_before") != gitlinks.get("parent_framework_after"):
        errors.append("Parent-Framework Gitlink changed without separate authorization")

    has_unique_work = bool(local_unique_files or untracked_unique or local_unique_commits)
    worktree_clean = worktree.get("clean") is True
    worktree_removed = "removed_local_worktree" in history
    local_branch_removed = "removed_local_branch" in history
    remote_removed = "removed_remote_branch" in history

    saw_exact_worktree_remove = False
    saw_exact_local_branch_delete = False
    saw_exact_remote_branch_delete = False
    for argv in validated_steps:
        lowered = [item.lower() for item in argv]
        if "worktree" in lowered and "remove" in lowered:
            if worktree_path not in argv:
                errors.append("worktree remove must name the exact task worktree_path")
            else:
                saw_exact_worktree_remove = True
        if "branch" in lowered and "-d" in argv:
            if manifest.get("branch") not in argv:
                errors.append("git branch -d must name the exact task branch")
            else:
                saw_exact_local_branch_delete = True
        if "push" in lowered and "origin" in lowered and "--delete" in lowered:
            if manifest.get("remote_branch") not in argv:
                errors.append("git push origin --delete must name the exact task remote branch")
            else:
                saw_exact_remote_branch_delete = True

    if disposition == "local_change_not_delivered":
        if not has_unique_work:
            errors.append("local_change_not_delivered requires unique local work evidence")
        if cleanup_status != "cleanup_blocked" or not blocked_steps:
            errors.append("local_change_not_delivered must retain work as cleanup_blocked")
    elif has_unique_work and cleanup_status != "cleanup_blocked":
        errors.append("unique local work must block cleanup rather than be removed")

    if cleanup_status == "cleanup_complete":
        if not worktree_clean:
            errors.append("cleanup_complete requires a clean task worktree")
        if worktree.get("registered_after") is not False:
            errors.append("cleanup_complete requires worktree.registered_after=false")
        if worktree_path and not worktree_removed:
            errors.append("cleanup_complete requires removed_local_worktree history")
    if cleanup_status == "safe_to_remove":
        if not worktree_clean:
            errors.append("safe_to_remove requires a clean task worktree")
        if has_unique_work:
            errors.append("safe_to_remove requires no unique local work")
        if worktree.get("registered_after") is not True:
            errors.append("safe_to_remove requires worktree.registered_after=true")
        if manifest.get("running_processes"):
            errors.append("safe_to_remove requires no running processes")
        if blocked_steps:
            errors.append("safe_to_remove requires no blocked cleanup steps")
        if "safe_to_remove" not in history:
            errors.append("safe_to_remove requires safe_to_remove cleanup history")
    if worktree_removed and (not worktree_clean or worktree.get("registered_after") is not False):
        errors.append("removed_local_worktree requires clean unregistered-after worktree evidence")
    if worktree_removed and not saw_exact_worktree_remove:
        errors.append("removed_local_worktree requires an exact worktree remove command")
    if local_branch_removed and not saw_exact_local_branch_delete:
        errors.append("removed_local_branch requires an exact git branch -d command")
    if remote_removed and not saw_exact_remote_branch_delete:
        errors.append("removed_remote_branch requires an exact git push origin --delete command")

    if disposition == "analysis_complete" and manifest.get("remote_branch"):
        errors.append("analysis_complete must not retain a task remote branch")
    if disposition == "no_change" and (manifest.get("remote_branch") or pr_state != "NONE"):
        errors.append("no_change must not create a remote branch or PR")
    if disposition in {"no_change", "merged", "closed_without_merge"} and worktree_path and not worktree_removed:
        errors.append("final cleanup disposition requires removing the task worktree")

    if pr_state == "OPEN":
        if disposition != "verified_pr":
            errors.append("an open PR requires expected_disposition=verified_pr")
        if not manifest.get("remote_branch"):
            errors.append("an open PR requires a retained remote_branch")
        if remote_removed:
            errors.append("an open PR branch must not be remotely deleted")
        if "remote_branch_retained_for_open_pr" not in history:
            errors.append("an open PR requires remote_branch_retained_for_open_pr history")
        if final_sha and (remote_sha != final_sha or pr_head != final_sha):
            errors.append("open PR local, remote, and PR-head SHA must match final_task_sha")
    if disposition == "verified_pr" and pr_state != "OPEN":
        errors.append("verified_pr requires PR.state=OPEN")

    if disposition == "merged":
        if pr_state != "MERGED":
            errors.append("merged disposition requires PR.state=MERGED")
        if not remote_removed:
            errors.append("merged disposition requires removed_remote_branch history")
        if remote.get("deletion_readback") != "absent":
            errors.append("merged remote cleanup requires an absent remote readback")
        if not local_branch_removed:
            errors.append("merged disposition requires removed_local_branch history")
    if disposition == "closed_without_merge":
        if pr_state != "CLOSED":
            errors.append("closed_without_merge requires PR.state=CLOSED")
        if not _string(pr.get("closure_disposition"), "PR.closure_disposition", errors):
            pass

    if final_sha and remote_sha and pr_state != "NONE" and pr_state != "OPEN" and pr_head != final_sha:
        errors.append("PR.head_sha must match final_task_sha")
    if initial_sha and final_sha and not task_id:
        errors.append("task identity is required for SHA evidence")
    return errors


def load_cleanup_manifest(path: Path) -> Mapping[str, Any]:
    """Load one regular UTF-8 JSON manifest without following a symlink."""

    if path.is_symlink() or not path.is_file():
        raise ValueError("cleanup manifest must be a regular file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("cleanup manifest is not valid UTF-8 JSON: {}".format(error))
    if not isinstance(value, Mapping):
        raise ValueError("cleanup manifest root must be an object")
    return value


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--policy-root",
        type=Path,
        help="read-only root containing ignored AGENTS.md and .codex policy files",
    )
    parser.add_argument(
        "--cleanup-manifest",
        type=Path,
        help="secret-free observed cleanup manifest to validate semantically",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_args(argv)
    if arguments.policy_root is not None:
        set_policy_root(arguments.policy_root)

    errors, validated = verify_regular_files(REQUIRED_FILES)
    if not errors:
        errors.extend(verify_markers())
        errors.extend(verify_config())
        errors.extend(verify_migration_matrix())
        errors.extend(verify_source_disposition_matrix())
        errors.extend(verify_markdown_structure_and_links())

    if arguments.cleanup_manifest is not None:
        try:
            manifest = load_cleanup_manifest(arguments.cleanup_manifest)
        except ValueError as error:
            errors.append(str(error))
        else:
            errors.extend(validate_cleanup_manifest(manifest))

    for relative in validated:
        emit("PASS", "regular UTF-8 file {}".format(relative))
    if errors:
        for error in errors:
            emit("ERROR", error)
        return 1
    if arguments.cleanup_manifest is not None:
        emit("PASS", "cleanup manifest is policy-consistent")
    emit("PASS", "MRTS governance structure and policy markers are valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
