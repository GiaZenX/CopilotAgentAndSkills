# TSK-0108 — Strom H „Messungen", Protokoll

Item: `TSK-0108` (derives_from `FR-0059`, acceptance_ref `AC-1`), Generation 2 nach `DEC-0057`/
`DEC-0060`. Arbeitsbaum `C:\Offline Repos\v2-testbed\_worktrees\g2-measure` (Branch `g2/measure`,
Basis `6d18407`), Rigs und Rohdaten unter
`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0108\`.

Der Strom lief in **zwei** Umsetzer-Läufen. Der erste wurde durch einen Nutzer-Stopp beendet, nicht
durch einen Fehler; dieser Abschnitt trennt darum, was vorgefunden war, von dem, was dieser Lauf
gemessen hat.

---

## 1. Vorgefunden (erster Lauf, 11:23–13:28)

Auf der Platte lagen: zwei Messdokumente unter `docs/reviews/`, ein neuer Prüfmodul
`tools/test_model_pins.py`, ein Zusatz in `tools/test_repo_hygiene.py`, drei Löcher-Einträge in
`docs/POST_V2_WISHLIST.md`. Ein Protokoll in `project_memory/staging/` gab es nicht — dieses hier
ist das erste.

Nachgeprüft und **übernommen**:

| Gegenstand | Stand | Beleg |
|---|---|---|
| `/cd` existiert im `-p`/SDK-Transport nicht | gemessen | `m12.log`, `m1.log` |
| Wortlaut des Trust-Dialogs | gemessen | `m2a.log` |
| Hooks des Ziels binden sofort, die des Starts fallen weg | gemessen | `cdrig/hooklog-m2b.jsonl`, `-m4` |
| `${CLAUDE_PROJECT_DIR}` bleibt am Startort | gemessen | dieselben |
| Registrierung des Ziels + Hook-DATEI des Starts (`H114`) | gemessen | `cdrig/hooklog-m10b.jsonl` |
| `agent:`-Bindung folgt keinem `/cd` (`H115`) | gemessen | `cdrig/hooklog-m4.jsonl`, Gegenprobe `-m7` |
| Subagenten des Ziels fehlen nach `/cd` | gemessen | `m4.log` (Task-Fehlertext) |
| Skills und MCP des Ziels binden sofort | gemessen | `cdrig/hooklog-m2b.jsonl`, `m8.log` |
| Ein `cd` im Bash-Werkzeug bindet nichts neu | gemessen | `cdrig/hooklog-m2b.jsonl` |
| Registrierung wird mitten in der Sitzung nachgelesen (`H116`) | gemessen, 5 Läufe | `cdrig/hooklog-m3.jsonl`, `cdrig/hooklog-m4.jsonl`, `cdrig/hooklog-m5.jsonl`, `cdrig/hooklog-m6.jsonl`, `cdrig/hooklog-m11.jsonl` |
| Unplatzierbarer Modell-Pin tötet den Spawn (kein stiller Rückfall) | gemessen | `model1.log`, `model2.log` |
| BOM-Stolperdraht + Gegenrichtung in `tools/test_repo_hygiene.py` | gebaut, grün | — |
| `tools/test_model_pins.py`, vier Prüfungen | gebaut, grün | — |

Nachgeprüft und **korrigiert** — drei Stellen, alle unten mit Messung:

1. Befund 14 des `/cd`-Dokuments war **konfundiert** (Abschnitt 2.1).
2. Befund 15 („gilt auch in der VS-Code-Erweiterung: ja") war **falsch in der Richtung, auf die es
   ankommt** (Abschnitt 2.2).
3. Zwei Verweise zeigten ins Leere: der Rohdatenpfad der Hook-Protokolle und eine Datei
   `hooklog-m13.jsonl`, die es nie gab (Abschnitt 2.5).

---

## 2. Dieser Lauf

### 2.1 Befund 14 war konfundiert — nachgemessen

Der erste Lauf schloss aus `m6`, die `agent:`-Zeile werde mitten in der Sitzung nicht nachgelesen:
`dirA`s `settings.json` wurde gegen eine mit `agent: agent-b` getauscht, die Antwort blieb
`AGENT-A`. **`agent-b.md` lag zu keinem Zeitpunkt in `dirA`** (nachgesehen: das Verzeichnis enthält
`agent-a.md` und `prober-b.md`) — „nicht nachgelesen" und „löst hier gar nicht auf" waren dieselbe
Beobachtung.

Nachgemessen mit `driver_rebind.py`, das die Rollendatei **vor** dem Tausch hineinkopiert
(`reb1.log`, `reb1.jsonl`):

```
{"tag": "A2", … "command": "echo REPORT-BINDING token=AGENT-A", "payload_cwd": "…\cdrig\dirA"}
     ── Tausch settings.json → A3 (agent: agent-b), agent-b.md liegt in dirA ──
{"tag": "A3", … "command": "echo REPORT-BINDING token=AGENT-A", "payload_cwd": "…\cdrig\dirA"}
```

Der Tag springt (Registrierung nachgelesen), die Rolle existiert, die Bindung bleibt. **Der Befund
trägt jetzt.** Nebeneffekt: `H116` ist damit ein zweites Mal belegt, diesmal headless.

### 2.2 Die VS-Code-Antwort war falsch — der Transport ist ein anderer

Der erste Lauf fuhr das Binary der Erweiterung durch eine ConPTY und schloss „dasselbe Programm,
dasselbe Verhalten". Gemessen wurde damit ein Transport, den das Panel **nicht** benutzt.

Aus dem Einstiegspunkt der Erweiterung selbst (`extension.js`, die Datei, die ihre `package.json`
als `main` nennt) gelesen: sie sucht `resources/native-binary/claude.exe` und startet es mit

```
["--output-format","stream-json","--verbose","--input-format","stream-json"]     (SDK-Basisliste)
{debug:null,"debug-to-stderr":null,"enable-auth-status":null,"no-chrome":null,
 "replay-user-messages":null}                                    (extraArgs der Erweiterung)
