# TSK-0079 — Board v2: Karten-Popup, echte Tabs, zwei hierarchische Backlog-Ansichten

Item: `project_memory/tasks/active/TSK-0079.yaml` (aus `inbox/active/FR-0053.yaml`).
Basis: HEAD `5ee0f26`, Stempel dev `2026.08.21-6` / office `-7` / research `-6`.
Umsetzer-Runde, ein Schreiber. Scratch ausschließlich unter
`C:/Offline Repos/v2-testbed/_round-scratch/TSK-0079/`.

Alle Zahlen unten sind gemessen, jede an genau einer Stelle. Was **nicht** gemessen wurde, steht in
§8 („Reste“), nicht zwischen den Zeilen.

---

## 1 Was gebaut wurde, und wo

| Datei | Was |
|---|---|
| `team-kits/kernel/backlog_tree.py` (neu, 277 Z.) | Die Ableitung der beiden Bäume. Kein HTML. `ROOT_TYPES`, die Kuratierung `VIEWS`, `parents_of`, `arrange`, die fünf Ablehnungsgründe + ihre Meldungen |
| `team-kits/kernel/board.py` (395 → 749 Z.) | Tabs, Modal, Baum-Rendering, Referenz-Buttons, Archivzählung, `_SCRIPT`, `_NOSCRIPT_STYLE` |
| `tools/test_board.py` (21 → 45 Fälle) | 19 Testfunktionen → 37 (45 Fälle, drei davon parametrisiert); der Parser liest jetzt Tabs, Views, Nodes, Gruppen, Details, Referenzen, jedes Element **und** jedes Attribut der Seite |
| `team-kits/{dev,office,research}-team/templates/project_memory/README.md` | Der Board-Absatz beschrieb „the card's fold carrying the item's own fields“ — die Klappkarte gibt es nicht mehr. Neuer Absatz: drei Ansichten, Klick öffnet den Datensatz, Unassigned, Verhalten ohne JavaScript |

Kernel-Dateien sind **nicht** gespiegelt (`team-kits/kernel/` existiert einmal); die Spiegelregel
in `tools/test_hooks.py` deckt `hooks/` und `templates/repo/scripts/` ab — beides unberührt. Die
drei READMEs sind kit-eigene Dateien (sie unterscheiden sich schon vorher zeilenweise); der geänderte
Absatz ist in allen dreien byte-gleich eingesetzt.

`git add team-kits/kernel/backlog_tree.py` war nötig: `tools/validate.py` meldete
„is hashed into a kit VERSION but not git-tracked“. Kein Commit, kein Push.

---

## 2 Entwurf (STEP 1) — die drei Entscheidungen und ihre Begründung

### 2.1 Tabs: der Zustand steht im DOM, nicht im Skript

Die aktive Ansicht ist das Fehlen von `hidden` an genau einem `<div class="view" data-view=…>`.
Das ist die Fassung, die der Browser **ohne CSS und ohne Skript** liest (UA-Regel
`[hidden] { display: none }`), und die ein Test ohne Browser lesen kann. Das Skript verschiebt nur
dieses Attribut; es entscheidet den Anfangszustand nicht — sonst zeigte die Datei für einen Moment
drei gestapelte Ansichten.

Tabs sind `<button>`, keine Anker: `test_the_page_shows_one_view_and_the_other_two_are_hidden_in_the_dom`
misst das (`{tag for …} == {"button"}`), weil „kein Anker-Scrollen“ genau das ist, was FR-0053/2
verlangt.

### 2.2 Modal: fertiges Markup, kein eingebettetes Datenpaket

Jedes Item wird **einmal** als `<article class="detail" data-detail="…" hidden>` gerendert, alle
zusammen im Overlay am Seitenende. Karten und Baumzeilen sind Knöpfe mit `data-open="<id>"`.

Damit gibt es **keine** eingebetteten Item-Daten und keine zweite Escaping-Schicht (JS-String, JSON,
Attribut-in-JS). `_SCRIPT` ist eine Konstante ohne jede Interpolation — ein `</script>` in einem
Titel ist damit *unmöglich* statt *escaped*. Gemessen als Eigenschaft, nicht als Absicht:
`test_the_page_script_carries_no_item_content_at_all` rendert zwei Stores ohne Gemeinsamkeit und
verlangt byte-gleiche Skripte.

