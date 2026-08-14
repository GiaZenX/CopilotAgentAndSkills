# `--map`-Feld → Leser → Formsicherheit: der gemessene Sweep zu BUG-0015 / AC-4

**Runde:** TSK-0033 (aus BUG-0015, Wurzel PR-0001) · **Datum:** 2026-08-14 · **Rolle:** harness-implementer

AC-4 von BUG-0015 verlangt: *„Geprueft ist, ob weitere vom `--map`-Flag gefuellte Felder einen
Leser haben, der eine Form voraussetzt: `roles` war der erste gefundene, nicht notwendig der
einzige."* Dieses Dokument hält die Messung fest — die Ableitung der Feldmenge, das Instrument, die
Tabelle, die Nachher-Zahlen und die **Grenze** der Methode samt der Lücke, die genau an dieser
Grenze gefunden wurde.

## 1. Woher die Feldmenge kommt (und wo sie aufhört)

Nicht aufgeschrieben, sondern aus dem laufenden Code abgeleitet. `migrate.parse_field_map:1145-1153`
verweigert jedes `--map TYPE.feld=…`, dessen Typ nicht in `REQUIRED_FIELDS` steht oder dessen Feld
nicht in `set(REQUIRED_FIELDS[TYPE]) | set(OPTIONAL_FIELDS.get(TYPE, ()))` liegt; `migrate._item_fields:1177`
kopiert dann genau über dieselbe Vereinigung. Die Oberfläche ist damit:

```
PYTHONPATH=team-kits python -B -c "…REQUIRED_FIELDS | OPTIONAL_FIELDS…"
→ 13 Typen · 72 (Typ, Feld)-Paare · 53 verschiedene Feldnamen
```

| Typ | Vertragsfelder (Pflicht ∪ optional) |
|---|---|
| BUG | acceptance_criteria, expected, observed, related_pr, repro, severity, title |
| CR | acceptance_criteria, change_description, target_pr, target_revision, title |
| DEC | consequences, context, decision, source, title |
| EVD | artifact_refs, kind, related, result, summary |
| EXP | derives_from, design, evidence_refs, success_criteria, variables |
| FR | related_pr, request_text, title |
| HYP | derives_from, statement, testable_prediction |
| INV | check, scope, source |
| PR | acceptance_criteria, class, goal, invariants, out_of_scope, priority, problem, title, user_story |
| PROC | derives_from, roles, steps, title |
| RQ | acceptance_criteria, class, motivation, out_of_scope, priority, question, title |
| SR | affected_components, contract, derives_from, title |
| TSK | acceptance_refs, allowed_scope, assigned_role, dependencies, derives_from, design_ref, expected_outputs, forbidden_scope, product_requirement, required_inputs, root_revision, type |

**Die Grenze steht hier, weil sie in Abschnitt 5 zubeißt:** das ist die Oberfläche des
`--map`-Flags, nicht die Menge aller Felder, die der Kernel schreibt und liest. Felder, die
ausschließlich der Kernel selbst setzt (`design_refs`, `supersedes`, `premise_rechecks`,
`approval_ref`, `revision`, …), stehen in keinem der beiden Tupel und waren für dieses Instrument
**unsichtbar**.

## 2. Das Instrument

Zwei Messungen, beide über den Code, der **läuft**, keine Zeichenkettensuche.

**(a) Ein Stolperdraht auf der Iteration.** Jeder Item-Lesevorgang dieses Codebestands geht durch
`yaml.safe_load` (`kernel/state.py:402`) — auch der der Hooks, die den Kernel als Item-Leser
benutzen. Eine `sitecustomize.py` auf dem `PYTHONPATH` ersetzt `yaml.safe_load` und hüllt jeden
**Skalar** eines Vertragsfelds in eine `str`-Unterklasse, deren `__iter__`/`__getitem__` den
aufrufenden Rahmen mit **Datei:Zeile** in eine Datei außerhalb des Repos protokollieren. Damit
meldet sich jeder Leser, der ein Wort als Folge seiner Buchstaben liest, **von selbst** — auch in
Kindprozessen, weil `sitecustomize` beim Interpreterstart geladen wird.

Positivkontrolle vor dem Bau (der Draht muss den bekannten Defekt finden, sonst misst er nichts):

