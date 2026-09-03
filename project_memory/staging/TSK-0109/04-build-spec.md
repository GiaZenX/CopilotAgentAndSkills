# 04 — Bauanleitung für die Build-Phase (Opus)

Was hier steht, muss ohne die Design-Phase ausführbar sein. Wo eine Entscheidung offen ist, steht
sie in `README.md` unter „Offene Fragen" und wird hier mit ihrer Nummer genannt.

## 1. Dateien

| Pfad im Kit | Landet im Projekt als | Wozu |
|---|---|---|
| `team-kits/office-team/templates/repo/tools/finance_dashboard.py` | `tools/finance_dashboard.py` | der Generator (Aggregation + Rendern) |
| `team-kits/office-team/templates/repo/tools/finance_dashboard.template.html` | `tools/finance_dashboard.template.html` | die Hülle: `:root`-Token, Struktur, das eine Skript; `{{slots}}` wie im Prototyp |
| `team-kits/office-team/templates/repo/dashboards/README.txt` | `dashboards/README.txt` | Ordnerführer wie `inbox/README.txt`: was hier liegt, wer es schreibt, dass man es nicht editiert |
| Ausgabe | `dashboards/finanzen.html` | eine Datei, fünf Reiter |
| `tools/test_finance_dashboard.py` (Werkstatt, `tools/**` ist im `allowed_scope`) | — | die Messungen aus Abschnitt 5 |

Beide Kit-Dateien sind heute **copy-if-absent** (`scaffold_team.sh` Zeilen 828–851): eine Kit-
Korrektur erreicht ein bestehendes Projekt nur über `.claude/kit_update_pending.repo`. Ob der
Generator in `team-kits/repo_kit_owned.txt` gehört, ist offene Frage 1 — die Antwort entscheidet
auch den Auslöser (Abschnitt 3).

## 2. Der Generator

Form: `python tools/finance_dashboard.py` ohne Argumente; optional `--root <Projektwurzel>` für
Tests. **Kein Argument darf `project_memory` oder `.claude` nennen**, denn `gate_write_scope`
verweigert jede schreibfähige Befehlszeile, die den Zustandsordner nennt — `kit_design_render.py`
löst darum eine Task-Id auf statt einen Pfad zu nehmen; hier löst der Generator die Wurzel selbst
auf (`ledger/` neben `project_memory/`).

Ablauf, in dieser Reihenfolge, und der Prototyp `make_mockups.py` ist das Vorbild für jede Zeile:

1. `sys.dont_write_bytecode = True`, dann `scripts/` in den Pfad; `import euer_report, ledger_add`.
   Damit gibt es die Vorzeichenregel und den Leser genau einmal. Ein Generator, der
   `NEGATIVE_DOC_TYPES` abschreibt, ist der Fehler, den `euer_report.py` in seinem Kopf beschreibt.
2. Ledgerdateien: `os.listdir("ledger")`, Filter `ledger_add.YEAR_FILE_RX`, je Datei
   `ledger_add.validate_file(path)` und `ledger_add.read_ledger(path)`. Kein `glob` (siehe
   `sibling_index`: ein `[` im Projektpfad ließ `glob` nichts finden).
3. `master_data.yaml`, `business_profile.yaml` mit `yaml.safe_load` (PyYAML steht in
   `requirements-office.txt`); fehlende Datei = leeres Mapping, kein Traceback.
4. Aggregation nach `02-data-contract.md`; Beträge als Cent-Ganzzahlen.
5. Rendern: die `view_*`-Funktionen des Prototyps; jede Zeile mit `data-*`-Attributen, die das
   Seitenskript liest; alle Texte durch `html.escape`. Die Hülle wird per `{{slot}}` gefüllt; die
   Slots stehen in der Vorlage, der Generator kennt keine zweite Liste davon — ein Slot, den die
   Vorlage trägt und der Generator nicht füllt, bleibt sichtbar stehen und fällt im Test auf.
6. Schreiben nach `dashboards/finanzen.html`, atomar (Sibling-Tempdatei + `os.replace`, wie
   `ledger_add.save_atomically`), UTF-8, `\n`.
7. Eine Zeile auf stdout: Ausgabepfad, Zeilenzahl, Zahl der Ledgerdateien, gültig ja/nein. Exit 0
   auch bei ungültigem Ledger — die Seite **ist** dann der Bericht über den Zustand; Exit 1 nur,
   wenn nichts geschrieben werden konnte.