Verlinkte Items: **jede** Zeichenkette in einem Feldwert, die wie eine Id aussieht und für die dieses
Board ein Item hat, wird ein Knopf (`_linked`). Keine Feldliste — `dependencies`, `acceptance_refs`
und Fließtext verhalten sich gleich, und ein Feld, das morgen Referenzen trägt, verlinkt am selben Tag.
Die Reihenfolge ist das Sicherheitsargument: **erst escapen, dann verlinken**. Das Muster
(`[A-Z]{2,4}-\d{4,}`) trifft nur Zeichen, die `html.escape` weder erzeugt noch verbraucht, also kann
ein Treffer nie Teil einer Escape-Sequenz sein und die eingesetzte Id kein Anführungszeichen
enthalten.

### 2.3 Bäume: nur echte Felder, und der **tiefste** auflösbare Elternteil

Kandidaten eines Items sind ausschließlich die Ids aus `backlog_types.PARENT_FIELDS` (dort aus
**beiden** Feldverträgen abgeleitet) — `TSK.derives_from` + `TSK.product_requirement`,
`BUG.related_pr`, `CR.target_pr`, `FR.related_pr`, `SR.derives_from`.

Ein `TSK` nennt **zwei** echte Eltern. „Der erste, der auflöst“ ist deshalb keine Regel, sondern ein
Münzwurf, der immer auf der Wurzel landet — der Systembaum wäre für immer zwei Ebenen tief. Regel:
der **tiefste** bereits platzierte Kandidat. Das braucht zwei Durchgänge (Tiefe ist erst bekannt,
wenn der Elternteil steht): der strenge platziert nur Kinder, von deren Kandidaten keiner mehr
aussteht; findet er nichts, ist der Zustand ein Zyklus, und der lockere platziert, was irgendeinen
gesetzten Kandidaten hat; findet auch der nichts, endet die Schleife. **Jede Runde setzt mindestens
ein Item oder beendet die Schleife** — das ist der Grund, warum `derives_from: <eigene id>` eine
Warnung kostet und keinen Hänger (§6, M14).

Kuratierung (welcher Typ in welcher Ansicht) ist **nicht** ableitbar — es gibt im Kernel keine
Eigenschaft „Kundensprache“. Sie steht deshalb einmal in `backlog_tree.VIEWS`, mit einem Stolperdraht,
der **beide** Enden misst
(`test_every_type_that_moves_through_a_lifecycle_is_placed_by_a_backlog_view`): ein genannter Typ,
den der Kernel nicht hat, ist ein toter Eintrag; ein Typ **mit Automat**, den keine Ansicht zeigt, ist
ein Eintrag, den jemand schuldet. Wurzeln sind dagegen abgeleitet:
`ROOT_TYPES = frozenset(ROOT_TYPE_BY_KIT.values()) | {"PROC"}` — PR/RQ aus der Kit-Karte, PROC als
eine benannte Ausnahme mit ihrem Grund (das Office-Kit sät kein Wurzel-Item und wird von seinen
Prozeduren geführt).

### 2.4 Unassigned: fünf Gründe, nicht fünf Schreibweisen für „kein Elternteil“

| Grund (`data-warning`) | Wann | Warum eigener Grund |
|---|---|---|
| `unassigned-missing-link` | Item nennt nichts, **obwohl** sein Vertrag das Bindungsfeld verlangt (`TSK`) | Vertragsbruch — reparierbar |
| `unassigned-no-link` | Item nennt nichts, und sein Vertrag **erlaubt** das (`FR.related_pr`, Spec II.2) | kein Defekt, sondern untriagiert |
| `unassigned-off-view` | nennt ein Item, das **auf diesem Board** steht, aber diese Ansicht nicht zeigt | falscher Ast, nicht falsche Id |
| `unassigned-unknown-link` | nennt eine Id, die kein aktives Item trägt (archiviert, Tippfehler) | Zeiger ins Leere |
| `unassigned-unreadable` | die Datei ist nicht parsbar | gehört trotzdem in die Ansicht |

Welcher Fall gilt, wird am **Vertrag** des Typs abgelesen (`DECLARED_REQUIRED_FIELDS ∩
PARENT_FIELDS`), nicht geraten. Beide Enden der Liste sind gemessen:
`test_every_reason_a_tree_can_refuse_an_item_is_one_a_store_can_produce` verlangt, dass zu jeder
Meldung ein Store existiert, der sie erzeugt, und umgekehrt.

### 2.5 Archivzahlen

Die Tab-Leiste trägt `archived, not on this board: N (TYP n, …)`. Gezählt wird, was
`state.archive_path` schreibt: `archive/<TYPE>/<year>/<ID>.yaml`, Stamm muss als Id **dieses** Typs
parsen. Nur diese Teilbäume werden gelesen — `staging.clear_staging` legt ganze Staging-Verzeichnisse
nach `archive/staging/`, dort läuft dieser Walk nie hinein.

---

## 3 Die Seite auf dem echten Store dieses Repos (208 Items)

