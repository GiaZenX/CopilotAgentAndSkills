# TSK-0030 — Messprotokoll (BUG-0016, DEC-0032, weiche Variante)

Umsetzer `harness-implementer`, 2026-08-10. Alle SDK-Messungen in einem **isolierten**
`CLAUDE_CONFIG_DIR` (`C:/hooktest-tsk0030/cfg`) mit kopierten Credentials — die echte
`~/.claude/settings.json` des Operators wurde **nie** verändert, `~/.claude/team-kits` nicht
angefasst. SDK `claude-agent-sdk` über `claude` 2.1.225, Modell sonnet,
`permission_mode=bypassPermissions`, `setting_sources=[user,project,local]`.

## Die vier Vor-dem-Bau-Messungen (DEC-0030)

### (a) Feuert ein User-Scope-PreToolUse-Hook unter bypassPermissions wie ein Projekt-Hook? — JA, hoher Sicherheitsgrad

User-Scope-Hook in `cfg/settings.json` (`PreToolUse: Bash`), Projekt-Hook als Positivkontrolle in
`proj/.claude/settings.json`. Beide feuerten:

```
user_marker : {"scope": "user",    "event": "PreToolUse", "tool": "Bash", "cwd": ".../proj"}
proj_marker : {"scope": "project", "event": "PreToolUse", "tool": "Bash"}
```

Und — das Entscheidende — ein User-Scope-Hook kann **ablehnen** (`exit 2`) und die Sitzung läuft
weiter (weiche Variante bestätigt): Hook `exit 2` auf `echo pwned > sideeffect.txt` →
`sideeffect.txt` wurde NICHT erzeugt, der Assistant meldete „The command was blocked by a PreToolUse
hook … a probe_deny user-scope hook explicitly denies this tool call", die Sitzung endete mit
`ResultMessage subtype=success` (kein Sitzungsabbruch). Reden bleibt also unbetroffen.

### (b) Überspringt merge_settings.py bei vorhandenem Ziel-hooks-Key? — JA (Vor-Fix), hoher Sicherheitsgrad

Direkter Lauf der **Vor-Fix**-`merge_settings.py` (`git show HEAD:user/merge_settings.py`) mit einer
Ziel-`settings.json`, die bereits einen fremden `hooks`-Key trägt:

```
merged settings: added defaults=-; preserved existing=hooks; ...
handover present with OLD merge? False
```

`preserved existing=hooks` ist genau der `merge_settings.py:85-89`-Zweig „existing wins" — der
Handover-Hook fällt still weg. Nach dem Fix (Array-Union pro Event) bleibt der Nutzer-Hook UND der
Handover-Hook steht drin; ein zweiter Merge dupliziert nichts (Dedup). Gemessen im Test
`test_settings_merge_unions_hooks_so_the_handover_guard_survives_a_user_hooks_key`.

### (c) Feuert der SessionStart(startup)-Cleanup nur bei echtem Neustart? — JA, hoher Sicherheitsgrad

SessionStart-Hooks in `cfg/settings.json`: einer mit `matcher: "startup"`, einer ohne Matcher
(loggt `source`). Drei Läufe: frisch, resume (dieselbe session_id = Reconnect), continue
(Terminal-Reattach):

```
sessionstart.log (jeder Matcher):  source=startup  / source=resume / source=resume
startupmatch.log (nur matcher=startup):  source=startup   (GENAU EIN Eintrag)
```

Der `startup`-Matcher feuerte nur beim echten frischen Prozess (source=startup) und **nicht** bei
resume/continue. Das `source`-Feld unterscheidet einen echten Neustart also zuverlässig von einem
Reattach.

**Design-Entscheidung daraus:** Der Cleanup-Hook prüft `source == "startup"` **im Hook-Körper**
statt über einen `startup`-SessionStart-**Matcher**. Grund gemessen: der Matcher `startup` hat keine
Repräsentation in der Codex-Provider-Übersetzung (`gen_provider_artifacts`) — der Suite-Test
`test_gen_provider_artifacts` lehnt jeden generierten Matcher ab, der nicht in
`("", "*", "Bash", "apply_patch")` liegt (rot mit `AssertionError: startup`). Die In-Body-Prüfung ist
äquivalent (Marker überlebt Reattach, löscht bei echtem Neustart), unit-testbar ohne Vertrauen in den
Provider und funktioniert auf beiden Providern. Der Hook läuft damit bei jedem SessionStart und ist
auf resume ein No-op.

