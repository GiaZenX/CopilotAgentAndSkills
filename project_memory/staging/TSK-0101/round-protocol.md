# TSK-0101 — Rollout-Sicherheit (Strom B des DEC-0057-Piloten): Rundenprotokoll

**Wanduhr:** Runde 1: Start 2026-09-01 21:20:51 +0200 · Ende 22:39:46 · **1 h 19 min**.
Nacharbeit nach Prüfer-FAIL: Ende 2026-09-02 00:22:07 · **rund 1 h 40 min**. Zusammen **rund
3 h** Umsetzer-Anteil; DEC-0057 (g) misst bis zum Prüfer-PASS.

**Baum:** `C:\Offline Repos\v2-testbed\_worktrees\stream-rollout` (Branch `stream/rollout`, auf
`c155a5f`). **Nicht committet** (DEC-0057 (e)). Übergabe:
`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0101\stream-rollout.patch` (2076 Zeilen, nach der Nacharbeit).
**Gegen `c155a5f` geprüft**: frischer Klon des Worktrees, `git checkout c155a5f`,
`git apply --check` → **rc 0**. Die Merge-Runde bekommt also keinen Patch, der erst dort scheitert.
**Provisorischer Stempel: 2026.09.02-1** in allen drei `VERSION`-Dateien (DEC-0057 (d)).

Geänderte/neue Dateien (11):

```
 docs/POST_V2_WISHLIST.md        | 166 +      (H86, H87, H88 — nur die reservierten Nummern)
 team-kits/kernel/kitupdate.py   | 487 +      (Klassifikation inkl. `unknown`, Pin als Bundle,
                                              Rollback-Leser, Preflight-CLI mit Rollback-Modus)
 team-kits/scaffold_team.ps1     | 213 +-     (Preflight, Restore-Menge als Daten, -Rollback, `..`-Verbot)
 team-kits/scaffold_team.sh      | 205 +-     (dasselbe im POSIX-Zwilling)
 team-kits/{dev,office,research}-team/VERSION | je 4 +-  (provisorischer Stempel)
 tools/test_kitupdate.py         | 623 +      (20 neue Tests, davon 8 parametrisiert; 77 Fälle statt 49)
 tools/test_user_defaults.py     |  95 +      (NEU: FR-0055, 3 Tests)
 tools/test_hooks_v2.py          |  27 +-     (ein Test las eine Liste, die es nicht mehr gibt)
 user/claude/settings.json       |   3 +-     (remoteControlAtStartup + Kommentar)
```

`project_memory/` im Worktree: **unberührt** (`git status --short` nennt es nicht).
Gespiegelte Kit-Dateien: **keine berührt** — nichts unter `team-kits/{dev,office,research}-team/`
außer den drei `VERSION`-Stempeln, also keine Spiegelarbeit fällig.

---

## 1. FR-0044 — Der Installer klassifiziert den Bestand, mit No-write-Nachweis

**Gebaut.** `kernel/kitupdate.classify(root)` beantwortet `greenfield | v2 | v1 | mixed` als
**Kreuzprodukt zweier unabhängiger Lesungen** über das Zustandsverzeichnis, nicht als vier Fälle:

* *Hat der Kernel hier einen eigenen Bereich?* — die `KERNEL`-Zeilen von `migrate.search_coverage`.
* *Liegt ein V1-Datensatz in einem durchsuchbaren Dokument?* — `migrate.scan_document` +
  `_declares_status` + `_is_backlog_type`, also **derselbe Erkenner**, den `migrate.build_plan` und
  `report._check_no_v1_records_outside_the_archive` benutzen. Ein eigener wäre die zweite Definition
  gewesen, an der Installer und Validator über dieselbe Datei verschieden urteilen.

Der Preflight läuft in **beiden** Zwillingen als **erster** Schritt (vor der Konfigurationsprüfung —
ein V1-Bestand hat keine V2-`project_config.yaml`, und eine Schema-Meldung wäre die falsche
Antwort), er **fällt geschlossen aus** (`preflight_cli`), und er wird aus dem Verzeichnis des
laufenden Skripts importiert (wie `gen_provider_artifacts.py`), nicht aus dem Staging.

