"""The kit-update route (FR-0006): what it refuses, what it leaves behind, and one real run.

WHY MOST OF THIS RUNS AGAINST A STUB INSTALLER -- the same reason `tools/test_presets.py` gives:
the kernel's decisions (is this an update at all, is the staging still the tree the user approved,
is a restart already pending, what does an ABORTED run leave) are decisions about a project's
records, and each needs its own arranged state. The installer those decisions end in is the kits'
own `scaffold_team`, and it is measured where it belongs: `test_a_lead_can_update_the_kit_end_to_
end` runs the real thing against a real scaffolded project through the shipped entry point and the
real approval hook, and `test_the_marker_this_command_leaves_really_stops_the_session` runs the two
hooks that read the marker as processes.

The stub is not a mock of the installer's behaviour. It is a script in the two spellings the kernel
starts, and every test using it asserts what the KERNEL did around it.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEAM_KITS = os.path.join(ROOT, "team-kits")
sys.path.insert(0, TEAM_KITS)

from kernel import approvals, cli, hashing, kitupdate, presets  # noqa: E402
from kernel.state import ProjectState, StateError  # noqa: E402

KIT = "demo-team"
OLD = "2026.07.01-1"
NEW = "2026.08.16-9"
ROLES_MANIFEST_HEADER = "# agents-and-skills:team-kit-roles v1 team=%s count=%d"
KITS = ("dev-team", "office-team", "research-team")


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def _read(path):
    with open(path, encoding="utf-8-sig") as handle:
        return handle.read()


STUB = '''"""A stand-in `scaffold_team` for what a KIT UPDATE does to the records this kernel reads.

The real one copies `.claude/hooks` and `.claude/kernel` LONG before it stamps
`.claude/kit_version`, and writes `.claude/HANDOVER_PENDING` as its very last act -- both measured
against the shipped scaffold (docs/reviews/2026-08-16-tsk0067-measurements.md). So this keeps that
ORDER, and STUB_PLAN says how far it gets:

  ok         -- bundle, stamp, trust record, pending-templates note and marker: a complete update
  bundle     -- replace the bundle and then hang: the window in which the stamp is stale
  stamped    -- bundle and stamp, then hang: the window in which everything but the marker is done
  no-marker  -- a COMPLETE update whose LAST act did not happen: everything but the marker, exit 0
  exit       -- refuse without touching anything (the real one rolls its own changes back)
  marker-only-- raise the marker and then refuse, touching nothing else: the one shape in which a
                run that moved nothing still leaves a project stopped
