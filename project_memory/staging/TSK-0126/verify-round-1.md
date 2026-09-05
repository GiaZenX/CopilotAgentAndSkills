# TSK-0126 — Merge-Prüfung Runde 1 (harness-verifier)

Gemessen am **gemergten Arbeitsbaum** `C:/Offline Repos/AgentAndSkills` (feat/harness-v2 @ 75a00d1
+ Working Tree), read-only; alle Läufe in einer `.git`-losen Kopie unter
`C:/Offline Repos/v2-testbed/_round-scratch/TSK-0126/verify/`. Rig unter `verify/rig/`
(`_rig.refuse_outside_rig()` + ausschliesslich binäres Lesen/Schreiben, `DEC-0070`).

**URTEIL: FAIL** — ein blockierender Befund (B1), ein blockierender Listen-Befund (B2), drei
mittlere, vier kleine. Der Merge selbst ist technisch sauber: AST-Vereinigung, Verfassungsnähte,
Migration, Stempel, Zeilenenden und Gate 5 halten jeder Messung stand. Was fällt, sind zwei
BEHAUPTUNGEN über Reichweite — eine im Loch-Eintrag `H163`, eine im Gate-5-Loch, das es nicht gibt.

---

## Befunde, blockierend zuerst

### B1 — BLOCKIEREND: Das research-Kit hat dieselbe Sackgasse wie office; Protokoll und `H163` behaupten das Gegenteil

`docs/POST_V2_WISHLIST.md:9731` — *„Zum Vergleich das research-Kit: seine Auftraege leiten von einem
`EXP` ab, und `EXP` traegt `success_criteria`, also fragt die Pflicht dort nie. **Nur das
office-Kit** steht ohne Ausweg in seinen eigenen Texten da."*
`project_memory/staging/TSK-0126/merge-protocol.md:94` — *„**Nicht** in research … also fragt die
Pflicht dort nie — gemessen"*.

Gemessen an einem **wirklich gescaffoldeten research-Piloten** (`verify/rig/e_research.py`,
`init_project_memory.ps1` + `scaffold_team.ps1` aus einer Kit-Kopie im Scratch, Kernel-Lease über
`dispatch.create_lease`):

```
=== RESEARCH pilot ===
  does the research template ship a home for SR (system/active)? False
  TSK derives_from an EXP (the prescribed shape)       -> LEASE GRANTED (rc 0)
  TSK derives_from the RQ root                         -> REFUSED DispatchError
        TSK-0001 hangs from RQ-0001 (class 'feature'), and no SR in status ACCEPTED hangs from that goal
  TSK derives_from a HYP                               -> REFUSED DispatchError
        TSK-0001 hangs from RQ-0001 (class 'feature'), and no SR in status ACCEPTED hangs from that goal
```

Die Pflicht fragt in research also **immer dann**, wenn der Ursprung kein `EXP`/`BUG`/`CR` ist — und
das ist keine exotische Form: `_assert_origins_belong_to_root_locked` lässt `derives_from: RQ` und
`derives_from: HYP` zu, und nur die Skills von researcher/data-analyst schreiben `EXP` vor. Die
Vorlage `team-kits/research-team/templates/project_memory/` liefert **kein** `system/`-Verzeichnis
(die Heimat von `SR`), und die research-Verfassung hat den Architektenschritt-Absatz nach der
bewussten Abweichung dieser Runde **nicht** bekommen. Ein research-Projekt trifft damit dieselbe
Verweigerung wie office, deren Abhilfewort in seinen eigenen Texten nicht vorkommt.

