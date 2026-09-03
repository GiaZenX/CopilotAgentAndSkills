# TSK-0114 — Merge-Runde der Generation 2 (DEC-0057, DEC-0060, DEC-0061)

Umsetzer: `harness-implementer` (Opus). Arbeitsbaum: `C:\Offline Repos\AgentAndSkills`, Branch
`feat/harness-v2`, Basis `c4f3cc0`. Rundenverzeichnis außerhalb des Repos:
`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0114\`. Wall-Clock 2026-09-02 19:35 – 23:5x,
**rund 4 h 15**, davon ~1 h 50 reine Testlaufzeit.

Kein Commit, kein Push, keine Installation.

---

## 0. Ausgangsmessung

```
git branch --show-current -> feat/harness-v2
git rev-parse HEAD        -> c4f3cc0f41375636b27b10972ca348d039d4b89f
git status                -> team-kits/, tools/, docs/ sauber;
                             project_memory/ trägt die uncommitteten Kernel-Schreibungen
```

Alle sieben Patches einzeln `git apply --check` gegen diesen Baum: **7 × OK**.
`project_memory/.audit/hook_events.jsonl` liegt in **keinem** der sieben Patches (über
`git apply --numstat` je Patch geprüft); die Datei im Arbeitsbaum ist von den Haken dieser Sitzung
geschrieben und wurde nicht angefasst.

---

## 1. Reihenfolge, Anwendung, Pin-Tests

Die Pin-Menge ist `tools/test_repo_hygiene.py`, `tools/test_shortening_net.py`,
`tools/test_ci_lint_pinned.py` und `tools/test_context_budget.py -k "pin or size"`;
`tools/test_model_pins.py` ist eine **neue Datei aus Strom H** und existiert erst ab Schritt 6.

| # | Strom | Patch | angewandt | ausgeschlossen | Pin-Ergebnis |
|---|---|---|---|---|---|
| 1 | F Kernel | `TSK-0106/stream-kernel.patch` | 24 von 27 Dateien | 3 × `VERSION` | 51 + 3 passed |
| 2 | G Office | `TSK-0113/stream-office.patch` | 20 von 24 | 3 × `VERSION`, Wunschliste | 53 + 3 passed |
| 3 | I Dashboard | `TSK-0109/stream-dashboard.patch` | 27 von 29 | `VERSION`, Wunschliste | 53 + 3 passed |
| 4 | K Humanizer | `TSK-0111/stream-humanizer.patch` | 7 von 11 | 3 × `VERSION`, Wunschliste, `tools/test_hooks.py` (Hand) | 53 + 3 passed |
| 5 | E Texte | `TSK-0105/stream-texts.patch` | 23 von 27 | 3 × `VERSION`, Wunschliste | 53 + 3 passed |
| 6 | H Messungen | `TSK-0108/stream-measure.patch` | 5 von 6 | Wunschliste | 60 + 3 passed |
| 7 | J Hygiene | `TSK-0110/stream-hygiene.patch` | 3 von 4 + 3 von 4 Hunks | Kopf-Hunk von `test_repo_hygiene.py` (Hand) | 72 + 3 passed |

Nach jedem Schritt lief zusätzlich `git apply --check` des NÄCHSTEN Patches; die beiden einzigen
Fehlschläge (K an `tools/test_hooks.py:2821`, J an `tools/test_repo_hygiene.py:2`) sind genau die
vorhergesagten Nähte und stehen unten.

**Alle Stempel-Hunks verworfen** — kein Zwischenstempel im Baum, ein Stempel am Ende (Abschnitt 7).

**Bereichsabweichung, benannt:** H's Patch enthält `project_memory/staging/TSK-0108/stream-protocol.md`.
Der `forbidden_scope` von TSK-0114 nennt `project_memory/**` mit der Ausnahme
`staging/TSK-0114/`; dieselbe Datei steht aber in den `required_inputs` desselben Items. Ich habe
sie angewandt (Staging ist kein kanonischer Zustand, `gate_write_scope` lässt sie durch, und ohne
sie zeigt eine Eingabezeile des Items ins Leere) und nenne den Widerspruch hier statt ihn zu lösen.

---

## 2. Nahttabelle — jede Auflösung mit beiden Seiten

| Ort | Seite A | Seite B | Auflösung |
|---|---|---|---|
| `team-kits/*/VERSION` | jeder Strom stempelte provisorisch | dito | alle Hunks verworfen, ein Stempel am Ende |
| `docs/POST_V2_WISHLIST.md` Tabelle `:2352` | F fügt H108–H110 **vor** der H99-Zeile ein | E/G/H/I/K fügen je nach der H99-Zeile ein | F's Zeilen versetzt; **alle 17 neuen Zeilen in Nummernordnung H105…H121 nach H99** |
| `docs/POST_V2_WISHLIST.md` Abschnitte am Ende | F's H108–H110 stehen vor dem H99-Abschnitt | E/G/H/I/K hängen an | F's Block versetzt; Abschnittsfolge H99, H105 … H121 aufsteigend |
| `tools/test_hooks.py` Docstring von `test_shared_kit_files_identical` (`@@ -2821`) | I ersetzt die zwei `_assert_mirrored`-Zeilen durch die `_shipped_code_dirs()`-Schleife und schreibt einen Absatz über die ABLEITUNG der Verzeichnisse | K hängt einen Absatz an, warum die Regel keine PRÄSENZ-Hälfte hat | I's Vierpunkt-Vorschlag angewandt: **beide Absätze überleben**, K's zuerst (er begründet den Ausnahmefall), I's zuletzt (er erklärt den Code direkt darunter); I's Schleife bleibt. Punkt 3 des Vorschlags (K's Ergänzungen an `KIT_SPECIFIC_SCRIPTS`) ist gegenstandslos — K's Patch fasst diese Konstante nicht an, geprüft über die Datei-Aufteilung des Patches |
| `tools/test_hooks.py` derselbe Docstring, I's Satz | I: „every one under `templates/repo/` that any kit ships **Python** into" | `_shipped_code_dirs` sammelt `.py` **oder** `.html` (sagt es im eigenen Docstring) | Satz zeigt jetzt auf `_shipped_code_dirs` statt die Auswahl zu wiederholen — die Zahl/Regel steht an einer Stelle |
| `tools/test_repo_hygiene.py` Modul-Docstring | G ergänzt „…and a statement that answers for a claim by naming a test must name one that exists" | J ergänzt „One member of this file REPORTS instead of judging…" | beide Sätze, in dieser Reihenfolge; J's übrige drei Hunks per `git apply` mit Offset |
| `docs/reviews/phase0-disposition.md` | G (+2/−2 Emissionszählung) | E (+16/−1) | keine Kollision im Text — E nach G sauber angewandt |
| `tools/test_role_contracts.py` | F (+36) | E (+249) | keine Kollision — disjunkte Bereiche |

---

## 3. Naht-SÄTZE, die kein Patch trug

### F: S1 — die Kommandoliste

Schiedsrichter: `test_hooks.test_every_span_that_presents_the_command_surface_names_all_of_it`.
Vor der Naht rot mit vier Fundstellen, jede „names 29, misses `freeze-report`,
`revise-document`, `verify-invariants`". Eingetragen an der Stelle, die der Reihenfolge des
Kernel-Parsers entspricht (`verify-invariants` nach `generate-index`, `revise-document` nach
`apply-proposal`, `freeze-report` nach `freeze-design`), in `team-kits/{dev,office,research}-team/
constitution/AGENTS.md` und in `README.md`. Danach grün.

Im README stand außerdem, Kit-Dokumente hätten seit TSK-0092 **eine** Route, die „any removal,
change or lost comment" verweigert — ohne die neue. Ein Satz ergänzt, der `revise-document` nennt.

### F: S11-a/b/c — die ROUTEN-Sätze

* **S11-a**, alle drei Verfassungen: `revise-document` in den Satz über `apply-proposal` eingefügt.
  Dabei wurde **„both on a user-minted approval" → „all three"** (dev, research) und **„Neither
  replaces the onboarding" → „None of them"** (office) nachgezogen — zwei Sätze, die die Naht
  selbst falsch gemacht hätte.
* **S11-b**, research `:60`: **F's Wortlaut ist gegen den laufenden Code korrigiert worden.** Der
  Vorschlag sagte, `revise-document` verweigere „a list that gains and loses entries in one step".
  Gemessen mit `kernel.documents.revision_plan` an vier Proben:

  | Vorschlag | Ergebnis |
  |---|---|
  | einen Eintrag ersetzen | ANGENOMMEN |
  | einen Eintrag löschen | ANGENOMMEN |
  | nur hinzufügen | VERWEIGERT (gehört zu `apply-proposal`) |
  | löschen UND hinzufügen in einem Schritt | **ANGENOMMEN** |

  Der geschriebene Satz sagt jetzt, was gilt: eine Revision, die nur HINZUFÜGT, wird verweigert,
  und außerhalb der gezeigten Stellen darf keine Zeile verlorengehen.
* **S11-c**, office `:293`: wörtlich wie vorgeschlagen (die Fassung war korrekt).

### G: E1–E7

| Naht | Ort | Was geschrieben wurde |
|---|---|---|
| E1 | `office-team/agents/shop-curator.md` | Plattformname aus der Routing-`description` entfernt; **beide Enden des Stolperdrahts**: `KNOWN_BINDINGS` in `tools/test_kit_neutrality.py` ist damit leer, und der Docstring, der „recorded rather than edited here" behauptete, sagt jetzt, dass die Naht geschrieben wurde |
| E2 | `office-team/skills/records-clerk/SKILL.md` | Quarantäne-Punkt zeigt auf `archive/_quarantine/<year>/` (Regel `FP-901`) und auf den Kopf des Wächters statt eine absolute Wand zu behaupten. In ENGLISCH gerendert — die Datei ist englisch, der Vorschlag im Protokoll deutsch |
| E3 | drei Verfassungen + drei `project-auditor.md` | Der Takt zeigt auf `hooks/_routine.audit_period_id` statt ihn ein zweites Mal zu nennen; dazu der Satz, dass `routine`/`analysis` heute keinen Erzeuger haben (`H111`). Gemessen: `request-approval` bietet `acceptance, delivery, document_proposal, document_revision, filing_correction, filing_rule, kit_update, preset, push, scope` — keine der beiden. Deshalb steht dort **keine Zahl** (G's Protokoll sagt „neun", es sind seit F zehn) |
| E4 | `office-team/skills/office-manager/SKILL.md` | Was der Sitzungsstart als DUE/OVERDUE meldet, gehört in den ersten Absatz an den Nutzer; `DEADLINE REGISTER INCOMPLETE` benannt. Alle drei Zeichenketten gegen `_duties.py` geprüft |
| E5 | dieselbe Datei, Onboarding-Punkt | `tax.filings` und `receivables.payment_terms_days` ergänzt; beide Felder in der Vorlage nachgeschlagen (`:70`, `:82`) |
| E6 | drei `session_status.py` | „deleted a real backlog" → „would delete a backlog nobody read" (BUG-0068 hält keine Löschung fest); 3 × 1 Treffer |
| E7 | `office-team/constitution/AGENTS.md:141` | Absolutsatz über die Archivwand → Zeiger auf „WHAT THIS DOES NOT SEE" im Kopf des Wächters |

### I: die Rollensätze (6.5) und die `.gitignore` (6.3)

* **bookkeeper, office-manager, office-developer** haben jetzt je einen Satz zur Finanzseite.
  **I's Vorschlag für den office-manager ist korrigiert:** er sagte, ein älterer Datenstand im Kopf
  der Seite zeige, dass sie alt ist. I's eigene spätere Messung (H117, `ABOUT.txt`) widerlegt das —
  ein Nachtrag lässt den Kopf byte-identisch. Beide Sätze sagen jetzt: die Regel ist der Lauf, nicht
  das Lesen, und zeigen auf `dashboards/ABOUT.txt`.
* **6.3 `.gitignore`** (in keinem Strom-Scope): `dashboards/*` + `!dashboards/ABOUT.txt`
  eingetragen, mit einem **neuen Test** (Abschnitt 5).
* **6.1/6.2 NICHT geschrieben** — siehe Abschnitt 8.

### Der Rollen-Routen-Satz in neun Rollentexten

F's Registrierung von `REVISION_WRITES` macht
`test_role_contracts.test_every_role_that_owns_a_kit_document_carries_the_route_that_writes_it`
**rot mit 14 Befunden** über neun Rollen in drei Kits (der Strom F hat diese Suite nach seiner
Nacharbeit nicht mehr gefahren, E hat sie gefahren, aber vor F). Die EINE Form, die
`test_the_document_route_is_one_text_wherever_it_stands` byte-gleich verlangt, ist in allen neun
gleich fortgeschrieben; der Satz über das, was `apply-proposal` verweigert, nennt jetzt
`revise-document` und dessen eigene Verweigerung. Danach 30 passed.

---

## 4. Der Namensprüfer der Löcherliste (Output 3)

Eine Änderung in `.claude/hooks/test_gates.py`, beide gemessenen Grenzen zusammen:

1. **`_prose_of`** schneidet Code-Zäune aus dem Rumpf eines Eintrags, bevor irgendetwas gepaart
   wird. Definition: eine Zeile, deren gestripptes Vorderende drei Backticks sind, öffnet oder
   schließt einen Block; Blockinhalt ist keine Spanne. Ein Eintrag mit unbalanciertem Zaun ist ein
   eigener Fehlschlag.
2. **`_tests_by_module`** löst einen zitierten Namen gegen `test_gates.py` **und** jede
   `tools/test_*.py` auf; **`_cited_test`** liest die vier Schreibweisen (nackt; Modulname mit
   Punkt; Dateipfad mit `::`; Auslassungspunkte statt des Moduls) als eine Frage. Auflösung:
   erst EXAKT, nur wenn nichts exakt antwortet als Teilzeichenkette — über den ganzen Korpus wäre
   ein Name, der der Anfang eines längeren ist, sonst mehrdeutig.
3. **H46** trägt sein Präfix (`test_hooks_v2.`).

**Wirkung, gemessen:** der Prüfer liest **127 statt 43** Zitate; 19 der 116 Einträge tragen einen
Zaun.

**Rot zuerst, sechs Pflanzungen im Klon** (`_round-scratch/TSK-0114/gaterig/`, außerhalb des Repos;
links die Fassung aus `HEAD`, rechts die reparierte; gefahren wurde je nur dieser eine Test):

| Pflanzung in H46 | HEAD | repariert |
|---|---|---|
| nichts (Grundlinie) | 1 passed | 1 passed |
| Geist-Name VOR dem Zaun | 1 failed | 1 failed |
| Geist-Name HINTER dem Zaun | **1 passed — falsches Grün** | 1 failed |
| lebender `tools/`-Test, nackt | **1 failed — falsches Rot** | 1 passed |
| lebender `tools/`-Test, modulqualifiziert | **1 passed — übersprungen, nie geprüft** | 1 passed |
| Geist-Name, modulqualifiziert | **1 passed — falsches Grün** | 1 failed |

Die vierte Zeile war **live**: H83 nennt
`test_reference_skills.test_the_codex_mirror_is_generated_per_skill_directory`
(`tools/test_reference_skills.py:364`), und der alte Leser fand den Namen in `test_gates.py` nicht.

**H121 ist geschlossen** (Tabellenzeile + Eintrag + Messung + Urteil), der N11-Rest aus Strom I
ebenso, im selben Eintrag als der Nachbarbefund benannt.

**Nachgeschärft in Nacharbeit 1** (2026-09-03), nachdem der Merge-Prüfer drei Schreibweisen
gepflanzt hat, die der erste Fix nicht erreichte:

* **M1 — der Korpus.** `_hole_entries` beginnt einen Eintrag an seiner `### H<n>`-Überschrift, also
  war jedes Zitat in der ZUSAMMENFASSUNGSTABELLE ungelesen. Neu: `_hole_citation_sources` gibt je
  Nummer den Eintrag UND die Zeile, die ihn beurteilt. Bewusst ein eigener Korpus statt eines
  weiteren `_hole_entries`: vier andere Leser stellen eintragsförmige Fragen an diesen einen, und
  `test_the_hole_list_judges_every_entry_it_carries` vergleicht die ZEILE gegen die
  `**Urteil …**`-Spanne des Rumpfes — die Zeile in den Rumpf zu falten hieße, beide Seiten dieses
  Vergleichs an denselben Ort zu legen.
* **M2 — was ein Zaun ist.** Eine Zaun-Zeile besteht NUR aus ihrem Marker (plus Infostring). Vorher
  zählte auch eine Zeile mit einer kurzen Code-Spanne aus drei Backticks mitten im Satz als Zaun,
  und dann entschied deren ANZAHL: ungerade laut, gerade still. `~~~` gilt jetzt ebenfalls als Zaun.
* **M2 (die Wurzel darunter).** Das allein reichte nicht: gepaart wurde „Backtick, Text, Backtick",
  also verschob ein Dreier-Lauf mitten im Satz jede Paarung dahinter, auch ohne Zaun. Gepaart wird
  jetzt nach LAUFLÄNGE (`_CODE_SPAN_RX`), wie Markdown selbst es tut. Diese Schärfe machte zwei
  Prosa-Idiome sichtbar, die keine Nennung sind — eine Spanne, deren INHALT einen Backtick trägt
  (eine Spanne, die eine Spanne zeigt), und das nackte Präfix `test_` — beide sind in `_cited_test`
  ausgenommen, mit dem Grund im Docstring, statt sie aus dem Dokument zu entfernen.

**Pflanzungstabelle, vorher/nachher** (Kopie außerhalb des Repos, `_round-scratch/TSK-0114/gaterig`;
`plants.py` fährt je nur den einen Test und stellt die Kopie danach zurück):

| Pflanzung | vor Nacharbeit 1 | nach Nacharbeit 1 |
|---|---|---|
| nichts (Grundlinie) | rc 0 | rc 0 |
| A6 Geist-Name in der H46-TABELLENZEILE | rc 0 — falsches Grün | **rc 1, Geist gemeldet** |
| A7 Geist zwischen zwei Zeilen mit Inline-Dreier-Lauf | rc 0 — falsches Grün | **rc 1, Geist gemeldet** |
| A2 Geist HINTER einem `~~~`-Zaun | rc 1, Geist gemeldet | rc 1, Geist gemeldet |
| A2b Geist INNERHALB eines `~~~`-Zauns | rc 0 | rc 0 — der benannte Preis |
| A2c Geist INNERHALB eines Backtick-Zauns | rc 0 | rc 0 — der benannte Preis |

A2b/A2c sind die Gegenprobe zum Preis des Schnitts und stehen im Docstring des Prüfers und im
Urteil von H121. Der Leser liest jetzt **140 Zitate statt 43** (127 nach dem ersten Schritt);
19 der 116 Einträge tragen einen Zaun.

**Drei eigene Fehler, die dieser Prüfer selbst gefangen hat** (alle behoben, alle protokolliert):
mein H121-Eintrag nannte Platzhalter-Testnamen in Backticks; der Kommentar an
`_CITATION_SPLIT_RX` tat dasselbe — der Prüfer und sein Nachbar
`test_every_check_this_apparatus_claims_in_its_own_prose_is_one_that_exists` wurden davon rot; und
die neue Tabellenzeile für H125 trug `Bash|PowerShell` in einer Zelle, was den Zeilenleser vier
Zellen statt drei sehen ließ.

---

## 5. Was diese Runde außerdem geschlossen hat (jeweils rot gemessen)

| Fix | Roter Test ohne ihn | Messung |
|---|---|---|
| `.gitignore`-Regel für die erzeugte Finanzseite (I 6.3) | `test_hooks_v2.test_the_office_gitignore_keeps_the_generated_dashboard_out_of_git` (neu) | Regel entfernt → `dashboards/finanzen.html` landet in git → 1 failed; `dir/*` durch `dir/` ersetzt → `ABOUT.txt` verschwindet → 1 failed |
| entartete Plural-Paare werden bei der Ernte verworfen (I-Rest, halb) | `test_finance_dashboard.test_every_count_on_the_page_reads_right_at_one` | Aufrufstelle auf `plural(n, "Buchungen", "Buchungen")` mutiert: **mit** Fix 1 failed („1 Buchungen"), **ohne** Fix 1 passed |
| `_same_place`: die Groß-/Kleinschreibungs-Hälfte hat einen Halter (G-Rest) | `test_office_duties.test_the_place_reader_folds_case_exactly_where_the_platform_does` (neu) | `normcase` entfernt → 1 failed, der genannte Nachbartest bleibt grün |
| der Flächen-Leser trennt Route von Inventar | `test_hooks.test_every_span_that_presents_the_command_surface_names_all_of_it` | Ausschluss entfernt → die vier Routen-Blöcke sind Befunde; mit Ausschluss und einem aus der dev-Verfassung gestrichenen Kommando → weiterhin rot („names 31, misses `freeze-report`") |
| `legal_form` — der Test fragt nach URTEILEN statt nach LESEN | `test_hooks_v2.test_no_shipped_office_module_decides_anything_on_the_legal_form` | Generator so mutiert, dass er auf `== "GmbH"` verzweigt → 1 failed; das bloße Drucken im Seitenkopf ist grün |
| die Ambitions-Regel im PM-Skill | `test_hooks_v2.test_the_design_ambition_is_still_the_users_call` | Verbot „NEVER decide any of it silently" entfernt → 1 failed |

**Der Plural-Rest ist nur zur Hälfte geschlossen, und die andere Hälfte ist widerlegt:** der
Vorschlag „drop the isupper sieve" wurde probiert und gemessen — jede Fixture wird dann rot an
`1 in`, weil die Seite den echten Satz „davon 1 in einem anderen Ledgerjahr storniert" trägt. Das
Sieb steht wieder, mit dieser Messung als Begründung im Code und mit dem Satz, was es nicht
erreicht.

---

## 6. Zeiger-Tabelle Wunschliste (Output 4)

Zwölf Sätze, je als **letzte Zeile** des Abschnitts, an der Überschrift als Anker (nicht an der
Zeilennummer). Die sieben dünnen FRs sind erfasst und stehen mit ihrer Nummer statt mit
„(dünnes FR anlegen)". Jede genannte Id wurde im Speicher nachgeschlagen (21 von 21 aufgelöst).

| § | Anker | Zeiger |
|---|---|---|
| 1 + 1a | `### 1a. Führung und Rangfolge …` | → FR-0078 (gilt auch für §1) |
| 1b | `### 1b. Claude Design …` | **Erledigt:** → FR-0045 |
| 1c | `### 1c. Was als ANLEITUNG eingebaut wurde …` | → FR-0077 |
| 2 | `## 2. Board- und Backlog-Ansichten` | → FR-0024 (+FR-0030/0053, offen FR-0017), Termine → FR-0079 |
| 3 | `## 3. Der Plan als Bild …` | → FR-0080 |
| 4 | `## 4. Effort-Stufen pro Rolle …` | → FR-0047, DEC-0034, DEC-0059 |
| 5 | `## 5. Finanz-Vorlagen …` | → FR-0032 (geliefert in TSK-0109), Kontenrahmen → FR-0081, FR-0002 |
| 6 | `## 6. Mehrere Spezialisten …` | → FR-0021 |
| 7 | `## 7. Ein dritter Evidence-Ausgang: blocked` | → FR-0082, Nachbar FR-0040 |
| 8 | `## 8. Ein Projekt vollautonom …` | → FR-0074, DEC-0058 |
| 9 | `## 9. Der Masterplan braucht einen Zustand` | **Teilweise:** DEC-0058/FR-0074; offene Hälfte bleibt L1 |
| 10 | `## 10. Die Freigabe programmatisch erteilen …` | → FR-0083 |

---

## 7. Reste-Nummerierung (Output 2)

Neu vergeben, jeder mit Tabellenzeile, Eintrag, Herkunft und `**Urteil …**`-Spanne:

* **H122** — der Melder über ungelesene Prosa fragt, was **git trägt** (J's N1). Kette: eine
  ignorierte Datei nennt ein Dokument → der Melder sieht die Nennung nicht → das Dokument wird als
  ungelesen gemeldet und verschoben. Begrenzung gemessen: außerhalb der Werkzeug-Caches trägt
  dieser Baum keine nicht-getragene Datei. Urteil: Rest, benannt.
* **H123** — eine Löschung mit einer FLAGGE statt eines Verbs kommt an `guard_fs_tripwire` vorbei
  (G's P12). **Kette in dieser Runde am gemergten Baum neu gefahren**, der Haken als echter
  Prozess auf einem Vorlagenprojekt außerhalb des Repos, mit einem echten Dokument unter
  `archive/finance/2026/`:

  ```
  rc=0  eine Suche, die ihre Treffer mit einer Lösch-Flagge entfernt
  rc=0  ein Archivierer mit quelllöschender Flagge
  rc=0  eine Löschung innerhalb eines anderen Programms
  rc=2  dieselbe Löschung mit einem Lösch-Verb
  rc=2  eine Bewegung aus dem Archiv heraus
  ```

  Urteil: OFFEN und gemessen, begrenzt durch den Kopf des Wächters und — seit dieser Runde — durch
  Verfassung und Rollentext, die die Wand nicht mehr absolut behaupten (E7/E2).
* **H124** — die Fristenmeldung liest `datetime.date.today()` der lokalen Maschine einmal je
  Sitzungsstart (G's P11). Urteil: Rest, benannt; ohne ein Feld für die Zeitzone nicht schließbar.

**Nicht nummeriert, mit Grund** (kein Angriffspfad, kein Datenverlust, oder es gibt schon ein Item):

* G's E2E-Deckung ist disjunktiv — der Test sagt das in seinem eigenen Docstring, und der Strom hat
  den Satz dort korrigiert. Keine Kette.
* G's P9-Nebenbefund (`session_brief.yaml` ohne PROC-Abschnitt) — das ist die zweite Hälfte von
  FR-0034, ein fehlendes Feature und kein Loch.
* G's F6 (der Kernel prüft `retention` nicht) — die Folge ist eine Meldung „DEADLINE REGISTER
  INCOMPLETE" bei jedem Sitzungsstart: fail-closed, Über-Meldung, kein Loch.
* F's N7 (Tray-Test 585 s / 346 s gegen 600 s) — eine Laufzeitmarge der Suite, kein Produktverhalten.
* H's Reibung `docs/agents/` — vom Strom als Reibung mit Messung benannt, kein Schutzverlust.
* K/H: die office-`settings.json` registriert PreToolUse-Haken ohne `timeout` — Kit-Seite, FR-0057.
* K: eine Haken-Datei, die von AUSSERHALB des Repos gestartet wird, passiert Gate 1 — das ist
  H80's bereits benannter Rest, keine neue Nummer.
* `test_gates._hole_rows` liest eine dreispaltige Tabelle INNERHALB eines Eintrags als
  Zusammenfassungszeile, wenn ihre erste Zelle eine H-Nummer trägt. Beim Schreiben von H121
  getroffen und durch eine andere Kopfzeile umgangen. **Über-Meldung, fail-closed** — der Test wird
  laut rot, nichts wird still durchgelassen. Kein Loch; hier benannt, damit der nächste Autor es
  weiß.

---

## 8. Was bewusst offen bleibt

* **I's Naht 6.1/6.2 (der Dashboard-Auslöser) ist NICHT gebaut.** I's eigenes Protokoll sagt: „Wenn
  diese Zeile ohne 6.2 landet, ist die einzige Folge, dass das Kit die Datei bei jedem Scaffold
  überschreibt — kein Fehler, aber auch kein Gewinn. Beide Zeilen gehören in EINEN Merge-Schritt."
  Und der Begründungstext, den 6.1 verlangt, würde behaupten, `gate_ledger_valid` starte den
  Generator nach jeder Buchung — was ohne 6.2 falsch wäre. 6.2 selbst ist eine Verhaltensänderung
  an einem ausgelieferten Gate mit eigener Frist-Messung und eigenem roten Test; das ist ein Bau,
  keine Naht. **H117 trägt beides mit Mechanismus und Kette.**
* **F's Nähte S2–S6** (research §6/§17 `freeze-report`, der Report-Writer-Rollentext, der
  `--run-scope`-Satz für QE/Reviewer, der `gate_git`-Verweigerungstext) sind **nicht geschrieben**:
  das Item nennt für diese Runde S1 und S11. H94 bleibt damit „offen, nur noch die Verfassungszeile".
* **H's Protokoll-Zeilennummer** (der eine N-Rest seines PASS) ist nicht korrigiert — die Datei
  liegt unter `project_memory/staging/TSK-0108/` und damit im `forbidden_scope` dieses Items.
* **REST — die `description`-Zeilen der drei `project-auditor.md` widersprechen ihrem eigenen
  Rumpf.** `team-kits/{dev,office,research}-team/agents/project-auditor.md:3` sagt „Project Auditor
  — weekly / event-triggered READ-ONLY reviewer …", während `:17` seit E3 sagt „Your cadence stands
  in the code and not a second time here". Beides in einer Datei, in allen drei Kits. Der Takt steht
  damit weiter an zwei Stellen — genau der Mechanismus, den E3 schließen sollte —, nur jetzt
  sichtbar nebeneinander. **Nicht angefasst, mit Grund:** die `description` ist eine Kit-Datei, sie
  geht in den Kit-Hash ein, und eine Änderung daran zöge einen weiteren Stempel und einen weiteren
  Volllauf nach sich; dazu ist sie die Fläche, an der der Router misst, gehört also der Runde, die
  die Rollen- und Verfassungstexte besitzt (Generation 3, Strom D). Bis dahin gilt der Rumpf: er ist
  die Anweisung an die Rolle, die `description` ist die Anzeige für den Router.
* **Zwei Stempel-Läufe statt einem, und die Reihenfolge dazwischen.** Der erste Lauf
  (`dev/office/research → 2026.09.02-11`) kam nach dem letzten GEPLANTEN Änderungsschritt. Danach
  fand Teil A des Volllaufs (`tools/test_hooks_v2.py`, 2132 passed / 5 failed) fünf Befunde, und
  drei davon berührten Kit-Dateien — also musste ein zweiter Stempel folgen. Die fünf, in der
  Reihenfolge, in der ich sie geschlossen habe:

  | # | Befund | Geändert | Kit-Datei? |
  |---|---|---|---|
  | 1 | `test_the_design_ambition_is_still_the_users_call` | `dev-team/skills/project-manager/SKILL.md`, `tools/test_hooks_v2.py` | ja |
  | 2 | `test_no_shipped_office_module_decides_anything_on_the_legal_form` | `tools/test_hooks_v2.py`, `office-team/templates/project_memory/business_profile.yaml` | ja |
  | 3 | `test_every_file_that_explains_ledger_writing_states_the_current_rule` | `office-team/skills/office-developer/SKILL.md`, `office-team/templates/repo/dashboards/ABOUT.txt` | ja |
  | 4+5 | `test_the_state_a_fresh_scaffold_leaves_behind_still_permits_delegation`, `test_a_project_with_no_trust_record_is_not_stopped_and_the_hole_is_named` | `tools/test_hooks_v2.py` (Fixture `dispatched_repo`) | nein |

  Danach der zweite Stempel: `dev/office → -12`, `research` **unverändert -11**, weil sein Inhalt
  sich nach dem ersten Lauf nicht mehr geändert hat und der Stempler nur bumpt, was sich ändert
  (dieselbe Lage wie in G's Runde: „office -16, dev/research unchanged -12"). Der Baum trägt damit
  genau einen konsistenten Stand, `--check` → unchanged ×3.

* **Zwei Nacharbeiten NACH dem Volllauf, beide ohne Kit-Datei und darum ohne dritten Stempel.**
  (a) `tools/constitution_section_pins.json` + der Journal-Eintrag in
  `docs/reviews/phase0-disposition.md`, weil mein Ambitions-Satz nach der Neuaufnahme kam; lesende
  Suiten: `test_shortening_net`, `test_context_budget`, `test_disposition` → **86 passed** (mein
  Lauf); der Merge-Prüfer hat dieselbe Menge weiter gefasst gefahren und **91 passed / 1 skipped**
  gemessen. (b) der Kommentar an `_CITATION_SPLIT_RX` in `.claude/hooks/test_gates.py`; lesende
  Suite ist die Gate-Suite, die der Prüfer danach **vollständig mit 489 passed** gemessen hat
  (beide Zahlen aus dem Prüferbericht zu TSK-0114, nicht aus meinem Lauf — meiner endete mit
  488 passed / 1 failed und war der Anlass für (b)).

---

## 9. Läufe

**Volle `tools/`-Suite, EINMAL nach der letzten Nacharbeit, in drei Teilen — jede Datei genau einmal:**

| Teil | Umfang | Ergebnis | Dauer |
|---|---|---|---|
| A | `tools/test_hooks_v2.py` | **2137 passed** | 14:40 |
| B | `tools/test_hooks.py` | **902 passed, 13 skipped** | 18:05 |
| C | die übrigen 31 Dateien | 1308 passed, 1 skipped, **1 failed** | 28:17 |

**Der Buchstabe von DEC-0050 und was hier wirklich lief:** Teil A ist der ZWEITE Lauf von
`tools/test_hooks_v2.py`. Der erste (2132 passed / 5 failed) war die Aufklärung, aus der die fünf
Befunde in Abschnitt 8 kommen; nach deren Behebung lief er noch einmal, und das ist die Zeile
oben. Die Suite als LIEFERKRITERIUM ist also einmal vollständig über den ausgelieferten Baum
gegangen, der Zähler „ein Lauf je Datei" gilt aber nur für diesen letzten Durchgang. Der
Merge-Prüfer hat beide großen Teile auf dem ausgelieferten Baum unabhängig nachgefahren und
dieselben Zahlen gemessen: `test_hooks_v2` **2137**, `test_hooks` **902 passed / 13 skipped**.

Gegenrechnung: `python -m pytest tools/ -q --collect-only` → **4362 collected**;
2137 + 915 + 1310 = **4362**. ✔

Der eine rote Test war `test_shortening_net.test_no_section_of_a_pinned_instruction_file_disappears_unnoticed`
— mein Ambitions-Satz im PM-Skill kam nach der Neuaufnahme der Abschnitts-Pins. Pin nachgezogen
(`pin_constitution_sections.py --write --note …`), danach
`test_shortening_net + test_context_budget + test_disposition` **86 passed**. Die Pin-Datei ist eine
`tools/`-Datei und geht in keinen Kit-Hash ein (`bump_kit_version.py --check` → unchanged).

**Gate-Suite vollständig:** `python -B -m pytest .claude/hooks/test_gates.py -q` →
**488 passed, 1 failed** (33:08). Der rote Test war
`test_every_check_this_apparatus_claims_in_its_own_prose_is_one_that_exists` und der Befund war
mein eigener Kommentar (Abschnitt 4). Nach der Korrektur:
`-k "claims_in_its_own_prose or hole or prefix or measurement or reference"` → **10 passed**.
Der von Strom J gemeldete Zeit-Test (BUG-0033), der auf sauberem `6d18407` 4 von 6 Läufen rot war,
lief in dieser Runde grün durch.

**Ratschen:** `pin_constitution_sections.py --write` (13 + 1 Abschnitte, mit Notiz),
`record_lead_package_sizes.py --write` (dev +845 B, office +1071 B, research +1218 B, mit Notiz).

**Werkzeuge:** `python -m ruff check .` → All checks passed. `python tools/validate.py` → all
structural checks passed. `python tools/bump_kit_version.py --check` → unchanged.

**Stempel:** `dev-team 2026.09.02-12`, `office-team 2026.09.02-12`, `research-team 2026.09.02-11`.

**Neue Dateien:** mit `git add -N` angemeldet (43 Stück), damit `validate.py` und der Kit-Hash
dieselbe Dateimenge sehen wie ein frischer Klon. Kein `git add` von Inhalten, kein Commit.

**Endzustand:** 124 Dateien geändert, +16314/−367 (ohne `project_memory/`).

---

## 10. DEC-0060 (g) — Generation 2, F-Zeile vervollständigt

| Strom | Umsetzer-Stufe(n) | Prüfer | Erstbefunde (B/M/N) | Nachprüfungen | Nacharbeiten | Spawn → PASS | Prosa-Anteil |
|---|---|---|---|---|---|---|---|
| E Texte | Fable | nicht protokolliert (vor dem Stopp) | 6 (1 B-als-Benennung / 2 / 3) | 6 → 0 | 1 (13,5 min) | ~1 h 55 | hoch (Spiegel-Untergrenze als Zahl, Brief-Zählung) |
| F Kernel | Opus (zwei Läufe) | Opus | 14 (4/3/7) | 14 → 5 (1 B) → 0 | 2 (48 + 12 min) | **~12 h** | gemischt: die vier B waren Mechanismus (nicht registrierte Route, ungetestetes `all`, zählende Karte, Exit-Code); der B der zweiten Runde war „der genannte Test kann nicht messen" |
| G Office | Opus (zwei Läufe + Neuschnitt) | Opus | 16 (3 B / 3 Löcherliste / 7 Nacharbeit + 3 Item) | 16 → 5 → 1 | 2 (57 + 15 min) | ~11 h | Runde 1 überwiegend Mechanismus; Runden 2–3 Prosa/Deckung |
| H Messungen | Opus (zwei Läufe) | Opus | 10 (4/3/3) | 12 → 6 → 4 → 1 → 0 | 4 (27/27/16/9 min) | ~5 h 30 | fast alles Prosa |
| I Dashboard | Fable (Entwurf, 26 min) + Opus (Bau + 3 Nacharbeiten) | Opus | 13 (1/5/7) | 13 → 10 (2 B am Fix) → 6 N → 1 N | 3 (1 h 26 / ~50 / 18 min) | ~9 h | gemischt |
| J Hygiene | Opus (zwei Läufe) | Opus | 10 (2/1/7) | 10 → 4 → 2 → 0 | 3 (27 / 7 / 2 min) | ~10 h | B waren Mechanismus, Rest Prosa |
| K Humanizer | Fable (Bau + 2 Nacharbeiten) → **Opus** (2 Nacharbeiten) | Opus ×4 | 9 (2/2/5) | 9 → 6 (5 neu) → 8 (6 Prosa) → **2 (0 Prosa)** → 1 → 0 | 4 (36/36/31/13 min) | ~7 h 50 | Fable-Nacharbeiten brachten je neue Universalsätze; Opus-Nacharbeiten keine |
| **TSK-0114 Merge** | **Opus** | (steht aus) | — | — | — | **~4 h 15** | die eigenen Befunde dieser Runde waren zur Hälfte Prosa (drei Sätze, die mehr behaupteten als der Code: S11-b, I's Manager-Satz, I's `_shipped_code_dirs`-Satz) und zur Hälfte Mechanismus (Rollenroute, Fixture-Ursprung, Aktenplan-`retention`) |

Was diese Runde der Lesung von DEC-0060 hinzufügt: **die teuersten Befunde der Merge-Runde waren
die, die kein Strom sehen konnte.** Jeder Strom war für sich grün. Es sind **sechs**, und sie stehen
hier einzeln, weil diese Zahl in die DEC-0057-Nachlese eingeht:

| # | Befund | Der Test, der ihn fing | Warum kein Strom ihn fahren konnte |
|---|---|---|---|
| 1 | F registriert `REVISION_WRITES`, neun Rollentexte nennen die Route nicht | `test_role_contracts.test_every_role_that_owns_a_kit_document_carries_the_route_that_writes_it` (14 Befunde) | F fuhr diese Suite nach seiner Nacharbeit nicht mehr; E fuhr sie, bevor F's Registrierung existierte |
| 2 | G's Vorlage antwortet `retention: null`, der Leser stürzt darüber | `test_hooks.test_the_shipped_filing_plan_is_understood_by_both_of_its_readers` | der Test steht in `tools/test_hooks.py`, das G nicht fuhr |
| 3 | I's Generator liest `legal_form`, den G's neuer Test verbietet | `test_hooks_v2.test_no_shipped_office_module_decides_anything_on_the_legal_form` | I's Datei existierte nicht, als G den Test schrieb; G's Test existierte nicht in I's Worktree |
| 4 | F's Ursprungsregel macht eine Fixture ungültig | `test_hooks_v2.test_the_state_a_fresh_scaffold_leaves_behind_still_permits_delegation` und `…test_a_project_with_no_trust_record_is_not_stopped_and_the_hole_is_named` | F fuhr `test_hooks_v2` nicht vollständig |
| 5 | E's Umschrift des PM-Skills löst die Ambitions-Regel aus ihrem Anker | `test_hooks_v2.test_the_design_ambition_is_still_the_users_call` | E fuhr `test_hooks_v2` nicht |
| 6 | I's `ABOUT.txt` erklärt Ledger-Schreiben ohne die geltende Regel | `test_hooks_v2.test_every_file_that_explains_ledger_writing_states_the_current_rule` | die Datei ist neu von I, der Test älter und nicht in I's Lauf |

Nicht in dieser Zählung: die Nähte, die ein Strom SELBST benannt hat (I × K im Docstring, F's S1,
G's E1–E7) — die waren bekannt und übergeben, nicht verborgen. Ebenfalls nicht: die Befunde, die
diese Runde selbst eingeführt hat (mein Satz im `office-developer`-Skill, zwei Platzhalter in
Backticks, eine Tabellenzelle mit einem Pipe-Zeichen). Eine Generation ohne Merge-Runde mit voller
Suite hätte die sechs oben ausgeliefert.

---

## 11. Nacharbeit 1 (2026-09-03) — die sieben Befunde der Merge-Prüfung

Prüferurteil: FAIL, B 1 / M 2 / N 4, alles Prosa oder Prüfer-Code, **keine Kit-Datei** — also kein
neuer Stempel. Prüfer-Rig `_round-scratch/TSK-0114/verify/`, meine Nachmessungen in
`_round-scratch/TSK-0114/gaterig/` und `…/pilot-h125-*`.

### B1 — H123 behauptete eine Begrenzung, die nicht gilt

Der dritte Satz sagte, die Fehlklasse des Versehens laufe vollständig durch den Wächter. **Selbst
nachgemessen** (`probe_h125.py`, Pilot außerhalb des Repos mit der ausgelieferten `.gitignore` des
Office-Kits, echter Beleg unter `archive/finance/2026/`, alle **acht** auf Bash und PowerShell
registrierten Office-Haken als Prozesse, nichts ausgeführt):

| Befehlszeile | Urteil der acht Haken |
|---|---|
| `unlink` auf den Beleg | ALLOW |
| `git clean -fdx` | ALLOW |
| `git clean -fdx archive` | ALLOW |
| `Clear-Content` auf den Beleg | ALLOW |
| `rm` (Kontrolle) | rc 2, `guard_fs_tripwire` |
| Bewegung aus dem Archiv (Kontrolle) | rc 2, `guard_fs_tripwire` |

Der Beleg ist im Piloten **ungetrackt und ignoriert** — die Menge, die `-fdx` entfernt; das ist das
Versehen in Reinform. Der dritte Begrenzungssatz von H123 gilt jetzt nur noch für die VERB-Klasse,
die dieser Eintrag beschreibt, und verweist für den Rest auf **H125** (neu: Tabellenzeile, Eintrag,
Herkunft, Kette, Urteil). H125 sagt ausdrücklich: **nichts begrenzt es** — der Wächterkopf nennt
diese Klasse nicht, und kein Text des Kits behauptet sie noch. Der Fix ist eine Eigenschaft statt
eines Verb-Tupels und damit ein Bau am Office-Kit; DEC-0056 spricht NICHT dagegen, weil ein
gelöschter Beleg unumkehrbar ist. Der Kopf des Wächters wurde nicht angefasst (Kit-Datei, und der
Eintrag sagt genau, dass der Kopf die Klasse nicht nennt).

### M1 + M2 — der Namensprüfer las zwei Sorten Zitat nicht

Beschrieben in Abschnitt 4 mit der Pflanzungstabelle. Kurz: der Korpus ist jetzt Eintrag **und**
Zusammenfassungszeile (`_hole_citation_sources`), eine Zaun-Zeile besteht nur aus ihrem Marker,
`~~~` zählt mit, und gepaart wird nach Lauflänge (`_CODE_SPAN_RX`). 140 gelesene Zitate statt 127.

### N1–N4

* **N1** H121's Umfangsangabe „10 von 97 … bleiben zehn" ist durch eine Tabelle mit BEIDEN Ständen
  ersetzt (2026-09-02: 97/10 im Worktree von TSK-0111; 2026-09-03: 116/19 im gemergten Baum, mit
  den neun dazugekommenen Nummern). Der zweite Begrenzungssatz sagt jetzt „ein Sechstel" statt
  „zehn".
* **N2** Der Widerspruch zwischen `project-auditor.md:3` und `:17` steht in Abschnitt 8 als Rest,
  mit Datei, Zeile, beidem Wortlaut und dem Grund, warum diese Runde ihn nicht anfasst.
* **N3** Die Aussage „sechs von acht" ist durch die Tabelle der sechs Befunde in Abschnitt 10
  ersetzt — je Befund der Test, der ihn fing, und warum kein Strom ihn fahren konnte. Was NICHT
  mitzählt, steht daneben.
* **N4** Abschnitt 8 trägt jetzt die fünf Befunde nach dem ersten Stempel mit Dateiliste und
  Reihenfolge sowie die zwei Nacharbeiten nach dem Volllauf mit ihren lesenden Suiten; die Zahlen
  des Prüfers sind als seine zitiert, meine als meine.

### Läufe der Nacharbeit 1

| Lauf | Ergebnis |
|---|---|
| Pflanzungen A6 / A7 / A2 / A2b / A2c (`plants.py`, je nur der eine Test) | siehe Tabelle in Abschnitt 4 |
| `probe_h125.py` (acht Haken × sechs Zeilen) | 4 × ALLOW, 2 × rc 2 |
| `.claude/hooks/test_gates.py` **voll** | **489 passed** (36:35) — nach dem einen Fehlschlag unten korrigiert und erneut voll gefahren |
| `tools/test_repo_hygiene.py` (der Leser der Wunschliste) | **25 passed** (2:05) |
| die sechs Löcherlisten-Tests (`-k hole`) | **5 passed** (die Menge, die `-k hole` heute wählt) |
| `python -m ruff check .` | All checks passed |
| `python tools/bump_kit_version.py --check` | unchanged ×3 (dev/office `2026.09.02-12`, research `2026.09.02-11`); `validate.py` grün |

**Ein eigener Fehler dieser Nacharbeit, gemessen statt behauptet:** der erste Gate-Vollauf nach
M1/M2 war **488 passed / 1 failed** — mein neuer Docstring in `_cited_test` zeigte das
Namens-Präfix in Backticks, und `test_every_check_this_apparatus_claims_in_its_own_prose_is_one_that_exists`
las das als Nennung eines Tests, den es nicht gibt. Das ist derselbe Fehler zum vierten Mal in
dieser Runde (H121-Eintrag, `_CITATION_SPLIT_RX`-Kommentar, H125-Tabellenzeile mit einem
Pipe-Zeichen, jetzt dieser). Der Docstring nennt beide Formen seither ausgeschrieben und sagt in
einem Klammersatz, warum — das ist die Regel, die diese Runde vier Läufe gekostet hat.
