# TSK-0077 — die Korrektur-Tür in der Ablage-Wand (FR-0050), gemessen

Umsetzer-Bericht. Item: `project_memory/tasks/active/TSK-0077.yaml` (derives_from `FR-0050`,
Hash-Regel aus `DEC-0048`). Stand vor der Runde: `2026.08.18-3`; ausgeliefert nach zwei
Prüfer-Runden als **office-team `2026.08.21-3`**, dev-team und research-team `2026.08.21-2`
(Runde 2 und 3 haben `_compat.py` angefasst, das in allen drei Kits liegt; die Office-Dateien
`guard_fs_tripwire.py`, `_filing.py` und `ENFORCEMENT.md` liegen nur in einem).

Jede Zahl unten ist an dieser Runde gemessen. Kein Satz behauptet Schutz, den der Code nicht
baut; wo eine Grenze offen bleibt, steht sie unter §7. §1-§5 sind der Erst-Bau, **§5a die
Nacharbeit auf Prüfer-Runde 1 (F1-F9)**, **§5b die auf Runde 2 (R1-R5)** — wo mehrere dasselbe
betreffen, gilt der spätere Abschnitt; §5c ist Runde 3 (V1-V6) und damit der letzte Stand.

---

## 1. Schritt 1 — was die Wand HEUTE tut (Ausgangsmessung)

Echte Hook-Prozesse, `guard_fs_tripwire.py` mit JSON auf stdin, gegen ein Projekt **außerhalb**
des Repos (`C:\Users\zenti\tsk0077\proj`, Trays `archive/1-Finanzen/2026/`, `inbox/`, `outbox/`,
leeres `project_memory/`), `HARNESS_KERNEL_PATH` auf `team-kits`. Gemessen 2026-08-18, vor jeder
Änderung:

| Kommandozeile | rc |
|---|---|
| `rm archive/1-Finanzen/2026/x.pdf` | 2 |
| `rm inbox/a.pdf` | 2 |
| `mv archive/1-Finanzen/2026/x.pdf outbox/x.pdf` | 2 |
| `mv archive/1-Finanzen/2026/x.pdf outbox/` | 2 |
| `cd archive/1-Finanzen/2026 && mv x.pdf ../../../outbox/` | 2 |
| `mv archive/1-Finanzen/2026/x.pdf archive/1-Finanzen/ok/` | 0 |

Also: die Wand steht in beide Richtungen, und ein Umzug INNERHALB des Archivs war nie diese
Regel. Was fehlte, war jede Tür — ein falsch abgelegtes Dokument blieb falsch abgelegt.

Ein Nebenbefund aus derselben Messung, der die Bauform mitbestimmt hat: die Verweigerung zur
Ordner-Schreibweise nannte als Ziel `outbox` (den Ordner), nicht `outbox/x.pdf` (die Stelle, an
der das Dokument landet). Eine Freigabe auf `outbox` hätte das Dokument nicht benannt.
`guard_fs_tripwire._landing` (Zeile 217) rechnet das jetzt aus, und die Verweigerung nennt seither
die Landestelle.

## 2. Der Entwurf, und warum er so und nicht anders liegt

**Eine neue APR-Art `filing_correction` auf der vorhandenen Maschinerie** — kein zweiter
Freigabe-Weg. Sie ist eine `LINE_MANIFEST_BUILDERS`-Art wie `push`/`preset`/`kit_update`, also
über `request-approval` von der Kommandozeile zu öffnen, vom Nutzer per `AskUserQuestion` zu
prägen, per `gate_approval` byte-verglichen.

**Was gehasht wird, ist genau die Operation plus ihr Grund** (DEC-0048 in konstruktiver
Richtung): `document`, `destination`, `content`, `reason`
(`approvals.filing_correction_subject_manifest`, Zeile 406). Der Torwächter vergleicht nur die
drei Operationsschlüssel (`filing_correction_operation`, Zeile 384) — der Grund ist, was dem
Nutzer gesagt wurde, nicht was die Shell tut; eine Freigabe ist keine andere, weil sie anders
begründet wurde.

**Löschen ist die Abwesenheit eines Ziels, nicht ein Wort.** `destination=""` heißt: das Dokument
landet nirgends. Damit die Kommandozeile das ausdrücken kann, liest `cli._line_manifest` jetzt die
SIGNATUR des Builders (`cli.optional_manifest_parameters`, Zeile 181): ein Subject-Schlüssel mit
Default darf auf der Zeile fehlen. Für `push`/`preset`/`kit_update` ändert das nichts — keiner von
ihnen hat einen Default, gemessen in
`tools/test_staging_cli.py::test_a_line_kind_without_a_defaulted_subject_key_still_demands_every_one`
(Zeile 631), inklusive `request-approval push --remote origin` → rc 2, "branch is missing".

**Einmalig, abgeleitet statt geflaggt.** `content` ist der SHA-256 der Bytes des Dokuments
(`hashing.document_content_hash`, Zeile 743). Nach der ausgeführten Korrektur liegt an der
Quelle nichts mehr, der Hash ist `None`, und dieselbe Freigabe deckt nichts mehr. Das ist exakt
die Bauform des Push-Tokens (`push_subject_manifest`): kein „verbraucht"-Flag in beschreibbarem
Zustand, das jemand ehrlich halten müsste.

**Wo die Mechanik liegt.** Der Auftrag nahm an, der Tripwire sei in allen drei Kits gespiegelt.
**Das stimmt nicht, gemessen:** `guard_fs_tripwire.py`, `gate_filing.py` und `_filing.py` liegen
NUR in `team-kits/office-team/hooks/` (dev und research haben keine dieser drei Dateien). Damit
löst sich die Ableitungsfrage von selbst: die Freigabe-Mechanik liegt im **gemeinsamen Kernel**
(`team-kits/kernel/`, eine Quelle für alle Kits), die Tür-Seite im Office-Guard. Keine Kopie pro
Kit, kein Eintrag in `KIT_SPECIFIC_HOOKS` nötig.

**Die Schichtgrenze, die der Auftrag als möglichen Abbruchgrund nannte, hält — mit einer
Bedingung.** `_filing.py` sagt ausdrücklich, warum `_kernel` in diesem Guard nichts zu suchen
hat: der Bridge-Import bewaffnet einen Excepthook, der jeden entkommenden Fehler zu rc 2 macht,
und der Vertrag dieses Guards ist „Unsicherheit → durchlassen". Gelöst, ohne den Vertrag zu
brechen: `correction_authority` (Zeile 410, in der Nacharbeit aus `approved_correction`
hervorgegangen) importiert die Bridge **erst auf dem Zweig, der ohnehin schon verweigert**, fängt
dort `BaseException` zu `None` und ruft `_kernel.disarm()` im `finally`. Damit gilt der alte Vertrag für jeden Aufruf, der die Trays nicht anfasst, und auf dem
Verweigerungszweig fallen beide Verträge zusammen: „konnte ich nicht prüfen" = „keine Freigabe" =
die Wand steht.

**gate_filing bleibt unberührt, und zwar per Ableitung.** Eine Operation, die diese Tür öffnet,
landet nie unter `archive/`: ein Löschen landet nirgends, und ein Move-out ist per Definition der
Bedingung in `_move_readings` (Zeile 244) einer, dessen Ziel NICHT unter `archive/` liegt. Die
Aktenplan-Prüfung von `gate_filing` ist damit für keine dieser Operationen die zweite Wand — sie
ist es unverändert für jede Ablage INS Archiv. Der einzige Fall, in dem beide Hooks zugleich
sprechen, ist ein Kommando, das unter der einen Lesart ablegt und unter einer anderen ausräumt;
dann entscheidet jeder Hook weiter seine eigene Frage, und `gate_filing` wurde nicht angefasst.

## 3. Was gebaut wurde, Datei für Datei

Zeilennummern gegen den AUSGELIEFERTEN Stand neu abgeleitet, nicht gegen einen
Zwischenstand.