Gemessen mit `_round-scratch/TSK-0079/measure_baseline.py` auf einer **Kopie** von
`project_memory/` (Gate 1 verbietet jeden Werkzeug-Schreibzugriff auf den kanonischen Baum):

| | vorher (HEAD 5ee0f26) | nachher |
|---|---|---|
| `generated/board.html` | 334 027 B | **465 398 B** (+39 %) |
| `generate_index()` gesamt (Index + Board) | 0,57 s | **0,49 / 0,52 / 0,54 / 0,55 s** (vier Läufe) |

Inhalt der Seite (`inspect_page.py`, aus dem gerenderten DOM):

```
views   board=sichtbar, product=hidden, system=hidden
tabs    Board 208 | Product backlog 47 | System backlog 68
archiv  91  (BUG 2, DEC 1, FR 10, SR 1, TSK 77)
208 Detail-Datensätze, 208 Karten, 115 Baumknoten, 353 Referenz-Knöpfe
Produkt: 3 PR als Wurzel, 11 FR darunter, 33 FR unter Unassigned (Grund: no-link)
System : 3 PR, 8 SR, 55 BUG, 2 TSK; Tiefe 0/1/2 = 3/64/1; Unassigned leer
```

Der eine Knoten auf Tiefe 2 ist ein TSK unter seiner SR; das zweite TSK (TSK-0079 selbst) hängt auf
Tiefe 1 unter PR-0002, weil sein `derives_from` auf FR-0053 zeigt — ein Item, das der Systembaum
nicht zeigt — und `product_requirement` der tiefste **auflösbare** Kandidat ist. Genau der Fall, den
die Regel aus §2.3 beschreibt.

**Keine mechanische Wand bei 199+ Karten.** Die im Auftrag befürchtete Grenze („modal-in-one-file
size limits“) tritt nicht ein: die Datensätze ersetzen die alten Klappkarten, sie kommen nicht dazu;
der Zuwachs von 131 kB sind Baumknoten, Referenz-Knöpfe und die Tab-Leiste. Keine Gabelung zu melden.

---

## 4 Browser-Messung: was die Suite nicht misst

Kein Browser läuft in `pytest`. Der Klick selbst ist deshalb **hier** gemessen, einmal, mit einem
echten Chromium auf der ausgelieferten Seite dieses Repos (208 Items):

Headless Chrome 1xx, `--dump-dom`, `--allow-file-access-from-files`; die Sonde
(`browser_probe.html`) lädt `board.html` in ein iframe und klickt wirklich
(`element.click()`, `KeyboardEvent('keydown')`). Edge (151.0.4129.93) startet auf diesem Host
headless nicht — Prozess endet sofort, kein CDP-Port, `--dump-dom`/`--screenshot`/`--print-to-pdf`
liefern nichts; deshalb Chrome.

```
scripts in page: 1
details in page: 208
1 initial          : views[board=SHOWN product=hidden system=hidden] overlay=hidden open=[]
card clicked       : BUG-0022
2 after card click : views[board=SHOWN …] overlay=SHOWN open=[BUG-0022]
ref clicked        : PR-0001
3 after ref click  : views[board=SHOWN …] overlay=SHOWN open=[PR-0001]
4 after Escape     : views[board=SHOWN …] overlay=hidden open=[]
5 after system tab : views[board=hidden product=hidden system=SHOWN] overlay=hidden open=[]
node clicked       : PR-0001
6 after node click : views[… system=SHOWN] overlay=SHOWN open=[PR-0001]
7 after close      : views[… system=SHOWN] overlay=hidden open=[]
8 back on board    : views[board=SHOWN product=hidden system=hidden] overlay=hidden open=[]
```

Damit sind die drei Wünsche des Nutzers am laufenden Artefakt belegt: Karte → Modal (2), ein Klick
auf eine verlinkte Id öffnet **deren** Modal (3), echte Tabs mit genau einer sichtbaren Ansicht (5, 8).

### 4.1 Ohne JavaScript

Gemessen mit zwei iframes, deren einziger Unterschied `sandbox="allow-same-origin"` (kein Skript)
gegen `sandbox="allow-same-origin allow-scripts"` ist — das ist genau der Schalter, an dem sowohl der
Parser (`<noscript>`) als auch das Skript hängen:

