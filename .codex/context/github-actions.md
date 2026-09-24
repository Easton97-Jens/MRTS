# MRTS GitHub Actions Delta

The current governance workflow is repository-owned CI evidence. It pins an exact regular CPython 3.14.6 lane, compiles `tools` and `mrts`, validates an isolated governance-policy fixture, runs standard-library governance/path tests, and checks PR diffs.

Read current workflow contents before making a claim; do not treat this summary as a permanent replacement for `.github/workflows/`.

Remote CI is separate from local tests and from Parent/Framework CI. Do not trigger, rerun, cancel, or modify workflows without current authority for that action.
