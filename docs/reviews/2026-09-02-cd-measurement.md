# `/cd` gemessen — was mitten in der Sitzung neu bindet und was nicht (FR-0059)

Messrunde 2026-09-02, Umsetzer-Stream „measurements" zu `TSK-0108`. Anlass: `FR-0059` und der
9-Punkte-Messplan in `docs/reviews/2026-08-29-cd-rebinding-research.md`. Die Recherche dort war
Doku-Lektüre; **hier ist gemessen**, und wo die Messung der Doku widerspricht, gilt die Messung.

## Rig und Verfahren

Zwei vorbereitete Projekte außerhalb des Repos, `…/_round-scratch/TSK-0108/cdrig/dirA` und `…/dirB`.
Jedes trägt eine eigene `.claude/settings.json` mit **einem PreToolUse-Hook auf `Bash`**, der eine
JSON-Zeile in eine gemeinsame Logdatei schreibt (welche Registrierung feuerte, welches Skript lief,
`cwd` aus der Nutzlast, `CLAUDE_PROJECT_DIR` aus der Umgebung), eine eigene `agent:`-Bindung auf
einen Rollen-Agenten mit unterscheidbarem System-Prompt, einen eigenen Skill und einen eigenen
Subagenten. Der gebundene Agent meldet seine Identität **nicht als Fließtext**, sondern indem er
einen Bash-Befehl mit seinem Token ausführt — so steht die Antwort im Hook-Log und nicht in einer
Selbstauskunft, die niemand nachprüft.

Zwei Transporte, weil `/cd` nur einen davon erreicht:

* **headless** (`claude -p --input-format stream-json --output-format stream-json
  --include-hook-events`), Treiber `driver.py` im Scratch;
* **interaktiv** über eine echte ConPTY (`ptydrive.py` + `pyte` zum Nachzeichnen des Bildschirms),
  weil `/cd` ein lokales Slash-Kommando ist und im `-p`-Transport gar nicht existiert (Befund 1).

Clients: CLI **2.1.258** sowie das mitgelieferte Binary der VS-Code-Erweiterung, **2.1.257**.
Der CLI hat sich während der Runde selbst aktualisiert: der Rauchtest zu Beginn zeigt noch das
2.1.251-Banner (`pty-smoke.log`), jeder danach ausgewertete Lauf 2.1.258 (nachgesehen in
`m2a.log`, `m4.log`, `m12.log`).

