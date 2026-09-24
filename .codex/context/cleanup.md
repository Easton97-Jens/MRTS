# MRTS Cleanup Policy Delta

Cleanup applies only to task-owned resources recorded before mutation.

For non-trivial versioned work, use a task-owned external worktree and a secret-free cleanup manifest under the policy-approved plan area. Safe lifecycle operations may include exact `git worktree remove`, `git worktree prune`, `git branch -d`, and—only with current authorization—`git push origin --delete` for the exact task branch.

Never use force removal, `git clean`, `git reset --hard`, stash, broad `rm`, remote rewriting, or cleanup of foreign resources.

An open PR retains its remote branch as `remote_branch_retained_for_open_pr`; local cleanup may result in `verified_pr_remote_cleanup_deferred` at the delivery layer.

Do not run `worktree remove`, `git branch -d`, or `push origin --delete` unless the corresponding current action classes are present.

Both enclosing Gitlinks must be compared before/after and remain unchanged unless separately authorized by their owning repositories.