wQ($):  return Q.CLAUDE_CODE_ENTRYPOINT="claude-vscode", delete Q.CLAUDECODE, …   (unbedingt)
```

Mit genau diesem Binary und genau dieser Argumentliste gefahren (`ext1.log`, `driver_ext.py`):

```
Runde 2  /cd …\cdrig\dirB          → "/cd isn't available in this environment."
Runde 3  Bash echo ext-turn-three  → init cwd = …\cdrig\dirA   (nicht bewegt)
```

und `cd` fehlt in der `slash_commands`-Liste des `init`-Ereignisses.

**Der Wechsel existiert dort trotzdem, unter anderem Namen.** `extension.js` trägt
`setCwd(pfad,{trustAccepted,trustedDirectory})` → `{subtype:"set_cwd",…}` in der Hülle
`{request_id,type:"control_request",request:{…}}`; die Zeichenkette `/cd` steht 14 mal im Bündel,
alle 14 in einer MIME-Typ-Tabelle — als Kommandoname kommt sie nicht vor (`count_cd.py`). Diese Hülle gesendet (`ext3.log`, `ext3.jsonl`, `driver_setcwd2.py`):

```
control_response: {"status":"ok","cwd":"…\cdrig\dirB","changed":true,"transcript_relocated":true}
{"tag":"REG-B","script_home":"SCRIPT-A","script_path":"…\dirA\.claude\hooks\log_hook.py",
 "payload_cwd":"…\cdrig\dirB","env_CLAUDE_PROJECT_DIR":"…/cdrig/dirA",
 "command":"echo REPORT-BINDING token=AGENT-A"}
```

Eine Zeile, drei Reproduktionen: `H114` (Registrierung Ziel, Datei Start), Befund 4
(`CLAUDE_PROJECT_DIR` bleibt), `H115` (Bindung bleibt) — **und ohne jeden Dialog**, weil `dirB`
früher einmal bestätigt worden war. Dass es für ein unbekanntes Ziel einen zweistufigen Handschlag
gibt, sagt die Fehlermeldung des ersten Versuchs (`ext2.log`): `set_cwd: invalid request —
trust_accepted requires trusted_directory (echo the directory from the needs_trust response)`.

Deshalb ist `H114`s Satz „begrenzt durch den Trust-Dialog" korrigiert worden: er beschreibt die
Hälfte der Fläche.

### 2.3 Punkt 7 des Messplans — Fortsetzen bindet

Der Plan verlangte, nach einem nicht bindenden `agent:` eine Fortsetzung zu fahren. Ausgangslage aus
2.1 (`dirA`: `agent: agent-b`, `agent-b.md` da, laufende Sitzung antwortet `AGENT-A`); dieselbe
Sitzung mit `--continue` (`reb2-resume.log`, `reb2-resume.jsonl`):

```
{"tag": "A3", … "command": "echo REPORT-BINDING token=AGENT-B", …}
```

Dass es eine Fortsetzung war: die `session_id` der Vorsitzung
(`6a9d6106-1cda-4145-95fc-8af3459b3301`) steht im Strom der neuen.

**Folge:** Die Zeremonie der Kits behält ihre Bitte um einen Neustart zu Recht — aber „Fenster
schließen und neu öffnen" ist nicht ihre einzige Erfüllung. Wortlaut ändern ist **Naht** (4.).

### 2.4 Die drei Antworten auf die Nutzerfrage

Die Frage war: „Geht das auch über die VS Code Extension, Claude Desktop oder nur im CLI?"

| Fläche | Antwort | Messung |
|---|---|---|
| CLI (Terminal, interaktiv) | **ja** — die Zeile ist `/cd <absoluter Pfad>`, mit Trust-Dialog beim ersten Mal | `m2a.log`, `cdrig/hooklog-m2b.jsonl` |
| VS-Code-Erweiterung | **nein** für `/cd` — es gibt das Kommando in ihrem Transport nicht; der Wechsel selbst gibt es als `set_cwd`, ohne Zeile zum Tippen | `ext1.log`, `ext3.log` |
| Claude-Desktop-App | **ungemessen, weil nicht installiert** — weder `%LOCALAPPDATA%\AnthropicClaude` noch `%APPDATA%\Claude` noch `%LOCALAPPDATA%\Programs\Claude` existieren auf diesem Host (2026-09-02) | — |

Was in der VS-Code-Zeile **nicht** gemessen ist: die Chat-Eingabe des Panels (ein Webview, nicht
skriptbar) — also ob die Erweiterung ein eigenes, clientseitiges `/cd` anbietet. Als Kommandoname
steht es im Bündel nicht. Das Prüfprotokoll für den Nutzer (20 Sekunden) steht im Messdokument.

### 2.5 Zwei Verweise, die ins Leere zeigten

* Das `/cd`-Dokument nannte alle Rohdaten unter dem Wurzelpfad des Scratch-Verzeichnisses; die
  Hook-Protokolle liegen aber in `cdrig\`, weil das Rig-Skript neben sich selbst schreibt.
* Das Modell-/BOM-Dokument belegte den BOM-Spawn mit `hooklog-m13.jsonl`. Diese Datei gibt es
  nicht: das Rig schreibt in **eine** Logdatei, die der Treiber erst nach dem Lauf umbenennt, und
  dieser Lauf wurde nicht umbenannt. Der Beleg steht in `ext1-before.jsonl`
  (`{"tag":"A2","t":"12:28:22", … "command":"echo PROBER-B-RAN"}`) und in `m13.log`; die präparierte
  Datei liegt noch da (`cdrig/dirA/.claude/agents/prober-b.md` beginnt mit `ef bb bf`, das
  Gegenstück in `dirB` mit `2d 2d 2d`, beides am 2026-09-02 nachgelesen).

---

## 3. Rot-zuerst — alle Läufe selbst gesehen

Klon außerhalb des Repos: `…\_round-scratch\TSK-0108\redclone`. Treiber `redfirst.py` und
`redfirst_count.py`; jeder Fall setzt zurück, Ausgangs- und Endstand grün.

```
baseline: (0, '6 passed in 6.55s')

=== R1 BOM vor eine Kit-Rollendatei -> rc=1
FAILED tools/test_repo_hygiene.py::test_no_file_a_parser_reads_from_byte_zero_starts_with_a_bom
=== R2 BOM vor .claude/settings.json -> rc=1
FAILED tools/test_repo_hygiene.py::test_no_file_a_parser_reads_from_byte_zero_starts_with_a_bom
=== R3 einem Skill den Frontmatter-Trenner nehmen -> rc=1
FAILED tools/test_repo_hygiene.py::test_every_shipped_role_and_skill_definition_is_a_file_that_check_looks_at
   (1 failed, 1 passed — die BOM-Prüfung bleibt grün: genau der stille Fall)
=== R4 model: opus-4-1-does-not-exist auf einer eigenen Rolle -> rc=1
FAILED tools/test_model_pins.py::test_every_model_a_shipped_role_pins_resolves_in_the_tiers_table
=== R5 den Pin-Leser auf team-kits/ verengen (Zustand vor dieser Runde) -> rc=1
FAILED tools/test_model_pins.py::test_the_pin_reader_covers_every_agents_directory_the_repo_tracks
FAILED tools/test_model_pins.py::test_a_tier_nobody_pins_is_not_an_error
=== R6 den Resolver alles annehmen lassen -> rc=1
FAILED tools/test_model_pins.py::test_the_reader_refuses_what_the_table_cannot_place_and_demands_no_tier_be_pinned

