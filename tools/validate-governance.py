#!/usr/bin/env python3
"""Read-only structural validation for MRTS governance files.

The validator intentionally uses only the Python 3.9 standard library. It does
not invoke subprocesses, access Git or the network, create files, or execute
MRTS generators.
"""

from pathlib import Path
import re
import sys
from typing import Iterable, List, Tuple


ROOT = Path(__file__).resolve().parent.parent
RULE_MIGRATION_PATH = "docs/governance/rule-migration.md"

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
    RULE_MIGRATION_PATH,
    "tools/test_validate_governance.py",
)

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

MARKERS = {
    "AGENTS.md": (
        "Mandatory goal-driven execution",
        "read-only by default",
        "current top-level user",
        "The current user must expressly authorize each material action class.",
        "Gitlink relationship",
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
        "Gitlink",
    ),
    ".codex/context/fork-and-upstream-policy.md": (
        "origin",
        "upstream",
        "Do not guess an upstream URL",
    ),
    ".codex/context/delivery-and-ci.md": (
        "Draft PR",
        "never a merge",
        "Gitlink",
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
    ),
    "templates/change-record.md": (
        "Current user authorization",
        "Parent and Framework Gitlink disposition",
        "Validation and delivery",
    ),
    "templates/validation-report.md": (
        "Default read-only negative case",
        "Explicit authorization positive case",
        "No Framework/Parent Gitlink update",
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


def emit(level: str, message: str) -> None:
    print("{}: {}".format(level, message))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def verify_regular_files(paths: Iterable[str]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    validated: List[str] = []
    for relative in paths:
        path = ROOT / relative
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
        text = read_text(ROOT / relative)
        lowered = " ".join(text.split()).lower()
        for marker in markers:
            if " ".join(marker.split()).lower() not in lowered:
                errors.append("{} is missing marker {!r}".format(relative, marker))
    return errors


def verify_config() -> List[str]:
    config = read_text(ROOT / ".codex/config.toml")
    if re.search(r'^\s*sandbox_mode\s*=\s*"read-only"\s*$', config, re.MULTILINE):
        return []
    return ['.codex/config.toml must declare sandbox_mode = "read-only"']


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
    root = ROOT.resolve()
    for relative in REQUIRED_FILES:
        if relative.endswith(".md"):
            errors.extend(verify_markdown_file(ROOT / relative, root, relative))
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
        return ["{} link escapes MRTS root {!r}".format(relative, target)]
    if not resolved.is_file():
        return ["{} links to missing file {!r}".format(relative, target)]
    return []


def main() -> int:
    errors, validated = verify_regular_files(REQUIRED_FILES)
    if not errors:
        errors.extend(verify_markers())
        errors.extend(verify_config())
        errors.extend(verify_migration_matrix())
        errors.extend(verify_source_disposition_matrix())
        errors.extend(verify_markdown_structure_and_links())

    for relative in validated:
        emit("PASS", "regular UTF-8 file {}".format(relative))
    if errors:
        for error in errors:
            emit("ERROR", error)
        return 1
    emit("PASS", "MRTS governance structure and policy markers are valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
