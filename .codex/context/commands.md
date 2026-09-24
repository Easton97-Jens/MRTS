# MRTS Command Policy Delta

Use repository-native entry points and explicit paths. Do not maintain a second exhaustive command catalog.

Governance parity checks use the MRTS-local `PYTHON`:

```text
$PYTHON -m compileall -q tools mrts
$PYTHON -m unittest -v tools.test_validate_governance tools.test_mrts_path_utils tools.test_generate_rules_paths
$PYTHON tools/validate-governance.py --policy-root <active-local-control-plane-root>
```

Generator commands must use explicit existing definition, rule-output, and test-output directories. Exploratory outputs belong under the configured external `OUTPUT_ROOT`/runtime roots, not the checkout.

`mrts/mrts.py` may start processes and write/remove generated/runtime files; inspect its effects and required authorization before execution.