| | Skript **aus** | Skript **an** |
|---|---|---|
| `<noscript>`-Kindelemente (beide Blöcke) | 1 / 1 (als Markup geparst) | 0 / 0 (nur Text) |
| `view[data-view=product]` | `hidden`, computed `display: block` | `hidden`, computed `display: none` |
| erstes `[data-detail]` | `hidden`, computed `display: block` | `hidden`, computed `display: none` |
| `.overlay` | `position: static` | `position: fixed` |
| `.tabs` | `display: none` | `display: flex` |
| Klick-Satz im Kopf (`.interactive`) | `display: none` | `display: inline` |
| `<noscript>`-Hinweis im Body | gerendert (`display: block`) | nicht vorhanden |
| Dokumenthöhe | **107 365 px** | **15 035 px** |

Die letzten beiden Zeilen sind der Grund, warum diese Messung zweimal lief: der Kopf der Seite sagt
„ein Klick öffnet den Datensatz“, und ohne Skript stimmt dieser Satz nicht. Er wird deshalb von
`_NOSCRIPT_STYLE` versteckt, und ein `<noscript>`-Absatz sagt stattdessen, was dann gilt. Eine Seite,
die eine Bedienung behauptet, die sie gerade nicht hat, ist derselbe Defekt wie ein Kommentar, der
Schutz behauptet, den der Code nicht baut — nur an einer Stelle, die der Nutzer liest.

Die Seite fällt also auf die eine lange Seite zurück, die FR-0030 ausgeliefert hat. **Nicht** auf
eine leere Seite — das stand bis zur Prüferrunde in `board.py`, in den drei READMEs und hier, und es
war falsch: die Board-Ansicht trägt kein `hidden`, ohne den Fallback stünde sie mit allen 208 Karten
da. Was der Fallback verhindert, ist eine **tote Bedienoberfläche** — eine Leiste, die nichts tut,
zwei Ansichten, die unerreichbar sind, und Karten, die nichts öffnen. Genau das sagen die drei
Stellen jetzt.

---

## 5 Selbstgenügsamkeit und feindlicher Inhalt

Beides als **Definition** gemessen, nicht als Liste verbotener Zeichenketten:

* `test_a_hostile_field_cannot_add_an_element_or_an_attribute_to_the_page` rendert denselben Store
  zweimal — einmal harmlos, einmal mit `</article><img src=x onerror=alert(1)><a
  href="javascript:alert(2)">x</a>` in Titel, Feldern **und** in der von Hand geschriebenen `id:`
  (`BUG-0002" onclick="alert(3)`) — und verlangt gleiche **Mengen** von Tag- und Attributnamen. Eine
  Injektion IST per Definition ein Element oder Attribut, das Item-Inhalt hinzugefügt hat. Zusätzlich:
  der feindliche Text muss weiterhin **sichtbar** sein (Escaping, das Inhalt verschluckt, ist keine
  Lösung).
* `test_the_page_carries_no_event_handler_and_no_link_out_of_itself`: kein Attribut**name** beginnt
  mit `on` (das ist die Klasse der Inline-Handler, nicht eine Aufzählung), kein Attribut**wert**
  beginnt mit einem URL-Schema, `//` oder `/`, und jedes `href` beginnt mit `#` und löst auf eine
  `id` **dieser** Seite auf.

---

## 6 Rot ohne den Fix (STEP 3)

Jede Mutation in einer **Kopie außerhalb** des Repos
(`_round-scratch/TSK-0079/clone`, frisch pro Mutation), Test vorher grün, nachher rot. Harness:
`_round-scratch/TSK-0079/mutate.py`.

