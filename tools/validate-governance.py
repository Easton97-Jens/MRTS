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
import errno
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple


ROOT = Path(__file__).resolve().parent.parent
POLICY_ROOT = Path(os.environ.get("MRTS_GOVERNANCE_POLICY_ROOT", str(ROOT))).resolve()
RULE_MIGRATION_PATH = "docs/governance/rule-migration.md"
AGENTS_FILE = "AGENTS.md"
MANIFEST_DIRECTORY = ".codex/plans"
MAX_MANIFEST_BYTES = 1024 * 1024
MAX_MANIFEST_DEPTH = 32
ORIGIN = "origin"

REQUIRED_FILES = (
    AGENTS_FILE,
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
    RULE_MIGRATION_PATH,
    "tools/test_validate_governance.py",
)

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")

MARKERS = {
    AGENTS_FILE: (
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
        "default_branch": "master",
        "urls": {
            "https://github.com/Easton97-Jens/ModSecurity-conector.git",
            "git@github.com:Easton97-Jens/ModSecurity-conector.git",
        },
    },
    "framework": {
        "root": "/root/git/ModSecurity-conector/modules/ModSecurity-test-Framework",
        "default_branch": "master",
        "urls": {
            "https://github.com/Easton97-Jens/ModSecurity-test-Framework.git",
            "git@github.com:Easton97-Jens/ModSecurity-test-Framework.git",
        },
    },
    "mrts": {
        "root": "/root/git/ModSecurity-conector/modules/ModSecurity-test-Framework/tools/MRTS",
        "default_branch": "main",
        "urls": {
            "https://github.com/Easton97-Jens/MRTS.git",
            "git@github.com:Easton97-Jens/MRTS.git",
        },
    },
}
WORKTREE_ROOT_ENVIRONMENTS = {
    "parent": "PARENT_GOVERNANCE_WORKTREE_ROOT",
    "framework": "FRAMEWORK_GOVERNANCE_WORKTREE_ROOT",
    "mrts": "MRTS_GOVERNANCE_WORKTREE_ROOT",
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
AUTHORIZED_ACTION_CLASSES = frozenset(
    (
        "content_edit",
        "worktree_create",
        "worktree_remove",
        "branch_create",
        "branch_delete_local",
        "branch_delete_remote",
        "commit",
        "push",
        "pr_create",
        "pr_update",
        "pr_close",
        "merge",
        "restore_recorded_gitlink",
    )
)
CLOSED_PR_DISPOSITIONS = {"replacement_pr", "explicit_discard"}
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
    return relative == AGENTS_FILE or relative.startswith(".codex/")


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
    if re.search(r'^\s*sandbox_mode\s*=\s*"workspace-write"\s*$', config, re.MULTILINE):
        return []
    return ['.codex/config.toml must declare sandbox_mode = "workspace-write"']


def verify_migration_matrix() -> List[str]:
    report = read_text(ROOT / RULE_MIGRATION_PATH)
    errors: List[str] = []
    if "## Rule migration matrix" not in report:
        errors.append("migration report is missing the Rule migration matrix heading")
    header = next((line for line in report.splitlines() if line.startswith("| Current rule |")), "")
    for heading in MATRIX_HEADINGS:
        if heading not in header:
            errors.append("migration matrix header is missing {!r}".format(heading))
    return errors


def verify_source_disposition_matrix() -> List[str]:
    report = read_text(ROOT / RULE_MIGRATION_PATH)
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
        if relative.endswith(".md"):
            errors.extend(
                verify_markdown_file(
                    path_for(relative), root_for(relative).resolve(), relative
                )
            )
    return errors


def verify_markdown_file(path: Path, root: Path, relative: str) -> List[str]:
    errors: List[str] = []
    text = read_text(path)
    if not text.lstrip().startswith("# "):
        errors.append("{} must start with a level-one Markdown heading".format(relative))
    for target in MARKDOWN_LINK_RE.findall(text):
        errors.extend(verify_markdown_link(path, root, relative, target))
    return errors


def verify_markdown_link(path: Path, root: Path, relative: str, target: str) -> List[str]:
    value = target.strip().strip("<>")
    destination = value.split("#", 1)[0]
    if not destination or "://" in destination or destination.startswith("mailto:"):
        return []
    if destination.startswith("/"):
        return ["{} has a non-relative Markdown link {!r}".format(relative, target)]
    resolved = (path.parent / destination).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return ["{} link escapes its selected root {!r}".format(relative, target)]
    if not resolved.is_file():
        return ["{} links to missing file {!r}".format(relative, target)]
    return []


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


def _normalise_cleanup_argv(
    argv: Sequence[Any],
) -> Tuple[List[str], List[str], List[str]]:
    if not argv or not all(isinstance(item, str) for item in argv):
        return [], [], ["cleanup_steps entries must be non-empty argv string lists"]
    raw = list(argv)
    return raw, [item.lower() for item in raw], []


def _shell_wrapper_violations(lowered: Sequence[str]) -> List[str]:
    executable = lowered[0].rsplit("/", 1)[-1]
    shell_executables = {"sh", "bash", "dash", "ksh", "zsh", "fish"}
    if executable in shell_executables and "-c" in lowered:
        return ["cleanup command must not hide actions behind a shell wrapper"]
    if executable == "rtk" and "run" in lowered and "-c" in lowered:
        return ["cleanup command must not hide actions behind a shell wrapper"]
    return []


def _git_command_index(lowered: Sequence[str]) -> Optional[int]:
    executable = lowered[0].rsplit("/", 1)[-1]
    if executable == "git":
        return 1
    if executable == "rtk" and len(lowered) > 1 and lowered[1] == "git":
        return 2
    return None


def _direct_git_command(
    raw: Sequence[str], lowered: Sequence[str], repository_root: str
) -> Tuple[List[str], List[str]]:
    git_index = _git_command_index(lowered)
    if git_index is None:
        return [], ["cleanup command must be a direct git or rtk git argv"]
    if len(raw) < git_index + 3 or raw[git_index] != "-C":
        return [], ["cleanup command must invoke Git in the selected repository root"]
    if raw[git_index + 1] != repository_root:
        return [], ["cleanup command must invoke Git in the selected repository root"]
    return list(raw[git_index + 2 :]), []


def _branch_cleanup_violations(command: Sequence[str], default_branch: str) -> List[str]:
    violations: List[str] = []
    lowered = [item.lower() for item in command]
    if "-D" in command:
        violations.append("cleanup command uses git branch -D")
    if "--force" in lowered or "-f" in command:
        violations.append("cleanup command force-deletes a local branch")
    if default_branch in command:
        violations.append("cleanup command targets the default branch")
    return violations


def _worktree_cleanup_violations(command: Sequence[str]) -> List[str]:
    lowered = [item.lower() for item in command]
    if len(lowered) > 1 and lowered[1] == "remove" and (
        "--force" in lowered or "-f" in command
    ):
        return ["cleanup command uses git worktree remove --force"]
    return []


def _push_cleanup_violations(command: Sequence[str], default_branch: str) -> List[str]:
    violations: List[str] = []
    lowered = [item.lower() for item in command]
    destination = lowered[1] if len(lowered) > 1 else ""
    if "--force" in lowered or "-f" in lowered:
        violations.append("cleanup command uses force-push")
    if destination != ORIGIN:
        violations.append("cleanup command pushes or deletes through a non-origin target")
    if "upstream" in lowered:
        violations.append("cleanup command pushes or deletes through upstream")
    if any(
        item == default_branch or item.endswith(":" + default_branch)
        for item in command[2:]
    ):
        violations.append("cleanup command targets the default branch")
    return violations


def _destructive_cleanup_violations(
    raw: Sequence[str], lowered: Sequence[str], command: Sequence[str], default_branch: str
) -> List[str]:
    violations: List[str] = []
    if any(item.rsplit("/", 1)[-1] == "rm" for item in lowered):
        violations.append("cleanup command uses rm rather than a Git-owned lifecycle action")
    if not command:
        return violations
    operation = command[0].lower()
    if operation == "branch":
        violations.extend(_branch_cleanup_violations(command, default_branch))
    elif operation == "worktree":
        violations.extend(_worktree_cleanup_violations(command))
    elif operation == "push":
        violations.extend(_push_cleanup_violations(command, default_branch))
    elif operation == "clean":
        violations.append("cleanup command uses git clean")
    elif operation == "reset" and "--hard" in [item.lower() for item in command]:
        violations.append("cleanup command uses git reset --hard")
    elif operation == "stash":
        violations.append("cleanup command uses git stash")
    elif operation == "remote" and any(
        item.lower() in {"set-url", "rename", "remove"} for item in command
    ):
        violations.append("cleanup command rewrites or removes a Git remote")
    elif operation == "config" and any(
        item.lower().startswith("remote.") for item in command
    ):
        violations.append("cleanup command rewrites remote configuration")
    return violations


def _is_permitted_cleanup_command(
    command: Sequence[str], worktree_path: str, branch: str, remote_branch: str
) -> bool:
    permitted = (
        ["worktree", "remove", worktree_path],
        ["worktree", "prune"],
        ["branch", "-d", branch],
        ["push", ORIGIN, "--delete", remote_branch],
    )
    return list(command) in permitted


def _contains_unsafe_command(
    argv: Sequence[Any],
    repository_root: str,
    worktree_path: str,
    branch: str,
    remote_branch: str,
    default_branch: str,
) -> List[str]:
    raw, lowered, violations = _normalise_cleanup_argv(argv)
    if violations:
        return violations
    violations.extend(_shell_wrapper_violations(lowered))
    command, command_violations = _direct_git_command(raw, lowered, repository_root)
    violations.extend(command_violations)
    violations.extend(
        _destructive_cleanup_violations(raw, lowered, command, default_branch)
    )
    if command and not _is_permitted_cleanup_command(
        command, worktree_path, branch, remote_branch
    ):
        violations.append("cleanup command is not an exact permitted task lifecycle operation")
    return violations


def _required_manifest_field_errors(manifest: Mapping[str, Any]) -> List[str]:
    return [
        "manifest is missing required field {}".format(field)
        for field in REQUIRED_MANIFEST_FIELDS
        if field not in manifest
    ]


def _is_strict_posix_descendant(
    candidate: PurePosixPath, parent: PurePosixPath
) -> bool:
    parent_parts = parent.parts
    return (
        len(candidate.parts) > len(parent_parts)
        and candidate.parts[: len(parent_parts)] == parent_parts
    )


def _approved_worktree_root(repository: str) -> PurePosixPath:
    environment_name = WORKTREE_ROOT_ENVIRONMENTS[repository]
    configured = os.environ.get(environment_name)
    if configured:
        candidate = PurePosixPath(configured)
        if candidate.is_absolute() and ".." not in candidate.parts:
            return candidate
        raise ValueError("{} must be an absolute traversal-free path".format(environment_name))
    if repository == "mrts":
        return PurePosixPath(str(ROOT.parent))
    raise ValueError("{} must select the task worktree root".format(environment_name))


def _validate_worktree_path(
    worktree_path: str, repository: str, errors: List[str]
) -> None:
    candidate = PurePosixPath(worktree_path)
    if not candidate.is_absolute():
        errors.append("worktree_path must be absolute")
        return
    try:
        approved_root = _approved_worktree_root(repository)
    except ValueError as error:
        errors.append(str(error))
        return
    if ".." in candidate.parts:
        errors.append("worktree_path is outside the selected task-owned external root")
    elif candidate == approved_root:
        errors.append("worktree_path must be below the selected task-owned external root")
    elif not _is_strict_posix_descendant(candidate, approved_root):
        errors.append("worktree_path is outside the selected task-owned external root")
    authoritative_roots = {
        PurePosixPath(str(item["root"])) for item in EXPECTED_REPOSITORIES.values()
    }
    if candidate in authoritative_roots:
        errors.append("worktree_path must not be an authoritative repository checkout")


def _validate_manifest_identity(
    manifest: Mapping[str, Any], errors: List[str]
) -> Optional[Dict[str, Any]]:
    if manifest.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    task_id = _string(manifest.get("task_id"), "task_id", errors)
    if task_id and ("/" in task_id or ".." in task_id):
        errors.append("task_id must not contain a path separator or traversal")

    repository = _string(manifest.get("repository"), "repository", errors).lower()
    spec = EXPECTED_REPOSITORIES.get(repository)
    if spec is None:
        errors.append("repository must be parent, framework, or mrts")
        return None

    repository_root = _string(manifest.get("repository_root"), "repository_root", errors)
    if repository_root and repository_root != spec["root"]:
        errors.append("repository_root does not match the selected repository")
    default_branch = _string(manifest.get("default_branch"), "default_branch", errors)
    if default_branch and default_branch != spec["default_branch"]:
        errors.append("default_branch does not match the selected repository")

    worktree_path = _string(manifest.get("worktree_path"), "worktree_path", errors)
    if worktree_path:
        _validate_worktree_path(worktree_path, repository, errors)
    branch = _string(manifest.get("branch"), "branch", errors)
    remote_branch = _string(
        manifest.get("remote_branch"), "remote_branch", errors, allow_empty=True
    )
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
    return {
        "task_id": task_id,
        "spec": spec,
        "repository_root": repository_root,
        "default_branch": default_branch,
        "worktree_path": worktree_path,
        "branch": branch,
        "remote_branch": remote_branch,
        "initial_sha": initial_sha,
        "final_sha": final_sha,
        "disposition": disposition,
        "cleanup_status": cleanup_status,
    }


def _validate_manifest_evidence(
    manifest: Mapping[str, Any], errors: List[str]
) -> Dict[str, Sequence[Any]]:
    local_unique_files = _require_list(
        manifest.get("local_unique_files"), "local_unique_files", errors
    )
    evidence_paths = _require_list(manifest.get("evidence_paths"), "evidence_paths", errors)
    running_processes = _require_list(
        manifest.get("running_processes"), "running_processes", errors
    )
    blocked_steps = _require_list(manifest.get("blocked_steps"), "blocked_steps", errors)
    if not evidence_paths:
        errors.append("evidence_paths must retain at least one evidence location")
    return {
        "local_unique_files": local_unique_files,
        "running_processes": running_processes,
        "blocked_steps": blocked_steps,
    }


def _validate_authorization(
    manifest: Mapping[str, Any], errors: List[str]
) -> Set[str]:
    authorization = _require_mapping(manifest.get("authorization"), "authorization", errors)
    if authorization.get("current_user_explicit") is not True:
        errors.append("authorization.current_user_explicit must be true")
    action_classes = _require_list(
        authorization.get("action_classes"), "authorization.action_classes", errors
    )
    if not action_classes:
        errors.append("authorization.action_classes must not be empty")
    selected: Set[str] = set()
    for action_class in action_classes:
        if not isinstance(action_class, str) or not action_class:
            errors.append("authorization.action_classes must contain non-empty strings")
        elif action_class not in AUTHORIZED_ACTION_CLASSES:
            errors.append(
                "authorization.action_classes contains unsupported action {!r}".format(
                    action_class
                )
            )
        elif action_class in selected:
            errors.append(
                "authorization.action_classes must not duplicate {!r}".format(action_class)
            )
        else:
            selected.add(action_class)
    return selected


def _validate_worktree_evidence(
    manifest: Mapping[str, Any], errors: List[str]
) -> Dict[str, Any]:
    worktree = _require_mapping(manifest.get("worktree"), "worktree", errors)
    if worktree.get("task_owned") is not True:
        errors.append("worktree.task_owned must be true")
    if worktree.get("registered_before") is not True:
        errors.append("worktree.registered_before must be true")
    if not isinstance(worktree.get("path_is_symlink"), bool):
        errors.append("worktree.path_is_symlink must be boolean")
    elif worktree.get("path_is_symlink") is not False:
        errors.append("worktree.path_is_symlink must be false")
    if not isinstance(worktree.get("clean"), bool):
        errors.append("worktree.clean must be boolean")
    if not isinstance(worktree.get("registered_after"), bool):
        errors.append("worktree.registered_after must be boolean")
    local_unique_commits = worktree.get("local_unique_commits")
    if (
        isinstance(local_unique_commits, bool)
        or not isinstance(local_unique_commits, int)
        or local_unique_commits < 0
    ):
        errors.append("worktree.local_unique_commits must be a non-negative integer")
        local_unique_commits = 0
    untracked_unique = _require_list(
        worktree.get("untracked_unique_files"), "worktree.untracked_unique_files", errors
    )
    return {
        "worktree": worktree,
        "local_unique_commits": local_unique_commits,
        "untracked_unique": untracked_unique,
    }


def _validate_remote_evidence(
    manifest: Mapping[str, Any], spec: Mapping[str, Any], errors: List[str]
) -> Dict[str, Any]:
    remote = _require_mapping(manifest.get("remote"), "remote", errors)
    if remote.get("name") != ORIGIN:
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
    return {"remote": remote, "remote_sha": remote_sha}


def _validate_pr_evidence(
    manifest: Mapping[str, Any], errors: List[str]
) -> Dict[str, Any]:
    pr = _require_mapping(manifest.get("PR"), "PR", errors)
    return {
        "pr": pr,
        "pr_state": _status_in(pr.get("state"), "PR.state", PR_STATES, errors),
        "pr_head": _sha(pr.get("head_sha"), "PR.head_sha", errors),
    }


def _validate_cleanup_history(
    manifest: Mapping[str, Any], errors: List[str]
) -> Sequence[Any]:
    history = _require_list(manifest.get("cleanup_history"), "cleanup_history", errors)
    for item in history:
        if not isinstance(item, str) or item not in CLEANUP_STATUSES:
            errors.append("cleanup_history contains an unsupported cleanup status")
    return history


def _lifecycle_command(argv: Sequence[str]) -> List[str]:
    lowered = [item.lower() for item in argv]
    git_index = _git_command_index(lowered)
    if git_index is None or len(argv) < git_index + 3 or argv[git_index] != "-C":
        return []
    return list(argv[git_index + 2 :])


def _required_cleanup_action_classes(
    validated_steps: Sequence[Sequence[str]],
) -> Set[str]:
    required: Set[str] = set()
    for argv in validated_steps:
        command = _lifecycle_command(argv)
        if command[:2] in (["worktree", "remove"], ["worktree", "prune"]):
            required.add("worktree_remove")
        elif command[:2] == ["branch", "-d"]:
            required.add("branch_delete_local")
        elif command[:3] == ["push", ORIGIN, "--delete"]:
            required.update({"branch_delete_remote", "push"})
    return required


def _validate_cleanup_steps(
    manifest: Mapping[str, Any],
    context: Mapping[str, Any],
    action_classes: Set[str],
    errors: List[str],
) -> List[Sequence[str]]:
    cleanup_steps = _require_list(manifest.get("cleanup_steps"), "cleanup_steps", errors)
    validated_steps: List[Sequence[str]] = []
    for step in cleanup_steps:
        argv = _require_list(step, "cleanup_steps entry", errors)
        errors.extend(
            _contains_unsafe_command(
                argv,
                context["repository_root"],
                context["worktree_path"],
                context["branch"],
                context["remote_branch"],
                context["default_branch"],
            )
        )
        if argv and all(isinstance(item, str) for item in argv):
            validated_steps.append(argv)
    for action_class in sorted(_required_cleanup_action_classes(validated_steps)):
        if action_class not in action_classes:
            errors.append(
                "cleanup step requires authorization.action_classes to include {!r}".format(
                    action_class
                )
            )
    return validated_steps


def _validate_gitlink_evidence(manifest: Mapping[str, Any], errors: List[str]) -> None:
    gitlinks = _require_mapping(manifest.get("gitlinks"), "gitlinks", errors)
    names = (
        "framework_mrts_before",
        "framework_mrts_after",
        "parent_framework_before",
        "parent_framework_after",
    )
    for name in names:
        _sha(gitlinks.get(name), "gitlinks." + name, errors)
    if gitlinks.get("framework_mrts_before") != gitlinks.get("framework_mrts_after"):
        errors.append("Framework-MRTS Gitlink changed without separate authorization")
    if gitlinks.get("parent_framework_before") != gitlinks.get("parent_framework_after"):
        errors.append("Parent-Framework Gitlink changed without separate authorization")


def _cleanup_actions(
    history: Sequence[Any],
    validated_steps: Sequence[Sequence[str]],
    context: Mapping[str, Any],
    errors: List[str],
) -> Dict[str, bool]:
    actions = {
        "worktree_removed": "removed_local_worktree" in history,
        "local_branch_removed": "removed_local_branch" in history,
        "remote_removed": "removed_remote_branch" in history,
        "saw_worktree_remove": False,
        "saw_local_branch_delete": False,
        "saw_remote_branch_delete": False,
    }
    for argv in validated_steps:
        command = _lifecycle_command(argv)
        if command[:2] == ["worktree", "remove"]:
            if command == ["worktree", "remove", context["worktree_path"]]:
                actions["saw_worktree_remove"] = True
            else:
                errors.append("worktree remove must name the exact task worktree_path")
        elif command[:2] == ["branch", "-d"]:
            if command == ["branch", "-d", context["branch"]]:
                actions["saw_local_branch_delete"] = True
            else:
                errors.append("git branch -d must name the exact task branch")
        elif command[:3] == ["push", ORIGIN, "--delete"]:
            if command == ["push", ORIGIN, "--delete", context["remote_branch"]]:
                actions["saw_remote_branch_delete"] = True
            else:
                errors.append(
                    "git push origin --delete must name the exact task remote branch"
                )
    return actions


def _validate_unique_work_retention(
    context: Mapping[str, Any],
    evidence: Mapping[str, Sequence[Any]],
    worktree_evidence: Mapping[str, Any],
    actions: Mapping[str, bool],
    errors: List[str],
) -> bool:
    has_unique_work = bool(
        evidence["local_unique_files"]
        or worktree_evidence["untracked_unique"]
        or worktree_evidence["local_unique_commits"]
    )
    if context["disposition"] == "local_change_not_delivered":
        if not has_unique_work:
            errors.append("local_change_not_delivered requires unique local work evidence")
        if context["cleanup_status"] != "cleanup_blocked" or not evidence["blocked_steps"]:
            errors.append("local_change_not_delivered must retain work as cleanup_blocked")
        if worktree_evidence["worktree"].get("registered_after") is not True:
            errors.append("local_change_not_delivered must retain the task worktree")
        if any(
            actions[name]
            for name in ("worktree_removed", "local_branch_removed", "remote_removed")
        ):
            errors.append("local_change_not_delivered must not record removed work")
    elif has_unique_work and context["cleanup_status"] != "cleanup_blocked":
        errors.append("unique local work must block cleanup rather than be removed")
    return has_unique_work


def _validate_cleanup_status(
    context: Mapping[str, Any],
    evidence: Mapping[str, Sequence[Any]],
    worktree_evidence: Mapping[str, Any],
    actions: Mapping[str, bool],
    has_unique_work: bool,
    errors: List[str],
) -> None:
    worktree = worktree_evidence["worktree"]
    worktree_clean = worktree.get("clean") is True
    if context["cleanup_status"] == "cleanup_complete":
        if not worktree_clean:
            errors.append("cleanup_complete requires a clean task worktree")
        if worktree.get("registered_after") is not False:
            errors.append("cleanup_complete requires worktree.registered_after=false")
        if context["worktree_path"] and not actions["worktree_removed"]:
            errors.append("cleanup_complete requires removed_local_worktree history")
    if context["cleanup_status"] == "safe_to_remove":
        if not worktree_clean:
            errors.append("safe_to_remove requires a clean task worktree")
        if has_unique_work:
            errors.append("safe_to_remove requires no unique local work")
        if worktree.get("registered_after") is not True:
            errors.append("safe_to_remove requires worktree.registered_after=true")
        if evidence["running_processes"]:
            errors.append("safe_to_remove requires no running processes")
        if evidence["blocked_steps"]:
            errors.append("safe_to_remove requires no blocked cleanup steps")


def _validate_cleanup_action_records(
    worktree_evidence: Mapping[str, Any],
    actions: Mapping[str, bool],
    errors: List[str],
) -> None:
    worktree = worktree_evidence["worktree"]
    if actions["worktree_removed"] and (
        worktree.get("clean") is not True or worktree.get("registered_after") is not False
    ):
        errors.append("removed_local_worktree requires clean unregistered-after worktree evidence")
    if actions["worktree_removed"] and not actions["saw_worktree_remove"]:
        errors.append("removed_local_worktree requires an exact worktree remove command")
    if actions["local_branch_removed"] and not actions["saw_local_branch_delete"]:
        errors.append("removed_local_branch requires an exact git branch -d command")
    if actions["remote_removed"] and not actions["saw_remote_branch_delete"]:
        errors.append("removed_remote_branch requires an exact git push origin --delete command")


def _validate_disposition_constraints(
    manifest: Mapping[str, Any],
    context: Mapping[str, Any],
    pr_state: str,
    actions: Mapping[str, bool],
    errors: List[str],
) -> None:
    disposition = context["disposition"]
    if disposition == "analysis_complete" and context["remote_branch"]:
        errors.append("analysis_complete must not retain a task remote branch")
    if disposition == "no_change" and (context["remote_branch"] or pr_state != "NONE"):
        errors.append("no_change must not create a remote branch or PR")
    if (
        disposition in {"no_change", "merged", "closed_without_merge"}
        and context["worktree_path"]
        and not actions["worktree_removed"]
    ):
        errors.append("final cleanup disposition requires removing the task worktree")


def _validate_open_pr(
    context: Mapping[str, Any],
    remote_evidence: Mapping[str, Any],
    pr_evidence: Mapping[str, Any],
    history: Sequence[Any],
    actions: Mapping[str, bool],
    errors: List[str],
) -> None:
    if pr_evidence["pr_state"] != "OPEN":
        if context["disposition"] == "verified_pr":
            errors.append("verified_pr requires PR.state=OPEN")
        return
    if context["disposition"] != "verified_pr":
        errors.append("an open PR requires expected_disposition=verified_pr")
    if not context["remote_branch"]:
        errors.append("an open PR requires a retained remote_branch")
    if actions["remote_removed"]:
        errors.append("an open PR branch must not be remotely deleted")
    if "remote_branch_retained_for_open_pr" not in history:
        errors.append("an open PR requires remote_branch_retained_for_open_pr history")
    if context["final_sha"] and (
        remote_evidence["remote_sha"] != context["final_sha"]
        or pr_evidence["pr_head"] != context["final_sha"]
    ):
        errors.append("open PR local, remote, and PR-head SHA must match final_task_sha")


def _validate_merged_pr(
    context: Mapping[str, Any],
    remote_evidence: Mapping[str, Any],
    pr_evidence: Mapping[str, Any],
    actions: Mapping[str, bool],
    errors: List[str],
) -> None:
    if context["disposition"] != "merged":
        return
    if pr_evidence["pr_state"] != "MERGED":
        errors.append("merged disposition requires PR.state=MERGED")
    if not actions["remote_removed"]:
        errors.append("merged disposition requires removed_remote_branch history")
    if remote_evidence["remote"].get("deletion_readback") != "absent":
        errors.append("merged remote cleanup requires an absent remote readback")
    if not actions["local_branch_removed"]:
        errors.append("merged disposition requires removed_local_branch history")


def _validate_closed_pr(
    context: Mapping[str, Any],
    remote_evidence: Mapping[str, Any],
    pr_evidence: Mapping[str, Any],
    actions: Mapping[str, bool],
    has_unique_work: bool,
    errors: List[str],
) -> None:
    if context["disposition"] != "closed_without_merge":
        return
    if pr_evidence["pr_state"] != "CLOSED":
        errors.append("closed_without_merge requires PR.state=CLOSED")
    closure_disposition = _string(
        pr_evidence["pr"].get("closure_disposition"), "PR.closure_disposition", errors
    )
    if closure_disposition and closure_disposition not in CLOSED_PR_DISPOSITIONS:
        errors.append("PR.closure_disposition has unsupported value {!r}".format(
            closure_disposition
        ))
    if has_unique_work:
        errors.append("closed_without_merge requires no unique local work")
    if actions["remote_removed"] and remote_evidence["remote"].get(
        "deletion_readback"
    ) != "absent":
        errors.append("closed_without_merge remote cleanup requires an absent remote readback")


def _validate_sha_evidence(
    context: Mapping[str, Any],
    remote_evidence: Mapping[str, Any],
    pr_evidence: Mapping[str, Any],
    errors: List[str],
) -> None:
    if (
        context["final_sha"]
        and remote_evidence["remote_sha"]
        and pr_evidence["pr_state"] not in {"NONE", "OPEN"}
        and pr_evidence["pr_head"] != context["final_sha"]
    ):
        errors.append("PR.head_sha must match final_task_sha")
    if context["initial_sha"] and context["final_sha"] and not context["task_id"]:
        errors.append("task identity is required for SHA evidence")


def validate_cleanup_manifest(manifest: Mapping[str, Any]) -> List[str]:
    """Return policy violations for a secret-free, observed cleanup manifest.

    This is a semantic validation of supplied evidence. It deliberately does
    not call Git, GitHub, the network, or the filesystem for manifest fields.
    """

    errors = _required_manifest_field_errors(manifest)
    if errors:
        return errors
    context = _validate_manifest_identity(manifest, errors)
    if context is None:
        return errors
    evidence = _validate_manifest_evidence(manifest, errors)
    action_classes = _validate_authorization(manifest, errors)
    worktree_evidence = _validate_worktree_evidence(manifest, errors)
    remote_evidence = _validate_remote_evidence(manifest, context["spec"], errors)
    pr_evidence = _validate_pr_evidence(manifest, errors)
    history = _validate_cleanup_history(manifest, errors)
    validated_steps = _validate_cleanup_steps(
        manifest, context, action_classes, errors
    )
    _validate_gitlink_evidence(manifest, errors)
    actions = _cleanup_actions(history, validated_steps, context, errors)
    has_unique_work = _validate_unique_work_retention(
        context, evidence, worktree_evidence, actions, errors
    )
    _validate_cleanup_status(
        context, evidence, worktree_evidence, actions, has_unique_work, errors
    )
    _validate_cleanup_action_records(worktree_evidence, actions, errors)
    _validate_disposition_constraints(
        manifest, context, pr_evidence["pr_state"], actions, errors
    )
    _validate_open_pr(
        context, remote_evidence, pr_evidence, history, actions, errors
    )
    _validate_merged_pr(context, remote_evidence, pr_evidence, actions, errors)
    _validate_closed_pr(
        context, remote_evidence, pr_evidence, actions, has_unique_work, errors
    )
    _validate_sha_evidence(context, remote_evidence, pr_evidence, errors)
    return errors


def _manifest_relative_parts(
    path_value: str, manifest_root: Path
) -> Tuple[Path, Tuple[str, ...]]:
    """Validate the CLI path before opening it below a controlled directory FD."""

    try:
        canonical_root = manifest_root.resolve(strict=True)
    except OSError as error:
        raise ValueError("cleanup manifest root is unavailable: {}".format(error))
    if not canonical_root.is_dir():
        raise ValueError("cleanup manifest root must be a directory")
    candidate_input = PurePosixPath(path_value)
    root_path = PurePosixPath(str(canonical_root))
    if ".." in candidate_input.parts:
        raise ValueError("cleanup manifest path must not contain traversal")
    candidate_path = (
        candidate_input
        if candidate_input.is_absolute()
        else root_path / candidate_input
    )
    if not _is_strict_posix_descendant(candidate_path, root_path):
        raise ValueError("cleanup manifest must be below {}".format(MANIFEST_DIRECTORY))
    relative_parts = candidate_path.relative_to(root_path).parts
    return canonical_root, relative_parts


def _read_manifest_text(root: Path, relative_parts: Sequence[str]) -> str:
    no_follow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if no_follow is None or directory is None:
        raise ValueError(
            "safe cleanup manifest loading requires O_NOFOLLOW and O_DIRECTORY support"
        )
    flags = os.O_RDONLY | no_follow | getattr(os, "O_CLOEXEC", 0)
    directory_flags = flags | directory
    directory_fd: Optional[int] = None
    try:
        directory_fd = os.open(str(root), directory_flags)
        for component in relative_parts[:-1]:
            next_directory_fd = os.open(component, directory_flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_directory_fd
        with os.fdopen(
            os.open(relative_parts[-1], flags, dir_fd=directory_fd), "rb"
        ) as source:
            if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                raise ValueError("cleanup manifest must be a regular file")
            content = source.read(MAX_MANIFEST_BYTES + 1)
    except OSError as error:
        if error.errno in {errno.ELOOP, errno.ENOTDIR}:
            raise ValueError(
                "cleanup manifest must not traverse a symlink or non-directory component"
            )
        raise ValueError("cleanup manifest cannot be read: {}".format(error))
    finally:
        if directory_fd is not None:
            os.close(directory_fd)
    if len(content) > MAX_MANIFEST_BYTES:
        raise ValueError("cleanup manifest exceeds {} bytes".format(MAX_MANIFEST_BYTES))
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("cleanup manifest is not valid UTF-8 JSON: {}".format(error))


def _validate_json_depth(value: Any) -> None:
    stack: List[Tuple[Any, int]] = [(value, 1)]
    while stack:
        current, depth = stack.pop()
        if depth > MAX_MANIFEST_DEPTH:
            raise ValueError("cleanup manifest exceeds JSON nesting limit")
        if isinstance(current, Mapping):
            stack.extend((item, depth + 1) for item in current.values())
        elif isinstance(current, list):
            stack.extend((item, depth + 1) for item in current)


def load_cleanup_manifest(
    path_value: str, manifest_root: Optional[Path] = None
) -> Mapping[str, Any]:
    """Load a bounded regular UTF-8 JSON manifest below the controlled plan root."""

    root = manifest_root if manifest_root is not None else ROOT / MANIFEST_DIRECTORY
    manifest_root, relative_parts = _manifest_relative_parts(path_value, root)
    try:
        value = json.loads(_read_manifest_text(manifest_root, relative_parts))
    except (json.JSONDecodeError, RecursionError) as error:
        raise ValueError("cleanup manifest is not valid UTF-8 JSON: {}".format(error))
    _validate_json_depth(value)
    if not isinstance(value, Mapping):
        raise ValueError("cleanup manifest root must be an object")
    return value


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--policy-root",
        type=Path,
        help="read-only root containing ignored AGENTS.md and .codex policy files",
    )
    parser.add_argument(
        "--cleanup-manifest",
        help=(
            "secret-free observed cleanup manifest below .codex/plans to validate "
            "semantically"
        ),
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
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