"""
import hashlib
import json
import os
import shutil
import sys
import time

CLAUDE = ".claude"


def bundle_hash(root):
    digest = hashlib.sha256()
    for sub in ("hooks", "kernel"):
        for name in sorted(os.listdir(os.path.join(root, CLAUDE, sub))):
            path = os.path.join(root, CLAUDE, sub, name)
            digest.update(name.encode() + b"\\0" + open(path, "rb").read() + b"\\0")
    return digest.hexdigest()


def install_bundle():
    """What the real scaffold does first: the kit's hooks and the staging's kernel, copied in."""
    kit = os.environ["STUB_KIT"]
    for source, target in ((os.path.join(kit, "hooks"), os.path.join(CLAUDE, "hooks")),
                           (os.path.join(os.path.dirname(kit), "kernel"),
                            os.path.join(CLAUDE, "kernel"))):
        shutil.rmtree(target, ignore_errors=True)
        shutil.copytree(source, target)


plan = (os.environ.get("STUB_PLAN") or "ok").split(",")
runs_file = os.environ["STUB_RUNS"]
runs = (int(open(runs_file).read() or "0") if os.path.exists(runs_file) else 0) + 1
open(runs_file, "w").write(str(runs))
verb = plan[runs - 1] if runs <= len(plan) else plan[-1]
hang = float(os.environ.get("STUB_HANG") or 30)
open(os.environ["STUB_WITNESS"], "w").write(verb)

if verb == "exit":
    print("stub refused the install")
    sys.exit(3)
if verb == "marker-only":
    open(os.path.join(CLAUDE, "HANDOVER_PENDING"), "w").write("raised\\n")
    print("stub refused the install after raising the marker")
    sys.exit(3)
install_bundle()
if verb == "bundle":
    time.sleep(hang)
    sys.exit(0)
open(os.path.join(CLAUDE, "kit_version"), "w").write(open(os.environ["STUB_STAGED"]).read())
if verb == "stamped":
    time.sleep(hang)
    sys.exit(0)
record = json.load(open(os.path.join(CLAUDE, "kit_state.json")))
record["hook_bundle_hash"] = bundle_hash(".")
json.dump(record, open(os.path.join(CLAUDE, "kit_state.json"), "w"), indent=2)
open(os.path.join(CLAUDE, "kit_update_pending.repo"), "w").write(
    "# diverged\\n- scripts/quality.py\\n")
if verb != "no-marker":
    open(os.path.join(CLAUDE, "HANDOVER_PENDING"), "w").write("installed\\n")
'''


def _stub_installer(staging, witness):
    """A `scaffold_team` in both spellings, dispatching to one Python stand-in.

    The behaviour lives in Python because the interesting cases are SEQUENCES (a killed run and the
    kernel's completing run). What stays in the shell files is the one thing the kernel chooses:
    which of the two it starts.
    """
    _write(os.path.join(staging, "stub_install.py"), STUB)
    _write(os.path.join(staging, "scaffold_team.ps1"),
           "param([string]$Team)\n& $env:STUB_PYTHON $env:STUB_SCRIPT\nexit $LASTEXITCODE\n")
    _write(os.path.join(staging, "scaffold_team.sh"),
           "#!/usr/bin/env bash\n\"$STUB_PYTHON\" \"$STUB_SCRIPT\"\n")
    os.chmod(os.path.join(staging, "scaffold_team.sh"), 0o755)
    return witness


def _stamp(version, content):
    return "version: %s\ncontent: %s\n" % (version, content)


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A project that LOOKS installed at an OLDER kit, with a NEWER one staged in a fake home.

    The staged kit is stamped with its own REAL `kernel.hashing.kit_hash`, because that is what
    `assert_the_staging_is_its_own_stamp` measures -- a hand-written hash would make every test
    here measure that refusal instead of its own subject.
    """
    home = tmp_path / "home"
    staging = home / ".claude" / "team-kits"
    kit = staging / KIT
    _write(str(kit / "hooks" / "gate.py"), "# the staged kit's hook\n")
    _write(str(kit / "agents" / "project-manager.md"), "---\nname: project-manager\n---\n")
    _write(str(staging / "kernel" / "state.py"), "# the staged kernel\n")
    witness = _stub_installer(str(staging), str(tmp_path / "witness.txt"))
    # STAMPED LAST, because `kit_hash` covers the staging's SHARED half as well (`@shared/...`) --
    # the stub installer's two shell files live there, so a stamp taken before them describes a
    # tree that no longer exists and every test would measure `assert_the_staging_is_its_own_stamp`
    # instead of its own subject.
    _write(str(kit / "VERSION"), _stamp(NEW, hashing.kit_hash(str(kit))))

    repo = tmp_path / "repo"
    _write(str(repo / ".claude" / "kit_version"), _stamp(OLD, "a" * 64))
    _write(str(repo / ".claude" / "team_kit_roles.txt"),
           (ROLES_MANIFEST_HEADER % (KIT, 1)) + "\nproject-manager\n")
    _write(str(repo / ".claude" / "hooks" / "gate.py"), "# an older kit's hook\n")
    _write(str(repo / ".claude" / "kernel" / "state.py"), "# an older kernel\n")
    _write(str(repo / ".claude" / "kit_state.json"), json.dumps(
        {"kit": KIT, "kit_version": "version: " + OLD, "state": "active",
         "hook_bundle_hash": hashing.hook_bundle_hash(str(repo / ".claude"))}))
    _write(str(repo / "project_memory" / "project_config.yaml"), "project:\n  preset: solo\n")

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("STUB_PYTHON", sys.executable)
    monkeypatch.setenv("STUB_SCRIPT", str(staging / "stub_install.py"))
    monkeypatch.setenv("STUB_RUNS", str(tmp_path / "runs.txt"))
    monkeypatch.setenv("STUB_WITNESS", witness)
    monkeypatch.setenv("STUB_STAGED", str(kit / "VERSION"))
    monkeypatch.setenv("STUB_KIT", str(kit))
    monkeypatch.setenv("STUB_PLAN", "ok")
    return {"state": ProjectState(str(repo / "project_memory")), "repo": repo, "kit": kit,
            "witness": witness, "home": home}


def approve(project):
    """Mint a real `kit_update` approval for what an update would do here."""
    import time

    from conftest import mint_via_hook
    state = project["state"]
    request = approvals.create_pending_request(
        state, kitupdate.KIND, manifest=kitupdate.change_manifest(state),
        approval_expires=time.time() + approvals.LINE_APPROVAL_VALIDITY)
    mint_via_hook(state, request)
    return request


def installed_version(project):
    return kitupdate.identity(_read(str(project["repo"] / ".claude" / "kit_version")))["version"]


def ran(project):
    return os.path.exists(project["witness"])


# -- what it refuses before anything moves ------------------------------------------------------

def test_a_kit_update_needs_a_user_approval_before_anything_moves(project):
    """No approval, no installer -- and the refusal names the line that opens the question.

    The remedy is the point of the refusal: the lead reading it must not fall back on the route
    V2 left it with (send the USER to a terminal), so the message carries the two commands.
    """
    with pytest.raises(StateError) as refused:
        kitupdate.apply(project["state"])
    assert "request-approval kit_update" in str(refused.value)
    assert OLD in str(refused.value) and NEW in str(refused.value)
    assert installed_version(project) == OLD
    assert not ran(project), "the installer ran without an approval"


def test_an_older_staging_is_refused_before_the_installer_starts(project):
    """A downgrade is not an update in the other direction -- it is a broken installation.

    Measured against a real staging 2026-08-02: a 07-18 kit offered to an 08-02 project prunes the
    hooks that project needs and leaves its newer kernel in place. Refused at the QUESTION too, so
    a user is never asked to approve one.
    """
    _write(str(project["repo"] / ".claude" / "kit_version"), _stamp("2026.09.01-1", "b" * 64))
    with pytest.raises(StateError, match="OLDER than the one this project runs"):
        kitupdate.change_manifest(project["state"])
    with pytest.raises(StateError, match="OLDER than the one this project runs"):
        kitupdate.apply(project["state"])
    assert not ran(project)


def test_the_same_release_is_not_an_update(project):
    """Re-applying the SAME release is a repair, and this command says so instead of doing it.

    It matters because the scaffold ALLOWS a same-version re-run (it re-syncs managed files), so
    without this branch `update-kit` would quietly become a way to re-run the installer -- with a
    user approval whose from and to say the same thing.
    """
    _write(str(project["repo"] / ".claude" / "kit_version"),
           _read(str(project["kit"] / "VERSION")))
    with pytest.raises(StateError, match="already runs the staged"):
        kitupdate.apply(project["state"])
    assert not ran(project)


def test_a_staging_with_the_same_stamp_and_other_content_is_refused(project):
    """One version stamp over two different trees is a finding, not an update.

    The briefing has been able to REPORT this since 2026-08-02 and nothing could act on it; the
    command refuses it, which is why `content:` is part of the comparison at all.
    """
    _write(str(project["repo"] / ".claude" / "kit_version"), _stamp(NEW, "c" * 64))
    with pytest.raises(StateError, match="SAME version stamp"):
        kitupdate.apply(project["state"])
    assert not ran(project)


def test_a_staging_edited_after_the_question_is_refused(project):
    """The staged tree must still hash to the `content:` its own VERSION claims.

    Checked BEFORE the first file moves, not by `write_kit_state` at the end of the scaffold: there
    the same finding costs a rolled-back enforcement layer, here it costs 20 ms of hashing (the
    three shipped kits, measured 2026-08-16).
    """
    approve(project)
    _write(str(project["kit"] / "hooks" / "gate.py"), "# edited after the user was asked\n")
    with pytest.raises(StateError, match="does not hash to the `content:`"):
        kitupdate.apply(project["state"])
    assert not ran(project)
    assert installed_version(project) == OLD


@pytest.mark.parametrize("marker", [entry["path"] for entry in kitupdate.RESTART_MARKERS])
def test_a_project_already_waiting_for_a_restart_is_refused(project, marker):
    """An install already happened here and no session start has consumed its marker.

    What that project needs is the restart, not a second installer run over the first one's
    record -- the scaffold's own "never overwrite an unconsumed marker" rule is about the same
    file. Both markers, from the definition rather than by name.
    """
    approve(project)
    _write(str(project["repo"] / marker), "pending\n")
    with pytest.raises(StateError, match="already waiting for a session restart"):
        kitupdate.apply(project["state"])
    assert not ran(project)
    assert installed_version(project) == OLD


def test_a_host_without_a_shell_for_the_installer_changes_nothing(project, monkeypatch):
    """"Nothing was changed" has to be true when it is printed.

    The interpreter search is a pure PATH lookup, so it belongs ahead of the run -- the ordering
    `presets.apply` had to learn the hard way, kept here by construction rather than by a second
    restore site.
    """
    approve(project)
    monkeypatch.setattr(presets.shutil, "which", lambda _name: None)
    with pytest.raises(StateError, match="no shell on this machine"):
        kitupdate.apply(project["state"])
    assert not ran(project)
    assert installed_version(project) == OLD


# -- the approval binds the two RELEASES --------------------------------------------------------

def test_an_approval_for_one_release_pair_does_not_cover_another(project):
    """Approve A -> B; the staging becomes C, and the same command refuses.

    The hash is over the OUTCOME (`approvals.kit_update_subject_manifest`), so a staging that moved
    between the question and the command is a different decision. Without the version pair in the
    manifest, an approval given for one release would install whatever is staged when it is spent.
    """
    approve(project)
    other = _read(str(project["kit"] / "VERSION")).replace(NEW, "2026.08.17-1")
    _write(str(project["kit"] / "VERSION"), other)
    with pytest.raises(StateError, match="no user approval"):
        kitupdate.apply(project["state"])
    assert not ran(project)
    assert installed_version(project) == OLD


def test_an_approval_does_not_cover_an_update_from_a_different_release(project):
    """...and the FROM side counts too: A -> B is not C -> B.

    The user is told what the project is losing, so an approval signed while the project ran A
    cannot be spent after it has been moved to C by something else.
    """
    approve(project)
    _write(str(project["repo"] / ".claude" / "kit_version"), _stamp("2026.07.02-1", "d" * 64))
    with pytest.raises(StateError, match="no user approval"):
        kitupdate.apply(project["state"])
    assert not ran(project)


def test_an_expired_kit_update_approval_authorises_nothing(project, monkeypatch):
    """An unused permission to replace the enforcement layer must not outlive the conversation."""
    approve(project)
    later = __import__("time").time() + approvals.LINE_APPROVAL_VALIDITY + 60
    monkeypatch.setattr(approvals.time, "time", lambda: later)
    with pytest.raises(StateError, match="no user approval"):
        kitupdate.apply(project["state"])
    assert not ran(project)


def test_the_question_the_user_sees_names_both_releases_and_no_full_hash(project, capsys):
    """What the user judges is "this kit, from here to there" -- and the digests are shortened.

    Both halves are the same rule: the hash covers the outcome, and the question has to be
    READABLE by the person who has to judge it (BUG-0041's finding). The two content hashes are
    128 of ~180 characters in full, so `approvals._render_manifest_value` renders any digest the
    way the sentence around it already renders one -- twelve characters and an ellipsis.
    """
    state = project["state"]
    assert cli.main(["--root", state.root, "request-approval", kitupdate.KIND]) == 0
    question = json.loads(capsys.readouterr().out)["question"]
    assert OLD in question and NEW in question and KIT in question
    manifest = kitupdate.change_manifest(state)
    assert manifest["to_content"] not in question, "the full staged content hash is in the question"
    assert manifest["to_content"][:approvals.DIGEST_SHOWN] in question


@pytest.mark.parametrize("flag", ["--kit", "--to-version", "--from-content"])
def test_a_resolver_owned_key_of_this_manifest_is_not_typed_on_the_line(project, capsys, flag):
    """Every key here is the kit's own statement about a release, so none of them is typed.

    A typed one could only differ from what the command re-derives, and then the question and the
    act would say different things -- the property `cli._line_manifest` refuses on.
    """
    state = project["state"]
    assert cli.main(["--root", state.root, "request-approval", kitupdate.KIND, flag, "x"]) == 2
    assert "not a value to type on this line" in capsys.readouterr().err


def test_the_update_command_is_on_the_surface_the_refusals_name(project):
    """`update-kit` and `request-approval kit_update` exist as the shipped parser spells them."""
    subcommands = cli.build_parser()._subparsers._group_actions[0].choices
    assert kitupdate.COMMAND in subcommands
    kinds = next(action.choices for action in subcommands["request-approval"]._actions
                 if action.dest == "kind")
    assert kitupdate.KIND in kinds


def test_the_version_order_is_the_numbers_and_not_the_string():
    """`2026.08.02-11` is newer than `-9`; a hand-edited stamp orders to nothing at all.

    The one definition `update-kit` refuses a downgrade on and the three session briefings read
    (`tools/test_hooks.py::test_the_version_order_is_read_from_the_numbers_and_not_from_the_string`
    measures the briefing end of it, as a real hook process).
    """
    assert kitupdate.version_order("2026.08.02-11") > kitupdate.version_order("2026.08.02-9")
    assert kitupdate.version_order("2026.07.18-1") < kitupdate.version_order("2026.08.02-1")
    assert kitupdate.version_order("") is None
    assert kitupdate.version_order("hand-edited") is None


# -- what a run leaves behind -------------------------------------------------------------------

@pytest.mark.parametrize("plan,marker", [("ok", "is in place"),
                                         ("no-marker", "was written by this command")])
def test_an_update_reports_both_readers_and_reads_the_marker_back(project, monkeypatch, plan,
                                                                  marker):
    """The happy path says what it READ, and nothing beyond it -- the marker line included.

    Two readers because one of them is stale for the whole window that matters: the stamp is what
    the project claims to run, the bundle is what it actually runs.

    AND THE MARKER LINE IS A READING, not a sentence: an installer that completed everything but
    its last act leaves a session whose kit has changed and no stop sign, and the success message
    has to say which of the two it is looking at. Both plans here, because a hardcoded "is in
    place" passes the first and fails the second -- which is the only way this claim can go red.
    """
    monkeypatch.setenv("STUB_PLAN", plan)
    approve(project)
    result = kitupdate.apply(project["state"])
    assert result["to"] == NEW and installed_version(project) == NEW
    assert "the enforcement bundle on disk is the STAGED kit's" in result["installed"]
    assert marker in result["marker"], result["marker"]
    assert os.path.exists(str(project["repo"] / kitupdate.HANDOVER_MARKER))
    assert "scripts/quality.py" not in result["pending_templates"]
    assert "1 repo template(s)" in result["pending_templates"]


def test_an_update_whose_installer_left_no_marker_says_so_and_writes_one(project, monkeypatch):
    """The measured window: everything done, the marker not yet written, the run killed there.

    Measured against the real scaffold 2026-08-16: between 2.4 s and 3.4 s of a 3.4 s run the
    stamp, the bundle and the trust record were the new release's and `.claude/HANDOVER_PENDING`
    was still absent, because the installer writes it last. A session there has had its kit
    replaced and nothing stops it. So the command ensures the marker itself and says which of the
    two it is looking at.
    """
    monkeypatch.setattr(presets, "INSTALLER_TIMEOUT", 3)
    monkeypatch.setenv("STUB_HANG", "6")
    monkeypatch.setenv("STUB_PLAN", "stamped,stamped")
    approve(project)
    with pytest.raises(StateError) as refused:
        kitupdate.apply(project["state"])
    message = str(refused.value)
    assert "was not left by the installer and was written by this command" in message, message
    assert os.path.exists(str(project["repo"] / kitupdate.HANDOVER_MARKER))


def test_an_aborted_update_is_not_reported_off_the_stamp_alone(project, monkeypatch):
    """The B4 window: the bundle is already the new kit's while the stamp still names the old one.

    Measured against the real scaffold with the child budget shortened to 1.6 s of a 3.4 s run:
    `.claude/hooks` and `.claude/kernel` were the staged kit's, `.claude/kit_version` still said
    2026.07.01-1 and `kit_state.json` still recorded the old bundle hash -- so every kernel-backed
    gate refused, and a message built on the stamp alone would have said the project still ran the
    old release. Both readings are in the refusal, and they disagree here.
    """
    monkeypatch.setattr(presets, "INSTALLER_TIMEOUT", 3)
    monkeypatch.setenv("STUB_HANG", "6")
    monkeypatch.setenv("STUB_PLAN", "bundle,bundle")
    approve(project)
    with pytest.raises(StateError) as refused:
        kitupdate.apply(project["state"])
    message = str(refused.value)
    assert "Nothing about the installation moved" not in message, message
    assert "stamp %s" % OLD in message, message
    assert "the enforcement bundle on disk is the STAGED kit's" in message, message
    assert kitupdate.UNREAD in message, message


def test_an_installer_that_refused_without_touching_anything_leaves_no_marker_and_can_be_retried(
        project, monkeypatch):
    """A project nothing happened to is not a project that has to restart -- MEASURED CHAIN.

    The other direction of the abort branch, and the sharper one: an over-alarming refusal is as
    wrong as a reassuring one, and here it was fatal. Measured against the real scaffold with a real
    approval and a typo in `project_config.yaml`'s preset -- a cause the PM can fix in-session
    through the kernel: the installer refused touching nothing, the command wrote the handover
    marker anyway, `gate_dispatch` then refused every spawn with "an installer changed this
    project's kit files" (false, by the reading this same command had just taken), the user-global
    guard closed the rest, and `assert_no_restart_is_pending` refused the RETRY. The session was
    dead over a typo.

    So: no marker on this branch, the message says so, and running the command again REALLY runs
    the installer again (the second plan verb is what proves it). Both assertions are on the state
    and on the witness, not on prose.
    """
    monkeypatch.setenv("STUB_PLAN", "exit,ok")
    approve(project)
    with pytest.raises(StateError) as refused:
        kitupdate.apply(project["state"])
    message = str(refused.value)
    assert "stub refused the install" in message
    assert "Nothing about the installation moved" in message, message
    assert "THE INSTALLATION HAD ALREADY MOVED" not in message, message
    assert "no restart marker was set" in message, message
    assert not os.path.exists(str(project["repo"] / kitupdate.HANDOVER_MARKER)), (
        "a run that changed nothing stopped the session anyway")
    assert _read(project["witness"]) == "exit", "the kernel started a second run over an intact tree"
    assert installed_version(project) == OLD

    # ...AND THE RETRY REALLY RUNS. Nothing was consumed: the same approval still covers the same
    # release pair, and the second attempt reaches the installer.
    assert kitupdate.apply(project["state"])["to"] == NEW
    assert _read(project["witness"]) == "ok"
    assert installed_version(project) == NEW


def test_a_refusal_that_did_leave_a_marker_says_so_rather_than_the_opposite(project, monkeypatch):
    """The other half of that reading: the branch reports the marker it FINDS, either way.

    Without this the sentence above could be a constant, and a constant is what this whole class of
    defect is made of. The stub raises the marker and then refuses without touching anything else,
    so the installation is unchanged AND the project is stopped -- the one combination in which the
    "no marker was set" sentence would be false.
    """
    monkeypatch.setenv("STUB_PLAN", "marker-only")
    approve(project)
    with pytest.raises(StateError) as refused:
        kitupdate.apply(project["state"])
    message = str(refused.value)
    assert "Nothing about the installation moved" in message, message
    assert "is in place, so this session is stopped either way" in message, message
    assert "no restart marker was set" not in message, message


# -- what the shipped texts may claim about that stop ---------------------------------------------
#
# A prose measurement, and it is allowed to be one: the subject IS the shipped text. What the code
# does is measured by `test_the_marker_this_command_leaves_really_stops_the_session` (the kit gate,
# as a process) -- and that test covers SPAWNS only, because that is all the kit builds.

# The shape the round shipped first, kept as the SPECIMEN the reader below is checked against. It
# exists nowhere in the tree any more, so quoting it claims nothing about another file.
_OVERCLAIM_SPECIMEN = ("the handover marker is set, so specialist spawns and further work-engine "
                       "commands are refused until the user restarts.")
def _stop_claims(text):
    """Sentences that claim MORE than a spawn refusal without naming the mechanism that would do it.

    THE CONDITION IS A PROPERTY, not a phrase: a claim about work-engine commands is honest exactly
    when the sentence names the HANDOVER GUARD, because that is the only thing in this harness that
    refuses them -- `handover guard` in prose, `handover_guard` as the file. "handover MARKER" is
    not it, and that is precisely the substitution the removed specimen made.

    Quotes and line breaks are flattened first: every site in a Python file wraps its sentence
    across string literals, so a per-line reader would cut the claim away from its condition (it
    did, on the two honest sites in `kitupdate.py`). And a sentence ends at a dot FOLLOWED BY
    SPACE, not at any dot -- `handover_guard.py` is one word, and splitting inside it cut the
    mechanism's name off the very claim it justifies.
    """
    flat = re.sub(r"\s+", " ", re.sub(r"[\"'`]", " ", text.replace(";", ".")))
    offenders = []
    for sentence in re.split(r"\.\s", flat):
        low = sentence.lower()
        if "refus" not in low:
            continue
        if "work-engine" not in low and "engine commands" not in low:
            continue
        if "handover guard" not in low and "handover_guard" not in low:
            offenders.append(sentence.strip())
    return offenders


def _texts_that_describe_the_stop():
    """(where, text) for every shipped file that tells a reader what the marker stops."""
    for kit in KITS:
        for relative in (os.path.join("constitution", "AGENTS.md"),
                         os.path.join("hooks", "session_status.py")):
            path = os.path.join(TEAM_KITS, kit, relative)
            yield "%s/%s" % (kit, relative.replace(os.sep, "/")), _read(path)
        for path in glob.glob(os.path.join(TEAM_KITS, kit, "skills", "*", "SKILL.md")):
            yield os.path.relpath(path, TEAM_KITS).replace(os.sep, "/"), _read(path)
    yield "kernel/cli.py", _read(os.path.join(TEAM_KITS, "kernel", "cli.py"))
    yield "kernel/kitupdate.py", _read(os.path.join(TEAM_KITS, "kernel", "kitupdate.py"))


def test_the_scoped_stop_sentence_is_the_one_every_kit_text_carries():
    """No shipped text may claim the KIT refuses work-engine commands -- it does not.

    MEASURED, which is why the sentence changed: with the marker in place, a `dispatch`, a `capture`
    and an `update-kit` line pass all eight of a kit's `Bash|PowerShell` gates rc 0. Only the
    USER-GLOBAL `~/.claude/hooks/handover_guard.py` refuses those, and `kernel/kitupdate.py`'s own
    docstring names that this file can be absent on a machine. So every site says what the kit
    builds (spawns) and names the guard as the condition for the rest.

    The reader is checked against a specimen of the sentence that was removed, so its silence
    cannot mean it stopped matching.
    """
    assert _stop_claims(_OVERCLAIM_SPECIMEN), (
        "the reader cannot see the sentence it was written for, so its silence proves nothing")
    offenders = ["%s: %s" % (where, sentence)
                 for where, text in _texts_that_describe_the_stop()
                 for sentence in _stop_claims(text)]
    assert not offenders, (
        "these shipped texts promise a refusal the kit does not build -- name the user-global "
        "handover guard as the condition, or claim only the spawn:\n  " + "\n  ".join(offenders))


# -- the marker really stops the session --------------------------------------------------------

def _hook(path, payload, cwd, env=None):
    return subprocess.run([sys.executable, "-B", path], input=json.dumps(payload),
                          capture_output=True, text=True, encoding="utf-8", errors="replace",
                          cwd=str(cwd), timeout=120,
                          env=dict(os.environ, CLAUDE_PROJECT_DIR=str(cwd),
                                   HARNESS_KERNEL_PATH=TEAM_KITS, **(env or {})))


@pytest.mark.parametrize("kit", KITS)
def test_the_marker_this_command_leaves_really_stops_the_session(tmp_path, kit):
    """The kit's OWN gate refuses a spawn while the marker stands -- in every kit, as a process.

    WHY THE KIT AND NOT ONLY THE GLOBAL GUARD: `~/.claude/hooks/handover_guard.py` refuses the same
    act, but it is a USER-global hook a project cannot see or install. After a kit update the
    session must stop whatever the machine's global settings look like, so `gate_dispatch` reads
    the marker too. Both directions, because a gate that refuses everything proves nothing: with
    the marker gone, THIS reason is gone from the refusal.
    """
    repo = tmp_path / kit
    _write(str(repo / "project_memory" / "project_config.yaml"), "project:\n  preset: solo\n")
    payload = {"hook_event_name": "PreToolUse", "tool_name": "Task", "cwd": str(repo),
               "tool_input": {"subagent_type": "backend-developer", "prompt": "no header"}}
    hook = os.path.join(TEAM_KITS, kit, "hooks", "gate_dispatch.py")

    _write(str(repo / ".claude" / "HANDOVER_PENDING"), "pending\n")
    stopped = _hook(hook, payload, repo)
    assert stopped.returncode == 2
    assert "HANDOVER_PENDING exists" in stopped.stderr, stopped.stderr

    os.remove(str(repo / ".claude" / "HANDOVER_PENDING"))
    after = _hook(hook, payload, repo)
    assert "HANDOVER_PENDING exists" not in after.stderr, after.stderr


@pytest.mark.parametrize("kit", KITS)
def test_every_marker_this_command_refuses_on_is_consumed_by_a_session_start(tmp_path, kit):
    """`RESTART_MARKERS` claims each entry is removed by a session start -- so run them.

    The claim is what makes the refusal honest ("end the session and start a new one" is only a
    remedy if a start really clears the marker). Measured by running the kit's SessionStart hooks
    as processes with `source: startup`, rather than by reading their source.
    """
    repo = tmp_path / kit
    _write(str(repo / "CLAUDE.md"), "<!-- agents-and-skills:team-kit %s -->\n" % kit)
    _write(str(repo / ".claude" / "kit_version"), _stamp(OLD, "a" * 64))
    for marker in kitupdate.RESTART_MARKERS:
        _write(str(repo / marker["path"]), "version: %s\n" % OLD)
    hooks = os.path.join(TEAM_KITS, kit, "hooks")
    for name in ("clear_handover_marker.py", "session_status.py"):
        _hook(os.path.join(hooks, name),
              {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(repo)}, repo,
              env={"USERPROFILE": str(tmp_path / "nohome"), "HOME": str(tmp_path / "nohome")})
    left = [marker["path"] for marker in kitupdate.RESTART_MARKERS
            if os.path.exists(str(repo / marker["path"]))]
    assert not left, "no SessionStart hook of the %s kit consumes %s" % (kit, left)


@pytest.mark.parametrize("kit", KITS)
def test_a_briefing_whose_kernel_is_unreachable_still_reports_the_kit_comparison(tmp_path, kit):
    """A kernel it cannot reach makes the briefing say so -- it does not make the paragraph vanish.

    THE REGRESSION THIS IS THE CORRECTION OF, measured in the suite: when the comparison moved into
    the kernel (FR-0006), the whole block was inside one `except` and a project without a reachable
    `.claude/kernel` lost the only sentence that tells a lead a newer release exists. That is the
    project that most needs one. So the unreachable case is a VERDICT (`_kernel.kit_update_verdict`
    → `unclear`), and what it may not do is claim a direction it did not measure.
    """
    repo = tmp_path / kit
    home = tmp_path / "home"
    _write(str(repo / "CLAUDE.md"), "<!-- agents-and-skills:team-kit %s -->\n" % kit)
    _write(str(repo / ".claude" / "kit_version"), _stamp(OLD, "a" * 64))
    _write(str(home / ".claude" / "team-kits" / kit / "VERSION"), _stamp(NEW, "b" * 64))
    result = subprocess.run(
        [sys.executable, "-B", os.path.join(TEAM_KITS, kit, "hooks", "session_status.py")],
        input=json.dumps({"hook_event_name": "SessionStart", "cwd": str(repo)}),
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(repo),
        timeout=120,
        # no HARNESS_KERNEL_PATH and no `.claude/kernel`: the kernel really is out of reach
        env={key: value for key, value in
             dict(os.environ, CLAUDE_PROJECT_DIR=str(repo), HOME=str(home),
                  USERPROFILE=str(home)).items() if key != "HARNESS_KERNEL_PATH"})
    briefing = json.loads(result.stdout.strip().splitlines()[-1])[
        "hookSpecificOutput"]["additionalContext"]
    assert "KIT VERSION MISMATCH" in briefing, briefing
    assert "could not be reached" in briefing, briefing
    assert "KIT UPDATE AVAILABLE" not in briefing, "a direction was claimed that nothing measured"


@pytest.mark.parametrize("kit", KITS)
def test_the_briefing_offers_the_command_and_not_the_dead_end(tmp_path, kit):
    """What the lead reads when an update is staged: the two commands, not "ask the user to run".

    A prose measurement of a RUNNING hook: the briefing is generated by a real `session_status.py`
    process over a project pinned to an older stamp, and what it may not contain is the sentence
    V2's gate hardening left behind (FR-0006) -- because a lead that reads it sends the user to a
    terminal instead of installing the update itself.
    """
    repo = tmp_path / kit
    home = tmp_path / "home"
    _write(str(repo / "CLAUDE.md"), "<!-- agents-and-skills:team-kit %s -->\n" % kit)
    _write(str(repo / ".claude" / "kit_version"), _stamp(OLD, "a" * 64))
    _write(str(home / ".claude" / "team-kits" / kit / "VERSION"), _stamp(NEW, "b" * 64))
    result = _hook(os.path.join(TEAM_KITS, kit, "hooks", "session_status.py"),
                   {"hook_event_name": "SessionStart", "cwd": str(repo)}, repo,
                   env={"USERPROFILE": str(home), "HOME": str(home)})
    briefing = json.loads(result.stdout.strip().splitlines()[-1])[
        "hookSpecificOutput"]["additionalContext"]
    assert "KIT UPDATE AVAILABLE" in briefing
    assert kitupdate.COMMAND in briefing and kitupdate.KIND in briefing
    assert "ASK THE USER TO RUN" not in briefing, briefing
    assert "You cannot run either yourself" not in briefing, briefing


# -- end to end ---------------------------------------------------------------------------------

def _scaffolded(tmp_path, kit="dev-team"):
    """A REAL project: this repo's kits staged in a fake home, installed by the real scaffold."""
    home = tmp_path / "home"
    staging = home / ".claude" / "team-kits"
    shutil.copytree(TEAM_KITS, str(staging), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    repo = tmp_path / "project"
    source = os.path.join(str(staging), kit, "templates", "project_memory",
                          "project_config.yaml")
    config = _read(source).replace('name: ""', 'name: "Rechnungswerkzeug"').replace(
        "stacks: [TODO]", "stacks: [python]")
    _write(str(repo / "project_memory" / "project_config.yaml"), config)
    environment = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         os.path.join(str(staging), "scaffold_team.ps1"), "-Team", kit],
        cwd=str(repo), capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=900, env=environment)
    assert result.returncode == 0, result.stdout + result.stderr
    return home, repo, environment


