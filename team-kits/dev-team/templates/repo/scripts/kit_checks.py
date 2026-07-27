#!/usr/bin/env python3
"""
kit_checks.py — KIT-OWNED quality checks. DO NOT EDIT IN THE PROJECT.

Every kit update OVERWRITES this file (like the hooks), so kit-level check fixes reach existing
projects without a manual merge — a real project's 1,241-line quality.py fork never received the
kit's xdist/pitfall fixes because "diff the whole runner" was an unrealistic work order. Project-
specific checks belong in scripts/quality.py (the runner, copy-if-absent, yours to extend); it
imports this module and calls run_kit_checks().

Shipped checks:
  * project_memory yaml-lint (parse + duplicate keys, over the whole typed item tree) +
    repo-wide yaml parse of every git-tracked *.yaml (a real decisions.yaml shipped ~50
    unparsable items and the dashboard swallowed the ParserError silently); template YAMLs
    excludable via `yaml_lint_exclude:` (glob list) in coding/research_guidelines
  * state validity — the kernel's own fail-closed validator (spec II.4 gate 4) run here rather
    than only in the merge gate
  * frontend pitfalls (raw secure-context APIs; local-first external asset loads;
    chunkSizeWarningLimit must never be ASSIGNED — raising the threshold instead of
    code-splitting is a defect, not a fix)
  * module invariants (architecture rules as data: a `module_invariants:` list of files that
    must never contain given tokens — the pattern hand-rolled itself three times in one real
    project before becoming this config)
  * file budget (no source file beyond max_lines — the anti-monolith gate; configurable +
    exemptable with a reason via `file_budget:`)

The yaml-lint excludes, the module invariants and the file budget read their knobs from the kit's
guidelines file; `_knob_hint` below is the ONE place that decides which file that is and what to
tell a user when the project has none.
"""
import fnmatch
import os
import re
import sys

# Browser APIs that need a SECURE CONTEXT (https / localhost) — raw use is silently dead on a
# plain-http LAN origin, and jsdom/unit tests stay green (a real run shipped a browser-dead send
# button exactly this way). Route them through ONE helper with a fallback; mark the reviewed helper
# line with a `secure-context` comment to satisfy this check. Test files (mocks/spies name these
# APIs legitimately) and comment-only lines are exempt — a real project's App.test.tsx clipboard
# MOCKS turned the gate red and forced a spy workaround (confirmed kit false positive).
SECURE_CONTEXT_APIS = ("crypto.randomUUID", "navigator.clipboard")
_LOCAL_HOSTS = ("localhost", "127.0.0.1", "0.0.0.0", "[::1]")
_TEST_FILE_RX = re.compile(r"(\.test\.|\.spec\.|(^|/)(tests?|__tests__)/)", re.I)
# comment-ONLY lines (heuristic; inline code+comment lines are still scanned)
_COMMENT_LINE_RX = re.compile(r"^\s*(//|\*|/\*|#|<!--)")

# vendored/generated code is not ours to fix — a `.next/` chunk or a vendored lib containing
# crypto.randomUUID must not turn the gate red (dot-dirs, vendor dirs, *.min.* are skipped).
SKIP_DIRS = ("node_modules", "dist", "build", "__pycache__", ".venv", "venv", "coverage",
             "target", "vendor", "third_party")

# The anti-monolith gate. Default threshold: hand-written source files stay below this many lines;
# a real App.tsx grew to 8,966 lines (+666 in one session) while its ui/ component library sat
# 100% unused — visibility flags alone demonstrably did nothing. Projects tune/exempt via the
# guidelines file (see _GUIDELINE_FILES):
#   file_budget:
#     max_lines: 800            # tighten for UI-heavy projects (e.g. 500)
#     exempt:
#       - path: frontend/src/app/App.tsx
#         reason: "legacy monolith — split tracked in TSK-0181"
FILE_BUDGET_DEFAULT = 800
_BUDGET_EXTS = {".py", ".js", ".mjs", ".ts", ".tsx", ".jsx", ".css", ".html", ".go", ".rs",
                ".c", ".cpp", ".h", ".cs", ".java", ".svelte", ".vue"}
