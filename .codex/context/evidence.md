# MRTS Evidence Policy Delta

Separate these evidence layers:

- source/static inspection;
- generator execution;
- unit/governance tests;
- optional MRTS infrastructure/go-ftw execution;
- Parent/Framework connector-host evidence.

A successful generator or governance validator does not prove connector runtime behavior. Generated files are not automatically current host evidence.

Store task-owned logs, analysis artifacts, manifests, hashes, and validation output under configured external roots. Keep secrets, credentials, raw sensitive traffic, and unbounded logs out of local control files.
