# MRTS governance rule migration

## Purpose and scope

This report establishes a native MRTS governance control plane while preserving
the Parent, Framework, and MRTS repositories as separate ownership and Git
boundaries. It applies to the existing MRTS Git root resolved with
`git rev-parse --show-toplevel`. A non-trivial versioned MRTS task normally
uses one task-owned external worktree under
`/var/tmp/codex/worktrees/mrts/<task-id>`; direct work in the embedded checkout
is allowed only when the current user expressly selects it and its separate
restoration path.

The governing outcome is intentionally narrow:

- MRTS is read-only by default when the current user does not explicitly name
  it as a writable target.
- A current user may explicitly authorize a scoped MRTS task. That task works
  only in MRTS's own Git repository, task-owned worktree, branch, commit,
  push, PR, and cleanup lifecycle.
- Parent and Framework never stage or commit MRTS source/files, and neither
  the Framework-MRTS nor Parent-Framework Gitlink moves without a separately
  explicit authorization.

Policy text is organizational control evidence. It does not prove that a
particular Codex host or sandbox technically denies an unauthorized write.

## Fork and remote verification

| Check | Expected | Observed | Status |
| --- | --- | --- | --- |
| GitHub repository | `Easton97-Jens/MRTS` | `Easton97-Jens/MRTS` | passed |
| Default branch | `main` | `main` | passed |
| Writable fork permission | required | administrator-level permission observed | passed |
| origin fetch / push | `https://github.com/Easton97-Jens/MRTS.git` | exact URL | passed |
| Upstream repository | verified official source | `owasp-modsecurity/MRTS` | passed |
| upstream fetch | official URL | `https://github.com/owasp-modsecurity/MRTS.git` | passed |
| upstream push | never use | prohibited by policy; no push performed | passed |

The existing Framework `.gitmodules` entry and local submodule configuration
already point to the same fork URL. No URL or Gitlink update is needed.

## Current local state and migration approach

Before this migration, Parent, Framework, and MRTS control-plane files treated
the existing checkout as unconditionally immutable. The current task's exact
user authorization selects the same existing MRTS repository as an independent
writable Git boundary; it does not authorize a Framework or Parent Gitlink
change.

The migration does not relax system/platform safety, default-branch protection,
force-push prohibition, upstream-push prohibition, secret handling, external
artifact containment, or independent Git/PR delivery.

## Task-owned worktree and cleanup lifecycle

Every non-trivial MRTS task has a secret-free cleanup manifest with task and
repository identity, exact root/path/branch, baseline/final SHA, default
branch, remote/PR evidence, expected disposition, unique local files,
evidence/process/cleanup/blocked-step records, and completion time. It records
the ordered cleanup states `pending`, `safe_to_remove`,
`removed_local_worktree`, `removed_local_branch`,
`remote_branch_retained_for_open_pr`, `removed_remote_branch`,
`restored_recorded_gitlink`, `cleanup_complete`, or `cleanup_blocked`.

The lifecycle distinguishes `analysis_complete`, `no_change`,
`local_change_not_delivered`, `verified_pr`, `merged`, and
`closed_without_merge`:

- An open verified PR retains its remote branch/head. Only after exact
  local/remote/PR SHA evidence, no unique local work/process, and no further
  edit plan may its local worktree/branch be removed; record
  `verified_pr_remote_cleanup_deferred`.
- A merged or evidenced closed PR may remove task-local and verified-`origin`
  remote branches only after current readback, no dependencies/unique work,
  and retained evidence.
- A task worktree is removable only after ownership, exact registered path,
  status/untracked/unique-commit/PR/process/evidence checks. Use only
  `rtk git -C <MRTS_ROOT> worktree remove <EXACT_WORKTREE_PATH>`, then
  `rtk git -C <MRTS_ROOT> worktree prune` and a new
  `rtk git -C <MRTS_ROOT> worktree list --porcelain`; never use `--force` or
  manually delete a registered worktree.
- A local branch is removed only after it is not checked out and only with
  `rtk git -C <MRTS_ROOT> branch -d <TASK_BRANCH>`. A refusal is retained as
  `cleanup_blocked_unmerged_local_branch`; never use `git branch -D`.
- A remote deletion uses only
  `rtk git -C <MRTS_ROOT> push origin --delete <TASK_BRANCH>` after the fresh
  MRTS fork preflight and GitHub/readback. Never push or delete through
  `upstream`.

The manifest/validator evaluates supplied evidence structurally; a passing
result does not itself execute cleanup or prove host enforcement.

## Rule migration matrix

