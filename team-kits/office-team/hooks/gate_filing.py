#!/usr/bin/env python3
"""
PreToolUse(Bash|PowerShell|Edit|Write|MultiEdit) — nothing lands in archive/ that the filing
plan does not have a rule for.

WHAT CHANGED AND WHY. V1 checked filing_log.yaml: after the clerk wrote a `filed:` entry, the gate
asked whether the target existed. Two things ended that. `filing_log.yaml` is now a REGENERATED
scan index (spec II.9) — nobody maintains it, so there is no claim in it left to verify — and
`filing_plan.yaml` became the single machine-readable truth. Which way a project DERIVED its plan
(from prose, or the prose from it) is a decision no gate can see; what the kit derives from the
plan is one artifact, `scripts/process_doc.py` renders it, and the plan's own header names it.

So the gate verifies the same thing one step earlier and against the real truth: the DESTINATION.
A document whose target matches no rule in the plan is not filed at all — spec II.9 is explicit
that it must not be moved, not renamed and not entered anywhere; the clerk asks the user with a
concrete rule proposal instead. Checking before the move is strictly stronger than checking a log
afterwards, because a wrong filing never happens rather than being reported.

WHAT THE GATE SEES, EXACTLY. One predicate ("does this destination match a rule?") behind two
readers. The tool-write reader is complete: every path an Edit/Write/MultiEdit or a Codex patch
creates goes through `_compat.file_paths`. The shell reader is not, and saying otherwise would be
the comment this repo bans. It is `_filing.created`, shared with the guard that watches the other
direction: it reads the syntactic forms in which a shell command NAMES the file it creates — a
redirection target, a flag that names the destination, and a positional destination at the place
that command's calling convention puts it — after lifting wrapper payloads and after following any
working-directory change the same command line performed. It does NOT see a write performed INSIDE
another program: `python -c "shutil.copy(...)"`, `tar -x -C archive/…`, a script that files by
itself. Those are the named residual risk; they are covered by `gate_write_scope` (a shell command
may not smuggle enforcement-relevant writes) and by the fact that filing is a clerk workflow, not a
scripted one. If a project starts filing from a script, the script — not this reader — is where the
rule belongs.

`guard_fs_tripwire` owns the other direction — deletes under inbox/ or archive/, and moves OUT of
archive/ — and deliberately leaves filing INTO the archive open; this gate is what makes that
opening safe. Both ask `_filing` where a token lands, so "inside the archive" means the same thing
on both sides of the wall; it did not before 2026-08-03, and that module's docstring records what
the difference cost.

FAIL-CLOSED, including on an empty plan: with no readable rule there is no truth to file against,
and "no plan yet" is precisely when a mis-filing is cheapest to make and dearest to undo.

WHERE THE PLAN COMES FROM, since the shipped template carries `rules: []` and this gate fails
closed on that — a fresh office project blocks on its FIRST filing. The plan is a kit DOCUMENT
(`kernel.layout.is_project_document`, like `project_config.yaml` and `product/masterplan.md`), not
canonical item state: no kernel path builder can name it, so no kernel command writes it, and
`gate_write_scope` refuses every tool write to it and says exactly that. That leaves ONE session in
a project's life in which it can be written — the global entry gate's, which runs before the kit is
installed; `user/claude/CLAUDE.md` and `user/codex/AGENTS.md` are told to fill it there from the
confirmed onboarding answers, and `tools/test_hooks.py` DERIVES that obligation from this gate
rather than from a list, so a document a gate blocks on can no longer be left out of them.

WHAT THAT DOES NOT FIX, named rather than left to be re-diagnosed as "gate too strict": a project
that was already installed with an empty plan. Nothing inside a session repairs it — the refusal
below is honest about that and points at the user, not at a command. The block itself is correct in
both cases; an unverifiable filing in a business archive is what this gate exists for.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import _kernel
except BaseException as exc:  # noqa: BLE001 — a hook that cannot load must not mean "allow"
    sys.stderr.write("[team-kit hook] refused: could not load hook helpers (%r). Remedy: run "
                     "`python scripts/harness.py doctor`; a partial checkout or half-finished kit update is the "
                     "usual cause.\n" % (exc,))
    sys.exit(2)

import re  # noqa: E402

import _compat  # noqa: E402
import _filing  # noqa: E402

HOOK = "gate_filing"
# Spelled as a literal here, and this is the one duplication in the schema that is deliberate: the
# WALL derivation (`kernel/layout.py`, `path_segments_composed`) follows module-level constants
# into a path composition and cannot follow an imported name, so a gate that got this name from
# `_filing` would stop being a wall for `doctor` and for the SessionStart briefing without any of
# them saying so. It is pinned by measurement rather than by agreement:
# `test_doctor_does_not_invent_a_wall_where_no_gate_stands` walks a real installed office project
# and requires exactly this file to come back as the office wall.
PLAN = "filing_plan.yaml"
# THE SCHEMA, in the two names every reader of the plan needs: the list, and the field that says
# WHERE a rule's documents live. Everything else a rule carries is display material and is rendered
# without being named (see `scripts/process_doc.py`) — which is what keeps a project that adds a
# field to its rules from having to touch code.
RULES = "rules"
PATH_TEMPLATE = "path_template"
# `<name>` inside a path_template. It stands for a non-empty run of characters WITHIN ONE SEGMENT:
# it never spans a `/`, and a segment may mix literals and placeholders. The first version anchored
# the whole segment (`^<...>$`), which is a list of one case wearing a definition's clothes — a real
# Aktenplan node `.../<Modell>_<Prozessor>/` was then read as a literal folder name and every filing
# under it refused, with the node itself sitting in that project's gate events.
PLACEHOLDER_RX = re.compile(r"<[^<>/]+>")
# ONE of the four reasons `rules` can find nothing, named because one caller has to tell it apart
# from the other three. `unfilled_documents` reports the SHIPPED-TEMPLATE state, and a plan that is
# missing, unparseable, or unreadable because PyYAML is absent is not that: those have remedies a
# session can act on, and reporting them as "only the user can fill this" would send a reader away
# from the fix. The gate itself blocks on all four identically — fail-closed does not care why.
NO_RULES_YET = "%s lists no rules yet" % PLAN


def rules(root):
    """The filing plan's rules, or a reason string why there are none to file against.

    THE ONE READER OF THE FILE, and that is the point of it being here rather than in each caller.
    `scripts/process_doc.py` renders the Ablage section of the Verfahrensdokumentation out of this
    same call: measured 2026-08-03, it had its own reader for a `naming_rule:`/`tree:` shape no
    writer produces, so the shipped template rendered as an em dash and an empty list while this
    gate refused every filing against the same file. Two readers of one document, disagreeing
    silently in opposite directions — the renderer follows the gate because the gate is the one
    with a blocking contract, and because what the entry gate and the user are told to WRITE is the
    shape the template's header documents, which is this one.
    """
    path = os.path.join(_kernel.state_dir(root), PLAN)
    if not os.path.isfile(path):
        return None, "%s does not exist" % PLAN
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return None, "PyYAML is not installed for the interpreter running the hooks"
    try:
        with open(path, encoding="utf-8-sig") as fh:
            plan = yaml.safe_load(fh) or {}
    except Exception as exc:  # noqa: BLE001
        return None, "%s could not be parsed (%s)" % (PLAN, exc)
    if not isinstance(plan, dict):
        return None, "%s is not a mapping" % PLAN
    found = [r for r in (plan.get(RULES) or []) if isinstance(r, dict) and r.get(PATH_TEMPLATE)]
    if not found:
        return None, NO_RULES_YET
    return found, None


def unfilled_documents(root):
    """{state-relative path: why} for the kit DOCUMENT this gate refuses ALL filing over.

    The empty-plan branch of `check` below, asked as a question instead of as a refusal -- both go
    through `rules`, so there is one condition and no copy of it. TWO narrowings, and each excludes
    something this gate does block on:

      * a plan WITH rules that simply does not cover today's destination is a filing DECISION, not
        a wall — the plan is written, it just has no rule for this document yet;
      * `NO_RULES_YET` and not "`rules` found nothing". The other three ways it can find nothing (no
        file, unparseable YAML, PyYAML absent) all have a remedy someone can act on, and reporting
        them through a message whose whole point is "only the user can fill this" would point the
        reader away from the fix.

    It is a QUERY and never blocks: `_kernel.block` is called from `check`, on the event that has a
    blocking contract. `_kernel.unfilled_gated_documents` calls this at SessionStart, so an office
    project is told its Aktenplan is empty before the first filing rather than by the refusal of
    it.
    """
    found, reason = rules(root)
    return {} if found or reason != NO_RULES_YET else {PLAN: reason}


def segment_pattern(segment):
    """One path segment of a path_template as a regular expression.

    A `<name>` is translated ANYWHERE in the segment and everything around it stays literal, so
    `<Modell>_<Prozessor>` matches `X250_i5` and `2026-<Monat>` matches `2026-03`. It never crosses
    a `/`: the placeholder is a run of characters inside this segment, which is what makes
    `archive/finance/2026` still fail to match `archive/finance` and `<year>` still refuse to
    swallow `2026/q1`.
    """
    out, last = [], 0
    for match in PLACEHOLDER_RX.finditer(segment):
        out.append(re.escape(segment[last:match.start()]))
        out.append("[^/]+")
        last = match.end()
    out.append(re.escape(segment[last:]))
    return "".join(out)


def rule_matches(path_template, directory):
    """Does `directory` (repo-relative, slash-separated, no trailing slash) match this rule?"""
    parts = [p for p in str(path_template).replace("\\", "/").strip().strip("/").split("/") if p]
    if not parts:
        return False
    return re.match("^" + "/".join(segment_pattern(p) for p in parts) + "$", directory) is not None


def check(root, targets):
    """`targets` is [(path token, bases it may be relative to)] — see `_filing.created`.

    Every base is read and any of them landing in the archive counts. That is the fail-closed
    direction: an over-block asks the clerk to name the rule, a missed reading files the document
    nowhere anyone can find.
    """
    directories = []
    for target, bases in targets:
        for base in bases:
            directory = _filing.archive_directory(root, base, target)
            if directory and directory not in directories:
                directories.append(directory)
    if not directories:
        return  # nothing is landing in the archive

    found, reason = rules(root)
    if found is None:
        _kernel.block(
            HOOK,
            "a document is being filed into %s, but there is no machine-readable filing plan to "
            "file it against: %s. The Aktenplan is the single truth for where a document belongs "
            "(spec II.9); without it a filing cannot be verified, and an unverifiable filing in a "
            "business archive is the failure this gate exists for."
            % ("/, ".join(directories) + "/", reason),
            remedy="propose the missing %s rules to the USER and stop there. The plan is a kit "
                   "document inside the write-locked state directory: no tool write reaches it "
                   "and no kernel command writes it (gate_write_scope refuses it with that "
                   "reason), so it is filled by the entry gate before the kit is installed, or "
                   "by the user in an editor outside this session. Name the rules concretely — "
                   "the fields one carries are stated in the plan's own header — and file "
                   "nothing until the file the user saves has them." % PLAN)
    unmatched = [d for d in directories
                 if not any(rule_matches(r.get(PATH_TEMPLATE), d) for r in found)]
    if unmatched:
        _kernel.block(
            HOOK,
            "no rule in %s covers %s. A document that matches no rule is NOT filed: leave it "
            "where it is, do not rename it, do not enter it anywhere."
            % (PLAN, ", ".join(sorted(unmatched))),
            remedy="ask the user with a CONCRETE proposal — either the existing rule this "
                   "document belongs under, or a new rule for it — and file only after the user "
                   "has saved the amended plan themselves; this session cannot write it (see the "
                   "refusal above for why). Inventing a folder is how an Aktenplan stops "
                   "describing the archive.")


def main():
    # No `hook_event_name` guard: this gate is registered on PreToolUse and nowhere else, so
    # the event is settled by settings.json. Re-checking a field a provider may simply omit
    # would turn the gate into a silent exit 0 -- the failure this whole phase is about.
    data = _kernel.payload(HOOK)
    if data.get("tool_name") not in ("Bash", "PowerShell", "Edit", "Write", "MultiEdit"):
        sys.exit(0)
    cwd = str(data.get("cwd") or "")
    root = _kernel.find_repo_root(cwd)
    bases = _filing.reading_bases(root, cwd)
    if data.get("tool_name") in ("Bash", "PowerShell"):
        command = str((data.get("tool_input") or {}).get("command") or "")
        check(root, _filing.created(command, bases))
    else:
        check(root, [(path, bases) for path in _compat.file_paths(data)])
    sys.exit(0)


if __name__ == "__main__":
    _kernel.run_gate(HOOK, main)
