# TSK-0100 — Rundenprotokoll (Strom A des DEC-0057-Piloten)

**Baum:** `C:\Offline Repos\v2-testbed\_worktrees\stream-design\`, Zweig `stream/design`, Basis
`c155a5f`. **Scratch:** `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0100\`.
**Start:** 2026-09-01 21:20:22 · **Ende:** 2026-09-01 22:50:07 · **Dauer: 1 h 30 min**
(Wanduhr des Umsetzers, DEC-0057 g; davon rund 30 min der Haken-Suitenlauf).
**Nicht getan, wie es der Strom verlangt:** kein Commit, keine volle `tools/`-Suite, keine
Installation in den globalen Store. Der Stempel ist PROVISORISCH.

**Übergabe:** `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0100\stream-design.patch`
(`git diff HEAD`, neue Dateien über `git add -N` enthalten).

---

## 1. FR-0068 — `frontend-design` als Referenz-Skill

**Gebaut:** `team-kits/dev-team/skills/frontend-design/{SKILL.md,LICENSE.txt}` plus die Zeile in
`NOTICES.md`.

**Herkunft, gemessen statt behauptet.** Gezogen von `raw.githubusercontent.com` am 2026-09-01.
Der lokal berechnete Git-Blob-Hash der geladenen Datei ist identisch mit dem, den die GitHub-API
für denselben Pfad meldet — damit ist die Kopie beweisbar die Datei des Repos und nicht ein
Renderer-Artefakt:

| | Bytes | Blob-SHA1 | letzter Commit des Ordners |
|---|---|---|---|
| `frontend-design/SKILL.md` | 8 260 | `decdff43d05908b4c1fc2cfd2d80fc5743440934` | `2235be7c60b551f5de82ade908fd3816455afcda` (2026-06-09) |
| `frontend-design/LICENSE.txt` | 10 174 | `f433b1a53f5b830a205fd2df78e2b34974656c7b` | dito |

`main` stand bei `53048666b05b4799081517d00e09e0a2dd688678`. Die Juli-Messung nannte für
`SKILL.md` 8 260 Bytes und für `LICENSE.txt` 10 174 Bytes — **unverändert seit Juli**, wie es die
August-Recherche schon festgehalten hatte. Beide Werte stehen im Frontmatter der ausgelieferten
Datei (`source_commit`, `source_blob_sha1`), damit eine spätere Runde neu ziehen und diffen kann.

**Lizenzkopie byte-identisch:** `sha256 0d542e0c…4594`, 10 174 Bytes, 0 CRLF — Download und
ausgelieferte Datei identisch (`.gitattributes` erzwingt LF, also überlebt das auch einen
Windows-Klon).

**Was umgeschrieben wurde, sechs markierte Stellen** (`[MOD-1]`…`[MOD-6]`, je inline und in einer
Liste am Ende): der Gedächtnis-Hinweis (der Auftrag ist der Brief, eine Lücke geht an den Manager
zurück); „write the code" auf den gestagten Entwurf verengt, der eingefroren nach unten gereicht
wird; „plan in your thinking, then show the user" **entfernt** (die Designerin spricht nicht mit
dem Nutzer, und das Harness hat genau diesen PM-Fehler in der eigenen Geschichte); der
unausgesprochene Qualitätsboden durch einen Zeiger auf die Stelle ersetzt, die ihn ausspricht; die
optionalen Screenshots durch die verpflichtende Sicht-Schleife ersetzt; der private Notizzettel
entfernt.

**Die Behauptung „sonst nichts angefasst" ist GEMESSEN**, nicht mit dem Auge geprüft:
`_round-scratch/TSK-0100/verify_fidelity.py` vergleicht Absatz für Absatz gegen die
Upstream-Bytes, unter Abzug der deklarierten Streichungen. Ergebnis für beide Skills:
**0 nicht deklarierte Unterschiede**. Für `frontend-design` sind das 25 Upstream-Absätze gegen 24
eigene (der eine gestrichene ist `[MOD-3]`).

**Eine Korrektur an mir selbst, gefunden bevor der Prüfer sie fand:** die erste Fassung des
Kopfbanners sagte „Every change this kit made is marked inline … nothing else in the body was
touched". Das ist eine Schutzbehauptung, die der Code nicht baut — eine Änderung OHNE Marke sieht
der Marken-Test prinzipiell nicht, weil keine Prüfung dieser Suite ins Netz geht. Das Banner sagt
jetzt, was gehalten wird (Marken ↔ Liste, mit dem Testnamen), was es nicht sieht, und wodurch eine
unmarkierte Änderung dennoch auffindbar bleibt (die Herkunft im Frontmatter). Die gemessene Zahl
„0 Unterschiede" steht hier im Bericht und ausdrücklich nicht in der Datei (SR-0008: eine Zahl
lebt an genau einer Stelle).

## 2. FR-0070 — `webapp-testing` als Referenz-Skill

**Gebaut:** `team-kits/dev-team/skills/webapp-testing/{SKILL.md,LICENSE.txt}` plus NOTICES-Zeile.

| | Bytes | Blob-SHA1 | letzter Commit des Ordners |
|---|---|---|---|
| `webapp-testing/SKILL.md` | 3 913 | `4726215301db64a0cc4d41fc3219c61f37a30f4a` | `b9e19e6f44773509fbdd7001d77ff41a49a486c1` (2026-04-20) |
| `webapp-testing/LICENSE.txt` | 11 345 | `4f881c52d1f72f4cfb720e339e2d35c3058d01a9` | dito |

Juli-Messung: 3,9 KB bzw. 11 345 B — deckungsgleich. Lizenzkopie byte-identisch
(`sha256 bc6b3af2…1362`).

**Drei markierte Änderungen**, und die erste war Pflicht statt Geschmack: der Upstream-Text zeigt
auf `scripts/with_server.py` und `examples/`, die dieses Kit bewusst **nicht** mitliefert (Juli:
ein zweites Executable neben einer SKILL wäre ein Skript, das die Gates nicht kennen). Ein Zeiger
auf eine Datei, die niemand hat, ist genau die Sackgassen-Behauptung, die TSK-0096 korrigiert hat
— alle Zeiger sind raus, die **Regel** („`--help` zuerst, Quelle nicht lesen") bleibt und zeigt auf
die Skripte, die dieses Kit ausliefert. `[MOD-2]`: der Screenshot-Pfad von `/tmp` in das
Staging-Verzeichnis der Aufgabe (auf den Windows-Hosts dieses Kits existiert `/tmp` nicht, und ein
Fund außerhalb des Projekts ist einer, den niemand öffnen kann). Verbliebene Nennungen von
`with_server`, `examples/` und `/tmp` in der Datei: **nur** innerhalb der Änderungs-Marken selbst
(gemessen per Grep).

**Überschneidung mit TSK-0099 geprüft, und es gibt jetzt genau drei Render-Wege statt vier**
(`[MOD-3]`, ausdrücklich als eigene Ergänzung markiert): `kit_design_render.py` für den gestagten
ENTWURF, `kit_browser_checks.py` für die GEBAUTE App, `scripts/quality.py` für die
produktspezifischen Flows. Das Skill schreibt diese Flows und ist kein vierter Screenshot-Pfad —
sonst liest ein Gate den einen Datensatz und eine Rolle schaut auf einen anderen.

## 3. FR-0045 — das Bündelschema aus dem echten Export

**Gebaut:** `team-kits/dev-team/templates/repo/scripts/kit_design_system_check.py` (Kit-eigen,
in `team-kits/repo_kit_owned.txt` aufgenommen — Begründung steht dort und ist eine
**Beurteilung**, kein Gate-Zwang: die Datei hält ein SCHEMA, und ein geforkter Projektstand würde
die Frage „ist dieses Design-System benutzbar" mit dem Vertrag von letztem Jahr beantworten,
während der Designer-Skill genau dieses Kommando nennt) plus der Abschnitt „A design system the
project already HAS" im `product-designer`-Skill.

**Das Bündel des Nutzers wurde NICHT ins Kit gezogen** — es ist sein Design-System. Ausgeliefert
werden das Schema und die Einwurfstelle.

**Am echten Export gemessen** (Kopie in den Scratch, Original nur gelesen): 184 Einträge; die von
`FR-0045` behauptete Form bestätigt sich Punkt für Punkt (`SKILL.md` mit Frontmatter, `readme.md`,
`_ds_manifest.json` mit `namespace`, 33 Komponenten, 309 Token, 6 Themes, 14 Fonts, 30 Cards,
`source: spa`). Neu gemessen und zum Vertragsbestandteil gemacht: **105 pfadförmige Werte im
Index, alle 105 lösen im Bündel auf.** Das macht den Index zu einem Index statt zu einer
Beschreibung und fängt den halb ausgepackten Export.

**Rot zuerst, am ECHTEN Archiv** (`_round-scratch/TSK-0100/mutate.py`, acht Mutationen je auf einer
frischen Kopie, danach der unberührte Export):

| Mutation | rc | genannter Fehlteil |
|---|---|---|
| `_ds_manifest.json` entfernt | 2 | „`_ds_manifest.json` is missing — the machine-readable spine" |
| `readme.md` entfernt | 2 | „`readme.md` is missing — the human half" |
| `SKILL.md` entfernt | 2 | „`SKILL.md` is missing — the entry point" |
| `SKILL.md` ohne Frontmatter | 2 | „carries no frontmatter block" |
| `tokens/` beim Auspacken verloren | 2 | „names 27 file(s) the bundle does not contain" |
| `namespace` gelöscht | 2 | „has no usable `namespace`" |
| Token-Liste geleert | 2 | „lists no `tokens` at all" |
| Index kein JSON | 2 | „is not readable JSON" |
| **unberührter Export** | **0** | `ok` |

**Ende zu Ende im echten Projekt**, nicht nur im Test: ein realer Scaffold-Lauf gegen ein
Wegwerf-`$HOME` legt `scripts/kit_design_system_check.py` ins Projekt; der echte Export dorthin
ausgepackt ergibt `rc 0`, dieselbe Ausgabe nach dem Löschen von `readme.md` ergibt `rc 2` mit dem
benannten Fehlteil. Der Suchlauf hält außerdem die elf echten dev-team-Skills NICHT für kaputte
Bündel (`rc 0`, „kein Design-System") — das ist die Falsch-Positiv-Richtung und sie ist als Test
über den echten Skill-Baum gebaut.

## 4. FR-0071 — welche Referenz-Skills ein Auftrag NENNT, ist abgeleitet

**Gebaut:** `team-kits/kernel/references.py` (neu), `presets.SKILLS_DIR` (neue Konstante an der
Stelle, die schon `AGENTS_DIR` trägt), Verdrahtung in `dispatch.create_lease` und
`dispatch.dispatch_header` unter dem Schlüssel `references`.

**Wo die Erklärung lebt und warum nicht in einer Karte daneben:** jedes Referenz-Skill deklariert
im eigenen Frontmatter `reference_for: {roles: [...], task_types: [...]}`. Eine getrennte Karte
wäre eine zweite Liste, die mit dem Verzeichnis in Schritt gehalten werden muss — genau die Drift,
die dieses Repo wiederholt gemessen hat. Der Preis ist benannt (siehe H84 d): die zweite Richtung
des Stolperdrahts wird an der ABLEITUNG dadurch tautologisch und ist dort nur noch ein Boden unter
der Konstruktion; die Richtung, die heute brechen kann, trägt ein zweiter Leser über die
Abruf-Schreibweise.

**Beide Achsen müssen passen** (Rolle UND Aufgabentyp), damit eine `docs`-Aufgabe nicht dieselben
schweren Design-Referenzen mitbringt wie ein Redesign. Gemessen als Unterschied:

- `type: ui`, `assigned_role: frontend-developer` → Lease und Header tragen
  `["frontend-design", "webapp-testing"]`.
- `type: docs`, dieselbe Rolle, dasselbe Projekt → **kein** Schlüssel `references`, weder in der
  Lease noch im Header.
- Projekt ohne `.claude/skills` → Lease wird lautlos ohne Schlüssel gebaut (dieselbe
  Fail-quiet-Richtung wie `hand_back_path`; ein Zeiger darf einen Hinweis zurückhalten, nie einen
  Dispatch blockieren).
- `parse_header` liefert den Schlüssel NICHT zurück — er erreicht die Entscheidungsfläche des
  Gates nicht und gewährt nichts. Ebenfalls als Assertion gebaut.

**Aufzählungen:** Die Rollen- und Typlisten in den beiden Frontmattern sind die einzige
unvermeidbare Aufzählung dieser Runde, und sie tragen den Stolperdraht an **beiden** Enden (H84 d
nennt die Grenze des zweiten).

**Die Regel, die der Lead vorgeschlagen hat**, steht als Verfassungsabschnitt **§1a** im dev-Kit
(genau eine Prozedur-Skill je Rolle, gleichnamig; beliebig viele geteilte Referenz-Skills; ein
Referenz-Skill ist definiert als eines, das KEIN `skills:`-Frontmatter nennt) und ist als
Eigenschaft über den ausgelieferten Baum gemessen: heute deklarieren alle **27** Rollen der drei
Kits genau ihr eigenes Skill. Der PM-Skill sagt an der DELEGATE-Stelle ausdrücklich, dass die
Referenz-Skills **nicht** seine sind.

**Ehrlichkeit nach DEC-0056:** der Fehler, den das fängt, ist **vorhergesagt und nicht gemessen** —
bis zu dieser Runde gab es nichts zu wählen. Das steht so in `references.py`, in H84(a) und hier.
Der Mechanismus ist entsprechend billig gehalten: eine Kernel-Datei, ein Frontmatter-Block je
Skill, kein Gate.

## 5. Rot zuerst — jede Messung in einem Klon AUSSERHALB des Repos

Klon: `_round-scratch/TSK-0100/redcheck/` (nur `tools/`, `team-kits/`, `NOTICES.md`, `ruff.toml`),
grün vor jeder Mutation. Treiber: `red.py` (Textmutation, danach zurückgesetzt) und `red2.py`
(Datei entfernt). Eine Mutation, deren Anker nicht greift, meldet sich als `BROKEN` statt still
grün zu sein.

| # | wiederhergestellter Defekt | roter Test |
|---|---|---|
| M1 | eine Rolle beansprucht ein zweites Skill | `test_reference_skills.py::test_a_role_declares_exactly_its_own_procedure_skill` |
| M2 | ein Referenz-Skill deklariert nichts | `::test_every_shipped_skill_is_either_a_role_procedure_or_a_declared_reference` |
| M3 | Deklaration nennt eine Rolle, die das Kit nicht hat | `::test_every_shipped_reference_skill_can_be_named_by_some_task` |
| M4 | Deklaration nennt einen Aufgabentyp außerhalb `TASK_TYPES` | dito |
| M5 | ein Kit-Text schickt eine Rolle zu `frontend-desgin` | `::test_every_skill_retrieval_route_a_shipped_kit_file_spells_resolves` |
| M6 | `for_task` nimmt einen Namen aus einer Liste neben dem Baum | `::test_no_order_can_name_a_reference_skill_the_kit_does_not_ship` |
| M7 | eine inline-Änderungsmarke verschwindet | `::test_every_modification_mark_is_listed_and_every_listed_one_is_marked` |
| M8 | `NOTICES.md` verliert die Zeile eines übernommenen Skills | `::test_every_vendored_skill_is_listed_here_and_every_listing_resolves` |
| M9 | die Lizenzkopie wird gelöscht, die Zeile bleibt | dito |
| M10 | ein übernommenes Skill verliert `source_commit` | `::test_every_vendored_skill_carries_the_provenance_a_later_round_can_re_fetch` |
| M11 | ein Referenz-Skill behauptet, vorgeladen zu sein | `::test_no_shipped_skill_claims_to_be_loaded_at_session_start` |
| M12 | die Lease trägt die Ableitung nicht mehr | `::test_the_dispatch_header_names_the_reference_skills_the_task_derives` |
| M13 | der Pfadleser rät am WERT statt am Schlüssel | `test_design_system_contract.py::test_the_path_reader_reads_the_KEY_and_not_the_look_of_the_value` |
| M14 | das Rückgrat verlangt die menschliche Hälfte nicht mehr | `::test_a_bundle_missing_a_spine_part_is_refused_and_the_part_is_named` |
| M15 | die Suche schlüsselt auf `SKILL.md` statt auf den Index | `::test_a_role_procedure_skill_is_never_mistaken_for_a_design_system` |

**M11b, die Gegenmessung:** dieselbe Mutation wie M11, gefahren gegen den VORHANDENEN Wächter
`test_context_budget.py::test_no_skill_a_session_can_reach_claims_to_be_preloaded` — **grün**. Das
ist der Grund, warum der neue Test existiert: der alte leitet seine Menge aus dem
`skills:`-Frontmatter der Rollen ab, und ein Referenz-Skill steht dort per Definition nicht. Ohne
den neuen Test war die Vorlade-Behauptung für genau die Dateien ungedeckt, die diese Runde
hinzufügt.

**Ein eigener Defekt, gefunden durch die Mutationsläufe und behoben:** M13 war im ersten Lauf
GRÜN. Die Sonde des Pfadlesers war nicht diskriminierend — jeder ihrer Werte hatte entweder einen
Schrägstrich UND einen Pfad-Schlüssel oder keines von beidem, also lieferte die falsche
Implementierung („ein String mit Schrägstrich ist ein Pfad") dieselbe Menge. Die Sonde trägt jetzt
zwei Werte, die die beiden Leser trennen (`16px/1.5` als CSS-Kurzform mit Schrägstrich ohne Datei,
`styles.css` als Datei in der Bündelwurzel ohne Schrägstrich), und der Grund steht in ihrem
Docstring.

## 6. Suiten, Stempel, Werkzeuge (Ergebnisse dieses Stroms)

| Lauf | Ergebnis |
|---|---|
| `tools/test_hooks.py` + `tools/test_hooks_v2.py` | **3007 passed, 13 skipped** (27:13) |
| `tools/test_approvals_dispatch.py test_kernel.py test_backlog_types.py test_reference_skills.py test_e2e.py test_staging_cli.py` | **443 passed** (2:29) |
| `tools/test_kitupdate.py test_repo_hygiene.py test_parity_sources.py test_ci_lint_pinned.py test_handover_marker.py test_report.py test_board.py` | **231 passed, 1 skipped** |
| `tools/test_shortening_net.py test_role_contracts.py test_context_budget.py test_disposition.py test_reference_skills.py test_design_system_contract.py test_kitupdate.py test_repo_hygiene.py` | **197 passed, 1 skipped** |
| `tools/test_presets.py test_schemas.py test_state.py` (im Kernel-Lauf) | grün |
| `python tools/validate.py` | **all structural checks passed** |
| `python -m ruff check .` | **All checks passed** |
| `python tools/bump_kit_version.py` | dev-team **2026.09.01-5**, office-team **2026.09.01-2**, research-team **2026.09.01-2** — PROVISORISCH |

| `tools/test_migrate.py` | **141 passed** (4:14) |

**Ein Datenpunkt für DEC-0057 g, und er spricht gegen die Erwartung:** der Strom sollte nach
(b) nur die betroffenen Suiten fahren, hat aber am Ende **jede** Datei unter `tools/` gefahren —
weil die Änderung im KERNEL sitzt und damit fast jede Suite berührt. Die eingesparte Suitenzeit
eines Strom-Laufs ist in diesem Zuschnitt also ungefähr null; gespart wird Wanduhr durch die
Parallelität, nicht durch weniger Prüfen. Nur die volle Suite als EIN Lauf gegen den vereinigten
Baum fehlt weiterhin und gehört der Merge-Runde.

**Warum office-team und research-team mitgestempelt sind, obwohl ich sie nicht angefasst habe:**
der Kernel geht in den Inhaltshash **jedes** Kits ein, und `references.py`/`dispatch.py`/
`presets.py` sind Kernel. Das ist keine Spiegelverletzung, sondern der Grund, warum der Stempel
laut DEC-0057 (d) provisorisch ist.

**Zwei Ratschen im Strom neu aufgezeichnet** (DEC-0057 c — die Merge-Runde zeichnet erneut auf):

- `tools/lead_package_sizes.json`: dev-team **41 260 → 42 621 B (+1 361)**. Journalzeile in
  `docs/reviews/phase0-disposition.md` mit dem Grund: §1a muss LADEN und nicht registriert sein —
  der SPEZIALIST bekommt die abgeleiteten Namen im Dispatch-Header und ist der Leser, und ein
  Spezialist lädt nur die Verfassung plus seine eigene Rollendatei. Kein anderes Kit betroffen.
- `tools/constitution_section_pins.json`: NEU `dev-team constitution §1a`, GEÄNDERT
  `dev-team skills/project-manager/SKILL.md §Work loop`. Beide Änderungen sind reine Ergänzungen,
  aus keinem Abschnitt wurde etwas entfernt.

**Ein Fund der Suite, kein Fund von mir, und darum hier:** `test_backlog_types` wurde rot, weil
`dispatch_header` eine lokale Variable `named` band. `_key_read_aliases` verfolgt eine Bindung
**nach Namen** und ist scope-blind, also erbte ein zweites, unbeteiligtes `named` am Dateiende den
Schlüssel `references` und dessen `"; ".join(named)` galt als ungeschützter Elementzugriff auf ein
Referenzlistenfeld. Die Variable heißt jetzt `reference_skills`; der Grund steht als Kommentar an
der Zeile. Und `test_parity_sources` wurde rot, weil meine erste Überschrift im
`product-designer`-Skill („## When the project HAS…") den vorhandenen Anker `design§when-the`
mehrdeutig machte, der auf „When the user chose the MINIMAL ambition" zeigte; die Überschrift
heißt jetzt „## A design system the project already HAS (a dropped-in export)".

## 7. Löcher — nur die reservierten Nummern H83–H85

- **H83 — ein Referenz-Skill erreicht nur Projekte auf dem Preset `all`.** Die Skill-Schleife
  beider Scaffold-Zwillinge filtert Skill-VERZEICHNISSE über die Preset-ROLLENliste. **Gemessen
  an echten Scaffold-Läufen** gegen ein Wegwerf-`$HOME` (kein Eingriff in den globalen Store):
  Preset `team` → 11 Skills auf der Platte, beide Referenz-Skills dabei; Preset `solo` → 5 Skills,
  **keines von beiden**. Nicht aus diesem Strom schließbar: `scaffold_team.*` steht in
  `forbidden_scope` und gehört TSK-0101. Der Umweg über `presets.yaml` ist kein Umweg, sondern ein
  zweiter Defekt (`validate.py` Schritt 6/7 verlangt echte Kit-Rollen). Der Schnitt für die
  Merge-Runde steht im Eintrag als **Eigenschaft**: kopieren, wenn im Preset ODER wenn das Kit für
  den Namen keine `agents/<name>.md` ausliefert.
- **H84 — was die Ableitung NICHT bindet:** der Fehler ist vorhergesagt, nicht gemessen; der Header
  erzwingt nichts; die Fluchttür ist Prosa; die zweite Stolperdraht-Richtung ist an der Ableitung
  tautologisch und die Abruf-Schreibweise liest nur die Codex-Form (Grund gemessen: `/hooks`,
  `/model`, `/schedule` sind Provider-Kommandos in allen drei Kits); die Kreuzmenge ist die des
  Kits, nicht die eines Projekts mit abgewähltem Preset.
- **H85 — was die Herkunfts- und Bündelprüfungen NICHT sehen:** eine UNMARKIERTE Textänderung;
  `NOTICES.md` reist nicht ins Projekt (was dort die Pflicht erfüllt, liegt im Skill-Ordner);
  das Bündelschema ist an EINEM Export gemessen (Prototyp-Export ungemessen, stand schon so in
  FR-0045); ein Bündel ohne `_ds_manifest.json` findet der Suchlauf nicht (Preis in der Meldung
  benannt, beide Richtungen gemessen); der INHALT des Design-Systems wird nicht beurteilt und
  nichts ist ein Gate.

## 8. Was ich bewusst NICHT geschlossen, sondern nur benannt habe

1. **H83** — die Auslieferungslücke oben, in ZWEI Ketten (Scaffold-Preset und Codex-Spiegel).
   Blockierend für das Feature, keine der beiden aus diesem Scope schließbar. **Die erste Fassung
   dieses Punktes war falsch und ist korrigiert:** sie behauptete, `solo`/`duo` installierten
   `product-designer` und `frontend-developer` ohnehin nicht. Gemessen am echten Scaffold
   installiert `duo` **sieben** Rollen einschließlich `frontend-developer`, und `quality-engineer`
   steckt in `solo` UND `duo` — die Rollen sind da, die Verzeichnisse nicht. Wie es sich äußert,
   ebenfalls gemessen (und anders als vermutet): der Header nennt keine toten Skills, weil die
   Ableitung das `.claude/skills` des PROJEKTS liest — `duo`/`frontend-developer`/`ui` → `[]`,
   `solo`/`quality-engineer` → `[]`, während dasselbe im `team`-Projekt
   `['frontend-design', 'webapp-testing']` liefert. Der Ausfall ist stille Abwesenheit einer
   Fähigkeit, kein hängender Zeiger.
2. **Die Übersichtstabelle der offenen Löcher** in `docs/POST_V2_WISHLIST.md` (Abschnitt „Die
   offenen Einträge auf einen Blick") führt schon **H82 aus TSK-0099 nicht**, und ich habe H83–H85
   ebenfalls nur als Einträge angehängt statt Zeilen dort zu ergänzen. Grund: dieselbe Tabelle ist
   die wahrscheinlichste Merge-Kollision mit Strom B, und die Prosa der Tabelle behauptet
   Vollständigkeit, die sie seit der Vorrunde nicht hat. **Das gehört in die Merge-Runde**, nicht
   in einen Strom.
3. **Kein Netz-Test gegen die Upstream-Bytes.** Bewusst nicht gebaut (H85 a); ersetzt durch die
   Herkunftsangaben im Frontmatter.
4. **Die Zeiger `tools/test_reference_skills.py` in Verfassung §1a und in den beiden Skill-Kopfnoten
   lösen in einem INSTALLIERTEN Projekt nicht auf** — sie zeigen in das Kit-Quellrepo. Das ist die
   bestehende Hausform (`product-designer/SKILL.md` nennt seit TSK-0099 `tools/test_hooks.py::…`
   genauso) und richtet sich an den Kit-Entwickler, nicht an das Projekt. Ich habe es nicht
   geändert, weil eine Abweichung von der Hausform hier zwei Schreibweisen erzeugt hätte; benannt
   statt still gelassen.
5. **`project_memory/.audit/hook_events.jsonl` im Arbeitsbaum ist um zwei Zeilen gewachsen** — ein
   Nebeneffekt der Testläufe (dieselben zwei Zeilen stehen dort schon vom 2026-08-31). Die Datei
   ist **nicht** im Patch enthalten; ich habe sie auch nicht zurückgesetzt, weil das Zurücksetzen
   von Dateien nicht meine Entscheidung ist.

## 9. Geänderte und neue Dateien

**Neu:** `NOTICES.md` · `team-kits/dev-team/skills/frontend-design/{SKILL.md,LICENSE.txt}` ·
`team-kits/dev-team/skills/webapp-testing/{SKILL.md,LICENSE.txt}` ·
`team-kits/dev-team/templates/repo/scripts/kit_design_system_check.py` ·
`team-kits/kernel/references.py` · `tools/test_reference_skills.py` ·
`tools/test_design_system_contract.py`

**Geändert:** `docs/POST_V2_WISHLIST.md` (H83–H85 angehängt) · `docs/reviews/phase0-disposition.md`
(zwei Ratschen-Journalzeilen) · `team-kits/dev-team/constitution/AGENTS.md` (§1a neu) ·
`team-kits/dev-team/skills/product-designer/SKILL.md` (Abschnitt zum eingeworfenen Design-System) ·
`team-kits/dev-team/skills/project-manager/SKILL.md` (DELEGATE: die Referenz-Skills sind nicht
seine) · `team-kits/kernel/dispatch.py` · `team-kits/kernel/presets.py` (`SKILLS_DIR`) ·
`team-kits/repo_kit_owned.txt` · `tools/constitution_section_pins.json` ·
`tools/lead_package_sizes.json` · `team-kits/{dev,office,research}-team/VERSION`

**Nicht angefasst:** `team-kits/kernel/kitupdate.py`, `scaffold_team.*`, `install.*`,
`init_project_memory.*`, `user/**`, `.claude/**`, alles unter `team-kits/office-team/` und
`team-kits/research-team/` außer deren `VERSION` (Kernel-Hash, siehe oben). Keine gespiegelte
Datei berührt: das neue Repo-Skript ist dev-only, und `_assert_mirrored` überspringt einen Namen,
den nur ein Kit trägt (wie `kit_design_render.py`).


---

# Nacharbeit nach dem Prüfer-FAIL (2026-09-01 23:23:52 – 2026-09-02 00:17:57, **54 min**)

Drei Blocker, alle geschlossen; vier Reste benannt, einer davon gebaut.

## F1 — echter Ausfall: eine nicht-UTF-8-Datei am Einwurfpunkt tötete jeden Dispatch

Selbst nachgemessen vor dem Fix (`_round-scratch/TSK-0100/f1/repro.py`, cp1252-`SKILL.md` unter dem
Skill-Verzeichnis): `declarations` und `for_task` je `UnicodeDecodeError: 'utf-8' codec can't decode
byte 0xfc`. Das ist genau der Ort, an den FR-0045 den Nutzer einlädt, sein Export-Bündel
auszupacken. Fix: `except (OSError, UnicodeDecodeError)` — ein **Fang** und ausdrücklich nicht
`errors="replace"`, weil ersetzte Bytes dem Abgleich einen verstümmelten Rollennamen als
Deklaration übergeben würden; eine Datei, die dieser Leser nicht dekodieren kann, ist eine, über die
er nichts sagt. Nach dem Fix: `declarations -> {}`, `for_task -> []`.
**Nachbar im selben Muster mitgefixt:** `dispatch.role_tools` hatte dieselbe Zeile. Dort liegt keine
gemessene Kette (die Datei schreibt der Installer), und der Kommentar sagt das so, statt eine zweite
Begründung zu erfinden.
**Der Docstring sagt jetzt das Gebaute**, nennt die gemessene Kette und den roten Test.

## F2 — der Codex-Spiegel trägt kein Referenz-Skill, drei Texte behaupteten es

Unabhängig nachgemessen am eigenen Scaffold-Rig, Preset `team`: `.claude/skills` = 12 Verzeichnisse
(11 Kit-Skills + das eingeworfene Design-System), `.agents/skills` = **9**, genau die installierten
Rollen. Ursache im laufenden Code gelesen: `gen_provider_artifacts.py` baut `roles` aus
`.claude/agents/*.md`, gefiltert durch `.claude/team_kit_roles.txt`, und spiegelt über diese Liste.
Ein Referenz-Skill hat keine Rolle.

Gemacht, alles im Scope: die drei Sätze (`frontend-design/SKILL.md`, `webapp-testing/SKILL.md`,
Verfassung §1a) sagen jetzt, dass es auf Codex **keine** native Kopie gibt und man
`.claude/skills/<name>/SKILL.md` liest. Der Routen-Test sagt in seinem Docstring, dass sein Subjekt
der KIT-Baum ist und was er deshalb nicht sieht. Und die Grundlage der neuen Sätze ist gegen den
laufenden Generator gepinnt: `test_the_codex_mirror_is_generated_per_role` liest per AST jede Stelle,
die einen Spiegelpfad zusammensetzt, und trennt dabei **Produzenten** (Schleife über einen Namen)
von **Aufzählern** (Schleife über einen Aufruf — `legacy_owned_outputs` listet die Vorgängerausgabe
zum Entfernen). Dass diese Trennung nötig ist, war eine eigene Messung: der erste Leser meldete den
Aufzähler als „Spiegel nicht mehr rollenabgeleitet", der zweite fand nur einen Produzenten statt
zwei, weil der `comprehension`-Knoten UNTER der Comprehension hängt und nicht über ihrem Element.

In `H83` steht die gemessene Codex-Kette, und der Merge-Schnitt hat jetzt **zwei** Stellen — die
Scaffold-Zwillinge und `team-kits/gen_provider_artifacts.py`, ausdrücklich als **Nahtdatei außerhalb
jedes Stroms** benannt, die die Merge-Runde anfassen muss.

## F3 — die Milderung war falsch

Siehe oben unter „bewusst nicht geschlossen". Beide Stellen (H83 und Protokoll) tragen jetzt die
Messung: `duo` = 7 Rollen inkl. `frontend-developer`, `quality-engineer` in `solo` und `duo`, und
die Ableitung schweigt dort, statt ins Leere zu zeigen.

## Reste

- **F4** — die Zahl „11 / 10 / 8 routes" im Docstring ist ersatzlos raus; der Docstring sagt jetzt
  ausdrücklich, dass eine ungepinnte Zählung dort nicht steht.
- **F5** und **F7** — in `H85(c)` als (c1) dateisystemabhängige Existenzprüfung und (c2)
  Pfad-Regel greift in unbekannte `*Path`-Schlüssel, je mit dem Grund, warum die Alternative
  schlechter wäre.
- **F6** — gebaut, weil billig: ein WRAPPER-Ordner bekommt „das Bündel liegt eine Ebene tiefer, in
  `<name>`" statt drei „X is missing"-Zeilen. Gebunden an eine benannte Form (kein Rückgrat hier,
  genau ein Kind mit Index). Die Zusammenfassungszeile schrieb „Re-export … a partial unpack is the
  shape this check exists for" — für einen Wrapper eine **falsche Anweisung**, deshalb nennt sie
  jetzt beide Ursachen statt einer. Grenze in `H85(d)`: eine zweite Ebene wird nicht gesucht, und
  der Suchlauf steigt weiterhin nicht hinab.

## Rot zuerst für die Nacharbeit (Klon außerhalb des Repos, `red3.py`)

| # | wiederhergestellter Defekt | roter Test |
|---|---|---|
| R1 | der Frontmatter-Leser fängt wieder nur `OSError` | `test_reference_skills.py::test_a_skill_file_that_is_not_utf8_never_reaches_the_dispatch` |
| R2 | der Codex-Spiegel wird über das Skill-Verzeichnis gebaut | `::test_the_codex_mirror_is_generated_per_role` |
| R3 | der Wrapper-Hinweis wird wieder ausgebaut | `test_design_system_contract.py::test_a_wrapper_folder_is_told_that_the_bundle_is_one_level_down` |
| R4 | der Wrapper-Hinweis feuert bei jedem fehlenden Index | `::test_the_wrapper_hint_never_hides_a_real_missing_part` |

Die 15 Mutationen der Erstrunde plus M9 wurden gegen den nachgearbeiteten Baum **erneut** gefahren:
alle rot, M11b weiterhin grün (die Gegenmessung).

**Ein eigener Defekt der Nacharbeit, gefunden durch R4:** meine erste zweite-Richtungs-Sonde für den
Wrapper-Hinweis war GRÜN gegen einen `wrapper_child` ohne eigenen Wächter — keine ihrer Proben trug
die einzige Form, über die der Wächter entscheidet (ein Verzeichnis, das SELBST ein Bündel ist und
zusätzlich ein Kind-Bündel hat). Die Probe ist ergänzt, der Grund steht in ihrem Docstring.

## Läufe der Nacharbeit

| Lauf | Ergebnis |
|---|---|
| `test_reference_skills test_design_system_contract test_context_budget test_backlog_types test_shortening_net test_role_contracts test_disposition test_parity_sources` | **184 passed** (1:08) |
| `test_approvals_dispatch test_kernel test_e2e test_staging_cli test_kitupdate test_repo_hygiene test_presets test_schemas` | **518 passed, 1 skipped** (5:09) |
| `test_hooks test_hooks_v2` | **3007 passed, 13 skipped** (28:49) |
| `test_migrate test_board test_report test_handover_marker test_ci_lint_pinned test_state` | **358 passed** (6:02) |
| Absatz-Treue gegen die Upstream-Bytes | erneut **0 nicht deklarierte Unterschiede** |
| `ruff check .` · `validate.py` | grün |
| Ratschen erneut aufgezeichnet (PROVISORISCH) | Lead-Paket dev **42 621 → 42 751 B (+130)**, ein Verfassungs-Pin `1a` CHANGED |
| Stempel (PROVISORISCH) | dev **2026.09.01-6**, office **2026.09.01-3**, research **2026.09.01-3** |

## Zusätzlich geänderte Dateien in der Nacharbeit

`team-kits/kernel/references.py` · `team-kits/kernel/dispatch.py` ·
`team-kits/dev-team/skills/frontend-design/SKILL.md` ·
`team-kits/dev-team/skills/webapp-testing/SKILL.md` ·
`team-kits/dev-team/constitution/AGENTS.md` ·
`team-kits/dev-team/templates/repo/scripts/kit_design_system_check.py` ·
`tools/test_reference_skills.py` · `tools/test_design_system_contract.py` ·
`docs/POST_V2_WISHLIST.md` · `docs/reviews/phase0-disposition.md` ·
`tools/lead_package_sizes.json` · `tools/constitution_section_pins.json` · die drei `VERSION`.
`team-kits/gen_provider_artifacts.py` wurde **gelesen und nicht angefasst** — Nahtdatei.