| Datei:Zeile | Was |
|---|---|
| `team-kits/kernel/hashing.py:707` | `DOCUMENT_HASH_LIMIT` (256 MiB) mit der Messung, warum es eine Schranke gibt |
| `team-kits/kernel/hashing.py:710` | `on_disk_position` — die Schreibweise, die das Dateisystem trägt (R2) |
| `team-kits/kernel/hashing.py:743` | `document_content_hash` — die Fassung eines Dokuments, `None` statt Ausnahme |
| `team-kits/kernel/approvals.py:58/77` | `filing_correction` in `APR_KINDS` und in `EXPIRING_KINDS` |
| `team-kits/kernel/approvals.py:304` | `filed_position` — EINE Schreibweise einer Position für beide Seiten (ohne `strip("/")`, F5) |
| `team-kits/kernel/approvals.py:328` | `is_project_position` — ist das ein Ort, den dieses Projekt hat? (F5/F7) |
| `team-kits/kernel/approvals.py:355/358` | `REASON_SHOWN` + `_one_line` — der Grund als EINE Zeile, vor dem Hash (F4) |
| `team-kits/kernel/approvals.py:384` | `filing_correction_operation` — die drei Fakten, die ein Gate messen kann |
| `team-kits/kernel/approvals.py:406` | `filing_correction_subject_manifest` — plus `reason`, `destination` mit Default, zwei Verweigerungen (F5/F7) |
| `team-kits/kernel/approvals.py:474` | Eintrag in `LINE_MANIFEST_BUILDERS` |
| `team-kits/kernel/approvals.py:980/1021` | `_filing_correction_target_form` + `TARGET_FORMS` |
| `team-kits/kernel/approvals.py:1206` | `_in_force_approvals` — die EINE Definition von „in Kraft" (aus `live_line_approval` gehoben) |
| `team-kits/kernel/approvals.py:1254` | `correction_operation_key` — EIN Schlüssel, von beiden Seiten gleich gebildet |
| `team-kits/kernel/approvals.py:1273` | `live_correction_approvals` — die MAP, ein Speicher-Lauf je Aufruf (F3) |
| `team-kits/kernel/approvals.py:1303` | `live_correction_approval` — die Einzelfrage über dieselbe Map |
| `team-kits/kernel/cli.py:181` | `optional_manifest_parameters` |
| `team-kits/kernel/cli.py:259` | `_document_content` — hasht das Dokument, verlangt die zurücklaufende Schreibweise (F5) |
| `team-kits/kernel/cli.py:314/339` | `_line_manifest` respektiert den Default des Builders; die Fehl-Meldung ist abgeleitet (F8) |
| `team-kits/kernel/migrate.py:117` | die Aufzählung der Line-Arten wird zur Eigenschaft (F9) |
| `team-kits/office-team/hooks/_filing.py:407` | `invocations` — die Zeile ganz, Invocation für Invocation (F1) |
| `…_filing.py:424/429/437/454` | `move_of`, `operands_of`, `directory_change`, `rewritten_by_the_shell` |
| `team-kits/office-team/hooks/_compat.py:76` | `HOOK_DEADLINE_SECONDS` — die Frist, an genau EINEM Ort (R4) |
| `…_filing.py:83/266/449` | `REDIRECT_SPAN_RX`, `_tokens` (schneidet die Umleitung heraus statt abzubrechen, V2), `redirects_of` (R1) |
| `…guard_fs_tripwire.py:151/157/160` | `CORRECTION_COST_SECONDS`, `CORRECTION_BUDGET_SHARE`, `budget_cap()` — die Decke, abgeleitet (R3) |
| `…guard_fs_tripwire.py:183` | `CORRECTION_CAP = 25` — gewählt aus einem Produktgrund, gemessen unter der Decke (F3/R3) |
| `…guard_fs_tripwire.py:188` | `CORRECTION_REMEDY` — der Weg hinaus, einmal geschrieben, in BEIDEN Verweigerungen |
| `…guard_fs_tripwire.py:217/234/244` | `_landing`, `_protected_readings`, `_move_readings` |
| `…guard_fs_tripwire.py:266/291` | `Line` + `read_the_line` — was die Zeile tut, und was der Guard NICHT platzieren konnte (F1/F2) |
| `…guard_fs_tripwire.py:410` | `correction_authority` — die Bridge, einmal pro Aufruf, mit `disarm()` (F3) |
| `…guard_fs_tripwire.py:449` | `open_the_door` — EINE Entscheidung über die ganze Zeile, vier Bedingungen |
| `…guard_fs_tripwire.py:530` | `record_corrections` — die Journalzeile, EINMAL am Ende beider Regeln |
| `team-kits/office-team/agents/records-clerk.md` | die Anfrage-Hälfte, ehrlich: anfragen, nicht umgehen |
| `team-kits/office-team/constitution/AGENTS.md` §2/5 | die Wand hat eine Tür, und was sie bindet |
| `team-kits/office-team/hooks/ENFORCEMENT.md` §1 | dieselbe Aussage, mit den Grenzen |

## 4. Die Frage-Sätze (BUG-0041-Publikum)

Gemessen über den ausgelieferten `request-approval`-Weg, echte Ausgabe:

> Freigabe erbeten: filing_correction für **eine Korrektur der Ablage: das Dokument
> »archive/1-Finanzen/2026/x.pdf« wird verschoben nach »outbox/x.pdf«** (Grund: falsch abgelegt;
> die Freigabe gilt nur für genau diese Fassung des Dokuments, Prüfsumme c24189a7647a…, und nur
> bis 2026-08-18T07:35:01Z) (Revision -, subject_manifest sha256 ea403d60de93…). …

> Freigabe erbeten: filing_correction für **eine Korrektur der Ablage: das Dokument
> »inbox/a.pdf« wird GELÖSCHT und ist danach weg** (Grund: Doppelscan derselben Rechnung; …).

Beide Ausgänge stehen als das da, was sie TUN. Kein Leser muss bemerken, dass ein Feld leer ist,
um zu erfahren, dass ein Dokument vernichtet wird. Jeder gehashte Schlüssel steht im Satz
(Dokument, Ausgang, Grund, Fassung, Ablauf) — das ist einer mehr als `_push_target_form` und
`_preset_target_form` zeigen — und die Prüfsumme wird wie jeder Digest in dieser Frage auf 12
Zeichen gekürzt (`_render_manifest_value`), weil eine 64-stellige Hexzahl mitten im Satz die
`kit_update`-Frage schon einmal unlesbar gemacht hat.

## 5. Schritt 3 — was gemessen wurde, und was ohne den Fix ROT wird

### 5.1 Die vier vom Item verlangten Eigenschaften (echte Hook-Prozesse)

Alle in `tools/test_hooks.py`, Abschnitt „FR-0050", jeweils gegen ein `tmp_path`-Projekt mit
echten Bytes in den Trays; die Freigabe wird über die AUSGELIEFERTE CLI angefordert und über den
ECHTEN `gate_approval.py`-Hook geprägt (`conftest.mint_via_hook`).

| # | Eigenschaft | Test |
|---|---|---|
| (a) | heute verweigert → freigegeben durchgelassen → nach dem Umzug wieder rc 2 | `test_a_correction_the_user_approved_is_the_one_operation_the_tripwire_lets_through` (8953), `test_a_correction_approval_stops_matching_once_the_document_is_gone` (8998) |
| (b) | eine ANDERE Operation unter derselben Freigabe → rc 2 (anderes Dokument, anderes Ziel, Löschen statt Verschieben, ein zweites unfreigegebenes Dokument daneben, zwei Dokumente in EINEM Move) | `test_a_different_operation_is_not_covered_by_a_correction_approval` (9030, 5 Fälle), `test_a_correction_approval_covers_one_version_of_the_document_and_not_a_path` (9043) |
| (c) | zurückgezogen / abgelaufen → rc 2 | `test_a_revoked_correction_approval_opens_nothing` (9057), `test_a_lapsed_correction_approval_opens_nothing` (9075) |
| (d) | alle Standardwege ohne Freigabe → rc 2, mit Kernel-Zustand und ohne | `test_the_wall_still_refuses_every_correction_nobody_approved` (8932) |

Dazu: `test_an_approved_deletion_is_the_half_that_has_no_destination` (8976),
`test_a_document_too_large_to_bind_cannot_be_corrected_by_approval` (9088),
`test_a_correction_of_an_umlaut_document_is_one_operation_in_both_normalisations` (9107),
`test_the_correction_door_is_journaled_and_the_note_claims_no_more_than_it_saw` (9153),
`test_a_refused_call_leaves_no_note_claiming_a_correction_was_let_through` (9173),
`test_a_refusal_names_the_document_that_is_missing_its_approval` (9192),
`test_both_refusals_name_the_one_route_a_correction_takes` (9221).

Kernel-/CLI-Seite in `tools/test_staging_cli.py`: `…_without_a_defaulted_subject_key…` (631),
`test_a_filing_correction_question_says_in_words_what_happens_to_the_document` (650),
`test_a_document_the_kernel_cannot_hash_is_refused_where_the_clerk_types_it` (683),
`test_a_document_outside_the_project_is_refused_rather_than_bound_to_an_approval_that_cannot_match`
(696), `test_the_correction_hash_binds_the_operation_and_the_reason_beside_it` (712),
`test_one_position_has_one_spelling_on_both_sides_of_a_correction` (740).

### 5.2 Rot-Nachweis: jeder Defekt in einem Klon AUSSERHALB des Repos wiederhergestellt

Klon: `C:\Users\zenti\tsk0077\clone` (Kopie von `team-kits/`, `tools/`, `docs/`, `user/`).
Skript: `C:\Users\zenti\tsk0077\red.py` — setzt den Defekt, fährt die betroffenen Tests, setzt
zurück. Jede Zeile ist ein eigener Lauf.

