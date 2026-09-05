"""Generation 4: ONE work order per product goal (DEC-0067), created through the kernel.

Seams are a FIELD (`--seam-scope`, C-4 of generation 3) and the cut is MEASURED with
`check-scopes --only` before any spawn (DEC-0070 (1)). Hole numbers are reserved IN the item
(generation-3 cut finding); next free after H150: G4-1 H151-H153, G4-2 H154-H156, G4-3 H157-H159,
G4-4 H160-H162. Not idempotent -- run once, read the ids.
"""
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
KERNEL = [sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory", "create-task"]

COMMON_FORBIDDEN = [
    "scaffold_team.*", "install.*", "init_project_memory.*", "team-kits/gen_provider_artifacts.py",
    "user/**", "CLAUDE.md", "project_memory/**",
]
# Shared on purpose by every stream: new files under tools/ and docs/, the provisional stamp.
COMMON_SEAMS = ["tools/**", "docs/**", "team-kits/*/VERSION"]

RIGOUR = (
    "Per absorbed wish or bug its own red-first test measured in a copy outside the repo (restore "
    "the defect, see red, put it back) and its own acceptance line in the protocol; the verifier "
    "reports PER acceptance criterion of the goal. Every new property claim -- code comment, "
    "docstring, docs, hole list -- is MEASURED before handover; a named test must be able to fail "
    "(four cases in generation 3 could not); every hole-list citation carries its module prefix; "
    "hole numbers {holes} ONLY, reserved here in the item; forbidden_scope project_memory/** "
    "EXCEPTS project_memory/staging/(this task id)/ -- said here so the item does not contradict "
    "itself (generation-3 cut finding). Wherever the truth about a shell can be executed, a real "
    "shell is the arbiter, not a derivation (DEC-0070). Only the READING suites run in the "
    "stream; the full suite belongs to the merge (DEC-0050, five breaches in generation 3 ~5 h)."
)
HANDOVER = (
    "Handover: worktree C:/Offline Repos/v2-testbed/_worktrees/g4-{name} (branch g4/{name} off "
    "feat/harness-v2 at 75a00d1); ALL scratch only under C:/Offline Repos/v2-testbed/_round-scratch/"
    "(this task id)/; a red-first rig refuses to run outside its own directory and writes binary "
    "(the generation-3 CRLF incident); verifier copies made WITHOUT the .git file of the worktree; "
    "patch = the worktree diff WITHOUT the VERSION hunks at C:/Offline Repos/v2-testbed/"
    "_round-scratch/(this task id)/stream-{name}.patch (a patch carrying VERSION hunks is a cut "
    "finding, DEC-0070); protocol at project_memory/staging/(this task id)/stream-protocol.md with: "
    "seam table (received / expected at merge), per-criterion acceptance line + red-first tests, "
    "measured lines, what was deliberately not closed but named, the one-line rejected alternative "
    "of the plan (FR-0084 shape), suite runs (reading suites only), provisional VERSION stamp, "
    "wall-clock and tokens for the (g) table. No commit, no push, no install to the global store."
)

STREAMS = {
    # ------------------------------------------------------------ G4-1  test discipline & hooks
    "testgate": dict(
        pr="PR-0004", type="implementation", acs=["AC-1", "AC-2", "AC-3", "AC-4"],
        allowed=[
            ".claude/hooks/gate_test_scope.py", ".claude/hooks/test_gates.py", ".claude/settings.json",
            "team-kits/*/hooks/**", "team-kits/*/settings/**",
            "team-kits/*/skills/quality-engineer/**",
            "team-kits/dev-team/templates/repo/scripts/kit_browser_checks.py",
            "team-kits/research-team/templates/repo/scripts/kit_browser_checks.py",
            "team-kits/*/VERSION", "tools/**", "docs/**",
        ],
        forbidden=[
            "team-kits/*/hooks/gate_dispatch.py",
            "team-kits/kernel/**", "team-kits/*/constitution/**", "team-kits/*/agents/**",
            "team-kits/*/skills/project-manager/**", "team-kits/*/skills/project-auditor/**",
            "team-kits/*/skills/parallel-streams/**", "team-kits/*/skills/humanizer/**",
            ".claude/hooks/gate_lead_write_scope.py", ".claude/hooks/gate_spawn_needs_item.py",
            ".claude/hooks/gate_commit_evidence.py", ".claude/hooks/gate_todo_items.py",
            ".claude/hooks/_harness.py", ".claude/agents/**", ".github/**", ".gitattributes",
        ] + COMMON_FORBIDDEN,
        seams=COMMON_SEAMS + [".claude/hooks/test_gates.py", "team-kits/*/hooks/session_status.py",
                              "team-kits/*/hooks/_routine.py"],
        inputs=[
            "project_memory/product/active/PR-0004.yaml (the goal; its AC-1..AC-4 are the contract) and the wishes it absorbed: project_memory/archive/FR/2026/FR-0086.yaml (the gate: property 'the line names no selection', intent said ON the line like gate 3, runners = the project's declared test command, threshold a config value), FR-0057.yaml (QE measure + the eight office hook entries without timeout), docs/POST_V2_WISHLIST.md H139 (the BUILD half of FR-0077: C1-C3 in browser_smoke())",
            "DEC-0050 (full suite once per round), DEC-0061 (run_scope full opens the merge), DEC-0063 (4), DEC-0070 (retrospective: rules 2 and 4), DEC-0056 (cost side of every gate)",
            "This repo: .claude/settings.json (every entry names a timeout; gate 1 reads its own), .claude/hooks/_harness.py (Deadline, command-line reading -- READ ONLY, forbidden), the four gates as the shape of a gate here, .claude/hooks/test_gates.py (EXPECTED_TOOLS compared with settings.json both ways); kits: team-kits/*/settings/settings.json, hooks/_gate.py + session_status.py (how a kit hook learns its deadline), gate_shell_hygiene.py (the neighbour that reads shell lines), skills/quality-engineer/SKILL.md; dev-team templates/repo/scripts/kit_browser_checks.py (mirrored to research byte-identical: change BOTH or KIT_SPECIFIC_SCRIPTS names the reason)",
            "project_memory/staging/generation-3-streams.md (g) notes: the five measured full-run breaches (which lines, which suites, how long) -- the error class this goal closes",
        ],
        outputs=[
            "PR-0004 AC-1 (FR-0086): a gate on the SCOPE of a test run in THIS repo (.claude/hooks/gate_test_scope.py registered in .claude/settings.json with a timeout, measured in test_gates.py) and one hook mirrored x3 in the kits: a command line that runs the whole declared test surface during a round is refused with the affected-suites sentence and the exact delivery line; the delivery prefix passes and the kernel records that run as run_scope full; a selection passes; a second bare full run after a recorded full run in the same round is refused unless that run yielded findings; measured as processes on a scaffolded pilot and here; red-first per branch; the threshold (suite duration or declared size) is a config value with its DEC line; H151-H153 for what stays open.",
            "PR-0004 AC-2 (FR-0057): every hook entry of every kit settings.json names a timeout (the eight office shell hooks first); a shipped test is red on an entry without one and the kit's own deadline reader refuses such an entry with a sentence (the shape of _harness.Deadline here); the quality-engineer and implementer skill texts state the run-scope rule as a PROCEDURE (affected suites in a round, the full run once before delivery), measured against the kit text.",
            "PR-0004 AC-3 (H139): C1/C2/C3 run in browser_smoke() of kit_browser_checks.py on the built app of a scaffolded dev pilot, each red on a planted violation; the research-team mirror byte-identical or KIT_SPECIFIC_SCRIPTS names the reason; H139 closed with the test named (module prefix).",
            "PR-0004 AC-4: the cost side per DEC-0056 named per gate and measured: a project whose whole suite runs in seconds, a project without UI, the deadline of every new hook against its registered timeout.",
            RIGOUR.format(holes="H151 to H153"),
            "Seams: constitution / PM-skill sentences that must name the new gate -> stream G4-3 (verbatim in the protocol); .claude/hooks/test_gates.py is shared with G4-2 (holes judges) and G4-4 (timing test) -- append your tests in a block of your own, never edit theirs; session_status.py / _routine.py are yours, G4-3 reports sentences for the auditor trigger; docs/POST_V2_WISHLIST.md: G4-2 migrates the hole list into items -- you file H151-H153 as entries in the CURRENT format and say so, G4-2's migration carries them over.",
            HANDOVER.format(name="testgate"),
        ],
    ),
    # ------------------------------------------------------------ G4-2  kernel contracts
    "kernel": dict(
        pr="PR-0005", type="implementation", acs=["AC-1", "AC-2", "AC-3", "AC-4", "AC-5"],
        allowed=[
            "team-kits/kernel/**", "team-kits/*/hooks/gate_dispatch.py", ".claude/hooks/test_gates.py",
            "team-kits/*/templates/project_memory/**",
            "team-kits/*/VERSION", "tools/**", "docs/**",
        ],
        forbidden=[
            "team-kits/kernel/kitupdate.py",
            "team-kits/*/hooks/_*.py", "team-kits/*/hooks/gate_approval.py", "team-kits/*/hooks/gate_git.py",
            "team-kits/*/hooks/gate_write_scope.py", "team-kits/*/hooks/session_status.py",
            "team-kits/*/hooks/guard_*.py", "team-kits/*/settings/**",
            "team-kits/*/constitution/**", "team-kits/*/agents/**", "team-kits/*/skills/**",
            "team-kits/*/templates/repo/**",
            ".claude/hooks/gate_*.py", ".claude/hooks/_harness.py", ".claude/settings.json", ".claude/agents/**",
            ".github/**", ".gitattributes",
        ] + COMMON_FORBIDDEN,
        seams=COMMON_SEAMS + [".claude/hooks/test_gates.py", "docs/POST_V2_WISHLIST.md"],
        inputs=[
            "project_memory/product/active/PR-0005.yaml (AC-1..AC-5) and what it absorbed: project_memory/bugs/active/BUG-0090.yaml (selection evidence vs VERIFIED), BUG-0091.yaml (task under an inbox item), project_memory/archive/FR/2026/FR-0085.yaml (SR duty by class), FR-0087.yaml (holes as items), project_memory/staging/TSK-0118/stream-protocol.md section 3 (C-2 refusal on overlapping scope in create_lease, C-3 worktree field on the lease -- with the two D tests that go red) and TSK-0117 section 6/10 (what C built: check-scopes, seam_scope, plan approval, blocked, minted_via)",
            "DEC-0061 (run scope), DEC-0064 (MST), DEC-0066 (hierarchy), DEC-0067 (bundle at PR), DEC-0068 (plan approval), DEC-0069 (H138 acceptance as the shape of a user-accepted hole), DEC-0070 (rules 1 and 2), DEC-0056",
            "team-kits/kernel/backlog_types.py (AUTOMATA, REQUIRED_FIELDS, ROOT_TYPE_BY_KIT, APPROVAL_TRANSITIONS, EVIDENCE_RESULTS, RUN_SCOPES), state.py (_assert_confirmed, capture, _dates_in), report.py (_delivery_evidence, qa_verdicts, validate_state), approvals.py (plan, minted_via, IRREVERSIBLE_KINDS), dispatch.py (create_lease), scopes.py (check-scopes), cli.py; team-kits/*/hooks/gate_dispatch.py; .claude/hooks/test_gates.py (the hole-list judges + name-resolution tests: they move to read ITEMS); docs/POST_V2_WISHLIST.md (150 entries to migrate once)",
            "project_memory/staging/generation-3-streams.md: the three cut findings about hand-reserved hole numbers (why FR-0087 exists) and the two-readers question",
        ],
        outputs=[
            "PR-0005 AC-1 (BUG-0090): a DEC line beside DEC-0061 decides refuse-or-walk; then either a passing test Evidence with run_scope selection that names the BUG walks FIXED -> VERIFIED, or the refusal text and evidence --help stop describing a targeted run; the merge gate's reading unchanged (test_report::test_a_pass_from_a_partial_run_is_not_merge_evidence_and_a_fail_still_is stays green); red-first.",
            "PR-0005 AC-2 (BUG-0091): create-task refuses an FR as product_requirement or derives_from with the triage route in the remedy (CONVERTED + resulting_item), or the DEC documents the allowed case and the board labels it as inbox work; existing tasks stay valid; a check over the index counts TSKs whose root is an FR (21 today); red-first.",
            "PR-0005 AC-3 (FR-0085): a TSK under a PR of class normal or large is refused at dispatch (kernel create_lease or gate_dispatch, decided with reasons) while no ACCEPTED SR hangs under that PR, remedy names the architect step; small is not asked; measured on a scaffolded pilot as a process; red-first.",
            "PR-0005 AC-4 (FR-0087): DEC first (BUG-shaped with a 'limits' duty and a user-minted acceptance edge, or an own type); ids by the kernel; the test_gates judges-test and name-resolution test read ITEMS (parsed), the merge seam table reads holes from the index; the existing H1-H150 migrated ONCE through the kernel with the H number kept as a field and a GENERATED pointer index left in docs/POST_V2_WISHLIST.md that a hand edit invalidates; the kits ship the same shape (templates/project_memory dirs); no second list beside the first for longer than this round; the other three streams file their new holes in the current format and you carry them over at merge -- say how in the protocol.",
            "PR-0005 AC-5 (C-2/C-3): create_lease refuses a task whose allowed_scope overlaps a running lease at file level (check-scopes as the predicate, seam_scope subtracted); a lease carries the worktree it was granted for; D's tests test_nothing_shipped_refuses_two_tasks_whose_scopes_overlap and test_the_lease_carries_no_tree_of_its_own rewritten to the new contract in THIS stream with the parallel-streams text lines that change handed to G4-3 verbatim as a seam.",
            RIGOUR.format(holes="H154 to H156"),
            "Seams: .claude/hooks/test_gates.py shared with G4-1 (gate 5 tests) and G4-4 (timing test) -- your block only; kitupdate.py is G4-4's (BUG-0088) -- forbidden here; constitution / PM-skill sentences (SR duty, inbox rule, hole items) -> G4-3 verbatim; hooks other than gate_dispatch.py -> G4-1; every other stream's hole entries arrive in the merge -- your migration must accept the current entry format from a patch.",
            HANDOVER.format(name="kernel"),
        ],
    ),
    # ------------------------------------------------------------ G4-3  procedure & retrospective
    "procedure": dict(
        pr="PR-0006", type="implementation", acs=["AC-1", "AC-2", "AC-3", "AC-4"],
        allowed=[
            "team-kits/*/constitution/**", "team-kits/*/skills/project-manager/**",
            "team-kits/office-team/skills/office-manager/**", "team-kits/*/skills/project-auditor/**",
            "team-kits/*/skills/parallel-streams/**", "team-kits/*/agents/project-auditor.md",
            "team-kits/*/agents/project-manager.md", ".claude/agents/harness-lead.md",
            ".claude/agents/harness-implementer.md", ".claude/agents/harness-verifier.md",
            "team-kits/*/VERSION", "tools/**", "docs/**",
        ],
        forbidden=[
            "team-kits/kernel/**", "team-kits/*/hooks/**", "team-kits/*/templates/**", "team-kits/*/settings/**",
            "team-kits/*/skills/quality-engineer/**", "team-kits/*/skills/humanizer/**",
            "team-kits/dev-team/skills/frontend-design/**", "team-kits/dev-team/skills/product-designer/**",
            ".claude/hooks/**", ".claude/settings.json", ".github/**", ".gitattributes",
        ] + COMMON_FORBIDDEN,
        seams=COMMON_SEAMS,
        inputs=[
            "project_memory/product/active/PR-0006.yaml (AC-1..AC-4) and what it absorbed: project_memory/archive/FR/2026/FR-0084.yaml (review as EVENT: four measured questions, three lines to the user, the rejected-alternative line in every TSK plan), FR-0005.yaml (cut critic presents a SMALLER plan), FR-0010.yaml (the five malformed order-line forms), project_memory/decisions/active/DEC-0070.yaml (rules 1, 2, 5 for the harness-lead role)",
            "DEC-0062, DEC-0063, DEC-0067 (the PM procedure of parallel specialists -- the parallel-streams skill you now own), DEC-0074-era context in FR-0074 (taste stays the user's), DEC-0056",
            "team-kits/*/constitution/AGENTS.md, skills/project-manager/SKILL.md, skills/project-auditor/SKILL.md, agents/project-auditor.md (the FR-0038/TSK-0112 run record: 'the hook reports, the PM spawns' -- the trigger lives in hooks/_routine.py + session_status.py, which G4-1 owns: your trigger sentences are a SEAM to G4-1), .claude/agents/harness-lead.md (gate 1 refuses the lead; you edit it), the lead-in rule test for shared constitution paragraphs (tools/test_role_contracts.py), tools/test_shortening_net.py (section pins)",
            "project_memory/staging/generation-3-streams.md: the eight cut findings and three orchestrator failures = the cases FR-0005/FR-0010/DEC-0070 rule 5 are written against; project_memory/staging/TSK-0114/merge-protocol.md section 9 and TSK-0120 section 9 ((g) tables = the retrospective's data)",
        ],
        outputs=[
            "PR-0006 AC-1 (FR-0084): the project-auditor role (kits) and the harness-lead role (here) ask the four measured questions at the named events (phase end, merge/release, repeated finding class, changed decision premise) and write three lines to the user into the session brief / the round log; a TSK plan without the rejected-alternative line is refused by the plan check (where a check exists; else the skill's own step with a measured pilot); measured on a scaffolded pilot; the trigger wiring in hooks is a SEAM to G4-1, verbatim.",
            "PR-0006 AC-2 (FR-0005): a cut critic step before the order in the PM skill (and in harness-lead.md here): it presents a smaller plan with what it removed and why, the PM records the choice; measured against the kit text and on a pilot.",
            "PR-0006 AC-3 (FR-0010): the five malformed order-line forms in the project-manager role text as a procedure with the case behind each; measured against the kit text (a test that can fail).",
            "PR-0006 AC-4 (DEC-0070): harness-lead.md carries rule 1 (measure the cut with check-scopes before spawn; reserve hole numbers in the item), rule 2 (a command-line guard is a DEC-first design round), rule 5 (a queued message is no delivery; silence longer than a verification's wall-clock = ListAgents), each pointing at DEC-0070; the harness-implementer / -verifier texts gain the generation-3 lessons that are theirs (real shell as arbiter; a rig refuses to run outside its directory and writes binary; a named test must be able to fail); a tools test reads the role texts for the pointers.",
            RIGOUR.format(holes="H157 to H159"),
            "Seams: you RECEIVE sentences from G4-1 (the test-scope gate), G4-2 (SR duty, inbox rule, hole items, lease refusal) and G4-4 (none expected) -- table 'received at cut time: none; expected at merge: G4-1, G4-2' in the protocol; the shared constitution paragraph rule (in >= 2 constitutions => in all three or listed with reason) measured by the existing tests.",
            HANDOVER.format(name="procedure"),
        ],
    ),
    # ------------------------------------------------------------ G4-4  repo hygiene
    "hygiene": dict(
        pr="PR-0007", type="ops", acs=["AC-1", "AC-2", "AC-3", "AC-4"],
        allowed=[
            ".github/**", ".gitattributes", "team-kits/kernel/kitupdate.py", ".claude/hooks/test_gates.py",
            "team-kits/*/VERSION", "tools/**", "docs/**",
        ],
        forbidden=[
            "team-kits/kernel/backlog_types.py", "team-kits/kernel/state.py", "team-kits/kernel/approvals.py",
            "team-kits/kernel/dispatch.py", "team-kits/kernel/report.py", "team-kits/kernel/scopes.py",
            "team-kits/kernel/cli.py", "team-kits/kernel/board.py", "team-kits/kernel/filing.py",
            "team-kits/*/hooks/**", "team-kits/*/settings/**", "team-kits/*/constitution/**",
            "team-kits/*/agents/**", "team-kits/*/skills/**", "team-kits/*/templates/**",
            ".claude/hooks/gate_*.py", ".claude/hooks/_harness.py", ".claude/settings.json", ".claude/agents/**",
        ] + COMMON_FORBIDDEN,
        seams=COMMON_SEAMS + [".claude/hooks/test_gates.py"],
        inputs=[
            "project_memory/product/active/PR-0007.yaml (AC-1..AC-4) and what it absorbed: project_memory/bugs/active/BUG-0069.yaml (CI red on every push; the three failure classes named there; TSK-0088 cancelled in gen 3), BUG-0025.yaml (.gitattributes eol; 33 CRLF files measured in generation 3, cause core.autocrlf=true local and system), BUG-0088.yaml (kit update leaves the agent-memory tree), BUG-0033.yaml (gate-3 timing test red under load, green solo -- five times in generation 3)",
            "DEC-0070 (the (g) notes on BUG-0033 and the CRLF incident), DEC-0056",
            ".github/workflows/** (the hosted runs), .gitattributes, tools/validate.py (the size/eol reader), team-kits/kernel/kitupdate.py, .claude/hooks/test_gates.py::test_gate3_answers_before_its_registration_however_costly_the_line_is_to_judge and its budget derivation, .claude/settings.json timeouts (READ ONLY)",
            "project_memory/staging/TSK-0120/merge-protocol.md section 1 (eol measurement: 35 -> 33 CRLF files, two normalised with byte-equality against HEAD) and the C stream's byte sweep (binaries decided by bytes, 2 071 binaries contain \\r\\n)",
        ],
        outputs=[
            "PR-0007 AC-1 (BUG-0069): the workflow is green on ubuntu and windows, or every red is a named skip with its class (shallow clone history, D: workspace mount, fixture size) -- never a failure the local suite does not reproduce; measured on one real hosted run (the user pushes on request; you prepare and measure locally what you can, and name what only the hosted run shows).",
            "PR-0007 AC-2 (BUG-0025): .gitattributes pins every text class; a shipped test / validate.py refuses a tracked text file with CRLF and names it; the 33 files normalised ONCE, binaries decided by bytes not extension, byte-equality against HEAD as the precondition; core.autocrlf named in the developer docs as the cause, not fixed by this repo.",
            "PR-0007 AC-3 (BUG-0088): update-kit removes the agent-memory tree the previous kit owned or lists it for the user with a sentence; measured on a pilot; red-first.",
            "PR-0007 AC-4 (BUG-0033): the gate-3 timing test measures against a budget DERIVED from the registered timeout with a load-aware margin, or names the load class it is -- no bare assert against a seconds constant; measured under 16 CPU burners and solo.",
            RIGOUR.format(holes="H160 to H162"),
            "Seams: .claude/hooks/test_gates.py shared with G4-1 and G4-2 -- your change is ONE test, named; kitupdate.py is yours and forbidden to G4-2 (say so in the protocol); no constitution sentence expected.",
            HANDOVER.format(name="hygiene"),
        ],
    ),
}


def main():
    for name, spec in STREAMS.items():
        argv = list(KERNEL) + [
            "--product-requirement", spec["pr"], "--derives-from", spec["pr"],
            "--type", spec["type"], "--assigned-role", "harness-implementer",
        ]
        for ac in spec["acs"]:
            argv += ["--acceptance-ref", ac]
        for path in spec["allowed"]:
            argv += ["--allowed-scope", path]
        for path in spec["forbidden"]:
            argv += ["--forbidden-scope", path]
        for path in spec["seams"]:
            argv += ["--seam-scope", path]
        for line in spec["inputs"]:
            argv += ["--required-input", line]
        for line in spec["outputs"]:
            argv += ["--expected-output", line]
        env = dict(os.environ, PYTHONPATH="team-kits")
        print("== stream", name, "(", spec["pr"], ")")
        result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8")
        print(result.stdout.strip()[-400:])
        if result.returncode != 0:
            print(result.stderr.strip()[-1500:])
            print("!! rc", result.returncode, "-- stopping")
            return result.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
