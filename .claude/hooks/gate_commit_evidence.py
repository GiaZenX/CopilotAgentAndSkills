#!/usr/bin/env python3
"""
Gate 3 (SR-0006): no commit without a verifier's verdict on THIS state.

WHAT IT READS. `_compat.git_invocations` -- the kits' shell reader, not a second regex. It resolves
wrapper payloads (`bash -lc "..."`), here-strings, line continuations and both shells' escapes, and
it reports a verb the text does not fix as UNRESOLVED, which `Invocation.runs` reads as "could be
any git command". A `git $V` line therefore reaches this gate, and the refusal carries the kits'
own `UNRESOLVED_VERB_NOTE` so the remedy ("spell the subcommand literally") is on the same page.

WHAT IT DEMANDS. An active Evidence item with `result: pass` that NAMES the digest of the current
working tree (`_harness.working_tree_digest`). Naming, not describing: the digest is the identity
of the subject, so a verdict recorded on an earlier state stops covering the tree the moment the
tree moves -- which is the whole point, and the reason `python tools/bump_kit_version.py` has to
run BEFORE the verdict is recorded rather than after.

THE LOCK THIS PUTS ON THE DOOR IS REAL, so the way through it is measured rather than asserted. The
refusal below prints the exact `kernel.cli evidence` line with the digest already substituted, and
`test_gate3_remedy_is_executable_and_opens_the_commit` reads that digest OUT of the refusal, runs
the command as printed, and repeats the same call -- so the remedy stops working the moment it is
edited into something unrunnable. A gate whose remedy cannot be executed is worse than no gate.

THE DIGEST IS TAKEN BEFORE THE LINE RUNS, which is all a PreToolUse hook can do -- so a line that
moves the tree and THEN commits was certified against a state that no longer exists when the commit
happens (`echo x >> docs/note.md && git commit -m wip`, measured rc 0 on 2026-08-05 with a valid
verdict recorded). That is closed by asking about the SHAPE of the line rather than about the
future: every command the line does not put AFTER the commit must be read-only, judged by the kits'
own classification -- and what the line puts after a commit it does not wait for is nothing.
`git add -A && git commit` survives it -- staging moves no byte the digest reads, because the
digest is `diff HEAD`, which covers staged and unstaged alike.

WHAT IT DOES NOT COVER, named rather than implied:
  * only `git commit`. A merge that records a commit (`git merge --no-ff`), a `git revert`, a
    `git rebase --continue` and `git am` all write history and are not refused here -- measured
    rc 0. SR-0006 says "kein Commit", and widening a contract silently is the other way to be
    wrong; `docs/POST_V2_WISHLIST.md` H2 carries the chain and the decision.
  * a commit made from a shell OUTSIDE the provider. Hooks gate tool calls, nothing else -- and
    that is the same door every refusal here names as the way to repair a broken gate.
  * a lead that WANTS past it. The refusal prints the command that lifts it, on purpose: this gate
    makes committing without a verdict an explicit, recorded act, not an impossible one.
"""
import os
import sys

# THE IMPORT IS INSIDE THE PROTECTION -- see the same block in `gate_lead_write_scope.py` and the
# measurement in `_harness.py`'s header: a module-level import failure exits 1, and the provider
# reads that as an allow.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import _harness
except BaseException as error:  # noqa: BLE001 -- a gate that cannot load must not mean "allow"
    sys.stderr.write(
        "[harness gate] refused: the shared body of this repo's gates (.claude/hooks/_harness.py) "
        "could not be loaded (%r), so this call could not be judged. A gate that cannot decide "
        "refuses.\nRemedy: repair the file from a shell OUTSIDE Claude Code and start a new "
        "session -- it cannot be repaired from inside this one.\n" % (error,))
    sys.exit(2)


