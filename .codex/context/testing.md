# MRTS Testing Policy Delta

Prefer the smallest focused check first, then repository governance checks appropriate to the change.

Current high-value checks include:

```text
$PYTHON -m compileall -q tools mrts
$PYTHON -m unittest -v tools.test_validate_governance tools.test_mrts_path_utils tools.test_generate_rules_paths
$PYTHON tools/validate-governance.py --policy-root <active-local-control-plane-root>
git diff --check
```

Use exact regular CPython 3.14.6 for governance-CI parity. The documented Python 3.9 syntax compatibility of the standard-library validator is a compatibility property, not permission to claim 3.14.6 CI parity from another interpreter.

A generator, unit-test, or governance PASS is MRTS evidence only. It is not connector-host runtime or Framework promotion evidence.