**Rohdaten.** Alles liegt unter `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0108\`, und jeder Verweis
unten nennt seinen Pfad **relativ zu diesem Verzeichnis** — es gibt keine Regel, aus der man ihn
ableiten könnte, und zwei Anläufe, das doch zu tun, sind schiefgegangen. Der Grund ist
mechanisch: das Rig-Skript schreibt immer in **eine** Datei `cdrig/hooklog.jsonl`, die zwischen
zwei Läufen gar nicht existiert — wer sie umbenennt, entscheidet, wie sie am Ende heißt — von Hand nach dem Lauf (die Reihe
`cdrig/hooklog-m*.jsonl`) oder durch den Treiber beim nächsten Start, der sie vorher als
`<lauf>-before.jsonl` beiseiteräumt. Darum steht die Hook-Zeile eines Laufs manchmal in der
`-before`-Datei des **nächsten**.

| Sorte | wo |
|---|---|
| Sitzungsmitschriften | direkt: `m1.log`…`m13.log`, `ext1.log`, `ext2.log`, `ext3.log`, `ext4-fullargs.log`, `reb1.log`, `reb2-resume.log`, `nested1.log`, `readme1.log`, `pty-smoke.log` |
| Hook-Protokolle der ersten Läufe | `cdrig/hooklog-m2b.jsonl`, `cdrig/hooklog-m3.jsonl`, `cdrig/hooklog-m4.jsonl`, `cdrig/hooklog-m5.jsonl`, `cdrig/hooklog-m6.jsonl`, `cdrig/hooklog-m7.jsonl`, `cdrig/hooklog-m9b.jsonl`, `cdrig/hooklog-m10b.jsonl`, `cdrig/hooklog-m11.jsonl` |
| Hook-Protokolle der späteren Läufe | direkt: `ext1.jsonl`, `ext1-before.jsonl`, `ext2.jsonl`, `ext3.jsonl`, `ext4-fullargs.jsonl`, `ext4-fullargs-before.jsonl`, `reb1.jsonl`, `reb2-resume.jsonl` |
| Das Rig-Skript selbst | `cdrig/log_hook.py` (Vorlage) und die zwei installierten Kopien `cdrig/dirA/.claude/hooks/log_hook.py` und `cdrig/dirB/.claude/hooks/log_hook.py` - wo unten `log_hook.py` in einer zitierten Kommandozeile oder Logzeile steht, ist eine davon gemeint |

## Der 9-Punkte-Messplan, Punkt für Punkt

Aus `docs/reviews/2026-08-29-cd-rebinding-research.md`. Die Spalte „Beleg" nennt die Datei, in der
der Lauf steht — wer die Zeile nicht findet, hat einen Befund vor sich, der nicht gemessen ist.

| Punkt | Stand | Befund | Beleg |
|---|---|---|---|
| 1 Client ≥ 2.1.246 | gemessen | Banner 2.1.258 (CLI), 2.1.257 (Erweiterung) | `m12.log`, `ext1.log` |
| 2 Zwei Verzeichnisse mit Hook + `agent:` | gebaut | Rig `cdrig/dirA`, `cdrig/dirB` | `cdrig/settings-*.json` |
| 3 `/cd` A→B: feuern B-Hooks, antwortet die Sitzung als B? | gemessen | Hooks ja, Bindung nein | 3, 6 · `cdrig/hooklog-m2b.jsonl` |
| 4 `${CLAUDE_PROJECT_DIR}` nach dem Wechsel | gemessen | bleibt am Start | 4 · `cdrig/hooklog-m2b.jsonl` |
| 5 Wortlaut des Trust-Dialogs | gemessen | wörtlich protokolliert | 2 · `m2a.log` |
| 6 `/cd` in `-p`/SDK auslösbar? | gemessen | nein | 1 · `m12.log`, `ext1.log` |
| 7 Falls Agent B nicht greift: Fortsetzen fahren | gemessen | `--continue` bindet, die laufende Sitzung nicht | 14, 17 · `reb1.log`, `reb2-resume.log` |
| 8 Statuszeile | gemessen | folgt dem Ziel, Agentenanzeige nicht | 11 · `m2a.log` |
| 9 Entscheidung über die Zeremonie | **nicht** Sache dieser Runde | Empfehlung in Befund 6/17, Entscheidung beim Lead | — |

Punkt 7 stand im Plan als `--resume`; gefahren ist `--continue`, weil das die Fortsetzung **derselben**
zuletzt gelaufenen Sitzung in diesem Verzeichnis ist und der Plan genau die wissen wollte. Eine
Fortsetzung einer `dirA`-Sitzung aus `dirB` heraus ist **nicht** gemessen: `--continue` sucht die
letzte Sitzung des aktuellen Verzeichnisses, erreicht die andere also gar nicht.

## 1. `/cd` gibt es in `-p`/SDK nicht

```
{"type":"assistant", … "content":[{"type":"text","text":"/cd isn't available in this environment."}]}
```

(`m12.log`, Client 2.1.258; gleiche Antwort in `m1.log`.) Passend dazu führt das `init`-Ereignis
derselben Sitzung unter `slash_commands` kein `cd`.

**Folge:** Die in der Recherche notierte Restsorge („in `-p` gibt es keinen Trust-Dialog, Hooks
nie-vertrauter Verzeichnisse laufen trotzdem") ist gegenstandslos — eine headless-Sitzung kann sich
gar nicht bewegen. Damit bleibt `/cd` das, was die Doku sagt: nur die tippende Person löst es aus.

## 2. Der Trust-Dialog vor dem Wechsel, wörtlich

Interaktiver Wechsel in ein noch nicht vertrautes Verzeichnis (`m2a.log`, Bildschirm nachgezeichnet):

```
Moving to a new directory:
This session hasn't worked here before. Is this a directory you created or one you trust?
Claude Code'll be able to read, edit, and execute files here.
⚠ This directory configures hooks that run commands, declared in .claude/settings.json
These will apply to this session as soon as you move. Only proceed if you trust this configuration.
Security guide
❯ No, stay put
  Yes, move here