Warum blockierend: die bewusste Abweichung der Runde („der Architektenschritt steht NUR in
dev-team") ruht auf dieser Behauptung, und die Nutzerentscheidung, die der Lead vorlegt, wird als
office-Frage gestellt, obwohl sie zwei Kits betrifft. Hausregel 3 in beide Richtungen: ein Dokument
darf keine Abwesenheit behaupten, die der Code nicht baut.

**Minimalfix:** die zwei Sätze korrigieren (H163 und Protokoll §3a) auf „office **und** research,
für jeden Auftrag, dessen Ursprung kein `EXP`/`BUG`/`CR` ist"; die zwei gemessenen research-Zeilen
in H163s Kettentabelle aufnehmen; die Nutzerfrage als Zwei-Kit-Frage stellen.

**Was eine Verengung konkret ändern würde** (für die Option, die der Lead dem Nutzer vorlegt):
`kernel/dispatch.architect_step_owed` (`team-kits/kernel/dispatch.py`, erste Zeile des Rumpfes) —
ein zusätzliches frühes `return False`, abgeleitet und nicht als Kit-Liste:
`os.path.isdir(os.path.join(state.root, ACTIVE_DIRS[ARCHITECT_STEP_TYPE]))` ist falsch → die Pflicht
fragt nicht. Gemessen: dev-team liefert `system/` in seiner Vorlage, office und research **nicht**
(`verify/rig`-Lauf oben und `ls */templates/project_memory`). Das ist eine Eigenschaft des
gescaffoldeten Bestands, keine Aufzählung von Kit-Namen, und sie fällt in genau den beiden Kits, in
denen `SR` in keinem Text steht.

### B2 — BLOCKIEREND für Ausgabe (3): eine gemessene, offene fail-open-Klasse von Gate 5 steht in keinem Loch

`.claude/hooks/gate_test_scope.py:31` behauptet als Eigenschaft: *„A word STRICTLY INSIDE a root (a
sub-path, a node id `file::name`) narrows the run and is therefore a selection"*. Ein **Glob**
innerhalb der Wurzel verengt aber nichts — die Shell expandiert ihn auf die ganze Fläche.

Gemessen als Prozess gegen die gemergte Kopie (`verify/rig/f_gate5d.py`, JSON auf stdin, `cwd` wie
vom Provider):

```
tools/ holds 40 test_*.py files
  rc 0 ALLOWED | python -m pytest tools/test_*.py -q
  rc 0 ALLOWED | python -m pytest tools/test_[a-z]*.py -q
  rc 2 REFUSED | python -m pytest tools/ -q
  rc 2 REFUSED | python -m pytest $(ls -d tools) -q
```

`pytest tools/test_*.py` fährt alle 40 erklärten Suitendateien — 42 Minuten, genau die Fehlerklasse,
für die das Gate gebaut ist, und keine Umgehungsabsicht, sondern eine gewohnte Schreibweise. Weder
`H151` noch `H152` (Optionen) noch `H153` (Läufer aus einer Expansion / nicht platzierbarer Ort)
decken einen POSITIONALEN Glob ab; `grep -i glob|wildcard` über `gate_test_scope.py` ist leer. Der
Auftrag reserviert `H165` und lässt es **unbenutzt** — hier ist sein Eintrag.

**Minimalfix:** entweder ein Wort mit `*`, `?` oder `[` innerhalb einer erklärten Wurzel als
NICHT-Auswahl lesen (Über-Verweigerung, die sichere Richtung, mit Satz auf der Zeile), oder `H165`
mit Mechanismus, obiger Kette, Urteil und Begrenzung schreiben.

### M1 — Der Schiedsrichter der Zeigernaht liest die Fortsetzungsform nicht, die die neuen Sätze benutzen

Protokoll §3 Zeilen 2 und 10 nennen
`tools/test_repo_hygiene.py::test_every_test_pointer_this_repo_writes_resolves` als Schiedsrichter
dafür, dass „jeder Zeiger auflöst". `tools/test_repo_hygiene.py:1013` verlangt aber
`\A(?P<path>[\w./-]*test_[\w-]+\.py)::(?P<name>test_\w*)\Z` — die Fortsetzungsform `` `::test_x` ``,
mit der die vier neuen G4-2-Sätze in allen drei Verfassungen und beide `parallel-streams`-Skills ihre
zweiten und dritten Zitate schreiben, hat keinen Dateiteil und wird gar nicht angesehen.

Mutation gemessen (`verify/rig/b_mutations.py`), in
`team-kits/dev-team/constitution/AGENTS.md`
`::test_a_seam_both_orders_declare_lets_the_second_lease_through` → `…throughX`:

```
[pointer sweep: a test citation in the dev constitution that does not exist]
    mutated -> rc 0 | 1 passed in 66.59s
    restored -> rc 0 | 1 passed in 66.08s
```

Die Aussage „jeder Zeiger löst auf" ist heute **wahr** (eigene Messung: 49 Zitate in
`team-kits/**/*.md`, 0 unaufgelöst) — gemessen wird sie nur zur Hälfte.
**Minimalfix:** in `_test_citations` die zuletzt genannte Suitendatei über den Absatz mitführen und
den Fall in `test_the_test_pointer_reader_reads_the_shapes_a_kit_file_writes` als Boden aufnehmen.

