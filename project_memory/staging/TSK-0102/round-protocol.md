# TSK-0102 — Stream C (office), Rundenprotokoll

Wanduhr: **Start 2026-09-01 21:22:47 +0200, erste Abgabe 23:23:31, Nacharbeit nach
Pruefer-FAIL 23:53:56 -> 2026-09-02 00:45:21, letzte Nacharbeit 01:06:04 -> 01:40:49 +0200** — zusammen 3 h 56 min (DEC-0057 g). Worktree `C:\Offline Repos\v2-testbed\_worktrees\stream-office` auf `stream/office`
ab `c155a5f`. Scratch: `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0102\`.

Übergabe:
* Patch: `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0102\stream-office.patch`
  (30 Dateien, +3001/−96; `git diff HEAD -- . ":(exclude)project_memory"`; nach der letzten Nacharbeit neu gezogen)
* Status: `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0102\stream-office.status.txt`
* Kein Commit, kein Push, kein globales Install (DEC-0057 b/d/e).

---

## 1. FR-0065 — Vier Augen für die BUCHUNG

### Was gebaut ist

Zwei Fangklassen, wie das Item sie verlangt, und die zweite ist neu:

* **(i) Rechnerisch** — unverändert `ledger_add.validate_row` (`net × (1+vat) = gross`), gefahren
  von `gate_ledger_valid`. Fängt Tripel, die nicht aufgehen.
* **(ii) Zweite unabhängige Lesung** — neu. `gate_second_booking` verweigert
  `commit`/`push`/`merge`/`tag`/Report, solange eine Ledger-Zeile, die noch **nicht in `HEAD`**
  steht, von weniger attestierten `booking_reading`-Datensätzen **verschiedener Läufe** gedeckt ist
  als ihre Kategorie verlangt — oder solange einer davon etwas anderes über sie sagt.

Neue/geänderte Dateien:

| Datei | Rolle |
|---|---|
| `team-kits/kernel/schemas/booking_reading.yaml` (neu) | Der Vertrag: `task_id`, `role`, `readings[]` mit `source` + 9 Ledger-Spalten |
| `team-kits/office-team/hooks/_bookings.py` (neu) | Vergleich Zeile↔Lesung, `HEAD`-Grundlinie, Freigabehebel |
| `team-kits/office-team/hooks/gate_second_booking.py` (neu) | `PreToolUse(Bash\|PowerShell)`, verweigert |
| `team-kits/office-team/hooks/record_booking_reading.py` (neu) | `PostToolUse`, attestiert Lauf + Beleg-Bytes |
| `team-kits/office-team/hooks/_readings.py` | verallgemeinert: `Contract`, `contract_of`, `stated`, `readings_required` zog hierher |
| `team-kits/office-team/hooks/gate_second_reading.py` | delegiert `readings_required` an `_readings` (eine Fassung, zwei Aufrufer) |
| `team-kits/office-team/hooks/gate_ledger_valid.py` | `requires_a_sound_ledger()` herausgezogen — EIN Leser für „wann müssen die Bücher stimmen" |
| `settings.json`, `ENFORCEMENT.md`, Verfassung §2.3, `bookkeeper.md`, `bookkeeper/SKILL.md`, `master_data.yaml` | Registrierung, Beschreibung, Pflicht, Hebel |

### Die drei offenen Entwurfsfragen des Items — **gemessen** entschieden

**(a) Volle zweite Lesung je Zeile oder Stichprobe?** → **Jede Zeile**, gebündelt je Lauf.
Gemessen (`_round-scratch/TSK-0102/measure_cost.py`, gegen die ausgelieferten Dateien):

```
fixer Kontext je LAUF (Rolle + SKILL + Verfassung): 48 249 Bytes
marginal je ZEILE (ein Lesungs-Eintrag):                276 Bytes
   1 Zeile  je Lauf: 48 525 B gesamt = 48 525 B/Zeile (100 %)
   5 Zeilen je Lauf: 49 629 B gesamt =  9 925 B/Zeile ( 20,5 %)
  20 Zeilen je Lauf: 53 769 B gesamt =  2 688 B/Zeile (  5,5 %)
  50 Zeilen je Lauf: 62 049 B gesamt =  1 240 B/Zeile (  2,6 %)
```

Verhältnis fix:marginal = **175:1**. FR-0035s Lehre trägt also auch hier: eine Stichprobe spart
fast nichts, weil sie den fixen Anteil trotzdem je Lauf zahlt — was spart, ist **Bündeln**. Ein
Datensatz trägt beliebig viele Einträge; die SKILL sagt das.
**Ehrliche Grenze dieser Messung:** sie zählt den Kontext des HARNESS, nicht den Beleg selbst. Eine
gescannte PDF muss der zweite Leser wirklich lesen, und das ist echte Kosten je Zeile, die diese
Zahlen nicht enthalten. Der Hebel unter (b) ist die Antwort darauf, nicht diese Tabelle.

Laufzeit des Gates, als echter Hook-Prozess, drei Punkte
(`_round-scratch/TSK-0102/measure_gate_cost.py`, bester von drei Läufen). **Die Zahlen sind
hostabhängig und als Größenordnung zu lesen, nicht als Konstante** — derselbe 480-Zeilen-Punkt:
0,240 s auf diesem Host unbelastet (Endstand nach der Nacharbeit), 0,487 s auf demselben Host unter
Suite-Last, 0,808 s auf dem Host des Prüfers:

```
   1 Zeile,  keine in HEAD: 0,207 s rc 2      1 Zeile,  alle in HEAD: 0,211 s rc 0
 120 Zeilen, keine in HEAD: 0,216 s rc 2    120 Zeilen, alle in HEAD: 0,222 s rc 0
 480 Zeilen, keine in HEAD: 0,240 s rc 2    480 Zeilen, alle in HEAD: 0,218 s rc 0
