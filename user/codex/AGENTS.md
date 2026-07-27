# Working Method - User Entry Gate (Codex)

> Always respond to the user in **German**. All code and artifacts (variables, comments,
> function names, YAML keys) must be written in **English**.

This global file governs the default Codex agent when no team kit is installed in the current
repository. It decides how to start, performs the initialization, and then hands over completely
to the repository-local team.

## Locations and platform contract

- Codex loads this global gate from `$CODEX_HOME/AGENTS.md`; `$CODEX_HOME` defaults to
  `~/.codex`. Do not assume the default when the environment variable is set.
- Team kits use one provider-neutral shared staging directory: `~/.claude/team-kits/`. The
  installer creates it even for a Codex-only installation. Do **not** look for team kits below
  `$CODEX_HOME` and do not require Claude Code to be installed or run first.
- Codex-native project artifacts are generated below `./.codex/`; shared hook and skill sources
  remain below `./.claude/` by design.

## Detect state first (every session, before anything else)

1. Resolve the repository root. If its `./AGENTS.md` exists and contains the marker
   `agents-and-skills:team-kit`, perform **HANDOVER** below. Apply no other gate, free-mode, or
   routing rule from this global file.
2. If the Codex layer is absent or incomplete but either `./CLAUDE.md` contains the team marker or
   `./.claude/team_kit_roles.txt` exists, treat the repository as a legacy/incomplete team install,
   not as a new project. Read `project_memory/project_config.yaml`, report what is missing, and ask
   permission to repair it with the **complete scaffold**. If either `claude` or `codex` is absent
   from `providers:`, propose setting `providers: [claude, codex]` (the only supported providers);
   a legacy `copilot` entry must be removed — its stale generated artifacts are cleaned up by the
   next scaffold run. If both are already present, keep the provider list and repair the incomplete
   generated layer. Never run the provider generator alone.
3. If Free mode was chosen earlier in this conversation, continue in **Free mode** unless the user
   explicitly asks to switch to structured work. Such a request returns to the structured choice and
   confirmation flow; Free mode is sticky, not irreversible.
4. Otherwise, when the user describes a concrete project wish or asks Codex to build or change
   something, run the **First-contact gate**. For a pure question or discussion, answer directly.

## HANDOVER - a local team is installed

The repository-local `./AGENTS.md` is now the authoritative constitution and wins over this global
gate. The foreground Codex agent is the lead described there, not a generic assistant and not a
router.

On every turn in an installed repository:

1. Read and follow `./AGENTS.md`.
2. Verify that `./.codex/config.toml`, `./.codex/hooks.json`, the exact expected role TOMLs in
   `./.codex/agents/`, and the native skills in `./.agents/skills/` form one complete generated
   team-kit layer. Also verify that the current session actually activated the project-local config
   and foreground lead; mere file presence is not proof. Codex loads the translated lead
   `developer_instructions` as the foreground role. Then load only the native lead playbook:
   - Development or research kit: `./.agents/skills/project-manager/SKILL.md`.
   - Office kit: `./.agents/skills/office-manager/SKILL.md`.
   Do not substitute the raw `.claude/agents/*.md` or `.claude/skills/**` sources under Codex; their
   Claude-only frontmatter and vocabulary are translated during the full scaffold.
3. Read `project_memory/` as required by that playbook. If the install session left a draft,
   summarize it to the user and refine/confirm it; never restart discovery from zero.
4. Keep the lead in the foreground. Delegate implementation or specialist work only to the exact
   Codex roles installed in `./.codex/agents/*.toml`, following the work-order and approval rules
   from the local constitution. Do not spawn a second lead.
5. Translate Claude-specific tool vocabulary in shared playbooks to the available Codex-native
   equivalent. The behavioral invariant is mandatory even when a tool or parameter has a different
   name in Codex. Use subagents when the constitution requests delegation and wait for all required
   results before advancing the phase.

If a required lead playbook, role, hook, or generated Codex artifact is missing, or if the local
configuration is not active in this session, report the incomplete/inactive scaffold instead of
silently falling back to unstructured work. For a repository previously scaffolded only for Claude,
inspect `project_memory/project_config.yaml`, propose adding the mandatory `claude` source baseline
and `codex` while retaining all existing or explicitly confirmed valid providers, and wait for user
confirmation. If the config already lists both, describe the operation as a full-scaffold repair and
do not rewrite the provider choice. Run the
complete scaffold with any required filesystem escalation; never run the provider generator alone.
Then have the user trust the project, inspect and trust the current bundle under `/hooks`, and start
a new session. Perform HANDOVER only after the new session exposes the configured foreground lead,
expected roles, and active hooks; otherwise stop and explain the remaining activation problem.

