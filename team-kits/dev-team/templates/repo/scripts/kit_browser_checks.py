#!/usr/bin/env python3
"""
kit_browser_checks.py — KIT-OWNED browser smoke (Tier 2). DO NOT EDIT IN THE PROJECT.

Serves the PRODUCTION build (`vite preview` on frontend/dist) and drives a real Chromium via
Playwright: the configured mount element must render non-empty and the console must stay free of
errors. This exists because jsdom-green unit tests shipped two REAL browser bugs in a live
project (a dead send button, a white screen): jsdom/Node always have crypto.randomUUID and always
count as a secure context — the actual failure (randomUUID throwing on a plain-http LAN origin)
is only observable in a real browser against the real build.

Config (optional) as an INV item:
  scope: browser_smoke
  value:
    entry: /             # path to open on the preview server
    mount_selector: "#root"   # element that must render non-empty

Degrades honestly: playwright or npx missing -> warn locally (CI installs + enforces); missing
frontend/dist -> warn (the build step reports its own failure; never double-fail). Product-
specific click-flows do NOT belong here — extend scripts/quality.py in the project for those.
Runtime budget: one preview boot + one page load; keep it well under the gate's hook timeout.

Every kit update OVERWRITES this file (like kit_checks.py), so fixes reach existing projects.
"""
import hashlib
import os
import socket
import subprocess
import time


def _config(root):
    """entry + mount_selector from the `browser_smoke` invariant's `value` — one reader.

    V1 read `browser_smoke:` out of `testing_guidelines.yaml`, a monolith V2 deleted and no kit
    ships a template for, so the knob was unreachable and the smoke always tested `/` and `#root`.
    It is an INV item now (`kit_checks.invariant_knob`). The regex fallback that used to stand
    beside this is gone with it: it existed for a machine without pyyaml, and without pyyaml the
    item store cannot be read at all — a second parser could only have disagreed with the first.
    """
    entry, mount = "/", "#root"
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import kit_checks
        cfg = kit_checks.invariant_knob(root, "browser_smoke")
    except Exception:
        return entry, mount
    if isinstance(cfg, dict):
        entry = str(cfg.get("entry") or entry).strip() or entry
        mount = str(cfg.get("mount_selector") or mount).strip() or mount
    return entry, mount


def _free_port():
    """A currently-free TCP port — hardcoding 4173 collided with parallel runs/leftover servers."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _terminate_process_tree(proc):
    """Windows: the Popen child is the shell/npx shim; the real `vite preview` node process is a
    GRANDCHILD that survives a plain terminate() — a live project found genuinely orphaned
    preview servers minutes after its gate runs (chronic memory pressure). taskkill /T kills the
    whole tree by PID lineage; POSIX terminate() already reaches the real process."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.terminate()
    try:
        proc.wait(timeout=10)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def _file_hash(path):
    """sha256 of a file, or None when it cannot be read (the caller then says nothing)."""
    try:
        with open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()
    except OSError:
        return None


def _served_index_hash(base):
    """sha256 of the index the server actually returns, or None when it cannot be fetched.

    None rather than a failure: a project with a custom entry, an auth wall or a redirect is not
    misconfigured, and this check has nothing to say about it. It speaks only when it can compare
    two concrete byte strings.
    """
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(base, timeout=5) as response:
            if response.status != 200:
                return None
            return hashlib.sha256(response.read()).hexdigest()
    except (urllib.error.URLError, OSError, ValueError):
        return None


def browser_smoke(root, ok, fail, warn):
    """Entry point for scripts/quality.py's node stage."""
    name = "frontend browser smoke (vite preview + Playwright)"
    fe = os.path.join(root, "frontend")
    if not os.path.isfile(os.path.join(fe, "dist", "index.html")):
        warn(name, "frontend/dist missing — the build step reports its own failure")
        return
    try:
        from playwright.sync_api import sync_playwright  # type: ignore[import-not-found]
    except ImportError:
        warn(name, "playwright (Python) not installed — add it to requirements-dev.txt and run "
                   "`playwright install chromium`; CI enforces this")
        return
    import shutil as _shutil
    if not _shutil.which("npx"):
        warn(name, "npx not available — cannot start `vite preview`")
        return
    import urllib.error
    import urllib.request

    entry, mount = _config(root)
    port = _free_port()
    url = "http://localhost:%d%s" % (port, entry if entry.startswith("/") else "/" + entry)
    env = os.environ.copy()
    for var in ("ELECTRON_RUN_AS_NODE", "ELECTRON_NO_ATTACH_CONSOLE"):
        env.pop(var, None)
    proc = subprocess.Popen(
        ["npx", "--no-install", "vite", "preview", "--port", str(port), "--strict-port"],
        cwd=fe, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        encoding="utf-8", errors="replace", shell=(os.name == "nt"), env=env)
    try:
        # probe the server ROOT, not entry: a 404 on a custom entry (HTTPError) still proves the
        # server is up — entry itself is judged by the browser below. A preview process that
        # dies immediately must fail FAST with its own output, not after 45s of silence (audit).
        base = "http://localhost:%d/" % port
        ready = False
        for _ in range(30):
            if proc.poll() is not None:
                out = (proc.stdout.read() if proc.stdout else "") or ""
                fail(name, "`vite preview` exited immediately (rc=%s)%s"
                     % (proc.returncode, (" :: " + out.strip()[-500:]) if out.strip() else ""))
                return
            try:
                urllib.request.urlopen(base, timeout=1)
                ready = True
                break
            except urllib.error.HTTPError:
                ready = True  # server responded (even 404) — it is up
                break
            except (urllib.error.URLError, OSError):
                time.sleep(0.5)
        if not ready:
            fail(name, "`vite preview` did not become ready on %s" % base)
            return

        # DELIVERY FRESHNESS (parity risk R6): what the server hands out must BE the build output.
        # A green smoke test against a stale bundle is the worst kind of pass -- it certifies code
        # that is not the code under review. The failure is silent by nature: a leftover dev server
        # on the port, a `dist/` from a previous branch, or a service worker replaying a cached
        # shell all render fine and all lie about what was tested.
        served_hash = _served_index_hash(base)
        built_hash = _file_hash(os.path.join(fe, "dist", "index.html"))
        if served_hash and built_hash and served_hash != built_hash:
            fail(name, "the server is not serving this build: index.html sha256 %s on disk vs %s "
                       "served. A pass here would certify a bundle nobody built — rebuild "
                       "(`npm run build`) and make sure no other server holds the port."
                 % (built_hash[:12], served_hash[:12]))
            return

        console_errors = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.on("console",
                        lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
                page.goto(url, wait_until="networkidle", timeout=15000)
                mount_html = page.inner_html(mount)
                browser.close()
        except Exception as exc:
            # missing BROWSER BINARY is a setup gap, not a product failure: requirements-dev
            # installs the playwright PACKAGE by default, so package-yes/browser-no is every
            # fresh machine's state — keep the documented warn degradation (CI enforces).
            # Every other Playwright/browser failure stays a real gate FAIL.
            msg = str(exc)
            if "Executable doesn't exist" in msg or "playwright install" in msg:
                warn(name, "Playwright browser not installed — run `playwright install "
                           "chromium` once; CI enforces this")
            else:
                fail(name, "Playwright run errored: %s" % exc)
            return
        if not mount_html.strip():
            fail(name, "%s rendered empty — the built app did not mount" % mount)
        elif console_errors:
            fail(name, "browser console error(s): " + "; ".join(console_errors[:3]))
        else:
            ok(name)
    finally:
        _terminate_process_tree(proc)
