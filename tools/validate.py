#!/usr/bin/env python3
"""
validate.py — structural self-check for the agents-and-skills repo (dogfooding).

Compiles every shipped hook/script, parses every YAML (templates, registry, agent + skill frontmatter)
and JSON (kit settings), and checks the wiring: each agent's `skills:` resolve to a skill dir, and every
registry role has an agent file. Exit 1 on any failure. Run locally or in CI: python tools/validate.py
"""
import glob
import json
import os
import sys

import yaml

# The in-memory compile below states the rule ("validation must never create __pycache__ that the
# installer could accidentally carry into the shared team-kit staging tree") and this script broke it
# with the imports it really performs: `preset_config` and `kernel.hashing` come from `team-kits/`, so
# every run left `team-kits/__pycache__` and `team-kits/kernel/__pycache__` behind — measured. A
# one-shot validator gains nothing from a bytecode cache, so it writes none.
sys.dont_write_bytecode = True

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "team-kits"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from preset_config import UniqueKeyLoader, load_preset_catalog  # noqa: E402
import lead_package  # noqa: E402  — the budget and its subject, defined once

fails = []
# Budgets that are MEASURED now and become failures in a later phase, so the number is visible
# while the work that fixes it is still ahead (spec II.5 Kuerzungs-Sequenz: cut only AFTER the
# replacing gates exist). A warning channel keeps the measuring stick honest without adding red
# that nobody can act on yet.
warns = []


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def frontmatter(text):
    if not text.startswith("---"):
        return None
    return yaml.load(text.split("---", 2)[1], Loader=UniqueKeyLoader)


# 1) compile python
for p in glob.glob(ROOT + "/team-kits/*.py") + \
         glob.glob(ROOT + "/team-kits/**/hooks/*.py", recursive=True) + \
         glob.glob(ROOT + "/team-kits/**/templates/repo/scripts/*.py", recursive=True) + \
         glob.glob(ROOT + "/tools/*.py"):
    try:
        # Compile in memory: validation must never create __pycache__ that the installer could
        # accidentally carry into the shared team-kit staging tree.
        compile(open(p, "rb").read(), p, "exec")
    except Exception as e:
        fails.append("compile %s: %s" % (rel(p), e))

# 2) parse YAML (templates + registry)
for p in glob.glob(ROOT + "/team-kits/**/templates/project_memory/*.yaml", recursive=True) + \
         [ROOT + "/team-kits/registry.yaml"]:
    try:
        yaml.load(open(p, encoding="utf-8").read(), Loader=UniqueKeyLoader)
    except Exception as e:
        fails.append("yaml %s: %s" % (rel(p), e))

# 3) parse kit settings.json
for p in glob.glob(ROOT + "/team-kits/*/settings/settings.json"):
    try:
        json.load(open(p, encoding="utf-8"))
    except Exception as e:
        fails.append("json %s: %s" % (rel(p), e))

# 4) agent frontmatter + skills wiring
for p in glob.glob(ROOT + "/team-kits/**/agents/*.md", recursive=True):
    fm = None
    try:
        fm = frontmatter(open(p, encoding="utf-8").read())
    except Exception as e:
        fails.append("frontmatter %s: %s" % (rel(p), e))
        continue
    if not fm:
        continue
    kit_dir = os.path.dirname(os.path.dirname(p))
    for sk in (fm.get("skills") or []):
        if not os.path.isdir(os.path.join(kit_dir, "skills", sk)):
            fails.append("%s: skills:[%s] has no skill dir" % (rel(p), sk))

# 5) skill frontmatter
for p in glob.glob(ROOT + "/team-kits/**/skills/**/SKILL.md", recursive=True):
    try:
        frontmatter(open(p, encoding="utf-8").read())
    except Exception as e:
        fails.append("skill frontmatter %s: %s" % (rel(p), e))

# 6) presets are executable policy: parse them strictly and prove that every explicit specialist
#    is a real kit role, while the foreground lead remains outside every specialist list. The same
#    implementation is called by both scaffold scripts, so CI and direct usage cannot disagree.
preset_catalogs = {}
for kit_dir in sorted(glob.glob(ROOT + "/team-kits/*")):
    if not os.path.isdir(os.path.join(kit_dir, "agents")):
        continue
    kit = os.path.basename(kit_dir)
    try:
        preset_catalogs[kit] = load_preset_catalog(kit_dir)
    except Exception as e:
        fails.append("%s/presets.yaml: %s" % (rel(kit_dir), e))

# 7) registry roles -> agent files exist, and its advertised presets exactly match the executable
#    kit policy (otherwise the entry gate can offer a preset that the scaffold cannot resolve).
reg = yaml.load(open(ROOT + "/team-kits/registry.yaml", encoding="utf-8").read(),
                Loader=UniqueKeyLoader)