| Wiederhergestellter Defekt | Ergebnis | rot geworden |
|---|---|---|
| M1 die Tür existiert nicht (HEAD-Verhalten: keine Freigabe wird je gelesen) | 7 failed, 9 passed | alle Durchlass-Tests (a)/(b)-Gegenprobe/(c)-erste Hälfte/Journal/Umlaut |
| M2 `content` bindet nichts (`"content": ""`) | 1 failed | `…covers_one_version_of_the_document_and_not_a_path` |
| M3 abgelaufene Freigabe gilt weiter | 1 failed | `…lapsed_correction_approval_opens_nothing` |
| M4 Widerruf ist nur ein Flag und wird nicht gelesen | 1 failed | `…revoked_correction_approval_opens_nothing` |
| M5a Löschen hört beim ersten Operanden auf | 1 failed | `…approved_deletion_is_the_half_that_has_no_destination` |
| M5b Move-out hört bei der ersten Invocation auf | 1 failed, 4 passed | `…different_operation…[… && mv y …]` |
| M5c ein Move wird nur nach seiner ersten Quelle gefragt | 1 failed, 4 passed | `…different_operation…[zwei Dokumente in EINEM Move]` |
| M6 Zielordner wird nicht zur Landestelle aufgelöst | 1 failed | `…one_operation_the_tripwire_lets_through` |
| M7 ein Subject-Schlüssel mit Default darf doch nicht fehlen | 1 failed | `…approved_deletion…` |
| M8 Operationsvergleich byte-weise statt kanonisch | 1 failed, 1 passed | `…umlaut_document_is_one_operation_in_both_normalisations` |
| M9 Dokument-Hash ohne Größenschranke | 1 failed | `…too_large_to_bind_cannot_be_corrected_by_approval` |
| M10 ein getippter Pfad wird genommen, wie er getippt wurde | 1 failed | `…one_position_has_one_spelling_on_both_sides_of_a_correction` |
| M11 die Lösch-Verweigerung nennt keinen Weg hinaus | 1 failed | `…both_refusals_name_the_one_route_a_correction_takes` |
| M12 die Art hat keine lesbare Form (Manifest-Schlüssel werden gerendert) | 1 failed | `…question_says_in_words_what_happens_to_the_document` |
| M13 die Journalzeile wird schon im ersten Zweig geschrieben | 1 failed | `…leaves_no_note_claiming_a_correction_was_let_through` |
| M14 die Verweigerung nennt die erste statt der unfreigegebenen Operation | 1 failed | `…refusal_names_the_document_that_is_missing_its_approval` |
| M15 ein Dokument außerhalb des Projekts wird trotzdem gehasht und signiert | 1 failed | `…outside_the_project_is_refused_rather_than_bound_to_an_approval_that_cannot_match` |

Zwei Messungen aus dieser Reihe haben den Bau korrigiert statt bestätigt, und beide standen im
ersten Durchgang GRÜN, obwohl der Defekt gesetzt war:

* die ursprüngliche Fassung von M5 traf nur den Lösch-Leser, während der gemessene Testfall ein
  Move war — der Test hätte den Gruppierungs-Fix nie verteidigt. Jetzt drei getrennte Defekte
  (M5a/b/c) und zwei zusätzliche Testfälle (zwei Dokumente in einem `rm`, zwei Quellen in einem
  `mv`).
* der Umlaut-Test bewies nichts über `live_correction_approval`: NTFS speichert den Namen so, wie
  er gegeben wurde, also waren beide Seiten ohnehin komponiert. Der Test prägt jetzt eine Freigabe
  auf die ZERLEGTE Schreibweise und fragt die Tür mit der KOMPONIERTEN — und der Docstring
  behauptet seither nicht mehr, irgendein Dateisystem hier liefere die zerlegte Form.

### 5.3 Drei Defekte, die ich beim eigenen Nachlesen gefunden habe (M13–M15)

Sie stammen aus dieser Runde, nicht aus dem Bestand, und stehen hier, weil das die Fehlerklasse
ist, die dieses Projekt reihenweise gekostet hat — die Korrektur bringt den nächsten Defekt mit:

* **die Journalzeile stand im ersten Zweig.** Lösch- und Move-Regel werden nacheinander geprüft.
  Ein Kommando, das ein freigegebenes Dokument löscht UND ein nicht freigegebenes aus dem Archiv
  bewegt, wurde von der ersten Regel durchgelassen und von der zweiten verweigert — und die
  Journalzeile behauptete „allowed under APR-0001" für einen Aufruf, der mit rc 2 endete. Jetzt
  wird EINMAL am Ende geschrieben, wenn jede Prüfung durch ist.
* **die Verweigerung nannte die erste Operation.** Mit einem freigegebenen und einem nicht
  freigegebenen Dokument auf derselben Zeile nannte sie das FREIGEGEBENE — die Rolle wäre zum
  Nutzer gegangen und hätte eine Freigabe erbeten, die sie schon hatte. `first_unapproved` nennt
  jetzt die, die fehlt.
* **ein Dokument außerhalb des Projekts wurde gehasht und signiert.** `guard_fs_tripwire` fragt
  nur nach Positionen RELATIV zur Projektwurzel; ein absoluter oder herauskletternder Pfad hätte
  eine Freigabe geprägt, die nie auf irgendetwas passt — eine Sackgasse ohne Meldung. Wird jetzt
  dort verweigert, wo der Sachbearbeiter sie tippt.

## 5a. NACHARBEIT nach dem Prüfer-Urteil FAIL (F1–F9)

Der Prüfer hat den Entwurf angegriffen und den KERN bestätigt (Zwillinge rc 2, Copy-then-delete
rc 2, Wieder-Ablage ins Archiv weiter von `gate_filing` gegen den Plan geprüft, Widerruf/Ablauf/
Manipulation korrekt, DEC-0048-Oberfläche byte-gleich, alle M-Rots reproduziert). Falsch war die
**Kante**: drei in einer Sitzung durchlaufende Löcher, die die Tür selbst eingebaut hat.

### F1 — die Freigabe deckte die ZEILE, nicht die Operation (blockierend)

`honoured += covered` machte aus „jede GESEHENE Operation ist freigegeben" die Durchlassbedingung
für die ganze Kommandozeile: alles, was der Guard nicht platzieren konnte, fuhr mit. Vom Prüfer
gemessen (echte Ketten, alle sechs registrierten Einträge, rc 0 wo HEAD rc 2 sagte).

Gebaut: der Guard liest jetzt die Zeile **Invocation für Invocation** (`_filing.invocations`,
`_filing.py:407`) und stuft jede als genau eines von vier Dingen ein — ein Verzeichniswechsel, den
er ausrechnen konnte; eine Kopie/Verschiebung; ein Löschen; **oder etwas anderes**. „Etwas anderes"
lässt die Tür zu. `guard_fs_tripwire.read_the_line` (Zeile 291) liefert das als `Line.unplaced`
(Zeile 266), und `open_the_door` (Zeile 449) entscheidet **einmal über die ganze Zeile**.

Nachher gemessen, alle rc 2 (vorher rc 0), Freigabe für `archive/1-Finanzen/2026/x.pdf →
outbox/x.pdf` liegt jeweils vor:

| Kette | vorher | nachher |
|---|---|---|
| `mv … outbox/x.pdf` allein (Gegenprobe) | 0 | **0** |
| `… && python -c "os.remove('archive/…/y.pdf')"` | 0 | **2** |
| `… && tar -cf a.tar --remove-files archive/…/y.pdf` | 0 | **2** |
| `… && rm $A` | 0 | **2** |
| `… && echo done` | 0 | **2** |
| `rm inbox/a.pdf $A` unter der Lösch-Freigabe | 0 | **2** |

### F2 — der „theoretische" Rohtext-Fall war konstruierbar (blockierend)

`rm inbox/a.pdf ~/archive/secret.pdf` unter der Inbox-Freigabe war rc 0: `DELETE_RX` feuert auf
`archive/`, der auflösende Leser platziert nur den freigegebenen Operanden, alles Gesehene ist
freigegeben — und die Shell expandiert `~` und löscht in `$HOME`. Der Satz in `ENFORCEMENT.md:33`
war damit **gemessen falsch**.

Gebaut, und ein Operand muss jetzt in ZWEI Bedeutungen platzierbar sein (`read_the_line`,
`unplaceable`):

* sein **Text muss der Pfad sein** (`_filing.rewritten_by_the_shell`, `_filing.py:454`) — `~`,
  `$VAR`, Glob, `%VAR%`;
* er muss **in eine Position im Projekt auflösen**.

Die zweite Hälfte habe ich beim eigenen Rot-Lauf gefunden, nicht der Prüfer: mein erster Fix ließ
`rm inbox/a.pdf ../archive/x.pdf` und `… /etc/passwd` durch (gewöhnlicher Text, kein `~`, keine
Variable — sie lösen nur in keine Position auf und wurden fallengelassen). Und die Rohtext-Regel
war dabei durch **nichts** gemessen: die Mutation N2b blieb im ersten Durchgang grün, weil die
Expansionsregel alle Testfälle schon abfing. Sie ist jetzt eigenständig gemessen — an einer
Über-Verweigerung (`rm outbox/archive-copy.txt` neben einer freigegebenen Korrektur), was sie
ehrlich ist: sie kostet eine Korrektur auf dieser Zeile, nie ein Dokument.