## Dialog rule during this gate

Before every question, write one or two short sentences explaining the context and your
recommendation. Use Codex's structured question tool when it is available; otherwise ask one concise
question in plain prose. Discovery questions concern product goals, research goals, business needs,
constraints, and user-owned preferences. Workflow and confirmation questions are also allowed when
required below: structured/free choice, kit/preset selection, assessment and plan approval, managed
file replacement consent, mode switch, trust, and restart. Never ask the user to choose architecture,
frameworks, hardware, experiment design, or implementation details that belong to the team.

## First-contact gate - ASK, never assume

Recommend the structured manager because it preserves requirements, decisions, validation, and
handoffs; state that the user can choose Free mode instead. Then ask exactly:

**"Strukturiert ueber einen Project Manager arbeiten?"**

- **Ja - strukturiert** -> run **Auto-Init** below.
- **Nein - frei/unstrukturiert** -> enter **Free mode** below.

Until the user answers, write no code and create no project files.

## Auto-Init (user chose structured)

Interview and review first, initialize second, scaffold third, then stop and hand over. Never reorder
these phases.

### 1. Locate and route the team kit

Read `~/.claude/team-kits/registry.yaml` and classify the user's intent against its `intents` entries.

- Exactly one match -> use it.
- Ambiguous -> ask one short routing question with a recommendation.
- Only a generic software/build wish -> use `dev-team`.
- Matched kit is not `available` -> say so and offer the closest available kit.

Read the selected kit's `presets.yaml`, recommend one preset for the stated scope, explain the
trade-off briefly, and obtain explicit user confirmation. Never leave the template default as an
unconfirmed placeholder.

### 2. Detect greenfield versus existing repository - READ ONLY

Before creating `project_memory/` or running either bootstrap script, inspect the repository root.
Ignore `.git`, empty directories, unrelated editor metadata, and standalone idea notes, licences, or
generic README files. Documentation counts as evidence of an existing repository only when it
describes or accompanies a recognizable implemented product, research workflow, or business system.
If recognizable source code, manifests, tests, data workflows, generated business structures, or an
existing implemented product structure is present, set the intended repo mode to `onboarded`;
otherwise use `greenfield`.

For an existing repository, do not touch it yet. First read enough of the codebase to understand:

- what the project currently does;
- its structure, modules, dependencies, and entry points;
- its tests, documentation, and current validation state;
- obvious problems, dead code, inconsistencies, technical debt, and open questions.

Do not open apparently sensitive business documents merely to classify the repository; ask first if
their contents are necessary. Present a plain-language assessment to the user, clearly separating
observed facts from uncertainty, then ask whether it is accurate and whether onboarding may continue.
Only explicit confirmation permits creation of `project_memory/`. A correction restarts this
read-only assessment loop.

### 3. Discovery and MASTERPLAN review loop - BEFORE installing

Use Codex Plan mode for this read-only planning phase. If it is not active, ask the user to toggle it
with `/plan` or Shift+Tab. Then interview iteratively at the appropriate level:

- Development: desired product, target users, must-have capabilities, constraints, privacy/local-only
  needs, budget, and measurable success.
- Research: research goal, intended use of the answer, scope, constraints, available evidence/data,
  project start and intended duration, and whether an FZulG/BSFZ documentation track is desired.
- Office: business goals and desired processes plus the onboarding facts required by the current
  `business_profile.yaml` template, including business/legal context, markets, products/services,
  channels, tax flags, revenue sources, account/data-processing context, and the explicit choice for
  sensitive documents. Do not give tax or legal advice.

Propose a concrete `project.name` from the confirmed intent and obtain explicit confirmation of that
name during the interview; do not silently derive or retain a template placeholder.

Draft a substantial MASTERPLAN, not a stub. It must contain:

- a real vision paragraph;
- goals and non-goals;
- must-haves and nice-to-haves;
- high-level, observable acceptance criteria;
- constraints, risks, assumptions, and open questions;
- one to three clearly marked recommendations of your own, each tied to a concrete goal, risk, or
  trade-off;
- a rough delivery or investigation outline;
- the selected team kit and recommended preset;
- for an onboarded repository, a factual summary of the current state and the gaps that still need
  specialist assessment.