| # | Der wiederhergestellte Defekt | Test, der rot wird | Ergebnis |
|---|---|---|---|
| M1 | die inaktiven Ansichten ohne `hidden` | `test_the_page_shows_one_view_and_the_other_two_are_hidden_in_the_dom` | 1 passed → **1 failed** |
| M2 | erster statt tiefster Elternteil | `test_a_task_hangs_under_the_item_it_was_cut_from_and_not_under_the_root` | 1 → **1 failed** |
| M3 | Unplatzierbares wird nicht gerendert | `…tree_cannot_place_is_visible_with_the_reason` + 5 Fälle | 6 → **6 failed** |
| M4 | ein Grund für jede Ablehnung | `test_the_reason_a_link_did_not_resolve_is_the_one_the_contract_gives` | 5 → **3 failed**, 2 passed (NO_LINK/UNREADABLE sind der unveränderte Zweig) |
| ~~M5~~ | `data-detail` ohne `quote=True` | — | **ungültig, siehe §10.2** |
| M6 | verlinken **vor** escapen | Hostile-Diff | 1 → **1 failed** |
| ~~M7~~ | Item-Inhalt ins `<script>` | — | **ungültig, siehe §10.2** |
| M8 | rekursiver Baum-Walk statt Stack | `test_a_long_chain_of_links_still_reaches_the_page` | 1 → **1 failed** |
| M9 | ein Datensatz **pro Ansicht** statt einer | `test_every_field_of_an_item_is_in_its_detail_exactly_once` | 1 → **1 failed** |
| M10 | `href` auf eine fremde Domain | No-Handler/No-Link-Test | 1 → **1 failed** |
| M11 | Archiv wird nicht gezählt | `test_the_tab_strip_counts_what_the_archive_holds…` | 1 → **1 failed** |
| M12 | `ROOT_TYPES` ohne PROC | Kit-Wurzeltest + Prozedur-Wurzeltest | 4 → **2 failed**, 2 passed (dev/research unberührt) |
| M13 | BUG in keiner Ansicht | Stolperdraht + Gruppentest | 2 → **2 failed** |
| M14 | kein Ausgang aus der Platzierungsschleife (`break` → `continue`) | `test_a_link_that_points_at_itself_cannot_hang_the_state_write` | 1 passed in 2 s → **TIMEOUT nach 180 s** |
| M15 | `HEADER_FIELDS` verbreitert | `test_every_field_of_an_item_is_in_its_detail_exactly_once` | 1 → **1 failed** |
| M16 | Kartentitel ohne den Item-Schutz | `test_an_item_no_renderer_can_read_costs_its_own_card_and_nothing_else` | 1 → **1 failed** |
| M17 | eine Tab-Zahl, die lügt | Tab-Test | 1 → **1 failed** |
| M18 | `data-open` im Markup umbenannt, Skript unverändert | `test_every_attribute_the_page_script_acts_on_is_one_the_renderer_writes` | 1 → **1 failed** |

### 6.1 Eine Behauptung, die die Messung widerlegt hat

Der erste Entwurf des Tiefentests stand bei **400** Ebenen, mit dem Satz „400 ist jenseits der
Rekursionsgrenze“. M8 blieb damit **grün** — die Behauptung war falsch. Nachgemessen
(`_round-scratch/TSK-0079/depth_probe.py`, rekursive Fassung):

```
depth   400  ok  2.8s  tiefster Knoten auf der Seite: True
depth   900  ok  4.1s  tiefster Knoten auf der Seite: True
depth  1100  ok  3.7s  tiefster Knoten auf der Seite: False   ← RecursionError
depth  1500  ok  6.0s  tiefster Knoten auf der Seite: False
```

Der Fehler ist dabei **kein Abbruch**: die `RecursionError` landet in `state._write_board`, das
absichtlich fail-soft ist. Der Zustandsschreibvorgang geht durch, eine Zeile geht nach stderr, und
die **Seite behält ihren alten Inhalt** — der Baum hört also still auf, die Wahrheit zu sagen. Der
Test heißt darum jetzt `test_a_long_chain_of_links_still_reaches_the_page` und baut 1200 Ebenen; der
Kommentar an `board._branches` behauptet keine Zahl mehr, sondern zeigt hierher.

---

## 7 Die 21 alten Board-Tests

Keiner ist gestrichen, alle 19 Funktionen (21 Fälle) laufen weiter; drei sind **mitgewandert**, mit
Grund:

| Test | Änderung | Grund |
|---|---|---|
| `test_every_field_of_an_item_is_on_its_card_exactly_once` → `…_is_in_its_detail_exactly_once` | liest den Datensatz statt der Klappkarte; **neu**: das Item steht auf dem Board und in **beiden** Bäumen und hat trotzdem genau einen Datensatz | die Klappkarte ist die Fläche, die FR-0053 ersetzt; die neue Hälfte fängt „ein Datensatz pro Ansicht“ (M9) |
| `test_a_title_that_closes_the_card_element…` → `…that_tries_to_close_the_elements_around_it…` | Titel schließt jetzt `</button></article></script>` | die Karte ist kein `<details>` mehr, und es gibt ein `<script>` |
| `test_an_item_no_renderer_can_read_costs_its_own_card_and_nothing_else` | dritter Eintrag, dessen **Titel** beim Rendern wirft | Karte und Baumknoten stehen außerhalb von `_detail`s try; ohne `_face_title` kostet ein Titel die ganze Seite (M16) |
| `test_a_revoked_approval…`, `test_a_self_referential…`, `test_an_alias_bomb…` | `page.folds` → `page.details` | dieselbe Prüfung, neue Fläche |
| `test_an_alias_bomb_cannot_stretch_a_state_write` | Byte-Schranke `+2048` → `+4096` | ein Item kostet jetzt zusätzlich einen Baumknoten und eine Warnzeile; die Schranke bleibt an `VALUE_MAX_CHARS` gebunden |

18 Testfunktionen sind neu (19 → 37; 21 → 45 Fälle).

---

## 8 Reste — benannt, nicht geschlossen