def _moves_the_tree_first(data, command):
    """Does this line change the working tree before the commit is recorded?

    Read as a sequence of commands, with the kits' own reader (`_harness.commands`): the commit is
    located, and everything that is not provably AFTER it must be a command whose verbs cannot
    modify anything and that redirects nothing into a file that retains it. A commit the reader
    cannot LOCATE (a wrapper payload, a verb the text does not fix) leaves the position unknown,
    and unknown is answered by requiring the whole line to be read-only -- the fail-closed
    direction, and the same one `Invocation.runs` takes for an unresolved verb.

    "NOT PROVABLY AFTER" IS WHAT THE ORDER OF THE TEXT CAN SHOW, and it shows nothing behind a
    commit the shell does not WAIT for: `git commit &` hands the commit to a child and goes on, so
    what follows runs while the commit reads the tree. Measured 2026-08-05 through this gate, with
    a valid verdict recorded: `echo more >> docs/note.md & git commit -m wip` rc 0 and
    `sed -i "s/a/b/" docs/note.md & git commit -m wip` rc 0, while the same lines with `;` or `&&`
    in that position were rc 2.

    A PIPE IS NO ORDERING EITHER, and that is the same sentence one level down: the stages of a
    pipeline run BESIDE each other, so a write in the committing pipeline is as unordered against
    the commit as one handed to the background. Measured 2026-08-05 with a valid verdict recorded:
    `sed -i "s/a/b/" docs/note.md | git commit -m wip` rc 0 and
    `(echo more >> docs/note.md)|git commit -m wip` rc 0, while the same writes with `;`, `&&` or
    `&` in that position were rc 2 (`docs/reviews/2026-08-05-tsk0015-measurements.md`, section 4).
    So the committing pipeline is examined too -- every stage of it EXCEPT the one that carries the
    commit.

    A COMMAND A SUBSTITUTION INTRODUCES IS ONE OF THE COMMANDS, and it is one the shell runs BEFORE
    the word it stands in reaches `git`. `_harness.command_line` places it like every other, which
    is what makes a write inside the COMMITTING stage visible at all -- that stage is dropped as a
    whole here, and a substitution is neither its verb nor its redirection. Measured 2026-08-07 with
    a valid verdict in the tree: `git commit -m wip $(sed -i s/prose/POISON/ docs/note.md)` was
    rc 0, the file read `POISON` afterwards and the commit carried it.

    ONLY THE VERB OF A STAGE IS THE COMMIT; ITS REDIRECTION IS THE SHELL. The shell sets a redirect
    up BEFORE it starts the program, so a redirect standing in the committing stage truncates its
    target while the commit is still to come. Measured 2026-08-05 through this gate with a valid
    verdict recorded: `git commit -am wip > docs/note.md` was rc 0, and end to end the file was
    EMPTY afterwards while the commit recorded a tree no verdict had ever seen -- `-am` puts the
    truncated file into the commit. So the committing pipeline is examined for its redirect targets
    as a whole, and only its VERBS are read stage by stage.

    A STAGE WITH NO VERB RUNS NOTHING, so it moves nothing -- the same reading `written_paths`
    already makes one level up. Without it the PowerShell spelling of this repo's own environment
    prefix (`$env:PYTHONPATH="team-kits"; git commit ...`) was refused as a line that changes the
    tree before it commits (measured rc 2, TSK-0008 R-a), and `_harness.stage_body` is here for
    the same reason: a declaration header is not the command.
    """
    module = _harness.shell_reader(data)
    compat = _harness.compat(data)
    sinks = module._null_sinks(data.get("tool_name"))
    read = _harness.command_line(module, compat, data, command)

    def records_a_commit(tokens):
        return any(call.runs("commit")
                   for call in compat.git_invocations(" ".join(str(token) for token in tokens)))

    at = next((index for index, (pipeline, _depth, _child) in enumerate(read)
               if records_a_commit(pipeline)), len(read))
    waited_for = not (at < len(read) and read[at][2])
    for index, (pipeline, _depth, _child) in enumerate(read):
        if index == at:
            stages = [stage for stage in _harness.stages(module, pipeline)
                      if not records_a_commit(stage)]
            # THE WHOLE PIPELINE, INCLUDING THE COMMITTING STAGE -- see "ONLY THE VERB OF A STAGE IS
            # THE COMMIT" in the module docstring.
            targets = module._redirect_targets(pipeline, sinks)
        elif index < at or not waited_for:
            stages = _harness.stages(module, pipeline)
            targets = module._redirect_targets(pipeline, sinks)
        else:
            continue
        bodies = [_harness.stage_body(module, stage) for stage in stages]
        bodies = [body for body in bodies if module._stage_verb(body)]
        if targets or not all(module._stage_is_read_only(body) for body in bodies):
            return " ".join(str(token) for token in pipeline)[:120]
    return ""