# DEFAULT scan areas — projects with additional top-level packages MUST list them via
# `source_areas:` in the guidelines file (see _GUIDELINE_FILES). A real project
# kept its whole codebase under compounder/ and "PASS file budget" was false-green for weeks
# (an 1,111-line file went undetected) because this tuple silently never matched anything.
_BUDGET_AREAS = ("src", "frontend", "scripts", "tests", "static", "public")


def _run_git(root, *args, timeout=30):
    """THE one git call site in this module: pinned UTF-8 decode (Windows' cp1252 mojibaked
    umlaut paths/messages — a recurring audit class) and core.quotepath=off (git otherwise
    octal-escapes non-ASCII paths, "M\\303\\274ller.yaml", and downstream isfile() checks
    silently skip real files)."""
    import subprocess
    return subprocess.run(["git", "-C", root, "-c", "core.quotepath=off", *args],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout)


def load_project_yaml(root, name):
    """Parse ONE project_memory YAML into a dict; {} when the file or pyyaml is missing or the
    text does not parse. THE structured reader for every config knob — an audit caught the same
    knob (source_areas) read by two diverging hand-rolled parsers (block-only regex vs yaml),
    silently scanning different areas. quality.py and kit_browser_checks call this too; their
    regex readers remain only as a pyyaml-less fallback. utf-8-sig: PS 5.1 writes a BOM."""
    p = os.path.join(root, "project_memory", name)
    if not os.path.isfile(p):
        return {}
    try:
        if os.path.getsize(p) > 2_000_000:
            return {}  # a multi-MB config would stall the BLOCKING hook path (audit: 15s/9MB)
        import yaml  # type: ignore[import-untyped]
        data = yaml.safe_load(open(p, encoding="utf-8-sig", errors="ignore").read())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


# The tuning knobs below (file_budget, source_areas, module_invariants, yaml_lint_exclude) are
# read from the kit's guidelines file. V2 dissolved the dev kit's coding_guidelines.yaml into INV
# items and has NOT yet decided where those knobs live (phase-0 disposition: "neue Heimat"), so a
# check must never print that filename as the way out: the scaffold no longer creates the file and
# gate_write_scope would refuse the write anyway. `_knob_hint` answers "where do I declare this?"
# from what the project actually has.
_GUIDELINE_FILES = ("coding_guidelines.yaml", "research_guidelines.yaml")


def _knob_hint(root, knob):
    """A walkable answer to "where do I declare `knob`?", or an honest "nowhere yet"."""
    for name in _GUIDELINE_FILES:
        if load_project_yaml(root, name):
            return "declare `%s:` in project_memory/%s" % (knob, name)
    return ("`%s:` has no home in this project — the guidelines monolith is gone in V2 and its "
            "config knobs have not been rehomed yet, so report the need instead of recreating "
            "the file" % knob)


def _more(items, shown):
    """Honest truncation: a display cut to the first N hits once made a PM report 'almost green'
    to the user while 13 findings were hidden — every truncated list says exactly how many more."""
    return " (+%d more)" % (len(items) - shown) if len(items) > shown else ""


def _local_first_declared(root):
    p = os.path.join(root, "project_memory", "project_config.yaml")
    try:
        return bool(re.search(r"(?m)^\s*local_first:\s*true\b",
                              open(p, encoding="utf-8", errors="ignore").read()))
    except Exception:
        return False


def _frontend_sources(root):
    """Browser-facing sources: everything under frontend/static/public, plus .html anywhere in src/
    and js/css under a static|public|www subdir of src/ (vanilla apps served by the backend). Plain
    backend .js under src/ is deliberately excluded — Node has no secure-context restriction."""
    exts = {".js", ".mjs", ".ts", ".jsx", ".tsx", ".html", ".css", ".svelte", ".vue"}
    for rel, browser_only in (("frontend", False), ("static", False), ("public", False), ("src", True)):
        d = os.path.join(root, rel)
        if not os.path.isdir(d):
            continue
        for dp, dn, fn in os.walk(d):
            dn[:] = [x for x in dn if x not in SKIP_DIRS and not x.startswith(".")]
            for f in fn:
                ext = os.path.splitext(f)[1].lower()
                if ext not in exts:
                    continue
                if browser_only and ext != ".html":
                    parts = os.path.relpath(dp, root).replace("\\", "/").split("/")
                    if not {"static", "public", "www"} & set(parts):
                        continue
                yield os.path.join(dp, f)