**Die entscheidende Messung — der Stempel unterscheidet V1 und V2 NICHT.** Der Vor-Kernel-Installer
schrieb `.claude/kit_version` UND `.claude/team_kit_roles.txt` genauso wie der heutige
(`git show 9e4419b~1:team-kits/scaffold_team.sh`). Alle drei Feldkopien tragen beides. Ein
Klassifikator, der diese Dateien fragt, hätte alle drei „V2" genannt.

**No-write-Nachweis** (der, den die Seitenkontrolle §5.6 mangels V1-Bestand nicht führen konnte) —
Baum-Hash Datei für Datei, vorher/nachher:

| Projekt | Dateien | Verdikt | Installer | geschrieben |
|---|---|---|---|---|
| synaipse-KOPIE | 1602 | `v1` (7 Monolithe, 632 Datensätze) | rc 1 | **nichts** |
| portfoliomanaigement-KOPIE | 4010 | `v1` (7 Monolithe, 285 Datensätze) | rc 1 | **nichts** |
| BuyPlugGo-KOPIE | 2590 | `v1` (`process_definitions.yaml`, 16) | rc 1 | **nichts** |

**Die Gegenmessung, ohne die der Nachweis nichts wert wäre** — derselbe Installer VOR dieser Runde
(R1-Klon), gegen eine frische synaipse-Kopie: **rc 0**, 128 neue Dateien, 64 geänderte, eine
gelöschte (`.claude/hooks/auto_dashboard.py`), `.claude/kernel` installiert, Stempel auf
2026.09.01-2 gesetzt — über einen Zustand, den kein V2-Kommando lesen kann und in den danach kein
Werkzeug mehr schreiben darf.

**Gegenrichtung gebaut und gemessen:** `greenfield` und `v2` installieren weiter (sonst wäre der
Nachweis von einem Installer erfüllt, der alles verweigert); `mixed` installiert **und sagt es
laut**.

## 2. FR-0041 — Pin und Rollback

**Pin.** `.claude/kit_pin` trägt dieselbe Zwei-Zeilen-Sprache wie jeder andere Stempel
(`identity`), dazu optional `kit:`. Der Pin verweigert **alle DREI Türen**: `update-kit` (im
`_plan`), den von Hand gestarteten Installer und den **Rollback** (beide im Preflight). Verglichen
wird ein **Bundle** — das Kit plus jedes Stempelfeld, das der Datensatz nennt —, nicht eine
Versionszeichenkette (siehe Nacharbeit §10, B3/B4). Ein Pin, dessen Stempel unlesbar
ist, **pinnt weiter** — eine beschädigte Aufzeichnung darf kein Entpinnen sein. Das Neuauflegen
**derselben** Fassung bleibt erlaubt (Reparatur), sonst wäre eine halb installierte Anlage gefangen.

**Rollback.** Der Installer sichert seit jeher nach `.claude/backups/<stempel>`, aber Sicherungs-
und Wiederherstellungsliste waren **zwei** Aufzählungen. Jetzt ist es **eine Menge** (`RESTORABLE` /
`$restorable`) mit drei Verbrauchern — Sicherung, Manifest `RESTORE_SET` *in* der Sicherung,
Wiederherstellung. `scaffold_team.sh --rollback` / `.ps1 -Rollback` spielt die Menge zurück, **die
die damalige Sicherung aufgezeichnet hat**, entfernt die Ankündigung eines rückgängig gemachten
Übergangs (`kit_updated_from`), setzt den Neustart-Marker und **nennt, was es nicht angefasst hat**.

**Dabei aufgefallener und geschlossener Defekt:** `.claude/kit_state.json` — der
Vertrauensdatensatz über das Hook-Bundle, den der Lauf selbst neu schreibt — war weder gesichert
noch wiederhergestellt. Ein Abbruch nach `write_kit_state.py` stellte das ALTE Bundle wieder her und
ließ den Hash des NEUEN daneben stehen.

