# Decided radar items

The radar-watcher reads this file FIRST each week and skips anything already listed here, so no item is
ever re-surfaced. Append one line per triaged candidate.

Format: `<slug> | <title> | accept | reject | <YYYY-MM-DD> | <one-line note>`

- radar-0703-background-subagents | Subagents background-by-default (2.1.198) | accept | 2026-07-04 | adopted as V14a: `run_in_background: false` delegation default + never advance phase before all notifications (commit f6f49d3)
- radar-0703-agent-permission-rules | Declarative `Agent(...)` permission rules | accept | 2026-07-04 | adopted as V14b: `deny: Agent(project-manager)` in both kit settings, defense-in-depth beside guard_agent_spawn (f6f49d3)
- radar-0703-matcher-audit-a1 | Hook-matcher audit / PowerShell bypass (A1) | accept | 2026-07-04 | adopted as V11: all shell gates match Bash AND PowerShell (tool check + settings matcher) + test (f6f49d3)
- radar-0706-subagent-reliability | Subagent/background reliability fixes (2.1.200) | reject | 2026-07-10 | no harness change — platform now fails empty subagents cleanly, matching §14a's assumption (noted in 40af990)
- radar-0706-askuserquestion-no-autocontinue | AskUserQuestion no longer auto-continues | reject | 2026-07-10 | benign — behaviour now matches the harness's user-gate intent; nothing to change
- radar-0706-notification-agent-events | Notification hook fires for background agents (2.1.198) | accept | 2026-07-10 | adopted as R1: notify_agent_events.py in both kits logs agent_completed/agent_needs_input to project_memory/.audit (40af990)
- radar-0706-permission-mode-rename | Permission mode "default" renamed "Manual" | reject | 2026-07-10 | cosmetic; kit settings set no defaultMode

- radar-0816-unpinned-ruff | Unpinned ruff in CI (BUG-0007 family) | accept | 2026-08-29 | resolved: rule set pinned in ruff.toml, version pinned in .github/workflows/ci.yml (ruff 0.15.20); reconfirmed green 08-21/08-28/08-29
- radar-0821-sonnet5-price-trigger | Sonnet-5 Sep-1 price increase watch | reject | 2026-08-29 | cancelled by Anthropic: $2/$10 is the standard price, the 2026-08-31 increase will not occur; only the stale kit COMMENT remains (rider fix itemized)
- radar-0829-bom-role-files | BOM-prefixed role/skill .md silently unloaded (fixed 2.1.239) | accept | 2026-08-29 | captured as FR-0060: structural no-BOM tripwire over shipped role/skill trees + CC-floor note
- radar-0829-substitution-matcher | CC fixed $()/backtick over-match in its own matcher (2.1.243) | accept | 2026-08-29 | captured as FR-0061: measure our classifier both directions in a clone; under-read -> hole list with chain
- radar-0829-model-404-fallback | Pinned-model 404 now silently falls back (2.1.247/48) | accept | 2026-08-29 | folded into FR-0047: the model:-pin test must assert the pin RESOLVES in model_tiers.yaml
- radar-0829-cachettl-frontmatter | experimental.cacheTtl agent frontmatter + promptCacheTtl settings (2.1.243/48) | reject | 2026-08-29 | no kit sets them; source-format duty notes the widened contract, generator tolerance to be confirmed when a round touches it
- news-0829-restricted-mode | claude --restricted ignores user+project settings (2.1.248) | accept | 2026-08-29 | captured as FR-0063: measure whether gates fire at all under --restricted; ungated file writes inside the project would be a hole-list chain
- news-0829-subagent-memory | subagent memory: frontmatter persists across sessions | accept | 2026-08-29 | captured as FR-0064: evaluate per role -- verifier and second-reader roles NO by design (fresh-eye/independence), implementer/lead measured first; source-format key for the Codex generator
- news-0829-maxturns-partial | subagent stopping at maxTurns now marked partial (2.1.246) | reject | 2026-08-29 | pure improvement, no kit change: a partial no longer looks finished; orchestrators see the marking and can SendMessage-continue
- news-0829-auto-continue | auto-continue after usage-limit reset (2.1.234) | reject | 2026-08-29 | helps overnight autonomy passively; no kit surface touches it
