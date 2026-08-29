# TSK-0087 / FR-0035 — Vier-Augen-Ablage mechanisch: Messungen

Alles hier ist gegen ein **scaffoldetes Office-Projekt ausserhalb des Repos** gemessen
(`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0087\probe`), installiert über
`scaffold_team.ps1` aus einer Kopie von `team-kits/` in einem eigenen `USERPROFILE`. „Kette" heisst
immer: jeder Hook, den `.claude/settings.json` des Projekts für dieses Ereignis und diesen
Tool-Namen registriert, als echter Prozess, Payload auf stdin, in der Reihenfolge der Datei.
Kit-Stand der Endmessungen: `office-team 2026.08.28-11`.

## 1. Die Lücke, vorher — reproduziert

Kit-Stand `2026.08.28-4` (der ausgelieferte Stand vor dieser Runde), Aktenplan mit zwei Regeln,
`inbox/scan_0001.pdf` vorhanden, **kein** Review-Datensatz irgendwo:

| Aufruf | Kette | Ergebnis |
|---|---|---|
| `mv inbox/scan_0001.pdf archive/finance/incoming_invoices/2026/2026-01-15_ACME_invoice.pdf` | 6 Bash-Hooks | **rc 0** (guard_fs_tripwire 0, gate_ledger_valid 0, gate_write_scope 0, gate_push_token 0, gate_shell_hygiene 0, gate_filing 0) |
| `Write` nach `archive/finance/incoming_invoices/2026/2026-02-02_BETA_invoice.md` | 6 Write-Hooks | **rc 0** |
| Kontrolle: `mv … archive/erfunden/…` | 6 Bash-Hooks | **rc 2** (`gate_filing`: „no rule in filing_plan.yaml covers archive/erfunden") |

Das ist die Messung des Prüfers vom 2026-08-25, unabhängig nachvollzogen. Die Wand stand, und sie
beantwortete eine andere Frage.

## 2. Die Kostenzahl — für den Nutzer

> **Die erste Fassung dieser Tabelle ist ÜBERHOLT und steht unten nur noch als Fehler.** Sie maß
> die Dateien, die diese Runde selbst vergrößert hat, in ihrem Zustand VOR der Runde, und für den
> Aktenplan einen Wert (577 B), den ein installiertes Projekt nie hat — das ist der Zwei-Regel-Plan
> des Messprojekts, nicht der ausgelieferte. Gültig ist die Tabelle darunter, gemessen gegen ein
> **frisch scaffoldetes Projekt auf dem Endstand** (`office-team 2026.08.29-2`). Der Prüfer hat
> denselben Fehler unabhängig gefunden; die Zahlen stimmen im Rahmen des Aktenplan-Unterschieds
> überein.

Die Policy-Frage aus FR-0035 („zwei Läufe für jedes Dokument, oder nur für die Klassen, die der
Plan markiert") gehört dem Nutzer. Was gemessen werden konnte, und was nicht:

**GÜLTIG — der feste Kontext, den ein zweiter Lauf laden muss** (Bytes exakt, aus dem
**installierten** Projekt nach der Runde; Token als Bytes/4, weil offline kein Tokenizer verfügbar
ist — das ist eine Näherung, keine Zählung):

| Datei | Bytes | ≈ Token |
|---|---:|---:|
| `.claude/agents/filing-reviewer.md` | 3 491 | 872 |
| `.claude/skills/filing-reviewer/SKILL.md` | 6 515 | 1 628 |
| `project_memory/business_profile.yaml` | 5 586 | 1 396 |
| **feste Summe** | **15 592** | **≈ 3 898** |
| `project_memory/filing_plan.yaml` — variabel | 577 … 4 684 | 144 … 1 171 |
| **Summe ohne Verfassung** | **16 169 … 20 276** | **≈ 4 042 … 5 069** |
| `AGENTS.md` (die Verfassung) | 35 922 | 8 980 |
| **Summe mit Verfassung** | **52 091 … 56 198** | **≈ 13 022 … 14 049** |

Der Aktenplan ist die einzige variable Größe: 577 B ist der Zwei-Regel-Plan des Messprojekts,
4 684 B der Plan, wie das Kit ihn ausliefert (Kopfkommentar plus Beispiele, den ein frisches
Projekt als Ausgangspunkt hat); der Prüfer maß an seinem gefüllten Plan 5 073 B, was am oberen Ende
dieser Spanne liegt. Ob ein Subagent die Verfassung mitlädt, ist **nicht gemessen** — dafür bräuchte
es einen echten Provider-Lauf, den ein Hook-Rig nicht erzeugen kann. Deshalb stehen beide Grenzen da.

**ÜBERHOLT (Stand vor der Runde, hier nur zur Nachvollziehbarkeit):** `filing-reviewer.md` 2 902,
`SKILL.md` 5 193, `filing_plan.yaml` 577, `business_profile.yaml` 5 586 → 14 258 B ≈ 3 560 Token;
mit `AGENTS.md` 34 570 → 48 828 B ≈ 12 210 Token.

**Die entscheidende Eigenschaft für die Kostenfrage**, und sie ist gemessen: der feste Kontext fällt
**pro LAUF an, nicht pro Dokument**. Ein `filing_reading`-Datensatz trägt eine Liste; ein Lauf kann
einen ganzen Posteingang in einem Datensatz klassifizieren. Gemessen in Fall N unten: ein Datensatz
mit drei Einträgen je Lauf gibt alle drei Ablagen frei. „Zwei Läufe pro Dokument" ist also in der
Praxis „ein zusätzlicher Lauf pro Sweep", solange der Manager den zweiten Leser gebündelt schickt.
Pro Dokument kommen nur der Dokumententext und ~50–80 Token Ausgabe dazu.

**Nicht gemessen:** die Wanduhrzeit eines Modelllaufs. Aus einem Hook-Rig heraus ist sie nicht
erzeugbar, und eine geschätzte Zahl wäre in diesem Bericht eine erfundene.

**Gemessen — was der Mechanismus selbst kostet** (Median aus 7 Läufen, echte Prozesse, zwei
unabhängige Durchgänge; der Prozessboden desselben Rechners steht als Referenz dabei):

| | Lauf 1 | Lauf 2 |
|---|---:|---:|
| `_gate.py`-Boden (ein Hook, der sofort beendet) | 80 ms | 81 ms |
| `gate_filing` allein (Stand wie ausgeliefert) | 127 ms | 126 ms |
| `gate_filing` + `gate_second_reading` (eine Registrierung, ein Prozess) | 201 ms | 192 ms |
| → **Aufschlag pro geprüftem Tool-Aufruf** | **+74 ms** | **+66 ms** |
| `record_filing_reading`, Aufruf schreibt keine Zustandsdatei (Normalfall) | 102 ms | 109 ms |
| `record_filing_reading`, Aufruf schreibt einen Lesungsdatensatz | 199 ms | 192 ms |

Nach der Nacharbeit (2026-08-29, Endstand, derselbe Rechner, Boden 83 ms): `gate_filing` allein
132 ms, beide zusammen 205 ms — **+73 ms**, was die unabhängige Messung des Prüfers (+71 ms)
bestätigt. Der Aufzeichner kostet 112 ms im Normalfall und 256 ms, wenn er einen Datensatz UND das
darin genannte Dokument hasht.

Die ganze Bash-Kette liegt bei ~0,70 s statt ~0,57 s. Der Normalfall des Aufzeichners kostet nur
~25 ms über dem Prozessboden, weil er die Pfade aus der Payload zuerst liest und bei „nichts unter
`project_memory/` geschrieben" vor dem Kernel-Import aussteigt.

## 3. Die Lücke, nachher — dieselbe Kette

`S.reset()` löscht vor jedem Fall Staging und Attestierungs-Store. Jeder Lesungsdatensatz wird
geschrieben **und dann über die echte PostToolUse-Kette attestiert**, mit dem `agent_id` des Laufs.

| Fall | Kette | Wer verweigert |
|---|---|---|
| A: Move, gar keine Lesung | rc 2 | `gate_second_reading` — „holds 0 that name it", „No attested reading names this document at all" |
| B: nur EINE attestierte Lesung | rc 2 | „holds 1 that name it" |
| C: zwei Lesungen, **derselbe** Lauf | rc 2 | „2 classification readings name …, and the attestations put all of them on ONE run (agent_A)" |
| D: zwei Lesungen, zwei Läufe, **einig** | **rc 0** | — |
| E: zwei Läufe, **uneinig** | rc 2 | beide Lesungen nebeneinander benannt (siehe unten) |
| F: direkter `Write` ins gedeckte Archiv | rc 2 | `gate_second_reading` — **auch mit zwei einigen Lesungen** (Nacharbeit B2: eine Landung ohne Dokument dahinter wird verweigert, nicht gegen fremde Lesungen geprüft) |
| G1: Ziel ausserhalb `archive/` | rc 0 | — |
| G2: Umsortieren **innerhalb** des Archivs, gleiche Regel + **anderer** Name | rc 2 | `gate_second_reading` (Nacharbeit B1 — vorher rc 0) |
| G2b: gleiche Regel UND gleicher Name | rc 0 | — |
| G3: Ziel, das keine Regel deckt | rc 2 | `gate_filing` (nicht `gate_second_reading`) |
| H: attestierten Datensatz nachträglich editiert | rc 2 | Attestierung gilt für die BYTES, nicht für den Pfad |
| L: zweiter Datensatz da, aber nie attestiert (Shell-Schreibweg) | rc 2 | benannter Rest, fällt sicher |

Der Text im Uneinigkeitsfall (E), vollständig:

```
[team-kit gate_second_reading] archive/finance/incoming_invoices/2026/2026-01-15_ACME_invoice.pdf
needs 2 independent classification readings before it is filed and the project holds 1 that name it.
The document is not moved and not renamed. The filing plan asks for the second reading here
(rule FP-001: no `second_reading: false`).
Recorded for this document:
  inbox/scan_0001.pdf -> …/2026-01-15_ACME_invoice.pdf (Eingangsrechnung ACME; run agent_A, staging/TSK-0001/reading_clerk.yaml)
  inbox/scan_0001.pdf -> …/2026-01-15_BETA_invoice.pdf (Eingangsrechnung BETA;  run agent_B, staging/TSK-0001/reading_second.yaml)
```

## 4. Die Policy sitzt im Plan, nicht im Hook

Dieselbe Bewegung, vier Zustände desselben Regelfelds:

| `second_reading` in der deckenden Regel | Kette |
|---|---|
| Feld fehlt | rc 2 (verlangt) |
| `false` | **rc 0** (freigegeben) |
| `true` | rc 2 |
| `"nein"` (ein Wort, das YAML nicht als false liest) | rc 2 |

Nur der Wert, den YAML selbst als Boolean `false` liest, gibt frei. Die Schreibweisen kommen damit
von PyYAML und stehen nirgends im Hook als Liste.

## 5. Unabhängigkeit: was gemessen wird und was nicht

Gemessen wird **Provenienz**: `record_filing_reading` schreibt pro Datensatz eine Zeile
`{record, sha256, run}` nach `project_memory/.filing/readings.jsonl`, wobei `run` das `agent_id`
aus der Payload des schreibenden Aufrufs ist — ein Feld, das der Provider füllt. Zwei Lesungen
zählen als unabhängig, wenn ihre Attestierungen zwei verschiedene Läufe nennen.

Der Store ist gegen den Agenten geschützt, gemessen über die volle Kette:

| Angriff | Kette |
|---|---|
| `Write` nach `project_memory/.filing/readings.jsonl` | rc 2, `gate_write_scope` |
| `echo x >> project_memory/.filing/readings.jsonl` | rc 2, `gate_write_scope` |
| `cd project_memory && echo x >> .filing/readings.jsonl` | rc 2, `gate_write_scope` |

**Was der Check NICHT sieht**, und keine Meldung behauptet etwas anderes: ob der zweite Lauf den
ersten Datensatz gelesen hat. Nichts in der Hook-Schicht beobachtet einen Read, die Datensätze
liegen in `staging/`, wo jede Rolle nachsehen darf, und der Store selbst ist lesbar. Gemessen wird
„zwei Läufe", nicht „zwei Aufmerksamkeiten".

**Die eine unbelegte Annahme, mit ihrer Richtung**: `tools/provider_observations.json` →
`agent_identity` hält fest, dass ein Subagent über seine eigenen Aufrufe hinweg dasselbe `agent_id`
trägt; ob **zwei Spawns derselben Rolle** zwei verschiedene Ids bekommen, ist dort nicht
festgehalten. Würde ein Provider eine Id wiederverwenden, läsen sich zwei echte Lesungen als ein
Lauf und die Ablage würde **verweigert** — die Über-Verweigerung. Die gefährliche Richtung
verlangte, dass ein Lauf zwei Ids bekommt, und das ist das Gegenteil des Gemessenen.

**Weitere benannte Reste** (Stand nach der Nacharbeit vom 2026-08-29):
- Ein Inbox-Dokument kann weiterhin ÜBERSCHRIEBEN werden — gemessen rc 0 auf drei Wegen. Was
  geschlossen ist, ist die Folge: die Lesungen decken das getauschte Dokument nicht mehr. Dass das
  Überschreiben selbst durchgeht, ist eine Eigenschaft von `guard_fs_tripwire` (Löschen ja,
  Überschreiben nein) und bleibt offen.
- Ein Dokument über `_readings.MAX_DOCUMENT_BYTES` (64 MB) bekommt keinen Stempel; seine Ablage
  wird verweigert statt ungebunden zugelassen. Über-Verweigerung, benannt.
- Ein Wort, dessen Position zwei existierende Dateien treffen kann, verlangt die Lesungen für
  beide. Über-Verweigerung, benannt (B2e).
- Ein `Write` oder ein Redirect direkt ins Archiv wird jetzt **immer** verweigert, auch mit
  passenden Lesungen: eine Ablage in diesem Kit VERSCHIEBT ein Dokument (§2.5). Wer Inhalt im
  Archiv braucht, der nie in einem Fach lag, muss das dem Nutzer vorlegen.
- Die Eintritts-Ausnahme vergleicht Regel und Dateinamen, **nicht** den Ordner: eine Bewegung, die
  nur den Wert eines Platzhalters ändert (`…/2026/x.pdf` → `…/2027/x.pdf`), bleibt ausgenommen,
  obwohl der Jahreswert klassifiziert — und kann dabei ein anderes, doppelt gelesenes Dokument
  überschreiben, ohne dass die Byte-Bindung läuft. Offen, im Code und in `ENFORCEMENT.md` benannt.
  Naheliegender Verschluss für eine Folgerunde, hier nicht gebaut: die Ausnahme zusätzlich am
  aufgelösten VERZEICHNIS festmachen, nicht nur am `path_template`.
- Der Aufzeichner attestiert nur die Pfade, die **dieser Aufruf nennt** — gelesen über dieselben
  zwei Leser, die auch die Ablagewand benutzt (`_compat.file_paths`, `_filing.created`). Ein
  Datensatz, der **innerhalb eines anderen Programms** entsteht (`python -c "open(...).write(...)"`,
  ein Skript), bekommt daher gar keinen Stempel, ist keine Lesung und verweigert die Ablage.
  Gemessen als Fall L. Derselbe Rest wie bei `gate_filing`, mit demselben Leser.
- Ein Schreibvorgang **innerhalb eines anderen Programms** (`python -c "shutil.move(...)"`) nennt
  auch kein Ablageziel, das dieser Leser sieht — ebenfalls der Rest, den `gate_filing` schon hat.
- Eine Befehlszeile, die den Store-Pfad **nirgends nennt** (ein Glob, ein Skript), wird hier von
  nichts verweigert — dieselbe Grenze, die `kit_state.json` hat.
- Der Lead (kein `agent_id`) ist EIN Lauf. Schreibt ein Spezialist die erste und der Lead die
  zweite Lesung, gilt das als zwei Läufe, obwohl der Lead den Bericht des Spezialisten gesehen hat.

## 6. Ein Defekt im ersten Wurf dieser Runde, gemessen und behoben

`mv inbox/scan_0001.pdf archive/finance/incoming_invoices/2026/` (Ziel ist ein VERZEICHNIS, es
wird also gar kein neuer Name vergeben) kam als Landung `…/2026` heraus, deren Elternebene keine
Regel deckt — das Gate stand ab und die Ablage lief mit **rc 0** durch, während beide Lesungen
einen anderen Namen nannten. Ursache: `_move` setzt sein `destination_is_directory` nur dort, wo
die Aufrufkonvention es sagt; der einfache letzte Operand ist immer `False`. `_filing.landings`
liest den Token jetzt zusätzlich über `names_a_directory`, genauso wie `created` es tut. Nach der
Korrektur: rc 2 auf `…/2026/scan_0001.pdf`, und rc 0, sobald beide Lesungen genau diesen Namen
nennen. Test: `test_a_move_into_a_folder_is_judged_on_the_name_the_document_keeps`.

## 6b. Ein zweiter Defekt im ersten Wurf: Fehlzuordnung im Aufzeichner

Der erste Wurf von `record_filing_reading` stempelte **jeden** noch nicht attestierten Datensatz,
den er im Staging FAND, auf den Aufrufer des gerade laufenden Tool-Aufrufs. Damit wird ein
Datensatz, dessen eigenes PostToolUse nie lief, dem **nächsten** Lauf zugeschrieben, der
irgendetwas tut — und zwei Datensätze desselben Registrators lesen sich dann als zwei Läufe. Der
Aufzeichner liest die Pfade jetzt aus der Payload (`named_by_this_call`, über dieselben zwei Leser
wie die Ablagewand) und attestiert nur, was dieser Aufruf benennt. Mutation im Klon: rc 0 statt
rc 2, gefangen von `test_a_record_this_call_did_not_write_is_not_attested_to_this_run`.

## 7. Ein Defekt im ersten Wurf eines TESTS dieser Runde

`test_an_agent_cannot_write_the_attestation_store_through_the_registered_chain` tippte den Pfad
`project_memory/.filing/readings.jsonl` in seine eigene Befehlszeile. Die Mutation „Store liegt in
`staging/`, wo jeder Spezialist schreiben darf" blieb damit **GRÜN** (2 passed). Der Test fragt den
Ort jetzt bei `_readings.store_path` ab — dem Code, der ihn zusammensetzt. Danach: RED.

## 8. Rot-ohne-Fix: neun Mutationen in einem Klon ausserhalb des Repos

Klon unter `…\_round-scratch\TSK-0087\mutants\` (grün vor jeder Mutation), Defekt eingesetzt, die
benannten Tests gefahren, Datei zurückgeschrieben.

| Wiederhergestellter Defekt | Ergebnis | Gefangen von |
|---|---|---|
| Gate gar nicht registriert | RED (3 failed) | `test_a_filing_with_no_independent_reading_is_refused_through_the_registered_chain`, `test_two_readings_from_one_run_are_not_two_readings`, `test_two_readings_that_disagree_refuse_the_move_and_name_both` |
| Recorder nicht registriert → nichts attestiert | RED (1 failed) | `test_two_independent_readings_that_agree_let_the_filing_through` |
| Policy-Default „nicht verlangt" | RED (2 failed) | `test_a_plan_rule_can_release_its_own_class_from_the_second_reading`, `test_a_filing_with_no_independent_reading_is_refused_through_the_registered_chain` |
| Unabhängigkeit zählt DATENSÄTZE statt LÄUFE | RED (1 failed) | `test_two_readings_from_one_run_are_not_two_readings` |
| Verzeichnis-Ziel wird nicht mit dem behaltenen Namen vervollständigt | RED (1 failed) | `test_a_move_into_a_folder_is_judged_on_the_name_the_document_keeps` |
| Attestierung am PFAD statt an den BYTES | RED (1 failed) | `test_an_edit_after_the_attestation_takes_the_reading_back` |
| Verweigerung joint nur über das Ziel → die andere Lesung wird nie genannt | RED (1 failed) | `test_two_readings_that_disagree_refuse_the_move_and_name_both` |
| Store liegt in `staging/` | RED (2 failed) | `test_an_agent_cannot_write_the_attestation_store_through_the_registered_chain` |
| Ein nicht attestierter Datensatz zählt als Lesung | RED (1 failed) | `test_an_unattested_record_is_not_a_reading` |
| Aufzeichner stempelt alles, was er findet, statt nur was dieser Aufruf nennt | RED (1 failed) | `test_a_record_this_call_did_not_write_is_not_attested_to_this_run` |

## 8b. Zwei bestehende Tests, die die neue Registrierung als falsch gelesen hätten

`tools/test_hooks_v2.py` unterstellte an zwei Stellen, ein Ereignis trage höchstens EINE
Mehr-Gate-Kette. Das Office-Kit hat jetzt zwei PreToolUse-Ketten (Spawn und Ablage) auf disjunkten
Matchern.

- `_multi_gate_chains` gibt den **Matcher** mit zurück; `_CHAIN_PAYLOADS` ist nach
  `(Ereignis, Tool)` verschlüsselt, und welche Payload eine Kette bekommt, entscheidet ihr eigener
  Matcher (`_payload_for`) statt einer Liste.
- `test_no_gate_that_mutates_the_state_runs_in_front_of_one_that_can_still_refuse` hatte pro Kette
  `assert mutating` als Kontrolle. Für eine Kette aus reinen Richtern verlangt das eine Mutation,
  die es nicht geben darf. Die Kontrolle ist jetzt zweigeteilt: **pro Kette** muss die Kette ihre
  Payload akzeptieren (das beweist, dass jedes Gate seinen Entscheidungspfad erreicht hat), **pro
  Kit** muss irgendein Gate mutiert haben (das beweist, dass der Apparat eine Mutation überhaupt
  noch erkennt).
- Dabei fiel auf, dass die alte Spawn-Fixture des Office-Kits die eigene Kette gar nicht passierte:
  gemessen verweigerte `gate_proc_approved` genau diese Payload mit „this project has no approved
  procedure at all", während `gate_dispatch` — allein gefahren — die Lease trotzdem nahm. Die
  Fixture mintet jetzt einen freigegebenen `PROC` und nennt ihn im Arbeitsauftrag; damit stimmt
  zum ersten Mal, was der Docstring seit jeher behauptete.

## 8c. Nacharbeit 2026-08-29: vier Blocker des Prüfers, nachgemessen und geschlossen

Alle vier zuerst gegen den Stand `2026.08.28-11` REPRODUZIERT, dann gegen `2026.08.29-2` erneut
gefahren — dieselben Befehlszeilen, dieselbe volle Kette.

| Angriff (volle Kette, scaffoldetes Projekt) | vorher | nachher |
|---|---|---|
| **B1** ehrliche Ablage mit zwei Lesungen | rc 0 | rc 0 |
| **B1** danach: dasselbe Dokument in eine andere Regel, anderer Name | **rc 0** | **rc 2** |
| **B1** danach: zurück in die eigene Regel unter `2099-12-31_FORGED_invoice.pdf` | **rc 0** | **rc 2** |
| **B2** ein ANDERES Dokument auf dasselbe Ziel | **rc 0** | **rc 2** |
| **B2** `echo forged >` auf dasselbe Ziel | **rc 0** | **rc 2** |
| **B2** direkter `Write` auf dasselbe Ziel | **rc 0** | **rc 2** |
| **B3** `ARCHIVE/…` und `Archive/…` (NTFS faltet) | **rc 0** | **rc 2** |
| **R1** `NotebookEdit` in einen gedeckten Pfad | **rc 0** | **rc 2** |

**B1 — was ein EINTRITT ist.** `entering` fragte nur, ob die Quelle im Archiv liegt; damit war das
Archiv nach der ersten ehrlichen Ablage ein freier Namensraum. Neu (`gate_second_reading.an_entry`):
Eintritt ist alles außer der einen Bewegung, bei der nichts klassifiziert wurde — gleiche Regel UND
gleicher Dateiname. Der falsche Zeiger auf `guard_fs_tripwire` ist an allen drei Stellen weg
(Gate-Kopf, `ENFORCEMENT.md`-Zeile, der Test, der das Loch als Absicht festschrieb); der Grund
steht jetzt dort: dieser Guard erlaubt archivinterne Bewegungen absichtlich, sein Kopfkommentar
hält die Messung von 2026-08-03 fest, die das Verweigern zum Defekt erklärte.

**B1b — der Nebenbefund, den der Prüfer als „wash-through" beschrieb, und die Korrektur dahinter.**
`second_reading: false` hieß im ersten Wurf „gar keine Lesung". Damit war jede freigegebene Klasse
ein Ordner, in den jedes Dokument ungelesen umbenannt werden konnte. Die Frage des Nutzers lautete
aber „zwei Läufe oder einer", nie „zwei oder keiner". Neu (`readings_required`): eine Freigabe
verlangt **eine** Lesung und nie keine; wo zwei Regeln einen Ort decken, gewinnt die höhere
Forderung.

**B2 — die Lesung deckt ein DOKUMENT, keinen Zielpfad.** Verglichen wurde nur `destination`.
Jetzt: eine Lesung zählt nur, wenn sie THIS document als `source` UND diesen Pfad als `destination`
nennt; eine Landung ohne Dokument dahinter (Redirect, Tool-Write, unauflösbare Quelle) wird
ausdrücklich verweigert statt gegen fremde Lesungen geprüft.

**B2c — und die Kette, die dabei sichtbar wurde.** Gemessen: nichts im Kit verweigert das
ÜBERSCHREIBEN eines Inbox-Dokuments (`echo >` rc 0, Tool-`Write` rc 0, `cp` darüber rc 0 —
`guard_fs_tripwire` verweigert das LÖSCHEN unter `inbox/`, nicht das Überschreiben). Damit läuft
„zwei Lesungen holen, Dokument tauschen, ablegen" innerhalb einer Sitzung durch — nach CLAUDE.md
blockierend. Geschlossen, indem `record_filing_reading` beim Attestieren zusätzlich die BYTES jedes
genannten Quelldokuments stempelt und das Gate sie beim Zug nachrechnet. **Entscheidung zu einem
`source_sha256`-FELD im Datensatz: nein**, mit Grund — der `filing-reviewer` hat `Read, Grep, Glob,
Write` und kein Werkzeug, das eine Befehlszeile ausführt, könnte also keinen Hash bilden. Ein Feld,
das die Rolle nicht füllen kann, wäre ein Vertrag, der wie Schutz aussieht und keiner ist. Der Hook
hat das Dateisystem; die Rolle nicht.

**B2e — ein Befund beim Nachlesen des eigenen Fixes.** Ein relatives Wort kann zwei Dokumente
meinen: `reading_bases` hält Repo-Wurzel UND Shell-Verzeichnis, und ein `cd` **fügt** eine Basis
hinzu, statt sie zu ersetzen (die Politik, die ein falsch gelesenes `cd` für das ZIEL harmlos
macht). Für die QUELLE fällt sie andersherum aus. `sources_of` behält jetzt nur Positionen, die
wirklich existieren, und `check` verlangt die Lesungen für **jeden** verbliebenen Kandidaten —
einen auszuwählen hieße, sich über ein Dokument zu irren, das niemand gelesen hat. Preis, benannt:
liegt zufällig eine gleichnamige Datei in der Repo-Wurzel, braucht die Ablage auch für die
Lesungen. Über-Verweigerung, und die Meldung nennt die Quelle, für die nichts gefunden wurde. Test:
`test_a_token_that_could_name_two_documents_needs_the_readings_for_both`.

**B3 — der Ablagefach-Vergleich.** `_filing.under` verglich Bytes. Jetzt über `os.path.normcase`,
also so, wie das Dateisystem dieses Hosts zwei Namen vergleicht: auf NTFS gefaltet, auf POSIX nicht.
Das ist eine Definition, kein Pflaster — auf Linux IST `ARCHIVE/` ein zweites Verzeichnis. Der Test
verzweigt entsprechend über `os.path.normcase` und misst damit das Dateisystem, nicht eine Plattform.

**R1 — `NotebookEdit`** steht jetzt auf dem Matcher der Kette und in beiden Gates.

**R2 — die Untergrenze in `test_role_contracts.py`.** Meine aggregierte Grenze war schwächer als die
alte: pro Schema ≥ 3 UND aggregiert ≥ 20 (der Lauf findet heute 24 — die 24 ist die Messung, die
Grenzen sind Grenzen).

**R3 — die Ordnungsbehauptung in `settings.json`.** Gemessen: der Prüfer tauschte die beiden Namen
und alles blieb grün, weil das zweite Gate für jeden Fall, den das erste verweigert, von selbst
aussteigt. Die Behauptung ist **entfernt**; an ihre Stelle tritt, was die Kette wirklich bringt (ein
Prozess statt zwei) plus der Verweis auf den Test. Und der Test misst die Eigenschaft jetzt wirklich:
`gate_second_reading` wird für das ungedeckte Ziel und für den leeren Plan **allein** gefahren und
muss rc 0 liefern — durch die Kette allein wäre das vom Launcher erfüllt worden.

**Zehn weitere Mutationen, alle rot** (Klon außerhalb des Repos, Defekt eingesetzt, gesehen,
zurückgesetzt) — zusammen mit den zehn der ersten Runde sind es zwanzig:

| Wiederhergestellter Defekt | Ergebnis | Gefangen von |
|---|---|---|
| archivinterne Bewegung ist nie ein Eintritt | RED | `test_an_archive_internal_rename_is_a_filing_decision_and_needs_its_own_readings` |
| eine freigegebene Regel verlangt GAR KEINE Lesung | RED (2) | `test_a_plan_rule_can_release_its_own_class_from_the_second_reading`, dito |
| Lesung deckt das ZIEL statt das Dokument | RED | `test_a_reading_authorises_the_document_it_names_and_not_the_target_path` |
| Landung ohne Quelle stützt sich auf fremde Lesungen | RED (2) | `test_a_landing_with_no_document_behind_it_is_refused` |
| Lesung nicht an die Bytes des Dokuments gebunden | RED | `test_a_document_swapped_after_the_readings_is_not_the_document_they_read` |
| Aufzeichner hasht das Quelldokument nicht | RED | dito |
| Ablagefach byteweise verglichen statt wie der Host | RED | `test_a_tray_is_the_tray_however_the_host_spells_its_case` |
| ein gedeckter Kandidat reicht bei mehrdeutigem Wort | RED | `test_a_token_that_could_name_two_documents_needs_the_readings_for_both` |
| Gate steigt bei ungedecktem Ziel nicht selbst aus | RED | `test_the_second_reading_gate_stands_down_where_it_is_not_the_question` |
| `NotebookEdit` auf keinem Matcher | RED | `test_a_notebook_write_reaches_both_filing_gates` |

## 8d. Nacharbeit 2026-08-29 (zweiter Durchgang): drei Auflagen des bestandenen Prüfurteils

**1. Der Ausnahme-Satz sagt jetzt, was der Code vergleicht.** `an_entry` vergleicht `path_template`
und Dateinamen, **nicht** den Ordner. Der Docstring nannte das „a folder being tidied" und behauptete
damit einen engeren Schutz als gebaut: `mv archive/finance/incoming_invoices/2026/x.pdf
…/2027/x.pdf` ist rc 0, obwohl der Jahreswert Teil der Klassifikation ist — und eine solche
Bewegung kann auf einem anderen, doppelt gelesenen Dokument landen, ohne dass die Byte-Bindung je
läuft, weil das Gate vorher aussteigt. Der Satz steht jetzt so da, in `gate_second_reading.py`
(Kopf von `an_entry`) und in `ENFORCEMENT.md`. **Kein Regress** — vor dieser Runde war *jede*
archivinterne Bewegung frei. Die Lücke bleibt offen und ist Sache der Löcherliste des Prüfers.

**2. Die Verweigerung erfindet keine Diagnose mehr.** `bound` fällt aus zwei Gründen aus: ein
Prüfsummen-**Unterschied** und eine Prüfsumme, die **nie genommen wurde**. Verzweigt wurde nur über
die Anzahl, also bekamen „Quelle existierte nie" und „Dokument größer als die Grenze" beide den Satz
über einen Austausch. Jetzt zwei getrennte Zweige: `stale` sagt „no longer match its bytes",
`unbound` sagt „could not be bound to a document at all … the binding was never made". Rot in beide
Richtungen gemessen.

**3. Die Behauptung „die höhere Forderung gewinnt" hat jetzt einen Stolperdraht.** Der Prüfer
mutierte `max`→`min` und alle 48 Tests blieben grün, weil kein Fixture zwei überlappende
`path_template` hatte. Neu: ein Plan mit `archive/finance/<area>/<year>/` (freigegeben) ÜBER
`archive/finance/incoming_invoices/<year>/` (gesichert). Drei Richtungen: der nur freigegebene Ort
legt mit einer Lesung ab, der überlappende nicht (und die Verweigerung nennt beide Regeln), mit
zwei Lesungen dann doch.

| Wiederhergestellter Defekt | Ergebnis | Gefangen von |
|---|---|---|
| Der No-Digest-Fall wird als Austausch gemeldet | RED (2) | `test_a_reading_that_could_not_be_bound_says_so_instead_of_reporting_a_swap` |
| Ein echter Austausch wird als nie gemachte Bindung gemeldet | RED | `test_a_document_swapped_after_the_readings_is_not_the_document_they_read` |
| Die NIEDRIGSTE Forderung der deckenden Regeln gewinnt | RED | `test_where_two_rules_cover_one_place_the_higher_demand_wins` |

Damit sind es 23 Mutationen über die ganze Aufgabe, alle rot; die beiden früheren Batterien liefen
nach dieser Änderung erneut und blieben rot.

## 9. Was diese Runde am Lead-Paket kostet

`tools/validate.py` verweigerte bei 43 202 B gegen 41 973 B Rekord. Zweimal gekürzt (erster Entwurf
+2 250 B, geliefert +1 229 B), dann über `tools/record_lead_package_sizes.py --write --note …`
angehoben — der vorgesehene Weg, mit Eintrag im Journal von `docs/reviews/phase0-disposition.md`.
Der Grund steht dort: ein Lead, der die Regel nicht trägt, diagnostiziert die Verweigerung seines
Registrators bei jedem Sweep neu.
