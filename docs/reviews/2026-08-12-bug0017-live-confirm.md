# BUG-0017 — live phase-1 confirmation with the committed fix (TSK-0053), 2026-08-12

## Measured verdict: /hooks ceremony REDUCED but NOT GONE — the prose ban does not hold. BUG-0017 needs a STRUCTURAL fix.

Live phase-1 pilot, HEAD `29bc987`, repo kit `dev-team 2026.08.12-4`, the FIXED
`user/claude/CLAUDE.md` deployed to `~/.claude/CLAUDE.md` for the run. Live config + store backed up,
deployed, then restored and **byte-verified** (entry file back to sha256 `95CDCB…` / 12868 B; store back
to `2026.08.10-1`). Scratch swept.

## What held, and what did not
- **At the restart message itself (Turn 0 — the exact spot TSK-0053 governs): GONE.** The closing
  say-line matched the fix text verbatim, 0 ceremony words: "✅ Team installiert … Bitte starte die
  Session neu … Du musst jetzt nichts freigeben, bestätigen oder eintippen — nur neu starten."
- **On the continuation path (Turn 2): /hooks RETURNS.** The entry session did NOT stop after install
  (BUG-0016 not enforced). When the persona said "weiter", the agent — still in the entry session —
  REQUESTED the scope approval (which the fix text explicitly forbids), the mint FAILED (entry-session
  hooks inactive), and the agent RE-INVENTED /hooks: "…vermutlich braucht es dafür einmalig einen
  `/hooks`-Befehl … um das geänderte Hook-Paket zu bestätigen" / "ich warte kurz, bis du `/hooks`
  ausgeführt hast".

## Why prose cannot close it — three measured reasons, none fixable by text
1. The fix demands "STOP after install" — **not enforced** (BUG-0016); the persona's "weiter" pulls the
   session onward. A non-technical persona keeps talking instead of restarting — the very trait the bug
   targets.
2. The fix demands "do not request/mint approval here" — the agent did it anyway when it continued.
3. On the failed mint, the agent re-derives /hooks from the REAL `restart_required` diagnosis. While
   that diagnosis is reachable in the entry session and the model meets it, it rationalises /hooks.

## The structural fix must enforce at least one of (design decision, coupled to BUG-0016)
- **(a)** the stop after install — a real BUG-0016 barrier that keeps the entry session from doing PM
  work at all;
- **(b)** make the entry session TECHNICALLY UNABLE to request/mint an approval (then the
  `restart_required` diagnosis never arises); a PM-type action in the entry session should cleanly
  REFUSE with "not until restart", so the agent gets an honest signal instead of a mint failure it
  rationalises;
- **(c)** remove/rewrite the `/hooks`-suggesting diagnosis path (wherever `restart_required` /
  `hook_trust: unverified` surfaces, its guidance must say "restart — /hooks is not part of this flow").

## The runner method (documented so it is NOT lost a third time)
`ClaudeAgentOptions(system_prompt={"type":"preset","preset":"claude_code"}, setting_sources=["user","project","local"], permission_mode="bypassPermissions", model="sonnet", max_budget_usd=15, can_use_tool=cb)`.
AskUserQuestion answered via `can_use_tool`: the callback returns
`PermissionResultAllow(updated_input=updated)` with `updated = dict(input_data); updated["answers"] = {question_text: chosen_label}`.
The scenario JSON supplies the persona turns + a needle→label map. The real shell is arbiter (real
`.claude` hooks fire, `tool_use` blocks logged). **Label matching must use the CURRENT paraphrased
option labels** (run 1 was discarded: it matched the old "Ja —" label, missed, and fell into free
mode — a runner bug, not a kit finding). Phase-1-only; stop before any build (~$3.18 to Turn 2).

## Honesty / scope
- The /hooks return is on the continuation path, not the restart message — but it is REALISTIC, not an
  artefact: BUG-0016 keeps the entry session live and a non-technical user keeps talking. The fix is
  NOT closed against the continuous chain.
- One data point, Sonnet, `bypassPermissions`, scripted persona — same declared deviations as priors.
  Interactive CLI still not measurable here (AC-3 open).