for team in reg.get("teams", []):
    kit = team["key"]
    for role in team.get("roles", []):
        if not os.path.isfile(ROOT + "/team-kits/%s/agents/%s.md" % (kit, role)):
            fails.append("registry: %s role '%s' has no agent file" % (kit, role))
    catalog = preset_catalogs.get(kit)
    advertised = team.get("presets")
    registry_roles = team.get("roles")
    if catalog is not None:
        if team.get("lead") != catalog["lead"]:
            fails.append("registry: %s lead %r does not match settings agent %r" %
                         (kit, team.get("lead"), catalog["lead"]))
        expected_specialists = set(catalog["roles"]) - {catalog["lead"]}
        if (not isinstance(registry_roles, list)
                or any(not isinstance(role, str) for role in registry_roles)
                or len(registry_roles) != len(set(registry_roles))
                or set(registry_roles) != expected_specialists):
            fails.append("registry: %s roles must list every specialist exactly once and exclude "
                         "foreground lead %r" % (kit, catalog["lead"]))
    if (not isinstance(advertised, list)
            or any(not isinstance(name, str) for name in advertised)
            or len(advertised) != len(set(advertised))):
        fails.append("registry: %s presets must be a unique string list" % kit)
    elif catalog is not None and advertised != list(catalog["presets"]):
        fails.append("registry: %s presets %r do not match presets.yaml %r" %
                     (kit, advertised, list(catalog["presets"])))

# 8) model_map/effort_map <-> specialist agent frontmatter (catch tier drift in the shipped kit)
for cfg in glob.glob(ROOT + "/team-kits/*/templates/project_memory/project_config.yaml"):
    kit_dir = os.path.dirname(os.path.dirname(os.path.dirname(cfg)))   # -> team-kits/<kit>
    try:
        conf = yaml.load(open(cfg, encoding="utf-8").read(), Loader=UniqueKeyLoader) or {}
    except Exception:
        continue  # YAML parse already reported in step 2
    lead = "project-manager"  # the session lead is excluded from the maps
    sp = os.path.join(kit_dir, "settings", "settings.json")
    if os.path.isfile(sp):
        try:
            lead = json.load(open(sp, encoding="utf-8")).get("agent") or lead
        except Exception:
            pass
    specialists = {os.path.splitext(os.path.basename(a))[0]
                   for a in glob.glob(os.path.join(kit_dir, "agents", "*.md"))} - {lead}
    field_of = {"model_map": "model", "effort_map": "effort"}
    for mapname, field in field_of.items():
        m = conf.get(mapname) or {}
        keys = set(m)
        for missing in sorted(specialists - keys):
            fails.append("%s: %s missing specialist '%s'" % (rel(cfg), mapname, missing))
        for stray in sorted(keys - specialists):
            fails.append("%s: %s has key '%s' with no matching agent" % (rel(cfg), mapname, stray))
        if lead in keys:
            fails.append("%s: %s must NOT list the session lead '%s'" % (rel(cfg), mapname, lead))
        # each specialist MUST carry the field, and it must equal the map value
        for role in sorted(specialists):
            ap = os.path.join(kit_dir, "agents", role + ".md")
            try:
                afm = frontmatter(open(ap, encoding="utf-8").read()) or {}
            except Exception:
                continue
            if field not in afm:
                fails.append("%s: specialist missing '%s:' frontmatter" % (rel(ap), field))
            elif role in keys and str(afm[field]) != str(m[role]):
                fails.append("%s: %s:%s != %s '%s' (%s)" % (rel(ap), field, afm[field], mapname, m[role], role))
    # the session lead carries model: + effort: but is NOT in the maps
    lp = os.path.join(kit_dir, "agents", lead + ".md")
    if os.path.isfile(lp):
        lfm = frontmatter(open(lp, encoding="utf-8").read()) or {}
        for field in ("model", "effort"):
            if field not in lfm:
                fails.append("%s: session lead missing '%s:' frontmatter" % (rel(lp), field))
    # kit SOURCES are provider-neutral: agent frontmatter must use tier aliases, never a concrete
    # provider model name (the scaffold resolves aliases per provider at install time)
    for ap in glob.glob(os.path.join(kit_dir, "agents", "*.md")):
        try:
            afm = frontmatter(open(ap, encoding="utf-8").read()) or {}
        except Exception:
            continue
        if "model" in afm and str(afm["model"]) not in ("lead", "worker", "light"):
            fails.append("%s: model '%s' — kit sources must use the tier aliases "
                         "lead/worker/light (model_tiers.yaml maps them per provider)"
                         % (rel(ap), afm["model"]))

