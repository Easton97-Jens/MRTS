# MRTS Project Overview

MRTS generates ModSecurity-compatible rules and regression-test definitions from structured YAML/JSON descriptions. It can also orchestrate selected local test infrastructure through `mrts/mrts.py`.

The repository owns the generator, rule/test definitions, generated examples/artifacts, path-containment helpers, governance tooling, and its own Git/CI lifecycle. It does not own Parent connector implementations, Framework connector promotion, or either enclosing Gitlink.

Current default branch is `main`. The repository is an independent delivery unit even when embedded at `tools/MRTS`.
