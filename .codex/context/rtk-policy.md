# MRTS RTK Policy Delta

Read `/root/.codex/RTK.md` before local command execution. Inherited `PARENT-COMMAND-EXECUTION` is the canonical generic RTK policy.

MRTS-specific additions:

- generator, governance, Git, test, diff, scanner, and cleanup commands use the verified RTK path;
- RTK does not grant write, package-install, network, GitHub, delivery, or merge authority;
- observed command, exit code, and limitations remain evidence facts;
- no raw-command fallback is invented merely because RTK rejects or lacks a capability.