# 9) kit VERSION stamps must match the kit content (forgetting a bump is a CI failure), and the
#    constitution marker must sit on line 1 (session_status parses only the first line for the kit key —
#    if it ever moved, update detection would go blind silently).
sys.path.insert(0, os.path.join(ROOT, "tools"))
from bump_kit_version import discover_kits, kit_hash  # noqa: E402

for kit in discover_kits(ROOT):
    kit_dir = os.path.join(ROOT, "team-kits", kit)
    vfile = os.path.join(kit_dir, "VERSION")
    if not os.path.isfile(vfile):
        fails.append("%s: missing team-kits/%s/VERSION — run python tools/bump_kit_version.py" % (kit, kit))
    elif ("content: %s" % kit_hash(kit_dir)) not in open(vfile, encoding="utf-8").read():
        fails.append("%s: kit files changed but VERSION not bumped — run python tools/bump_kit_version.py" % kit)
    cpath = os.path.join(kit_dir, "constitution", "AGENTS.md")
    if not os.path.isfile(cpath):
        fails.append("%s: missing constitution/AGENTS.md (renamed from CLAUDE.md — the source file "
                     "carries the vendor-neutral name it ships under)" % kit)
    else:
        lines = open(cpath, encoding="utf-8", errors="ignore").read().splitlines()
        if not lines or "agents-and-skills:team-kit" not in lines[0]:
            fails.append("%s: constitution marker not on LINE 1 — session_status kit-update detection "
                         "reads only the first line" % kit)
        # THE ONE SIZE STATEMENT ABOUT A CONSTITUTION — through the package it is part of, and in
        # BYTES. What stood here was a 220-LINE ceiling on the constitution and a second one on the
        # lead SKILL, and measured they said nothing about size: all three constitutions held the
        # limit only because 31 to 46 of their lines ran 110-1899 characters (reflowed to 100
        # columns: 383/368/394 lines), while a compaction pilot cut 24.9 % of the bytes and RAISED
        # its line count from 20 to 36. A line ceiling beside a byte budget is a ceiling that pushes
        # against it. Removed rather than replaced by a per-file byte number: nothing derives one,
        # and a second invented constant next to the first is what this repo keeps paying for
        # (`tools/lead_package.py` carries the reasoning and the number).
        #
        # The package is a CI-side budget, not a hook: nothing writes these files at runtime.
        # WARNING until phase 3 (II.11/3) does the shrinking; promote to `fails` there.
        total = lead_package.size(kit_dir)
        if total > lead_package.MAX_BYTES:
            warns.append("%s: lead instruction package is %d bytes (> %d, spec II.5) — "
                         "agent.md + Lead-SKILL + constitution all load at every session "
                         "start. Phase 3 (II.11/3) shrinks these; this becomes a hard failure "
                         "then." % (kit, total, lead_package.MAX_BYTES))

# 10) intended-identical hooks/scripts must stay byte-identical across kits (audit finding: a fix
#    applied in one kit silently diverges the others — exactly the drift class this repo hunts).
MIRROR_DEV_RESEARCH = [
    "hooks/guard_yaml_valid.py", "hooks/guard_agent_spawn.py", "hooks/notify_agent_events.py",
    "hooks/guard_scratchpad_ref.py", "hooks/gate_subagent_output.py", "hooks/guard_harness_selfmod.py",
    "hooks/guard_pm_scope.py", "hooks/guard_no_adhoc.py", "hooks/guard_question_context.py",
    "hooks/gate_memory_complete.py", "hooks/gate_pipeline.py", "hooks/guard_guidelines.py",
    "hooks/_root.py", "hooks/_audit.py", "hooks/_compat.py",
    "templates/repo/scripts/quality.py", "templates/repo/scripts/kit_checks.py",
    "templates/repo/scripts/kit_browser_checks.py", "templates/repo/scripts/retro.py",
    # kit-NEUTRAL by content (it names project_memory/** and generic source dirs, nothing dev- or
    # research-specific), so the two copies have always been identical and a fix to one belongs in
    # both. It was carried along in the phase-2 lockstep on that reasoning while nothing held it —
    # the office copy is deliberately different (a document workspace, not a code repo) and stays
    # out of every mirror set.
    "templates/repo/.claude/claude-security-guidance.md",
]
MIRROR_DEV_OFFICE = [
    "hooks/guard_yaml_valid.py", "hooks/guard_agent_spawn.py", "hooks/notify_agent_events.py",
    "hooks/guard_scratchpad_ref.py", "hooks/gate_subagent_output.py", "hooks/guard_harness_selfmod.py",
    "hooks/guard_question_context.py", "hooks/guard_pm_scope.py", "hooks/guard_no_adhoc.py",
    "hooks/_root.py", "hooks/_audit.py", "hooks/_compat.py",
]
for other, names in (("research-team", MIRROR_DEV_RESEARCH), ("office-team", MIRROR_DEV_OFFICE)):
    for name in names:
        a = os.path.join(ROOT, "team-kits", "dev-team", name)
        b = os.path.join(ROOT, "team-kits", other, name)
        if not (os.path.isfile(a) and os.path.isfile(b)):
            fails.append("mirror: %s missing in dev-team or %s" % (name, other))
        elif open(a, "rb").read() != open(b, "rb").read():
            fails.append("mirror: %s diverged between dev-team and %s — copy the fixed file" % (name, other))

