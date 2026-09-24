# MRTS Context Index

Load only the files relevant to the active task.

| Task | MRTS-local file | Inherited Parent owner |
| --- | --- | --- |
| Repository identity / scope | `project-overview.md`, `architecture.md`, `repository-boundaries.md` | `PARENT-ARCHITECTURE-AND-BOUNDARIES` |
| Precedence / instruction conflict | `policy-precedence.md` | `PARENT-POLICY-PRECEDENCE` |
| Goal / plan / prompt reconciliation | `goal-driven-execution.md` | `PARENT-TASK-WORKFLOW` |
| RTK / command execution | `rtk-policy.md`, `commands.md` | `PARENT-COMMAND-EXECUTION` |
| Feasibility | `feasibility.md` | `PARENT-FEASIBILITY` |
| Read-only default / action classes | `read-only-policy.md`, `repository-boundaries.md` | local MRTS owner |
| Python / dependencies / provenance | `dependency-and-supply-chain.md`, `tool-provenance.md` | `PARENT-PYTHON-POLICY`, `PARENT-TOOLING-AND-LANGUAGE` |
| Tests / governance / evidence | `testing.md`, `governance-validation.md`, `evidence.md` | `PARENT-TESTING-AND-EVIDENCE` |
| Security / findings | `security.md`, `finding-management.md` | `PARENT-SECURITY-POLICY`, `PARENT-FINDINGS` |
| Git / forks / delivery | `git-policy.md`, `fork-and-upstream-policy.md`, `delivery-and-ci.md` | local MRTS authorization rules |
| GitHub Actions | `github-actions.md` | local MRTS CI delta |
| Documentation | `documentation.md` | repository-native docs |
| Cleanup / restoration | `cleanup.md` | local MRTS lifecycle |
| Final completion | `definition-of-done.md` | `PARENT-DEFINITION-OF-DONE` |

The historical filenames above are retained because `tools/validate-governance.py` requires them. They are intentionally concise and must not become duplicated copies of Parent policy bodies.