```

Im Normalzustand (Buch committed) kostet das Gate rund 0,2 s je Commit, unabhängig von der Größe.

**(b) Was ist ERZWINGBAR, was bleibt Verfahren?** Das Muster aus FR-0035, unverändert: **Herkunft
ist messbar, Blindheit nicht.** Erzwungen ist, dass N verschiedene Läufe je einen eigenen Datensatz
geschrieben haben, dass jeder an die BYTES des Belegs gebunden ist und dass die Zeile mit jedem
übereinstimmt. NICHT erzwungen — und in Kopf, ENFORCEMENT-Zeile und Verweigerungstext ausdrücklich
so gesagt — ist, ob der zweite Lauf den ersten Datensatz gesehen hat.
Der **Hebel gehört dem Nutzer**: `second_reading: false` an einer Kategorie in `master_data.yaml`
(kit-Dokument, kein Werkzeugschreibzugriff, nur über `apply-proposal` mit Nutzerfreigabe). Gleiche
Schreibweise, gleiche Funktion (`_readings.readings_required`) wie beim Aktenplan; eine Freigabe ist
EINE Lesung, nie keine.

**(c) Migration der einäugig gebuchten Zeilen** → **Ableitung statt Flagge**: geurteilt wird nur
über Zeilen, deren CSV-Felder nicht schon in `HEAD` stehen. Keine Aufzählung, keine Grundlinien-
Datei, nichts Prägbares — der einzige Weg nach `HEAD` ist ein Commit, und der Commit ist einer der
Momente, an denen dieses Gate steht. Damit sind bestehende Bücher unangetastet und die Regel gilt
ab ihrer Einführung nach vorn.

### Zwei Entscheidungen, die vom Naheliegenden abweichen (mit Grund)

* **Kein Urteil beim Spawn**, obwohl `gate_ledger_valid` dort urteilt: die zweite Lesung schreibt
  ein zweiter Spawn — eine Verweigerung dort verweigerte den Ausweg aus sich selbst.
  `test_the_booking_gate_stands_at_the_shell_moments_and_not_at_a_dispatch` misst beide Hälften.
* **Die Kette `gate_ledger_valid.py gate_second_booking.py` ist in der REIHENFOLGE tragend** (anders
  als die Ablage-Kette): `_gate.py` hält beim ersten Refusal, und ein Ledger, dessen Zeilen kaputte
  Daten sind, muss als das gemeldet werden, bevor jemand zurück zum Beleg geschickt wird.

### Ein Defekt, den ich beim Bauen selbst gefunden und geschlossen habe

`vat_rate: 0` (Kleinunternehmer, Reverse Charge, steuerfrei) ist in YAML die Ganzzahl 0 und damit
**falsy**. Der geerbte Erkenner testete Einträge auf Wahrheit — jede solche Lesung wäre verworfen
worden, die Zeile nie deckbar, das Projekt von den eigenen Commits abgeschnitten mit einer
Verweigerung, die auf Datensätze zeigt, die da sind. `_readings.stated` entscheidet das jetzt.
Rot gemessen: M2 unten.

---

## 2. FR-0062 — Kit-Lücken-Log je Projekt

Gebaut: `team-kits/kernel/gaplog.py` (der Schreiber), `tools/harvest_kit_gaps.py` (die Ernte),
`tools/test_gaplog.py` (8 Tests).

* **Wo es liegt:** `project_memory/.audit/kit_gaps.jsonl` im PROJEKT — dieselbe Fläche, in die die
  Haken ohnehin protokollieren, und eine, in die `gate_write_scope` keinen Agenten-Schreibzugriff
  lässt. Der Kernel schreibt, die Rolle ruft nur auf; die Schreibverweigerung bleibt intakt.
* **Was ein Eintrag trägt:** `tried` + `refused` (beide Pflicht, sonst Verweigerung mit Begründung),
  `item` und `title` optional, dazu `ts`, `kit_version` und eine **inhaltsadressierte `id`**.
  **Kein Vokabular** — kein `kind:`, keine Schwere, keine Kategorie (P4-12: eine Aufzählung, die ein
  echtes Projekt nicht erweitern kann, ist der nächste Defekt). Feldgrenze 2 000 Zeichen mit
  Schnittmarke; Dateigrenze 512 KB, danach Verweigerung statt stillem Verlust.
* **Warum inhaltsadressiert:** `record` ist damit idempotent (dieselbe Wand zweimal = ein Eintrag)
  UND die Ernte kann von AUSSEN als „gesichtet" markieren, ohne je in den fremden Speicher zu
  schreiben. Der Erntestand liegt in `tools/kit_gap_harvest.json` HIER, indiziert nach
  Projektpfad + Eintrags-id. Als Bytes gemessen: das Projektlog ist vor und nach einem Marklauf
  identisch.
* **Ernte:** `python tools/harvest_kit_gaps.py <projekt> …` oder `--all` über `$HARNESS_PROJECTS`;
  Exit 1 heißt „es liegt etwas an". Ohne Argumente = `--all`, Exit 0.

### SEAM (cli.py) — die Verdrahtung, die die MERGE-Runde einsetzen muss

`kernel/cli.py` gehört diese Runde einem anderen Stream. Der Verb ist deshalb **nicht** verdrahtet.
Exakt einzusetzen:

**(1) Import**, in der Importliste von `kernel/cli.py`, alphabetisch zwischen `filing` und
`hashing`:

```python
from . import gaplog
```

**(2) Subparser**, in `build_parser`, direkt nach dem `documents.COMMAND`-Block (nach dem
`for name in manifest_parameters(...)`-Schleifenende des `proposal`-Parsers) und vor
`archive = sub.add_parser("archive", ...)`:

```python
    # THE REPORTING HALF of the dead-end family BUG-0041/BUG-0068/BUG-0070 (FR-0062). A session that
    # hits an infrastructure boundary tells the user -- and the report dies in the chat. This books
    # it into the project's own log instead, where the kit's maintainer reads it across repos. The
    # KERNEL is the writer, so the agent-write refusal under `project_memory/` stays intact; nothing
    # forces a session to call it, and `kernel/gaplog.py` says so rather than implying otherwise.
    gap = sub.add_parser(
        gaplog.COMMAND,
        help="record a kit gap in this project's own log (what you tried, what refused you)")
    gap.add_argument("--tried", required=True,
                     help="what this session was trying to do, in its own words")
    gap.add_argument("--refused", required=True,
                     help="the message that stopped it, verbatim")
    gap.add_argument("--title", default="", help="a one-line name (defaults to the start of --tried)")
    gap.add_argument("--item", default="", help="the item this happened under, if there is one")
```

**(3) Dispatch**, im Kommando-Zweig, direkt nach dem `if args.command == documents.COMMAND:`-Block:

```python
        if args.command == gaplog.COMMAND:
            entry = gaplog.record(state, args.tried, args.refused, args.title, args.item)
            print("kit gap %s: %s" % (entry["id"],
                                      "recorded" if entry["recorded"] else "already recorded"))
            # THE USER STILL HEARS IT IN THIS TURN. The log is for the kit's maintainer, not a
            # substitute for telling the person whose work just stopped (§8 of every constitution).
            print("NOT done here: the user has not been told. Say it to them in this same turn.")
            return 0
