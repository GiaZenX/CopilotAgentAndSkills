# TSK-0116 — Strom B „Büro-Finanzen" (Generation 3, DEC-0062)

Worktree `C:/Offline Repos/v2-testbed/_worktrees/g3-office` (Branch `g3/office`, Basis e45c0ca).
Scratch ausschließlich `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0116/`.
Patch: `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0116/stream-office.patch`.

---

## 1. Vorgefunden

Gelesen: `FR-0076`, `TSK-0116.yaml`, `docs/POST_V2_WISHLIST.md` (H123, H125),
`_round-scratch/TSK-0114/probe_h125.py`, `staging/generation-2-streams.md`,
`staging/TSK-0107/`, `staging/TSK-0113/stream-protocol.md` (F6, I3),
`staging/TSK-0109/build-protocol.md` (N2.3.1/N2.3.2, N4.1) + `user-feedback.md`,
`DEC-0053/0056/0062/0063`, die vier Office-Vorlagen, `euer_report.py`,
`finance_dashboard.py` + Template, `guard_fs_tripwire.py`, `_filing.py`, `_duties.py`,
`kernel/filing.py`, und die Office-Registrierung `settings/settings.json` (nur lesend).

**Die acht auf `Bash|PowerShell` registrierten Office-Haken**, aus der Registrierung gelesen, nicht
erinnert: `guard_fs_tripwire`, `gate_ledger_valid`, `gate_second_booking`, `gate_write_scope`,
`gate_push_token`, `gate_shell_hygiene`, `gate_filing`, `gate_second_reading`. **Kein einziger
Eintrag nennt ein `timeout`.**

**Vorgefundener Stand, am ausgelieferten Baum gelesen:**

- `master_data.yaml` liefert `categories: {expense: [], income: []}` — das Vokabular steht nur als
  Kommentar, `euer_line` ist dort ein Freitext-Etikett, keine Zeilennummer. Das ist die
  P4-12/BUG-0071-Kette.
- `euer_report.py` summiert nur „## Nach Kategorie" und liest `master_data.yaml` gar nicht.
- `finance_dashboard.py` zeigt dasselbe Freitext-Etikett in der Spalte „Zeile Anlage EÜR".
- AfA: nichts. Kein Anlagenverzeichnis, keine Abschreibung, kein GWG-Wert irgendwo.
- `business_profile.yaml`: `kleinunternehmer: null` ohne Interview-Satz; **kein** `founding_year`,
  während `finance_dashboard.threshold` im Fall `previous_unknown` ausdrücklich sagt, dass das Feld
  fehlt.
- `kernel/filing.py` nimmt `retention` als Freitext (F6).
- `guard_fs_tripwire.DELETE_VERBS` ist ein Tupel aus sieben Verben (H125).

---

## 2. Plan und der verworfene Weg

**Der verworfene Weg, in einer Zeile (FR-0084-Form):** Verworfen wurde, die Zeilennummern der
Anlage EÜR **im Code** (als Zuordnungstabelle in `euer_report.py`) zu führen und
`master_data.yaml` unverändert zu lassen — das hätte die Vokabularlücke geschlossen, aber die
Nummern an den Kit-Stand gebunden statt an das Formularjahr, sodass jede Formularänderung ein
Kit-Update statt einer Zeile in einer Nutzerdatei gewesen wäre; FR-0076 verlangt ausdrücklich das
Gegenteil, und die Messung beim Quellenlesen (Abschnitt 5.4) bestätigt es.

**Zweiter verworfener Weg (H125):** Verworfen wurde, die Zerstörung **dateisystemseitig** zu
beantworten (Vorher/Nachher-Vergleich), wie H125 selbst es andeutet — ein `PreToolUse`-Haken läuft
*vor* der Zeile und hat kein Nachher; die Antwort müsste ein zweiter Prozess nach dem Werkzeug
sein, und der kann nicht mehr verweigern.

**Dritter verworfener Weg (H125, während des Baus verworfen und gemessen):** Eine Ausnahme in der
Zerstörungs-Vokabelliste für die quelllöschenden Kopier-Flaggen (`rsync --remove-source-files`,
`robocopy /MOVE`), abgeleitet aus `_filing.SOURCE_DELETING_FLAGS`. Gemessen: sie feuert **nie** —
`_filing` erkennt beide als Kopierer, der Kopier-/Bewegungszweig beantwortet die Aufrufung zuerst.
Eine Aufzählung, die nichts fängt, ist genau der Defekt dieser Runde; sie wurde entfernt und durch
die gemessene Reihenfolge ersetzt
(`tools/test_hooks.py::test_a_filing_move_with_a_source_deleting_copier_flag_is_judged_as_a_move`).

---

## 3. Nahttabelle

| # | Naht | Wohin | Warum nicht hier |
|---|---|---|---|
| S1 | Onboarding-Frage Steuerstatus (Wortlaut 7.1) | **Strom D** (`skills/office-manager/SKILL.md`) | `team-kits/*/skills/**` ist `forbidden_scope` |
| S2 | Onboarding-Frage Gründungsjahr (Wortlaut 7.2) | **Strom D** | dito |
| S3 | Satz für `records-clerk`/Office-Verfassung zur neuen Wächter-Eigenschaft (Wortlaut 7.3) | **Strom D** | `constitution/**`, `agents/**` verboten |
| S4 | `retention`-Frage beim MINTEN in den zwei ehrlichen Formen (`kernel/approvals.py`) — macht `retention: null` überhaupt erreichbar (H130) | **Strom C** | jede Kernel-Datei außer `filing.py` verboten |
| S5 | optionaler Melder über unlesbare `retention` im Kernel-Bericht (`kernel/report.py`) | **Strom C** | dito; heute meldet `_duties` das beim Sitzungsstart |
| S6 | `_duties._retention_years` auf `kernel.filing.retention_span` umstellen (die zweite Kopie auflösen) | **Strom C/D** (`office-team/hooks/_*.py`) | `hooks/_*.py` verboten |
| S7 | `tools/test_hooks.py`: dieser Strom fügt einen Block „H125" ein (vor dem FR-0050-Türabschnitt) und ändert **eine** Zeile in `test_a_fresh_office_project_files_its_first_document_without_the_user_editing_yaml` | **gemeinsam mit Strom A** | geteilte Datei; Kollisionsstellen unten benannt |
| S8 | Einstiegs-Interview `user/CLAUDE.md`: Steuerstatus + Gründungsjahr gehören in die Office-Onboarding-Fragen; das Kategorien-Vokabular muss der Einstieg NICHT mehr erfinden | **Lead** | `user/**` verboten |

**S7 im Detail, damit die Merge-Runde nichts sucht:** eingefügt ist ein zusammenhängender Block
direkt vor der Zeile
`# ---------------- FR-0050: the ONE approval-shaped door in that wall ----------------`
(Helfer `_tray_project`, `_guard_hooks_without`, `_guard` und sechs Tests). Die zweite Änderung ist
eine Zeile im FR-0031-Durchlauf: das Manifest bekommt statt des Draft-Platzhalters eine echte
Aufbewahrung, weil der Kernel den Platzhalter seit F6 verweigert.

---

## 4. Was gebaut wurde — Abnahmezeile je FR

### FR-0076 (1) — ausgeliefertes Standardvokabular mit Formularzeilen

`team-kits/office-team/templates/project_memory/master_data.yaml` liefert **15 Kategorien** aus
(12 Ausgaben, 3 Einnahmen), jede mit `euer_line` als **Zahl** und `euer_line_label` als
Formularbeschriftung, dazu einen Block `euer_form:` mit `year`, `source` und `gwg_limit_net`.
Umbenennen und Ergänzen bleibt offen; eine Kategorie, die das Ledger führt und das Vokabular nicht
kennt, bleibt als Rohschlüssel sichtbar und landet in der Gruppe „ohne Zeile".

> **Abnahme:** Ein frisches Projekt startet mit einem gefüllten Vokabular; jede ausgelieferte
> Kategorie trägt Schlüssel, deutsches Etikett und eine Zeilennummer, die der Berichtsleser als
> ganze Zahl liest; Formularjahr und Herkunft stehen in der Datei und nicht im Code. Gemessen an
> der geparsten Vorlage **und** an einer erzeugten Seite:
> `tools/test_finance_dashboard.py::test_a_fresh_project_ships_a_category_vocabulary_the_p4_12_stall_cannot_recur_on`.

