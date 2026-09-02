"""Which REFERENCE skills a work order names -- derived from the task, never chosen by the role.

WHY THIS EXISTS (FR-0071). Until this round every shipped role declared exactly one skill, named
after itself, so there was nothing to choose. The moment a second, SHARED skill sits beside the
roles, the failure mode is the default one: the role text names them all and the role reaches for
the habitual one. This repo's own idiom is the answer -- the order is generated from the item -- so
the reference skills a specialist is pointed at are computed here from two frozen fields of the
task (`assigned_role` and `type`, both in `backlog_types.TSK_PLAN_FIELDS`) and ride in the dispatch
header, next to `hand_back` and `checkpoint`.

WHAT IT IS NOT, said plainly because DEC-0056 asks for the measured error a mechanism catches and
there is none yet: the wrong-pick failure is PREDICTED, not observed in a transcript. Nothing here
enforces anything -- the header is a pointer the role can ignore, and a role may open a skill the
order does not name (the constitution asks it to say so in the envelope). What this buys is that
the choice is VISIBLE in the generated order instead of happening silently, and that a text task
does not drag in the heavyweight design references. It is deliberately the cheap half.

THE DECLARATION LIVES IN THE SKILL, not in a map beside it. A separate map would be a second list
to keep in step with the directory, and this repo has measured that drift often enough to stop
writing the second list: a skill declares in its own frontmatter which roles and which task types
it is for, so adding a reference skill is one file and removing one cannot leave a dangling row.

    reference_for:
      roles: [product-designer, frontend-developer]
      task_types: [design, ui]

A skill directory WITHOUT that key is a role's own procedure skill (one per role, named like the
role) and is not a reference skill at all -- see `kernel.backlog_types.TASK_TYPES` for the closed
type vocabulary a declaration is read against, and
`tools/test_reference_skills.py::test_every_shipped_reference_skill_can_be_named_by_some_task` for
the tripwire that a shipped reference skill no task could ever reach fails the suite.
"""
import os

REFERENCE_KEY = "reference_for"
ROLES_KEY = "roles"
TASK_TYPES_KEY = "task_types"
SKILL_FILE = "SKILL.md"


def skills_dir(repo_root: str) -> str:
    """Where the INSTALLED skills live, asked of the installer that puts them there.

    The same shape and the same reason as `dispatch.agents_dir`: `presets.SKILLS_DIR` is the path
    the kit installer writes into, so a kit that moved its skills would move this reader with it.
    Deferred import because `presets` pulls in `subprocess`/`shutil` for the installer it drives,
    and composing a dispatch needs neither.
    """
    from .presets import SKILLS_DIR

    return os.path.join(repo_root, SKILLS_DIR)


def _frontmatter(path: str):
    """The YAML frontmatter of one SKILL.md, or None when it cannot be read.

    None is NOT "no declaration": it means the question could not be asked. Both callers below
    treat an unreadable file as contributing nothing, which is the fail-quiet direction a POINTER
    is allowed to take -- withholding a hint, never granting a permission.

    "CANNOT BE READ" INCLUDES THE WRONG ENCODING, and leaving that out was a real outage rather
    than a tidiness point: this reader walks EVERY directory under the installed skills folder, and
    that folder is exactly where `FR-0045` invites the user to unpack their own design-system
    export. One `SKILL.md` saved as ANSI there raised `UnicodeDecodeError` out of `declarations`,
    through `for_task`, out of `create_lease` -- every dispatch in the project dead with a
    stacktrace, from a file nobody in the apparatus wrote. Measured on a cp1252 file at that exact
    drop-in point; the red test is
    `tools/test_reference_skills.py::test_a_skill_file_that_is_not_utf8_never_reaches_the_dispatch`.

    It is a CATCH and not `errors="replace"` on purpose: replacing undecodable bytes would hand the
    matcher a mutated role name and call the result a declaration. A file this reader cannot decode
    is one it says nothing about.
    """
    import yaml

    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError):
        return None
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    try:
        front = yaml.safe_load(text[3:end])
    except yaml.YAMLError:
        return None
    return front if isinstance(front, dict) else None


def _words(value):
    """A declaration's `roles`/`task_types` as a set of words, tolerant of the one-string spelling."""
    if value is None:
        return set()
    if isinstance(value, str):
        value = [part.strip() for part in value.split(",")]
    if not isinstance(value, list):
        return set()
    return {str(one).strip() for one in value if str(one).strip()}


def declarations(directory: str) -> dict:
    """{skill name: {"roles": set, "task_types": set, "path": str}} for every REFERENCE skill there.

    A skill whose frontmatter carries no `reference_for` is absent from the result -- that is the
    definition of "reference skill" this kit uses, and the same definition read from the other end
    (a skill no role's `skills:` frontmatter names) is what the suite measures the two against.
    A declaration that is present but empty on either axis stays in the result WITH an empty set,
    so `for_task` can never name it and the tripwire can see it. Dropping it here instead would
    hide exactly the dead weight the tripwire exists for.
    """
    out = {}
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return out
    for name in names:
        path = os.path.join(directory, name, SKILL_FILE)
        if not os.path.isfile(path):
            continue
        front = _frontmatter(path)
        if not front or REFERENCE_KEY not in front:
            continue
        block = front.get(REFERENCE_KEY)
        if not isinstance(block, dict):
            block = {}
        out[name] = {ROLES_KEY: _words(block.get(ROLES_KEY)),
                     TASK_TYPES_KEY: _words(block.get(TASK_TYPES_KEY)),
                     "path": path}
    return out


def for_task(directory: str, role, task_type) -> list:
    """The reference skills THIS task names -- role AND type must both match, sorted.

    Both, not either: "every skill this role ever uses" is the habitual-pick failure with extra
    steps, and the point of deriving from the task is that a `docs` task for the designer does not
    arrive carrying the same references a `ui` task does.

    Names only. A caller that needs the file asks `resolve`, so the header stays small and the one
    place that knows the layout stays `skills_dir`.
    """
    role, task_type = str(role or ""), str(task_type or "")
    if not role or not task_type:
        return []
    return sorted(name for name, rule in declarations(directory).items()
                  if role in rule[ROLES_KEY] and task_type in rule[TASK_TYPES_KEY])


def resolve(directory: str, name: str):
    """The SKILL.md a named reference skill resolves to, or None -- the other end of `for_task`."""
    path = os.path.join(directory, str(name or ""), SKILL_FILE)
    return path if os.path.isfile(path) else None