restored: (0, '4 passed in 0.86s')
```

```
=== baseline -> rc=0   4 passed
=== der Frontmatter-Leser trifft nichts (^model: → ^modell:) -> rc=1
FAILED tools/test_model_pins.py::test_the_pin_reader_covers_every_agents_directory_the_repo_tracks
=== restored -> rc=0   4 passed
```

**Beide Enden des BOM-Drahtes sind damit rot gesehen:** R1/R2 das Ende „ein BOM steht da", R3 das
Ende „eine Definition fällt still aus der geprüften Menge heraus". Der Fall, den der Draht meint,
ist benannt und nicht erfunden: `.claude/hooks/_harness.py` öffnet `.claude/settings.json` mit
`json.load` und `encoding="utf-8"` — ein BOM lässt diesen Aufruf scheitern. Was der Gate-**Prozess**
daraus macht, ist nicht gemessen (ein Gate lässt sich aus einer Sitzung heraus nicht starten,
`H80`), und genau so steht es im Docstring.

**Was die Korrekturen dieses Laufs betrifft:** sie liegen sämtlich in Prosa (`docs/`), nicht im
Code. Ein Prosa-Fehler hat keinen roten Test — was ihn fängt, sind die vier Prüfungen der
Löcherliste in `.claude/hooks/test_gates.py` (Tabellenzeile ↔ Urteil, Verweis ↔ Dokument), und die
laufen; sie hätten die drei Korrekturen aber **nicht** gefunden, weil keine von ihnen eine
Struktur verletzte. Das ist die Grenze, und sie steht hier statt als Schutzbehauptung im Dokument.

---

## 4. Nahtstellen — wörtlich, nicht geschrieben

Alle vier liegen außerhalb `tools/**` und `docs/**` und sind in diesem Strom **nicht** angefasst
worden.

1. **`model_tiers.yaml` bzw. ein Kit-Hook für den protokollierten Pin-Fehler (`FR-0047`).** Sichtbar
   ist ein unplatzierbarer Pin heute nur im Gespräch: der Elternteil liest den API-Fehler im
   Werkzeugergebnis, und es bleibt nichts zurück. Zwei Hälften: (a) **vorher** — ein `PreToolUse`-
   Wächter auf `Agent|Task`, der die Frontmatter der gespawnten Rolle liest, wie
   `gate_spawn_needs_item.py` es für `harness_item` bereits tut, und einen Wert verweigert, den
   `model_tiers.yaml` nicht platzieren kann; der Leser dafür liegt fertig als
   `the_table_can_place` in `tools/test_model_pins.py` und ist eine Ableitung aus der Tabelle, keine
   Namensliste. (b) **nachher** — ein `SubagentStop`/`PostToolUse`-Hook der Kits, der den Fehlertext
   einsammelt. Eigentümer: der Hook-Eigentümer von dev/office.
2. **`README.md`, Quickstart-Abschnitt: die Claude-Code-Untergrenze für BOM.** Die Installer prüfen
   eine Client-Version nur für Codex (`install.sh`/`install.ps1`, Grenze 0.131.0); für Claude Code
   prüft nichts. Ob aus der Notiz „< 2.1.239 überspringt eine `.md` mit BOM" eine Prüfung werden
   soll, ist eine Entscheidung, kein Schreibauftrag.
3. **Der Satz in `CLAUDE.md` dieses Repos: „Was beim Sitzungsstart bindet, ist die Registrierung".**
   Gemessen gilt er nicht mehr (`H116`, jetzt zweimal belegt: interaktiv und headless). Die Datei
   liegt außerhalb dieses Streams.
4. **Der Wortlaut der Neustart-Zeremonie** in `~/.claude/CLAUDE.md` und in den Kit-Verfassungen.
   Gemessen (2.3) erfüllt **auch ein Fortsetzen** derselben Unterhaltung die Bitte, nicht nur ein
   kalter Start. Heute sagt die Zeremonie nur „Fenster schließen/öffnen oder neue Session". Ob sie
   das aufnehmen soll — und ob sie es überhaupt soll, weil „neu starten" die einfachere Anweisung
   für einen nicht-technischen Nutzer ist —, ist eine Entscheidung des Leads, kein Textfehler.

Eine fünfte Sache ist **keine** Naht, sondern eine offene Messung: `H114`s Fix bräuchte eine
Schreibweise der Hook-Kommandozeile, die dem Wechsel folgt. Der Hook-Prozess läuft nach dem Wechsel
mit dem Arbeitsverzeichnis des Ziels (gemessen: `process_cwd` = `dirB`), ein relativer Pfad würde
also mitwandern — mit dem bekannten Preis, dass eine Sitzung auch in einem Unterverzeichnis stehen
kann. Das ist Kit-Bereich und steht im Eintrag, nicht hier als Auftrag.

---

## 5. Läufe dieses Laufs

| Lauf | Ergebnis |
|---|---|
| `python -m ruff check .` | All checks passed |
| `pytest tools/test_model_pins.py tools/test_repo_hygiene.py -q` | 15 passed (15 s) |
| `pytest tools/test_hooks.py -k "model or tier or bom" -q` | 11 passed, 902 deselected (95 s) |
| `pytest .claude/hooks/test_gates.py -k "hole or measurement or reference" -q` | 8 passed, 481 deselected (136 s), **nach** den Änderungen an der Löcherliste |
| `redfirst.py`, `redfirst_count.py` | 7 Mutationen, alle rot, Ausgangs- und Endstand grün |

**Volle Suite: absichtlich nicht gefahren** (`DEC-0050`). Berührt sind `tools/test_model_pins.py`,
`tools/test_repo_hygiene.py` und drei Dokumente; die betroffenen Suiten sind oben gelaufen. Die
volle Suite ist Lieferkriterium der letzten Nacharbeit, nicht dieser Runde.

**Kein Versionsstempel.** `git status` nennt keine Datei unter `team-kits/`; `tools/bump_kit_version.py`
hat in diesem Paket nichts zu stempeln.

---

## 6. Was ungemessen bleibt, und warum

* **Die Chat-Eingabe der VS-Code-Erweiterung.** Webview, nicht skriptbar. Gemessen ist das Programm
  dahinter, seine Argumentliste und sein Antwortverhalten.
* **Die Claude-Desktop-App.** Auf diesem Host nicht installiert; sie ist ein anderes Programm als
  Claude Code. Diese Runde behauptet über sie nichts.
* **Wodurch die Erweiterung `setCwd` auslöst.** Dass sie es kann und das Binary es ausführt, ist
  gemessen; was im Panel davorsteht, nicht.
* **Ob ein Hook oder ein MCP-Server `set_cwd` schicken kann.** Der Kanal ist stdin des
  Client-Prozesses. Damit bleibt der Punkt „programmatische Trigger jenseits des Modells" aus der
  Recherche offen.
* **Ob ein BOM auf `.claude/settings.json` ein Gate zum Verweigern oder zum Durchlassen bringt.**
  Ein Gate lässt sich aus einer Sitzung heraus nicht starten (`H80`).
* **Verhalten unterhalb 2.1.239 (BOM) bzw. 2.1.246 (`/cd`).** Für beide gibt es auf diesem Host
  keinen Client.
* **`--fallback-model` und die Sicherheits-Umleitung der Plattform.** Eigene Messungen, nicht in
  diesem Auftrag.
* **Die `effort:`-Werte.** Ihr Vokabular steht in `model_tiers.yaml` nur in einem Kommentar und wird
  von keinem Leser ausgewertet; bewusst nicht mitgeprüft.
* **Eine Fortsetzung einer `dirA`-Sitzung aus `dirB` heraus.** `--continue` sucht die letzte Sitzung
  des aktuellen Verzeichnisses und erreicht die andere gar nicht.

---

## 7. Nacharbeit 1 (Prüfbericht Opus, 10 Befunde)

Der Prüfer hat die Substanz bestätigt (`reb1` und `ext1` unabhängig reproduziert, 11 Mutationen rot)
und zehn Befunde erhoben. Alle zehn sind hier abgearbeitet; jeder **neu geschriebene
Eigenschaftssatz** steht unten mit der Messung, die ihn trägt.

### 7.1 Code (B2, B3) — zwei Prädikate, beide zu eng bzw. zu weit

**B3 — der Rollen-Leser sah nur die erste Ebene.** `under_an_agents_directory` in
`tools/test_model_pins.py` fragt jetzt `"agents" in dirname.split("/")` statt nach dem
Elternverzeichnis, und der Deckungstest benutzt **dieselbe** Funktion, damit nicht wieder ein Ende
enger sein kann als das andere.

> *Neuer Eigenschaftssatz:* „Ein Client lädt eine Rolle aus **jeder Tiefe** unterhalb eines
> `agents`-Verzeichnisses."
> *Messung (selbst gefahren, nicht übernommen):* `.claude/agents/nested/agent-z.md` ins Rig gelegt,
> per Task-Werkzeug mit `subagent_type: agent-z` gestartet — der Subagent lief
> (`nested1.log`; Hook-Zeile `{"tag":"A3","t":"14:58:51", … "echo NESTED-Z-RAN"}` in
> `ext4-fullargs-before.jsonl`), und `agent-z` steht in der Antwort des Clients auf „list the agent
> types available to you" (`readme1.log`). CLI 2.1.258.

> **Überholt durch Nacharbeit 2 (Abschnitt 8):** die hier beschriebene Subtraktion
> `opens_as_prose` gibt es nicht mehr. Sie hat auf dem verfolgten Baum nichts entfernt und kannte
> eine von vier Schreibweisen. Der Absatz bleibt als Aufzeichnung dessen stehen, was Nacharbeit 1
> getan hat.

**B2 — der Gegentest verlangte Frontmatter von Dateien, die kein Client lädt.**
`is_a_definition_a_client_loads` in `tools/test_repo_hygiene.py` hat jetzt eine Klausel pro Lader
plus eine gemessene Subtraktion: Rolle = `.md` unterhalb `agents/` (jede Tiefe), Skill = Datei
**namens** `SKILL.md`, und nichts davon, wenn die Datei als Prosa öffnet (`opens_as_prose`, erste
Zeile eine Markdown-Überschrift). Der Test verlangt zusätzlich, dass **beide** Lader vertreten
sind — eine Fassung, die eine Hälfte still verliert, käme sonst über die Zählung durch.

> *Neuer Eigenschaftssatz:* „Eine `README.md` ohne Frontmatter in einem `agents`-Verzeichnis wird
> vom Client still ignoriert, ist also keine Definition."
> *Messung:* `README.md`, beginnend mit `# Notes about the roles in this directory`, in
> `cdrig/dirA/.claude/agents/` gelegt und den Client nach seinen Agententypen gefragt — die Antwort
> nennt zehn Namen, `agent-a, agent-b, agent-z, claude, claude-code-guide, Explore, general-purpose,
> Plan, prober-b, statusline-setup`, ohne README und ohne jede Meldung (`readme1.log`).
> (Die Zeichenkette `# The roles here` steht nicht im Rig, sondern in der Testfixtur von
> `redfirst2.py`; die erste Fassung dieses Absatzes hat die beiden verwechselt.)

Gemessener Bestand danach: **1050** verfolgte Dateien, davon **61** Definitionen = **32** Rollen +
**29** `SKILL.md` + 0 sonstige. Die beiden Fehlalarme des Prüfers sind grün, die Schärfe bleibt.

**Rot-zuerst, alle selbst gesehen** (Klon `redclone`, Treiber `redfirst2.py`; jede Zeile ist ein Lauf
mit dem NEUEN und einer mit dem ALTEN Prädikat):

```
baseline hygiene: rc=0 1 passed          baseline pins: rc=0 4 passed

B2-a  ein Referenz-Dokument neben SKILL.md (Strom K's Form)   NEU rc=0 passed | ALT rc=1 failed
B2-b  eine README.md neben den Rollen                         NEU rc=0 passed | ALT rc=1 failed
B2-c  eine Rolle OHNE Trenner                                 NEU rc=1 failed | ALT rc=1 failed
B2-d  eine SKILL.md OHNE Trenner                              NEU rc=1 failed | ALT rc=1 failed
B3    eine GESCHACHTELTE Rolle mit totem Pin                  NEU rc=1 failed | ALT rc=0 passed
B2-e  die SKILL-Hälfte des Prädikats trifft nichts            rc=1 failed  (Ausgang grün)

restored hygiene: rc=0 1 passed          restored pins: rc=0 4 passed
```

B2-c und B2-d sind die Gegenprobe zur Entschärfung: der Draht bleibt an beiden Enden scharf.

### 7.2 Text (B1, B4, M1–M3, N1, N2)

* **B1** — `H114`s Begrenzung behauptete den Trust-Dialog vor jedem `/cd`. Gemessen gilt er nur vor
  dem **ersten** Wechsel in ein Verzeichnis: das Steuerskript `pty-m4.txt` sendet zwischen dem `/cd`
  nach `dirB` und der nächsten Eingabe **keinen** Tastendruck, und der Lauf `m4.log` geht durch.
  Auf dem `set_cwd`-Weg ist es dasselbe. Tabellenzeile und Rumpf sagen das jetzt, mit dem Zusatz,
  dass **zwei** Fassungen dieses Absatzes den Dialog stärker gemacht haben, als er ist.
* **B4** — meine eigene Pfadkorrektur war falsch: die `ext*`/`reb*`-Hook-Protokolle liegen in der
  Wurzel des Scratch-Verzeichnisses, nicht in `cdrig/`, und `cdrig/hooklog.jsonl` existiert zwischen
  zwei Läufen gar nicht — die BOM-Spawn-Zeile steht in `ext1-before.jsonl`, weil der nächste
  Treiberstart die gemeinsame Logdatei beiseiteräumt. Der Rohdaten-Absatz nennt jetzt eine Tabelle
  statt einer Regel, und **jeder** Verweis nennt seinen Pfad relativ zum Scratch-Verzeichnis.
  Geprüft wird das nicht mehr von Hand: `check_refs.py` liest die Backtick-Spannen der vier
  Dokumente, nimmt die `.log`/`.jsonl`-Belege heraus und schlägt sie auf der Platte nach; übersprungen
  wird nur, was der Satz drumherum ausdrücklich als nicht existent bezeichnet. **Stand nach
  Nacharbeit 1: 58 Spannen geprüft, 0 fehlend** — die 53 im ersten Entwurf dieses Satzes waren der
  Lauf VOR dem letzten Abschnitt.
* **M1** — „extension.js setzt `sdk-ts`" war falsch gelesen. Beide `sdk-ts`-Zuweisungen (Offsets
  2229002, 2758314) stehen hinter `if(!U.CLAUDE_CODE_ENTRYPOINT)`; der Umgebungsbauer `wQ($)`
  (Offset 3080381) endet mit `return Q.CLAUDE_CODE_ENTRYPOINT="claude-vscode", …` — unbedingt. Die
  fünf Argumente sind die Basisliste des gebündelten SDK, dazu kommen die `extraArgs` der
  Erweiterung (Offset 3052386). **Ergebnis unverändert, selbst nachgefahren:** mit
  `CLAUDE_CODE_ENTRYPOINT=claude-vscode` und allen fünf Zusatzflags antwortet `/cd` weiter mit
  „isn't available in this environment", und die Sitzung bleibt in `dirA` (`ext4-fullargs.log`).
* **M2** — die Erweiterung trägt `claude-vscode.terminal.open` („Claude Code: Open in Terminal") in
  ihrer `package.json` bei; das ist der Weg vom Panel zum CLI, wo die `/cd`-Zeile gilt. **Gelesen,
  nicht durchgefahren** — so steht es auch im Dokument.
* **M3** — der empfohlene Rundlauf führt über `C:\Offline Repos\v2-testbed`, und das trägt kein
  `.claude/`. Nach Befund 3 ist zwischen den beiden Zeilen **kein** Gate dieses Repos registriert;
  das steht jetzt als dritte Einschränkung dort, mit dem Hinweis auf ein Zwischenziel, das selbst
  eine Registrierung hat.
* **N1** — 1046 → **1050** verfolgte Dateien (die vier neuen Dateien dieser Runde), nachgezählt.
* **N2** — „die interaktiven Läufe zeigen alle das 2.1.258-Banner" gestrichen: `pty-smoke.log` zeigt
  2.1.251. Der Absatz nennt jetzt den Rauchtest getrennt und die drei nachgesehenen Läufe beim Namen.
* **N3** ist Item-Sache und gehört dem Lead.

### 7.3 Läufe der Nacharbeit

| Lauf | Ergebnis |
|---|---|
| `python -m ruff check .` | All checks passed |
| `pytest tools/test_model_pins.py tools/test_repo_hygiene.py -q` | 15 passed |
| `pytest tools/test_hooks.py -k "model or tier or bom" -q` | 11 passed, 902 deselected |
| `pytest .claude/hooks/test_gates.py -k "hole or measurement or reference" -q` | 8 passed, 481 deselected |
| `redfirst2.py` + die SKILL-Hälfte | 6 Mutationen, Ausgang und Ende grün |
| `check_refs.py` | 53 Belegpfade, 0 fehlend — **abgelöst**: der Lauf am Ende der Nacharbeit 1 zählte 58 (Abschnitt 7.2) |

### 7.4 Was die Nacharbeit NICHT geschlossen hat

* Ob das Terminal, das `claude-vscode.terminal.open` öffnet, wirklich den CLI mit `/cd` bringt —
  gelesen im Manifest, nicht durchgefahren.
* Der zweistufige Vertrauens-Handschlag von `set_cwd` an einem wirklich unbekannten Verzeichnis
  (unverändert offen aus Abschnitt 6).
* Ob eine Definition, die als Prosa öffnet UND wirklich eine Rolle sein sollte, durch
  `opens_as_prose` fällt. Das ist die bewusst gewählte Kante: eine Rolle, die ihren Trenner
  verliert, beginnt mit ihrem ersten Frontmatter-Schlüssel und nicht mit `#` — gemessen in B2-c,
  wo genau diese Datei rot wird.

---

## 8. Nacharbeit 2 (zweiter Prüfbericht Opus: B=3, M=2, N=7)

### 8.0 Vorgefunden: der Index dieses Worktrees war verändert

Die Kopie des Prüfers trug die `.git`-DATEI des Worktrees mit, sein `git add -A` lief deshalb gegen
`.git/worktrees/g2-measure/index`; er hat den Index danach aus `git ls-files` rekonstruiert.
Selbst nachgemessen, bevor irgendetwas geändert wurde:

```
git rev-parse HEAD       6d18407129d7a80c729c792c8eedc1884d2c7fb2   (unverändert)
git diff HEAD --stat     6 files changed, 1479 insertions(+)        (identisch zur Übergabe)
cat .git                 gitdir: C:/Offline Repos/AgentAndSkills/.git/worktrees/g2-measure
git status --porcelain   M / A   statt   MM / AM
```

Also: **Dateiinhalte und Diff unversehrt**, nur die Staging-Spalten stehen anders. Vor dem neuen
Patch läuft wieder `git add -N` für jede neue Datei, damit der Patch sie trägt.

### 8.1 Der Client-Schlüssel, selbst gemessen (Grundlage für B1 und B2)

Fünf Dateien unter `agents/` gelegt, eine je Eröffnungsform, und den Client sein `init`-Ereignis
sprechen lassen (`plant_shapes.py`, Mitschrift `shapes1.log`, CLI 2.1.258):

| Datei | erste Zeile | in `init.agents` |
|---|---|---|
| `p-ok.md` | der Trenner | **ja** |
| `p-atx.md` | eine ATX-Überschrift, darunter gültige Frontmatter | nein |
| `p-setext.md` | eine Setext-Überschrift, darunter gültige Frontmatter | nein |
| `p-prose.md` | Prosa, keine Frontmatter | nein |
| `p-html.md` | ein HTML-Kommentar, darunter gültige Frontmatter | nein |

> *Eigenschaftssatz, gebunden an diese fünf Formen und diese Client-Version:* von den fünf Formen
> lädt der Client genau die, deren **erste Zeile der Frontmatter-Trenner** ist.

Damit fallen beide Prüferbefunde zusammen: `opens_as_prose` kannte **eine** von vier Formen, die der
Client verwirft (B2) — und der Client-Schlüssel darf trotzdem nicht der Gegenstand werden, weil die
Datei, für die die Prüfung existiert, genau die ist, die ihre erste Zeile verloren hat.

### 8.2 B1 — die Klausel entschied nichts

Reproduziert (`redfirst3.py`, Zeile INERT): mit der Klausel aus Nacharbeit 1 im Klon läuft der Test
grün, und mit derselben Klausel auf `return False` **auch**. Der Zensus über die 1050 verfolgten
Dateien zeigt warum: sie subtrahiert keine einzige. Ersatzlos entfernt.

### 8.3 B2/N5/N6/N7 — ein Ort, ein Name, eine Funktion

`is_a_definition_a_client_loads(relative)` trägt jetzt zwei Klauseln und keine Subtraktion: Rolle =
`.md` unterhalb eines `agents`-Verzeichnisses (`under_an_agents_directory`), Skill = Datei **namens**
`SKILL.md`. Die Rollen-Hälfte wird aus `tools/test_model_pins.py` **importiert**, nicht kopiert.
Gemessen:

```
H.under_an_agents_directory is P.under_an_agents_directory   True
P.under_an_agents_directory.__module__                       test_model_pins
hasattr(H, "opens_as_prose")                                 False
1050 verfolgt -> 61 Definitionen = 32 (agents) + 29 (SKILL.md)
```

Die Docstrings behaupten nichts Universelles mehr. Statt „a client reads a role … at any depth" und
„a human always writes" steht dort, was gemessen ist, und daneben die **Reibung**: der Gegenstand ist
breiter als der Client — `docs/agents/notes.md` fällt hinein und wird von keinem Client gelesen
(`verify2/cases3.py`). Die Abhilfe für so eine Datei ist, sie zu verschieben, nicht die Prüfung zu
verbreitern.

### 8.4 Rot-zuerst, vollständig neu (`redfirst3.py`)

NEU = dieser Stand, ALT = Nacharbeit 1 (im Klon rekonstruiert), NARROW = die geteilte Funktion auf
Ebene 1 verengt.

```
baseline hygiene rc=0 1 passed      baseline pins rc=0 4 passed

INERT    rework-1-Code                             rc=0 passed
INERT    ...mit der Klausel auf False              rc=0 passed      -> sie entschied nichts

CATCH    Rolle ohne Trenner                        NEU rc=1 | ALT rc=1
CATCH    SKILL.md ohne Trenner                     NEU rc=1 | ALT rc=1
KEPT     Referenzdatei neben SKILL.md (Strom K)    NEU rc=0 | ALT rc=0
SHARED   GESCHACHTELTE Rolle ohne Trenner          NEU rc=1 | ALT rc=1 | NARROW rc=0
SHARED   GESCHACHTELTE Rolle mit totem Pin         NEU rc=1 | ALT rc=1 | NARROW rc=0
FRICTION Datei unter agents/ mit Überschrift      NEU rc=1 | ALT rc=0

both-loaders-Draht: SKILL-Hälfte trifft nichts    rc=1 failed
restored hygiene rc=0 1 passed      restored pins rc=0 4 passed
```

Zwei Zeilen sind die Kernaussage. **SHARED** zeigt, dass der Gegenstand der Hygiene-Prüfung
wirklich aus der importierten Funktion kommt: verengt man sie in `test_model_pins`, wird die
gepflanzte geschachtelte Datei in **beiden** Modulen grün. **FRICTION** ist die Reibung aus 8.3,
offen ausgewiesen und kein gefangener Fehler — darum steht sie hier und nicht als Erfolg.

### 8.5 Text (B3, M1, M2, N1–N4)

* **B3** — das Messdokument beschrieb noch das Prädikat von vor der Nacharbeit. Es nennt jetzt die
  zwei Lader-Schlüssel, den Testnamen und ausdrücklich, dass eine `.md` unter `skills/`, die nicht
  `SKILL.md` heißt, **nicht** Gegenstand ist.
* **M1** — „`/cd` kommt im Bündel null mal vor" war falsch. Nachgezählt (`count_cd.py`): **14**
  Vorkommen, alle in einer MIME-Typ-Tabelle; als Kommandoname kommt die Zeichenkette nicht vor. An
  allen fünf Stellen korrigiert, und der Befund stützt sich ausdrücklich auf die
  `slash_commands`-Liste und den Versuch, nicht auf die Abwesenheit einer Zeichenkette.
* **M2** — die Tabellenzeile zu `H114` sagte „auf beiden Wegen gemessen". Sie trennt jetzt: `/cd`
  mit Erst-Dialog (`m2a.log`) und dialogfreier Wiederholung (`m4.log`), `set_cwd` nur für den
  dialogfreien Wechsel an ein bereits vertrautes Ziel, unbekanntes Ziel **nicht gemessen**. Weil das
  die dritte Fassung desselben Satzes war, prüft ihn ab jetzt ein Skript: `check_limits.py` liest
  die drei Stellen (Tabellenzeile, Eintragsrumpf, Messdokument §2), zieht aus jeder dieselben fünf
  Aussagen und meldet Abweichungen. **Stand: 0 Probleme.** Was es NICHT prüft, steht in seinem
  Kopfkommentar: ob die Aussagen wahr sind — dafür sind die Logs da.
* **N1** — „Zwei Einschränkungen" wurde **drei** (die dritte kam in Nacharbeit 1 dazu).
* **N2** — 53 wurde **58** Spannen.
* **N3** — die Rig-Datei beginnt mit `# Notes about the roles in this directory`; die Client-Antwort
  trägt zehn Namen, jetzt vollständig zitiert.
* **N4** — die drei Offsets sind **Zeichen**-Offsets in der als UTF-8 gelesenen Datei (3 181 619
  Zeichen gegenüber 3 200 852 Bytes), und der zweite Wächter liest `e0`, nicht `U`.

### 8.6 Läufe der Nacharbeit 2

| Lauf | Ergebnis |
|---|---|
| `python -m ruff check .` | All checks passed |
| `pytest tools/test_model_pins.py tools/test_repo_hygiene.py -q` | 15 passed (19 s) |
| `pytest tools/test_hooks.py -k "model or tier or bom" -q` | 11 passed, 902 deselected (141 s) |
| `pytest .claude/hooks/test_gates.py -k "hole or measurement or reference" -q` | 8 passed, 481 deselected (296 s) |
| `redfirst3.py` | 8 Zeilen, Ausgang und Ende grün |
| `check_refs.py` | 58 Belegspannen, 0 fehlend |
| `check_limits.py` | 3 Stellen, 5 Aussagen, 0 Probleme |
| `unbackticked_run.py` (der Leser des Prüfers, auf den Arbeitsbaum gerichtet) | 5 Treffer, alle `log_hook.py` |

Zu den fünf Treffern des letzten Laufs: es sind **zitierte** Kommandozeilen und Logzeilen, keine
Belegverweise — der Name steht dort, weil das Rig ihn schreibt. Damit ein Leser die Datei trotzdem
findet, nennt die Rohdaten-Tabelle des Messdokuments jetzt ihre drei Kopien (`cdrig/log_hook.py`
und die zwei installierten unter `cdrig/dirA/` bzw. `cdrig/dirB/`). Alle anderen unbebacktickten
Namen lösen auf.

### 8.7 Was Nacharbeit 2 NICHT geschlossen hat

* Die **Reibung** aus 8.3: eine `.md` unter `agents/`, die kein Client lädt, wird trotzdem nach
  einem Trenner gefragt. Bewusst so, mit der Messung daneben; die Alternative wäre ein
  tautologischer Gegentest.
* Ob an einem wirklich unbekannten Ziel ein `set_cwd`-Dialog erscheint (unverändert offen).
* Ob das Terminal aus `claude-vscode.terminal.open` den CLI mit `/cd` bringt — Manifest gelesen,
  nicht durchgefahren.

---

## 9. Nacharbeit 3 (Nachprüfung 2: B=1, M=1, N=4)

### 9.1 B1 — der benannte Test konnte nicht scheitern

Der Rumpf von `H114` sagte weiter „auf beiden Wegen dasselbe" und nannte das unbekannte Ziel
nirgends, während `check_limits.py` trotzdem 0 Probleme meldete. Der Prüfer hat gezeigt, woran das
lag: die Zelle „unknown target marked unmeasured" fragte nur, ob die Wörter *nicht gemessen*
irgendwo in der Spanne stehen — und ein **unverwandter** Satz („wann die Erweiterung ihn schickt,
ist nicht gemessen") trug sie. Das ist der teurere Befund von `SR-0008`: ein Draht, der nicht
scheitern kann, behauptet Deckung.

Zwei Änderungen. Der Rumpf trennt die Wege jetzt genauso wie Tabellenzeile und §2: `/cd` mit
Erst-Dialog und dialogfreier Wiederholung, `set_cwd` nur für das bereits vertraute Ziel, unbekanntes
Ziel **NICHT gemessen**. Und `check_limits.py` bindet die Zelle an das **Ziel** statt an das Wort
(`unbekannt\w*\s+\**Ziel\**[^.]{0,160}?(NICHT gemessen|…)`) und bekommt eine zweite Zelle für die
Aussage, die dreimal falsch war: eine Spanne, die eine Begrenzung für **beide Wege auf einmal**
behauptet, ist ein Problem.

**Rot-zuerst (`redfirst_limits.py`, gegen eine Kopie der zwei Dokumente, der Arbeitsbaum wird nicht
angefasst):**

```
baseline                                                   rc=0  0 problem(s)
ZIEL     Rumpf ohne "unbekanntes Ziel NICHT gemessen"      rc=1  ...names set_cwd without marking the UNKNOWN TARGET unmeasured
KONTROLLE Rumpf ohne den UNVERWANDTEN "nicht gemessen"     rc=0  0 problem(s)
ZIEL     Rumpf verallgemeinert wieder über beide Wege      rc=1  ...asserts one limitation for both ways at once
ZIEL     Tabellenzeile "nur vor dem ERSTEN" -> "vor jedem" rc=1  ...does not restrict the dialog to the first move
ZIEL     Messdokument §2 dieselbe Änderung                 rc=1  ...does not restrict the dialog to the first move
restored                                                   rc=0  0 problem(s)
```

Die **Kontrollzeile** ist der eigentliche Beleg: das Streichen des unverwandten Satzes lässt den
Prüfer jetzt grün — der Auslöser ist auf den richtigen Satz gewandert. Die Mutation des Prüfers,
die vorher rc 0 gab („auf beiden Wegen dasselbe" abschwächen), wird jetzt rot.

### 9.2 M1 — ausgelieferter Code zeigte in ein Verzeichnis, das aufgeräumt wird

Die beiden Docstrings verwiesen auf `shapes1.log`, `plant_shapes.py`, `nested1.log`,
`ext4-fullargs-before.jsonl` und drei Dateien des Prüfers — alle unter `_round-scratch/`. Die
Fünf-Formen-Messung steht jetzt als **§5a** im Messdokument
(`docs/reviews/2026-09-02-model-pin-and-bom-measurement.md`): Verfahren, Tabelle der fünf Dateien,
Client-Antwort, Datum, CLI-Version, warum die Client-Regel nicht der Gegenstand wird, und die
Rohdatennamen. Die Docstrings zeigen auf diesen Abschnitt.

### 9.3 N1 — Universalquantor mit der falschen Messung darunter

„IT IS WIDER THAN ANY CLIENT READS … no client reads that tree (measured in `cases3.py`)" ist
ersetzt: der Gegenstand ist weiter als das, was **dieser** Client liest (gemessen: §5a); dass
`docs/agents/` hineinfällt, ist **Reibung**, und gemessen ist daran der rote Lauf, nicht ein Client.
Damit stimmt auch wieder, was Abschnitt 8.3 über die Docstrings sagt.

### 9.4 N2 — „cannot drift apart" trug nichts

Gemessen vom Prüfer: eine lokale, verengte Neudefinition lässt 15 Tests grün, aber `ruff` fängt sie
als F811. Der Satz sagt das jetzt: **zwei Definitionen DIESES NAMENS fängt `ruff` (F811); eine
Funktion unter anderem Namen fängt nichts** — die Teilung ist eine Verabredung mit einer
mechanischen Hälfte, nicht mehr.

### 9.5 N3 — die Tiefe hatte auf dem ausgelieferten Baum keinen Halter

Das Repo liefert keine geschachtelte Rolle, also war das Verengen der geteilten Funktion still.
Neu: `test_the_role_predicate_reaches_any_depth_and_stops_at_the_directory_name` sagt beide Kanten
auf Literalpfaden (`a/agents/b/c.md` wahr, `a/agents-old/c.md`, `agents.md`, `a/agents/c.txt`
falsch).

**Rot-zuerst (`redfirst_narrow.py`; die eine vorbestehende Klon-Abweichung ist abgewählt und im
Skript begründet):**

```
baseline, Prädikat weit                              rc=0  15 passed
Prädikat VERENGT, mit dem neuen Halter               rc=1  1 failed, 14 passed
Prädikat VERENGT, Halter abgewählt (der alte Stand)  rc=0  14 passed
restored                                             rc=0  15 passed
```

Zeile drei ist der Befund des Prüfers, reproduziert; Zeile zwei ist seine Behebung.

### 9.6 N4 — zwei Zahlen für denselben Lauf

Die Zeile `| check_refs.py | 53 Belegpfade |` in Abschnitt 7.3 ist als **abgelöst** markiert und
verweist auf die 58 aus Abschnitt 7.2.

### 9.7 Läufe der Nacharbeit 3

| Lauf | Ergebnis |
|---|---|
| `python -m ruff check .` | All checks passed |
| `pytest tools/test_model_pins.py tools/test_repo_hygiene.py -q` | **16 passed** (der neue Halter) |
| `pytest tools/test_hooks.py -k "model or tier or bom" -q` | 11 passed, 902 deselected (126 s) |
| `pytest .claude/hooks/test_gates.py -k "hole or measurement or reference" -q` | 8 passed, 481 deselected (195 s) |
| `check_refs.py` | **65** Belegspannen, 0 fehlend |
| `check_limits.py` | 3 Stellen, 6 Aussagen, 0 Probleme |
| `redfirst_limits.py` | 4 Ziel-Mutationen rot, 1 Kontroll-Mutation grün |
| `redfirst_narrow.py` | verengt rot nur mit dem Halter |

### 9.8 Was Nacharbeit 3 NICHT geschlossen hat

* Die Reibung bleibt (eine `.md` unter `agents/`, die kein Client lädt, wird nach einem Trenner
  gefragt) — jetzt an der dauerhaften Stelle §5a begründet statt im Scratch.
* Dass die zwei Module dieselbe Funktion benutzen, ist nur zur Hälfte mechanisch gesichert: `ruff`
  fängt eine zweite Definition **desselben Namens**, eine unter anderem Namen fängt nichts. Steht
  so im Docstring.
* `set_cwd` an einem wirklich unbekannten Ziel, und das Terminal aus
  `claude-vscode.terminal.open` — unverändert offen.

---

## 10. Nacharbeit 4 (Nachprüfung 3: B=1, M=1, N=2)

### 10.1 B1 — die Löcherliste versprach einen Wächter, den es nach der Runde nicht gibt

Der `H114`-Rumpf sagte: „Seit der vierten prüft `check_limits.py`, dass diese Stelle, die
Tabellenzeile und §2 dieselben Aussagen tragen." Zwei Gründe, warum der Satz weg ist:
`check_limits.py` liegt in `_round-scratch/` und ist **nicht im Patch** — nach dem Rundenabschluss
existiert es nicht mehr; und die Zelle gegen die Verallgemeinerung ist **wortgebunden** (der Prüfer
hat gemessen: „für `/cd` und `set_cwd` gilt dieselbe Grenze" läuft blind durch). Der Satz ist
gestrichen; an seine Stelle tritt der schlichte Hinweis, dass diese Fassung die Wege trennt und wer
sie ändert, die anderen beiden Stellen mitändert. Nichts Neues nach `tools/` — ein
Prosa-gegen-Prosa-Test wäre eine neue Aufzählung.

**`check_limits.py` ist damit ein Instrument dieser Runde und nichts weiter.** Was es kann, ist
gemessen (Abschnitt 9.1): es fängt den fehlenden Ziel-Satz und die aufgeweichte
Erst-Wechsel-Aussage an allen drei Stellen. Was es nicht kann, steht hier: die Zelle gegen die
Verallgemeinerung über beide Wege ist an eine Schreibweise gebunden und geht bei einer anderen
Formulierung blind durch. Ausgeliefert wird es nicht.

### 10.2 M1 — zwei Scratch-Zeiger standen noch im ausgelieferten Modul

`tools/test_model_pins.py` zeigte auf `verify3/probes/cases3.py` (die Datei heißt `verify2/cases3.py`
— der Zeiger war doppelt falsch) und auf `verify3/probes/narrow.py`. Beide Sätze tragen die Aussage
jetzt selbst: die Reibung verweist auf §5a des Messdokuments, und der Halter-Test sagt „gemessen,
indem man genau das tut" statt einen fremden Dateinamen zu nennen. Gegenprobe:

```
grep -rn "verify2|verify3|_round-scratch|shapes1|cases3|narrow.py" tools/
  tools/provider_observations.json:44   "location": ".../_round-scratch/TSK-0082/deadline-rig"
  tools/test_hooks.py:7061              # .../_round-scratch/TSK-0066/half3/DREHBUCH-haelfte3.md
```

Beide Treffer sind **rundenfremd** (TSK-0082 und TSK-0066) und werden hier nicht angefasst. Aus
dieser Runde steht kein Scratch-Zeiger mehr in `tools/`.

### 10.3 N1 — zwei Abschnittszeiger zeigten auf sich selbst

Die Zeile mit den 53 steht in §7.3, die 58 stehen in §7.2. Beide Zeiger sind entsprechend
richtiggestellt (die Zeile selbst und der Satz in §9.6).

### 10.4 N2 — eine 165 Zeichen lange Zeile

Entstanden durch eine Textersetzung ohne Umbruch. Der Absatz ist neu umbrochen. **Längste Zeile
danach:** `tools/test_repo_hygiene.py` 101 Zeichen (Zeile 634, aus einer früheren Runde),
`tools/test_model_pins.py` 102 Zeichen (Zeile 13, Kopfkommentar dieser Runde). Beide sind kein
Lint-Fehler: `ruff.toml` wählt `E4`, `E7`, `E9`, `F` — `E501` ist nicht darunter, es gibt also
keine erzwungene Grenze, nur den Hausstil.

### 10.5 Läufe der Nacharbeit 4

| Lauf | Ergebnis |
|---|---|
| `python -m ruff check .` | All checks passed |
| `pytest tools/test_model_pins.py tools/test_repo_hygiene.py -q` | 16 passed |
| `pytest tools/test_hooks.py -k "model or tier or bom" -q` | siehe Bericht |
| `pytest .claude/hooks/test_gates.py -k "hole or measurement or reference" -q` | siehe Bericht |
| `check_refs.py` | 65 Belegspannen, 0 fehlend |
| `check_limits.py` | 0 Probleme |
| `redfirst_limits.py` | 4 Ziel-Mutationen rot, 1 Kontroll-Mutation grün (nach der B1-Änderung erneut) |