```

**(4) Verfassungssatz** — gehört in dieselbe Merge-Änderung wie (1)–(3), **nie allein**. In
`team-kits/office-team/constitution/AGENTS.md` §8, unmittelbar hinter „Every ‚report it (§8)'
elsewhere in this file points here.":

> **AND BOOK IT**, in the same turn as the sentence to the user:
> `python scripts/harness.py report-gap --tried "<what you were doing>" --refused "<the message you
> got, verbatim>" --item <ITEM-ID>` appends it to this project's own kit-gap log, which the kit's
> maintainer reads across projects. Telling the user alone is what BUG-0068 and BUG-0070 cost: both
> were recovered only by the maintainer reading entire sessions afterwards. The command is the
> writer — you still never write `project_memory/` yourself — and nothing forces you to run it: no
> hook can see a gap you did not book, so this is a duty you carry and not one the kit enforces.

**Warum der Satz NICHT schon im Patch steht:** eine Verfassung, die ein Kommando nennt, das
`--help` nicht führt, schickt die Rolle in eine Route, die es nicht gibt — genau BUG-0041s Form.
Der Tripwire dagegen ist gebaut und liegt im Patch:
`tools/test_gaplog.py::test_the_gap_command_and_the_duty_that_names_it_arrive_together`.
Er prüft **beide Richtungen**
und wird rot, sobald eine Hälfte allein landet. Heute ist er absichtlich still (keine Hälfte da) —
das ist der Zustand, den dieses Protokoll trägt und den ein Test nicht messen kann.

Auch für dev-team und research-team gilt derselbe Satz; die beiden Verfassungen liegen in fremden
Streams und sind hier **bewusst nicht angefasst**.

---

## 3. FR-0031 — bindender Aktenplan-Entwurf + gerenderter Baum

Gebaut: `team-kits/office-team/templates/repo/scripts/filing_plan.py` (neu, office-eigen) mit zwei
Modi, dazu die Anbindung in `process_doc.py`, die Onboarding-Sequenz in der Manager-SKILL und
-Rollendatei und ein Hinweis im Kopf von `filing_plan.yaml`.

* **`--draft`** leitet je Dokumentklasse, die der EIGENTÜMER im Onboarding unter
  `business_profile.yaml` → `document_sources` genannt hat, eine Regel ab und druckt die beiden
  Kommandozeilen (`request-approval filing_rule` und `add-filing-rule`) mit den Flags dazu. Es
  schreibt **nichts**. Genau dieselbe Liste vergleicht `kernel.filing.uncovered_document_sources`
  gegen den Plan — es gibt also keine zweite Antwort auf „welches Papier hat dieser Betrieb".
* **Keine erfundene Taxonomie.** Zwei Strukturentscheidungen trifft der Entwurf, beide aus den
  auskommentierten Beispielen der ausgelieferten Vorlage, beide in der Ausgabe als Vorschlag
  benannt: ein `<year>`-Ordner je Klasse und die Namensform. Die **Aufbewahrungsfrist wird NICHT
  vorgeschlagen** — sie steht als `TBD - ask the Steuerberater` in der Freigabefrage, weil eine
  Zahl, die das Kit wählt, eine wäre, die der Nutzer unterschreibt statt entscheidet.
* **Eine Klasse, deren Name kein Ordnername sein kann**, wird gemeldet und bekommt keine Regel —
  sie bleibt damit für `uncovered_document_sources` sichtbar, statt irgendwo abgelegt zu werden, wo
  niemand sie gemeint hat.
* **`--tree`** rendert den Plan als Verzeichnisbaum. **EIN Renderer:** `process_doc.py` füllt den
  Ablage-Abschnitt der Verfahrensdokumentation mit `filing_plan.tree_lines(rules)` — der Test
  vergleicht Identität, nicht Ähnlichkeit.
* **Ein Leser des Plans, aber der richtige:** `--draft`/`--tree` gehen über
  `kernel.filing.existing_rules`, nicht über `gate_filing.rules` — letzteres meldet einen Plan mit
  `rules: []` als unlesbar, und genau das ist der Zustand, für den dieses Skript da ist.

Rot-zuerst für den Kern: `test_a_fresh_office_project_files_its_first_document_without_the_user_editing_yaml`
fährt die Kette in einem frischen Office-Projekt — leerer Plan → `mv` rc 2 (`gate_filing`) →
`filing_plan.py --draft` → Freigabe **durch den echten Freigabe-Haken** (`conftest.mint_via_hook`,
`PostToolUse(AskUserQuestion)`) → `kernel.filing.apply(state, manifest)` → zwei Klassifikations-
Lesungen → `mv` rc 0.
**Genau gesagt, was der Test NICHT fährt:** nicht die argparse-Schicht von `add-filing-rule`,
sondern die Kernel-Funktion, die dieser Zweig aufruft (`cli.py`: `filing.apply(state,
_line_manifest(...))`) — mit dem Manifest, das aus den vom Entwurf GEDRUCKTEN Flags gebaut wurde. Was
damit gemessen ist: dass die gedruckten Flags ein Manifest ergeben, das `approvals` annimmt, und dass
`filing.apply` es ohne Handarbeit in den Plan schreibt. Was NICHT gemessen ist: dass die
Kommandozeile selbst durch argparse geht. Gespielt wird außerdem eine Sache: die ANTWORT des
Nutzers, die keine Software geben darf.

---

## 4. Rot-zuerst: gemessen, nicht behauptet

Klon **außerhalb** des Repos (`_round-scratch/TSK-0102/redcheck`, Kopie des Worktrees), je Mutation
angewandt → Tests gefahren → zurückgesetzt. Skripte: `redfirst.py`, `redfirst_gaplog.py`.
Baseline vor den Mutationen: 38 passed.

