# Modell-Pins und BOM — gemessen (FR-0047, FR-0060)

Messrunde 2026-09-02, Umsetzer-Stream „measurements" zu `TSK-0108`. Rig: ein gescaffoldetes
Projektchen außerhalb des Repos (`…/_round-scratch/TSK-0108/modelrig`) mit zwei Rollen, die nichts
tun außer eine Modellangabe zu tragen; getrieben headless über `claude -p` im
`stream-json`-Transport, Client **2.1.258**. Rohdaten `model1.log`, `model2.log`, `m13.log`.

## 1. Ein Pin, den der Client nicht kennt, fällt nicht zurück — der Spawn stirbt

Rolle `bogus-pin` mit `model: opus-4-1-does-not-exist`, per Task-Werkzeug gestartet. Auf `stderr`
der Sitzung:

```
[claude-code:unrecognized_model] {"model":"opus-4-1-does-not-exist[1m]","query_source":"agent:custom:bogus-pin"}
```

und als Ergebnis desselben Werkzeugaufrufs (`is_error: true`), wörtlich:

```
Agent terminated early due to an API error: There's an issue with the selected model
(opus-4-1-does-not-exist[1m]). It may not exist or you may not have access to it.
(error type model_not_found, HTTP 404, request id req_…, model sent to the API:
opus-4-1-does-not-exist)
```

Das Aufgaben-Ereignis derselben Sitzung trägt `"status": "failed"`. Der Elternteil bekommt den
Fehler also **sichtbar** — als fehlgeschlagenen Werkzeugaufruf mit dem Modellnamen darin.

## 2. Derselbe harte Fehler trifft die Tier-ALIASE, die die Kit-Quellen tragen

Rolle `alias-pin` mit `model: worker` — genau der Wert, den `team-kits/*/agents/*.md` im Quellstand
buchstabieren:

```
Agent terminated early due to an API error: There's an issue with the selected model (worker).
… model sent to the API: worker
```

Damit ist die Alias-Übersetzung beim Installieren (`scaffold_team.sh`/`.ps1`) **tragend** und nicht
Kosmetik: bliebe ein Alias in der installierten Frontmatter stehen, wäre die Rolle nicht spawnbar.
Diese Seite ist bereits gemessen und gedeckt —
`test_both_scaffold_launchers_leave_no_tier_alias_in_installed_frontmatter` in `tools/test_hooks.py`
fährt beide Starter und liest die installierte Frontmatter; sie wird hier deshalb **nicht** noch
einmal gebaut.

## 3. Korrektur an der Annahme von `FR-0047`

Das Radar-Item führte einen „unresolvable pinned model" als etwas, das **still** die Fallback-Kette
mitreitet. Für einen Rollen-Pin trifft das auf diesem Client nicht zu (Befunde 1 und 2): es gibt
keinen stillen Rückfall, sondern einen abgebrochenen Spawn mit HTTP 404.