Enter to confirm · Esc to cancel
```

Die Vorauswahl steht auf **„No, stay put"**; die Hook-Warnung nennt die Datei, aus der die
Registrierung kommt.

**Wie weit dieser Dialog reicht — und das ist die Begrenzung, auf die sich `H114` stützt:** er steht
nur vor dem **ersten** Wechsel in ein Verzeichnis. Ein späterer `/cd` in dasselbe, inzwischen
bestätigte Verzeichnis zeigt ihn nicht mehr — gemessen im Lauf `m4.log`, dessen Steuerskript
`pty-m4.txt` zwischen dem `/cd` und der nächsten Eingabe keinen Tastendruck sendet. Auf dem
`set_cwd`-Weg (Befund 16) ist überhaupt nur der dialogfreie Wechsel an ein bereits vertrautes Ziel
gemessen; ob an einem unbekannten Ziel ein Dialog erscheint, ist **NICHT gemessen** — belegt ist dort
nur die Fehlermeldung, die einen zweistufigen Handschlag beschreibt (`ext2.log`).

Ob der Dialog wiederkommt, wenn sich die Hook-Konfiguration seit der Bestätigung **geändert** hat,
ist ebenfalls nicht sauber gemessen (im betreffenden Lauf wurden die Tasten blind gesendet).

## 3. Hooks des Zielverzeichnisses binden sofort — und die des Startverzeichnisses fallen weg

Nach dem Wechsel A → B feuert pro Bash-Aufruf **genau eine** Zeile, und die trägt B:

```
{"tag": "B", … "command": "echo REPORT-BINDING token=AGENT-A",
 "payload_cwd": "…\cdrig\dirB", "env_CLAUDE_PROJECT_DIR": "…/cdrig/dirA"}
```

(`cdrig/hooklog-m2b.jsonl`, dritte Zeile; unabhängig wiederholt in `cdrig/hooklog-m4.jsonl`, erste Zeile.)
`/cd` **tauscht** also, es ergänzt nicht — das bestätigt die Doku.

## 4. `${CLAUDE_PROJECT_DIR}` bleibt am Startort

Dieselbe Zeile: `env_CLAUDE_PROJECT_DIR` zeigt weiter auf `dirA`, während `payload_cwd` schon `dirB`
ist. Das gilt in jedem Lauf nach jedem Wechsel.

## 5. Neue Registrierung, ALTE Hook-Dateien — der gefährliche Teil (`H114`)

Beide Verzeichnisse buchstabieren ihre Hook-Kommandozeile so, wie unsere Kits es tun, nämlich
`python -B "${CLAUDE_PROJECT_DIR}/.claude/hooks/log_hook.py" REG-<X>`, und jede Kopie des Skripts
meldet, aus welchem Verzeichnis sie stammt. Nach dem Wechsel A → B:

```
{"tag": "REG-B", "script_home": "SCRIPT-A",
 "script_path": "…\cdrig\dirA\.claude\hooks\log_hook.py", …}
```

(`cdrig/hooklog-m10b.jsonl`, zweite Zeile.) Das Argument kommt aus **B**s Registrierung, ausgeführt wird
**A**s Datei. Wer zwischen zwei Kit-Projekten wechselt, lässt also die Gates des Startprojekts über
die Arbeit im Zielprojekt urteilen. Eintrag mit Kette und Grenze: `H114` in
`docs/POST_V2_WISHLIST.md`.

## 6. Die `agent:`-Bindung wechselt NICHT — die zentrale offene Frage der Recherche

Im selben Lauf lautet der Befehl, den der gebundene Agent ausführt, nach dem Wechsel weiter
`echo REPORT-BINDING token=AGENT-A` (Befund 3, Zeile oben), obwohl `dirB/.claude/settings.json`
`agent: agent-b` sagt; die Fußzeile der Oberfläche zeigt bis zum Sitzungsende `agent-a`.

Gegenprobe mit einem **Neustart** in demselben Verzeichnis (`cdrig/hooklog-m7.jsonl`):

```
{"tag": "B2", … "command": "echo REPORT-BINDING token=AGENT-B",
 "payload_cwd": "…\cdrig\dirB", "env_CLAUDE_PROJECT_DIR": "…/cdrig/dirB"}