| Current rule | Target rule | Change class | Owner | Authorization | Behaviour impact | Evidence | Validator check | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Global goal-driven execution contract and validation | Keep mandatory contract, feasibility, milestones, validation, and reconciliation | migrate_exact | MRTS | every task | none to product | active skill and `AGENTS.md` | required policy markers | implemented |
| Global RTK command proxy | Require canonical RTK for every command | reference_global_policy | MRTS | every command | command evidence only | `rtk-policy.md` | required policy markers | implemented |
| Parent/Framework unconditional MRTS read-only wording | Default read-only; current user may explicitly target MRTS | adapt_to_mrts | Parent / Framework / MRTS | current top-level user and task contract | governance only | migrated policy clauses | policy markers and review | implemented |
| Existing MRTS immutable/read-only-only plan | Allow explicit, action-class-scoped MRTS task plan | adapt_to_mrts | MRTS | current top-level user | governance only | `AGENTS.md` / read-only policy | authorization markers | implemented |
| Non-trivial versioned work in a shared checkout | One task-owned external worktree and cleanup manifest unless the user explicitly selects direct embedded work | adapt_to_mrts | MRTS | explicit `worktree_create` / direct-checkout selection | governance and delivery isolation only | cleanup policy / manifest | manifest semantics and negative fixtures | implemented |
| Post-delivery branch/worktree retention | Evidence-gated local cleanup; retain an open PR remote branch; delete merged/evidenced-closed remote branch only after readback | adapt_to_mrts | MRTS | explicit deletion action classes | governance only | cleanup/delivery policy | merged/open/dirty/foreign/unsafe command fixtures | implemented |
| `sandbox_mode = "read-only"` claimed as enforced mode | Retain declared conservative default; require observed runtime evidence before claiming enforcement | adapt_to_mrts | MRTS local configuration | active environment separately grants capability | no product behavior | config and policy text | declared-default marker | implemented |
| Parent/Framework/MRTS separate ownership | Retain separate repository, branch, PR, and evidence lifecycles | retain_existing | all | every cross-repo task | none | boundary policies | Gitlink wording review | implemented |
| Framework staging / Gitlink prohibition | Retain: MRTS source never staged in Framework; Gitlink only by separately authorized Framework task | retain_existing | Framework | separate Framework authorization | none | Framework status/diffs | final Gitlink checks | implemented |
| Parent Framework Gitlink prohibition | Retain: no Parent Gitlink update by implication | retain_existing | Parent | separate Parent authorization | none | Parent status/diff | final Gitlink checks | implemented |
| Writable fork branch, exact staging, normal push and PR | Use only after explicit task action authority and own MRTS delivery lifecycle | merge_with_existing | MRTS | explicit branch/commit/push/PR authority | governance/delivery only | Git and delivery policies | final SHA/PR checks | implemented |
| `origin` / `origin.pushurl` / `upstream` relationship | both origin fetch and effective push resolve to `Easton97-Jens/MRTS`; upstream is verified source and never receives a push/delete | adapt_to_mrts | MRTS | explicit remote action when changing config | no product behavior | remote verification | remote-mismatch/upstream negative fixtures | implemented |
| Generators, orchestrator, Python dependencies and external tools | Keep external output/runtime/tool-root containment | retain_existing | MRTS | separate generator/dependency authorization | none | command/dependency policies | no-write validator scope | implemented |
| Security, findings, evidence and secrets rules | Keep scoped security assessment, truthful evidence and secret safety | migrate_exact | MRTS | applicable task | none | security/evidence policies | required policy markers | implemented |
| Parent/Framework subagent and PR policies | No inferred MRTS authority; a separate MRTS task/PR is required | adapt_to_mrts | all | current top-level user | governance only | boundary policies | final review | implemented |
| Existing English-only MRTS documentation convention | Use English governance documents; no German companion is required by current MRTS convention | retain_existing | MRTS | documentation task | documentation only | README/INSTALL inventory | report present | implemented |
| Existing product scripts / generated examples | Do not modify or regenerate them for governance validation | not_applicable_with_reason | MRTS | separate product task | none | source inventory | validator does not execute scripts | implemented |
| Tokens, personal configuration, private environments, caches | Do not copy or version | sensitive_do_not_copy | all | never | none | secret-hygiene review | final scan/search | implemented |
| Parent/Framework ignored local control planes | Update in place; do not create artificial commits or PRs | local_only_do_not_copy | Parent / Framework | current task | local governance only | ignore classification | final status | implemented |

## Source rule disposition matrix

