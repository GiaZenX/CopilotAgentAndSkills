# TSK-0105 — Stream E „texts" (DEC-0057 Generation 2), Protokoll des Umsetzers

Worktree `C:\Offline Repos\v2-testbed\_worktrees\g2-texts` (Branch `g2/texts` ab 6d18407 = Release
2026.09.02-10). Übergabe: `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0105\stream-texts.patch`
(82 007 B, 991 Zeilen, 27 Dateien, `git diff HEAD` nach `git add -N .`) und `git-status.txt` daneben.
Kein Commit, keine Installation, keine volle `tools/`-Suite (DEC-0057 b). Stempel PROVISORISCH:
alle drei Kits `2026.09.02-12` (nach der Nacharbeit; -11 war der erste Stand). Rundenscratch nur unter `_round-scratch/TSK-0105/`.

Wall-clock: erstes Scratch-Artefakt 11:26 (`comment_density.py`), Patch 12:04; die Lesephase davor
(Items, Verfassungen, Rollen, Canyon) ohne Dateispur, geschätzt ~45 min → rund 1 h 25 vom Spawn bis
zu diesem Bericht.

## 1. Was gebaut wurde, je FR

### FR-0069 — Design-Brief (dev-Kit)
* `skills/project-manager/SKILL.md` (a0): das Brief-Verfahren ersetzt die Ambitionsfrage. Erst das
  Repo lesen (Stack, Palette, Typografie, Produktvokabular, bestehende Site = abgeleitete Hälfte,
  nichts davon wird gefragt), dann EIN Frageaufruf mit dem, was keine Datei beantwortet: Ambition,
  was es erreichen soll und für wen, Ton, was es nicht werden darf (+ Referenzen bei Exploration).
  Beide Hälften als EIN Decision-Item, getrennt gehalten. Trennung ZIEL/SCHREIBWEISE: eine
  Prozessregel ist ein `INV`, nie ein Designauftrag — gemessener Fehler (Canyon `DEC-0002` →
  `DEC-0011`) und Kosten des legitimen Wegs stehen im Absatz (DEC-0056 b).
* Verfassung §5a.5: „design BRIEF is the user's own question — the repo is read before it, only what
  no file answers is asked, in ONE call".
* `skills/product-designer/SKILL.md` „Read first": liest den Brief mit beiden Hälften; eine
  Prozessregel, die den Brief erreicht hat, ist ein Befund in `followups`, keine Zeichenanweisung.
  Zeile 148 „design-brief Decision item".
* `skills/frontend-design/SKILL.md` [MOD-1]: liest das Brief-Item (Mark-Liste unverändert,
  `test_every_modification_mark_is_listed_and_every_listed_one_is_marked` grün).
* FORM entschieden: Prosa-Struktur im bestehenden Ambitions-Decision-Item (Option 3 aus FR-0069).
  Grund: kein Kernel-Feld nötig (DEC-0056, Kernel ist Stream F), der Designer liest dieses Item
  heute schon, und ein typisiertes Brief-Item wäre ein zweites Item für dieselbe Entscheidung.
  Ein Frageaufruf trägt vier Punkte (AskUserQuestion erlaubt bis zu vier Fragen je Aufruf).

### FR-0007 — Kommentardisziplin, nutzergeschärft
* EIN Absatz, byte-identisch in allen drei Verfassungen (dev §14, research §14, office §8):
  „**A comment says what the code cannot.**" — Namen und Form sagen das WAS; ein Kommentar trägt
  genau zwei Dinge: ein WARUM, das der Code nicht sagen kann, als Zeiger aufs Item, und eine
  GEMESSENE Grenze; Docstring, der die Signatur wiederholt, ist derselbe Defekt; kein Gate
  (Heuristik über Prosa wird nicht gebaut); wer die Änderung beurteilt, liest jeden geänderten
  Kommentar dagegen. Anlass `FR-0007`.
