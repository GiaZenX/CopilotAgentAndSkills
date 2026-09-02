# TSK-0104 — Merge-Runde des DEC-0057-Piloten: Protokoll

**Baum:** `c:\Offline Repos\AgentAndSkills`, Zweig `feat/harness-v2`, Basis `c155a5f` (Haupt-Baum,
kein Worktree). **Kein Commit, kein Push, keine Installation in den globalen Store.**
**Scratch:** ausschließlich `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0104\`.

**Wanduhr:** Start `2026-09-02T01:50:04+0200`, Ende `2026-09-02T04:12+0200` — **2 h 22 min**.
**66 Dateien geändert** (+8 855/−246) gegenüber `c155a5f`, `project_memory/` ausgenommen.

**Anwendungsreihenfolge (DEC-0057 e):** B → A → C → D, je einzeln mit `git apply --3way`, und nach
JEDEM Patch die Pin-/Ratschen-Tests (`test_shortening_net.py` + `test_context_budget.py`) — der
Grund steht in Seam-Notiz 16: Strom C hatte genau diese Suite in seiner DEC-0050-Auswahl vergessen,
obwohl er gepinnte Dateien änderte.

---

## 1. Konfliktprotokoll

| Patch | Dateien mit Konflikt | Konflikt-Hunks | davon Inhaltsentscheidung |
|---|---|---|---|
| **B** `stream-rollout.patch` | **0** | 0 | 0 |
| **A** `stream-design.patch` | 4 | 4 | 1 |
| **C** `stream-office.patch` | 6 | 8 | 5 |
| **D** `stream-research.patch` | 4 | 4 | 3 |
| **Summe** | **14** | **16** | **9** |

**Wie jeder aufgelöst wurde — nie durch Fallenlassen einer Seite:**

* **Die drei `team-kits/*/VERSION` (7 Hunks, A/C/D).** Keine Seite ist richtig: der vereinigte Baum
  hat einen dritten Inhaltshash (DEC-0057, „was Worktrees nicht lösen", Punkt 1). Aufgelöst auf den
  jeweils NEUEREN Stempel (`2026.09.02-1`) als Zwischenstand; der Stempel der Runde entsteht am
  Ende aus `tools/bump_kit_version.py` und überschreibt beide Seiten (§7). **Keine
  Inhaltsentscheidung**, sondern eine, die der Stempler ohnehin ersetzt.
* **`docs/POST_V2_WISHLIST.md` (3 Hunks, A/C/D) — Inhaltsentscheidung.** Alle Ströme hängen
  Einträge ans Ende an, also kollidiert jeder mit jedem. Aufgelöst nach **H-Nummer**, nicht nach
  Patch-Reihenfolge: H83–H85 (A) vor H86–H88 (B), dann H89–H91 (C), dann H92–H95 (D) **vor** H99
  (C) — D musste zwischen C's Blöcke eingesetzt werden, ein reines Anhängen hätte die Liste
  unsortiert gelassen. Skripte:
  `_round-scratch/TSK-0104/resolve_wishlist_A.py`, `resolve_append_only.py`, `resolve_wishlist_D.py`.
  Jedes prüft seine Anker und bricht ab, statt still nichts zu tun.
* **`docs/reviews/phase0-disposition.md` (4 Hunks, C/D) — Inhaltsentscheidung.** Beide Journale
  (Verfassungs-Pins, Lead-Paket-Größen) sagen in ihrem eigenen Kopf, dass sie **append-only** sind.
  Beide Seiten bleiben, in der Reihenfolge ours→theirs, was hier zugleich die chronologische ist.
* **`tools/lead_package_sizes.json` (2 Hunks, C/D) — Inhaltsentscheidung, je Kit.** Jeder Strom hat
  die zwei Kits, die er nicht anfasste, auf seinem Ausgangswert stehen lassen. Genommen wurde je
  Kit der Wert des Stroms, der es geändert hat: dev 42 751 (A), office 49 353 (C), research 45 402
  (D). Danach ist der Rekord für JEDES Kit exakt die Messung des vereinigten Baums — nachgewiesen
  dadurch, dass `test_context_budget` (Gleichheit, nicht Deckel) nach dem D-Patch grün blieb.
* **`tools/constitution_section_pins.json`** hat trotz Änderung durch A, C und D **nicht**
  konfligiert: die Datei ist nach Kit geschachtelt, und die drei Ströme schrieben in verschiedene
  Kits. Nachgeprüft, nicht angenommen (alle drei Kit-Schlüssel vorhanden, Pin-Test grün).

**Seam-Notiz 11 (CRLF-Risiko) ist nicht eingetreten, und das ist gemessen:**
`team-kits/dev-team/skills/project-manager/SKILL.md` trägt bei `c155a5f` **0** CRLF im Blob und
**0** im Arbeitsbaum; der A-Patch lief sauber durch. Der Prüfer von A hat vermutlich seine eigene
Kopie gemessen. Dafür trägt eine ANDERE Datei CRLF — siehe §5 (2).

---

## 2. Nahtarbeit 1 — `kernel/cli.py`: vier neue Verben plus die Verfassungspflicht

### `report-gap` (C) + der Pflichtsatz — als EIN Paket

Verdrahtet genau wie in TSK-0102 §2 vorgegeben (Import, Subparser, Dispatch), und der
Verfassungssatz in `team-kits/office-team/constitution/AGENTS.md` §8 liegt in derselben Änderung.
C's Stolperdraht `test_the_gap_command_and_the_duty_that_names_it_arrive_together` ist grün.

**Und er musste ein zweites Mal repariert werden — der Prüfer hat es an der Naht gemessen.** Sein
Pflicht-Ende las jede **NENNUNG** von `report-gap` in den office-Texten. Dieselbe Merge-Runde hat
den Namen aber in die §0-Kommandoflächen-Liste derselben Verfassung eingetragen, und die hält
`test_hooks.py::test_every_span_that_presents_the_command_surface_names_all_of_it` aus dem Parser
**vollständig** — also folgte „genannt" ab sofort aus „verdrahtet", und die Zusicherung war ein
Theorem. Gemessen: die ganze Pflicht-Passage aus der Verfassung entfernt → **1 passed**.
**Gebaut:** das Pflicht-Ende liest jetzt einen **AUFRUF** (`_CALLS_THE_COMMAND`: der Einstiegspunkt
unmittelbar vor dem Verb), nicht einen Namen. Eine Flächenliste NENNT ein Kommando; nur ein Text,
der die Aufrufzeile buchstabiert, SCHICKT jemanden hin — und die Pflicht ist die zweite Sorte.
Rot zuerst in beiden Richtungen: M6a und M6b in §6.

**An dem Draht selbst musste ich etwas ändern, und es ist ein Hausregel-2-Fall:** er las `cli.py`
als **Zeichenkette** (`"gaplog.COMMAND" in cli`). Ein Kommentar, der den Namen nennt, hätte ihn
genauso befriedigt wie ein Subparser. Er fragt jetzt `cli.build_parser()` — die Fläche, die
`--help` druckt und auf der argparse verteilt. **Gemessen** (Mutation M7): eine `cli.py` vom
Merge-Basisstand plus ein Kommentar `# a comment that merely names gaplog.COMMAND` → der neue
Leser meldet `wired: False` und wird **rot**; der alte hätte `True` gemeldet und wäre grün geblieben.

### `pin-kit` / `unpin-kit` / `rollback-kit` (B, H87)

**Sie drucken und handeln nicht.** Das ist die Entscheidung dieser Runde und keine halbe Umsetzung;
sie hat einen Grund, der als **Eigenschaft** formuliert ist und nicht als drei Fälle:

> Eine Sitzung darf einen Hebel ziehen, der nur Verweigerung **hinzufügt**, nie einen, der sie
> **wegnimmt**.

* Einen Pin zu LÖSEN nimmt weg — er ist das Einzige, was zwischen dieser Sitzung und einer
  ersetzten Durchsetzungsschicht steht. Ein `unpin-kit`, das löscht, wäre genau der Zustand, den
  `kitupdate.PIN_FILE`s Kopfkommentar ausschließt („a pin is the user's statement and not a
  role's") — ein Kommentar, der Schutz behauptet, den der Code dann nicht mehr baute.
* Ein Rollback ersetzt die Durchsetzungsschicht wie ein Update; `update-kit` darf das nur auf eine
  geprägte Freigabe, und **keine Freigabeart deckt einen Rollback**. Eine neue Art wäre ein
  Eingriff in `approvals.APR_KINDS`, die Schemata und alle drei Verfassungen — Gerüst über dem Haus
  (DEC-0056) und keine Merge-Arbeit.
* Einen Pin zu SETZEN fügt nur hinzu. Trotzdem druckt auch `pin-kit` nur: die Datei ist die Aussage
  des Nutzers, und derselbe Kommentar trüge sie sonst nicht mehr.

Was die drei liefern, ist genau das, was H87 als fehlend benannte („Bequemlichkeit und eine frühere
Ansage"): der Pfad der Pin-Datei mit den zwei Zeilen **dieses** Projekts, die Pin-Datei zum Löschen
mit dem Wortlaut des vorhandenen Pins, und die Sicherung mit der Installer-Zeile, die sie
zurückspielt (`kitupdate.restorable`, schon vorhanden). Ein gepinntes Projekt sagt `rollback-kit`
außerdem, dass der Pin auch den Rollback stoppt — vor dem Start des Installers, wo die vorhandene
Verweigerung erst danach greift.

---

## 3. Nahtarbeit 2 — `session_status.py`: ein gepinntes Projekt hört vom Pin

Die **Ableitung** liegt in `_kernel.kit_update_verdict` (gespiegelt, byte-identisch über alle drei
Kits — nachgeprüft per Hash), der **Wortlaut** in jedem `session_status.py` (steht als
kit-spezifisch in `KIT_SPECIFIC_HOOKS`, drei verschiedene Dateien seit jeher).

Neues, fünftes Verdikt `pinned`. Es trifft genau **einen** der vier Sätze — den einzigen, der den
Nutzer um ein OK bittet; die anderen drei sagen ohnehin „nicht installieren". Der Nag wird **nicht**
stummgeschaltet (das wäre `BUG-0078`s Markerklasse): dieselbe Tatsache kommt einen Schritt früher,
mit dem Wortlaut des Pins.

Gemessen am ausgelieferten Haken **als Prozess**, über alle drei Kits:
`tools/test_kitupdate.py::test_a_pinned_project_hears_about_its_pin_instead_of_an_offer` — und der
Test hält **beide** Enden: der Vergleich der beiden Stempel muss weiter dastehen, sonst wäre die
Reparatur eine Stummschaltung.

---

## 4. Nahtarbeit 3–6

### 3. `gen_provider_artifacts.py` — der Codex-Spiegel (A/F2, H83)

Neuer Gegenstand des Spiegels: `native_skill_sources(repo)` = **jedes unmittelbare Kind von
`.claude/skills/` mit einer `SKILL.md`**. Das ist dieselbe Definition, nach der beide Provider ein
Skill erkennen, und dieselbe, die der Generator schon für seine `missing_skills`-Prüfung benutzt —
also eine Definition statt einer Liste, und ein morgen dazukommendes Referenz-Skill ist am Tag
seiner Auslieferung gedeckt. **Ausdrücklich mit erfasst und im Docstring benannt:** ein Bündel, das
der NUTZER dort ausgepackt hat (`FR-0045` lädt dazu ein) — die gewollte Richtung, denn die
Alternative wäre, dass die beiden Provider verschiedene Skills sehen.

A's AST-Test wurde wie vorhergesagt rot und ist auf die neue Wahrheit umgeschrieben:
`test_the_codex_mirror_is_generated_per_skill_directory`. **Dabei ist Seam-Notiz 12 geschlossen:**
der Leser nahm einen Aufzähler nach dem NAMEN `listdir` aus, also wäre eine dritte Spiegelstelle,
buchstäblich als `for x in os.listdir(<skills>)` geschrieben, überall grün durchgegangen. Er trennt
jetzt nach der **umgebenden Funktion** — `legacy_owned_outputs` ist die Inventur der
Vorgängerausgabe, alles andere produziert —, und die Ausnahme ist an **beiden** Enden gehalten:
jede produzierende Stelle muss die eine Ableitung laufen, UND die Inventur muss weiterhin eine
Spiegelstelle enthalten, sonst entschuldigte die Ausnahme eine Funktion, die mit dem Spiegel nichts
mehr zu tun hat.

Die drei Sätze, die A auf „auf Codex gibt es keine native Kopie" korrigiert hatte, sagen jetzt
wieder das Gegenteil (Verfassung §1a, `frontend-design/SKILL.md`, `webapp-testing/SKILL.md`). Dass
ein Satz in EINER Runde zweimal umgeschrieben werden musste, steht so in H83 — es ist der Preis
dafür, die Aussage und nicht nur ihre Grundlage zu pflegen.

### 4. `scaffold_team.sh` + `.ps1` — der Preset-Schnitt (A/H83)

Beide Zwillinge überspringen ein Skill-Verzeichnis nur noch, wenn das Kit für seinen Namen eine
`agents/<name>.md` ausliefert **und** das Preset diese Rolle nicht führt. Die Frage „ist dieser
Name eine Rolle" geht an das `agents/`-Verzeichnis des Kits, nicht an eine Liste.

Gemessen am **echten** Installer in beiden Zwillingen über die Presets `team`, `duo`, `solo`, je in
einem **frischen** Projekt, und in beide Richtungen (jedes rollenlose Skill kommt überall an; ein
Rollen-Skill außerhalb des Presets weiterhin nicht). H83 behält A's Urteil „stille Abwesenheit
einer Fähigkeit, kein hängender Zeiger" — der Absatz mit der Messung steht unverändert im Eintrag —
und ist als GESCHLOSSEN mit einem benannten Rest fortgeschrieben (das subtraktive Entfernen läuft
weiter über die Rollen-Liste).

### 5. `README.md` — Kommandofläche (B/S3)

Die Liste in Zeile 331 ff. trägt die vier neuen Verben; zwei neue Absätze erklären Pin und Rollback
in Nutzersprache. `test_every_span_that_presents_the_command_surface_names_all_of_it` bleibt grün —
dafür mussten auch die §0-Listen **aller drei Verfassungen** die vier Namen aufnehmen (der Test
verlangt von einer präsentierenden Spanne Vollständigkeit).

**Eine gemessene Kleinigkeit, die daraus folgte:** die Gegenrichtung
(`test_every_command_a_role_is_handed_is_on_the_entry_points_surface`) liest nur
`<INVOCATION> <wort>`-Zeilen, keine bloßen Namen in Backticks. Unter Mutation M1 (cli.py auf dem
Basisstand) war sie für `unpin-kit` und `report-gap` rot, für `pin-kit` und `rollback-kit` aber
still. Deshalb nennen die README-Absätze die drei Kommandos jetzt als volle Befehlszeilen —
danach sind **alle vier** Verben in beiden Richtungen gehalten (nachgemessen, §5 Punkt 6).

### 6. Die Übersichtstabelle der Löcherliste

Fünfzehn fehlende Zeilen ergänzt: **H82** (die Auslassung, die TSK-0099 begann) bis **H95** und
**H99**. H96–H98 sind reservierte, unbenutzte Nummern (B); H100/H101 existieren nicht (C hat H101
nach Messung ausdrücklich nicht eingetragen).

**Damit das nicht wieder driftet, ist es jetzt gebaut statt versprochen:**
`tools/test_repo_hygiene.py::test_every_hole_has_a_row_in_the_summary_and_every_row_has_a_hole`
leitet beide Mengen aus dem Dokument ab (jede `### H<n>`-Überschrift, jede erste Tabellenzelle, die
H-Nummern trägt) und hält sie in beiden Richtungen.

**Die D-Klausel** in `report_lint.py` („so no cut separates them") war an ihren eigenen Zahlen
widerlegt — 70 gegen 88 und 220, jede Grenze zwischen 71 und 87 trennt sie. Ersetzt durch das
allgemeine Argument: ein echtes Tag hat **keine** Länge (die Attributliste ist unbegrenzt), also
ist jede Zahl hier auf einen Baum gepasst und tauscht beim ersten längeren echten Tag einen stillen
Fehltreffer gegen einen lauten falschen Befund. Dieselbe Korrektur im Piloten
(`docs/pilot/2026-09-01-research-pilot.md` R5), dort ausdrücklich als Korrektur markiert.

**B-Reste (Seam-Notiz 15):** (a) der Satz „the twins now refuse the same word for the same reason"
ist qualifiziert — er gilt für den **Elternschritt**, nicht für ein **absolutes** Wort. Ich habe das
nachgemessen statt zitiert (§5 Punkt 5) und die Messung samt Urteil in `H88 (a3)` eingetragen; beide
Zwillingskommentare sagen es jetzt. (b) der Docstring von `kitupdate.classify` beschrieb nur noch
den Melde-Fall und nicht mehr den entscheidenden `unknown`-Zweig — ergänzt, mit dem Satz, den er
gekostet hat.

**C-Rest (Seam-Notiz 17 b)** war im Strom schon erledigt: die `cmd.exe`-Begründung steht im
Docstring von `as_shell_value`. Nachgeprüft.

---

## 5. Was NICHT in den Seam-Notizen stand (die Überraschungen)

1. **Mein eigener Scaffold-Test konnte nicht scheitern.** Die erste Fassung installierte `team`,
   `duo` und `solo` nacheinander in DASSELBE Projekt. Mutation M4 (der alte Rollenfilter zurück)
   blieb **grün**: das subtraktive Entfernen läuft über die Rollen-Manifestdatei, also blieben die
   Referenz-Skills des `team`-Laufs einfach liegen. Korrigiert auf ein frisches Projekt je Preset;
   danach ist M4 in **beiden** Zwillingen rot. Der Docstring trägt diesen Grund.
2. **47 versionierte Textdateien tragen CRLF auf der Platte**, obwohl `.gitattributes` `eol=lf`
   pinnt — darunter `team-kits/office-team/hooks/session_status.py` (608 Zeilen).
   **git sieht das nicht**: es normalisiert beim Hinzufügen, die Dateien gelten als unverändert.
   Gemessen: **keine** davon liegt in einem Lead-Paket, also war nichts falsch — und nichts hätte es
   sagen können. Der Test, den man dafür hält (`test_every_file_the_package_weighs_checks_out_lf`),
   fragt git nach dem **Attribut**, nicht nach den Bytes. Geschlossen: derselbe Test liest jetzt
   zusätzlich die Bytes. Ich habe die 47 Dateien **nicht** normalisiert — das wäre eine große,
   unabhängige Änderung mitten in einer Merge-Runde, und der Kit-Hash normalisiert CRLF ohnehin
   (siehe §9).
3. **Die Emissionszahl in `phase0-disposition.md` bewegte sich** (21 → 22), weil
   `session_status.py` einen `parts.append`-Zweig dazubekam.
   `test_shortening_net.py::test_the_session_start_hook_emits_what_the_disposition_counts` wurde rot
   und hat die Stelle selbst genannt; Dokument nachgezogen, samt der Zeile „eine gelöschte
   Emissionsstelle senkt sie auf 21".
4. **Der Seam-Draht von C war eine Zeichenkettensuche** über `cli.py` (Hausregel 2). Umgeschrieben
   auf `build_parser()`; die Differenz ist mit M7 gemessen.
5. **B-Rest (a) nachgemessen statt übernommen.** Echter Installer, beide Zwillinge, ein absoluter
   Pfad als einzige Zeile eines `RESTORE_SET`: POSIX-Zwilling **rc 0**, Baum unverändert (er liest
   das Wort als repo-relativ, findet in der Sicherung nichts unter diesem Namen); PowerShell-Zwilling
   **rc 1**, aber über eine **unbehandelte `GetFullPath`-Ausnahme**, nicht über seine eigene
   Verweigerung. **Kein Zwilling schreibt außerhalb des Repositoriums** — anders als bei der
   `..`-Kette, wo wirklich gelöscht wurde. Als `H88 (a3)` eingetragen, nicht geschlossen.
6. **Die Gegenrichtung der Kommandoflächen-Prüfung liest keine bloßen Namen** (§4.5). Unter M1
   gemessen, danach durch volle Befehlszeilen im README geschlossen und erneut unter M1 gemessen:
   jetzt sind alle vier Verben rot, wenn der Parser sie verliert.
7. **Seam-Notiz 11 traf nicht zu** (CRLF an der PM-SKILL) — gemessen, siehe §1.
8. **`test_hooks.py::test_nothing_shipped_still_spells_a_v1_monolith_path` wurde rot — und zwar
   erst am vereinigten Baum.** Strom B's neue Datei `tools/test_kitupdate.py` legt für den
   Bestands-Klassifikator einen echten V1-Bestand an und legt dafür die beiden verschobenen
   Monolithen des Aufgaben- und des Fortschrittsspeichers unmittelbar im Zustandswurzelverzeichnis
   ab — ihre Pfade stehen hier bewusst NICHT wörtlich, siehe den Nachtrag unter diesem Punkt.
   **Kein Strom konnte das sehen:**
   B fuhr `test_hooks.py` nur mit `-k "scaffold or preset or settings"`, A fuhr die ganze Datei —
   gegen einen Baum, der B's Fixture noch nicht hatte. Genau die Klasse, für die DEC-0057 die volle
   Suite der Merge-Runde zuweist. Aufgelöst über die vorhandene, an beiden Enden bewachte Ausnahme
   `MIGRATION_CODE_FILES` (dieselbe, die `tools/test_migrate.py` trägt): die Eigenschaft, die sie
   verlangt, gilt hier — die beiden Wörter sind `_write(...)`-Argumente in einem Test, der bei jedem
   Lauf läuft, also wird ein veralteter dort laut. `test_the_migration_code_exemption_is_neither_
   dead_nor_free` hält den neuen Eintrag von beiden Seiten (er muss existieren UND der Sweep muss
   ihn ohne die Ausnahme wirklich finden).
   **Nachtrag, und er ist selbst eine Messung:** dieser Absatz hat den Sweep im vollen Lauf des
   Leads ein zweites Mal rot gemacht — er buchstabierte die beiden Pfade, und der Sweep liest
   auch `project_memory/staging/`. Zwei Fassungen standen zur Wahl; entschieden hat die Messung
   am Leser selbst: er nimmt heute **906** Dateien, davon **491** unter `project_memory/` und
   **56** unter `staging/`, und der einzige Treffer im ganzen Baum war dieser Absatz. Den Sweep
   auf „ausgelieferte Flächen“ zu verengen hätte also keine Fehlmeldung entfernt, sondern
   ausgerechnet die Fläche ausgenommen, auf der die Regel am nötigsten ist: `staging/` hält
   VORSCHLÄGE, also Text, der später Code werden soll — und der Grund des Sweeps ist wörtlich,
   dass ein Text, der den V1-Pfad noch buchstabiert, der Weg ist, auf dem der Pfad zurück in den
   Code darunter kommt. Eine Eigenschaft, die das rechtfertigt, gibt es nicht; „außer staging“
   wäre genau die Aufzählung, gegen die Hausregel 1 steht. Also ist der Absatz umformuliert und
   der Leser unangetastet — keine Datei unter `tools/` oder `team-kits/` hat sich dafür bewegt.
9. **Mein Byte-Zahn lief in einem Klon ohne `.git` gar nicht.** Erst als eigenständiger Test
   (M8) wird er rot; in seinen Nachbarn eingefaltet stand er hinter zwei `pytest.skip`s und die
   Mutation kam als „1 skipped" zurück. Der Docstring sagt das jetzt als Grund für die Trennung.

---
10. **Das Pflicht-Ende des Naht-Drahts war nach dieser Runde ein THEOREM** — vom Prüfer an der
   Naht gefunden, von mir nachgemessen. `told` las eine NENNUNG von `report-gap`; dieselbe Runde
   schrieb den Namen in die §0-Kommandoflächen-Liste derselben Verfassung, und die hält der
   Vollständigkeitstest aus dem Parser — also folgte „genannt" aus „verdrahtet". Gemessen:
   Pflicht-Passage ganz entfernt → **1 passed**. Das ist die zweite Runde in Folge, in der genau
   dieser Draht zu wenig gelesen hat (die erste war die Zeichenkettensuche über `cli.py`, §5.4);
   beide Male hat ihn eine Änderung DERSELBEN Runde entwertet, was den Fall lehrreicher macht als
   die Reparatur: ein Draht, dessen eines Ende aus dem anderen folgt, ist ab da nur noch Prosa.
11. **Der Rollback löschte über eine fremde Aufzeichnung — und meine erste Begründung dafür war am
   falschen Aufrufer gemessen.** Das Löschen ist real (beide Zwillinge, rc 0, „Rollback done.",
   Datei weg). Ich hatte daraus geschlossen, dass kein Vergleich je Pfad die Fälle trennen kann,
   und das mit „14 von 15 Zeilen ohne Kopie, 12 davon im Projekt" belegt. **Beide Stücke waren
   falsch, und der Prüfer hat es gemessen:** eine wirklich frische Installation schreibt gar keine
   `RESTORE_SET`; jene Gestalt gehört zum ABBRUCH-Rückbau, der die Menge direkt fährt und keine
   fremden Daten liest. Der ROLLBACK-Pfad sieht das Manifest der ZWEITEN Installation: 15 Zeilen,
   **2** ohne Kopie, **0** davon im Projekt (nachgemessen). Und es GIBT einen zweiten,
   unabhängigen Besitznachweis — `RESTORABLE` im Skript selbst. Damit ist die Regel schreibbar und
   gebaut (M10–M12 in §6), und `H88 (a4)` steht auf GESCHLOSSEN. **Die Lehre ist nicht der Fix, sondern der
   Aufrufer:** eine Zahl, die an der falschen Aufrufstelle gemessen wurde, trägt eine Begründung,
   die genau falsch herum stimmt.
12. **Der PowerShell-Zwilling schreibt sein eigenes `RESTORE_SET` MIT einer UTF-8-BOM**, und der
   POSIX-Zwilling strippte sie nicht — also war die ERSTE aufgezeichnete Zeile für ihn ein Name,
   den es nicht gibt: rc 0, „Rollback done.", Datei nie zurückgespielt. Vorbestehend, von keinem
   Strom und keiner Suite gesehen (`test_both_installer_twins_record_the_same_restore_set`
   vergleicht die geschriebenen Manifeste miteinander, nicht das Lesen des einen durch den
   anderen). Aufgefallen erst, weil die Besitzregel aus §5.11 daran ANSCHLUG. Mit geschlossen.


## 6. Rot zuerst — jede Messung in einem Klon AUSSERHALB des Repos

Klon: `_round-scratch/TSK-0104/redfirst` (Kopie ohne `.git` und ohne Caches, angelegt von
`make_clone.py`). Treiber: `redfirst.py` — je Mutation: anwenden → `bump_kit_version.py` (sonst misst
man den fehlenden Stempel) → Tests → zurücksetzen. Ein Anker, der nicht greift, meldet sich als
`BROKEN` statt still grün zu bleiben. **Grundlauf vor jeder Mutation: 40 passed, 2 skipped.**

| # | wiederhergestellter Defekt | rot |
|---|---|---|
| **M1** | `kernel/cli.py` auf `c155a5f` (keine Pin-Routen, kein `report-gap`) | 3: `test_kitupdate.py::test_the_kit_pin_routes_print_and_never_write` (argparse: „invalid choice"), `test_gaplog.py::test_the_gap_command_and_the_duty_that_names_it_arrive_together`, `test_gaplog.py::test_the_gap_verb_books_through_the_entry_point` |
| **M1b** | dieselbe Mutation, Gegenrichtung gemessen | `test_hooks.py::test_every_command_a_role_is_handed_is_on_the_entry_points_surface` rot (4 Stellen, nach der README-Korrektur 7 Stellen für alle vier Verben); `…names_all_of_it` bleibt grün — das ist die Grenze dieses Tests, §5.6 |
| **M2** | `_kernel.py` + alle drei `session_status.py` auf `c155a5f` | 3: `test_a_pinned_project_hears_about_its_pin_instead_of_an_offer[dev-team, office-team, research-team]` |
| **M3** | `gen_provider_artifacts.py` auf `c155a5f` (Spiegel je ROLLE) | 3: `test_the_codex_mirror_is_generated_per_skill_directory`, `test_a_reference_skill_reaches_every_preset_and_not_only_team[powershell, bash]` |
| **M4** | nur der Skill-SCHNITT beider Zwillinge zurück (alles andere aus Strom B bleibt) | 2: `test_a_reference_skill_reaches_every_preset_and_not_only_team[powershell, bash]` — „preset duo landed […] — the shared reference skills ['frontend-design', 'webapp-testing'] belong to no role" |
| **M5** | eine Zeile (H92) aus der Übersichtstabelle entfernt | 1: `test_repo_hygiene.py::test_every_hole_has_a_row_in_the_summary_and_every_row_has_a_hole` |
| **M6** | office-Verfassung ganz auf `c155a5f` (Pflicht UND §0-Nennung weg) | 1: `test_the_gap_command_and_the_duty_that_names_it_arrive_together`. **Diese Messung war zu grob und ist ersetzt — siehe M6a/M6b**: sie entfernte BEIDE Vorkommen auf einmal und bewies deshalb nicht, dass die Pflicht allein das Ende hält |
| **M6a** | **nur** die Pflicht-Passage der office-Verfassung entfernt (§0-Liste bleibt) | 1: derselbe Draht — **vor** dem Leser-Fix **grün** (der Befund des Prüfers), **nach** ihm rot („wired: True; texts naming it: []") |
| **M6b** | **nur** `report-gap` aus der §0-Liste der office-Verfassung entfernt, Pflicht bleibt | der Naht-Draht bleibt **grün** (richtig, das ist nicht seine Frage), rot wird `test_hooks.py::test_every_span_that_presents_the_command_surface_names_all_of_it` („names 28, misses report-gap") — die Arbeitsteilung ist damit gemessen und nicht behauptet |
| **M7** | `cli.py` auf `c155a5f` PLUS ein Kommentar, der `gaplog.COMMAND` nur NENNT | 1: derselbe Draht, `wired: False` — die Gegenmessung zur alten Zeichenkettensuche, die hier grün geblieben wäre |
| **M8** | `dev-team/constitution/AGENTS.md` im Klon auf CRLF gesetzt (305 Zeilen) | 1: `test_context_budget.py::test_no_file_the_package_weighs_carries_crlf_on_disk` — und der Attribut-Nachbar meldet im selben Lauf `skipped` (kein `.git` im Klon), was genau der Grund für die Trennung der beiden ist |
| **M10** | Besitzregel aus BEIDEN Zwillingen entfernt (Stand vor der Nacharbeit) | 2: `test_kitupdate.py::test_neither_twin_replays_a_manifest_line_it_does_not_own[powershell, bash]` — rc 0 statt Verweigerung, `docs/note.md` gelöscht |
| **M11** | nur der BOM-Abstrich entfernt, Besitzregel bleibt | POSIX-Zwilling **rc 1** gegen das Manifest seines EIGENEN Zwillings (Über-Verweigerung); PowerShell bleibt grün, weil `Get-Content` die Marke ohnehin abstreift — darum ist der Abstrich dort ein Pin und kein Fix, und der Kommentar sagt das |
| **M12** | BOM-Abstrich UND Besitzregel entfernt (Stand vor dieser Runde) | der ausgelieferte Kreuzfall: ps1 schreibt, sh spielt zurück → **rc 0, erste aufgezeichnete Zeile nie zurückgespielt** — der stille Ausfall, an dem die erste Prüfmessung dieser Runde vorbeilief |
| **M9** | `MIGRATION_CODE_FILES` ohne den neuen Eintrag (der Fund aus §5.8) | 1: `test_hooks.py::test_nothing_shipped_still_spells_a_v1_monolith_path` — im Repo selbst beobachtet, bevor die Ausnahme eingetragen wurde, mit beiden Wörtern und ihrer Datei im Text der Verweigerung |

---

## 7. Ratschen und Stempel — je EINMAL, auf dem vereinigten Baum

**`tools/lead_package_sizes.json`** (`record_lead_package_sizes.py --write --note`, eine
Journalzeile je Kit in `docs/reviews/phase0-disposition.md` §10):

| Kit | vorher | nachher | Grund |
|---|---|---|---|
| dev-team | 42 751 | **42 760** (+9) | §0 gewinnt vier Kommandos, §1a verliert die längere Codex-Qualifizierung, die diese Runde falsch gemacht hat |
| office-team | 49 353 | **50 052** (+699) | dieselben vier Kommandos plus der §8-Pflichtsatz zu `report-gap` (FR-0062) |
| research-team | 45 402 | **45 456** (+54) | nur die vier Kommandos |

**`tools/constitution_section_pins.json`** (`pin_constitution_sections.py --write --note`, eine
Journalzeile in §9): **5 Abschnitte** — §0 aller drei Verfassungen (Kommandofläche), dev §1a
(Codex-Satz ersetzt, nichts entfernt), office §8 (der neue Pflichtsatz).

**Stempel (die Auslieferung, DEC-0057 d — das „7.x → 7" des Nutzers):**
`dev-team`, `office-team`, `research-team` je **`2026.09.02-10`** — die −10 ersetzt die −7: die
Nacharbeiten an den Prüferbefunden haben `team-kits/gen_provider_artifacts.py` (veraltete Zahlen im
Docstring) und beide `scaffold_team`-Zwillinge (die Besitzregel und den BOM-Abstrich) berührt.
Zwischendurch wurde mehrfach gestempelt, weil `validate.py` und die Scaffold-Tests sonst den
fehlenden Stempel statt der Sache messen; der letzte Lauf meldet für alle drei Kits `unchanged`.

**Spiegel byte-identisch:** `tools/test_hooks.py::test_shared_kit_files_identical` grün.
`_kernel.py` ist über alle drei Kits hash-gleich (nachgeprüft); `session_status.py` bleibt
kit-spezifisch mit dem Grund, den `KIT_SPECIFIC_HOOKS` schon nennt.

---

## 8. Läufe

| Lauf | Ergebnis |
|---|---|
| Pin-/Ratschen-Tests nach **jedem** Patch (4×) | je **77 passed** (~37 s) |
| `test_kitupdate` `test_gaplog` `test_reference_skills` `test_design_system_contract` `test_repo_hygiene` `test_disposition` | **142 passed, 1 skipped** (9:00) |
| `test_kernel` `test_approvals_dispatch` `test_backlog_types` `test_e2e` `test_staging_cli` `test_presets` `test_schemas` `test_state` | **541 passed** (3:22) |
| `test_role_contracts` `test_shortening_net` `test_context_budget` `test_research_chain` `test_migrate` `test_report` `test_board` `test_handover_marker` `test_parity_sources` `test_ci_lint_pinned` `test_user_defaults` | **433 passed** (6:10) |
| `test_hooks` + `test_hooks_v2`, erster Lauf | **3031 passed, 13 skipped, 1 failed** (28:40) — der Fund aus §5.8 |
| `test_hooks` + `test_hooks_v2`, nach dem Fix | **3032 passed, 13 skipped** (28:39) |
| `test_context_budget` `test_shortening_net` `test_repo_hygiene` `test_disposition` (Abschluss) | **95 passed** (1:12) |
| `test_kitupdate` ganz (Rollback), letzte Nacharbeit | **82 passed, 1 skipped** (8:17) |
| `test_gaplog` `test_repo_hygiene` `test_disposition` `test_shortening_net` `test_context_budget` | **105 passed** (0:55) |
| `test_hooks.py -k "monolith or v1 or scaffold or surface"` | **21 passed, 6 skipped** (3:57) |
| `python -m ruff check .` | **All checks passed** |
| `python tools/validate.py` | **all structural checks passed** |

**Die volle `tools/`-Suite habe ich bewusst NICHT gefahren** — der Auftrag weist sie dem
Sitzungsagenten als Lieferschritt zu. Die Auswahl oben deckt jede Datei ab, die diese Runde berührt,
plus alles, was `kernel/cli.py` liest.

---

## 9. Zusätzlich geschlossen: der Byte-Zahn am Lead-Paket

`test_context_budget.py::test_every_file_the_package_weighs_checks_out_lf` fragt git nach dem
`eol`-**Attribut**. Das ist das VERSPRECHEN; die Bytes können auseinanderlaufen, weil git beim
Hinzufügen normalisiert. Eine Lead-Paket-Datei mit CRLF auf der Platte erzeugte einen Größenrekord,
den kein LF-Checkout je erreicht — und der Deckel ist eine **Gleichheit**, also ginge nicht die
Maschine rot, die ihn schrieb, sondern die CI. Neu daneben:
`test_no_file_the_package_weighs_carries_crlf_on_disk`, das die Bytes liest. Heute grün (keine der
47 CRLF-Dateien liegt in einem Lead-Paket); rot, sobald eine es tut (M8).

**Als eigener Test und nicht als Zusatzzeile im Nachbarn** — das ist gemessen: eingefaltet stand die
Zusicherung hinter den zwei `pytest.skip`s des Nachbarn (kein `git`, kein Arbeitsbaum), und die
Mutation kam im Klon als „1 skipped" zurück statt rot. Eine Zusicherung, die im Messrig nicht läuft,
ist die Deckungsbehauptung, gegen die Hausregel 5 steht.

---

## 10. Was ich bewusst NICHT geschlossen, sondern benannt habe

1. **Die `report-gap`-Pflicht steht nur in der office-Verfassung.** Das Kommando liegt im Kernel und
   ist damit in allen drei Kits da; dev und research haben es also, ohne dass ihre Verfassung es
   nennt. Das ist die **ungefährliche** Richtung (eine ungenutzte Fähigkeit, keine Sackgasse — die
   gefährliche, „Verfassung nennt ein Kommando, das es nicht gibt", ist überall zu). Nicht getan,
   weil es zwei weitere Lead-Pakete und zwei weitere gepinnte Abschnitte bewegt und eine
   Textentscheidung für zwei fremde Kits ist. FR-0062 bleibt insoweit halb geliefert; C hat das in
   seinem §8.2 genauso benannt.
2b. **`H88 (a4)` ist GESCHLOSSEN** (Besitzregel auf dem Rollback-Pfad, beide Zwillinge, rot je
   Zwilling). Offen bleibt dort genau ein Satz: ein Manifest, das AUSSCHLIESSLICH Pfade aus
   `RESTORABLE` nennt, aber von fremder Hand stammt, ist von einem echten nicht zu unterscheiden —
   dagegen hülfe nur ein Herkunftsnachweis über die Zeilen, und der Schaden wäre dann auf die
   Menge begrenzt, die der Installer ohnehin ersetzt — plus, vom Prüfer nachgemessen, die
   `KEPT_ONLY`-Dateien über den Kopie-Zweig (überschrieben, nicht gelöscht). Benannt am Ende von
   `H88 (a4)`, mit dem Ein-Zeilen-Schluss, der dort nicht mehr gemacht wurde.

2. **`H88 (a3)`** — die Zwillinge beantworten ein absolutes Wort in der `RESTORE_SET` verschieden,
   und die PowerShell-Hälfte tut es über eine unbehandelte Ausnahme. Kein Zwilling schreibt
   außerhalb. Nicht geschlossen: der Fix braucht zwei Zwillinge und je einen eigenen roten Lauf,
   und die PowerShell-Hälfte müsste zusätzlich die Ausnahme in eine Verweigerung verwandeln.
3. **`BUG-0087`** — `tools/test_hooks_v2.py` enthält ein `assert … or True`, ein Test, der nicht
   scheitern kann, direkt neben dem Budget-Thema. Vorbestehend, vom Lead als eigener BUG erfasst,
   von mir nicht angefasst.
4. **Die 47 CRLF-Dateien im Arbeitsbaum** bleiben, wie sie sind. Sie zu normalisieren wäre eine
   große, mit dieser Runde unverwandte Änderung; der Kit-Hash normalisiert CRLF ohnehin
   (`kernel.hashing.kit_hash`), und die eine Stelle, an der rohe Bytes wirklich zählen, ist seit §9
   gemessen. **Ob sie zurückgesetzt werden, ist die Entscheidung des Nutzers, nicht meine.**
5. **`project_memory/.audit/hook_events.jsonl`** ist durch die Testläufe gewachsen (Seam-Notiz 9).
   Liegt in meinem `forbidden_scope`; nicht angefasst, nicht zurückgesetzt.
6. **Item-Hygiene (Seam-Notiz 10)** — die `expected_outputs`/`forbidden_scope`-Widersprüche in
   TSK-0101/0102/0103 sind Sache des Leads; ich schreibe keine Items.
7. **Der subtraktive Rückbau eines Referenz-Skills** ist ungemessen: das Entfernen läuft über die
   Rollen-Liste, ein zurückgezogenes Referenz-Skill bliebe im Projekt stehen. Als Rest in `H83`.
8. **`H92`–`H95` und `H99`** bleiben offen und blockierend zur Abnahme durch den Nutzer — sie liegen
   im Kernel bzw. sind `H11`s Klasse und sind keine Merge-Arbeit. Sie haben jetzt Zeilen in der
   Übersichtstabelle, also sieht der Nutzer sie überhaupt.

---

## 11. DEC-0057 (g) — die Zahlen dieser Merge-Runde

* **Wanduhr der Merge-Runde: 2 h 22 min** (01:50 → 04:12). Reine Suitenzeit darin: rund
  **76 min** (2 × 28:40 für `test_hooks`+`test_hooks_v2`, 9:00 + 3:22 + 6:10 für die drei anderen
  Auswahlen) plus rund 12 min Rot-zuerst-Läufe und 4 × 37 s Pin-Läufe zwischen den Patches.
  Anders gesagt: **etwa die Hälfte der Merge-Runde war Warten auf Suiten.**
* **Konflikte:** 14 Dateien mit Konflikt, **16 Hunks**, davon **9 mit echter Inhaltsentscheidung**
  (die 7 `VERSION`-Hunks sind es nicht — der Stempler ersetzt beide Seiten). Kein Patch war
  unanwendbar; Strom B lief völlig konfliktfrei durch, weil er als erster angewandt wurde.
* **Nahtbefunde, die NICHT in den Seam-Notizen standen: 12** (§5) — elf im Merge selbst plus der
  BOM-Kreuzfall, der bei der Messung von §5.11 herausfiel. Zwei hat erst der Prüfer an der Naht
  gefunden (§5.10, §5.11); drei wären ohne die Rot-zuerst-Läufe unentdeckt geblieben (mein eigener
  nicht-scheiternder Scaffold-Test; die Grenze der Gegenrichtungs-Prüfung; der Byte-Zahn, der im
  Klon nur „skipped" sagte).
  **Einer wäre durch einen seriellen Lauf verhindert worden** — der V1-Monolith-Sweep (§5.8): eine
  serielle Runde hätte B's Fixture zusammen mit der vollen Suite gesehen. Die übrigen elf nicht:
  fünf sind Eigenschaften des vereinigten Baums (Seam-Notiz 11 traf nicht zu, Emissionszahl, CRLF,
  Zeichenkettensuche, Theorem-Draht), vier sind Messfehler meiner eigenen Tests und Sonden, zwei sind vorbestehende
  Defekte, die diese Runde beim Messen aufgedeckt hat (BOM-Kreuzfall, Rollback-Besitz).
* **Suitenläufe:** Ströme A–D zusammen 14 (aus ihren Protokollen) + Merge 6 benannte Auswahlen
  (davon `test_hooks`+`test_hooks_v2` zweimal) + 4 Pin-Läufe zwischen den Patches + 10
  Rot-zuerst-Läufe.
* **Was die Merge-Runde gekostet hat**, gegenüber der Erwartung aus DEC-0057: die sechs
  Nahtdateien, die die Notizen vorher benannt hatten, waren zusammen ungefähr eine halbe Runde
  Arbeit; die zwölf Überraschungen ungefähr noch einmal so viel. Die Ströme selbst haben, wie
  DEC-0057 vorhersagte, **Wanduhr gespart und keine Token**.
