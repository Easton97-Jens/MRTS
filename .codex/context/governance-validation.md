# MRTS Governance Validation Delta

The repository-native governance validator is read-only. It validates required local control-plane files/markers, config mode, versioned migration matrices, Markdown structure/links, and optional cleanup-manifest semantics.

For CI parity use exact regular CPython 3.14.6:

```text
$PYTHON -m compileall -q tools mrts
$PYTHON tools/validate-governance.py --policy-root <active-local-control-plane-root>
$PYTHON -m unittest -v tools.test_validate_governance tools.test_mrts_path_utils tools.test_generate_rules_paths
```

The standard-library validator's Python 3.9 syntax compatibility does not make another interpreter equivalent to the pinned governance CI lane.

Do not modify versioned governance tests merely to make a local policy layout pass. Preserve the required historical context filenames as concise compatibility policies.