### FR-0076 (2) — Summen je Formularzeile, Bericht und Seite in Parität

`scripts/euer_report.py` liest das Vokabular (`read_vocabulary`), gruppiert die bezahlten Buchungen
zusätzlich je Formularzeile (`by_form_line`) und druckt den Abschnitt „## Nach Zeile der Anlage EÜR
`<Jahr>`" mit Herkunftszeile. Der EÜR-Reiter des Dashboards rendert dieselben Zeilen aus
**derselben** Funktion (`line_table_html` ruft `euer_report.by_form_line`).

> **Abnahme:** Für acht Quartale (zwei Fixtures) stimmen die Überschriften und beide Beträge je
> Zeile zwischen dem erzeugten Bericht und der erzeugten Seite überein, und die Summe aller
> Zeilenbeträge ist dieselbe wie die Kategoriensumme desselben Quartals:
> `tools/test_finance_dashboard.py::test_the_dashboard_and_the_report_agree_on_every_form_line`,
> `tools/test_finance_dashboard.py::test_the_per_line_sums_and_the_per_category_sums_are_the_same_money`.

### FR-0076 (3) — AfA nur als Hinweis

`euer_report.asset_hints` markiert eine bezahlte **Anschaffung** (Ausgabe, keine Korrektur), deren
**Netto** die GWG-Grenze aus dem Vokabular übersteigt, mit dem Satz `ASSET_HINT` =
„Anlagegut — mit der Steuerberatung klären". Kein Anlagenverzeichnis, keine Abschreibungsrechnung,
kein Zweig auf die Rechtsform. Bericht und Seite sagen denselben Satz aus derselben Konstante und
beide schreiben dazu, dass der **Beleg** gemessen wird und nicht die einzelne Position. Der
Rechtshinweis (`DISCLAIMER` im Bericht, „keine Steuerberatung" auf jedem Reiter) bleibt.

> **Abnahme:** Eine Buchung über der Grenze wird markiert, eine darunter nicht; der Hinweis ist ein
> Satz und keine Zahl (nirgends ein Abschreibungsbetrag); und dieselbe Buchung wird **nicht** mehr
> markiert, wenn allein `euer_form.gwg_limit_net` in `master_data.yaml` erhöht wird — das ist die
> Messung dafür, dass die Grenze ein Vokabularwert und keine Konstante ist:
> `tools/test_finance_dashboard.py::test_the_afa_hint_is_a_flag_whose_limit_comes_from_the_vocabulary`.
> Der Nutzerhebel je Kategorie (`afa_hint: false`, wie `second_reading` nur der Boolean) ist an
> beiden Enden gemessen:
> `tools/test_finance_dashboard.py::test_a_category_can_switch_the_afa_hint_off_and_only_the_boolean_false_does_it`.

### Nähte aus Generation 2, hier geschlossen

**`kleinunternehmer: null` mit dem Interview-Satz.** Der Wortlaut aus dem G-Nahtabschnitt des
I-Protokolls (`staging/TSK-0109/build-protocol.md`, N2.3.1) steht jetzt wörtlich als Kommentar über
dem Feld, ergänzt um die Interview-Frage selbst und um den Satz, warum `null` ausgeliefert wird.

**`founding_year` — angelegt, WEIL es jetzt einen Leser gibt.** Die Begründung aus I3 hatte drei
Teile; der erste („in diesem Baum existiert kein Leser") ist seit TSK-0109 **falsch**:
`finance_dashboard.threshold` sagt im Zustand `previous_unknown` ausdrücklich, dass das Feld fehlt.
Das Feld ist mit seinem Leser zusammen angelegt: ist `tax.founding_year` gleich dem Ledgerjahr, gilt
für das laufende Jahr die 25.000-EUR-Grenze und die Seite entscheidet; ist es ein früheres Jahr,
fehlt nur die Vorjahresdatei und die Seite verweigert weiter — mit **zwei verschiedenen** Sätzen
statt des einen, der bis jetzt für beide Fälle sprach und über ein Feld sprach, das es nicht gab.
Der Onboarding-Satz ist Naht S2.

**`tax_state` unverändert.** Die drei Fälle aus Strom I (`True` → § 19, `False` → Regelbesteuerung,
alles andere → unbekannt) sind nicht angefasst; die bestehende Messung
(`test_only_a_boolean_answers_the_tax_question`) läuft unverändert grün.

**F6 — der Kernel prüft die Aufbewahrung.** `kernel/filing.py` bekommt `retention_span` und
`retention_refusal`; `apply` verweigert eine Regel, deren Aufbewahrung keine Spanne in Jahren nennt,
**bevor** die Freigabe überhaupt nachgeschlagen wird, und lässt die Datei byte-identisch.

> **Abnahme:** Der Platzhalter des ausgelieferten Entwurfs, ein Satz ohne Zahl und ein
> ausgeschriebenes „acht Jahre" werden verweigert; eine zählbare Spanne geht unverändert in den
> Plan; die Datei bleibt bei jeder Verweigerung byte-identisch:
> `tools/test_kernel.py::test_a_retention_the_deadline_register_cannot_read_is_refused_before_it_reaches_the_plan`.
> Dass Kernel und Fristenregister dieselbe Lesung haben, ist über einen Korpus gemessen:
> `tools/test_office_duties.py::test_the_kernel_and_the_duty_register_read_a_retention_the_same_way`.

**Folge, die dazugehört:** `scripts/filing_plan.py --draft` schrieb bisher
`"TBD - ask the Steuerberater"` in das Feld — genau den Wert, den der Kernel jetzt verweigert. Der
Platzhalter ist zu einem erkennbaren Platzhalter geworden
(`"<Aufbewahrung in Jahren -- mit dem Steuerberater klaeren>"`, weiter ohne Zahl, weiter mit
„Steuerberater"), und der Entwurf sagt jetzt, dass er ersetzt werden muss.

### H125 — geschlossen

`DELETE_VERBS` ist weg. An seiner Stelle steht eine Eigenschaft mit zwei Hälften, und nur eine ist
eine Definition:

- **WO** (Definition): eine Zerstörung REICHT an Positionen — die benannten Pfade, und wenn sie
  keine nennt, das Arbeitsverzeichnis. Verweigert wird, wenn diese Reichweite ein Fach von Rang
  trifft (`sweeps_a_tray` fragt dafür das Dateisystem).
- **WAS** (Vokabelliste, und sie bleibt eine): `NAMING_DESTRUCTION` / `SWEEPING_DESTRUCTION`,
  gelesen über **jedes** Wort einer Aufrufung (Kommandowort, Flagge, Unterbefehl) und nach
  **Wortstamm** statt exakter Schreibweise. Der Rest steht als `H129`.

> **Abnahme:** Am gescaffoldeten Piloten außerhalb des Repos, gegen alle acht registrierten
> Office-Haken als Prozesse, HEAD e45c0ca gegen diese Runde: sechs Zeilen von ALLOW auf rc 2, zwei
> Kontrollen unverändert rc 2, sechs Über-Verweigerungs-Kontrollen unverändert rc 0 (Abschnitt 5.1).
> Rot ohne den Fix:
> `tools/test_hooks.py::test_the_archive_guard_refuses_a_destruction_that_is_not_spelled_rm`,
> `tools/test_hooks.py::test_a_sweep_is_refused_only_where_a_tray_of_record_lies_under_it`,
> `tools/test_hooks.py::test_every_destroying_stem_is_load_bearing_at_both_ends`.

---

## 5. Die Messungen

### 5.1 H125 — acht Haken als Prozesse, HEAD gegen diese Runde

Rig: `_round-scratch/TSK-0116/probe_h125_v2.py`. Pilot: echtes git-Arbeitsverzeichnis außerhalb des
Repos mit der ausgelieferten `.gitignore` des Office-Kits und einem echten Beleg unter
`archive/finance/2026/` (git bestätigt: die Datei ist ignoriert und ungetrackt). Gefahren wird jede
Zeile durch **alle acht** Haken über `tools/test_hooks.py::run_hook_process`. **Nichts ausgeführt** —
gemessen wurde die Entscheidung.

| Befehlszeile | HEAD e45c0ca | TSK-0116 | wer verweigert |
|---|---|---|---|
| `unlink archive/finance/2026/invoice.pdf` | ALLOW | **rc 2** | `guard_fs_tripwire` |
| `git clean -fdx` | ALLOW | **rc 2** | `guard_fs_tripwire` |
| `git clean -fdx archive` | ALLOW | **rc 2** | `guard_fs_tripwire` |
| `Clear-Content archive/finance/2026/invoice.pdf` | ALLOW | **rc 2** | `guard_fs_tripwire` |
| `find archive -name x.pdf -delete` (H123-Form) | ALLOW | **rc 2** | `guard_fs_tripwire` |
| `tar --remove-files -cf out.tar archive/…` (H123-Form) | ALLOW | **rc 2** | `guard_fs_tripwire` |
| KONTROLLE `rm archive/finance/2026/invoice.pdf` | rc 2 | rc 2 | `guard_fs_tripwire` |
| KONTROLLE `mv archive/… inbox/…` | rc 2 | rc 2 | `guard_fs_tripwire` |
| `rm outbox/draft.txt` | ALLOW | ALLOW | — |
| `git clean -fdx docs` | ALLOW | ALLOW | — |
| `ls archive/finance/2026` | ALLOW | ALLOW | — |
| `cat archive/finance/2026/invoice.pdf` | ALLOW | ALLOW | — |
| `clear` | ALLOW | ALLOW | — |
| `python -c "import os; os.remove('archive/…')"` | ALLOW | ALLOW | — (das ist `H129`) |

**Die Über-Verweigerung, zweiter Lauf mit `--empty`** (derselbe Pilot ohne `archive/` und ohne
`inbox/`): `git clean -fdx` ist **ALLOW** — das ist die Abwägung, die H125 verlangt hat. Die
übrigen Zeilen bleiben dort verweigert, weil sie einen Fachpfad ausdrücklich **nennen**; das ist die
bestehende, pfadrelationale Lesung des Wächters und nicht neu.

### 5.2 Die Frist gegen die registrierte gemessen

Die Office-Registrierung nennt für **keinen** ihrer acht `Bash|PowerShell`-Einträge ein `timeout`
(aus `settings/settings.json` gelesen: `{None}`). Die wirksame Frist ist damit das
Provider-Standardfenster, das dieselbe Datei mit ~600 s dokumentiert;
`_compat.HOOK_DEADLINE_SECONDS = 60.0` ist das Budget, das die Haken sich selbst geben.
**Langsamster einzelner Haken-Prozess über alle 14 gemessenen Zeilen × 8 Haken × 2 Bäume:
0,446 s** — 0,74 % des Selbstbudgets, rund 0,07 % des Standardfensters.

### 5.3 Der verworfene Ausnahme-Eintrag (gemessen, nicht überlegt)

`rsync --remove-source-files inbox/scan.pdf archive/finance/2026/scan.pdf` ist mit und ohne die
Ausnahme rc 0. Erst wenn `_filing.DUPLICATING` in einer Kopie `rsync` nicht mehr kennt, wird die
Zeile rc 2 — also trägt die **Reihenfolge** der Lesungen die Antwort, nicht die Ausnahme. Die
Ausnahme ist entfernt, die Reihenfolge im Kopf des Wächters benannt und beidseitig gemessen.

### 5.4 Die Zeilennummern — was gelesen wurde und was daraus folgt

Gelesen am 2026-09-03: drei öffentliche Ausfüllhilfen zur Anlage EÜR. Befund: dieselbe Beschriftung
steht je nach Formularjahr auf verschiedenen Zeilen (Waren/Roh-/Hilfsstoffe: 25 in einer undatierten
Hilfe, 27 für 2024 und für 2025), und zwei Hilfen widersprachen sich bei der Werbe-Zeile (51 gegen
54). **Der amtliche Vordruck wurde nicht gelesen und wird nicht mitgeliefert.** Genau das ist der
Grund, warum Jahr und Herkunft im Vokabular stehen und im Code keine Nummer und kein Jahr: eine
Korrektur ist eine Zeile in einer Nutzerdatei. Steht als `H131` mit dieser Messung.

### 5.5 Zwei Zeilen, die beim Bau selbst gemessen wurden

- Der erste Schnitt der AfA-Tabelle trug `class="ledger open"`. Gemessen an der Browser-Suite: das
  Seitenskript läuft über `table.ledger.open tbody tr` und rechnet daraus die Mahnkandidaten — die
  Zählung auf dem Reiter „Offene Posten" wurde falsch
  (`test_dunning_candidates_follow_the_frozen_clock` rot). Klasse geändert, Test wieder grün.
- Der erste Schnitt des AfA-Hinweises markierte im `regular`-Fixture sechs Wareneinkäufe, alle über
  800 EUR netto und keiner davon ein Anlagegut. Daraus wurde der Nutzerhebel `afa_hint: false` (im
  Vokabular, nicht im Code) und der Satz, dass der BELEG gemessen wird; die ausgelieferte Vorlage
  schaltet ihn für `goods` mit dem Grund daneben ab.

---

## 6. Rot zuerst — elf Messungen in einer Kopie außerhalb des Repos

Rig: `_round-scratch/TSK-0116/red_first.py`. Es kopiert den Worktree nach
`_round-scratch/TSK-0116/red/` **ohne dessen `.git`-Datei**, stellt je Fix den ursprünglichen Defekt
wieder her, fährt den Test, verlangt Rot, setzt zurück und verlangt wieder Grün.

| Defekt, wiederhergestellt | Test | grün | ROT | zurück |
|---|---|---|---|---|
| Vokabular liefert wieder leer aus (P4-12) | `…::test_a_fresh_project_ships_a_category_vocabulary_the_p4_12_stall_cannot_recur_on` | 1 passed | **1 failed** | 1 passed |
| Bericht summiert nur je Kategorie | `…::test_the_dashboard_and_the_report_agree_on_every_form_line` | 2 passed | **2 failed** | 2 passed |
| kein AfA-Hinweis | `…::test_the_afa_hint_is_a_flag_whose_limit_comes_from_the_vocabulary` | 1 passed | **1 failed** | 1 passed |
| GWG-Grenze als Konstante im Code | dasselbe | 1 passed | **1 failed** | 1 passed |
| `founding_year` wird nicht gelesen | `…::test_the_founding_year_decides_the_case_the_missing_previous_year_leaves_open` | 1 passed | **1 failed** | 1 passed |
| Profil beantwortet den Steuerstatus ab Werk | `…::test_the_shipped_profile_leaves_the_tax_status_and_the_founding_year_unanswered` | 1 passed | **1 failed** | 1 passed |
| Kernel nimmt jede Aufbewahrung | `test_kernel.py::test_a_retention_the_deadline_register_cannot_read_is_refused_before_it_reaches_the_plan` | 1 passed | **1 failed** | 1 passed |
| die zwei Aufbewahrungs-Leser driften | `test_office_duties.py::test_the_kernel_and_the_duty_register_read_a_retention_the_same_way` | 1 passed | **1 failed** | 1 passed |
| H125: wieder das Tupel aus sieben Verben | `test_hooks.py::test_the_archive_guard_refuses_a_destruction_that_is_not_spelled_rm` | 6 passed | **6 failed** | 6 passed |
| H125: Fegen wird überall verweigert | `test_hooks.py::test_a_sweep_is_refused_only_where_a_tray_of_record_lies_under_it` | 1 passed | **1 failed** | 1 passed |
| H125: zerstörende Wörter nur am Kommandowort | `test_hooks.py::test_every_destroying_stem_is_load_bearing_at_both_ends` | 15 passed | **3 failed, 12 passed** | 15 passed |

Dazu die beiden Stolperdrähte, die **innerhalb** der Tests mutieren (Kopie der Haken, ein Eintrag
entfernt, Haken als Prozess): 15 Wortstämme je an beiden Enden, und die Reihenfolge der Lesungen
gegen `_filing.DUPLICATING`.

---

## 7. Nähte, wörtlich (hier NICHT geschrieben)

### 7.1 S1 — Onboarding-Frage Steuerstatus → Strom D

> „Bist du Kleinunternehmer nach § 19 UStG — weist du also keine Umsatzsteuer aus? (ja/nein)"

Die Antwort geht als `true` oder `false` nach `business_profile.yaml` → `tax.kleinunternehmer`.
**Nur diese beiden Werte sind eine Antwort**; alles andere liest das Dashboard als „nicht
beantwortet" und zeigt dann weder USt-Summen noch eine Zahllast. Der Satz steht seit dieser Runde
als Kommentar in der Vorlage; ein Interview, das ihn nicht stellt, lässt das Projekt dauerhaft im
Zustand „unbekannt".

### 7.2 S2 — Onboarding-Frage Gründungsjahr → Strom D

> „In welchem Jahr hast du das Geschäft angemeldet?"

Die Antwort geht als vierstellige Jahreszahl nach `business_profile.yaml` → `tax.founding_year`.
Ohne sie kann die § 19-Wache den Fall „kein Vorjahr im Ledger" nicht entscheiden und verweigert die
Aussage (was sie tut, korrekt).

### 7.3 S3 — Satz für `records-clerk` und die Office-Verfassung → Strom D

> „Der Archiv-Wächter fragt nicht mehr nach einem Lösch-Verb, sondern nach der Reichweite einer
> Zerstörung: eine Befehlszeile, die etwas entfernt oder leert und dabei `inbox/` oder `archive/`
> erreicht, wird verweigert — auch dann, wenn sie gar keinen Pfad nennt (`git clean -fdx`). Was er
> trotzdem nicht sieht, steht in seinem eigenen Kopf unter „WHAT THIS DOES NOT SEE"; lies das dort,
> statt dich auf eine Zusammenfassung zu verlassen."

Nichts an diesem Satz behauptet Vollständigkeit — das ist Absicht und derselbe Grund, aus dem
TSK-0114 die absoluten Zusagen aus Verfassung und Rollentext genommen hat.

### 7.4 S4/S5/S6 — Kernel- und Haken-Nähte → Strom C (bzw. C/D)

- **S4 (`kernel/approvals.py`, H130):** `filing_rule_subject_manifest` verweigert eine Regel ohne
  Aufbewahrung, also ist die zweite ehrliche Form (`retention: null`) über `add-filing-rule` nicht
  erreichbar. Vorschlag: die Frage in den zwei Formen stellen („eine Spanne in Jahren, oder
  ausdrücklich keine") und eine ausdrückliche „keine"-Antwort als leeren Wert zulassen.
- **S5 (`kernel/report.py`):** optional — ein Rollup über Regeln, deren Aufbewahrung unlesbar ist.
  Heute meldet `_duties` das beim Sitzungsstart; der Kernel-Bericht wäre die kit-unabhängige Hälfte.
- **S6 (`office-team/hooks/_duties.py`):** `_retention_years` auf `kernel.filing.retention_span`
  umstellen. Bis dahin gibt es zwei Kopien einer Definition, und sie werden gemessen statt
  versprochen (`test_the_kernel_and_the_duty_register_read_a_retention_the_same_way`).

### 7.5 S8 — Einstiegs-Interview → Lead (`user/CLAUDE.md`, verboten)

Zwei Punkte: (1) die Fragen 7.1 und 7.2 gehören in das Office-Onboarding; (2) der Absatz über die
Kit-Dokumente kann für das Office-Kit sagen, dass `master_data.yaml` seit dieser Runde **gefüllt**
ausgeliefert wird — der Einstieg muss dort kein Vokabular mehr erfinden, sondern nur noch prüfen,
ob die Kategorien zum Geschäft passen.

---

## 8. Was bewusst NICHT geschlossen, aber benannt ist

1. **`H129` — die WAS-Hälfte der Zerstörungsregel bleibt eine Vokabelliste.** Ob ein Programm eine
   Datei entfernt, ist aus der Befehlszeile nicht ableitbar. Gemessen offen:
   `python -c "import os; os.remove('archive/…')"` ist rc 0 durch alle acht Haken. Begrenzt durch
   den beidseitigen Stolperdraht je Eintrag, das Lesen über jedes Wort einer Aufrufung, und
   `DEC-0056` (der Gegner ist der Irrtum).
2. **`H130` — `retention: null` ist über `add-filing-rule` nicht erreichbar.** Gemessen im
   Kernel-Test. `kernel/approvals.py` liegt im `forbidden_scope`; Naht S4.
3. **`H131` — die Zeilennummern stammen aus Sekundärquellen.** Gemessen beim Lesen (Abschnitt 5.4).
   Begrenzt dadurch, dass Jahr und Herkunft im Vokabular stehen, beide Leser sie neben jede
   Zeilensumme drucken und im Code keine Nummer steht.
4. **Der Rest von `H123`** — eine Flagge, die im ZIEL löscht (`robocopy /MIR`, `rsync --delete`).
   Grund ist die Reihenfolge der Lesungen, und die ist beidseitig gemessen; der Eintrag ist
   entsprechend verkleinert statt geschlossen.
5. **Kein Zweig auf die Rechtsform.** FR-0076 schließt die GmbH aus; daraus einen `legal_form`-Zweig
   zu bauen wäre eine zweite, ungemessene Behauptung — und die Profilvorlage hält ausdrücklich fest,
   dass heute **nichts** im Kit diesen Wert prüft. Der AfA-Hinweis hängt deshalb an der Buchung, nicht
   an der Rechtsform. Bewusst so, hier benannt.
6. **Die Bewirtungsquote wird nicht gerechnet.** Zeile 63 ist beschränkt abziehbar; kein Bericht
   dieses Kits kürzt sie. Beide Leser schreiben hin, dass keine Quote und keine Obergrenze des
   Formulars eingerechnet ist.
7. **Der AfA-Hinweis misst den BELEG, nicht die Position.** Eine Rechnung über hundert Kleinteile
   sieht aus wie eine Maschine. Im Code, im Bericht und auf der Seite gesagt; der Nutzerhebel je
   Kategorie ist die Antwort darauf, die der Kit geben kann.
8. **Keine Sichtungsrunde für die zwei neuen Tabellen auf dem EÜR-Reiter.** TSK-0109 hat die Seite
   mit 54 gerenderten Bildern gesichtet; diese Runde hat die neuen Abschnitte **nicht** als Bild
   angesehen, nur im DOM gemessen. Das ist kein Loch mit Kette, aber eine offene Prüfung: die
   Merge- oder Design-Runde sollte den Reiter einmal ansehen, besonders bei 390 px.
9. **`PAYMENT_TERM_DAYS` bleibt eine Konstante im Generator.** Das Feld im Profil ist eine Naht aus
   Strom I an Strom G und wurde hier nicht mitgenommen — es gehört nicht zu FR-0076.
10. **Die Fixtures behalten `crossyear` in der alten Form** (Beschriftung statt Zahl). Absicht: der
    Zweig „diese Kategorie nennt keine Zeile" wird an einer echten Fixture und einer echten Seite
    gemessen und nicht nur an einer eingebauten Ersatzdatei.

---

## 9. Läufe, Stempel, Aufwand

**Testumfang nach DEC-0050** — die berührten Suiten, nicht die volle Suite (die gehört der
Merge-Runde):

| Lauf | Ergebnis |
|---|---|
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |
| `python -m pytest tools/test_repo_hygiene.py` | 25 passed (1:56) |
| `python -m pytest tools/test_hooks.py tools/test_kernel.py tools/test_office_duties.py` | 1096 passed, 13 skipped (15:33) |
| `python -m pytest tools/test_hooks.py tools/test_finance_dashboard.py` (Schlusslauf nach der letzten Korrektur) | 980 passed, 13 skipped (18:32) |
| `python -B -m pytest .claude/hooks/test_gates.py` | **488 passed, 1 failed** — siehe unten |

**Der eine rote Gate-Test ist keiner dieser Runde, und das ist gemessen.**
`test_gate3_answers_before_its_registration_however_costly_the_line_is_to_judge` misst die
WANDZEIT von Gate 3 dieses Repos (`.claude/hooks/gate_commit_evidence.py`) — eine Datei, die
dieser Strom nicht anfassen darf und nicht angefasst hat. Er scheitert im **unveränderten
Hauptrepo** auf demselben Host genauso: Worktree `assert 6.128 < 5.5`, Hauptrepo (sauber, e45c0ca)
`assert 6.252 < 5.5`. Der Test nennt den Fall in seiner eigenen Meldung: „under parallel load it is
BUG-0033". Im ersten vollen Lauf derselben Runde war er grün (489 passed) — er ist
lastabhängig. **Nicht von mir behoben, nicht von mir verschlechtert, hier benannt.**

**Spiegel-Regel.** Geändert sind ausschließlich office-eigene Dateien
(`office-team/hooks/guard_fs_tripwire.py`, die Vorlagen), `team-kits/kernel/filing.py` (eine einzige
Kopie, kein Spiegel), `tools/**` und `docs/**`. Kein gespiegelter Name ist berührt.
`guard_fs_tripwire.py` existiert **nur** im Office-Kit, und genau deshalb braucht sie **keinen**
Eintrag in `KIT_SPECIFIC_HOOKS`: dieses Tupel nennt Namen, die in mehreren Kits liegen und dort
absichtlich verschieden sind (heute `session_status.py`, `format_on_write.py`,
`document_trays.txt`, `ENFORCEMENT.md`). Die erste Fassung dieses Satzes behauptete einen Eintrag,
den es nicht gibt (Prüferbefund N1). Die Spiegel-Tests der Haken-Suite laufen im Lauf oben mit.

**Versionsstempel (provisorisch).** `python tools/bump_kit_version.py` →
dev-team `2026.09.03-1`, research-team `2026.09.03-1`, **office-team `2026.09.03-4`**
(viermal gestempelt, weil nach dem ersten Stempel noch zwei Korrekturen am Office-Kit kamen:
die Reichweiten-Antwort bei einem nicht platzierbaren Arbeitsverzeichnis und ein doppelter
Punkt in der Verweigerung; beide nach dem Stempel erneut gemessen).

**Aufwand (für die (g)-Tabelle aus DEC-0060).** Wanddauer bis zum ersten Bericht rund
**2 h 15 min** (Spawn ~07:40, Bericht 09:56 Ortszeit); Tokens rund **450 k**. Stufe: Opus. Davon
gingen rund 50 min in Suitenläufe (drei volle Haken-/Gate-Läufe à 15–22 min), die
nach DEC-0050 nur einmal am Ende nötig gewesen wären — sie liefen dreimal, weil zwei
Korrekturen nach dem ersten Schlusslauf kamen.

**Kein Commit, kein Push, keine Installation in den globalen Speicher.**


---

## 10. Nacharbeit 1 (Prüfurteil FAIL: B 2 / M 2 / N 6)

### 10.1 B1 — die Reichweite wurde nur in EINER Richtung gelesen

**Gefunden.** `swallows_a_tray` gab es noch nicht; gefragt wurde ausschließlich „liegt der Operand
UNTER einem Fach". Damit war jede Zeile, die die Projektwurzel oder das Arbeitsverzeichnis benennt,
ALLOW — obwohl sie dieselben Belege löscht wie die Zeile ohne den Punkt. Der Beweis, dass
beide dieselbe Zerstörung sind, kommt vom Befehl selbst: `git clean -ndx` und `git clean -ndx .`
drucken zeichengleich „Would remove archive/…".

**Gebaut.** Die Reichweite wird beidseitig gelesen. `swallows_a_tray(root, base, token)` fragt, ob
ein Fach von Rang IN dem liegt, was der Operand benennt; ein Operand, der die Wurzel oder das
Arbeitsverzeichnis benennt, ist damit dieselbe FEGENDE Form wie eine Zeile ohne Pfad — die
beiden werden mit **einem** Leser beantwortet (`WORKING_DIRECTORY` ist der Pfad, der das
Arbeitsverzeichnis benennt), statt mit zwei Zweigen, die auseinanderlaufen können. Dazu: das
Wort hinter einer Ausschluss-Flagge (`-e <muster>`, `--exclude <muster>`) ist kein Pfad, den die
Zeile anfasst, und verengt darum kein Fegen (`EXCLUDING_FLAGS`, beide Enden gemessen).

**Der Verweigerungstext.** Er lautete „Run the destruction with the paths it should really touch,
outside inbox/ and archive/" — er schickte den Irrtum in die Umgehung. Er sagt jetzt
ausdrücklich, dass das Benennen von Wurzel oder Arbeitsverzeichnis dieselbe Verweigerung ist,
dass Umschreiben kein Weg heraus ist, und dass die Frage dem NUTZER gehört.

**Gemessen** (Rig `_round-scratch/TSK-0116/probe_h125_v3.py`, gescaffoldeter Pilot außerhalb des
Repos, echter Beleg unter `archive/finance/2026/`, alle acht registrierten Office-Haken als
Prozesse über `tools/test_hooks.py::run_hook_process`, nichts ausgeführt):

| Befehlszeile | HEAD e45c0ca | erster Schnitt | Nacharbeit 1 |
|---|---|---|---|
| `git clean -fdx .` | ALLOW | ALLOW | **rc 2** |
| `git clean -fdx ./` | ALLOW | ALLOW | **rc 2** |
| `git clean -fdx -e docs` | ALLOW | ALLOW | **rc 2** |
| `rm -rf .` | ALLOW | ALLOW | **rc 2** |
| `find . -name '*.pdf' -delete` | ALLOW | ALLOW | **rc 2** |
| `Remove-Item -Recurse -Force .` (tool_name Bash) | ALLOW | ALLOW | **rc 2** |
| `Remove-Item -Recurse -Force .` (tool_name PowerShell) | ALLOW | ALLOW | **rc 2** |
| `shred .` | ALLOW | ALLOW | **rc 2** |
| `clc archive/…/invoice.pdf` (N2, Alias) | ALLOW | ALLOW | **rc 2** |

**Kontrollen, alle unverändert:** `rm archive/…` und die Bewegung aus dem Archiv bleiben
rc 2; `git clean -fdx docs`, `rm outbox/draft.txt`, `ls`, `cat`, `clear` bleiben rc 0; **alle acht
Vorfahren-Formen in einem Projekt OHNE Fach von Rang bleiben rc 0** (Lauf mit `--empty`), während
Zeilen, die einen Archivpfad ausdrücklich NENNEN, dort weiter verweigert werden — das ist die
bestehende, pfadrelationale Lesung und nicht neu.

**Rot ohne den Fix:**
`tools/test_hooks.py::test_a_destruction_that_names_an_ANCESTOR_of_a_tray_is_the_same_destruction`
(7 Fälle, beide Tool-Namen) → 7 passed → **7 failed** → 7 passed;
`tools/test_hooks.py::test_an_exclusion_flag_does_not_narrow_a_sweep` → **1 failed**.

### 10.2 M1 — das Fegen wurde gegen die falsche Basis gemessen

**Gefunden.** `sweeps_a_tray` lief über ALLE Basis-Lesungen, und jede Liste enthält die
Projektwurzel — also war `git clean -fdx` mit `cwd=docs` und `cd docs && git clean -fdx` rc 2
für ein Archiv, das die Zeile gar nicht erreicht. Genau diese Über-Verweigerung bringt einen
Nutzer dazu, die Punkt-Schreibweise zu lernen, die B1 beschreibt.

**Gebaut.** `where_it_runs(root, bases)` wählt die TIEFSTE Lesung. Der Auftrag nannte „die letzte
aus `current`" — **das ist nicht die richtige Definition, und es ist gemessen**: die beiden
Erzeuger legen die echte Basis an entgegengesetzte Enden (`_filing.reading_bases` → `[root, cwd]`,
die echte LETZTE; `_filing._bases_after` → `[cd-Ziel, …, root]`, die echte ERSTE). Mit
`current[-1]` war `cwd=docs` rc 0 und `cd docs && …` weiter rc 2. Die Tiefe beantwortet beide.

**Gemessen:** `git clean -fdx` mit `cwd=docs` → **rc 0**; `cd docs && git clean -fdx` →
**rc 0**; `cd archive && git clean -fdx` → **rc 2**; `cd outbox && rm -rf .` → **rc 0**.
Der Testfall `cwd=docs` steht jetzt in
`tools/test_hooks.py::test_a_sweep_is_refused_only_where_a_tray_of_record_lies_under_it`, dazu die
`cd`-Schreibweise und die Gegenprobe `cd archive`. Rot ohne den Fix: **1 failed**.

**Der Preis, den diese Verengung zuerst kostete — in Nacharbeit 2 geschlossen.**
`_filing._bases_after` liest ein `cd` überall in einer Aufrufung, auch eines, das nur ein
Argument ist; solange das Fegen ALLE Basen fragte, konnte eine solche Fehl-Lesung nur
hinzufügen, seit es die tiefste wählt, konnte sie verengen. Gemessen war das eine aktive
Unter-Verweigerung (`echo cd outbox ; rm -rf .` rc 0). Siehe Abschnitt 11.1: die Basis folgt jetzt
nur noch einem Verzeichniswechsel, dessen KOMMANDOWORT einer ist.

### 10.3 B2 — das Urteil zu H125

`H125` bleibt **GESCHLOSSEN**, und der Eintrag nennt die Vorfahren-Form jetzt ausdrücklich mit
ihrer Messung (eigene Tabelle, HEAD / erster Schnitt / Nacharbeit 1) sowie die acht zusätzlichen
Über-Verweigerungs-Kontrollen. **H144 wird nicht gebraucht und bleibt unbenutzt.** Was der
Eintrag NICHT deckt, steht als eigener Absatz darin: die Vokabelliste (`H129`) und die Verengung
durch ein fehlgelesenes `cd` (10.2).

### 10.4 M2 — die zwei Aufbewahrungs-Leser wurden an Stichproben verglichen

**Gefunden.** Der Test verglich 16 feste Beispiele; `|jahren` in einem der beiden Leser ließ ihn
grün — genau die Driftrichtung, für die F6 existiert.

**Gebaut.** Der Test vergleicht jetzt die **kompilierten Muster selbst** (`pattern` und `flags`) und
erzeugt seinen Korpus aus den Einheiten-Alternativen, die BEIDE Muster tragen (`_units_of`), dazu
die Formen ohne Zahl. Der Kommentar in `kernel/filing.py` sagt das jetzt so, statt „feeds both
readers the same corpus".

**Rot ohne den Fix, in beide Richtungen gemessen:** `|jahren` im Kernel-Leser → **1 failed**;
`|jahren` im Register → **1 failed**.

### 10.5 N2, N3, N4, N6, N1

- **N2:** `clc` (kanonischer Alias von `Clear-Content`) ist jetzt ein Stamm — gemessen von ALLOW
  auf rc 2 — und fällt damit unter denselben beidseitigen Stolperdraht wie jeder andere
  Eintrag. Die Begrenzung in `H129` sagt jetzt, dass eine Verb-Substantiv-Form ohne eigene Nennung
  trägt, ein ALIAS aber nur, wenn er selbst ein Stamm ist (`ri`, `clc` sind es). Zusätzlich
  benennt `H129` die Klasse „leert eine Datei durch SCHREIBEN" (`Set-Content`, `sc`, `Out-File`,
  `dd of=`, eine Umleitung), die diese Regel überhaupt nicht liest — gemessen rc 0.
- **N3:** `finance_dashboard.load_project` überspringt einen Vokabular-Eintrag, der kein Mapping
  ist, genauso wie `euer_report.read_vocabulary` es tut. Vorher: `AttributeError`, rc 1, **keine
  Seite**, während der Bericht über dieselbe Datei rc 0 blieb. Rot ohne den Fix:
  `tools/test_finance_dashboard.py::test_a_vocabulary_entry_that_is_not_a_mapping_costs_a_category_and_not_the_page`.
- **N4:** Der Eintrag `H130` sagt jetzt, dass die EINHEIT eine Vokabelliste ist und welche Formen
  darum mit Abhilfe verweigert werden (`"10 Jahren"`, die YAML-Ganzzahl `10`, `"10a"`, `"P10Y"`,
  `"zehn Jahre"`, `"6 Monate"`), und dass eine Erweiterung beide Leser betrifft — also die Naht
  S6. Nicht erweitert: der Kernel darf `_duties` nicht importieren, und eine einseitige Erweiterung
  ist genau die Drift, die M2 misst.
- **N6:** Zahl korrigiert. Auf meinem Piloten mit vorhandenem Zustandsverzeichnis, fünf
  Läufe der Zeile, die den Freigabespeicher wirklich öffnet (`rm` auf den Beleg):
  min 0,189 s, **max 0,280 s**. Der Prüfer maß für dieselbe Zeile 0,899 s; beide liegen
  weit innerhalb von 60 s, und im Eintrag steht die größere. Der rote Gate-Test
  (`test_gate3_answers_before_its_registration_however_costly_the_line_is_to_judge`) ist,
  wie der Prüfer bestätigt, nicht dieser Runde.
- **N1:** Der Spiegel-Satz in Abschnitt 9 war falsch und ist korrigiert.
- **N5:** unverändert — „nichts für eine GmbH" bleibt Prosa und kein Zweig; Begründung
  in 8.5, Entscheidung der Merge-Runde.

### 10.6 Läufe der Nacharbeit

| Lauf | Ergebnis |
|---|---|
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |
| Rot-zuerst-Rig `red_first_rework1.py` (Kopie ohne `.git`) | **15 von 15** rot ohne den jeweiligen Fix |
| `python -m pytest tools/test_hooks.py tools/test_finance_dashboard.py tools/test_kernel.py tools/test_office_duties.py` | 1157 passed, 13 skipped (17:38) |
| `python -B -m pytest .claude/hooks/test_gates.py` | 488 passed, **1 failed** — derselbe lastabhängige `test_gate3_answers_before_its_registration_…`, den der Prüfer als BUG-0033 und nicht als meinen bestätigt hat (er fällt solo auf dem sauberen Hauptrepo: 4,54 gegen 4,5) |

**Versionsstempel (provisorisch, Nacharbeit 1):** office-team `2026.09.03-5`, dev-team und
research-team `2026.09.03-2`.

**Aufwand der Nacharbeit 1:** Wanddauer rund **1 h 50 min** (bis 11:43 Ortszeit), Tokens rund **110 k**; davon rund 65 min in den beiden Schlussläufen (Suiten 17:38, Gate-Suite 23:02).


---

## 11. Nacharbeit 2 (Wiederholungsprüfung FAIL: B 2 / N 2, überwiegend Buchführung)

### 11.1 B4 — die `cd`-Verengung: GESCHLOSSEN statt als Rest geführt

Ich habe den ersten der beiden angebotenen Wege genommen, weil er so klein ist, wie er aussah, und
weil ein dritter Zustand in einem GESCHLOSSENEN Eintrag genau das ist, was `CLAUDE.md` verbietet.

**Gebaut.** `moves_the_working_directory(tokens, base)` in `guard_fs_tripwire`: die Basis, gegen die
`swallows_a_tray` misst, wird nur von einer Aufrufung fortgeschrieben, deren **Kommandowort**
(erstes Token nach Flaggen und `VAR=`-Zuweisungen) ein Verzeichniswechsel ist **und** die
`_filing.directory_change` als berechenbar meldet. `read_the_line` führt diese Basis selbst
(`standing`) statt sie aus `_filing`s Fortschreibung zu nehmen; jede andere Lesung dieses
Wächters behält `_filing`s weitere Antwort, weil dort eine Fehl-Lesung nur hinzufügen kann.

**Gemessen** (Rig `_round-scratch/TSK-0116/probe_rework2.py`, gescaffoldeter Pilot außerhalb des
Repos, alle acht registrierten Office-Haken als Prozesse, nichts ausgeführt):

| Befehlszeile | HEAD e45c0ca | Nacharbeit 1 | Nacharbeit 2 |
|---|---|---|---|
| `echo cd outbox ; rm -rf .` | ALLOW | ALLOW | **rc 2** |
| `grep -r cd outbox ; rm -rf .` | ALLOW | ALLOW | **rc 2** |
| `ls cd outbox && rm -rf .` | ALLOW | ALLOW | **rc 2** |
| `echo cd docs ; git clean -fdx` | ALLOW | ALLOW | **rc 2** |

**Die vier Kontrollen bleiben rc 2** (`echo "cd outbox"`, `printf 'cd outbox'`, `echo cd $X`,
`echo cd archive`), **M1 bleibt in beiden Richtungen**: `cwd=docs` rc 0, `cd docs && git clean -fdx`
rc 0, `cd archive && git clean -fdx` rc 2, `cd outbox && rm -rf .` rc 0. Dazu neu gemessen:
`cd $DIR && rm -rf .` ist rc 2 — ein Wechsel, den der Leser nicht berechnen kann, lässt die
Basis stehen, statt sie zu raten.

**Rot ohne den Fix**, in einer Kopie ohne `.git` (`red_first_b4.py`):
`tools/test_hooks.py::test_a_word_that_only_LOOKS_like_a_cd_does_not_move_the_sweep`
→ 1 passed → **1 failed** → 1 passed; und als Gegenprobe, dass die Verengung noch die ist, die
M1 trägt: dieselbe Zeile auf `root` festgenagelt macht
`tools/test_hooks.py::test_a_sweep_is_refused_only_where_a_tray_of_record_lies_under_it` rot.

**H144 wird nicht gebraucht und bleibt unbenutzt.**

### 11.2 B3 — drei gemessene Klassen, die ein GESCHLOSSEN-Urteil nennen muss

Kein Code: für keine der drei sehe ich einen Drei-Zeilen-Fix, und jede wäre ein eigener Bau
(ein Leser für Pipelines, ein Auflöser für Links, ein Glob-Ausdehner). Alle drei sind auf
meinem eigenen Piloten nachgemessen, HEAD und diese Runde antworten identisch — nichts, was diese
Runde verschlechtert hätte:

| Klasse | Zeile | HEAD | diese Runde |
|---|---|---|---|
| Pipe → `xargs rm -rf` | `ls archive` an `xargs rm -rf` | rc 0 | rc 0 |
| Pipe, Nullbyte | `find . -print0` an `xargs -0 rm -rf` | rc 0 | rc 0 |
| Pipe, PowerShell | `Get-ChildItem -Recurse` an `Remove-Item -Force` | rc 0 | rc 0 |
| Junction `belege/ → archive/` | `rm belege/finance/2026/invoice.pdf` | rc 0 | rc 0 |
| dieselbe als Ganzes | `rm -rf belege` | rc 0 | rc 0 |
| Glob | `rm -rf *` | rc 0 | rc 0 |
| Glob mit Punkt | `rm -rf ./*` | rc 0 | rc 0 |
| Glob, fegend | `git clean -fdx *` | rc 0 | rc 0 |

Die Junction habe ich selbst angelegt (`mklink /J` im Piloten, gelungen), statt die Zahl zu zitieren.
Alle drei Klassen stehen jetzt (1) als eigene Tabelle mit Begründung im Eintrag `H125`, (2) in
der Restliste des Wächterkopfs unter „WHAT THIS DOES NOT SEE", und (3) im Urteil von `H125`,
das jetzt lautet: **geschlossen für die benannte und die Vorfahren-Form; nicht gedeckt sind Pipe,
Link, Glob und die Vokabelliste (`H129`)**.

Warum jede eine eigene Klasse ist und keine unter `H129` fällt: bei der Pipe steht das
zerstörende Wort in der Liste — was fehlt, ist die WO-Hälfte, weil kein Wort der Zeile die
Pfade nennt. Beim Link stimmt beides, und die Auflösung fehlt. Beim Glob nennt der Kopf des
Wächters den Mechanismus seit langem; neu ist nur, dass `H125` ihn selbst nennt, statt sich auf
einen Verweis zu verlassen — `rm -rf *` ist die alltäglichste Schreibweise dieser Zerstörung.

### 11.3 N7 und N8

- **N7:** `git clean -fdx -e archive` (und `-e archive -e inbox`) wird mitverweigert — die eine
  sorgfältige Schreibweise. Der Kommentar an `EXCLUDING_FLAGS` sagt das jetzt und sagt auch,
  warum es so bleibt: die Kosten sind eine Korrektur und nie ein Beleg, und die Alternative wäre,
  die Muster-Grammatik jedes Befehls zu lesen — ein zweiter Parser pro Befehl, also genau der
  Preis, den `H123` protokolliert.
- **N8:** Der Satz nannte den langsamsten EINZELNEN Haken-Prozess und las sich wie eine Aussage
  über den ganzen Aufruf. Beide Zahlen stehen jetzt da, mit dem, was sie messen: langsamster
  einzelner Prozess **0,280 s** (Prüfer: 0,899 s), langsamste ZEILE über alle acht Haken
  zusammen **1,276 s** (Prüfer: 0,565 s; 25 Zeilen × 8 Haken × 2 Bäume in
  `probe_rework2.py`). Geurteilt wird gegen die zweite — ein Aufruf besteht aus allen acht:
  2,1 % des Selbstbudgets von 60 s.

### 11.4 Läufe der Nacharbeit 2

Umfang nach der Vorgabe des Koordinators — keine volle Gate-Suite:

| Lauf | Ergebnis |
|---|---|
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |
| `pytest .claude/hooks/test_gates.py -k hole` (die drei Löcherlisten-Knoten) | 5 passed (1,6 s) |
| `pytest tools/test_hooks.py -k "tripwire/sweep/door/…"` | 100 passed (56 s) |
| Rot-zuerst `red_first_b4.py` (Kopie ohne `.git`) | 2 von 2 rot ohne den Fix |

**Versionsstempel (provisorisch, Nacharbeit 2):** office-team `2026.09.03-6`; dev-team und
research-team unverändert `2026.09.03-2`.

**Aufwand der Nacharbeit 2:** Wanddauer rund **50 min** (bis 12:12 Ortszeit), Tokens rund **60 k**.


---

## 12. Nacharbeit 3 (dritte Prüfung FAIL: B 1)

### 12.1 B5 — ein Verzeichniswechsel, der gar nicht landet

**Gefunden.** `moves_the_working_directory` fragte, ob das Kommandowort ein Wechsel ist und ob das
Ziel berechenbar ist — nicht, ob der Wechsel STATTFINDET. Damit verengte ein `cd`, das ins Leere
geht, die Reichweite auf ein Verzeichnis, das es nicht gibt, und das darauf folgende `rm -rf .` war
frei. Die schlimmste der Formen ist der Tippfehler: genau die Unfallklasse, für die diese Wand
nach `DEC-0056` überhaupt existiert.

**Gebaut.** Das berechnete Ziel muss ein Verzeichnis SEIN und INNERHALB des Projekts liegen:

```python
    moved = os.path.normpath(os.path.join(base, str(argument).replace("\\", "/")))
    if not os.path.isdir(moved):
        return None
    return moved if _filing.position(root, moved, WORKING_DIRECTORY) is not None else None
```

Die zweite Hälfte ist der `cd ..`-Fall, den der Auftrag ausdrücklich nachzuprüfen verlangt:
eine Basis oberhalb der Wurzel hätte „kein Fach unter dieser Basis" geantwortet, und das ist die
falsche Antwort — unter ihr liegt das ganze Projekt. Der Wechsel wird darum nicht gefolgt und die
Reichweite bleibt die Wurzel.

**Gemessen** (Rig `_round-scratch/TSK-0116/probe_rework3.py`, Pilot außerhalb des Repos, alle acht
registrierten Office-Haken als Prozesse, nichts ausgeführt; `rm -rf .` allein ist rc 2):

| Befehlszeile | HEAD e45c0ca | Nacharbeit 2 | Nacharbeit 3 |
|---|---|---|---|
| `cd nichtda ; rm -rf .` | ALLOW | ALLOW | **rc 2** |
| `cd docs2 ; rm -rf .` (Tippfehler) | ALLOW | ALLOW | **rc 2** |
| `cd .. ; rm -rf .` | ALLOW | ALLOW | **rc 2** |
| KONTROLLE `cd outbox && rm -rf .` | ALLOW | ALLOW | ALLOW |
| KONTROLLE `cd docs && git clean -fdx` | ALLOW | ALLOW | ALLOW |
| KONTROLLE `cd archive && rm -rf .` | rc 2 | rc 2 | rc 2 |
| KONTROLLE `rm -rf .` | ALLOW | rc 2 | rc 2 |

**Rot ohne den Fix**, in einer Kopie ohne `.git` (`red_first_b5.py`), **dreimal** — einmal für
den ganzen Fix und einmal je Hälfte, damit keine der beiden Zeilen tot ist:
`tools/test_hooks.py::test_a_directory_change_that_never_lands_does_not_move_the_sweep`
→ 1 passed → **1 failed** → 1 passed, für (a) den ganzen Rückbau, (b) nur die
Existenzprüfung entfernt, (c) nur die Innerhalb-des-Projekts-Prüfung entfernt.

### 12.2 Was der Fix NICHT schließt → `H144`

Vier Formen, in denen das Ziel existiert, der Wechsel aber nicht wirkt — gemessen rc 0:
`false && cd outbox ; rm -rf .`, `ls` in eine Pipe an `cd outbox` mit folgendem `rm -rf .`,
`cd outbox` in eine Pipe an `rm -rf .`, `cd outbox & rm -rf .`. Alle vier brauchen den TRENNER
zwischen zwei Aufrufungen, und den gibt `_filing._walk` nicht heraus; `hooks/_*.py` ist
`forbidden_scope`.

Das steht jetzt an vier Stellen: **(1)** eigener Eintrag `H144` mit Mechanismus, Kette, Urteil
„Rest, benannt" und Begrenzung; **(2)** Naht an Strom C/D, wörtlich unten; **(3)** vierter Punkt
in der Restliste des Wächterkopfs; **(4)** vierte Zeile in der `H125`-Tabelle „Was dieser
Eintrag NICHT deckt". Der Einleitungssatz dieser Tabelle behauptete Vollständigkeit („alles,
was ein GESCHLOSSEN-Urteil nennen muss") — er sagt jetzt, dass er die bis heute GEMESSENEN
Klassen nennt und ausdrücklich nicht, dass es keine weiteren gibt; die vierte Zeile kam ja erst
durch diese Prüfung dazu.

### 12.3 Naht S9 an Strom C/D, wörtlich (hier NICHT geschrieben)

> **`_filing` soll den TRENNER je Aufrufung herausgeben.** `_filing.invocations(command, bases)`
> liefert heute `(text, tokens, bases)` je Aufrufung. Gebraucht wird ein viertes Feld: der
> **Trenner, der VOR dieser Aufrufung stand** — `""` für die erste, sonst `";"`, `"&&"`,
> `"||"`, `"|"` oder `"&"` —, gelesen aus derselben Zerlegung, die `INVOCATION_RX` ohnehin
> macht (`_filing._walk`, `INVOCATION_RX.findall`). Damit kann
> `guard_fs_tripwire.read_the_line` einen Verzeichniswechsel nur dann fortschreiben, wenn der
> Trenner VOR der nächsten Aufrufung `";"` oder `"&&"` ist UND der Wechsel selbst nicht hinter
> `"|"` oder `"&"` stand — die vier Formen aus `H144` fallen dann heraus.
> **Test, den der Strom mitliefern muss** (in `tools/test_hooks.py`, die acht Haken als Prozesse,
> Pilot außerhalb des Repos): `false && cd outbox ; rm -rf .`, `ls | cd outbox ; rm -rf .`,
> `cd outbox | rm -rf .` und `cd outbox & rm -rf .` sind **rc 2**, während
> `cd outbox && rm -rf .` und `cd docs && git clean -fdx` **rc 0** bleiben und
> `cd archive && rm -rf .` **rc 2** bleibt — beide Enden, in einer Kopie außerhalb des Repos
> rot gemessen.
> **Warum es nicht hier gebaut wird:** `team-kits/office-team/hooks/_*.py` liegt im
> `forbidden_scope` von TSK-0116, und eine zweite Zerlegung der Befehlszeile im Wächter wäre
> genau die zweite Wahrheit, die `_filing` existiert um zu verhindern.

### 12.4 Läufe der Nacharbeit 3

| Lauf | Ergebnis |
|---|---|
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |
| `pytest tools/test_hooks.py -k "never_lands or LOOKS_like_a_cd or sweep_is_refused or ANCESTOR or exclusion_flag"` | 11 passed (7,7 s) |
| `pytest .claude/hooks/test_gates.py -k hole` | 5 passed |
| Rot-zuerst `red_first_b5.py` (Kopie ohne `.git`) | 3 von 3 rot ohne den jeweiligen Teil |

**Versionsstempel (provisorisch, Nacharbeit 3):** office-team `2026.09.03-7`; dev-team und
research-team unverändert `2026.09.03-2`.

**Aufwand der Nacharbeit 3:** Wanddauer rund **40 min** (bis 12:31 Ortszeit), Tokens rund **45 k**.


---

## 13. Nacharbeit 4 (vierte Prüfung PASS — zwei Textzeilen zum Abschluss)

### 13.1 M3 — der Link erreicht das Fach auch als ARBEITSVERZEICHNIS

Der Eintrag `H125` (b) und der Restlisten-Punkt im Wächterkopf beschrieben die Link-Klasse nur als
BENENNENDE Löschung (`rm belege/…/invoice.pdf`). Die schwerere Hälfte fehlte: nach `cd belege`
steht die Shell IM Archiv, und die Vorfahren-Form kostet dann nicht einen Beleg, sondern das ganze
Fach.

**Auf eigenem Piloten nachgemessen** (`_round-scratch/TSK-0116/probe_rework4.py`, echte Junction
`belege/ → archive/` per `mklink /J`, alle acht registrierten Office-Haken als Prozesse, nichts
ausgeführt) — identisch zur Messung des Prüfers, und HEAD antwortet gleich:

| Befehlszeile | HEAD e45c0ca | diese Runde |
|---|---|---|
| `cd belege ; rm -rf .` | rc 0 | rc 0 |
| `cd belege/finance ; rm -rf .` | rc 0 | rc 0 |
| `cd belege ; git clean -fdx` | rc 0 | rc 0 |
| KONTROLLE `cd archive ; rm -rf .` | rc 2 | rc 2 |
| KONTROLLE `rm belege/finance/2026/invoice.pdf` | rc 0 | rc 0 |
| KONTROLLE `rm archive/finance/2026/invoice.pdf` | rc 2 | rc 2 |

**Geschrieben:** ein Satz in `H125` (b) (die Verengung aus `M1` misst gegen ein Verzeichnis, dessen
Namen sie nicht auflöst — dieselbe Klasse, keine neue Nummer), ein Satz im Restlisten-Punkt des
Wächterkopfs, und drei Zeilen in der Tabelle „Was dieser Eintrag NICHT deckt".

### 13.2 N9 — der Urteilssatz zählte drei über einer Tabelle mit vier Klassen

`H125` sagt jetzt: „geschlossen für die benannte und die Vorfahren-Form; nicht gedeckt sind die
**vier** Klassen der Tabelle oben (Pipe, Link, Glob, `H144`) und die Vokabelliste (`H129`)".

### 13.3 Ein Stempel war doch nötig — gemessen, nicht angenommen

Der Auftrag sagte „kein Stempel (kein Kit-Code)". Der Satz aus 13.1 gehört aber in den
DOCSTRING von `team-kits/office-team/hooks/guard_fs_tripwire.py`, und ein Docstring ist Kit-Code:
`python tools/validate.py` antwortete
„`office-team: kit files changed but VERSION not bumped`". Also gestempelt — **office-team
`2026.09.03-8`**, dev-team und research-team unverändert `2026.09.03-2`. Am VERHALTEN hat sich
nichts geändert (nur Prosa), was die zehn Tripwire-Knoten nach dem Stempel bestätigen.

### 13.4 Läufe der Nacharbeit 4

| Lauf | Ergebnis |
|---|---|
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed (nach dem Stempel) |
| `pytest .claude/hooks/test_gates.py -k hole` | 5 passed (2,8 s) |
| `pytest tools/test_hooks.py -k "never_lands or LOOKS_like_a_cd or sweep_is_refused or ANCESTOR"` | 10 passed (7,5 s) — Gegenprobe, dass der Docstring nichts am Verhalten änderte |

**Aufwand der Nacharbeit 4:** Wanddauer rund **20 min** (bis 12:44 Ortszeit), Tokens rund **25 k**.