### F3 — die Tür machte aus einer Verweigerung eine Zeitüberschreitung (blockierend, schärfster)

Ein getöteter Hook wird vom Provider als „hook error, carry on" gelesen — also als **Durchlass**,
auf genau dem Aufruf, den die Wand verweigern soll. Gemessen vom Prüfer **ohne jede Freigabe**:
296-KB-Zeile, 8000 Archivdokumente an einem `rm` → **114 349 ms** (HEAD: 540 ms), linear skalierend
(204 APRs, 300 Operanden → 69,8 s). Registrierung ohne `timeout` → Provider-Vorgabe 60 s → getötet →
die Massenlöschung läuft **unverweigert**.

Vier Ursachen, vier Fixes:

1. **Speicher-Scan einmal pro Aufruf** statt pro Operand: `approvals.live_correction_approvals`
   (`approvals.py:1273`) liefert eine MAP `{Operationsschlüssel: Freigabe}`; der Guard holt sie
   einmal (`correction_authority`, `guard_fs_tripwire.py:410`) und macht danach Wörterbuch-Zugriffe.
   Beide Seiten bilden den Schlüssel mit **derselben** Funktion (`correction_operation_key`,
   `approvals.py:1254`).
2. **`open_state` einmal pro Aufruf** — im selben Griff.
3. **Dokument-Hash je Position memoisiert** (`versions` in `open_the_door`).
4. **Abbruch beim ersten ungedeckten Operanden**, und eine **Obergrenze**:
   `CORRECTION_CAP = 25` (`guard_fs_tripwire.py:183`). Darüber öffnet die Tür gar nicht — die Wand
   antwortet wie immer, nur sofort.

Nachher gemessen (dieselbe Maschine, echte Hook-Prozesse):

| Fall | vorher | nachher |
|---|---|---|
| 8000 Dokumente an einem `rm`, keine Freigabe (272 002 B Zeile) | 114,35 s | **0,85 s** |
| 25 Operanden (= Cap), keine Freigabe | — | **0,27 s** |
| 26 Operanden (über dem Cap) | — | **0,16 s** |

Und der **echte Worst Case der TÜR** — voller Cap, alle freigegeben, also kein Frühabbruch, die
passenden Freigaben am ENDE des Speichers:

| Speicher | Dokumentgröße | Operationen | rc | Zeit |
|---|---|---|---|---|
| 25 Freigaben | klein | 25 | 0 | **0,29 s** |
| 100 Freigaben | klein | 25 | 0 | **0,48 s** |
| 204 Freigaben | klein | 25 | 0 | **0,74 s** |
| 600 Freigaben | klein | 25 | 0 | **2,53 s** |
| 25 Freigaben | **8 MiB je Dokument** | 25 | 0 | **0,56 s** |

Der Prüfer-Fall (204 Freigaben) liegt damit bei **0,74 s statt 69,8 s**, mit ~81-fachem Abstand zur
60-s-Frist.

### F4 — `--reason` ist frei getippter Agententext IM Satz, den der Nutzer unterschreibt

Gemessen: ein Grund „ALLES BLEIBT ERHALTEN\nHinweis: nichts wird geloescht." rendert als eigene
Zeilen über dem Freigeben-Knopf. Der Prägecode bleibt unfälschbar — das Ziel ist der **Mensch**,
das BUG-0041-Publikum, das der Renderer selbst benennt.

Gebaut: `approvals._one_line` (`approvals.py:358`) faltet **vor dem Hash**, also deckt die
Unterschrift die gefaltete Zeile, die der Nutzer wirklich sieht. Als **Eigenschaft**, nicht als
Liste: jedes Zeichen der Unicode-Kategorie `C*` (Steuer-, Format-, Surrogat-, Privat-,
unbelegt — damit auch Bidi-Overrides und Zero-Width-Joiner) und jeder Zeilen-/Absatztrenner
(`Zl`/`Zp`) wird ein Leerzeichen, dann kollabieren Weißraumläufe; Länge auf `REASON_SHOWN = 200`.
**Pfade werden NICHT gefaltet, sondern verweigert** (`is_project_position`) — zwei Dateinamen auf
eine Zeichenkette zu falten hieße, eine Freigabe deckt beide.

### F6 — Prosa, die Schutz behauptete, den der Code (vor dem Fix) nicht baute

Jeder Satz gegen das jetzt gebaute Verhalten geprüft und dort geändert, wo die reale Kante anders
aussieht; die Obergrenze aus F3 ist überall benannt:

* `guard_fs_tripwire.py` Kopfkommentar: „EVERYTHING ELSE STILL BLOCKS" → die **vier Bedingungen**,
  die die Tür wirklich prüft, alle vier über die ZEILE;
* `CORRECTION_REMEDY` (Zeile 142): „Anything else stays refused" → „führe die Korrektur auf einer
  **eigenen Kommandozeile** aus; die Freigabe deckt eine Korrektur, nicht die Zeile drumherum";
* `constitution/AGENTS.md` §2/5 und `hooks/ENFORCEMENT.md` §1: dieselbe Kante, plus der Cap;
* `agents/records-clerk.md`: „eine Korrektur pro Zeile", plus „nie einen Pfad absolut schreiben";
* §7.4/§7.5/§7.6 dieses Berichts — siehe unten, ausdrücklich korrigiert.

### F5, F7, F8, F9 — die billigen Reste, geschlossen

* **F5**: `_document_content` (`cli.py:259`) verlangt jetzt, dass die getippte Schreibweise
  **zurückläuft** — gegen die Projektwurzel aufgelöst und zurücknormalisiert muss dasselbe
  herauskommen. Zusätzlich hört `filed_position` (`approvals.py:304`) auf, mit `strip("/")` aus
  `/etc/passwd` das projekt-aussehende `etc/passwd` zu machen; `is_project_position`
  (`approvals.py:328`) entscheidet, ob eine Position ein Ort dieses Projekts ist.
* **F7**: ein **ausdrücklich angegebenes** Ziel, das leer normalisiert (`.`, `./`, `/`, Leerzeichen),
  wird verweigert (`approvals.py:453`) — es wäre sonst still zur LÖSCHUNG in der Frage geworden.
  Das Weglassen der Flagge bleibt die Art, eine Löschung zu erbitten.
* **F8**: die Fehl-Meldung für einen fehlenden Subject-Schlüssel wird aus denselben zwei Aussagen
  abgeleitet, auf die die Schleife entscheidet (`cli.py:339`) — sie nennt `--content` nicht mehr
  (resolver-eigen, beim Tippen verweigert) und `--destination` als optional in Klammern.
* **F9**: `migrate.py` nennt keine vier Line-Arten mehr und keine Zahl, sondern die Eigenschaft.
* **Einmaligkeit ehrlicher gefasst** (`approvals.py:406`): die Freigabe deckt **diese Bytes an
  dieser Stelle, solange sie dort liegen** — also auch wieder, wenn eine byte-gleiche Datei
  zurückgelegt wird. Der Fragetext sagte das schon; der Docstring war enger als die Wirklichkeit.
* **Ein Nebenbefund aus F7**: ein Builder, der sein Subject verweigert, verweigert die ZEILE. Als
  `ApprovalError` kam das als Exit 1 zurück, neben Exit 2 des Resolvers für dieselbe Flagge —
  gleiche Eingabe, gleicher Fehler, zwei Codes. `_line_manifest` übersetzt das jetzt in eine
  `UsageError`.

### Rot-Nachweis der Nacharbeit

Klon außerhalb des Repos, Skript `C:\Users\zenti\tsk0077\red2.py`; jeder Defekt einzeln gesetzt,
Tests gefahren, zurückgesetzt:

| Wiederhergestellter Defekt | Ergebnis |
|---|---|
| N1 die Tür ignoriert, was sie auf der Zeile nicht platzieren konnte (F1) | 5 failed |
| N2a ein Operand, dessen TEXT nicht der Pfad ist, wird fallengelassen (F2) | 1 failed |
| N2b ein Operand, der keinen Ort im Projekt nennt, wird fallengelassen | 1 failed |
| N2c die beiden Lösch-Lesarten werden nicht je Invocation verglichen (F2) | 1 failed |
| N3 die Tür hat keine Obergrenze für ihre Arbeit (F3) | 1 failed |
| N3b der Freigabe-Speicher wird je Operand statt je Aufruf aufgelöst (F3) | 1 failed |
| N4 ein frei getippter Grund erreicht die Frage ungefaltet (F4) | 1 failed |
| N5 die getippte Schreibweise muss nicht zurücklaufen (F5) | 1 failed |
| N7 ein Ziel ohne Position wird zur Löschung (F7) | 3 failed |
| N8 die Fehl-Meldung druckt jeden Manifest-Schlüssel als Flagge (F8) | 1 failed |
| N9 `filed_position` behält `strip()`, ein absoluter Pfad sieht relativ aus (F5) | 1 failed |
| N10 ein unplatzierbarer Move-Operand verdeckt die Verschiebung daneben | 3 failed |
| N10b ein unplatzierbarer Lösch-Operand verdeckt das Löschen daneben | 1 failed |