def check_frontend_pitfalls(root, ok, fail, warn):
    """Greps for what jsdom-green tests cannot catch: (a) raw secure-context-only APIs (see
    SECURE_CONTEXT_APIS above); (b) with project_config `local_first: true`, frontend RESOURCES
    loaded from an external origin (CDN fonts/scripts — a real local-first run shipped a Google-CDN
    font no gate caught). Only resource loads count (link/script/img src, css url()/@import) — a
    plain <a href> link to an external site stays legal."""
    api_hits, cdn_hits, scanned = [], [], False
    local_first = _local_first_declared(root)
    # (?:https?:)?// also catches protocol-relative loads like href="//fonts.googleapis.com/…"
    res_html = re.compile(r"<(?:link|script|img)\b[^>]*?(?:href|src)\s*=\s*[\"']((?:https?:)?//[^\"']+)", re.I)
    res_css = re.compile(r"(?:url\(\s*[\"']?|@import\s+[\"'])((?:https?:)?//[^\"')]+)", re.I)
    for path in _frontend_sources(root):
        scanned = True
        rel = os.path.relpath(path, root)
        minified = os.path.basename(path).lower().endswith((".min.js", ".min.css"))
        is_test = bool(_TEST_FILE_RX.search(rel.replace("\\", "/")))
        try:
            lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
        except Exception:
            continue
        prev = ""
        for i, line in enumerate(lines, 1):
            # minified bundles keep API names but are vendored — only OUR code gets the API grep;
            # the local-first RESOURCE grep still applies (an external font in a .min.css is a violation)
            if not minified and not is_test and any(api in line for api in SECURE_CONTEXT_APIS):
                if ("secure-context" not in line and "secure-context" not in prev
                        and not _COMMENT_LINE_RX.match(line)):
                    api_hits.append("%s:%d" % (rel, i))
            if local_first and os.path.splitext(path)[1].lower() in (".html", ".css"):
                for rx in (res_html, res_css):
                    for m in rx.finditer(line):
                        if not any(h in m.group(1) for h in _LOCAL_HOSTS):
                            cdn_hits.append("%s:%d %s" % (rel, i, m.group(1)[:80]))
            prev = line
    if api_hits:
        fail("secure-context APIs", "raw %s used (%s%s) — silently dead on a non-secure origin "
             "(http:// over LAN); use ONE helper with a fallback and mark it `secure-context`"
             % ("/".join(SECURE_CONTEXT_APIS), "; ".join(api_hits[:5]), _more(api_hits, 5)))
    if cdn_hits:
        fail("local-first assets", "external asset load(s) in a local_first project: %s%s — bundle "
             "them locally (fonts/scripts/styles must not leave the machine)"
             % ("; ".join(cdn_hits[:5]), _more(cdn_hits, 5)))
    if scanned and not api_hits and not cdn_hits:
        ok("frontend pitfalls (secure-context%s)" % (", local-first assets" if local_first else ""))


_WARNLIMIT_RX = re.compile(r"chunkSizeWarningLimit\s*[:=]")
_VITE_CONFIGS = ("vite.config.ts", "vite.config.js", "vite.config.mts", "vite.config.mjs")


def check_frontend_build_config(root, ok, fail, warn):
    """`chunkSizeWarningLimit` must never be ASSIGNED in a vite config: raising Vite's 500 kB
    chunk-warning threshold to silence the warning (instead of code-splitting) is a defect
    masquerading as a fix — a real project ratified exactly this rule after catching the bump in
    review. Matches the key followed by :/= only, so a protective COMMENT that merely mentions
    the key never trips the guard."""
    fe = os.path.join(root, "frontend")
    checked, hits = 0, []
    for fn in _VITE_CONFIGS:
        for base in (fe, root):
            p = os.path.join(base, fn)
            if not os.path.isfile(p):
                continue
            checked += 1
            try:
                for i, line in enumerate(open(p, encoding="utf-8", errors="ignore"), 1):
                    if _WARNLIMIT_RX.search(line):
                        hits.append("%s:%d" % (os.path.relpath(p, root).replace("\\", "/"), i))
            except Exception:
                continue
    if hits:
        fail("frontend build config", "chunkSizeWarningLimit is ASSIGNED (%s%s) — raising the "
             "warning threshold hides an unsplit bundle; fix by code-splitting, never by raising "
             "the limit" % ("; ".join(hits[:3]), _more(hits, 3)))
    elif checked:
        ok("frontend build config (chunkSizeWarningLimit never assigned)")