### M2 — `H163` nennt zwei Tests als das, was die Regel hält; beide bleiben grün, wenn man die Regel löscht

`docs/POST_V2_WISHLIST.md:9743` — *„Gehalten wird die Regel selbst von
`…::test_only_an_origin_that_carries_criteria_excuses_the_architect_step` und
`…::test_a_small_goal_is_not_asked_and_neither_is_a_bugfix_order`."*

Mutation (`verify/rig/d_mutations.py`): `dispatch.architect_step_owed` gibt immer `False` zurück
(die Pflicht ist damit weg):

```
  test_approvals_dispatch.py as shipped: rc 0 | 194 passed
  with the duty removed:                 rc 1 | 2 failed, 192 passed
      RED: test_a_goal_of_an_unknown_class_is_asked_for_the_architect_step
      RED: test_an_order_deriving_from_a_proposed_requirement_is_still_asked
  restored:                              rc 0 | 194 passed
```

Die beiden GENANNTEN Tests sind unter den 192 grünen. **Minimalfix:** in H163 die zwei Tests nennen,
die wirklich rot werden.

### M3 — Drei veraltete Zahlen im ausgelieferten Protokoll (eine davon die, gegen die der Nutzer misst)

1. `merge-protocol.md:77` (Naht 8): *„der neue Kit-Haken ×3 byte-gleich `8e5c8dff65a6`"* —
   gemessen `9ee53c33a77a`, und §8 desselben Dokuments nennt ebenfalls `9ee53c33a77a`. Zwei Werte
   für eine Datei in einem Dokument; die Zeile stammt aus der Zeit vor M8/M9.
2. `merge-protocol.md:73` (Naht 4): *„`git diff --numstat` = **25 / 1**"* — gemessen
   `40  2  docs/reviews/phase0-disposition.md` (die Runde hat danach ihre eigenen 9 Dispositions-
   und 3 Grössenzeilen angehängt).
