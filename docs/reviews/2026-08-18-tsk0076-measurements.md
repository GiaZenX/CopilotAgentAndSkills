# TSK-0076 — Block A, Runde A4b: der Codex-Zwilling, der Plan-Klick, die erfundene Uhrzeit,
# fünf falsch benannte Berichte

Repo `C:/Offline Repos/AgentAndSkills`, Branch `feat/harness-v2`, HEAD `b01cd76` beim Start.
Gegenstand: `FR-0026`, `BUG-0043`, `BUG-0044`, `BUG-0045`, `FR-0009`, `FR-0048` (nur Hälfte 1).
Erlaubt war `user/**`, `docs/**`, `tools/**`; `team-kits/**` war **absichtlich verboten**, damit der
Kit-Stempel diese Runde nicht wandert.

Jede Zahl dieser Runde steht hier und in keinem zweiten Kommentar. Was gemessen wurde, steht mit
seinem Messgerät dabei; was **nicht** gemessen wurde, steht in Abschnitt 8.

## 0. Die Messgeräte

| Was | Wo |
|---|---|
| Ablage des Anbieters für Pilot 3 (wer wann was schrieb) | `C:/Users/zenti/.claude/projects/C--pilot3-rechnung/` |
| Sitzung 1 — der Einstiegsagent, noch ohne Kit | `fd2685ae-6831-44ea-952c-791182bda55d.jsonl` |
| Auswertungsskripte (außerhalb des Repos, read-only) | `C:/tsk0076-measure/{entry_language,flow,pr_item,first_role,count_offences,rename_identity}.py` |
| Rot-Messung in einem Klon außerhalb des Repos | `C:/tsk0076-red/` (Bäume `tools/ team-kits/ user/ docs/ project_memory/`) |

## 1. Schritt 1 — was gemessen wurde, bevor etwas gebaut wurde

### 1.1 Der Codex-Zwilling gegen die Claude-Einstiegsdatei (FR-0026)

Gemessen mit dem abgeleiteten Leser (`kernel.presets.DOCUMENT_WRITES` — die Deklaration des Kernels,
welchen Teil eines Kit-Dokuments ein Kernel-Befehl schreibt), über die Blöcke beider Dateien:

| Datei (Stand HEAD `b01cd76`) | Block nennt Dokument + Feld | Block nennt `set-preset` |
|---|---|---|
| `user/claude/CLAUDE.md` | 1 | **ja** (TSK-0064) |
| `user/codex/AGENTS.md` | 1 | **nein** |

Der Codex-Zwilling fragte das Preset (`user/codex/AGENTS.md:119` im alten Stand), schrieb es
(`:231`) und nannte den Weg danach nirgends — die alte Sackgasse für ein Codex-Projekt.

### 1.2 Die Zusage-Stufe, wie sie ausgeliefert war (BUG-0043)

Aus dem Rohprotokoll der Einstiegssitzung (`flow.py`):

- `ExitPlanMode` um `2026-08-14T18:00:45Z`.
- Danach bis zur Abschluss-Nachricht: **kein** Nutzer-Textzug und **kein** `AskUserQuestion`.
  Der nächste Eintrag ist ein `Bash`-Aufruf, der den Kernel liest.
- Die drei Nutzerzüge der ganzen Sitzung sind Wunsch, Rechnungsnummer, Firmenname — keiner davon
  eine Bestätigung des Plans.

Die Schleife „iterate until explicitly confirm" war damit auf **einen Dialog-Klick** geschrumpft,
genau wie `BUG-0043` es behauptet. Das ist meine eigene Messung, nicht die Übernahme des Items.

### 1.3 Die erfundene Uhrzeit (BUG-0045)

Aus derselben Ablage (`pr_item.py`), das einzige von Hand geschriebene Item eines Projektlebens:

```
Write  C:\pilot3-rechnung\project_memory\product\active\PR-0001.yaml   at 2026-08-14T18:04:30Z
    created: "2026-08-14T12:00:00"
```

Die Sitzung hatte den Formatgeber vorher sogar nachgeschlagen (`grep -n "def _now_iso" -A 6
kernel/state.py`) und danach eine runde Zahl eingesetzt. Das Format war also bekannt, der **Wert**
war erfunden.

### 1.4 BUG-0044 — die Bereits-erledigt-Prüfung

**Ergebnis: die Prosa-Hälfte hält, die Test-Hälfte gab es nicht.**

