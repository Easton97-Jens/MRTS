# MRTS Delivery and CI Delta

MRTS delivery is independent from Framework and Parent. When authorized, use a task branch and create/update a Draft PR after task-owned validation.

A verified open PR may end in `verified_pr_remote_cleanup_deferred` when the remote task branch must remain for review. Local task worktree/branch cleanup may proceed only under the exact cleanup policy and action classes.

`verified_pr` is never a merge. Merge requires the current explicit `merge` action class plus exact PR-head, checks/reviews/conversations, and repository-state verification.

No MRTS delivery action updates either enclosing Gitlink by implication.
