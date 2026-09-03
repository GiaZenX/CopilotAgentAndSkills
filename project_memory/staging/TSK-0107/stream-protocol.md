# TSK-0107 (Strom G, Büro) — Stromprotokoll

Arbeitsbaum: `C:/Offline Repos/v2-testbed/_worktrees/g2-office` (Branch `g2/office`, Basis `6d18407`).
Arbeitsverzeichnisse: `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0107/`.
Kein Commit, kein Push, keine Installation. Stempel provisorisch.

---

## 0. Vorgefunden

Ein Vorgänger-Lauf war durch einen Nutzer-Stopp beendet worden (kein Fehler). Auf der Platte lagen
12 Einträge, kein Protokoll, kein Patch. Rekonstruiert aus `git diff HEAD`, den Seam-Notes und der
Messungsdatei:

**Gebaut und laufend:**

* `team-kits/office-team/hooks/_duties.py` (neu, ~570 Zeilen) — das Fristenregister als ein Modul mit
  fünf Zuflüssen (`filing_duties`, `retention_duties`, `receivable_duties`, `review_duties`,
  `routine_duties`), einem gemeinsamen Zeitbudget und einer dreiwertigen Antwort je Quelle
  (Pflicht / nichts / **unlesbar**).
* `session_status.py` (nur office) — der handgeschriebene `stale_register_entries`-Nörgler ist
  entfallen und durch den Absatz des Registers ersetzt.
* Drei Vorlagen (`business_profile.yaml`, `filing_plan.yaml`, `compliance_register.yaml`) — F2–F5
  von `FR-0002`, plus `tax.filings` und `receivables.payment_terms_days` als Quellen des Registers.
* Zwei neue Suiten (`tools/test_office_duties.py`, `tools/test_kit_neutrality.py`), 30 Tests, grün.
* `docs/POST_V2_WISHLIST.md` — `H111`–`H113` samt Tabellenzeilen.
* `docs/reviews/2026-09-02-tsk0107-office-duties-measurements.md` — die Messungen des ersten Laufs.
* Seam-Notes (`seam-notes.md`) mit E1–E4, F1–F4, I1.

**Offen bzw. fehlerhaft vorgefunden** (alles unten im Detail): ein Testzeiger ins Leere, zwei
Löcher, deren Testnennung `test_gates.py` rot gemacht hätte, F6 unangetastet, eine Zahl mit falscher
Begründung, drei Sätze, die mehr behaupteten als der Baum trägt, und die FR-0028-Messung ohne
zweiten Nachweis.

**Nicht im Patch:** `project_memory/.audit/hook_events.jsonl` ist eine Nebenwirkung der laufenden
Haken dieses Repos und gehört nie in ein Paket.

---

## 1. Je Eingabe: Stand und Messung

### FR-0034 — Fristenregister aus `business_profile` / `filing_plan` / Ledger + Sitzungsstart-Meldung

**Stand: gebaut, gemessen.** Ein Register, fünf Zuflüsse, ein Absatz beim Sitzungsstart. Die
Ableitungen sind Eigenschaften und keine Aufzählungen: ein Jahresordner ist ein Verzeichnisname aus
vier Ziffern (nicht eine Liste der Platzhalter-Schreibweisen), eine Steuerperiode ist Periodenlänge
plus Verzug (das Kit weiß nicht, was eine Voranmeldung ist), ein Forderungsposten ist eine
Einnahmezeile ohne Zahldatum, deren Belegart die eigene Richtung nicht mindert.

Rote Tests (alle in `tools/test_office_duties.py`, gegen den ausgelieferten Hook als **Prozess**):

| Eigenschaft | Test |
|---|---|
| die Frist der zuletzt GESCHLOSSENEN Periode, mit Rechtsgrundlage | `test_the_session_start_hook_names_the_tax_deadline_the_profile_declares` |
| abweichendes Wirtschaftsjahr wird als *unlesbar* gemeldet, nicht ins Kalenderjahr gerechnet | `test_a_shifted_fiscal_year_is_reported_as_unread_rather_than_placed_in_the_calendar_year` |
| eine Periode, die das Jahr nicht teilt, wird gemeldet statt still fallen gelassen | `test_a_filing_entry_whose_period_does_not_divide_the_year_is_reported_rather_than_skipped` |
| abgelaufene Aufbewahrung wird genannt, laufende nicht | `test_a_year_past_its_retention_is_named_and_one_inside_it_is_not` |
| unlesbare Aufbewahrungsangabe wird gemeldet, nicht als erfüllt gelesen | `test_a_retention_this_reader_cannot_parse_is_reported_rather_than_read_as_met` |
| ein `path_template`, der aus dem Projekt klettert, wird nicht begangen | `test_a_path_template_that_climbs_out_of_the_project_is_not_walked` |
| unbezahlte Rechnung ja, unbezahlte Gutschrift nein | `test_an_unpaid_invoice_is_a_dunning_candidate_and_an_unpaid_credit_note_is_not` |
| ohne Zahlungsziel keine Mahnkandidaten (das Kit erfindet keine Frist) | `test_without_payment_terms_the_ledger_produces_no_dunning_candidate` |
| das Register schreibt nichts in das Projekt, das es liest | `test_the_duty_register_writes_nothing_into_the_project_it_reads` |
| unlesbare Quelle ≠ leeres Register | `test_an_unreadable_source_is_named_rather_than_read_as_an_empty_register` |
| leere Datei ≠ kaputte Datei | `test_an_empty_state_document_is_not_reported_as_unparseable` |
| ein Projekt ohne Pflichten bekommt KEINEN Absatz | `test_a_project_that_owes_nothing_gets_no_paragraph` |