# 11) every §-reference in hooks/skills/agents AND in the constitution itself must resolve to a
#     heading (## N.) or a bold anchor (**Na.) in that kit's constitution — a block message citing
#     a deleted paragraph teaches the agent to look for nothing (audit finding after the
#     constitution diet). The constitution is in the list because it cites itself more than any
#     other file does, and an unchecked self-reference is exactly how four office `(§8)` pointers
#     shipped aiming at a section that did not carry the rule they cited.
import re as _re  # noqa: E402
for kit_dir_name in os.listdir(os.path.join(ROOT, "team-kits")):
    cpath = os.path.join(ROOT, "team-kits", kit_dir_name, "constitution", "AGENTS.md")
    if not os.path.isfile(cpath):
        continue
    cons = open(cpath, encoding="utf-8", errors="ignore").read()
    anchors = set(_re.findall(r"(?m)^##+\s*(\d+[a-z]?)\.", cons))
    anchors |= set(_re.findall(r"(?m)^\*\*(\d+[a-z]?)\.", cons))
    for pattern in ("constitution/AGENTS.md", "hooks/*.py", "skills/*/SKILL.md", "agents/*.md"):
        for p in glob.glob(os.path.join(ROOT, "team-kits", kit_dir_name, pattern)):
            txt = open(p, encoding="utf-8", errors="ignore").read()
            for m in _re.finditer(r"§(\d+[a-z]?)", txt):
                # a `§2.7`-style sub-reference resolves to its PARENT section, so the parent is
                # what has to exist. Skipping the whole reference (the earlier behaviour) let
                # `§99.1` through, which is the same dead pointer one level down.
                if m.group(1) not in anchors:
                    fails.append("%s: references §%s which does not exist in %s's constitution"
                                 % (rel(p), m.group(1), kit_dir_name))
                    break  # one finding per file is enough

# 12) every file the kit hash covers must be git-tracked. An ignored-but-present file makes
#     VERSION true only on THIS machine: a real .gitignore'd office seed kept local validate green
#     while CI was red and fresh clones could not install (the hash walks the FILESYSTEM).
import subprocess as _sp  # noqa: E402
# READ THE HASH'S OWN ENUMERATION, do not re-walk the tree beside it. This check used to walk the
# kit directory with its own copy of the skip rules, which meant it covered the kit's half of the
# subject and not the SHARED half -- an untracked file at the team-kits root is hashed into every
# kit and was reported by nobody. `kit_hash_inputs` is what `kit_hash` iterates, so "hashed into
# VERSION" is answered by the thing that does the hashing.
sys.path.insert(0, os.path.join(ROOT, "team-kits"))  # noqa: E402
from kernel.hashing import kit_hash_inputs  # noqa: E402
try:
    _git = _sp.run(["git", "ls-files", "team-kits"], cwd=ROOT, capture_output=True,
                   text=True, timeout=30)
    _tracked = set(_git.stdout.splitlines()) if _git.returncode == 0 else None
except Exception:
    _tracked = None  # no git available (e.g. an exported tree) — hash/track parity is then moot
if _tracked is not None:
    _untracked = set()
    for kit in discover_kits(ROOT):
        for _name, _path in kit_hash_inputs(os.path.join(ROOT, "team-kits", kit)):
            if _path is None:
                # a directory link contributes its NAME to the hash and no content (see
                # `_kit_files`); there is no file here to ask git about
                continue
            relp = os.path.relpath(_path, ROOT).replace("\\", "/")
            if relp not in _tracked:
                # deduplicated across kits: a shared input is in all three hashes and one finding
                # per file is what a reader can act on
                _untracked.add(relp)
    for relp in sorted(_untracked):
        fails.append("%s is hashed into a kit VERSION but not git-tracked "
                     "(check .gitignore) — CI and fresh clones will disagree "
                     "with the local hash" % relp)

for w in warns:
    print("  [warn] " + w)
if fails:
    print("VALIDATION FAILED (%d):" % len(fails))
    for f in fails:
        print("  - " + f)
    sys.exit(1)
print("validate.py: all structural checks passed%s."
      % (" (%d budget warning(s))" % len(warns) if warns else ""))
