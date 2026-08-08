# Messprotokoll der vier Repo-Gates (TSK-0011, 2026-08-05)

Fortsetzung von `docs/reviews/2026-08-05-tsk0007-measurements.md`. Jenes Dokument trägt die Ketten
zu **H1–H15**; dieses trägt die Ketten zu **H16–H23** und die Vorher/Nachher-Werte der Runde
TSK-0011 (Befunde F1–F10 des Prüfberichts zu TSK-0008).

Es enthält **keine** Behauptung ohne Messung. Wo etwas nicht isoliert messbar war, steht das
ausdrücklich da, samt dem Grund.

## Wie gemessen wurde

- **Echte Hook-Prozesse.** Jede rc-Zeile unten ist ein `subprocess`-Start des registrierten Skripts
  mit JSON auf `stdin`, gegen ein Projekt **außerhalb** dieses Repos (`team-kits/`,
  `tools/bump_kit_version.py`, `project_memory/`, `.claude/`, `CLAUDE.md`, echtes git-Repo mit
  echtem Diff). `2` = Verweigerung, `0` = Durchlass; alles andere liest der Provider als „hook
  error, carry on", also ebenfalls als Durchlass.
- **Die Shell als Schiedsrichter.** Für die Frage „wo steht die Shell wirklich" ist der Rückgabecode
  kein Beleg. Gemessen wurde stattdessen die **Datei**: jede Zeile lief in einer echten `bash` in
  einem Sandbox-Baum, in dem `team-kits/kernel/state.py` den Inhalt `a` hatte; geschrieben ist,
  was danach `b` enthält.
