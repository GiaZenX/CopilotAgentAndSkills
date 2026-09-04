"""Generation 3 cut (DEC-0062): five stream work orders, created through the kernel.

Why a script and not five shell lines: the orders are long prose, and a shell line of that length
broke on quoting twice (2026-09-03). This calls the same sanctioned route -- `kernel.cli
create-task` -- with argument LISTS, so nothing is re-quoted. The lead ran it once; the created
items are the authority, this file is the record of what was asked. Re-running it would create
five more tasks, so it is not idempotent by design: read the ids it printed instead.

Common lines every stream carries (DEC-0063 (5), the handover prompt of TSK-0114):
measure every new property claim before handover; hole-list citations with module prefix; scratch
only under _round-scratch/<TSK>/; worktree copies for the verifier WITHOUT the .git file; streams
run only their DEC-0050 affected suites (full suite = merge round); VERSION stamp provisional;
forbidden_scope project_memory/** EXCEPTS project_memory/staging/<TSK>/.
"""
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
KERNEL = [sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory", "create-task"]

COMMON_FORBIDDEN = [
    "scaffold_team.*", "install.*", "init_project_memory.*", "team-kits/gen_provider_artifacts.py",
    "user/**", "CLAUDE.md", ".claude/**", "project_memory/**",
]

HANDOVER = (
    "Handover: worktree C:/Offline Repos/v2-testbed/_worktrees/g3-{name} (branch g3/{name} off "
    "feat/harness-v2 at e45c0ca); ALL scratch only under C:/Offline Repos/v2-testbed/_round-scratch/"
    "(this task id)/; verifier copies made WITHOUT the .git file of the worktree; patch = the worktree "
    "diff at C:/Offline Repos/v2-testbed/_round-scratch/(this task id)/stream-{name}.patch; protocol "
    "at project_memory/staging/(this task id)/stream-protocol.md with: seam table, per-FR acceptance "
    "line + red-first tests, measured lines, what was deliberately not closed but named, the one-line "
    "rejected alternative of the plan (FR-0084 shape), suite runs (affected suites only -- the full "
    "suite belongs to the merge round), provisional VERSION stamp, wall-clock and tokens for the (g) "
    "table. No commit, no push, no install to the global store."
)

RIGOUR = (
    "Per FR its own red-first test measured in a copy outside the repo (restore the defect, see red, "
    "put it back) and its own acceptance line in the protocol; the verifier reports PER FR "
    "(DEC-0062 (4)). Every new property claim -- code comment, docstring, docs, hole list -- is "
    "MEASURED before handover (the most frequent finding of generation 2); every hole-list citation "
    "carries its module prefix; hole numbers {holes} ONLY; forbidden_scope project_memory/** excepts "
    "project_memory/staging/(this task id)/."
)

STREAMS = {
    # ---------------------------------------------------------------- A  Board & Plan
    "board": dict(
        pr="FR-0075", type="ui",
        allowed=[
            "team-kits/dev-team/templates/repo/scripts/generate_dashboard.py",
            "team-kits/dev-team/templates/repo/scripts/progress.dashboard.template.html",
            "team-kits/kernel/board.py", "team-kits/kernel/backlog_tree.py",
            "team-kits/kernel/plan_diagram.py",
            "team-kits/*/VERSION", "tools/**", "docs/**",
        ],
        forbidden=[
            "team-kits/kernel/backlog_types.py", "team-kits/kernel/cli.py", "team-kits/kernel/state.py",
            "team-kits/kernel/approvals.py", "team-kits/kernel/documents.py", "team-kits/kernel/report.py",
            "team-kits/kernel/filing.py", "team-kits/kernel/dispatch.py",
            "team-kits/dev-team/templates/repo/scripts/kit_*.py",
            "team-kits/*/constitution/**", "team-kits/*/agents/**", "team-kits/*/skills/**",
            "team-kits/*/hooks/**", "team-kits/*/settings/**",
            "team-kits/office-team/templates/**", "team-kits/research-team/templates/**",
        ] + COMMON_FORBIDDEN,
        inputs=[
            "project_memory/inbox/active/FR-0075.yaml (primary)",
            "project_memory/inbox/active/FR-0079.yaml",
            "project_memory/inbox/active/FR-0080.yaml",
            "project_memory/decisions/active/DEC-0062.yaml (cut rule: grouped FRs, per-FR red test, seams named up front) and DEC-0063.yaml (generation-2 verdict: measure every new property claim before handover; Fable = design pass only, Opus builds)",
            "docs/POST_V2_WISHLIST.md sections 2 and 3 (what FR-0079/FR-0080 point to) and the hole-list tail (H125 is the last number taken)",
            "project_memory/staging/TSK-0109/ (README, 01 to 04, user-feedback.md, review/): the finance-dashboard design pass and sighting loop this stream repeats for the backlog board",
            "team-kits/dev-team/skills/frontend-design/SKILL.md and team-kits/dev-team/skills/webapp-testing/SKILL.md",
            "docs/research/2026-07-27-plan-als-diagramm.md (FR-0080: generated, not maintained -- already answered there)",
            "team-kits/kernel/board.py, team-kits/kernel/backlog_tree.py, team-kits/dev-team/templates/repo/scripts/generate_dashboard.py + progress.dashboard.template.html, project_memory/generated/index.yaml (the existing data contract; no new writer)",
        ],
        outputs=[
            "TWO-STEP (FR-0075, the shape of TSK-0109): phase 1 = a DESIGN PASS (Fable, frontend-design skill) against the brief in FR-0075 -- who reads the board, what they look for first (blocked / waiting on the user / in flight), states empty project, healthy, blocked -- sighted per the BUG-0076 doctrine (Playwright, 1280 + 390 px, dark, every tab and filter), recorded under project_memory/staging/(this task id)/; the pass MEASURES whether kernel/board.py and the dev-team HTML board ever disagree on the same numbers and recommends one renderer with two outputs or two renderers, with reason; it names in one line the alternative brief it rejected and why. Phase 1 ends with a report to the lead. Phase 2 (Opus, second spawn) builds on the existing generator with the existing data contract (generated/index.yaml + rollups): no new writer, no new field unless the design pass measured a missing one and reports it as a seam; kept from FR-0030: refresh trigger, kit ownership, one-file property.",
            "FR-0079 (MST): phase 1 recommends TYPE or FIELD with the kernel consequences spelled out (backlog_types AUTOMATA / ACTIVE_DIRS / REQUIRED_FIELDS, index, board timeline); the DEC is the USER decision, captured by the lead before phase 2 starts. If TYPE: phase 2 renders MST on the board timeline from a fixture, and the type-definition lines for backlog_types.py are a SEAM to stream C (verbatim in the protocol with the test each needs; the lead hands them to C during the round; applied in C or in the merge, never here). If FIELD: the field is rendered and the DEC named beside it. Either way FR-0079 keeps its own red-first test and acceptance line.",
            "FR-0080: implementation plan and mindmap generated from the items (index / rollups) as .drawio.svg, regenerated by the SAME trigger as the board (the one call site that regenerates the board; if that site is in a file this stream does not own -- kernel/cli.py is C-owned -- the one call line is a seam, verbatim); a hand edit of a generated diagram is detected by a test; nothing is hand-maintained. If a module of its own is needed it is team-kits/kernel/plan_diagram.py and nothing else in the kernel.",
            RIGOUR.format(holes="H126 to H128"),
            "Seams reported, never written here: constitution / role / skill sentences the new board or diagrams need -> stream D (verbatim in the protocol); kernel type or trigger lines -> stream C; tools/test_hooks.py mirror-dir tests (shared with stream B: files derived from templates/repo dirs shipping *.py); docs/POST_V2_WISHLIST.md appended only under the reserved numbers.",
            HANDOVER.format(name="board"),
        ],
    ),
    # ---------------------------------------------------------------- B  Buero-Finanzen
    "office": dict(
        pr="FR-0076", type="implementation",
        allowed=[
            "team-kits/office-team/templates/project_memory/**",
            "team-kits/office-team/templates/repo/**",
            "team-kits/office-team/hooks/guard_fs_tripwire.py",
            "team-kits/kernel/filing.py",
            "team-kits/*/VERSION", "tools/**", "docs/**",
        ],
        forbidden=[
            "team-kits/kernel/approvals.py", "team-kits/kernel/backlog_types.py", "team-kits/kernel/cli.py",
            "team-kits/kernel/state.py", "team-kits/kernel/documents.py", "team-kits/kernel/report.py",
            "team-kits/kernel/board.py", "team-kits/kernel/backlog_tree.py", "team-kits/kernel/dispatch.py",
            "team-kits/office-team/hooks/_*.py", "team-kits/office-team/hooks/gate_*.py",
            "team-kits/office-team/hooks/session_status.py",
            "team-kits/dev-team/**", "team-kits/research-team/**",
            "team-kits/*/constitution/**", "team-kits/*/agents/**", "team-kits/*/skills/**",
            "team-kits/*/settings/**",
        ] + COMMON_FORBIDDEN,
        inputs=[
            "project_memory/inbox/active/FR-0076.yaml (primary; FR-0081 SKR03/04 is deliberately NOT in this stream)",
            "docs/POST_V2_WISHLIST.md entries H125 (the archive-guard delete rule is a verb tuple; chain measured against all eight registered office shell hooks) and H123 (the flag form); plus C:/Offline Repos/v2-testbed/_round-scratch/TSK-0114/probe_h125.py if still present (the six probe lines)",
            "project_memory/staging/generation-2-streams.md (entries of streams G and I) and project_memory/staging/TSK-0107/, TSK-0113/, TSK-0109/user-feedback.md: the office seams left open -- kleinunternehmer: null shipped + the tax-status interview question as template comment (wording verbatim in the G protocol), founding_year judged not added for lack of a reader, tax_state three cases, F6 = the kernel does not validate retention of the filing plan",
            "project_memory/decisions/active/DEC-0056.yaml (gates guard against ERROR not INTENT; the irreversibility exception H125 invokes), DEC-0053.yaml (P4-12 empty vocabulary, BUG-0071), DEC-0062.yaml, DEC-0063.yaml",
            "team-kits/office-team/templates/project_memory/master_data.yaml + business_profile.yaml + filing_plan.yaml; templates/repo/scripts/euer_report.py; templates/repo/tools/finance_dashboard.py + template; hooks/guard_fs_tripwire.py; kernel/filing.py; the office settings registration (READ-ONLY: which eight shell hooks run and with which timeout)",
            "The ONLY kernel file this stream may write is kernel/filing.py -- every other kernel line is a seam to stream C.",
        ],
        outputs=[
            "FR-0076 (1): a SHIPPED default category vocabulary in the master_data.yaml template (Wareneinkauf, Buerobedarf, Bewirtung, Porto, Software/Hosting, Werbung, Reisekosten, Telefon/Internet, Versicherungen, Beitraege/Gebuehren, Fremdleistungen, Miete, and the income lines) where each category carries the LINE NUMBER of the current official Anlage EUeR; the form year is a property of the vocabulary, not of the code; the user can rename or add; the P4-12 empty-vocabulary stall cannot recur on a fresh project (test). (2): euer_report.py sums per form line IN ADDITION to per category, and the finance-dashboard EUeR tab shows the per-line sums (parity test report vs page). (3): AfA as a HINT only -- a booking whose net exceeds the GWG limit (a profile/vocabulary value, not a constant) is flagged 'Anlagegut -- mit der Steuerberatung klaeren'; no asset register, no depreciation arithmetic; nothing for a GmbH; the legal caveat stays on every page.",
            "Office seams of generation 2 CLOSED here: kleinunternehmer: null shipped with the tax-status interview question as the template comment (verbatim from the G protocol) so a fresh project starts 'unknown' until asked; founding_year added ONLY together with a reader that needs it (else the protocol repeats the measured reason it stays out); the three tax_state cases stay as stream I built them; F6: the kernel VALIDATES the retention values of the filing plan in kernel/filing.py so the deadline register can no longer meet a rule it cannot parse in silence -- if the validate entry point that must call it lives in kernel/report.py, that ONE call line is a seam to stream C, verbatim in the protocol.",
            "H125 CLOSED: guard_fs_tripwire.DELETE_VERBS replaced by a PROPERTY ('this line removes or empties a file under a ranked tray') instead of a verb tuple; measured as PROCESSES against all eight registered office shell hooks on a scaffolded pilot outside the repo: unlink, git clean -fdx with and without a path, Clear-Content, find -delete -> rc 2; the two controls (rm, move out of archive) still rc 2; the over-refusal weighed and measured (git clean in a project WITHOUT an archive must not fail; a delete outside every ranked tray stays rc 0); the hook deadline measured against its registered timeout; DEC-0056 named (irreversible -> the exception applies); the H125 entry moves to closed with its test named with module prefix; H123 re-read and corrected if the property now covers the flag form too (say which).",
            RIGOUR.format(holes="H129 to H131"),
            "Seams reported, never written here: sentences for the office constitution, office-manager, bookkeeper or filing-reviewer skills -> stream D (verbatim in the protocol); tools/test_hooks.py mirror-dir tests shared with stream A; the entry-interview sentence (user/CLAUDE.md, forbidden) reported to the lead; any kernel line outside filing.py -> stream C.",
            HANDOVER.format(name="office"),
        ],
    ),
    # ---------------------------------------------------------------- C  Freigaben & Beweismittel
    "approvals": dict(
        pr="FR-0074", type="implementation",
        allowed=[
            "team-kits/kernel/**",
            "team-kits/*/hooks/gate_approval.py", "team-kits/*/hooks/gate_git.py",
            "team-kits/*/VERSION", "tools/**", "docs/**",
        ],
        forbidden=[
            "team-kits/kernel/board.py", "team-kits/kernel/backlog_tree.py", "team-kits/kernel/plan_diagram.py",
            "team-kits/kernel/filing.py",
            "team-kits/*/hooks/_*.py", "team-kits/*/hooks/gate_dispatch.py", "team-kits/*/hooks/gate_write_scope.py",
            "team-kits/*/hooks/gate_design_*.py", "team-kits/*/hooks/guard_*.py", "team-kits/*/hooks/session_status.py",
            "team-kits/*/constitution/**", "team-kits/*/agents/**", "team-kits/*/skills/**",
            "team-kits/*/templates/**", "team-kits/*/settings/**",
        ] + COMMON_FORBIDDEN,
        inputs=[
            "project_memory/inbox/active/FR-0074.yaml (primary: plan-level approval + autonomous work-through)",
            "project_memory/inbox/active/FR-0082.yaml (EVIDENCE_RESULTS += blocked)",
            "project_memory/inbox/active/FR-0083.yaml (approval via the Claude Agent SDK canUseTool with readable provenance)",
            "project_memory/bugs/active/BUG-0089.yaml (frozen-field remedy names an edge AUTOMATA does not have)",
            "project_memory/decisions/active/DEC-0034.yaml (escalation ladder, untouched), DEC-0056.yaml (cost side of every gate decision), DEC-0061.yaml (EVD run scope, the neighbour of FR-0082), DEC-0062.yaml, DEC-0063.yaml",
            "docs/POST_V2_WISHLIST.md sections 7 and 10 and the H80 chain (the refuted 'headless unreachable' premise FR-0083 must not inherit)",
            "team-kits/kernel/approvals.py, backlog_types.py (AUTOMATA, APPROVAL_TRANSITIONS, EVIDENCE_RESULTS), state.py, cli.py, report.py; team-kits/dev-team/hooks/gate_approval.py and gate_git.py (mirrored x3 -- byte-identical or a KIT_SPECIFIC_HOOKS reason)",
            "project_memory/staging/TSK-0106/dec-run-scope.json -- the shape of a DEC proposal a stream hands the lead (the user decides, the kernel captures)",
            "The hook files this stream may write are gate_approval.py and gate_git.py in all three kits; every other hook line (incl. _kernel.py, gate_dispatch.py) is a seam. The kernel files owned by A (board.py, backlog_tree.py, plan_diagram.py) and B (filing.py) are forbidden.",
        ],
        outputs=[
            "FR-0074, DEC FIRST: a DEC proposal at project_memory/staging/(this task id)/dec-plan-approval.json in the shape of TSK-0106/dec-run-scope.json -- the lead captures it, the USER decides; the build follows the decided shape: an approval KIND at plan level covering the confirmed product-goal list (hash over the list and each goal's criteria), after which per-goal scope questions are not asked; what REMAINS a question is a PROPERTY (irreversible or taste-bound: merge/push, design choices, money, anything the plan did not settle), not a list; the delivery side stays per goal (verdicts, evidence, merge gates); a goal the team cannot do as planned comes back as a question, not an improvisation; the widened control hole is measured and named (hole list or DEC consequence). Constitution and PM-skill sentences (planning phase thorough by design, own proposals, the remaining-questions property) are a SEAM to stream D, verbatim in the protocol.",
            "FR-0082: EVIDENCE_RESULTS gains 'blocked'; gate_git closes on it like on 'fail'; the recorded sentence says WHAT blocked and that nothing was checked; a blocked evidence without that sentence is refused by the kernel; the merge reads it (report.py); red-first on kernel and on gate_git as a process.",
            "FR-0083: an approval minted through the Agent SDK canUseTool carries a PROVENANCE the kernel reads and prints on the approval card; a gate that requires a human-minted token refuses the programmatic one with a sentence; measured against gate_approval.py as a process on a pilot outside the repo; the H80 correction (headless is reachable) is what this builds on, not the refuted premise; red-first.",
            "BUG-0089: the frozen-field refusal derives its remedy from AUTOMATA (the edges that exist from the current state) -- or a READY -> DRAFT edge is added with its index/brief consequences (returned item = re-planned, not new); the test plants a state whose automaton has no DRAFT edge and asserts the remedy does not name DRAFT; red-first.",
            "MST seam from stream A (FR-0079): if the user's DEC says TYPE, the type-definition lines arrive from A through the lead during the round and this stream applies them in backlog_types.py (automaton, ACTIVE_DIRS, REQUIRED_FIELDS, index) with a test; if FIELD, or no DEC before this stream's handover, nothing is done and the protocol says so. Leases/dispatch requirements from stream D (FR-0021) are RECEIVED the same way: built only if D delivers a concrete requirement with its test through the lead; else listed as not built.",
            RIGOUR.format(holes="H132 to H134"),
            HANDOVER.format(name="approvals"),
        ],
    ),
    # ---------------------------------------------------------------- D  Parallele Spezialisten
    "parallel": dict(
        pr="FR-0021", type="implementation",
        allowed=[
            "team-kits/*/constitution/**",
            "team-kits/*/skills/project-manager/**", "team-kits/office-team/skills/office-manager/**",
            "team-kits/dev-team/skills/parallel-streams/**",
            "team-kits/*/agents/project-manager.md", "team-kits/*/agents/project-auditor.md",
            "team-kits/*/VERSION", "tools/**", "docs/**",
        ],
        forbidden=[
            "team-kits/kernel/**", "team-kits/*/hooks/**", "team-kits/*/templates/**", "team-kits/*/settings/**",
            "team-kits/dev-team/skills/frontend-design/**", "team-kits/dev-team/skills/product-designer/**",
            "team-kits/dev-team/skills/webapp-testing/**", "team-kits/*/skills/humanizer/**",
        ] + COMMON_FORBIDDEN,
        inputs=[
            "project_memory/inbox/active/FR-0021.yaml (primary; FR-0084 review-as-event is NOT in this stream -- user decision 2026-09-03, generation 4)",
            "project_memory/decisions/active/DEC-0057.yaml, DEC-0060.yaml, DEC-0062.yaml, DEC-0063.yaml, DEC-0059.yaml -- the MEASURED mechanics this stream ports into the kits: worktree per stream, allowed_scope = ownership and disjoint at file level, grouped requirements, cap by one round's attention, seams named at cut time, merge round as its own verification, one release, tiers",
            "project_memory/staging/generation-2-streams.md and project_memory/staging/TSK-0114/merge-protocol.md (the seam table, the (g) table, the six merge-only findings, and section 8: the project-auditor description-vs-body residue N2)",
            "project_memory/inbox/active/FR-0022.yaml (human names for instances -- referenced, not built)",
            "team-kits/dev-team/constitution/AGENTS.md, team-kits/*/skills/project-manager/SKILL.md, team-kits/*/agents/project-auditor.md (x3); READ-ONLY: team-kits/kernel/dispatch.py + team-kits/dev-team/hooks/gate_dispatch.py + gate_write_scope.py (what a lease carries today and how allowed_scope is enforced per task -- the property the procedure builds on)",
            "tools/test_constitution*.py / the agent-text tests of stream E gen 2 (the lead-in rule: a section in >= 2 constitutions is in all three or listed with reason)",
        ],
        outputs=[
            "FR-0021: the PM procedure for PARALLEL specialists in the dev kit, derived from DEC-0057/0060/0062/0063 and written as (a) a procedure skill team-kits/dev-team/skills/parallel-streams/, (b) a constitution section, (c) the project-manager skill lines -- cut by file ownership, group requirements that share files, cap by one round's attention, allowed_scope per TSK disjoint at file level and CHECKED before dispatch, one worktree per stream, streams run affected suites only, the merge round is a verification of its own with a seam table, one release. What the kernel or hooks must carry for it (a lease per instance and role, the worktree path on the lease, the seam table as an item field, a dispatch refusal on overlapping scopes) is a SEAM to stream C: listed as concrete requirements, verbatim, each with the test it needs -- nothing built in kernel or hooks here.",
            "DEC-0062 (6) as kit text, MEASURED on a pilot copy: the procedure's own pre-dispatch check (a documented command over the kernel index, or a script under tools/ if the check needs code) refuses two tasks whose allowed_scope overlaps at file level -- red-first; where the refusal must be a hook, that is the seam to C and the protocol says which half is text and which half waits.",
            "The section appears in all three constitutions or the reason is listed (the lead-in rule of gen-2 stream E, measured by the existing constitution tests); sentences OTHER streams owe (A, B, C, E) are NOT written here -- they arrive in the merge; the protocol carries a table 'seam sentences received at cut time: none; expected at merge: from B, C, E'.",
            "N2 closed: the description line of the three project-auditor.md agents made consistent with their body sentence (merge-protocol section 8 residue), measured by the existing agent-text test; if that test cannot see the mismatch, it gains the case red-first.",
            RIGOUR.format(holes="H135 to H137"),
            HANDOVER.format(name="parallel"),
        ],
    ),
    # ---------------------------------------------------------------- E  Design-Gates
    "design": dict(
        pr="FR-0077", type="implementation",
        allowed=[
            "team-kits/dev-team/hooks/gate_design_*.py", "team-kits/dev-team/hooks/ENFORCEMENT.md",
            "team-kits/dev-team/settings/settings.json",
            "team-kits/dev-team/templates/repo/scripts/kit_design_render.py",
            "team-kits/dev-team/templates/repo/scripts/kit_design_system_check.py",
            "team-kits/dev-team/templates/repo/scripts/kit_browser_checks.py",
            "team-kits/dev-team/skills/frontend-design/**", "team-kits/dev-team/skills/product-designer/**",
            "team-kits/dev-team/skills/webapp-testing/**",
            "team-kits/*/VERSION", "tools/**", "docs/**",
        ],
        forbidden=[
            "team-kits/kernel/**",
            "team-kits/dev-team/hooks/_*.py", "team-kits/dev-team/hooks/gate_approval.py", "team-kits/dev-team/hooks/gate_git.py",
            "team-kits/dev-team/hooks/gate_dispatch.py", "team-kits/dev-team/hooks/gate_write_scope.py",
            "team-kits/dev-team/hooks/guard_*.py", "team-kits/dev-team/hooks/session_status.py",
            "team-kits/dev-team/templates/repo/scripts/generate_dashboard.py",
            "team-kits/dev-team/templates/repo/scripts/progress.dashboard.template.html",
            "team-kits/*/constitution/**", "team-kits/*/agents/**",
            "team-kits/dev-team/skills/project-manager/**", "team-kits/*/skills/humanizer/**",
            "team-kits/office-team/**", "team-kits/research-team/**",
        ] + COMMON_FORBIDDEN,
        inputs=[
            "project_memory/inbox/active/FR-0077.yaml (primary: the mechanically checkable halves of the standard hardening)",
            "project_memory/inbox/active/FR-0078.yaml (a gate on exactly ONE primary goal per view + the SKILL line with a procedure instead of an adjective)",
            "docs/POST_V2_WISHLIST.md sections 1, 1a and 1c",
            "team-kits/dev-team/skills/frontend-design/SKILL.md, product-designer/SKILL.md, webapp-testing/SKILL.md; hooks/gate_design_sighted.py and its tests in tools/; templates/repo/scripts/kit_design_render.py, kit_design_system_check.py, kit_browser_checks.py; team-kits/dev-team/settings/settings.json (every entry carries a timeout; FR-0057 is generation 4 -- this stream only keeps its own new entries honest)",
            "project_memory/bugs/active/BUG-0076.yaml (the sighting doctrine) and project_memory/staging/TSK-0109/review/ (the sighting loop as it ran)",
            "project_memory/decisions/active/DEC-0056.yaml (the cost side of every gate: what a project without a UI pays must be measurable and near zero), DEC-0062.yaml, DEC-0063.yaml",
            "The office and research kits are NOT touched: design gates are dev-team specific (KIT_SPECIFIC_HOOKS reason if a mirror test asks).",
        ],
        outputs=[
            "FR-0077: the mechanically checkable halves as tests/gates in the dev-team kit -- C1/C2/C3 axe run, keyboard path, prefers-reduced-motion + :focus-visible presence; B2/B3 colour literals outside the token sheet -- each RED on a planted violation (red-first) and run as the shipped script or hook on a scaffolded project outside the repo; every new hook registration carries a timeout and its deadline is measured; the wishlist section 1c points here.",
            "FR-0078: a gate or design-review check that refuses a view whose brief names no or more than one primary goal, with a sentence; the product-designer / frontend-design SKILL line states the PROCEDURE (how the goal is chosen and shown) instead of an adjective, measured against the kit text; a planted view with two primary goals is refused; red-first.",
            "Cost side per DEC-0056 named per gate: what the over-refusal is, what a project without a UI pays (measured, not asserted), and the deadline of every new hook against its registered timeout.",
            RIGOUR.format(holes="H138 to H140"),
            "Seams reported, never written here: constitution / PM-skill sentences that must name the new gates -> stream D (verbatim in the protocol); ENFORCEMENT.md is E-owned and updated for the new gates; nothing in kernel or in the other kits.",
            HANDOVER.format(name="design"),
        ],
    ),
}


def main():
    for name, spec in STREAMS.items():
        argv = list(KERNEL) + [
            "--product-requirement", spec["pr"], "--derives-from", spec["pr"],
            "--type", spec["type"], "--assigned-role", "harness-implementer", "--acceptance-ref", "AC-1",
        ]
        for path in spec["allowed"]:
            argv += ["--allowed-scope", path]
        for path in spec["forbidden"]:
            argv += ["--forbidden-scope", path]
        for line in spec["inputs"]:
            argv += ["--required-input", line]
        for line in spec["outputs"]:
            argv += ["--expected-output", line]
        env = dict(os.environ, PYTHONPATH="team-kits")
        print("== stream", name, "(", spec["pr"], ")")
        result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8")
        print(result.stdout.strip()[-600:])
        if result.returncode != 0:
            print(result.stderr.strip()[-1500:])
            print("!! rc", result.returncode, "-- stopping; earlier streams are created, later ones are not")
            return result.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
