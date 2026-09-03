# TSK-0111 — Rundenprotokoll (Strom K „humanizer", zweite DEC-0057-Generation, Stufe Fable)

**Baum:** `C:\Offline Repos\v2-testbed\_worktrees\g2-humanizer\`, Zweig `g2/humanizer`, Basis
`6d18407` (Release 2026.09.02-10). **Scratch:** `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0111\`.
**Start:** 2026-09-02, erste Uhrzeitlesung 11:25:03 (die Lesephase davor — Item, FR, DECs,
`references.py`, die Tests, die die Datei lesen werden — ist nicht gemessen, geschätzt ~10 min).
**Ende:** siehe Abschnitt 7. **Nicht getan, wie es der Strom verlangt:** kein Commit, keine volle
`tools/`-Suite, keine Installation in den globalen Store. Die Stempel sind PROVISORISCH
(`2026.09.02-12` in allen drei Kits nach dem Erstdurchgang; `2026.09.02-13` nach Nacharbeit 1, Abschnitt 8; `2026.09.02-16` nach Nacharbeit 2, Abschnitt 9; `2026.09.02-17` nach Nacharbeit 3, Abschnitt 10).
Lochnummern H120–H122: **H120 ist seit Nacharbeit 2 verbraucht** (§9.1), H121/H122 nicht (§9.4). Der
Satz in Abschnitt 5 daneben beschreibt den Erstdurchgang und ist abgelöst.

**Übergabe:** `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0111\stream-humanizer.patch`
(`git diff HEAD`, neue Dateien über `git add -N` enthalten).

---

## 1. Gebaut

### 1.1 Der Referenz-Skill `humanizer`, dreifach byte-identisch

`team-kits/{dev,office,research}-team/skills/humanizer/SKILL.md` — drei Kopien, sha256
`8cd4a159…3a60` im Erstdurchgang (der aktuelle Hash steht in Abschnitt 9), 0 CRLF, ~16 KB. Kein `LICENSE.txt` daneben, keine `references/`-Datei: der Text
ist eigener Text, und ein Lizenz-Beileger ist in dieser Suite die DEFINITION von „vendored"
(`test_reference_skills._vendored`), also darf keiner dort liegen. `NOTICES.md` unangetastet (Auftrag:
nur bei übernommenem Wortlaut; keiner übernommen — und eine Zeile dort, die das Verzeichnis nennt,
verlangt über `test_every_vendored_skill_is_listed_here_and_every_listing_resolves` sofort eine
Lizenzkopie). `repo_kit_owned.txt` unangetastet: das ist die Liste der Repo-**Skripte**, die der
Scaffold überschreibt; ein Skill-Verzeichnis kopiert der Scaffold ohnehin (H83-Schleife, beide
Zwillinge), gemessen unten in 2.3.

**Der Vertrag, am laufenden Leser gemessen, nicht geraten.** `kernel.references` liest
`reference_for:` mit den Schlüsseln `roles` und `task_types` (`REFERENCE_KEY`, `ROLES_KEY`,
`TASK_TYPES_KEY`), Liste oder Ein-String-Schreibweise. Deklariert:

```
reference_for:
  roles: [product-editor, marketing-planner, report-writer, product-designer, project-manager, office-manager]
  task_types: [docs, ui, design, research, implementation]