def _harness(repo, environment, *argv):
    return subprocess.run([sys.executable, "-B", os.path.join(str(repo), "scripts", "harness.py")]
                          + list(argv), cwd=str(repo), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=900, env=environment)


def _fingerprint(root):
    seen = {}
    for directory, dirnames, filenames in os.walk(str(root)):
        dirnames[:] = [name for name in dirnames if name != "__pycache__"]
        for name in filenames:
            path = os.path.join(directory, name)
            with open(path, "rb") as handle:
                seen[os.path.relpath(path, str(root))] = handle.read()
    return seen


def test_a_lead_can_update_the_kit_end_to_end(tmp_path):
    """FR-0006 walked to the end with nothing stubbed: the real kit, scaffold, entry point and hook.

    The project is scaffolded and then pinned to an OLDER stamp, which is what a project looks like
    when a newer harness has been installed on the machine. The lead asks, the user answers the
    question the kernel composed, the lead runs ONE command, and the release moves -- with
    `project_memory/` byte-identical throughout, which is the promise the old flow made in prose.
    """
    if os.name != "nt" or not shutil.which("powershell"):
        pytest.skip("the scaffold's PowerShell twin runs on Windows")
    pytest.importorskip("yaml")
    home, repo, environment = _scaffolded(tmp_path)
    staged = _read(str(home / ".claude" / "team-kits" / "dev-team" / "VERSION"))
    _write(str(repo / ".claude" / "kit_version"), _stamp(OLD, "a" * 64))
    os.remove(str(repo / ".claude" / "HANDOVER_PENDING"))   # what a real restart would clear
    before = _fingerprint(repo / "project_memory")

    opened = _harness(repo, environment, "request-approval", kitupdate.KIND)
    assert opened.returncode == 0, opened.stderr
    question = json.loads(opened.stdout)
    assert OLD in question["question"] and kitupdate.identity(staged)["version"] in \
        question["question"], question["question"]

    payload = {"hook_event_name": "PostToolUse", "tool_name": "AskUserQuestion", "cwd": str(repo),
               "tool_input": {"questions": [question]},
               "tool_response": {"answers": {question["question"]: question["options"][0]["label"]},
                                 "questions": [question]}}
    minted = _hook(os.path.join(str(repo), ".claude", "hooks", "gate_approval.py"), payload, repo,
                   env={"HOME": str(home), "USERPROFILE": str(home)})
    assert "recorded for %s" % kitupdate.KIND in minted.stderr, minted.stderr + minted.stdout

    applied = _harness(repo, environment, kitupdate.COMMAND)
    assert applied.returncode == 0, applied.stderr
    assert "RESTART REQUIRED" in applied.stdout
    assert "the enforcement bundle on disk is the STAGED kit's" in applied.stdout
    assert _read(str(repo / ".claude" / "kit_version")) == staged
    assert os.path.exists(str(repo / kitupdate.HANDOVER_MARKER))
    assert _fingerprint(repo / "project_memory") != before, "the approval was not recorded at all"
    canonical = {name: body for name, body in _fingerprint(repo / "project_memory").items()
                 if not name.startswith("approvals") and not name.startswith("generated")
                 and ".audit" not in name}
    assert canonical == {name: body for name, body in before.items()
                         if not name.startswith("approvals") and not name.startswith("generated")
                         and ".audit" not in name}, "the installer touched project state"


