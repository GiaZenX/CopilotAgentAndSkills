# TSK-0096 / BUG-0075 — Rundenprotokoll (Umsetzer)

Datum: 2026-08-30 · Rolle: `harness-implementer` · Arbeitsverzeichnis ausserhalb des Repos:
`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0096\`

## 1. Was gebaut wurde

**Die Route steht jetzt in der Definition jeder Rolle, die ein Kit-Dokument besitzt** — neun Rollen
in drei Kits, abgeleitet und nicht aufgezählt:

| Kit | Rolle | Dokumente (aus §6 × `documents.accepts`) |
|---|---|---|
| dev-team | project-manager | `project_config.yaml` |
| office-team | office-manager | `business_profile.yaml`, `project_config.yaml` |
| office-team | records-clerk | `filing_plan.yaml` |
| office-team | bookkeeper | `master_data.yaml` |
| office-team | product-editor | `content_guidelines.yaml`, `product_catalog.yaml` |
| office-team | compliance-researcher | `compliance_register.yaml` |
| office-team | marketing-planner | `marketing_plan.yaml` |
| research-team | project-manager | `fzulg_documentation.yaml`, `project_config.yaml` |
| research-team | methodologist | `literature.yaml`, `methodology.yaml`, `research_guidelines.yaml` |

Der Absatz ist in allen neun Dateien byte-gleich bis zu dem Satz, der die eigene Datei nennt; danach
steht das Rollen-Eigene (welche Datei, wer das Kommando fährt, welches Feld ein anderer Schreiber
besitzt).

## 2. Die Ableitung (AC-1/AC-4), und woher jede Hälfte kommt

Neu in `tools/test_role_contracts.py`, Abschnitt 7:

* **schreibbare Dokumente** — `kernel.documents.accepts` gegen einen aus dem Template-Baum
  aufgestellten Projektordner. Keine Endungsliste: `product/masterplan.md` und jedes `README.md`
  fallen heraus, weil sie nicht als YAML-Mapping vergleichbar sind.
* **Besitztabelle** — die Markdown-Tabelle der Verfassung, gefunden über **zwei** Eigenschaften: ihr
  Kopf nennt eine OWNER-Spalte, und ihre Zeilen nennen mindestens eine Datei, die das Projekt
  wirklich hat. Die zweite Eigenschaft ist nicht Zierde: dev und research fahren zusätzlich eine
  **Phasentabelle** mit `Owner`-Spalte (dev `AGENTS.md` Zeile 102), die Schritte zuordnet statt
  Dateien; ohne die zweite Eigenschaft war der Reader dort rot mit „2 Tabellen". Office hat in
  seiner Phasentabelle keine solche Spalte — gemessen, `probe_rework.py`; ein früherer Satz hier und
  im Docstring behauptete „jedes Kit", das war ein Allquantor über drei Fällen mit einem
  Gegenbeispiel (Prüferbefund F4).
* **Rollenauflösung** — Token der Owner-Zelle gegen (a) den Dateinamen der Rolle und (b) die
  `Keywords:`-Liste ihrer `description`. Das ist nötig, weil die drei Tabellen sich nicht reimen:
  office schreibt `Manager`, `Records-Clerk` im Klartext, dev/research schreiben `**PM**` — und `PM`
  steht in keinem Dateinamen, wohl aber in beiden Keyword-Listen. Der Freitext der `description`
  wird bewusst NICHT gelesen (dev-Architekt nennt sich „invoked by the Project Manager", ein
  Freitext-Reader gäbe jedem dev-Dokument zwei Besitzer).
* **Partielle Schreiber** — `kernel.layout.partial_writers` pro Dokument. Deshalb muss die Route der
  Records-Clerk `add-filing-rule` nennen und die der drei Leads `set-preset`: `apply-proposal`
  verweigert eine Änderung an einem Feld, das ein benannter Schreiber besitzt.

## 3. Rot-zuerst (Messung, nicht Behauptung)

### 3.1 Gegen den AUSGELIEFERTEN Baum, vor jeder Textänderung

`python -B -m pytest tools/test_role_contracts.py -q -k owns_a_kit_document`

**10 Befunde über 9 Besitzer-Rollen** (nachgemessen mit der AUSGELIEFERTEN Testfassung gegen die
Rollentexte aus `git HEAD`, im Klon: `mutate3.py`, Protokoll `rework-mutations.txt`): 7 Rollen
nannten `apply-proposal` in ihrer Definition **gar nicht** (dev/project-manager, office/bookkeeper,
office/compliance-researcher, office/marketing-planner, office/records-clerk,
research/methodologist, research/project-manager); office/office-manager und office/product-editor
nannten es, aber ohne die zu stagende Datei, und der office-manager ausserdem ohne `set-preset`.

Der erste Lauf (`red-before.txt`) meldete **12** — er lief gegen die Testfassung VOR der
Verfeinerung `span != staged`, die eine blosse Erwähnung des Vorschlagsbereichs nicht mehr als
zweite gestagte Datei zählt; die zwei zusätzlichen Befunde waren dieser Leserfehler, nicht zwei
weitere Mängel im Baum. Die Datei bleibt als Beleg des ersten Laufs liegen, die gültige Zahl ist 10
(Prüferbefund F6).

### 3.2 Mutationen in einem Klon AUSSERHALB des Repos

`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0096\mutate.py`, Ausgabe in `mutations.txt`.
Basislauf des gelieferten Baums: 3 passed.

| Mutation | rot geworden |
|---|---|
| M1 product-editor verliert den Routen-Absatz (der Livefall, Hälfte 1) | `test_every_role_that_owns_a_kit_document_carries_the_route_that_writes_it`, `test_the_document_route_is_one_text_wherever_it_stands` |
| M2 product-editor stagt `claims_policy.proposed.md` statt `content_guidelines.yaml` (der Livefall, Hälfte 2) | `test_every_role_that_owns_a_kit_document_carries_the_route_that_writes_it` |
| M3 records-clerk nennt `add-filing-rule` nicht mehr | `test_every_role_that_owns_a_kit_document_carries_the_route_that_writes_it` |
| M4 filing-reviewer (besitzt kein Dokument) bekommt die Route | `test_every_role_that_owns_a_kit_document_carries_the_route_that_writes_it` |
| M5 methodologist formuliert EINEN Satz der Form um | `test_the_document_route_is_one_text_wherever_it_stands` |
| M6 office-manager wird auf `product/masterplan.md` geschickt | `test_every_role_that_owns_a_kit_document_carries_the_route_that_writes_it`, `test_no_document_owner_is_routed_at_one_the_command_would_refuse` |
| M7 filing-reviewer nennt das Kommando in einem ABSATZ statt in einem Aufzählungspunkt (`mutate2.py`) | `test_every_role_that_owns_a_kit_document_carries_the_route_that_writes_it` |

**M5 war zuerst GRÜN.** Die erste Fassung von `test_the_document_route_is_one_text_wherever_it_stands`
fragte nur „die Absätze teilen mindestens einen Satz"; drei von vier Sätzen blieben geteilt, die
Untergrenze hielt, und die umformulierte Behauptung („a new file beside a kit document is fine")
kam durch. Die Fassung, die ausgeliefert wird, schneidet jeden Routen-Absatz an seinem ersten Satz
ab, der eine gestagte Datei nennt, und vergleicht die Vorläufe auf **Gleichheit**. Damit ist M5 rot.

**M3, M5 und M6 waren danach ein zweites Mal grün — an der MESSAPPARATUR, nicht am Test.** Nach dem
Neuumbruch der neun Absätze (§8) fanden die wörtlichen Suchmuster des Mutationsskripts ihre Stelle
nicht mehr und mutierten nichts; drei Mutationen meldeten „3 passed", als wären sie gedeckt. Genau
die Klasse, die dieses Repo „ein Test, der nicht scheitern kann" nennt — hier auf der Seite des
Messrigs. `mutate.py` ersetzt seither über Regex mit `\s+` zwischen den Wörtern und **behauptet
jeden Treffer** (`assert len(found) == 1`), so dass eine Mutation, die nichts trifft, laut abbricht
statt grün zu melden.

## 4. AC-3 — Entscheidung: die ROLLE sagt es, ein Kernel-Weg wird als Folgepunkt benannt

**Gemessen** (`probe_refusal.py`, gegen den laufenden Kernel, office-Template):

* Füllen eines leeren Skalars → `ACCEPTED: ['tone: gefüllt mit sachlich']`
* Ersetzen eines gefüllten Werts → `REFUSED: the proposal changes `tone`, which already carries a
  value, and this command only ADDS … Remedy: … correcting a value the project already recorded is
  an edit the user makes themselves.`
* Löschen eines Schlüssels → `REFUSED: the proposal drops `tone` … removing something is an edit the
  user makes themselves.`

**Entscheidung: der Rollentext sagt es, und zwar in dem Absatz, der die Route trägt.** Drei Gründe,
und alle drei sind gemessen statt gemeint:

1. Der Kernel sagt es bereits selbst — beide Verweigerungen enden auf „an edit the user makes
   themselves". Ein Rollentext, der stattdessen einen Weg verspräche, behauptete Schutz, den der
   Code nicht baut; ein Rollentext, der schweigt, ist genau der Zustand, aus dem der Livefall kam.
2. Der Livefall selbst ist ein REFUSED-Fall. `content_guidelines.yaml` liefert `claims_policy` als
   gefüllten Block-Skalar aus (siehe Kopf der Vorlage); die „überarbeitete Quellen-Regel" ersetzt
   ihn, also hätte `apply-proposal` sie verweigert. Der Text sagt das jetzt ausdrücklich in der
   product-editor-Definition: der Weg über den Editor des Nutzers war richtig, falsch war die
   erfundene Datei und die Prosa statt Alt- und Neu-Zeilen.
3. Ein Ersetzungs-Kommando ist eine andere Freigabefrage, nicht dieselbe mit einem Flag mehr. Die
   ganze Sicherheit von `apply-proposal` ist „nichts Bestehendes kann verschwinden"; wer das
   aufhebt, muss dem Nutzer pro Stelle ALT und NEU zeigen, sonst unterschreibt er eine Zahl — das
   ist die Klasse, für die `documents._owned_elsewhere` gebaut wurde (Prüferbefund B4). Das ist eine
   eigene, sicherheitslastige Runde.

**Benannter Folgepunkt, in dieser Runde NICHT gebaut:** ein Kernel-Weg für die ersetzende Änderung
eines Kit-Dokuments (Arbeitstitel: `replace-in-document`), mit einer Freigabekarte, die pro Stelle
Alt und Neu zeigt. Er ist kein „bekannt, kommt später" im Sinne der Löcherliste — es ist keine
Durchsetzungslücke, sondern eine fehlende Fähigkeit, also ein FR-Item. Der Sitzungsagent muss es
aufnehmen; der Umsetzer darf unter `project_memory/` nichts ausserhalb von `staging/` schreiben.

## 5. Was diese Runde bewusst NICHT geschlossen hat

* **Der Ersetzungsweg** (oben, §4) — benannt, nicht gebaut.
* **Prosa bleibt Prosa.** Die drei neuen Tests lesen Text. Sie können erkennen, dass eine Route
  fehlt, dass sie die falsche Datei nennt und dass die Form auseinanderläuft. Sie können nicht
  erkennen, ob eine Rolle sie befolgt — kein Hook liest Freitext. Ein Text, der in allen neun
  Dateien dasselbe FALSCHE sagt, kommt durch; was ihn sichtbar macht, ist, dass er neunmal geändert
  werden muss, und der Sektionspin über den drei Lead-Dateien.
* **SKILL-Dateien sind nicht Gegenstand der Ableitung.** Geprüft wird `agents/<rolle>.md`, weil das
  die Datei ist, die der Provider der Rolle einspielt; ein SKILL ist registriert, nicht injiziert
  (gemessen 2026-08-02, `tools/provider_observations.json`). Eine SKILL-Datei wurde trotzdem
  korrigiert, weil sie das Gegenteil behauptete (§6 unten).
* **`staging/<task-id>/` vs. `staging/<TSK-ID>/`** — die research-methodologist-Definition schreibt
  die Ablage in einem älteren Satz klein. Der Kernel schreibt `<TSK-ID>`; der neue Absatz auch. Die
  alte Schreibweise steht unangetastet, weil sie kosmetisch ist und nicht zum Auftrag gehört.

## 4a. Nacharbeit nach dem FAIL des Prüfers (F1–F6 + ein geschlossenes Loch)

| Befund | Was war | Was jetzt gilt (gemessen) |
|---|---|---|
| **F1** blockierend | `research-team/constitution/AGENTS.md` §5a/7: „`research_guidelines.yaml` still has NO writer at all … report the need instead of hand-writing it" — für ein Dokument, das diese Runde dem Methodologen zuweist. Die Verfassung übertrumpft die Rollendatei. | Der Teilsatz sagt jetzt, was §6 derselben Datei führt: kein TOOL-Schreibzugriff, aber `apply-proposal` über `staging/<TSK-ID>/research_guidelines.yaml`; Ändern/Löschen bleibt Editorschritt des Nutzers. Gemessen: `documents.accepts` = True. |
| **F2** blockierend | dev PM und research PM: „The **model/effort maps** are the half with no writer" — 30 Zeilen unter dem neuen Routen-Absatz. | Gemessen (`probe_rework.py`): NEUER Eintrag → `ACCEPTED: ['model_map.data-migrator: neu, Wert worker', 'effort_map.data-migrator: neu, Wert high']`; GEÄNDERTER Eintrag → `REFUSED … only ADDS`. Der Text sagt jetzt genau das. |
| **F3** | Die drei Lead-Texte druckten die Befehlszeile ohne `--reason`. | Gemessen (`probe_reason.py`): `request-approval document_proposal` und `apply-proposal` ohne `--reason` → **rc 2**, „a document_proposal approval question must say what it releases, and reason is missing"; mit `--reason` → rc 0 bzw. die erwartete Freigabe-Verweigerung. `--reason` steht in allen drei Texten. Die unvollständige Remedy in `kernel/documents.py` ist **nicht** angefasst — eigenes Item des Sitzungsagenten. |
| **F4** | Docstring von `_ownership_table`: „every kit also runs a PHASE table with an `Owner` column". | Gemessen: dev und research ja, **office nein**. Allquantor raus, die beiden Orte benannt. Auch in §2 dieses Protokolls korrigiert. |
| **F5** | Docstring: „…cannot invent a second one beside it" — eine Garantie, die der Test nicht baut. | Auf Absicht gedreht („no OCCASION to invent"), mit Zeiger auf die Grenze; die Grenze steht als H79 (a) in der Löcherliste. |
| **F6** | „12 Befunde" stammten aus der Testfassung vor `span != staged`. | Mit der ausgelieferten Fassung nachgemessen: **10**. §3.1 trägt Zahl und Ursache. |

**Ein Loch geschlossen statt benannt (Prüfer-V1):** ein schreibbares Kit-Dokument, für das die
Besitztabelle KEINEN Besitzer nennt, schuldete die Route niemandem.
`test_every_role_that_owns_a_kit_document_carries_the_route_that_writes_it` prüft jetzt zusätzlich
je Kit, dass `writable − owned` leer ist. Heute für alle drei Kits leer; rot gemessen als **M8** an einem in das
office-Template eingelegten `supplier_terms.yaml` (`mutate3.py`).

**Drei Löcher benannt statt geschlossen:** `docs/POST_V2_WISHLIST.md` **H79** (Eintrag +
Tabellenzeile) — erfundene Zweitdatei ohne `staging/`-Präfix unsichtbar; derselbe falsche Text in
allen Besitzer-Definitionen kommt durch; SKILLs und Verfassungen liegen ausserhalb der Ableitung,
obwohl beide dieselbe Falschaussage tragen können (in dieser Runde je eine gefunden und von Hand
korrigiert).

## 4b. Nachzügler aus dem Lieferlauf des Sitzungsagenten

`tools/test_hooks.py::test_every_span_that_presents_the_command_surface_names_all_of_it` war rot auf
`research-team/agents/project-manager.md`: „names 3, misses add-filing-rule, apply-proposal, …".
Ursache war mein F2/F3-Satz — er nannte `capture` in Backticks und brachte den §0-Aufzählungspunkt
damit auf DREI Kommandonamen. Ab drei liest dieser Draht einen Block als **Präsentation der
Kommandofläche** und verlangt dann alle 25 oder gar keine Liste (der Schwellwert liegt in einer
gemessenen leeren Bandbreite zwischen „Prosa erwähnt ein Kommando" und „Text listet die Fläche").

Fix nach der Regel, die der Test selbst nennt: unter drei Namen bleiben. Der Satz sagt dieselbe
Sache ohne den Kommandonamen — „`fzulg_documentation.yaml` is no typed item, so nothing on the item
path creates it". Isolierter Lauf danach: **1 passed**; `-k surface` (alle drei Geschwister):
**3 passed**.

Gegenprobe für die anderen beiden Leads, wie beauftragt (`probe_surface.py`, zählt je Block die
Kommandonamen in Backticks gegen `cli.build_parser()`): kein Block einer Rollendatei liegt bei drei.
Bei ZWEI liegen jetzt vier Blöcke — dev PM §0 und research PM §0 (`request-approval`, `transition`)
sowie die Routen-Absätze von dev PM, research PM und office-manager (`apply-proposal`, `set-preset`)
und der von records-clerk (`add-filing-rule`, `apply-proposal`). Das ist kein Fehler und keine
Umgehung, aber ein benannter Rand: ein Besitzer, dessen Dokument einen **zweiten** benannten
Teilschreiber bekäme, überschritte die Schwelle allein durch die abgeleitete Pflicht aus §2. Der
§0-Block der research-Verfassung nennt alle 25 und ist damit vollständig.

## 5a. Zwei Befunde aus der Selbstprüfung, in derselben Runde behoben

1. **Der Routen-Absatz behauptete beinahe eine Verweigerung, die es nicht gibt.** „A NEW file beside
   a kit document is not a proposal" liest sich wie ein Kernel-Nein. Gemessen: `proposal_path` nimmt
   **jede** Datei in `staging/<TSK-ID>/`, nur der INHALT wird verglichen — eine vollständige, gültige
   YAML-Fassung unter anderem Namen ginge durch. Der Absatz sagt das jetzt: „it compares CONTENT and
   never the file name, so the NAME is yours to get right". Verweigert wird nur die Hälfte, die der
   Parser sieht (Prosa), und genau die traf den Livefall.
2. **Die Gegenrichtung las nur Aufzählungspunkte.** Eine Rolle ohne eigenes Dokument, die das
   Kommando in einem gewöhnlichen Absatz nennt, wäre durchgekommen. Der Test liest auf dieser Seite
   jetzt die **ganze** Definition; auf der Besitzerseite bleibt der Aufzählungspunkt die Einheit,
   weil dort gefragt wird, was EIN Block sagt. Messung: M7.

## 6. Berichtigte Falschaussagen (Hausregel 3, beide Richtungen)

Drei ausgelieferte Sätze behaupteten eine Sackgasse, die der Code seit `apply-proposal` nicht mehr
baut — die über-alarmierende Richtung, und sie ist genauso falsch wie die beruhigende:

* `office-team/agents/bookkeeper.md`: „Nothing can write the file — it is a kit document, and no
  command names it".
* `office-team/skills/bookkeeper/SKILL.md` Schritt 4: „nothing can write the FILE … no `harness.py`
  command names this file … the USER, who edits the file outside the session".
* `research-team/agents/project-manager.md`: „`fzulg_documentation.yaml` … is no typed item either,
  so nothing writes it after the install".

Nach dem Prüferbericht kamen drei weitere dazu (§4a): die research-Verfassung („`research_guidelines.
yaml` still has NO writer at all", F1) und in beiden PM-Definitionen „the **model/effort maps** are
the half with no writer" (F2) — die letzten beiden waren nur zur Hälfte falsch, und genau die Hälfte
sagen sie jetzt: eine ÄNDERUNG hat keinen Schreiber, ein NEUER Eintrag hat einen.

## 7. Geänderte Dateien

Kit-Texte: `team-kits/{dev-team,research-team}/agents/project-manager.md`,
`team-kits/research-team/agents/methodologist.md`,
`team-kits/research-team/constitution/AGENTS.md` (F1),
`team-kits/office-team/agents/{office-manager,product-editor,bookkeeper,records-clerk,compliance-researcher,marketing-planner}.md`,
`team-kits/office-team/skills/bookkeeper/SKILL.md`.
Werkzeuge: `tools/test_role_contracts.py` (Abschnitt 7).
Dokumentation: `docs/POST_V2_WISHLIST.md` (H79 + Tabellenzeile).
Aufzeichnungen: `tools/constitution_section_pins.json`, `tools/lead_package_sizes.json`,
`docs/reviews/phase0-disposition.md` (je eine Journalzeile pro Kit/Sektion).

Gespiegelte Dateien: **keine berührt** — Rollendefinitionen und SKILLs sind kit-eigen, `hooks/`,
`kernel/` und `settings/` blieben unangetastet.

Lead-Paket-Wachstum (gemessen, in zwei Schritten mit je einer Journalnotiz aufgezeichnet):
dev 39444 → 40633 → 40755 B, office 46401 → 47561 → 47685 B, research 43486 → 44774 → 44898 B.
Die drei Leads besitzen selbst Dokumente und fahren die Route ausserdem für jeden Spezialisten,
also gehört der Absatz in das geladene Paket.

## 8. Läufe und Stempel (Stand nach der Nacharbeit)

* `python -m ruff check .` — All checks passed.
* `python tools/bump_kit_version.py` → dev-team **2026.08.30-16**, office-team **2026.08.30-17**,
  research-team **2026.08.30-17** (der Nachzügler aus §4b berührt nur research; dev und office
  blieben unverändert).
* `pytest tools/test_hooks.py -k surface -q` — 3 passed (nach dem Fix aus §4b).
* `python tools/validate.py` — all structural checks passed.
* `pytest tools/test_role_contracts.py tools/test_shortening_net.py tools/test_context_budget.py
  tools/test_disposition.py tools/test_repo_hygiene.py -q` — 119 passed.
* `pytest tools/test_hooks.py -k "mirror or version or instruction or role or constitution" -q` —
  32 passed.
* `pytest tools/test_kitupdate.py -q` und `pytest tools/test_hooks_v2.py -k "agent or role or
  frontmatter or dispatch" -q` — grün (vor der Nacharbeit; die Nacharbeit ändert nur Prosa in
  denselben Dateien).