def check_project_memory_yaml(root, ok, fail, warn):
    """Every YAML under project_memory/ must parse and carry no duplicate keys (safe_load keeps
    only the last duplicate silently). The write-time hook (guard_yaml_valid) catches Edit/Write
    immediately — this stage is the merge/CI backstop and the ONLY one that also sees
    shell-written files.

    The walk is RECURSIVE because the V2 state is one file per item under
    `project_memory/<type>/active/` (spec II.2): a top-level-only listing is what the monolith era
    needed and would now scan an almost empty directory while every real item went unchecked —
    and `_repo_wide_yaml_parse` skips project_memory/ on the promise that this pass is the
    stricter one. It is the same defect the write-time guard was fixed for one layer up, where a
    path is now accepted on its `project_memory` SEGMENT rather than on its parent directory.

    `archive/` is the one subtree left out, for the same reason `_repo_wide_yaml_parse` caps file
    size: this runs on every merge and CI reads it cold. An archived item is frozen — it was
    linted while it was active, nothing may write it again, and the kernel's own validator does
    not scan it either (`_iter_active`), so re-parsing a monotonically growing history twice per
    file would buy nothing and cost seconds that grow forever. The parse step uses the C loader for
    the same reason, wherever PyYAML ships it; the duplicate-key pass stays on the Python composer,
    which is the node API this walk was written against."""
    d = os.path.join(root, "project_memory")
    if not os.path.isdir(d):
        return
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        warn("yaml-lint (project_memory)", "pyyaml not installed; runs + hard-fails in CI")
        return
    loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)

    def dup_keys(text):
        found = []
        try:
            node_root = yaml.compose(text, Loader=yaml.SafeLoader)
        except Exception:
            return found
        stack = [node_root] if node_root is not None else []
        visited = set()  # anchors/aliases make the node graph cyclic — never walk a node twice
        while stack:
            node = stack.pop()
            if id(node) in visited:
                continue
            visited.add(id(node))
            if isinstance(node, yaml.MappingNode):
                seen = set()
                for k, v in node.value:
                    if isinstance(k, yaml.ScalarNode):
                        if k.value in seen:
                            found.append("duplicate key %r line %d" % (k.value, k.start_mark.line + 1))
                        seen.add(k.value)
                    stack.append(k)
                    stack.append(v)
            elif isinstance(node, yaml.SequenceNode):
                stack.extend(node.value)
        return found

    bad = []
    for dp, dn, fn in os.walk(d):
        dn[:] = sorted(x for x in dn if x not in SKIP_DIRS and not x.startswith("."))
        if dp == d:
            dn[:] = [x for x in dn if x != "archive"]  # frozen history, see the docstring
        for name in sorted(fn):
            if not name.endswith((".yaml", ".yml")):
                continue
            rel = os.path.relpath(os.path.join(dp, name), d).replace("\\", "/")
            try:
                text = open(os.path.join(dp, name), encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            try:
                yaml.load(text, Loader=loader)
            except yaml.YAMLError as e:
                bad.append("%s: %s" % (rel, str(e).splitlines()[0]))
                continue
            for msg in dup_keys(text):
                bad.append("%s: %s" % (rel, msg))
    ok("yaml-lint (project_memory)") if not bad else fail(
        "yaml-lint (project_memory)", "; ".join(bad[:6]) + _more(bad, 6))
    _repo_wide_yaml_parse(root, yaml, ok, fail, warn)


def _yaml_lint_excludes(root):
    """Glob patterns from coding/research_guidelines `yaml_lint_exclude:` — Helm/Jinja-templated
    YAMLs are legitimately unparsable and must not turn the repo-wide parse red."""
    out = []
    for name in _GUIDELINE_FILES:
        data = load_project_yaml(root, name)
        out += [str(g).replace("\\", "/") for g in (data.get("yaml_lint_exclude") or [])]
    return out


def _repo_wide_yaml_parse(root, yaml, ok, fail, warn):
    """Parse EVERY git-tracked *.yaml/*.yml, not only project_memory/ — a real decisions.yaml
    shipped ~50 unparsable items while the dashboard generator swallowed the ParserError silently
    (upstreamed from a live project's fork). Parse-only outside project_memory (which already got
    the stricter duplicate-key pass above). Requires git (no tracked files -> skip
    silently); files beyond the size cap are skipped WITH a warn (a multi-MB pnpm-lock.yaml must
    not cost the gate minutes — audit finding); the C loader is used when available."""
    try:
        r = _run_git(root, "ls-files", "*.yaml", "*.yml")
        files = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()] if r.returncode == 0 else []
    except Exception:
        files = []
    if not files:
        return  # no git / nothing tracked — project_memory pass above already ran
    excludes = _yaml_lint_excludes(root)
    loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
    bad, skipped_big, count = [], [], 0
    for rel in files:
        rel_norm = rel.replace("\\", "/")
        if rel_norm.startswith("project_memory/"):
            continue  # covered by the stricter pass above
        if any(fnmatch.fnmatch(rel_norm, pat) for pat in excludes):
            continue
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            continue  # tracked but deleted in the working tree
        try:
            if os.path.getsize(path) > 1_000_000:
                skipped_big.append(rel_norm)
                continue
        except OSError:
            continue
        count += 1
        try:
            yaml.load(open(path, encoding="utf-8", errors="ignore").read(), Loader=loader)
        except yaml.YAMLError as e:
            first = str(e).splitlines()[0]
            mark = getattr(e, "problem_mark", None)
            where = ":%d" % (mark.line + 1) if mark else ""
            bad.append("%s%s: %s" % (rel_norm, where, first))
        except Exception:
            continue
    if skipped_big:
        warn("yaml-lint (repo-wide)", "skipped %d file(s) over 1 MB (%s%s) — too big for a "
             "pure-Python parse in the gate; lint them in CI if they matter"
             % (len(skipped_big), "; ".join(skipped_big[:3]), _more(skipped_big, 3)))
    if bad:
        fail("yaml-lint (repo-wide)", "; ".join(bad[:6]) + _more(bad, 6)
             + " — genuinely templated YAML (Helm/Jinja) is excludable: %s"
             % _knob_hint(root, "yaml_lint_exclude"))
    elif count:
        ok("yaml-lint (repo-wide, %d tracked file(s))" % count)


