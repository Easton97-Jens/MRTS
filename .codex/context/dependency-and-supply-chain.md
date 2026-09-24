# MRTS Dependency and Supply-Chain Policy Delta

MRTS basic rule generation requires Python 3. Optional covered-variable checks may require `msc_pyparser`; full local execution may additionally depend on tools such as `go-ftw` and `albedo`.

Do not install missing dependencies globally. Provision only task-required dependencies into the MRTS-owned environment or task-owned external tool area with recorded source/version/provenance.

Do not silently substitute Parent/Framework environments, moving versions, unverified downloads, or a different executable found earlier in `PATH`.