# -- the bootstrap for a stock that predates this command (BUG-0059) -----------------------------

BRIDGE = os.path.join(ROOT, "user", "bridge", "update_kit.py")
NOTICE = os.path.join(ROOT, "user", "claude", "hooks", "kit_bridge_notice.py")


def _load_bridge():
    """The shipped bootstrap, imported by path -- it installs outside any package."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("_bridge_under_test", BRIDGE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _notice(repo, home):
    """The global notice as a process, in the environment a real session gives it.

    NOT `_hook`, and the difference is the measurement: that helper exports
    `HARNESS_KERNEL_PATH`, which makes a project's entry point resolve THIS repo's kernel instead
    of its own -- so an old stock would answer `update-kit --help` with exit 0 and the notice would
    correctly stay silent about a route the project does not have.
    """
    return subprocess.run(
        [sys.executable, "-B", NOTICE],
        input=json.dumps({"hook_event_name": "SessionStart", "source": "startup",
                          "cwd": str(repo)}),
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(repo),
        timeout=300,
        env={key: value for key, value in
             dict(os.environ, CLAUDE_PROJECT_DIR=str(repo), HOME=str(home),
                  USERPROFILE=str(home)).items() if key != "HARNESS_KERNEL_PATH"})


def _run_bridge(repo, environment):
    return subprocess.run([sys.executable, "-B", BRIDGE], cwd=str(repo), capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=900,
                          env=environment)


def _make_it_old_stock(repo):
    """The one property that defines the stock this bootstrap is for: no `update-kit` on ITS surface.

    Taken by deleting the modules `2026.08.14-9` never had (`kitupdate`, `presets`) rather than by
    editing a parser, so the entry point answers the way that release's really answered -- measured
    against a real install of it, rebuilt from this repo's own history: exit 2 on
    `update-kit --help`, while `.claude/kernel/` held neither module.
    """
    for name in ("kitupdate.py", "presets.py"):
        path = os.path.join(str(repo), ".claude", "kernel", name)
        if os.path.exists(path):
            os.remove(path)


def test_the_bridge_reads_the_route_off_the_projects_own_entry_point(tmp_path):
    """`has_the_approved_route` asks the PARSER, and all three of its answers are measured.

    Not the presence of `.claude/kernel/kitupdate.py`: a copied module is not a command on the
    surface, and the surface is what a lead types. True on a project this repo's scaffold installed,
    False once the modules that release never had are gone, None where there is no entry point at
    all -- the third is its own answer because "no surface to ask" is not "asked and told no".
    """
    if os.name != "nt" or not shutil.which("powershell"):
        pytest.skip("the scaffold's PowerShell twin runs on Windows")
    _home, repo, _environment = _scaffolded(tmp_path)
    bridge = _load_bridge()
    assert bridge.has_the_approved_route(str(repo), kitupdate.COMMAND) is True
    _make_it_old_stock(repo)
    assert bridge.has_the_approved_route(str(repo), kitupdate.COMMAND) is False
    os.remove(os.path.join(str(repo), "scripts", "harness.py"))
    assert bridge.has_the_approved_route(str(repo), kitupdate.COMMAND) is None


def test_the_bridge_refuses_a_project_that_can_reach_the_approved_route(tmp_path):
    """The refusal that keeps this a bootstrap rather than a back door.

    The bootstrap mints nothing and reads no approval, so the one thing it may not be is an
    alternative to `update-kit`. The project here is BEHIND (so the direction is not what refuses)
    and carries the command -- and the refusal names the route that asks the user.
    """
    if os.name != "nt" or not shutil.which("powershell"):
        pytest.skip("the scaffold's PowerShell twin runs on Windows")
    _home, repo, environment = _scaffolded(tmp_path)
    _write(str(repo / ".claude" / "kit_version"), _stamp(OLD, "a" * 64))
    os.remove(str(repo / kitupdate.HANDOVER_MARKER))
    refused = _run_bridge(repo, environment)
    assert refused.returncode != 0, refused.stdout
    assert kitupdate.COMMAND in refused.stderr and kitupdate.KIND in refused.stderr, refused.stderr
    assert _read(str(repo / ".claude" / "kit_version")).startswith("version: %s" % OLD), (
        "the bootstrap installed over a project that had the approved route")


def test_a_stock_without_update_kit_is_lifted_by_the_bootstrap_and_told_about_it(tmp_path):
    """BUG-0059 end to end: the lift a 2026.08.14-9 project cannot perform for itself.

    ONE project, both halves, because they are one chain: the global SessionStart notice is what
    tells that project's lead the bootstrap exists (its own briefing cannot -- it shipped with the
    release that had no command), and the bootstrap is what performs the lift. Both run as
    processes, against a project this repo's scaffold really installed and then stripped of the two
    kernel modules that release never had.

    WHAT THE SUITE CANNOT MEASURE, named rather than implied: that the provider merges a
    USER-GLOBAL SessionStart hook into a session of a project that registers its own. That is
    provider behaviour (`tools/provider_observations.json`), and it is why the bootstrap adds a
    route without removing the one the old briefing describes.
    """
    if os.name != "nt" or not shutil.which("powershell"):
        pytest.skip("the scaffold's PowerShell twin runs on Windows")
    pytest.importorskip("yaml")
    home, repo, environment = _scaffolded(tmp_path)
    staged = _read(str(home / ".claude" / "team-kits" / "dev-team" / "VERSION"))
    os.makedirs(str(home / "agents-and-skills"), exist_ok=True)
    shutil.copy(BRIDGE, str(home / "agents-and-skills" / "update_kit.py"))
    _write(str(repo / ".claude" / "kit_version"), _stamp(OLD, "a" * 64))
    os.remove(str(repo / kitupdate.HANDOVER_MARKER))   # what a real restart would have cleared
    before = _fingerprint(repo / "project_memory")

    # ...with the command on its surface the notice says nothing: that project's own briefing
    # offers the approved route, and a second voice there would be noise on a correct state.
    quiet = _notice(repo, home)
    assert quiet.returncode == 0 and not quiet.stdout.strip(), quiet.stdout

    _make_it_old_stock(repo)
    spoken = _notice(repo, home)
    briefing = json.loads(spoken.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "update_kit.py" in briefing and kitupdate.COMMAND in briefing, briefing

    lifted = _run_bridge(repo, environment)
    assert lifted.returncode == 0, lifted.stderr + lifted.stdout
    assert "RESTART REQUIRED" in lifted.stdout, lifted.stdout
    assert _read(str(repo / ".claude" / "kit_version")) == staged
    assert os.path.exists(str(repo / kitupdate.HANDOVER_MARKER)), (
        "the session was not stopped after its kit changed underneath it")
    assert _fingerprint(repo / "project_memory") == before, "the bootstrap touched project state"

    # ...and afterwards the project has the approved route, so the notice goes quiet again.
    silent = _notice(repo, home)
    assert not silent.stdout.strip(), silent.stdout


def test_the_notice_is_registered_globally_with_a_timeout_and_its_file_is_shipped():
    """A hook the user's global settings do not register runs nowhere -- and one with no timeout is
    a hook the host may kill mid-decision, which for this one means a lead that never hears about
    the bootstrap. Read off the shipped settings, the file the installer merges into the user's."""
    with open(os.path.join(ROOT, "user", "claude", "settings.json"), encoding="utf-8") as handle:
        settings = json.load(handle)
    entries = [hook for group in settings["hooks"].get("SessionStart", [])
               for hook in group.get("hooks", [])]
    named = [hook for hook in entries if os.path.basename(NOTICE) in hook.get("command", "")]
    assert named, "the global settings register no SessionStart hook for %s" % NOTICE
    assert all(hook.get("timeout") for hook in named), named
    assert os.path.isfile(NOTICE)


