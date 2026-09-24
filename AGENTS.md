# MRTS Repository Instructions

<!-- codex-control-plane-routing:mrts -->

## Scope

These instructions govern the independent MRTS Git repository at the root returned by `git rev-parse --show-toplevel`.
When embedded, the expected checkout is `/root/git/ModSecurity-conector/modules/ModSecurity-test-Framework/tools/MRTS`.
The Gitlink relationship does not merge MRTS ownership, branches, commits, pull requests, delivery authority, or evidence with Framework or Parent.

## Mandatory startup order

For every MRTS task:

1. read `/root/.agents/skills/goal-driven-execution/SKILL.md` completely;
2. read `/root/.codex/RTK.md` before shell/project commands;
3. when embedded, read Parent `AGENTS.md` and Parent `.codex/inheritance-manifest.toml`;
4. when embedded, read Framework `AGENTS.md` and the Framework MRTS-boundary policy;
5. read this `AGENTS.md`;
6. read `.codex/inheritance-manifest.toml` and `.codex/context/index.md`;
7. load only the inherited Parent owners and MRTS-local policies required by the task.

Do not copy Parent policy bodies into MRTS files. Parent-wide rules are inherited by digest-pinned policy IDs. MRTS files contain only repository-specific constraints and compatibility routing required by the repository-native governance validator.

## Mandatory goal-driven execution

Use the global skill for goal, execution contract, plan, milestones, validation, and completion reconciliation. A read-only discovery pass may locate the active control plane before the full plan, but must not change product state.

## Default read-only boundary

MRTS is read-only by default. Unless the current top-level user explicitly selects MRTS as a writable target for the active task, only inspect and analyze it. A permissive `sandbox_mode` is a declared runtime capability and does not imply permission.

The current user must expressly authorize each material action class.

Allowed action-class vocabulary:

`content_edit`, `worktree_create`, `worktree_remove`, `branch_create`, `branch_delete_local`, `branch_delete_remote`, `commit`, `push`, `pr_create`, `pr_update`, `pr_close`, `merge`, `restore_recorded_gitlink`.

No policy, prior task, subagent, issue, PR, commit, or generic request adds a missing action class.

## Repository boundaries

Parent, Framework, and MRTS are separate Git and delivery units. An MRTS task never authorizes:

- Parent or Framework content changes;
- the Framework `tools/MRTS` Gitlink update;
- the Parent Framework Gitlink update;
- Parent or Framework commits, pushes, PRs, or merges.

A Framework or Parent task likewise never authorizes MRTS changes by implication.

## Worktree and Git safety

For non-trivial versioned MRTS work, use a task-owned external worktree below `/var/tmp/codex/worktrees/mrts/<task-id>` unless the current user explicitly selects the embedded checkout and authorizes the required action classes.

Before delivery actions, verify the current remote topology. `origin` must resolve to the writable `Easton97-Jens/MRTS` repository. `upstream` is informational only. A mismatch is `blocked_remote_mismatch`; never rewrite remotes as a fallback.

Never commit/push directly to `main`, force-push, use an administrative bypass, weaken checks, or infer merge authority. The highest automatic delivery state is `verified_pr`; an actual merge requires the current explicit `merge` action class and exact-head verification.

## Command execution

RTK is mandatory for shell, Git, test, diff, generator, scanner, and validation commands. Parent `PARENT-COMMAND-EXECUTION` remains the canonical generic execution policy. MRTS-specific command selection is routed through `.codex/context/commands.md`.

## Runtime, generated output, and storage

Use the active MRTS `.codex/config.toml` roots. Task-owned source copies, generated output, build/runtime data, logs, caches, analysis data, evidence, temporary files, and Python environments belong under `/var/tmp/codex/MRTS` or the explicit external worktree root.

Do not use Parent, Framework, or the MRTS checkout as overflow storage. Versioned `generated/` output is changed only when the current task explicitly authorizes the corresponding content change and the generator/update contract requires it.

## Python

MRTS owns its Python environment. Governance CI uses exact regular CPython `3.14.6`; the standard-library governance validator remains syntax-compatible with the documented Python 3.9 baseline. Do not silently use the Parent or Framework virtual environment.

Use `/var/tmp/codex/MRTS/venv` for the MRTS-local environment when Python setup is required. Optional dependencies such as `msc_pyparser` are installed only for tasks that actually require them and only in the task-approved MRTS environment.

## Security and evidence

Treat generator paths, output containment, YAML input, subprocess invocation, external tools, runtime infrastructure, Git/GitHub state, and cleanup manifests as security boundaries. Do not weaken path containment or convert a generator/tool success into connector-host runtime evidence.

Findings need concrete evidence, a legitimate control, scope, impact, counterevidence, and validation. Cross-repository findings are reported to the owning repository without modifying it.

## Context routing

Start with `.codex/context/index.md`. Important MRTS-local owners include repository boundaries, read-only authorization, commands/generators, Python/dependencies, testing/governance, security/findings, Git/delivery, cleanup, and Definition of Done.

The repository-native governance validator requires several historical `.codex/context/*` filenames. These files are intentionally retained as short routing/delta policies; do not expand them by copying Parent policy bodies.

## Completion

Before reporting completion, reconcile the exact user request, authorized action classes, validation performed, MRTS HEAD/status, remote destination when relevant, cleanup state, and both enclosing Gitlinks when embedded. Report only observed branch, SHA, PR, CI, review, and merge facts.
