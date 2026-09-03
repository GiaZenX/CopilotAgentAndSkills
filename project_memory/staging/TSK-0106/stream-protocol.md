# TSK-0106 — Stream F (kernel), zweite DEC-0057-Generation

Worktree `C:/Offline Repos/v2-testbed/_worktrees/g2-kernel` (Branch `g2/kernel`, aus `6d18407`).
Patch: `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0106/stream-kernel.patch` (1703 Zeilen,
17 geänderte Dateien, keine neuen Dateien — `git add -N` war ein No-op).
Rot-Rig (außerhalb des Repos): `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0106/redrig/`.

Geliefert: **(1) BUG-0083 + BUG-0086, (2) BUG-0084, (3) BUG-0085, (4) FR-0040.**
**Nicht geliefert und bewusst abgebrochen: Punkt (5) der Auftragsliste** (FR-0017, FR-0018,
FR-0037, FR-0039, FR-0054, FR-0067) — Begründung unten unter „Was nicht geschlossen wurde".

---

## 1. BUG-0083 + BUG-0086 — die Ursprungsprüfung urteilt transitiv und fällt bei Mehrdeutigkeit zu

**Gebaut.** `report._root_of` ist ersetzt durch `report.origin_root_conflict(state, origin_id,
root_id)`. Die Frage ist nicht mehr „welches Item ist die Wurzel dieses Ursprungs", sondern
„gehört dieser Ursprung zu DIESER Wurzel"; beantwortet wird sie mit `_reaches_on_every_path` —
dieselbe Wanderung wie `_hangs_from`, aber mit `all` statt `any`, zyklensicher, und eine Sackgasse
ist ein Nicht-Ankommen wie jedes andere. Beide Aufrufer benutzen dieselbe Funktion
(`dispatch._assert_origins_belong_to_root_locked` importiert sie und zitiert ihren Satz), also kann
der Anlege-Weg nicht verweigern, was `validate` durchlässt.

Drei Fälle, drei Sätze: alle Elternpfade führen zur Wurzel → angenommen; keiner → „X belongs to Y,
not to this task's root Z"; ein Teil → die Mehrdeutigkeit wird benannt, samt dem Elternteil, der
wegführt (die Abhilfe ist eine andere als beim Fremdwurzel-Fall).

**Dritter Fall, von dieser Runde selbst gefunden statt gemeldet:** derselbe `None` stand auch für
„GAR KEIN Elternteil". Ein Ursprung, der selbst eine Wurzel ist (ein zweites `PR`), wurde unter
jeder anderen Wurzel angenommen — derselbe Schaden, weil der Dispatch-Gate `acceptance_refs` gegen
den Ursprung auflöst. Sichtbar wurde es daran, dass sieben Fixture-Aufrufe in
`tools/test_approvals_dispatch.py` rot wurden, die `PR-0001` als Ursprung unter einer anderen
Wurzel nannten. Kollateral gemessen und begrenzt: ein Helfer (`_analysis_task`), sieben identische
Aufrufstellen, eine Extraktion in `test_report` (sie las die ganze Meldung als Feldnamen, weil das
Referenz-Finding die Form `<feld> -> …` hat und dieses Finding Prosa ist).

**Rot ohne den Fix** (Klon, alte Ein-Sprung-Fassung `parents[0] if len(parents) == 1 else None`
wiederhergestellt):
- `tools/test_kernel.py::test_a_task_may_derive_from_an_experiment_two_levels_under_its_root`
- `tools/test_kernel.py::test_an_origin_with_a_parent_outside_the_root_is_refused_at_creation`
- `tools/test_kernel.py::test_a_task_may_not_derive_from_a_ROOT_item_of_another_tree`
- `tools/test_report.py::test_a_task_on_an_origin_two_levels_under_its_root_is_fine`
- `tools/test_report.py::test_an_origin_that_reaches_the_root_through_only_one_of_its_parents_is_refused`