* Schreibende Rollen, je ein Satz mit Zeiger: backend, frontend, devops (dev); researcher,
  data-analyst, research-engineer (research); office-developer (Schritt 3 umformuliert — „explicit,
  commented aggregation" war das Gegenteil der Regel).
* Prüfende Rollen: QS-Skill Schritt 1 und Reviewer-Skill Schritt 1 „Comments are reviewed like
  code (`FR-0007`)".
* KEINE Obergrenze, kein Ratio-Draht — Begründung aus der Messung (§2).

### FR-0012 — Entscheidung-in-Prosa-Fänger
NICHT in die Kits geschrieben, mit Grund: `staging/FR-0012/ausloeser-geschaerft.md` (mit dem
Nutzer erarbeitet) legt die Reihenfolge fest — „erst hier bauen und messen, ob es trägt; erst dann
entscheiden, ob es in die Kits gehört". Der Prüfer dieses Repos ist `harness-verifier`, dessen
Definition unter `.claude/agents/` liegt = verbotener Bereich. Also NAHTSTELLE, Wortlaut in §6.

### FR-0062 zweite Hälfte — Pflichtsatz in dev und research
Der office-Absatz „**AND BOOK IT**, in the same turn as the sentence to the user: `python
scripts/harness.py report-gap …`" steht jetzt byte-identisch (aus der office-Datei kopiert, nicht
abgetippt) nach dev §2.10 und research §2.10, als eigener Absatz. Der Stolperdraht
`tools/test_gaplog.py::test_the_gap_command_and_the_duty_that_names_it_arrive_together` liest
weiter die INVOKATION (`_CALLS_THE_COMMAND`), jetzt je Kit, und die Dateien je Kit sind abgeleitet
(Verfassung + Agentdatei + Skill des Leads aus `lead_package.lead_role`).