def check_module_invariants(root, ok, fail, warn):
    """Architecture invariants as DATA: coding/research_guidelines `module_invariants:` lists
    files that must never contain given tokens (e.g. a pure classifier module that must stay
    I/O-free). A real project hand-rolled this guard three separate times (provenance, hardware
    scoring, single-DB-connection) — the duplication is the proof the config knob belongs here.
      module_invariants:
        - path: src/scoring/percent_match.py
          forbidden_tokens: ["import aiosqlite", "open("]
          reason: "pure scoring module — all I/O lives in the store layer (ADR-0034)"
    """
    rules = []
    for name in _GUIDELINE_FILES:
        data = load_project_yaml(root, name)
        for entry in (data.get("module_invariants") or []):
            if (isinstance(entry, dict) and entry.get("path")
                    and entry.get("forbidden_tokens")):
                rules.append(entry)
    if not rules:
        return
    hits, stale, effective = [], [], 0
    for rule in rules:
        rel = str(rule["path"]).replace("\\", "/")
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            stale.append(rel)
            continue
        effective += 1
        try:
            lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
        except Exception:
            continue
        tokens = rule["forbidden_tokens"]
        if isinstance(tokens, str):
            tokens = [tokens]  # a bare string would otherwise iterate CHARACTERS (audit repro)
        for i, line in enumerate(lines, 1):
            if _COMMENT_LINE_RX.match(line):
                continue  # prose may legitimately NAME the forbidden token
            for tok in tokens:
                if str(tok) in line:
                    hits.append("%s:%d contains %r — %s"
                                % (rel, i, str(tok), str(rule.get("reason") or "invariant")))
    if hits:
        fail("module invariants", "; ".join(hits[:5]) + _more(hits, 5))
        return
    if stale:
        warn("module invariants", "declared file(s) missing: %s — update module_invariants "
             "in the guidelines (a stale rule guards nothing)" % "; ".join(stale[:4]))
    if effective:  # never count dead rules as a PASS (audit: stale-only showed warn AND ok)
        ok("module invariants (%d rule(s))" % effective)


def _count_lines(path):
    """Physical line count WITHOUT the trailing-newline off-by-one: an exactly-800-line file with a
    final newline is 800 lines, not 801."""
    with open(path, "rb") as fh:
        data = fh.read()
    if not data:
        return 0
    return data.count(b"\n") + (0 if data.endswith(b"\n") else 1)