```
ITER  roles  'records-clerk'  …/scripts/process_doc.py:129
ITER  steps  'file it'        …/scripts/process_doc.py:131
```

**(b) Ein Differenzlauf über beide Schreibweisen.** Für jedes der 72 Paare wird das Feld in jedem
Item, das es trägt, einmal als **Skalar** und einmal als **einelementige Liste** geschrieben, und
dann die volle Leserbatterie gefahren; die Ausgaben werden verglichen (Hashes und Uhrzeiten
normalisiert, weil die sich bei jeder Inhaltsänderung bewegen).

Batterie (13 Leser, je als **Prozess**): `kernel.cli validate | generate-index |
generate-session-brief | doctor`, `scripts/process_doc.py`, `scripts/proc_hash.py`,
`scripts/generate_dashboard.py`, `scripts/retro.py`, `scripts/kit_checks.py`, und die Hooks
`gate_test_coverage.py`, `guard_guidelines.py`, `gate_git.py`, `gate_memory_complete.py`.
Zustandsbasis: ein Projekt mit **je einem Item jedes der 13 Typen**, alle Vertragsfelder gefüllt.

**(c) Drei gezielte Sonden** für die Leser, die eine Lease, eine Bindung oder eine Freigabe
brauchen und deshalb nicht in der Batterie laufen: `dispatch.validate_dispatch` über eine echte
Lease (`create_lease` → `dispatch_header` → `parse_header`), `gate_write_scope.py` mit einem echt
gebundenen Spezialisten (`dispatch.bind_agent`), und `gate_test_coverage.py`/`guard_guidelines.py`
gegen ein `INV` in beiden Schreibweisen.

## 3. Die Tabelle

| Feld (Typen) | Leser | Formsicherheit | Beleg |
|---|---|---|---|
| `roles`, `steps` (PROC) | `office-team/.../scripts/process_doc.py:129,131` | **war unsicher — behoben** | Draht ITER + gerendertes Dokument |
| `acceptance_refs` (TSK) + `acceptance_criteria` (PR/RQ/CR/BUG), `success_criteria` (EXP) | `dispatch.validate_dispatch:465`, `dispatch._criteria_ids:911` | **war unsicher — behoben** | Sonde: SPAWN ALLOWED gegen Kriterien, die es nicht gibt |
| `allowed_scope`, `forbidden_scope` (TSK) | `gate_write_scope._scope_entries` (×3 Kits) | **war unsicher — behoben** | Sonde: `secrets/keys` rc 0 → rc 2 |
| `dependencies` (TSK) | `report.py:439`, `dispatch.py:948` | war unsicher, laute Richtung — behoben | Draht ITER `report.py:438`; 8 Befunde statt 1 |
| `derives_from` (TSK/HYP/EXP/SR/PROC), `related` (EVD), `related_pr`, `target_pr`, `product_requirement` | `report._parent_bindings`, `report:1067`, `report:945/1052`, `dispatch:123/928` | sicher — waren bereits normalisiert | Draht: kein Treffer |
| `scope` (INV) | `gate_test_coverage.py:177`, `guard_guidelines.py:128-129` + `:156`, `kit_checks.py:171,189` | **unsicher in der LISTEN-Richtung — offener Rest, `H42`** | Sonde: rc 2 → **rc 0** |
| `kind`, `result` (EVD) | `gate_git.py:254,301` | Liste → fail-closed (Merge verweigert) | Batterie `differs` |
| `root_revision` (TSK), `target_revision` (CR) | `dispatch:164,438` | Liste → fail-closed | Sonde: „planned against root revision [1]" |
| `title` (alle) | `report:185,201`, `generate_dashboard.py:369` | Liste → Python-Repr im Index; kosmetisch, kein Gate liest es | Batterie `differs` |
| `invariants`, `out_of_scope`, `goal`, `problem`, `question`, `motivation` | `approvals._SCOPE_FIELDS` — nur über `canonical_json` **gehasht**, nie zerlegt | sicher | Batterie + Quelltext |
| `assigned_role`, `type`, `class`, `severity`, `priority`, `design_ref`, `check`, `source`, `summary` | Skalarvergleiche | sicher bzw. fail-closed | Batterie: kein `differs` |
| `affected_components`, `variables`, `required_inputs`, `expected_outputs`, `artifact_refs`, `evidence_refs`, `consequences`, `context`, `decision`, `observed`, `expected`, `repro`, `request_text`, `statement`, `testable_prediction`, `design`, `contract`, `change_description`, `user_story` | kein zerlegender Leser in `team-kits/**` | sicher mangels Leser | Batterie (0 Signale) + Leserinventar |