def _gate(repo, command, kit="dev-team"):
    """The kit's own write-scope gate, as a process, on one command line."""
    payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "cwd": str(repo),
               "tool_input": {"command": command}}
    return subprocess.run(
        [sys.executable, "-B", os.path.join(TEAM_KITS, kit, "hooks", "gate_write_scope.py")],
        input=json.dumps(payload), capture_output=True, text=True, encoding="utf-8",
        errors="replace", cwd=str(repo), timeout=120,
        env=dict(os.environ, CLAUDE_PROJECT_DIR=str(repo), HARNESS_KERNEL_PATH=TEAM_KITS))


def test_the_installer_puts_the_bootstrap_where_a_locked_down_project_can_still_start_it(tmp_path):
    """WHERE the bootstrap lives is the whole of why it works, so both halves are measured together.

    `gate_write_scope` refuses a write-capable command line that NAMES `.claude` or `team-kits` --
    which is why a project one release behind cannot start the installer itself, and why a
    bootstrap installed under either name would be equally unreachable. The installer therefore
    places it outside both, and this test measures that against the gate that runs: the line
    starting the bootstrap passes, the line starting the scaffold does not.

    Measured by hand once, against a real `2026.08.14-9` install rebuilt from this repo's history
    (that release's own gate, every hook its settings register on `Bash`): exit 0 for the bootstrap
    line, exit 2 for the scaffold. What runs here is today's gate over today's installed path, so a
    release that starts protecting that directory breaks this rather than the pilot.
    """
    if os.name != "nt" or not shutil.which("powershell"):
        pytest.skip("the PowerShell installer runs on Windows")
    home = tmp_path / "home"
    pythonpath = os.pathsep.join(path for path in sys.path if path)
    installed = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         os.path.join(ROOT, "install.ps1"), "-Target", "claude", "-Force"],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=900, env=dict(os.environ, USERPROFILE=str(home), HOME=str(home),
                              CODEX_HOME=str(tmp_path / "codex"), PYTHONPATH=pythonpath))
    assert installed.returncode == 0, installed.stdout + installed.stderr
    bootstrap = home / "agents-and-skills" / "update_kit.py"
    assert bootstrap.is_file(), (
        "the installer registers a notice that names %s and did not place it" % bootstrap)

    repo = tmp_path / "project"
    _write(str(repo / ".claude" / "kit_version"), _stamp(OLD, "a" * 64))
    passes = _gate(repo, 'python "%s"' % bootstrap)
    assert passes.returncode == 0, (
        "the bootstrap cannot be started in a project at all:\n%s" % passes.stderr)
    refused = _gate(repo, 'powershell -File "%s" -Team dev-team'
                    % (home / ".claude" / "team-kits" / "scaffold_team.ps1"))
    assert refused.returncode == 2, (
        "the installer line is no longer refused, so the bootstrap's whole reason is gone:\n%s"
        % refused.stdout)


