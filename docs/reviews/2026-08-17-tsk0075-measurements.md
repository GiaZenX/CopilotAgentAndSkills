# TSK-0075 — Messungen (Block A, Runde A4a)

Auftrag aus `project_memory/tasks/active/TSK-0075.yaml` (BUG-0049, BUG-0050, FR-0027).
Alle Messungen gegen den **laufenden** Code: die Kit-Hooks als echte Prozesse mit JSON auf stdin
gegen ein Projekt **außerhalb** des Repos (`C:\Temp\tsk0075\proj`), der Kernel gegen ein aus dem
**ausgelieferten** `dev-team`-Kit gestelltes Projekt (`C:\Temp\tsk0075\fr27`). Rot-ohne-Fix in einem
Klon außerhalb des Repos (`C:\Temp\tsk0075\clone`).

---

## 1. BUG-0049 — die Durchlass-Zeile sagte in acht von acht Fällen das Falsche

### 1.1 Gemessen (vorher)

`team-kits/dev-team/hooks/gate_subagent_output.py:38-47` (Stand vor dieser Runde): auf
`stop_hook_active` wurde protokolliert und mit 0 beendet; die Zeile lautete
`"%s still missing %s" % (atype, ",".join(missing) or "nothing")`.

Drei echte Hook-Prozesse, ein Projekt außerhalb des Repos, `stop_hook_active: true`:

| Nachricht des Subagenten | rc | Protokollzeile |
|---|---|---|
| `summary: I did the work\nstatus: DONE` | 0 | `gave_up` — `backend-developer still missing nothing` |
| `all done!` | 0 | `gave_up` — `backend-developer still missing summary` |
| `summary: reviewed` (quality-engineer) | 0 | `gave_up` — `quality-engineer still missing verdict` |

Der erste Fall ist der, den Pilot 3 achtmal aufzeichnete: der Wiederholungsversuch **hatte
geliefert**, die Sperre hat funktioniert, und die Aufzeichnung meldet ein Aufgeben.

### 1.2 Zweiter, nicht gemeldeter Befund derselben Zeile

Der Durchlass-Zweig stand **vor** den beiden Zuständigkeitsprüfungen (`atype` gesetzt, Rollendatei
vorhanden). Gemessen, gleiches Verfahren:

| `agent_type` | rc | Protokollzeile |
|---|---|---|
| `Explore` (Fremdagent, den dieses Gate auf jedem anderen Pfad durchlässt) | 0 | `gave_up` — `Explore still missing summary` |
| `""` (kein Agenttyp) | 0 | `gave_up` — ` still missing summary` |

Zwei Vertragsverletzungen, protokolliert gegen Agenten, die keinen Vertrag schulden. Das ist
dieselbe Ungenauigkeit wie AC-1 und wurde mitgeschlossen.

### 1.3 Gebaut

`team-kits/*/hooks/gate_subagent_output.py`: Zuständigkeit **vor** Zustand; der Durchlass schreibt
`retry_delivered` mit `"<rolle>: retry delivered the output contract"` bzw. `gave_up` mit
`"<rolle>: giving up with <keys> still missing"`. `retro.py` zählt Nicht-Block-Ereignisse generisch
nach Namen, also wandert der neue Name ohne zweite Änderung in die Retro.

### 1.4 Nachher, gleiche Messung

| Fall | rc | Protokollzeile |
|---|---|---|
| Vertrag geliefert | 0 | `retry_delivered` — `backend-developer: retry delivered the output contract` |
| zweite Verletzung | 0 | `gave_up` — `backend-developer: giving up with summary still missing` |
| `Explore` / kein Typ | 0 | **keine Datei, keine Zeile** |

### 1.5 Rot ohne Fix

Klon außerhalb des Repos, der ursprüngliche Zweig wörtlich wiederhergestellt
(`C:\Temp\tsk0075\red_b49.py`):

```
--- with the fix in place            2 passed
--- with the ORIGINAL defect restored
FAILED test_hooks.py::test_the_give_up_line_says_what_the_retry_did
FAILED test_hooks.py::test_a_foreign_agent_leaves_no_give_up_record
                                     2 failed
--- restored                         2 passed
```

Der erste Fehlschlag zitiert wörtlich `{'event': 'gave_up', 'reason': 'backend-developer still
missing nothing'}`, der zweite `'Explore still missing summary'`.

### 1.6 AC-2 — der Durchlass bleibt, benannt

**Entscheidung: behalten.** Der Provider setzt `stop_hook_active` auf **jeder** Fortsetzung, die ein
Stop-Hook verursacht hat; ein erneutes Blockieren ist also keine zweite Chance, sondern eine
Endlosschleife. Ein begrenzter Zähler bräuchte beschreibbaren Zustand, der eine
Durchsetzungsfrage entscheidet — genau die Form, die dieses Repo beim Push-Token abgelegt hat.
Kein Kit registriert einen zweiten blockierenden `SubagentStop`-Hook (gemessen in
`team-kits/dev-team/settings/settings.json`: `notify_agent_events` + dieses Gate).

