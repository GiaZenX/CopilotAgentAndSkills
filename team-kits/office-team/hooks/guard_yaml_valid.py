#!/usr/bin/env python3
"""
PostToolUse(Edit|Write|MultiEdit|NotebookEdit) — validate a project_memory/*.yaml IMMEDIATELY after it is written.

A real run shipped decisions.yaml/architecture.yaml as invalid YAML repeatedly: the architect (a
spec-writing role without Bash) could not parse-check its own artifacts, the dashboard generator
swallowed the error silently, and a pipeline lint only catches it at MERGE time — after which a
different role had to hot-fix another owner's file. This hook closes the loop at WRITE time: the
moment any role writes broken YAML (parse error OR duplicate key — safe_load silently keeps the
last duplicate), it gets the exact error back and fixes its OWN file on the spot.

Parsing uses yaml.safe_load only; duplicate keys are found by walking yaml.compose()'s node graph
(compose builds nodes, never constructs objects — no code-execution surface). Claude receives an
exit-2 correction; Codex receives a PostToolUse `decision: block` response. Defensive: not a
project_memory yaml / no PyYAML / internal error -> exit 0.

WELL-FORMEDNESS ONLY. This hook used to carry a second job: the progress.yaml format contract
("`status` stays ONE line, history goes to the append-only `log:`"). That contract died with the
monolith (spec II.2) — the per-item state has no single status field to regrow into a blob, and
what a typed item must contain is its TYPE's field contract, answered by the state validator
(`kernel/report.validate_state`) against `kernel/backlog_types`. Re-answering it here from a
PostToolUse hook would be the second truth that spec II.4 forbids.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _compat

YAML_TIPS = ("Tips: put prose containing ':' in a block scalar (key: |), quote strings with special "
             "characters, and never repeat a key at the same level.")


def block(rel, msg, why="is INVALID YAML after your edit", tips=YAML_TIPS):
    if len(msg) > 600:
        msg = msg[:600] + " …"
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import _audit
        _audit.record("guard_yaml_valid", rel)
    except Exception:
        pass
    message = (
        "[team-kit guard] %s %s:\n%s\n"
        "Fix it NOW — you own this artifact. %s Do not hand the file to another role; "
        "do not leave it broken.\n" % (rel, why, msg, tips)
    )
    _compat.stop(message, "PostToolUse")


def state_relative_path(norm):
    """The edited file's path from the `project_memory` segment on.

    The message says "fix it NOW — you own this artifact", so it has to name a path the owner can
    open. A basename stopped doing that when the state became typed: `product/active/PR-0001.yaml`
    was reported as `project_memory/PR-0001.yaml`, which exists nowhere, and the same basename can
    now sit in several directories at once. The absolute path would be noise — agents address
    files repo-relative — so the cut is at the state directory.
    """
    parts = norm.split("/")
    return "/".join(parts[parts.index("project_memory"):])


def find_duplicate_keys(yaml_mod, text):
    """Walk the composed node graph (no object construction) and collect duplicate mapping keys."""
    dupes = []
    try:
        root = yaml_mod.compose(text, Loader=yaml_mod.SafeLoader)
    except Exception:
        return dupes  # parse problems are reported by safe_load already
    stack = [root] if root is not None else []
    visited = set()  # anchors/aliases make the node graph cyclic — never walk a node twice
    while stack:
        node = stack.pop()
        if id(node) in visited:
            continue
        visited.add(id(node))
        if isinstance(node, yaml_mod.MappingNode):
            seen = set()
            for k, v in node.value:
                if isinstance(k, yaml_mod.ScalarNode):
                    if k.value in seen:
                        dupes.append("duplicate key %r (line %d) — safe_load silently keeps only "
                                     "the last one" % (k.value, k.start_mark.line + 1))
                    seen.add(k.value)
                stack.append(k)
                stack.append(v)
        elif isinstance(node, yaml_mod.SequenceNode):
            stack.extend(node.value)
    return dupes


def check(path):
    norm = path.replace("\\", "/")
    if "project_memory" not in norm.split("/") or not norm.endswith((".yaml", ".yml")):
        return
    if not os.path.isfile(path):
        return
    rel = state_relative_path(norm)

    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return  # no parser available here; the pipeline yaml-lint still catches it in CI

    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
    except Exception:
        return

    try:
        yaml.safe_load(text)
    except yaml.YAMLError as e:
        block(rel, str(e))
    except Exception:
        return  # internal edge case — never block on our own bug

    dupes = find_duplicate_keys(yaml, text)
    if dupes:
        block(rel, "\n".join(dupes))


def main():
    data = _compat.load()
    if data.get("tool_name") not in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        sys.exit(0)
    for path in _compat.file_paths(data):
        check(path)
    sys.exit(0)


if __name__ == "__main__":
    main()
