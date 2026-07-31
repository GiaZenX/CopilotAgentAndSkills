# Der Plan als Bild — Recherche und Empfehlung

## 0. Befund im Repo zuerst (damit die Empfehlung nicht auf Prosa aufsetzt)

Die draw.io-Werkzeugkette aus Spec II.6a existiert heute **als Zusage, nicht als Datei**:

- `git ls-files | grep -i "drawio|\.svg$"` liefert **null Treffer** — es gibt kein einziges getracktes `.drawio.svg`, keine Vorlagen-Diagramme, kein `.vscode/extensions.json`-Template. Beides verspricht `docs/HARNESS_V2_SPEC.md:549`.
- Die einzige maschinelle Prüfung ist `c:\Offline Repos\AgentAndSkills\team-kits\kernel\staging.py` → `_assert_xml_wellformed()`, und das ist ein blosses `ET.parse()`. Der Docstring sagt das selbst ehrlich: *„a true browser render check is phase-2 tooling — the companions' `render_check: True` currently attests EXACTLY that well-formedness, nothing more"*. Ein `render_check: True` behauptet also mehr, als es prüft.
- `.drawio.svg` steht in `hooks/_kernel.py:77` `CANONICAL_SUFFIXES = (".yaml", ".yml", ".html", ".drawio.svg")` — das Format ist im Schreibpfad zugelassen.
- `ACTIVE_DIRS` (`team-kits/kernel/backlog_types.py:149`) kennt `ARC → architecture/active` und `WFR → design/wireframes`. **Ein Planbild ist keiner dieser Typen** — das ist unten die wichtigste Abgrenzung.

---

## 1. Generiert oder gepflegt?

