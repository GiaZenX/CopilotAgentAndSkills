# Messprotokoll der vier Repo-Gates (TSK-0007, 2026-08-05)

Dieses Dokument ist das **Artefakt**, das `TSK-0003` als `expected_output` verlangt hat und das nur
im Gespräch existierte. Ein Messwert, der nur in einer Sitzung steht, ist verloren, sobald sie
zusammengefasst wird — das ist der Fall, gegen den `DEC-0003` geschrieben wurde.

Es enthält **keine** Behauptung ohne Messung. Wo etwas nicht gemessen werden konnte, steht das
ausdrücklich da, samt dem Grund und dem Verfahren, das es messen würde.

## Wie gemessen wurde

- **Echte Hook-Prozesse.** Jede Zeile unten ist ein `subprocess`-Start des Skripts mit JSON auf
  `stdin` und dem Rückgabecode als Urteil (`2` = Verweigerung, `0` = Durchlass, alles andere liest
  der Provider als „hook error, carry on", also ebenfalls als Durchlass). Kein Import, keine
  Funktion, keine Zeichenkettensuche über eine Datei.
- **Über die Registrierung, nicht über eine Dateiliste.** Der Messstand liest
  `.claude/settings.json`, löst den Matcher in Werkzeugnamen auf und startet **genau die Hooks, die
  für dieses `tool_name` registriert sind** — sonst misst man ein Skript und nicht das, was der
  Provider täte. Genau diese Unterscheidung war der Grund, warum 38 grüne Tests F2 nicht bemerkt
  haben.
- **Außerhalb des Repos.** Der Messstand baut ein Projekt in einem Temp-Verzeichnis (`team-kits/`,
  `tools/bump_kit_version.py`, `project_memory/`, `.claude/`, `CLAUDE.md`, ein echtes git-Repo mit
  einem echten Diff). Gate 3 hasht den Arbeitsbaum; im Repo gemessen hinge jeder Lauf davon ab, was
  sonst gerade unversioniert ist.
- **Skripte:** `scratchpad/tsk0007/bench.py` (Vorher/Nachher-Matrix) und
  `scratchpad/tsk0007/redcheck.py` (Defekt im Klon wiederherstellen, Test rot sehen). Beide liegen
  im Sitzungs-Scratchpad, nicht im Repo — sie messen einen Stand, sie sind kein Produkt.

## Was jedes Gate prüft, und woran es gemessen wurde

| Gate | Ereignisse (Registrierung) | Subjekt der Messung |
|---|---|---|
| `gate_lead_write_scope.py` | `Write\|Edit\|MultiEdit\|NotebookEdit`, `Bash\|PowerShell` | ein Pfad, den der Aufruf schreiben würde — aus `tool_input.file_path` oder aus dem, was eine Befehlszeile schreibt |
| `gate_spawn_needs_item.py` | `Agent\|Task` | die Item-Ids im Spawn-Text, aufgelöst gegen `project_memory/` |
| `gate_commit_evidence.py` | `Bash\|PowerShell` | die Gestalt der Befehlszeile + der Diff-Hash des Arbeitsbaums gegen die aktiven `EVD`-Items |
| `gate_todo_items.py` | `TodoWrite` | die Einträge der Aufgabenliste |

## 1. Angriffe: vorher rc, nachher rc

Alle Zeilen als Sitzungsagent (`agent_type: harness-lead`, kein `agent_id`), außer wo vermerkt.
„vorher" = Stand nach TSK-0003, „nachher" = Stand nach TSK-0007.

| # | Aufruf | vorher | nachher |
|---|---|---|---|
| A1 | `python -c "open('team-kits/dev-team/hooks/gate_git.py','w')…"` | 0 | **2** |
| A2 | `python -c "open('team-kits/kernel/state.py','w')…"` | 0 | **2** |
| A3 | `python -c "open('.claude/hooks/gate_todo_items.py','w')…"` | 0 | **2** |
| A4 | `python -c "open('.claude/settings.json','w')…"` | 0 | **2** |
| A5 | `python -c "open('tools/bump_kit_version.py','w')…"` | 0 | **2** |
| A6 | `sed -i 's/a/b/' team-kits/dev-team/hooks/gate_git.py` | 0 | **2** |
| A7 | `Set-Content -Path .claude/hooks/gate_todo_items.py -Value ''` (PowerShell) | 0 | **2** |
| A8 | `echo x > .claude/settings.json` | 0 | **2** |
| A9 | `rm -rf team-kits` | 0 | **2** |
| A10 | `cd .claude/hooks && rm gate_todo_items.py` | 0 | **2** |
| A11 | `python -c "open('project_memory/evidence/active/EVD-9999.yaml','w')"` | 0 | **2** |
| A12 | `Write tools/bump_kit_version.py` | 0 | **2** |
| A13 | `Write .claude/agents/harness-lead.md` | 0 | **2** |
| A14 | `Write .claude/settings.local.json` | 0 | **2** |
| A15 | `Write project_memory/evidence/active/EVD-9999.yaml` | 0 | **2** |
| A16 | dasselbe als **Subagent** | 0 | **2** |
| A17 | `Write` mit leerem `tool_input` | 0 | **2** |
| D1 | `Write kits/dev-team/hooks/gate_git.py` durch `mklink /J kits team-kits` | 0 | **2** |
| D2 | `sed -i … kits/dev-team/hooks/gate_git.py` durch dieselbe Junction | 0 | **2** |

A1–A8 sind die acht Zeilen des Prüfberichts. Auffällig an „vorher": die ausführende Spalte war
immer `gate_commit_evidence.py` allein — auf `Bash|PowerShell` lief kein anderes Gate.

## 2. Gegenprobe: was weiterhin laufen muss

Der teure Fehler wäre ein Gate, das die eigene Arbeit stilllegt. Alle Zeilen nachher **rc 0**:

| Aufruf | nachher |
|---|---|
| `PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory generate-index` | 0 |
| `$env:PYTHONPATH="team-kits"; python -B -m kernel.cli --root project_memory generate-index` | 0 |
| `python -B -m pytest .claude/hooks/test_gates.py -q` | 0 |
| `python -B -m pytest tools/ -q` | 0 |
| `python tools/bump_kit_version.py` | 0 |
| `python -m ruff check .` | 0 |
| `git status --short`, `git add -A` | 0 |
| `cat .claude/hooks/gate_todo_items.py`, `grep -rn STATE_ROOT team-kits/` | 0 |
| `Write docs/note.md`, `Write CLAUDE.md`, `Write radar/note.md` | 0 |
| `Write project_memory/staging/TSK-0007/verdict.md` | 0 |
| Subagent schreibt `team-kits/dev-team/hooks/gate_git.py` | 0 |
| `Write` außerhalb des Repos | 0 |
| Spawn, der ein offenes Item nennt | 0 |

Jede dieser Zeilen nennt `team-kits`, `.claude` oder `project_memory` in einer schreibfähigen
Pipeline. Die Regel der Kits („nennt den Baum und kann schreiben → verweigern") hätte alle
verweigert; deswegen ist sie hier nicht übernommen worden, sondern nur ihr **Leser**.

## 3. Fail-closed: der gemeinsame Rumpf fehlt

`_harness.py` aus der Kopie gelöscht, dann jeden **registrierten** Hook mit einer Nutzlast starten,
die er verweigern müsste:

| Ereignis | vorher | nachher |
|---|---|---|
| `Write` → `gate_lead_write_scope.py` | rc **1** (= Durchlass) | **2** |
| `Bash` → `gate_lead_write_scope.py`, `gate_commit_evidence.py` | rc **1** | **2** |
| `Task` → `gate_spawn_needs_item.py` | rc **1** | **2** |
| `TodoWrite` → `gate_todo_items.py` | rc **1** | **2** |

Der zweite bereits vorhandene Fall (`team-kits/` fehlt, also kein Kernel erreichbar) war schon
vorher rc 2 und ist es geblieben — er wird von `guarded()` abgedeckt, der Import nicht.

## 4. Gate 3: die Gestalt der Zeile

Mit aufgezeichnetem, gültigem Urteil im Baum:

| Zeile | vorher | nachher |
|---|---|---|
| `git commit -m wip` | 0 | 0 |
| `git add -A && git commit -m wip` | 0 | 0 |
| `echo more >> docs/note.md && git commit -m wip` | **0** | **2** |
| `git merge --no-ff other` | 0 | 0 *(H2, offen)* |
| `git revert --no-edit HEAD` | 0 | 0 *(H2, offen)* |

## 5. Laufzeit

Bester von drei Läufen, echter Prozess, Projekt mit den drei Kits und dem vollen `project_memory`:

| Gate | Nutzlast | Laufzeit |
|---|---|---|
| `gate_lead_write_scope.py` | `Write docs/note.md` | 0,58 s |
| `gate_lead_write_scope.py` | `Bash` mit der Kernel-Zeile | 0,52 s |
| `gate_commit_evidence.py` | `git commit -m wip` | 0,61 s |
| `gate_spawn_needs_item.py` | Spawn mit Item | 0,45 s |
| `gate_todo_items.py` | ein gebundener Eintrag | 0,45 s |

Ein `Bash`-Aufruf kostet jetzt **zwei** Hook-Prozesse (≈ 1,1 s), weil Gate 1 dort mitläuft. Das ist
derselbe Hebel, den `docs/POST_V2_WISHLIST.md` L11 für die Kits benennt: die Kosten liegen im
Interpreterstart, nicht im Zustands-Walk.

## 6. Die Nutzlast des Aufrufers — was gemessen ist und was nicht

Gate 1 steht darauf, dass `_compat.calling_subagent` den Sitzungsagenten von einem Subagenten
unterscheiden kann. Diese Voraussetzung ist **in diesem Repo** noch nie erhoben worden; sie war aus
den Kits übernommen.

**Gemessen (2026-08-05, echter Hook-Prozess in diesem Repo, Sonde in `gate_lead_write_scope.py`,
danach entfernt):** die Hooks dieses Repos laufen in dieser Sitzung wirklich — ein `Bash`-Aufruf mit
`git commit --dry-run` wurde von `gate_commit_evidence.py` verweigert. Die aufgezeichnete Nutzlast
eines **Subagenten** trägt beide Felder:

```
{"session_id": "...", "cwd": "C:\\Offline Repos\\AgentAndSkills", "permission_mode": "...",
 "agent_id": "a6d673a9aa6f127a2", "agent_type": "harness-implementer",
 "hook_event_name": "PreToolUse", "tool_name": "Write", "tool_use_id": "..."}
```

`agent_id` ist gesetzt und `agent_type` trägt die **Rolle des Aufrufers**. Dazu passend, durch das
laufende Gate gemessen: ein `Write` nach `.claude/hooks/` aus diesem Subagenten heraus wird
**erlaubt** — `calling_subagent` liefert also einen Namen, und Gate 1 hält sich korrekt heraus.

**NICHT gemessen: die Nutzlast des Sitzungsagenten selbst.** Ein Subagent kann keine erzeugen — der
Sitzungsagent müsste einen Werkzeugaufruf machen, während die Sonde installiert ist, und das
entscheidet er, nicht der Umsetzer. Die Notiz in `tools/provider_observations.json`
(`agent_identity.correction_2026_08_04`) behauptet, das sei hier grundsätzlich unmessbar
(„nothing here can make a provider emit a hook event"); die Zeile oben zeigt, dass das für die
Subagenten-Hälfte **nicht** stimmt. Für die Sitzungs-Hälfte stimmt sie weiterhin, aus einem anderen
Grund: nicht das Repo ist das Hindernis, sondern die Rolle des Messenden.

**Was auf dem Spiel steht, in beide Richtungen:**

| Form der Lead-Nutzlast | `calling_subagent` | Folge für Gate 1 |
|---|---|---|
| `agent_type` = gebundene Rolle, kein `agent_id` (erwartet) | `""` | aktiv — richtig |
| beide Felder fehlen | `""` | aktiv — richtig |
| `agent_id` vorhanden | Name | **Gate 1 überspringt den Lead: tot** |
| `agent_type` ≠ gebundene Rolle | Name | **Gate 1 überspringt den Lead: tot** |

**Verfahren, das die fehlende Hälfte misst** (drei Minuten, vom Sitzungsagenten auszuführen —
`.claude/hooks/` ist ihm durch Gate 1 gesperrt, es geht also aus einer Shell außerhalb von Claude
Code und mit Sitzungsneustart):

1. In `_harness.payload()` vor dem `return` einen Block einfügen, der `data` ohne `tool_input` als
   JSON-Zeile an eine Datei außerhalb des Repos anhängt, umschlossen von `try/except BaseException:
   pass` (eine Sonde darf nie ein Urteil ändern).
2. Sitzung neu starten, **einen** beliebigen Werkzeugaufruf als Sitzungsagent machen (kein Spawn).
3. Die Datei lesen: enthält die Zeile ein `agent_id`, ist Gate 1 für den Lead tot und das ist ein
   Blocker; trägt `agent_type` nicht `harness-lead`, ebenso.
4. Den Block entfernen, Sitzung neu starten.

## 7. Rote Tests: jeder Fix, im Klon außerhalb des Repos wiederhergestellt

Verfahren: das Repo wird nach `scratchpad/tsk0007/mut/` kopiert, dort der **ursprüngliche Defekt**
wiederhergestellt und der benannte Test gefahren. „rot" heißt: `pytest` rc 1 mit den genannten
Fehlschlägen.

| Wiederhergestellter Defekt | Test, der rot wird | Ergebnis |
|---|---|---|
| `import _harness` außerhalb des `try` (alle vier Gates) | `test_a_gate_whose_shared_body_is_gone_still_refuses` | 11 failed |
| Gate 1 nicht auf `Bash\|PowerShell` registriert | `test_the_registration_is_the_one_the_contract_asks_for` | 1 failed |
| Gate 1 liest keine Befehlszeilen | `test_gate1_leaves_the_sessions_own_commands_runnable` | 10 failed |
| `written_paths` liefert nichts (Shell-Leser blind) | `test_gate1_refuses_a_shell_write_into_a_protected_area` | 12 failed |
| Produzent nicht geschützt | `test_gate1_refuses_the_session_agent[tools/…]` | 1 failed |
| `.claude/` zurück auf zwei Pfade | `test_gate1_refuses_the_session_agent[agents/…, settings.local.json]` | 2 failed |
| Matcher von Gate 1 auf `"Write"` verengt | `test_the_registration_is_the_one_the_contract_asks_for` | 1 failed |
| Gate 3 verliert `PowerShell` | dito | 1 failed |
| Gate-2-Matcher `"NeverFires"` | dito | 1 failed |
| Gate-1-Registrierung zeigt auf `gate_todo_items.py` | dito | 1 failed |
| Gate 3 prüft die Gestalt der Zeile nicht | `test_gate3_refuses_a_line_that_moves_the_tree_before_it_commits` | 1 failed |
| `project_memory/` wieder werkzeugschreibbar | `test_gate1_refuses_canonical_state_from_every_caller` | 2 failed |
| `abspath` statt `realpath` | `test_gate1_reads_a_junction_as_the_tree_it_points_at` | 1 failed |
| die drei frühen `return`s bei unlesbarer Nutzlast | `test_a_payload_a_gate_cannot_read_is_refused` | 3 failed |
| Untracked-Hälfte des Digests entfernt | `test_gate3_sees_a_file_git_does_not_track_yet` | 1 failed |
| `evidence_naming` nur auf `summary` | `test_gate3_reads_the_digest_in_any_field_of_the_record` | 1 failed |
| Pfadkandidaten nur als Teilzeichenketten (kein ganzer Reading) | `test_gate1_refuses_a_protected_path_spelled_absolutely_through_a_space` | 1 failed |
| `TSK-0003` auf `VALIDATED` gesetzt | **alte** Testdatei: 2 failed / **neue**: 3 passed | wie erwartet |

Drei Beobachtungen, die zum Protokoll gehören, weil sie zeigen, wie ein Test *nicht* misst, was er
zu messen scheint:

- „Gate 1 liest keine Befehlszeilen" macht die **Angriffs**-Tests nicht rot — das Gate verweigert
  dann alles auf der Shell als „nicht inspizierbar" und besteht sie aus dem falschen Grund. Rot
  wird die **Gegenrichtung**. Erst beide Testklassen zusammen fixieren den Fix.
- Umgekehrt: macht man nur den Shell-Leser blind (`written_paths` liefert nichts), sind es die 12
  Angriffs-Tests, die rot werden, und die 10 Gegenproben bleiben grün. Beide Richtungen sind
  belegt.
- Der **absolute Pfad mit Leerzeichen** war ein Defekt dieser Runde, nicht der vorigen: die erste
  Fassung des Shell-Lesers suchte nur pfadähnliche Teilzeichenketten, und der Pfad dieses Repos
  (`C:/Offline Repos/AgentAndSkills`) zerfällt daran. Gefunden beim Gegenlesen der eigenen Arbeit,
  gemessen, geschlossen, rot belegt.
- Und in die andere Richtung: eine zweite „Verbesserung" derselben Stelle (`-c` über alle Readings
  statt über den Token-Text) wurde **wieder entfernt**, weil ihre Mutation grün blieb — der
  Tokenizer der Kits liefert das Wort bereits aufgelöst. Eine Änderung ohne roten Test ist eine
  behauptete Deckung, und das ist teurer als keine Änderung.

## 8. Suite

`python -B -m pytest .claude/hooks/test_gates.py -q` — vorher **38 passed** (82 s), nachher
**97 passed** (136 s). Die Suite unter `tools/` ist in
dieser Runde nicht das Maß: `team-kits/` und `tools/` sind `forbidden_scope` von `TSK-0007`, dort
arbeitet parallel ein anderer Umsetzer, und `python tools/bump_kit_version.py` wurde bewusst
**nicht** gefahren — es hätte eine fremde, laufende Änderung gestempelt. Dieselbe Entscheidung
beschreibt `CLAUDE.md` bereits für den 2026-08-04.
