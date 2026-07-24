# Kernel schemas (HARNESS_V2_SPEC.md II.5 / II.11 Phase 1)

Mandatory-field schema files, fixed BEFORE kernel operations use them:

| file | contract | budget |
|---|---|---|
| result_envelope.yaml | specialist -> orchestrator result envelope (II.1/II.5) | <= 4 KB serialized |
| session_brief.yaml | generated/session_brief.yaml content contract (II.5) | <= 25 KB serialized |
| arc_companion.yaml | ARC companion YAML fields (II.2/II.6a) | - |
| wfr_companion.yaml | WFR companion YAML fields (II.2/II.6a) | - |

Validation: `kernel/schemas.py` (strict -- unknown top-level fields are
rejected, fail-closed). Budgets are measured over the canonical JSON
serialization (`kernel/hashing.canonical_json`) so the limit is
implementation-independent.

**Deliberately NOT duplicated here:** the V1->V2 status-mapping table lives
canonically in `kernel/backlog_types.py` (importable by the migration tool).
One canonical storage location per piece of information (II.12) -- a YAML twin
would be a second source of truth.

Distribution: single source under `team-kits/kernel/`; the scaffold copies the
kernel (incl. this directory) into each kit installation (Phase 2/4 wiring).