def test_the_posix_installer_places_the_bootstrap_too(tmp_path):
    """The twin, because a user on POSIX gets the same notice naming the same file."""
    if os.name == "nt" or not shutil.which("bash"):
        pytest.skip("POSIX installer integration runs on Unix CI")
    home = tmp_path / "home"
    home.mkdir()
    pythonpath = os.pathsep.join(path for path in sys.path if path)
    installed = subprocess.run(
        ["bash", os.path.join(ROOT, "install.sh"), "--target", "claude", "--force"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=900,
        env=dict(os.environ, HOME=str(home), PYTHONPATH=pythonpath))
    assert installed.returncode == 0, installed.stdout + installed.stderr
    assert (home / "agents-and-skills" / "update_kit.py").is_file(), installed.stdout


# -- BUG-0068: the repo-template refresh must not dead-end the user or overstate divergence --------

KIT_OWNED_MANIFEST = os.path.join(TEAM_KITS, "repo_kit_owned.txt")


def _owned_repo_scripts():
    """The repo paths the scaffold OWNS (always overwrites) -- the manifest both scaffold twins read."""
    owned = set()
    with open(KIT_OWNED_MANIFEST, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line and not line.startswith("#"):
                owned.add(line)
    return owned


TRANSIENT_TEMPLATE_DIRS = ("__pycache__", ".ruff_cache", ".mypy_cache", ".pytest_cache")


def _repo_templates(kit):
    """Every file `<kit>/templates/repo` ships, repo-relative -- what a scaffold places in a project.

    The transient directories both scaffold twins prune are pruned here too, for the same reason:
    nothing ships them, so nothing may demand anything of them.
    """
    base = os.path.join(TEAM_KITS, kit, "templates", "repo")
    for directory, dirnames, filenames in os.walk(base):
        dirnames[:] = [name for name in dirnames if name not in TRANSIENT_TEMPLATE_DIRS]
        for name in filenames:
            yield os.path.relpath(os.path.join(directory, name), base).replace(os.sep, "/")


def _guard_refuses(kit, repo, rel):
    """Does THIS kit's `guard_harness_selfmod` refuse a tool write to `rel` in an installed project?

    ASKED OF THE PROCESS, not of a constant: the guard decides on FOUR sources at once
    (`BLOCKED_REPO_PATHS`, `BLOCKED_PROVIDER_PREFIXES`, `BLOCKED`, `BLOCKED_FILES`) plus the
    constitution pair, and a reader that parsed one of them answered for one of them. Measured: a
    repo template at `templates/repo/.codex/notes.md` is refused (rc 2, "part of the ENFORCEMENT
    LAYER") while a `BLOCKED_REPO_PATHS` reader saw nothing -- the enumeration-instead-of-property
    shape this round removed on the manifest side, still standing on the test side.
    """
    payload = {"tool_name": "Write", "cwd": str(repo),
               "tool_input": {"file_path": os.path.join(str(repo), *rel.split("/"))}}
    result = subprocess.run(
        [sys.executable, "-B", os.path.join(TEAM_KITS, kit, "hooks", "guard_harness_selfmod.py")],
        input=json.dumps(payload), capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=120, env=dict(os.environ, CLAUDE_PROJECT_DIR=str(repo)))
    return result.returncode == 2


def test_every_guarded_repo_template_is_refreshed_by_the_scaffold(tmp_path):
    """A repo template the guard refuses in-session writes to MUST be scaffold-owned (BUG-0068).

    Otherwise a kit fix to it reaches the project by NO route: the PM may not merge it, copy-if-absent
    keeps the fork forever, and the pending list hands the non-developer user `cp` lines for a file
    nobody in the session may write -- the ledger judge, measured live on the real BuyPlugGo update.

    THE SUBJECT IS EVERY SHIPPED REPO TEMPLATE, asked of the RUNNING guard, because "guarded" is a
    property of that guard's whole decision and not of one of its four constants. A file only this
    kit ships is only this kit's question, so the walk is per kit; the owned set is DATA
    (`team-kits/repo_kit_owned.txt`, read by both scaffold twins).

    The floor is here for the reason every derived reader in this repo carries one: zero refusals
    would mean the payload stopped reaching the guard, not that nothing is guarded. Measured today:
    39 templates across the three kits, 2.9 s, four of them refused.
    """
    owned = _owned_repo_scripts()
    (tmp_path / ".claude").mkdir(parents=True)      # what `_root.find_repo_root` anchors on
    refused = []
    for kit in KITS:
        for rel in _repo_templates(kit):
            if not _guard_refuses(kit, tmp_path, rel):
                continue
            refused.append((kit, rel))
            assert rel in owned, (
                "%s guards %s from in-session writes but the scaffold does not own it, so a kit fix "
                "to it reaches the project by no route (BUG-0068). Add it to %s."
                % (kit, rel, os.path.relpath(KIT_OWNED_MANIFEST, ROOT)))
    assert len(refused) >= 2, (
        "only %s were refused; the reader stopped reaching the guard rather than finding nothing "
        "guarded" % refused)


def test_a_guarded_script_is_refreshed_and_a_line_ending_drift_is_not_pending(tmp_path):
    """BUG-0068 end to end on a REAL office scaffold: both live defects, in one re-scaffold.

    Restores both in a copy: the project's `scripts/ledger_add.py` is forked (a content change no
    in-session route may make, which the old flow handed the user as `cp` lines) and a copy-if-absent
    script is drifted to CRLF (content-identical, which the byte differ read as 'differs' and put on
    the pending list). The re-scaffold must overwrite the guarded judge back to the kit's copy and
    leave NEITHER file on `.claude/kit_update_pending.repo`.

    Red without the fix: the judge stays forked (copy-if-absent) and the CRLF drift is listed.
    """
    if os.name != "nt" or not shutil.which("powershell"):
        pytest.skip("the scaffold's PowerShell twin runs on Windows")
    pytest.importorskip("yaml")
    home, repo, environment = _scaffolded(tmp_path, kit="office-team")
    template = (home / ".claude" / "team-kits" / "office-team" / "templates" / "repo" / "scripts")
    judge = repo / "scripts" / "ledger_add.py"
    drifted = repo / "scripts" / "euer_report.py"
    # a real fork of the guarded judge -- a change no in-session route may make
    with open(judge, "a", encoding="utf-8") as handle:
        handle.write("\n# LOCAL FORK\n")
    # a copy-if-absent script drifted to CRLF: content-identical, bytes differ
    drifted.write_bytes(drifted.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))

    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         os.path.join(str(home / ".claude" / "team-kits"), "scaffold_team.ps1"),
         "-Team", "office-team"],
        cwd=str(repo), capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=900, env=environment)
    assert result.returncode == 0, result.stdout + result.stderr

    # the guarded judge is refreshed to the kit's copy -- the sanctioned installer route, fork gone
    assert judge.read_bytes().replace(b"\r\n", b"\n") == \
        (template / "ledger_add.py").read_bytes().replace(b"\r\n", b"\n")
    assert b"LOCAL FORK" not in judge.read_bytes()

    # THE ENTRIES, not the file's TEXT: the pending header names `scripts/ledger_add.py` itself, as
    # the example of what never lands on such a list, so a substring test over the whole file held
    # only while the fixture produced no pending file at all. Measured: with one real divergence in
    # the tree the ledger assertion was False although the judge WAS correctly refreshed, and in the
    # EOL-only red tree the test failed on that line instead of on `euer_report.py` -- a red
    # pointing at the wrong defect. `pending_entries` is the reader this round introduced for it.
    pending = str(repo / ".claude" / "kit_update_pending.repo")
    listed = kitupdate.pending_entries(pending)
    assert "scripts/ledger_add.py" not in listed, listed   # guarded -> refreshed, never pending
    assert "scripts/euer_report.py" not in listed, listed  # CRLF-only drift is not a divergence