### FR-0057 — QS-Testumfang
* Gemessen (§3): was die QS heute bei einem kleinen Fix-Umfang startet.
* Maß dort, wo es wirkt: QS-`description` (das erste, was ein Spawn sieht) und Reviewer-`description`
  tragen beide Hälften; Reviewer-Skill Schritt 2 bekommt „Scope the runs (DEC-0050)"; Verfassung
  §5a.7 (dev + research) „whose runs are SCOPED — the affected tests while the round is open, the
  full suite ONCE before its verdict (DEC-0050; its role text carries the rule)". Der QS-Skill trug
  Schritt 3 („Staged testing") schon; unverändert.
* Draht: `tools/test_role_contracts.py::test_every_verdict_role_states_the_scope_of_its_runs` —
  Verdict-Rollen aus `gate_subagent_output.VERDICT_ROLES` (AST-gelesen), beide Hälften in
  Beschreibung UND `## Do`.

### FR-0064 — Gedächtnis je Rolle
Entscheidung je Rolle (Canyon-Messung: ~57 Dateien, fünf Rollen):
| Rolle | Kit | Schlüssel | Grund |
|---|---|---|---|
| quality-engineer | dev | ENTFERNT | Urteilsrolle; Canyon-Gedächtnis hielt 11 Themen, 3 davon Gate-Entscheidungen (re-gate-by-baseline-diff, gating-a-live-theme-dev-origin, when-a-static-check-is-green…). Drift NICHT gemessen; die Entscheidung stützt sich auf die Rolle (frische Lesung), nicht auf gemessene Drift |
| reviewer | research | ENTFERNT | dieselbe Rolle (Verdict) |
| bookkeeper | office | ENTFERNT | die zweite Lesung ist ein zweiter Spawn DERSELBEN Rolle; Kanal gemessen offen (§4, H105) |
| records-clerk, filing-reviewer | office | hatten keinen | — |
| backend, frontend, devops, software-architect, PM | dev | BEHALTEN | Umsetzer/Vorschläger, deren Ausgabe eine andere Rolle beurteilt; Canyon: 20/17/3/2 Dateien Werkzeug-Handwerk (Playwright, theme-check, Liquid-Fallen, Kit-Reibung) |
| researcher, methodologist, PM | research | BEHALTEN | dito |
| office-manager | office | BEHALTEN | Lead, erste Lesung ist nie seine |
Pflichtsatz „Consult your agent memory before, update it after." aus QE und Reviewer entfernt;
`test_the_memory_duty_is_only_prescribed_where_the_role_has_memory` bleibt grün (6 Träger, Boden 6).
Draht: `tools/test_role_contracts.py::test_no_role_whose_reading_must_be_fresh_carries_a_craft_memory`
— Rollen abgeleitet aus `VERDICT_ROLES` ∪ jede `writer_role` eines Kernel-Schemas.
Codex: `gen_provider_artifacts.gen_codex_agent` liest `description`, `model`, `effort` und den
`codex:`-Overlay; den Schlüssel `memory` liest es NIE (Zeilen 829–848 gelesen), nur der Pflichtsatz
wird per `MEMORY_DUTY_RX` umgeschrieben. Entfernen ändert für Codex nichts — keine Nahtstelle.

### Spiegel, Ratchets, Stempel
* Rollendateien sind über die Kits NICHT byte-identisch (project-auditor je Kit anders: „PM" vs
  „manager"; md5 gemessen) — „byte-identisch, wo der Text geteilt ist" ist damit die Absatzebene.
  Neuer Draht `tools/test_role_contracts.py::test_a_paragraph_the_constitutions_share_is_one_text`:
  DEFINITION „ein fetter Leitsatz, der in allen drei Verfassungen einen Absatz eröffnet, ist
  geteilter Text" + Ausnahmetabelle `KIT_SPECIFIC_PARAGRAPHS` (fünf Einträge, je mit Grund),
  beide Enden gemessen (toter Eintrag / nicht mehr geteilter Leitsatz). Gemessen vor der Tabelle:
  fünf geteilte Leitsätze, alle fünf verschieden, keiner davon die zwei Absätze dieser Runde.
* Pins: 8 Sektionen CHANGED (dev §2/§5a/§14 + PM-Skill „Work loop"; research §2/§5a/§14;
  office §8), alle reine Ergänzungen; `pin_constitution_sections.py --write` mit Notiz
  (PROVISORISCH), Journalzeilen in `docs/reviews/phase0-disposition.md`.
* Lead-Paket: dev 42760→44667 (+1907), office 50052→51096 (+1044), research 45456→47310 (+1854);
  `record_lead_package_sizes.py --write` mit Notiz (PROVISORISCH).
* `bump_kit_version.py`: 2026.09.02-11 alle drei (PROVISORISCH).

## 2. Messung Kommentardichte (FR-0007) — Canyon_3.4.0, nur lesend

Skript `_round-scratch/TSK-0105/comment_density.py` (Python: tokenize + ast-Docstrings; JS/CSS:
`//` und `/* */`; Liquid: `{% comment %}`, `{% # %}`, `<!-- -->`, `/* */`; Leerzeilen raus).
„Spezialist" = jede Codedatei, die ein Commit nach der Kit-Installation (66fd3ed) berührt hat.

| Gruppe | Dateien | Zeilen | Kommentar | Anteil |
|---|---|---|---|---|
| Spezialist .py (tools/, scripts/quality*) | 21 | 4 276 | 1 190 | **27,8 %** |
| Spezialist .mjs | 9 | 2 239 | 405 | 18,1 % |
| Spezialist .js | 2 | 575 | 167 | 29,0 % |
| Spezialist .css (bpg-brand.css) | 1 | 910 | 315 | **34,6 %** |
| Spezialist .liquid | 43 | 7 000 | 482 | 6,9 % |
| Vendor-Theme .liquid | 248 | 77 051 | 597 | 0,8 % |
| Vendor-Theme .css | 3 | 4 311 | 229 | 5,3 % |
| Vendor-Theme .js | 74 | 16 966 | 4 742 | 28,0 % |
| **Kit-eigener Code** (`.claude/` + `scripts/`) .py | 57 | 27 538 | 12 626 | **45,8 %** |

Befund: in Liquid und CSS schreiben die Spezialisten 6–9× dichter als das Theme, das sie erweitern
(Liquid 6,9 % vs 0,8 %, CSS 34,6 % vs 5,3 %; in JS liegen beide gleichauf, 18–29 % vs 28 %) — und der dichteste Code im ganzen Projekt ist der des Kits selbst
(45,8 %), also das Vorbild, das sie vor sich haben. Stichprobe der Inhalte (`tools/check_faq_literal.py`,
`assets/bpg-brand.css`, `snippets/tax-info.liquid`, `sections/bpg-product-description.liquid`): die
Kopfkommentare sind überwiegend WARUM-mit-Zeiger (DEC/INV/TSK, KNOWN-RED-Grenze) in Kit-Manier,
dazwischen WAS-Wiederholung („Values below are transcribed 1:1 … nothing here is invented",
„Accepts: has_discounts_enabled: {boolean}") und Auftragsprosa. **Warum keine Obergrenze:** die
dichtesten Spezialistendateien sind genau die mit gemessenen Grenzen und Zeigern; ein Ratio kann
Wiederholung nicht von Grenze unterscheiden, und das Kit fiele durch jede Grenze zuerst. Die Regel
bleibt qualitativ, der Träger ist die prüfende Rolle. → Nahtstelle §6 (Kit-Code als Vorbild).

## 3. Messung QS-Umfang (FR-0057) — Canyon_3.4.0

Fall: TSK-0044, Gate-Lauf 2 nach einer Fix-Runde (kleine Änderung: 404-Strings). Einzige Spur ist
das Staging der QS: `staging/TSK-0044/gate_run_log.md` — 15 Instrumentenläufe, davon
`python scripts/quality.py` genau EINMAL, im Hintergrund, 141,63 s (`quality_full_run.txt`, erster
Timing-Block des Projekts); Entwickler-Nachweise `EVD-0028`, `EVD-0033` liefen `quality.py --only
liquid` (betroffener Stack). Also: die QS hält das Maß aus ihrem Skill-Schritt 3 bereits; was
fehlte, war das Maß an der Stelle, die ein Spawn zuerst liest (`description`: „run the tests") und
in der Verfassung am GATE-Schritt. Kein Kernel-Feld und kein Hook sieht den Umfang — H106.

## 4. Messung Gedächtniskanal (FR-0064) — office-Hooks 2026.09.02-10 als echte Prozesse

Wegwerfprojekt `_round-scratch/TSK-0105/memory-channel-proj` (Kit-Hooks, settings.json,
bookkeeper.md kopiert). Payload: `Write`, `agent_type: bookkeeper`, Ziel
`.claude/agent-memory/bookkeeper/amazon-invoice-footer.md`, Inhalt eine Notiz mit den Zahlen EINES
Belegs (302-4471: 214,20 brutto / 180,00 netto / 19 %). Gegen JEDE der sechs auf `Write`
registrierten Stufen der office-settings.json:

```
mit Schlüssel (Stand vor der Runde):  guard_no_adhoc 0 · guard_pm_scope 0 · guard_harness_selfmod 0
                                      gate_write_scope 0 · guard_memory_budget 0 · gate_filing+gate_second_reading 0
ohne Schlüssel (Stand jetzt):         alle sechs rc 0   ← Rest (a) von H105: Schreibseite offen
Rollendatei entfernt:                 gate_write_scope rc 2 (Regel 6 hängt an der Rollendatei, nicht am Schlüssel)
dieselbe Notiz + "booked under TSK-0007": guard_memory_budget rc 2 (wegen der Id, nicht der Zahlen)
```

## 5. Rot zuerst — Klon `_round-scratch/TSK-0105/red-first` (robocopy des Worktrees ohne .git)

`red_first.py`: je Mutation Datei im Klon verändert, Test gefahren, Datei aus dem Worktree
zurückkopiert. Grundlinie ohne Mutation: 5 passed.

| # | Mutation | Test | Ergebnis |
|---|---|---|---|
| M1a | `memory: project` zurück auf dev quality-engineer | …fresh_carries_a_craft_memory | 1 failed |
| M1b | Schlüssel zurück auf office bookkeeper | dito | 1 failed |
| M1c | Pflichtsatz „Consult your agent memory" zurück im Reviewer-Text (ohne Schlüssel) | dito | 1 failed |
| M2a | „affected" aus der QS-`description` gestrichen | …states_the_scope_of_its_runs | 1 failed |
| M2b | Staged-Testing-Satz aus QS-Skill `## Do` geschnitten | dito | 1 failed |
| M2c | Umfangssatz aus Reviewer-Skill geschnitten | dito | 1 failed |
| M3a | ein Wort in der dev-Kopie des Kommentarabsatzes | …share_is_one_text | 1 failed |
| M3b | AND-BOOK-IT-Absatz aus der dev-Verfassung entfernt | …one_text + gaplog …arrive_together | 2 failed |
| M3c | Ausnahme-Leitsatz in research umbenannt (totes-Ende-Draht) | …one_text | 1 failed |
| M3d | research-Kopie des AND-BOOK-IT-Absatzes um ein Wort geändert | …one_text | 1 failed |

Nicht gemessen: das andere Ende der Ausnahmetabelle (ein Eintrag, dessen Absätze identisch
GEWORDEN sind) — dafür müsste ein kit-spezifischer Absatz in drei Kits gleich gemacht werden;
der Zweig ist geschrieben (`identical_exceptions`), sein Rot ist behauptet, nicht gesehen.

## 6. Nahtstellen (nicht in meinem Bereich, wörtlich)

1. **FR-0012 → `.claude/agents/harness-verifier.md`** (Prüferpflicht, fail-open, kein Gate).
   Einzufügen nach „## Attack the FIX, not the original attack" als eigener Abschnitt:
   > ## A decision that landed in prose
   >
   > Mechanical trigger, no judgement in it: a NUMBER or a named threshold that stands in a
   > `docs/` file the round changed AND in something that runs (code, a settings file, a hook
   > table) AND in no active item under `project_memory/`. When it fires, read the paragraph and
   > answer one question — does it bind future behaviour? — and if yes, hand the lead the DEC body
   > (title, context, decision, consequences, source) instead of a remark. Say per paragraph which
   > way you decided; a reader that only nods is the failure this duty exists against. This is a
   > finding, never a refusal, and it covers the class BINDING VALUE only: a binding rule without a
   > number (`DEC-0024`/`DEC-0025` were two) passes it, and that limit is stated here so nobody
   > reads the duty as the whole of `FR-0012`. Occasion: `FR-0012`, two decisions in
   > `docs/pilot/2026-08-09-plan.md` that the user caught and no round did.
   Kits: bewusst NICHT (Reihenfolge aus `staging/FR-0012/ausloeser-geschaerft.md`: erst hier messen).
2. **`gate_write_scope` Regel 6 (Hooks aller drei Kits):** das Gedächtnisfenster öffnet an der
   Existenz von `agents/<role>.md`, nicht am Schlüssel `memory:` — H105 Rest (a). Enger: Regel 6
   liest das Frontmatter mit und öffnet nur für eine Rolle, die den Schlüssel trägt. Test-Docstring
   in `tools/test_hooks.py::test_a_role_writes_its_own_craft_memory_and_only_its_own` (Fall 3)
   müsste die neue Bedingung nennen.
3. **Humanizer-Skill (Stream K):** FR-0069s Nutzerurteil „mit dem Humanizer für UI-Text". Damit
   die UI-Text-Tabelle des Designers ihn bekommt, muss sein `reference_for:` `product-designer`
   und `frontend-developer` für `design`/`ui` nennen (`kernel.references.for_task`, beide
   Achsen). Ich nenne den Skill in keinem Rollentext — ein Name, den nichts prüft, wäre eine
   Behauptung; die Ableitung macht die Nennung überflüssig.
4. **Kit-eigener Code als Vorbild (Kernel/Hooks/Templates):** 45,8 % Kommentaranteil in
   `.claude/` + `scripts/` des Projekts — dichter als alles, was die Spezialisten schreiben. Die
   Regel aus FR-0007 gilt dem Kit selbst zuerst; das ist eine Sichtung dieser Dateien gegen SR-0008,
   kein Textstream.
5. **FR-0040 (Evidence Teillauf/Volllauf):** der einzige Ort, an dem H106 zählbar würde
   (Kernel-Schema-Feld). Nicht von diesem Stream.

## 7. Suiten (DEC-0050-Auswahl nach den geänderten Dateien und den Tests, die sie lesen)

* `tools/test_role_contracts.py` + `test_gaplog.py` + `test_repo_hygiene.py`: 49 passed (36,9 s)
* `test_shortening_net.py` + `test_context_budget.py` + `test_disposition.py` + `test_repo_hygiene.py`:
  95 passed (88 s) — nach Pin/Größen-Aufzeichnung
* `test_reference_skills.py`: 56 passed + 2, die vor dem Stempel rot waren (Installer-Rollback auf
  ungestempeltem Kit) und nach `bump_kit_version.py` grün: 2 passed (318 s)
* `tools/test_hooks.py -k "surface or mirror or constitution or role"`: 27 passed (117 s)
* `.claude/hooks/test_gates.py -k "hole or measurement or reference"`: 8 passed (2×, 131 s / 114 s)
* `python tools/validate.py`: alle Strukturprüfungen bestanden; `python -m ruff check .`: sauber
* Volle `tools/`-Suite: NICHT gefahren (DEC-0057 b, Merge-Runde).

## 8. Löcherliste

H105 (GESCHLOSSEN, mit benanntem Rest: Schreibseite), H106 (Rest, benannt: Umfang eines QS-Laufs
ist Prosa), H107 (Rest, benannt: Brief trennt Ziel/Schreibweise nur als Prosa) — je Mechanismus,
gemessene Kette, Urteil, Tabellenzeile. H105 nennt den Test mit Dateipfad (`tools/…::test_…`), weil
`test_every_test_the_hole_list_names_is_one_that_exists` nackte `test_`-Spannen nur in
`test_gates.py` auflöst.

## 9. Bewusst nicht geschlossen, benannt

* FR-0012 in den Kits (Reihenfolge der Staging-Notiz) — Nahtstelle 1.
* Schreibseite des Gedächtnisfensters (H105 a) — Nahtstelle 2.
* Verdict-Drift durch Gedächtnis NICHT gemessen (kein Kontrollprojekt); die Entscheidung stützt
  sich auf den gemessenen Kanal und die Rolle.
* Ein Zähler für den QS-Umfang (H106) — Kernel, FR-0040.
* Der Provider (lädt er ohne Schlüssel wirklich nichts?) ist hier nur am Frontmatter gemessen.
* Der Kommentarabsatz sagt „No gate holds this rule" — gemessen an den Hooks (kein Hook parst
  Kommentare; `_compat.py:1291` nennt einen Kommentar nur als Prosa-Beispiel). Ein Gate, das
  einmal kommt, macht den Satz falsch; er hängt am Sektions-Pin.

## 10. Nacharbeit nach Prüfer-FAIL (sechs Befunde), 2026-09-02 12:10–12:50

| Befund | Änderung | Messung |
|---|---|---|
| F1 (mittel) | `test_a_paragraph_the_constitutions_share_is_one_text` als DEFINITION: ein fettes Leitwort, das in MINDESTENS ZWEI Verfassungen einen Absatz eröffnet, steht in allen dreien byte-identisch oder mit Grund in `KIT_SPECIFIC_PARAGRAPHS`; fünf Einträge dazu (`A place you name…`, `Presets are MECHANICAL`, `This local constitution is AUTHORITATIVE…`, `Two-level acceptance:`, `User = customer`), je mit Grund; die wachsende Zahl (`>= len(...) + 2`) ist weg; beide Tabellenenden: „nie nötig" = Leitwort in < 2 Dateien, „tot" = in allen drei identisch; Docstring nennt den setdefault-Erstvorkommen-Leser | **m4 des Prüfers rot**: dritter geteilter Absatz in alle drei eingefügt (2 passed), dann FR-0007-Absatz aus office entfernt → 1 failed; Grundlinie 2 passed. Vollsatz rot zuerst erneut: M1a–M3d alle RED, Grundlinie 5 passed. M3c ist unter der neuen Definition „Leitwort in ZWEI Kits umbenannt" (in einem Kit umbenannt bleibt zu Recht grün: zwei Träger sind geteilter Text) |
| F2 (mittel) | EIN Aufruf, VIER Fragen überall: PM-Skill (a0) — Referenzen fahren bei Exploration im Freitext der Ambitionsfrage mit, „a fifth question is more than one call carries"; Designer-Skill Zeile 92 und H107 zählen dieselben vier | `gate_approval.py` misst 2–4 Fragen je Aufruf (Prüfer) |
| F3 (blockierend, Benennung) | H105 Rest (b): Gedächtnisbaum einer früheren Kit-Version bleibt beim Update liegen (Prüfer-grep: kein Installer/Scaffold/Kernel-Pfad nennt `agent-memory`; Canyon trägt 12 Dateien für quality-engineer); Provider-Laden ohne Schlüssel ausdrücklich ungemessen; Urteil geschärft auf „GESCHLOSSEN für NEUE Installationen; für bestehende am Frontmatter abgestellt, am Provider nicht gemessen"; Tabellenzeile gleich; Rollensätze ehrlich in `quality-engineer.md`, `reviewer.md`, `bookkeeper.md`: „No role memory is declared for you … a memory tree an older kit wrote is not removed by an update, whether the platform loads it without the key is unmeasured — if one exists, say so in your envelope"; Test-Docstring nennt denselben Rest | Gate-Suite Löcher-Drähte 8 passed |
| F4 | Protokoll §2: „5–9× dichter" auf Liquid und CSS eingeschränkt; JS liegt gleichauf (18–29 % vs 28 %) | Zahlen unverändert, vom Prüfer reproduziert |
| F5 | Zählung „two verdict roles and three four-eyes writers" + `>= 5` raus; Leere-Prüfung je QUELLE (Verdict-Leser und Schema-Leser müssen je eine ausgelieferte Rolle geliefert haben) | `-k fresh_carries` grün; M1a–M1c rot |
| F6 | QS- und Reviewer-Skill: „the only place a CHANGED comment is judged" | — |

Nahtstelle 6 (neu, für den Lead → `kitupdate`, Stream F hat es nicht im Scope): ein Update, das
einer Rolle den Schlüssel `memory:` nimmt, entfernt ihren vorhandenen Baum unter
`.claude/agent-memory/<role>/` nicht und nennt ihn nicht — Rest (b) von H105; Fix-Form: `kitupdate`
listet solche Bäume in der Pending-Datei oder verschiebt sie in die Sicherung.

Läufe nach der Nacharbeit (Worktree, Stempel -12): role_contracts + gaplog + shortening_net +
context_budget + disposition + repo_hygiene 135 passed (84 s); test_hooks
`-k "surface or mirror or constitution or role or memory"` 57 passed, 1 skipped (143 s); test_gates
`-k "hole or measurement or reference"` 8 passed (145 s); ruff sauber; validate.py bestanden; Pins
1 Sektion neu aufgezeichnet (PM-Skill „Work loop", F2), Paketgrößen unverändert („every size is the
one on record"); Patch neu: 27 Dateien, 87 393 B.