def _budget_config(root):
    """file_budget + source_areas from whichever guidelines file the project has (`_GUIDELINE_FILES`,
    and `_knob_hint` for what to tell a user who has none): {max_lines, exempt: [{path, reason}],
    areas}. Both knobs are homeless in a V2 dev project — see the comment above `_GUIDELINE_FILES` —
    so the defaults below are what a dev project actually runs with today.
    Exemptions are architect-owned and REQUIRE a reason — a bare path does not count.
    `source_areas:` (top-level key) EXTENDS the default scan areas; it can never remove them
    (removing would silently un-gate src/ — the false-green class this key exists to kill)."""
    max_lines, exempt, areas = FILE_BUDGET_DEFAULT, {}, list(_BUDGET_AREAS)
    for name in _GUIDELINE_FILES:
        data = load_project_yaml(root, name)
        if not data:
            continue
        declared = data.get("source_areas")
        # list-guard: a scalar `source_areas: src` would iterate CHARACTERS (audit repro)
        for extra in (declared if isinstance(declared, list) else []):
            name_clean = str(extra).strip().strip("/").replace("\\", "/")
            # the char class blocks separators, but NOT dot-only names: '..' walked the
            # PARENT directory in an audit repro — a scan area must be a real child name
            if (re.fullmatch(r"[A-Za-z0-9_.-]+", name_clean)
                    and set(name_clean) != {"."} and name_clean not in areas):
                areas.append(name_clean)
        cfg = data.get("file_budget") or {}
        if isinstance(cfg, dict) and cfg:
            if isinstance(cfg.get("max_lines"), int) and cfg["max_lines"] > 0:
                max_lines = cfg["max_lines"]
            for entry in (cfg.get("exempt") or []):
                if isinstance(entry, dict) and entry.get("path") and str(entry.get("reason") or "").strip():
                    exempt[str(entry["path"]).replace("\\", "/")] = str(entry["reason"])
            break
    return max_lines, exempt, areas


def source_files(root):
    """Yields (relative path, line count) for every file the file budget covers.

    THE definition of "a hand-written source file of this project" — scan areas, the
    vendored/generated skip list, the extension set and the `.min.*` exclusion in ONE place.
    Public because the dashboard's repo-vitals panel reports on exactly the files this gate
    enforces: it used to carry its own copy of the extension set, its own minified filter and a
    third line counter, and a panel that disagrees with the gate is worse than no panel.

    The line count is None for a file that cannot be read. That case still has to be yielded:
    it proves the scan area matched, and the budget check's "NO scan area matched" warning must
    not fire for a directory that plainly holds sources.
    """
    for area in _budget_config(root)[2]:
        d = os.path.join(root, area)
        if not os.path.isdir(d):
            continue
        for dp, dn, fn in os.walk(d):
            dn[:] = [x for x in dn if x not in SKIP_DIRS and not x.startswith(".")]
            for f in fn:
                if os.path.splitext(f)[1].lower() not in _BUDGET_EXTS:
                    continue
                if f.lower().endswith((".min.js", ".min.css")):
                    continue
                path = os.path.join(dp, f)
                rel = os.path.relpath(path, root).replace("\\", "/")
                try:
                    yield rel, _count_lines(path)
                except Exception:
                    yield rel, None


def check_file_budget(root, ok, fail, warn):
    """No hand-written source file beyond max_lines. Deterministic anti-monolith gate: split the
    file or add an architect-owned exemption WITH a reason (visible, reviewable) — never both grow
    silently. Which files count is `source_files()` (vendored/generated/minified/dot-dirs skipped)."""
    max_lines, exempt, areas = _budget_config(root)
    offenders, scanned = [], False
    for rel, n in source_files(root):
        scanned = True
        if n is None:
            continue
        if n > max_lines and rel not in exempt:
            offenders.append((rel, n))
    if offenders:
        offenders.sort(key=lambda t: -t[1])
        fail("file budget (<=%d lines)" % max_lines,
             "%d file(s) over budget: %s%s — SPLIT them into modules (a real App.tsx reached 8,966 "
             "lines while its ui/ library sat unused); an architect-owned exemption WITH a reason "
             "is the only alternative: %s"
             % (len(offenders), "; ".join("%s (%d)" % o for o in offenders[:5]), _more(offenders, 5),
                _knob_hint(root, "file_budget: exempt")))
    elif scanned:
        ok("file budget (<=%d lines%s)" % (max_lines, ", %d exemption(s)" % len(exempt) if exempt else ""))
    else:
        # NEVER stay silent: a project that keeps its code under an unlisted top-level package
        # would otherwise read every report as budget-green (real incident: compounder/ was never
        # scanned and an 1,111-line file went undetected for weeks).
        warn("file budget",
             "NO scan area matched (%s) — the project's top-level source package(s) must be "
             "declared: %s" % (", ".join(areas), _knob_hint(root, "source_areas")))