Determinismus: gleicher Baum → gleiche Bytes. Kein `datetime.now()`, keine Zufallswerte, keine
`dict`-Reihenfolge ohne `sorted`. Das Alter offener Posten rechnet das Seitenskript aus der Uhr des
Betrachters (Vorlage, Abschnitt „open items"); ohne Skript zeigt die Spalte „—".

Was der Generator NIE tut: eine Datei außer `dashboards/finanzen.html` schreiben; `master_data`
oder das Profil ergänzen; eine Kategorie erfinden (ein Schlüssel ohne Label wird als Schlüssel
gezeigt); einen Bericht unter `reports/` anfassen.

## 3. Der Auslöser — abgeleitet, nicht gewählt

Gemessen am Hauptrepo, Stand 2026-09-02:

- Das Kernel-Board (`generated/board.html`, FR-0030) wird in `state._regenerate_index_locked`
  geschrieben: jeder Kernel-Schreiber kommt dort vorbei, darum gibt es genau einen Auslöser
  (`kernel/board.py`, Kopf; `docs/reviews/2026-08-16-tsk0071-measurements.md`).
- Das Dev-Kit-Dashboard `scripts/generate_dashboard.py` hat **keinen** Auslöser: es ist ein
  Hand-Schritt der Checkliste (`dev-team/constitution/AGENTS.md` Zeilen 73 und 171, PM-Skill
  Zeile 207) — „the one generated artifact the kernel does NOT write". FR-0030 nennt genau das
  als gemessene Grundlinie: nichts lief es, also war es standardmäßig veraltet.
- Der Ledger hat keinen Kernel-Schreiber. Seine Schreibwege: `scripts/ledger_add.py`
  (`save_atomically`) und die erlaubte Handbearbeitung. Die **eine** Stelle, an der beide
  vorbeikommen, ist `gate_ledger_valid.handle_post_tool_use` (PostToolUse auf Edit/Write/
  MultiEdit/Bash/PowerShell, Registrierung `office-team/settings/settings.json` Zeile 163): sie
  erkennt geänderte Ledgerdateien am Stempel und validiert sie.
- Präzedenz dafür, dass ein Hook ein Repo-Template-Skript ausführt: genau dieser Hook startet
  `scripts/ledger_add.py --validate` (`VALIDATOR`), und die Eigenschaft, die das trägt, ist „kit-
  owned und gegen Sitzungsschreibzugriff geschützt" (`repo_kit_owned.txt`, Kopf;
  `guard_harness_selfmod.BLOCKED_REPO_PATHS`).

Daraus folgt die Empfehlung, und sie ist ein **SEAM-Item für Stream G** (Hooks und
`templates/repo/scripts` sind dessen Eigentum, `repo_kit_owned.txt` liegt in keinem Scope):

> Nach dem Validieren geänderter Ledgerdateien in `gate_ledger_valid.handle_post_tool_use` den
> Generator starten, fail-soft (ein Fehlschlag ist eine stderr-Zeile, nie eine Verweigerung —
> Komfort-Hook-Semantik, `_kernel.py` Zeile 44), unter demselben Budget; dafür
> `tools/finance_dashboard.py` in `repo_kit_owned.txt` (damit der Hook das Kit ausführt und nicht
> einen Fork) — was ihn zugleich aus dem anpassbaren `tools/`-Eigentum des Office-Developers
> herausnimmt (offene Frage 1).

Was der Build-Phase in ihrem eigenen Scope bleibt: der Generator als von Hand startbarer Befehl,
getestet; und der Satz in `dashboards/README.txt`, dass die Datei ohne den Seam beim Buchen NICHT
mitläuft. Behauptet werden darf „auto-regeneriert" erst, wenn der Seam gebaut und gemessen ist —
bis dahin ist die Datei so veraltet wie das Dev-Dashboard, und das steht als Lochkandidat unten.

Änderungen an `master_data.yaml` und `business_profile.yaml` (Kernel-Route `apply-proposal`,
Onboarding) lösen nichts aus; das Label einer neuen Kategorie erscheint mit der nächsten Buchung.
Benannt, nicht geschlossen.

## 4. Was `gate_ledger_valid` heute NICHT sieht

`_BLOCKED_SCRIPT_RX` erkennt `euer_report` als Report und verweigert ihn bei ungültigem Ledger.
`finance_dashboard` steht nicht darin: der Generator läuft auch gegen einen ungültigen Ledger.
Darum validiert er selbst und sagt es auf der Seite (Banner). Ob der Ausdruck den Generator
aufnehmen soll, ist Sache von G und Teil des Seams; die Seite ist so gebaut, dass beides stimmt.

## 5. Was ein Test misst — jeder rot ohne seinen Fix