## 4. Nachher

Derselbe Draht, derselbe Lauf, nach den Behebungen:

| | vorher | nachher |
|---|---|---|
| Paare mit Signal (Iteration oder Ausgabedifferenz) | 8 | 6 |
| Paare, in denen ein Leser einen **Skalar iteriert** | 3 (`PROC.roles`, `PROC.steps`, `TSK.dependencies`) | **0** |

Die verbliebenen sechs sind sämtlich die **Listen**-Richtung auf skalar gemeinten Feldern:
`BUG.title` (kosmetisch), `CR.target_revision` und `TSK.root_revision` (fail-closed, gemessen),
`EVD.kind` und `EVD.result` (fail-closed), `INV.scope` (**`H42`**, still).

## 5. Die Grenze und was an ihr gefunden wurde

Der Sweep sieht die Vertragsfelder der Typen, die `capture` erzeugt. **Felder, die der Kernel
selbst schreibt, liegen außerhalb und blieben unsichtbar** — die Prüfung dieser Runde hat genau
dort weitergesucht und drei Stellen derselben Klasse gefunden, alle nicht `--map`-erreichbar:

* `design_refs` (auf PR/RQ). Erzeuger ist `staging.freeze_design:319` — `refs = list(root.get("design_refs") or [])`,
  danach `state._update_item_locked(root_id, {"design_refs": refs})`: ein skalares `design_refs`
  wird buchstabenweise zerlegt **und in den kanonischen Zustand zurückgeschrieben**. Ganz
  durchgemessen: `capture PR` nimmt das Feld als Skalar an, `freeze_design` schreibt danach **35
  Einträge** (34 Buchstaben + die neue Referenz) in den aktiven PR, Revision unverändert `1 → 1`.
  Die Leser dahinter: `cli.py:675` (`", ".join(...)` in der gedruckten Zeile) und `dispatch.py:479`
  (`[str(ref) for ref in (root.get("design_refs") or [])]`), wodurch ein UI-Task gegen ein Design
  verweigert wird, das existiert.
* `supersedes` (DEC): `report.py:1236` und `:1270`, beide `for ref in item.get(DEC_SUPERSEDES_FIELD) or []`.
* `premise_rechecks` (PR/RQ/CR): `report.py:1154` und `:1170`.

Das ist als `H43` in `docs/POST_V2_WISHLIST.md` mit Mechanismus, Kette und Urteil eingetragen; die
Behebung trägt `BUG-0038`. **Die Lehre über das Instrument, nicht über die Felder:** eine Sweep-Menge,
die aus der Oberfläche EINES Kommandos abgeleitet ist, misst die Leser dieses Kommandos — nicht die
Eigenschaft „ein Leser setzt eine Form voraus". Wer den Sweep wiederholt, leitet die Menge aus den
**Schreibern** des Zustands ab (`capture`, `_update_item_locked`, `staging.freeze_*`), nicht aus
`parse_field_map`.

## 6. Was daraus im Code steht

* Die eine Definition: `team-kits/kernel/backlog_types.py::field_elements`.
* Rot-ohne-Fix (je im Klon außerhalb des Repos gemessen):
  `test_hooks.test_process_doc_renders_a_scalar_field_as_one_element`,
  `test_hooks_v2.test_a_scalar_scope_decides_like_a_one_element_list`,
  `test_approvals_dispatch.test_a_scalar_acceptance_ref_is_one_ref_not_four_letters`,
  `test_approvals_dispatch.test_a_scalar_dependency_is_one_dependency`,
  `test_report.test_a_scalar_dependency_is_reported_once_not_once_per_letter`.
* Offene Reste: `H42` (`INV.scope`, Vertragsentscheidung offen), `H43` / `BUG-0038` (Felder
  außerhalb der Sweep-Menge).