| # | Wiederhergestellter Defekt | Wird ROT |
|---|---|---|
| M1 | `gate_second_booking` gar nicht registriert (Zustand vor dieser Runde) | 6: `…row_nobody_read_twice…`, `…wrong_but_reconciling…`, `…from_one_run…`, `…git_cannot_answer…`, `…user_released…`, `…document_swapped…` |
| M2 | Einträge auf Wahrheit statt auf „beantwortet" geprüft (`vat_rate: 0`) | `test_a_reading_of_a_zero_rated_invoice_is_a_reading` |
| M3 | `master_data.yaml` aus der Projektwurzel statt aus dem Zustandsverzeichnis | `test_a_category_the_user_released_needs_one_booking_reading_and_never_none` |
| M4 | Grundlinie schluckt jede Zeile (nichts wird je geurteilt) | 6 |
| M5 | Gar keine Alt-Zeilen-Ausnahme (`HEAD` nie gelesen) | `test_a_row_already_in_head_is_not_booked_again` |
| M6 | Schema deklariert `category` nicht mehr | `…asks_for_exactly_the_ledger_columns…`, `…user_released…` |
| M7 | Der `git`-Rückzug wird zur Verweigerung (Deadlock-Richtung) | `…git_cannot_answer_for_stands_the_booking_gate_down…` |
| M8 | Die Uneinigkeit nennt weder Feld noch Werte | `test_a_wrong_but_reconciling_row_is_refused_although_the_arithmetic_holds` |
| M9 | `process_doc` rendert einen eigenen Baum statt des einen Renderers | `…renders_the_plan_as_the_tree_from_the_one_renderer` |
| M10 | Der Entwurf schlägt eine eigene Aufbewahrungsfrist vor | `test_the_draft_makes_no_retention_number_up` |
| M11 | Der Entwurf schlägt eine Regel für eine schon gedeckte Klasse vor | `test_the_draft_proposes_nothing_for_a_class_the_plan_already_files` |
| G1 | Lücke ohne Verweigerungstext buchbar | `test_a_gap_with_no_refusal_or_no_attempt_is_refused` |
| G2 | Eintrags-id trägt die Uhr | `test_the_entry_id_ignores_the_clock_and_reads_the_content` (+5 Folgefehler, s. u.) |
| G3 | Feld wird ohne Schnittmarke gekürzt | `test_a_pasted_transcript_is_cut_and_says_so` |
| G4 | Die Ernte markiert IM fremden Projektspeicher | `…never_writes_into_it`, `…walks_every_project…` |

**Eine Ehrlichkeit zu G2:** die Mutation zog `time` in eine Funktion, die es nicht importiert hat,
und erzeugte darum einen NameError, der sechs Tests rot machte statt zwei. Der benannte Test ist
darunter und die Richtung stimmt; die Mutation war unsauberer als die anderen.

Zwei Defekte fanden ihre Tests **live beim Bauen**, bevor die Fassung stand — M3 (der Hebel griff
nicht, weil `master_data.yaml` an der falschen Stelle gesucht wurde) und M8 (die Verweigerung
zeigte die Lesungen, aber nicht die Zahlen der ZEILE daneben). Beide sind oben in der Kopie
nachgemessen.

---

## 5. Läufe

* `python -m ruff check .` — **All checks passed**
* `python tools/bump_kit_version.py` — **provisorisch** gestempelt (DEC-0057 d):
  `dev-team 2026.09.01-1`, **`office-team 2026.09.02-3`** (Stand nach der Nacharbeit; die erste Abgabe stand auf `2026.09.01-4`), `research-team 2026.09.01-1`
* `python tools/validate.py` — **all structural checks passed**
* Betroffene Suiten (DEC-0050), Lauf der ERSTEN Abgabe — der massgebliche Lauf ist der der Nacharbeit in §9: `test_hooks.py`, `test_hooks_v2.py`, `test_role_contracts.py`,
  `test_schemas.py`, `test_kernel.py`, `test_repo_hygiene.py`, `test_gaplog.py`,
  `test_disposition.py`, `test_context_budget.py` →
  **3264 passed, 13 skipped, 0 failed** in 28:33 min
  (`_round-scratch/TSK-0102/suite-final.txt`).
  Volle `tools/`-Suite **nicht** gefahren — Stream-Regel; sie gehört der Merge-Runde.

Fünf Tests fielen im vorletzten Lauf und sind geschlossen, nicht umgangen: die beiden neuen Haken
starteten nicht mit `_kernel.GATE_PREAMBLE` (`…starts_with_the_preamble`,
`…refuses_outside_the_one_funnel`), die neue `PostToolUse`-Kette hatte keine Nutzlast in
`_CHAIN_PAYLOADS` (`…mutates_the_state_runs_in_front_of…`), `harvest_kit_gaps.py` beendete sich ohne
Argumente mit 2 und cachte Bytecode in den Kit-Baum (`…leaves_no_bytecode_in_it`), und eine
ENFORCEMENT-Zeile behauptete Reichweite ohne den §0-Zeiger (`…names_the_session_it_holds_for`).

---

## 6. Ratschen und Stempel — was die MERGE-Runde neu aufnehmen muss

* **`tools/lead_package_sizes.json`**: `office-team 47 793 → 49 353 B (+1 560)`, mit Notiz im
  Journal von `docs/reviews/phase0-disposition.md`, als **PROVISORISCH** und mit dem Grund
  gekennzeichnet: zwei neue Mechanismen, die die Verfassung nennen muss (FR-0065 §2.3, FR-0031 in
  der Rollendatei). Beide Absätze wurden nach der ersten Messung um rund ein Drittel gekürzt.
  Neu aufzunehmen beim Merge (DEC-0057 c).