Benannt ist er im Modul-Docstring von `gate_subagent_output.py` (Absatz „THE ONE-RETRY
PASS-THROUGH …"), der `test_the_give_up_line_says_what_the_retry_did` als Messung nennt; dieser Test
behauptet den Durchlass mit (`rc 0` auf der verletzenden Wiederholung), damit er nicht versehentlich
geschlossen und still grün bleibt.

**Vorschlagstext für die Löcherliste** (`docs/POST_V2_WISHLIST.md` ist für diesen Umsetzer
gesperrt — der Lead trägt ihn ein oder verwirft ihn):

> ### H49 — Die zweite Vertragsverletzung eines Subagenten läuft ungebremst durch (neu, TSK-0075)
>
> **Mechanismus:** `gate_subagent_output` blockiert einen Spezialisten, der ohne seinen
> Ausgabeblock stoppt. Der Provider setzt auf der dadurch ausgelösten Fortsetzung
> `stop_hook_active`, und der Hook ehrt dieses Flag: er beendet mit 0, statt erneut zu blockieren.
> Wäre es anders, liefe der Subagent in eine Endlosschleife, denn das Flag steht auf jeder
> weiteren Fortsetzung ebenfalls. Damit ist genau die **zweite** aufeinanderfolgende Verletzung
> ungeblockt — der PM baut dann doch auf Prosa.
>
> **Kette (gemessen 2026-08-17, echter Hook-Prozess, Projekt außerhalb des Repos,
> `docs/reviews/2026-08-17-tsk0075-measurements.md`, Abschnitt 1):** `SubagentStop` mit
> `stop_hook_active: true` und der Nachricht `all done!` → **rc 0**, Protokoll
> `gave_up — backend-developer: giving up with summary still missing`. In Pilot 3 wurde die Kette
> nicht durchlaufen: alle 8 gemessenen Fälle waren gelieferte Wiederholungen (B13).
>
> **Urteil: offen, nicht schließbar mit den Mitteln dieses Ereignisses.** Was stattdessen begrenzt:
> (a) es braucht **zwei** Verletzungen hintereinander, die erste wird blockiert und mit einer
> Anweisung beantwortet, die nur den Ausgabeblock verlangt; (b) der Durchlass ist seit TSK-0075
> **zustandsgenau protokolliert** — `gave_up` heißt jetzt wirklich aufgegeben, `retry_delivered`
> heißt, die Sperre hat gewirkt —, sodass die Retro des PM den Fall zählen kann statt ihn im Rauschen
> von acht Fehlmeldungen zu verlieren; (c) ein Zähler pro Subagentenlauf wäre beschreibbarer
> Zustand, der eine Durchsetzungsfrage entscheidet, und ist deshalb bewusst nicht gebaut.

---

## 2. BUG-0050 — zwei gemessene Ausbrüche, beide gefangen; die Grenze benannt

### 2.1 Gemessen (vorher)

`team-kits/dev-team/hooks/guard_question_context.py`: die R2-Heuristik zählt **verschiedene**
Treffer aus `_TECH_VOCAB_RX` und warnt ab zwei. Echte Hook-Prozesse, Rohdaten-UTF-8:

| Frage (Klasse aus Pilot 3, Wortlaut rekonstruiert) | rc | stderr |
|---|---|---|
| Git-Identität (Name/E-Mail für die Commits) | 0 | **still** |
| Fenster-Titelleiste („Was steht oben in der Titelleiste?") | 0 | **still** |
| „SQLite ablegen und in Python schreiben?" (der Fang aus dem Piloten) | 0 | `[team-kit note] … technical choices (python, sqlite)` |
| drei Produktfragen (Ablageort, Nummernstart, Logo-Position) | 0 | still |

### 2.2 Entscheidung je Ausbruchsklasse

Beide Klassen werden **gefangen, als WARNUNG**, nicht als Block. Grund: die Nutzerentscheidung vom
2026-07-24 stellt R2/R13 ausdrücklich als warnend-nie-blockierend; R2b ist dasselbe Urteil über
Wortwahl und erbt die Antwort, statt sie neu aufzumachen. Blockierend ist in diesem Hook nur die
Regel mit der harten, prüfbaren Eigenschaft (die Frage verweist auf etwas, das nicht dasteht).

Beide Klassen teilen eine **Eigenschaft**, und die ist die Mitgliedsregel der neuen Wortmenge:
*ein Wort, das die Person nur hat, weil ein Rechner und eine Werkzeugkette existieren* — eine
Rechnung hat keine Titelleiste und keinen Commit. Daraus fällt die Schwelle: R2 braucht **zwei**
Treffer, weil seine Wörter eine Produktlesart haben („Datenbank", „Index"); R2b braucht **einen**,
weil seine keine haben.

### 2.3 Gebaut

* `_MACHINE_VOCAB_RX` + `_MACHINE_VOCAB_MIN = 1` und eine dritte Warnung (`kind="R2b"`) in
  `team-kits/*/hooks/guard_question_context.py`.
* **Ausnahme für kernel-erzeugte Fragen:** eine Frage mit `[APR-REQ:<id>]` bekommt keine
  Wortwahl-Beratung. Ohne sie hätte **jede** Push-Freigabefrage eine Falschwarnung getragen
  (gemessen unten) — und die Beratung hätte zum Umformulieren des einen Textes geraten, dessen
  Umformulierung nichts mintet (Pilot 3, B15).
* `repository`/`repo` wieder aus R2b entfernt: `repository-pattern` ist ein R2-Wort, und eine Frage
  mit zwei Urteilen über eine Grenze ist Rauschen.

### 2.4 Nachher, gleiche Messung

| Fall | rc | stderr |
|---|---|---|
| Git-Identität | 0 | `[team-kit note] … only the MACHINE has (commits, git)` |
| Titelleiste | 0 | `[team-kit note] … only the MACHINE has (titelleiste)` |
| „python, sqlite" | 0 | unverändert R2 (`technical choices`) |
| drei Produktfragen | 0 | still |

Die Ausnahme, gegen die **echte** Kernel-Frage
(`Freigabe erbeten: push für push -> origin/main @ aaaaaaaa … [APR-REQ:bbbb…]`):

| Variante | rc | stderr |
|---|---|---|
| die Frage, wie der Kernel sie baut | 0 | still |
| derselbe Text ohne Marker | 0 | `… only the MACHINE has (push)` |
| Marker als Beinahe-Treffer `[APR-REQ:short]` | 0 | `… only the MACHINE has (push)` |

Und die Gegenprobe, warum das kein Ausweg ist: `gate_approval.py` als echter Prozess auf demselben
Ereignis — eine Frage mit **wohlgeformtem** Marker ohne passende Anfrage ist **rc 2**
(„no pending approval request aaaa… "), ein Beinahe-Treffer ist ihm markerlos (**rc 0**). Wer den
Marker anlegt, um die Warnung zu kaufen, wird vom nächsten Hook geblockt; wer ihn falsch schreibt,
bekommt die Warnung trotzdem. Deshalb ist die Marker-Schreibweise beider Hooks **gepinnt**.

### 2.5 Rot ohne Fix (vier Ablationen im Klon, `C:\Temp\tsk0075\red_b50.py`)

| Ablation | betroffener Test | Ergebnis |
|---|---|---|
| R2b-Heuristik entfernt | `test_the_two_escape_classes_warn_and_product_questions_stay_quiet` | 3 failed, 3 passed → restored 6 passed |
| Marker-Ausnahme entfernt | `test_the_advice_exemption_uses_gate_approvals_own_marker` | 1 failed → restored 1 passed |
| Marker lose gelesen (`\[APR-REQ:`) | + `test_the_guard_and_the_gate_spell_the_approval_marker_the_same` | 2 failed → restored 2 passed |
| `repository` zurück in R2b | `test_no_question_gets_both_verdicts_about_one_boundary` | 1 failed → restored 1 passed |
| `ENFORCEMENT.md`-Zeile auf ihren alten Wortlaut zurück | `test_the_enforcement_table_names_every_warning_the_guard_emits` | 1 failed → restored 1 passed |

### 2.6 AC-2 — was Kit-Texte über die Eigenschaft behaupten

Gesichtet: alle drei Verfassungen, die PM-Skills, die drei `hooks/ENFORCEMENT.md`.

* Die Verfassungssätze („ASK product questions only", „A technical question to the user is a
  defect", §14) sind **Pflichten an den PM**, keine Schutzbehauptungen — sie bleiben unverändert.
  Der einzige Satz, der einen Hook nennt (§5a/2: „`guard_question_context` refuses it on Claude"),
  bezieht sich auf die **Selbstenthaltungs-Regel**, und die blockiert der Hook wirklich.
* Zu wenig sagte `hooks/ENFORCEMENT.md`: die Zeile zu `guard_question_context` nannte nur die
  blockierende Hälfte. Eine Tabelle, die zwei (jetzt drei) Warnungen verschweigt, lässt die Rolle,
  die gerade eine `[team-kit note]` bekommen hat, ohne Zeile dazu — und die Grenze dieser Warnungen
  steht dann nirgends, wo sie gelesen wird. Die Zeile nennt jetzt die drei Warnungen, dass sie
  Wortnetze über den Fragetext sind (**eine technische Frage ohne solches Wort geht durch**) und die
  Marker-Ausnahme. In allen drei Kits, gleicher Wortlaut.
  Das ist **abgeleitet statt gemerkt**: `test_the_enforcement_table_names_every_warning_the_guard_emits`
  liest die Warn-Arten aus den `_warn`-Aufrufen des Hooks (`ast`) und verlangt jede davon in der
  Zeile jedes Kits — eine vierte Heuristik kann nicht in eine Tabelle einziehen, die noch drei
  beschreibt.

**Die benannte Grenze, ausdrücklich:** R2b ist ein **Wortnetz**, keine Bedeutungsprüfung. Eine
technische Frage ohne eines dieser Wörter erreicht den Nutzer weiterhin. „Freitext-Sprachurteil"
war im Auftrag ausgeschlossen, und der Modul-Docstring sowie `ENFORCEMENT.md` sagen die Grenze
jetzt hin, statt sie durch Schweigen zu bestreiten.

---

## 3. FR-0027 — die Preset-Frage nennt das Team DANACH und was entfernt wird

### 3.1 Gemessen (vorher), gegen den laufenden Kernel

Gestellt aus dem ausgelieferten `dev-team`-Kit (dessen eigene `presets.yaml`: `solo` = 4
Spezialisten, `duo` = 6), also literally die Aufwertung, die FR-0027 beschreibt:

```
QUESTION: Freigabe erbeten: preset für [preset: duo, removes: -, roles: backend-developer /
devops-engineer / frontend-developer / project-auditor / quality-engineer / software-architect]
(Revision -, subject_manifest sha256 6d8e831b1d10…). …
```

Vier der sechs Namen sind bereits installiert; `removes: -` ist der Platzhalter für die leere Liste.
Die entfernende Richtung (`duo → solo`) rendert `removes: devops-engineer / frontend-developer`
unter demselben Maschinen-Schema.

### 3.2 Die Entscheidung, und warum sie vom Wortlaut des Items abweicht

**Gebaut ist: die Frage nennt die Rollen, die das Projekt DANACH hat, und jede, die entfernt wird.
Nicht gebaut ist: welche davon neu sind.** Das ist eine bewusste Abweichung vom Wunschtext
„nennt, was HINZUKOMMT und was WEGFÄLLT" und hier ist die Messung dazu:

Die hinzukommende Menge ist *Ziel minus Installiertes*. Das Installierte steht **nicht** im
gehashten Manifest — absichtlich, weil die Freigabe an das ERGEBNIS gebunden ist
(`approvals.preset_subject_manifest`). Und der Auftrag verbietet ausdrücklich, das Manifest zu
ändern. Zwei verschiedene Ausgangslagen, dieselbe angefragte Aufstellung, gemessen gegen den
laufenden Kernel:

| installiert | angefragt | `subject_manifest_hash` | „hinzu" wäre |
|---|---|---|---|
| die 4 aus `solo` | `duo` | `6d8e831b1d10eb61…` | 2 Rollen |
| nur `software-architect` | `duo` | `6d8e831b1d10eb61…` (identisch) | 5 Rollen |

Ein Delta in der Frage wäre also der eine Satz darin, den der Nutzer unterschreibt und der Hash
**nicht** deckt; `set-preset` nähme dieselbe Freigabe in beiden Zuständen an. Die zweite
Möglichkeit — das Installierte ins Manifest aufnehmen — wurde verworfen, weil sie genau die
Hash-Semantik verschiebt, die das Item unbewegt haben will.

Der Ankersatz der Verfassungen wurde deshalb auf das heruntergezogen, was der Code baut
(Hausregel: kein Text behauptet Schutz, den der Code nicht baut) — in beiden Richtungen, also auch
ohne Alarm: `team-kits/dev-team/constitution/AGENTS.md:208`,
`team-kits/research-team/constitution/AGENTS.md:217`,
`team-kits/dev-team/skills/project-manager/SKILL.md:161`,
`team-kits/research-team/skills/project-manager/SKILL.md:138`.

### 3.3 Gebaut

`team-kits/kernel/approvals.py`: `_push_target_form` (unverändertes Verhalten, aus dem `if`-Zweig in
eine Funktion gehoben), `_preset_target_form` (neu) und die Zuordnung `TARGET_FORMS`. Der generische
Zweig, der das gehashte Manifest Schlüssel für Schlüssel rendert, bleibt die Vorgabe für jede Art
ohne Eintrag.

### 3.4 Nachher, und die geforderte Bytemessung

```
QUESTION: Freigabe erbeten: preset für die Rollen-Aufstellung 'duo' -- danach im Team:
backend-developer, devops-engineer, frontend-developer, project-auditor, quality-engineer,
software-architect; entfernt: keine (Revision -, subject_manifest sha256 6d8e831b1d10…). …

QUESTION: Freigabe erbeten: preset für die Rollen-Aufstellung 'solo' -- danach im Team:
backend-developer, project-auditor, quality-engineer, software-architect; entfernt:
devops-engineer, frontend-developer (Revision -, subject_manifest sha256 880b41bea94d…). …
```

Manifest **unbewegt**, gleiche Übergänge, vor und nach der Änderung:

| Übergang | sha256 über `yaml.safe_dump(manifest)` | `subject_manifest_hash` |
|---|---|---|
| `solo → duo` vorher | `28203a00195e57bcc21da1cc40d8c249a6ce4aa025c0bbda306941a8b07c64e8` | `6d8e831b1d10eb615179b63118b9784df8ff1a31a81d93b1c8fcf2f17ca7cbfa` |
| `solo → duo` nachher | **identisch** | **identisch** |
| `duo → solo` vorher | `dd7d7eac21b8d75fb452b8b84f0e389c3ce598927a380cc4c08a130088f61d0c` | `880b41bea94d86f07875d4a38f0f4f13a8289a01d5c580f99908e193135e9bac` |
| `duo → solo` nachher | **identisch** | **identisch** |

Die Options-Beschreibung, die der Nutzer anklickt, trägt denselben Satz — sie ist Teil dessen, was
`gate_approval` Zeichen für Zeichen vergleicht.

### 3.5 Rot ohne Fix (`C:\Temp\tsk0075\red_fr27.py`)

| Ablation | Tests | Ergebnis |
|---|---|---|
| `preset` aus `TARGET_FORMS` entfernt | `…names_the_team_afterwards_and_what_goes`, `…resolver_answers_with_nothing…`, `…every_target_form…` | 3 failed → restored 3 passed |
| Manifest trägt `installed=sorted(current)` | `test_the_added_roles_are_not_what_a_preset_approval_binds` | 1 failed → restored 1 passed |

Die zweite Ablation ist der Stolperdraht in die andere Richtung: sobald das Manifest trägt, was ein
Delta bräuchte, wird dieser Test rot — und dann ist eine Delta-Darstellung baubar.

---

## 4. Was mit welchem Werkzeug nachgezogen wurde

*(Endstand nach Runde 3; die Zahlen der einzelnen Läufe stehen im Journal, nicht hier.)*

* `tools/pin_constitution_sections.py --write --note …` — drei Läufe: 7 Abschnitte in Runde 1
  (2 Verfassungen, 2 PM-Skills, 3 `ENFORCEMENT.md`), 7 in Runde 2 (office kommt dazu, die
  Begründung wird korrigiert), 3 in Runde 3 (die drei `ENFORCEMENT.md`). Journal in
  `docs/reviews/phase0-disposition.md`, Abschnitt 9.
* `tools/record_lead_package_sizes.py --write --note …` — Endstand dev `34867 B`,
  office `36024 B`, research `38950 B`.
  **Die erste Fassung dieser Zeile war falsch:** sie las „office unverändert (dessen Verfassung
  trägt den Preset-Satz nicht)". `team-kits/office-team/constitution/AGENTS.md` trug den Satz sehr
  wohl — in der alten Form; warum der Sweep ihn nicht fand, steht in 4b/F1. Office ist seit Runde 2
  mitgezogen, und seit Runde 3 hängt die Aussage aller drei Verfassungen am Renderer statt an einem
  Sweep (4c).
* `tools/bump_kit_version.py` — alle drei Kits, Endstand `2026.08.18-3`.
* Spiegel: `gate_subagent_output.py`, `guard_question_context.py` byte-identisch über alle drei Kits
  (sha256-Vergleich); `ENFORCEMENT.md` ist in `KIT_SPECIFIC_HOOKS` mit Grund geführt und pro Kit
  gepflegt.

## 4a. Die Abnahmeläufe

Gegen den ausgelieferten Stand `2026.08.18-3` (Runde 3; die Läufe der Runde 1 gegen
`2026.08.17-13` sind damit ersetzt und stehen hier nicht mehr, damit nur eine Zahl gilt):

* `python -m ruff check .` — All checks passed
* `python tools/validate.py` — all structural checks passed
* `python -m pytest tools/ -q` — **2824 passed, 13 skipped** (35:10)
* `python -B -m pytest .claude/hooks/test_gates.py -q` — **243 passed** (48:30)
* Spiegel: `gate_subagent_output.py` `a992aff2be65e3f4`, `guard_question_context.py`
  `b376055f23357a22` — je ein Hash über alle drei Kits.

**Nicht von diesem Umsetzer:** während der Runde sind `CLAUDE.md` (ein Absatz über
`decisions/active/` und `DEC-0034`), `project_memory/.audit/hook_events.jsonl` sowie neue Items
(`DEC-0047`, `FR-0049`…`FR-0052`, `TSK-0076`) im Arbeitsbaum aufgetaucht. Beides liegt außerhalb
des erlaubten Bereichs dieses Auftrags und wurde hier nicht angefasst; es steht hier, damit es
niemand dieser Runde zurechnet.

*[Nachtrag Lead 2026-08-18, auf Prüfer-Befund N1 (Runde 2): zwei weitere Änderungen im Baum sind
MEINE — die Korrektur von `project_memory/bugs/active/BUG-0050.yaml` (`observed`, über den
Kernel geschrieben) und der Korrekturkasten in
`docs/pilot/2026-08-14-pilot-3-rechnungswerkzeug.md` (Blockzählung 61 → 59 + 2 Warnungen).
Beide setzen den F3-Befund dieser Runde in die betroffenen Akten um und wurden in der Sitzung
angekündigt; der Prüfer hat zu Recht verlangt, dass dieser Absatz sie ausdrücklich zuordnet.]*

## 4b. Runde 2 — die Prüfbefunde F1–F8 (2026-08-18)

Der Prüfer hat FAIL gegeben. Drei Blocker, vier Reste. Die FR-0027-Abweichung selbst wurde
**bestätigt** (er hat beide Hash-Messungen nachgestellt und zusätzlich eine echte Freigabe geprägt,
die in zwei Installationszuständen gilt) und liegt jetzt als **DEC-0048** fest; die Begründungen
zitieren diese Nummer.

### F1 (blockierend) — office trug den alten Satz, und mein Bericht behauptete das Gegenteil

**Meine Aussage in Abschnitt 4 war falsch** („office unverändert (dessen Verfassung trägt den
Preset-Satz nicht)"). `team-kits/office-team/constitution/AGENTS.md:254` trug den Satz sehr wohl —
in der ALTEN Form „(the question names every role added and removed)". Der Grund für den Fehlgriff
ist der lehrbuchhafte: mein Sweep war ein **zeilenweiser** `grep`, und genau in diesem Kit bricht
der Satz mitten in der Wendung um (`added and` / `removed)`), also fand er nichts. Eine
Zeichenkettensuche über eine Datei misst die Datei, nicht die Aussage.

**Gebaut:** office bekommt denselben heruntergezogenen Satz. Dazu — wie vom Prüfer verlangt — der
**abgeleitete** Stolperdraht `test_every_kit_constitution_describes_the_preset_question_the_kernel_builds`:
er **ruft den Renderer auf** (`approvals.TARGET_FORMS["preset"]`), flacht jede Verfassung, die
`request-approval preset` überhaupt nennt, auf eine Zeile ab und verlangt, dass sie die zwei
gerenderten Hälften beschreibt und die dritte nicht verspricht. Drei Kits geprüft.

### F2 (blockierend) — meine Begründung war zu stark und messbar falsch

Behauptet hatte ich: „was installiert ist, steht nicht im gehashten Manifest". **Selbst
nachgemessen, gleicher Aufbau wie Abschnitt 3:**

| installiert | angefragt | `removes` | `subject_manifest_hash` |
|---|---|---|---|
| die 4 aus `solo` | `duo` | `[]` | `6d8e831b1d10` |
| alle Rollen (`team`) | `duo` | `product-designer, research-engineer, tech-writer, ux-researcher` | `c82f5a2fb91e` |

Der Hash **bewegt sich** also mit dem Installationszustand — `removes` ist zustandsabgeleitet
(`kernel/presets.py:236`) und gehasht. Außerhalb liegt **nur der Schnitt** (installiert ∩ Ziel), und
das ist genau die Menge, aus der ein Delta berechnet würde. Korrigiert in allen Heimaten:
`team-kits/kernel/approvals.py:781-786`, den drei Verfassungen, den zwei PM-Skills; die
Journal-Zeilen sind **append-only**, also steht die Korrektur dort als neue Zeile in der Konvention
des Journals selbst (beide `--write --note`-Läufe sagen ausdrücklich „KORREKTUR der Notiz von heute
früh"). Der Renderer-Kommentar zitiert `DEC-0048`.

Gemessen wird die korrigierte Aussage jetzt von
`test_the_removed_roles_ARE_hashed_so_the_approval_follows_the_installation` — genau die Tatsache,
die der alte Satz bestritt.

### F3 (blockierend) — jede Warnung stand als `block` im Protokoll

**Gemessen** (echter Hook-Prozess, rc 0):
`{"hook": "guard_question_context", "event": "block", "reason": "R2b: …"}`. `_warn` rief
`_audit.record`, und das ist die Block-Schreibweise (`_audit.py:80-81`). Folgen, beide belegt:
`retro.py:93` zählt `event == "block"` als „gates blocked work" — und **die Pilot-3-Forensik hat
genau das gelesen**: die zwei Zeilen, die als „`guard_question_context` fing 2 technische Fragen ab"
in BUG-0050 stehen, waren R2-**Warnungen**. Gefangen wurde nichts; vier technische Fragen erreichten
die Persona. Das ist derselbe Defekt wie BUG-0049, eine Datei weiter: eine Aufzeichnung, die sagt,
die Durchsetzung habe etwas getan, was sie nicht getan hat.

**Gebaut:** `record_event("guard_question_context", "warn", …)`. Nachher gemessen:
`{"event": "warn", …}` bei rc 0. Der Hook-Docstring nennt den Fall und den Test; der Modul-Docstring
sagt jetzt hin, was Pilot 3 **nicht** gezeigt hat.

### F4 (Rest, entschieden) — die Wortmenge hielt ihre eigene Mitgliedsregel nicht ein

Der Prüfer hat **8 Produktfragen** gemessen, jede mit **einem** mehrdeutigen Wort, jede fälschlich
gewarnt. Nachgestellt und um eine neunte ergänzt (Shell-Tankkarte). **Entscheidung: beides**, wie
angeboten — zwei Stufen *und* der ehrliche Regelsatz:

* Stufe 1 (ein Treffer genügt): Wörter, deren **dominante** Lesart die Maschine ist — `git`,
  `rebase`, `pull request`, `commits?`, Titelleiste/Fenstertitel/Taskleiste/Startmenü,
  Datei-Explorer, Eingabeaufforderung/Kommandozeile/Befehlszeile, PowerShell, Umgebungsvariable.
* Stufe 2 (**zwei** verschiedene Treffer, R2s Schwelle und R2s Grund): `push`, `branch`, `merge`,
  `commit\w*`, `terminal`, `konsole`/`console`, `explorer`, `shell`, `betriebssystem`/
  `operating system`.

**Mitgliedschaft in Stufe 2 ist keine Meinung, sondern die Messung:** ein Wort, das dieses Repo
**in einer Produktfrage gesehen hat**, steht dort — und der Korpus, der es gesehen hat, ist der Test.

Nachher, alle 15 Fälle gegen den laufenden Hook: **9/9 Produktfragen still**, **5/5 gewollte
Warnungen erhalten** (inkl. Git-Identität *ohne* das Wort „git", über `commits?`, und der Fall mit
zwei mehrdeutigen Wörtern). `:120` („bought by the two escapes … and by nothing else") ist ersetzt:
die Menge ist absichtlich breiter als zwei Sätze, weil eine Klasse kein Satz ist.

**Dabei selbst gefunden:** einer meiner neun Gegenbeispiel-Sätze („automatisch gemerged") traf
**kein einziges** Muster — `merge\w*` ist an einer Wortgrenze verankert, die Präfixform passt nicht.
Der Fall wäre unabhängig vom Code immer grün geblieben; aufgefallen ist er nur, weil er die Ablation
überlebte, während sieben rot wurden. Behoben, und ein Test verhindert die Wiederholung:
`test_every_ambiguous_case_exercises_the_tier_it_measures` liest das **ausgelieferte Musterobjekt**
und verlangt pro Satz einen Treffer und pro Satz ein **anderes** Wort.

### F5, F6, F7, F8 (Reste, behoben)

* **F5:** der „pinned"-Zeiger nennt jetzt den Test statt `main`.
* **F6:** `_warn` hängt `_compat.reference_note()` an — gemessen vorher „ENFORCEMENT im stderr:
  **False**", nachher **True**. Eine gewarnte Rolle bekam bis jetzt die einzige Tabelle nicht zu
  sehen, die die Grenzen der Heuristik nennt.
* **F7:** die `gate_subagent_output`-Zeile nennt den Ein-Wiederholungs-Durchlass in allen drei Kits,
  **abgeleitet** gemessen: `test_the_enforcement_table_names_the_condition_the_gate_does_not_refuse_under`
  liest die Ereignisnamen aus dem `record_event`-Aufruf des Hooks (die zweite Stelle ist ein
  Bedingungsausdruck, also aus dessen Teilbaum) und verlangt beide plus `stop_hook_active` in der
  Zeile.
* **F8:** statt den Satz zu kürzen, ist der Test auf die zweite Hälfte **erweitert**:
  `test_the_added_roles_are_not_what_a_preset_approval_binds` prägt jetzt eine echte Freigabe über
  den Freigabe-Hook, verschiebt danach die Installation **innerhalb** der Zielmenge und misst, dass
  `live_line_approval` sie weiterhin trägt und `presets.apply` durchläuft.

### Folgeschaden von F4, den der Abschlusslauf gefunden hat — und die Korrektur der Begründung

Der volle Suite-Lauf nach F4 warf `test_the_advice_exemption_uses_gate_approvals_own_marker` rot:
der Test hatte gemessen, dass die **unmarkierte** Push-Freigabefrage warnt — und mit `push` in der
zweiten Stufe warnt sie nicht mehr. Damit war die **Begründung** der Marker-Ausnahme („die
Push-Frage würde einen Falschalarm auslösen") nicht mehr wahr.

Nachgemessen über **jede** Freigabe-Art, die ein Manifest hat (`push`, `preset`, `kit_update`,
`routine`), markiert und unmarkiert: **keine einzige** vom Kernel gebaute Frage löst heute noch eine
der drei Heuristiken aus. Also:

* Die Ausnahme **bleibt** — sie ist strukturell richtig (eine Beratung über Wortwahl hat zu einem
  Text, den der PM nicht umformulieren darf, nichts zu sagen) und ihr Wegfall hinge daran, dass sich
  Kernel-Wortlaut und Wortstufen zufällig nicht überschneiden.
* Der Kommentar sagt jetzt **hin**, was gemessen ist und was nicht: der Falschalarm war auf der
  ersten Fassung von R2b real, heute schützt die Ausnahme die nächste Formulierung, nicht die
  heutige — und live gemessen bleibt die andere Hälfte.
* Der Test misst jetzt genau diese Hälfte, mit einer Frage, die das Modell geschrieben haben könnte:
  voller Maschinenwörter, mit angeklebtem, wohlgeformtem Marker. Hier still, bei `gate_approval`
  **rc 2**; mit Beinahe-Marker hier laut, bei `gate_approval` **rc 0**. Die alte Zusicherung wäre auf
  Leere durchgelaufen.

### Rot ohne Fix, Runde 2 (Klon außerhalb des Repos, `C:\Temp\tsk0075\red_round2.py`)

| Ablation | Test | Ergebnis |
|---|---|---|
| office-Verfassung zurück auf die alte Zusage | `…constitution_describes_the_preset_question…` | 1 failed → restored |
| dev-Verfassung zurück auf die alte Zusage | dasselbe (der Draht ist nicht office-spezifisch) | 1 failed → restored |
| `_warn` schreibt wieder `_audit.record` | `test_a_warning_is_recorded_as_a_warning_and_not_as_a_block` | 1 failed → restored |
| mehrdeutige Wörter zurück in Stufe 1 | `test_a_single_ambiguous_word_is_not_a_technical_question` | 7 failed, 2 passed → restored 9 passed |
| `reference_note()` wieder entfernt | `test_a_warning_is_recorded_as_a_warning_and_not_as_a_block` | 1 failed → restored |
| Durchlass-Klausel aus der ENFORCEMENT-Zeile | `…names_the_condition_the_gate_does_not_refuse_under` | 1 failed → restored |
| Marker-Ausnahme entfernt (neuer Test) | `test_the_advice_exemption_uses_gate_approvals_own_marker` | 1 failed → restored |
| Marker lose gelesen (neuer Test) | + `…spell_the_approval_marker_the_same` | 2 failed → restored |

(7 statt 9 in der vierten Zeile, weil die Ablation nur die acht Wörter zurückschiebt, die sie
benennt: `commit\w*` und `operating system` blieben in Stufe 2, ihre zwei Sätze also still.)

## 4c. Runde 3 — Übernahme einer abgebrochenen Nacharbeit (2026-08-18)

Der Umsetzer der Runde 2 ist **mitten in der Nacharbeit** abgebrochen. Diese Runde hat deshalb
zuerst festgestellt, was auf der Platte steht (`git diff` gegen HEAD `19d93f2`, Hunk für Hunk gegen
die Befundliste), und dann den Rest gebaut.

| Befund | Zustand bei der Übernahme | in dieser Runde |
|---|---|---|
| F1 office-Satz + abgeleiteter Draht | gebaut (`office-team/constitution/AGENTS.md:256`, `test_every_kit_constitution_describes_the_preset_question_the_kernel_builds`) | der Draht misst jetzt **beide** Hälften des Satzes (unten, (2)) |
| F2 zu starke Begründung in allen Heimaten | gebaut (`kernel/approvals.py:781-791`, drei Verfassungen, zwei PM-Skills, Journal-Korrekturzeilen) | unverändert |
| F3 `warn` als eigene Ereignisart | gebaut (`guard_question_context.py:191`) | unverändert |
| F4 zwei Wortstufen + ehrliche Mitgliedsregel | gebaut (`:149-164`, 9 Gegenbeispiele) | die Wortliste aus der `ENFORCEMENT.md`-Zeile entfernt (unten, (1)) |
| F5 „pinned" zeigt auf den Test | gebaut (`:60-67`) | unverändert |
| F6 `reference_note()` an der Warnung | gebaut (`:192`) | unverändert |
| F7 Durchlass in der ENFORCEMENT-Zeile | gebaut (alle drei Kits) | unverändert |
| F8 Test auf die Prägung erweitert | gebaut (`test_presets.py:704`) | unverändert |
| Abnahme | Stempel `2026.08.18-2`, pins/sizes geschrieben, **kein** Abschlusslauf | vollständig neu gefahren, Stempel `-3` |

Nichts davon war halb gebaut: jeder in 4b genannte Test existierte und lief grün (34 in
`tools/test_presets.py`, 40 in der Guard-/Gate-Auswahl von `tools/test_hooks.py`). Offen war der
**Abschluss** — und die zwei Defekte, die die Nacharbeit selbst mitgebracht hat.

### (1) Die ENFORCEMENT-Zeile trug die zweite Wortstufe als Liste

`(push, branch, merge, terminal, console, explorer, shell, operating system)` stand als Aufzählung
in allen drei `hooks/ENFORCEMENT.md` — eine Kopie des Musters, die schon bei der Auslieferung
ungenau war (`konsole`, `betriebssystem` und die `\w*`-Formen fehlen; `commits?` steht in der
ERSTEN Stufe und `commit\w*` in der zweiten). **Gemessen, dass sie niemand liest:** Ablation B9 —
die Liste zurückgeschrieben, alle 21 Guard-Tests **grün**. Eine Prosa-Kopie, die kein Test liest
und die schon abweicht, ist genau die Aufzählung, die eine Runde später der nächste Defekt ist.
Ersetzt durch die Eigenschaft plus Zeiger auf das ausgelieferte Muster
(`guard_question_context._AMBIGUOUS_VOCAB_RX`, dieselbe `hooks/`-Ablage wie die Tabelle) — die
Schreibweise, die dieselbe Datei für `gate_write_scope._ORDERING_COMMANDS` schon benutzt.
**Das ist eine Streichung, kein Fix, und hat darum keinen roten Test**; die Messung dazu ist B9.

### (2) Der F1-Stolperdraht maß nur die Hälfte, die er verlangt

`test_every_kit_constitution_describes_the_preset_question_the_kernel_builds` rief den Renderer auf
und prüfte die zwei Hälften, die er **druckt**. Die dritte Zusage der Verfassungen — „nicht, welche
davon neu sind" — stand nur als Prosa auf beiden Seiten: hätte ein späterer Renderer die neuen
Rollen genannt, wäre der Test grün geblieben und drei Verfassungen hätten das Gegenteil behauptet.
Genau der Satz, den Hausregel 3 in beide Richtungen verbietet. Der Test rendert jetzt **dieselbe
Zielmenge aus zwei Installationsständen** (`tools/test_presets.py:757`): das Manifest ist die
einzige Eingabe des Renderers und trägt den Schnitt aus Installiertem und Ziel nicht, also ist der
Satz aus beiden Ständen identisch, während „hinzu" `{beta}` bzw. `{alpha, beta}` wäre.
Gemessen als Ablation C4 gegen C5 (unten): das Manifest um `installed` erweitert lässt diesen Test
**grün** (dort schlägt der Manifest-Draht `…added_roles…` an), erst die daraus **gerenderte**
Delta-Zeile macht ihn rot.

### Rot ohne Fix, Runde 3 — jede Richtung neu gemessen

Klon **außerhalb** des Repos, jede Ablation einzeln angewandt und danach aus einer unberührten
Kopie zurückgesetzt (`C:\Temp\tsk0075b\ablate.py`, Klon `…\clone`, Referenz `…\pristine`).
Basislinie vorweg: 25 + 6 der ausgewählten Tests grün.

| # | Ablation | rot geworden |
|---|---|---|
| A1 | `gate_subagent_output.py` (alle Kits) zurück auf HEAD | `…give_up_line_says_what_the_retry_did`, `…foreign_agent_leaves_no_give_up_record`, `…enforcement_table_names_the_condition…` |
| A2 | die `gate_subagent_output`-Zeile der Tabelle zurück auf HEAD | `…enforcement_table_names_the_condition_the_gate_does_not_refuse_under` |
| B1 | `_warn` schreibt wieder über `_audit.record` (Art `block`) | `test_a_warning_is_recorded_as_a_warning_and_not_as_a_block` |
| B2 | `reference_note()` wieder aus der Warnung entfernt | dasselbe (die zweite Zusicherung desselben Tests) |
| B3 | `_AMBIGUOUS_VOCAB_MIN = 1` (R2bs erster Schnitt) | `test_a_single_ambiguous_word_is_not_a_technical_question` — **9 von 9** |
| B4 | Marker-Ausnahme entfernt | `test_the_advice_exemption_uses_gate_approvals_own_marker` |
| B5 | Marker loser gelesen als `gate_approval` ihn liest | dasselbe + `…spell_the_approval_marker_the_same` |
| B6 | `repository` zurück in R2b | `test_no_question_gets_both_verdicts_about_one_boundary` |
| B7 | R2b ganz entfernt | `…two_escape_classes…` (3 Fälle), `…recorded_as_a_warning…`, `…advice_exemption…`, `…enforcement_table_names_every_warning…` |
| B8 | die `guard_question_context`-Zeile der Tabelle zurück auf HEAD | `test_the_enforcement_table_names_every_warning_the_guard_emits` |
| B9 | die Wortliste zurück in die Tabelle (diese Runde) | **keiner** — die Messung zu (1) |
| C1 | office-Verfassung zurück auf „names every role added and removed" | `…constitution_describes_the_preset_question…` |
| C2 | dev-Verfassung zurück auf dieselbe alte Zusage | dasselbe (der Draht ist nicht office-spezifisch) |
| C3 | `approvals.py` zurück auf HEAD (kein `TARGET_FORMS`) | `…names_the_team_afterwards…`, `…every_target_form…`, `…constitution_describes…`, `…resolver_answers_with_nothing…` |
| C4 | das gehashte Manifest trägt `installed` | `test_the_added_roles_are_not_what_a_preset_approval_binds` |
| C5 | …und die Frage rendert das Delta daraus | zusätzlich `…constitution_describes…` — die Hälfte aus (2) |
| C6 | `removes` nicht mehr zustandsabgeleitet | `test_the_removed_roles_ARE_hashed…`, `…names_the_team_afterwards…` |

## 5. Reste, ausdrücklich benannt

1. **Der Ein-Wiederholungs-Durchlass bleibt offen** (Abschnitt 1.6) — Vorschlagstext H49 oben, der
   Lead entscheidet über den Eintrag in `docs/POST_V2_WISHLIST.md`.
2. **R2b ist ein Wortnetz, keine Bedeutungsprüfung, und das kostet in BEIDE Richtungen** — eine
   technische Frage ohne eines dieser Wörter erreicht den Nutzer weiterhin, **und** eine echte
   Umgebungs-Abklärung mit nur einem Wort der zweiten Stufe („was zeigt dein Terminal an?") bleibt
   seit F4 still, während eine Produktfrage mit zwei solchen Wörtern warnt. Beide Richtungen stehen
   im Docstring und in der `ENFORCEMENT.md`-Zeile, zu der eine gewarnte Rolle seit F6 auch wirklich
   geführt wird.
3. **Die Frage nennt kein Delta** (Abschnitt 3.2, jetzt `DEC-0048`) — bewusste Abweichung vom Wortlaut von FR-0027,
   mit der Messung, die sie trägt; die Kit-Sätze sind darauf heruntergezogen.
4. **Wie laut eine Warnung überhaupt ist**, bleibt wie gehabt schwach: auf `PreToolUse` erreicht nur
   exit 2 garantiert das Modell. Das steht seit 2026-07-24 im Docstring des Hooks und ist der Preis
   des Nicht-Blockierens, nicht ein Rest dieser Runde.
5. **Der Verfassungs-Draht misst die Aussage, nicht die Formulierung** — und das kostet in die
   Über-Verweigerungs-Richtung: er verlangt in jeder Verfassung, die `request-approval preset`
   nennt, die Wendungen „HAS afterwards", „not which of them are new" und die `DEC-0048`. Ein Kit,
   das denselben wahren Satz anders formuliert, wird rot, obwohl es nichts falsch behauptet. Das
   ist die bewusste Seite: die Alternative wäre ein Sprachurteil über Freitext, und das ist im
   Auftrag ausgeschlossen. Was der Draht dagegen **wirklich** ableitet, ist die Eigenschaft dahinter
   (Renderer aus zwei Installationsständen, 4c/(2)) — die Wendungen sind nur der Aufhänger.
6. **Der Zeiger `guard_question_context._AMBIGUOUS_VOCAB_RX` in den drei `ENFORCEMENT.md` löst
   nichts auf, was ein Test prüft.** Für Aussagen unter `.claude/hooks/` erzwingt `test_gates.py`
   das Auflösen eines in Backticks genannten Testnamens; für Kit-Dokumente gibt es keinen solchen
   Leser. Der Zeiger ist damit so haltbar wie der Name der Konstante — besser als die Wortliste, die
   er ersetzt (die war schon falsch und ebenfalls ungeprüft), aber nicht gebaut.