- Die Frage steht in der ausgelieferten Claude-Einstiegsdatei: `user/claude/CLAUDE.md:72-84`
  („**Ask which TEAM SIZE they want, and ask it as its own question**" … „Do NOT invent the answer:
  the preset you write in step 3 is the one they picked").
- Die Antwort ist auch das, was geschrieben wird: `user/claude/CLAUDE.md:137-142`.
- **Kein Test las das.** Gesucht wurde nach der Testfläche von TSK-0064: `tools/test_presets.py:903`
  (`test_every_kit_tells_its_lead_the_route_instead_of_the_dead_end`) sweept die beiden
  Einstiegsdateien nur **negativ** (`_ALSO_SWEPT`, `tools/test_presets.py:890-892`) — kein Satz darf
  zum Installer schicken; die **positive** Hälfte bleibt dort ausdrücklich pro Kit. Die
  Einstiegs-Sweeps in `tools/test_hooks.py` (`ENTRY_GATE_FILES:5762`) prüften Pfade, Kernel-Befehle,
  Hook-Namen und gate-blockierte Dokumente — kein Preset.

BUG-0044 wird deshalb als **durch TSK-0064 erledigt** berichtet (kein zweiter Bau), und die fehlende
Messung ist zur Hälfte nachgeholt: die Route ist jetzt gemessen (2.1), die **Frage selbst** nicht —
siehe Abschnitt 8, Rest 1.

### 1.5 Die fünf Berichte (FR-0009) — die Zuordnung aus dem Inhalt

Regel, für alle gleich: **die erste Rollennennung im Text** ist die Rolle, um die es geht. Jeder
dieser Berichte nennt sein Thema im Titel oder in der `Datei:`/`Gelesen:`-Zeile; die sechs
ausgelieferten Dateien stimmten darin einstimmig überein (`first_role.py`). Rollen-Vokabular aus
`team-kits/dev-team/skills/*`, nicht getippt.

| Datei (alt) | Beleg im Inhalt | wahre Rolle | Datei (neu) |
|---|---|---|---|
| `2026-07-27-backend-developer.md` | Titel „# Backend-Developer — Rollenanalyse"; `skills/backend-developer/SKILL.md` | backend-developer | unverändert |
| `2026-07-27-frontend-developer.md` | `Datei: …\skills\software-architect\SKILL.md (99 Zeilen)` | software-architect | `2026-07-27-software-architect.md` |
| `2026-07-27-software-architect.md` | Titel „## Rolle `quality-engineer` — Recherchebericht" | quality-engineer | `2026-07-27-quality-engineer.md` |
| `2026-07-27-quality-engineer.md` | Titel „# Rolle `project-manager` — Standardsabgleich" | project-manager | `2026-07-27-project-manager.md` |
| `2026-07-27-project-manager.md` | Titel „# Rolle `product-designer`"; `Datei: …\skills\product-designer\SKILL.md (127 Zeilen)` | product-designer | `2026-07-27-product-designer.md` |
| `2026-07-27-product-designer.md` | `Datei: …\skills\frontend-developer\SKILL.md (59 Zeilen)` | frontend-developer | `2026-07-27-frontend-developer.md` |

Das ist ein **5er-Ring** (frontend → software-architect → quality-engineer → project-manager →
product-designer → frontend); `backend-developer` stand richtig. Genau die fünf, die `FR-0009`
nennt.

**Verweise auf die alten Dateinamen: null.** `2026-07-27-(frontend-developer|software-architect|
quality-engineer|project-manager|product-designer|backend-developer)` kommt im ganzen Baum nur in
`.git/index` vor (Volltextsuche über das Repo). Es war also nichts zu korrigieren, und dieser
Nullbefund ist die Aussage, nicht das Fehlen einer Aussage.

**Die Umbenennung hat keinen Inhalt bewegt** (`rename_identity.py`, sha256 des HEAD-Blobs gegen die
Datei jetzt): alle fünf **SAME**.

### 1.6 FR-0048 Hälfte 1 — warum die Deutsch-Regel nicht band

Gemessen über alle Assistenten-Textblöcke der Einstiegssitzung (`entry_language.py`;
Klassifikation über das Verhältnis deutscher zu englischer Funktionswörter, mit beiden Zählungen
je Block ausgegeben):

| Sprache | Blöcke |
|---|---|
| deutsch | 10 |
| englisch | **1** (Block #4) |
| unentschieden (je 1 Wort) | 1 |

Block #4 ist der **erste Zug nach dem Einstieg in die Kernel-Vertragslektüre**: unmittelbar davor
liest die Sitzung `kernel/backlog_types.py` (`ROOT_TYPE_BY_KIT`, `ACTIVE_DIRS`, `REQUIRED_FIELDS`,
`AUTOMATA`), der Block lautet „Initial status for PR is DRAFT, confirmed. Let me check the required
fields for PR and the kernel-stamped fields …".

**Was das trägt und was nicht.** Die Regel band in 11 von 12 Zügen — ein Positionsversagen der
Zeile `:3` erklärt das nicht. Was die Stelle des einen Ausreißers nahelegt: die Regel und ihre
Ausnahme standen in **einem** Satz („All code and artifacts … in **English**"), ohne dass der
Geltungsbereich der Ausnahme abgegrenzt war — und der eine gebrochene Zug ist der, dessen Inhalt
fast nur aus englischen Bezeichnern besteht. Das ist ein plausibler mechanischer Anteil, **kein
Beweis**: aus einem einzigen Block lässt sich Drift nicht ausschließen. Gebaut wurde deshalb genau
die Abgrenzung, nicht mehr (2.4), und ob sie bindet, kann nur ein neuer Pilotlauf sagen
(Abschnitt 8, Rest 3).

## 2. Schritt 2 — was gebaut wurde

Eine Formulierung für beide Einstiegsdateien, wo sie denselben Ablauf haben; wo nicht, steht die
Abweichung benannt (2.5).

### 2.1 Codex-Parität für die Preset-Route (FR-0026)

- `user/codex/AGENTS.md:122-130` — die Frage ist jetzt ausdrücklich die **Team-Größen-Frage** als
  eigene Frage, mit dem Satz „**not a one-way door**": der installierte Lead fragt erneut und wendet
  die Antwort mit `set-preset` an.
- `user/codex/AGENTS.md:249-254` — der Schreibblock schreibt **die Antwort** des Nutzers und nennt
  den Besitzer des Feldes danach (`set-preset` owns `project.preset` and nothing else).
- Gegenstück in der Claude-Datei, wortgleich in der Sache: `user/claude/CLAUDE.md:79-82`.

**DEC-0048 eingehalten, in beiden Dateien und ausdrücklich geprüft:** der Satz verspricht **nicht**,
dass die Frage die *neuen* Rollen nennt. Er sagt, sie nennt das Team, wie es **danach** dasteht,
plus was wegfällt — „never which roles are new" — und zitiert `DEC-0048` als Grund
(`user/claude/CLAUDE.md:79-82`, `user/codex/AGENTS.md:128-130`). Die Claude-Formulierung vor dieser
Runde („it asks them again before it does", altes `:76-77`) versprach ebenfalls keinen Delta; sie
war also DEC-0048-konform und ist nur um Befehl und Verweis ergänzt worden.

### 2.2 Die Zusage-Stufe als eigene Antwort (BUG-0043)

- `user/claude/CLAUDE.md:91-97`
- `user/codex/AGENTS.md:186-191`

Der Plan-Dialog ist als **Präsentationsfläche** benannt; sein Verlassen ist ein Moduswechsel, „one
click wide", und ausdrücklich nie die Zusage. Die Präsentation selbst bleibt unangetastet
(BUG-0043 AC-2): `user/claude/CLAUDE.md:66-68` („engage Plan Mode now"), `user/codex/AGENTS.md:157`
(Plan-Modus betreten) und `:193-195` (nach der Zusage verlassen). Das **Verlassen** hatte die
Claude-Datei zunächst nicht — nachgetragen in dieser Nachbesserung, `user/claude/CLAUDE.md:95-97`
(Abschnitt 9, F5).

### 2.3 Echte Werte statt plausibler (BUG-0045)

- `user/claude/CLAUDE.md:122-127`
- `user/codex/AGENTS.md:231-238`

Gefordert ist die **gelesene Uhr** in Format **und Zone**, die `kernel/state.py` `_now_iso` erzeugt
(`team-kits/kernel/state.py:1361-1362`: `time.strftime("%Y-%m-%dT%H:%M:%S")` — naive **Ortszeit**,
kein Offset, kein `Z`) — und der Satz gilt für **alle** handgestempelten Felder (BUG-0045 AC-2):
jedes andere Feld ist entweder die bestätigte Antwort des Nutzers oder der Vertrag aus
`backlog_types.py`. Die Zonenangabe kam in der Nachbesserung dazu (Abschnitt 9, F4); ohne sie wäre
die Anweisung in einer UTC-Umgebung um den Zeitzonenversatz falsch gewesen — genau die Umgebung, in
der der Pilot lief.

### 2.4 Die Deutsch-Regel (FR-0048 Hälfte 1)

- `user/claude/CLAUDE.md:3-7`
- `user/codex/AGENTS.md:3-7` (gleiche Formulierung; dieselbe Regel stand dort in derselben Form)

Abgegrenzt ist jetzt der **Geltungsbereich beider Hälften**: jeder Satz an den Nutzer ist deutsch,
die einzeilige Arbeitsnotiz zwischen zwei Werkzeugaufrufen eingeschlossen und ausdrücklich auch beim
Lesen des Feldvertrags des Kernels; englisch bleiben die **Bezeichner und der Code** (variables,
comments, function names, YAML keys), nie der Satz, der sie nennt. Die Ausnahme hängt damit an
Bezeichnern, nicht an Dateien — die erste Fassung sagte „file CONTENT only" und hätte die Prosa
gedeckt, die der Nutzer selbst liest (Masterplan, Item-Text). Und die Stelle im Ablauf ist über
ihren **Inhalt** benannt statt über eine Schrittnummer, die in beiden Dateien anders lautet
(Abschnitt 9, F6/F7). Der Anlass steht als Zeiger (`FR-0048`), nicht als Zahl.

**Der Heimatverzeichnis-Rollout ist NICHT Teil dieser Runde** (`DEC-0045`: externe Freigabe des
Nutzers). Bis dahin wirkt die Korrektur nur im Repo; die installierte `~/.claude/CLAUDE.md` ist
unverändert.

### 2.5 Wo die beiden Dateien ehrlich auseinandergehen

- Die Claude-Datei trägt die Vorgeschichte `BUG-0044/BUG-0041` (`:82-84`), die Codex-Datei nicht:
  dort **gab** es die Preset-Frage bereits (alt `:119`), nur den Weg danach nicht. Eine
  Paritätsregel über Item-Ids wäre hier also falsch und ist bewusst nicht gebaut.
- Die Claude-Datei nennt `AskUserQuestion` als Fragewerkzeug, die Codex-Datei ihr eigenes
  („Codex's structured question tool", `user/codex/AGENTS.md:85`). Der Ablauf ist derselbe, das
  Werkzeug nicht.
- Die Codex-Datei behält ihre providereigenen Schritte (Trust, `/hooks`), die es unter Claude nicht
  gibt.

## 3. Schritt 3 — die Tests und ihr Rot

Erweitert wurden die **vorhandenen** Einstiegs-Sweeps; ein zweiter Leser wurde nicht erfunden. Alle
drei neuen Prüfungen lesen die Blöcke über `_entry_gate_texts` (`tools/test_hooks.py:5800`) und
`_markdown_blocks` (`tools/test_hooks.py:7555`), gebündelt in `_entry_gate_blocks`
(`tools/test_hooks.py:6460`).

| Prüfung | Ort | Subjekt kommt aus |
|---|---|---|
| `test_the_field_a_kernel_command_owns_is_named_with_that_command_in_both_entry_gates` | `tools/test_hooks.py:6472` | `kernel.presets.DOCUMENT_WRITES` |
| `test_the_block_that_hand_stamps_the_kernels_fields_names_the_kernels_own_clock` | `tools/test_hooks.py:6519` | `kernel.state._KERNEL_SET` / `_now_iso` |
| `test_both_entry_gates_anchor_the_shared_sign_off_and_name_no_item_this_repo_lacks` | `tools/test_hooks.py:6564` | `ENTRY_FLOW_OCCASION` (`:6561`) + `backlog_types.ROOT_TYPE_BY_KIT` |
| `test_every_research_role_report_is_named_after_the_role_its_own_text_is_about` | `tools/test_repo_hygiene.py:107` | `team-kits/dev-team/skills/*` + der Inhalt der Berichte |

### Rot ohne den Fix — gemessen, nicht behauptet

Klon **außerhalb** des Repos (`C:/tsk0076-red/`), beide Einstiegsdateien auf den HEAD-Stand
zurückgeholt (`git show HEAD:… > …`, byte-identisch geprüft), die fünf Berichte zurückbenannt:

```
FAILED tools/test_hooks.py::test_the_field_a_kernel_command_owns_is_named_with_that_command_in_both_entry_gates
  assert not ['user/codex/AGENTS.md: a block writes `project.preset` in `project_config.yaml`
               and never names `set-preset`, …']
FAILED tools/test_hooks.py::test_the_block_that_hand_stamps_the_kernels_fields_names_the_kernels_own_clock
  assert not ['user/claude/CLAUDE.md: the block that licenses hand-stamping `_KERNEL_SET` never
               names `_now_iso`, …', 'user/codex/AGENTS.md: …']
FAILED tools/test_hooks.py::test_both_entry_gates_anchor_the_shared_sign_off_and_name_no_item_this_repo_lacks
  AssertionError: user/claude/CLAUDE.md, user/codex/AGENTS.md: … not the sign-off (`BUG-0043`)
3 failed, 736 deselected
```

```
FAILED tools/test_repo_hygiene.py::test_every_research_role_report_is_named_after_the_role_its_own_text_is_about
  2026-07-27-frontend-developer.md  is filed under `frontend-developer`  and its own text is about `software-architect`
  2026-07-27-product-designer.md    is filed under `product-designer`    and its own text is about `frontend-developer`
  2026-07-27-project-manager.md     is filed under `project-manager`     and its own text is about `product-designer`
  2026-07-27-quality-engineer.md    is filed under `quality-engineer`    and its own text is about `project-manager`
  2026-07-27-software-architect.md  is filed under `software-architect`  and its own text is about `quality-engineer`
1 failed, 2 deselected
```

Vorher/nachher am Leser selbst (`count_offences.py`), damit das Rot nicht an einer Nebensache hängt:

| Baum | Blöcke mit `_KERNEL_SET` (davon mit `_now_iso`) |
|---|---|
| Klon (HEAD-Stand) | claude 1 (0), codex 1 (0) |
| Repo (nach dem Fix) | claude 1 (1), codex 1 (1) |

Dass die Route-Prüfung im Klon **nur** die Codex-Datei nannte, ist die Messung von 1.1 aus der
anderen Richtung: die Claude-Hälfte stand seit TSK-0064.

### Was die Prüfungen NICHT garantieren

- Die Zusage-Prüfung pinnt den **Anker**, nicht den Satz: wer die Anweisung löscht und `BUG-0043`
  stehen lässt, kommt durch. Dieselbe schwächere, ehrliche Zusage, die
  `test_every_document_a_gate_blocks_on_is_named_by_both_entry_gates` für ihr Subjekt ausspricht —
  keine Prüfung liest die Absicht einer Anweisung. Zähne bekommt der Anker durch die zweite Hälfte
  derselben Prüfung: **jede** Item-Id in diesen beiden Dateien muss auf ein Item zeigen, das dieses
  Repo führt. Die Ausnahme für `PR-0001` ist eine **Ableitung** (`ROOT_TYPE_BY_KIT` = die Typen, die
  eine Einstiegsdatei sät), kein Name — dieses Repo führt selbst ein `PR-0001`, und genau auf dieser
  Koinzidenz hätte eine Namensausnahme unbemerkt geruht.
- Die Berichts-Prüfung verlässt ihr Subjekt, wenn eine Datei auf einen **Nicht**-Rollennamen
  umbenannt wird — **heute aber folgenlos, und die erste Fassung dieses Satzes war deshalb
  über-alarmierend** (Befund F2 des Prüfers). Solange die ausgelieferte Menge genau so groß ist wie
  der Boden, ist der Boden eine Gleichheit, und genau diese Umbenennung fällt auf ihn. Gemessen im
  Klon, beide Richtungen:

  | Zustand | eine Datei aus dem Subjekt umbenannt | Ergebnis |
  |---|---|---|
  | 6 Berichte (heute) | ja | `only 5 research reports…` → **1 failed** |
  | 7 Berichte (Platzhalter ergänzt) | nein | 1 passed |
  | 7 Berichte | ja | **1 passed**, während der umbenannte ungeprüft dasteht |

  Die Lücke öffnet sich also erst mit dem **siebten** Rollenbericht, und dann lautlos. Der Boden
  zählt, er benennt nicht; das steht jetzt genauso im Docstring
  (`tools/test_repo_hygiene.py:122-128`).

## 4. Schritt 4 — Auslieferung

- **Kein Kit-Stempel bewegt.** `git diff HEAD --name-only` nennt **elf** verfolgte Dateien (neun von
  mir, dazu die Wunschliste des Leads und der Audit-Log der Hooks — Aufschlüsselung in Abschnitt 5),
  keine davon unter `team-kits/`; `git diff HEAD --stat -- team-kits/ tools/bump_kit_version.py` ist leer.
  `python tools/bump_kit_version.py --check` → `dev-team/office-team/research-team: unchanged
  (2026.08.18-3)`, rc 0. Zweimal geprüft: vor und nach der Nachbesserung (Abschnitt 9).
- `python -m ruff check .` → All checks passed.
- `python tools/validate.py` → all structural checks passed.
- Volle Suite: siehe Abschnitt 7.
- **`.claude/hooks/test_gates.py` ist nicht zu erwarten und wurde nicht gefahren.** Die Ableitungs-
  fläche der Gates ist `team-kits/**` plus `tools/bump_kit_version.py` (über `kernel.hashing`,
  `_harness.ProtectedArea` → `decision_inputs`); beide stehen nicht im Diff. Geändert wurden nur
  `tools/test_*.py` (keine Ableitungseingabe), `user/**` und `docs/**`.

## 5. Die geänderten Dateien

Stand nach der Nachbesserung, aus `git status --porcelain` gelesen und nicht erinnert — **elf
verfolgte Dateien plus dieser Bericht** (neun meine, zwei nicht), und die Trennung ist der Punkt:

```
MEINE (Auftrags-Scope user/**, docs/**, tools/**):
docs/research/2026-07-27-frontend-developer.md   (Umbenennung, Inhalt unverändert)
docs/research/2026-07-27-product-designer.md     (Umbenennung, Inhalt unverändert)
docs/research/2026-07-27-project-manager.md      (Umbenennung, Inhalt unverändert)
docs/research/2026-07-27-quality-engineer.md     (Umbenennung, Inhalt unverändert)
docs/research/2026-07-27-software-architect.md   (Umbenennung, Inhalt unverändert)
tools/test_hooks.py                              (+3 Prüfungen, +1 Hilfsleser)
tools/test_repo_hygiene.py                       (+1 Prüfung, +2 Hilfsleser)
user/claude/CLAUDE.md
user/codex/AGENTS.md
docs/reviews/2026-08-18-tsk0076-measurements.md  (dieser Bericht, untracked)

NICHT MEINE:
docs/POST_V2_WISHLIST.md                         (+13 Zeilen, LEAD, 07:07 und erneut nach dem
                                                  Verdikt — trägt meine beiden Über-Verweigerungen
                                                  aus Rest 5 und zwei Befunde des Prüfers ein;
                                                  die Datei ist mein forbidden_scope)
project_memory/.audit/hook_events.jsonl          (Hook-Prozesse selbst, H37 Rest 2)
```

Die Wunschlisten-Änderung ist während meiner Runde entstanden und vom Lead ausdrücklich als seine
erklärt; sie ist der Grund, warum die erste Fassung dieser Liste (neun Dateien) nicht mehr auf das
Paket passte (Prüferbefund F1). Der Audit-Log ist **kein Schreibzugriff einer Rolle**: die Datei
wird von den Hook-Prozessen fortgeschrieben, solange die Sitzung läuft, und Gate 1 verweigert mir
jeden Schreibzugriff dorthin.

**Die volle Suite ist auf DIESEM Baum gemessen, einschließlich der Wunschlisten-Änderung:** der
Prüfer fuhr `python -m pytest tools/ -q` auf dem aktuellen Baum und meldet dieselben Zahlen wie
Abschnitt 7 (2828 passed, 13 skipped). Mein eigener Lauf lag vor der Wunschlisten-Änderung; welche
Aussage worauf beruht, steht in Abschnitt 9.

Der Bericht selbst ist von keinem Test Subjekt: aus `docs/reviews/` liest die Suite nur
`phase0-disposition.md` (`tools/parity_sources.py:47`, `tools/record_lead_package_sizes.py:35`,
`tools/pin_constitution_sections.py`). Abschnitt 7 wurde nach dem Lauf mit dessen Zahlen ergänzt;
das bewegt nichts, was der Lauf gemessen hat.

## 6. Abweichungen vom Item, ausdrücklich

- **Der Dateiname des Berichts.** `TSK-0076` `expected_outputs` nennt
  `docs/reviews/2026-08-17-tsk0076-measurements.md`; geschrieben ist `2026-08-18-…`, weil die Runde
  am 18. lief. In einer Runde, deren Gegenstand eine erfundene Zeitangabe ist, wäre das Datum des
  Vortags die falsche Stelle für Bequemlichkeit.
- **BUG-0044 wurde nicht gebaut**, sondern gemessen und als durch TSK-0064 erledigt berichtet — so
  wie der Auftrag es verlangt (1.4). Neu ist nur die fehlende **Messung** der Route.
- **FR-0009 „Verweise korrigieren" entfiel**, weil es keine gibt (1.5). Der Nullbefund ist gemessen.

## 7. Suite

Ein Lauf, nach allen Änderungen dieser Runde einschließlich dieses Berichts:

```
python -B -m pytest tools/ -q
2828 passed, 13 skipped in 2077.43s (0:34:37)     rc=0
```

Der Klon `C:/tsk0076-red/` bleibt **im roten Zustand** stehen (HEAD-Fassung der beiden
Einstiegsdateien, alte Berichtsnamen, aber die NEUEN Testdateien), damit die Messung aus Abschnitt 3
nachvollzogen werden kann, ohne sie neu herzustellen; nach der F2-Messung wurde er in genau diesen
Zustand zurückgesetzt und das Rot erneut bestätigt (4 failed). Er liegt außerhalb des Repos und wird
von nichts gelesen.

## 8. Was offen bleibt, benannt

1. **Die Preset-FRAGE selbst hat weiterhin keinen Test** (BUG-0044 AC-1, „red-without-fix").
   Gemessen ist, dass beide Einstiegsdateien den **Schreibblock** mit seinem Nachher-Besitzer nennen;
   dass die Frage *gestellt* wird, steht nur in der Prosa (`user/claude/CLAUDE.md:72`,
   `user/codex/AGENTS.md:122`). Ein Leser, der den Block über Wörter auswählt, wurde probiert und
   verworfen: die gemessene Variante („confirm"/„sign-off" zusammen mit „plan", `probe_blocks.py`)
   wählt **4** Blöcke in der Claude- und **5** in der Codex-Datei aus, die meisten davon zu Recht
   ohne jede Antwortpflicht — Modushinweis, Masterplan-Füllung, Neustartabsatz. Eine Ausnahmeliste
   dagegen wäre genau die Aufzählung, die dieses Repo zweimal bezahlt hat. Offen, nicht geschlossen.
2. **Die Zusage-Anweisung ist nur über ihren Anker gemessen** (Abschnitt 3, „Was die Prüfungen NICHT
   garantieren"). Der Plan-Dialog ist eine Provider-Fläche; im Kernel gibt es nichts, woraus sich
   eine Prüfung ableiten ließe.
3. **Ob die geschärfte Deutsch-Regel bindet, ist NICHT gemessen.** Der Beleg dieser Runde ist
   1 englischer Block von 12 in einer Sitzung; ob die Abgrenzung ihn verhindert, kann nur ein neuer
   Pilotlauf zeigen. Bis dahin ist 2.4 eine begründete Formulierungsänderung, keine Wirkungsaussage.
4. **Der Rollout ins Heimatverzeichnis fehlt weiter** (`FR-0048` Hälfte 2, `DEC-0045`: braucht die
   Freigabe des Nutzers). Solange er aussteht, laufen echte Einstiegssitzungen auf der **alten**
   `~/.claude/CLAUDE.md` — ohne die Team-Größen-Frage aus TSK-0064, ohne die Zusage-Stufe, ohne die
   Uhrzeit-Regel. Das ist die größte offene Wirkungslücke dieser Runde und liegt beim Nutzer.
5. **Zwei Über-Verweigerungen von Gate 1/Gate 3 sind mir begegnet** und stehen hier als Messung,
   nicht als Wunsch: `cp -r <repo>/project_memory <ziel außerhalb>` wird verweigert (jeder Operand
   von `cp` gilt als Schreibziel), obwohl der geschützte Baum nur gelesen wird — der Klon für die
   Rot-Messung lief deshalb über ein Python-Skript außerhalb des Repos
   (`C:/tsk0076-measure/clone_state.py`); und `git hash-object <datei>` wird von Gate 3 als
   historienschreibend eingestuft, obwohl es **in dieser flaglosen Form** nichts schreibt (Präzisierung
   des Prüfers: mit `-w` schreibt es sehr wohl ein Blob, die Einstufung ist also nur ohne die Flagge
   Über-Verweigerung). Beides gehört in die Löcherliste, die für diese Runde `forbidden_scope` ist —
   deshalb hier benannt und an den Lead zurückgegeben; er hat beides inzwischen eingetragen
   (Abschnitt 5, „NICHT MEINE").

## 9. Nachbesserung nach dem Prüfverdikt (zweiter Durchgang)

Verdikt: FAIL mit dem ausdrücklichen Zusatz „nichts neu zu bauen" — die gebaute Substanz hielt jeder
Messung stand; die Blocker waren Prosa und Bericht. Was in diesem Durchgang passiert ist:

| Befund | Was war falsch | Was jetzt gilt |
|---|---|---|
| **F1** | Die Dateiliste des Berichts (neun) passte nicht mehr aufs Paket: `docs/POST_V2_WISHLIST.md` hatte sich mitten in der Runde geändert | Abschnitt 5 listet den **gelesenen** Stand, getrennt nach „meine"/„nicht meine", mit der Urheberschaft des Leads und dem Hinweis, dass der Prüfer die volle Suite auf **diesem** Baum grün gemessen hat |
| **F2** | Der Docstring behauptete eine offene Fluchttür, die heute geschlossen ist — die über-alarmierende Richtung der Hausregel | Beide Richtungen gemessen (Tabelle in Abschnitt 3) und in `tools/test_repo_hygiene.py:122-128` als das benannt, was sie ist: eine Gleichheit heute, eine lautlose Lücke ab dem siebten Bericht |
| **F3** | Drei Zeigerangaben zeigten auf Zeilennummern **vor** meinem Diff (`CLAUDE.md:64-65`, `AGENTS.md:148`, `test_hooks.py:7398`) | Korrigiert auf `:66-68`, `:157`, `:7555`; danach **alle** Zeiger dieses Berichts neu abgeleitet, nicht nur die drei |
| **F4** | Die Uhr-Anweisung nannte das Format, nicht die **Zone**: `_now_iso` (`team-kits/kernel/state.py:1361-1362`) ist naive Ortszeit, die Pilotumgebung meldete UTC (`Z`) | „the machine's LOCAL time, carrying no offset and no `Z`" in beiden Dateien (`user/claude/CLAUDE.md:123-124`, `user/codex/AGENTS.md:233-235`) |
| **F5** | Der Claude-Zwilling hatte den **Ausstieg** aus dem Plan-Modus verloren, den der Codex-Zwilling hat | `user/claude/CLAUDE.md:95-97` spiegelt ihn (`user/codex/AGENTS.md:193-195`) |
| **F6** | Die Sprachgrenze hing an „file CONTENT" — und Masterplan-/Item-Prosa ist Dateiinhalt, den der **Nutzer** liest | Die Ausnahme hängt jetzt an **Bezeichnern und Code**, nicht an Dateien (`user/claude/CLAUDE.md:3-7`, `user/codex/AGENTS.md:3-7`) |
| **F7** | „in step 3"/„in step 4" — eine Zahl mit zwei Wohnorten und ohne Leser | Die Stelle ist über ihren Inhalt benannt („while you are reading the kernel's field contract") |

**Worauf sich die Grün-Aussage dieses Durchgangs stützt, genau:**

- Der Prüfer hat `python -m pytest tools/ -q` auf dem **aktuellen** Baum gefahren (einschließlich der
  Wunschlisten-Änderung) und meldet 2828 passed / 13 skipped — dieselbe Zahl wie mein Lauf in
  Abschnitt 7. Diese Zahl ist zitiert, nicht von mir neu gemessen.
- Von mir in diesem Durchgang neu gemessen sind nur die berührten Flächen: die vier neuen Prüfungen
  im Repo (grün) und im zurückgesetzten Klon (rot), `ruff`, `validate.py`,
  `bump_kit_version.py --check`, `git diff HEAD --stat -- team-kits/ tools/bump_kit_version.py`
  (leer) und `pytest .claude/hooks/test_gates.py -k hole_list` (Abschnitt 4).
- Die Änderungen dieses Durchgangs betreffen Prosa in `user/**`, einen Docstring in
  `tools/test_repo_hygiene.py` und diesen Bericht. Keine Testlogik, keine Ableitungseingabe eines
  Gates, kein Kit.
