# MRTS Feasibility Delta

Use inherited `PARENT-FEASIBILITY` for generic feasibility reasoning.

MRTS adds an authorization gate: technical feasibility never substitutes for missing current user action classes. A writable sandbox, existing fork permission, installed dependency, or clean checkout does not itself authorize a write or delivery action.

Complete safe independent read-only work when possible. Report the smallest missing action class, prerequisite, credential, tool, environment fact, or user decision instead of inventing authority.