**Was dieser Lauf hier zusätzlich gemessen hat** (Abschnitt 2.4): die Ledger-Grenze an beiden Enden
und die Kostenmessung des Sitzungsstarts in der teuren statt in der billigen Richtung.

### FR-0038 — Laufdatensatz + Überfälligkeitsmeldung; der Hook meldet, der PM spawnt

**Stand: gebaut, gemessen, mit zwei benannten Grenzen (`H112`).** Der Laufdatensatz wird
**abgeleitet** statt zusätzlich geschrieben: `notify_agent_events` schreibt jeden `subagent_stop`
ohnehin ins Ereignis-Log; `_duties.last_run` liest ihn. Die Periode ist eine ISO-Woche.

Rote Tests:

* `test_the_register_reads_the_run_record_the_shipped_hook_really_writes` — fährt
  `notify_agent_events.py` als Prozess und liest sein Ergebnis durch `_duties.last_run` zurück. Eine
  Umbenennung dort wird rot statt blind.
* `test_a_run_in_an_earlier_week_leaves_the_routine_due` — beide Richtungen, „immer fällig" und „nie
  fällig" scheitern beide.
* `test_a_rotated_event_log_makes_the_routine_read_as_due_rather_than_as_run` — die sichere
  Ausfallrichtung.
* `test_the_duty_register_starts_no_process_at_all` — `DEC-0028` als Eigenschaft des Syntaxbaums:
  kein `subprocess`, kein `system`, kein `Popen`.
* `test_the_audited_role_is_a_role_this_kit_ships`, `test_no_routine_approval_can_be_minted_in_this_kit_today`
  — die beiden Enden der einen Nennung, die das Modul trägt.

**Spiegelentscheidung `session_status.py`: NICHT spiegeln — und das ist kein Versäumnis.** Die Datei
steht seit Langem in `KIT_SPECIFIC_HOOKS` (`tools/test_hooks.py`) mit dem Grund „the session briefing
names each kit's own artifacts and nags". Die Spiegelregel hat einen Stolperdraht an **beiden**
Enden (`_assert_mirrored`): eine gespiegelte Datei, die auseinanderläuft, wird rot — und ein Eintrag
in der Ausnahmeliste, dessen Kopien identisch geworden sind, ebenfalls. Gemessen:
`pytest tools/test_hooks.py -k "shared_kit_files_identical or document_trays or session_status"` →
**21 passed**. Der Zusatz gehört ausschließlich in die Office-Fassung, weil Register, Ledger und
Aktenplan Office-Gegenstände sind. Das neue `_duties.py` liegt nur in `office-team/hooks/`, wie
`_bookings.py`, `_filing.py` und `_readings.py`; die Spiegelregel greift für einen Namen, den nur
ein Kit trägt, gar nicht — gemessen mit `which_office_only.py`.

Die Formulierung im Item (`expected_outputs` 1) verlangt „session_status.py mirrored byte-identical
across kits". Das widerspricht der bestehenden, begründeten Ausnahme; ich habe die Ausnahme
gehalten und melde die Abweichung hier ausdrücklich als solche, statt sie stillschweigend zu
erfüllen oder zu ignorieren.

### FR-0028 — werkzeug- und produktgruppen-agnostisch

**Stand: gemessen (Rückruf) + gebaut (Neutralitätstest).**

**(a) Die Rückruf-Messung**, verlangt als „PROC lehren → nächste Sitzung, gleiches Repo → hält".
Zwei frisch aufgesetzte Office-Projekte aus dem Arbeitsbaum, alle Schritte über die ausgelieferten
Haken als Prozesse (`probe/recall_measure.py`). In diesem Lauf **neu gefahren**, Ausgabe:

```
STEP 0  a spawn before anything was taught
        rc=2  [team-kit gate_proc_approved] specialist spawn refused: this project has no approved
              procedure at all, and the office kit dispatches specialists only
STEP 1  taught PROC-0001, status DRAFT
STEP 2  after the user's approval: status APPROVED, approved_hash 3d2d7261f8b44cf0
STEP 3  session 1 spawn under the taught PROC: rc=0
STEP 4  session 2, same repo: the PROC is still APPROVED (Eingangsroutine: jede Datei oeffnen, kla)
STEP 5  the session-start briefing points the manager at the taught PROCs: YES
STEP 6  session 2 spawn under the same PROC: rc=0
STEP 7  after the taught steps were edited past the kernel: rc=2  ... PROC-0001 was edited past the
              kernel after its approval (its content no longer hashes to the stamped app…)
STEP 8  the same PROC id in the OTHER repo: rc=2  ... this project has no approved procedure at all
```