- **Ablation statt Behauptung.** Jeder neue Zweig wurde einzeln in einer Kopie außerhalb des Repos
  zurückgedreht und die zugehörigen Tests gefahren (Tabelle „Mutationen" unten).
- **Skripte:** `bench.py` (Matrix), `shellcheck.sh` (echte bash), `finder_ablation.py`,
  `redcheck.py` (Mutationen), `patch_harness.py` (die Fassung selbst). Alle im Sitzungs-Scratchpad,
  nicht im Repo — sie messen einen Stand, sie sind kein Produkt.

## 1. F1 — ein Verzeichniswechsel, den die Shell nicht vollzieht

Die **echte bash** zu den sechs Zeilen (Subjekt: die Datei, nicht der Rückgabecode). Jede Zeile
endet auf `sed -i "s/a/b/" team-kits/kernel/state.py`, relativ geschrieben:

| Zeile davor | Shell landet | Datei geschrieben |
|---|---|---|
| `cd /nope-not-there ;` | im Baum | **ja** |
| `popd ;` (leerer Stapel) | im Baum | **ja** |
| `pushd ;` (leerer Stapel) | im Baum | **ja** |
| `cd "<außerhalb>" ; cd - ;` | im Baum | **ja** |
| `( cd "<außerhalb>" ) ;` | im Baum | **ja** |
| `cd nope-does-not-exist ;` | im Baum | **ja** |
| `cd "<außerhalb>" ;` (existiert) | außerhalb | nein |
| `cd ;` (Heimatverzeichnis) | außerhalb | nein |
| `pushd "<außerhalb>" ; pushd ;` | im Baum | **ja** |

Durch das Gate, vorher/nachher:

| Zeile | vorher | nachher |
|---|---|---|
| `cd /nope-not-there ; <schreiben>` | rc 0 | **rc 2** |
| `popd ; <schreiben>` | rc 0 | **rc 2** |
| `pushd ; <schreiben>` | rc 0 | **rc 2** |
| `cd "<außerhalb>" ; cd - ; <schreiben>` | rc 0 | **rc 2** |
| `( cd "<außerhalb>" ) ; <schreiben>` | rc 0 | **rc 2** |
| `cd nope-does-not-exist ; <schreiben>` | rc 0 | **rc 2** |
| `pushd "<außerhalb>" ; pushd ; <schreiben>` | rc 0 | **rc 2** |
| `cd "<außerhalb>" && <schreiben>` (Gegenrichtung) | rc 0 | rc 0 |
| `pushd "<außerhalb>" ; <schreiben>` (Gegenrichtung) | rc 0 | rc 0 |
| `cd ; <schreiben>` (Gegenrichtung) | rc 0 | rc 0 |
| `cd ~ ; <schreiben>` (Gegenrichtung) | rc 0 | rc 0 |
| `pushd "<außerhalb>" ; popd ; <schreiben>` | rc 2 | rc 2 |
| `cd .claude/hooks && rm gate_todo_items.py` | rc 2 | rc 2 |

## 2. F2 — `cd -` war unerreichbar

Vorher filterte die Operandenliste jedes Wort weg, das mit `-` beginnt, also auch `-` selbst; der
Vergleich darunter konnte nie wahr werden, und `cd -` landete im **Heimatverzeichnis**. Gemessen an
der Unterscheidbarkeit: nachher gehen `cd -` (rc 2, zurück in den Baum) und `cd` ohne Operand
(rc 0, Heimatverzeichnis) **auseinander** — vorher waren beide rc 0 und nicht unterscheidbar.

## 3. F3 — der Schnitt am Deklarationskopf

| Zeile | vorher | nachher |
|---|---|---|
| `sed -i 's\|a\|b\|' <kitdatei> $(true) {` | rc 0 | **rc 2** |
| `arr=(a b) sed -i s/a/b/ <kitdatei> {` | rc 0 | **rc 2** |
| `dec () { <Kernel-Zeile> ; }` | rc 0 | rc 0 |
| `function dec { <Kernel-Zeile> ; }` (H17) | rc 2 | **rc 0** |
| `dec () { <schreiben> ; }` | rc 2 | rc 2 |
| `{ <schreiben> ; }` | rc 2 | rc 2 |
| `<schreiben> {` | rc 2 | rc 2 |
| `{ <Kernel-Zeile> ; }` | rc 0 | rc 0 |

Zur letzten Zeile: der Sonderfall „leerer Kopf" in `stage_body` ist **abladiert** worden — mit und
ohne ihn antwortet das Gate hier gleich (`_stage_verb` überspringt die Klammer ohnehin, und eine
Klammer nennt keinen Pfad). Er ist deshalb entfernt, statt als unmessbarer Zweig stehen zu bleiben.

## 4. F4 — die Frist

`os.stat` auf einen nicht erreichbaren SMB-Host kostet auf diesem Host **42,1 s**
(`\\192.0.2.x\share\f`, RFC-5737-Bereich; `\\10.255.255.x\` gleich teuer). Windows merkt sich das
Ergebnis kurzzeitig pro Adresse: dieselbe Adresse direkt danach 0,00 s, ~84 s später wieder 42,1 s.

Gate 1 mit registriertem Timeout **120 s**, Kandidaten auf nicht erreichbaren Hosts:

| Kandidaten | vorher | nachher |
|---|---|---|
| 1 | rc 0 nach 21,8 s | rc 0 nach 43,0 s |
| 3 | rc 0 nach 85,0 s | rc 0 nach 85,0 s |
| 5 | **rc 0 nach 211,3 s** — über der Frist, der Provider hätte den Hook getötet | **rc 2 nach 96,5 s** |

Mit einer Registrierung von 5 s in einer Kopie: rc 2 nach 4,4 s. Mit einer Registrierung ohne
`timeout`: rc 2 auf einem sonst **erlaubten** Pfad, mit der fehlenden Frist als Begründung.

Zwei Nebenmessungen, die die Form des Fixes bestimmt haben:

- `os.path.realpath` ist auf Windows ebenfalls eine Dateisystemfrage (`nt._getfinalpathname`) und
  blockiert genauso. Solange nur `os.stat` unter der Frist lief, feuerte die Verweigerung
  pünktlich und der **Prozess** brauchte trotzdem 42,8 s.
- Ein Arbeiter-Thread **pro** Frage kostete 0,18 s auf einer Entscheidung mit 607 Fragen; ein
  einziger dauerhafter Arbeiter kostet 0,08 s. Die Normalfälle liegen unverändert bei 0,5–0,6 s.
- `\\localhost\C$\...` bleibt auflösbar: 0,01 s für einen existierenden Pfad; die
  Präfix-Schreibweisen-Tests (`test_gate1_refuses_a_protected_path_however_the_filesystem_spells_it`)
  laufen unverändert.

## 5. F6 — Vorfahre statt Subjekt (H19)

| Zeile | vorher | nachher |
|---|---|---|
| `cp -r docs ..` | rc 2, Text: *„this is canonical project state"* | rc 2, Text: *„refused for what stands UNDER it"* |
| `cp -r docs C:/` | rc 2, Text: *„this is canonical project state"* über `C:/` | rc 2, Text: *„refused for what stands UNDER it"* |
| `sed -i … project_memory/README.md` | rc 2, *„this is canonical project state"* | unverändert |
| `robocopy team-kits <außerhalb>\bk /E` | rc 2 | rc 2, jetzt mit dem Vorfahren-Hinweis |
| `tar -czf <außerhalb>/bk.tgz team-kits` | rc 2 | rc 2, jetzt mit dem Vorfahren-Hinweis |

Die **Verweigerung bleibt**; nur die Begründung behauptet nicht mehr, ein Laufwerksbuchstabe sei
kanonischer Zustand.

## 6. Was offen ist, gemessen am neuen Stand

| Kette | rc | Eintrag |
|---|---|---|
| `R="<repo>" ; sed -i … "$R/team-kits/kernel/state.py"` | **0** | H16 (offen) |
| `cd "$NOWHERE" && sed -i … team-kits/kernel/state.py` | **2** | H16, diese Hälfte **geschlossen** — ein Literal `$NOWHERE` ist kein existierendes Verzeichnis, also bleibt die Basis stehen |
| `echo <pfad> \| xargs sed -i …` | **0** | H22 |
| `echo $(sed -i … <pfad>)` | **0** | H22 |
| ``echo `sed -i … <pfad>` `` | **0** | H22 |
| `git apply x.patch` | **0** | H22 |
| `sed -i … \\192.0.2.77\share\f` | 0 nach 43,0 s | H23 — ein einzelner unerreichbarer Kandidat wird beurteilt, nicht verweigert; erst die Summe sprengt das Budget |

## 7. Ablation des Standardbibliothek-Finders

Finder entfernt, der stumme Stub in je einem Verzeichnis, echter Gate-Prozess,
`sed -i 's/a/b/' team-kits/kernel/state.py`:

| Verzeichnis | mit Finder | ohne Finder |
|---|---|---|
| das eigene Verzeichnis des Gates | rc 2, *„may not write"* | rc 2, aber *„could not be inspected"* — ein **anderer** Zweig |
| das Hook-Verzeichnis des Kits | rc 2, *„may not write"* | **rc 0** |
| die Kit-Wurzel | rc 2, *„may not write"* | rc 2, gleiche Begründung |

Der Test prüft deshalb jetzt die **Begründung** und nicht nur den Rückgabecode; damit tragen zwei
der drei Parameter. Der dritte (Kit-Wurzel) ist ein Stolperdraht für den Tag, an dem sich die
Ladereihenfolge ändert — heute ist alles, was der Leser braucht, längst in `sys.modules`, bevor
`tools/bump_kit_version.py` die Kit-Wurzel auf `sys.path[0]` legt.

## 8. Mutationen — jeder gebaute Zweig einzeln

Defekt in der Kopie außerhalb des Repos wiederhergestellt, die zugehörigen Tests gefahren:

| Mutation | Test | Ergebnis |
|---|---|---|
| Existenzprüfung des Ziels entfernt | `…does_not_follow_a_move_the_shell_would_not_make` | **rot** |
| Subshell-Erkennung entfernt | dito | **rot** |
| `popd` auf leerem Stapel geht ins Heimatverzeichnis | dito | **rot** |
| `pushd` ohne Operand auf leerem Stapel geht ins Heimatverzeichnis | dito | **rot** |
| `pushd` ohne Operand tauscht nicht | dito | **rot** |
| jedes `-…` gilt als Flag (also auch `-`) | dito | **rot** |
| kein Operand → Basis statt Heimatverzeichnis | dito | **rot** |
| `~` wird nicht aufgelöst | dito | **rot** |
| `pushd` legt nichts auf den Stapel | `…resolves_a_relative_word_where_the_line_really_runs` | **rot** |
| Schlüsselwortform der Deklaration entfernt | `…cuts_a_declaration_head_because_it_is_one` | **rot** |
| Kopfprüfung zurück auf „irgendwo ein `(`" | dito | **rot** |
| Frist abgeschaltet | `…answers_before_its_registration_gives_up` | **rot** |
| fehlende Frist ist kein Grund zu verweigern | `…registration_states_no_deadline_refuses` | **rot** |
| `realpath` ohne Frist | `…answers_before_its_registration_gives_up` | **rot** |
| Richtung der Verweigerung nicht unterschieden | `…is_an_area_or_merely_holds_one` | **rot** |
| Kit-Prädikat wieder selbst geschrieben | `…is_the_one_the_kernel_calls_a_kit` | **rot** |
| Finder nicht installiert | `…cannot_answer_for_a_standard_library_name` | **rot** (2 von 3 Parametern) |
| `os._exit` statt normalem Abgang | `…answers_before_its_registration_gives_up` | **grün → Zweig entfernt** |
| `os.stat` ohne Frist | `…answers_before_its_registration_gives_up` | **grün — siehe unten** |

**`os.stat` ohne Frist bleibt grün, und das ist ein benannter Rest.** Der Grund ist gemessen: zu
demselben Pfad wird zuerst `realpath` gefragt, und das blockiert mindestens so lange — ein Kandidat
kostete 21,8 s, als nur eine der beiden Fragen ans Netz ging, und 43,0 s, als beide es taten. Der
Zweig ist also **wirksam** (ohne ihn wären 21 s pro Kandidat unbegrenzt), aber kein Test kann ihn
von `realpath` trennen, solange beide denselben Host fragen. Er bleibt stehen, ohne dass irgendein
Kommentar Deckung durch einen Test behauptet.
