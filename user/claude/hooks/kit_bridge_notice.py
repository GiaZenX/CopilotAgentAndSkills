#!/usr/bin/env python3
"""Global SessionStart notice — the ONE channel a project one release behind still reads (BUG-0059).

WHY IT IS USER-GLOBAL, and the argument is a measurement rather than a preference. A project
installed at `2026.08.14-9` carries that release's hooks, skills and constitution; nothing in this
repo can change what they say, and its SessionStart briefing says, verbatim (measured 2026-08-22
against a real install of that release, rebuilt from this repo's history): "ASK THE USER TO RUN the
scaffold_team script and then init_project_memory … You cannot run either yourself". The only files
of that session a NEW release still owns are the ones in the user's home, which the harness
installer writes — so a hook registered in `~/.claude/settings.json` is the only place a correction
can be put. Everything else the old project reads about the update is its own copy.

WHAT IT SAYS AND WHAT IT MAY NOT: it names the bootstrap (`user/bridge/update_kit.py`, installed as
`~/agents-and-skills/update_kit.py`) and the duty to ask the user first, because that bootstrap
mints no approval. It claims no enforcement: nothing in the old stock can make a PM ask, and this
hook cannot refuse anything — SessionStart hooks inform.

SILENT UNLESS ALL FOUR HOLD, which is what keeps it invisible in every other project on the machine:
the folder is a kit installation (the marker line), a strictly newer release is staged (the KERNEL's
own comparison, `kitupdate.relation`), the project's OWN entry point does NOT carry `update-kit`
(asked of that parser, `bridge.has_the_approved_route`), and the bootstrap is really installed. A
project that HAS the command gets nothing from here: its own briefing offers the approved route.
Measured as a process on both shapes -- silent with the command present, speaking once it is gone,
silent again after the lift -- inside
`tools/test_kitupdate.py::test_a_stock_without_update_kit_is_lifted_by_the_bootstrap_and_told_about_it`.
(That pointer is checked by nobody: the backtick tripwire in `.claude/hooks/test_gates.py` reads the
harness's OWN hooks, not this user-global one, so it is kept honest by hand.)

NOT MEASURED HERE, and named rather than assumed: that the provider merges a USER-GLOBAL SessionStart
hook into a session of a project that registers its own SessionStart hooks, and that this
`additionalContext` reaches the lead there. What IS measured is one project-owned SessionStart hook's
additionalContext arriving verbatim (`tools/provider_observations.json`, `injectable`), and this hook
runs under the same registration mechanism as the global handover guard (DEC-0032). If it never
arrives, the old project keeps exactly the flow its own briefing describes — this adds a route and
removes none.
"""
import json
import os
import re
import sys

# The kit shim's marker, in the ONE position it counts: line 1 of `./CLAUDE.md`. Same structural
# rule the kits' own `session_status.py` applies, and for the reason DEC-0039/BUG-0011 record -- a
# quoted, negated or commented mention is not an installation.
_MARKER_RX = re.compile(r"\s*<!--\s*agents-and-skills:team-kit\s+([\w-]+)\s*-->\s*$")
# Where the harness installer puts the bootstrap this notice points at. One spelling, two readers:
# the installers write it here, this hook reads it back, and if it is absent the notice stays silent
# rather than naming a file nobody would find.
BRIDGE = os.path.join(os.path.expanduser("~"), "agents-and-skills", "update_kit.py")
STAGING = os.path.join(os.path.expanduser("~"), ".claude", "team-kits")


def _kit_of(cwd):
    try:
        with open(os.path.join(cwd, "CLAUDE.md"), encoding="utf-8-sig", errors="ignore") as handle:
            first = handle.readline()
    except OSError:
        return ""
    found = _MARKER_RX.match(first)
    return found.group(1) if found else ""


def _load(path, name):
    import importlib.util                                            # noqa: PLC0415
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def notice(cwd):
    """The paragraph this project needs, or "" -- every condition read off disk, none assumed."""
    kit = _kit_of(cwd)
    if not kit or not os.path.isfile(BRIDGE):
        return ""
    if STAGING not in sys.path:
        sys.path.insert(0, STAGING)
    from kernel import kitupdate                                     # noqa: PLC0415
    bridge = _load(BRIDGE, "agents_and_skills_update_kit_bridge")
    answer = kitupdate.relation(cwd, kit)
    if answer["verdict"] != kitupdate.UPDATE_AVAILABLE:
        return ""
    if bridge.has_the_approved_route(cwd, kitupdate.COMMAND) is not False:
        return ""
    return (
        "KIT UPDATE, AND THIS PROJECT CANNOT REACH THE COMMAND FOR IT (BUG-0059): the staged '%s' "
        "kit is %s, this project runs %s, and its OWN entry point does not carry `%s` -- that "
        "command arrived in a later release, which is why the other briefing you get here tells you "
        "to ASK THE USER TO RUN two shell commands. Do NOT do that: a non-technical user was "
        "measured failing at exactly that step twice (pilot 3 B4, pilot 4 P4-1). A one-time "
        "bootstrap for this ONE lift is installed on this machine and you may run it yourself, from "
        "the project folder:\n"
        "    python \"%s\"\n"
        "FIRST ask the user, in plain words and in their language, whether the update should be "
        "installed now, and run it only if they say yes: this route records no approval, so their "
        "answer in the chat is the whole of the decision. It installs the release the user already "
        "staged and refuses every other direction. AFTERWARDS the update is complete -- run no "
        "installer again, tell the user what changed and ask them to restart the session; the new "
        "hooks, roles and settings bind only at the next start. From that start on this project has "
        "`request-approval %s` + `%s`, which asks and RECORDS the user's answer, and the bootstrap "
        "above refuses to act here at all."
        % (kit, answer["to"].get("version") or "an unreadable version",
           answer["from"].get("version") or "an unreadable version", kitupdate.COMMAND, BRIDGE,
           kitupdate.KIND, kitupdate.COMMAND))


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:                     # noqa: BLE001 -- a notice must never cost a session start
        data = {}
    text = ""
    try:
        if isinstance(data, dict) and str(data.get("hook_event_name") or "") == "SessionStart":
            text = notice(data.get("cwd") or os.getcwd())
    except BaseException:                 # noqa: BLE001 -- same reason: this hook only informs
        text = ""
    if text:
        sys.stdout.write(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart", "additionalContext": text}}))
    sys.exit(0)


if __name__ == "__main__":
    main()