### Ein Loch, das die Nacharbeit selbst eingebaut hat — vom Abschlusslauf gefangen

Der erste vollständige `tools/`-Lauf nach der Nacharbeit meldete **`1 failed, 2870 passed`** in
`tools/test_hooks.py::test_fs_tripwire_blocks_move_out_of_archive` — einem Test, der ÄLTER ist als
diese Tür. `mv archive/fin/a.pdf /tmp/gone.pdf`, also ein Move, der das Archiv an ein Ziel
außerhalb des Projekts leert, war **rc 0 statt rc 2**.

Ursache: ich hatte „die Tür kann nicht öffnen" mit „der Guard hat nichts gesehen" verwechselt. Eine
Invocation mit einem unplatzierbaren Operanden wurde ganz übersprungen (`continue`), also erreichten
die Operationen, die sie SEHR WOHL platziert hatte, die Verweigerung nie — und `/tmp/gone.pdf` ist
genau so ein unplatzierbarer Operand. Die WAND verlor damit den Fall, für den es sie gibt.

Gebaut: `unplaced` wird notiert, die Lesung läuft weiter; nur `open_the_door` fragt `unplaced`
überhaupt ab. Dazu drei neue Fälle, die dieselbe Verwechslung auch dort messen, wo kein älterer
Test hinsieht — auf der Lösch-Seite und hinter einem `cd`
(`tools/test_hooks.py::test_an_operand_this_guard_cannot_place_never_hides_the_operation_beside_it`).
Ohne den Fix: N10 → 3 failed, N10b → 1 failed.

Neue Tests: `tools/test_hooks.py::test_an_approval_covers_its_correction_and_not_the_rest_of_the_line`
(9252, 4 Fälle), `…::test_a_delete_approval_does_not_cover_an_operand_the_shell_rewrites` (9270),
`…::test_a_delete_approval_does_not_cover_an_operand_outside_this_project` (9288),
`…::test_the_two_delete_readings_disagreeing_keeps_the_line_shut` (9304),
`…::test_the_door_refuses_a_line_that_would_correct_more_than_it_may_decide_about` (9322),
`…::test_the_door_reads_the_approval_store_once_however_many_documents_a_line_names` (9350),
`…::test_a_reason_the_requester_typed_cannot_write_its_own_lines_into_the_question` (9394),
`…::test_a_correction_approval_covers_the_bytes_again_when_they_are_put_back` (9021);
`tools/test_staging_cli.py::test_a_document_named_in_a_spelling_the_gate_cannot_produce_is_refused_at_the_command_line`
(712), `…::test_a_destination_that_names_no_place_in_this_project_is_refused` (737, 6 Fälle),
`…::test_the_missing_key_remedy_names_the_flags_this_command_really_takes` (757).

Der Latenz-Test misst **den Cap und eine Zählung**, keine Wanduhr: eine Sekundenbehauptung in der
Suite ist ein Flackern, das auf eine ausgelastete Maschine wartet. Die Zählung läuft gegen die
Funktion, die WIRKLICH läuft — `guard_fs_tripwire.open_the_door` über einen echten Freigabe-Speicher,
mit gezähltem `kernel.approvals.consumed_request`: einmal je gespeicherter Freigabe ist ein Scan.

## 5b. NACHARBEIT nach Prüfer-Runde 2 (R1–R5)

Runde 2 hat F1–F9 und N10 **bestätigt** (alle Reiter rc 2, die F2-Ketten rc 2, die F3-Zahlen
reproduziert, die Cap-Grenze exakt, die Faltung als Eigenschaft mit `hash(roh) == hash(gefaltet)`,
die 22-Fall-Wand-Batterie NEU == HEAD Zeile für Zeile, DEC-0048-Oberfläche byte-gleich). Ein neuer
blockierender Rand plus vier Reste.

### R1 — Ausgabe-Umleitungen waren nicht Teil der Zeile, die die Tür liest (blockierend)

`>` ist Shell-Syntax, kein Operand: `_filing._tokens` schneidet die Umleitung von der Argumentliste
ab, also konnte kein Leser von Operanden sie je sehen. Gemessen mit lebender Freigabe — sechs
Ketten rc 0, obwohl die Umleitung ein Dokument von Rang auf null Bytes kürzt:

| Kette | vorher | nachher |
|---|---|---|
| `mv …/x.pdf outbox/x.pdf` allein (Gegenprobe) | 0 | **0** |
| `… > inbox/b.pdf` | **0** | **2** |
| `… >> inbox/b.pdf` | **0** | **2** |
| `… > archive/1-Finanzen/2026/b.pdf` | **0** | **2** |
| `… > $LOG` | **0** | **2** |
| `rm inbox/a.pdf > inbox/b.pdf` (Lösch-Freigabe) | **0** | **2** |
| `rm inbox/a.pdf >> inbox/b.pdf` | **0** | **2** |
| `… \| tee inbox/b.pdf` (unlesbare Invocation) | 2 | **2** |
| `… > outbox/log.txt` (außerhalb der Trays) | 0 | **0** |

Gebaut: `_filing.redirects_of` (die Fläche, die der Ledger-Guard seit BUG-0003 schon liest) je
Invocation, und `read_the_line` behandelt jedes Ziel wie einen Operanden. **Ein Ziel in einem Tray
ist nie eine approvierbare Operation**, sondern schließt die Tür — Begründung im Code: eine
`filing_correction` bindet Bytes, die an einer Stelle EXISTIEREN, und die Bytes, die eine Umleitung
schreiben wird, gibt es nicht, wenn der Nutzer gefragt wird. Es gibt also keine ehrliche Frage.

### R1b — vier Prosastellen behaupteten die geschlossene Fassung

Kopfkommentar, `ENFORCEMENT.md` §1, Verfassung §2/5, `records-clerk.md`: alle vier nennen jetzt die
Umleitung, und alle vier tragen die ehrliche Grenze, die vorher fehlte — **die vier Bedingungen
entscheiden die TÜR, nie die WAND.** Ein `python -c "os.remove(…)"` oder ein blankes
`> inbox/x.pdf` allein auf einer eigenen Zeile verweigert hier nach wie vor niemand.

### R2 — der F5-Rundlauf war lexikalisch (Rest, geschlossen)

`--document ARCHIVE/…` läuft lexikalisch perfekt zurück und öffnet auf einem
groß-/kleinschreibungs-unempfindlichen Dateisystem dieselbe Datei — also wurde eine echte Freigabe
geprägt, die danach nichts traf: eine **verbrannte Nutzer-Antwort**, schlimmer als eine
Verweigerung. `hashing.on_disk_position` liest jetzt die Schreibweise zurück, die das Dateisystem
wirklich trägt, und eine abweichende wird **mit dem echten Namen** verweigert, damit der
Sachbearbeiter ihn aus der Meldung kopieren kann. Beide Richtungen gemessen.

### R3 — der Cap-Test leitete seine Probe aus dem Cap ab (Rest, geschlossen)

Damit blieb er grün, wenn jemand den Cap auf 60 hob — die Eigenschaft, für die es den Cap gibt
(Entscheidung innerhalb der Frist), war ungeschützt. Jetzt: `guard_fs_tripwire.budget_cap()` rechnet
die Decke aus der Frist (`_compat.HOOK_DEADLINE_SECONDS`) mal dem Anteil, den diese eine
Entscheidung ausgeben darf (`CORRECTION_BUDGET_SHARE = 0.1`), geteilt durch das Budget je Korrektur
(`CORRECTION_COST_SECONDS = 0.2`, bewusst eine Größenordnung über allem Gemessenen, damit es auf
einem langsamen Host hält — und in der langsamen Richtung falsch zu liegen macht die Decke nur
kleiner). Decke heute **30**, gewählter Cap **25** aus einem Produktgrund. `CORRECTION_CAP = 61`
wird rot.

### R4 — die 60 Sekunden lebten an zwei Orten (Rest, geschlossen)

Sie lebten an **sechs**: fünf Prosa-Stellen in `_compat.py` und eine im Guard. Jetzt gibt es
`_compat.HOOK_DEADLINE_SECONDS`, und die Kommentare, die darüber argumentieren, zeigen dorthin.
`_compat.py` ist gespiegelt — alle drei Kits neu kopiert, md5-gleich geprüft.

### R5 — die Reststelle „Speicher-Scan" ist host-abhängig

Beide Messungen gehören in den Bericht, keine davon in einen Kommentar:

| Host | je gespeicherter Freigabe | 60-s-Frist erreicht bei |
|---|---|---|
| Umsetzer (dieser) | ~3,8 ms | ~15 700 Freigaben |
| Prüfer | ~1,15 ms | ~52 000 Freigaben |