def _session_start(repo, home):
    """The kit's OWN installed `session_status.py`, as the process a real session start runs.

    The project's staging is the fake HOME's, because that is where the kernel looks for the kit
    template an entry must be re-checked against (`presets.staging_root`).
    """
    return _hook(os.path.join(str(repo), ".claude", "hooks", "session_status.py"),
                 {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(repo)},
                 repo, env={"HOME": str(home), "USERPROFILE": str(home)})


def test_a_pending_entry_that_matches_again_stops_nagging_and_a_resolved_list_goes(tmp_path):
    """The merge backlog is re-validated against the tree, not believed as written (BUG-0068).

    THE MEASURED CASE, on the user's real office project 2026-08-26: `kit_update_pending.repo` named
    four scripts that were RAW byte-identical to the installed template, three with mtimes older than
    the update -- and the nag fired every session until a PM deleted the file by hand, which is how a
    non-developer user ends up in the terminal for files that already match.

    BOTH DIRECTIONS, because a reader that reports nothing proves nothing: an entry whose file really
    still differs must go on nagging, and the list must survive while it does. Only when every entry
    matches again does the nag fall silent and the file go.

    Red without the fix: the matching entries are reported and the file stays, in both halves.
    """
    if os.name != "nt" or not shutil.which("powershell"):
        pytest.skip("the scaffold's PowerShell twin runs on Windows")
    pytest.importorskip("yaml")
    home, repo, _ = _scaffolded(tmp_path, kit="office-team")
    template = home / ".claude" / "team-kits" / "office-team" / "templates" / "repo"
    pending = repo / ".claude" / "kit_update_pending.repo"
    really = repo / "requirements-office.txt"
    drifted = repo / "scripts" / "proc_hash.py"

    # one entry that really differs, one untouched (matches), one that differs only in line endings
    with open(really, "a", encoding="utf-8") as handle:
        handle.write("local-extra-package==1.0\n")
    drifted.write_bytes(drifted.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    _write(str(pending), "# written by an installer run\n- requirements-office.txt\n"
                         "- scripts/euer_report.py\n- scripts/proc_hash.py\n")

    nagging = _session_start(repo, home)
    assert "KIT MERGE BACKLOG" in nagging.stdout, nagging.stdout + nagging.stderr
    assert "requirements-office.txt" in nagging.stdout          # really differs -> still nags
    assert "euer_report.py" not in nagging.stdout               # matches the template -> dropped
    assert "proc_hash.py" not in nagging.stdout                 # line endings only -> dropped
    assert pending.is_file(), "a list with work left in it must survive"
    # ...and here the assurance IS earned: every entry was held against a readable template
    assert "Each entry was re-checked" in nagging.stdout, nagging.stdout

    # ...and once the one real divergence is merged, the whole list is resolved
    shutil.copyfile(str(template / "requirements-office.txt"), str(really))
    quiet = _session_start(repo, home)
    assert "KIT MERGE BACKLOG" not in quiet.stdout, quiet.stdout
    assert not pending.exists(), "a list with nothing left in it is the nag, so it goes"


def test_a_backlog_that_could_not_be_re_checked_says_so(tmp_path):
    """With no staged kit to compare against, the nag must NOT sign itself "re-checked" (BUG-0068).

    THE MEASURED FALSE CLAIM: hanging the assurance on "the kernel answered" rather than on "a
    comparison happened" printed `Each entry was re-checked against the kit template` over a project
    whose staged kit is not on this machine -- naming two files as diverging that are RAW
    byte-identical to the kit template, with nothing opened to decide it. That is the BUG-0068
    symptom plus an assurance the round before this one did not even make, and by this hook's own
    instruction it lands in the FIRST paragraph of the reply to a non-technical user.

    TWO WAYS TO LOSE THE COMPARISON, both real and both measured here: the staged kit is gone (a
    second machine, a project synced through OneDrive, or simply before the harness install), and
    the ownership manifest that says WHICH kit this is cannot be read. The entries must still be
    reported -- losing the backlog is the other failure -- and the sentence must say it did not
    check them.
    """
    if os.name != "nt" or not shutil.which("powershell"):
        pytest.skip("the scaffold's PowerShell twin runs on Windows")
    pytest.importorskip("yaml")
    home, repo, _ = _scaffolded(tmp_path, kit="office-team")
    pending = repo / ".claude" / "kit_update_pending.repo"
    # both entries are UNTOUCHED, so with a readable staging both would be dropped as matching
    _write(str(pending), "# written by an installer run\n"
                         "- scripts/euer_report.py\n- scripts/proc_hash.py\n")

    staged = home / ".claude" / "team-kits" / "office-team"
    shutil.rmtree(str(staged))
    gone = _session_start(repo, home)
    assert "KIT MERGE BACKLOG" in gone.stdout, gone.stdout + gone.stderr
    assert "euer_report.py" in gone.stdout, "the backlog must not be lost when it cannot be checked"
    assert "NOT re-checked here" in gone.stdout, gone.stdout
    assert "Each entry was re-checked" not in gone.stdout, gone.stdout
    assert pending.is_file(), "an unjudged list must never be deleted"

    # ...and the same when it is the OWNERSHIP MANIFEST that cannot be read: which kit's templates
    # these entries belong to is then unknown, so nothing can be compared either.
    shutil.copytree(str(home / ".claude" / "team-kits" / "dev-team"), str(staged),
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    os.remove(str(repo / ".claude" / "team_kit_roles.txt"))
    unknown = _session_start(repo, home)
    assert "KIT MERGE BACKLOG" in unknown.stdout, unknown.stdout + unknown.stderr
    assert "NOT re-checked here" in unknown.stdout, unknown.stdout
    assert "Each entry was re-checked" not in unknown.stdout, unknown.stdout


def _deny_read(path, allow=False):
    """Deny (or restore) READ on `path` for the current user -- the narrowest real unreadable file.

    An ACL denial is the reachable shape the fix is for: the same state a locked file or a OneDrive
    placeholder that is not hydrated presents to `open()`, and the user's real project lives in
    OneDrive. `icacls` rather than a chmod, because on Windows the read bit is an ACE.

    `RD` (read DATA) and not the simple right `R`: `R` also denies READ_CONTROL, after which icacls
    cannot read the DACL to take the deny back off -- measured `Zugriff verweigert`, rc 5, on a file
    under `%TEMP%`, where the inherited grant is Modify and carries no WRITE_DAC of its own. `RD` is
    also the narrower statement: what this test needs is a file `open()` refuses, nothing more.
    """
    who = "{}\\{}".format(os.environ.get("USERDOMAIN", ""), os.environ.get("USERNAME", ""))
    argv = ["icacls", str(path)] + (["/remove:d", who] if allow else ["/deny", "%s:(RD)" % who])
    # CHECKED, because an ACL command that quietly did nothing turns this whole test into air --
    # and in the other direction leaves a denied file behind for pytest's own cleanup to trip on.
    result = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=120)
    assert result.returncode == 0, (argv, result.stdout, result.stderr)


def test_a_pending_list_that_cannot_be_read_is_never_called_resolved(tmp_path):
    """A list that EXISTS and cannot be opened is unknown -- not empty, not resolved, not deleted.

    THE DEFECT THIS ROUND INTRODUCED, and the expensive direction of it: `pending_entries` answered
    `[]` for "no such file" AND for "could not be read", so a genuinely unmerged backlog behind an
    ACL denial came back with zero entries, the caller read that as "nothing left to merge", and the
    hook DELETED the file -- the kit fix dropped out together with the record of it. Before the
    re-validation existed the same denial produced no nag either, but the file SURVIVED, so this was
    a regression rather than an old hole.

    BOTH DIRECTIONS, because a reader that never deletes proves nothing: the readable list that
    really is resolved must still go.
    """
    if os.name != "nt" or not shutil.which("powershell"):
        pytest.skip("the scaffold's PowerShell twin runs on Windows")
    pytest.importorskip("yaml")
    home, repo, _ = _scaffolded(tmp_path, kit="office-team")
    template = home / ".claude" / "team-kits" / "office-team" / "templates" / "repo"
    pending = repo / ".claude" / "kit_update_pending.repo"
    diverged = repo / "scripts" / "euer_report.py"

    # a GENUINE unmerged divergence, so a deletion here really would lose a kit fix
    with open(diverged, "a", encoding="utf-8") as handle:
        handle.write("\n# project fork\n")
    _write(str(pending), "# written by an installer run\n- scripts/euer_report.py\n")

    _deny_read(pending)
    try:
        with pytest.raises(OSError):
            open(str(pending), "rb").close()   # the denial really denies, or this test measures air
        denied = _session_start(repo, home)
        assert pending.is_file(), "an unreadable list was DELETED -- the backlog is gone with it"
        assert "UNREADABLE" in denied.stdout, denied.stdout + denied.stderr
        assert "kit_update_pending.repo" in denied.stdout, denied.stdout
        # ...and nothing anywhere in the briefing may call it resolved
        assert "already match" not in denied.stdout, denied.stdout
        assert "Each entry was re-checked" not in denied.stdout, denied.stdout
    finally:
        _deny_read(pending, allow=True)

    # COUNTER-DIRECTION: readable again and really resolved -> the list still goes
    with open(str(pending), "rb") as handle:      # the restore restored, or the rest measures air
        handle.read()
    shutil.copyfile(str(template / "scripts" / "euer_report.py"), str(diverged))
    quiet = _session_start(repo, home)
    assert "KIT MERGE BACKLOG" not in quiet.stdout, quiet.stdout
    assert not pending.exists(), "a readable, resolved list must still be deleted"