```

Warum diese Rollen: die aus dem Auftrag (Office-Editor, Marketing-Planer, Report-Writer, Designer
für UI-Text) plus die beiden Kit-Leads für ihre Antworten an den Nutzer. Für die Leads gilt eine
Grenze, die in der Datei steht und hier noch einmal: ein Lead wird von der Verfassungsschleife nicht
dispatcht, also erreicht ihn die Ableitung in der Praxis nicht (der Kernel prüft die Rolle nicht —
B9, Abschnitt 8) — die Nennung ist Dokumentation, der Weg zu ihm ist sein eigener Text
(Naht E, Abschnitt 4). **Nicht deklariert:** die Korrespondenz-Fähigkeit aus FR-0033, weil es die
Rolle nicht gibt — der neue Test wird genau darauf rot (M1 in 2.2).

Warum diese Typen: welcher Wert des geschlossenen Vokabulars ein TEXT-Auftrag bekommt, entscheidet
der Lead beim Routen, und kein Office-/Research-Text legt einen fest (gegrept: `create-task`,
`--type`, `type:` in den drei Lead-Skills und beiden Verfassungen — keine Stelle). Also alle Typen,
unter denen ein Text-Deliverable ankommen kann; `implementation` ist dabei, weil nichts einen Lead
hindert, einen Copy-Auftrag so zu typen (und die Suiten selbst typen ihre Standard-TSK so,
`test_hooks_v2.TSK_FIELDS`). Nebenwirkung, benannt: `product-designer` × `implementation` trägt den
Skill mit; harmlos, weil der Header ein Zeiger ist und keine Ladung.

**Was drinsteht — Eigenschaften, keine Phrasenlisten.** Zehn gemessene Eigenschaften
(Satzlängen-Varianz, Gedankenstrich-/Doppelpunkt-Dichte, Abschwächer-Stapel, Diskursmarker,
Dreierregel + „nicht X, sondern Y", Schluss-Zusammenfassung, leere Intensivierer, elegante
Variation, Assistenten-Register, vorhersagbares Vokabular), je als Definition mit so vielen
Illustrationen, wie die Klasse braucht (Nacharbeit 1, Befund B2: der Satz „EINE Illustration" hielt
gegen die Zählung des Prüfers nicht — 56 quotierte Literale; die Datei sagt es jetzt so, wie ihr
Schlussabschnitt es schon sagte), Messung und Zug; dazu die deutsche Schicht G1–G7 (Nominalstil/Verbalstil, Anglizismen und Calques,
FEHLENDE Modalpartikel als deutsches Merkmal mit der Register-Bedingung — G3 ist EIGENE Ableitung, nicht aus den Quellen gelernt: jurigis führt kein Modalpartikel-Muster, marmbiz führt das Übermaß (`particle_count.max: 1`), nicht das Fehlen (Befund B7; die ausgelieferte Datei behauptet die Herkunft nicht) —, das Gedankenstrich-Glyph,
„kann" als absorbierendes Modal, Eröffner/Schließer, Anrede-Drift). Davor: wo die Stimme herkommt
(Office: das Content-Guidelines-Dokument aus dem *Read first* des eigenen Skills; Designer: Brief +
UI-Text-Tabelle der DSN; Report-Writer: Template + EXP; Lead: die Klartext-Regel der Verfassung), das
Verfahren messen → umschreiben → nachmessen ohne Dialog, und am Ende die Grenzen.

**Warum das Office-Dokument dort NICHT beim Dateinamen genannt wird:** die Datei ist in dev und
research gespiegelt, und `test_hooks.test_instruction_files_name_only_state_files_a_v2_project_has`
verurteilt jeden `.yaml`-Namen, den das jeweilige Kit nirgends ausliefert (PHANTOM-Regel). Der Zeiger
geht deshalb auf die Stelle, die den Namen trägt — das *Read first* des Rollen-Skills — statt auf
den Namen. Das ist zugleich SR-0008-konform (Ort statt Zitat).

**Quellen und Lizenzen, korrigiert gegen den Triage-Text.** Gelesen (roh): harshaneel/humanize
`humanize/SKILL.md` (MIT), Aboudjem/humanizer-skill `skills/humanizer/SKILL.md` (MIT),
jurigis/avoid-ai-writing-multilingual `SKILL-DE.md` + `sources/DE-sources.md` (MIT),
marmbiz/humanizer-de `README.md` + `NOTICE` (Code MIT, **Musterkatalog CC BY-SA 4.0**,
Wikipedia-abgeleitet — also nur Orientierung, wie die Wikipedia-Seite selbst). Drei Zuschreibungen des
Triage-Texts sind so nicht haltbar und stehen im Skill richtig:

| Triage sagt | gemessen |
|---|---|
| „Economist/McGill: GPT-4.1 at 3.28x human rate over 55,940 sentences" | **zwei Quellen**: 3,28× = Freeburg, zitiert im McGill-OSS-Artikel (Lia Erisson, 8. Mai 2026), GPT-4.1 in Standard-Essays; 55 940 Sätze / 1,2 M Wörter = The Economist (Aug. 2026, eigene Artikel gegen ChatGPT, Claude, Gemini, Grok) — dort liegt **nur Claude über** der menschlichen Gedankenstrich-Rate, ChatGPT deutlich darunter; längere Sätze, weniger Kommas/Semikola, kaum Klammern |
| „rule-of-three (Barrons count 50 → 200+)" | Barron's zählte **„it's not X, it's Y"**: 49 (2023) → 100 (2024) → 208 (2025) US-Unternehmensdokumente (berichtet April 2026) — die Dreierregel hat diese Zahl nicht |
| „Wikipedia CC BY-SA orientation only" | bleibt; zusätzlich gilt es für marmbiz' Katalog |

Gelesen über Sekundärquellen, benannt: der Economist-Text selbst ist bezahlschrankiert — gelesen über
den Daring-Fireball-Auszug (2026-08-11) und den Suchtreffer-Abriss; der Fast-Company-Abruf kam mit
403 zurück. Die Modell-Abhängigkeit der Gedankenstrich-Dichte ist damit selbst ein Argument der
Datei: darum Eigenschaft (Strich tut Komma-Arbeit) statt Verbot.

**„Kein Wortlaut übernommen" ist eine Aussage darüber, wie geschrieben wurde, nicht eine gemessene
Eigenschaft** — kein Test dieser Suite vergleicht die Datei mit den Quellen; die Kopfzeile der Datei
sagt das so. Der Verifier kann es stichprobenartig gegen die vier Roh-URLs prüfen.

### 1.2 `tools/test_shared_skill_contract.py` (neu, 5 Tests; der Erstdurchgang schrieb hier 6, gemessen 5 — Befund B6)

Zwei Fragen, die `test_reference_skills.py` nicht beantwortet, je als Eigenschaft über ALLE
Referenz-Skills (Definition: kein `skills:`-Frontmatter nennt sie — `_reference_skills`, importiert,
nicht kopiert):

* **totes Ende der Deklaration**: jede genannte Rolle wird von einem Kit ausgeliefert, das den Skill
  ausliefert (Vereinigung über die liefernden Kits, nicht „jedes Kit" — der Office-Editor ist nicht
  tot, weil dev ihn nicht hat); jeder Typ steht in `backlog_types.TASK_TYPES`. Der bestehende
  Erreichbarkeits-Test ist mit EINEM lebenden Paar je Kit zufrieden, hinter dem sich der tote Name
  versteckt — gemessen M1/M2.
* **Spiegel**: jede Datei eines Referenz-Skill-Verzeichnisses, das mehr als ein Kit ausliefert, ist
  byte-identisch, außer `KIT_SPECIFIC_SKILL_FILES` nennt den Grund (leer; beide Enden wie
  `test_hooks.KIT_SPECIFIC_HOOKS`). **Nur Referenz-Skills**, und das ist gemessen, nicht gewählt: über
  alle Skills gelesen meldete die Regel `project-auditor` (×3), `project-manager` (×2),
  `research-engineer` (×2) — Rollen-Skills, die per Konstruktion je Kit anders sind
  (`_round-scratch/TSK-0111/shared_skill_drift.py`).

Plus je ein Boden-Test, der die Leser über einen Probe-Baum bzw. eine Tabelle treibt (beide Enden
der Ausnahmekarte, Drift, Einzelkit).

### 1.3 Kleinigkeit in `tools/test_design_system_contract.py`

Der Docstring von `test_a_role_procedure_skill_is_never_mistaken_for_a_design_system` sagte „eleven
directories" — eine Zählung, die mit genau diesem Skill falsch wurde (zwölf). Ersetzt durch die
Ableitung („every skill directory the kit ships, role or reference"). Kein Verhalten geändert.

### 1.4 Das Vorher/Nachher-Paar für den Nutzer

`project_memory/staging/TSK-0111/humanizer-before-after.md`: ein erfundener, realistischer
Produkttext (Isolierflasche 750 ml), die „Vorher"-Fassung so gebaut, wie ein Modell schreibt
(Eröffner, Em-Dashes, Dreier, „nicht nur … sondern", Abschwächer, Nominalstil, neun Namen für ein
Produkt, Schluss-Frage, null Modalpartikel), die „Nachher"-Fassung mit dem Skill wie eine Rolle es
täte. **Die Zahlen und die Zusage dieses Absatzes sind abgelöst** — die Erstfassung behauptete hier
„Fakten und Reichweiten unverändert" (widerlegt, B4) und trug die Zählung der ersten
Nachher-Fassung (208 → 88 Wörter usw.); der gültige Stand ist die Tabelle in der Datei selbst,
gezählt in Abschnitt 8.1 (B4/B5) und Abschnitt 9 (N3/N4). Das Urteil über
den Klang ist des Nutzers; die Datei sagt ihm, was er entscheiden soll, und dass der eigentliche Test
an seinem echten Text läuft.

### 1.5 Stempel

`team-kits/{dev,office,research}-team/VERSION` → `2026.09.02-12` (provisorisch; zweimal gestempelt,
-11 nach dem ersten Stand, -12 nach drei Prosa-Korrekturen an der Datei, siehe 3).

---

## 2. Messungen

### 2.1 Die laufende Ableitung je Kit (`measure_contract.py`)

| Paar | dev | office | research |
|---|---|---|---|
| product-designer × ui | `[frontend-design, humanizer]` | `[humanizer]` | `[humanizer]` |
| product-designer × docs | `[humanizer]` | `[humanizer]` | `[humanizer]` |
| frontend-developer × ui | `[frontend-design, webapp-testing]` (unverändert) | `[]` | `[]` |
| frontend-developer × docs | `[]` (der bestehende Test `test_a_task_of_another_type_gets_a_different_order` bleibt wahr) | | |
| product-editor × docs / implementation | `[humanizer]` | `[humanizer]` | `[humanizer]` |
| report-writer × docs / research | `[humanizer]` | `[humanizer]` | `[humanizer]` |
| project-manager / office-manager × docs | `[humanizer]` | `[humanizer]` | `[humanizer]` |
| researcher × research | `[]` | `[]` | `[]` |

Der Satz im dev-PM-Skill „a task typed `docs` gets none of the design references a `ui` task gets"
bleibt wahr — `humanizer` ist keine Design-Referenz.

### 2.2 Rot zuerst (Kopie außerhalb des Repos, `red_first.py`, fünf Mutationen, je zurückgesetzt)

| # | wiederhergestellter Defekt | roter Test | Gegenprobe im selben Lauf |
|---|---|---|---|
| M1 | Rolle `correspondence` (kein Kit liefert sie) neben den lebenden, in allen drei Kopien | `test_shared_skill_contract.py::test_every_role_a_reference_skill_names_is_shipped_by_a_kit_that_ships_the_skill` **1 failed** | `test_reference_skills.py::test_every_shipped_reference_skill_can_be_named_by_some_task` **passed** (die Lücke, die der neue Test schließt); Spiegel-Test passed |
| M2 | Typ `copy` neben den lebenden | `::test_every_task_type_a_reference_skill_names_is_in_the_kernel_vocabulary` **1 failed** | Erreichbarkeits-Test **passed** |
| M3 | ein Byte Drift in der Office-Kopie (`—` → `--`) | `::test_a_skill_shipped_by_several_kits_is_one_file_in_all_of_them` **1 failed** | ganze `test_reference_skills.py` **18 passed** |
| M4 | Ausnahme-Eintrag `humanizer/SKILL.md` bei identischen Kopien | Spiegel-Test **1 failed** („every copy is identical — drop the exception") | — |
| M5 | `reference_for` in der Research-Kopie entfernt | `test_reference_skills.py` **2 failed, 16 passed** (der bestehende Kein-drittes-Kind-Test + Erreichbarkeit) und Spiegel-Test **failed** | — |

Baseline vor und nach allen Mutationen: 6 + 1 passed.

### 2.3 Auslieferung in Office und Research, echter Installer (nicht nur dev)

Der H83-Test fährt den Installer nur für dev. Eigene Messung mit demselben Zwillings-Rig
(`test_kitupdate._staging/_run_installer`, PowerShell-Zwilling, Wegwerf-HOME unter Scratch,
Template-Preset des jeweiligen Kits): office rc 0, `.claude/skills` = `[bookkeeper, filing-reviewer,
humanizer, office-manager, project-auditor, records-clerk]`, `.agents/skills` identisch; research
rc 0, `[humanizer, methodologist, project-auditor, project-manager, researcher, reviewer]`, Spiegel
identisch. `for_task` auf dem INSTALLIERTEN Baum: product-editor × docs → `[humanizer]`,
report-writer × docs → `[humanizer]`. Der Bash-Zwilling ist für office/research **nicht** gefahren
(der H83-Test deckt ihn für dev; die Schleife ist in beiden Zwillingen dieselbe kit-agnostische
Zeile — das ist ein Lese-Argument, keine Messung).

### 2.4 Suiten (im Worktree, DEC-0060 Regel 2: abgeleitet aus den Dateien, die geändert wurden, und
den Tests, die sie lesen)

Geändert: drei `SKILL.md` (gelesen von den Ehrlichkeits-Sweeps in `test_hooks`/`test_hooks_v2`,
von `test_kitupdate`, `test_presets`, `test_role_contracts`, `test_context_budget`,
`test_reference_skills`, `validate.py`), drei `VERSION` (Installer- und Hash-Tests), zwei
`tools/`-Dateien.

| Lauf | Ergebnis |
|---|---|
| `test_shared_skill_contract test_reference_skills test_context_budget test_role_contracts` | **92 passed** (6:26, parallel zu A/B) |
| `test_shortening_net test_disposition test_parity_sources` (DEC-0060 Regel 1, Pins/Ratschen) | **53 passed** (0:43) — keine Ratsche bewegt: der Skill liegt in keinem Lead-Paket |
| A: `test_kitupdate test_presets test_design_system_contract test_repo_hygiene test_backlog_types` | siehe 7 |
| B: `test_hooks test_hooks_v2` | siehe 7 |
| `ruff check .` · `validate.py` | grün |

**Nicht gefahren:** die volle Suite (Strom-Regel), `.claude/hooks/test_gates.py` (kein Gate
berührt).

---

## 3. Eigene Korrekturen, gefunden vor dem Prüfer

1. Der erste Schnitt des Spiegel-Tests las **alle** Skills und war rot auf drei Rollen-Skills, die per
   Konstruktion differieren — die Regel war eine Aufzählung im Gewand einer Eigenschaft. Jetzt: die
   Definition „Referenz-Skill" aus `test_reference_skills`, und die Messung steht im Docstring.
2. Ein Frontmatter-Kommentar behauptete eine Messung über fremde Texte („measured 2026-09-02: none
   names one") und zitierte die Suite („the default the office kit's own suite types a task with") —
   beides Behauptungen, die mit E's Änderungen rotten. Ersetzt durch die Eigenschaft (der Lead
   entscheidet den Typ beim Routen).
3. Drei Prosa-Stellen der Datei: „all four assume a dialogue" war für harshaneel ungenau (es fragt
   nichts, wird aber vom Nutzer mit Text aufgerufen) → „built for a user who pastes a text and answers
   for it"; „no sentence under eight words" trug eine Zahl ohne Quelle → „no short sentence at all";
   ein wörtliches Zitat aus dem Product-Editor-Skill → Zeiger auf dessen Text-Standard (E besitzt den
   Text).
4. Das McGill-Jahr: erst „2025" geraten, nachgemessen 8. Mai 2026.

---

## 4. Nahtstücke für Strom E (Rollen-/Verfassungstexte — E schreibt, ich liefere den Satz)

Jeder Satz nennt beide Abrufwege, weil der Routen-Leser (`_route_mentions`) die Codex-Form liest und
der Claude-Slash-Befehl allein ungedeckt wäre. Alle lösen heute auf (drei Kits liefern das
Verzeichnis).

| Datei | Stelle | Satz (verbatim, E darf ihn im Idiom der Datei kürzen) |
|---|---|---|
| `office-team/skills/product-editor/SKILL.md` | Abschnitt „The text standard", nach den zwei Selbsttests | Before a description goes into the envelope, open the `humanizer` reference on it (`/humanizer`; Codex reads `.agents/skills/humanizer/SKILL.md`) and run its measure–rewrite–re-measure pass: the voice stays the one the guidelines set, the skill only removes what reads as machine prose, and it touches no fact. Your work order names it when the task type is one it declares; it is not yours to own. |
| `office-team/skills/marketing-planner/SKILL.md` | Do 2 „Drafts" | Same sentence, on post and campaign drafts. |
| `research-team/skills/report-writer/SKILL.md` | Do 1, bei den Prosa-Platzhaltern (problem, methodology, conclusion, limitations) | For the prose placeholders open the `humanizer` reference (`/humanizer`; Codex `.agents/skills/humanizer/SKILL.md`); numbers, claims and the template stay untouched, and its German items G3/G5 are off in this register, as it says itself. |
| `dev-team/skills/product-designer/SKILL.md` | bei „The words are part of the contract" (UI-Text-Tabelle) | Run the `humanizer` reference over the sentences of the UI-text table (`/humanizer`; Codex `.agents/skills/humanizer/SKILL.md`); labels and controls stay with `frontend-design`'s UX-writing rules. Your `ui`/`design` order names both. |
| `dev-team/skills/project-manager/SKILL.md`, `research-team/skills/project-manager/SKILL.md`, `office-team/skills/office-manager/SKILL.md` | bei „speaks plain German to the user" / §8 Behavior | The craft half of this rule is the `humanizer` reference (`/humanizer`; Codex `.agents/skills/humanizer/SKILL.md`): open it on a reply longer than a few lines before you send it. No work order names it for you — you are never dispatched — so this sentence is the only route. |
| `office-team/constitution/AGENTS.md`, `research-team/constitution/AGENTS.md` | ein Absatz 1a wie in dev | Die Regel „eine Prozedur je Rolle, beliebig viele Referenzen" steht heute nur in dev; `test_a_role_declares_exactly_its_own_procedure_skill` nennt in seinem Docstring, dass die Erweiterung dem gehört, der den anderen Kits einen geteilten Skill gibt — das ist diese Runde, und die Verfassung ist E's. |
| Lead-Skills, ROUTE-Schritt (optional) | | Wenn E den Typ für Text-Aufträge festlegen will (`docs` liegt nahe), trägt der Skill ihn bereits. |

Was E **nicht** ändern muss: der DELEGATE-Satz im dev-PM-Skill (bleibt wahr, 2.1) und die
Frontmatter der Rollen (`skills:` bleibt 1:1 — sonst wird der Skill Eigentum und fällt aus der
Referenz-Definition).

---

## 5. Bewusst nicht geschlossen, benannt

* **Der Lead ist über die Ableitung nicht erreichbar.** `for_task` läuft in `create_lease`, und ein
  Lead hat keine Lease. Die Nennung im Frontmatter ist Dokumentation; der Weg ist E's Satz. Kein
  H-Eintrag: das ist eine Grenze des Zeiger-Mechanismus, den FR-0071 bewusst als „billige Hälfte"
  gewählt hat, keine Lücke mit Angriffskette.
* **Nichts misst, ob eine Rolle den Skill anwendet.** Pflicht ohne Gate, mit Absicht (DEC-0056: ein
  Prosa-Skill für einen Prosa-Fehler); die Spur ist die eine Envelope-Zeile, die das Verfahren
  verlangt. Der Test des FR bleibt der des Nutzers am echten Text.
* **~~Keine Lochnummer verbraucht (H120–H122).~~** — **abgelöst in §9.1:** H120 ist verbraucht (Eintrag
  in `docs/POST_V2_WISHLIST.md`), H121/H122 sind es nicht. Der Satz galt für den Erstdurchgang: die
  Löcherliste führt gemessene Lücken mit Kette, und die zwei Punkte oben sind Grenzen, keine Ketten.
* **Bash-Zwilling für office/research nicht gemessen** (2.3), und der Preset-Schnitt für
  office/research nicht über alle Presets — der H83-Test tut das für dev, und die Schleife ist
  dieselbe; parametrisieren über Kits hätte den Test verdreifacht (~2,5 min je Zwilling), und die
  Merge-Runde kann das billiger als jede Stream-Suite entscheiden.
* **`implementation` in den Typen** ist die breiteste Nennung; wenn E den Text-Typ festlegt, kann eine
  spätere Runde die Liste verengen. Beide Enden bleiben dann gemessen.
* **Die Property-Illustrationen enthalten deutsche Beispielwörter** („hochwertig", „Darüber hinaus" …).
  Das sind Illustrationen einer Definition, keine Verbotsliste — die Datei sagt das an zwei Stellen;
  ein Leser, der sie als Liste liest, hat sie falsch gelesen, und das ist nicht messbar.

---

## 6. Geänderte Dateien

> **Stand des Erstdurchgangs. Abgelöst — die gültige Liste steht in §10.3.**

Neu: `team-kits/dev-team/skills/humanizer/SKILL.md` ·
`team-kits/office-team/skills/humanizer/SKILL.md` ·
`team-kits/research-team/skills/humanizer/SKILL.md` · `tools/test_shared_skill_contract.py`.
Geändert: `tools/test_design_system_contract.py` (ein Docstring) · die drei `VERSION`.
Im Hauptrepo nur `project_memory/staging/TSK-0111/` (dieses Protokoll, das Paar).
**Nicht angefasst:** `NOTICES.md`, `team-kits/repo_kit_owned.txt`, `docs/**`, alle Rollen-,
Verfassungs- und Prozedur-Skill-Texte, Kernel, Hooks, Templates, Scaffold.

## 7. Läufe A und B, Ende

| Lauf | Ergebnis |
|---|---|
| A: `test_kitupdate test_presets test_design_system_contract test_repo_hygiene test_backlog_types` | **172 passed, 1 skipped** (22:39, parallel zu B) |
| B: `test_hooks test_hooks_v2` | **3031 passed, 13 skipped, 1 failed** (48:09, parallel zu A und zum Installer-Probelauf) — der eine: `test_hooks_v2.py::test_the_id_scan_is_linear_on_the_worst_legal_input`, ein Wanduhr-Verhältnis-Test über den Id-Scan des Memory-Hooks (`near > 5 * jitter`), nichts, was diese Runde berührt. Auf der ruhigen Maschine dreimal allein gefahren: **passed (46,9 s), failed (13,0 s), passed (11,2 s)** — ein Jitter-Test, der auch ohne Last nicht stabil ist. Nicht meiner (Hooks/Hygiene), hier benannt, nicht angefasst. |

**Ende:** 2026-09-02 12:30 · **Dauer: ~1 h 15 min** ab der ersten Uhrzeitlesung, ~1 h 25 min ab
Spawn (geschätzt) — davon ~50 min die beiden Hintergrund-Suiten, während derer Rot-zuerst,
Installer-Probe und Protokoll liefen.

**Zwei Beobachtungen außerhalb meines Bereichs, für den Lead:**

1. **Ein Test der Haken-Suite schreibt in das `project_memory/.audit/hook_events.jsonl` des
   Baums, in dem er läuft.** Nach Lauf B trug der Worktree eine neue Zeile (`12:05:34`,
   `gate_needs`, „the hook payload could not be read or parsed"); die identische Zeile von
   `10:29:36` steckt bereits in `6d18407`, die Merge-Runde hat sie also mit committet. Der Text kommt
   aus `dev-team/hooks/_kernel.py`; welcher Test den Haken mit unlesbarem Payload gegen die
   Repo-Wurzel statt gegen `tmp_path` fährt, habe ich nicht gesucht (Hooks und `project_memory/`
   sind außerhalb meines Scopes). **Der Patch schließt `project_memory/` aus** (`git diff HEAD --
   . ':!project_memory'`, 8 Dateien); die Zeile im Worktree bleibt stehen und wird NICHT
   zurückgesetzt — das ist die Entscheidung des Nutzers, nicht meine.
2. Der Jitter-Test oben.

**Übergabe (Stand Erstdurchgang, abgelöst durch §10.3):** `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0111\stream-humanizer.patch`
— damals 8 Dateien: drei `SKILL.md` (neu), `tools/test_shared_skill_contract.py` (neu),
`tools/test_design_system_contract.py`, drei `VERSION`.

---

## 8. Nacharbeit 1 — die neun Befunde des Prüfers (Fable), 2026-09-02

**Wer/wann:** zweiter Nacharbeits-Lauf; der erste war sofort nach dem Start gestoppt worden, und
`git status` im Worktree zeigte beim Übernehmen nichts über den Stand -12 hinaus (nur die
Hook-Nebenwirkung `project_memory/.audit/hook_events.jsonl`). Start ohne Uhrzeitlesung (aus den
Scratch-Zeitstempeln ~13:40 geschätzt), **Ende 14:19:50 gelesen** (14:07:42 vor der letzten Messung am gestempelten Klon), davon ~6 min Suite A und ~7 min der gestempelte Klon-Lauf im Hintergrund.
**Rot-zuerst-Klon:** `_round-scratch/TSK-0111/rework-red/` (Kopie des Worktrees per `robocopy`,
`.git` entfernt, damit nichts dort auf das echte Repo zeigt).

### 8.1 Je Befund

**B1 (blockierend, Instrument) — die Spiegelregel sah nur Dateien, die in ≥ 2 Kits liegen.**
`tools/test_shared_skill_contract.py`, Abschnitt 2, umgebaut:

* `_shipping_kits(kit_dirs)` → `{skill: {kit}}` aus `_reference_skills` je Kit: die Menge, gegen
  die jede Datei gehalten wird, kommt aus den **Verzeichnissen**, nicht aus den Dateien — eine Tabelle
  nur über Dateien kann eine Datei mit einem einzigen Eintrag nicht sehen, und genau das war der
  erste Schnitt (`if len(copies) < 2: continue`).
* `_assert_one_directory(by_path, shipping, exceptions)` (vorher `_assert_one_file`) prüft in dieser
  Reihenfolge **Präsenz** (`set(copies) == shipping[skill]`, Fehlermeldung „a shared skill is ONE
  directory in every kit that ships it") und dann **Inhalt**. Die Ausnahmekarte erlaubt einer Datei
  zu DIFFERIEREN, nie zu FEHLEN; der Kommentar an `KIT_SPECIFIC_SKILL_FILES` sagt das. (Der Satz,
  der hier stand — „wie bei `test_hooks.KIT_SPECIFIC_HOOKS`, wo jede genannte Datei in allen drei
  Kits liegt" — war falsch: `format_on_write.py` fehlt in office; N1/H120 in Abschnitt 9.)
  Beide Enden: ein Eintrag mit < 2 Kopien oder identischen Kopien ist tot und fällt (vorher fiel
  nur der identische Fall).
* **Eigener Fund beim Selbstangriff:** `glob("**/*")` überspringt Punkt-Dateien, `cp -R` im Installer
  liefert sie aus. Jetzt `os.walk` (mit `__pycache__`-Filter über `dirs[:]`); der Docstring von
  `_skill_files_by_path` nennt die Messung.
