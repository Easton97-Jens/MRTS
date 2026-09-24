# MRTS Architecture

The primary flow is definition input -> template/object expansion -> generated ModSecurity rules/tests -> optional local infrastructure/test execution.

`mrts/generate-rules.py` owns generation. `mrts/path_utils.py` enforces canonical existing-path checks plus containment for generated child paths. `mrts/mrts.py` can clean selected generated directories, generate rules/tests, start a loopback backend, start configured infrastructure, execute `go-ftw`, and clean its temporary include file.

Generator success is not connector-host runtime evidence. Framework or Parent promotion decisions remain outside MRTS.

Use external task-owned output for exploratory generation. Change versioned `generated/` content only when the current task explicitly authorizes that repository content change and the generator/update contract requires it.