1. **Der Klick ist in der Suite nicht ausgeführt.** Es gibt keinen Browser in `pytest`. Die Suite
   misst zwei Dinge: den DOM-Zustand, den der Renderer schreibt, und die **Kopplung** Skript↔Markup
   (`test_every_attribute_the_page_script_acts_on_is_one_the_renderer_writes`: jeder `data-`-Name,
   den das Skript nennt, existiert auf der Seite, und jeder `<button>` trägt mindestens einen Namen,
   auf den das Skript reagiert — M18). Was **nicht** gemessen ist: dass ein Klick die richtige
   Wirkung hat. Das steht in §4, einmal, von Hand. Ein Regressionsschutz dafür müsste einen Browser
   in die Suite holen; das ist eine eigene Entscheidung und keine dieser Runde. Der Modul-Docstring
   von `tools/test_board.py` sagt genau diese Grenze, damit sie nicht als Deckung gelesen wird.
2. **Ein Wurzeltyp wird nie geschachtelt.** Ein `PROC` mit `derives_from` bleibt eine Wurzel — die
   eine Stelle, an der der Baum eine echte Verbindung ungenutzt lässt. Entscheidung mit Begründung im
   Docstring von `arrange`, festgehalten von
   `test_a_procedure_that_names_another_one_is_still_a_root`, damit sie sichtbar verrottet.
3. **Sprache der Tab-Beschriftungen.** FR-0053 nennt die Tabs deutsch („Produkt-Backlog“,
   „System-Backlog“). Ausgeliefert sind **englische** Beschriftungen („Product backlog“,
   „System backlog“), weil die ganze Seite englisch ist (`Backlog board`, `no further fields`,
   Warnungen). Bewusste Abweichung, eine Zeile groß (`backlog_tree.VIEWS[*].label`) — wenn der Nutzer
   die Seite deutsch will, ist das eine eigene, ganze Entscheidung (dann auch Spaltenköpfe,
   Warnungen, Kopfzeile), keine halbe hier.
4. **`unassigned-off-view` fasst zwei Lagen zusammen:** „nennt ein Item, das diese Ansicht nicht
   zeigt“ und „nennt ein Item dieser Ansicht, das selbst in einem Zyklus hängt“. Beide Male ist der
   Satz wahr; unterschieden werden sie nicht. Aufgefallen beim Bauen, nicht gemessen als Schaden.
5. **FR-0054 (BUG→SR) ist nicht gebaut**, wie beauftragt. Ein BUG hängt an `related_pr`, also unter
   der Wurzel — im Systembaum dieses Repos sind das 55 Knoten in drei Gruppen.
6. **Die Archivzählung kostet einen Verzeichnis-Walk pro Zustandsschreibvorgang.** Auf diesem Store
   (91 archivierte Items) ist er im Gesamtwert von 0,52 s nicht messbar abgesetzt; er wächst mit der
   Zahl **archivierter Items**. Keine Schranke eingebaut — eine Zahl ohne gemessenen Anlass wäre
   geraten.
7. **`docs/POST_V2_WISHLIST.md` ist verbotener Bereich** in diesem Auftrag; die Punkte 1, 2 und 4
   stehen deshalb nur hier und im Bericht an den Lead, nicht in der Löcherliste.

---

## 9 Abschluss

```
python tools/bump_kit_version.py   dev 2026.08.21-9, office 2026.08.21-10, research 2026.08.21-9
python -m ruff check .             All checks passed
python tools/validate.py           all structural checks passed
python -B -m pytest .claude/hooks/test_gates.py -q     243 passed          in  900,19 s (15:00)
python -B -m pytest tools/test_board.py -q              45 passed          in   19,74 s
python -B -m pytest tools/ -q                         2951 passed, 13 skipped, 1727,33 s (28:47)
```

Der Lauf oben ist der **letzte**, mit genau dem Stand, der hier liegt (Stempel `-9/-10/-9`).

Zwei frühere volle Läufe zur Einordnung, beide ohne Befund am Code:

* **11 failed / 2939 passed** — nach dem Lauf hatte ich zwei Docstrings korrigiert und den Stempel
  nicht erneuert. `validate.py` meldet dann „VERSION not bumped“, und die bekannten ~10
  Scaffold-/Installer-Tests fallen mit. Genau der Fall, den Hausregel 7 beschreibt.
* **2950 passed / 13 skipped (29:50)** und **2951 passed / 13 skipped (28:49)** — die Läufe vor der
  letzten Änderung (`.interactive` + `<noscript>`-Hinweis, §4.1). Der Unterschied von 1 ist der
  nachgereichte Kopplungstest (M18).