Was in dieser Runde **nicht** gemessen wurde und darum auch nicht behauptet wird: das Verhalten von
`--fallback-model` (laut `claude --help` nur mit `--print` wirksam, „when the default model is
overloaded or not available") und das der plattformeigenen Sicherheits-Umleitung, die `FR-0047`
ursprünglich ausgelöst hat. Beides sind eigene Messungen.

## 4. Was noch fehlt, damit ein Pin-Fehler ein PROTOKOLLIERTES Ereignis wird

Sichtbar ist der Fehler heute nur im Gespräch: der Elternteil liest ihn im Werkzeugergebnis. Es
bleibt nichts davon zurück — kein Eintrag im Zustand, keine Zeile in einem Protokoll, und der
nächste Spawn derselben Rolle läuft in denselben Fehler.

Zwei Hälften, beide **außerhalb dieses Streams**:

* **Vorher statt nachher:** ein `PreToolUse`-Wächter auf `Agent|Task` kann die Frontmatter der
  gespawnten Rolle lesen — `gate_spawn_needs_item.py` tut genau das bereits für `harness_item` —
  und einen Wert verweigern, den `model_tiers.yaml` nicht platzieren kann. Der Leser dafür steht
  seit dieser Runde als `the_table_can_place` in `tools/test_model_pins.py` und ist eine
  Ableitung aus der Tabelle, keine Namensliste.
* **Nachher als Zustand:** damit ein fehlgeschlagener Spawn eine Spur hinterlässt, braucht es einen
  Kit-Hook (`SubagentStop`/`PostToolUse`), der den Fehlertext einsammelt. Das ist Kit-Bereich →
  **Nahtstelle** für den Hook-Eigentümer von dev/office, hier nur benannt.

Diese Runde baut die Prüfung, die ohne Client auskommt: dass **kein** ausgelieferter Rollen-Pin
unplatzierbar ist (`tools/test_model_pins.py`, beide Richtungen).

## 5. BOM: heute keiner, und die Prüfung liest ab jetzt die richtige Menge

Bestand am 2026-09-02: von **1050** von git verfolgten Dateien beginnt **keine** mit `EF BB BF`.
Der neue Stolperdraht in `tools/test_repo_hygiene.py` fragt nicht nach Verzeichnissen, sondern nach
einer Eigenschaft — welche Datei ein Leser **ab Byte 0** als Struktur liest
(`read_from_byte_zero`): eine `.json` (der JSON-Parser fängt dort an), eine Datei, deren erste Zeile
der Frontmatter-Trenner ist (jede Rolle, jeder Skill), und eine, deren erste Zeile der Kit-Marker
ist. Heute sind das 61 Rollen-/Skill-Definitionen, 10 JSON-Dateien und 3 Konstitutionen.

Die Gegenrichtung ist ein eigener Test,
`test_every_shipped_role_and_skill_definition_is_a_file_that_check_looks_at`. Sein Gegenstand sind
**zwei Lader-Schlüssel**, nicht zwei Verzeichnisse: eine Rolle ist jede verfolgte `.md` unterhalb
eines `agents`-Verzeichnisses (in beliebiger Tiefe, `under_an_agents_directory`), ein Skill ist die
Datei **namens** `SKILL.md`. Eine `.md` unter `skills/`, die anders heißt — ein Referenz-Dokument,
das ein Skill mitbringt —, ist damit **nicht** Gegenstand. Jeder Gegenstand muss von
`read_from_byte_zero` erkannt werden, sonst fiele eine Rolle, die ihren Trenner verliert, still aus
der BOM-Prüfung heraus.

## 5a. Welche Datei unter `agents/` der Client wirklich lädt — fünf Formen, gemessen

Diese Messung trägt den Gegenstand der beiden Prüfungen aus §5, und sie steht hier statt im
Scratch-Verzeichnis, weil der Code auf sie zeigt und das Scratch beim Rundenabschluss aufgeräumt
wird.

**Verfahren.** Fünf Dateien in `.claude/agents/` eines Rig-Projekts außerhalb des Repos, eine je
Eröffnungsform, danach eine headless-Sitzung; ausgewertet wird die Liste `agents` im
`init`-Ereignis des Clients — also die Auskunft des Laders selbst, nicht eine Vermutung darüber.
Gefahren am **2026-09-02** gegen **Claude Code 2.1.258**.

| Datei | erste Zeile | Rest | in `init.agents` |
|---|---|---|---|
| `p-ok.md` | der Frontmatter-Trenner | gültige Frontmatter | **ja** |
| `p-atx.md` | eine ATX-Überschrift | darunter gültige Frontmatter | nein |
| `p-setext.md` | eine Setext-Überschrift | darunter gültige Frontmatter | nein |
| `p-prose.md` | ein Prosasatz | keine Frontmatter | nein |
| `p-html.md` | ein HTML-Kommentar | darunter gültige Frontmatter | nein |

Die Antwort des Clients nennt `p-ok` und keine der vier anderen; es gibt dazu keine Meldung, keine
Warnung und keinen Fehler.

**Ergebnis, gebunden an diese fünf Formen und diese Client-Version:** geladen wird die Datei, deren
**erste Zeile der Frontmatter-Trenner** ist.

**Warum diese Regel trotzdem NICHT der Gegenstand der Prüfungen ist.** Genau die Datei, für die der
Stolperdraht existiert — eine Rolle, die ihren Trenner verloren hat —, würde sich damit selbst aus
der Menge nehmen; der Gegentest wäre tautologisch. Der Gegenstand bleibt darum der **Ort** (eine
`.md` unterhalb eines `agents`-Verzeichnisses) beziehungsweise der **Name** (`SKILL.md`), und der
Preis dafür ist Reibung: ein Dokument, das jemand zwischen die Rollen legt, wird nach einem
Trenner gefragt, den kein Lader von ihm verlangt. Das ist gewollt und steht so auch in den
Docstrings von `tools/test_repo_hygiene.py` und `tools/test_model_pins.py`.

**Rohdaten:** `plant_shapes.py` legt die fünf Dateien an, `shapes1.log` ist die Mitschrift der
Sitzung (beide unter `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0108\`). Zwei unabhängige
Wiederholungen des Prüfers liegen als `verify2/probe.log`, `verify2/probe2.log` und
`verify3/shapes-v3.log` daneben. Eine zweite, ältere Messung derselben Klasse: eine Rolle in einem
UNTERverzeichnis (`.claude/agents/nested/agent-z.md`) wird gefunden, gespawnt und steht in derselben
Liste — Mitschrift `nested1.log`, Hook-Zeile in `ext4-fullargs-before.jsonl`.

## 6. Auf diesem Client lädt eine Rollendatei MIT BOM

Gegenprobe im `/cd`-Rig: `prober-b.md` mit vorangestelltem `EF BB BF` in das aktuelle Projekt
kopiert und gespawnt — der Subagent lief (Mitschrift `m13.log`; die Hook-Zeile dazu steht in
`ext1-before.jsonl`, `{"tag":"A2","t":"12:28:22", … "command":"echo PROBER-B-RAN"}`, Client
2.1.258). Die präparierte Datei liegt noch im Rig: `cdrig/dirA/.claude/agents/prober-b.md` beginnt
mit `ef bb bf`, `cdrig/dirB/.claude/agents/prober-b.md` mit `2d 2d 2d`, beides nachgelesen am
2026-09-02. (Der Weg dieser Zeile durch zwei falsche Verweise ist der Grund, warum jeder Beleg hier seinen
Pfad ausschreibt: die erste Fassung nannte `hooklog-m13.jsonl`, die es nie gab, die zweite
`cdrig/hooklog.jsonl`, die es zu dem Zeitpunkt nicht mehr gab. Das Rig schreibt in EINE Datei, und
der nächste Treiberstart räumt sie als `<lauf>-before.jsonl` beiseite — hier als
`ext1-before.jsonl`.) Der Stolperdraht schützt also **nicht** vor einem
Schaden, den dieser Host heute nimmt; er schützt vor Clients unterhalb der Grenze und vor unseren
eigenen Lesern (Befund 7).

### Die CC-Grenze, als eine Zeile

> **Claude Code < 2.1.239 überspringt jede `agents`/`skills`/`commands`-`.md`, die mit einem UTF-8-BOM
> beginnt, ohne Meldung** — eine Rolle, die es dort nicht gibt, ist eine Rolle, die nicht bindet.

Herkunft: Radar-Eintrag `radar/2026-08-29-claude.md` zum Changelog 2.1.239, in dieser Runde **nicht
nachgemessen** (dieser Host liegt darüber). **Durchgesetzt wird sie nirgends:** die Installer prüfen
eine Version nur für Codex (`install.sh`/`install.ps1`, Grenze 0.131.0), für Claude Code prüft
nichts. Der Ort, an dem so eine Grenze in den Installationsnotizen steht, ist der
Quickstart-Abschnitt in `README.md` — der liegt außerhalb des Bereichs dieses Streams und ist als
**Nahtstelle** gemeldet, samt der Entscheidung, ob aus der Notiz eine Prüfung werden soll.

## 7. Ein eigener Leser, den ein BOM heute schon trifft — gelesen, nicht ausgeführt

`.claude/hooks/_harness.py` liest `.claude/settings.json` mit `json.load` und `encoding="utf-8"`
(Zeilen 166/167, die Stelle, an der `Deadline` die registrierte Frist holt). Dass ein BOM diesen
Aufruf scheitern lässt, ist nachgemessen und nicht angenommen — dieselben zwei Zeilen gegen eine
`settings.json` mit `EF BB BF` davor:

```
utf-8     -> JSONDecodeError: Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0)
utf-8-sig -> {'hooks': {}}
```
**Was der Gate-Prozess daraus macht, ist in dieser Runde nicht gemessen** — ein Gate lässt sich aus
einer Sitzung heraus nicht starten (`H80`), und ohne diesen Lauf steht hier keine Aussage darüber,
ob das eine Verweigerung oder ein Durchlass wird. Genau darum deckt der Stolperdraht die `.json`-
Dateien mit ab, statt sich auf Rollen zu beschränken.

## 8. Rot-zuerst: was ohne die neuen Prüfungen durchginge

Gemessen in einem Klon außerhalb des Repos (`…/_round-scratch/TSK-0108/redclone`, Treiber
`redfirst.py`); Ausgangslage und Endstand jeweils grün.

| Mutation | rot wird |
|---|---|
| BOM vor eine Kit-Rollendatei | `test_no_file_a_parser_reads_from_byte_zero_starts_with_a_bom` |
| BOM vor `.claude/settings.json` | dieselbe |
| einem Skill den Frontmatter-Trenner nehmen | `test_every_shipped_role_and_skill_definition_is_a_file_that_check_looks_at` (die BOM-Prüfung bleibt grün — genau der stille Fall) |
| `model: opus-4-1-does-not-exist` in einer Rolle dieses Repos | `test_every_model_a_shipped_role_pins_resolves_in_the_tiers_table` |
| den Pin-Leser wieder auf `team-kits/` verengen (der Zustand vor dieser Runde) | `test_the_pin_reader_covers_every_agents_directory_the_repo_tracks` |
| den Resolver alles annehmen lassen | `test_the_reader_refuses_what_the_table_cannot_place_and_demands_no_tier_be_pinned` |
| den Frontmatter-Leser auf ein Muster stellen, das nichts trifft | `test_the_pin_reader_covers_every_agents_directory_the_repo_tracks` — die anderen drei Prüfungen bleiben dabei grün, das ist genau der stille Fall |

## 9. Eine Vermutung, die die Messung widerlegt hat (und darum nicht im Code steht)

Der erste Entwurf des Pin-Lesers trug eine CR-Toleranz im Muster, mit der Begründung, ein
CRLF-Checkout könne den Pin unsichtbar machen — die Fehlklasse, die es beim Scaffold wirklich gab.
Im Klon nachgemessen: **32** Rollendateien auf CRLF umgestellt, Prüfung grün; und mit dem
Muster ohne CR-Toleranz ebenfalls grün. Grund: `pinned_model` liest im Textmodus, und der
normalisiert `\r\n` zu `\n`, bevor das Muster überhaupt läuft (Gegenprobe: eine CRLF-Datei so
gelesen enthält **0** Wagenrückläufe). Die Toleranz und ihre Begründung sind darum wieder
entfernt — sie hätten einen Schutz behauptet, den es nicht braucht. Geblieben ist die Zählung der
gefundenen Pins, die einen Leser, der nichts trifft, tatsächlich rot macht (Tabelle oben, letzte
Zeile).

## Offen / nicht gemessen

* `--fallback-model` und die Sicherheits-Umleitung der Plattform (Befund 3).
* Ob ein BOM auf `.claude/settings.json` ein Gate zum Verweigern oder zum Durchlassen bringt
  (Befund 7).
* Die `effort:`-Werte: ihr Vokabular steht in `model_tiers.yaml` nur in einem **Kommentar**, wird von
  keinem Leser ausgewertet und ist hier bewusst nicht mitgeprüft — benannt, nicht geschlossen.
* Verhalten unterhalb 2.1.239 (BOM) — dafür gibt es auf diesem Host keinen Client.