### (d) Spürbare Latenz des globalen No-op-Hooks — ~87 ms Median, mittlerer–hoher Sicherheitsgrad

No-op-Pfad (Marker abwesend → `exit 0`) als realer Prozess, 15 Läufe nach Warmup:

```
no-op hook latency ms: min=80.3 median=87.2 max=123.9
```

Dominiert vom Python-Interpreter-Start auf diesem Windows-Host. Das ist der dauerhafte Tarif auf
JEDEN Write/Edit/Bash/Task/PowerShell/Agent-Aufruf JEDER Claude-Code-Sitzung des Nutzers. Der Nutzer
hat der Invasivität in DEC-0032 zugestimmt.

## Rote Tests (gesehen, nicht behauptet)

Alle drei Defekte in Klonen **außerhalb** des Repos wiederhergestellt, rot gesehen, zurückgesetzt:

1. `test_settings_merge_unions_hooks_...` — gegen `HEAD:user/merge_settings.py`: `handover present
   with OLD merge? False` → Test rot.
2. `test_handover_guard_blocks_product_code_write_under_marker`,
   `test_handover_guard_blocks_spawns_and_engine_shell_but_not_reading` — gegen einen No-op-Klon
   (`exit 0`): product write / spawn / engine-shell alle rc 0 statt 2 → Tests rot.
3. `test_clear_handover_marker_removes_it_only_on_a_real_restart` — gegen einen Klon ohne die
   `if source != "startup": return False`-Zeile: Marker bei source=resume gelöscht → Test rot.

## Bewusst NICHT geschlossen, aber benannt

- **Produktcode-Schreibung per roher Shell-Umleitung** (`echo x > src/foo.py`) wird vom
  Handover-Hook NICHT abgelehnt — dieselbe Klasse Shell-Schreibverb-Loch, das auch das viel größere
  `gate_write_scope` offen lässt (H22/H34). Der gemessene Produktcode-Vektor ist das Write/Edit-Tool,
  das abgedeckt ist. Bewusste Grenze der weichen Variante, keine Reimplementierung eines fragilen
  Shell-Parsers im globalen Hook.
- **`install.sh` (POSIX)** kopiert den globalen Hook NICHT nach `~/.claude/hooks/` — die Datei liegt
  außerhalb des `allowed_scope` von TSK-0030 (`install.ps1` ist drin, `install.sh` nicht).
  **KORREKTUR 2026-08-10 (TSK-0031, Prüfverdikt B1): die hier ursprünglich genannte Schwere war zu
  harmlos.** „Installiert sich nicht" verfehlt den gemessenen Schaden: `merge_settings.py` registriert
  den Hook UNBEDINGT, `install.sh` legt die Datei aber nicht — die Registrierung zeigt dann auf eine
  fehlende Datei, `python <fehlt>` liefert **exit 2**, und ein PreToolUse-Hook mit exit 2 ist ein
  **BLOCK**. Damit wird auf einem POSIX-Host **jeder Werkzeugaufruf in jeder Sitzung** verweigert
  (mit oder ohne Marker), nicht nur der Fix ausgelassen. Gemessen: `python /pfad/does-not-exist.py`
  → exit 2. **GESCHLOSSEN in TSK-0031:** `install.sh` bekam denselben Kopierschritt wie `install.ps1`
  (`user/claude/hooks/*.py` → `~/.claude/hooks/`, VOR dem Merge); Prinzip: kein Installer registriert
  je einen Hook, dessen Datei nicht liegt. Roter Test:
  `test_hooks.py::test_install_sh_places_every_hook_it_registers`.
- **Office-Kit-Planartefakte**: Der Hook erlaubt unter dem Marker genau die drei in DEC-0032
  benannten Planartefakte (`product/masterplan.md`, `project_config.yaml`, `product/active/PR-0001*`).
  Das Office-Kit hat kein PR-Wurzelitem, sondern `business_profile.yaml`/`filing_plan.yaml`; deren
  Nach-Marker-Verfeinerung würde der Hook heute ablehnen. DEC-0032 nennt exakt die drei; eine
  Erweiterung wäre eine Entscheidungsänderung, keine Umsetzung.
