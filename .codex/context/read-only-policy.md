# MRTS Default Read-Only Policy

Read-only is the declared default for MRTS when the current top-level user has not explicitly selected MRTS as a writable task target.

The current top-level user must authorize material action classes for writes and delivery. A `workspace-write` sandbox or writable root is a technical capability and does not imply permission.

Read-only inspection may examine source, tests, local control files, Git state, and relevant evidence without changing repository or remote state.