* **Alle drei `VERSION`-Dateien geändert.** Das ist erwartet und nicht Scope-Bruch: der Kit-Hash
  läuft über `team-kits/kernel/`, und diese Runde legt dort `gaplog.py` und
  `schemas/booking_reading.yaml` ab — damit bewegt sich der Inhalt aller drei Kits. DEC-0057
  („Both may touch kernel files and all three VERSION files — that is the expected seam") deckt das;
  der Auftrags-`forbidden_scope` nennt es nicht, deshalb steht es hier ausdrücklich.
* `tools/constitution_section_pins.json` — **DIESE ZEILE WAR FALSCH**; was wirklich gilt, steht in §10 (N2): vier Abschnitte neu aufgenommen, provisorisch, Notiz im Journal.

---

## 7. Löcher (H89–H91), mit Messung, in `docs/POST_V2_WISHLIST.md`

* **H89** — ohne `git` kann die Vier-Augen-Buchung Alt- von Neuzeilen nicht unterscheiden und
  **tritt zurück** statt zu verweigern. Gemessen: Projekt ohne `git init`, ungelesene Zeile,
  `git commit` durch die volle Kette **rc 0**; mit `git init` rc 2. Warum nicht geschlossen: die
  Gegenrichtung säße auf genau dem Commit, der die Zeilen zu Altzeilen machte. Begrenzt durch: der
  Rückzug wird je Datei ins Audit-Log geschrieben, und die Verfassung macht `git` ohnehin zur
  Pflicht.
* **H90** — zwei identische Buchungen EINES Belegs teilen sich ein Lesepaar. Gemessen: zwei Zeilen,
  identisch außer `id`, beide ohne `invoice_no`, ein Lesepaar → `git commit` **rc 0**. Mit gesetzter
  `invoice_no` greift `ledger_add.validate_cross`. Gehört in die Duplikatsregel des Validators, nicht
  in dieses Gate.
* **H91** — der gerenderte Baum zeigt den PLAN, nicht die Platte. Gemessen: ein real angelegtes
  `archive/alte_ablage/2019/x.pdf` kommt in `--tree` nicht vor. Der Abgleich Plan↔Platte ist die
  Prüfung des `project-auditor`, nicht die des Renderers.

---

## 8. Was ich BEWUSST NICHT geschlossen habe (benannt, nicht übersehen)

1. **Der `report-gap`-Verb ist nicht verdrahtet** (cli.py = fremder Stream) und **darum steht der
   Pflichtsatz auch nicht in der Verfassung**. Beides ist ein Paket; §2 dieses Protokolls trägt den
   exakten Text beider Hälften, `test_the_gap_command_and_the_duty_that_names_it_arrive_together`
   wird rot, wenn eine allein landet. **Ohne diese Verdrahtung ist FR-0062 halb geliefert:** der
   Speicher und die Ernte laufen, aber kein Projekt kann heute eine Lücke buchen.
2. **Die Pflicht steht nur für office**, wo sie überhaupt hinkäme — `dev-team` und `research-team`
   sind fremde Streams. FR-0062 gilt für alle drei Verfassungen.
3. **`master_data.yaml` wächst nur über `apply-proposal`.** Der Freigabehebel `second_reading: false`
   ist damit für den Nutzer erreichbar, aber es gibt kein Kommando, das eine EINZELNE Kategorie
   freigibt — der Bookkeeper stagt das ganze Dokument, der Nutzer gibt frei. Das ist der Weg, den
   BUG-0075 gebaut hat; ich habe ihn nicht verbreitert.
4. **`einvoice_extract.py` schreibt keine Lesung.** Der Extraktor ist der Lauf, der BUG-0072
   produziert hat; ihn seine eigene Lesung schreiben zu lassen, wäre die erste von zwei — gebaut ist
   nur, dass der Bookkeeper sie von Hand schreibt. Das ist eine Bequemlichkeit, die die Fangklasse
   nicht ändert (die zweite Lesung muss ein anderer Lauf sein), und sie ist nicht gebaut.
5. **Kein Kommando erzeugt ein `booking_reading`-Gerüst.** Die Rolle schreibt die YAML von Hand nach
   `staging/`. Bei zehn Belegen ist das zehn Einträge in einer Datei — machbar, aber unbequem, und
   ein Generator wäre ein eigener Eingriff mit eigener Fehlklasse (ein Gerüst, das die Zahlen aus
   der ZEILE vorbelegt, wäre genau die Bestätigungsschleife, die das Item ausschließt).
6. **`project_memory/.audit/hook_events.jsonl` im Worktree ist um eine Zeile gewachsen** — ein
   `gate_needs`-Vermerk aus einem Testlauf, derselbe Vorgang, der schon vor dieser Runde Zeilen
   erzeugt hat. Die Datei liegt in meinem `forbidden_scope`; ich habe sie **nicht** angefasst und
   **aus dem Patch ausgeschlossen** (`":(exclude)project_memory"`). Sie bleibt im Worktree geändert;
   ob sie zurückgesetzt wird, ist die Entscheidung des Nutzers, nicht meine.
7. **Der Baum zeigt Platzhalter** (`<year>`), keine echten Jahresordner — er beschreibt die Form,
   nicht den Bestand. Das ist H91 und ausdrücklich gewollt.

---

# 9. NACHARBEIT nach Prüfer-FAIL (2026-09-01 23:53 → 2026-09-02 00:45 +0200)

Der Prüfer bestätigte den Kern (Kernfall, Unabhängigkeit, Bindung an Zeile UND Beleg, Migration,
Hebel inkl. `vat_rate: 0`, Kettenreihenfolge, H89/H91 ehrlich, FR-0031 schreibt nichts, FR-0062
byte-identischer Speicher, beide Seam-Drähte rot, sechs Mutationen nachgefahren, 175:1 exakt
reproduziert) und meldete sieben Befunde. Was daraus wurde:

## F1 + F2 — ein Kausalsatz, der gemessen falsch war (blockierend, AUFGESCHRIEBEN statt geschlossen)

An drei Stellen stand wortgleich: *„no snapshot can be minted: the only way into `HEAD` is a commit,
and a commit is one of the moments this gate stands in."* Das ist falsch, und ich habe beide Ketten
mit meinem eigenen Rig gegen die Kette aus der ausgelieferten `settings.json` nachgemessen
(`_round-scratch/TSK-0102/probe_h99.py`, `probe_h99b.py`):

```
KETTE A   git commit -am books                      rc 2  VERWEIGERT
          printf '…git commit…' > release.sh        rc 0
          bash release.sh                           rc 0  DURCHGELASSEN
            → die ungelesene Zeile steht in HEAD
          git commit -m more  (echter Commit)       rc 0  DURCHGELASSEN, null Lesungen

KETTE B   ein attestierter Lauf                     rc 2  VERWEIGERT
          echo>>, cp, Glob, sed -i, tee, python -c,
          cd&&echo, Write, Append-Redirect          rc 2  alle DIREKTEN Wege VERWEIGERT
          bash mint.sh  (heredoc an den Store)      rc 0  DURCHGELASSEN
          git commit -m books                       rc 0  die falsche 14,28 ist gebucht
```

**Ein Zusatzbefund aus meinem Nachmessen, der die Kette teurer macht, als sie aussieht:** der Store
ist *erste-Zeile-gewinnt je (Datensatz, sha256)*. Eine gefälschte Zeile über DENSELBEN Datensatz
ändert gar nichts — gemessen, Commit blieb rc 2. Wer prägen will, muss den Datensatz erst KOPIEREN
und die Kopie attestieren. Drei bewusste Schritte, nicht einer.

**(a) Der Satz ist gestrichen**, an allen drei Stellen — `_bookings.py` (Kopf), `ENFORCEMENT.md`
(Zeile 52), `tools/test_hooks.py` (Docstring von `test_a_row_already_in_head_is_not_booked_again`).
Was dort jetzt steht, ist die Ableitung als das, was sie ist: *„die Grundlinie IST `HEAD`, und was
`HEAD` bewegt, ist so weit erkannt, wie `gate_ledger_valid.requires_a_sound_ledger` reicht — nicht
weiter"*, plus der Verweis auf `H99`. Der Test-Docstring sagt zusätzlich, dass er die
Migrations-EIGENSCHAFT misst und nicht deren Reichweite.

**(b) `H99` steht in `docs/POST_V2_WISHLIST.md`** mit Mechanismus, beiden gemessenen Ketten, der
Erste-Zeile-gewinnt-Begrenzung, dem Grund gegen ein Schließen (es ist `H11`s Klasse und liegt in
zwei Dateien, die diese Schicht nicht besitzt — eine eigene Antwort hier wäre Gerüst über dem Haus,
DEC-0056) und mit dem, was stattdessen begrenzt: **Absicht statt Versehen** (die Fehlklasse, für die
FR-0065 gebaut ist, läuft vollständig durch die Schicht) und **Sichtbarkeit im Commit** (das Vehikel
ist eine Datei im Arbeitsbaum, anders als eine Befehlszeile). Urteil: blockierend, als benannte
Ausnahme geführt, Abnahme des Nutzers offen — gleicher Stand wie `H11`.
**`H11` hat den Querverweis** bekommen: ein Absatz, der die Buchungsschicht als dritte Folge derselben
Interpreter-Ausnahme nennt (nach „schreibt eine geschützte Datei" und „stellt eine Freigabe aus").

## F3 — die Suite löschte den echten Erntestand des Leads (blockierend, geschlossen)

`tools/test_gaplog.py` benutzte den REALEN Pfad `tools/kit_gap_harvest.json` und entfernte ihn im
`finally`. Ein grüner Lauf löschte damit, was der Lead schon triagiert hatte; zwei parallele Läufe
hätten sich überschrieben.

* `harvest_kit_gaps.harvest_path()` liest jetzt `HARNESS_KIT_GAP_HARVEST` und fällt sonst auf die
  Repo-Datei zurück. **Pro Aufruf aufgelöst, nicht beim Import** — eine beim Import eingefrorene
  Konstante sähe umgelenkt aus und wäre es nicht.
* Alle Erntetests bekommen ihre eigene Datei unter `tmp_path`.
* Neu: `test_the_real_harvest_record_is_not_a_test_fixture` — misst beide Enden als BYTES: die
  Umlenkung wird beschrieben, und der echte Pfad ist danach unverändert (oder weiter nicht da).
  **Rot ohne den Fix**: Umlenkung entfernt → rot.

## F4 — kein Zeitbudget (Rest → gebaut)

Gemessen als ausgelieferter Hook-Prozess, schlechtester Fall (jede Lesung über EINEN Beleg, dann
hilft kein Index): der Join ist linear in Zeilen **und** Lesungen, und die eigenen Schranken des
Moduls (8 MB Ledger ≈ 55 000 Zeilen; `_readings.MAX_FILES` = 400) multiplizieren über die
Tötungsgrenze — und ein getöteter Haken ist ein **Durchlass**.

Drei Eingriffe, alle gemessen:

| | 1920 Zeilen × 399 Lesungen, gewöhnliche Form (viele Belege) | schlechtester Fall (ein Beleg) |
|---|---|---|
| vorher | 1,527 s | 6,497 s |
| `by_source` (Index) | 1,042 s | 4,000 s |
| + `_policy` (master_data einmal statt je Zeile) | **0,560 s** | **3,816 s** |

* **`by_source`** indiziert die Lesungen nach Beleg; das nimmt die Kosten weg, die ein Projekt für
  *andere* Belege zahlt — die gewöhnliche Form.
* **`_policy`** parst `master_data.yaml` einmal je Prozess statt einmal je ZEILE (vorher: ein
  YAML-Parse pro Zeile in einem blockierenden Haken).
* **`TOTAL_BUDGET = 15`** in `_bookings`, mit der Rechnung im Kommentar: die beiden Ledger-Gates
  laufen SEQUENZIELL IN EINEM PROZESS, also addieren sich ihre Budgets gegen
  `_compat.HOOK_DEADLINE_SECONDS` = 60 s; 40 (Nachbar) + 15 = 55 bleibt darin, 40 + 40 nicht. Bei
  Verbrauch wird VERWEIGERT und gesagt, welche Zeilen nicht angesehen wurden; die Abhilfe ist ein
  eigener Absatz (`BUDGET_REMEDY`), weil „wir haben nicht hingesehen" den Leser woandershin schickt
  als „diese Zeile hat niemand gelesen".

**Rot-zuerst, und hier ist meine erste Testfassung selbst durchgefallen:** sie setzte das Budget auf
0 — das fängt aber schon die DATEI-Schleife ab, bevor eine einzige Zeile läuft, also blieb sie grün,
als ich die ZEILEN-Prüfung entfernte (gemessen als genau diese Mutation). Die Fassung misst jetzt
beide Stellen getrennt: Budget 0 → Datei-Zweig („NOT CHECKED", ohne Zeilenzahl), Budget 0,001 s →
Zeilen-Zweig („never looked at"), ausgeliefertes Budget → rc 0. Beide Mutationen sind jetzt rot.

## F5 — ein Sonderzeichen im Dokumenttyp wurde Shell-Syntax (gebaut)

`usable_segment` war eine **Verbotsliste** von Pfadzeichen und sagte nichts über die, die Daten in
Syntax verwandeln. `document_types: [inv$(whoami)]` erzeugte eine gedruckte Zeile
`--path-template "archive/inv$(whoami)/<year>/"`, und die SKILL weist die Rolle an, diese Zeilen zu
fahren. Kein Angreifer nötig: ein `&` oder `$` in einem Ordnernamen ist ein ganz gewöhnlicher
Dienstag.

* `usable_segment` ist jetzt eine **Erlaubnisliste**: jedes Zeichen muss ein Buchstabe oder eine
  Ziffer im Alphabet des Nutzers sein (`str.isalnum`, unicode-fähig — `Prüfbericht` geht durch) oder
  `_`, `-`, `.`. Enger als ein Dateisystem verlangt, und zwar absichtlich: dasselbe Wort ist
  Pfadsegment UND Shell-Wort, und nur die engere der beiden Antworten ist für beides sicher.
* `as_shell_value` ersetzt in JEDEM gedruckten Wert die Zeichen, die eine Shell **innerhalb eines
  doppelt gequoteten Wortes** ausführt — `$`, Backtick, Backslash, `"` und Steuerzeichen. Eine
  Definition für beide Shells, weil die gedruckte Zeile eine Zeile ist. `&`, `;` und Klammern
  bleiben **stehen**: sie sind innerhalb von `"…"` in bash wie in PowerShell literal, und ein Test,
  der sie verböte, würde eine Regel messen, die der Code nicht hat.
* Zwei rote Tests: `test_a_class_name_that_would_become_shell_syntax_is_not_proposed` (drei
  Klassen abgelehnt, die gewöhnliche daneben vorgeschlagen; kein `$`/Backtick/Backslash in einer
  gedruckten Zeile, gerade Anzahl `"`) und `test_an_owners_own_words_stay_readable_in_the_printed_reason`
  (die Gegenrichtung: Umlaute, `&`, `%`, Satzzeichen überleben). Beide ohne den Fix rot.
* Der gedruckte NOT-PROPOSED-Satz und die Manager-SKILL sagen jetzt beide **beides**: Ordnername
  UND Wort auf der Kommandozeile.

**Grenze der Definition, benannt statt als Loch geführt:** „beide Shells" heißt bash und PowerShell —
die zwei, für die der Einstiegspunkt dieses Kits geschrieben ist und auf die die Haken registriert
sind. `cmd.exe` expandiert `%VAR%` auch in Anführungszeichen; es gibt in diesem Kit kein Werkzeug,
das dorthin führt, also existiert keine erreichbare Kette und ich trage kein `H101` ein.

## F7 — ein Wort zu viel (geschlossen)

`_readings.py`: „a shell line that names the path NOWHERE (a glob, a script)". Der Glob ist gemessen
**rc 2**. Der Satz nennt jetzt nur noch die Skriptform, verweist auf `H11` und sagt ausdrücklich,
dass der Glob eine Runde lang falsch dort stand.

## F8 / F9 — Protokollpräzisierungen (in §3 und §1 eingearbeitet)

* §3 sagt jetzt genau, was der E2E-Test fährt (`kernel.filing.apply` mit dem aus den GEDRUCKTEN
  Flags gebauten Manifest, Freigabe durch den echten Haken) und was er **nicht** fährt (die
  argparse-Schicht von `add-filing-rule`).
* §1 kennzeichnet die Laufzeittabelle als hostabhängig und nennt drei Messpunkte für dieselbe Zelle:
  0,240 s (dieser Host, unbelastet, Endstand) / 0,487 s (derselbe Host unter Suite-Last) / 0,808 s
  (Host des Prüfers).

## Läufe der Nacharbeit

* `python -m ruff check .` — **All checks passed**
* `python tools/gen_known_holes.py --check` — **up to date** (die Runde fügt keinen
  `known_hole`-Marker hinzu; die H-Nummern der Löcherliste speisen diese Datei nicht)
* `python tools/bump_kit_version.py` — office **2026.09.02-2** (provisorisch; dev/research unverändert `2026.09.01-1`) — der
  letzte Stempel deckt eine reine Textkorrektur in `ENFORCEMENT.md` nach dem Suitenlauf:
  die Zeile behauptete für den Buchungs-Store zwei gemessene Schreibweisen, während ich in
  `probe_h99b.py` acht gemessen habe; sie nennt jetzt die acht und die eine, die durchkommt.
* `python tools/validate.py` — **all structural checks passed**
* Betroffene Suiten: **3268 passed, 13 skipped, 0 failed** in 30:13 min
  (`_round-scratch/TSK-0102/suite-final2.txt`)
* Rot-zuerst der Nacharbeit (`redfirst2.py`, Kopie außerhalb des Repos), fünf Mutationen, alle rot:

| Mutation | Wird ROT |
|---|---|
| F3: Umlenkung entfernt, echter Pfad wieder benutzt | `test_the_real_harvest_record_is_not_a_test_fixture` |
| F4: ZEILEN-Prüfung des Budgets entfernt | `test_a_booking_check_that_runs_out_of_time_refuses_instead_of_being_killed` |
| F4b: DATEI-Schleife merkt das verbrauchte Budget nicht | dieselbe |
| F5: `usable_segment` zurück auf die Verbotsliste | `test_a_class_name_that_would_become_shell_syntax_is_not_proposed` |
| F5b: gedruckte Werte gehen nicht durch `as_shell_value` | `test_an_owners_own_words_stay_readable_in_the_printed_reason` |

Die elf Mutationen der Erstrunde (§4) bleiben gültig; die Fassungen, an denen sie hängen, sind durch
die Nacharbeit nur ergänzt, nicht ersetzt.

## Was die Nacharbeit an §8 ändert

Neu in der Liste dessen, was **bewusst nicht geschlossen** ist:

8. **`H99` — die Buchungsschicht ist so weit erkannt, wie `requires_a_sound_ledger` reicht.** Ein
   Skript trägt eine ungelesene Zeile nach `HEAD` (dauerhaft ausgenommen) und prägt die zweite
   Lesung. Blockierend, als benannte Ausnahme geführt, Abnahme des Nutzers offen. Nicht von hier aus
   schließbar: es ist `H11`s Klasse, und sie liegt in `gate_write_scope` und `gate_ledger_valid` —
   zwei Dateien, die diese Schicht nicht besitzt.

Unverändert offen bleiben die Punkte 1–7 aus §8, insbesondere: **der `report-gap`-Verb ist weiterhin
nicht verdrahtet** (Seam, §2), und damit ist FR-0062 weiterhin halb geliefert.

---

# 10. LETZTE NACHARBEIT (2026-09-02 01:06 → 01:40 +0200)

Der Prüfer bestätigte alle sieben Vorrundenbefunde als geschlossen (F5 sogar über den ganzen
Unicode-Raum gemessen). Es blieben ein blockierender Befund und zwei kleine.

## N2 — ein roter Test IM gelieferten Baum (blockierend, geschlossen)

`tools/test_shortening_net.py::test_no_section_of_a_pinned_instruction_file_disappears_unnoticed`
war rot: vier gepinnte Abschnitte hatten sich bewegt, alle durch diese Runde —

* GEÄNDERT `office agents/office-manager.md` „What you are and are not" (Aktenplan-Bullet, FR-0031)
* GEÄNDERT `constitution/AGENTS.md` „2. Hard rules" (Vier-Augen-Buchung in II.9 + die zwei neuen
  Haken in der vollständigen Liste, FR-0065)
* GEÄNDERT `hooks/ENFORCEMENT.md` „1. What each mechanism refuses" (neue Zeile + der korrigierte
  `HEAD`-Satz, H99)
* NEU `skills/office-manager/SKILL.md` „The Aktenplan at onboarding" (die Sequenz, die FR-0031
  verlangt)