Beide Zahlen sagen dasselbe: die Grenze ist real und liegt weit jenseits dessen, was ein Projekt an
Nutzer-Klicks sammelt. Sie ist **nicht** geschlossen — eine Obergrenze dort träfe `push`, `preset`
und `kit_update` mit und ist eine Kernel-Entscheidung.

### Latenz nach dem R1-Fix, neu gemessen

| Fall | Wert |
|---|---|
| 8000 Dokumente an einem `rm`, keine Freigabe (272 002 B) | **0,75 s** (HEAD-Zustand vor F3: 114,35 s) |
| voller Cap (25 Operationen), 25 Freigaben im Speicher | **0,237 s** |
| voller Cap (25 Operationen), 204 Freigaben im Speicher | **0,823 s** |

### Rot-Nachweis Runde 2

Klon außerhalb des Repos (`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0077\clone`, Skript
`red3.py`):

| Wiederhergestellter Defekt | Ergebnis |
|---|---|
| R1 ein Umleitungsziel ist nicht Teil der Zeile | 5 failed |
| R1b nur die Tray-Hälfte der Umleitungsregel fällt weg | 4 failed |
| R2 der Rundlauf ist lexikalisch (Groß-/Kleinschreibung) | 1 failed |
| R3 der Cap darf über sein Budget hinaus gehoben werden | 1 failed |

Neue Tests: `tools/test_hooks.py::test_a_redirect_is_part_of_the_line_the_door_reads` (6 Fälle),
`…::test_a_redirect_into_a_tray_shuts_the_door_on_an_approved_delete_too`,
`…::test_the_cap_stays_inside_the_budget_it_exists_for`;
`tools/test_staging_cli.py::test_a_document_named_in_the_wrong_case_is_refused_by_its_real_name`.

