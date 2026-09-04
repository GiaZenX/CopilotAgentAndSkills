"""Generation 4 cut (DEC-0067): four PRODUCT GOALS, captured through the kernel, one per stream.

The user decided the four on 2026-09-03 ("Ja die vier"); the deferred block (FR-0024 interactive
backlog system, FR-0023, FR-0025, FR-0019, FR-0022, FR-0081, FR-0033) is its own generation and is
NOT in here. Wishes are merged into the goals at triage (FR -> MERGED, resulting_item = the PR;
BUG.related_pr -> the PR) by the lead after this runs. Each goal's acceptance criteria carry the
acceptance line of every wish it absorbs (DEC-0062 (4): every wish keeps its own red test and
acceptance line). Not idempotent -- run once; read the ids it prints.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
KERNEL = [sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory", "capture", "PR"]

GOALS = [
    {
        "title": "G4-1 Test discipline and hook hygiene: a gate on the SCOPE of a test run (this repo + kits), timeouts on every kit hook registration, and the design checks' BUILD half",
        "class": "normal",
        "user_story": "As the lead of this repo and as the PM of a kit project, I want a full-suite run during a round to be REFUSED unless the line says it is the delivery run, every kit hook registration to carry a timeout, and the design checks to reach the built app, so that a round no longer pays hours for runs nobody asked for and no hook is silently killed into an ALLOW.",
        "problem": "Generation 3 measured five unrequested full-suite runs (~5 h) although every order carried the DEC-0050 sentence; the office kit registers eight shell hooks and none carries a timeout (a killed hook is an ALLOW); the design checks of FR-0077 stop at the rendered draft because kit_browser_checks.py is mirrored into research-team (H139). Absorbs FR-0086 (the gate), FR-0057 (the QE measure + timeouts), H139 (the BUILD half of FR-0077).",
        "goal": "During a round a command line that runs the whole declared test surface is refused with the affected-suites sentence unless it carries the delivery prefix; that prefix run is the one recorded as run_scope full (DEC-0061); every hook entry of every kit settings.json names a timeout and _harness.Deadline-style reading refuses an entry without one; the C1-C3 checks run in browser_smoke() of the built app with the mirror kept byte-identical or KIT_SPECIFIC_SCRIPTS naming the reason.",
        "acceptance_criteria": [
            {"id": "AC-1", "text": "FR-0086: Given a scaffolded pilot in a round, When a bare full-suite line is run, Then it is refused with the affected-suites sentence; When the same line carries the delivery prefix, Then it passes and the kernel records run_scope full; When a selection (-k, node id, sub-path) is run, Then it passes; When a second bare full run follows a recorded full run in the same round, Then it is refused unless the previous full run yielded findings (DEC-0063 (4)); measured as processes, red-first; this repo's gate 5 measured in test_gates.py"},
            {"id": "AC-2", "text": "FR-0057: Given the three kits' settings.json, When any hook entry lacks a timeout, Then a shipped test is red and the session-start reader refuses that entry with a sentence; the quality-engineer and implementer skills state the run-scope rule (affected suites in a round, the full run once before delivery) as a procedure, measured against the kit text"},
            {"id": "AC-3", "text": "H139: Given a built app on a scaffolded dev pilot, When kit_browser_checks.py's browser_smoke() runs, Then C1/C2/C3 (axe or its equivalent without npm, keyboard path, reduced motion / focus-visible) are checked and each is red on a planted violation; the research-team mirror stays byte-identical or KIT_SPECIFIC_SCRIPTS names the reason; H139 closed with the test named"},
            {"id": "AC-4", "text": "Cost side per DEC-0056 named per gate: what a project whose suite runs in seconds pays (the threshold is a config value, not a constant), what a project without UI pays for AC-3 (nothing measurable)"},
        ],
        "invariants": [
            "A runner nobody declared is not judged (the declared test command of the project is the property, not a list of runner names)",
            "A killed hook is an ALLOW: every new registration carries a timeout and its deadline is measured",
            "Mirrored files stay byte-identical across kits unless KIT_SPECIFIC_* names the reason",
        ],
        "out_of_scope": [
            "Any narrowing of the archive guard (H125 pipe/link/glob) -- a command-line guard is a DEC-first design round, not a stream (DEC-0070 (2))",
            "BUG-0025 line endings (G4-4)",
        ],
        "priority": "high",
    },
    {
        "title": "G4-2 Kernel contracts: honest evidence for a BUG (BUG-0090), no work order under an inbox item (BUG-0091), SR duty by PR class (FR-0085), holes as typed items (FR-0087), leases for parallel specialists (C-2/C-3)",
        "class": "large",
        "user_story": "As the PM of a kit project and as the lead here, I want every rule that today is discipline (a regression run verifies a bug, a task hangs from a goal, an architect derives SRs for a normal goal, a measured gap is an item, one lease per specialist instance) to be a wire in the kernel, so that a relapse is refused and shown, not remembered.",
        "problem": "Five measured gaps of the same class -- the kernel accepts what the constitution forbids or lets a lie stand: a passing selection-scoped test Evidence does not verify a BUG while the refusal asks for exactly that run (BUG-0090); create-task accepts an FR as product_requirement (BUG-0091, 21 tasks in this repo); the SR step is procedure only (FR-0085); hole-list entries live in a document with hand-reserved numbers (FR-0087, three cut findings in generation 3); a lease cannot carry a worktree and the dispatch does not refuse overlapping scopes (stream D's C-2/C-3).",
        "goal": "Each of the five is a DEC-first contract in backlog_types/state/approvals/dispatch/report with its red test, the kits read the same contract, and the migration of the existing hole list runs once through the kernel with a generated pointer index left in the document.",
        "acceptance_criteria": [
            {"id": "AC-1", "text": "BUG-0090: Given a FIXED BUG and a passing test Evidence that names it and declares run_scope selection, When the BUG is transitioned to VERIFIED, Then the outcome the DEC line chose happens (walks, or the refusal text and evidence --help stop describing a targeted run); the merge gate's reading is unchanged (a passing selection opens no merge); red-first on e45c0ca+"},
            {"id": "AC-2", "text": "BUG-0091: Given an FR, When create-task names it as product_requirement or derives_from, Then it is refused with the triage route (CONVERTED + resulting_item), or the DEC documents why a task under an untriaged wish is allowed and the board labels it as inbox work; existing tasks stay valid; a check over the index counts TSKs whose root is an FR"},
            {"id": "AC-3", "text": "FR-0085: Given a PR of class normal or large with no ACCEPTED SR, When its first TSK is dispatched, Then dispatch (kernel or gate_dispatch) refuses with the architect remedy; a small PR is not asked; measured on a scaffolded pilot, red-first"},
            {"id": "AC-4", "text": "FR-0087: Given the hole list, When the migration runs, Then every H entry is a typed item with its H number kept as a field, ids come from the kernel, the test_gates judges-test and name-resolution test read the items, the merge seam table reads holes from the index, the document carries a generated index that a hand edit invalidates; a user-accepted exception is walkable only through a minted approval; the kits ship the same shape"},
            {"id": "AC-5", "text": "C-2/C-3: Given two READY tasks whose allowed_scope overlaps at file level, When the second is dispatched, Then create_lease refuses with the overlapping path (check-scopes as the predicate); a lease carries the worktree it was granted for; D's tests test_nothing_shipped_refuses_two_tasks_whose_scopes_overlap and test_the_lease_carries_no_tree_of_its_own are rewritten to the new contract and the parallel-streams texts updated in the same stream"},
        ],
        "invariants": [
            "A status the supervised party can set itself is a status no gate reads as approval",
            "One definition per rule: two readers of the same store are one derivation, never two spellings",
            "An EVD is immutable; a duty on new records lives at the surface that records them",
        ],
        "out_of_scope": [
            "The board rendering of holes (kernel/board.py lane) beyond what FR-0087 needs to show open holes",
            "F5 evidence-path normalisation unless it falls out of AC-1",
        ],
        "priority": "high",
    },
    {
        "title": "G4-3 Procedure and retrospective: review as an EVENT in the kits and here (FR-0084), a cut critic before the order (FR-0005), the five malformed order lines in the PM role (FR-0010), and the orchestrator rules of DEC-0070 in the lead role text",
        "class": "normal",
        "user_story": "As the user of a kit project, I want the project to ask 'could this be cheaper or better' at phase ends, merges and repeated findings -- three lines to me, decisions mine -- and every work-order plan to name the way it rejected, so that reflection stops being something only I bring.",
        "problem": "Reflection appeared in generation 2 and 3 only where the procedure demanded a measurement (FR-0084); the cut has no critic and produced eight findings against it in generation 3 (FR-0005, DEC-0070 (1)); order lines in generation 3 were refuted by measurement three times (FR-0010, DEC-0070 rule 5); the lead's own rules (a 'queued' message is no delivery; a command-line guard is a DEC-first round) exist only in a DEC and a logbook.",
        "goal": "The project-auditor role and the harness-lead role ask the four measured questions at the named events and write three lines to the user; a TSK plan without the rejected-alternative line is refused by the plan check; a cut critic presents a SMALLER plan before the order; the PM role text carries the five malformed order-line forms; harness-lead.md carries DEC-0070 rules 1, 2 and 5 (an implementer edits it, gate 1 refuses the lead).",
        "acceptance_criteria": [
            {"id": "AC-1", "text": "FR-0084: Given a phase end, a merge, a repeated finding class or a changed decision premise on a scaffolded pilot, When the auditor run fires, Then the session brief carries the four questions with measured answers and three lines to the user; When a TSK plan lacks the rejected-alternative line, Then the plan check refuses it; measured on a pilot copy, red-first"},
            {"id": "AC-2", "text": "FR-0005: Given an order draft, When the cut critic runs, Then it presents a smaller plan with what it removed and why, and the PM records the choice; measured against the kit text and on a pilot"},
            {"id": "AC-3", "text": "FR-0010: the five malformed order-line forms are in the project-manager role text as a procedure (not adjectives), each with the case that produced it, measured against the kit text"},
            {"id": "AC-4", "text": "DEC-0070 rules 1, 2 and 5 in .claude/agents/harness-lead.md (measured cut before spawn via check-scopes; a command-line guard is a DEC-first design round; a queued SendMessage to a completing agent is not a delivery, silence longer than a verification's wall-clock is a ListAgents check), each pointing at its DEC; test_gates or a tools test reads the role text for the pointers"},
        ],
        "invariants": [
            "Taste stays the user's (FR-0074): no per-item questioning, no 'creativity' instruction in a role text",
            "A role text names the test that holds a property claim, or the claim is not made",
        ],
        "out_of_scope": [
            "Building the review as a kernel type or automaton -- it rides on the auditor run record (FR-0038/TSK-0112)",
        ],
        "priority": "normal",
    },
    {
        "title": "G4-4 Repo hygiene: the hosted CI is green or honest (BUG-0069), line endings pinned and the 33 CRLF files normalised (BUG-0025), kit update leaves no memory residue (BUG-0088), the load-class gate test stops flapping (BUG-0033)",
        "class": "normal",
        "user_story": "As the user who gets an 'All jobs have failed' mail on every push, I want the external signal to mean something again, the checkout to obey .gitattributes, a kit update to leave no stale tree, and the gate suite to be green on a busy host, so that red means red.",
        "problem": "GitHub CI is red on every push while the local delivery suite is green (BUG-0069, TSK-0088 cancelled in generation 3 because its scope team-kits/** overlapped every stream); core.autocrlf=true local and system writes CRLF against .gitattributes -- 33 files in this checkout, one stray write in generation 3 (BUG-0025); a kit update removes the memory: key from a role but leaves the agent-memory tree (BUG-0088); test_gate3_answers_before_its_registration_however_costly_the_line_is_to_judge is red under load and green solo, five times in generation 3 (BUG-0033).",
        "goal": "CI runs the delivery suite the way the local run does or says which classes it cannot (shallow clone, D: workspace, fixture size) as skips with reason; .gitattributes is the authority and a shipped test refuses a CRLF text file in the tree; update-kit removes what the previous kit owned; the timing test measures against a budget derived from the registered timeout with a load-aware margin or is marked as the load class it is.",
        "acceptance_criteria": [
            {"id": "AC-1", "text": "BUG-0069: Given a push to GitHub, When the workflow runs on ubuntu and windows, Then it is green, or every red is a named skip with the reason class (shallow clone history, D: mount, fixture size) -- never a failure the local suite does not reproduce; measured on one real run"},
            {"id": "AC-2", "text": "BUG-0025: Given the checkout, When tools/validate.py or a shipped test runs, Then a tracked text file with CRLF is refused with the file named; the 33 files are normalised once (binaries decided by bytes, not by extension); .gitattributes pins every text class"},
            {"id": "AC-3", "text": "BUG-0088: Given a kit update that drops a role's memory: key, When update-kit runs, Then the agent-memory tree the previous kit owned is removed or listed for the user with the sentence; measured on a pilot"},
            {"id": "AC-4", "text": "BUG-0033: Given the gate suite under parallel load, When the gate-3 timing test runs, Then it is green or names the load class with a measured margin against the registered timeout -- not a bare assert against a constant seconds value; measured under 16 CPU burners"},
        ],
        "invariants": [
            "A number lives in one place: the timing budget derives from the registration, never a second constant",
            "Nothing in this goal changes a kit hook's behaviour -- G4-1 owns hooks and registrations",
        ],
        "out_of_scope": [
            "Repo layout changes beyond .gitattributes and .github",
        ],
        "priority": "normal",
    },
]


def main():
    env = dict(os.environ, PYTHONPATH="team-kits")
    for goal in GOALS:
        result = subprocess.run(KERNEL, input=json.dumps(goal), cwd=ROOT, env=env,
                                capture_output=True, text=True, encoding="utf-8")
        print(goal["title"][:40], "->", (result.stdout.strip() or result.stderr.strip())[-300:])
        if result.returncode != 0:
            return result.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