**Der Preis, ehrlich benannt (H87):** der Pin schaltet den Update-Nag **nicht** ab. Gemessen am
ausgelieferten `session_status.py` als Prozess gegen ein gepinntes Projekt: der Text sagt
„KIT UPDATE AVAILABLE … On their OK you install it YOURSELF" und nennt den Pin mit keinem Wort. Der
PM schlägt also vor, der Nutzer sagt ja, die Freigabe wird geprägt — und erst `update-kit`
verweigert. Das ist die **laute** Reihenfolge (nichts wird installiert); der Preis ist eine
überflüssige Frage und eine Freigabe, die nichts öffnet. Die Gegenrichtung wäre genau die
Markerklasse aus `BUG-0078`: eine Datei, die eine Meldung dauerhaft verstummen lässt.

## 3. FR-0055 — remoteControlAtStartup

`user/claude/settings.json` liefert `"remoteControlAtStartup": false` aus; der Schlüssel steht nicht
mehr unter „Deliberately NOT shipped", sondern mit seinem Grund im Kommentar. **Am Installer war
nichts zu ändern**: `merge_settings.py` ergänzt fehlende Top-Level-Schlüssel und lässt vorhandene
stehen — gemessen als Prozess gegen ein Wegwerf-`HOME`: ohne Schlüssel → `false`, mit `true` →
`true` bleibt (und `theme: light` daneben unangetastet). Der dritte Test ist der **Stolperdraht**:
jeder Pfad, den der Kommentar als „nicht ausgeliefert" nennt, wird gegen die Datei aufgelöst und
muss fehlen — eine halbe Änderung (Schlüssel ohne Kommentar) wird rot.

## 4. FR-0046 — Feldtest

Kopiert wurde **Kopie-von-Kopie** nach `_round-scratch/TSK-0101/pilots-master/` (die Master unter
`C:\Offline Repos\v2-pilot` sind **nicht** angefasst; jeder Lauf arbeitet auf einer frischen Kopie
der Runden-Master, die dadurch mehrfach nutzbar bleiben).

**Der wichtigste Befund widerspricht dem Item.** `FR-0046` sagt „ALL THREE are the update-kit path
(old-V2 → new-V2), NOT migration; the earlier V1 guess was wrong (measured)". **Das stimmt nicht.**
Alle drei Stempel (2026.07.17-8 / -9, 2026.07.18-3) liegen VOR dem Kernel-Commit `9e4419b`
(2026-07-24 23:02), und alle drei tragen monolithische `project_memory/*.yaml`, kein
`.claude/kernel`, kein `kit_state.json`, kein `scripts/harness.py`. **Es sind V1-Bestände.** Damit
ist `update-kit` dort gar nicht erreichbar — der Einstiegspunkt existiert nicht —, und der einzige
Weg ist der Installer von Hand. Das ist ein Item-Befund für den Lead, kein Fehler im Gebauten.

| Schritt (synaipse-Kopie, `mixed` gemacht: Kernelbereich dazugelegt) | Ergebnis |
|---|---|
| Installation über `mixed`-Bestand | rc 0; Kernel + Einstiegspunkt installiert; **V1-Monolithe überleben**; Neustart-Marker gesetzt; 7 abweichende Repo-Templates aufgezeichnet; Preflight sagt beides laut |
| `harness.py validate` danach | rc 1, **7 Fehler**, genau die SR-0001-Meldung über dieselben 7 Dokumente (632 Datensätze) — das Verdikt `mixed` und der Validator sind sich einig |
| Nächste Fassung in ein **gepinntes** Projekt | rc 1, „PINNED to 2026.09.01-2 and 2099.12.31-9 is a different release", **Baum unverändert** |
| Pin gelöst, nächste Fassung installiert | rc 0, Stempel 2099.12.31-9 |
| **Rollback** | rc 0, 15 aufgezeichnete Pfade, **byte-gleich**, Stempel zurück auf 2026.09.01-2; nicht angefasst und benannt: `agent-memory`, `claude-security-guidance.md`, `HANDOVER_PENDING`, `kit_last_seen_version`, `kit_update_pending.repo`, `project_path.state` |

