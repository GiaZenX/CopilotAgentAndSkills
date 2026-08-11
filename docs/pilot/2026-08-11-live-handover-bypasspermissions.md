# Live-Handover-Pilot — bypassPermissions + BUG-0016, HEAD 394ba2b, 2026-08-11

Prüfer-Lauf aus dem committeten HEAD (`git archive 394ba2b`, Guard-sha `1e60a232…`), isoliertes
HOME `C:/verifier-box/_home-head`, echtes `~/.claude` nur gelesen. Artefakte:
`C:/verifier-box/_hook_battery.py`, `_live_probe_head.py`, `_live_ac2.py`, `runs/livehead.jsonl`.

## Die zentrale Frage ist beantwortet: JA, der User-Scope-Hook feuert unter bypassPermissions

Live über die SDK (`permission_mode=bypassPermissions`, `setting_sources` inkl. user → isoliertes
HOME, Subjekt sonnet), Marker vorab gesetzt. Produkt-Write nach dem Marker:
```
USE Write game/hero.js
RESULT err=True PreToolUse:Write hook error: [handover] refused: 'game/hero.js' is product code …
hero.js exists: False
```
Write geblockt (rc 2), Datei nicht erzeugt. **Fix-Design-Frage 1 positiv:** der Guard ist im realen
Einstiegsfluss wirksam, nicht wirkungslos. Das validiert den ganzen globalen-Hook-Ansatz.

## BUG-0016-Fix selbst: PASS

- Direkte Hook-Batterie 30/30 wie dokumentiert: Produkt-Write BLOCK, Plan-Artefakte ALLOW, Spawn
  BLOCK, Engine-Derivation BLOCK (einzeilig, `cd &&`, `cat |`, `;`, **mehrzeiliger Block** [TSK-0032],
  `for…do`, Subshell, `VAR=v`, Continuation), `doctor`/`--help` ALLOW, Heredoc-Body ALLOW,
  Marker-Löschung BLOCK. Benannte Residuen (`sh -c`, `eval`, `$(…)`, Roh-Redirect, `mv .claude`)
  ALLOW — korrekt.
- Live-Gegenprobe TSK-0032: mehrzeiliger `kernel.cli`-Block nach Marker → BLOCK live.
- Rote Tests reproduziert: TSK-0031-Mutation → 23 rot; TSK-0032-Mutation → 3 rot.
- AC-1 PASS (Live), AC-2 PASS mit Nuance (bei einer Formulierung stoppte der wohlmeinende Agent
  selbst; die Klasse ist über Step A/Batterie gedeckt).
- AC-3 / AC-4 NICHT GEMESSEN — brauchen den vollen Auto-Init+Neustart über zwei Sitzungen, und der
  ist durch F1 blockiert (Kit nicht installierbar).

## F1 — KORRIGIERT: kein „Kaputt-committet", sondern eine Zeilenenden-Empfindlichkeit (BUG-0025)

**Ursprüngliche Lesart war ein Mess-Artefakt.** Der Pilot baute aus `git archive 394ba2b | tar -x`;
`git archive` wandelt auf diesem Windows-Host die `.md` nach CRLF (je Zeile +1 Byte), sodass das
Lead-Instruction-Package auf 31006/32124/35129 wuchs und `tools/validate.py` abbrach. Vom Lead
nachgemessen (2026-08-11): **Arbeitsbaum = HEAD-Blob = 30674 (LF) = Rekord → `validate.py` besteht
(exit 0)**. Die Commits `41dd8f4`/`394ba2b` sind auf einem LF-Baum grün; die frühere BUG-0024
(„zwei Commits mit rotem validate.py") war falsch gerahmt und ist **REJECTED**.

**Der echte, engere Bug (BUG-0025, medium):** `.gitattributes` pinnt `*.py`/`*.sh`/VERSION auf
`eol=lf`, aber **nicht `.md`**. Ein Standard-Git-for-Windows-Klon (autocrlf=true) checkt die `.md`
als CRLF aus → dasselbe 31006 → `install.sh`/`validate.py` bricht ab und installiert nichts. Der
Dev-Baum ist LF und verdeckt es, und die Prüfung läuft nicht in `pytest tools/` (Verwandtschaft
BUG-0014). Fix: `.md`/text auf `eol=lf` pinnen ODER die Größe zeilenenden-normalisiert messen; plus
`validate.py` in die Abnahme ziehen. **Kein Nachzeichnen der Größen** — der Umsetzer hat das zu
Recht verweigert, sein LF-Baum ist am Rekord.

## F2 — MINOR (Über-Verweigerung, sicher, dokumentiert)

`handover_guard.py:460-472` (`_segment_touches_the_marker`): Marker-Wortabgleich ohne Quote-Maske,
also verweigert `echo "…HANDOVER_PENDING…"` / `git commit -m "…HANDOVER_PENDING…"`. Nur mehr, nie
weniger; deckt sich mit dem Docstring-Wortlaut, kein Loch. Optionaler Fix: dieselbe Quote-Maske wie
`_segments`. Nicht als eigenes Item geführt (Reibung, nicht Defekt) — Notiz für eine spätere
Guard-Politur.