`.claude/hooks/test_gates.py` lief vor der letzten Kernel-Änderung; sie berührt keine Datei unter
`.claude/` und keinen Pfad, den ein Gate liest — die 243 Tests messen die vier Gates dieses Repos,
nicht den Kernel.

---

## 10 Nacharbeit nach der Prüferrunde (2026-08-21)

Verdikt: **FAIL** — zwei blockierende Befunde, fünf Reste. Beide Blocker waren echt, beide sind
geschlossen, und zwei meiner eigenen Rot-Belege aus §6 waren **ungültig**. Der Reihe nach.

### 10.1 B1 — die Aliasbombe war im neuen Modul wieder offen

`backlog_tree.parents_of` rief `str(one)` auf jedem Element eines Bindungsfeldes auf. Genau der
Defekt, den TSK-0071 in `board._emit` geschlossen hat: `yaml.safe_load` löst Aliase in **geteilte**
Objekte auf, und ein einziger `str()`-Aufruf faltet den ganzen Graphen aus — kein Budget kann einen
einzelnen Aufruf unterbrechen. Dazu war `str(one) not in found` eine lineare Suche pro Element.

Warum der alte Bombentest das nicht sah: er füllt `repro` und `observed`, also Felder, die **nur der
Renderer** liest. Bindungsfelder liest seit TSK-0079 ein zweiter Leser.

Gemessen (Prüfer, hier reproduziert): eine 535-Byte-`SR` mit der Bombe in `derives_from` →
**97,77 s / 480 MB** pro Zustandsschreibvorgang gegen 0,02 s ohne. In meiner Mutationsmessung
(24 Ebenen, die Tiefe des vorhandenen Bombentests) läuft der **eine** Test mit dem
wiederhergestellten Defekt **638 s** statt 3 s.

Fix (`team-kits/kernel/backlog_tree.py`, `parents_of`): ein Container in einem Bindungsfeld ist
**keine** Referenz und wird übersprungen; Dedup über ein `set`. Eine Id ist per Konstruktion ein
Skalar, also geht nichts verloren, was eine Bindung legitim tragen kann — das Item liest sich als
„ohne <Feld>“ und steht sichtbar unter Unassigned.

Rot ohne den Fix: **M19** — `test_an_alias_bomb_in_a_binding_field_cannot_stretch_a_state_write`,
1 passed (3 s) → **1 failed (638 s)**.

### 10.2 B2 — die feindliche Id kam nie auf der Seite an, und meine M5/M7-Belege waren ungültig

**Der Fixture-Defekt.** Die feindliche Datei wurde Feld für Feld mit `yaml.safe_dump(value).strip()`
zusammengesetzt. `safe_dump` eines Skalars hängt den Dokument-Ende-Marker `...` an, und `strip()`
entfernt ihn nicht (er ist kein Leerraum). Die Datei war damit ein kaputter Mehrdokument-Strom, das
Item landete als `(unreadable)`, und die feindliche Id und der feindliche Titel erreichten die Seite
**nie**. Fix: **ein** `yaml.safe_dump` über die ganze Abbildung — plus zwei Ankunfts-Asserts, damit
ein Fixture, das seinen Angriff nicht ausliefert, künftig selbst rot wird.

**Der Mutations-Defekt, und der ist meiner.** Die M5- und M7-Mutationen aus §6 haben die **Zahl der
`%s`-Platzhalter** einer Formatzeichenkette verändert. `board.render` warf damit für jedes Item
`TypeError: not all arguments converted during string formatting`, die Seite wurde gar nicht
geschrieben, und der Test scheiterte an einer **fehlenden Datei**. Das ist ein Rot aus mechanischem
Grund und **kein** Beleg, dass die Prüfung den Defekt sieht. Beide Zeilen in §6 sind darum
durchgestrichen.

Nachgemessen mit gültigen Mutationen (`_round-scratch/TSK-0079/mutate3.py`) — und mit `quote=False`
statt eines nackten `html.escape(x)`, denn dessen Vorgabe **ist** `quote=True`, ein bloßer Aufruf
wäre eine Nulloperation gewesen:

| # | Defekt | Fixture | Ergebnis |
|---|---|---|---|
| M5d | `data-detail` mit `quote=False` | repariert | 2 passed → **1 failed** (`KeyError: 'BUG-0002" onclick="alert(3)'` — der Ankunfts-Assert), 1 passed |
| M5e | Karten-`data-open` mit `quote=False` | repariert | 2 passed → **1 failed**, 1 passed |
| M5f | **derselbe** Defekt | **wie ausgeliefert** | 1 passed → **1 passed** — die Gegenrichtung, die B2 beweist |
| M7b | Item-Ids ins `<script>` interpoliert, Formatzeichenkette unangetastet | — | 1 passed → **1 failed** |