**Kosten der Lesung, gemessen (warm):** synaipse 2,9–3,1 s über 20 Dokumente, BuyPlugGo 0,95–1,03 s
über 14, portfolio 0,77–0,92 s. Der Bereich des Kernels wird nicht gelesen, sonst wäre es die
Größenordnung des Zustands statt die der Dokumente.

---

## 5. Rot zuerst — jede Messung in einem Klon AUSSERHALB des Repos

Klon: `_round-scratch/TSK-0101/redfirst` (robocopy ohne `.git`), Originale per
`git show c155a5f:<pfad>` zurückgeschrieben (ohne BOM, LF — ein BOM vor `#!` wäre ein Defekt des
Messgeräts), danach jeweils `tools/bump_kit_version.py`, sonst misst man `write_kit_state`.

| Lauf | wiederhergestellter Defekt | rot |
|---|---|---|
| **R1** | `kitupdate.py`, `scaffold_team.sh`, `scaffold_team.ps1` auf `c155a5f` | **15 Tests**: `test_a_stock_is_classified_from_two_independent_readings`, `test_a_v2_project_is_not_called_v1_by_the_records_its_own_kernel_wrote`, `test_a_document_the_reading_could_not_open_is_named_and_not_read_as_empty`, `test_a_v1_stock_is_refused_and_the_installer_writes_nothing[powershell,bash]`, `test_a_greenfield_project_still_installs[powershell,bash]`, `test_a_pinned_project_refuses_the_update_and_says_how_the_pin_is_lifted`, `test_a_pin_that_names_the_release_being_installed_is_not_a_refusal`, `test_a_pin_record_that_cannot_be_read_still_pins`, `test_the_installer_itself_refuses_a_pinned_project_and_writes_nothing[powershell,bash]`, `test_a_rollback_restores_the_previous_bundle_byte_for_byte[powershell,bash]`, `test_a_snapshot_without_a_restore_set_is_not_offered_as_the_previous_bundle` |
| **R2** | `user/claude/settings.json` auf `c155a5f` | **2**: `test_the_shipped_defaults_turn_remote_control_off`, `test_a_machine_that_already_set_remote_control_keeps_its_own_value` (der Stolperdraht ist dort korrekt GRÜN — die alte Datei ist in sich stimmig) |
| **R3** | nur `.claude/kit_state.json` aus der Restore-Menge beider Zwillinge entfernt | **2**: `test_a_rollback_restores_the_previous_bundle_byte_for_byte[powershell,bash]` |
| **R4** | Schlüssel ausgeliefert, Kommentar NICHT korrigiert (die halbe Änderung) | **1**: `test_no_key_the_defaults_ship_is_still_listed_as_deliberately_not_shipped` |

`test_both_installer_twins_record_the_same_restore_set` fällt in R1 mit, weil es das Manifest liest,
das es dort nicht gibt (`FileNotFoundError` in `_restore_set`) — es ist in der R1-Auswahl nicht
enthalten und darum oben nicht mitgezählt.

## 6. Suiten (DEC-0050: betroffene Suiten, nicht die volle)

| Suite | Ergebnis |
|---|---|
| `tools/test_kitupdate.py` + `test_user_defaults.py` + `test_repo_hygiene.py` | 75 passed, 1 skipped (3:53) |
| `tools/test_presets.py` (im ersten Durchgang mit) | grün (Teil von 108 passed, 1 skipped) |
| `tools/test_migrate.py` + `test_kernel.py` + `test_handover_marker.py` | 271 passed (5:11) |
| `tools/test_hooks.py -k "scaffold or preset or settings"` | 30 passed, 6 skipped |
| `tools/test_hooks_v2.py -k "scaffold or kernel_as_one_layer"` | 11 passed |
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |

**Volle Suite bewusst nicht gefahren** — DEC-0057 (b): sie gehört der Merge-Runde.

