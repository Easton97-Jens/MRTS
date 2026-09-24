# MRTS Security Policy Delta

Apply inherited `PARENT-SECURITY-POLICY` and inspect MRTS-specific trust boundaries:

- YAML/JSON definitions and template expansion;
- generated rule/test filenames and path containment;
- symlink/traversal handling;
- subprocess argv and executable provenance;
- optional `go-ftw`, `albedo`, infrastructure start/stop tools;
- generator cleanup behavior;
- Git/GitHub destination identity;
- cleanup-manifest parsing and exact lifecycle operations;
- secrets or sensitive data in generated/evidence output.

Do not weaken `path_utils.py` containment, governance validation, or cleanup restrictions to make a test pass. Security claims require observed evidence and a legitimate control.