* Umbenannt, weil der Name die Regel trägt: `test_a_skill_shipped_by_several_kits_is_one_directory_in_all_of_them`,
  Boden-Test `test_the_mirror_rule_fails_on_a_drift_on_a_lone_file_and_on_an_idle_exception` (neue
  Fälle: einsame Datei mit und ohne Eintrag → rot; Eintrag auf einem Ein-Kit-Skill → rot). Zahl der
  Tests bleibt **5**. `import glob` entfernt (tot).

**Rot zuerst, im Klon, mit dem Instrument des Prüfers (V1 = `office-team/skills/humanizer/references/extra.md`):**

| Schritt | Ergebnis |
|---|---|
| alter Test (-12), Baum sauber | 5 passed |
| alter Test, V1 gepflanzt | **5 passed** — der Befund, reproduziert |
| neuer Test, V1 gepflanzt | **1 failed**: `AssertionError: skills/humanizer/references/extra.md exists in office-team, but humanizer is shipped by dev-team, office-team, research-team -- a shared skill is ONE directory in every kit that ships it …` |
| V1 entfernt | 5 passed |
| M3 (ein Byte Drift in der Office-Kopie), neuer Spiegel-Test | 1 failed (Inhalts-Hälfte hält weiter) |
| V2 = `office-team/skills/humanizer/.office-only`, `os.walk`-Schnitt | **1 failed** (`skills/humanizer/.office-only exists in office-team, but …`) |
| V2, glob-Schnitt MIT Präsenz-Prüfung (im Klon nachgebaut) | **1 passed** — blind, wie der Docstring sagt; V1 im selben Schnitt: 1 failed |
| V1 gepflanzt, Klon UNgestempelt, `test_reference_skills` | 2 failed, 16 passed — die beiden Installer-Zwillinge über den `VERSION`-Hash (jedes geänderte Byte), keine Spiegelregel |
| V1 gepflanzt, Klon GESTEMPELT (`bump_kit_version.py` im Klon), `test_reference_skills` | **18 passed** — die Lücke, die der Test schließt; derselbe Baum, neuer Spiegel-Test: 1 failed |
| zurückgesetzt (`ls -a`: nur `SKILL.md`; `VERSION` aus dem Worktree zurückkopiert, `--check` dreimal unchanged) | 5 passed |