```

Der Neustart ist also genau das, was die Bindung setzt. **Für die Install-/Update-Zeremonie der Kits
heißt das: die Bitte um einen Neustart bleibt nötig** — sie ist der einzige Weg, auf dem der
Project Manager aktiviert wird.

## 7. Subagenten des Zielverzeichnisses stehen nach `/cd` nicht zur Verfügung

In einer Sitzung, die nachweislich in `dirB` steht (Befund 3, erste Zeile von `cdrig/hooklog-m4.jsonl`),
antwortet das Task-Werkzeug auf den Subagenten, den es nur in `dirB` gibt:

```
Error: Agent type 'prober-b' not found. Available agents: agent-a, claude, claude-code-guide,
Explore, general-purpose, Plan, statusline-setup
```

Die verfügbaren Agenten sind weiterhin die von `dirA`. Der Changelog-Eintrag zu 2.1.246 nennt
„agents" ausdrücklich als eines der Dinge, die sofort greifen — **für Subagenten und für die
`agent:`-Bindung trifft das auf 2.1.258 nicht zu**. Eintrag: `H115`.

## 8. Skills des Zielverzeichnisses binden sofort

Der nur in `dirB` vorhandene Skill lief nach dem Wechsel (`cdrig/hooklog-m2b.jsonl`, vierte Zeile,
`"command": "echo SKILL-B-LOADED"`).

## 9. MCP-Server des Zielverzeichnisses binden sofort

Nach dem Wechsel zeigt `/mcp` (`m8.log`, Bildschirm nachgezeichnet):

```
Project MCPs (C:\…\cdrig\dirB\.mcp.json)
❯ rig-mcp-b · ◯ connecting…
```

Der Server aus `dirB` ist übernommen. Ein Freigabedialog erschien in diesem Lauf zwischen Wechsel
und Auflistung **nicht**; er bleibt „connecting…", weil das Rig-Serverchen absichtlich kein MCP
spricht.

## 10. Ein `cd` im Bash-Werkzeug bindet nichts neu

```
{"tag": "B", … "command": "cd \"…\\cdrig\\dirA\" && echo bash-cd-test",
 "payload_cwd": "…\cdrig\dirB", …}
```

(`cdrig/hooklog-m2b.jsonl`, fünfte Zeile.) Weder Registrierung noch `cwd` der Sitzung folgen ihm.

## 11. Die Statuszeile folgt dem Ziel

Der Pfad rechts unten steht schon auf `dirB`, während der Trust-Dialog noch offen ist (`m2a.log`).
Die Agenten-Anzeige daneben bleibt `agent-a` — konsistent mit Befund 6.

## 12. Eine geänderte `settings.json` wird MITTEN in der Sitzung neu gelesen — ganz ohne `/cd`

Der überraschendste Befund der Runde, viermal in verschiedenen Verzeichnissen und Modi:

| Lauf | Wechsel der Datei | nächster Bash-Aufruf feuert | Modus |
|---|---|---|---|
| `cdrig/hooklog-m3.jsonl` | `A` → `A2` | `A2` | `bypassPermissions` |
| `cdrig/hooklog-m4.jsonl` | `B` → `B2` | `B2` | `bypassPermissions` |
| `cdrig/hooklog-m5.jsonl` | `A2` → `A` | `A` | Standardmodus, `--allowedTools Bash` |
| `cdrig/hooklog-m6.jsonl` | `A` → `A3` | `A3` | `bypassPermissions` |

Kein `/cd`, kein Neustart, kein Dialog. Und es ist nicht an eine Nutzer-Runde gebunden: im Lauf
`cdrig/hooklog-m11.jsonl` schreibt **die Sitzung selbst** die Datei im ersten Werkzeugaufruf und der
zweite Aufruf derselben Runde läuft bereits unter der neuen Registrierung:

```
{"tag": "REG-A", … "command": "cp \"…/settings-A2.json\" \"…/dirA/.claude/settings.json\""}
{"tag": "A2",    … "command": "echo mid-turn-probe"}
```

**Für dieses Repo heißt das:** der Satz „was beim Sitzungsstart bindet, ist die Registrierung" in
`CLAUDE.md` gilt so nicht mehr. Die Folge für den Schutzapparat steht als `H116` in
`docs/POST_V2_WISHLIST.md`; die Korrektur des Satzes selbst liegt außerhalb dieses Streams
(`CLAUDE.md` ist nicht sein Bereich) und ist als Nahtstelle gemeldet.

## 13. Eine neu hinzugefügte Rollendatei im AKTUELLEN Verzeichnis greift sofort

Im selben Lauf, in dem `agent:` unverändert blieb, wurde `prober-b.md` nach `dirA/.claude/agents/`
kopiert — und der Spawn lief (`cdrig/hooklog-m6.jsonl`, dritte Zeile, `"command": "echo PROBER-B-RAN"`).
Zusammen mit Befund 7: die Rollenliste wird **für das Startverzeichnis** nachgelesen, folgt aber
keinem `/cd`.

## 14. Die `agent:`-Zeile bindet auch im laufenden Verzeichnis nicht nach

**Erst falsch gemessen, dann richtig — die erste Fassung dieses Befundes war konfundiert.** Sie
stützte sich auf Lauf `m6`: dort wurde `dirA`s `settings.json` mitten in der Sitzung gegen eine
getauscht, die `agent: agent-b` sagt, und die Antwort blieb `token=AGENT-A`. Nur lag `agent-b.md`
zu keinem Zeitpunkt in `dirA` — „die Bindung wird nicht nachgelesen" und „der genannte Name löst
hier gar nicht auf" waren dieselbe Beobachtung, und der Befund konnte zwischen ihnen nicht
unterscheiden.

Nachgemessen ohne den Konfundierer (`reb1.log`, `reb1.jsonl`, Treiber `driver_rebind.py`, der
die Rollendatei **vor** dem Tausch hineinkopiert):

```
Runde 1 (settings A2, agent: agent-a)   → tag A2, echo REPORT-BINDING token=AGENT-A
   Tausch settings.json → A3 (agent: agent-b), agent-b.md liegt in dirA
