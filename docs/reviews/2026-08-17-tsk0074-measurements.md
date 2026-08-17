# TSK-0074 / BUG-0046 — wer spricht in dem Strom, den der Nutzer liest

Gegenstand: Pilot-3-Befund **B5** („Fachjargon leckt in die Nutzeransicht, PM kann es nicht
abstellen"). Der Befund trug die Aufteilung „teils Instrument, teils real" **ohne Messung**; AC-2
verlangt genau diese Trennung als Messung. Alles unten ist gegen laufende Software oder gegen die
Rohdaten des Piloten gemessen. Jede Messzahl dieser Runde hat hier ihr Zuhause — mit einer
Ausnahme, die keine Doppelung sein darf: die drei Byte-Differenzen der Lead-Pakete gehören in
`tools/lead_package_sizes.json` und in das Journal in `docs/reviews/phase0-disposition.md`; wo sie
unten auftauchen, sind sie ein Verweis auf diese Stellen, nicht deren zweite Fassung.

Repo `C:/Offline Repos/AgentAndSkills`, Branch `feat/harness-v2`. Die Identität des Pakets, das
ausgeliefert wird — Stempel, Spiegel-Prüfsumme, Byte-Differenzen — steht an genau EINER Stelle:
Abschnitt 9.

## 0. Die Messgeräte

| Was | Wo |
|---|---|
| Rohprotokolle des Piloten (was die Persona zu sehen bekam) | `C:/pilot3-rig/runner/runs/rechnung3-*.jsonl` |
| Ablage des Anbieters für dasselbe Projekt (wer welche Nachricht ablegte) | `C:/Users/zenti/.claude/projects/C--pilot3-rechnung/` |
| Das Relais des Rigs, Zeile für Zeile | `C:/pilot3-rig/runner/persona_run3.py:254-262` (jeder `TextBlock` wird protokolliert) und `:284` (`heard = "\n".join(...)` — **alle** Textblöcke eines Zuges gehen ungefiltert an die Persona) |
| Auswertung, wiederholbar | `docs/reviews/2026-08-17-tsk0074-relay-origin.py` |
| Live-Sonden gegen die Plattform (CLI 2.1.221, SDK 0.2.129, Sonnet) | `C:/tsk0074-probe/probe_relay.py`, `C:/tsk0074-probe/probe_background.py` |

**Die Herkunft wird nicht am Wortlaut entschieden, sondern daran, wohin der Anbieter die Nachricht
gelegt hat**: eigene Sitzung → `<store>/<session>.jsonl`, Subagent → eine Abschrift **unter**
`<store>/<session>/` neben einer `.meta.json` mit ihrem `agentType`. Das ist der Grund, warum diese
Messung nicht in die von `guard_question_context` (R2, `team-kits/dev-team/hooks/guard_question_context.py:65-90`)
dokumentierte Klasse fällt: dort wird Absicht/Vokabular aus Freitext modelliert, und dieser Weg ist
in diesem Repo als Warnung-ohne-Zähne eingestuft, nicht als Entscheidung.

## 1. Die Anteilstabelle (AC-2)

Erzeugt mit

```
python docs/reviews/2026-08-17-tsk0074-relay-origin.py \
  --store "C:/Users/zenti/.claude/projects/C--pilot3-rechnung" \
  --relay C:/pilot3-rig/runner/runs/rechnung3-phase1-20260814-195559.jsonl \
          C:/pilot3-rig/runner/runs/rechnung3-phase2-20260814-200720.jsonl \
          C:/pilot3-rig/runner/runs/rechnung3-phase2-20260814-210935.jsonl \
          C:/pilot3-rig/runner/runs/rechnung3-phase2-20260814-214707.jsonl \
          C:/pilot3-rig/runner/runs/rechnung3-phase2-20260814-222434.jsonl
```

Ganzer Pilot, Assistenten-Textblöcke:

| Sprecher | abgelegt | an die Persona weitergereicht |
|---|---|---|
| die Sitzung selbst (Einstiegsagent bzw. PM) | 124 | 124 |
| `backend-developer` | 113 | 111 |
| `software-architect` | 26 | 21 |
| **Summe** | **263** | **256** |

**51,6 % des Stroms, den die Nutzerin las, waren nicht der PM** (132 von 256). Die sieben nicht
weitergereichten Spezialistenblöcke sind der Schlüssel zum nächsten Abschnitt.

Sitzung 3 — die Sitzung mit den vier Beschwerden (S3 Züge 1, 9, 10, 11):

| Sprecher | abgelegt | weitergereicht |
|---|---|---|
| PM | 34 | 34 |
| `backend-developer` (2 Abschriften) | 33 | 33 |
| `software-architect` | 5 | 5 |

72 Blöcke erreichten die Persona, 38 davon (52,8 %) aus einer Spezialisten-Abschrift. Zuordnung
100 % — kein Block blieb unzugeordnet, keiner mehrdeutig.

**Jeder englische Block in den vier Beschwerdezügen ist Spezialistenherkunft.** Die Sätze, die die
Persona wörtlich zitierte, sind belegt: „My edits … Let me fix with `--fix`" (S3 Zug 9) und
„TSK-0002's status is now `SUBMITTED`" (S3 Zug 10) stehen beide in
`.../f81f6918-.../subagents/agent-a22d318354e871160.jsonl` (`agentType: backend-developer`), nicht
in der Sitzungsabschrift.

## 2. Der Mechanismus — `run_in_background`

Im Piloten selbst liegt ein sauberes Experiment, das niemand geplant hat:

| Sitzung | Beauftragungen | Modus | Spezialistenblöcke abgelegt | davon weitergereicht |
|---|---|---|---|---|
| S2 | 3 `Agent`-Aufrufe | `run_in_background: False` | 7 | **0** |
| S3–S5 | 19 `Agent`-Aufrufe | `run_in_background: True` | 132 | **132** |

(Aufrufe ≠ gestartete Agenten: die Ablage trägt 13 Spezialisten-Abschriften; ein `gate_dispatch`-Block
und doppelt protokollierte Blöcke erklären die Differenz. Von den 7 S2-Blöcken sind 5 sauber — der
Architekten-Zug lief zu Ende —, 2 stammen aus dem Zug, den die Umgebung abschoss.)

Live nachgestellt, heute, gleiche CLI-Version, **ein Flag umgelegt und sonst nichts**:

| Sonde | Modus | Was im Strom der Elternsitzung ankam |
|---|---|---|
| `probe_relay.py`, 3 Läufe | `false` | **kein** `AssistantMessage`-Textblock des Kindes; nur seine `tool_use`/`tool_result`-Nachrichten, jede mit `parent_tool_use_id` |
| `probe_background.py` | `true` | im **Folgezug**: `AssistantMessage parent_tool_use_id=toolu_01BQydjXEv3GHEMvn2GLc9ar ['Now let me check the imports and re-run ruff.']` |

Damit ist die Kette geschlossen: **der Beauftragungsmodus entscheidet, ob die Arbeits-Erzählung
eines Spezialisten in den Strom gerät, den der Nutzer liest.** Das Kit hat diesen Hebel — und
seine Regel („`false`, außer du parallelisierst bewusst") stand bis heute ohne diesen Grund da.

Kosten der Sonden, aus den protokollierten `ResultMessage.total_cost_usd` (kumulativ je Sitzung):
`relay.jsonl` 0,4293 $, `relay2.jsonl` 0,1683 $, `relay3.jsonl` 0,1242 $, `background.jsonl`
0,2408 $ — **zusammen 0,9626 $** (Sonnet, DEC-0027/DEC-0031-Linie).

Zur Wortwahl der Kit-Prosa („**English** work narration"): 116 der 139 Spezialistenblöcke tragen
drei oder mehr englische Funktionswörter; die übrigen sind größtenteils zu kurze englische Sätze
für diese Schwelle, mindestens einer ist deutsch. Der Satz im Kit beschreibt also den Regelfall,
nicht eine Ausnahmslosigkeit — der Punkt der Regel ist ohnehin der Strom, nicht die Sprache.

## 3. Der Kit-Anteil (AC-1)

BUG-0046 nennt als reale Hälfte „mixed German/English jargon **within single PM turns**". Auf der
Ebene einer einzelnen PM-Nachricht ist das im ganzen Piloten **ein** Fall:

- `ccaee232` Block #16: „**Good**, alles gestaged. Jetzt committen:" — 1 von 112 Blöcken der
  Kit-PM-Sitzungen (S2–S5), ein Wort.

Die 12 Blöcke der Sitzung 1 gehören nicht zum Kit: dort ist noch kein Kit installiert, es spricht
der Einstiegsagent unter `user/claude/CLAUDE.md`. Dort steht der zweite Fall, und er ist der
deutlichere: `fd2685ae` Block #3 ist **vollständig englisch** („Initial status for PR is DRAFT,
confirmed. Let me check the required fields …"). `user/**` liegt im `forbidden_scope` dieses
Auftrags — der Fall ist benannt, nicht geschlossen (Abschnitt 7).

Die Mischung, über die sich die Persona beschwerte, ist also eine Mischung **im Zug**, nicht **in
der Nachricht**: zwei Sprecher, nicht ein sprunghafter PM. Genau deshalb konnte der PM sie nicht
abstellen, und genau deshalb war seine ehrliche Antwort („kann ich technisch nicht zuverlässig
garantieren") richtiger als das Versprechen, das er zwei Züge vorher gegeben hatte.

**Die eigentliche Kit-Schuld liegt eine Ebene früher**, und sie ist eine Zusicherung ohne Bau:
die Verfassungen sagten „**PM speaks plain German to the user** — jargon stays between agents".
Die zweite Hälfte ist eine Eigenschaft des Nutzerbildes, die das Kit nicht herstellt. Der PM las
sie als Zusage, gab sie an die Nutzerin weiter (S3, PM-Block #10: „Ich achte darauf, dass dir sowas
möglichst nicht mehr direkt vor die Augen kommt"), beauftragte danach weiter im Hintergrund und
musste zwei Beschwerden später zurücknehmen (PM-Block #30). Eine Beschwerde wurde so zu vier.

## 4. Die Regel, wie sie ausgeliefert war (abgeleitet, nicht erinnert)

| Ort | Was dort steht |
|---|---|
| `team-kits/dev-team/constitution/AGENTS.md:4` · `research:4` · `office:4` | Präambel: Antwort auf Deutsch, Artefakte Englisch — **Paritätsregel 1, `behalten (min-keep)`** (`docs/reviews/phase0-disposition.md:786`) |
| `team-kits/dev-team/agents/project-manager.md:15` · `research:15` · `office/office-manager.md:14` | dieselbe Regel in der Rollen-Frontmatter |
| `team-kits/dev-team/agents/project-manager.md:32` · `research:33` · `office/office-manager.md:45` | „plain, high-level German — NEVER jargon" |
| `team-kits/dev-team/constitution/AGENTS.md:243` · `research:249` · `office:261` | die Verhaltensregel — **hier stand die Zusicherung** |
| `team-kits/gen_provider_artifacts.py:178` und `:190` | dieselbe Regel für die Codex-Artefakte |
| `user/claude/CLAUDE.md:3` | der Einstiegsagent (außerhalb des Auftrags-Scopes) |

Kein einziger Spezialisten-Rollentext nennt eine Sprache (gemessen: `grep -c -i "german\|deutsch"`
über `team-kits/*/agents/*.md` — 2 Treffer nur in den drei Lead-Rollen, 0 in allen 23 anderen). Das
ist kein Defekt: ihre Erzählung ist internes Gespräch. Sie wird erst durch den Modus zum
Nutzerbild.

## 5. Was gebaut wurde

1. **Die Zusicherung ist weg, der gemessene Grund steht da** —
   `team-kits/dev-team/constitution/AGENTS.md:243-247`, `research-team/…:249-253`,
   `office-team/…:261-265` (dieselbe Formulierung, an die Absatzform des Office-Kits angepasst):
   die Pflicht des PM bleibt unangetastet, die Zusage über fremde Stimmen wird durch den Mechanismus
   und die Verhaltensregel ersetzt („nie versprechen, es abzustellen").
2. **Der Preis steht dort, wo der Modus gewählt wird** —
   `team-kits/dev-team/skills/project-manager/SKILL.md:98-103`,
   `research-team/skills/project-manager/SKILL.md:51-56`,
   `office-team/skills/office-manager/SKILL.md:55-60`.
3. **Ein mechanischer Hinweis am Entscheidungspunkt** —
   `team-kits/dev-team/hooks/guard_agent_spawn.py:131-151` (Kommentar; die Entscheidung `:152`, die Notiz `:153-158`) (gespiegelt, byte-identisch in allen drei
   Kits): ein Spawn mit `run_in_background: true` bekommt eine Notiz auf stderr, exit 0. Er liest
   ein **Werkzeug-Eingabefeld** (einen JSON-Boolean), keinen Freitext. Keine Verweigerung — eine
   bewusste Parallel-Charge bleibt erlaubt. Seine Reichweite ist die schwache Sorte (auf PreToolUse
   erreicht nur exit 2 garantiert das Modell; die **Aussage** dazu trägt `guard_question_context`), und
   das steht im Kommentar statt als Schutzbehauptung.

Nicht gebaut, mit Grund: **kein Gate, das Sprache oder Jargon aus Freitext beurteilt.** Das ist die
in der Aufgabe genannte, bekannt verworfene Richtung; die gemessene Referenz dafür ist die
R2-Heuristik in `guard_question_context` (Warnung, nie Block, Nutzerentscheid 2026-07-24) samt
ihrer im Piloten gemessenen Porosität (Befund B14: 2 gefangen, 2 durchgelassen). Ebenfalls
verworfen: eine `systemMessage` beim Sitzungsstart, die der Nutzerin das Geplapper erklärt — im
Terminal unsichtbar, das ist der gemessene blinde Fleck aus BUG-0039.

## 6. Rot ohne den Fix

`tools/test_hooks.py::test_background_spawn_is_told_the_user_sees_it_and_a_foreground_one_is_not`
(Definition `tools/test_hooks.py:804` — in DIESEM Baum nachgezählt; die `def`-Zeile, nicht der
Docstring). Gemessen in einer Kopie **außerhalb** des Repos
(`C:/tsk0074-red/`), zweimal: Runde 1 mit dem ersten Notizblock (1742 Zeichen entfernt), Runde 2
mit dem überarbeiteten (2141 Zeichen entfernt). Beide Male dieselbe Zeile:

```
E   AssertionError: (True, '')
E   assert False is True
C:\tsk0074-red\tools\test_hooks.py:823: AssertionError
```

Mit dem Fix: grün. Der Test prüft **beide** Enden — Hintergrund erzeugt die Notiz, Vordergrund
erzeugt keine —, weil eine Notiz auf jedem Spawn nichts über die Wahl aussagen würde.

Die Prosaänderungen tragen keinen eigenen roten Test; sie bewegen die Sektionspins, und die sind
mit den vorgesehenen Werkzeugen bewegt worden (`pin_constitution_sections.py --write --note`, 6
Sektionen; `record_lead_package_sizes.py --write --note`). Die Byte-Differenzen selbst stehen dort,
wo sie hingehören — in `tools/lead_package_sizes.json` und im Größenjournal von
`docs/reviews/phase0-disposition.md` — und werden hier nicht nachgeschrieben.

## 7. Der Satz für die Instrument-Hälfte

Wo dieser Befund zitiert wird, gehört genau dieser Satz dazu:

> **Die Instrument-Hälfte von B5 ist gemessen und benannt: 132 der 256 Textblöcke, die die
> Pilot-Persona las, stammten aus einer Spezialisten-Abschrift, die der Anbieter getrennt ablegt
> und im Strom mit `parent_tool_use_id` kennzeichnet — das Rig reichte sie ungefiltert weiter
> (`persona_run3.py:284`). Eine eigene Oberfläche, die dieses Feld liest, klappt sie ein; das ist
> FR-0024/BUG-0039 und nicht das Kit. Was dem Kit gehört, ist der Modus: mit
> `run_in_background: false` erreichte kein einziger Spezialistenblock den Strom (S2: 7 abgelegt, 0
> weitergereicht), mit `true` jeder (S3–S5: 132 von 132). Gemessen ist dabei der SDK-Strom — der
> Transport, den Rig und Sonden lesen; was ein Terminal-Client davon einklappt, ist NICHT gemessen
> und wird darum nirgends behauptet.**

## 8. Was offen bleibt, benannt

- **Der Einstiegsagent bricht dieselbe Regel** (`fd2685ae` Block #3, vollständig englisch). Die
  Datei ist `user/claude/CLAUDE.md`, `forbidden_scope` dieses Auftrags. Nicht angefasst, nicht
  geschlossen — Rückgabe an den Lead.
- **Die Unterdrückung selbst ist vom Kit aus nicht schließbar.** Begrenzt wird sie durch zwei
  Dinge, beide gemessen: den Modus (Abschnitt 2) und die Kennzeichnung im Strom, die eine eigene
  Oberfläche auswerten kann (`parent_tool_use_id`, Sonde). Was die **echte CLI** im Terminal
  anzeigt, ist hier **nicht** gemessen — die Sonden messen den SDK-Strom, den auch das Rig las. Die
  Behauptung des Pilotberichts, „die echte CLI klappt Subagenten-Aktivität ein", bleibt damit
  unbelegt; sie ist nicht mein Scope (`docs/pilot/**`).
- **`BUG-0046` behauptet die Mischung „within single PM turns“ — also in der PM-Nachricht.**
  Gemessen ist ein Zwei-Sprecher-Effekt (Abschnitt 3); das ist die eine überzogene Formulierung.
  Der Pilotbericht selbst sagt „im SELBEN Zug“ und meint damit den Zug, nicht die Nachricht — das
  bestätigt meine Messung und wird hier ausdrücklich NICHT als Widerspruch geführt (eine frühere
  Fassung dieses Berichts las ihn falsch). Beide Dateien liegen außerhalb meines Scopes; die
  Korrektur von BUG-0046 ist eine Lead-Entscheidung.
- **Die Notiz feuert nur auf dem Boolean `True`** (`guard_agent_spawn.py:152`, `is True`), während
  die Pflichtprüfung eine Zeile darüber (`:113`) nur die ANWESENHEIT des Feldes erzwingt und den
  Typ nicht verengt. Ein Aufrufer, der `"true"` als Zeichenkette oder `1` schickt, bekommt still
  keine Notiz. Richtung bewusst so gewählt (lieber eine fehlende Notiz als eine erfundene für einen
  Vordergrund-Spawn), im Hookkommentar benannt — und hier für die Löcherliste, weil der Eintrag
  dorthin gehört und `docs/POST_V2_WISHLIST.md` außerhalb meines Scopes liegt.
- **Der Hinweis des Hooks ist ein Hinweis, keine Kontrolle.** Ob er das Modell erreicht, hängt an
  der stderr-Sichtbarkeit auf PreToolUse-exit-0; das ist die schwache Klasse, die dieses Repo
  bereits kennt.

## 9. Der Abschlusslauf

**Das ausgelieferte Paket, einmal und abschließend:** alle drei Kits `2026.08.17-10`
(`bump_kit_version.py`, danach „unchanged"), `guard_agent_spawn.py` in allen drei Kits
byte-identisch, md5 `633ab38e726b2dfc7eabdfd3cf1ca867`. Die Stempel `-8` (Runde 1) und `-9`
(Runde 2) sind überholt und stehen nur noch als Verlauf in Abschnitt 10.

- `python -m ruff check .` → All checks passed.
- `python tools/validate.py` → all structural checks passed (Spiegel eingeschlossen).
- `python -m pytest tools/ -q` → **2795 passed, 13 skipped, 0:33:15, exit 0** (Runde 1) und nach
  der Nacharbeit erneut **2795 passed, 13 skipped, 0:34:01, exit 0** (Runde 2).
- `.claude/hooks/test_gates.py` **hätte laufen müssen**, und meine erste Begründung war falsch: die
  Gates leiten ihren geschützten Bereich aus `team-kits/` und `tools/bump_kit_version.py` ab
  (`.claude/hooks/_harness.py:531-535` und `:744-746`), also liegen Hook-Änderung, VERSION-Stempel,
  Pins und Größenrekord genau auf dieser Fläche — „an `.claude/**` nichts geändert“ ist nicht die
  Frage, die darüber entscheidet. Nachgeholt in dieser Runde (Zahlen unten).
- Nebenwirkung des Suite-Laufs, benannt statt versteckt: zwei Zeilen in
  `project_memory/.audit/hook_events.jsonl` (Kit-Hook-Unterprozesse, die auf die Repo-Wurzel
  zurückfielen). Das ist der bekannte Rest H37/2; `project_memory/**` liegt im `forbidden_scope`,
  also weder rückgängig gemacht noch angefasst. Die Änderung an
  `project_memory/generated/index.yaml` stammt aus der Item-Erfassung des Leads um 12:14:46, nicht
  aus dieser Runde.

## 10. Nacharbeit nach dem Prüfverdikt (Runde 2)

Der Prüfer bestätigte die Messung und verwarf zwei Aussagen. Beide sind hier korrigiert, dazu fünf
Berichts- und Kommentarbefunde.

| Befund | Was falsch war | Was jetzt steht |
|---|---|---|
| **F1** (blockierend) | Die ausgelieferte Prosa behauptete die Nutzerwirkung ohne die Grenze, die dieser Bericht selbst zieht: gemessen ist der **SDK-Transport**, nicht das Terminal. Übertreibung in dieselbe Richtung wie eine Beschwichtigung — der PM hätte vor etwas gewarnt, das der Nutzer vielleicht gar nicht sieht. | Ein Nebensatz in allen sechs Prosastellen, im Hookkommentar (`:135-137`), in der Hook-Notiz selbst (`:153-158`) und im Zitiersatz (Abschnitt 7): „gemessen auf dem SDK-Strom; was ein Terminal-Client davon einklappt, ist es nicht". Die Notiz sagt jetzt „appears in this session's own stream" statt „the user reads" und macht die Ansprache **bedingt** („if the user asks"). |
| **F2** (blockierend) | `2026-08-17-tsk0074-relay-origin.py` schrieb die verworfene Richtung weiter DEC-0029 zu — dieselbe Fehlzuschreibung, die Abschnitt 0 bereits korrigiert hatte. | Im Docstring ersetzt durch die R2-Heuristik in `guard_question_context` plus B14, mit ausdrücklichem Hinweis auf die frühere Fehlzuschreibung. |
| **F3** | Der Hookkommentar sagte, `guard_question_context` „carries that measurement" über die stderr-Reichweite. Es trägt eine **Aussage** über den Plattformvertrag, keine Messung; B14 maß die Trefferquote einer Regex. | „which `guard_question_context` **states** at its top"; die nacherzählte Pilotgeschichte ist auf den Verweis eingedampft, dafür stehen jetzt die Zeiger `BUG-0046` und dieser Bericht im Kommentar (SR-0008). |
| **F4** | Die Sondenkosten waren geschätzt („≈ 1,9 $"); die Behauptung „jede Zahl steht genau einmal, hier" war für die drei Byte-Differenzen falsch. | Kosten aus den protokollierten `total_cost_usd` (Abschnitt 2, **0,9626 $**); der Satz in der Kopfzeile nennt jetzt Rekord und Journal als das Zuhause der Byte-Zahlen. |
| **F5** | Meine Begründung, `test_gates.py` sei nicht nötig, war falsch begründet. | Abschnitt 9 korrigiert und der Lauf nachgeholt: **243 passed** (0:38:10). |
| **F6** | Der Bericht las den Pilotbericht als Fehlbehauptung; der sagt „im SELBEN **Zug**" und wird von der Messung **bestätigt**. | Abschnitt 8 korrigiert: nur `BUG-0046` („within single PM turns") ist die überzogene Formulierung. |
| **F7** | Die neue Verfassungszeile nannte `run_in_background` ohne die „on Claude"-Qualifikation, die dieselbe Datei sonst führt (`:44`, `:141`) — ein Codex-Lead hätte einen Hebel gelesen, den er nicht hat. | „on Claude" in allen drei Verfassungen; die Office-SKILL-Zeile ebenfalls auf „On Claude set …" gebracht. |
| **F8** | Die Stille der Notiz bei `"true"`/`1` stand nur im Hookkommentar. | Zusätzlich in Abschnitt 8 als Restposten für die Löcherliste. |

Rot ohne den Fix, mit dem überarbeiteten Hook erneut gemessen (`C:/tsk0074-red/`, Notizblock von
2141 Zeichen entfernt): dieselbe Zeile, `AssertionError: (True, '')`; mit Fix grün.

Abschlusslauf der Nacharbeit (Runde 2): Stempel und Größenrekord mit den vorgesehenen Werkzeugen
und Begründung nachgezogen (6 Sektionspins), `ruff` sauber, `validate` sauber,
`.claude/hooks/test_gates.py` **243 passed** (0:38:10), `python -m pytest tools/ -q` **2795
passed, 13 skipped** (0:34:01). Die Zahlen des Pakets selbst stehen in Abschnitt 9.

### Runde 3 — der Schliff

| Befund | Was falsch war | Was jetzt steht |
|---|---|---|
| **N1** (blockierend) | Kopfzeile und „Abschlusslauf" nannten weiter die Paket-Identität der
Runde 1, während längst ein anderes Paket auslieferte — genau der Zwei-Stellen-Defekt, gegen den
dieser Bericht argumentiert. | Die Identität steht jetzt an genau einer Stelle (Abschnitt 9),
die Kopfzeile verweist nur noch dorthin, die Byte-Differenzen stehen ausschließlich in Rekord
und Journal, und überholte Stempel sind als Verlauf markiert. |
| **N2** (blockierend) | Abschnitt 5 sagte weiter „die **Messung** dazu trägt
`guard_question_context`", was F3 eine Seite später zurücknahm. | „die **Aussage** dazu". |
| **N3** | Der Hookkommentar zitierte die Notiz falsch („appears in the stream"). | Die
Anführungszeichen sind weg; der Kommentar nennt die Eigenschaft (`:136-137`, nachgezählt: die Notiz benennt
den Strom DIESER Sitzung und macht den Satz an den Nutzer bedingt) statt eines Zitats, das
verrotten kann. |
| **N4** | Die Rot-Messung war nur für Runde 1 belegt. | Abschnitt 6 führt jetzt beide
Messungen. Der Zeiger bleibt `tools/test_hooks.py:804`: die vom Prüfer vorgeschlagene `:802`
stimmt in seinem Baum, in diesem steht dort `_spawn_result`; nachgezählt und deshalb NICHT blind
übernommen. |

Weil N3 eine Kit-Datei berührt, bewegt sich der Kit-Hash: neu gestempelt (die Zahl steht in
Abschnitt 9, nicht hier), Datei gespiegelt, `ruff` und `validate` sauber, Pins und Größenrekord unverändert (ein Kommentar
gehört weder zum Lead-Paket noch zur Pin-Fläche — beide Werkzeuge melden „current").

**Was in Runde 3 gelaufen ist und warum nicht mehr:** geändert wurde ein Kommentar-String, kein
Codepfad — die Entscheidung `:152`, die Notiz `:153-158` und jede andere Anweisung der Datei
sind byteweise dieselben. Gefahren sind deshalb der benannte Spawn-Test (der Kommentar liegt in
seiner Datei) und die Hash-/Versions-Teilmenge, weil der Stempel sich bewegt hat:
`tools/test_kitupdate.py tools/test_presets.py tools/test_context_budget.py
tools/test_shortening_net.py` → **138 passed** (0:02:24), und `tools/test_hooks.py -k
"background_spawn_is_told or version or hash"` → **13 passed**. Der grüne Vollauf aus Runde 2
(2795 passed, 13 skipped) steht damit weiter, weil kein Codepfad ihn ungültig macht.
`test_gates.py` ist nicht nötig: dieselbe Dateimengen-Logik, die den Lauf in Runde 2 verlangte,
sagt hier ab — die Datei liegt zwar auf der Ableitungsfläche, geändert wurde aber nur ihr
Inhalt als Kommentar, und der Prüfer hat diese Begründung für diese Runde ausdrücklich
getragen.
