# MRTS Local Codex Control Plane

This directory contains MRTS-local Codex configuration and repository-specific policy deltas.

Parent-wide rules are inherited through `.codex/inheritance-manifest.toml`. The repository-native governance validator requires the historical local context filenames, so those names are retained as concise routing/delta files rather than copied Parent policy bodies.

Runtime, build, generated scratch output, caches, evidence, analysis data, and Python environments belong under `/var/tmp/codex/MRTS` unless a higher-priority active configuration overrides them.

The MRTS checkout is read-only by default by policy. `sandbox_mode = "workspace-write"` is a technical capability required by the repository governance contract and does not grant write authority.