**Ein Test musste geändert werden, und warum:**
`tools/test_hooks_v2.py::test_both_scaffolds_manage_the_kernel_as_one_layer` suchte per Regex nach
einer Zeile `backup_local … .claude/kernel`. Die gibt es nicht mehr — die Menge ist Daten geworden.
Der Test liest jetzt die **Deklaration** der Menge, und sein Docstring nennt die **Laufzeit-Hälfte**,
die diese Runde neu baut: `tools/test_kitupdate.py::test_both_installer_twins_record_the_same_
restore_set` fährt **beide** Zwillinge wirklich und vergleicht die geschriebenen Manifeste Eintrag
für Eintrag. Der alte Docstring behauptete, die POSIX-Hälfte sei auf diesem Läufer nicht
ausführbar; sie ist es (alle `[bash]`-Fälle oben laufen).

## 7. Was ich bewusst NICHT geschlossen, sondern benannt habe

1. **Pin und Rollback haben keinen Kernel-Befehl** (H87). Gemessen am ausgelieferten Einstiegspunkt:
   25 Unterkommandos, kein `pin`, kein `rollback`. Grund ist der **Auftrag**, nicht die Technik:
   `team-kits/kernel/cli.py` ist für diesen Strom verboten. Heute setzt der Nutzer den Pin, indem er
   `.claude/kit_pin` aus einer Shell **außerhalb** der Sitzung anlegt, und löst ihn durch Löschen —
   bewusst nicht aus der Sitzung, denn `gate_write_scope` verweigert dort jeden Werkzeug-Schreibzugriff
   auf `.claude/`, und ein Pin, den der Agent selbst setzen könnte, wäre schlimmer als keiner.
2. **Der Pin schweigt in der Sitzungsmeldung** (H87, Messung oben). Der Satz gehört in
   `session_status.py` — eine Kit-Datei, für diesen Strom verboten.
3. **Was die Klassifikation nicht sieht** (H86): ein V1-Speicher außerhalb des
   Zustandsverzeichnisses (`docs/old/tasks.yaml` → `greenfield`, gemessen), ein umbenannter im
   Zustandsverzeichnis (`tasks.yaml.bak` → `greenfield`, gemessen; das ist `L19`), einer im
   Kernelbereich (`L20`). Alle drei sind Grenzen **eines** Lesers, den zwei andere Stellen des
   Kernels schon benutzen; sie zu schließen hieße, eine zweite Definition von „V1-Datensatz" zu
   schreiben.
4. **Was der Rollback nicht rückgängig macht** (H88): die Merge-Rückstandsliste des NEUEN Kits
   überlebt dessen Rücknahme; Sicherungen von vor dieser Runde tragen kein `RESTORE_SET` und werden
   mit Grund verweigert statt geraten.
5. **`mixed` wird installiert, nicht verweigert.** Begründung im Code: ein `mixed`-Bestand HAT eine
   lebende V2-Installation, das Update betrifft genau die, und die V1-Reste sind ein Befund, den der
   Validator ohnehin bei jedem Lauf macht. Verweigern hieße, jedes Projekt zu blockieren, das je
   einen Rest getragen hat. Der Preflight sagt es dafür laut.

## 8. Nahtstellen für die Merge-Runde (außerhalb meines Bereichs, nicht angefasst)

* **S1 — `team-kits/kernel/cli.py`:** `pin-kit` / `unpin-kit` / `rollback-kit` fehlen. Die
  Mechanismen sind da (`kitupdate.pin_in_force`, `assert_not_pinned`, `previous_bundle`,
  `restorable`, `rollback_command`); es fehlen drei Unterkommandos.
* **S2 — `session_status.py` (alle drei Kits, gespiegelt):** ein Satz, der einen bestehenden Pin
  nennt, statt das Update anzubieten. Gemessene Kette in H87.
* **S3 — `README.md`:** die Kommandoflächen-Liste (Zeile 333) und der Update-Abschnitt (ab 748)
  kennen weder Pin noch Rollback. `README.md` liegt nicht in meinem `allowed_scope`.
* **S4 — Item-Korrektur `FR-0046`:** die Behauptung „ALL THREE are the update-kit path … NOT
  migration" ist an den Kopien widerlegt (§4). Das Item sollte der Lead korrigieren, bevor jemand
  daraus einen Auftrag erzeugt.