**Gegenrichtung gemessen** (damit die Verweigerung nicht in „jeder mehrelterige Ursprung ist
verboten" verfällt): `test_kernel.py::test_an_origin_whose_parents_all_hang_from_the_root_is_still_creatable`
und `test_report.py::test_an_origin_whose_parents_all_hang_from_the_root_is_still_accepted`.

**Pin-Test invertiert, wie sein eigener Docstring es verlangte.**
`test_research_chain.py::test_a_task_on_an_experiment_cannot_name_the_question_the_experiment_hangs_from`
heißt jetzt `test_a_task_may_name_an_experiment_two_levels_under_the_question_it_serves` und misst
beide Richtungen (Erfolg + weiterhin richtige Verweigerung unter einer fremden Frage). Der Umweg in
Szenario 1 (ein Experiment mit ZWEI Eltern) ist entfernt: die Kette läuft jetzt mit der Hypothese
allein, so wie §4 sie beschreibt. Neu daneben:
`test_an_experiment_hanging_from_two_questions_is_refused_as_an_origin`.

**Dev- und office-Ketten unverändert:** `test_a_cross_root_origin_is_refused_at_creation`,
`test_a_task_under_its_own_root_is_still_creatable`, `test_a_task_deriving_from_another_roots_tree_is_an_error`,
`test_a_task_deriving_from_its_own_roots_tree_is_fine` bleiben grün.

## 2. BUG-0084 — keine Freigabe für ein Paar, das keine Kante geht

**Gebaut.** `approvals._assert_the_pair_commits_an_edge` läuft in `create_pending_request`, sobald
der Gegenstand AUS DEM ITEM gebildet wird, und verweigert jedes `(Typ, Art)`, das
`APPROVAL_TRANSITIONS` nicht führt. Der Gegenstand wird VOR der Prüfung gebildet, damit eine Art,
die überhaupt nicht item-abgeleitet ist, ihre eigene Verweigerung behält. Die `HYP`-Freigabe ist
damit nicht mehr anforderbar — und der Ausweg, der zu ihr zwang, existiert seit (1) nicht mehr.

**Entschieden, nicht geraten:** der andere in BUG-0084 genannte Weg (HYP in `HASHED_FIELDS`, echter
Gegenstand) wäre eine Spec-Änderung — Verfassung §4, `INVALIDATION_TARGET` („HYP deliberately
absent") und `APPROVAL_TRANSITIONS` sagen einstimmig, dass es diese Freigabe nicht gibt.

**AC-3 war bereits gebaut, und der Befund las den abgeleiteten WERT.**
`report.accepted_without_a_verdict` steht seit TSK-0082 auf
`delivery_roots = set(ROOT_TYPE_BY_KIT.values())`; `{PR, RQ}` IST diese Ableitung. Was fehlte, war
die Messung der INKLUSIONS-Richtung — die Ausschluss-Richtung (office/PROC) hatte einen Test, die
Einschluss-Richtung keinen, und eine Aufzählung `{"PR"}` wäre grün durchgekommen. Neu:
`test_report.py::test_a_task_under_every_kit_root_is_asked_for_its_delivery_verdict`.

**Rot ohne den Fix** (beide Enden getrennt mutiert, DEC-0060 Regel 4):
- Aufruf aus dem Anforderungspfad entfernt → `test_approvals_dispatch.py::test_a_hypothesis_cannot_be_given_a_scope_approval` („DID NOT RAISE ApprovalError")
- Urteil um eine Ausnahme `item_type in ("HYP", "SR")` erweitert → zusätzlich
  `test_approvals_dispatch.py::test_no_item_type_can_be_approved_on_a_kind_that_commits_no_edge`
- `delivery_roots` durch `{"PR"}` ersetzt → `test_report.py::test_a_task_under_every_kit_root_is_asked_for_its_delivery_verdict`

**Nicht geschlossen und benannt:** ein Paar, das die Tabelle FÜHRT, verspricht nur die KANTE, nicht
dass sein Gegenstand den Inhalt des Items beschreibt — `PROC/scope` und beide `delivery`-Gegenstände
decken ein Feld ihres Typs oder keines. Das ist die alte, an `_SCOPE_FIELDS` niedergeschriebene
Enge; diese Runde rührt sie nicht an, und der Docstring des neuen Wächters sagt das ausdrücklich.

## 3. BUG-0085 — ein gesanktionierter Weg für den gerenderten Bericht

**Gebaut.** `staging.freeze_report(state, staging_key, subject_id, source_name)` als VIERTE
Freeze-Operation — damit war sie am Tag ihrer Entstehung auf der Kommandozeile, weil
`cli.FREEZE_OPERATIONS` Name, `--help` und Body-Vertrag aus der Signatur ableitet
(`freeze_parameters`). Der Report-Writer rendert weiter nach `staging/<TSK-ID>/<name>` (rc 0,
unverändert), `python scripts/harness.py freeze-report` legt die Bytes in `reports/` ab.

Vier Eigenschaften, die aus dem Kopieren eine Zustandsänderung machen:
- der gefilte Pfad wird an `evidence_refs` des Gegenstands angehängt, WENN dessen Feldvertrag
  dieses Feld führt (abgeleitet aus `DECLARED_REQUIRED_FIELDS`, heute die `EXP` — genau das Feld,
  auf dem `gate_memory_complete` den Merge blockt). Für einen Gegenstand ohne dieses Feld (die `RQ`
  eines Förderberichts) sagt die Ausgabe, dass NICHTS die Bindung trägt, statt sie anzudeuten;
- ein Projekt ohne dieses Fach wird verweigert statt beschenkt (das Fach ist eine Kit-Entscheidung;
  `report_lint.py` liefert nur das research-Kit);
- ein bereits abgelegter Bericht wird NIE überschrieben — ausgeliefertes Material ist die Klasse,
  die DEC-0056 (c) auf voller Sorgfalt hält; die Verweigerung lässt die gestagten Bytes stehen;
- der Name des Schreibers bleibt erhalten, weil ihn etwas LIEST: `report_lint.py` findet einen
  Bericht an seiner POSITION und druckt seinen Namen an jedem Finding.

`layout.kernel_written_subtrees` fragt jetzt auch `staging.reports_dir`, damit das Fach als
kernel-geschrieben deklariert ist statt als Kit-Dokument ohne Schreiber.

**Rot ohne den Fix** (Klon, `"report": staging.freeze_report` aus `FREEZE_OPERATIONS` ausgetragen
und der Kit-Stempel im Klon erneuert, damit der Scaffold nicht schon an der Signatur scheitert):
`tools/test_research_chain.py::test_a_rendered_report_reaches_the_tray_through_the_kernel` — rc 2
mit einer Befehlsliste ohne `freeze-report`.
Grün misst derselbe Test die ganze Kette an echten Prozessen im gescaffoldeten Projekt:
Werkzeug-Schreibzugriff auf das Fach rc 2 (bleibt richtig), auf `staging/` rc 0, `freeze-report`
rc 0, Datei im Fach, gestagte Kopie verbraucht, `evidence_refs` gesetzt, `report_lint.py` findet
den Bericht unter seinem Namen, Merge blockt danach nicht mehr auf `ANALYZED without evidence_refs`.
Einheitsebene: `test_staging_cli.py::test_a_report_is_filed_by_the_kernel_and_never_overwrites_one`,
`::test_a_report_for_a_subject_without_the_field_is_filed_and_says_so`,
`::test_a_project_whose_kit_ships_no_reports_tray_is_refused_rather_than_given_one`.

**Der Stolperdraht der Suite hat gegriffen und wurde bedient, nicht umgangen:**
`test_every_caller_that_composes_a_staged_path_has_an_escape_battery` wurde rot, weil
`freeze_report` `contained_child` aufruft; die abgeleitete Escape-Batterie
(`test_no_freeze_parameter_can_reach_outside_the_state_root`) deckt alle drei `str`-Parameter des
neuen Kommandos ab, und die Fixture legt das `reports/`-Fach an — sonst wäre das Kommando
stillschweigend aus beiden Parametrisierungen gefallen.

**AC-2 von BUG-0085 ist NICHT erfüllt und liegt bei Stream E** (§6/§17 nennen den Weg nicht) —
siehe Seam-Items. H94 steht deshalb als „offen, nur noch die Verfassungszeile".

## 4. FR-0040 — die Evidenz erklärt ihren Lauf

**Gebaut.** `EVD` bekommt zwei OPTIONALE Felder: `run_command` (die ausgeführte Zeile) und
`run_scope` (geschlossene Vokabel `full` | `selection`, über `_CLOSED_VOCABULARY`). Sie sind EIN
Satz und werden gemeinsam oder gar nicht erklärt — `capture` verweigert die Hälfte. Auf der
Kommandozeile: `--run-command` / `--run-scope`; unbeantwortet werden die Schlüssel weggelassen
statt als `null` geschrieben.

**Die Regel am Merge:** `report._delivery_evidence` lässt einen PASS, der sich als `selection`
erklärt, nicht mehr als Lieferurteil durch. Ein FAIL aus einem Teillauf bleibt ein Fail — die
Asymmetrie ist das Argument: ein Lauf über einen Teil der Arbeit kann einen Defekt ZEIGEN, aber
nicht seine Abwesenheit.

**Rot ohne den Fix** (beide Hälften getrennt entfernt):
- `tools/test_report.py::test_a_pass_from_a_partial_run_is_not_merge_evidence_and_a_fail_still_is`
- `tools/test_staging_cli.py::test_cli_evidence_records_the_run_behind_the_verdict_or_neither_half_of_it`

**Offen und als H108 benannt:** eine Evidenz, die GAR NICHTS erklärt, zählt weiter wie bisher. Die
Pflicht lässt sich auf `EVD` nicht nachträglich erzwingen — gemessene Kosten stehen im DEC-Entwurf.

### DEC-Entwurf zu FR-0040 (vom Lead zu erfassen, FR-0040: „DEC first")

```
title: Eine Evidenz erklaert ihren Lauf -- Umfang und Befehl werden Vertragsfelder von EVD,
  optional getragen und am Merge gelesen; die Pflicht bleibt eine Nutzerentscheidung

context: 'FR-0040 (TSK-0069 Seitenpruefung N7). GEMESSEN: REQUIRED_FIELDS["EVD"] nennt kind,
  related, result, summary, artifact_refs -- kein Feld nennt den Befehl, den Umfang oder die
  Auswahl des Laufs, also ist ein PASS aus `pytest -k eine_sache` von einem PASS ueber die ganze
  Suite nicht unterscheidbar. Zugleich behaupteten zwei Stellen das Gegenteil: der Kommentar an
  `backlog_types.EVIDENCE_RESULTS` ("spec II.10a already rules that a partial run is not merge
  evidence") und der Verweigerungstext von `gate_git._refuse_unless_the_item_is_green` ("spec
  II.10a: a partial run is not merge evidence either") -- zwei Prosa-Zusagen ohne Leser.
  KOSTEN DER PFLICHT, gemessen statt vermutet: (a) EVD ist ein IMMUTABLE_TYPE, kein Kommando
  aendert ein Feld daran, und ein Pflichtfeld gilt fuer GESPEICHERTE Items
  (DECLARED_REQUIRED_FIELDS speist die Feld-Pflichtschleife des Validators) -- allein dieses
  Repository haelt 76 aktive EVD-Datensaetze (2026-09-02), von denen jeder am Tag der Pflicht ein
  Validator-Error waere, den kein Kommando repariert, und gate_memory_complete blockt darauf jeden
  Merge und Push; (b) die Pflicht stattdessen an die BEFEHLSZEILE zu haengen (required=True) macht
  jede ausgelieferte Rollen- und Verfassungszeile falsch, die `harness.py evidence` ohne die Flags
  lehrt -- in allen drei Kits.'

decision: '(a) EVD traegt zwei OPTIONALE Vertragsfelder: `run_command` (die ausgefuehrte Zeile,
  woertlich) und `run_scope` aus der geschlossenen Vokabel {full, selection}. Sie sind EIN Satz:
  `capture` verweigert eine Haelfte ohne die andere, denn ein Umfang ohne Befehl ist eine
  Behauptung ohne Beleg und ein Befehl ohne Umfang ein Datensatz, den der Merge nicht lesen kann.
  (b) Ein PASS, der sich als `selection` erklaert, ist KEIN Lieferurteil (report._delivery_evidence)
  -- ein FAIL aus einem Teillauf bleibt eines. Die Asymmetrie ist die Begruendung: ein Lauf ueber
  einen Teil der Arbeit kann einen Defekt zeigen, nicht seine Abwesenheit. (c) Der Kernel LEITET
  den Umfang NICHT aus der Befehlszeile ab: was ein Volllauf ist, ist eine Tatsache ueber den
  Testlaeufer des Projekts, nicht ueber eine Zeichenkette -- eine Liste von pytest-Flags waere eine
  Regel ueber EINEN Laeufer in einem Kernel, den drei Kits teilen. Die Erklaerung gehoert der Rolle,
  der Befehl ist das, woran ein Auditor sie prueft. (d) Eine Evidenz, die GAR KEINEN Umfang
  erklaert, behaelt den heutigen Stand. Ob die Erklaerung Pflicht wird -- und damit welche der
  beiden gemessenen Kosten das Projekt traegt -- ist eine Nutzerentscheidung und steht als H108 in
  docs/POST_V2_WISHLIST.md.'

consequences: 'Die beiden Prosa-Zusagen im Kontext sind fuer einen ERKLAERTEN Teillauf jetzt wahr
  und fuer eine schweigende Evidenz weiterhin zu stark -- der Satz in gate_git gehoert den Hooks
  und ist ein Seam-Item. Rollen- und Verfassungstexte, die `harness.py evidence` lehren, sollten die
  beiden Flags nennen (Seam-Item Stream E); ohne sie funktioniert das Kommando unveraendert.
  Nachbarn: DEC-0050 (Testumfang je Runde -- diese Felder sind das, was ihn ueberhaupt
  protokollierbar macht), FR-0057 (dieselbe Frage auf der Kit-Seite), H108.'

source: FR-0040 (Nutzerurteil 2026-09-02 "JA, BAUEN -- DEC first"); Messungen der Runde TSK-0106
  (Stream F), Protokoll unter project_memory/staging/TSK-0106/
```

---

## Seam-Items — Texte, die diese Runde NICHT geschrieben hat (Stream E bzw. Hook-Eigner)

Wörtlich, zum Übernehmen; die Runde hat sie nur gemessen.

**S1 — alle drei Verfassungen, §2 (die Kommandoliste).** Die Aufzählung „today that is `doctor`,
… `freeze-architecture`, `freeze-wireframe`, `freeze-design`, `migrate`, …" ist unvollständig.
Einfügen nach `freeze-design`:

> `freeze-report`,

Betroffen: `team-kits/dev-team/constitution/AGENTS.md`, `team-kits/office-team/constitution/AGENTS.md`,
`team-kits/research-team/constitution/AGENTS.md` (Zeile 30 in der research-Fassung).

**S2 — research-Verfassung §6, Zeile der Report-Writer-Zuordnung** (`reports/EXP-*.{tex,pdf,html}`,
`reports/fzulg_application_RQ-*.md`). Anzufügen:

> Rendered into `project_memory/staging/<TSK-ID>/` and filed with `python scripts/harness.py
> freeze-report` (stdin body: `staging_key`, `subject_id`, `source_name`); the tray itself stays
> closed to the write tools, and a report already filed is never overwritten.

**S3 — research-Verfassung §17.** Anzufügen:

> A report reaches `project_memory/reports/` only through `freeze-report`, which appends its path
> to the experiment's `evidence_refs` -- the field the merge is blocked on. Render under a name
> that says which run it is: a second file of the same name is refused, not replaced.

**S4 — Rollentext des Report-Writers** (research-Kit): dieselbe Zeile wie S2, plus der Hinweis, dass
der Bericht VOR dem Ablegen gelintet wird (`scripts/report_lint.py` liest das Fach nach dem
Ablegen ebenfalls).

**S5 — jeder Rollentext, der `harness.py evidence` lehrt** (QE/Reviewer in allen drei Kits):

> Record what you ran: `--run-command "<the exact line>" --run-scope full|selection`. A passing
> `selection` is recorded and does not open a merge; a failing one still closes it.

**S6 — Hook-Eigner, nicht Stream E:** `team-kits/{dev,research}-team/hooks/gate_git.py`,
`_refuse_unless_the_item_is_green`, Verweigerungstext „(spec II.10a: a partial run is not merge
evidence either)". Dieser Satz war bis zu dieser Runde eine Zusage ohne Leser; er ist jetzt für
einen ERKLÄRTEN Teillauf wahr und für eine schweigende Evidenz weiterhin zu stark. Vorschlag:

> (spec II.10a: a run that declares itself a selection does not open a merge -- one that declares
> no scope is not distinguished, H108)

---

## Was nicht geschlossen wurde, und warum — benannt statt still

1. **Punkt (5) der Auftragsliste ist nicht angefasst** (FR-0017 Gliederungsknoten, FR-0018
   Dubletten-Hinweis, FR-0037 Pfadlängen-Warnung, FR-0039 INV-Produzent, FR-0054 `related_sr`,
   FR-0067 Ersetzen/Löschen in Kit-Dokumenten). Der Auftrag erlaubt das ausdrücklich („STOP after
   (1)–(3) + (4) and hand over; say what the smallest useful first half was"). Diese vier Punkte
   SIND die kleinste nützliche Hälfte: sie hängen aneinander (der von H92 empfohlene Ausweg ist
   H93, der Bericht ist die Bedingung, an der die research-Kette endet), und sie berühren genau die
   Dateien, die ein zweiter Halbsatz noch einmal berühren würde. FR-0054 und FR-0037 wären klein,
   aber FR-0054 (`related_sr`) fasst dieselbe Ursprungsprüfung an, die diese Runde gerade umgebaut
   hat, und FR-0067 ist eine eigene Sicherheitsabwägung — beides in derselben Übergabe hätte den
   Seam der Merge-Runde verbreitert, ohne die Gruppe zu schließen.
2. **H108** (Evidenz ohne Umfangserklärung) — mit Mechanismus, gemessener Kette, Begrenzung und
   Urteil in der Löcherliste, dazu der DEC-Entwurf oben. Zur Abnahme durch den Nutzer.
3. **H94 bleibt offen**, aber nur noch als Verfassungszeile (S2/S3). Der Weg existiert und ist
   gemessen; was fehlt, ist, dass §6/§17 ihn NENNEN.
4. **Die Enge von `_SCOPE_FIELDS`** (ein gelistetes Paar verspricht die Kante, nicht die Deckung
   des Inhalts) — alte, benannte Enge, von dieser Runde nicht berührt und im Docstring des neuen
   Wächters ausdrücklich ausgenommen.
5. **`_hangs_from` behält sein `any`** — es beantwortet die andere Frage (Erreichbarkeit, für die
   Bindung einer Evidenz an ihre Wurzel). Die beiden zusammenzulegen wäre dieselbe Verwechslung in
   die andere Richtung.
6. **Die Testnamen, die die Löcherliste in Backticks nennt, prüft der Stolperdraht NICHT.**
   `test_gates._hole_entries`-Leser (`test_every_test_the_hole_list_names_is_one_that_exists`) liest
   nur punktlose Spannen und löst sie gegen `test_gates.py` auf; meine Zitate sind
   modulqualifiziert (`test_kernel.test_…`) und tragen darum einen Punkt. Sie sind von Hand gefahren
   und stimmen — geprüft wird das von nichts.

## Läufe (Worktree, provisorischer Stempel 2026.09.02-12 auf allen drei VERSION-Dateien)

| Lauf | Ergebnis |
|---|---|
| `ruff check .` | All checks passed |
| `tools/validate.py` | all structural checks passed |
| `test_kernel + test_state + test_report + test_approvals_dispatch + test_backlog_types + test_staging_cli + test_repo_hygiene` | 585 passed (4:37) |
| `test_research_chain + test_e2e` | 30 passed (2:55) |
| `test_hooks_v2 -k "approval or dispatch or validate"` | 481 passed, 1651 deselected (2:53) |
| `test_board + test_shortening_net + test_context_budget + test_disposition + test_schemas + test_presets + test_gaplog + test_role_contracts` | 233 passed (2:56) |
| `.claude/hooks/test_gates.py -k "hole or measurement or reference"` (im Worktree) | 8 passed (1:56) |
| `test_hooks + test_kitupdate + test_reference_skills + test_migrate` | siehe Nachtrag unten |

Die Suiten-Auswahl ist aus den geänderten Dateien und ihren Lesern abgeleitet (DEC-0060 Regel 2),
nicht aus dem Thema; `test_shortening_net`/`test_context_budget` sind mitgefahren, weil gepinnte
Dateien per Konstruktion betroffen sind (DEC-0060 Regel 1). Die volle Suite gehört der Merge-Runde
(DEC-0050).

---

# Fortsetzung nach dem Nutzer-Stopp (zweiter Lauf, 2026-09-02)

## Was ich vorgefunden habe

Der Arbeitsbaum war **byte-identisch mit `stream-kernel.patch` (12:24)**: `git diff HEAD` neu
erzeugt und gegen den Patch gediffed — 1703 Zeilen, kein Unterschied. Seit dem Patch ist also
nichts mehr in den Baum gelaufen; das Protokoll oben beschreibt den Baum korrekt.

**Was das Protokoll oben NICHT enthält, obwohl es passiert ist:** seine Läufe-Tabelle endet mit
„`test_hooks + test_kitupdate + test_reference_skills + test_migrate` | siehe Nachtrag unten" —
und es gibt keinen Nachtrag. Das Ergebnis dieses Laufs liegt im Scratch (`hooks-run.txt`, 13:45):
**2 failed, 898 passed, 13 skipped**. Beide Fehlschläge sind echt und gehören zu Punkt (3) des
ersten Laufs:

1. `test_hooks.test_every_evidence_command_a_text_spells_names_every_argument_the_cli_requires` —
   `staging.py` buchstabierte in der Verweigerung „dieses Projekt hat kein `reports/`-Fach" eine
   `evidence`-Zeile mit nur `--artifact-ref`. Der Parser verlangt vier weitere Argumente; die
   Verweigerung schickte eine Rolle also auf eine Befehlszeile, die argparse ablehnt.
   **Behoben** (die Zeile nennt jetzt jedes Pflichtargument), gemessen: vorher rot, nachher grün.
2. `test_hooks.test_every_span_that_presents_the_command_surface_names_all_of_it` — mit
   `freeze-report` wächst die Kommandofläche, und jede Aufzählung, die sie präsentiert, ist damit
   unvollständig. Fünf Fundstellen: drei Verfassungen, `README.md` — und `kernel/cli.py`.
   **Der Kernel-Anteil ist behoben** und war ein Nebeneffekt: ein neuer Kommentar im
   `main()`-Block schrieb `` `capture` `` in Backticks, womit der Block drei Kommandonamen führte
   und über die Schwelle des Lesers rutschte („ein Block, der drei nennt, präsentiert die
   Fläche"). Der Kommentar zeigt jetzt auf die Codestelle (`state.capture_preflight`) statt auf
   das Kommando — genauer und ohne Nebenwirkung. **Die vier übrigen Fundstellen liegen außerhalb
   des `allowed_scope` dieser Aufgabe** und sind unten als Naht S1 benannt; die Suite bleibt bis
   dahin an dieser Stelle rot. Mit `verify-invariants` und `revise-document` (unten) fehlen den
   vier Texten jetzt **drei** Kommandos, nicht eines.

## Was ich geprüft habe

Jede Behauptung des ersten Protokolls gegen den Baum: `origin_root_conflict` samt beider Aufrufer,
`_assert_the_pair_commits_an_edge`, `freeze_report` + `FREEZE_OPERATIONS` + `layout`,
`RUN_SCOPES`/`RUN_RECORD_FIELDS` samt CLI-Flags und `_delivery_evidence`. Alles gebaut wie
beschrieben, alle genannten Tests existieren und laufen grün. Die roten Messungen des ersten Laufs
habe ich nicht wiederholt (sie sind protokolliert); die zwei roten Tests oben waren die einzige
Abweichung zwischen Protokoll und Baum.

## Punkt (5) der Auftragsliste — gebaut

Alle sechs. Rot-Rig: `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0106/redrig2/` (Kopie von
`team-kits/` + `tools/` außerhalb des Repos; `sync_rig.py` setzt zurück, `mut67.py`/`mutate.py`
setzen je eine Mutation, `run_red.py` fährt Mutation + Auswahl und protokolliert das Urteil).

### FR-0037 — die Pfadlängen-Warnung des Validators

`lock.PORTABLE_PATH_MAX_CHARS = 240` (die Zahl an genau einer Stelle, neben `ext_path`, weil dort
das Langpfad-Wissen liegt) und `report._check_portable_path_budget`. **Eine** Warnung für den Baum
statt einer je Datei, und gelesen wird nur, was der Scan ohnehin öffnet (aktive Items,
Staging-Schlüssel, Leases) — ein Render tief in einem Staging-Verzeichnis ist der benannte blinde
Fleck und wird in derselben Prüfung mitgemessen.

Rot ohne den Fix (drei Mutationen, jede einzeln):
`test_report.test_a_state_tree_past_the_portable_path_limit_is_warned_once` fällt, wenn der Aufruf
fehlt, wenn der Befund ein `error` statt einer `warning` ist, und wenn er je Datei statt einmal
je Baum kommt.

### FR-0054 — `related_sr`, optional, auf Wurzelzugehörigkeit geprüft

`OPTIONAL_FIELDS["BUG"] += ("related_sr",)` und der Name in `_BINDING_FIELD_NAMES` — damit ist es
ein Bindungsfeld, und der Systembaum hängt den Bug unter die SR statt unter die Wurzel, ohne dass
im Renderer ein Fall dazukommt (die Platzierungsregel „tiefster auflösbarer Elternteil" macht es).
`report._check_bug_system_link` beurteilt das Feld über `origin_root_conflict` — also auf
**Zugehörigkeit** und nicht nur auf Existenz; das ist der Rest, den FR-0054 in seinem eigenen Text
als „nicht wiederholen" benennt (`related_pr`/`target_pr` prüfen nur Existenz).

Rot ohne den Fix (drei Mutationen): ohne das Bindungsfeld fällt
`test_board.test_a_bug_that_names_a_system_requirement_hangs_under_it_rather_than_under_the_root`;
ohne den Aufruf und mit einer reinen Existenzprüfung statt der Zugehörigkeit fällt
`test_report.test_a_bug_may_name_the_system_requirement_it_hit_but_only_under_its_own_root`.

**Bewusst abgewichen:** die Index-Zeile bekommt `related_sr` NICHT. Gemessen:
`state._regenerate_index_locked` schreibt je Item `id, type, title, status, revision,
approval_ref` (+ `blocked_by`) und **kein einziges Bindungsfeld** — auch `related_pr`,
`derives_from` und `target_pr` stehen dort nicht. Das Board liest die Item-Körper direkt, die
Gruppierung braucht die Index-Zeile also nicht; ein einzelnes Bindungsfeld dort wäre eine Form,
die der Index für keinen anderen Typ hat.

### FR-0018 — der weiche Dubletten-Hinweis

`report.similar_items` + `DUPLICATE_HINT_SIMILARITY` + `DUPLICATE_HINT_LIMIT`, gedruckt von
`cli` beim `capture` auf **stderr**, nach der Id auf stdout, ohne Exit-Code-Änderung, und BERECHNET
VOR dem Anlegen (das neue Item kann sich nicht selbst treffen).

Welche Felder den Inhalt ausmachen, ist nicht neu entschieden: `HASHED_FIELDS` ist die Antwort des
Kernels darauf („die Felder, deren Änderung eine Freigabe entwertet"). Ein Typ ohne diese
Definition bekommt keinen Hinweis statt eines geratenen.

**Die Schwelle ist gemessen, nicht gewählt** (beide Enden, an echten Daten — dem Bestand dieses
Repos, 97 Items der Typen mit `HASHED_FIELDS`):

| Messung | n | Ergebnis |
|---|---|---|
| ehrliche Nachbarpaare (alle Paare gleichen Typs) | 3686 | Maximum **0.314**, 99.9-Perzentil 0.256 |
| Wiedervorlage, 70 % der Wortwahl behalten | 97 | Minimum **0.597** |
| Wiedervorlage, 60 % der Wortwahl behalten | 97 | Minimum **0.493** |
| Wiedervorlage, 50 % der Wortwahl behalten | 97 | Minimum 0.393 |

Zwischen 0.314 und 0.493 liegt ein leeres Band; `0.45` liegt darin. Eine Schwelle darunter
(0.25 gemessen) macht den ersten Teil des Tests rot (Fehlalarm auf zwei verschiedenen
Requirements), eine darüber (0.95) den zweiten (echte Wiedervorlage stumm) — beides gefahren.

Rot ohne den Fix (vier Mutationen):
`test_report.test_the_duplicate_hint_stays_quiet_on_ordinary_neighbours` (beide Bandkanten),
`test_report.test_the_duplicate_hint_covers_every_type_whose_content_the_kernel_defines`
(Aufzählung `("PR","SR")` statt der Ableitung),
`test_staging_cli.test_capture_names_the_neighbours_it_found_and_captures_the_item_anyway`
(CLI-Anbindung entfernt).

### FR-0039 — Produzent für `INV.verified` und der Merge-Blocker

Drei Teile:
* `report.invariant_check_resolution` — `check.ref` als `<pfad>::<name>`, relativ zur
  Projektwurzel, aufgelöst durch **Parsen** (AST) statt durch Fahren. Drei Antworten: aufgelöst,
  nachweislich nicht aufgelöst, **unentscheidbar** (siehe unten).
* `state.record_invariant_verification` — der Produzent. **Kein `transition`**, und das ist die
  Entscheidung: jeder andere Status hält eine Entscheidung fest, dieser eine Messung des
  Repositorys; der Aufrufer übergibt keinen Status. Beide Richtungen: verschwindet der Test, geht
  das Item zurück auf `unverified`.
* `report._check_invariant_checks` — ein nicht auflösbarer Check ist ein **Error**, und damit der
  Merge-Blocker, den FR-0039 verlangt: `gate_memory_complete.state_errors` hält jeden Push auf
  Validator-Errors an. Ein auflösbarer Check bei `unverified` ist eine **Warnung** mit dem Befehl
  als Abhilfe.
* Kommandozeile: `verify-invariants [INV-nnnn ...]`, Exit 1 solange einer unaufgelöst ist.

Am **laufenden Hook** gemessen, in beide Richtungen:
`test_hooks.test_an_invariant_whose_check_names_no_test_blocks_the_merge` — Merge rc 2 mit der
genannten Datei im Text, dann dieselbe Testdatei geschrieben und derselbe Merge rc 0.

Rot ohne den Fix (drei Mutationen): Befund abgeklemmt →
`test_report.test_an_invariant_whose_check_resolves_to_no_test_is_an_error_and_a_resolving_one_is_not`
UND der Hook-Test oben; Namensauflösung blind → `test_state.test_an_invariant_is_verified_by_its_
check_and_unverified_when_it_stops_resolving`; Produzent nur vorwärts → derselbe.

**Eine Ratsche musste ich erweitern, und das ist protokollpflichtig.**
`test_approvals_dispatch.test_no_direct_status_write_can_produce_a_status_an_approval_commits`
liest jeden direkten Status-Schreiber im Kernel und verlangt, dass sein Wertebereich aus einer
Kernel-Karte begrenzbar ist. Der neue Produzent war ihr eine unbegrenzbare Form — die Verweigerung
selbst nennt „add the shape to `_possible_statuses`" als einen der drei zulässigen Wege. Die neue
Form ist ein **Subscript auf einen Modulkonstanten von `kernel.state`** (Name in Großschreibung,
im Modul veröffentlicht, alle Werte Strings); der Index wird bewusst nicht gelesen. Dass die
Ratsche danach noch Zähne hat, ist gemessen: derselbe Schreiber, der seinen Wert aus einer
**lokalen** Liste nimmt, ist weiterhin ein Befund.

### FR-0017 — Gliederung des Backlogs, als Attribut, mit gemessener Entscheidung

FR-0017 lässt die Designfrage ausdrücklich offen („echter inhaltsloser Heading-Knoten als Parent
vs. ein Area-Path-artiges Attribut"). Ich habe sie **messend** entschieden:

**Der Knoten-Weg ist kein Kernel-Weg.** Ein Typ in `ACTIVE_DIRS` ist zugleich ein Präfix in
`guard_no_adhoc.ITEM_TYPES` — und dieses Konstant liegt in `team-kits/{dev,office,research}-team/
hooks/guard_no_adhoc.py`, also im `forbidden_scope` dieser Aufgabe. Gemessen im Rot-Rig: ein
zusätzlicher Typ `HDG` in `ACTIVE_DIRS` macht
`test_hooks.test_no_adhoc_covers_every_item_type` rot („Extra items in the right set: 'hdg'"),
während `test_board` (78 Tests) und `test_backlog_types` grün bleiben — das Board rendert nur
Typen, deren Verzeichnis das Kit-Template ausliefert, und Templates sind ebenfalls verboten. Ein
Knotentyp ist also eine Änderung an drei Kit-Hooks, drei Template-Bäumen und drei Verfassungen;
ein Attribut kostet ein Feld und keine Datei außerhalb des Kernels.

Gebaut: `AREA_FIELD` (`area`), `AREA_SEPARATOR`, `AREA_MAX_DEPTH = 2`, `area_segments`, und
`UNIVERSAL_OPTIONAL_FIELDS` — ein Feld, das **jeder** von `capture` erzeugte Typ tragen darf, weil
Gliederung orthogonal zum Typ ist (eine Zweierliste „PR und SR" müsste für das nächste Kit wieder
geöffnet werden).

Der von FR-0017 zwingend verlangte Schutz gegen Über-Fragmentierung, in zwei Teilen und ohne jede
Zählschwelle:
* **Tiefe** wird beim `capture` verweigert (`AREA_MAX_DEPTH`), nicht hinterher gemeldet;
* **Wildwuchs** wird an dem Moment adressiert, den die Regel des Nutzers selbst nennt („ein neues
  Heading nur, wenn ein Requirement wirklich in keines passt"): `report.standing_areas`, gedruckt
  von `cli`, wenn ein Body eine Ebene nennt, die noch kein Item trägt. Keine Zahl trennt 1000
  Headings von 999 ehrlichen; was sie trennt, ist, ob der Schreibende die vorhandene Gliederung
  gesehen hat.

Rot ohne den Fix (drei Mutationen): `AREA_MAX_DEPTH = 9` →
`test_state.test_an_item_may_carry_an_outline_area_but_not_a_third_level`;
`UNIVERSAL_OPTIONAL_FIELDS = ()` →
`test_backlog_types.test_every_captured_type_declares_the_outline_field_and_none_declares_it_twice`
(dieser Test existiert, weil die erste Fassung des Feldes **unmessbar** war: `capture` speichert
auch ein nicht deklariertes Feld, der Vertrag war also durch nichts belegt);
Hinweis abgeklemmt → `test_staging_cli.test_capture_shows_the_outline_when_a_body_invents_a_new_level`.

### FR-0067 — `revise-document`: ersetzen und löschen, Stelle für Stelle

Eine **zweite** Route neben `apply-proposal`, kein erweiterter Vorschlag. Grund: die additive Karte
verspricht wörtlich „die Freigabe FÜGT nur HINZU — sie ändert nichts Bestehendes und löscht
nichts". Eine Route für beides müsste dieses Versprechen bedingt machen, und eine Zusicherung mit
Verzweigung neben dem Wert, den sie verneint, ist genau der Defekt, den Prüferbefund F2 gemessen
hat.

* `documents._spots` — jede Stelle, an der sich die Fassungen unterscheiden, **benannt**, mit
  altem und neuem Wert. Eine Stelle ist ein Pfad, den beide Dokumente benennen: ein Mapping-Key
  ist einer, ein Listeneintrag nicht. Listen werden in den drei eindeutigen Lesarten beurteilt
  (nur gewachsen → additiv; nur verloren → jede Streichung mit ihrem Wert; gleiche Länge → Stelle
  für Stelle). Eine Liste, die **gleichzeitig** gewinnt und verliert, wird verweigert: welcher
  Eintrag welcher wurde, wäre geraten, und eine Karte auf einer Vermutung zeigt dem Nutzer eine
  Änderung, die es nicht gibt.
* `documents.revision_plan` — dieselben drei Lesarten wie die additive Route (Daten, Skelett,
  doppelte Keys). Ersetzte Pfade werden geblankt wie ein Fill, gelöschte werden aus **beiden**
  Skeletten geschnitten (`_blanked_spans(..., cuts=...)`).
* `approvals.document_revision_subject_manifest` + `_document_revision_target_form` — die Karte.
  **Gelöschtes zuerst und als solches benannt** (ein ersetzter Wert ist danach noch im Dokument
  nachlesbar, ein gelöschter nirgends), und die Anzahl der Stellen ist durch das bestehende
  `MAX_PROPOSAL_CHANGES` begrenzt: darüber wird **verweigert**, nie zusammengefasst.
* `documents.apply_revision` + `cli revise-document` — dieselbe Reihenfolge wie `apply`
  (neu ableiten, Freigabe gegen das REKONSTRUIERTE Manifest, schreiben, zurücklesen, bei
  Abweichung die Originalbytes wiederherstellen).

**Sicherheitsabwägung nach DEC-0056 — der Fehler, den eine Rolle wirklich macht, nicht ein
Angriffspfad.** Zwei gemessene Fehler, beide beim Bauen aufgetreten und beide geschlossen:

1. **Die Karte verschwieg den neuen Wert.** Die Deskriptoren werden auf je eine Zeile gefaltet
   (`approvals._one_line(one, 120)`). Ein umgeschriebener Blockskalar — der Live-Fall vom
   2026-08-30 — ergab EINEN Deskriptor mit beiden Werten, und die Faltung schnitt ihn nach dem
   ALTEN Wert ab: die Karte zeigte, was verschwindet, und nicht, was kommt. Gemessen an
   `test_a_revision_may_rewrite_a_value_that_takes_several_lines`, bevor es den Fix gab. Jetzt ist
   eine Ersetzung **zwei** Deskriptoren („bisher …", „neu …"), jeder für sich gefaltet — und eine
   Ersetzung kostet damit zwei der Stellen, die eine Frage tragen darf, was sie zu lesen auch
   kostet.
2. **Ein Schnitt nahm einen Kommentar mit, ohne ihn zu zeigen.** Eine Streichung schneidet ihren
   Eintrag aus dem Zeilenvergleich (sonst wäre ihr eigenes Verschwinden ein „verlorene Zeile").
   Gemessen an einem Dokument mit einem Kommentar zwischen zwei Listeneinträgen: Streichung
   angenommen, Eintrag in der Karte, **Kommentar nirgends**. Jetzt werden die Kommentare ein
   zweites Mal auf den UNgeschnittenen Skeletten verglichen, und ein Kommentar, den das Dokument
   verliert, ist ein eigener Deskriptor („Kommentar entfällt: …") — gezeigt, gezählt, unterschrieben.

Rot ohne den Fix (sieben Mutationen, jede einzeln, alle rot):
`cuts = set()`, `fills` ohne `replace`, „nur-additiv" nicht verweigert, Listen-Mehrdeutigkeit
geraten, `MAX_PROPOSAL_CHANGES` abgeklemmt, Löschungen als Anzahl gerendert, und der Planwähler
fest auf die additive Route.
Betroffene Tests: `test_kernel.test_a_revision_writes_exactly_the_spots_the_card_showed_and_the_
other_route_refuses_it`, `test_kernel.test_a_revision_may_rewrite_a_value_that_takes_several_lines`,
`test_kernel.test_a_revision_the_kernel_cannot_name_spot_by_spot_is_refused` (beide Parameter),
`test_kernel.test_a_comment_that_a_deletion_would_take_with_it_stands_in_the_card`,
`test_kernel.test_the_two_document_routes_each_resolve_their_own_plan_on_the_command_line`,
`test_approvals_dispatch.test_a_revision_card_shows_every_spot_and_is_never_a_count`.

## Löcher

* **H109** — „sammelbar" ist geparst, nicht gefahren: ein `@pytest.mark.skip`-Test gilt als
  vorhanden. Gemessene Dreitabelle in der Löcherliste (Kernel sagt `verified`, der Läufer sagt
  „1 skipped").
* **H110** — einen Check, dessen Datei der Kernel nicht parsen kann, beantwortet er mit
  UNENTSCHIEDEN (Warnung, kein Blocker). Fail-closed wurde gemessen und **verworfen**: es sperrt
  jeden Merge jedes Projekts, dessen Tests nicht Python sind, ohne Ausweg.
* H108 steht unverändert aus dem ersten Lauf.

## Nahtstellen — Texte, die diese Runde NICHT geschrieben hat

Zusätzlich zu S1–S6 des ersten Laufs (unverändert gültig), und **S1 ist jetzt blockierend für die
Suite**:

**S1 (erweitert).** Die Kommandoliste in §2 aller drei Verfassungen und in `README.md` nennt jetzt
DREI Kommandos nicht: `freeze-report`, `verify-invariants`, `revise-document`. Solange sie fehlen,
ist `test_hooks.test_every_span_that_presents_the_command_surface_names_all_of_it` rot. Einzufügen
in dieselbe Aufzählung:

> `freeze-report`, `verify-invariants`, `revise-document`,

Betroffen: `team-kits/dev-team/constitution/AGENTS.md`,
`team-kits/office-team/constitution/AGENTS.md`,
`team-kits/research-team/constitution/AGENTS.md`, `README.md`.

**S7 — Rollentext des Bookkeepers/Product-Editors (office) und jeder Rolle, die ein Kit-Dokument
besitzt.** Anzufügen:

> Correcting or removing something a kit document already records has a route now:
> stage the document as it should stand and run `python scripts/harness.py request-approval
> document_revision --kit-document <file> --proposal staging/<TSK-ID>/<file> --reason "<why>"`,
> then `python scripts/harness.py revise-document` with the same flags. Every replaced and every
> deleted spot stands in the approval question with its old and its new wording -- the user
> approves those spots and nothing else. Additions keep going through `apply-proposal`, whose
> question promises that nothing existing changes.

**S8 — QA-/Architektentext (dev, research), wo `INV` gelehrt wird.** Anzufügen:

> An invariant's `check.ref` names a test as `<path>::<name>`, relative to the project root, and
> `python scripts/harness.py verify-invariants` is what records `verified` -- nobody writes that
> status by hand. Until the named test exists, the state validator reports the invariant as an
> error and the merge stays closed.

**S9 — PM-Rollentext aller drei Kits, wo `capture` gelehrt wird.** Anzufügen:

> `capture` prints two hints on stderr and refuses nothing for them: similar existing items of the
> same type, and -- when the body names an `area` nobody uses yet -- the outline the backlog
> already has. An `area` is at most two levels (`Dokument/Überschrift`); a third is refused.

## Läufe dieses zweiten Laufs

Stempel: **2026.09.02-15** auf allen drei `VERSION`-Dateien (provisorisch). Dreimal gestempelt,
weil dreimal danach noch eine Kernel-Datei angefasst wurde — der Scaffold prüft den Inhaltshash
gegen den Stempel und verweigert sonst die Installation. Das ist die gemessene Reihenfolge:
**stempeln ist der letzte Schritt vor dem Paket, nicht der erste nach dem Bauen.**

| Lauf | Ergebnis |
|---|---|
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |
| `test_kernel + test_approvals_dispatch + test_state + test_report + test_staging_cli + test_backlog_types + test_board + test_repo_hygiene` | **654 passed** (4:51) |
| `test_research_chain + test_e2e + test_schemas` | 59 passed (2:36) |
| `test_shortening_net + test_context_budget + test_presets + test_disposition + test_gaplog + test_role_contracts` | 154 passed + 3 rot → behoben, danach grün (siehe unten) |
| `test_hooks_v2 -k "approval or dispatch or validate or document"` | 488 passed, 1 rot (Stempel) → nach dem Neustempeln grün |
| `test_hooks` (voll) | Lauf 3: 892 passed, 9 failed — 8 davon der veraltete Stempel (nach dem Neustempeln alle 8 grün, 10:23), 1 die Naht S1 |
| `.claude/hooks/test_gates.py -k "hole or measurement or reference"` | 8 passed (2:20) |

**Die drei roten Ratschen dieses Laufs waren echte Befunde und sind Teil der Lieferung:**

1. `test_board.test_no_kernel_writer_of_a_rendered_file_leaves_the_board_behind` — `apply_revision`
   schreibt eine Datei und regeneriert kein Board. Richtig so (ein Kit-Dokument hat keine Karte),
   also steht es jetzt mit seinem Grund in `_WRITERS_THE_BOARD_DOES_NOT_RENDER`, wie sein
   additiver Zwilling.
2. `test_presets.test_every_target_form_names_a_live_apr_kind` — eine neue Karte darf nur mit
   einer Messung dessen ankommen, was sie rendert. Nachgeliefert:
   `test_kernel.test_the_question_a_document_revision_asks_shows_every_field_the_hash_covers`
   (jeder gehashte Wert steht in der Frage, und die Frage ist deterministisch).
3. `test_role_contracts` (zwei Tests) — mein zweites Dokument-Kind machte `kit_document` und
   `proposal` zu „von mehr als einem Kind getippten" Werten, und der Leser, der auf ALLE Anker
   zugleich prüft, fand daraufhin in keinem Kit mehr einen Regelabschnitt: **0 statt ≥6**. Beides
   sind Pfade, keine Prosa — eine Regel über die SPRACHE eines Wertes hat über einen Pfad nichts
   zu sagen. Der Leser liest die Ausnahme jetzt aus dem laufenden Code (`_positioned_manifest_
   parameters`: ein Parameter, den ein Builder an `filed_position` gibt, ist eine Position), und
   die Zähne sind gemessen: mit `positions = set()` ist der Test wieder rot.

**Ein vierter Befund war ein Fehler von mir und ist behoben:** meine Einfügung in `test_kernel.py`
trennte einen `@pytest.mark.parametrize`-Dekorator von seinem Test — die neun Fälle des
Sicherheitstests des additiven Weges liefen dadurch gar nicht (`fixture 'what' not found`, ein
Collection-ERROR, kein stiller Ausfall). Der Dekorator sitzt wieder an seinem Test; `test_kernel`
ist mit 127 Tests grün.

## Was ich bewusst NICHT geschlossen habe, benannt

1. **Naht S1 hält die Suite rot.** Drei Verfassungen und `README.md` zählen die Kommandofläche auf
   und nennen `freeze-report`, `verify-invariants` und `revise-document` nicht. Alle vier Dateien
   liegen außerhalb des `allowed_scope`. Das ist kein Loch der Löcherliste (nichts setzt falsch
   durch), sondern eine Lieferbedingung der Merge-Runde: solange sie fehlt, ist
   `test_hooks.test_every_span_that_presents_the_command_surface_names_all_of_it` rot.
2. **FR-0017 bekommt KEINE Zählschwelle gegen Wildwuchs.** Gebaut sind die Tiefengrenze und der
   Hinweis im Moment der Erfindung. Eine Regel „höchstens N Bereiche" oder „ein Bereich mit nur
   einem Item ist ein Befund" wäre eine Zahl, die niemand begründen kann, und der zweite Fall ist
   der Normalzustand jedes wachsenden Backlogs (das erste Item einer neuen Ebene). Wenn der Nutzer
   eine harte Grenze will, ist das eine Entscheidung, keine Nacharbeit.
3. **FR-0054 ohne Index-Zeile** (Messung oben), und `related_pr`/`target_pr` behalten ihre alte
   Enge: nur Existenz, keine Wurzelzugehörigkeit. Diese Runde hat sie nicht angefasst — sie ist
   in FR-0054 als „L9-Rest" benannt und betrifft zwei Felder, deren Leser ich nicht vermessen habe.
4. **FR-0067 deckt keine Liste, die gleichzeitig gewinnt und verliert.** Verweigert mit Begründung
   statt geraten; die Rolle macht daraus zwei Schritte. Ebenso unangetastet: `apply-proposal`
   bleibt wortgleich, was es war.
5. **H108 (Evidenz ohne Umfangserklärung) bleibt offen** — Nutzerentscheidung, DEC-Entwurf oben.
6. **Die Ratschen-Erweiterung an `_possible_statuses`** ist eine Öffnung: ein Subscript auf einen
   Modulkonstanten von `kernel.state` gilt als begrenzt, ohne dass der Index gelesen wird. Gemessen
   ist, dass die Ratsche danach noch greift (lokale Liste → weiterhin Befund); nicht gemessen ist
   ein Fall, in dem ein Modulkonstant und eine lokale Variable denselben Großbuchstabennamen
   tragen — dafür ist die Namensform (Großschreibung + im Modul veröffentlicht) die Begrenzung.

## Nachtrag: Rate-Limit-Abbruch und der abschließende Volllauf

Der zweite Lauf wurde einmal durch das **Sitzungs-Rate-Limit** unterbrochen (kein Fehler, keine
Nacharbeit) — Stand zum Zeitpunkt des Abbruchs: alles gebaut und gemessen, der abschließende
`test_hooks`-Volllauf lief noch. Nach dem Zurücksetzen weitergemessen, nichts wiederholt.

**Abschlusslauf `test_hooks` (voll, nach dem letzten Stempel `-15`): 898 passed, 13 skipped,
3 failed** — und keiner der drei ist ein inhaltlicher Befund:

* `test_every_span_that_presents_the_command_surface_names_all_of_it` — die Naht S1 (drei
  Verfassungen + `README.md`, alle außerhalb des `allowed_scope`).
* zweimal `test_the_shipped_scaffold_records_the_trays_of_the_kit_it_installs[sh-…]` —
  `subprocess.TimeoutExpired` von `scaffold_team.sh` nach 600 s. Der Lauf brauchte insgesamt
  45:25 statt der sonst gemessenen ~24 Minuten, weil parallel ein zweiter pytest-Prozess auf
  derselben Maschine lief. **Isoliert nachgemessen: `-k "scaffold_records_the_trays"` → 4 passed
  in 5:45** (`_round-scratch/TSK-0106/scaffold-recheck.txt`). Maschinenlast, kein Defekt.

Damit ist der Stand des Pakets: **eine** rote Stelle in der Suite, und die ist die benannte Naht.

Übergabe: `_round-scratch/TSK-0106/stream-kernel.patch` (3974 Zeilen, 25 Dateien, keine neuen
Dateien; `project_memory/.audit/hook_events.jsonl` kommt darin nicht vor) und `git-status.txt`.

---

# Nacharbeit 1 (Pruefer-FAIL: B 4, M 3, N 7)

Rig dieser Runde: `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0106/rework1/` (ein Skript je
Befund, Pilotkopie `pilot-research/`); Rot-Rig weiterhin `.../redrig2/`.

## Rot-zuerst-Tabelle dieser Nacharbeit

| Befund | Mutation im Klon | Roter Test |
|---|---|---|
| B1 | zweiter Eintrag aus `DOCUMENT_WRITES` entfernt (deklariert, nicht registriert) | `test_hooks.test_every_route_the_kernel_has_into_a_kit_document_is_named_by_the_gate_that_refuses_one`, `test_kernel.test_a_generic_document_writer_is_named_only_for_the_documents_it_would_write` |
| B2 | `all` -> `any` in `_reaches_on_every_path` | `test_report.test_an_origin_whose_only_parent_hangs_from_two_roots_is_refused` |
| N3 | Zweigwahl zurueck auf `len(astray) == len(parents)` | derselbe Test |
| B3 | Listenzuwachs wieder als Anzahl | `test_kernel.test_a_revision_that_also_grows_a_list_shows_every_added_entry_and_no_count` |
| B4 | `refuted += resolved is not True` (Unentscheidbare zaehlen wieder mit) | `test_staging_cli.test_verify_invariants_records_what_the_check_resolves_to_and_exits_on_the_gap` |
| M1 | Scan parst wieder je Item | `test_report.test_one_scan_parses_each_test_file_once` |
| M2 (a) | Tokenizer zurueck auf die ASCII-Klasse | `test_report.test_the_duplicate_hint_reads_a_word_in_any_script_not_only_in_ascii` |
| M2 (b) | `DUPLICATE_HINT_MIN_WORDS = 0` | `test_report.test_the_duplicate_hint_says_nothing_about_items_too_small_to_compare` |
| N4 | Gliederungs-Hinweis wieder vor den Schreibvorgang | `test_staging_cli.test_capture_shows_the_outline_when_a_body_invents_a_new_level` |
| N5 | Baum ignoriert `area` wieder | `test_board.test_children_of_one_parent_stand_under_their_outline_area` |

## B1 - die zweite Route war deklariert und nirgends registriert

**Am INSTALLIERTEN Gate gemessen**, in einer Kopie des Pruefer-Piloten
(`rework1/pilot-research/`, Sonde `rework1/gate_probe.py`): `Write project_memory/methodology.yaml`

* vorher: rc 2, und der Text nennt „`apply-proposal` writes what a staged proposal ADDS (never a
  change, never a removal)" - `revise-document` kommt nicht vor;
* nachher: rc 2, und der Text nennt beide Routen woertlich.

Gebaut: zweiter Eintrag in `documents.DOCUMENT_WRITES`; der Uebersprung in `_owned_elsewhere`
liest die Kommandos dieses Moduls jetzt aus `DOCUMENT_WRITES` statt aus einem `== COMMAND`.

**Der erste Testversuch war eine Identitaet**, und das gehoert ins Protokoll: er las die Erwartung
aus derselben Registrierung, die er prueft - mit geloeschtem zweiten Eintrag verschwand die
Erwartung mit, und der Test blieb gruen. Die Erwartung kommt jetzt von der anderen Seite des
Moduls (`KIND_BY_COMMAND`: Kommando -> Freigabeart -> Plan). Drei Aufzaehlungs-Pins umgestellt:
die zwei vom Pruefer benannten und die `filing_plan.yaml`-Zeile, die beim Nachfahren auffiel.

## B2 / N3 - das `all` hatte keinen Test, und die Verweigerung widersprach sich

Der Aufbau, den es braucht: `HYP-0001` haengt an `RQ-0001` UND `RQ-0002`, `EXP-0001` hat **einen**
Elternteil `HYP-0001`. `origin_root_conflict` laeuft die Eltern des Ursprungs selbst ab, also
entscheidet das `all` erst am Grosselternteil. Der Docstring nannte einen Test, der eine Ebene
hoeher misst; er nennt jetzt beide und sagt, welcher was misst.

N3: welcher der zwei Saetze wahr ist, entscheidet jetzt, **wo die Pfade enden** (`root_id not in
tops`) statt wie viele Eltern abweichen - die Zaehlung sagte im Grosseltern-Fall beides zugleich
(„belongs to RQ-0001/RQ-0002, not to RQ-0001"). Der Satz spricht auch nicht mehr von „several
items", weil die Mehrdeutigkeit ueber dem Ursprung sitzen kann; nachgemessen mit der Sonde des
Pruefers (`verify/allany_probe.py`) gegen den nachgearbeiteten Kernel.

## B3 - die Karte zaehlte, waehrend sie versprach, nicht zu zaehlen

Gemessen (`rework1/b3_probe.py`): eine Revision, die `language` ersetzt und `instruments` wachsen
laesst, druckte „instruments: 3 Eintraege hinzu" - im selben Satz mit „jede betroffene Stelle
steht oben im Wortlaut, alt und neu, niemals als Anzahl". Jetzt ein Deskriptor je Eintrag,
gefaltet wie die zwei Ersetzungs-Deskriptoren; ueber `MAX_PROPOSAL_CHANGES` wird verweigert (mit
der Zahl), nie gekuerzt. Die additive Route bleibt unveraendert - ihre Karte sagt ausdruecklich
das Gegenteil zu.

## B4 - der Exitcode trug den H110-Zustand weiter

Gemessen (`rework1/b4_probe.py`): ein INV mit `tests/invariants.spec.js` -> `verify-invariants`
rc **1**, `validate` im selben Moment rc **0** mit einer Warnung. Jetzt zaehlt nur, was
nachweislich nicht aufgeloest ist; Unentscheidbare bekommen eine eigene Zeile, die H110 nennt, und
der Exitcode bleibt 0. `record_invariant_verification` gibt dafuer `(item, resolved, reason)`
zurueck - der dritte Zustand wird durchgereicht statt vom Aufrufer neu abgeleitet.

## M1 - der Validator parste je Invariante

Gemessen (`rework1/m1_time.py`, 30 INV auf eine 0,50-MB-Testdatei, je dreimal):

| | Lauf 1 | Lauf 2 | Lauf 3 |
|---|---|---|---|
| vorher | 6,89 s | 6,47 s | 6,14 s |
| nachher | 0,26 s | 0,22 s | 0,22 s |

Ein Cache `{abspath -> definierte Namen}` fuer die Dauer EINES `validate_state`-Laufs. Der Test
zaehlt `ast.parse`-Aufrufe statt Sekunden: eine Stoppuhr misst die Maschine, ein Aufrufzaehler die
Regel. Einzelabfragen (der Produzent) parsen weiter, weil dort eine veraltete Antwort teurer waere
als ein Parse.

## M2 - der Tokenizer war eine Alphabet-Aufzaehlung, und darunter lag ein zweiter Fehler

(a) Der Leser liest jetzt Buchstaben in jeder Schrift statt `a-z`. An der laufenden Funktion
gemessen: `Pruefung der Groesse` (mit Umlauten geschrieben) ergibt drei ganze Woerter statt
Fragmenten.

(b) **Bandmessung mit dem laufenden Tokenizer wiederholt** (98 Items, 3772 Paare, 2026-09-02):
ehrliches Maximum **0.314**; Wiedervorlage mit 70 % erhaltener Wortwahl min **0.597**, mit 60 %
min **0.493**. Das Band ist unveraendert, die Schwelle bleibt **0.45** - jetzt an dem Leser
gemessen, der laeuft.

(c) **Ein Fehlalarm, den (a) NICHT behebt und den ich beim Nachmessen fand:** zwei unverwandte
kurze Bugs („404 -> 200" und „500 -> 200") teilen `200` und die Severity und liegen bei **0.500**.
Ursache ist nicht das Alphabet, sondern die Groesse: ueber vier Woertern entscheidet ein einziges
geteiltes Wort. Am selben Bestand gemessen: das **kleinste echte Item hat 49** Inhaltswoerter, die
**kleinste Vereinigung eines ehrlichen Paares 93**, die Rauschfaelle liegen bei vier bis acht.
Dazwischen liegt ein sehr breites leeres Band; `DUPLICATE_HINT_MIN_WORDS = 20` liegt darin.

(d) **Die Fixtures waren kleiner als jedes echte Item** und sind jetzt so lang wie echte Prosa -
derselbe Defekt, der beim ersten Bau zwei verschiedene Requirements auf 0.429 gebracht hatte.

**Benannte Grenze (kein Loch, weil nichts falsch durchsetzt):** eine Schrift ohne Wortgrenzen
(Japanisch, Chinesisch) ergibt EIN Token je Phrase, bleibt damit unter dem Boden, und der Hinweis
schweigt fuer einen solchen Bestand. Stille ist die sichere Richtung; was das schloesse, waere ein
Segmentierer, und der gehoert nicht in einen Kernel, den drei Kits teilen. Im Test gemessen.

## M3 - FR-0040 hat einen erfassungsfertigen DEC-Koerper

`project_memory/staging/TSK-0106/dec-run-scope.json`, Felder wie `decisions/active/DEC-0060.yaml`.
**Erfassbarkeit gemessen**, nicht behauptet: gegen einen Wegwerf-State erfasst der Kernel den
Koerper als `DEC-0001 VALID` mit genau den fuenf Vertragsfeldern (`rework1/probe_dec.py`). Die
gebauten Stellen nennen bis zur Nummer diesen Pfad: `backlog_types.RUN_SCOPES` traegt den Zeiger,
`RUN_RECORD_FIELDS`, `state.capture_preflight` und `report._delivery_evidence` zeigen auf ihn.
Naht S10 ist inzwischen erledigt: erfasst als **DEC-0061**, und die vier Zeiger nennen die Nummer. Die Zahl „76 aktive EVD" ist aus
`backlog_types` verschwunden (N1) und steht im DEC mit ihrem Bezugspunkt: **75 auf 6d18407**
(gemessen; im Hauptbaum sind es am selben Tag 76 - deshalb der Bezugspunkt).

## N-Befunde

* **N1** Zahl aus `backlog_types` entfernt; sie steht in H108 und im DEC.
* **N2** `lock.py` nennt den Abschnitt (spec II.4) statt die Zahl ueber der Zahl.
* **N4** Der Gliederungs-Hinweis steht hinter dem Schreibvorgang: ein Body, den der Kernel
  verweigert, wurde nie eine Ebene, und ein Rat ueber eine nicht angelegte Ebene ist genau das
  Rauschen, gegen das der Hinweis begrenzt ist. Die Gliederung wird weiterhin VOR dem Schreiben
  gelesen, damit das neue Item sich nicht selbst empfiehlt.
* **N5 - gebaut, nachdem die Groesse gemessen war.** Betroffen waren `backlog_tree.grouped_children`
  (eine Definition), `board._branches` (eine Schleife, zwei Attribute), der HTML-Leser der
  Testsuite und ein Test, der die Gruppenstruktur liest. Das ist klein, also gebaut: die Gruppen
  eines Elternknotens haben einen zweiten Schluessel - den Bereich -, die Ueberschrift traegt ihn,
  und die UNSORTIERTE Gruppe steht am Ende. Fuer ein Projekt ohne `area` ist die Seite unveraendert
  (48 Board-Tests gruen). Was das NICHT ist: ein Dashboard-Neubau - der ist **FR-0075**, und die
  Ansicht dort wird diese Gruppierung erben oder ersetzen.
* **N6 -> Naht S11** (unten, woertlich).
* **N7 - als Rest benannt statt weggemessen.** `test_hooks -k scaffold_records_the_trays` braucht
  isoliert **585 s** (Pruefer) bzw. 346 s (mein Lauf) gegen ein **600-s-Timeout im Test**. Die
  Marge ist eine Nebenlast breit: im Volllauf mit einem zweiten pytest-Prozess auf derselben
  Maschine lief sie ab (zwei `sh`-Parametrierungen, Lauf 4 der ersten Runde). Kein Produktdefekt,
  aber auch keine Messung, auf die man sich verlassen kann - die Grenze gehoert hoeher oder der
  Scaffold-Lauf entlastet. Rest fuer die Merge-Runde, benannt, nicht geschlossen.

## Nahtliste S1-S11 (woertlich)

**S1 - Paragraph 2 aller drei Verfassungen und `README.md`, die Kommandoliste.** Nach
`freeze-design` einfuegen:

> `freeze-report`, `verify-invariants`, `revise-document`,

Betroffen: `team-kits/dev-team/constitution/AGENTS.md`,
`team-kits/office-team/constitution/AGENTS.md`,
`team-kits/research-team/constitution/AGENTS.md`, `README.md`. Solange sie fehlen, ist
`test_hooks.test_every_span_that_presents_the_command_surface_names_all_of_it` rot.
**Merge-Hinweis des Pruefers:** S1 fasst denselben Paragraph-2-Absatz an wie Strom E (-12) - S1
**nach** E anwenden; Schiedsrichter ist derselbe Test.

**S2 - research-Verfassung Paragraph 6**, Zeile der Report-Writer-Zuordnung. Anzufuegen:

> Rendered into `project_memory/staging/<TSK-ID>/` and filed with `python scripts/harness.py
> freeze-report` (stdin body: `staging_key`, `subject_id`, `source_name`); the tray itself stays
> closed to the write tools, and a report already filed is never overwritten.

**S3 - research-Verfassung Paragraph 17.** Anzufuegen:

> A report reaches `project_memory/reports/` only through `freeze-report`, which appends its path
> to the experiment's `evidence_refs` -- the field the merge is blocked on. Render under a name
> that says which run it is: a second file of the same name is refused, not replaced.

**S4 - Rollentext des Report-Writers** (research): dieselbe Zeile wie S2, plus der Hinweis, dass
der Bericht vor dem Ablegen gelintet wird.

**S5 - jeder Rollentext, der `harness.py evidence` lehrt** (QE/Reviewer, alle drei Kits):

> Record what you ran: `--run-command "<the exact line>" --run-scope full|selection`. A passing
> `selection` is recorded and does not open a merge; a failing one still closes it.

**S6 - Hook-Eigner:** `team-kits/{dev,research}-team/hooks/gate_git.py`,
`_refuse_unless_the_item_is_green`. Vorschlag:

> (spec II.10a: a run that declares itself a selection does not open a merge -- one that declares
> no scope is not distinguished, H108)

**S7 - Rollentext jeder Rolle, die ein Kit-Dokument besitzt.** Anzufuegen:

> Correcting or removing something a kit document already records has a route now: stage the
> document as it should stand and run `python scripts/harness.py request-approval
> document_revision --kit-document <file> --proposal staging/<TSK-ID>/<file> --reason "<why>"`,
> then `python scripts/harness.py revise-document` with the same flags. Every replaced and every
> deleted spot stands in the approval question with its old and its new wording -- the user
> approves those spots and nothing else. Additions keep going through `apply-proposal`, whose
> question promises that nothing existing changes.

**S8 - QA-/Architektentext (dev, research), wo `INV` gelehrt wird.** Anzufuegen:

> An invariant's `check.ref` names a test as `<path>::<name>`, relative to the project root, and
> `python scripts/harness.py verify-invariants` is what records `verified` -- nobody writes that
> status by hand. Until the named test exists, the state validator reports the invariant as an
> error and the merge stays closed. A check this kernel cannot parse is reported as undecided: a
> warning, no merge blocker, and the command exits 0.

**S9 - PM-Rollentext aller drei Kits, wo `capture` gelehrt wird.** Anzufuegen:

> `capture` prints two hints on stderr and refuses nothing for them: similar existing items of the
> same type, and -- when the body names an `area` nobody uses yet -- the outline the backlog
> already has. An `area` is at most two levels (`document/heading`); a third is refused.

**S10 - ERLEDIGT, keine Merge-Auflage mehr.** Der Lead hat den Koerper ueber den Kernel erfasst:
**DEC-0061 VALID** (`project_memory/decisions/active/DEC-0061.yaml`). Alle vier gebauten Stellen
nennen jetzt die Nummer statt des Staging-Pfades: `backlog_types.RUN_SCOPES` (Zeile 392),
`backlog_types.RUN_RECORD_FIELDS` (400), `state.capture_preflight` (793) und
`report._delivery_evidence` (1439). `dec-run-scope.json` bleibt im Staging als das, was erfasst
wurde; die Autoritaet ist ab jetzt der Datensatz.

**Ein Rest, der dem Merge gehoert und den ich gemessen habe:**
`test_repo_hygiene.test_every_decision_pointer_in_a_shipped_kit_file_resolves` ist IM WORKTREE rot
und nennt genau die vier neuen Zeiger. Der Grund ist die Baumtrennung, nicht der Inhalt: der
Worktree steht auf 6d18407 und sein `project_memory/decisions/active/` endet bei DEC-0060, waehrend
DEC-0061 im Hauptbaum liegt. Gemessen: in einer Kopie ausserhalb des Repos, in der der Kernel
dieses Stroms und die Entscheidungen des Hauptbaums zusammenstehen (59 DEC-Dateien, DEC-0061
darunter), ist derselbe Test **gruen** (2 passed). Im Merge stehen beide Haelften ohnehin zusammen;
bis dahin ist dieser eine rote Test erwartbar und erklaert.

**S11 - die ROUTEN-Saetze** (nicht die Kommandoliste aus S1). Sie sagen heute, Ersetzen und
Loeschen habe keine Route - seit dieser Runde falsch. **Gegen die drei Dateien geprueft statt
behauptet** (die erste Fassung dieser Naht zitierte EINEN Satz und behauptete „dev/office tragen
dieselben Saetze"; gemessen: research 1 Treffer, dev 0, office 0 - office traegt den Sachverhalt
anders formuliert, dev an dieser zweiten Stelle gar nicht):

| Stelle | Treffer | Was zu tun ist |
|---|---|---|
| `apply-proposal` adds to any kit document the kernel can compare | dev 1, office 1, research 1 | S11-a in allen dreien |
| „Rewriting or deleting a rule that already stands there …" | dev 0, office 0, **research 1** (`:60`) | S11-b nur research |
| „… it ADDS only, so correcting what a document already says stays the user's own edit …" | dev 0, **office 1** (`:293`), research 0 | S11-c nur office |

**S11-a - alle drei Verfassungen, Paragraph 2.** Nach „`apply-proposal` adds to any kit document
the kernel can compare" einfuegen:

> , `revise-document` replaces or deletes a spot in one -- every spot in the approval question,
> old and new

**S11-b - nur research, Paragraph 7 (`:60`).** Den Satz „Rewriting or deleting a rule that already
stands there is refused on that route and stays the user's own edit; that one you report."
ersetzen durch:

> Rewriting or deleting a rule that already stands there goes through `revise-document`: stage the
> file as it should stand, and the approval question shows every replaced and deleted spot with
> its old and its new wording. What that route refuses -- a list that gains and loses entries in
> one step -- is still the user's own edit, and that one you report.

**S11-c - nur office (`:293`).** Den Halbsatz „and it ADDS only, so correcting what a document
already says stays the user's own edit." ersetzen durch:

> and it ADDS only. Correcting or removing what a document already says has its own route,
> `revise-document`, on its own approval: the question shows every replaced and every deleted spot
> with its old and its new wording, and the user approves those spots and nothing else.


## Ein Fehler IN der Nacharbeit, gefunden von den bestehenden Tests

Meine erste N3-Fassung entschied den Zweig allein an `root_id not in tops`. Das kippte zwei
bestehende Tests (`test_report.test_an_origin_that_reaches_the_root_through_only_one_of_its_
parents_is_refused`, `test_kernel.test_an_origin_with_a_parent_outside_the_root_is_refused_at_
creation`): bei ZWEI Eltern, von denen einer die Wurzel erreicht, enthalten die tops der
abweichenden Pfade die Wurzel nicht - die Mehrdeutigkeit wurde als Fremdwurzel gemeldet, das
Spiegelbild des Fehlers, den ich beheben sollte.

Die Bedingung ist jetzt die eine Frage, die beide Ebenen beantwortet: steht die Wurzel am Ende
IRGENDEINES Pfades? (`len(astray) == len(parents) and root_id not in tops` -> Fremdwurzel, sonst
Mehrdeutigkeit.) **Beide Haelften einzeln rot gemessen:** nur die Zaehlung -> der Grosseltern-Test
faellt; nur `tops` -> der Zwei-Eltern-Test faellt.

## Laeufe der Nacharbeit 1

Stempel: **2026.09.02-16** auf allen drei `VERSION`-Dateien (provisorisch), gesetzt nach der
letzten Aenderung.

| Lauf | Ergebnis |
|---|---|
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |
| `test_state test_report test_board test_staging_cli test_backlog_types test_kernel test_approvals_dispatch test_repo_hygiene` | **660 passed** (3:28) |
| `test_hooks -k "command_surface or evidence_command or invariant or adhoc or approval or document"` | 79 passed, **1 failed** - und das ist S1 (die vier Texte ausserhalb des Scope) |
| `.claude/hooks/test_gates.py -k "hole or measurement or reference"` | 8 passed (2:56) |
| `test_hooks_v2 -k validate_py_is_green` | passed (der Stempel deckt den Baum) |
| Pilotkopie: `gate_write_scope` vorher/nachher | rc 2 ohne / mit `revise-document` im Text |

Volle Suite nicht (Merge-Runde, DEC-0050).

Uebergabe: `_round-scratch/TSK-0106/stream-kernel.patch` (4575 Zeilen, 27 Dateien, keine neuen
Dateien, kein `.audit`-Eintrag) und `git-status.txt`; die erfassungsfertige Entscheidung liegt als
`project_memory/staging/TSK-0106/dec-run-scope.json`.

---

# Nacharbeit 2 (Nachpruefung: B 1, M 1, N 3)

## B-neu - der Kommentar behauptete eine Deckung, die beim Fixture-Umbau verlorenging

Derselbe Mechanismus wie B2 aus Runde 1, eine Ebene weiter: der Satz an
`DUPLICATE_HINT_SIMILARITY` nannte einen Test, der „beide Kanten" misst. Beim Umbau der Fixtures
auf echte Prosa (M2 (d)) sind die Paare aus dem Band gewandert, der Satz blieb stehen.

**Gemessen, vorher** (`rework1/edges.py`): das Nachbarpaar lag bei **0.056**, die Wiedervorlage
bei **0.950** - unter 0.25 bzw. auf der 0.95-Kante, also war weder die untere noch die obere
Mutation ueber diesen Test rot.

**Jetzt drei Paare, jedes mit einer Aufgabe** (Scores mit dem laufenden Leser, `_content_words`):

| Paar | Score | Was es haelt |
|---|---|---|
| unverwandtes Requirement desselben Projekts | **0.056** | ein Backlog sieht so aus - hier zu feuern waere das Nerven, das die FR verbietet |
| NACHBAR: gleiches Thema, andere Forderung | **0.329** | die UNTERE Kante; das engste echte Paar des Bestands liegt bei 0.314 |
| WIEDERVORLAGE: dasselbe Requirement neu formuliert | **0.662** | die OBERE Kante |

**Beide Kanten im Rot-Rig gemessen:** Schwelle 0.25 -> Test rot (der Nachbar wird laut);
Schwelle 0.95 -> Test rot (die Wiedervorlage verstummt). Der Kommentar sagt jetzt, was der Test
wirklich traegt, und dass die Behauptung eine Runde lang unwahr war.

## M-neu - S11 zitierte einen Satz und behauptete seine Verbreitung

**Mechanismus:** die Nahtliste hat EIN Zitat aus der research-Verfassung genommen und
„dev/office tragen dieselben Saetze" dazugeschrieben, ohne die drei Dateien gegeneinander zu
pruefen. Gemessen: research 1 Treffer, dev 0, office 0 - office traegt denselben Sachverhalt
anders formuliert (`office-team/constitution/AGENTS.md:293`), dev an dieser zweiten Stelle gar
nicht. S11 ist jetzt in drei benannte Stellen mit je eigenem Wortlaut geteilt (S11-a/-b/-c, oben),
jede mit ihrer gemessenen Trefferzahl.

## N-Befunde dieser Runde

* **N-neu-1** „98 items" aus dem Schwellenkommentar entfernt - dieselbe Klasse wie die „76":
  mit dem laufenden Leser zaehlt der Worktree 96, c4f3cc0 96, das Live-Repo 98. Die Verteilung
  steht im Protokoll, die Zahl in keinem Kommentar.
* **N-neu-2** Die Loecherliste nennt an beiden Stellen (`:2352`, `:6809`) jetzt `DEC-0061` (VALID)
  statt eines Entwurfs im Protokoll.
* **N-neu-3** Der Satz an `_owned_elsewhere` behauptete, ein literales `== COMMAND` haette „den
  Deskriptor der anderen Route durchgelassen". Gemessen: Rueckbau auf das Literal laesst 453 Tests
  gruen, und konstruktiv kann es nicht durchlassen (`one.path` gleicht nie dem Prosasatz
  `REVISION_WRITES`). Der Kommentar sagt jetzt, was gilt - zwei eigene Kommandos, also beantwortet
  ein Literal eine Frage ueber zwei - und nennt die Messung samt der Feststellung, dass hier kein
  Loch geschlossen wurde.

## Laeufe der Nacharbeit 2

Stempel **2026.09.02-18** auf allen drei `VERSION`-Dateien, gesetzt nach der letzten Aenderung.

| Lauf | Ergebnis |
|---|---|
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |
| die acht Module | 659 passed, 1 failed - der bekannte Rote: `test_repo_hygiene.test_every_decision_pointer_in_a_shipped_kit_file_resolves`, weil `DEC-0061` im Hauptbaum liegt und der Worktree auf 6d18407 steht (in einer vereinten Kopie gruen gemessen) |
| `test_report` Kanten-Mutationen | 0.25 rot, 0.95 rot |
| `.claude/hooks/test_gates.py -k "hole or measurement or reference"` | 8 passed |
