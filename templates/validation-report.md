# MRTS validation report template

## Validation target

- Task and exact paths:
- MRTS root / branch / HEAD:
- Baseline and final Framework/Parent Gitlink state:
- Security and authorization boundary:

## Checks

| Check | Command / procedure | Status | Result / limitation |
| --- | --- | --- | --- |
|  |  | `passed` / `failed` / `blocked` / `not_run` / `not_applicable` |  |

## Boundary controls

- Default read-only negative case:
- Explicit authorization positive case:
- Selected action classes and task-owned-worktree evidence:
- No unauthorized Git/remote/dependency/generator action:
- No Framework/Parent Gitlink update:
- Secret/artifact hygiene:

## Remote and cleanup lifecycle

- origin fetch URL / effective push URL / expected `Easton97-Jens/MRTS` result:
- GitHub owner, writable permission, archive state, and default branch:
- Local / remote / PR-head SHA relation:
- Cleanup manifest and exact worktree registration/status/untracked/unique-commit/process evidence:
- Open PR retained remote branch or merged/closed remote-delete readback:
- Local `rtk git ... branch -d` result and no `branch -D`:
- Exact non-force `rtk git ... worktree remove` / `worktree prune` / list readback:
- No `git clean`, `git reset --hard`, force-push, or upstream push:
- Framework-MRTS and Parent-Framework Gitlink OIDs before/after:

## Conclusion

- Acceptance criteria disposition:
- Residual risk:
- Delivery state:
- Cleanup final status:
