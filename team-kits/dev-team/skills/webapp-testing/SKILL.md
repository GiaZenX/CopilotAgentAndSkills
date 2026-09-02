---
name: webapp-testing
description: >
  REFERENCE skill (no role owns it): how to drive a local web application with Playwright —
  reconnaissance-then-action, selector discovery, the networkidle rule, console logs. Open it when
  a work order names it. Adapted from anthropics/skills `webapp-testing`. NOT loaded at session
  start and named by no role's `skills:` frontmatter — open it with `/webapp-testing`. On Codex the
  generated mirror carries every skill directory, so it is also at
  `.agents/skills/webapp-testing/SKILL.md`.
license: Apache-2.0 — complete terms in LICENSE.txt beside this file
source: https://github.com/anthropics/skills/tree/main/skills/webapp-testing
source_commit: b9e19e6f44773509fbdd7001d77ff41a49a486c1
source_blob_sha1: 4726215301db64a0cc4d41fc3219c61f37a30f4a
modified: true
# WHICH ORDERS NAME THIS SKILL (FR-0071) -- read by `kernel.references.for_task`, which requires a
# match on BOTH axes. `test` is QA's regression and flow work, `ui` the surface both roles touch;
# the July survey judged exactly these two roles the direct fit.
reference_for:
  roles: [quality-engineer, frontend-developer]
  task_types: [ui, test]
---

# Web Application Testing

> **Modified from the upstream file.** Copyright the original authors, Apache-2.0 (`LICENSE.txt`
> beside this file). The changes are marked inline as `[MOD-n]` and listed under "Modifications" at
> the end, and those two are held to each other by
> `tools/test_reference_skills.py::test_every_modification_mark_is_listed_and_every_listed_one_is_marked`.
> What that CANNOT see is an edit carrying no mark at all: no test here reaches the network. What
> makes such an edit findable is the provenance in the frontmatter — `source_commit` and
> `source_blob_sha1` identify the exact upstream bytes, so a later round re-fetches and diffs
> instead of trusting this banner.

To test local web applications, write native Python Playwright scripts.

> **[MOD-1] The upstream `scripts/with_server.py` and `examples/` are NOT shipped with this copy,
> and every pointer to them is gone from the body below.** The reason is the kit's own boundary,
> measured in July: this kit's executable helpers live in `templates/repo/scripts/`, are refreshed
> by the scaffold and are covered by the enforcement layer's hashing; a second executable sitting
> beside a skill file would be a script the gates do not know. What survives is the RULE, which is
> the part worth having, retargeted at the scripts this kit does ship: **always run a bundled script
> with `--help` first, and do not read its source until you have run it and found that a customised
> solution is genuinely necessary.** They are large, and reading them costs context for nothing.
> Server lifecycle is yours to write inline (start it, wait for the port, tear it down) or to take
> from `scripts/quality.py` in the project.

## Decision Tree: Choosing Your Approach

```
User task → Is it static HTML?
    ├─ Yes → Read HTML file directly to identify selectors
    │         ├─ Success → Write Playwright script using selectors
    │         └─ Fails/Incomplete → Treat as dynamic (below)
    │
    └─ No (dynamic webapp) → Is the server already running?
        ├─ No → Start it yourself, wait for the port, and tear it down again
        │        (see [MOD-1]); then write a simplified Playwright script
        │
        └─ Yes → Reconnaissance-then-action:
            1. Navigate and wait for networkidle
            2. Take screenshot or inspect DOM
            3. Identify selectors from rendered state
            4. Execute actions with discovered selectors
```

## Example

An automation script contains only Playwright logic:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True) # Always launch chromium in headless mode
    page = browser.new_page()
    page.goto('http://localhost:5173') # Server already running and ready
    page.wait_for_load_state('networkidle') # CRITICAL: Wait for JS to execute
    # ... your automation logic
    browser.close()
```

## Reconnaissance-Then-Action Pattern

1. **Inspect rendered DOM**:
   ```python
   page.screenshot(path='project_memory/staging/<your task-id>/inspect.png', full_page=True)
   content = page.content()
   page.locator('button').all()
   ```

2. **Identify selectors** from inspection results

3. **Execute actions** using discovered selectors

> **[MOD-2] The screenshot path is the task's own staging directory, not `/tmp`.** Two reasons, and
> the second is the one that bites: `/tmp` does not exist on the Windows hosts this kit runs on, and
> anything an executor produces has to be findable by whoever reads the result — a file outside the
> project is a finding nobody can open. Staging is archived or emptied with the task, so a finding
> that must outlive the round goes into the result envelope as text.

> **[MOD-3] This skill is NOT a second way to take the screenshots this kit already takes.** Three
> routes exist and each has one subject: `python scripts/kit_design_render.py <task-id>` renders the
> STAGED DESIGN DRAFT before anyone has seen it (and writes the record `gate_design_sighted` reads);
> `scripts/kit_browser_checks.py` is the Tier-2 smoke over the BUILT app (mount element non-empty,
> console free of errors); `scripts/quality.py` carries the project's own flows. Use this skill to
> WRITE those product-specific flows and to debug a page interactively — never to add a fourth
> screenshot path beside the three, because then a gate reads one record and a role looks at
> another.

## Common Pitfall

❌ **Don't** inspect the DOM before waiting for `networkidle` on dynamic apps
✅ **Do** wait for `page.wait_for_load_state('networkidle')` before inspection

## Best Practices

- Use `sync_playwright()` for synchronous scripts
- Always close the browser when done
- Use descriptive selectors: `text=`, `role=`, CSS selectors, or IDs
- Add appropriate waits: `page.wait_for_selector()` or `page.wait_for_timeout()`

## Modifications from the upstream file (Apache-2.0 section 4(b))

Three changes. The upstream file was judged in `docs/research/2026-08-31-skill-survey.md` section 1 as the
closest fit of the whole survey — no end-user dialogue, no memory between tasks, file in / file out
— which is why the process half needed no rewriting at all and only the bundled assets and the
in-kit boundaries did.

- **[MOD-1]** the unshipped `scripts/with_server.py` + `examples/` pointers removed, the black-box
  `--help` rule kept and retargeted at this kit's own scripts
- **[MOD-2]** the screenshot path moved from `/tmp` into the task's staging directory
- **[MOD-3]** an added boundary: this skill writes flows, it is not a fourth screenshot route