Belegt: das beigebrachte Verfahren überlebt den Sitzungswechsel im selben Repo (4/5/6), es kann
nicht still verändert werden (7), es wandert nicht in ein anderes Geschäft (8) — genau die
Klarstellung des Nutzers vom 2026-09-02 —, und der leere Zustand blockiert (0).
**Ausdrücklich NICHT belegt:** dass ein Modell dem Verfahren inhaltlich folgt. Gemessen ist der
Apparat. Ob der Text befolgt wird, ist eine Frage an eine echte Sitzung (`DEC-0025`-Piloten).

**(b) Der Neutralitätstest** (`tools/test_kit_neutrality.py`): 59 Rollentexte (drei Verfassungen,
alle Agent-Definitionen über ihre **geparste** Frontmatter, alle Skills) plus alle Zustandsvorlagen
des Office-Kits. Zwei Eigenschaften, je mit Ratsche in beide Richtungen. Ein Fund:
`office-team/agents/shop-curator.md`, dessen Routing-`description` mit „…, audit, Shopify." endet.
Als **Naht** eingetragen, nicht hier geändert (Rollentexte sind Strom E). Ein zweiter Eintrag:
`project_config.yaml: providers` als einzige gefüllt ausgelieferte Liste, mit Grund.

Rote Tests: `test_the_binding_reader_can_tell_a_binding_from_an_illustration` (der Boden — „alles
melden" und „nichts melden" scheitern beide), `test_no_role_text_binds_a_kit_to_a_named_platform`,
`test_every_office_state_template_ships_its_lists_empty`.

### FR-0002 F2–F6 — Vorlagenarbeit

**Stand: F2–F5 gebaut (vorgefunden), F6 war bereits ausgeliefert und ist jetzt gemessen.**
Der Stand aller acht Punkte steht ab jetzt in `docs/office-kit-from-field.md` als Tabelle — dort,
wo die Prosa liegt, statt in einem zweiten Dokument.

* **F2** Aufbewahrung: Spanne + Rechtsgrundlage im Feld `retention`, plus der Ehrlichkeitsvermerk.
  Der Waechter darauf ist `_duties.retention_duties`.
* **F3** Benennung: `filename_template` als Schema, mit den drei Abweichungen, die im Feld auftraten.
* **F4** Eingang/Archiv als Definition, mit dem mechanischen Grund.
* **F5** Löschquarantäne `archive/_quarantine/` plus Beispielregel `FP-901`.
* **F6** `.gitignore`: **beide** Hälften standen schon in der Vorlage; gemessen war nur die
  DSGVO-Hälfte. Neu ist der Stolperdraht auf die zweite (Abschnitt 3.2).
* **F7/F8**: eigene Pakete, in der Tabelle als offen benannt, mit der Stelle, an der sie hängen.