**Scratch-Disziplin:** alle Arbeiten außerhalb des Repos liegen ab dieser Runde unter
`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0077\`.

## 5c. NACHARBEIT nach Prüfer-Runde 3 (V1–V6)

Runde 3 hat R1-Kern, R2, R3 und die gebaute Hälfte von R4 **bestätigt** (erweiterte Batterie: `2>`,
`>|`, fd-Formen, gespleißte Ziele, PowerShell-Reiter — alle rc 2; Cap-Grenze, Latenz-Kopfzahlen,
Nicht-Regressions-Stichprobe grün). Drei blockierende Befunde, **eine Wurzel**.

### Die Wurzel: `_filing._tokens` beendete die Argumentliste an der ersten Umleitung

`re.split(r"[<>]", invocation)[0]` warf **jedes Wort nach dem Operator** weg. Eine Shell tut das
nicht: `> log.txt mv a b` führt `mv a b` aus, mit umgeleiteter Ausgabe. Eine **führende** Umleitung
versteckte damit das ganze Kommando vor jedem Leser dieses Moduls — die Wand sah kein Löschen mehr,
der Aktenplan-Check keine Ablage. Gebaut: `_filing.REDIRECT_SPAN_RX` schneidet die Umleitung samt
ihrem Ziel **heraus**, statt die Liste dort zu beenden. Gemessen mit `tokens_probe.py`:

| Invocation | vorher | nachher |
|---|---|---|
| `> log.txt mv a b` | `[]` | `['mv', 'a', 'b']` |
| `mv a b > log.txt` | `['mv','a','b']` | `['mv','a','b']` |
| `> "my log.txt" rm a` | `[]` | `['rm', 'a']` |
| `rm x 2>&1` | `['rm','x']` | `['rm','x','&1']` (das `&1` ist ein Wort ohne Ort — benannt im Docstring) |

### V1 — eine führende Umleitung schaltete die Lösch-Regel ab (blockierend, die WAND)

Ohne jede Freigabe, echte Hook-Prozesse:

| Kommandozeile | vorher | nachher |
|---|---|---|
| `> outbox/log.txt rm archive/…/y.pdf` | **0** | **2** |
| `>outbox/log.txt rm archive/…/y.pdf` (ohne Leerzeichen) | **0** | **2** |
| `< outbox/log.txt rm archive/…/y.pdf` | **0** | **2** |
| `> outbox/log.txt del archive/…/y.pdf` | **0** | **2** |
| `> /tmp/x rm archive/…/y.pdf` | **0** | **2** |
| `> outbox/log.txt mv archive/…/y.pdf /tmp/gone.pdf` | **0** | **2** |

### V2 — dieselbe Wurzel auf der Tür-Seite (blockierend)

| Kette (mit lebender Freigabe für den Move) | vorher | nachher |
|---|---|---|
| `mv <freigegeben> outbox/x.pdf &> inbox/b.pdf` | **0** | **2** |
| `> inbox/b.pdf mv <freigegeben> outbox/x.pdf` | **0** | **2** |
| `mv <freigegeben> outbox/x.pdf && > inbox/b.pdf` | **0** | **2** |
| `> outbox/log.txt mv <freigegeben> outbox/x.pdf` (Gegengewicht) | 0 | **0** |
| `mv <freigegeben> outbox/x.pdf && > outbox/log.txt` (Gegengewicht) | 0 | **0** |

Dazu (a): der Umleitungs-Scan läuft jetzt **vor** dem Token-Check, also auch für eine Invocation,
die aus nichts als einer Umleitung besteht.

### V4 — die Journalzeile ohne Freigabe (Rest, geschlossen)

Ohne gedeckte Korrektur stand dort „allowed under user approval : " — eine leere Id-Liste, also die
Behauptung eines Durchgangs unter einer Freigabe, die es nicht gibt. Zwei Schlösser: die leere
Antwort der Tür ist „zu" statt „offen" (`[] is not None` war der Durchfall), und
`record_corrections` schreibt für eine leere Liste nichts.

### Zwei eigene Fehlgriffe in dieser Runde, gemessen statt geglaubt

Mein erster Rot-Lauf hatte **vier von fünf Mutationen grün**. Das heißt: die Guard-seitigen
Änderungen waren durch den `_tokens`-Fix gar nicht mehr gemessen.

* **(b) „eine tokenlose Invocation mit Text ist unplaced" habe ich wieder ENTFERNT.** Nach dem
  echten Fix ist eine tokenlose Invocation genau eines: Umleitungen und Leerraum — und die hat der
  Scan davor bereits beurteilt. Die Regel war damit reine Über-Verweigerung ohne Schutz dahinter:
  `mv <freigegeben> outbox/ && > outbox/log.txt` wurde rc 2, obwohl die Umleitung vollständig
  platziert ist. Gemessen mit `reachable.py`, nicht überlegt.
* **Zwei Tests bestanden aus dem falschen Grund.** Der V1c-Test lief gegen ein Projekt ohne
  Zustandsverzeichnis, also verweigerte die Tür wegen der fehlenden Freigabe-Auskunft statt wegen
  der leeren Operationsliste; der V4-Test rief `record_corrections` ohne `CLAUDE_PROJECT_DIR`, also
  landete die Notiz woanders. Beide korrigiert, beide danach rot ohne den Fix.

### V3 — die vier Prosastellen, jede Behauptung DIESE RUNDE gemessen

`prose.py` fährt jede Aussage der vier Texte als echten Hook-Prozess. **25 von 25 halten**:

| Behauptung | rc | erwartet |
|---|---|---|
| die freigegebene Korrektur auf eigener Zeile läuft | 0 | 0 |
| ein `cd` davor ist in Ordnung | 0 | 0 |
| eine Invocation, die er nicht liest: `python -c` | 2 | 2 |
| …`tar --remove-files` | 2 | 2 |
| …`echo` | 2 | 2 |
| …`tee` hinter einer Pipe | 2 | 2 |
| ein Operand, den die Shell umschreibt: `$VAR` | 2 | 2 |
| …ein Glob | 2 | 2 |
| …`~/…` | 2 | 2 |
| ein Operand, der keinen Ort im Projekt nennt | 2 | 2 |
| ein `cd`, dem er nicht folgen kann | 2 | 2 |
| ein Umleitungsziel, das die Shell umschreibt | 2 | 2 |
| eine Umleitung IN einen Tray von Rang | 2 | 2 |
| …vorangestellt geschrieben | 2 | 2 |
| …als `&>` | 2 | 2 |
| ein Umleitungsziel ohne Ort im Projekt | 2 | 2 |
| ein zweites, unfreigegebenes Dokument | 2 | 2 |
| ein Ziel außerhalb des Projekts | 2 | 2 |
| ein Löschen, das nur die Rohtext-Lesart sieht | 2 | 2 |
| ein anderes Dokument unter derselben Freigabe | 2 | 2 |
| ein anderes Ziel | 2 | 2 |
| eine Löschung, wo ein Move freigegeben war | 2 | 2 |
| eine Umleitung außerhalb der Trays, aber im Projekt, ist gewöhnliche Arbeit | 0 | 0 |
| **Grenze:** eine blanke Tray-Umleitung allein verweigert hier niemand | 0 | 0 |
| **Grenze:** ein `python -c`-Löschen allein verweigert hier niemand | 0 | 0 |

Die beiden letzten Zeilen sind die ehrliche Hälfte, die stehen bleibt: **Tür, nicht Wand.**

### V5 / V6 (Reste)

* **V5**: Runde 2 behauptete, die Kommentare zeigten nun alle auf `_compat.HOOK_DEADLINE_SECONDS`.
  Falsch — die wörtlichen „60 s" stehen weiter in fünf Kommentaren von `_compat.py` und vier von
  `gate_ledger_valid.py`, und `gate_ledger_valid.TOTAL_BUDGET = 40` leitet sich aus nichts ab. Der
  Kommentar sagt jetzt genau das: **eine** Ableitung liest die Konstante (der Korrektur-Cap), der
  Rest ist ein eigener Durchgang. `TOTAL_BUDGET` habe ich **nicht** angefasst — fremdes Gate.
* **V6**: der Gegengewicht-Satz nannte nur „außerhalb der Trays". Gemessen enger: gewöhnliche Arbeit
  ist eine Umleitung, deren Ziel **im Projekt und außerhalb der Trays** liegt; ein Ziel außerhalb
  des Projekts (oder `$LOG`) schließt die Tür wie jedes andere unplatzierbare Wort. Satz und Test
  sagen das jetzt.
* **Ungemessene Schreibweisen derselben Klasse**, vom Prüfer benannt und hier als Rest geführt:
  Here-Doc/`<<<`, `exec >`, Prozess-Substitution, `xargs`. Nicht gemessen, nicht behauptet.

### Latenz nach der Runde neu gemessen

| Fall | Wert |
|---|---|
| 8000-Operanden-`rm`, keine Freigabe (272 002 B) | **0,81 s** |
| 25 Operanden (= Cap), keine Freigabe | **0,19 s** |
| 26 Operanden (über dem Cap) | **0,09 s** |
| voller Cap, 25 Freigaben im Speicher | **0,24 s** |
| voller Cap, 204 Freigaben im Speicher | **0,80 s** |
| voller Cap, 8 MiB je Dokument | **0,40 s** |

### Rot-Nachweis Runde 3

Klon außerhalb des Repos, Skript `red4.py`:

| Wiederhergestellter Defekt | Ergebnis |
|---|---|
| V1a der Umleitungs-Scan läuft nach dem Token-Check | 2 failed |
| V1c die Tür beantwortet eine leere Zeile als geöffnet | 1 failed |
| V2 `_tokens` beendet die Argumentliste an der ersten Umleitung | 2 failed |
| V4 `record_corrections` schreibt eine Zeile für eine leere Liste | 1 failed |

Neue Tests: `tools/test_hooks.py::test_a_leading_redirect_does_not_hide_the_command_behind_it`
(6 Fälle), `…::test_the_door_answers_an_empty_line_as_closed_not_as_open`,
`…::test_a_journal_line_never_claims_a_passage_under_no_approval_at_all`, plus vier neue Fälle in
`…::test_a_redirect_is_part_of_the_line_the_door_reads`.

## 6. Schritt 4 — Auslieferung

* `python tools/bump_kit_version.py`, nach jedem Nach-Fix gefahren: Ausgang `2026.08.18-3` für
  alle drei, ausgeliefert **office-team `2026.08.21-3`**, dev/research `2026.08.21-2`. Bis Runde 2 lag office vorn
  (`2026.08.20-1` gegen `2026.08.18-6`), weil der Stempler stempelt, was sich geändert hat und der
  Office-Guard nur in ein Kit geht; R4 hat dann `_compat.py` angefasst, das in allen dreien liegt.
* Spiegelung, nachgeprüft statt behauptet: die drei geänderten Hook-Dateien
  (`guard_fs_tripwire.py`, `_filing.py`, `gate_filing.py`) existieren **nur** im Office-Kit
  (gemessen über alle drei `hooks/`-Verzeichnisse); die vier geteilten Helfer `_audit.py`,
  `_compat.py`, `_kernel.py`, `_gate.py` sind über die drei Kits **byte-identisch** (md5 verglichen)
  und wurden nicht angefasst. `ENFORCEMENT.md` und die Verfassungen sind per `KIT_SPECIFIC_HOOKS`
  bzw. per Bauart kit-eigen; `team-kits/kernel/` existiert einmal; `records-clerk.md` ist eine
  Office-Rolle. Es gibt also nichts zu spiegeln und keinen neuen Eintrag in `KIT_SPECIFIC_HOOKS`.
* `tools/pin_constitution_sections.py --write --note …`, zweimal (Erst-Bau und Nacharbeit) → beide
  Male dieselben zwei Sektionen (`office-team constitution/AGENTS.md §2`, `office-team
  hooks/ENFORCEMENT.md §1`), Journalzeilen in `docs/reviews/phase0-disposition.md`.
* `tools/record_lead_package_sizes.py --write --note …` → office-team 36 024 B → 36 524 B (+500,
  Erst-Bau) → **36 855 B** (+331, Nacharbeit: die Kante, die der Prüfer als fehlend gemessen hat).
  dev/research unverändert.
* `python -m ruff check .` → all checks passed.
* `python tools/validate.py` → all structural checks passed.
* `python -m pytest tools/ -q` und `python -B -m pytest .claude/hooks/test_gates.py -q` → §8.

Laufzeit des Guards insgesamt, 5 Aufrufe je Fall gegen ein installiertes Projekt: ein Aufruf, der
keine geschützte Position nennt, kostet **144 ms**; einer, der eine nennt und darum die Bridge
lädt, **249 ms** (+105 ms, einmal pro Entscheidung, nie auf dem Normalpfad). SHA-256 über eine
Datei auf diesem Host, warm, 1-MiB-Blöcke: 16 MiB 0,021 s, 64 MiB 0,050 s, 256 MiB 0,217 s —
daraus die Schranke in `hashing.py:707`. Die Zahlen der TÜR stehen in §5a unter F3.

## 7. Was ich BEWUSST nicht geschlossen, aber benannt habe

1. **Der Auftrag war in einer Tatsache falsch**, und ich habe nicht darum herumgebaut: der
   Tripwire ist NICHT in allen drei Kits gespiegelt, er existiert nur im Office-Kit (gemessen:
   `dev-team/hooks/` und `research-team/hooks/` enthalten weder `guard_fs_tripwire.py` noch
   `gate_filing.py` noch `_filing.py`). Die abgeleitete Platzierung ist Kernel + Office-Guard.
2. **„Einmalig" heißt: einmal ERFOLGREICH.** Läuft das freigegebene Kommando nicht (es scheitert
   aus einem anderen Grund, oder es wird gar nicht abgeschickt), liegt das Dokument noch da und
   die Freigabe deckt es weiter — bis sie abläuft (1 h, `LINE_APPROVAL_VALIDITY`). Das ist im
   Fragetext, im Docstring und im Test so gesagt und nicht als harter Ein-Schuss ausgegeben. Ein
   echter Verbrauchszähler hätte ein „benutzt"-Flag in beschreibbaren Zustand gelegt — genau die
   Bauform, die das Ledger-Gate vier Runden gekostet hat.
3. **Der dauerhafte Nachweis ist die geprägte Anfrage**, nicht die Journalzeile.
   `approvals/consumed/<id>.yaml` trägt Dokument, Fassung, Ziel, Grund und Prägecode und bleibt
   liegen. `project_memory/.audit/hook_events.jsonl` ist lokale Diagnose (so sagt es `_audit`
   selbst) und wird rotiert; sie sagt „durchgelassen", nie „ausgeführt" — ein PreToolUse-Hook
   läuft vor dem Kommando und kann das Gegenteil nicht wissen.
4. **KORRIGIERT NACH F1/F2 — der alte Punkt 4 war zu eng.** Er sagte, nicht approvierbar bleibe,
   was der Guard nicht benennen kann, und meinte damit nur zwei Fälle. Die gebaute Regel ist
   breiter und steht jetzt so da: **die Tür öffnet nur für eine Zeile, auf der der Guard ALLES
   platzieren konnte.** Eine Invocation, die er nicht liest (`python -c`, `tar --remove-files`,
   ein `echo`), ein Operand, dessen Text nicht der Pfad ist (`$VAR`, Glob, `~/…`), ein Operand,
   der keinen Ort im Projekt nennt (`../…`, `/etc/passwd`), ein `cd`, dem er nicht folgen kann,
   eine Lesart-Uneinigkeit beim Löschen, ein Ziel außerhalb des Projekts, mehr Korrekturen als
   `CORRECTION_CAP` — jedes davon lässt die Tür zu, und zwar für die ganze Zeile. Das ist an
   mehreren Stellen Über-Verweigerung (ein `echo` neben einer freigegebenen Korrektur reicht) und
   genau so gewollt: eine Freigabe, die „was diese Zeile tut" deckt, wäre die stehende Erlaubnis,
   gegen die die Wand gebaut ist.
5. **Alle Residuen des Guards von 2026-08-03 bleiben, wie sie sind**, und die Tür macht sie
   **nicht größer**: ein Löschen INNERHALB eines anderen Programms (`python -c "os.remove(...)"`),
   ein Operand, den die Shell vor Gebrauch umschreibt, `tar --remove-files`, `robocopy … /MIR` ins
   Archiv. Der Guard SIEHT sie weiterhin nicht — allein auf einer Zeile laufen sie unverweigert
   durch, wie vor dieser Runde. Was sich geändert hat: sie können nicht mehr an einer freigegebenen
   Korrektur mitfahren (das war F1, gemessen rc 0). Sie stehen unverändert im Kopfkommentar des
   Guards und in `docs/POST_V2_WISHLIST.md` (nicht in meinem Bereich).
6. **KORRIGIERT NACH F2 — der alte Punkt 6 war gemessen falsch.** Er nannte den Rohtext-Fall
   „theoretisch" und behauptete, ich hätte keine Kommandozeile konstruieren können. Der Prüfer hat
   eine konstruiert: `rm inbox/a.pdf ~/archive/secret.pdf` unter der Inbox-Freigabe, rc 0, volle
   Kette rc 0 — die Shell expandiert `~` und löscht in `$HOME`. Ein „ich habe es nicht geschafft"
   ist keine Grenze, sondern eine unbewiesene Behauptung, und sie stand hier in der beruhigenden
   Richtung. Geschlossen durch die beiden Platzierbarkeits-Bedeutungen und den Vergleich der beiden
   Lösch-Lesarten je Invocation (§5a/F2). Was jetzt an dieser Stelle offen bleibt und ich NICHT
   behaupte, geschlossen zu haben: eine Invocation, die der Guard gar nicht als Lösch- oder
   Move-Verb liest und die dennoch löscht, sieht er weiter nicht — sie schließt nur die Tür, statt
   durch sie zu gehen (Punkt 5).
7. **`README.md` Zeile ~440 sagt weiter „the line kind is about publishing a commit"**, einzahlig,
   obwohl es inzwischen vier Line-Arten gibt. Der Satz war schon vor dieser Runde veraltet
   (`preset`, `kit_update`). `README.md` liegt **außerhalb meines erlaubten Bereichs** — ich habe
   ihn nicht angefasst und melde ihn hier. Die gleichlautende Stelle IM Bereich
   (`team-kits/kernel/migrate.py`) habe ich zur Ableitung umgeschrieben.
8. **Die Frage ist lang.** Ob `AskUserQuestion` eine Options-`description` dieser Länge
   ungekürzt anzeigt, habe ich nicht gemessen — dafür bräuchte es eine echte Sitzung. Die
   `preset`- und `kit_update`-Fragen liegen in derselben Größenordnung, also ist das keine neue
   Klasse; gemessen ist es trotzdem nicht. `REASON_SHOWN = 200` begrenzt seit F4 wenigstens den
   Teil, den ein Agent frei füllt.
9. **Der Freigabe-Speicher wird ganz gelesen, nicht nur seine lebenden Einträge** (Zahlen beider
   Hosts in §5b/R5 — sie unterscheiden sich um Faktor drei und sagen dasselbe).
   `_in_force_approvals` läuft über JEDE `APR-*.yaml`, auch über widerrufene und abgelaufene, und
   löst jede auf ihre geprägte Anfrage zurück. Gemessen auf diesem Host: ~3,8 ms je gespeicherter
   Freigabe plus ~0,25 s Grundkosten (25 → 0,29 s, 204 → 0,74 s, 600 → 2,53 s). Die 60-s-Frist
   wäre damit bei rund **15 700 gespeicherten Freigaben** erreicht. Jede davon kostet einen Klick
   des Nutzers, und `filing_correction` läuft nach einer Stunde ab — die Zahl der LEBENDEN ist also
   praktisch klein, die Zahl der DATEIEN wächst aber über die Projektlaufzeit. Ich habe das nicht
   begrenzt: eine Obergrenze dort träfe `push`, `preset` und `kit_update` mit und ist eine
   Kernel-Entscheidung, keine Anpassung dieser Tür. Hier steht sie mit ihrer Messung statt als
   „später".
10. **Die Obergrenze `CORRECTION_CAP = 25` ist eine Über-Verweigerung mit Ansage.** Wer 40
    Dokumente auf einmal korrigieren lassen will, bekommt rc 2 und muss in Stapeln fragen. Das ist
    der Preis dafür, dass die Entscheidung die Frist des Providers nicht überlebt; die Zahl steht
    an genau einer Stelle (`guard_fs_tripwire.py:183`) mit ihrer Begründung, und die Decke, unter
    der sie liegen muss, wird gerechnet statt behauptet (§5b/R3).
11. **Eine Umleitung in einen Tray ALLEIN auf ihrer Zeile verweigert hier niemand** (`echo x >
    inbox/y.pdf`). Die beiden Regeln dieses Guards greifen an einem Lösch-VERB und an einem Move
    AUS dem Archiv; eine Umleitung ist keines von beidem. `gate_filing` fängt die `archive/`-Hälfte
    (es liest Umleitungsziele unter den Pfaden, die ein Kommando ERZEUGT), die `inbox/`-Hälfte
    fängt nichts. Benannt statt geschlossen, weil das Schließen eine neue WAND-Regel für jedes
    Office-Projekt wäre und keine Eigenschaft dieser Tür — die Tür verweigert eine solche Umleitung
    nur, wenn sie auf einer Zeile mitfährt, die eine Korrektur erbittet (R1).

## 8. Suite-Zahlen

Je EIN vollständiger Lauf auf dem Baum, der ausgeliefert wird — also nach beiden Nacharbeiten
(§5a F1–F9 samt N10, §5b R1–R5, §5c V1–V6), nach dem Stempel (office `2026.08.21-3`,
dev/research `2026.08.21-2`), nach dem Pin- und dem Größen-Eintrag:

* `python -B -m pytest tools/ -q` → **2897 passed, 13 skipped in 1643,13 s (0:27:23)**, Exit 0
* `python -B -m pytest .claude/hooks/test_gates.py -q` → **243 passed in 594,34 s (0:09:54)**, Exit 0
  (läuft nicht in `tools/` mit; hier gefahren, weil Kit-Hooks geändert wurden)
* `python -m ruff check .` → all checks passed
* `python tools/validate.py` → all structural checks passed

Frühere vollständige Läufe, als Historie und nicht als Abnahme, weil der Baum sich danach bewegt
hat: Erst-Bau `2852 passed / 13 skipped` und `243 passed`; erster Nacharbeits-Lauf **`1 failed,
2870 passed`** — der Fehlschlag, der N10 gefunden hat, oben dokumentiert; letzter Lauf vor Runde 2
`2874 passed / 13 skipped` und `243 passed`; Runde 2 `2883 passed / 13 skipped` und
`243 passed`, davor **`1 failed, 2882 passed`** —
`test_instruction_files_name_only_state_files_a_v2_project_has`, weil mein neuer Satz in
`ENFORCEMENT.md` eine Beispieldatei (`inbox/x.pdf`) in Backticks nannte und der Test das als
behaupteten Zustandspfad liest. Korrigiert, indem der Satz den Tray nennt statt eine erfundene
Datei — ein Prosa-Fehler, kein Verhalten. Die `test_gates.py`-Laufzeit schwankt stark mit der
Auslastung der Maschine (3207 s gegen 378 s bei identischer Testzahl); die Zahl, die zählt, ist
243 passed / Exit 0.

Zwischenläufe während des Baus sind hier absichtlich nicht aufgeführt — eine Zahl aus einem Baum,
der sich danach noch bewegt hat, ist keine Abnahme. **Ein Zwischenlauf gehört trotzdem in den
Bericht**, weil er sonst als verschwiegener Fehlschlag dastünde: der vorletzte `tools/`-Lauf
meldete `1 failed, 2851 passed` in
`tools/test_hooks_v2.py::test_the_id_scan_is_linear_on_the_worst_legal_input` —

> the scan at 51200 B costs 0.193 s and its two series were only stable to 0.090 s, so this
> difference is the host and no ratio over it means anything

Das ist der Zweig, den dieser Test für genau diesen Fall selbst vorsieht: die Maschine war zu
unruhig, um die Messung zu tragen, also scheitert er mit dieser Lesart, statt auf Rauschen zu
behaupten. Er misst `guard_memory_budget`s Id-Scan, den diese Runde nicht berührt, und im
Abschlusslauf auf ruhiger Maschine ist er grün. Beide Male dieselbe Maschine, dasselbe Kommando.

Der einzige Schreibvorgang nach diesen beiden Läufen ist dieser Abschnitt selbst: `docs/` geht in
keinen Kit-Hash ein (`tools/bump_kit_version.py` misst `team-kits/<kit>`), also verlangt er keinen
neuen Stempel — nachgeprüft mit einem erneuten `bump_kit_version.py`, das „unchanged" meldet.