**B4 (blockierend, das Paar) + B5 (Zähltabelle).** Nachher-Fassung neu geschrieben, faktentreu:
Getränke bleiben Getränke, der Arbeitstag ein ganzer, „nahezu jeden gängigen" bleibt, „12" bleibt
Ziffer, die Haltbarkeitsaussage steht mit EINEM Abschwächer statt zwei, die drei Einsatzorte
bleiben. Das Instrument `measure_pair.py` ist neu: **eine Regel je Zeile**, jede Regel eine benannte
Konstante (`HEDGE` inkl. „sollte", `EVALUATIVE` inkl. „zuverlässig"/„stilvoll", `PRODUCT_NAME` mit
gefaltetem Plural, `TRIPLET` mit je einem Vorwort je Glied, `ANGLICISM`, `LIGHT_VERB`, `PARTICLE`,
`MARKER`), plus eine Zeile `facts present`, die jede Zahl, jedes Attribut und jeden Referenten in
BEIDEN Texten zählt. Neue Zahlen (209/11 → 97/7 Wörter/Sätze): Satzlängen 21 22 25 20 24 16 20 19 15
16 11 → 5 13 25 13 17 8 16; Dreier-Folgen 7 → 0; Em-Dashes/Doppelpunkte 3/1 → 0/0; `HEDGE` 5 → 1;
`MARKER` 4 → 0; „nicht nur … sondern" 1 → 0; `TRIPLET` 4 → 1 (Büro/Sport/Reisen — es SIND drei);
`EVALUATIVE` 10 → 0; `PRODUCT_NAME` 9 → 2; `LIGHT_VERB` 3 → 0; `PARTICLE` 0 → 1; `ANGLICISM` 2 → 0;
Frage 1 → 0. Die Datei `humanizer-before-after.md` führt jetzt ausdrücklich, **was die Nachher-Fassung
anders sagt** (vier Punkte: „bis zu 750 ml" → „750 ml" als G5 mit der Katalog-Voraussetzung; der
Abschwächer-Stapel auf eins; die gestrichenen Eröffner/Schließer/Wertungen; der bleibende Dreier)
statt „jede Zahl unverändert" zu behaupten. `before.txt`/`after.txt` im Scratch nachgezogen; die
erste Nachher-Fassung liegt als `after-v1.txt` daneben (Beleg des Befunds).

