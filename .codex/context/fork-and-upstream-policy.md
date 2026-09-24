# MRTS Fork and Upstream Policy Delta

The expected writable repository is `Easton97-Jens/MRTS`.

Before an authorized branch push, PR operation, or remote deletion, inspect both fetch and effective push destinations, including:

```text
git remote get-url origin
git remote get-url --push origin
```

Both must resolve to the expected user repository. A mismatch is `blocked_remote_mismatch`.

`upstream` is informational. Never push, delete branches, rewrite URLs, or fall back to `upstream` to bypass an origin mismatch.
