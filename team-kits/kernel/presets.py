"""Changing the team preset of an INSTALLED project -- the half that had no walkable route.

THE DEAD END THIS EXISTS TO END (BUG-0041, pilot 3 finding B4). A preset decides which specialist
roles a project has installed, and after the scaffold ran there was no way to change it from
inside a session: `gate_write_scope` refuses every tool write under the state directory, so
`project_config.yaml` had no writer, and it refuses every write-capable command line naming
`.claude` or `team-kits`, so the scaffold could only be started by a human. The lead's only
remaining move was to send the USER to a text editor and a terminal -- and the user pilot 3
measured is a person who has neither, so the reported gap landed with the one party unable to
close it. `docs/pilot/2026-08-14-pilot-3-rechnungswerkzeug.md` carries the chain.

WHY THE KERNEL AND NOT A WIDER GATE. The refusals above are right: a session that may write
`.claude` may rewrite the gates that judge it. What was missing is a route that changes the role
set WITHOUT handing the session that permission -- so the kernel does it, on the user's minted
approval, the same way it is the one writer of canonical state.

WHY IT RUNS THE KIT'S OWN INSTALLER instead of copying role files itself. Installing a role is not
`cp agents/x.md`: it is the ownership manifest, the backup, the rollback, the symlink pre-flight,
the tier-alias rewrite, the model/effort re-stamp from `project_config.yaml`, the provider artifact
regeneration for Codex and the trust record. `scaffold_team.{ps1,sh}` is that, and a second
implementation here would be a second answer to "which roles are installed" -- the shape this
harness has been burned by often enough that `KIT_SPECIFIC_HOOKS` exists to name the exceptions.

WHAT THAT INSTALLER MAY NOT BE USED FOR HERE, and it is a refusal rather than a caveat: a scaffold
run also re-copies hooks, kernel and constitution from the staging, so against a NEWER staging it
would be a kit update wearing a preset change's clothes -- a user who approved "add the designer"
would get a new enforcement bundle. `assert_installable` refuses unless the staged kit still
declares the RECORDED KIT IDENTITY -- it compares the two VERSION files, which is the kit's own
statement about which release it is, and nothing more
(`test_a_preset_change_refuses_to_smuggle_in_a_kit_update`). That the staged TREE really is that
release is the installer's half of the check and not this one's: `write_kit_state.py` re-hashes the
kit it installed from and fails the run, which rolls it back (measured by the verifier with a
smuggled file and an untouched VERSION -- the scaffold caught it, this comparison did not).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys

import yaml

from . import approvals
from .state import ProjectState, StateError

# The APR kind that authorises this operation. One name, three readers: the vocabulary, the
# manifest builder and the refusal below.
KIND = "preset"
COMMAND = "set-preset"

# THE ONE PART OF A KIT DOCUMENT A KERNEL COMMAND WRITES, declared where the writing happens.
# `kernel.layout.partial_writers` hands it to the write-scope gate, whose refusal for a kit
# document said in every kit that NO `harness.py` command writes such a file -- true until this
# module, and a refusal that denies a route the harness has is how a role learns to stop reading
# them. A second field or a second document is one entry here and no edit anywhere else.
DOCUMENT_WRITES = ({"document": "project_config.yaml", "field": "project.preset",
                    "command": COMMAND},)

# The scaffold's own ownership record, and the ONE file this module reads the installation off:
# it names the kit (`team=`) and lists exactly the role files that installation manages. Both
# scaffold twins write it unconditionally and refuse to work against a truncated one, so a project
# that has it has it in this shape -- and this reader is held against a manifest a REAL scaffold
# run produced, not one written beside the test (`test_a_lead_can_change_the_preset_end_to_end`).
ROLES_MANIFEST = os.path.join(".claude", "team_kit_roles.txt")
_ROLES_HEADER_RX = re.compile(
    r"^#\s*agents-and-skills:team-kit-roles\s+v1\s+team=([A-Za-z0-9_-]+)\s+count=(\d+)\s*$")
# What the scaffold copied out of the staged kit at install time. Compared BYTE for byte rather
# than by its first line: the label and the content hash both live in it, so equality is "this is
# the kit this project was installed from" without a second rule about which part counts.
KIT_VERSION_FILE = os.path.join(".claude", "kit_version")
STAGED_VERSION_FILE = "VERSION"
# Where a kit is staged on this machine. The same location both scaffold twins resolve
# (`$HOME/.claude/team-kits`, `$env:USERPROFILE\.claude\team-kits`); `expanduser` answers with the
# platform's own of the two.
STAGING_RELATIVE = os.path.join(".claude", "team-kits")
PRESET_RESOLVER = "preset_config.py"
# How long the installer may run before this command gives up on it. A scaffold copies a few
# hundred small files and regenerates the provider artifacts; the timeout is here so a hung shell
# ends as a refusal with the tree rolled back rather than as a command that never returns.
INSTALLER_TIMEOUT = 600.0
# HOW A CHILD PROCESS'S OUTPUT IS DECODED, and it is not `text=True`. That decodes with the
# console codepage, so a byte the codepage has no character for raises `UnicodeDecodeError` out of
# a reader thread and the command dies on a message rather than on its work -- measured against
# the shipped `init_project_memory.ps1` on this host (cp1252, byte 0x81). What these two children
# produce is a DIAGNOSTIC to pass on, so an undecodable byte must cost a replacement character and
# nothing else. Same doctrine as `cli._json_body`: the kernel decides the encoding, not the
# console (BUG-0018).
#
# THE FOUR NAMES `kernel.kitupdate` READS OUT OF THIS MODULE are public for one reason: it starts
# the SAME installer, against the same staging, and a copy of the decoding rule, of the reader that
# keeps line endings, of the interpreter search or of the child budget would be a second answer to
# a question this module already answers (`CHILD_TEXT`, `read_text`, `installer_command`,
# `INSTALLER_TIMEOUT`). What that module does NOT reuse is everything about roles: its subject is
# the release, and the two readings are different data.
CHILD_TEXT = {"text": True, "encoding": "utf-8", "errors": "replace"}


def repo_root(state: ProjectState) -> str:
    """The project the state directory belongs to."""
    return os.path.dirname(state.root)


def staging_root() -> str:
    return os.path.join(os.path.expanduser("~"), STAGING_RELATIVE)


def read_text(path: str) -> str:
    """The file as it stands, line endings included (`newline=""`).

    Universal-newline reading would hand back `\\n` for a CRLF file, and both readers here care:
    the version comparison is an equality between two files, and the config edit writes back what
    it read minus one value -- a silent CRLF-to-LF rewrite of a kit document is a change nobody
    asked for and nothing would report.
    """
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return handle.read()


def installation(root: str) -> dict:
    """{"kit", "roles"} for this project, read off the scaffold's ownership manifest.

    `roles` is every role file that installation manages, lead included -- the lead is always
    first, and which of them it is comes from the kit catalogue rather than from this file's order.
    """
    path = os.path.join(root, ROLES_MANIFEST)
    try:
        lines = read_text(path).splitlines()
    except OSError:
        raise StateError(
            "this project has no %s, so nothing here can say which kit installed it or which "
            "roles that installation owns -- refused rather than guessed. Remedy: the kit was "
            "never scaffolded into this directory, or the record was lost; ask the user to run "
            "the scaffold for the team once, from a shell outside this session."
            % ROLES_MANIFEST.replace(os.sep, "/")) from None
    header = _ROLES_HEADER_RX.match(lines[0].rstrip("\r") if lines else "")
    roles = [line.rstrip("\r").strip() for line in lines[1:]]
    roles = [role for role in roles if role]
    if not header or len(roles) != int(header.group(2)):
        raise StateError(
            "%s is truncated or not the record this kit writes (header/count do not describe its "
            "%d role line(s)) -- refused, because removing roles from a list that is already "
            "incomplete deletes work capacity nobody chose. Remedy: restore it from "
            ".claude/backups/, or ask the user to re-run the scaffold."
            % (ROLES_MANIFEST.replace(os.sep, "/"), len(roles)))
    return {"kit": header.group(1), "roles": roles}


def kit_dir(kit: str) -> str:
    directory = os.path.join(staging_root(), kit)
    if not os.path.isdir(directory):
        raise StateError(
            "the kit '%s' is not staged on this machine (%s), so its roles cannot be installed "
            "from here. Remedy: this is an infrastructure gap, not a retry -- report it and name "
            "the directory; the kits are installed once per machine, outside any project."
            % (kit, directory))
    return directory


def assert_installable(root: str, directory: str) -> None:
    """Refuse a preset change against a kit that is not the one this project runs.

    See the module docstring: the installer re-copies the whole enforcement bundle, so a differing
    staging would make this command a kit update the user never approved.
    """
    installed = os.path.join(root, KIT_VERSION_FILE)
    staged = os.path.join(directory, STAGED_VERSION_FILE)
    try:
        same = read_text(installed) == read_text(staged)
    except OSError as exc:
        raise StateError(
            "cannot compare the staged kit with the one this project installed (%s) -- refused "
            "(fail-closed): without that comparison a preset change cannot be told apart from a "
            "kit update. Remedy: report the gap and name the file." % exc) from None
    if not same:
        raise StateError(
            "the staged kit is not the one this project is installed at (%s differs from the "
            "kit's own %s), so installing its roles would replace this project's hooks, kernel "
            "and constitution as well -- a kit update, which nobody approved here. Remedy: do the "
            "kit update first, as its own step with its own user decision, and change the preset "
            "afterwards."
            % (KIT_VERSION_FILE.replace(os.sep, "/"), STAGED_VERSION_FILE))


def resolve(directory: str, preset: str) -> dict:
    """The kit's own answer to "which specialists does this preset install".

    ASKED OF `preset_config.py`, which is the file both scaffold twins ask and the repo validator
    parses, and asked as a SUBPROCESS exactly as they do. Two reasons, and the second is the one
    that matters: its strict loader is what makes a preset mechanical (duplicate keys, unknown
    roles and the foreground lead as a specialist are all refusals there), and a second reader here
    would be a second policy; and it lives in the staging rather than in this package, so importing
    it would pull a module out of the user's home directory into the kernel process.
    """
    script = os.path.join(os.path.dirname(directory), PRESET_RESOLVER)
    try:
        result = subprocess.run([sys.executable, "-B", script, "--kit", directory,
                                 "--preset", preset, "--source", COMMAND,
                                 "--format", "json"],
                                capture_output=True, timeout=120, **CHILD_TEXT)
    except (OSError, subprocess.SubprocessError) as exc:
        raise StateError(
            "the kit's preset resolver (%s) could not be run (%s) -- refused; nothing was "
            "changed. Remedy: report the gap and name the file." % (script, exc)) from None
    if result.returncode != 0:
        raise StateError(
            "%s No files were changed." % (result.stderr or result.stdout or "").strip())
    try:
        answer = json.loads(result.stdout)
    except ValueError:
        raise StateError(
            "the kit's preset resolver answered something this kernel cannot read -- refused; "
            "nothing was changed. Remedy: report the gap.") from None
    return answer


def _plan(state: ProjectState, preset: str) -> dict:
    """Everything one preset change needs to know, resolved once: kit, staging, manifest.

    `apply` and the approval question are two readers of ONE derivation -- if each resolved the
    kit and the role delta for itself, the question could name a set the command then does not
    install, which is the one thing the approval hash exists to prevent.
    """
    root = repo_root(state)
    installed = installation(root)
    directory = kit_dir(installed["kit"])
    assert_installable(root, directory)
    resolved = resolve(directory, preset)
    target = set(resolved.get("specialists") or [])
    current = {role for role in installed["roles"] if role != resolved.get("lead")}
    return {
        "kit": installed["kit"],
        "kit_dir": directory,
        "manifest": approvals.preset_subject_manifest(
            resolved.get("preset"), sorted(target), sorted(current - target)),
    }


def change_manifest(state: ProjectState, preset: str) -> dict:
    """What a change to `preset` would DO here, in the shape the approval hashes.

    The approval question is built from this and `apply` re-derives it, refusing unless the hash
    still matches (`test_a_preset_approval_does_not_cover_a_different_role_set`).
    """
    return _plan(state, preset)["manifest"]


# -- the writes -----------------------------------------------------------------------------

_PROJECT_BLOCK_RX = re.compile(r"^project\s*:\s*(?:#.*)?$")
_PRESET_LINE_RX = re.compile(
    r"^(?P<head>[ \t]+preset[ \t]*:[ \t]*)(?P<value>'[^']*'|\"[^\"]*\"|[^#\s]*)(?P<tail>.*)$")


def config_path(state: ProjectState) -> str:
    """The kit document this command writes ONE key of -- see `_with_preset` for how narrowly."""
    return os.path.join(state.root, "project_config.yaml")


def _with_preset(text: str, preset: str) -> str:
    """`text` with `project.preset` set, and NOTHING else about the file touched.

    A line edit rather than a YAML round-trip, and that is the whole reason this is not three
    lines: `project_config.yaml` is a kit DOCUMENT whose comments carry the model ladder, the
    escalation rules and the reason for every default. `yaml.safe_dump` of a parsed copy would
    write back a valid file with all of that deleted -- the kernel silently destroying the one
    document in the project nothing else can rewrite.

    The block is found structurally (the top-level `project:` mapping and the indented lines under
    it), and exactly one `preset:` line inside it is accepted; anything else is refused rather than
    guessed at, because writing the wrong one would leave the recorded preset and the installed
    roles disagreeing.
    """
    lines = text.splitlines(keepends=True)
    start = next((index for index, line in enumerate(lines)
                  if _PROJECT_BLOCK_RX.match(line.rstrip("\r\n"))), None)
    if start is None:
        raise StateError(
            "project_config.yaml has no top-level `project:` block, so there is no recorded "
            "preset to change -- refused. Remedy: report the gap and name the file.")
    hits = []
    for index in range(start + 1, len(lines)):
        bare = lines[index].rstrip("\r\n")
        if bare and not bare[0].isspace() and not bare.lstrip().startswith("#"):
            break                                   # the next top-level key ends the block
        match = _PRESET_LINE_RX.match(bare)
        if match:
            hits.append((index, match))
    if len(hits) != 1:
        raise StateError(
            "project_config.yaml's `project:` block carries %d `preset:` line(s); this kernel "
            "writes exactly one and refuses to guess which. Remedy: report the gap and name the "
            "file." % len(hits))
    index, match = hits[0]
    ending = lines[index][len(lines[index].rstrip("\r\n")):]
    lines[index] = match.group("head") + preset + match.group("tail") + ending
    return "".join(lines)


def record_preset(state: ProjectState, preset: str) -> str:
    """Write `project.preset` and hand back the file as it was, for a caller that must undo it.

    READ BACK AND PARSED before it is accepted: the line edit above is a text operation, and the
    only proof that it produced the recorded preset is asking YAML what the file now says. A file
    that parses to anything else is restored here and the operation refuses
    (`test_a_config_the_write_did_not_actually_change_is_restored`).
    """
    path = config_path(state)
    try:
        before = read_text(path)
    except OSError as exc:
        raise StateError(
            "project_config.yaml cannot be read (%s), so the preset it records cannot be "
            "changed -- refused. Remedy: report the gap and name the file." % exc) from None
    state._write_text_atomic(path, _with_preset(before, preset))
    try:
        written = (yaml.safe_load(read_text(path)) or {}).get("project") or {}
    except Exception:                                   # noqa: BLE001 -- any parse failure is one
        written = {}
    if written.get("preset") != preset:
        state._write_text_atomic(path, before)
        raise StateError(
            "writing the preset into project_config.yaml did not produce a file that records it; "
            "the file was restored unchanged and nothing was installed. Remedy: report the gap "
            "and name the file.")
    return before


def installer_command(kit: str):
    """The kit's own scaffold, started the way this host can start it.

    Platform-native first, and the first candidate whose interpreter this host actually HAS wins
    -- so a Windows box without PowerShell still installs through Git Bash rather than the user
    being told to do it by hand, which is the failure mode this whole module exists against. Both
    twins take the same two facts (team, and the preset out of `project_config.yaml`), so which one
    runs changes nothing but the interpreter.
    """
    staging = staging_root()
    powershell = ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                  os.path.join(staging, "scaffold_team.ps1"), "-Team", kit]
    candidates = [("powershell", powershell), ("pwsh", powershell),
                  ("bash", [os.path.join(staging, "scaffold_team.sh"), kit])]
    if os.name != "nt":
        candidates.reverse()
    for executable, arguments in candidates:
        found = shutil.which(executable)
        if found:
            return [found] + list(arguments)
    raise StateError(
        "no shell on this machine can start the kit's installer (looked for %s), so the roles "
        "cannot be installed from here -- nothing was changed. Remedy: this is an infrastructure "
        "gap; report it and name the machine."
        % ", ".join(sorted({name for name, _arguments in candidates})))


AGENTS_DIR = os.path.join(".claude", "agents")
# The installer's OTHER role-artifact destination, and it is stated here for the same reason as
# `AGENTS_DIR`: this module is what drives the scaffold, so the paths the scaffold writes are its
# answer to give. `UNREAD` below already had to name `.claude/skills` in prose; `kernel.references`
# now reads it, and a kit that moved its skills would move both with this line instead of leaving a
# second spelling somewhere to go stale.
SKILLS_DIR = os.path.join(".claude", "skills")
ROLE_SUFFIX = ".md"

# WHAT THE TWO READERS DO NOT COVER, in the words the refusals carry -- one sentence, and EVERY
# outcome that reports on the installation carries it, because a scope stated in some of them is a
# scope the others deny. `_installed_state` reads the ownership record and the role FILES it names;
# the same installer run also writes `.claude/skills/<role>/` and the generated provider artifacts,
# and neither is re-read after a failure.
#
# MEASURED, not foreseen, and in BOTH directions. At a 1.5 s abort against the real scaffold the
# verifier saw the roles back and both readers consistent while `.claude/skills` had gone from
# seven directories to none -- under a sentence that said "nothing is missing"; the next full
# installer run restored them. Replaying the same abort here landed in a different phase of the
# same run and left the other shape: the ownership record naming five roles while `.claude/agents`
# held nine and `.claude/skills` seven, i.e. LEFTOVERS of the half-installed set, which the next
# full run prunes by that same record. Neither shows in these readings.
#
# So no message here makes an unconditional completeness claim; the limit travels with the
# statement, and `test_the_outcome_messages_carry_the_limit_of_what_was_re_read` is what keeps it
# there.
UNREAD = ("the role skills, the generated provider artifacts and any role artifact this "
          "installation does not own were not re-read, so a missing or a leftover one would not "
          "show here")


def _installed_state(root: str) -> dict:
    """{"roles", "missing"} -- the ownership RECORD and whether the files it claims are there.

    TWO READERS, BECAUSE ONE OF THEM IS STALE FOR THE WHOLE WINDOW THIS MATTERS IN. The installer
    removes the old role FILES first and writes the ownership manifest LAST (measured order in its
    own console log: skills, then `.claude/team_kit_roles.txt`, then `settings.json`). So a run
    that is killed in between leaves a manifest naming a set that is no longer on disk -- and a
    caller that asked only the manifest would report "unchanged" over two deleted roles. Measured
    by the verifier against the real scaffold at a 1.5 s abort: manifest 7, `.claude/agents` 5.

    `missing` is the manifest's roles that have no file, so it is empty exactly when the two agree.
    None for both fields means the manifest itself could not be read -- one more thing to report on
    a failure path, never a reason to stop reporting. A file the manifest does NOT name is not
    counted: the scaffold tolerates role files it does not own (its collision branch exists for
    them), so an extra one is not a half-written install.

    WHAT IT DOES NOT READ is `UNREAD` above -- stated there because the refusals have to carry it
    to the user, and a limit written only in a docstring is one the messages deny.
    `test_a_half_written_installation_is_never_reported_as_unchanged` measures the agents half.
    """
    try:
        roles = list(installation(root)["roles"])
    except StateError:
        return {"roles": None, "missing": None}
    directory = os.path.join(root, AGENTS_DIR)
    return {"roles": roles,
            "missing": [role for role in roles
                        if not os.path.isfile(os.path.join(directory, role + ROLE_SUFFIX))]}


def _agrees(left: dict, right: dict) -> bool:
    """Do two readings describe the SAME, whole installation?

    Both have to be readable, name the same roles, and have every named role on disk. The last
    condition is what keeps a half-written installation out of the "nothing changed" outcome.
    """
    return (left["roles"] is not None and right["roles"] is not None
            and left["roles"] == right["roles"] and not left["missing"] and not right["missing"])


def _describe(reading: dict) -> str:
    """One reading in the words a lead passes on to the user."""
    if reading["roles"] is None:
        return "unreadable"
    listed = ", ".join(reading["roles"]) or "-"
    if reading["missing"]:
        return "%s in the ownership record, but the role file(s) for %s are gone" % (
            listed, ", ".join(reading["missing"]))
    return listed


def _after_a_failed_install(state, root, before, was, command, reason):
    """Put the project back as far as it can be put back, and refuse with the TRUE state.

    THE DEFECT THIS EXISTS FOR, measured by the verifier against the real installer with the
    timeout shortened: the abort branch restored the config and said "no role was changed" while
    two role files were already deleted -- the installer had removed the old set and was killed
    before it wrote the new one. A refusal that describes a state the project is not in is worse
    than the failure it reports, because it is what the lead passes on to the user; and the user's
    still-living approval cannot repair it either, since `removes` has moved and the hash no longer
    matches (`test_an_aborted_install_reports_the_state_it_actually_left`).

    So nothing here is asserted: the installation is READ BACK -- the ownership record and the role
    files it claims (`_installed_state`) -- and the three outcomes are told apart by that reading.
    Unchanged, and whole -- say so. Anything else -- run the installer once more, now against the
    RESTORED config, which is exactly the operation that reinstalls the old preset; if that brings
    the installation back, say what happened, and if it does not, name what the project has now
    against what it had. The repair is deliberately the same command and not a second
    implementation of one.

    THE REPAIR RUN IS RE-READ EVEN WHEN IT IS KILLED, and that is not a detail: what stops the
    first run usually stops the second, and the reading used to happen INSIDE the try -- so an
    aborted repair left the state "unreadable" and printed the loudest of the three outcomes over a
    project the verifier measured intact. An over-alarming refusal is as wrong as a reassuring one
    (`test_a_repair_run_that_is_killed_after_its_work_is_not_reported_as_a_loss`). The run's own
    exit code decides nothing here; both outcomes below are decided by the re-reading.

    RETURNS the refusal instead of raising it, so both call sites read `raise
    _after_a_failed_install(...)` and the control flow of `apply` stays on its own page.
    """
    state._write_text_atomic(config_path(state), before)
    now = _installed_state(root)
    if _agrees(was, now):
        return StateError(
            "%s The recorded preset was restored, and the ownership record and the role files it "
            "names are unchanged (%s); %s. Remedy: report the gap, and pass that limit on with it."
            % (reason, _describe(was), UNREAD))
    repair_note = ""
    try:
        again = subprocess.run(command, cwd=root, capture_output=True,
                               timeout=INSTALLER_TIMEOUT, **CHILD_TEXT)
        if again.returncode != 0:
            repair_note = " (the repair run itself exited %d)" % again.returncode
    except (OSError, subprocess.SubprocessError) as exc:
        repair_note = " (the repair run could not be completed: %s)" % exc
    repaired = _installed_state(root)
    if _agrees(was, repaired):
        return StateError(
            "%s The install had already changed the installation; the recorded preset was restored "
            "and running the installer against it put the roles back (%s)%s -- read off the "
            "ownership record and the role files it names; %s. The change itself did not happen. "
            "Remedy: report the gap, and pass that limit on with it."
            % (reason, _describe(was), repair_note, UNREAD))
    return StateError(
        "%s THE PROJECT IS NOT IN THE STATE IT WAS: the ownership record and the role files it "
        "names were %s and are now %s%s; %s. The recorded preset was restored to what it was, so "
        "the config no longer describes the roles on disk. Remedy: report this to the user with "
        "these two lists and stop -- the roles are restored by running the kit's installer for the "
        "recorded preset, which is a step for a shell outside this session, and the backups of the "
        "run are under .claude/backups/."
        % (reason, _describe(was), _describe(repaired), repair_note, UNREAD))


def apply(state: ProjectState, preset: str) -> dict:
    """Record `preset` and install exactly its roles -- the operation BUG-0041 asked for.

    ORDER, and every step of it is deliberate. The approval is checked first, so nothing moves
    without it. The config is written BEFORE the installer runs, because the installer reads the
    recorded preset back out of that file -- so what gets installed is what the project now
    records, rather than two arguments that could disagree. What a FAILED install leaves behind is
    `_after_a_failed_install`, which measures the roles rather than claiming anything about them.

    WHAT THIS DOES NOT DO, and it is the honest half of the remedy the caller prints: it cannot
    make the new roles usable in the RUNNING session. The provider reads its agent set at session
    start, so the restart request is not politeness -- and the installer's own handover marker
    stops this session deriving further, which is the state the kits already use after an install.
    """
    with state.lock:
        plan = _plan(state, preset)
        manifest = plan["manifest"]
        if approvals.live_line_approval(state, KIND, manifest) is None:
            raise StateError(
                "no user approval covers this preset change, so nothing was changed. What it "
                "would do: install %s%s. Remedy: ask for it first -- `python scripts/harness.py "
                "request-approval %s --preset %s` prints the question, and the USER approves by "
                "answering it; then run this command again."
                % (", ".join(manifest["roles"]) or "no specialist at all",
                   " and REMOVE %s" % ", ".join(manifest["removes"]) if manifest["removes"] else "",
                   KIND, preset))
        root = repo_root(state)
        # BEFORE the config moves: this is what the failure paths compare against, and after the
        # write there is no way back to it.
        was = _installed_state(root)
        # ...AND THE INTERPRETER SEARCH BELONGS HERE TOO, ahead of the write. It is a pure PATH
        # lookup with no side effect, and its refusal says "nothing was changed" -- a sentence that
        # was false the moment it stood one line further down: the config already carried the new
        # preset, `_after_a_failed_install` was never reached, and the next scaffold run would have
        # read that config and installed a change nobody approved. Measured with the candidate
        # interpreters pointed at names this host does not have; practically unreachable on Windows
        # and real on a POSIX host without bash, which is exactly where the `.sh` twin ships
        # (`test_a_host_without_a_shell_for_the_installer_changes_nothing`). Ordering it before the
        # write makes the sentence true by construction rather than by a second restore site.
        command = installer_command(plan["kit"])
        before = record_preset(state, preset)
        try:
            result = subprocess.run(command, cwd=root, capture_output=True,
                                    timeout=INSTALLER_TIMEOUT, **CHILD_TEXT)
        except (OSError, subprocess.SubprocessError) as exc:
            raise _after_a_failed_install(
                state, root, before, was, command,
                "the kit's installer did not complete (%s)." % exc) from None
        if result.returncode != 0:
            raise _after_a_failed_install(
                state, root, before, was, command,
                "the kit's installer refused (exit %d). It said:\n%s\n"
                % (result.returncode,
                   ((result.stderr or "") + (result.stdout or "")).strip()[-1200:]))
        return {"kit": plan["kit"], "preset": preset,
                "roles": manifest["roles"], "removed": manifest["removes"],
                "installed": installation(root)["roles"]}
