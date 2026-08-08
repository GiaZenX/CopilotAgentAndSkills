# Prüfbericht Runde 2 — `harness.py migrate`

Gemessen 2026-08-04 vom `harness-verifier` gegen den Arbeitsbaum bei HEAD `ae9d37d` (uncommittet),
Kits `2026.08.04-9/-10/-9`. Arbeitskopien außerhalb des Repos; im Repo nur `git status`/`git diff`.
**Verdikt: FAIL.**

Aus Runde 1 geschlossen und sauber gemessen: Teilschreibung mit Beleg, doppelte Legacy-Id, der
positive Gegenbeweis im Freigabetest, `state_fingerprint`, R2/R3-Richtung-1, R6, R8, die drei
Spiegel. Unabhängig bestätigt: Suite `2213 passed, 12 skipped`, ruff sauber, `validate` sauber.

**Der Anker-Angriff landet nicht.** Vier Anker-/Alias-Formen in einem Dokument → alle sechs
Datensätze gemeldet; ein echter YAML-Zyklus terminiert. Grund im Code: der Datensatz wird im
Schleifenkörper des Elterncontainers angehängt, **vor** und unabhängig vom `seen`-geschützten
Abstieg.

---

## B2' — ein drittes Feld wächst mit der Dokumentzahl

`kernel/migrate.py:761-772` baut `decision` mit **einer Zeile pro Quelldokument** und ohne
Kurzform; `:800-802` tauscht nur `context` und `consequences`.

Gemessen (office-Scaffold, 300 V1-Quelldateien mit je einem übersetzbaren Datensatz):

```
run recorded as DEC-0001
receipt=DEC-0001.yaml  bytes=17285  lines=204
[ERROR] DEC-0001: item exceeds budget (17285 bytes / 204 lines; max 12288/200)
```

Knapp über der Grenze (206 Quellen): `bytes=12306 lines=148`, ebenfalls exit 1. Der Fallback
greift — er hilft nur nicht, weil das gewachsene Feld keine Kurzform hat.

Der Docstring `:732-742` behauptet die fehlende Vollständigkeit wörtlich: *„the LONG and the SHORT
form of **every growing part** are built together"*.

Ein reiner **Zeilen**-Riss bei passenden Bytes ist nicht herstellbar (~60 B je Zeile, beide Grenzen
reißen praktisch gleichzeitig). Der Defekt steht über die Byte-Grenze.

**Minimalkorrektur:** `decision` bekommt dieselbe Lang/Kurz-Paarung, und die Bedingung wird nach
dem Tausch **erneut** geprüft, bis `_too_large` `None` sagt.

## B5 — die R3-Reparatur meldet eine Harness-Lücke als Erfolg

`migrate.py:448-463` unterscheidet mit einer einzigen Tatsache: `legacy_type not in v1_types()`.
Gemessen ist `v1_types()` = `{PRD, PROC, SR, TSK}` — **vier**.

Gemessen an einem echten dev-Scaffold (V1-`bugs.yaml`, `change_requests.yaml`, `decisions.yaml`,
`feature_requests.yaml` im Schema der eigenen V1-Templates) und an einem research-Scaffold
(`research_questions.yaml`, `hypotheses.yaml`):

```
ID-SHAPED BUT NOT ITEMS (4) -- read, not imported, not a blocker:
  bugs.yaml BUG-0001: `BUG` is no V1 backlog type -- … so this is a record of some other kind
NOTHING TO DO: no record is translatable in this state.        exit=0
```

Der gedruckte Grund ist unwahr. Mit dem Kernel selbst gemessen:

| Typ | V2-capture-Typ | Zeile in der V1-Tabelle |
|---|---|---|
| BUG, CR, FR, RQ, HYP, EXP | **ja** | nein |
| PROD, ADR | nein | nein |

Für research bleibt damit der **gesamte Backlog außer `tasks.yaml`** still liegen, für dev vier von
acht Artefakten — und der Lauf meldet **exit 0**.

