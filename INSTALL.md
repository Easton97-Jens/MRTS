# Installing MRTS

MRTS needs Python 3. The standard-library governance validator remains
syntax-compatible with Python 3.9. Its CI and pull-request validation lane
uses the exact stable CPython 3.14.6 release (the regular, GIL-enabled build),
not a floating `3.14` selector or a free-threaded variant.

If you only want to build a rule set, basic Python 3 is enough. If you want to
check covered variables, install
[msc_pyparser](https://github.com/digitalwave/msc_pyparser), which is also
available through [PyPI](https://pypi.org/project/msc-pyparser/).

## Governance validation

The focused governance checks use only the Python standard library:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tools.test_validate_governance
PYTHONDONTWRITEBYTECODE=1 python3 tools/validate-governance.py \
  --policy-root <local-control-plane-root>
```

The second command requires the local, ignored `AGENTS.md` and `.codex`
control plane. A cleanup manifest is accepted only as a regular UTF-8 JSON
file below `.codex/plans`; it is bounded in size and nesting, and validation
checks supplied evidence without executing cleanup commands.