Der zweite der beiden ausgewählten Tests (`…no_event_handler_and_no_link_out_of_itself`) bleibt bei
M5d/M5e grün, und das ist richtig: sein Store schreibt keine Id von Hand, er greift Feld**werte** an.

**Der ausgelieferte Code war in beiden Fällen korrekt** — der Prüfer hat die feindliche Id durch den
echten Schreibweg geschickt und sie escaped vorgefunden. Kaputt war der Beweis, nicht der Schutz.

### 10.3 Die fünf Reste

| # | Befund | Was jetzt gilt | Rot ohne Fix |
|---|---|---|---|
| N1 | „statt einer, die nichts zeigt“ — falsch: ohne Fallback steht die **Board-Ansicht mit allen Karten** da, nur tot | korrigiert in `board.py` (Modul-Docstring + `_NOSCRIPT_STYLE`), in den drei READMEs, im `<noscript>`-Absatz der Seite und in §4.1 | Prosa, kein Test — die Messung dahinter steht in §4.1 |
| N2 | das anfängliche `hidden` des Overlays war ungemessen (es ist `position: fixed; inset: 0` — ohne das Attribut liegt es ab dem ersten Bild über allem) | eine Zeile im vorhandenen DOM-Zustands-Test | **M20** 1 passed → **1 failed** |
| N3 | die Behauptung „der Walk betritt `archive/staging/` nie“ hatte keinen Test | Gegenrichtung im Archiv-Test: eine item-förmige Datei unter `archive/staging/2026/TSK-0001/` darf die Zahl nicht bewegen | **M21** 1 passed → **1 failed** |
| N4 | der `VALUE_MAX_CHARS`-Schnitt konnte eine Referenz **erfinden** (`PR-000199999` → Knopf auf `PR-0001`) | `_CUT_REFERENCE` verwirft am Schnitt jeden nachlaufenden Id-Lauf | **M22** 1 passed → **1 failed** (siehe unten) |
| N5 | „1 request name no related_pr“ | die fünf Meldungen tragen kein finites Verb und kein Possessivpronomen mehr, also nichts, was sich beugen müsste | Grammatik ist maschinell nicht prüfbar — **kein** Test behauptet das |

**N4 kostete einen zweiten Anlauf, und das gehört hierher:** der erste Testentwurf klebte den Füller
direkt an die Id (`xxxPR-0001`). `_REFERENCE` verlangt eine Wortgrenze, also war das gar kein
Treffer — der Test maß die Grenzregel statt das Budget und blieb mit wiederhergestelltem Defekt
**grün** (M22, erster Lauf). Mit einem Leerzeichen vor dem Fragment wird er rot. Ein Test, der nicht
scheitern kann, ist teurer als keiner; das ist die Regel, und sie hat mich in dieser Runde zweimal
erwischt (hier und bei der Tiefe in §6.1).

### 10.4 Sprache der Seite — geht an den Nutzer, nicht an mich

Bleibt als benannte Abweichung (§8.3). Der Prüfer hat den Mechanismus dazugelegt: diese Runde hat
die **englische Prosafläche vergrößert** — zwei Leitabsätze, zehn Typbezeichnungen, fünf
Warnungsvorlagen, der Unassigned-Text und der `<noscript>`-Hinweis —, und zwar für genau das
Publikum, für das die Verfassung einfache Sprache verlangt. Die Entscheidung gehört dem Nutzer; der
Lead trägt sie vor.

### 10.5 Abschluss der Nacharbeit

```
python tools/bump_kit_version.py   dev 2026.08.21-10, office 2026.08.21-11, research 2026.08.21-10
python -m ruff check .             All checks passed
python tools/validate.py           all structural checks passed
python -B -m pytest tools/test_board.py -q               47 passed          in    22,85 s
python -B -m pytest tools/ -q                         2953 passed, 13 skipped, 1883,33 s (31:23)
python -B -m pytest .claude/hooks/test_gates.py -q      243 passed          in 1162,91 s (19:22)
```

Beide Läufe mit genau dem Stand, der jetzt hier liegt (Stempel `-10/-11/-10`), keiner davon rot.

Der Board-Absatz der drei `templates/project_memory/README.md` ist nach der Korrektur wieder
byte-gleich (sha256 der Passage, alle drei `08c01f98378dc5ec`). Seite auf dem echten Store nach der
Nacharbeit: **465 445 B**, `generate_index()` 0,52 / 0,54 / 0,56 s; Klick-Sonde im Browser
unverändert durchgelaufen (Karte → Modal → Referenz → Escape → Tab → Baumzeile → Close → Board).
