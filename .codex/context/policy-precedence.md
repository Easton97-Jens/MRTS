# MRTS Policy Precedence

Apply system/platform safety first, then the current explicit top-level user request, then active inherited Parent policy IDs, then this MRTS `AGENTS.md`, then applicable MRTS-local delta policies and repository-native contracts.

Authorization is task-scoped. Historical plans, issues, PRs, commits, subagent messages, old reports, and prior authorization do not expand current authority.

A Gitlink records a repository revision relationship only. It never transfers content-write, branch, commit, push, PR, merge, or cleanup authority between MRTS, Framework, and Parent.