Runde 2                                  → tag A3, echo REPORT-BINDING token=AGENT-A
```

Der Tag springt von `A2` auf `A3`, die Registrierung ist also nachgelesen; die Rolle `agent-b`
existiert in diesem Verzeichnis; die Antwort bleibt trotzdem `AGENT-A`. **Jetzt trägt der Satz:**
Registrierung und Rollenliste werden nachgelesen, die Sitzungsbindung nicht. Nebenbei ist damit
Befund 12 ein zweites Mal belegt, diesmal im headless-Transport statt in der Oberfläche.

## 15. VS-Code-Erweiterung: dasselbe Programm — aber ein anderer Transport, und dort gibt es `/cd` nicht

Die installierte Erweiterung `anthropic.claude-code-2.1.257-win32-x64` bringt ein eigenes Binary mit
(`resources/native-binary/claude.exe`, 208 MB, `--version` → 2.1.257). Ihr eigener Einstiegspunkt
`extension.js` — die Datei, die `package.json` als `main` nennt — sucht es über
`resources/native-binaries/<arch>/claude.exe` bzw. `resources/native-binary/claude.exe` und startet
es mit dieser Argumentliste, wörtlich aus dem Bündel:

```
["--output-format","stream-json","--verbose","--input-format","stream-json"]
```

Das sind die fünf Argumente des **gebündelten SDK**; die Erweiterung legt ihre eigenen `extraArgs`
darauf, nämlich `{debug:null,"debug-to-stderr":null,"enable-auth-status":null,"no-chrome":null,
"replay-user-messages":null}` (Offset 3052386), also fünf weitere Flags. Und die Umgebung baut sie
selbst, in `wQ($)` (Offset 3080381), wo der letzte Ausdruck lautet:

```
return Q.CLAUDE_CODE_ENTRYPOINT="claude-vscode", delete Q.CLAUDECODE, …
```

**unbedingt.** Die beiden `sdk-ts`-Zuweisungen desselben Bündels stehen beide hinter einem
Wächter — `if(!U.CLAUDE_CODE_ENTRYPOINT)` bei der einen, `if(!e0.CLAUDE_CODE_ENTRYPOINT)` bei der
anderen —, das ist der Vorgabewert des SDK, den das Panel nie erreicht. Alle drei Stellen sind
**Zeichen**-Offsets in der als UTF-8 gelesenen Datei (2229002, 2758314, 3080381 gegen
`wQ`); die Datei hat 3 181 619 Zeichen und 3 200 852 Bytes, als Byte-Offsets treffen die Zahlen also
nicht. Der erste Anlauf dieser Runde hat sie für die Zuweisung der Erweiterung gehalten und
das Rig mit `sdk-ts` gefahren.

Das ist **nicht** die interaktive Oberfläche, sondern genau der Transport aus Befund 1. Derselbe
Anlauf hatte das Binary außerdem durch eine ConPTY gefahren (`cdrig/hooklog-m9b.jsonl`) und daraus
„gilt auch in VS Code" geschlossen — gemessen war dabei ein Transport, den das Panel nie benutzt.

Nachgemessen mit dem Binary **und** der Argumentliste der Erweiterung (`ext1.log`, Treiber
`driver_ext.py`, Start in `dirA`):

```
Runde 1  Bash echo ext-turn-one     → läuft, Antwort beginnt mit AGENT-A
Runde 2  /cd …\cdrig\dirB           → "/cd isn't available in this environment."
Runde 3  Bash echo ext-turn-three   → init cwd = …\cdrig\dirA  (die Sitzung hat sich nicht bewegt)
```

Und die `slash_commands`-Liste des `init`-Ereignisses derselben Sitzung führt kein `cd`.

Ein zweites Mal mit der **vollständigen** Fläche gefahren — `CLAUDE_CODE_ENTRYPOINT=claude-vscode`
und alle fünf `extraArgs`-Flags dazu (`ext4-fullargs.log`) — kommen dieselben drei Zeilen heraus:
Runde 2 wieder „/cd isn't available in this environment.", Runde 3 wieder `init cwd` = `dirA`. Was
sich zwischen den beiden Läufen unterscheidet, ist nur der Bindungs-Token (`AGENT-A` gegen
`AGENT-B`), und das ist eine Nebenwirkung des Rigs: `dirA`s `settings.json` stand beim zweiten Lauf
schon auf der Fassung aus Befund 14. Genau das zeigt aber die andere Hälfte — die `agent:`-Bindung
aus `settings.json` greift in diesem Transport sehr wohl, nur `/cd` gibt es nicht.

## 16. Der Wechsel, den das Panel wirklich hat, heißt `set_cwd` — und er löst dieselben Löcher aus

`extension.js` trägt statt eines `/cd` eine **Steuer-Anfrage** über denselben stdin-Kanal:
`setCwd(pfad,{trustAccepted,trustedDirectory})` schickt
`{subtype:"set_cwd",path,trust_accepted,trusted_directory}` in der Hülle
`{request_id,type:"control_request",request:{…}}`. Die Zeichenkette `/cd` steht im Bündel
**14** mal — alle 14 in einer MIME-Typ-Tabelle (`application/cdfx+xml`, `application/cdmi-*`,
`application/cdni`); **als Kommandoname kommt sie nicht vor**. Was den Befund trägt, ist ohnehin
nicht die Abwesenheit einer Zeichenkette, sondern die `slash_commands`-Liste des `init`-Ereignisses
und die Antwort auf den Versuch (`ext1.log`, `ext4-fullargs.log`).

Genau diese Hülle gesendet (`ext3.log`, `ext3.jsonl`, Treiber `driver_setcwd2.py`), Start in
`dirA`, Ziel `dirB`:

```
control_response: {"status":"ok","cwd":"…\cdrig\dirB","changed":true,"transcript_relocated":true}
danach:  {"tag":"REG-B", "script_home":"SCRIPT-A",
          "script_path":"…\dirA\.claude\hooks\log_hook.py",
          "payload_cwd":"…\cdrig\dirB", "env_CLAUDE_PROJECT_DIR":"…/cdrig/dirA"}
          "command": "echo REPORT-BINDING token=AGENT-A"