# Enforcement files no agent may change inside a project (provider-NEUTRAL second line of
# defense: session hooks only exist on the CLI that ran them — a git-level check catches shell
# bypasses and other CLIs; documented real-world compromise pattern is rewriting instruction
# files outside any reviewed diff). A kit update legitimately changes them — and always changes
# .claude/kit_version in the same diff, which lifts the gate.
_ENFORCEMENT_HARD = ("AGENTS.md", "CLAUDE.md", ".claude/hooks/", ".claude/settings.json",
                     ".claude/settings.local.json", ".claude/provider_artifacts.json",
                     ".claude/team_kit_roles.txt", ".codex/", ".agents/skills/",
                     ".github/hooks/")
_ENFORCEMENT_SOFT = (".github/workflows/", "scripts/quality.py", "scripts/kit_checks.py",
                     "scripts/kit_browser_checks.py")


def check_enforcement_diff(root, ok, fail, warn):
    """Diff the current branch against the main branch: hard-fail on enforcement-layer changes
    without a kit-version change; warn on CI/gate-file changes and deleted test files ("any
    change that weakens CI is a blocker" — the reviewer must SEE it)."""
    base = ""
    for cand in ("origin/main", "main", "master"):
        try:
            r = _run_git(root, "rev-parse", "--verify", "--quiet", cand, timeout=10)
            if r.returncode == 0:
                base = cand
                break
        except Exception:
            return
    if not base:
        return  # no base branch (fresh repo) — nothing to diff against

    def _rev(name):
        try:
            r = _run_git(root, "rev-parse", name, timeout=10)
            return r.stdout.strip() if r.returncode == 0 else ""
        except Exception:
            return ""

    def _diff(*args):
        try:
            r = _run_git(root, "diff", "--name-status", *args)
            return r.stdout.splitlines() if r.returncode == 0 else []
        except Exception:
            return []

    if _rev("HEAD") and _rev("HEAD") == _rev(base):
        # HEAD *is* the base branch (solo/trunk workflow): base...HEAD is empty, so a tampered
        # commit straight to main would pass silently (audit finding) — check the last commit
        # plus the working tree instead of a false green.
        lines = _diff("HEAD~1...HEAD")  # may be empty on the root commit
        scope = "last commit + working tree (HEAD is the base)"
    else:
        lines = _diff(base + "...HEAD")
        scope = "vs %s" % base
    lines += _diff("HEAD")  # uncommitted working-tree/index changes count in every mode
    changed, deleted = [], []
    for line in lines:
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status, path = parts[0], parts[-1].replace("\\", "/")
        changed.append(path)
        if status.startswith("D"):
            deleted.append(path)
    if not changed:
        ok("enforcement diff (no changes, %s)" % scope)
        return
    kit_updated = any(p == ".claude/kit_version" for p in changed)
    hard = [p for p in changed
            if any(p == e or p.startswith(e) for e in _ENFORCEMENT_HARD)]
    if hard and not kit_updated:
        fail("enforcement diff", "enforcement-layer file(s) changed in this branch WITHOUT a kit "
             "update: %s%s — no agent (or shell command) edits hooks/settings/the constitution in "
             "a project; harness changes arrive via a kit update (which stamps .claude/kit_version "
             "in the same diff). Revert these, or run the real kit update."
             % ("; ".join(hard[:5]), _more(hard, 5)))
        return
    soft = [p for p in changed
            if any(p == e or p.startswith(e) for e in _ENFORCEMENT_SOFT)]
    dead_tests = [p for p in deleted
                  if p.startswith("tests/") or "/tests/" in p or ".test." in p or ".spec." in p]
    notes = []
    if soft and not kit_updated:
        notes.append("gate/CI file(s) changed: %s%s" % ("; ".join(soft[:4]), _more(soft, 4)))
    if dead_tests:
        notes.append("test file(s) DELETED: %s%s" % ("; ".join(dead_tests[:4]), _more(dead_tests, 4)))
    if notes:
        warn("enforcement diff", "review deliberately: %s — any change that weakens CI/tests is a "
             "blocker unless explicitly approved (record the approval as a decision item under "
             "project_memory/decisions/active/)" % " | ".join(notes))
    else:
        ok("enforcement diff (%s)" % scope)