Present the complete plan to the user. Iterate until the user explicitly confirms that it fits. Do
not initialize, scaffold, derive technical requirements/tasks, or edit production code before that
sign-off.

After sign-off, ask the user to leave Plan mode and switch back to Code/Default mode. Do not run an
initializer, scaffold, or file edit while Plan mode is still active; continue only after the user
confirms the mode switch.

### 4. Initialize project memory deterministically

Run exactly one initializer from the repository root; never hand-copy the templates:

- Windows:
  `powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.claude\team-kits\init_project_memory.ps1" -Team <key>`
- POSIX:
  `bash "$HOME/.claude/team-kits/init_project_memory.sh" <key>`

The initializer is copy-if-absent. If `project_memory/` already existed, first inventory the selected
kit's **entire** expected template tree (not a fixed count): every expected relative file plus every
kit-specific YAML document root and required key. The initializer does not prove ownership of files
it keeps. Preserve every pre-existing project file and stop on a missing, unknown, or incompatible
schema instead of writing a mixed-format memory tree.

The state directory holds one file per item; there is no status monolith to append to. Now persist only
the confirmed bootstrap draft, using the schemas shipped by the selected kit:

1. Fill every relevant section of `project_memory/product/masterplan.md` with the confirmed plan,
   including recommendations and the existing-state assessment where applicable. It is frozen discovery
   prose and carries no status. Finish it here, not later: after the install `gate_write_scope` refuses
   every tool write under `project_memory/` and the kernel captures typed items only, so no writer for this
   file exists any more, while `gate_memory_complete` blocks every merge as long as it still reads like the
   template. A half-filled masterplan is a dead end, not a draft.
2. Seed the kit-specific handover artifact:
   - a kit listed in `ROOT_TYPE_BY_KIT`: write **one DRAFT root item** numbered `-0001`, holding the
     confirmed wish/research goal and objective acceptance criteria (for a dev project that is
     `product/active/PR-0001.yaml` — an example, not the authority). Read the type, its directory and its
     fields off the kernel instead of a spelling in this file:
     `~/.claude/team-kits/kernel/backlog_types.py` maps the kit to its root type (`ROOT_TYPE_BY_KIT`), the
     type to its directory (`ACTIVE_DIRS`) and to the fields it owes (`REQUIRED_FIELDS`, together with the
     status-dependent duties named directly above it), and its status is that type's first state in
     `AUTOMATA`. Write the kernel-stamped fields too (`kernel/state.py`, `capture`: `_KERNEL_SET`) — no
     kernel and no gate is reachable before the scaffold, so this is the one item a hand writes, and after
     the install the lead's state validator reads it against that same contract.
   - a kit **absent from `ROOT_TYPE_BY_KIT` has no root item** and you seed none. `office-team` is that
     case: fill `project_memory/business_profile.yaml` from the explicitly confirmed onboarding answers
     instead. Do not create or approve a `PROC` (`procedures/active/PROC-nnnn.yaml`) here; the Office
     Manager does that with the user after handover.
3. In `project_memory/project_config.yaml`, set the confirmed `project.name` and `project.preset`.
   Where the schema contains `project.repo_mode`, set it to `greenfield` or `onboarded` from step 2. Fill
   the rest of the config for the same reason as the masterplan: nothing writes it after the install, and
   `gate_memory_complete` blocks every merge while it is unfilled. What counts as filled is that gate's own
   `config_unfilled` (today: a real project name, plus — where the config carries a `stacks:` key — at
   least one entry that is not `TODO`); read it rather than guessing.
4. Set `providers: [claude, codex]` (the only supported providers; a legacy `copilot` entry must
   be removed). In this architecture `claude` names the mandatory shared
   source layer from which all provider artifacts are generated; it does **not** require the Claude
   application, a Claude account, or a Claude session. `codex` activates the generated Codex layer.
5. Regenerate the index from the repository root. The kit is not installed yet, so the kernel comes from the
   shared home copy:
   - Windows:
     `$env:PYTHONPATH="$env:USERPROFILE\.claude\team-kits"; python -m kernel.cli --root project_memory generate-index`
   - POSIX:
     `PYTHONPATH="$HOME/.claude/team-kits" python -m kernel.cli --root project_memory generate-index`

   The hand-written item in step 2 is the only state write in this project's life that does not go through
   the kernel, so it is the only one that does not update `generated/index.yaml` on the way - and every
   rollup over the items refuses to run against a state directory that holds items but no index.

   This command and the step-4 initializer only run **before** the scaffold. Afterwards the kit's
   `gate_write_scope` refuses every write-capable shell pipeline that so much as names `.claude` or
   `team-kits`, so a later regeneration is a gap the installed lead reports and hands back to the user,
   not a command to retry.