* **S5 — beide Ströme stempeln:** die drei `VERSION`-Dateien tragen meinen provisorischen Stempel
  `2026.09.02-1`; die Merge-Runde stempelt neu (DEC-0057 (d)).
* **S6 — `tools/test_hooks_v2.py`** ist eine geteilte Datei; mein Eingriff dort ist auf **einen**
  Testkörper begrenzt (27 Zeilen), damit die Naht klein bleibt.

## 9. Arbeitsverzeichnisse

Alles unter `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0101\`:
`probe/` (Messskripte), `pilots-master/` (die drei Kopien, wiederverwendbar), `field-runs/`
(die Läufe), `redfirst/` (der Rot-Klon), `stream-rollout.patch`, `field-report-*.json`.
Die Master unter `C:\Offline Repos\v2-pilot\` sind unangetastet.


---

## 10. Nacharbeit nach dem Prüfer-FAIL (2026-09-01/02)

Sechs Befunde, **alle geschlossen**, keiner als Loch abgelegt. Je Fix ein Klon außerhalb des Repos
(`_round-scratch/TSK-0101/redfirst`, robocopy ohne `.git`), EINE Mutation zurück, `bump_kit_version`,
roter Lauf.

### B1 (blockierend) — eine unvollständige Lesung war eine MELDUNG, keine ENTSCHEIDUNG

Der Prüfer maß an einer echten BuyPlugGo-Kopie mit **einer** unbalancierten `[`: Verdikt
`greenfield`, Installer **rc 0**, +132/−1/~58 Dateien, `.claude/kernel` über den V1-Zustand
installiert — während die gedruckte Zeile sagte, die Einschätzung könne zu kurz sein. Zwei
Kommentare behaupteten dabei Schutz, den der Code nicht baute.

**Gebaut:** ein **fünftes Verdikt** `unknown`, und zwar als Ableitung statt als Sonderfall — die
vier alten Verdikte beschreiben eine Lesung, die FERTIG wurde. Wo eine unvollständige Lesung die
Entscheidung ändern kann, ist genau eine Stelle: liegt schon ein V1-Datensatz vor, steht das
Verdikt fest; besitzt der Kernel einen eigenen Bereich, sind die Reste `v2` und `mixed` und **beide
werden geschrieben**; fehlt beides, stehen `greenfield` und `v1` gegeneinander. Nur dort ist
„nicht hingesehen" nicht als „nichts gefunden" auflösbar.

**Nachgemessen an genau der Kette des Prüfers** (dieselbe BuyPlugGo-Kopie, dieselbe `[`):
`stock: unknown`, Installer **rc 1**, **0** Dateien hinzugefügt/geändert/gelöscht, kein Kernel
installiert.

**Rot:** `test_a_document_the_reading_could_not_open_is_its_own_verdict` und —
**an der Entscheidung, nicht an der Meldung** — `test_a_stock_whose_reading_did_not_complete_is_not_
written_over[powershell,bash]`: der rote Lauf meldet „the installer wrote over a stock it could not
read", also den Baum-Hash. Gegenrichtung gegen Über-Verweigerung:
`test_a_reading_that_did_not_complete_over_a_LIVE_v2_project_still_installs` (bleibt in der
Mutation grün).

**Korrigiert:** beide Kommentare in `kitupdate.py` und `H86` — dort steht der Fall jetzt als
**(e) GESCHLOSSEN** mit dem Satz, den er gekostet hat: *eine Meldung ist kein Schutz*. Das alte
Urteil „(d) ist kein Loch, sondern der bezahlte Preis" bezog sich nur auf die Laufzeitkosten und
steht so nur noch dafür.

### B2 (blockierend) — ein Kommentar nannte einen Test, den es nicht gab

`scaffold_team.sh` verwies auf `test_an_aborted_install_restores_the_trust_record_with_the_bundle`;
den gab es nicht, und der reale Rollback-Test sagt in seinem Docstring ausdrücklich „not an aborted
run". **Statt den Namen zu streichen ist der Test gebaut**, weil der Abbruchpfad erzwingbar ist:
nach einer echten Installation wird `.codex` durch eine **Datei** ersetzt, der letzte Schritt des
Installers (`gen_provider_artifacts.py`) scheitert daran, und der Lauf rollt sich selbst zurück.
`tools/test_kitupdate.py::test_an_aborted_install_puts_the_trust_record_back_with_the_bundle`,
beide Zwillinge, grün. **Rot** in der Mutation „`.claude/kit_state.json` aus der Restore-Menge
entfernt" (zusammen mit den zwei Rollback-Fällen: 4 rot).

### B3 (Sicherheit) — ein Pin auf eine Versionszeichenkette ließ einen KIT-TAUSCH durch

`bump_kit_version.py` stempelt alle drei Kits auf denselben Stand; der Prüfer maß: gepinnt auf
`dev-team 2026.09.01-4`, `scaffold_team office-team` → **rc 0**, +114 Dateien, Durchsetzungsschicht
und Verfassung ersetzt, Pin schweigt.

**Gebaut:** der Pin hält ein **Bundle**. Verglichen wird das **Kit** — aus der `kit:`-Zeile des
Datensatzes, sonst aus dem Besitzmanifest der Installation (`pinned_kit`) — plus **jedes
Stempelfeld, das der Datensatz nennt**. Ein Feld, das er nicht nennt, wird nicht erfunden:
`content:` ist der exakte Baum, und es von einem Pin zu verlangen, der nur eine Version nennt,
machte aus jeder Reparatur eine Verweigerung. **Rot:**
`test_a_pin_does_not_let_another_kit_in_at_the_same_version` (beide Richtungen: fremdes Kit als
Argument, und ein Datensatz, der selbst ein anderes Kit nennt).

### B4 (Sicherheit) — der Rollback lief VOR dem Pin und hinterließ eine Falle

Gemessen: gepinnt auf 2099.12.31-9, `--rollback` → rc 0, Stempel zurück auf 2026.09.01-4, Pin
bleibt — und danach ließ der Pin **weder** Update **noch** Reparatur durch, weil das einzige
zugelassene Bundle nicht mehr installiert war.

**Gebaut:** der Rollback-Zweig beider Zwillinge fragt jetzt zuerst den Preflight im Modus
`rollback`, der genau eine Frage stellt (`assert_no_pin_blocks_a_rollback`). Der Interpreter wird
dafür vor dem Zweig aufgelöst; die Klassifikation läuft dort **nicht** — ein Rollback schreibt kein
neues Bundle über einen fremden Bestand, sondern eines zurück, das dieses Projekt schon lief.
**Rot:** `test_a_pin_stops_a_rollback_in_both_twins[powershell,bash]` (rc 0 statt Verweigerung),
plus die Kernel-Hälfte `test_a_pin_stops_a_rollback_too`. Beide Tests prüfen auch die
Gegenrichtung: ohne Pin läuft derselbe Rollback.

### B5 (Sicherheit) — der POSIX-Zwilling löschte AUSSERHALB des Repositoriums

Neu durch diese Runde: `assert_safe_repo_path` bekommt seit dem Restore-Manifest **Dateidaten**
vorgelegt. Der Prüfer maß mit `../victim.txt` in einer `RESTORE_SET`: bash **rc 0** und die Datei
**gelöscht**, PowerShell rc 1 (dort löst `GetFullPath` auf). Ursache: der `case`-Vergleich gegen
`"$REPO"/*` ist textuell.

**Gebaut:** beide Zwillinge verweigern ein Wort mit `..`-Bestandteil — als Regel darüber, woher
die Wörter KOMMEN (der Installer setzt seine selbst zusammen und erzeugt nie einen Elternschritt),
nicht als Normalisierung. Die Verweigerung greift, bevor irgendetwas gelöscht wird: erst werden
alle Zeilen geprüft, dann zurückgespielt. **Rot:**
`test_neither_twin_replays_a_snapshot_that_points_out_of_the_repository[powershell-bash]` — und die
erste Zusicherung des Tests ist die **Löschung**, der rote Lauf meldet also „the rollback deleted a
file outside the repository". Die Richtung `bash-powershell` bleibt in der Mutation grün, weil
`GetFullPath` sie schon dort fing; genau darum werden **beide** Leserichtungen gefahren.
Der Docstring von `test_both_installer_twins_record_the_same_restore_set` behauptete die
Leserichtung, ohne sie zu messen — er sagt jetzt, was er misst, und nennt den neuen Test.

### B6 (klein) — eine Verweigerung nannte 7 Dokumente und listete 5

`_v1_summary` hängt jetzt „and N more" an. **Rot:**
`test_a_refusal_that_lists_five_documents_says_how_many_it_did_not_list`.

### Eine Reihenfolge, die dabei gemessen und geändert wurde

Der Preflight stand vor der Konfigurationsprüfung; mein Kommentar begründete das mit „ein
V1-Bestand hat keine V2-`project_config.yaml`". **Das ist an den echten Beständen widerlegt:** alle
drei Feldkopien tragen eine Vor-Kernel-Konfiguration und alle drei bestehen
`gen_provider_artifacts.py --check-config-only` (rc 0, gemessen 2026-09-02). Er stand damit vor
einer Prüfung, die eine eigene, konkretere Meldung für dieselbe Datei hat — sichtbar geworden an
`tools/test_hooks.py::test_scaffold_preset_and_map_sync`, dessen absichtlich kaputte
`project_config.yaml` meine Verweigerung statt der Provider-Meldung bekam. Der Preflight liegt
jetzt **hinter** den beiden Prüfungen, die eine eigene Datei besitzen, und weiter **vor** jedem
Schreibzugriff. Beide Reihenfolgen sind sicher (beide verweigern, beide schreiben nichts); die
Meldung, auf die ein Leser handeln kann, entscheidet. Der Kommentar trägt jetzt diese Messung.

### Suiten nach der Nacharbeit

| Suite | Ergebnis |
|---|---|
| `tools/test_kitupdate.py` + `tools/test_user_defaults.py` (ganz) | **79 passed, 1 skipped** (6:52) |
| `tools/test_hooks.py -k "scaffold or preset or settings"` | 30 passed, 6 skipped (3:25) |
| `tools/test_hooks_v2.py -k "kernel_as_one_layer or scaffold"` | 11 passed |
| `tools/test_presets.py` + `tools/test_repo_hygiene.py` | 42 passed |
| Feldtest neu gefahren (alle drei Kopien, frisch kopiert) | je `v1`, rc 1, **wrote_nothing: true** |
| Feldtest B1-Kette (BuyPlugGo mit `[`) | `unknown`, rc 1, **0 Dateien**, kein Kernel |
| `python -m ruff check .` · `python tools/validate.py` | sauber |

**Löcherlisten-Drähte geprüft:** jeder in `docs/POST_V2_WISHLIST.md` in Backticks genannte Name der
Form `tools/test_*.py::test_*` wurde über den AST der Testdateien aufgelöst — 33 genannt, **32
lösen auf**; der eine Rest ist `tools/test_report.py::test_x`, ein **Platzhalter in Prosa** aus
einem fremden Eintrag (er erklärt gerade, dass solche Namen von niemandem nachgeschlagen werden).
Dasselbe über die sechs von mir geänderten Dateien: **0 unaufgelöste Nennungen**. Einen
ausgelieferten Stolperdraht dafür habe ich **nicht** gebaut: er müsste genau diesen Platzhalter
ausnehmen, und eine Ausnahmeliste ist der Defekt, den die Hausregel meint. Das bleibt benannt.

### Was die Nacharbeit NICHT geschlossen hat

Nichts Neues. Die reservierten Nummern **H96–H98 sind nicht benutzt**; B1–B6 sind geschlossen, und
die vorhandenen Einträge H86/H87/H88 sind auf den gebauten Stand korrigiert — H86 um **(e)**, H87 um
die beiden Pin-Erweiterungen und das Urteil „an allen DREI Türen gemessen", H88 um **(a2)**
(Traversal) und den nachgereichten Abbruchtest.