**Minimalkorrektur:** die zweite Tatsache liegt bereits vor — `legacy_type in REQUIRED_FIELDS`
scheidet `PROD`/`ADR` (wirklich kein Item-Typ → melden, überspringen) von den sechs Backlog-Typen
ohne Tabellenzeile (eigener Befund, kein `exit 0`, kein „NOTHING TO DO").

## B6 — `capture_preflight` zur Planzeit macht jede V1-Elternkette unmigrierbar

`migrate.py:495` fragt das Urteil des Schreibers gegen den Zustand **vor** dem Lauf; der Lauf legt
die Eltern aber erst an.

Gemessen (office-Scaffold, PROC-0001 und PROC-0002 mit `derives_from: PROC-0001`):

```
WHAT IT WOULD IMPORT (1)   PROC-0001 -> a new PROC item
BLOCKED (1)                PROC-0002: derives_from PROC-0001 does not exist
exit=1
```

`plan_is_executable` ist False → der Lauf verweigert **wholesale** → PROC-0001 entsteht nie → beim
nächsten Trockenlauf fehlt das Elternteil wieder. **Der Zustand ist stationär.**

`PARENT_FIELDS` deckt `PROC.derives_from`, `SR.derives_from`, `TSK.(product_requirement,
derives_from)`, `HYP/EXP.derives_from`, `BUG.related_pr`, `CR.target_pr`, `FR.related_pr` — die
Elternkette ist die Normalform jedes V1-Stores.

**Minimalkorrektur:** die Vorprüfung gegen den Zustand ausführen, den der Lauf **erreicht haben
wird** (die Ids, die dieser Plan anlegt, als vorhanden mitgeben), oder Bindungsfelder, deren Ziel
derselbe Plan erzeugt, aus der Planzeitprüfung nehmen und in Abhängigkeitsreihenfolge schreiben.
Zu messen sind beide Gegenrichtungen: Ziel **nicht** im Plan (muss weiter blockieren) und Zyklus
(A→B, B→A).

## B7 — der erweiterte Leser akzeptiert einen Schutz, der beweisbar nicht läuft

`tools/test_approvals_dispatch.py:1982-1991` sucht mit `ast.walk(node)` **irgendeinen** Aufruf im
Funktionskörper — ohne Reihenfolge und ohne Erreichbarkeit.

Gemessen gegen das echte `kernel/state.py`:

| Mutation an `capture` | Ergebnis |
|---|---|
| `capture_preflight(...)` **hinter** `_write_yaml_atomic` verschoben | **GREEN — akzeptiert** |
| `capture_preflight(...)` in einen `if False:`-Zweig gelegt | **GREEN — akzeptiert** |
| `_KERNEL_SET`-Wächter aus `capture_preflight` entfernt | RED ✔ |
| Delegation an ein Geschwister, das aus anderem Grund verweigert | RED ✔ |
| zwei Sprünge (`capture` → `_pre_hop` → `capture_preflight`) | GREEN (so gewollt) |

Das widerspricht dem Docstring `:1913` (*„before it writes anything"*) und der Begründung
`:1932-1933` (*„reachable from the writer"*). Erreichbarkeit stellt ein ungeordneter `ast.walk`
nicht fest.

**Minimalkorrektur:** den Aufruf **vor** dem ersten persistierenden Schreiben desselben Körpers
verlangen (Positionsvergleich im AST). Den Satz zurückzunehmen wäre die schlechtere Hälfte — er
beschreibt die Eigenschaft, die gewollt ist.

---

## Restlöcher (nicht rundenblockierend, aber zu schließen)

**R-a** — der Identitäts-Zyklenschutz `migrate.py:221` (`id(node) in seen`), der `_SCAN_DEPTH`
ersetzt hat, hat **keinen roten Test**: Mutation entfernt → `26 passed`.

**R-b** — die Ordinal-Suche `:840-846` ist ungemessen (Rückbau auf Id-Suche → `26 passed`). Ihr
Docstring nennt sie „the second line of the same defence"; niemand misst diese zweite Linie.

**R-c** — ein V1-Datensatz unter einem gepunkteten Pfad wird still verschluckt (gemessen:
`project_memory/.legacy/old_procs.yaml` mit PROC-0099 → **null** Erwähnungen im Trockenlauf),
während der Modulkopf `:32-37` absolut verspricht *„no silent skip"*.

**R-d** — `tools/test_hooks_v2.py:5072` sagt weiterhin *„the V1 `PRD-` prefix, which spec II.2 keeps
alive through `legacy_ids`"* — das Feld, das R6 überall sonst als nie existent korrigiert hat.

**R-e** — `README.md:355-356` schreibt „16 procedures imported, `validate` clean" einem Feldprojekt
auf Kit `2026.07.17-8` zu; `_last_v1_commit()` liefert `33a807e` mit office-`VERSION`
`2026.07.26-6`. Wenn die Zahl aus einem Feldprojekt stammt, gehört das dazugesagt.

**R-f** — `_too_large` unterschätzt um exakt +1 Byte für PROC (Platzhalter `id: DEC-0000`/`status:
VALID` gegen `PROC-0001`/`DRAFT`; Differenz konstant 1 über drei Stichproben). Das 1-Byte-Fenster
wurde **nicht** getroffen — ungemessen, nicht entwarnt.

**R-g** — ein gescheitertes `_write_yaml_atomic` lässt `<ID>.yaml.tmp-<pid>` in
`procedures/active/` liegen; die Datei geht danach in `state_fingerprint` ein.

## Ausdrücklich nicht gemessen

Kein research-Scaffold in Runde 1 (nachgeholt in Runde 2). Codex-Artefakte (`.codex/hooks.json`,
`config.toml`) nie auf `migrate` geprüft. Die Rekursionsgrenze von `scan_document` auf einem
pathologisch tief verschachtelten Dokument ist hergeleitet, nicht gemessen. Die gemeldete
Defektbatterie des Umsetzers (25/25 rot) wurde nicht nachgespielt — stattdessen lief eine eigene
Batterie aus 16 Mutationen.
