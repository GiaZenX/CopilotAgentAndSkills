# TSK-0072 (BUG-0047) + TSK-0073 (BUG-0048) — Messungen

Runde 2026-08-17, ein Umsetzer, ein Arbeitsbaum. Beide Items gehören zu **einem** Vertrag: was ein
Spezialist am Ende seines Laufs tun soll und womit. Reihenfolge: **TSK-0073 zuerst**, weil dessen
Entscheidung (wer die Ergebnis-Rückgabe fährt) festlegt, wann ein Spezialist überhaupt noch
existiert — und genau daran hängt TSK-0072s Frage, wann er sein eigenes Memory schreiben darf.
TSK-0072 kam danach und musste deshalb nichts umbauen.

Alle Messungen laufen als **echte Hook-Prozesse** gegen ein mit den ausgelieferten Installern
gebautes Projekt **ausserhalb** dieses Repos (`C:\Temp\harness-tsk0072\`), nicht als Import.

---

## 1. STEP 1 — der gemessene Ausgangszustand

### 1.1 BUG-0047: das Rollenmemory war an **jedem** Punkt gesperrt, nicht erst nach `submit-result`

Scaffold (dev-team, Preset `solo`), `PR-0001` erfasst, `TSK-0001` für `backend-developer` mit
`allowed_scope: src/`, Scope-Approval über den echten `gate_approval`-Hook gemintet, `dispatch`,
`bind_agent`, `spawn_outcome` → `IN_PROGRESS`. Dann ein `Write` auf
`.claude/agent-memory/backend-developer/MEMORY.md` durch **alle fünf** registrierten
`Write`-Hooks des Projekts (aus dessen eigener `.claude/settings.json` gelesen):

| Zeitpunkt | `gate_write_scope` | Begründung im stderr |
|---|---|---|
| während `IN_PROGRESS` | **rc 2** | `'.claude/agent-memory/backend-developer/memory.md' is outside TSK-0001's allowed_scope (src)` |
| nach `submit-result` | **rc 2** | `'.claude/agent-memory/…/memory.md': this subagent is not bound to a task, so it has no write scope at all` |

Die anderen vier (`guard_no_adhoc`, `guard_pm_scope`, `guard_memory_budget`,
`guard_harness_selfmod`) gaben rc 0 — **nur** dieses eine Gate verweigerte. Damit ist der
Löcherlisten-Eintrag L6 in einem Punkt **zu freundlich**: er sagt „sobald `submit-result` gelaufen
ist"; gemessen gibt es gar keinen Moment, in dem die von den Rollentexten vorgeschriebene Pflicht
(„Consult your agent memory before, update it after") erfüllbar wäre. Zwei Mechanismen, kein
Fenster dazwischen.

Der Shell-Weg (`echo … >> .claude/agent-memory/backend-developer/MEMORY.md`) war rc 2 mit der
Begründung *„this command names the enforcement layer … Hooks and settings are maintained by the
scaffold"* — die L6 zu Recht als falschen Grund benennt: `agent-memory/` ist weder Zustand noch
Enforcement-Code.

Die vier Orte des Vertrags, alle vier gemessen statt erinnert:

| Ort | Datei:Zeile (vor der Reparatur) | Befund |
|---|---|---|
| Rollentexte mit der Pflicht | abgeleitet, s. 1.2 | 8 Rollen, 2 davon ohne Memory-Feature |
| Task-Scope-Durchsetzung | `team-kits/dev-team/hooks/gate_write_scope.py:478` (`_assert_in_scope`) | verweigert `agent-memory` als „ausserhalb allowed_scope" |
| unbound-Zweig | `…/gate_write_scope.py:519` | verweigert nach dem Lease-Ende alles |
| `guard_memory_budget` | `team-kits/dev-team/hooks/guard_memory_budget.py:306` (`_check_ids`), `:262` (`_check_size`) | funktioniert — bleibt unverändert (AC-2) |
| Pfadkonvention | `guard_memory_budget.py:75` `MEMORY_DIR = "agent-memory"`, `:254` `_role_base` | einzige Definition, wird jetzt geteilt |

### 1.2 Welche Rollen tragen die Memory-Pflicht — abgeleitet, nicht aufgezählt

Die Pflicht ist **kein** Satz, den dieser Bericht festlegt: `team-kits/gen_provider_artifacts.py`
schreibt sie für Codex um (Codex hat kein Rollenmemory), und dieses Regex ist damit die laufende
Definition von „dieser Text schreibt die Memory-Pflicht vor". Sie steht jetzt als
`gen_provider_artifacts.MEMORY_DUTY_RX` (`team-kits/gen_provider_artifacts.py:680`) statt inline in
`codex_text`.

Über die ausgelieferten Rollendefinitionen abgeleitet: **8 Rollen** tragen die Pflicht
(dev `backend-developer`, `devops-engineer`, `frontend-developer`, `quality-engineer`,
`software-architect`; research `methodologist`, `researcher`, `reviewer`). Davon hatten **zwei**
kein `memory:` in der Frontmatter — `dev-team/devops-engineer` und `research-team/researcher`:
ihnen wurde befohlen, ein Verzeichnis zu konsultieren, das der Provider ihnen nie gibt.

### 1.3 BUG-0048: wer kann den geforderten Befehl überhaupt fahren

Neu abgeleitet (nicht der Vorprüfung des Leads geglaubt), über die ausgelieferte
`tools:`-Frontmatter aller drei Kits gegen die Werkzeuge, die eine Kommandozeile ausführen
(`kernel.dispatch.COMMAND_TOOLS` = `Bash`, `PowerShell`; identisch mit
`gate_write_scope.SHELL_TOOLS` und mit dem `Bash|PowerShell`-Matcher jeder
`settings/settings.json`):

**Ohne Shell — 8 dispatchbare Spezialisten:**
dev-team `product-designer`, `research-engineer`, `software-architect` (bestätigt die Vorprüfung);
research-team `methodologist`; office-team `compliance-researcher`, `marketing-planner`,
`product-editor`, `shop-curator`.

Wo der Vertrag den Befehl **von jeder dispatchten Rolle** verlangte — der eine Ort, der alle
Rollen gleichzeitig anspricht:

| Kit | Datei:Zeile (vorher) | Satz |
|---|---|---|
| dev | `team-kits/dev-team/constitution/AGENTS.md:167` | „A dispatched role therefore CHECKPOINTS — `python scripts/harness.py checkpoint <TSK-ID>`" |
| research | `team-kits/research-team/constitution/AGENTS.md:166` | identisch |
| office | `team-kits/office-team/constitution/AGENTS.md:232` | identisch |

Die **rollen-eigenen** Texte waren dagegen schon sauber: kein `agents/<rolle>.md` und kein
`SKILL.md` einer shell-losen Rolle nennt den Einstiegspunkt (die drei SKILLs, die ihn nennen —
`project-auditor`, `quality-engineer`, `reviewer` — haben alle `Bash`). Ebenso gemessen: der
Einstiegspunkt hatte **keine** Route für ein abgelegtes Envelope (`submit-result` war reine
Flag-Oberfläche, `team-kits/kernel/cli.py:387–403` vorher), also war der gelebte Workaround
„Envelope als Datei + PM tippt ab" nirgends im Vertrag benannt und im Kernel nicht vorgesehen.

---

## 2. STEP 2 — Entscheidungen und was gebaut wurde

### 2.1 TSK-0073: der Vertrag benennt beide Pfade, abgeleitet pro Rolle

**Gabelung:** *nicht* „die submittenden Rollen bekommen die Shell". Grund, gemessen und
dokumentiert: dass der Architekt keine Shell hat, ist Absicht und steht seit Langem als solche im
Code — `gate_write_scope._only_reads_staging` (`team-kits/dev-team/hooks/gate_write_scope.py`,
Docstring): „The architect role has no shell to run the kernel with **by design**: it leaves a
proposal in `staging/<task-id>/` and the lead books it in." Die Shell nachzurüsten hätte acht
Rollen eine Kommandozeile gegeben, um eine Vertragszeile zu retten.

**Gebaut** (ein kohärenter Satz über alle drei Kits, kein Kit-Drift):

1. `kernel/dispatch.py` — `COMMAND_TOOLS`, `HAND_BACK_KEY/SELF/LEAD`, `agents_dir()`,
   `role_tools()`, `hand_back_path()`. Der Pfad wird **pro Rolle aus ihrer eigenen installierten
   Definition** abgeleitet; eine morgen hinzukommende Rolle wird am Tag ihres Erscheinens beurteilt.
2. `create_lease` legt den Wert in die Lease, `dispatch_header` gibt ihn im Header aus — dieselbe
   Bauart wie `checkpoint`, das dort schon mitfährt. Gemessen im Scaffold:
   `HARNESS_DISPATCH {"hand_back": "lead", "lease": …, "root_revision": 1, "task_id": "TSK-0001"}`
   für `software-architect`, `self` für `backend-developer`.
3. `submit-result --from <NAME>` (`team-kits/kernel/cli.py`, `_submitted_envelope`): der
   Spezialist legt das Envelope als **eine** JSON-Datei unter `staging/<TSK-ID>/` ab — der einzige
   Pfad innerhalb des Zustandsverzeichnisses, den `gate_write_scope` einem gebundenen Spezialisten
   lässt — und der Lead nennt die Datei. Der Name geht durch `staging.contained_child`, denselben
   Engpass wie jeder Freeze-Parameter; `--from` zusammen mit einem Inhalts-Flag wird verweigert,
   `task_id` muss übereinstimmen. **Warum das mehr ist als Bequemlichkeit:** ohne diese Route tippt
   der Lead das Envelope aus der Schlussnachricht ab und ist damit Autor eines Datensatzes, den der
   Spezialist geschrieben hat.
4. Verfassungen ×3 (§6): der Absatz „WHO BOOKS THAT ENVELOPE IN…" plus die **Qualifizierung der
   Checkpoint-Pflicht** — sie bindet nur den `self`-Pfad, und für `lead` steht dort, was stattdessen
   gilt (keine Zwischenspeicherung; ein Abbruch wird von vorn wiederholt). Das ist keine neue
   Härte, sondern die ehrliche Fassung des schon vorhandenen Rückfallwegs.
5. Lead-Rollentexte ×3 (`dev/research agents/project-manager.md`, `office agents/office-manager.md`):
   die PM-Hälfte — Envelope mit `--from` einbuchen, nicht abtippen.
6. `templates/repo/scripts/harness.py` (gespiegelt ×3): der Absatz, der „jede Rolle kann für jede
   Aufgabe zurückmelden" als Gefahr beschreibt, benennt jetzt die **eine** sanktionierte Nutzung
   davon.

### 2.2 TSK-0072: ein Fenster, exakt so gross wie das eigene Memory-Verzeichnis

**Gabelung:** Fenster bauen, **nicht** Pflicht streichen. Begründung, gemessen:
`guard_harness_selfmod` nimmt `.claude/agent-memory/**` ausdrücklich von der Enforcement-Sperre aus
(`team-kits/dev-team/hooks/guard_harness_selfmod.py:16`), und `guard_memory_budget` existiert
ausschliesslich, um den Inhalt genau dieser Schreibzugriffe zu begrenzen. Ein Budget auf einem Pfad,
den niemand schreiben darf, ist eine Regel ohne Gegenstand — die Pflicht zu streichen hätte zwei
ausgelieferte Mechanismen gegenstandslos gemacht.

**Gebaut:** `gate_write_scope._own_craft_memory` (Regel 6), drei Bedingungen, alle abgeleitet:

* die **Rolle** ist die, die der Payload nennt (`agent_type`) — vom Provider gesetzt, gemessen in
  `tools/provider_observations.json` (`agent_identity.subagent`: „a SUBAGENT's PreToolUse payload
  carries both fields, non-empty"), und dieselbe Quelle, auf der Regel 4 schon entscheidet;
* die Rolle ist **eine von uns**, geprüft mit dem Prädikat von `gate_subagent_output` (eine
  installierte Definition existiert), wobei der Ort aus `kernel.presets.AGENTS_DIR` kommt;
* das **Verzeichnis** ist `<Providerverzeichnis>/agent-memory/<Rolle>/`, wobei der Verzeichnisname
  aus `guard_memory_budget.MEMORY_DIR` importiert wird — eine Definition, zwei Türen, genau wie
  `guard_pm_scope.production_code` schon importiert wird.

Das Fenster steht **vor und nach** der Rückgabe offen; der allgemeine Task-Scope schliesst nach
`submit-result` unverändert. Der **Shell**-Weg bleibt zu (eine Kommandozeile trägt keine
Rollenidentität, an der man sie festmachen könnte) — aber die Verweigerung nennt jetzt die Tür, die
es gibt (`_CRAFT_MEMORY_HAS_A_DOOR`). Diese Ergänzung ist bewusst als **bedingter Satz** formuliert
und nicht pro Pfad entschieden: ein zweiter Pfadleser in diesem Gate ist genau die Stelle, die hier
wiederholt schiefgegangen ist.

Ausserdem: `memory: project` in `dev-team/agents/devops-engineer.md` und
`research-team/agents/researcher.md` — die zwei Rollen, denen die Pflicht ohne Feature
vorgeschrieben war. **Ehrlich gesagt:** dass der Provider daraufhin wirklich Memory lädt, kann
dieses Repo nicht messen; das gilt für alle vier schon ausgelieferten `memory:`-Zeilen genauso. Was
gemessen ist, ist der Widerspruch, den der Test hält.

### 2.3 Nach den Messungen unverändert (AC-2)

`guard_memory_budget` wurde **nicht angefasst**. Gemessen am selben Pfad, den Regel 6 jetzt öffnet:
eine Item-Id im Memory → rc 2 („references project items (TSK-0001)"), 9 000 Byte → rc 2
(Byte-Budget). Das Fenster erweitert **wer** schreiben darf, nichts daran, **was** landen darf.

---

## 3. STEP 3 — rot ohne den Fix

Alle Roterien in einem Klon **ausserhalb** des Repos (`C:\Temp\harness-tsk0072\clone*`), Defekt
wiederhergestellt, Test gefahren, rot **gesehen**, Klon verworfen.

| Test | Defekt, der wiederhergestellt wurde | Ergebnis |
|---|---|---|
| `tools/test_role_contracts.py::test_the_checkpoint_duty_binds_only_the_roles_that_could_run_it` | der ausgelieferte Satz „A dispatched role therefore CHECKPOINTS" + der `lead`-Rückfall gelöscht | **rot**, 6 Befunde (3 Kits × 2 Hälften), mit den Rollennamen: dev `product-designer, research-engineer, software-architect`, office 4, research `methodologist` |
| `…::test_every_shipped_specialist_is_told_a_path_its_toolset_can_walk` | `python scripts/harness.py submit-result` in den `## Output to the PM`-Block der Architekten-SKILL gepflanzt (genau die Form, die BUG-0048 beschreibt) | **rot**, `dev-team/software-architect: SKILL.md` |
| `…::test_the_command_running_tools_are_one_fact_in_three_places` | `COMMAND_TOOLS = ("Bash",)` | **rot**, `({'bash'}, {'bash','powershell'})` |
| `…::test_the_memory_duty_is_only_prescribed_where_the_role_has_memory` | die zwei `memory: project`-Zeilen aus HEAD zurückgeholt | **rot**, `['dev-team/devops-engineer', 'research-team/researcher']` |
| `tools/test_hooks.py::test_a_role_writes_its_own_craft_memory_and_only_its_own` | A: `gate_write_scope.py` aus HEAD | **rot**, das eigene Memory ist wieder rc 2 |
| dito | B: Regel 6 liest die Rolle aus dem **Pfad** statt aus dem Aufrufer (aufgeweitetes Fenster) | **rot** an der Richtung „fremdes Rollenmemory" — der Test misst also die Enge, nicht nur die Existenz |
| `tools/test_hooks.py::test_a_shell_less_specialists_result_reaches_the_kernel` | A: `dispatch.py` + `cli.py` aus HEAD | **rot** |
| dito | B: nur die zwei Zeilen, die `hand_back` in den Header schreiben | **rot**, `assert None == 'lead'` |
| dito | C: nur `cli.py` aus HEAD (`--from` weg) | **rot**, `assert 2 == 0` (argparse kennt das Flag nicht) |

Jeder Klon war **vor** dem Einbau des Defekts grün — das ist mitgemessen und steht in jedem Lauf
als erste Zeile.

### AC-2 von BUG-0048, Ende zu Ende im Scaffold

`test_a_shell_less_specialists_result_reaches_the_kernel` fährt die Kette in der Reihenfolge, in
der eine Sitzung sie geht: Header sagt `hand_back: lead` → der Spezialist legt sein Envelope ab und
**alle fünf** registrierten `Write`-Gates geben rc 0 → die Zeile
`python scripts/harness.py submit-result --task-id TSK-0001 --from result.json` geht durch **alle
acht** registrierten `Bash`-Gates und läuft dann → `TSK-0001 -> SUBMITTED`, und das gespeicherte
`tasks/results/TSK-0001.envelope.yaml` ist Feld für Feld das Objekt des Spezialisten.

---

## 4. STEP 4 — Auslieferung

* `python tools/bump_kit_version.py` → alle drei Kits **`2026.08.17-7`**.
* `python -m ruff check .` → clean.
* `python tools/validate.py` → „all structural checks passed" (nach dem Anheben des
  Lead-Paket-Rekords, s. u.).
* `python -B -m pytest tools/ -q` → **2794 passed, 13 skipped, 32:02** — EIN Lauf, nach der
  gesamten Nacharbeit einschliesslich §4c. Voll gefahren und nicht eingeschränkt, weil ein
  KIT-HOOK und damit der Bundle-Hash sich bewegt haben und der Versionsstempel mit. (Vorläufer:
  2793/13 in 31:21 nach §4a; 2785/13 in 31:23 vor der Nacharbeit; 2784/13 **plus einem
  Fehlschlag** im allerersten, s. 4.1.)
* Spiegel: `hooks/gate_write_scope.py` und `templates/repo/scripts/harness.py` sind über die drei
  Kits byte-identisch (sha256 geprüft), `KIT_SPECIFIC_HOOKS` brauchte keinen neuen Eintrag.
* **Lead-Paket:** die Verfassungen wachsen um insgesamt **+1731 / +1724 / +1701 Byte** (dev /
  office / research), in drei Schritten: +1275/+1265/+1245 für die beiden Verträge,
  +391/+394/+391 für die drei Korrekturen aus §4a (B3, N2, N6), +65/+65/+65 für N10 aus §4c. Beide Male mit
  `tools/record_lead_package_sizes.py --write --note …` angehoben und mit
  `tools/pin_constitution_sections.py --write --note …` neu gepinnt (9 Sektionen je Durchgang; der
  zweite Durchgang deckt auch `hooks/ENFORCEMENT.md` ab, das der Pin mitführt). Alle vier Notizen
  stehen im Journal von `docs/reviews/phase0-disposition.md`. Die allererste Fassung war
  +2455 Byte/Kit und wurde vor dem ersten Anheben um rund 1 200 Byte pro Kit gekürzt.
* `.claude/hooks/test_gates.py`: **keine Gate-Eingabe dieses Repos verändert** — es wurde nichts
  unter `.claude/**` und nichts an `tools/bump_kit_version.py` oder `kernel.hashing` angefasst.
  Gefahren wurde er trotzdem, und zwar zweimal, weil `.claude/hooks/_harness.py` das Kit-Modul
  `gate_write_scope` IMPORTIERT und dieses jetzt zusätzlich `guard_memory_budget` lädt und aufruft.
  Ergebnis: erst **1 failed, 242 passed** (der vorbestehende H48-Fehlschlag), dann **243 passed**
  — den H48-Eintrag hat in der Zwischenzeit eine andere Hand ergänzt, s. 4.2. Nach §4c noch
  einmal gefahren, weil die Importfläche dieses Pfads (`_harness` → `gate_write_scope` →
  `guard_memory_budget`) sich ein weiteres Mal bewegt hat: **243 passed** (33:49), unverändert.

### 4.1 Ein Defekt, den diese Runde selbst eingebaut und wieder ausgebaut hat

Der **erste** vollständige Suite-Lauf war **nicht** grün: 1 failed, 2784 passed.
`tools/test_migrate.py::test_no_remedy_literal_this_repo_ships_names_a_place_inside_a_state_directory`
meldete `[('team-kits/kernel/cli.py', 646, 'the word', 'staging/%s/'), (…, 677, …)]` — beide aus
den neuen `submit-result`-Verweigerungen. Das ist genau `DEC-0024`: eine Verweigerung, die einen
Ort **innerhalb** des Zustandsverzeichnisses als auszufüllende Stelle hinschreibt, lässt den Leser
den Namen wählen. Beide Sätze benennen jetzt den **Mechanismus** statt des Pfads („die
Staging-Verzeichnis, das die eigene Aufgabe besitzt"), ohne den bekannten blinden Fleck dieses
Tests (Formatierung ausserhalb des Literals) auszunutzen — das wäre Umgehung, nicht Reparatur.

Bei derselben Durchsicht fiel eine zweite Ungenauigkeit auf, die kein Test gefangen hätte: der
`--from`-Hilfetext versprach „(JSON or YAML)", während `_submitted_envelope` ausschliesslich JSON
liest (mit derselben Begründung, die `_json_body` dafür trägt). Der Hilfetext sagt jetzt JSON.

### 4.2 Ein Rotlauf, der NICHT von dieser Runde stammt — und inzwischen von fremder Hand behoben

**Erster Lauf** (vor der Nacharbeit): `python -B -m pytest .claude/hooks/test_gates.py -q` →
**1 failed, 242 passed** (29:04), `test_the_hole_list_judges_every_entry_it_carries`:
`entries with no row: ['H48']`. `H48` wurde von **TSK-0071** (HEAD `0bb2f62`) in
`docs/POST_V2_WISHLIST.md:4184` eingetragen, ohne Zeile in der Urteilstabelle.
`git diff --name-only HEAD -- docs/POST_V2_WISHLIST.md .claude/` war zu diesem Zeitpunkt leer —
der Fehlschlag bestand vor dieser Runde und lag in einem für diesen Auftrag **verbotenen**
Bereich. Gemeldet, nicht repariert.

**Zweiter Lauf** (nach der Nacharbeit): **243 passed**, kein Fehlschlag. Der Grund ist **nicht**
diese Runde: `docs/POST_V2_WISHLIST.md` trägt inzwischen eine Zeile mehr (`git diff --stat HEAD`
= 1 insertion, die H48-Urteilszeile bei `:2114`), geschrieben von **einer anderen Hand** im selben
Arbeitsbaum, während hier gearbeitet wurde. Festgehalten, weil es zwei Dinge bedeutet: der
gemeldete Befund ist erledigt, und dieser Arbeitsbaum hat in dieser Runde **einen zweiten
Schreiber** gehabt — die Zeile stammt nicht von mir und ich habe die Datei nicht angefasst.

---

## 4a. Nacharbeit nach dem Prüferurteil (FAIL, vier blockierende Befunde)

Der Prüfer hat das Paket zurückgewiesen. Was er fand und was daraus wurde — die Zahlen in §4
gelten für den Stand **nach** dieser Nacharbeit.

### B1 (echtes Loch) — Regel 6 war werkzeugblind, `guard_memory_budget` ist formblind

**Der Befund, gemessen vom Prüfer im Scaffold gegen dieselbe Rolle und dieselben ausgelieferten
Werkzeuge** (Ziel `.claude/agent-memory/backend-developer/MEMORY.md`, `agent_type`
`backend-developer`): `Edit` mit **leerem** `old_string` + 200 KB → von allen fünf Gates
**erlaubt**; dasselbe mit Item-Ids → erlaubt; `MultiEdit` mit einem leeren `old_string` → erlaubt;
`Write` **ohne** `content`-Schlüssel → erlaubt; `NotebookEdit` mit 200 KB + Ids → rc 0 durch alle
fünf. Die gewöhnliche Schreibweise jedes einzelnen war korrekt verweigert, und gegen das Gate
**vor** Regel 6 war jede einzelne rc 2. Ursache: `guard_memory_budget._resulting_text`/`_apply`
geben für jede Form, die sie nicht rekonstruieren können, `None` zurück und der Aufrufer lässt
durch — richtig für ein Budget, tödlich, sobald ein zweites Gate dieses Schweigen als Urteil liest.
**Mein Fehler**: Regel 6 hat die Deckung durch den Budget-Wächter *behauptet* statt sie zu
*erfragen*.

**Gebaut** (`guard_memory_budget.judges_this_write`, von `gate_write_scope._own_craft_memory` als
vierte Bedingung gefragt): das Fenster öffnet nur, wenn (a) das zum Pfad passende Budget die
Inhaltsregel überhaupt trägt (`forbid_ids`) und (b) der Inhalt **dieses** Aufrufs modelliert ist.
Beide Gates scheitern damit in dieselbe Richtung. Dazu die eine Stelle im Budget-Wächter, an der
ein fehlender `content`-Schlüssel als leere Datei gelesen wurde — jetzt „nicht modelliert";
**das Urteil des Wächters selbst ändert sich dadurch nicht** (gemessen: rc 0 vorher wie nachher
für beide Formen, `guard_memory_budget` allein).

Gemessen nach dem Fix, alle sechs Formen `REFUSED`, und die legitimen weiterhin `ALLOWED`
(gewöhnlicher `Write`, leerer `content`, gewöhnlicher `Edit`); 200 KB und Item-Ids weiterhin vom
Budget-Wächter verweigert; fremdes Rollenmemory weiterhin vom Gate.

**Nebenwirkung, die N7 miterledigt:** Bedingung (a) schliesst `notes.txt` neben den Topics aus —
dessen Budget (`memory-other`) trägt bewusst keine Inhaltsregel („a pasted fixture may legitimately
contain ids"). Gemessen: `notes.txt` mit `TSK-0001` → **REFUSED**. Die Tabelle wurde dafür
**nicht** angefasst; AC-2 („die Inhaltsregel bleibt") bleibt wörtlich erfüllt, und die
Fensterdefinition heisst jetzt „Craft-Artefakt", was die Verfassung ohnehin sagt.

**Rot ohne den Fix** (Klon ausserhalb): D — `judges_this_write` durch `return True` ersetzt →
`AssertionError: Edit with an empty old_string`; E — der `content`-Leser zurückgedreht →
`AssertionError: Write with no content key`.

**Die zwei falsch gewordenen Sätze** sind mitkorrigiert: `tools/test_hooks.py` behauptete
„the window widens WHO may write and nothing about WHAT may land there" ohne die zweite Hälfte zu
messen (misst sie jetzt), und `gate_write_scope.py` behauptete `guard_memory_budget` polizeiere
den Inhalt „precisely" (steht jetzt als Bedingung im Code statt als Behauptung im Kommentar).

### B2 — `hooks/ENFORCEMENT.md` behauptete in allen drei Kits abgeschafften Schutz

Die `gate_write_scope`-Zeile (dev:24 / research:24 / office:32) sagte „a bound specialist writing
outside its `allowed_scope`, an UNBOUND subagent writing anything" — beide Halbsätze seit Regel 6
falsch. Mein Bericht hatte in §6.4 einen **anderen** Satz derselben Datei geprüft und daraus
„unverändert richtig" geschlossen; das war die falsche Stelle. Die Zeile nennt jetzt die Ausnahme
und ihre zwei Hälften, gepinnt mit `pin_constitution_sections.py --write --note` (der Pin deckt
`hooks/ENFORCEMENT.md` mit ab).

### B3 — „der eine Pfad ausserhalb deines `allowed_scope`" ist falsch

Gegenbeispiel ist §6 dieser Runde selbst: ein gebundener Spezialist schreibt `staging/<eigenes
TSK>/` **und** sein Rollenmemory. Korrigiert an allen vier Stellen: Verfassungen ×3 (nennen jetzt
beide, mit der Innen/Aussen-Unterscheidung), der Gate-Docstring („outside a task scope **and
outside the state directory**") und die drei Zeilen im Grössenjournal von
`docs/reviews/phase0-disposition.md`.

### B4 — die Containment-Behauptung von `--from` hatte keinen rotfähigen Test

Der Prüfer hat gemessen: `contained_child` → `os.path.join` mutiert, **63 Tests grün**, und
`--from ../../../outside.json` bucht ein. Der ausgelieferte Code war richtig, die **Deckung**
fehlte. Gebaut in `tools/test_staging_cli.py`: die Escape-Formen stehen jetzt einmal
(`ESCAPE_SHAPES`, von beiden Batterien gefüttert), eine neue parametrisierte Batterie über
`submit-result --from` mit denselben vier universellen Invarianten plus „die Aufgabe darf sich
nicht bewegt haben", und ein **abgeleiteter Boden**: `_contained_child_callers()` liest per AST
jede Kernel-Funktion, die den Engpass nennt, und verlangt für jede eine Batterie — ein vierter
Aufrufer wird am Tag seines Erscheinens rot. **Rot gemessen** mit derselben Mutation: zwei
Fehlschläge (`--from '../../../preview.html'` bucht ein; der Boden meldet den verschwundenen
Aufrufer).

### Die nicht-blockierenden Befunde

| | Entscheidung |
|---|---|
| **N1** | Der Satz in der Shell-Verweigerung band eine Enge, die den Lead nicht bindet. Er spricht jetzt vom **Subagenten** und nennt die Lead-Ausnahme ausdrücklich. |
| **N2** | „`gate_subagent_output` refuses a stop without it" ersetzt durch das, was der Hook tut: er blockiert einen Stopp, dessen Schlussnachricht kein `summary:` trägt (plus `verdict:` für die zwei Urteilsrollen), einmal pro Zyklus. |
| **N3** | Der Docstring von `staging.contained_child` sagte „every caller today appends a FILE NAME afterwards" — durch meinen neuen Aufrufer überholt. Er sagt jetzt, dass der Satz abgelaufen ist, und nennt die **neue** Messung: `--from '...'`, `'.. '` und `'   '` erreichen `open()` auf dem Staging-**Verzeichnis** und enden dort mit rc 2 (Permission denied), `'..'` mit rc 1 am Engpass — nicht ausnutzbar, aus einem anderen Grund als vorher, und die Bedingung, unter der es eines wird, steht dabei. |
| **N4** | Die acht Rollennamen und die Zahl „acht" sind aus dem Modul-Docstring von `tools/test_role_contracts.py` heraus und stehen nur noch hier im Bericht. |
| **N5** | Gebaut statt benannt: `test_the_lead_of_every_kit_with_a_shell_less_role_carries_the_relay` — für jedes Kit, in dem **irgendeine** Rolle auf `hand_back: lead` auflöst, muss der eigene Lead-Text das Relais nennen, und „das Relais" ist das Flag, das der ausgelieferte Parser wirklich trägt. **Rot gemessen**: Bullet aus allen drei Lead-Texten geschnitten → drei Befunde. |
| **N6** | Ehrlich gemacht statt erzwungen: `--from` ist auch für eine Rolle mit Shell benutzbar, und der Lead darf beides. Die Verfassung sagt jetzt, dass der Header nennt, was das **eigene** Werkzeugset gehen kann, und den Lead in keiner Richtung einschränkt. Erzwingen wäre falsch: der Lead muss ein Envelope auch dann einbuchen können, wenn das Kind abgestürzt ist. |
| **N7** | Durch B1 miterledigt (s. o.), ohne die Budget-Tabelle anzufassen. |

(Der N2-Satz ist in Runde 2 noch einmal korrigiert worden — s. N10 in §4c.)

---

## 4c. Nacharbeit nach dem Prüferurteil, Runde 2

Runde 1 hat der Prüfer vollständig als behoben nachgemessen und meine Zahlen exakt reproduziert.
Ein neuer blockierender Befund, drei billige, einer zum Abwägen.

### B5 (blockierend) — die zwei Gates fragten über **verschiedene Namen**

**Der Mechanismus, nicht zwei Fälle.** `gate_write_scope` löst ein Ziel mit `realpath` auf
(sein eigener Docstring sagt warum: „REALPATH, not abspath"), `guard_memory_budget.main` mit
`abspath`. Regel 6 reichte dem Prädikat den **aufgelösten** Namen, der Wächter urteilte danach über
den **wörtlichen**. Jede Schreibweise, die der eine platt macht und der andere behält, öffnete das
Fenster auf ein Urteil, das nie stattfand.

**Vom Prüfer gemessen**, zwei unabhängige Schreibweisen, echte Prozesse, gebundener
`backend-developer`, alle fünf `Write`-Gates:

| Schreibweise | Gate liest | Wächter liest | Ergebnis vorher |
|---|---|---|---|
| `MEMORY.md::$DATA` (NTFS-Datenstrom) | `memory.md` → `memory-index`, Inhaltsregel AN | `MEMORY.md::$DATA` → `memory-other`, Inhaltsregel AUS | Item-Ids **ALLOWED-BY-ALL**, 200 Zeilen **ALLOWED-BY-ALL** (dieselben Bytes unter dem einfachen Namen: REFUSED) |
| `MYCRAF~1.MAR` (8.3-Kurzname) | die lange `.markdown`-Datei | `MYCRAF~1.MAR` → `memory-other` | **ALLOWED-BY-ALL**, langer Name REFUSED |

**Gebaut:** `guard_memory_budget.guard_relative(root, path)` — **eine** Ableitung, **zwei** Leser
(`main` und `judges_this_write`), und das Prädikat leitet den Namen jetzt selbst ab, statt einen
fremden entgegenzunehmen. `gate_write_scope` übergibt kein `rel` mehr; der Kommentar an der
Aufrufstelle sagt, warum.

**Nachgemessen im Scaffold nach dem Fix** (`measure_b5.py`): `MEMORY.md::$DATA` mit Item-Ids →
**REFUSED**, mit 200 Zeilen → **REFUSED**, in beiden Fällen von `gate_write_scope` (Regel 6 öffnet
nicht, der Schreibzugriff fällt auf die Scope-Prüfung); die Kontrollen unter dem einfachen Namen
weiterhin vom Budget-Wächter verweigert. **Rot ohne den Fix** (Klon ausserhalb, Prädikat wieder mit
dem Namen des Aufrufers gefüttert): `AssertionError: the craft topic under a spelling the two gates
read differently`.

**Ehrliche Grenze dieser Messung:** die 8.3-Hälfte liess sich auf diesem Host **nicht**
reproduzieren — `dir /x` liefert auf diesem Volume keine Kurznamen (8.3-Erzeugung deaktiviert), und
ohne Kurznamen macht auch `realpath` nichts platt. Gemessen ist also **ein** Vertreter der Klasse
(der Datenstrom); der zweite ist auf diesem Host nicht messbar und wird durch dieselbe Ableitung
geschlossen. Der Test trägt die Datenstrom-Richtung und ist so formuliert, dass sie auf einem Host,
auf dem beide Auflösungen übereinstimmen, aus dem anderen Grund verweigert wird — die Zusicherung
ist dieselbe.

**Die getrennte Frage, ausdrücklich entschieden:** ob `main` selbst `realpath` auflösen sollte,
bleibt **offen und wird hier nicht angefasst**. Das würde den Wächter Schreibzugriffe **verweigern**
lassen, die er heute erlaubt — eine Ausweitung einer Inhaltsregel mit eigener
Falsch-positiv-Frage —, und AC-2 hält seine Verhaltensweise fest. Die Folge ist
**Über-Verweigerung**: ein Rollenmemory, das über eine nicht platt gemachte Schreibweise adressiert
wird, fällt aus dem Fenster. Kosten, die eine Rolle melden kann, kein Loch. Steht als Rest unten.

### N8 — ein `old_string`, den die Datei nicht enthält

`_apply` gab dafür den **unveränderten** Text zurück, und `judges_this_write` las das als
„geurteilt". Gemessen: `Edit` mit abwesendem `old_string` + 200 KB / + Item-Ids →
**ALLOWED-BY-ALL**. Jetzt: `None` (nicht modelliert) → **REFUSED**, Kontrolle mit vorhandenem
`old_string` weiterhin **ALLOWED**. **Rot ohne den Fix**: `AssertionError: Edit with an old_string
the file does not contain`.

**Ein Urteil des Wächters bewegt sich dabei doch**, und das sage ich statt es zu verschweigen:
ein `Edit` mit abwesendem `old_string` auf eine Datei, die **schon** Item-Ids enthält, war vorher
rc 2 (die Inhaltsregel sah die Ids im unveränderten Text) und ist jetzt rc 0. Gemessen, beide
Zustände. Bewertung: das war die Verweigerung eines Aufrufs, der **nichts ändert**, an einer Datei,
die ohnehin schon so aussieht — kein Schutz, auf den jemand baut, und die Datei bleibt mit `Write`
reparierbar. Auf der sauberen Datei bleibt rc 0 wie vorher.

### N9 / N10 / N11

| | Entscheidung |
|---|---|
| **N9** | Die Shell-Verweigerung versprach die Tür weiter, als sie nach B1 ist. Sie sagt jetzt dazu: „and there only to the craft topics `guard_memory_budget` judges, so a `notes.txt` beside them is refused through that door too." |
| **N10** | Die **Zahl** ist raus. Der Satz nennt jetzt die Liste des Hooks statt „die zwei Urteilsrollen" und sagt, dass das Kit eine solche Rolle führen kann oder nicht — womit er in `office-team` (das keine der beiden ausliefert) aufhört, falsch zu sein, und keine zweite Heimat für `gate_subagent_output.VERDICT_ROLES` mehr ist. Verfassungen ×3, neu gepinnt, Grössenrekord +65 B/Kit. |
| **N11** | **Symmetrisiert.** Die absolute Form konnte kein Modul-Konstant sein (sie nennt ein pro Lauf erzeugtes Verzeichnis), also stand sie nur an der älteren Batterie; jetzt trägt die gemeinsame Parametrisierung einen Platzhalter, den beide Batterien zur Laufzeit auflösen — die Laufwerksbuchstaben-Klausel von `contained_child` wird damit von **beiden** Aufrufern erreicht. **Ehrlich dazu:** die Ergänzung ist Deckung, keine einzeln rotfähige Richtung — nimmt man die Auflösung wieder heraus, bleibt die Suite grün, weil der Platzhalter dann als gewöhnlicher Nicht-Einzelname verweigert wird. Dass keine EINZELNE Klausel von `contained_child` rotfähig ist, steht schon im Docstring dieser Funktion („EACH HALF ALONE catches all of them"); rot wird sie nur, wenn der Engpass ganz verschwindet, und genau das misst die B4-Mutation. |


### 4b. Zeiger, am Ende neu abgeleitet (Stand nach der Nacharbeit)

| Was | Wo |
|---|---|
| Regel 6, das Fenster | `team-kits/dev-team/hooks/gate_write_scope.py:507` `_own_craft_memory`, angewandt `:611`, vierte Bedingung `:569` |
| die Verweigerung, die die Tür nennt | `…/gate_write_scope.py:497` `_CRAFT_MEMORY_HAS_A_DOOR` |
| das Inhalts-Prädikat | `team-kits/dev-team/hooks/guard_memory_budget.py:299` `judges_this_write` |
| die EINE Namensableitung, zwei Leser | `…/guard_memory_budget.py:266` `guard_relative`, gelesen von `:331` und von `main` `:451` |
| die zwei Formen, die „nicht modelliert" heißen | `…/guard_memory_budget.py:247` `_apply` (leerer und abwesender `old_string`), `content`-Leser in `_resulting_text` |
| Hand-back-Pfad im Kernel | `team-kits/kernel/dispatch.py:81` `COMMAND_TOOLS`, `:91` `HAND_BACK_KEY`, `:279` `agents_dir`, `:292` `role_tools`, `:333` `hand_back_path`; Lease `:258`, Header `:376` |
| `--from` | `team-kits/kernel/cli.py:402` (Parser), `:619` `_submitted_envelope` |
| Containment-Docstring | `team-kits/kernel/staging.py:85` `contained_child` |
| Memory-Pflicht als Definition | `team-kits/gen_provider_artifacts.py` `MEMORY_DUTY_RX` / `MEMORY_FRONTMATTER_KEY` |
| Tests — Rollenverträge | `tools/test_role_contracts.py:303`, `:324`, `:384`, `:421`, `:476` |
| Tests — echte Hook-Prozesse | `tools/test_hooks.py:9989` (E2E), `:10108` (Regel 6, elf Richtungen), Payload-Bauer `:10079` |
| Tests — Containment | `tools/test_staging_cli.py:1132` `ESCAPE_SHAPES`, `:1198` `ABSOLUTE_ESCAPE`, `:1135` `_contained_child_callers`, `:1170` (Boden), `:1202` (Batterie) |

---

## 5. Vorschlag für L6 (`docs/POST_V2_WISHLIST.md` — verbotener Bereich, der Lead trägt ihn ein)

Der Eintrag ist nicht nur zu erledigen, er war auch in einem Punkt **falsch**: die Sperre begann
nicht erst nach `submit-result`. Vorgeschlagene Ersetzung des ganzen Abschnitts:

> ### L6 — Rollenmemory ist vorgeschrieben und gesperrt — **geschlossen am 2026-08-17 (BUG-0047,
> TSK-0072)**
>
> Der Eintrag war zusätzlich in einem Punkt falsch: er nannte `submit-result` als Auslöser.
> Gemessen im Scaffold gegen die projekteigenen Hooks (2026-08-17) war das eigene Memory an
> **jedem** Punkt gesperrt — während `IN_PROGRESS` mit „outside TSK-0001's allowed_scope", danach
> mit „this subagent is not bound to a task". Es gab also kein Fenster, das `submit-result`
> geschlossen hätte, sondern von Anfang an keines.
>
> Geschlossen als **Regel 6** in `gate_write_scope` (`_own_craft_memory`): der Aufrufer schreibt
> `<Providerverzeichnis>/agent-memory/<seine eigene Rolle>/**` und sonst nichts ausserhalb seines
> Task-Scopes — vor und nach der Rückgabe, während der allgemeine Task-Scope danach unverändert
> geschlossen bleibt. Alle drei Bedingungen sind abgeleitet (Payload-`agent_type`,
> `kernel.presets.AGENTS_DIR`, `guard_memory_budget.MEMORY_DIR`).
> `tools/test_hooks.py::test_a_role_writes_its_own_craft_memory_and_only_its_own` hält sechs
> Richtungen, darunter fünf Verweigerungen; ein aufgeweitetes Fenster (Rolle aus dem Pfad statt aus
> dem Aufrufer) wurde in einem Klon rot gemessen.
>
> **Offen bleibt der Shell-Weg, und zwar absichtlich:** `handle_shell` löst keine Rolle auf, also
> könnte ein Fenster dort nur jedes Rollenmemory für jeden Aufrufer öffnen. Die Verweigerung nennt
> seit dieser Runde die Tür, die es gibt (Write/Edit-Werkzeug für einen Subagenten), statt „Hooks
> and settings are maintained by the scaffold" — der falsche Grund, den dieser Eintrag zu Recht
> anmerkte.
>
> **Und offen bleibt eine Nicht-Kongruenz, die beim ersten Anlauf ein echtes Loch war** (vom
> Prüfer gemessen, in derselben Runde geschlossen): das Fenster entscheidet über **Pfad und
> Rolle**, der Inhaltswächter über die **Form des Payloads** — zwei Mengen, die nicht deckungsgleich
> sind. Geschlossen ist das dadurch, dass das Fenster den Wächter fragt, statt ihn anzunehmen
> (`guard_memory_budget.judges_this_write`), also fail-closed in dieselbe Richtung. Was damit
> **verweigert statt gedeckt** ist: jede Payload-Form, die der Wächter nicht rekonstruieren kann
> — ein `Edit` mit leerem `old_string`, ein `NotebookEdit`, ein Codex-`apply_patch` — und jede
> Datei im Memory-Baum, deren Budget keine Inhaltsregel trägt. Ein Rollenmemory als Notebook oder
> über Codex zu pflegen ist damit **nicht möglich**; das ist Über-Verweigerung mit Ansage, kein
> Loch, und die Schliessrichtung wäre, den Inhalt dieser Formen im Wächter zu modellieren
> (`guard_memory_budget.py`, „Modelling notebook content is phase 3").

---

## 6. Was diese Runde bewusst NICHT geschlossen hat

1. **Shell-Schreibzugriff auf das eigene Rollenmemory** bleibt verweigert (s. o.). Begründung im
   Gate; Vorschlag für L6 in Abschnitt 5.
2. **`memory: project` ist nicht messbar.** Dass der Provider daraufhin Rollenmemory lädt, kann
   dieses Repo nicht nachweisen — kein Test hier kann einen Provider dazu bringen. Der Test hält
   nur den Widerspruch (Pflicht ohne Feature), nicht die Wirkung.
3. **Die shell-losen SKILLs benennen den `lead`-Pfad nicht selbst.** Er steht in der Verfassung
   (die jede Rolle lädt) und im Dispatch-Header (den jede Rolle wörtlich erhält); acht SKILL-Kopien
   desselben Satzes wären genau die Duplikation, die hier auseinanderläuft. Der Test verlangt von
   den Rollentexten nur, dass sie **keine** Kommandozeile fordern, die die Rolle nicht fahren kann.
4. **`hooks/ENFORCEMENT.md`:** der Satz „A subagent's own `submit-result`/`evidence` stay open"
   beschreibt, was das Gate erlaubt, und ist für `self`-Rollen weiterhin richtig. **Der Satz, den
   ich hätte prüfen müssen, war ein anderer** — s. B2 in Abschnitt 4a; er ist jetzt korrigiert.
5. **`submit-result` kennt weiterhin keine Aufrufer-Identität.** `--from` fügt keine hinzu: jede
   Rolle konnte schon vorher für jede laufende Aufgabe zurückmelden (der Absatz dazu steht in
   `templates/repo/scripts/harness.py` und bleibt gültig). Was `--from` ändert, ist nur, **wessen
   Bytes** der Kernel speichert.
6. **Der Fall „gebundener Spezialist, dessen Rolle im Payload eine andere ist als
   `assigned_role`"** wird von Regel 6 nach dem Payload entschieden, nicht nach dem Task. Das ist
   Absicht (das Memory gehört der laufenden Rolle, nicht der Aufgabe) und deckt sich mit Regel 4,
   die dieselbe Quelle liest; eine zweite Quelle wäre eine zweite Meinung über eine Identität.
7. **Der LEAD darf weiterhin in JEDES Rollenmemory schreiben** — das war schon vorher so (Regel 2
   trifft ihn nicht) und Regel 6 hat daran nichts geändert; gemessen in derselben Runde. Ob ein
   Lead das Memory eines Spezialisten kuratieren darf, ist eine Produktfrage und keine, die diese
   beiden Items stellen. Benannt, nicht entschieden.
8. **H48 in `docs/POST_V2_WISHLIST.md`** war ein vorbestehender Rotlauf in verbotenem Bereich und
   ist während dieser Runde von fremder Hand ergänzt worden (s. 4.2) — nicht von mir.
9. **Ein Rollenmemory als Notebook oder über Codex ist nicht pflegbar** — Über-Verweigerung aus
   B1, mit Schliessrichtung benannt (s. Abschnitt 5, zweiter Absatz des L6-Vorschlags).
10. **`--from` liest JSON, nicht YAML.** Das gespeicherte Envelope ist YAML (das schreibt der
   Kernel), die Eingabe ist JSON — aus demselben Grund, den `_json_body` nennt: YAML tippt `no` zu
   `false` und `1.10` zu einer Zahl um, und ein `summary` ist in jedem Fall eine Zeichenkette.
   Wer YAML ablegt, bekommt eine Verweigerung mit dieser Begründung, keine stille Umdeutung.

---

*[Lead-Korrekturen 2026-08-17, nach dem PASS der Prüfrunde 3: (1) Die „ehrliche Grenze" in §4c
(8.3-Kurzname „durch dieselbe Ableitung mit geschlossen, aber nicht gemessen") ist ÜBERHOLT — der
Prüfer hat die 8.3-Schreibweise in seinem eigenen Scaffold reproduziert (8.3-Generierung dort
aktiv, `dir /x` zeigte `MYCRAF~1.MAR`) und den Fix dagegen gemessen: `Write MYCRAF~1.MAR` mit
Item-Ids → REFUSED (vorher, Runde 2, dieselbe Datei: ALLOWED-BY-ALL). Beide Vertreter der Klasse
sind damit GEMESSEN zu, nicht nur abgeleitet. (2) Die in §4.2 und §6.8 als „fremde Hand"
verbuchte Änderung an `docs/POST_V2_WISHLIST.md` (H48-Urteilszeile) war der Lead selbst — sein
protokollierter Abschluss-Fix der TSK-0071-Runde, dem Prüfer beider Runden vorab angekündigt.
Korrekt gemeldet, kein Vorfall.]*