**B2 (Hausregel 3, Datei).** `SKILL.md` Absatz vor Eigenschaft 1: „ONE illustration … 40–70 entries"
→ „a definition, a count and a move, with as many illustrations as the class needs and no more: the
count is the check, the examples are illustrations …" — die Fassung des Schlussabschnitts, der das
schon sagte. G2 geschärft: Definition (englisch unter der Oberfläche), der Test je Eintrag (der
Property-10-Test auf die Sprache gedreht: sagt es das Gewerbe/der Käufer auf Deutsch?), die
Abgrenzung (ein Fachwort wie „Display" ist Vokabular des Gegenstands, kein Tell); „robust" als
Illustration gestrichen — ein deutsches Wort, das in Eigenschaft 7 hingehört, wo es zählt. Das
Instrument des Prüfers (`v_literals.py`, auf den Worktree gedreht: `v_literals_wt.py`) zählt jetzt 57
Literale — die Datei behauptet dazu keine Zahl mehr.

**B3 (Hausregel 3, `tools/`).** `test_reference_skills.py`, Docstring von
`test_a_role_declares_exactly_its_own_procedure_skill`: „because only dev-team ships reference
skills … belongs to whoever gives them a shared skill" → alle drei Kits liefern jetzt einen
(`humanizer`, FR-0072), §1a steht nur in dev, die Verfassungen sind Strom E's Text, `TSK-0105` trägt
die Naht. Die Naht-Zeile in Abschnitt 4 (Verfassungen) zeigt weiter auf genau diesen Docstring.
Gesucht nach Gleichbedeutendem in `tools/**` und `docs/**` (`only dev-team ships|only dev-team's
constitution|only dev-team carries|dev-team alone ships|only dev ships`, dazu `reference skill` ×
`dev-team|only|dev kit|one kit`): **eine** weitere Stelle geprüft und belassen —
`test_reference_skills.py:693` „dev-team ships no reference skill — this test would be vacuous" ist
die Leere-Wache eines Tests, der den Installer nur für dev fährt, keine Aussage über die anderen
Kits. `docs/reviews/phase0-disposition.md` nennt §1a als dev-Eintrag (Chronik, wahr).

**B6.** §1.2: 6 → 5 Tests, in place korrigiert.

**B7.** §1.1: G3 als eigene Ableitung benannt (jurigis führt kein Modalpartikel-Muster, marmbiz das
Übermaß, nicht das Fehlen); die Datei behauptete die Herkunft nie — dort nichts geändert.

**B9.** Frontmatter-Kommentar: „a lead is not dispatched, so … the derivation never fires" → „a lead
is not dispatched by the constitution's loop, so in practice only its own text sends it here". Der
Kernel prüft nicht, ob eine Rolle ein Lead ist — die Grenze ist die der Verfassung.

**B8 — aufgehoben.** Der Opus-Prüfer der Nachprüfung hat den Befund zurückgenommen: der Kommentar in
`team-kits/scaffold_team.sh:718` ist datiert („Measured 2026-09-01") und war zu diesem Datum richtig;
`scaffold_team.ps1` trägt keinen solchen Kommentar. Kein Befund, nichts für die Merge-Runde.

### 8.2 Spiegel, Stempel, Läufe

* Drei `SKILL.md` byte-identisch: sha256 `47b12ef2cace4aba…6949a4`, 0 CRLF, 16 739 B (aus dev
  kopiert, dann Hashes verglichen).
* `python tools/bump_kit_version.py` → **2026.09.02-13** in allen drei Kits (provisorisch). Danach
  wurden nur noch `tools/`-Dateien geändert; `bump_kit_version.py --check` (read-only) meldet
  dreimal „unchanged" — die `tools/`-Änderungen bewegen den Kit-Hash nicht.
* `python -m ruff check tools/` grün · `python tools/validate.py` grün.
* Suite A (DEC-0050): `test_shared_skill_contract test_reference_skills test_design_system_contract
  test_gaplog test_repo_hygiene` → **59 passed** (6:01; Log `suite-rework1-A.log`). Vor dem Stempel
  war `test_reference_skills` zweimal rot am Installer-Hash („does not hash to the `content:` in its
  own VERSION") — der erwartete Zustand zwischen Änderung und Stempel, nach dem Stempel grün.
* Suite B: `test_hooks -k "skill or reference or mirror"` → **12 passed, 901 deselected**
  (`suite-rework1-B.log`).
* **Nicht gefahren:** die volle Suite (Strom-Regel), `.claude/hooks/test_gates.py` (kein Gate berührt).

### 8.3 Übergabe

`stream-humanizer.patch` NEU: 71 498 B (nach der Docstring-Präzisierung STAMPED, Tabelle in 8.1; `--check` danach dreimal unchanged), 9 Dateien (drei `SKILL.md`, drei `VERSION`,
`tools/test_shared_skill_contract.py`, `tools/test_reference_skills.py`,
`tools/test_design_system_contract.py`), `project_memory/` ausgeschlossen (`grep hook_events` → 0).
`git-status.txt` daneben. Im Hauptrepo nur `project_memory/staging/TSK-0111/` (Protokoll, Paar).

### 8.4 Bewusst nicht geschlossen, benannt

* ~~Eine Zeile in G2 ist 101 Zeichen lang~~ — **falsch gemessen** (`awk length` zählt Bytes, nicht
  Zeichen; N6): die einzige Zeile über 100 Zeichen war Zeile 44 (136, Quellen-/Lizenzkopf), G2 hielt
  99. In Nacharbeit 2 umgebrochen und in Zeichen nachgemessen (Abschnitt 9).
* **Die Präsenz-Hälfte kennt keine legitime Ein-Kit-Datei in einem geteilten Skill.** Gebaut mit
  Absicht (die Karte erlaubt Differenz, nicht Fehlen; Vorbild `KIT_SPECIFIC_HOOKS`); ein Kit, das eine
  solche Datei braucht, bekommt sie in alle Kopien oder eine neue, begründete Karte. Heute gibt es
  den Fall nicht.
* **H120–H122 weiter unbenutzt;** B1 war ein Instrumentenfehler, kein Loch mit Kette. Der
  Punkt-Datei-Fund ist dasselbe Instrument, dieselbe Runde.
* **Der Dreier „Büro/Sport/Reisen" bleibt** und wird als 1 gezählt — Fakt der Vorlage, nicht Reflex.
* **Naht-Sätze (Abschnitt 4) unverändert nicht geschrieben** — E's Text.
* **Das Urteil über das Paar** bleibt des Nutzers; die Datei sagt ihm jetzt, wo die Nachher-Fassung
  von der Vorlage abweicht, damit er es beurteilen kann statt es zu entdecken.

---

## 9. Nacharbeit 2 — die Nachprüfung (Opus): B4 wieder offen, N1–N6, H120/H121, 2026-09-02

**Muster, das der Prüfer benannt hat und das sich in dieser Runde noch zweimal wiederholt hätte:**
ein Fix bringt einen neuen Allsatz mit, den die Datei selbst bricht. Darum steht in 9.2 zu JEDER neu
geschriebenen Eigenschaftsbehauptung der Einzeiler, der sie misst — und zwei davon haben mich vor
der Übergabe selbst erwischt (N2-Erstfassung „otherwise a question": vier Blöcke ohne Frage;
„office liefert acht eigene Haken": elf). **Start** aus dem Zeitstempel des Prüfer-Instruments
(14:49) geschätzt, **Ende 15:30:15 gelesen**; darin ~10 min Suite A.

### 9.1 Je Befund

**N2 (blockierend, Kit-Datei).** `SKILL.md`: „a definition, a count and a move … the count is the
check" → „a definition, a check and a move … the check is a count where the property is countable
and otherwise the definition read against the text". Dieselbe Klasse an vier weiteren Stellen, die
der Prüfer nicht genannt hat und die ich beim Durchgang über every/all/never/only/each/„the check
is" gefunden habe: die Beschreibung („each with the measurement you take" → „the check you make"),
Verfahrensschritt 2 („each say what to count; write the counts down" → „what to check, mostly a
count; write the answers down"), Schritt 3/4 („each count that stands out", „when the counts moved"
→ check), Schlussabschnitt („the counts are the check" → „the checks decide, the examples
illustrate"). Zeile 44 (136 Zeichen, N6) umgebrochen. **Drei Stempel** für diese eine Datei, und
zwei davon sind mein Defekt: -14 mit zwei neuen Zeilen über 100 Zeichen (der Umbruch nur
verschoben), -15 nach dem `textwrap`-Umbruch beider Absätze, -16 nach der Korrektur des
„otherwise a question"-Satzes. Seit -15 läuft die Zeichenprüfung VOR dem Stempel im selben Skript
(`assert not over`). Endstand: sha256 `b2cd9c0c7fe5cf1f874a931b…`, 16 811 B, 0 CRLF, dreifach.

**N1 (blockierend, tools).** `_assert_one_directory`-Docstring: der Halbsatz „every file it names
exists in all three kits" ist weg; jetzt: die Karte hat die FORM von `KIT_SPECIFIC_HOOKS`, nicht
dessen Regel — die Haken-Regel hat keine Präsenz-Hälfte (`format_on_write.py` in dev und research,
nicht in office). **H120** in `docs/POST_V2_WISHLIST.md` (Tabellenzeile vor der
GESCHLOSSEN-Sammelzeile, Eintrag am Ende) mit Mechanismus, drei gemessenen Ketten und Urteil „kein
Loch mit Kette — von Nachbarn gedeckt, mit benannter Grenze". **Die Präsenz-Hälfte in `test_hooks`
NICHT gebaut**, mit Grund: die Haken-Mengen sind je Kit per Konstruktion verschieden (office elf
eigene Dateien, `comm` über die drei Verzeichnisse), eine Ausnahmekarte mit Fehlen-Grund wäre die
Aufzählung, aus der `test_shared_kit_files_identical` herausgeschrieben wurde; und Präsenz hat dort
eine eigene Autorität — die Registrierung —, deren beide Richtungen zwei bestehende Tests halten.
Der Docstring von `test_shared_kit_files_identical` nennt sie jetzt (`tools/test_hooks.py`, im
Scope). Die falsche Aussage im Protokoll §8.1 ist in place korrigiert (Klammersatz).

**H121 — als Mechanismus gebaut, keine Lochnummer verbraucht.** Grenze (1), „ein ganzes
Skill-Verzeichnis verschwindet aus einem Kit": neuer Test
`test_a_reference_skill_ships_in_every_kit_that_ships_a_role_it_names` mit Ableitung `_kits_owed`
(die Deklaration sagt über ihre Rollen, wo der Skill hingehört — jedes Kit, das eine genannte Rolle
liefert, schuldet das Verzeichnis). Grenze (2), Privatisierung über `agents/humanizer.md`: von
`test_reference_skills.test_every_shipped_skill_is_either_a_role_procedure_or_a_declared_reference`
gehalten, im Docstring des neuen Tests benannt, gemessen. `test_shared_skill_contract.py` hat jetzt
**6 Tests**; Boden-Fall für `_kits_owed` im Probe-Test.

**N3 / B4 (blockierend, Staging).** „Der Körper" → „Die Flasche" (Referent zurück); die
Abweichungsliste ist von vier auf **acht** gewachsen, Satz für Satz gegen die Vorlage: 750 ml (G5),
Haltbarkeits-Stapel, „kann halten" → „hält" (G5), Erlaubnis → Anweisung (Spülmaschine), Empfehlung →
Anweisung (Handwäsche), „absolut auslaufsicheres Handling" → „läuft nicht aus", die gestrichenen
Eröffner/Schließer/Wertungen inkl. „ideal für"/„perfekt für unterwegs"/„Nachhaltigkeit", der
bleibende Dreier. Die `HEDGE`-Zeile 5 → 1 ist jetzt auf alle vier entfernten Abschwächer
zurückgeführt. `after.txt` nachgezogen.

**N4.** „zehn Wortstämme" → elf (Regex gezählt: 11), Instrument-Label „(10-word regex)" → „(11 stems
in the regex)"; „Jede Zeile hat genau eine Regel" ist jetzt wahr, weil die zwei Doppelzeilen geteilt
sind (Wörter | Sätze; Em-Dashes | En-Dashes | Doppelpunkte) — 17 Zeilen statt 14.

**N5.** §1.1: Hash-Zeile als Erstdurchgang markiert, der Lead-Satz auf die B9-Fassung; §1.4:
„Fakten und Reichweiten unverändert" und die neun alten Zahlen ausdrücklich als abgelöst markiert
(die Datei selbst ist der gültige Stand), „acht Namen" → neun.

**N6.** §8.4-Punkt durchgestrichen und als Messfehler benannt (`awk length` zählt Bytes); Zeile 44
umgebrochen, in Zeichen nachgemessen (Python `len`, keine Zeile > 100).

**B8.** Aufgehoben, im Protokoll so benannt (datierter Kommentar, damals richtig; `.ps1` trägt
keinen).

### 9.2 Jede neue Eigenschaftsbehauptung, mit ihrem Einzeiler

| Behauptung (wo) | Messung | Ergebnis |
|---|---|---|
| ~~„the check is a count where the property is countable …"~~ — **abgelöst in §10.2** (M1: der Satz steht so nicht mehr in der Datei; „17/17 mit Definitionssatz" war ungemessen) | `verify2/m_countclaim.py` über den Worktree + Einzeiler (17 Blöcke: `*Move:*`, Definitionssatz nach dem Namen) | 9/17 Blöcke mit Zählverb (1–5, G1, G2, G4, G5), 8 ohne (6–10, G3, G6, G7); **17/17 mit Move, 17/17 mit Definitionssatz**. Die Erstfassung „otherwise a question" fiel hier: 8, 9, G3, G7 tragen keine Frage |
| keine Zeile > 100 Zeichen (SKILL.md, N6) | Python `len` je Zeile, vor dem Stempel | -14 wurde MIT (84, 103), (101, 123) gestempelt — die Prüfung lief erst danach (mein Fehler); der erste Umbruchversuch scheiterte am `assert` mit (85, 102), (101, 134) und wurde nicht geschrieben; -15/-16: keine Zeile > 100 |
| „`format_on_write.py` ships in dev and research and not in office, on purpose … which hooks a kit ships is decided by its registration" (test_hooks-Docstring, H120) | `ls` der drei `hooks/`; `grep -rl format_on_write team-kits/office-team/` | dev ✓ research ✓ office ✗; office: **(none)** — kein Agent, keine Verfassung, keine Registrierung nennt sie |
| „a registered name that is not shipped fails `test_every_registered_hook_script_is_shipped_by_its_kit`" | Klon: `dev-team/hooks/format_on_write.py` entfernt, vier Tests | **1 failed** (genau dieser), Spiegel-Test grün |
| „a shipped name nobody wrote a rule-home for fails `test_every_hook_documented_in_its_constitution`" | Klon: `office-team/hooks/extra_hook.py` gepflanzt | **1 failed** (genau dieser), Spiegel-Test grün; `test_hooks_v2 -k shipped` 17 passed |
| „Was KEIN Test hält: ausgeliefert + dokumentiert + nicht registriert" (H120-Grenze) | Klon: `extra_hook.py` + Namenszeile an die Office-Verfassung | vier Tests **4 passed**; `-k shipped` 16 passed + **1 failed = Größen-Ratsche** des Lead-Pakets (`test_the_shipped_lead_packages_are_within_their_own_record`, 50 113 > 50 052 B) — sieht die Zeile, nicht den Haken |
| „the office kit alone ships eleven no other kit has" (test_hooks-Docstring, H120) | `comm -23` über sortierte `ls` der drei Verzeichnisse | 11 Namen (`_bookings.py … record_filing_reading.py`); Erstfassung sagte acht |
| neuer Test rot bei verschwundener Kopie; Tote-Rollen-Test ebenfalls rot; Spiegel-Test grün (Docstring) | Klon: `office-team/skills/humanizer/` verschoben | neuer Test **1 failed** (`humanizer names roles that office-team ship, and office-team ship no skills/humanizer/ …`), Tote-Rollen-Test 1 failed, Spiegel-Test **1 passed** (die Lücke) |
| Privatisierung wird von `test_every_shipped_skill_is_either_a_role_procedure_or_a_declared_reference` gehalten, Spiegel-Test still (Docstring) | Klon: `office-team/agents/humanizer.md` mit `skills: [humanizer]` | Drittes-Kind-Test **1 failed**, Spiegel-Test 1 passed, neuer Test 1 passed; zurückgesetzt 6 passed |
| `_kits_owed` meldet ein zweites Kit, das die Rolle ohne den Skill liefert (Boden) | Probe-Test im Suite-Lauf | `["other-team", "probe-team"]`, grün |
| ~~„vollständig, Satz für Satz verglichen" (Paar)~~ — **abgelöst in §10.2** (N1a: 13 selbst gewählte Sonden messen keine Vollständigkeit) | `verify2/v_pair2.py` | beide Textblöcke identisch zu `before.txt`/`after.txt`; 13 Token-Sonden — jede Vorher-Sonde, die im Nachher fehlt, hat eine Nummer in der Liste (1–7); `Der Körper besteht` before=False after=False |
| „elf Wortstämme" (Paar, Instrument) | `v_pair2.py` zählt die Regex | 11 |
| Tabellenzeilen mit genau einer Regel (Paar) | Lesen der 17 Zeilen | keine Zeile mit zwei Zahlen aus zwei Regeln |

### 9.3 Läufe, Stempel, Übergabe

* `ruff check tools/` grün · `validate.py` grün · `bump_kit_version.py --check` nach den
  `tools/`-/`docs/`-Änderungen dreimal unchanged (Endstand **2026.09.02-16**).
* Suite A (`test_shared_skill_contract test_reference_skills test_design_system_contract test_gaplog
  test_repo_hygiene`): **60 passed** (10:14; `suite-rework2-A.log`) — `test_gaplog`/`test_repo_hygiene`
  lesen die Löcherliste mit H120 mit. Suite B (`test_hooks -k "skill or reference or mirror"`):
  **12 passed, 901 deselected** (`suite-rework2-B.log`). Einzeln: `test_shared_kit_files_identical`
  passed nach dem Docstring; `test_shared_skill_contract` 6 passed.
* **Nicht gefahren:** volle Suite (Strom-Regel), `test_gates.py` (kein Gate berührt), die
  `test_hooks_v2`-Registrierungstests im Worktree (nur im Klon als Messrig; sie lesen
  `hooks/`-Verzeichnisse, die nicht angefasst wurden).
* `stream-humanizer.patch` NEU: **83 568 B, 11 Dateien** (+ `docs/POST_V2_WISHLIST.md`,
  + `tools/test_hooks.py` gegenüber Nacharbeit 1), `project_memory/` ausgeschlossen (`grep
  hook_events` → 0); `git-status.txt` daneben. Im Hauptrepo nur `project_memory/staging/TSK-0111/`.

### 9.4 Bewusst nicht geschlossen, benannt

* **H120 bleibt als Eintrag mit Grenze**: ausgeliefert + dokumentiert + nicht registriert ist totes
  Gewicht, das kein Test meldet — gemessen, kein Durchsetzungsverlust.
* **H121/H122 unbenutzt**: Grenze (1) ist ein Test, Grenze (2) ein benannter Nachbartest.
* **Die Ableitung `_kits_owed` ist strenger als heute nötig**: ein Skill, der eine Rolle nennt, die
  nur ein Kit liefert, MUSS in diesem Kit liegen. Wer einen Referenz-Skill absichtlich in einem Kit
  weglässt, dessen Rolle er nennt, hat keinen Ausweg außer der Deklaration — das ist gewollt (die
  Deklaration ist die einzige Aussage über den Ort) und steht hier, weil es die erste Stelle ist,
  an der eine spätere Runde anstoßen wird.
* **Naht-Sätze (Abschnitt 4) weiterhin nicht geschrieben.** Das Urteil über das Paar bleibt beim
  Nutzer; die acht Punkte sind seine Lesehilfe, keine Rechtfertigung.

---

## 10. Nacharbeit 3 — die acht Befunde des dritten Prüfers (Opus), 2026-09-02

**Wer/wann:** dritter Nacharbeits-Lauf, Modellstufe **Opus** (DEC-0059; die Nacharbeiten 1 und 2
liefen auf Fable und brachten je eine neue Runde „Prosa behauptet mehr, als der Code baut").
Der Lauf wurde einmal vom **Sitzungslimit abgebrochen** — direkt nach dem Einlesen von Item und
Ist-Zustand — und nach dem Reset fortgesetzt. Vor der Fortsetzung `git status --porcelain` im
Worktree gegen `_round-scratch/TSK-0111/git-status.txt` gestellt: 12 Zeilen, zeilenweise identisch,
davon `project_memory/.audit/hook_events.jsonl` die nicht zu patchende.
**Arbeitsverzeichnis:** `_round-scratch/TSK-0111/rework3/` — Klon des Worktrees in `rework3/wt`,
Rot-zuerst-Kopie des Paar-Dokuments in `rework3/red/`. Sonst nichts außerhalb, nichts im Repo außer
`project_memory/staging/TSK-0111/`.

### 10.1 Je Befund

**B1 — der H120-Eintrag machte `test_gates.py` rot (blockierend).** Vier `tools/`-Testnamen standen
nackt in Backticks; `test_every_test_the_hole_list_names_is_one_that_exists` verlangt für eine nackte
`test_*`-Spanne einen Treffer im Syntaxbaum von `test_gates.py` selbst (eine Spanne mit Punkt liest
es als Dateinamen und überspringt sie). **Fix:** Modulpräfix an allen sieben Stellen des Eintrags (gezählt über den Eintragsbereich) —
`test_hooks_v2.test_every_registered_hook_script_is_shipped_by_its_kit`,
`test_hooks.test_shared_kit_files_identical` (3×),
`test_hooks.test_every_hook_documented_in_its_constitution`,
`test_hooks.test_every_hook_an_entry_gate_names_is_shipped_by_every_kit_in_that_blocks_scope`,
`test_hooks_v2.test_the_shipped_lead_packages_are_within_their_own_record` —, dazu die Spanne
`test_hooks_v2 -k shipped` → `tools/test_hooks_v2.py -k shipped` (sie verlor beim Whitespace-Abzug
ihre Leerzeichen und sah aus wie ein nackter Testname) und in der Tabellenzeile
`test_shared_skill_contract` → `tools/test_shared_skill_contract.py` (gemeint ist die Datei). Der
Gate-Test wurde **nicht** aufgeweicht.

*Rot zuerst, beide Läufe in der Kopie `rework3/wt` außerhalb des Repos, Auswahl
`-k "hole_list or every_tilde_subject or every_reference_to_a_measurement or every_cell or hole or measurement or reference"`:*

| Stand | Ergebnis |
|---|---|
| vorgefunden | **1 failed, 7 passed**, 481 deselected (445 s) — `test_every_test_the_hole_list_names_is_one_that_exists`, mit genau den vier Namen im Assertion-Text |
| nach dem Fix | **8 passed**, 481 deselected (193 s) |

**Auslöser-Lehre, für die nächste Runde:** `test_gates.py` läuft nicht erst, wenn ein Gate berührt
ist, sondern sobald eine Datei geändert ist, die es **liest** — die Löcherliste steht als
`HOLE_LIST` in `.claude/hooks/test_gates.py:4464`. Nacharbeit 2 hat den Lauf mit „kein Gate berührt"
weggelassen (§9.3) und genau deshalb den roten Stand ausgeliefert.

**B2 — die Abweichungsliste des Paar-Dokuments war zum dritten Mal unvollständig (blockierend).**
Ursache war die Form: der alte Punkt 7 zählte auf, was jemandem aufgefallen war. **Fix:** die Liste
ist jetzt eine **Zerlegung**. `humanizer-before-after.md` trägt eine Tabelle, die die Vorlage in 25
Abschnitte zerlegt und jedem gegenübersetzt, was im Nachher-Text an seiner Stelle steht; die Spalte
„Art" kennt genau drei Werte (`unverändert`, `Abweichung → n`, `gestrichen → n`) und verweist auf
15 nummerierte Punkte darunter. `devlist.py` (neben dem Dokument im Staging; Wegwerf-Instrument der
Runde, nicht Teil des Kits) liest Vorlage, Nachher-Fassung und Tabelle **aus demselben Dokument**
und rechnet nach.

*Messung nach dem Fix:* 25 Zeilen, 15 Punkte; 206 Wortmarken Vorlage / 97 Nachher; **111** Wörter
der Vorlage, die der Nachher-Text nicht führt; Topfverteilung `Abweichung 44 · gestrichen 64 ·
unverändert 3`; **0 ohne Zeile**. Mit dem Instrument des Prüfers gegengelesen: `verify3/p_devlist.py`
meldet für dieselben 111 Wörter jetzt **0×** „nicht in der Liste" (vorher fehlten dort u. a.
„robustem", „innovative", „einzigartige" — die drei, die der Prüfer namentlich nannte).

*Rot zuerst, `rework3/red_devlist.py` gegen eine Kopie des Dokuments außerhalb des Repos:*

| Mutation | rc | erste Meldung |
|---|---|---|
| Baseline (Kopie unverändert) | 0 | GRÜN |
| m1: ein Wort aus einer Vorlage-Zelle gelöscht („robustem") | **1** | Zelle steht so nicht mehr im Text + 42 Zeichen ohne Zelle |
| m2: eine ganze Tabellenzeile gelöscht (Zeile 21) | **1** | Nummern laufen nicht durch + 21 Zeichen ohne Zelle |
| m3: eine „Art", die keiner der drei Werte ist | **1** | „leicht geändert" ist keiner der drei Werte |
| m4: ein Punkt, den keine Zeile nennt | **1** | Punkt 16 nennt keine Zeile — toter Eintrag |
| m5: eine gestrichene Zeile bekommt einen Nachher-Text | **1** | Art und Nachher-Zelle passen nicht + 13 Zeichen ohne Zelle |
| zurückgesetzt | 0 | GRÜN |

Damit misst das Instrument **beide** Enden: die Zeile ohne Punkt und den Punkt ohne Zeile.

**M1 — SKILL.md behauptete eine Zählform, die 8 von 17 Blöcken haben.** Geändert: die Überschrift
`:96` „what to count, what the count means, what to do" → **„what to check, what the answer means,
what to do"**; `:84` „mostly a count" → **„often a count, otherwise the definition read against the
text"**; `:98–100` „the check is a count **where the property is countable** and otherwise …" →
**„for some of them the check is a count, for the rest it is the definition itself read against the
text"**. Damit ist die widerlegte Eigenschaft („countable") weg.

**Bewusst NICHT so gemacht, wie der Auftrag es vorschlug:** der Auftrag wollte an `:98–100` die
Ableitung mit Zahl („eight blocks name a count …, the other nine … — `p_skill.py`"). Zwei Gründe
sprechen dagegen: die Zahl wäre eine **zweite** Kopie einer Rundenmessung in einer ausgelieferten
Kit-Datei — sie rottet mit dem nächsten Block, und nichts fängt das —, und `p_skill.py` ist ein
Wegwerf-Instrument des Prüfers; ein Zeiger aus einer Kit-Datei darauf zeigt ins Leere. Die Zahl
steht deshalb in §10.2 und nur dort. Das ist eine bewusste Abweichung vom Auftragswortlaut und wird
als solche gemeldet.

**M2 — „eleven" im Docstring von `test_shared_kit_files_identical`.** Die wachsende Dateizahl ist
raus: „the office kit alone ships **a set of hooks** no other kit has (`comm` over the three
directories; **the count and the date it was taken are in that entry, not here**)". Die Zahl steht
jetzt an genau einer Stelle — im H120-Eintrag, und dort **mit Datum** („elf Dateien, gemessen am
2026-09-02 mit `comm` …"), das vorher fehlte.

**Zusatz, gleiche Klasse wie N3, im selben Docstring gefunden:** der Satz „PRESENCE is not this
rule's question: **a name only one kit ships is skipped, not judged** (`format_on_write.py` …)"
machte dieselbe falsche Gleichsetzung wie die Tabellenzeile — die Datei liegt in zwei Kits. Neu:
„it compares the copies of the kits that ship a name and **never asks whether a kit is MISSING
one**". Kein eigener Befund des Prüfers, aber derselbe Defekt eine Datei weiter.

**N1 — die zwei Zeilen der §9.2-Tabelle, deren Einzeiler nicht misst, was der Satz sagt.** Beide in
place als abgelöst markiert (durchgestrichen, mit Zeiger auf §10.2): (a) `v_pair2.py` mit 13 selbst
gewählten Sonden kann Vollständigkeit nicht messen — ersetzt durch `devlist.py`; (b) „17/17 mit
Definitionssatz" war ungemessen: `m_countclaim.py` zählt Zählverben und `*Move:*`, sonst nichts. Was
daran messbar ist, steht in §10.2; was nicht, steht dort als gelesen und nicht gemessen.

**N2 — drei abgelaufene Stellen des Protokolls.** Kopfzeile („Lochnummern: keine verwendet") und
§5-Punkt tragen jetzt die Ablösungsmarkierung mit Zeiger auf §9.1 (H120 ist verbraucht); §6
(„Geänderte Dateien", 8) und die Zeile „Übergabe, endgültig: 8 Dateien" in §7 sind als Stand des
Erstdurchgangs markiert und zeigen auf §10.3.

**N3 — die H120-Tabellenzeile setzte `len(copies) < 2` und `format_on_write.py` gleich.** Die Datei
liegt in **zwei** Kits, fällt also nicht in diesen Zweig. Neu sagt die Zeile den Mechanismus: die
Regel „fragt für einen Namen nur, ob die Kopien der liefernden Kits gleich sind — ob ein Kit ihn gar
nicht liefert, fragt keine ihrer beiden Schleifen". Der Absatz **Mechanismus** im Eintrag sagt jetzt
beide Hälften (der `len(copies) < 2`-Zweig **und** die Ausnahmeschleife fragen nicht nach Präsenz),
und **Der lebende Fall** ist ausdrücklich „die zweite Richtung, nicht die erste": zwei Kopien, auf
der Ausnahmeliste, und die beiden Kopien unterscheiden sich wirklich — sonst meldete die
Ausnahmeschleife die Ausnahme als überflüssig (gemessen: sha256 `4a8f63d5…` dev vs `ac141083…`
research).

**N4 — Item-Defekt (`user/` ist verbotener Bereich).** Kein Fix im Code. Das Paar-Dokument sagt in
`:3–7` unverändert, dass der Umsetzer den Text **erfunden** hat, damit der Live-Shop nicht gelesen
werden musste, und wie die eigentliche Probe am echten Text liefe. Es behauptet an keiner Stelle,
die Kopie des Nutzers zu sein.

### 10.2 Jede neue Behauptung dieser Nacharbeit, mit ihrem Einzeiler

| Behauptung (wo) | Messung | Ergebnis |
|---|---|---|
| „jedes Wort der Vorlage steht in genau einer Tabellenzeile; kein Wort in der Tabelle, das in keinem der beiden Texte steht" (Paar-Dokument) | `project_memory/staging/TSK-0111/devlist.py` — Deckung beider Volltexte durch die Zellen, überschneidungsfrei, aus demselben Dokument gelesen | 25 Zeilen / 15 Punkte; 111 fehlende Wörter, **0 ohne Zeile**; Töpfe `Abweichung 44 · gestrichen 64 · unverändert 3`; rc 0 |
| dasselbe, gegen das Instrument des Prüfers | `verify3/p_devlist.py` | **0** der 111 Wörter mit „nicht in der Liste" |
| „`devlist.py` wird rot, sobald ein Wort fehlt" (Paar-Dokument) | `rework3/red_devlist.py`, fünf Mutationen an einer Kopie außerhalb des Repos | 5× rc 1, Baseline und Rücksetzung rc 0 (Tabelle in §10.1) |
| „jeder Verweis löst auf, kein Punkt ohne Zeile" (Paar-Dokument) | dieselbe Kopie, m3/m4 | beide Richtungen rot |
| „often a count, otherwise the definition read against the text" (SKILL.md `:84`, `:98–100`) | `verify3/p_skill.py`, geparst: Block für Block der Teil vor `*Move:*` | **8 von 17** Blöcken nennen eine Zählung als Prüfung (1–5, G1, G2, G5); 17/17 tragen ein `*Move:*` |
| dass die **anderen neun** „die Definition gegen den Text lesen" | `rework3/m_check_shape.py` (Kriterium im Docstring: Zählsatz vs. Lese-Imperativ am Satzanfang) | **nicht bestätigt**: 8 nennen einen Zählsatz, 1 einen Lese-Imperativ, 8 nennen keins von beiden. Deshalb steht in der Datei **nicht** „jeder Block sagt, welche der beiden es ist"; der Satz beschreibt die zwei Prüfformen, er behauptet nicht, jeder Block benenne seine |
| „17/17 mit Definitionssatz" (§9.2, alt) | — | **ungemessen**: `m_countclaim.py` zählt Zählverben und `*Move:*`. Messbar ist `*Move:*` (17/17); dass die Prosa davor eine DEFINITION ist, ist gelesen, nicht gemessen, und steht hier als solches |
| „`format_on_write.py` liegt in zwei Kits, die Kopien unterscheiden sich wirklich" (H120, neu) | `sha256sum` der beiden Dateien | `4a8f63d5…` (dev) ≠ `ac141083…` (research); office hat sie nicht |
| „der Docstring nennt die Zahl nicht mehr, der Eintrag nennt sie mit Datum" (M2) | Lesen beider Stellen nach der Änderung | Docstring: keine Zahl; Eintrag: „elf Dateien, gemessen am 2026-09-02 mit `comm`" |
| „keine nackte `test_*`-Spanne mehr im H120-Eintrag" (B1) | `rework3/p_spans.py` — dieselben Helfer wie der Gate-Test (`_hole_entries(_hole_section())`), Spannen ausgedruckt | vorher 33 Spannen, **4 nackt**; nachher 34 Spannen, **0 nackt** |
| SKILL.md: byte-identisch ×3, keine Zeile > 100 Zeichen, 0 CR | `sha256sum`; Python `len` je Zeile | 3× `3b1efc2c…`, längste Zeile **100**, CR **0** |

### 10.3 Läufe, Stempel, Übergabe (gültiger Stand)

* **Stempel:** `python tools/bump_kit_version.py` → **2026.09.02-17** in allen drei Kits;
  `--check` danach dreimal *unchanged*.
* `python -m ruff check .` **All checks passed** · `python tools/validate.py` **all structural
  checks passed**.
* **Gate-Tests** (Kopie außerhalb des Repos, Auswahl der Löcherliste): **8 passed** — der Lauf, den
  Nacharbeit 2 ausgelassen hat.
* **Suite A:** `test_shared_skill_contract test_reference_skills test_design_system_contract
  test_repo_hygiene` **50 passed** (4:24) · `test_gaplog` **10 passed** · zusammen die 60 der
  Vorrunde. **Suite B:** `test_hooks -k "skill or reference or mirror"` **12 passed, 901
  deselected**.
* **Volle Suite nicht gefahren** (DEC-0050): diese Nacharbeit berührt drei `SKILL.md`,
  `docs/POST_V2_WISHLIST.md`, EINEN Docstring in `tools/test_hooks.py` (an zwei Stellen) und
  drei `VERSION` — Textflächen und ein Stempel, keine Codepfade.
* **Geänderte Dateien, gültig: 11** — `docs/POST_V2_WISHLIST.md`, drei `SKILL.md` (neu), drei
  `VERSION`, `tools/test_shared_skill_contract.py` (neu), `tools/test_design_system_contract.py`,
  `tools/test_hooks.py`, `tools/test_reference_skills.py`. Im Hauptrepo nur
  `project_memory/staging/TSK-0111/` (Protokoll, Paar-Dokument, `devlist.py`).
* **Übergabe:** `_round-scratch/TSK-0111/stream-humanizer.patch` neu erzeugt
  (`git add -N` für die neuen Dateien, dann `git diff HEAD -- docs team-kits tools`),
  `git-status.txt` daneben. `project_memory/.audit/hook_events.jsonl` ist **nicht** im Patch.

### 10.4 Bewusst nicht geschlossen, benannt

* **Der Gate-Test liest einen Eintrag mit Code-Zaun falsch — seit Nacharbeit 4 als `H121`
  GESCHRIEBEN**, nicht mehr als Rest geführt (§11). Der dritte Zustand „bekannt, kommt später"
  existiert in diesem Repo nicht: gemessen und offen gehört in die Löcherliste. Tabellenzeile und
  Eintrag stehen in `docs/POST_V2_WISHLIST.md` mit Mechanismus, Kette, Umfang, lebender Instanz
  (H46) und der Schreibregel als Begrenzung.
* **`p_skill.py` druckt Zeile 84 weiterhin** in seiner Liste „sentences that still frame the check
  as a count" — sein Muster `each say what to` trifft jede Formulierung dieses Satzes, nicht nur die
  alte. Die Zeile sagt jetzt beide Prüfformen. Ich habe den Satz **nicht** umformuliert, nur damit
  das Instrument still ist; das wäre Anpassen des Textes an die Messung.
* **Die Präsenz-Hälfte der Haken-Spiegelregel bleibt ungebaut** (H120, unverändert): ausgeliefert +
  dokumentiert + nicht registriert ist totes Gewicht, das kein Test meldet.
* **Der Vorher-Stand von B2 ist nicht nachgemessen.** Das alte Paar-Dokument wurde beim Fix
  überschrieben; gemessen ist nur der Nachher-Stand (0 von 111 ohne Zeile). Für den Vorher-Stand
  gilt der Befund des Prüfers mit seinen drei namentlichen Wörtern.
* **Zwei Beobachtungen des Prüfers, außerhalb meines Bereichs, hier als Reste:** (1) eine
  Haken-Datei, die **außerhalb** des Repos gestartet wird, passiert Gate 1 mit rc 0 — die
  H80-Ableitung greift auf Kopien nicht; (2) die 29 Registrierungen eines gescaffoldeten
  Office-Projekts tragen **kein `timeout`-Feld** (Kit-Seite, `FR-0057`).
* **Das Urteil über das Paar bleibt beim Nutzer.** Die Tabelle und die 15 Punkte sind seine
  Lesehilfe, keine Rechtfertigung; `devlist.py` sagt nur, dass nichts fehlt — nicht, dass die
  Nachher-Fassung gut ist.

---

## 11. Nacharbeit 4 — ein Befund und eine Kürzung, 2026-09-02

Nachprüfung 4 (Opus, 38 min) hat alle acht Befunde der Nacharbeit 3 als geschlossen gemessen, keinen
neuen Prosa-Befund gefunden und **einen** Punkt beanstandet.

### 11.1 M-neu — die Zaun-Blindheit gehört in die Löcherliste, nicht ins Protokoll

`round-protocol.md` führte sie als „Rest für die Merge-Runde". Diesen dritten Zustand gibt es in
diesem Repo nicht (CLAUDE.md: gemessen und offen → Löcherliste). **Geschrieben als `H121`** —
Tabellenzeile neben H120 und Eintrag am Ende von `docs/POST_V2_WISHLIST.md`, mit Mechanismus (die
Drei-Backtick-Paarung, beide Zaun-Hälften), gemessener Kette, Umfang mit Datum, lebender Instanz,
Herkunft und `**Urteil: …**`-Spanne samt Begrenzung. **Der Eintrag selbst trägt keinen Code-Zaun**,
damit seine eigenen Zitate gelesen werden; alle Testnamen darin sind mit Modulpräfix geschrieben.

*Kette, in meiner eigenen Kopie nachgefahren* (`rework4/fencechain.py` gegen `rework4/wt`, derselbe
Geist-Name `test_a_name_no_file_in_this_repo_defines` zweimal in H120 gepflanzt, gefahren nur
`test_gates.test_every_test_the_hole_list_names_is_one_that_exists`):

| Fall | Ergebnis |
|---|---|
| Baseline | rc 0 — 1 passed |
| (a) VOR dem Zaun | **rc 1 — 1 failed** |
| (b) HINTER dem Zaun | **rc 0 — 1 passed** |
| (c) eines meiner eigenen Präfixe hinter dem Zaun wieder nackt geschrieben | **rc 0 — 1 passed** |
| zurückgesetzt | rc 0 — 1 passed |

*Umfang* (`rework4/p_fence.py`, über `test_gates._hole_entries`, nicht über eine Textsuche):
**10 von 97** Einträgen tragen einen Zaun (H46, H47, H48, H65, H92, H93, H94, H95, H99, H120),
gezählt vor H121; mit H121 sind es 10 von 98, weil er keinen trägt. In genau einem davon steht
hinter dem Zaun ein nackter Name: H46 nennt
`test_hooks_v2.test_a_descriptor_duplication_is_a_redirect_but_a_file_after_gt_amp_is_a_write`
(dort ohne Präfix), definiert in `tools/test_hooks_v2.py:6840`.

*Die eigene Betroffenheit*: von den sieben Präfixen, die Nacharbeit 3 in H120 geschrieben hat,
liegen **vier vor** und **drei hinter** dem Zaun; nur die vier hält der Draht — Fall (c) oben.

*H46 nicht angefasst.* Es ist die lebende Instanz, die der Eintrag benennt; der Eintrag sagt
stattdessen, dass ein Fix des Lesers das Präfix in H46 im selben Zug mitschreiben muss, sonst
schlägt die Reparatur dort als falsches Rot auf.

### 11.2 N-neu — das Paar-Dokument erklärt dem Nutzer keine Prüf-Semantik mehr

`humanizer-before-after.md` erklärte neun Zeilen lang die Deckungssemantik von `devlist.py`. Das ist
die Zusicherung an den Prüfer, nicht die Lesehilfe des Nutzers. Jetzt drei Zeilen: dass das Skript
daneben nachrechnet, dass es nicht zum Kit gehört, und dass das Urteil in der Spalte „Art" seines
ist. Der Rest steht unverändert im Docstring von `devlist.py`. Tabelle (25 Zeilen) und Punkte (15)
sind **nicht** angefasst.

### 11.3 Läufe, Stempel, Übergabe

* Löcherlisten-Auswahl der Gate-Tests in der Kopie `rework4/wt`
  (`-k "hole_list or every_tilde_subject or every_reference_to_a_measurement or every_cell or hole or measurement or reference"`):
  **8 passed**. Format-Test `test_gates.test_the_hole_list_judges_every_entry_it_carries` einzeln:
  **1 passed**.
* `devlist.py` gegen das gekürzte Dokument: **rc 0**, weiterhin 0 Wörter ohne Zeile.
* **Kein Stempel.** Diese Nacharbeit berührt nur `docs/POST_V2_WISHLIST.md` und das Staging; keine
  Kit-Datei ist geändert, also bleiben die drei `VERSION` auf **2026.09.02-17**
  (`bump_kit_version.py --check`: dreimal *unchanged*).
* Patch und `git-status.txt` neu erzeugt; `hook_events` kommt im Patch **0×** vor.