**Empfehlung: generiert — und die übliche Gegenrede („generiert ist hässlich") trifft ausgerechnet bei einem Planbild nicht zu.**

Der Grund ist technisch und lohnt die Genauigkeit: „generiert ist hässlich" heisst in Wahrheit *„ein Programm kann keinen Graphen layouten"*. Das stimmt — die mxGraph-Layoutalgorithmen leben im **Editor** (JavaScript/ELK), nicht in einer Python-Bibliothek. draw.io selbst dokumentiert automatisches Layout nur an drei Stellen: `Arrange > Layout` im Editor, der CSV-Import mit `# layout: verticalflow|horizontalflow|elkOrganic|libavoid` ([drawio.com/docs/manual/insert/insert-from-csv](https://www.drawio.com/docs/manual/insert/insert-from-csv/)), und der `#create`-URL-Parameter ([drawio.com/docs/reference/diagram-generation](https://www.drawio.com/docs/reference/diagram-generation/)). Selbst die eigene „Insert from text"-Baumsyntax layoutet **nicht** automatisch — die Doku empfiehlt ausdrücklich, danach von Hand `Arrange > Layout` zu wählen ([insert-from-text](https://www.drawio.com/docs/manual/insert/insert-from-text/)).

**Ein Umsetzungsplan ist aber kein Graph, den man layouten müsste.** Er ist ein Raster: Spalten = Stufen, Zeilen = Vorgänge. Koordinaten sind eine Multiplikation, kein Algorithmus. Damit fällt der einzige echte Nachteil der Generierung weg.

### Was es an Werkzeug gibt

| Werkzeug | Was es kann | Belastbarkeit |
|---|---|---|
| **drawpyo** ([Repo](https://github.com/MerrimanInd/drawpyo), [Doku](https://merrimanind.github.io/drawpyo/)) | Python → `.drawio`-XML; eigene Auto-Layouts für **Tree, BinaryTree, Bar/Pie, Legend**; kann draw.io-Shape-Libraries laden | ~411 Sterne, 154 Commits, 27 offene Issues. Kein Graph-Layout, **kein SVG-Ausgang**. Für ein Raster-Planbild ist die Bibliothek Overhead. |
| **drawio-desktop CLI** `drawio -x -f svg --embed-diagram` | erzeugt aus `.drawio` ein echtes `.drawio.svg` | Funktioniert, ist aber **Electron**: unter Linux/CI braucht es xvfb und `--no-sandbox`. Für ein Hook, das bei jedem Session-Start läuft, ist das eine schwere Abhängigkeit. ([Issue 848](https://github.com/jgraph/drawio-desktop/issues/848), [Exportformate](https://www.drawio.com/docs/manual/export/export-diagram/)) |
| **XML selbst schreiben** | `<mxGraphModel>`-Fragment, unkomprimiert | **Das ist draw.ios eigene Empfehlung für maschinelle Erzeugung.** Wörtlich: *„AI systems should not generate compressed content"*; Regeln: (0,0) oben links, Kinder von Gruppen relativ, eindeutige IDs, keine Kommentare. ([diagram-generation](https://www.drawio.com/docs/reference/diagram-generation/)) |

### Der Kniff für `.drawio.svg` ohne Electron

Ein `.drawio.svg` ist ein **valides SVG mit dem kompletten `<mxfile>`-XML im `content`-Attribut des Wurzelelements** ([drawio.com/docs/manual/export/embed-svg](https://www.drawio.com/docs/manual/export/embed-svg/), [hediet/vscode-drawio](https://github.com/hediet/vscode-drawio)). Weil der Generator die Koordinaten ohnehin selbst legt, kann **derselbe Layout-Durchgang beide Darstellungen ausgeben**: die SVG-Rechtecke/Pfade/Texte *und* das `content`-XML. Kein Chromium, kein Java, keine Node-Abhängigkeit — reines Python neben dem Kernel. Das ist der Punkt, an dem „generiert" hier billig wird.

**Ehrliche Einschränkung:** Beide Darstellungen aus einer Quelle heisst auch, sie können auseinanderlaufen, wenn jemand nur eine Hälfte anfasst. Genau deshalb gehört die Datei nach `generated/` und wird nicht committet (Spec II.2) — sie ist Ausgabe, kein Zustand. Wer sie im draw.io-Editor bearbeitet, hält eine Wegwerfkopie in der Hand, und die nächste Regenerierung überschreibt sie. Das ist keine Schwäche, das ist die Zusicherung „kann nie veralten".

### Neu und relevant: draw.io hat jetzt einen offiziellen Validierungspfad

Seit dem MCP-Release veröffentlicht jgraph eine **XSD für das Dateiformat**: [`jgraph/drawio-mcp/shared/mxfile.xsd`](https://github.com/jgraph/drawio-mcp/blob/main/shared/mxfile.xsd), ausdrücklich gedacht, *„to validate AI-generated output before saving"*, plus eine [XML-Referenz](https://github.com/jgraph/drawio-mcp/blob/main/shared/xml-reference.md). Das ist für diesen Harness die wichtigste Einzelmeldung der ganzen Recherche — siehe Gate-Tabelle in Abschnitt 4.

---

## 2. Die Alternativen, an der Frage gemessen, die der User wirklich gestellt hat

Die dritte Spalte ist die entscheidende: *kann ein Nicht-Techniker das Ergebnis danach anfassen?*

| | als Text versionierbar | Render ohne Netz | **danach von Laien editierbar** |
|---|---|---|---|
| **Mermaid** | ja, sehr diff-freundlich | **mit Vorbehalt.** Offizielles `mmdc` startet für **jedes** Diagramm ein headless Chrome via Puppeteer (~170 MB Chromium). Browserlose Alternative `mermaidx` (QuickJS + resvg) existiert, ist aber jung und dünn adoptiert — kein Fundament für ein Gate. | **nein als Text — aber ja über die Brücke:** draw.io importiert Mermaid als **native, editierbare draw.io-Shapes** (`Arrange > Insert > Mermaid`, Option „Diagram" statt „Image"). Vorbehalt aus der Doku: *„Any changes to the position, size or connection type will be discarded if you edit the Mermaid source."* Die Rückkopplung ist also gekappt. ([mindmap-from-text](https://www.drawio.com/docs/manual/mermaid/mindmap-from-text/), [mermaid-cli #650](https://github.com/mermaid-js/mermaid-cli/issues/650)) |
| **PlantUML** | ja | ja, aber **Java** (`plantuml.jar`), für viele Diagrammtypen zusätzlich Graphviz. Mindmaps brauchen kein Graphviz. | nein; draw.io kann PlantUML ebenfalls importieren, gleiche Einbahnstrasse. ([plantuml.com/mindmap-diagram](https://plantuml.com/mindmap-diagram)) |
| **Structurizr (C4-as-code)** | ja (DSL) | `structurizr-cli` ist **Java**; Export nach `plantuml`, `c4plantuml`, `mermaid`, `dot`, `d2`, `ilograph`, `json`, `static` — **kein draw.io-Exporter** ([docs.structurizr.com/cli/export](https://docs.structurizr.com/cli/export)) | nein | 
| **Excalidraw** | JSON — technisch Text, praktisch **diff-feindlich** (jede Verschiebung ändert Koordinaten in einem grossen Array) | ja, `.excalidraw.svg` trägt die Szene eingebettet, VS-Code-Extension arbeitet offline ([excalidraw/excalidraw-vscode](https://github.com/excalidraw/excalidraw-vscode)) | **am besten von allen** — genau dafür gebaut. Aber **maschinell erzeugen ist das Gegenteil seiner Stärke**: kein Layout, kein etablierter Generator. |
| *(D2, der Vollständigkeit halber)* | ja | **ja, sauber** — ein einzelnes Go-Binary, kein Browser, kein Java, eingebautes Layout (dagre/ELK) | nein |

**Fazit zu Structurizr:** Es ist hier schlicht das falsche Werkzeug. Structurizr modelliert **Architektur** (C4). Der User will einen **Umsetzungsplan mit Fortschritt**. Und ohne draw.io-Exporter müsste man ausgerechnet das Format verlassen, das der Harness schon kanonisiert hat.

**Fazit zu Excalidraw:** Es beantwortet Frage 3 („editierbar") besser als alles andere und Frage 1 („generierbar") schlechter als alles andere. Für einen *generierten* Statusplan disqualifiziert. Als handgezeichnetes Beiwerk denkbar — aber dann hat man wieder die handgepflegte Zweitfassung, die laut `POST_V2_WISHLIST.md` genau das Problem ist.

**Structurizr, PlantUML und mermaid-cli haben ausserdem eine Gemeinsamkeit, die im Harness zählt:** sie ziehen eine Laufzeit (JVM bzw. Chromium) in einen Hook-Pfad, der heute mit nichts als Python auskommt. Das ist der eigentliche Ausschlussgrund, nicht die Diagrammqualität.

---

## 3. Mindmap: welche Formate überleben Maschine *und* Hand?

Die Antwort ist überraschend eindeutig: **eingerückte Textlisten**. Alles andere fällt auf einer der beiden Seiten um.

| Format | Maschine schreibt | Mensch ändert | Urteil |
|---|---|---|---|
| **Mermaid `mindmap`** — reine Einrückung, keine Pfeile, keine Klammern ([mermaid.js.org/syntax/mindmap](https://mermaid.js.org/syntax/mindmap.html)) | trivial | **trivial** — Zeile einfügen, Tab drücken. Das kann jeder. | **beste Kombination.** Zusätzlich: draw.io importiert es als native Shapes (s. o.), GitHub rendert es inline. |
| **Markdown-Liste + markmap** ([markmap.js.org](https://markmap.js.org/), [Repo](https://github.com/markmap/markmap), MIT) | trivial | trivial — es *ist* nur eine Bulletliste | gleichwertig; erzeugt eine interaktive Standalone-HTML (auf-/zuklappbar, zoombar). Kein draw.io-Bezug. |
| **PlantUML `@startmindmap`** — `*`/`**`/`***`, `+`/`-` für Seitenwahl | trivial | leicht | gut, aber Java im Renderpfad |
| **FreeMind `.mm` / OPML** | trivial (XML-Baum) | nur in Freeplane o. ä. — nicht im Editor, nicht im Repo-Workflow | fällt durch |
| **draw.io Mindmap-Shapes** (Advanced-Shape-Library; die Container **rücken beim Hinzufügen automatisch nach**, [automated-layout-shapes](https://www.drawio.com/docs/manual/shapes/automated-layout-shapes/)) | schlecht (Container mit relativen Kindkoordinaten) | **ideal** — auf den Pfeil klicken, Knoten wächst, Layout rückt selbst nach | fällt auf der Maschinenseite durch |
| **XMind** | ZIP-Archiv | gut | nicht diffbar → fällt durch |

**Kernaussage für den User:** Eine Mindmap ist per Definition das Artefakt, an dem *er* schnell etwas ändern will. Sie darf deshalb **nicht generiert** werden — ein generiertes Bild, in das man hineinschreibt, verliert seine Änderungen beim nächsten Lauf. Die Mindmap ist die *gepflegte* Hälfte, und ihr Format muss so einfach sein, dass Pflegen keine Hürde ist. Eine eingerückte Liste ist diese Hürde nicht.

---

## 4. Konkrete Empfehlung für dieses Repo

**Zwei Artefakte mit zwei verschiedenen Lebensläufen — sie nicht zu trennen ist der Fehler, den man hier machen kann.**

### A) Statusplan — GENERIERT, nicht committet

```
project_memory/generated/plan.drawio.svg
```

- **Quelle:** `generated/index.yaml` + die aktiven Item-Dateien — exakt dieselbe Quelle wie `dashboard.html` (Spec II.7). Keine zweite Wahrheit.
- **Erzeuger:** ein Modul neben dem Kernel, z. B. `team-kits/kernel/plan_diagram.py`, aufgerufen aus `team-kits/kernel/cli.py` als dritter Unterbefehl neben den vorhandenen `generate-index` und `generate-session-brief` (`cli.py:27-28`), und ausgelöst vom selben Hook, der heute schon das Dashboard neu baut (`auto_dashboard`).
- **Layout:** fest verdrahtet. Bahnen von links nach rechts — **Wunsch → Ziel → Bausteine → Arbeit → Abgenommen** (bewusst ohne PR/SR/TSK im sichtbaren Text; die IDs stehen klein darunter). Zeilen = Items. Kein Layout-Algorithmus, keine Layout-Bibliothek, keine Electron-/JVM-Abhängigkeit.
- **Ausgabe:** SVG-Geometrie **und** `content="<mxfile>…"` unkomprimiert aus demselben Durchgang.
- **Nicht committet** (Spec II.2: `generated/**`). Damit kann es strukturell nicht veralten und erzeugt keine Merge-Konflikte.

**Die wichtigste Abgrenzung:** Dieses Bild ist **kein ARC und kein WFR**. Kein Companion-YAML, kein `diagram_hash`, kein `approval_ref`, kein Promotion-Pfad, kein Eintrag in `ACTIVE_DIRS`. Ein regenerierbares Bild darf keinen Freigabeweg erben — sonst friert der Kernel eine Ausgabe ein und der User genehmigt eine Ansicht.

### B) Mindmap — GEPFLEGT, committet

```
project_memory/product/plan.mindmap.md      (Mermaid ```mermaid mindmap-Block)
```

Neben `product/masterplan.md`, das laut Spec II.2 schon genau dieser Sorte angehört: *„eingefrorenes Discovery-Artefakt (keine Statusquelle)"*. Sie ist Absicht, nicht Zustand — deshalb committet und deshalb von Hand.

**Zwei Dinge, die vor der Umsetzung entschieden werden müssen, nicht stillschweigend gemacht:**

1. `CANONICAL_SUFFIXES` (`hooks/_kernel.py:77`) kennt `.md` nicht. `masterplan.md` existiert trotzdem — d. h. `.md` wird irgendwo geduldet. **Welcher Pfad das erlaubt, muss man nachlesen, bevor man eine zweite `.md` in `product/` legt**, sonst blockt `gate_write_scope` oder — schlimmer — er blockt nicht und niemand weiss warum.
2. Alternative, die diese Frage komplett vermeidet: die Mindmap als Abschnitt **in** `masterplan.md`. Kostet keinen neuen Dateityp und kein Gate. Dagegen spricht nur, dass ein eingefrorenes Discovery-Artefakt schlecht der Ort für etwas ist, woran man täglich schiebt.

Der Weg zum Bild: `Arrange > Insert > Mermaid`, Option **„Diagram"** (nicht „Image") → native, frei verschiebbare draw.io-Shapes. Mit der ausdrücklichen Ansage im SKILL-Text, dass diese Kopie ein Wegwerfbild ist und die Quelle die Textliste bleibt.

---

### Und jetzt die Linie, um die es Ihnen geht: GATE oder SKILL?

**GATE — mechanisch prüfbar, gehört in einen Hook oder Test:**

| Prüfung | Warum sie ein Gate sein darf |
|---|---|
| **Regenerieren ⇒ identisches Byte-Ergebnis** (`plan.drawio.svg` neu bauen, mit dem vorhandenen vergleichen) | Das ist der *einzige* Test, der die Zusage „kann nie veralten" **erzwingt** statt sie zu behaupten. Ohne ihn ist „generiert" auch nur Prosa. |
| **Validierung gegen [`mxfile.xsd`](https://github.com/jgraph/drawio-mcp/blob/main/shared/mxfile.xsd)** statt `ET.parse()` | Hebt `_assert_xml_wellformed` in `staging.py` von „ist XML" auf „ist ein gültiges draw.io-Dokument". Ein offizielles Schema von jgraph, kein Eigenbau. **Trifft nebenbei auch ARC und WFR** — und macht `render_check: True` erstmals zu einer Aussage, die annähernd hält, was der Name verspricht. Umbenennen sollte man es trotzdem: es bleibt eine Struktur-, keine Renderprüfung. |
| **Jeder Knoten trägt eine existierende ID aus `ACTIVE_DIRS`** | Fail-closed. Verhindert einen Schritt im Bild, den es im Zustand nicht gibt. |
| **Status wird nie allein über Farbe getragen** — jeder Knoten hat zusätzlich Textlabel oder Symbol | [WCAG 2.2 SC 1.4.1 „Use of Color"](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html). Bei generiertem SVG ist das trivial prüfbar: zähle Knoten ohne Statustext. |
| **Kontrast der Statuspalette ≥ 4.5:1 (Text) bzw. ≥ 3:1 (Ränder/Flächen)** | [WCAG 2.2 SC 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) / [SC 1.4.11 Non-text Contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html). Die Palette ist endlich und liegt im Generator → als Unittest über eine Farbtabelle rechenbar. |
| **Keine hart kodierte Hex-Farbe im Generatorcode** — Farben nur aus der benannten Statustabelle | Dasselbe Argument wie beim Frontend-Token-Gate, hier aber leichter durchzusetzen, weil es genau einen Erzeuger gibt. |
| **Grössenbudget:** max. N Knoten pro Datei | Spec II.6a fordert das bereits als Prosa (*„Diagramme bleiben klein — ein Anliegen pro Datei"*) und mildert damit das LLM-Layout-Risiko. Eine Zahl ist zählbar, ein „bleiben klein" nicht. |

**SKILL — Urteil, darf sich nicht als erzwungen ausgeben:**

- **Was überhaupt aufs Bild gehört** und in welcher Reihenfolge. Kein Gate kann Relevanz messen.
- **Die Flughöhe und die Wortwahl** („Wunsch" statt „PR", „Abgenommen" statt „APR delivery"). Hier ist die ehrliche Zwischenlösung eine **Begriffs-Sperrliste als Gate** — 12 verbotene Wörter im sichtbaren Text —, aber sie muss im Kommentar wörtlich sagen: *sie prüft die Abwesenheit von zwölf Wörtern, nicht Verständlichkeit*. Das ist genau die Sorte Kommentar, die dieser Harness laut Ihren eigenen Lektionen sonst falsch schreibt.
- **Die Pflege der Mindmap** — wann ein Ast wandert, wann er ein eigener Zweig wird. Reines Urteil.
- **Die Ansage, dass die draw.io-Kopie einer Mermaid-Mindmap eine Wegwerfkopie ist.** Nicht prüfbar, nur sagbar — die draw.io-Doku bestätigt den Datenverlust ausdrücklich.

---

### Wo etwas dünn oder umstritten ist

- **`mermaidx`** (browserloses Mermaid-Rendering) ist die technisch eleganteste Lösung für Netz-freies Rendern, aber jung und dünn adoptiert. Nicht als Gate-Abhängigkeit einbauen.
- **Die `mxfile.xsd`** ist mit „Version 1.0" beschriftet und liegt im MCP-Repo, nicht in `jgraph/drawio` selbst. Sie ist offiziell, aber neu — vor dem Gate einmal gegen ein echtes, von der VS-Code-Extension gespeichertes `.drawio.svg` gegenprüfen. Wenn die Extension etwas schreibt, das die XSD ablehnt, wäre das Gate ein Blocker für Handarbeit statt ein Schutz.
- **`--embed-diagram` in der CLI:** Issue #848 ist geschlossen und die Exportdoku listet den Flag, aber ich habe keine Versionsnummer belegen können, ab der er sicher vorhanden ist. Für die Empfehlung ist das folgenlos — der vorgeschlagene Weg braucht die CLI gar nicht.
- **draw.ios „Insert from text"-Baumsyntax** wäre der naheliegende Generierungsweg, layoutet aber laut eigener Doku **nicht** automatisch. Wer sie einplant, plant einen manuellen `Arrange > Layout`-Klick ein.