Every source considered for this governance migration has an explicit
disposition below. “Current user” means the current top-level user instruction,
not a Parent/Framework policy, an agent brief, a prior task, or a PR.

| Quelle | Regel/Zweck | MRTS-relevant | Entscheidung | MRTS-Ziel | Begründung |
| --- | --- | ---: | --- | --- | --- |
| Global `goal-driven-execution` skill | Contract, feasibility, milestones, validation, and prompt reconciliation | yes | migrate_exact | `AGENTS.md`, `goal-driven-execution.md`, task-contract template | The workflow applies to every MRTS task and does not itself grant write authority. |
| Global `/root/.codex/RTK.md` | Canonical command wrapper, capability verification, and command evidence | yes | reference_global_policy | `rtk-policy.md`, `commands.md`, `AGENTS.md` | MRTS routes to the global source of truth rather than copying a local RTK implementation. |
| Parent `AGENTS.md` | Separate repositories, default read-only boundary, explicit current-user selection, no implied Gitlink | yes | adapt_to_mrts | `AGENTS.md`, `repository-boundaries.md`, `read-only-policy.md` | MRTS is writable only in its own repository after exact action-class authorization. |
| Parent `policy-precedence.md` | Authority order and non-inferable MRTS authorization | yes | adapt_to_mrts | `policy-precedence.md` | Preserves system/security precedence and rejects authorization inferred from Parent/Framework text. |
| Parent `cross-repository-orchestration-policy.md` | Parent/Framework/MRTS coordination, Gitlink separation, nested-checkout evidence | yes | adapt_to_mrts | `repository-boundaries.md`, `evidence.md`, `definition-of-done.md` | Direct work in the existing MRTS root remains independent of either Gitlink lifecycle. |
| Parent `framework-policy.md` and Framework ownership rules | Framework may not stage MRTS source or update Gitlinks by implication | yes | retain_existing | `repository-boundaries.md`, `git-policy.md` | This control remains necessary even when MRTS work is explicitly authorized. |
| Parent `security-workflow.md`, `security.md` | Security triggers, focused validation, no unsupported enforcement claim | yes | adapt_to_mrts | `security.md`, `testing.md`, `evidence.md` | MRTS security work is scoped to MRTS and records limitations truthfully. |
| Parent `finding-management-policy.md` | Durable finding ownership, evidence, verification, risk disposition | yes | adapt_to_mrts | `finding-management.md`, `evidence.md` | Adds MRTS-local finding structure without allowing a finding to update a Gitlink. |
| Parent `definition-of-done.md`, `task-workflow.md`, `prompt-adherence-policy.md` | Completion evidence, scope reconciliation, delivery limits | yes | adapt_to_mrts | `definition-of-done.md`, templates | An authorized MRTS task needs its own evidence while Parent/Framework Gitlinks remain unchanged. |
| Parent Python, dependency, storage, testing, and command policies | No implicit installs/caches; external generator/runtime output; bounded validation | yes | adapt_to_mrts | `dependency-and-supply-chain.md`, `commands.md`, `testing.md`, `cleanup.md` | Content-write authority does not authorize dependency, generator, cache, or runtime side effects. |
| Parent Git, delivery, master, PR-retention, and subagent policies | Explicit staging, normal fork push, Draft PR, no merge/default push/force/admin bypass | yes | adapt_to_mrts | `git-policy.md`, `fork-and-upstream-policy.md`, `delivery-and-ci.md`, `cleanup.md` | MRTS owns its own branch/fork/PR lifecycle; Parent/Framework never confer it. |
| Parent local audit and tests | Validate default boundary plus explicit current-user route | yes | adapt_to_mrts | Parent `.codex` audit and focused tests | Audit expectations must not treat the authorized MRTS path as a policy conflict. |
| Framework `AGENTS.md` | Framework task boundary, RTK, default read-only MRTS behavior | yes | adapt_to_mrts | MRTS `AGENTS.md`, `rtk-policy.md` | Framework work remains non-authorizing; the user-selected MRTS task is separate. |
| Framework precedence, local, repository-boundary, and MRTS-boundary policies | Scope selection, Gitlink/staging protection, direct-checkout handling | yes | adapt_to_mrts | `policy-precedence.md`, `repository-boundaries.md`, `read-only-policy.md` | Preserves Framework-only safeguards and removes an absolute veto of the current user. |
| Framework security, delivery, master, restoration, DoD, and subagent policies | Separate security/delivery lifecycle; no Framework-derived MRTS authority | yes | adapt_to_mrts | `security.md`, `delivery-and-ci.md`, `definition-of-done.md`, templates | A separately selected MRTS task cannot be used to bypass Framework controls or alter its Gitlink. |
| Framework `.gitmodules` and local submodule configuration | Fork URL and recorded MRTS Gitlink | yes | retain_existing | `fork-and-upstream-policy.md`, migration evidence | Both URLs already use the verified fork; no URL or Gitlink edit is required. |
| Framework local audit and focused tests | Detect RTK/boundary-policy drift | yes | adapt_to_mrts | Framework local audit and tests | Expected text now checks the default boundary and explicit-user exception. |
| Existing MRTS `AGENTS.md`, `.codex/config.toml`, and read-only policy | Existing default read-only language and local sandbox declaration | yes | merge_with_existing | native `AGENTS.md`, `read-only-policy.md`, `policy-precedence.md` | Retains the conservative default while documenting task-scoped user authorization and no runtime-enforcement overclaim. |
| Existing MRTS README, INSTALL, CHANGES, and project layout | English documentation convention and Python 3.9 project shape | yes | retain_existing | `project-overview.md`, `documentation.md`, `testing.md` | Governance documentation stays English and the validator uses only the Python standard library. |
| Existing MRTS generators/orchestrators and product sources | Product/runtime behavior and generated outputs | yes | not_applicable_with_reason | command/testing policy only | The task is governance-only; no generator or product source is executed or modified. |
| Existing MRTS CONTRIBUTING/SECURITY files and GitHub workflows | Repository contribution/security/CI convention | no — absent at inventory time | not_applicable_with_reason | migration report evidence | Missing files are not fabricated; future additions need their own scope. |
| Sensitive local settings, credentials, environments, caches, and evidence payloads | Prevent secret/private-data copying and machine-specific leakage | yes | sensitive_do_not_copy | no versioned MRTS destination | Governance docs record only safe provenance and redacted evidence. |
| Parent/Framework ignored local control planes | Local governance edits that are not versioned | yes | local_only_do_not_copy | Parent/Framework existing ignored files | Update in place and report them; do not manufacture a Parent/Framework commit or PR. |
| Unclear new authority outside the current prompt | Any action not enumerated by the current user | yes | conflict_requires_resolution | task contract and feasibility record | Stop and obtain a new current-user decision rather than inferring authority. |

