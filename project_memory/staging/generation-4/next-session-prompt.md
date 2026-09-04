# Handover prompt for the next session (write nothing from memory -- the state on disk is the authority; this file only points)

Weiter mit Generation 4. Stand: Generation 3 ist gemergt, geprüft und committet (Merge `6704221`,
Close-out `46eaaf2`, Generation-4-Schnitt im Folge-Commit; Kits dev/research `2026.09.04-1`, office
`2026.09.04-3`; Beweismittel EVD-0080 (Merge), EVD-0081 (Volllauf), EVD-0082/EVD-0083 (Zustands-
Commits)). Push: Generation 2 wurde 2026-09-03 auf Wort des Nutzers gepusht; alles danach ist NICHT
gepusht -- Push nur auf Wort des Nutzers in der laufenden Sitzung. Lies in dieser Reihenfolge, bevor
du etwas tust:

1. `project_memory/decisions/active/DEC-0070.yaml` -- die Rückschau von Generation 3, sechs Regeln;
   Regel 1 (Schnitt MESSEN, nicht schreiben: `check-scopes` über die Stream-Items VOR dem Spawn),
   Regel 2 (ein Befehlszeilen-Wächter ist eine DEC-first-Designrunde, kein Strom), Regel 5 („queued"
   ist keine Zustellung; Stille länger als eine Prüfung = ListAgents, nicht warten).
2. `project_memory/staging/generation-4-streams.md` -- das Logbuch von Generation 4: die vier Ziele
   (PR-0004 Test-Disziplin & Haken, PR-0005 Kernel-Verträge, PR-0006 Verfahren & Rückschau, PR-0007
   Repo-Hygiene), was jedes aufgenommen hat, der Dateibesitz (zu MESSEN), die Nähte, die Regeln je
   Auftrag. Plan-Freigabe APR-0005 ist erteilt (DEC-0068, erste Anwendung); PR-0001..0007 sind
   APPROVED.
3. `project_memory/staging/generation-3-streams.md` -- das Logbuch von Generation 3 mit der
   (g)-Tabelle, den acht Schnitt-Befunden und den Prozessnotizen; dazu
   `project_memory/staging/TSK-0120/merge-protocol.md` §6 (Schnitt- und Auftragsbefunde) und §9.
4. `project_memory/decisions/active/DEC-0062.yaml`, `DEC-0063.yaml`, `DEC-0067.yaml`, `DEC-0068.yaml`
   (Schnitt, Regeln, Bündelung am Ziel, Plan-Freigabe) und `DEC-0066.yaml` (FR = Posteingang;
   ein Auftrag hängt an PR/BUG/CR/EXP).
5. `project_memory/generated/index.yaml` -- der Zustand (eine `session_brief.yaml` gibt es in
   diesem Repo nicht).

Was zuerst ansteht (die Entscheidung, WANN gespawnt wird, liegt beim Nutzer -- frage ihn):

- **Je Ziel EIN Auftrag** (DEC-0067): `create-task` mit `--product-requirement PR-000n
  --derives-from PR-000n`, `allowed_scope` = der Dateibesitz aus dem Logbuch, `forbidden_scope`
  mit der Ausnahme `project_memory/staging/<TSK>/` IM ITEM (Schnitt-Befund aus Generation 3),
  Lochnummern IM ITEM reserviert (nächste freie: H151), `seam_scope` für die geteilten Dateien
  (der Kernel trägt das Feld seit Generation 3), die Regeln aus dem Logbuch als expected_outputs.
  Erzeuge die Aufträge mit einem Skript in `staging/generation-4/` (Argumentlisten; eine Shell-Zeile
  dieser Länge brach in Generation 3 zweimal an der Quotierung).
- **Vor dem Spawn messen** (DEC-0070 Regel 1): `PYTHONPATH=team-kits python -B -m kernel.cli --root
  project_memory check-scopes --only TSK-a TSK-b TSK-c TSK-d` -- 0 Überlappungen außerhalb der
  deklarierten Nähte, sonst ist der Schnitt falsch, nicht der Auftrag. Prüfe auch: kein weiterer
  offener Auftrag überlappt (TSK-0088 tat das in Generation 3); jedes Item nennt nur Dateien, die
  der ausgelieferte Kit-Vertrag zulässt (die erzwungene research-Skill-Kopie); keine gespiegelte
  Datei erlaubt UND das Spiegel-Kit verboten (kit_browser_checks.py in Generation 3).
- Worktrees: `git worktree add "C:/Offline Repos/v2-testbed/_worktrees/g4-<name>" -b g4/<name>
  <HEAD>` (fünf Zeilen, keine Schleife -- Gate 1 verweigert `$` in Pfaden und `do PYTHONPATH=…`).
- Stufen (DEC-0059/0063): Opus Umsetzer, Opus Prüfer; kein Fable-Designpass in dieser Generation.
- G4-1 zuerst spawnen (DEC-0070 Regel 4: der Volllauf-Gate vor allem anderen), dann die drei anderen
  parallel; Deckel 4.

Regeln, die Generation 3 gemessen hat und die im nächsten Auftrag stehen müssen: jede neue
Eigenschaftsbehauptung wird gemessen, bevor sie steht; nur lesende Suiten im Strom (fünfmal
verletzt, ~5 h); echte Shell als Schiedsrichter, wo die Wahrheit über die Shell ausführbar ist;
Kopien von Worktrees OHNE `.git`; Scratch nur unter `_round-scratch/<TSK>/`; VERSION-Hunks nicht
im Patch; Rot-zuerst-Rig verweigert außerhalb seines Verzeichnisses und schreibt binär (der
CRLF-Vorfall); Löcherlisten-Zitate mit Modulpräfix; ein benannter Test muss scheitern können
(vier Fälle in Generation 3).

Offen beim Nutzer, ohne Eile: Push von Generation 3 (`6704221`, `46eaaf2`, Folge-Commit) --
ja/nein; Geschmacksurteil Humanizer-Paar (drei Fassungen in
`staging/TSK-0111/research-existing-humanizers.md` §4) für FR-0072; der zurückgestellte Block
(interaktives Backlog-System FR-0024, FR-0023, FR-0025, FR-0019, FR-0022, FR-0081, FR-0033) als
eigene Generation, wenn er es sagt.

Abgeschlossen im Zustand: TSK-0115..0120 CANCELLED (= über 6704221 geliefert) und archiviert; die
zehn gelieferten FRs MERGED und archiviert; sieben weitere FRs in PR-0004..0006 aufgegangen;
BUG-0083..0086 und BUG-0089 VERIFIED; DEC-0064..0070 VALID; H125/H136/H144/H150 geschlossen,
H126/H127 verkleinert, H128/H149 reserviert-unbenutzt, H129-H135/H137-H143/H145-H148 offen mit
Ketten; keine offene Freigabe-Anfrage.