Neu aufgenommen mit `python tools/pin_constitution_sections.py --write --note "…"`; die Notiz nennt
jede der vier Bewegungen mit ihrem Grund und ist als **provisorisch** gekennzeichnet (DEC-0057 c,
Journalzeile in `docs/reviews/phase0-disposition.md`). Danach grün: 36 passed.

**Die URSACHE, und sie ist meine:** `tools/test_shortening_net.py` stand nicht in den neun Suiten,
die ich als DEC-0050-betroffen ausgewählt hatte — obwohl die Runde vier gepinnte Instruktionsdateien
ändert und diese Suite damit **per Konstruktion** betroffen ist. Die Auswahl war nach Themen
gemacht („Office-Haken, Rollen, Kernel, Hygiene") statt nach der Frage, welche Datei die Runde
anfasst und wer sie liest. Die Suite ist jetzt Teil des Abschlusslaufs. Und §6 dieses Protokolls
sagte „`tools/constitution_section_pins.json` unverändert" — das war schlicht falsch; korrigiert.

## N1 — die Budget-Summe stand als Prosa da (geschlossen)

`_bookings.py` rechnete im Kommentar „40 + 15 = 55 < 60", und die 40 war eine Kopie einer Konstante
aus `gate_ledger_valid.py`. Kein Test las beide zusammen: der vorhandene hält nur
`gate_ledger_valid.TOTAL_BUDGET < 60`, also bliebe bei 50 + 15 = 65 alles grün, während die
GEKETTETEN Gates den 60-Sekunden-Deadline überlaufen — und ein getöteter Haken ist ein Durchlass.

* Neu: `tools/test_hooks_v2.py::test_the_two_ledger_gates_budgets_together_fit_inside_the_hook_deadline`
  liest alle drei Zahlen aus den Modulen (`gate_ledger_valid`, `_bookings`, `_compat`) und prüft die
  SUMME; dazu ein Zahn gegen ein Budget von 0.
* Die Arithmetik ist aus dem Kommentar raus; er nennt jetzt den Test.
* **Rot ohne den Fix:** `gate_ledger_valid.TOTAL_BUDGET` auf 50 gesetzt → mein Test rot, die
  19 Nachbartests derselben Auswahl **grün** — genau die Lücke, die der Befund nennt.

**Vorbestehend, nicht meine Runde, hier nur notiert:** `tools/test_hooks_v2.py:9428` enthält ein
`assert … or True` — ein Test, der nicht scheitern kann. Nicht angefasst, weil er außerhalb dieses
Auftrags liegt.

## N3 — Windows-Gerätenamen (mitgenommen)

`usable_segment` ließ `CON`, `PRN`, `AUX`, `NUL`, `COM1`–`COM9`, `LPT1`–`LPT9` durch: alles
Buchstaben und Ziffern, also sagte die Alphabet-Regel ja — und Windows legt den Ordner trotzdem nie
an. Der Schaden ist die unleserlichste Sorte: der Plan nimmt die Regel, der Nutzer gibt sie frei,
und die ABLAGE scheitert viel später mit einem Betriebssystemfehler, den niemand mit dem Onboarding
verbindet. `con` ist eine plausible Abkürzung für eine Schublade.

`RESERVED_ON_WINDOWS` schließt sie aus, auf den STAMM vor dem ersten Punkt angewandt (`CON.txt` ist
ebenfalls reserviert). Es ist eine Aufzählung, weil das Betriebssystem hier der Aufzählende ist; der
Kommentar sagt das. Roter Test: `test_a_class_name_windows_cannot_make_a_folder_of_is_not_proposed`
— beide Enden, denn `console` wird weiter vorgeschlagen (die Regel gilt dem Stamm, nicht einem
Präfix). Ohne den Ausschluss rot.

## cmd.exe — die Begründung steht jetzt am Code

Der Halbsatz sitzt im Docstring von `as_shell_value`: die zwei Shells sind die, auf die die Haken
registriert sind; `cmd.exe` ersetzt in `"…"` nur `%VAR%`, kein Werkzeug dieses Kits führt dorthin,
und der Schaden wäre ein verfälschter FRAGETEXT, nie ein laufender Befehl. Darum ein Satz und kein
Loch.

## Läufe der letzten Nacharbeit

* `python -m ruff check .` — **All checks passed**
* `python tools/validate.py` — **all structural checks passed**
* `python tools/bump_kit_version.py` — office **2026.09.02-3** (provisorisch; dev/research
  unverändert `2026.09.01-1`)
* Abschlusslauf, jetzt **mit `test_shortening_net.py`**: `test_hooks`, `test_hooks_v2`,
  `test_role_contracts`, `test_schemas`, `test_kernel`, `test_repo_hygiene`, `test_gaplog`,
  `test_disposition`, `test_context_budget`, `test_shortening_net` →
  **3306 passed, 13 skipped, 0 failed** in 28:09 min
  (`_round-scratch/TSK-0102/suite-final3.txt`)
* Rot-zuerst (`redfirst3.py`, Kopie außerhalb des Repos), drei Mutationen, alle rot:

| Mutation | Wird ROT |
|---|---|
| N1: `gate_ledger_valid.TOTAL_BUDGET` auf 50 (Kette 65 s gegen 60 s) | `test_the_two_ledger_gates_budgets_together_fit_inside_the_hook_deadline` (19 Nachbartests bleiben grün) |
| N2: Abschnitts-Pins zurück auf den Stand von `c155a5f` | `test_no_section_of_a_pinned_instruction_file_disappears_unnoticed` |
| N3: `usable_segment` schließt die Gerätenamen nicht mehr aus | `test_a_class_name_windows_cannot_make_a_folder_of_is_not_proposed` |

## Korrektur an §6 dieses Protokolls

`tools/constitution_section_pins.json` ist **nicht** unverändert. Die Merge-Runde muss **zwei**
Ratschen neu aufnehmen, nicht eine:

* `tools/lead_package_sizes.json` — office 47 793 → 49 353 B (+1 560), Notiz im Journal
* `tools/constitution_section_pins.json` — vier Abschnitte (drei geändert, einer neu), Notiz im
  Journal

Beide provisorisch nach DEC-0057 c.
