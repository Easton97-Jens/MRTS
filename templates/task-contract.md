# MRTS task contract template

## Task identity

- Task / date:
- Current user authorization (exact scope):
- Classification: `trivial` | `non_trivial` | `blocked`
- MRTS root (`git rev-parse --show-toplevel`):

## Goal and scope

- Goal:
- Required deliverables:
- In scope:
- Non-goals:
- Parent impact and Gitlink disposition:
- Framework impact and MRTS Gitlink disposition:

## Authorization and feasibility

- Authorized action classes (`content_edit` / `worktree_create` / `worktree_remove` / `branch_create` / `branch_delete_local` / `branch_delete_remote` / `commit` / `push` / `pr_create` / `pr_update` / `pr_close` / `merge` / `restore_recorded_gitlink`):
- Prohibited actions:
- Feasibility status and evidence:
- Assumptions and open decisions:
- Security invariant and relevant trust boundaries:

## Baseline and plan

- MRTS branch / HEAD / status:
- Default branch:
- origin fetch URL / effective push URL / upstream URL:
- GitHub repository / owner / archive state / writable permission:
- Framework-recorded MRTS Gitlink:
- Parent-recorded Framework Gitlink:
- Worktree ownership, exact task-owned path, creation time, and initial SHA:
- Cleanup manifest path and planned lifecycle disposition:
- Milestones and validation:
- Delivery state and cleanup disposition:

## Cleanup manifest and retention

- `task_id`, repository, repository root, worktree path, local branch, remote branch, and PR:
- Initial SHA, final task SHA, default branch, and expected merge/closure disposition:
- Local unique files, evidence paths, running processes, cleanup steps, blocked steps, completion time:
- Cleanup status/history (`pending` through `cleanup_complete` or `cleanup_blocked`):
- Open PR branch retention / merged-or-closed remote deletion readback:
- Embedded-checkout recorded-Gitlink restoration (only when expressly authorized):

## Completion

- Final validation evidence:
- Residual risks / checks not run:
- Requirement reconciliation:
- Overall outcome: `complete` | `partial` | `blocked` | `failed`