* `python -B -m pytest .claude/hooks/test_gates.py -q` — 244 passed, **1 failed**, und der Fehler
  war meiner: `test_every_reference_to_a_measurement_leads_to_one` verlangt, dass ein
  `docs/reviews/*.md`, das ein Löcherlisten-Eintrag NENNT, den Eintragsnamen auch trägt. H79 nannte
  das Dispositionsdokument als Ort der Journalzeile. Der Zeiger geht jetzt auf
  `tools/pin_constitution_sections.py`, also auf den laufenden Code statt auf ein Dokument, das die
  Nummer nicht führt. Nachlauf `-k "hole or measurement or reference"` — 8 passed.
* Die **volle** Suite ist nach DEC-0050 der Lieferschritt des Sitzungsagenten und wurde hier nicht
  gefahren.

## 9. Ratschen (beide, mit Journalzeile)

* `tools/pin_constitution_sections.py --write --note …` — in zwei Schritten insgesamt 9 Sektionen:
  drei „What you are and are not" (Routen-Absatz), dann nach dem Prüferbericht dieselben drei
  erneut plus zwei „Startup gate" und die research-Verfassung „2. Hard enforcement (NEVER skip)".
* `tools/record_lead_package_sizes.py --write --note …` — dev 39444 → 40633 → 40755 → 40981 B,
  office 46401 → 47561 → 47685 → 47793 B, research 43486 → 44774 → 44898 → 45410 → 45422 B. Der
  grosse research-Sprung (+512) ist der Verfassungssatz aus F1, der letzte (+12) der Nachzügler
  aus §4b. Insgesamt 10 Sektionen im Pin-Journal, 10 Kit-Zeilen im Grössenjournal.