**Zu `DEC-0056`.** Dieser Strom hat **kein neues Gate gebaut**. F5 und F2 lehnen sich an den
vorhandenen `guard_fs_tripwire` an — das ist die benannte Ausnahme („Sorgfalt für Unumkehrbares"),
und der **gemessene Fehler**, den diese Wand fängt, ist die irrtümliche Löschung eines
Geschäftsdokuments: nicht reparierbar, und im Feld die Klasse, für die F5 überhaupt geschrieben
wurde. Was die Wand tut, ist gebaut und gemessen, nicht behauptet —
`test_fs_tripwire_blocks_archive_delete`, `test_fs_tripwire_blocks_move_out_of_archive`,
`test_fs_tripwire_allows_a_move_that_stays_inside_the_archive`,
`test_a_correction_the_user_approved_is_the_one_operation_the_tripwire_lets_through`
(alle `tools/test_hooks.py`). Die Vorlage nennt deshalb den **Ort** (`guard_fs_tripwire`) und keine
Wiederholung des Satzes.

---

## 2. Was dieser Lauf am Vorgefundenen korrigiert hat

### 2.1 Ein Testzeiger, der ins Leere zeigte — und der Draht dagegen

`_duties.py:52` schrieb die Budget-Rechnung `tools/test_hooks_v2.py::…` zu; der Test liegt in
`tools/test_office_duties.py`. Ein Satz, der sich als gemessen liest und einen Leser in die falsche
Datei schickt. Gebaut wurde die Eigenschaft, nicht nur die Korrektur:

`tools/test_repo_hygiene.py::test_every_test_pointer_this_repo_writes_resolves` liest jede voll
qualifizierte Knoten-Id aus den Backtick-Spannen von `team-kits/` **und** `docs/` und löst sie im
Syntaxbaum der genannten Suite auf.

```
team-kits/ allein, vor der Reparatur   : 122 geprüft, 1 unauflösbar (_duties.py:52)
team-kits/ + docs/, nach der Reparatur : 184 geprüft, 0 unauflösbar
```

Gesehene Rot-Meldung:
`team-kits/office-team/hooks/_duties.py:52 cites tools/test_hooks_v2.py::test_the_session_start_budgets_together_fit_inside_the_hook_deadline -- no such test`.

Der Boden dazu ist `test_the_test_pointer_reader_reads_the_shapes_a_kit_file_writes`: der Leser muss
die umgebrochene Form, die parametrisierte Fall-Id und den Punkt am Spannenende sehen — und darf auf
einen bloßen Dateinamen, einen unqualifizierten Namen und eine modul-qualifizierte KONSTANTE nicht
anspringen. **Zwischenbefund, der beinahe ein Defekt geworden wäre:** meine erste Fassung benutzte
die zeilenweise Spannen-Lesung des Nachbarn und fand über dem unreparierten Baum **0** Fundstellen —
die eine echte ist über zwei Zeilen umgebrochen. Das steht als Messung am Kommentar von
`_CODE_SPAN_RX`.

**Was der Leser bewusst NICHT liest**, benannt statt später entdeckt: einen Namen ohne Dateiangabe
und einen Namen außerhalb von Backticks. Gemessen mit dem weiteren Leser (jedes `test_*`-Wort):
114 verschiedene Namen, 136 Fundstellen ohne Auflösung — fast alle Suite-DATEInamen (`test_hooks_v2`)
oder Hälften umgebrochener Namen. `docs/research/` bleibt außen vor, weil dort Feldnotizen ÜBER
andere Projekte liegen, die deren Suiten zitieren.

### 2.2 Zwei Löcher, deren Testnennung `test_gates.py` rot gemacht hätte

`.claude/hooks/test_gates.py::test_every_test_the_hole_list_names_is_one_that_exists` löst einen
**unqualifizierten** Namen in einem Loch ausschließlich in `test_gates.py` auf. `H112` nannte zwei
Tests aus `tools/test_office_duties.py` unqualifiziert.

```
vorher : pytest .claude/hooks/test_gates.py -k "hole or measurement or reference"
         -> 1 failed, 7 passed
            "H112 names `test_a_rotated_event_log_…`, and 0 tests in test_gates.py answer to it"
nachher: -> 8 passed
```

Behoben durch Qualifizieren (`tools/test_office_duties.py::…`) in `H111` und `H112`. Damit greift
für sie zugleich der Draht aus 2.1 — der Leser dort überspringt genau die Spannen mit Punkt, die
`test_gates` nicht liest, und umgekehrt. Die beiden Prüfungen überlappen nicht und lassen zusammen
keine Lücke.

### 2.3 Drei Sätze, die mehr behaupteten als der Baum trägt

* **`BUG-0068` „hat einen echten Backlog gelöscht".** Das Item hält das nicht fest; es beschreibt
  eine Sackgasse beim Vorlagen-Abgleich und eine überstellte Liste. In `_duties.py` und im
  Testdocstring zeigt der Satz jetzt auf den **Ort**, an dem das Kit dieselbe Unterscheidung schon
  zieht: `session_status.main`, Meldung „KIT MERGE BACKLOG UNREADABLE".
* **„eine Erhebung des Office-Kits am 2026-08-31"** in `filing_plan.yaml` — ein Dokument dieses
  Namens gibt es nicht. Der Satz sagt jetzt, was zutrifft: kein primärer Gesetzestext gelesen,
  keiner mitgeliefert.
* **„zwei Fassungen"** für die Eingang/Archiv-Grenze — das Felddokument sagt „mehrere Fassungen
  (v1.2 → v1.9)". Die Zahl ist raus; ein Verweis auf `docs/…` wäre in einer AUSGELIEFERTEN Vorlage
  ein toter Zeiger im Projekt des Nutzers und steht deshalb auch nicht da.

### 2.4 Eine Zahl mit der falschen Begründung

`MAX_LEDGER_YEARS = 12` trug einen Kommentar, der **zehn** begründete. Ersetzt durch die zutreffende
Begründung (Kostengrenze des Sitzungsstarts) und an beiden Enden gemessen:
`test_the_receivable_feed_opens_the_years_its_own_bound_names` legt ein Ledger EIN Jahr tiefer als
die Grenze an; das Jahr knapp innerhalb muss gelesen, das knapp außerhalb darf nicht gelesen werden.

Dabei kam die zweite Hälfte heraus: die Maximal-Messung des Sitzungsstarts war in der **billigen**
Richtung gebaut. Jeder Zufluss kehrt bei `MAX_PER_FEED` zurück, also ist ein Ledger voller offener
Rechnungen nach 200 Zeilen fertig; der teure Fall ist das **ruhige** Ledger ohne Ausstieg. Die
Messung trägt jetzt bezahlte Zeilen in allen erlaubten Jahren, die unbezahlten nur im ältesten, und
beweist mit einer eigenen Zusicherung, dass das tiefste Jahr wirklich geöffnet wurde.

### 2.5 F6, jetzt gemessen

`tools/test_hooks_v2.py::test_the_office_gitignore_still_lets_the_tray_seeds_into_a_fresh_clone`.
Ablagen aus `kernel.trays` (dieselbe Ableitung wie `hooks/document_trays.txt`), Seeds sind die
wirklich ausgelieferten Dateien darunter, entschieden wird mit `git check-ignore` in einem
Wegwerf-Repo. Beide Richtungen: der Seed muss durchkommen, ein Geschäftsdokument in derselben Ablage
muss draußen bleiben.

```
Mutation außerhalb des Repos: inbox/* archive/* outbox/*  ->  inbox/ archive/ outbox/
-> FAILED  "archive/README.txt is a file the kit SHIPS and the .gitignore hides it"
zurückgesetzt -> passed
```

### 2.6 „Das Kit verschickt nichts" — vom Versprechen zur Eigenschaft

`business_profile.yaml` verspricht dem Nutzer bei den Zahlungszielen, dass nichts verschickt wird.
Gebaut: `tools/test_hooks_v2.py::test_the_office_kit_ships_nothing_that_could_send` liest die
Importe aller **44** ausgelieferten Python-Module des Office-Kits aus dem Syntaxbaum. Beide Enden —
`test_the_reader_of_reaching_modules_sees_a_planted_one` misst den Leser, und der Test liest das
Versprechen zuerst aus der Vorlage, damit er keine Regel über nichts wird.

```
Mutation außerhalb des Repos: `import smtplib` an scripts/ledger_add.py
-> FAILED  "... these shipped modules can reach off the machine: {'…/ledger_add.py': ['smtplib']}"
```

### 2.7 Ein Kommentar, der einen Bericht behauptete, den es nicht gab

Der `AUDIT_ROLE`-Kommentar sagte, die ungedeckte Gegenrichtung („eine ZWEITE prüfende Rolle taucht
unbemerkt auf") werde „als Naht gemeldet". Gemeldet war sie nirgends. Der Kommentar benennt die
Grenze jetzt selbst und behauptet keinen Bericht: „ist diese Rolle ein Prüfer" ist keine Eigenschaft,
die eine ausgelieferte Datei dieses Kits trägt — sie abzuleiten hieße, sie zu erfinden.

---

## 3. Löcher

Nur `H111`–`H113`, wie beauftragt. Jeder Eintrag hat Mechanismus, gemessene Kette, Tabellenzeile,
Herkunft (`TSK-0107`) und eine `**Urteil …**`-Spanne; die Backtick-Testnamen lösen auf.

| Nr. | Urteil | Kurz |
|---|---|---|
| `H111` | **offen**, Dokumentationslücke des Apparats | `routine`/`analysis`-Freigaben haben in keinem Kit einen Erzeuger, obwohl alle drei Verfassungen die Auditor-Routine darauf reiten lassen |
| `H112` | **Rest, benannt** | der Laufdatensatz ist ein Nebenprodukt des Ereignis-Logs: eine rotierte Generation liest sich als „nie gelaufen" (sichere Richtung), ein AUFGEBENDER Lauf zählt als Lauf (unsichere Richtung) |
| `H113` | **Rest, benannt** | das Register kennt kein „erledigt" — Über-Meldung, nie Schweigen |

Nachgerechnet und bestätigt (gegen die Module dieses Baums):

```
approvals.APR_KINDS            : analysis, scope, delivery, acceptance, routine, push, preset,
                                 kit_update, filing_correction, filing_rule, document_proposal
approvals.item_derived_kinds() : acceptance, delivery, scope
request-approval choices       : item_derived ∪ line_manifest  = 9 Arten, keine der beiden dabei
kernel/cli.py nennt "routine"  : False
office scripts/harness.py      : False
```

`H112(b)` war argumentiert, nicht gemessen. Jetzt gemessen — beide ausgelieferten Haken als Prozesse
auf DERSELBEN `SubagentStop`-Nutzlast, danach das ausgelieferte `_duties` befragt:

```
vor jedem Stop:                       routine due = True
gate_subagent_output rc=0   notify_agent_events rc=0
   log: event=gave_up         reason=project-auditor: giving up with summary still missing
   log: event=subagent_stop   reason=project-auditor
_duties.last_run liest:               2026-09-02 13:59:29   (unreadable: None)
nach dem Aufgeben:                    routine due = False
```

Beide Zeilen stehen im selben Log; die zweite löscht die Wochenmeldung, die erste sagt, dass nichts
geliefert wurde, und niemand verbindet sie. Die Ausgabe steht bei `H112` in der Löcherliste.

Lauf: `pytest .claude/hooks/test_gates.py -k "hole or measurement or reference"` → **8 passed**
(vorher 1 failed, siehe 2.2). `pytest tools/test_repo_hygiene.py -k hole` → 1 passed.

---

## 4. Nähte — wörtlich, nicht geschrieben

Alle Dateien unten liegen außerhalb des `allowed_scope` dieses Stroms. **Nichts davon wurde
geändert.**

### An Strom E (Rollentexte, Skills, Verfassungen)

**E1 — `team-kits/office-team/agents/shop-curator.md`, Routing-`description` (FR-0028).**
Sie endet mit „…, audit, Shopify.". Eine `description` ist das, woran die Plattform eine Anfrage
misst; damit ist die Shop-Rolle für den Router die SHOPIFY-Rolle. Vorschlag, wörtlich: das letzte
Listenglied streichen und durch »whatever shop system the business runs« ersetzen. Der Eintrag steht
in `KNOWN_BINDINGS` (`tools/test_kit_neutrality.py`) mit Eigentümer; wird das Wort entfernt, meldet
derselbe Test, dass der Eintrag zu löschen ist.

**E2 — `team-kits/office-team/skills/records-clerk/SKILL.md:82` nennt `0-Inbox/Prüfen/Löschen/`.**
Dieser Knoten ist für ein archiviertes Dokument unerreichbar; `0-Inbox` ist gar keine Ablage dieses
Kits (`hooks/document_trays.txt`: `archive`, `inbox`, `outbox`). Vorschlag, wörtlich: »Ein Dokument,
das überholt, beschädigt oder doppelt ist, wandert mit protokolliertem Grund nach
`archive/_quarantine/<Jahr>/` (Regel `FP-901` im Aktenplan). Aus dem Archiv heraus bewegt niemand
etwas — `guard_fs_tripwire` verweigert das, und der einzige Weg dort hindurch ist eine Freigabe, die
der Nutzer für genau ein Dokument erteilt.«

**E3 — Der Audit-Takt steht ab jetzt an zwei Stellen.** `_duties.audit_period_id` legt ihn als
ISO-Woche fest; die drei Verfassungen und die drei `project-auditor`-Texte sagen weiterhin „läuft
wöchentlich oder ereignisgetrieben". Vorschlag, wörtlich: »Der Takt steht im Code
(`_duties.audit_period_id`, eine ISO-Woche) und nicht hier ein zweites Mal.« Im selben Satz steht
dort die Behauptung, der Dispatch reite auf einer `APR.kind: routine` oder `analysis` — die es laut
Messung nicht anlegen lässt (`H111`); entweder sagt der Satz das, oder Strom F baut den Weg.

**E4 — Kein Rollentext kennt das Fristenregister.** Die Sitzungsstart-Meldung sagt dem Manager, dass
das Register VORSCHLÄGT und nichts tut; kein Text des `office-manager` sagt, was er damit tun soll.
Vorschlag, wörtlich, für `skills/office-manager/SKILL.md`: »Was der Sitzungsstart als DUE / OVERDUE
meldet, gehört in deinen ERSTEN Absatz an den Nutzer, in seinen Worten und mit dem Datum. Das
Register schlägt vor; entschieden wird vom Nutzer. Meldet es DEADLINE REGISTER INCOMPLETE, nenne die
Quelle, die nicht gelesen werden konnte — eine kurze Liste ist dann kein ruhiges Geschäft.«

**E5 (neu) — Der Onboarding-Schritt fragt die neuen Felder nicht ab.**
`skills/office-manager/SKILL.md:69` zählt auf, was das Interview in `business_profile.yaml` schreibt.
`tax.filings` und `receivables.payment_terms_days` fehlen dort; ohne sie bleibt das Register bei
einem frisch aufgesetzten Projekt stumm, und nach der Installation gibt es für dieses Dokument nur
noch `apply-proposal`. Vorschlag, wörtlich, als Ergänzung der Klammer: »…, die wiederkehrenden
Abgaben mit Periodenlänge und Verzugstagen (`tax.filings`) und das Zahlungsziel, ab dem eine offene
Rechnung eine Mahnung wert ist (`receivables.payment_terms_days`) — beide sind die Quellen der
Fristenmeldung beim Sitzungsstart; bleiben sie leer, meldet sie dazu nichts.«

**E6 (neu) — Ein Satz in den drei gespiegelten `session_status.py`.** Dort steht seit Längerem
„Reading the empty entry list as 'resolved' deleted a real backlog (BUG-0068)". `BUG-0068` hält
keine Löschung fest (siehe 2.3). Der Satz gehört dem, der die gespiegelte Datei besitzt — eine
Änderung nur in office hätte drei Fassungen erzeugt. Vorschlag, wörtlich: »Reading the empty entry
list as 'resolved' would delete a backlog nobody read (BUG-0068).«

### An Strom F (Kernel)

**F1 — `generated/session_brief.yaml` trägt keine Fristen.** FR-0034 nennt den Sitzungs-Brief als
den natürlichen Träger. Geliefert ist die Office-Seite: `_duties.register()` gibt die Fristen als
`{what, due, source}` zurück, `_duties.briefing()` den Absatz. Für den Brief selbst braucht es
`kernel/report.generate_session_brief` plus einen Abschnitt im Schema
`kernel/schemas/session_brief.yaml`.

**F2 — `routine`/`analysis` haben keinen Erzeuger** (`H111`). Solange das so ist, NENNT das Register
Rolle und Takt im Code. `test_no_routine_approval_can_be_minted_in_this_kit_today` wird rot, sobald
ein Weg dazukommt — dann gehört die Ableitung an die Freigabe.

**F3 — `dispatch.last_completed` / `next_due` haben weiterhin keinen Erzeuger** (der Ursprungsbefund
von FR-0038). Bekommt der Kernel einen, sollte `_duties.last_run` ihn lesen.

**F4 — Es gibt kein „erledigt"** (`H113`). Kanonischer Zustand und eine offene Entscheidung über die
FORM, keine Implementierungsfrage.

**F5 (neu) — Ein gemeinsamer Schlüssel für die beiden Ereigniszeilen** (`H112(b)`).
`gate_subagent_output` schreibt `gave_up`, `notify_agent_events` schreibt `subagent_stop`; beide
hängen am selben Ereignis, tragen nur einen Zeitstempel auf Sekunden und stehen in unbestimmter
Reihenfolge. Ein Schlüssel (die `session_id` genügt) würde die Zeilen verbinden — das ändert zwei
gespiegelte Haken in drei Kits.

### An Strom I / TSK-0109 (Dashboard) — mit meiner Entscheidung

**I1 — Das Finanz-Dashboard kann die Fristen zeigen, ohne sie zweimal abzuleiten.**
`_duties.register(root, today)` ist der eine Leser und gibt `(Liste, Unlesbares)` zurück. FR-0034
nennt diese Anzeige ausdrücklich als optional. **Entscheidung: gehört nach Strom I**, nicht hierher.

**I2 (a) — Auslöser für `templates/repo/tools/finance_dashboard.py` in
`gate_ledger_valid.handle_post_tool_use`. ENTSCHEIDUNG: NICHT verdrahtet, als Naht gemeldet.**
Der Grund ist der, den dieses Repo als Regel führt: der Generator liegt nicht in meinem Baum, also
kann ich **nicht messen, dass die Zeile etwas tut**. Eine fail-soft-Zeile, die niemand messen kann,
ist genau eine Schutzbehauptung ohne Bau — und `templates/repo/tools/**` steht zusätzlich in meinem
`forbidden_scope`. Der Ort ist `handle_post_tool_use`, nach der Gültigkeitsprüfung und vor dem
Rücksprung, damit ein ungültiges Ledger keine Anzeige erzeugt. Vorschlag, wörtlich:

```python
    # THE VIEW FOLLOWS THE LEDGER, and only a VALID one: this runs after the verdict above, so a
    # ledger that does not validate never produces a dashboard that looks authoritative.
    # FAIL-SOFT BY CONSTRUCTION -- a PostToolUse hook that refused here would turn a missing
    # generator into a refused write. Nothing here is the source of truth; the ledger is.
    generator = os.path.join(root, "tools", "finance_dashboard.py")
    if os.path.isfile(generator):
        try:
            subprocess.run([sys.executable, "-B", generator], cwd=root,
                           capture_output=True, timeout=DASHBOARD_BUDGET_SECONDS)
        except Exception:
            pass
```

Zwei Dinge, die der Strom, der das verdrahtet, mitliefern muss und die ich nicht liefern kann:
(1) eine Messung, die den Generator als Prozess laufen sieht und die erzeugte Datei prüft;
(2) eine Entscheidung zu `DEC-0028` — ein Hook startet hier einen PROZESS. Das ist kein
Modellprozess, also nicht der Fall, den `DEC-0028` verbietet; gesagt werden muss es trotzdem, weil
`_duties` daneben ausdrücklich gar keinen Prozess startet und der Unterschied sonst wie ein
Widerspruch aussieht. Was `repo_kit_owned.txt` erlaubt, ist die zweite Bedingung an den Pfad.

**I2 (b) — `payment_term_days` unter `tax:` in `business_profile.yaml`. ENTSCHEIDUNG: NICHT als
zweites Feld angelegt.** Das Zahlungsziel steht bereits in diesem Baum, als
`receivables.payment_terms_days`, mit dem Kommentarblock, der sagt, was es tut und was passiert,
wenn es leer bleibt. Ein zweites Feld unter `tax:` wäre eine zweite Wahrheit über dieselbe Zahl —
genau das, was dieses Repo als Defektklasse führt. Ein Zahlungsziel ist außerdem keine Steuerfrage.
**Für Strom I gilt damit: der Schlüssel ist `receivables.payment_terms_days`** (Ganzzahl Tage,
`null` = Funktion aus). Der Leser dafür existiert und heißt `_duties.receivable_duties`; wer die
Mahnkandidaten anzeigen will, ruft ihn auf, statt die Zahl ein zweites Mal zu interpretieren.
Der Onboarding-Satz dazu ist **E5** oben.

---

## 5. Läufe

Testumfang nach `DEC-0050` — die Suiten, die die geänderten Dateien LESEN. Die volle Suite läuft
**nicht** in dieser Runde; sie ist Lieferkriterium und gehört an die Merge-Runde, nach der letzten
Nacharbeit. Was hier lief, alles im Arbeitsbaum:

| Lauf | Ergebnis |
|---|---|
| `pytest tools/test_office_duties.py tools/test_kit_neutrality.py tools/test_repo_hygiene.py tools/test_disposition.py tools/test_gaplog.py` | **60 passed** |
| `pytest tools/test_hooks_v2.py -k "office or filing or ledger or gitignore or session_status or template or reaching or could_send"` | **733 passed** |
| `pytest tools/test_hooks.py -k "office or filing or ledger or session_status or mirror or shared_kit or trays or tripwire"` | erst 95 passed / **4 failed** (ausschließlich der fehlende Kit-Stempel), nach `bump_kit_version.py` **99 passed** |
| `pytest tools/test_hooks.py::test_the_shipped_scaffold_records_the_trays_of_the_kit_it_installs` | **4 passed** (8:08) |
| `pytest tools/test_shortening_net.py tools/test_context_budget.py` | **78 passed** — die Vorlagen sind dort nicht gepinnt, die Ratschen bleiben unberührt |
| `pytest .claude/hooks/test_gates.py -k "hole or measurement or reference"` | vorher 1 failed / 7 passed, nachher **8 passed** |
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |

Mutationsläufe (jeweils in einer Kopie **außerhalb** des Repos unter
`_round-scratch/TSK-0107/mutants/`, danach zurückgesetzt): `.gitignore`-Falle → rot; `import smtplib`
im Office-Kit → rot. Die beiden Zeiger-Defekte wurden am unreparierten Baum selbst rot gesehen
(2.1, 2.2), also ohne Mutation.

## 6. Stempel

`python tools/bump_kit_version.py` → `office-team: 2026.09.02-13` (dev/research unverändert
`2026.09.02-10`). **Provisorisch** — die Merge-Runde stempelt neu.

## 7. Übergabe

* Patch: `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0107/stream-office.patch` — 14 Dateien,
  2 331 Zeilen, +2 123 / −38 (`git add -N` für die vier neuen Dateien, `git diff HEAD`, **ohne**
  `project_memory/.audit/hook_events.jsonl`). Gegengeprüft: `git apply --check --reverse` läuft
  sauber gegen den Arbeitsbaum, der Patch bildet ihn also vollständig ab.
* Status: `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0107/git-status.txt`.
* Messungen: `docs/reviews/2026-09-02-tsk0107-office-duties-measurements.md` (Abschnitt 5 ist dieser
  Lauf).
* Nähte: Abschnitt 4 hier; `seam-notes.md` daneben ist der Stand des ersten Laufs und wird von
  diesem Abschnitt abgelöst.

## 8. Was offen bleibt, benannt

1. **`H111`, `H112(b)`, `H113`** — mit Messung, Urteil und Begrenzung in der Löcherliste. Keine
   davon hat eine Angriffskette; `H112(b)` ist ein falsch-negatives Nicht-Nörgeln in einer Fläche,
   die nur vorschlägt.
2. **F7 und F8 von `FR-0002`** — eigene Pakete, in `docs/office-kit-from-field.md` als offen
   eingetragen, mit der Stelle, an der sie hängen.
3. **Der Widerspruch im Item** zwischen `expected_outputs` 1 („session_status.py mirrored
   byte-identical") und der bestehenden, begründeten Ausnahme in `KIT_SPECIFIC_HOOKS`. Ich habe die
   Ausnahme gehalten; die Entscheidung gehört dem Nutzer bzw. der Merge-Runde.
4. **Der Neutralitätstest deckt Plattform-NAMEN und gefüllte Vorlagen-Listen ab, nicht jede Form von
   Produktgruppen-Bindung.** „Ist dieses Wort eine Handelsplattform" ist Weltwissen und bleibt eine
   Aufzählung — mit Stolperdraht an beiden Enden, aber ohne Anspruch auf Vollständigkeit. Ein
   Rollentext, der eine Produktgruppe in eigener Prosa nennt, ohne einen dieser Namen zu benutzen,
   wird nicht gefunden.
5. **`_duties.AUDIT_ROLE` deckt nur eine Richtung.** Eine ZWEITE prüfende Rolle würde unbemerkt
   danebentreten; „ist diese Rolle ein Prüfer" ist keine Eigenschaft, die eine ausgelieferte Datei
   trägt. Steht so im Kommentar.
6. **Der Rückruf-Nachweis ist ein Apparat-Nachweis.** Dass ein Modell dem beigebrachten Verfahren
   inhaltlich folgt, ist damit nicht gezeigt und gehört in einen `DEC-0025`-Piloten.
7. **`I2(a)`** — der Dashboard-Auslöser ist als Codeblock übergeben und bewusst nicht verdrahtet.
