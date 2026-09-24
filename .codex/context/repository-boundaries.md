# MRTS Repository Boundaries

MRTS is read-only by default during Parent or Framework work.

When MRTS is changed by a separately authorized task, the preferred location for non-trivial versioned work is a task-owned worktree below `/var/tmp/codex/worktrees/mrts/<task-id>`.

Framework may show `tools/MRTS (new commits)` when the embedded checkout has moved locally. That observation is not permission to stage or update the Framework Gitlink.

The Framework-MRTS Gitlink and Parent-Framework Gitlink must remain unchanged unless their owning repositories receive separate current authorization.

Parent, Framework, and MRTS preserve separate status, branch, commit, PR, CI, review, delivery, evidence, and cleanup records.