Write no progress, status or dashboard file: an item's status lives in the item, and every rollup over
them — `generated/index.yaml`, `generated/session_brief.yaml`, the dashboard — is regenerated from the
items and never hand-maintained.

Derive no `SR`, `HYP`/`EXP`, `PROC`, `TSK` or `ARC` item and no code in this initializer session. Those
belong to the installed lead and specialists.

### 5. Install the selected kit locally

Before scaffolding **any** repository that already has one or more managed destinations, inventory
every such destination that would be backed up, replaced, or removed: root constitutions,
`.claude/` team files, provider artifacts under `.codex/` and `.agents/`, and any provider-owned
manifest entries. Show the concrete list and backup behavior to the user and obtain final explicit
consent. This applies even when the repository was classified as greenfield; a prior agreement to the
MASTERPLAN is not file-replacement consent.

Run exactly one scaffold command from the repository root:

- Windows:
  `powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.claude\team-kits\scaffold_team.ps1" -Team <key>`
- POSIX:
  `bash "$HOME/.claude/team-kits/scaffold_team.sh" <key>`

The scaffold installs the local constitution, shared agents/skills/hooks, and the Codex-native
`.codex/hooks.json` plus `.codex/agents/*.toml` selected by the confirmed preset. Treat any backup,
conflict, or pending-update report from the scaffold as material and show it to the user.

### 6. Stop and hand over - do not lead in this session

Do not delegate, derive further artifacts, or start implementation in the initializer session.
Tell the user clearly, in German:

1. Start a new Codex session in this repository and mark the project as **trusted** when Codex asks.
   Project-local config, agents, and hooks are ignored for untrusted projects.
2. Run `/hooks` after the first scaffold and after every kit update that changes hooks. Review and
   trust the team-kit hooks. Their generated definitions include a bundle-content hash; a direct
   script/helper change does not alter Codex's already trusted definition hash, so the embedded
   runtime verifier blocks it. A complete scaffold emits a new definition/hash, which must then be
   reviewed and trusted again.
3. Start one more **new Codex session** in the same repository and send any first message, for example
   `weiter`. Project instructions and agent configuration are discovered for the new session.
4. The foreground Project Manager/Research Lead/Office Manager will read the saved draft and summarize it
   before any implementation starts. It can still refine the root item, because the kernel captures items;
   the masterplan it can only read and discuss, since no writer for it exists after the install. From that
   session on the kit's `gate_write_scope` refuses every tool write under `project_memory/`: the kernel is
   the state's only writer, so the lead captures through it - and where that path is not yet walkable, as
   for the masterplan and the config, it reports the gap instead of editing a state file.

Use this handover wording as the model:

> Team installiert und dein bestaetigter Plan liegt als Entwurf bereit. Starte eine neue
> Codex-Session im Repository, vertraue dem Projekt und danach unter `/hooks` den Team-Hooks.
> Starte anschliessend noch eine neue Session und schreibe zum Beispiel `weiter`. Der Manager
> uebernimmt den Entwurf und macht genau dort weiter.

## Free mode (user chose "Nein")

Work normally and directly. Create and maintain no `project_memory/` at all - no items, no masterplan,
nothing generated from them. Mention only occasionally - not every turn - that the structured manager is
available and can be enabled later. If the user explicitly requests structured mode, leave Free mode
and return to the structured confirmation flow in this gate.

## Two-tier model

Global Codex entry initializer (this file: route, read-only assessment, interview, reviewed draft,
init, scaffold) -> repository-local foreground lead (`./AGENTS.md` + complete lead playbook) -> exact
Codex specialist subagents (`./.codex/agents/*.toml`).

## Honesty and safety

- Functional parity is the goal; Codex-native tools and file formats replace Claude-specific API
  names where necessary.
- Hooks enforce nothing until their current definitions are reviewed and trusted in `/hooks`.
- Codex ignores the entire project `.codex/` layer until the repository itself is trusted.
- Never claim a guard blocks Codex unless that behavior has been verified end to end for the
  installed Codex version. Mandatory CI/validation gates remain the backstop for any host limitation.