def decide():
    data = _harness.payload()
    compat = _harness.compat(data)
    command = str((data.get("tool_input") or {}).get("command") or "")
    if not command.strip():
        # A CALL THIS GATE CANNOT READ IS NOT A CALL IT MAY ALLOW: this gate is registered on the
        # shell tools only, and every shell call carries a command line. One that carries none
        # could not be inspected, which is not the same as "harmless".
        _harness.refuse(
            "this tool call could not be inspected: the payload of a shell tool carries no "
            "command line, so there is nothing to read.\n"
            "Remedy: if this is a legitimate call in a shape the gate does not read, report it -- "
            "the gate refuses rather than guessing, and a guess here is a silent allow.")
    if not any(call.runs("commit") for call in compat.git_invocations(command)):
        return
    moving = _moves_the_tree_first(data, command)
    if moving:
        _harness.refuse(
            "no commit: this line changes the working tree before the commit records it (`%s`).\n"
            "The subject of a verdict is a STATE, and a hook is asked BEFORE the line runs -- so "
            "the digest this gate could check describes the tree as it is NOW, not the tree the "
            "commit would record. A verdict on the first cannot cover the second.\n"
            "A command the shell does not wait for counts as being in front of the commit wherever "
            "it stands, because nothing orders it against one.\n"
            "Remedy: split the call. Run the change, then let the verifier judge the result, then "
            "commit on its own line. `git add` is not a change in this sense and stays allowed: "
            "the digest is the diff to HEAD, which covers staged and unstaged alike." % moving,
            note=compat.unresolved_verb_note(command))
    root = _harness.repo_root(data)
    token = _harness.working_tree_digest(root)
    found = _harness.evidence_naming(root, token)
    if found:
        return
    _harness.refuse(
        "no commit: this working tree carries no passing Evidence.\n"
        "The subject of a verdict is a STATE, and this one is\n"
        "    %s\n"
        "(HEAD, the full diff to the working tree, and every untracked non-ignored file; "
        "`%s/` is excluded, because the record is written into it).\n"
        "No active Evidence item with `result: pass` names that digest.\n"
        "\n"
        "Remedy -- the verifier records its verdict, then the commit is open:\n"
        "    PYTHONPATH=team-kits python -B -m kernel.cli --root %s evidence \\\n"
        "        --kind review --result pass --related <ITEM-ID> \\\n"
        "        --summary \"verifier PASS for %s\" \\\n"
        "        --artifact-ref <path/relative/to/%s>\n"
        "(PowerShell: $env:PYTHONPATH=\"team-kits\"; python -B -m kernel.cli --root %s evidence "
        "...)\n"
        "The digest moves with the package, so run `python tools/bump_kit_version.py` BEFORE "
        "recording the verdict, not after."
        % (token, _harness.STATE_ROOT, _harness.STATE_ROOT, token, _harness.STATE_ROOT,
           _harness.STATE_ROOT),
        note=compat.unresolved_verb_note(command))


if __name__ == "__main__":
    _harness.guarded(decide)
