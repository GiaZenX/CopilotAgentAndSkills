# Family E round 1 — Verifier verdict (TSK-0034 BUG-0013, TSK-0035 BUG-0006), 2026-08-11

Kit-hardening batch: kit hooks resolving stdlib names from an agent-writable dir (BUG-0013), and the
ordering-branch derivation missing helper hops (BUG-0006). One implementer, one suite acceptance,
verifier over two rounds + a residue-closing polish.

## Verdict: PASS

### TSK-0035 / BUG-0006 — PASS (round 1)
Transitive `_reaches_producer`/`_commands_reaching` with cycle guard: fixture yields
`{direct, one-hop, two-hops}`, cycle terminates and is not counted. Red-without-fix reproduced
(direct-only → `{direct}`). At the live `kernel/cli.py` all three CLI branches call the producers
directly, so `_ORDERING_COMMANDS` is unchanged and there is nothing to mirror — confirmed.

### TSK-0034 / BUG-0013 — PASS (round 2, after rework)
Round 1 FAIL was real and blocking: the finder was bound to `import _kernel`, so enforcement hooks
that never import `_kernel` (`gate_pipeline`, `gate_test_coverage`, `guard_no_adhoc`, …) resolved
`re`/`subprocess` unprotected — a planted `subprocess.py` silently disabled `gate_pipeline`
(red pipeline → rc 0). Reworked: the stdlib-wins finder moved into the LAUNCHER `_gate.py`
(`_stdlib_guard.py`, installed before every `exec`), so every registered hook is covered regardless
of `_kernel`. Verifier round 2, measured over the real launcher:
- planted `subprocess.py`: guard on → rc 2, not executed, correct reason ("quality pipeline RED");
  guard off → rc 0, executed. Red-without-fix confirmed.
- `_compat.stop` gate + planted `re.py`: guard on → rc 2 for the guard's OWN reason ("Blocked
  creating"); guard off → rc 2 from the launcher catch-all — the REASON assertion is what makes the
  test real (exit-code-only would pass without the fix).
- fail-closed: `_stdlib_guard.py` removed → every launched gate rc 2 ("guard could not be installed").
- registration tripwire (`test_every_refusal_capable_registered_hook_runs_through_the_launcher`):
  both ends measured — a new `_compat.stop` gate registered off-launcher → RED; a comfort hook
  direct-registered → GREEN. The property ("every refusal-capable registered hook runs behind the
  launcher") is enforced at the registration surface, not as a gate list.
- mirror: `_stdlib_guard.py`/`_gate.py`/`_kernel.py` byte-identical across the three kits.
Round-1 comment defect (importlib preload claim) fixed: `_stdlib_guard` reaches `PathFinder` via
`sys.meta_path`, imports only `os`/`sys`.

### Residue polish (verifier-specified, then closed)
The round-2 PASS named two latent test-infra residues; both closed with red-without-fix tests and a
self-check that no comfort hook is misclassified:
- (A) `_refuses` widened from a 2-construct enumeration to the property "calls a no-return refusal"
  (`_compat.stop`/`_kernel.block`/`sys.exit`/`os._exit`, attribute or aliased; literal 0 = allow,
  non-literal = conservative refuse). Named remaining residue: fully dynamic refusal
  (`raise SystemExit`, `getattr(...)(...)`) — no shipped hook uses it (measured).
- (B) `_stage_launcher` now follows the transitive `sibling_import_closure` (one home in
  `tools/conftest.py`, shared with `_stage_kernel_bridge`) instead of a one-level parse, so a
  grandchild import can no longer make all launcher tests silently measure fail-closed.

## Enforcement code unchanged since PASS (lead measurement)
md5 of the three enforcement files matches the verifier's measured values exactly across all three
kits: `_stdlib_guard.py` 6288308c, `_gate.py` 0e752cc4, `_kernel.py` 506f7aec. The polish rounds
touched only `tools/` test infrastructure — the verified substance is byte-identical.

## Acceptance
`pytest tools/ -q` → 2444 passed / 13 skipped, one run; ruff clean; `tools/validate.py` exit 0;
kit stamp dev/office/research 2026.08.11-3 (`--check` unchanged; the enforcement changes were stamped
in the rework round, the polish touched only `tools/`).

## Named residues carried (non-blocking)
1. Direct run without launcher AND without `_kernel` (test suite / hand diagnosis) stays unprotected
   — production routes every refusal-capable hook through `_gate.py` (verified via settings.json +
   frontmatter). Documented in `_gate.py` next to the existing `-B` residual.
2. New fail-closed dependency on `_stdlib_guard.py` — a half-shipped kit (`_gate.py` without the
   guard) refuses every gated call rather than running unprotected. Deliberate; documented.
3. `tools/bump_kit_version.py:32` puts `team-kits/` on sys.path unguarded — a tool, not a hook, runs
   only in this repo.
4. Non-stdlib shadowing (`yaml`) in the hooks dir — outside BUG-0013's stdlib scope; handled
   separately in `.claude/hooks`.
5. `sys.stdlib_module_names` assumes Python ≥ 3.10 — consistent with `.claude/hooks/_harness.py`.
6. `_refuses` does not recognise fully dynamic refusals — no shipped hook uses them.
