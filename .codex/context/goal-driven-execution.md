# MRTS Goal-Driven Execution Delta

The canonical workflow is the global `/root/.agents/skills/goal-driven-execution/SKILL.md` plus inherited `PARENT-TASK-WORKFLOW`.

For MRTS add these fields to the execution contract when relevant:

- current user authorization;
- selected MRTS action classes;
- MRTS base SHA/branch/status;
- Framework-MRTS Gitlink before/after disposition;
- Parent-Framework Gitlink before/after disposition;
- MRTS validation commands;
- cleanup-manifest path for non-trivial versioned work;
- delivery endpoint and exact PR/head state if delivery is authorized.

Planning never grants a missing action class.