def check_state_validity(root, ok, fail, warn):
    """The state kernel's own fail-closed validation (spec II.4 gate 4), run in the pipeline.

    Without this the full graph scan — duplicate ids, unreadable item files, an approval whose
    expiry disagrees with the request it was minted from, a task deriving from a foreign root —
    happens only in the merge gate, i.e. the first time somebody tries to merge, which is the
    latest possible moment to learn that the state is broken.

    The kernel is reached through `.claude/hooks/_kernel.py`, the ONE module that knows where the
    kernel lives, so this reports on exactly the kernel the gates enforce — or says that it could
    not reach it. It never reports "valid" on a validator it did not run.
    """
    if not os.path.isdir(os.path.join(root, "project_memory")):
        return  # no canonical state (a plain repo running the quality pipeline)
    bridge_dir = os.path.join(root, ".claude", "hooks")
    if not os.path.isfile(os.path.join(bridge_dir, "_kernel.py")):
        warn("state validity", "no .claude/hooks/_kernel.py, so the state validator was NOT run "
                               "— re-run the team scaffold for this repo")
        return
    if bridge_dir not in sys.path:
        sys.path.insert(0, bridge_dir)
    try:
        import _kernel  # type: ignore[import-not-found]
        # importing the bridge arms the gate excepthook; this process is a report runner, so an
        # ordinary exception here must stay an exception instead of becoming "the hook failed"
        _kernel.disarm()
        report = _kernel.kernel_module("report", root)
        findings = report.validate_state(_kernel.open_state(root))
    except Exception as exc:
        warn("state validity", "the state validator could not run (%s: %s) — `harness doctor` "
             "names what is missing" % (type(exc).__name__, exc))
        return
    errors = [f for f in findings if f.get("severity") == "error"]
    others = [f for f in findings if f.get("severity") != "error"]

    def _line(f):
        return "%s: %s (%s)" % (f.get("item"), f.get("message"), f.get("remedy"))

    if errors:
        fail("state validity", "%d state error(s): %s%s"
             % (len(errors), "; ".join(_line(f) for f in errors[:5]), _more(errors, 5)))
        return
    if others:
        warn("state validity", "%d state warning(s): %s%s"
             % (len(others), "; ".join(_line(f) for f in others[:5]), _more(others, 5)))
        return
    ok("state validity (kernel validator, 0 findings)")


def check_ops_pitfalls(root, ok, fail, warn):
    """Deterministic ops tripwires. Compose without a pinned top-level `name:` derives the
    project name from the FOLDER — after a folder rename, `docker compose` silently created a
    fresh empty volume while 6.27M rows of production data sat in the old one (real incident,
    caught hours before data entry would have diverged)."""
    for name in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
        p = os.path.join(root, name)
        if not os.path.isfile(p):
            continue
        try:
            head = open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        if not re.search(r"(?m)^name\s*:", head):
            warn("ops: compose project name",
                 "%s has no top-level `name:` — compose derives it from the FOLDER name, and "
                 "a folder rename then silently detaches your volumes (a real project nearly lost "
                 "its price database). Pin `name: <project>`." % name)
        else:
            ok("ops: compose project name pinned (%s)" % name)


def run_kit_checks(root, ok, fail, warn):
    """Entry point for scripts/quality.py — runs every kit-owned check."""
    check_project_memory_yaml(root, ok, fail, warn)
    check_state_validity(root, ok, fail, warn)
    check_frontend_pitfalls(root, ok, fail, warn)
    check_frontend_build_config(root, ok, fail, warn)
    check_module_invariants(root, ok, fail, warn)
    check_file_budget(root, ok, fail, warn)
    check_ops_pitfalls(root, ok, fail, warn)
    check_enforcement_diff(root, ok, fail, warn)
