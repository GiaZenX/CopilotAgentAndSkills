# TSK-0078 — Messungen (FR-0049 Ablage-Prüfkette, FR-0051 Manager-Pins, zwei TSK-0077-Reste)

Rolle: Umsetzer. Alles hier ist gemessen, nicht erinnert; jede Zahl steht in genau diesem Dokument
und nicht zusätzlich in einem Kommentar. Scratch ausschließlich unter
`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0078\`.

Drei Dateien im Auslieferungsstand zeigen auf dieses Dokument (die drei Verfassungen, §11 bzw. §7);
sie nennen darin genau die Modell-Messung in Abschnitt 2.

---

## 1. FR-0051 — welche Quelle das Modell der VORDERGRUND-Sitzung bestimmt

**Aufbau.** Ein Projekt außerhalb jedes Repos
(`…\TSK-0078\model-pin\`), das nichts enthält außer `.claude/settings.json` mit
`{"agent": "probe-lead"}` und `.claude/agents/probe-lead.md`. Vier Läufe von
`claude -p "Say OK" --output-format stream-json --verbose`, Provider `claude.exe` 2.1.238,
headless. Gelesen wurde `init.model` des Streams und `result.modelUsage` (welches Modell die
Antwort wirklich erzeugt hat); zwischen den Läufen wurde ausschließlich die Frontmatter-Zeile
`model:` verändert.

| Frontmatter `model:` | ausdrückliche Modellwahl | `init.model` | `result.modelUsage` |
|---|---|---|---|
| `haiku` | keine | `claude-haiku-4-5-20251001` | `claude-haiku-4-5-20251001` |
| `opus` | keine | `claude-opus-5` | `claude-opus-5` |
| `fable` | keine | `claude-fable-5` | `claude-fable-5` |
| `opus` | `--model sonnet` | `claude-sonnet-5` | `claude-sonnet-5` |

**Was das entscheidet.** Beide Hälften sind wahr und keine allein: die `model:`-Frontmatter der
GEBUNDENEN Sitzungsrolle bestimmt das Modell der Vordergrund-Sitzung (Zeile 1–3), und eine
ausdrückliche Modellwahl des Nutzers schlägt sie (Zeile 4). Der Pin ist also ein **Default**, kein
Schloss — und `fable` ist auf diesem Host ein auflösbarer Modellname, kein Platzhalter.

**Grenze, ausdrücklich.** Gemessen ist die Flagge `--model` im Headless-Lauf, nicht der interaktive
`/model`-Befehl. Beide sind dieselbe Vorrangfamilie (Nutzerwahl vor Rollen-Default), aber nur die
erste ist hier gemessen. Ebenfalls **nicht** gemessen: ob `effort:` aus der Frontmatter die
Vordergrund-Sitzung steuert — der Stream gibt keinen Effort-Wert aus, an dem man es ablesen könnte.
Die Verfassungstexte behaupten deshalb nur die Modell-Hälfte.

**Gebaut daraus:** `model: fable` in `dev-team/agents/project-manager.md:5` und
`research-team/agents/project-manager.md:5` (effort bleibt `high`); `office-manager` bleibt `lead`
(= opus) / `high`. Die drei Verfassungen sagen beide Hälften; keine behauptet, ein Hook halte den
Pin (keiner tut es).

**Nebenbefund, gemessen an `tools/validate.py`.** Die Prüfung dort war eine Aufzählung
(`("lead", "worker", "light")`) und wies `fable` ab — einen Wert, den `model_tiers.yaml` als
§11-Eskalationspin dokumentiert und `gen_provider_artifacts.provider_model` seit einer echten
Projekt-Map überträgt. Ersetzt durch eine Ableitung aus `model_tiers.yaml`
(`gen_provider_artifacts.provider_neutral_model`); Testrot in Abschnitt 5.

---

## 2. FR-0049 — die Prüfkette, und wo sie auf gebaute Mechanik trifft

**Entwurf (STEP 1), auf der ausgelieferten Mechanik.**

1. Manager → `records-clerk` (Dispatch): öffnet JEDE Datei einzeln, auch in einem Sammelabwurf,
   und schreibt **eine Zeile pro Dokument** nach `project_memory/staging/<TSK-ID>/filing_proposals.yaml`.
   Nichts bewegt sich. Der Clerk hat `Bash`, also `hand_back: self`.
2. Manager → `filing-reviewer` (Dispatch über die Vorschlagsdatei): urteilt pro Dokument
   `accept`/`object`/`partial` mit Begründung, schreibt `filing_verdicts.yaml`. Die Rolle hat
   **kein** kommandofähiges Werkzeug → `kernel.dispatch.hand_back_path` antwortet `lead`, also
   stagt sie ihren Envelope und der MANAGER bucht ihn mit `submit-result --from` ein (TSK-0073/
   BUG-0048-Mechanik, keine zweite Rückgabestrecke erfunden).
3. Manager → Clerk: bewegt genau die `accept`-Einträge. `gate_filing` urteilt wie bisher.
4. Einwände/Unklares → Manager → USER. Der Clerk kann den Nutzer nicht fragen (siehe Abschnitt 4).
5. Neue Dokumentklasse → Name+Ort mit dem Nutzer → `filing_rule`-Freigabe → der KERNEL hängt genau
   die freigegebene Regel an → dann wird abgelegt.

**Warum drei Dispatches und nicht zwei.** „Accepted files move immediately" heißt *ohne auf den
Nutzer zu warten*, nicht *im selben Prozess*: ein abgeschickter Subagent kann nicht auf ein Urteil
warten, das erst nach seinem Ende entsteht. Das ist die einzige Stelle, an der die Form des
Nutzerentwurfs auf die Spawn-Mechanik trifft; die Reihenfolge seiner fünf Schritte bleibt
unverändert.

**Die Verträge liegen in EINER Datei, nicht in zwei Rollentexten:**
`team-kits/kernel/schemas/filing_proposal.yaml` und `filing_verdict.yaml`. Beide tragen
`writer_role:`; `tools/test_role_contracts.py::test_the_pipeline_texts_name_the_fields_their_own_schema_declares`
läuft über jede Schema-Datei, die diesen Schlüssel trägt, und hält den zugehörigen SKILL an die
Feldnamen. Das Vokabular `accept|object|partial` steht ausschließlich im Schema und wird vom
Validator erzwungen (`item_enums`, neu in `kernel/schemas.py`).

**Was hier KEIN Hook ist — und die Selbstkorrektur dazu.** Der erste Satz, den ich an drei Stellen
geschrieben hatte, lautete „kein Hook liest oder validiert eine der beiden Dateien". Gemessen
2026-08-21 gegen alle registrierten Office-Hooks als echte Prozesse
(`…\TSK-0078\yaml-guard2\`, PostToolUse-Payload auf
`project_memory/staging/TSK-0001/filing_proposals.yaml`):

```
wohlgeformt, aber SCHEMA-widrig   jeder Hook rc 0
kaputtes YAML                     guard_yaml_valid rc 2, alle anderen rc 0
```

Also: **einer** liest sie — `guard_yaml_valid` parst jedes `project_memory/**.yaml` nach dem
Schreiben, Staging eingeschlossen — und zwar ausschließlich auf Wohlgeformtheit. Kein Hook prüft
ein Feld des Schemas, kein Gate entscheidet etwas aus dem Inhalt. Die drei Stellen (Schema-Kopf,
`hooks/ENFORCEMENT.md`, Verfassung §2.5) sagen jetzt genau das, und
`tools/test_hooks.py::test_the_only_hook_that_reads_a_staged_pipeline_file_reads_it_for_well_formedness`
misst beide Hälften, damit die Aussage sichtbar verrottet statt still.
Die Wand bleibt `gate_filing`, unverändert, zum Zeitpunkt der Bewegung.

**Modellbesetzung (DEC-0047).** `records-clerk` und `filing-reviewer` laufen auf `worker`/`low`.
Der Clerk fällt damit von `high` auf `low` — das ist die Nutzerentscheidung („reine Auslese"), und
sie trifft **auch** seine Migrations- und Duplikat-Arbeit, die nicht reines Lesen ist. Benannt,
nicht stillschweigend mitgenommen.

---

## 3. Der freigegebene Weg, den Ablageplan wachsen zu lassen

**Warum überhaupt gebaut und nicht als Lücke gemeldet.** `filing_plan.yaml` ist ein Kit-DOKUMENT:
`gate_write_scope` verweigert jeden Werkzeug-Schreibzugriff, und bis zu dieser Runde schrieb es
auch kein Kommando. Die einzige Auskunft war „der Nutzer soll einen Texteditor öffnen" — genau die
Sackgasse, die BUG-0041 für das Preset gemessen hat (der gemeldete Mangel landet bei der Partei,
die ihn nicht schließen kann). Die Mechanik trägt es sauber: `kernel/presets.py` hat die Form
bereits (`DOCUMENT_WRITES` + `layout.partial_writers` + Freigabe + Rückprüfung), und die
Zeilen-Freigabekinder lesen ihre Flaggen aus der Signatur des Manifest-Bauers.

**Gemessen, gegen die ausgelieferten Hooks, in `…\TSK-0078\rule-gate\`:**

```
vor der Regel   mv inbox/rechnung.pdf archive/1-Finanzen/Eingangsrechnungen/2026/…   gate_filing rc 2
                ("filing_plan.yaml lists no rules yet")
Frage           request-approval filing_rule …  → die Frage, die der Nutzer unterschreibt:
                „Freigabe erbeten: filing_rule für eine neue Regel im Ablageplan (FP-003):
                 invoice, credit_note werden ab jetzt unter »archive/1-Finanzen/Eingangsrechnungen/<Jahr>«
                 abgelegt und nach dem Muster »YYYY-MM-DD_<Lieferant>_Rechnung« benannt,
                 Aufbewahrung: 8 Jahre … die Freigabe FÜGT diese eine Regel HINZU, ändert keine
                 bestehende und legt selbst kein Dokument ab, und sie gilt nur bis …"
nach dem Mint   add-filing-rule …                                                    rc 0
dieselbe Zeile  mv … archive/1-Finanzen/Eingangsrechnungen/2026/…                    gate_filing rc 0
erfundener Ort  mv … archive/erfunden/x.pdf                                          gate_filing rc 2
zweiter Lauf    add-filing-rule … (dieselbe, noch lebende Freigabe)                   rc 1
                („already carries a rule with the id 'FP-003'")
ohne Freigabe   add-filing-rule …                                                     rc 1, Datei unverändert
```

Der Plan behält dabei alle Kommentare (Feldliste, Platzhalter-Syntax, Aufbewahrungs-Defaults):
geschrieben wird per Zeilen-Edit, danach wird die Datei **zurückgelesen und geparst** und die
angehängte Regel Feld für Feld mit der freigegebenen verglichen; bei jeder Abweichung werden die
alten Bytes zurückgeschrieben und der Befehl verweigert.

**Die Verweigerung nennt den Weg von selbst.** `gate_write_scope` baut ihre Meldung aus
`kernel.layout.partial_writers`; ohne eine Zeile Gate-Code zu ändern steht dort jetzt
(gemessen, `…\TSK-0078\scope-project\`):

> The one exception is not this write: `python scripts/harness.py add-filing-rule` owns rules in it
> -- and that command asks the USER first.

`gate_filing`s eigene zwei Verweigerungen nennen den Weg über `gate_filing.growth_route`, die
`kernel.filing` nach Kind und Kommando FRAGT statt eine Kopie der Namen zu tragen.

---

## 4. Ein Nebenbefund, gemessen an Frontmatter gegen Text

`records-clerk.md` trug (Auslieferungsstand) für die FR-0050-Korrekturtür: „Relay the printed
question VERBATIM with **AskUserQuestion**". Die Frontmatter dieser Rolle gewährt
`Read, Grep, Glob, Bash, Edit, Write` — kein Fragewerkzeug. Die Antwort eines Subagenten erreicht
den MANAGER, nie den Nutzer; die Anweisung war also auf keinem Weg befolgbar, und §5 derselben
Verfassung sagt von der anderen Seite, dass der Manager die einzige kundenseitige Rolle ist.

Korrigiert: der Clerk gibt die gedruckte Frage **wörtlich an den Manager**. Der neue Test ist eine
Ableitung (Fragewerkzeug = der Matcher, auf dem das Kit `guard_question_context` registriert;
Gewährung = die `tools:`-Frontmatter der Rolle), kein Namensverzeichnis.

---

## 5. Rot ohne den Fix — jede Messung in einer Kopie AUSSERHALB des Repos

Kopie: `…\TSK-0078\red-clone\` (nur `team-kits/` und `tools/`; Treiber
`…\TSK-0078\run_red.py`, Defekte in `…\TSK-0078\mutate.py`). Jeweils ein Defekt
wiederhergestellt, Suite-Auswahl gefahren, danach zurückgesetzt.

| Wiederhergestellter Defekt | Datei | rot |
|---|---|---|
| `_filing.py` im Stand vor dieser Runde | `office-team/hooks/_filing.py` | `test_the_door_reads_a_stream_redirect_as_the_one_word_it_is` (4 Fälle) + `test_a_both_streams_redirect_names_the_file_it_writes` — 5 failed |
| `_DOCUMENT_WRITER_MODULES = ("presets",)` | `kernel/layout.py` | `test_every_kernel_module_that_writes_into_a_document_is_registered`, `test_the_office_document_refusal_names_the_command_that_owns_a_field_of_it` — 2 failed |
| Freigabeprüfung vor dem Schreiben entfernt | `kernel/filing.py` | `test_a_filing_rule_is_written_only_when_the_user_approved_exactly_it` — 1 failed |
| Zeilen-Edit durch YAML-Round-Trip ersetzt | `kernel/filing.py` | `test_appending_a_rule_keeps_everything_else_in_the_plan` (+1) — 2 failed |
| Rückprüfung nach dem Schreiben entfernt | `kernel/filing.py` | `test_a_write_that_does_not_produce_the_approved_rule_is_rolled_back` — 1 failed |
| Anhängen tut gar nichts | `kernel/filing.py` | u. a. `test_a_rule_the_user_approved_opens_this_gate_for_exactly_that_place` — 4 failed |
| `growth_route` nennt keinen Weg | `office-team/hooks/gate_filing.py` | `test_the_refusal_that_blocks_a_filing_names_the_route_that_grows_the_plan` — 1 failed |
| Clerk-Satz „…with AskUserQuestion" zurück | `office-team/agents/records-clerk.md` | `test_no_role_text_names_a_user_question_tool_its_own_definition_denies` — 1 Befund |
| Reviewer-SKILL Schritt 6 ohne Feldnamen | `office-team/skills/filing-reviewer/SKILL.md` | `test_the_pipeline_texts_name_the_fields_their_own_schema_declares` — 1 Befund |

Der Defekt **`rule_from` verfälscht** (`id` + "-typo") ging NICHT rot — richtig so und hier
festgehalten, weil es die Falle benennt: Schreiber und Rückprüfung leiten beide aus derselben
Funktion ab, also macht ein Fehler IN ihr beide einig. Deshalb misst
`…_is_rolled_back` stattdessen den RENDERER, der ein Feld verliert.

Zum N2-Rest zusätzlich die direkte Messung am laufenden Hook (vor dem Fix,
`…\TSK-0078\door-before2\`, lebende `filing_correction`-Freigabe):

```
mv archive/1-Finanzen/2026/x.pdf outbox/x.pdf          rc 0
mv archive/1-Finanzen/2026/x.pdf outbox/x.pdf 2>&1     rc 2
   „an invocation this guard does not read as a filing operation (1)"
```

Nach dem Fix (`…\TSK-0078\door-after\`): `2>&1`, `>&2`, `2>&-` je rc 0;
`>&inbox/b.pdf` weiter rc 2 (Umleitung in ein Fach von Rang);
`2>/dev/null` weiter rc 2 (Ziel außerhalb des Projekts — die bekannte Über-Verweigerung V6,
unverändert).

---

## 6. Was diese Runde NICHT geschlossen hat (benannt, nicht verschwiegen)

- **`filing-reviewer` steht nicht in `gate_subagent_output.VERDICT_ROLES`** (dort:
  `quality-engineer`, `reviewer`). Bewusst: das dortige `verdict:` ist ein PASS/FAIL über eine
  AUFGABE, die Urteile dieser Rolle sind pro Dokument und liegen in ihrer Verdikt-Datei. Die Liste
  ist über alle drei Kits gespiegelt; ein Eintrag dort wäre eine Änderung an dev und research für
  eine office-Rolle.
- **Keine Maschine liest die beiden Staging-Artefakte.** Ein Vorschlag, den niemand geprüft hat,
  erreicht `gate_filing` genau wie jede andere Bewegung. Ein Gate dafür wäre eine neue Wand für
  jedes Office-Projekt und nicht die Eigenschaft dieser Runde; die Rollentexte, das Schema und
  ENFORCEMENT.md sagen es an allen drei Stellen so.
- **`business_profile.yaml` trägt weiterhin keine Adresse, wenn der Nutzer keine einträgt.** Der
  neue Schlüssel `business.billing_address` ist OPTIONAL: für ein Einzelunternehmen ist das die
  Privatadresse, und die Datei liegt für immer in git (der Kopf der Vorlage nennt den Fall, in dem
  das schon einmal passiert ist). Ist er leer, prüft der Reviewer den NAMEN und schreibt pro
  Dokument dazu, dass die Adresse nicht geprüft wurde. Das ist die eine Stelle, an der der
  Nutzerentwurf („recipient name+address match business_profile") nur zur Hälfte gebaut ist —
  gebaut ist der Vergleich, nicht die Pflicht, den Wert zu hinterlegen.
- **`kernel/filing.py` hängt nur AN.** Eine bestehende Regel zu ändern oder zu entfernen kann einen
  ganzen Archivzweig verwaisen lassen; das ist eine Migration (PROC mit Trockenlauf), kein
  Einzeiler, und der Befehl verweigert es.
- **`>&<Datei>` in `_redirect_targets_in`** war vor dieser Runde für JEDEN Leser unsichtbar
  (gemessen: `echo x >&archive/…/y.pdf` erreichte `gate_filing` als gar nichts). Das ist jetzt
  geschlossen — aufgeführt, weil es eine Erweiterung über den Auftrag hinaus ist und der Prüfer
  wissen soll, dass sie gemessen wurde und nicht nur behauptet ist.
- **`docs/POST_V2_WISHLIST.md` ist verbotener Bereich für diese Runde**, deshalb steht keine dieser
  Zeilen dort. Wer sie in die Löcherliste heben will, findet hier Mechanismus und Kette.

---

## 6a. NACHARBEIT nach dem Prüfer-Urteil (FAIL, vier Blocker)

Alle vier geschlossen, jeder mit einer Messung und einem Test, der ohne den Fix rot wird
(Ablationen in `…\TSK-0078\mutate.py`, Treiber `run_red.py`, Klon `red-clone`).

### B1 — Briefing und `doctor` verweigerten den Weg, den diese Runde gebaut hat

Gemessen gegen ein frisches Scaffold: das SessionStart-Briefing nannte `add-filing-rule` nicht und
sagte weiter „no `python scripts/harness.py` command writes it. Filling it is the USER's to do";
`doctor` druckte `kernel_writer: null` daneben. Das ist BUG-0041s Form — und es traf **auch**
`project_config.yaml`, dessen `project.preset` `set-preset` seit BUG-0041 besitzt: der Test
`test_doctor_names_the_documents_that_wall_a_project_off` PINNTE `is None` und hielt damit das
Werkzeug auf der Sackgasse fest.

Gebaut, als **eine** Ableitung an drei Stellen (`kernel.layout.partial_writers`, dieselbe, die
`gate_write_scope` fragt): `_kernel.partial_write_routes` + `_route_clause` (gespiegelt ×3),
`report.doctor` (`kernel_writer` und die Notiz), `registry.yaml` (Ableitung statt „One single
FIELD is the exception"), und beide Tests fragen jetzt `partial_writers` statt einer Konstante.
Beide Richtungen: ein Dokument MIT Schreiber muss ihn nennen, eines ohne darf keinen behaupten.

Rot ohne den Fix: `doctor_route` → 1 failed · `briefing_route` → 1 failed.

### B2 — ein `path_template`, das mit einem Platzhalter BEGINNT, riss die Wand ganz auf

```
vorher (Klon):  request-approval rc 0 → add-filing-rule rc 0 → gate_filing auf archive/erfunden: rc 0
nachher (Repo): request-approval rc 2 (an der Frage abgelehnt) → gate_filing: rc 2
```

Als **Definition** geschlossen, nicht als Muster: das erste Segment trägt kein `<` und kein `>`.
Damit wird der Kernel kein zweiter Leser der Platzhalter-Syntax — über ein Segment, das keines von
beiden enthält, sind sich alle Lesarten einig — und er muss weiterhin nicht wissen, welcher Ordner
das Archiv ist. Was NICHT geprüft wird, steht dabei: ob das literale erste Segment das Ablagefach
ist. Eine Regel mit anderem Wurzelordner passt auf nichts — eine unbrauchbare Regel, keine offene
Wand.

Rot ohne den Fix: `wildcard_root` → 4 failed. (Beim ersten Lauf **grün** — da hatte ich die Regel
gebaut und keinen Test dazu; genau das hat die Ablation gezeigt.)

### B3 — der Schema-Kopf behauptete eine Durchsetzung, die niemand aufruft

`kernel.schemas.validate` wird im ausgelieferten Baum für `filing_verdict` **nirgends** gerufen; ein
wohlgeformtes, schema-widriges Verdikt passiert jeden registrierten Office-Hook mit rc 0. Der Satz
sagt jetzt beides getrennt: die Rollentexte hält `tools/test_role_contracts.py` an das Vokabular,
`validate` weist ein viertes Wort ab **wenn es gefragt wird**, und zur Laufzeit fragt es niemand.
Der `item_enums`-Zweig hat jetzt eigene Tests in `tools/test_schemas.py` (beide Richtungen: jedes
deklarierte Wort geht durch, jedes andere nicht).

Rot ohne den Fix: `item_enums` → 1 failed.

### B4 — die Rückprüfung verglich gegen sich selbst

`written[0] != rule_from(manifest)` — Schreiber und Prüfer waren dieselbe Funktion, also blieb die
Ablation „`rule_from` hängt `-typo` an die Id" grün, während der Plan eine Regel bekam, die niemand
unterschrieben hat. Jetzt gibt es `RULE_FIELDS` (eine Tabelle, zwei Leser): `rule_from` BAUT daraus,
`signed_rule` LIEST die Manifest-Werte roh, und `apply` vergleicht gegen `signed_rule`. Der Satz im
Modulkopf ist damit wahr statt absolut behauptet.

Rot ohne den Fix: `self_check` → 1 failed · `rule_typo` (die Ablation des Prüfers) → 4 failed.

### Reste

- **N1** `filing.RULE_ID_RX` war tot und schon auseinandergedriftet (`{1,31}` gegen `{0,31}`) —
  gelöscht; die Id-Form lebt nur noch in `approvals.RULE_ID_RX`, und `RULE_FIELDS` sagt im Kommentar
  warum hier keine zweite Antwort steht.
- **N2** „six rule fields" → die Zahl ist weg; eine Regel hat die Felder, die `RULE_FIELDS` nennt.
- **N3 — ausdrückliche Abweichung vom `allowed_scope` des Items.** `README.md` liegt NICHT in
  `team-kits/**`, `tools/**`, `docs/reviews/**`. Ich habe es geändert (eine Zeile: `add-filing-rule`
  in die Kommandoflächen-Liste), weil `test_every_span_that_presents_the_command_surface_names_all_of_it`
  sonst rot bleibt — der Tripwire verlangt, dass JEDER Block, der die Fläche aufzählt, sie ganz
  aufzählt, und README.md ist einer davon. Inhaltlich richtig, im Bereich falsch: der Lead nimmt es
  ab oder nimmt es zurück.
- **N4 — gemessen entschieden.** `settings.json` sagte `"model": "opus"`, während die Frontmatter
  `fable` sagt. Gemessen (viertes Probe-Paar, Provider 2.1.238): `"model": "fable"` in
  `settings.json` löst auf `claude-fable-5` auf und die Sitzung läuft. Deshalb steht in dev/research
  jetzt `fable` — dieselbe Sprosse wie die gebundene Rolle, also **eine** Antwort statt zweier;
  office bleibt `opus`, weil das dort schon die Antwort der gebundenen Rolle ist. Der `_comment`
  aller drei Dateien trägt jetzt die Rangfolge mit ihrer Messung. Der Rückfall greift ohnehin nur
  für Rollen ohne eigenes `model:`, und `tools/validate.py` lässt keine solche Rolle ausliefern.
- **N5 — offen, benannt:** eine vom Kernel angehängte Regel trägt nie `required_metadata`,
  `collision_policy` oder `examples`, und kein Weg fügt sie später hinzu. Grund: was der Nutzer
  nicht gesehen hat, schreibt der Befehl nicht. Folge: solche Regeln sind ärmer als
  handgeschriebene, und die Verfahrensdoku rendert entsprechend weniger. Vorschlag für die
  Löcherliste (ich darf sie nicht schreiben): entweder die drei Felder in die Freigabefrage
  aufnehmen oder einen zweiten, ebenso engen Befehl für sie.
- **N6 — offen, benannt:** die Naht Verdikt → Bewegung ist Verfahrensprosa. Nichts hindert den
  Manager daran, die Verdikte zu paraphrasieren, statt genau die `accept`-Einträge weiterzugeben;
  `gate_filing` prüft danach nur noch das Ziel gegen den Plan, nicht, ob dieses Dokument geprüft
  wurde. Vorschlag: ein Gate, das eine Bewegung aus `inbox/` gegen ein Verdikt in `staging/`
  verlangt — eine neue Wand für jedes Office-Projekt, also eine Entscheidung des Nutzers.
- **N7 — benannt und jetzt ausgesprochen:** `add-filing-rule` steht in keiner der beiden Mengen, mit
  denen `gate_write_scope` einem Subagenten Befehle verweigert. Ein Spezialist kann ihn also fahren.
  Harmlos, weil die Freigabe die Regel bindet und kein Befehl prägt — aber unausgesprochen war es
  eine Erlaubnis, die niemand abgewogen hat; sie steht jetzt in `hooks/ENFORCEMENT.md`.

## 7. Abschluss — gemessen, nicht behauptet

| Schritt | Ergebnis |
|---|---|
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |
| `python -m pytest tools/ -q` | **2927 passed, 13 skipped, 0 failed** (27:31) |
| `python -B -m pytest .claude/hooks/test_gates.py -q` | **243 passed** (13:26) |
| Stempel | dev `2026.08.21-6` · office `2026.08.21-7` · research `2026.08.21-6` |

(Die Zahlen sind die des Laufs NACH der Nacharbeit aus §6a; der Lauf davor war 2915/13/0.)

Der erste vollständige Lauf dieser Runde war **6 failed, 2908 passed** — jeder der sechs Befunde
war ein Stolperdraht, der genau seine Sache tat, und keiner davon war ein Testfehler:

1. `test_board.py::test_no_kernel_writer_of_a_rendered_file_leaves_the_board_behind` — ein neuer
   Kernel-Schreiber, der weder Index noch Board neu baut, muss mit seinem Grund eingetragen werden
   (`filing.apply` schreibt ein Kit-Dokument, für das es keine Karte gibt).
2. `test_hooks.py::test_instruction_files_name_only_state_files_a_v2_project_has` — die beiden
   Schema-Dateinamen sind KEIN Projektzustand; sie stehen jetzt mit Grund in
   `STATE_FILES_NOT_SHIPPED`.
3. `test_hooks.py::test_every_span_that_presents_the_command_surface_names_all_of_it` — vier Texte
   zählen die Kommandofläche auf und mussten `add-filing-rule` mitnennen; zwei weitere Blöcke
   (`kernel/cli.py`, `office-team/hooks/ENFORCEMENT.md`) rutschten durch je EINE neue Nennung über
   die Schwelle von drei und nennen den Befehl jetzt als volle Aufrufzeile statt als bloßes Wort.
4. `test_migrate.py::test_no_remedy_literal_this_repo_ships_names_a_place_inside_a_state_directory`
   — mein Beispielpfad in einer Verweigerung nannte einen Ort im Zustandsverzeichnis (DEC-0024);
   die Verweigerung zeigt jetzt auf die Beispiele des Ablageplans statt eigene zu erfinden.
5. `test_presets.py::test_every_target_form_names_a_live_apr_kind` — eine neue lesbare
   Freigabe-Frage darf nur mit ihrer eigenen Messung ankommen.
6. `test_staging_cli.py::test_cli_request_approval_offers_exactly_the_kinds_a_manifest_builder_exists_for`
   — die generische Sonde reicht jedem Bauer `"x"`; meine Regel-Id-Mindestlänge von zwei Zeichen war
   eine willkürliche Schranke und ist weg.

Danach ein zweiter vollständiger Lauf, grün, mit den Zahlen oben. Zwischen den beiden Läufen wurden
Kit-Dateien geändert, also erneut `record_lead_package_sizes.py --write --note`,
`pin_constitution_sections.py --write --note` und `bump_kit_version.py` — die erste Fassung war
sonst am eigenen Stempel gescheitert (`write_kit_state`: „does not hash to the `content:` in its
own VERSION"), was `test_presets.py::test_a_lead_can_change_the_preset_end_to_end` mit dem echten
Scaffold gemessen hat.