Alle gegen ein gescaffoldetes Office-Projekt außerhalb des Repos
(`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0109\`), mit den Beispielprojekten aus
`sample/<state>/` als Fixture (die Build-Phase kopiert sie nach `tools/fixtures/` oder erzeugt sie
mit `make_mockups.build_sample`). Namen sind Vorschläge; Eigenschaften nicht.

| Test | Misst | Rot, wenn |
|---|---|---|
| `test_the_dashboard_and_euer_report_agree_on_every_quarter` | für jedes Jahr und Quartal der Fixture: die Summen, die der Generator aggregiert, gegen die Zahlen, die `euer_report.py` in `reports/euer_<y>_Q<q>.md` schreibt (gelesen aus dem laufenden Skript, nicht aus einer Kopie) | die Vorzeichenregel abgeschrieben oder ein Storno doppelt gezählt wird |
| `test_the_generator_writes_exactly_one_file` | Hash aller Dateien vor/nach dem Lauf; nur `dashboards/finanzen.html` unterscheidet sich; kein `__pycache__`, kein Lock | der Generator irgendwo sonst hinschreibt |
| `test_the_same_tree_renders_the_same_bytes` | zwei Läufe, identische Bytes | ein Zeitstempel oder eine unsortierte Iteration hineinkommt |
| `test_the_documented_command_passes_the_write_scope_gate` | die Befehlszeile aus `dashboards/README.txt` durch den echten `gate_write_scope`-Prozess (`tools/test_hooks.run_hook_process`) im gescaffoldeten Projekt: rc 0 | die Zeile den Zustandsordner nennt |
| `test_filters_narrow_rows_and_the_sum_follows` | Playwright headless: Richtung=Einnahmen, Status=offen → sichtbare Zeilen und `[data-sum]` gleich dem im Test unabhängig aus der CSV gerechneten Wert; danach Reset → alle Zeilen | Filter oder Summe am Skript vorbeigehen |
| `test_dunning_candidates_follow_the_frozen_clock` | `page.clock.install(time=…)`; Zahl der Stempel „mahnen" und `[data-overdue-count]` gleich den offenen Einnahmezeilen älter als `PAYMENT_TERM_DAYS` | die Frist oder die Richtung falsch gelesen wird |
| `test_an_empty_project_renders_a_direction` | Fixture `empty`: Exit 0, `#view-ueberblick .empty` vorhanden (DOM geparst, nicht String-Suche), kein Traceback | ein fehlendes `ledger/` eine Ausnahme wirft |
| `test_an_invalid_ledger_is_named_on_the_page` | Fixture `alarm`: `.banner.alarm` enthält den ersten Befund von `ledger_add.validate_file` wörtlich; Stempel „ungültig" im Überblick | der Generator die Validierung überspringt |
| `test_the_threshold_verdict_switches_at_the_limits` | parametrisiert: Vorjahr 25.000,00 → `within`, 25.000,01 → `previous_exceeded`; laufend analog mit 100.000 | die Grenze als `>=` oder falsch gelesen wird |
| `test_the_page_makes_no_request_beyond_itself` | Playwright `page.on("request")`: nur die eigene `file://`-URL | jemand eine Schrift oder ein Skript von außen einbindet |
| `test_every_template_slot_is_filled` | die Vorlage wird nach `{{` geparst; die Ausgabe enthält keins | ein Slot hinzukommt, den der Generator nicht kennt |
| `test_a_kleinunternehmer_false_profile_hides_the_watch_and_null_names_the_gap` | zwei Profile → Reiter fehlt bzw. Leerzustand mit dem Feldnamen | der Reiter aus dem falschen Feld abgeleitet wird |

Rot-zuerst nach Hausregel 5: den Defekt in einer Kopie außerhalb des Repos wiederherstellen, den
Test scheitern sehen, zurücksetzen, Namen im Bericht.

## 6. Lochkandidaten H117–H119 (die Build-Phase misst und nummeriert)

- **Kein Auslöser, bis der Seam gebaut ist**: die Datei kann veraltet sein wie das Dev-Dashboard;
  Kette: Buchung per `ledger_add.py`, Seite unverändert. Begrenzung: Datenstand im Kopf ist das
  jüngste Ledgerdatum, und die Seite nennt den Befehl.
- **Keine Herkunft**: eine von Hand geschriebene `dashboards/finanzen.html` ist von einer
  generierten nicht zu unterscheiden (kein Pendant zu `render.json` / `gate_design_sighted`); der
  Generator wird von `gate_ledger_valid` nicht als Report erkannt und läuft gegen ungültige Daten,
  sagt es aber. Nach DEC-0056 kein Härtungsziel, aber benannt.
- **Frist und Uhr**: Mahnkandidaten hängen an einer Konstante (30 Tage) und an der Uhr des
  Betrachters; mit Skript aus zeigt die Seite kein Alter. Begrenzung: die Seite sagt beides.

## 7. Seams außerhalb dieses Streams, zum Melden

- **G** (Hooks, `templates/repo/scripts`, `templates/project_memory`): Auslöser in
  `gate_ledger_valid`; optional `_BLOCKED_SCRIPT_RX`; optional ein Zahlungsfrist-Feld im
  `business_profile.yaml` (offene Frage 3).
- **E** (Texte): Sätze in Bookkeeper-, Office-Manager- und Office-Developer-Skill, die
  `dashboards/finanzen.html` und den Befehl nennen (das TSK nennt das ausdrücklich als E-Seam).
- **unowned**: `team-kits/repo_kit_owned.txt`; `templates/repo/.gitignore` (offene Frage 2);
  `requirements-office.txt`, falls Playwright für die Tests dort erwartet würde — nein: die Tests
  laufen in der Werkstatt, das Projekt braucht kein Playwright.
