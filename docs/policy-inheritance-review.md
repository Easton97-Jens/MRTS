# Parent policy inheritance review

This change reviews three inherited policy changes against canonical Connector
commit `11fab78a5447f75cb254ddf963eca770fa04ba04`. MRTS retains the policies by
identity and SHA-256 in [the inheritance manifest](../.codex/inheritance-manifest.toml).
Canonical policy bodies remain owned by the Connector repository.

| Policy | Reviewed source change | MRTS effect |
| --- | --- | --- |
| `PARENT-COMMAND-EXECUTION` | Connector commit `9913026c1feec85a1862d22987689a1ebcef6d97` documents native RTK hooks, `rtk bypass` for complete evidence, and separate wrapper/authentication authority. | Keep RTK around native MRTS commands. Hook configuration does not authorize writes, credentials, installation or delivery. Existing host-local hook choices remain authoritative. |
| `PARENT-TESTING-AND-EVIDENCE` | Connector commit `42fd5a8e895aca3a36b09eb09fe5c7cf9c3399e3` defines the shared expanded default inventory ceiling of100 and freezes historical I12 closeout to existing evidence. | MRTS cases selected by Parent count in that shared ceiling. Standalone MRTS governance tests remain a separate explicitly selected repository check; no new default cases, automatic historical matrix, or capability promotion is introduced. The current readiness request authorizes only its targeted repairs and checks. |
| `PARENT-DEFINITION-OF-DONE` | The same Connector commit defines scoped completion and the finite I12 closeout boundary. | Preserve actual missing validation and truthful partial/blocked results; a focused MRTS governance success is neither connector runtime qualification nor a merge authorization. |

The previous pinned bytes were located in actual Connector Git history and
matched each old SHA-256 before reviewing the complete text delta. All27
canonical source digests were checked against their actual files; only these
three MRTS pins required changes. MRTS local read-only/action-class, dependency,
governance, evidence and delivery deltas remain stricter and compatible. No
policy body, local execution configuration, test expectation, enclosing Gitlink,
or CI requirement is changed.

Validation uses the Parent inheritance validator against an explicitly recorded
composition of the selected Parent/Framework policies and this candidate MRTS
manifest, plus MRTS-native governance checks on the exact regular CPython3.14.6
lane. The local Sonar precheck is suspended by the current user's explicit
instruction; existing hosted checks are preserved. Execution commands and
terminal results are recorded with the pull request and task evidence. A
candidate-policy check does not claim that the enclosing repositories have
already integrated or pinned this MRTS revision. Those integrations require
separate authorization and exact resulting commit identities.