3. `merge-protocol.md:129` (Tabelle des schreibenden Laufs): *„Lauf 1: 152 Items, 152 Prosadateien",
   Dokument 191 513 B, sha `be9a465b`*. Gemessen gegen das GEMERGTE Dokument
   (`verify/rig/c_idem.py`): **154 Items, 154 Indexzeilen, 191 836 B, sha `53b805f2f9e26ec6`** — und
   das ist byte-gleich mit dem, was das eigene Log `judges-run3.txt` der Runde schon sagt
   („154 written … 154 prose files"). Der Nutzer vergleicht seinen EINEN schreibenden Lauf gegen
   diese Tabelle. **Minimalfix:** Tabelle auf 154 nachziehen oder als Vor-H163/H164-Messung
   kennzeichnen.

### m1 — Ausgabe (7) verlangt eine ZEIGERTABELLE; es gibt nur eine Nahtzeile

`merge-protocol.md` hat §3 (Nahttabelle, Zeile 10 = „Zeiger"), §7 (Löcher), §9 ((g)), §10
(Zuschnitt), §0 (verworfener Weg). Eine eigene Zeigertabelle fehlt.

### m2 — Der Zuschnittbefund Z6 nennt eine Datei; gemessen sind es zwei ausserhalb `allowed_scope`

`verify/rig/j_tree.py`: ausserhalb von `allowed_scope` berührt sind `user/claude/statusline.py`
(Z6 nennt es), **`.gitignore`** (nennt Z6 nicht) und das vorbestehende untracked
`radar/2026-09-04-claude.md`. Beide sind inhaltsgleich zu HEAD, also kein Schaden — der Mechanismus
ist aber „der Normalisierer läuft über den ganzen Checkout", nicht „eine Datei".

### m3 — `PR-0004` AC-2 ist wörtlich nicht geliefert (angenommene Abweichung)

AC-2 verlangt: *„When any hook entry lacks a timeout, Then a shipped test is red"*. Gemessen
(`verify/rig/seams.py`): dev 1/31, office **0/30**, research 1/28 Kit-Einträge nennen ein `timeout`;
`_kernel.start_the_deadline` verweigert einen Eintrag ohne Fenster ausdrücklich **nicht**. Das ist
die vom Lead ANGENOMMENE Abweichung (Standardfenster des Providers, Eigenschaftstest
`tools/test_hooks.py::test_a_registration_names_a_window_exactly_when_its_gate_can_outlive_the_default`)
— sie muss im Urteil je Ziel als Abweichung stehen, nicht als Erfüllung.

### m4 — `PR-0007` AC-1 ist in dieser Runde nicht entscheidbar

Der gehostete CI-Lauf braucht den Push (Nutzerwort). Protokoll §11 (2) nennt das; im Ziel-Urteil
bleibt AC-1 OFFEN.

---

## Ergebnis je erwarteter Ausgabe

| # | Ausgabe | Urteil |
|---|---|---|
| 1 | vier Patches in Nahtreihenfolge, Normalisierung dazwischen | **PASS** |
| 2 | zehn Nähte von Hand mit Schiedsrichter | **PASS mit Einschränkung** (M1: der Schiedsrichter der Zeigernaht deckt eine Zitatform nicht; M3.1/M3.2 veraltete Zahlen) |
| 3 | Löcherliste H151–H165 in einer Ordnung | **FAIL** (B2: gemessene offene Klasse ohne Eintrag; B1: falsche Reichweite in H163; M2: Testnennung hält nicht) |
| 4 | Merge-Befunde rot-zuerst behoben oder benannt; Zuschnittbefunde tabelliert | **PASS mit Einschränkung** (m2) |
| 5 | EIN Stempel, voller Lauf einmal, test_gates, ruff, validate, Gate 5 als Prozess | **PASS** |
| 6 | Hostregel | **PASS** |
| 7 | Protokoll mit allen Tabellen | **PASS mit Einschränkung** (m1 Zeigertabelle fehlt; M3 Zahlen) |

## Ergebnis je Ziel

| Ziel | AC | Urteil |
|---|---|---|
| **PR-0004** | AC-1 (Gate 5) | PASS als Prozess gemessen; **B2** ist der unbenannte Rest |
| | AC-2 (timeouts) | **ABWEICHUNG, vom Lead angenommen** (m3) — wörtlich nicht geliefert |
| | AC-3 (design checks) | nicht gemessen (kein dev-Pilot mit gebauter App gefahren) |
| | AC-4 (Kostenseite) | PASS — Schwelle ist Daten (`tools/test_surface.json`), im Gate-Kopf begründet |
| **PR-0005** | AC-1..AC-5 | PASS im gemergten Baum: Kontrakte gebaut, Fixtures fragen den Kernel statt ihn zu kopieren (Mutation: Fixture aus → 100 von 194 rot), Kollisionstür verweigert, Lease-Verweigerung + Arbeitsbaum gemessen. **B1** ist die Reichweite, die AC-3 (`FR-0085`) über die Kits hinweg offenlässt |
| **PR-0006** | AC-1 | PASS für die Grenze: `H158` bleibt offen, gemessen (`_routine.py`/`session_status.py` numstat leer, Nahttest grün) |
| | AC-2/AC-3 | PASS (Skills ×3, Verfassungsabsatz byte-gleich ×3, Schiedsrichter rot-zuerst gemessen) |
| | AC-4 | PASS (`DEC-0070` 4× in `.claude/agents/harness-lead.md`, jeweils mit Zeiger) |
| **PR-0007** | AC-1 | **OFFEN** — braucht den Push (m4) |
| | AC-2 | PASS: 52 Dateien normalisiert und byte-gleich zu HEAD, 0 CR in jeder geänderten Textdatei ausser dem einen unerreichbaren Auditlog, `check-attr` `text: auto`/`eol: lf` |
| | AC-3 | PASS (kitupdate.py, ein Schreiber) |
| | AC-4 | PASS für die gemessene Lastklasse, Rest benannt (H162) |

---

## Ausdrückliche Negativbefunde — GEMESSEN

* **(a) AST-Vereinigung** (`verify/rig/a_ast_union.py`, Patches einzeln auf `git show 75a00d1:…`
  angewandt, `core.autocrlf=false`): Basis **283** Definitionen, gemergt **323**, Vereinigung nach
  Abzug der 10 von G4-2 entfernten = **323**. `missing 10` sind exakt die von G4-2 entfernten,
  `extra 0`, `duplicate names []`. **Und stärker als eine Namensmenge:** für jede Definition, die ein
  Strom geändert hat, trägt die gemergte Datei den Rumpf DIESES Stroms („none — every definition a
  stream changed carries that stream's body"). G4-4s einzige geänderte Definition ist
  `test_gate3_answers_before_its_registration_however_costly_the_line_is_to_judge`.
* **(b) Verfassungen** (`verify/rig/b_constitutions.py`): die drei geteilten Blöcke byte-gleich ×3
  (verworfene Alternative 880 Zeichen, Posteingang 523, Lease 894); Architektenschritt nur dev
  (688); `gate_test_scope` in der Inventarzeile ×3 (dev:92, office:191, research:73); das tote Zitat
  steht in keinem ausgelieferten Text mehr (einzige Restnennung: der Docstring des ersetzenden Tests
  `tools/test_parallel_streams.py:338`, als Historie); 49 Zitate in den Kit-Texten, 0 unaufgelöst.
  Mutationen: ein Wort im office-Absatz → `test_a_paragraph_the_constitutions_share_is_one_text`
  1 failed → restauriert 1 passed; `gate_test_scope` aus der Inventarzeile (dev bzw. research) →
  `tools/test_shortening_net.py` 3 failed / 33 passed → restauriert 36 passed.
* **(b) Übersetzung**: Inhalt und Testnamen der vier deutschen G4-2-Sätze (TSK-0122 §8) sind in den
  englischen Fassungen erhalten; die SR-Pflicht steht in der korrigierten Form („An `SR` origin never
  exempts … it satisfies the duty only by BEING the accepted architect step"), was `dispatch.py`
  auch baut.
* **(c) Migration**: Probelauf über das gemergte Dokument gegen eine frische `project_memory`-Kopie
  ausserhalb des Repos → **„154 written, 0 already in the store, 0 prose files"**, rc 0, keine
  Kollision. Schreibender Lauf gegen den fertig migrierten Bestand → rc 0, **„0 written, 154 already
  in the store"**, Dokument 795 232 → 191 836 B, sha `53b805f2f9e26ec6`, **byte-gleich** mit dem
  Ergebnis des Umsetzers, 154 Indexzeilen, 0 CR.
* **(c) Tür-Angriff**: derselbe Dokumentabschnitt `H151` mit geändertem Mechanismus gegen den
  Bestand → **rc 1**, Verweigerung nennt Feld (`observed`) und beide Lesarten. H165 kommt im
  Dokument nicht vor (kein Item dafür erzeugt).
* **(c) H164s eigene Klasse**: 179 `regression_tests`-Einträge über die migrierten Items, **jeder**
  löst auf genau einen Test auf.
* **(d) M5/M6**: Fixture `satisfy_the_architect_step` abgeschaltet → `tools/test_approvals_dispatch.py`
  **100 failed / 94 passed**; restauriert 194 passed. Die Verweigerung wird also wirklich getroffen.
* **(d) M7**: die Eigenschaft „kein Traceback" mit ihrem benannten Test in `tools/test_hooks_v2.py`
  vorhanden, beide Richtungen als Wegwerf-Werkzeuge gemessen.
* **(d) M8/M9/M10**: die vier Schiedsrichter (`test_migrate`, `test_hooks`,
  `test_the_registration_is_the_one_the_contract_asks_for`, `test_each_gate_refuses_on_every_tool_
  name_it_is_registered_for`) 17 passed; Mutation „Gate 5 aus `.claude/settings.json` entfernt" →
  1 failed. `tools/test_parity_sources.py` 9 passed.
* **(e) H163 am echten office-Piloten** (gescaffoldet, `create_lease` über den Kernel):
  `class='feature'` REFUSED, `class=None` REFUSED, `class='small'` rc 0,
  `class='technical_enabler'` rc 0, `class='feature'` + ACCEPTED `SR` unter dem `PROC` rc 0. Das
  Wort `SR` kommt in `team-kits/office-team/**/*.md` **0 mal** vor.
* **(f) Gate 5 als Prozess** (`verify/rig/f_gate5.py`, echter Haken, JSON auf stdin): bare full run
  **rc 2**; `DELIVERY_RUN=TSK-0126` **rc 0** (auch in der PowerShell-Schreibweise); geschlossenes
  Item **rc 2**; Unsinn **rc 2**; eine Datei / zwei Dateien / ein Knoten **rc 0**;
  `.claude/hooks/test_gates.py` in voller Länge **rc 2**, mit Präfix **rc 0**; Rig ausserhalb des
  Repos **rc 0**; `grep -rn pytest tools/` **rc 0**; Payload ohne `cwd` **rc 2** (fail-closed, eigener
  Satz). Schreibweisen der ganzen Fläche (`tools`, `"tools/"`, `./tools`, absoluter Pfad in
  Anführungszeichen, `tools//`, `tools/.`, `tools/../tools`, `.`, `..`, `cd tools && pytest .`,
  hinter Pipe/Umleitung, ohne Positional) **alle rc 2**.
* **(f) EXPECTED_TOOLS**: `test_the_registration_is_the_one_the_contract_asks_for` vergleicht in
  beide Richtungen und ist rot, wenn Gate 5 aus der Registrierung fällt. **Jeder** der sechs Einträge
  in `.claude/settings.json` nennt ein `timeout` (alle 120), und
  `test_every_registered_hook_states_the_time_it_gets` wird rot, wenn man Gate 5s `timeout` entfernt
  (gemessen: 1 failed → restauriert 2 passed).
* **(g) Stempel**: `2026.09.05-2` ×3, `tools/bump_kit_version.py --check` → „unchanged" ×3.
  Reihenfolge: letzte Inhaltsänderung im `allowed_scope` `tools/test_hooks_v2.py` **08:14**, Stempel
  **07:31**, Lieferlauf-Log **08:58** — **nach** dem Lieferlauf ist im `allowed_scope` **nichts**
  mehr angefasst worden; die einzigen späteren Schreibvorgänge (09:17) sind der Zustand des Leads
  (`generated/*`, `staging/generation-4-streams.md`, `DEC-0074`).
* **(h) Lieferlauf**: `full-run-3.txt` **4682 passed / 14 skipped / 0 failed, 42:28**, im echten Repo
  gefahren (Pfad in der Warnung); `gates-run-2.txt` **7 failed / 537 passed**, und die sieben sind
  namentlich die migrierten Richter.
* **(j) Baum**: 79 inhaltlich geänderte Dateien; 52 im Arbeitsbaum berührte ohne Inhaltsänderung,
  **alle 52 byte-gleich zu HEAD**; 0 CR in jeder geänderten Textdatei ausser
  `project_memory/.audit/hook_events.jsonl` (607 CR, die eine unerreichbare);
  `git check-attr` `text: auto` / `eol: lf` für `.md` wie `.py`; die `VERSION`-Diffs enthalten nur
  den Stempel. Spiegel: `hooks/gate_test_scope.py` ×3 `9ee53c33a77a`, `hooks/_kernel.py` ×3
  `13e47244d9aa`, `kit_browser_checks.py` und `skills/parallel-streams/SKILL.md` dev == research.
  `project_memory/`-Änderungen sind sämtlich die des Leads; vom Merge geschrieben ist dort nur
  `staging/TSK-0126/`.
* **Nebenwerkzeuge**: `record_lead_package_sizes.py` „every size is the one on record" (dev 51 847,
  office 56 728, research 54 162 — genau die Protokollzahlen); `tools/validate.py` grün.

## Ausdrücklich NICHT gemessen

* Die volle `tools/`-Suite (DEC-0050) — das Lieferlauf-Log gelesen und nachgerechnet, nicht neu
  gefahren; ebenso `ruff` (Behauptung übernommen).
* **Ob der Lieferlauf wirklich das Präfix `DELIVERY_RUN=TSK-0126` trug**: das Log echot keine
  Umgebung, Gate 5 bindet erst beim nächsten Sitzungsstart, und es existiert kein `EVD` mit
  `run_scope: full` und `related: TSK-0126` — die „einmal"-Hälfte des Gates ist im Moment des Laufs
  also unbewiesen und unerzwungen (zweimal dasselbe Präfix ist heute rc 0 / rc 0, gemessen).
* Ein vollständiger schreibender Migrationslauf aus dem UNmigrierten Bestand heraus: mein eigener
  lief unter fremder Hostlast (acht CPU-gebundene `python.exe` eines Fremdjobs ab 09:40) in den
  900-s-Timeout; die Eigenschaft wurde stattdessen gegen den fertigen Bestand gemessen.
* `PR-0004` AC-3 (Browser-Checks an einer gebauten App) und die Spawn-Hälfte des Architektenschritts
  über den Kit-Haken `gate_dispatch` — gemessen ist die Lease-Hälfte.
* `PR-0007` AC-1 (gehosteter CI-Lauf) und die härtere Lastklasse von `H162` (Hostregel).

## Eigene Fehlgriffe in dieser Runde

* Ich habe die Timeout-Mutation zuerst mit einer zu SCHMALEN Auswahl gefahren (zwei Knoten) und
  daraus „nichts wird rot" gelesen. Mit
  `test_every_registered_hook_states_the_time_it_gets` in der Auswahl wird sie rot. Kein Befund.
* Ich habe kurz einen abgeschnittenen Testnamen (`test_gate3_answers_…_costly…`) in einem migrierten
  Item als Befund gelesen. Der Richter streift `\u2026` ab (`test_gates.py:4649`) und löst korrekt
  auf — mein Leser tat es nicht. Kein Befund.

---

## Was blockiert und was Rest ist

* **B1 blockiert die Runde**: der Fix ist drei Sätze plus zwei gemessene Zeilen, und die
  Nutzerfrage muss als Zwei-Kit-Frage gestellt werden, bevor der Nutzer sie beantwortet.
* **B2 blockiert Ausgabe (3)**, ist aber wahlweise als benannter Rest zu schliessen: `H165` ist
  reserviert und unbenutzt, der Eintrag ist eine Seite.
* **M1, M2, M3, m1, m2** sind Nacharbeiten am Text und an einem Leser, keine Sperren des Pakets.
* **m3, m4** sind keine Befunde gegen den Umsetzer, sondern Urteile je AC, die in der Abnahme
  stehen müssen.
