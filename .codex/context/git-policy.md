# MRTS Git Policy Delta

The default branch is `origin/main`. Never commit/push directly to `main`.

MRTS Git writes require the exact current user-authorized action classes. Preserve unrelated work; use explicit staging only.

Before delivery, remote identity must pass the fork/upstream preflight. A mismatch is `blocked_remote_mismatch`.

The highest automatic delivery state is `verified_pr`; open-PR cleanup may use `verified_pr_remote_cleanup_deferred` when the remote branch must remain for the PR.

An MRTS commit, branch, or PR never authorizes a Framework or Parent Gitlink update.

Never force-push, reset hard, clean, stash unrelated work, rewrite published history, or alter remote configuration as a fallback.