```

Drei Dinge auf einmal, alle in einer Zeile: die Registrierung des **Ziels** feuert, die Hook-**Datei**
des **Starts** läuft (`H114` reproduziert), `CLAUDE_PROJECT_DIR` bleibt am Start (Befund 4), und die
`agent:`-Bindung bleibt `AGENT-A` (`H115` reproduziert).

**Ohne jeden Dialog.** Der erste Versuch mit `trust_accepted:true` und ohne `trusted_directory` kam
als Fehler zurück — wörtlich: `set_cwd: invalid request — trust_accepted requires trusted_directory
(echo the directory from the needs_trust response)` (`ext2.log`) —, also gibt es einen zweistufigen
Vertrauens-Handschlag für **unbekannte** Verzeichnisse. Für `dirB`, das in dieser Runde früher
einmal von Hand bestätigt worden war, brauchte es ihn nicht: der Aufruf **ohne** jedes Vertrauensfeld
antwortete sofort mit `status: ok, changed: true`.

**Was hier nicht gemessen ist und darum nicht behauptet wird:** wodurch die Erweiterung `setCwd`
auslöst. Dass sie es kann und dass das Binary es annimmt, ist gemessen; ob im Panel ein Klick, ein
Arbeitsbereichswechsel oder gar nichts davor steht, ist es nicht.

## 17. Ein `--continue` (Fortsetzen) bindet den `agent:` — der Neustart muss kein kalter sein

Punkt 7 des Messplans. Ausgangslage nach Befund 14: `dirA` trägt `settings.json` mit
`agent: agent-b`, `agent-b.md` liegt darin, und die **laufende** Sitzung antwortet weiter als
`AGENT-A`. Dieselbe Sitzung mit `--continue` fortgesetzt (`reb2-resume.log`,
`reb2-resume.jsonl`):

```
{"tag": "A3", … "command": "echo REPORT-BINDING token=AGENT-B", …}
```

Dass es wirklich eine Fortsetzung war und kein Neustart: die `session_id` der Vorsitzung
(`6a9d6106-1cda-4145-95fc-8af3459b3301`) steht im Strom der neuen.

**Folge für die Zeremonie der Kits:** Die Bitte um einen Neustart bleibt richtig (Befund 6/14 — die
laufende Sitzung bindet nicht nach), aber „Fenster schließen und neu öffnen" ist nicht die einzige
Erfüllung; ein Fortsetzen derselben Unterhaltung genügt für die `agent:`-Zeile ebenfalls. Ob der
Wortlaut der Zeremonie das aufnehmen soll, ist eine Entscheidung außerhalb dieses Streams und als
Nahtstelle gemeldet.

## Antworten auf die beiden Nutzerfragen

### „Welche Zeile tippe ich, damit diese Sitzung die neue Hook-Registrierung liest?"

**Nach Befund 12: gar keine.** Eine geänderte `.claude/settings.json` wirkt in der laufenden Sitzung
ab dem nächsten Werkzeugaufruf. Dass die Hook-**Dateien** ohnehin schon bei jedem Aufruf frisch
gelesen werden, steht seit `H12` fest (dort gemessen, in dieser Runde nicht nachgemessen); neu ist,
dass auch die **Registrierung** nachgelesen wird.

Wer es trotzdem erzwingen will (oder eine ältere Client-Version fährt), fährt einen Rundlauf —
zwei Zeilen, jede mit Enter, und falls der Dialog aus Befund 2 erscheint, mit Pfeil-runter auf
**„Yes, move here"** und Enter bestätigt:

```
/cd C:\Offline Repos\v2-testbed
/cd C:\Offline Repos\AgentAndSkills
```

**Drei Einschränkungen, alle gemessen.** Erstens: Das ist nur unbedenklich, wenn die Sitzung im
Repo **gestartet** wurde — `${CLAUDE_PROJECT_DIR}` bleibt am Startort (Befund 4), und die Gates
dieses Repos buchstabieren ihre Kommandozeilen genau damit (Befund 5). Eine Sitzung, die anderswo
startet und ins Repo hinein-`/cd`t, lässt die Hook-Dateien des Startorts urteilen. Zweitens: Was ein
`/cd` **nicht** bringt, ist die `agent:`-Bindung (Befund 6) — wer den Sitzungsagenten wechseln will,
startet die Sitzung neu **oder setzt sie fort**; beides bindet, gemessen in Befund 17.

Drittens, und das trifft genau die beiden Zeilen oben: `C:\Offline Repos\v2-testbed` trägt kein
`.claude/`. Nach Befund 3 tauscht ein `/cd` die Registrierung aus, also ist zwischen der ersten und
der zweiten Zeile **kein einziges** der vier Gates dieses Repos registriert. Wer den Rundlauf fährt,
arbeitet in dieser Spanne ungeschützt; ein Zwischenziel, das selbst eine `.claude/settings.json`
hat, vermeidet das.

Die beiden Zeilen gelten nur in der **interaktiven Oberfläche im Terminal**. Im Panel der
VS-Code-Erweiterung gibt es sie nicht (Befund 15).

### „Geht das auch über die VS Code Extension, Claude Desktop oder nur im CLI?"

Drei Antworten, jede mit ihrer Messung oder mit dem Grund, warum keine da ist.

* **CLI (Terminal): ja, gemessen.** Die interaktive Oberfläche kennt `/cd`, führt den Wechsel aus
  und zeigt vorher den Dialog aus Befund 2 (Befunde 2, 3, 8, 9, 11). Die Zeile, die man tippt, steht
  oben.
* **VS-Code-Erweiterung: `/cd` gibt es dort NICHT — gemessen, und in der Runde vorher stand hier das
  Gegenteil.** Das Panel startet zwar dasselbe Programm, aber im `stream-json`-Transport, und der
  antwortet auf `/cd` mit „isn't available in this environment" und führt `cd` nicht in seiner
  Kommandoliste (Befund 15, `ext1.log`). **Der Wechsel selbst existiert dort trotzdem** — als
  Steuer-Anfrage `set_cwd`, die die Erweiterung selbst schickt und die dieselben zwei Löcher auslöst
  wie ein `/cd` (Befund 16, `ext3.log`). Für den Nutzer heißt das: in VS Code gibt es keine Zeile
  zum Tippen, und wenn das Panel den Ordner wechselt, wandern die Hook-**Dateien** trotzdem nicht mit.
  **Einen Weg zum CLI gibt es aus VS Code heraus trotzdem:** die Erweiterung trägt in ihrer
  `package.json` das Kommando `claude-vscode.terminal.open` mit dem Titel „Claude Code: Open in
  Terminal" bei — das öffnet ein Terminal mit dem CLI, und dort gilt die CLI-Zeile oben. **Gelesen,
  nicht durchgefahren:** das Manifest ist gemessen, das geöffnete Terminal nicht.
  **Nicht gemessen bleibt** die Chat-Eingabe des Panels selbst (ein Webview, das sich nicht skripten
  ließ) — also ob die Erweiterung ein eigenes, clientseitiges `/cd` anbietet, dessen Name im Bündel
  nicht als Kommando steht. Gemessen ist das Programm dahinter und der Kanal, über den es bewegt
  wird.
* **Claude-Desktop-App: ungemessen, weil auf diesem Host nicht installiert.** Weder
  `%LOCALAPPDATA%\AnthropicClaude` noch `%APPDATA%\Claude` noch `%LOCALAPPDATA%\Programs\Claude`
  existieren (nachgesehen 2026-09-02). Sie ist ein anderes Programm als Claude Code; diese Runde
  behauptet über sie **nichts** — weder dass `/cd` dort existiert noch dass es fehlt.

## Protokoll für den Nutzer: was diese Runde nicht messen konnte

**A. Die Chat-Eingabe der VS-Code-Erweiterung (ca. 20 Sekunden).** Nach Befund 15 ist die erwartete
Antwort „`cd` steht nicht in der Liste"; die zwanzig Sekunden prüfen, ob das Panel doch etwas
Eigenes anbietet.

1. VS Code im Repo öffnen, das Claude-Code-Panel öffnen.
2. In die Eingabezeile `/` tippen und die Vorschlagsliste ansehen: steht **`cd`** darin?
3. Falls ja (also entgegen der Messung): `/cd C:\Offline Repos\v2-testbed`, Enter — passiert etwas,
   und erscheint dabei ein Dialog?
4. Ergebnis (Liste ja/nein, Dialog ja/nein) an den Lead; er hängt es an `FR-0059`.

**B. Die Claude-Desktop-App**, falls sie irgendwann installiert ist: dieselben drei Schritte. Solange
sie nicht installiert ist, bleibt die Frage offen und wird nicht geraten.

## Offen / nicht gemessen

* Ob `/cd` die **SessionStart**-Hooks des Zielverzeichnisses auslöst (im Rig war keiner registriert).
* Ob nach `/cd` ein **Freigabedialog** für MCP-Server unter anderen Berechtigungsmodi erscheint —
  Befund 9 hält nur fest, dass in diesem Lauf keiner zu sehen war.
* Ob die Registrierung aus Befund 12 bei **jedem** Werkzeugaufruf oder nur an bestimmten Punkten neu
  gelesen wird; gemessen ist die kürzeste beobachtete Frist: der nächste Aufruf derselben Runde.
* Das Verhalten unterhalb der Client-Version dieses Hosts. Alles hier ist an 2.1.258 bzw. 2.1.257
  gemessen; für ältere Clients gilt die Recherche, nicht diese Messung.
* **Wodurch die VS-Code-Erweiterung `setCwd` auslöst** (Befund 16). Gemessen ist, dass sie es kann
  und dass das Binary es ausführt; was im Panel davor steht, nicht.
* **Ob eine Haken-Datei oder ein MCP-Server `set_cwd` schicken kann.** Der Kanal ist stdin des
  Client-Prozesses, den weder Hook noch Werkzeug beschreiben — nachgemessen ist das nicht, und der
  Punkt „programmatische Trigger jenseits des Modells" aus der Recherche bleibt damit offen.
* **Der zweistufige Vertrauens-Handschlag von `set_cwd` an einem wirklich unbekannten Verzeichnis.**
  Gemessen ist nur die Fehlermeldung, die ihn beschreibt (`ext2.log`), und der Weg ohne ihn an einem
  bereits vertrauten Ziel.
* Ob die Chat-Eingabe der VS-Code-Erweiterung ein eigenes, clientseitiges `/cd` anbietet. Als
  Kommandoname steht es im Bündel nicht (die 14 Vorkommen der Zeichenkette sind eine MIME-Tabelle);
  das Webview selbst ließ sich nicht skripten.