## Native control-plane structure

```text
AGENTS.md
.codex/
  README.md
  context/
    index.md
    project-overview.md
    architecture.md
    policy-precedence.md
    repository-boundaries.md
    goal-driven-execution.md
    rtk-policy.md
    commands.md
    testing.md
    security.md
    finding-management.md
    dependency-and-supply-chain.md
    github-actions.md
    tool-provenance.md
    documentation.md
    evidence.md
    git-policy.md
    fork-and-upstream-policy.md
    delivery-and-ci.md
    feasibility.md
    cleanup.md
    definition-of-done.md
    read-only-policy.md
    governance-validation.md
templates/
  task-contract.md
  change-record.md
  validation-report.md
tools/
  validate-governance.py
  test_validate_governance.py
```

All versioned documentation uses repository-relative paths and `MRTS_ROOT`.
The local configuration can document the known installation, but it is not the
only functional repository definition.

## Control-plane versioning disposition

The existing MRTS Git configuration classifies `AGENTS.md` and `.codex/` as
local control-plane material through `.git/info/exclude`. They are updated in
place for this checkout but deliberately are not force-staged or added to the
MRTS commit. The versioned governance deliverables are
`docs/governance/rule-migration.md`, the reusable templates, and the
standard-library validator and its no-write test under `tools/`.

Parent and Framework `AGENTS.md` and `.codex/` policy edits are likewise
local/ignored in their existing repositories. No synthetic Parent or Framework
commit or PR is created. This is a versioning classification, not evidence
that local policy text is technically enforced by every runtime environment.

## Validation and residual risk

The native validator is deliberately read-only. It validates control-plane
structure/markers and semantic consistency of a caller-supplied cleanup
manifest; it does not execute cleanup or prove sandbox enforcement, generator
runtime, external service behavior, GitHub CI, reviews, SonarQube, remote
deletion, or access-control behavior beyond the evidence actually observed.
Those conditions remain task specific and must be reported with their exact
status.

The final migration validation records Markdown/routing, validator, policy
searches, `git diff --check`, secret hygiene, remote configuration, MRTS
branch/HEAD/status, Framework Gitlink status, Parent Gitlink status, and the
separate MRTS delivery evidence. No Gitlink update is part of this migration.
