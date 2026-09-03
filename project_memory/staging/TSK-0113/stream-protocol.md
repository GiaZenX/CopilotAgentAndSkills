# TSK-0113 + TSK-0112 (Strom G, Büro) — Stromprotokoll der Nacharbeit 1

Arbeitsbaum: `C:/Offline Repos/v2-testbed/_worktrees/g2-office` (Branch `g2/office`, Basis `6d18407`).
Arbeitsverzeichnisse: `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0113/` und `…/TSK-0112/`.
Kein Commit, kein Push, keine Installation. Stempel provisorisch.

Dieses Protokoll trägt **beide** Items. Abschnitt 1–9 gehören zu `TSK-0113` (Neuschnitt von
`TSK-0107`), Abschnitt 10 zu `TSK-0112` (kit-unabhängiger Routine-Zufluss).
`project_memory/staging/TSK-0112/stream-protocol.md` verweist hierher.

**Unterbrechung.** Der Lauf wurde einmal durch ein Sitzungslimit abgebrochen (kein Fehler), und
zwar mitten im Neutralitätstest über rohe Vorlagenzeilen. Nach dem Wiederaufsetzen wurde zuerst der
Stand auf der Platte gemessen (`git status`, `git diff HEAD --stat`, die drei betroffenen Suiten:
**57 passed**) und dann fortgesetzt; nichts wurde doppelt gebaut.

---

## 0. Vorgefunden

14 Dateien unkommittiert, Stempel `office-team: 2026.09.02-13`, alle Suiten des Vorgängers grün.
Jede Behauptung seines Protokolls, die dieser Lauf übernimmt, ist am Baum nachgemessen worden; die
drei, die dabei nicht standhielten, sind P1, P5 und P7 unten.

Nicht im Patch: `project_memory/.audit/hook_events.jsonl` — Nebenwirkung der laufenden Haken dieses
Repos.

---

## 1. P1 (blockierend) — das Register häufte Vergangenheit an, der Absatz verlor die Steuerfrist

**Vorgefunden.** Der Kopfkommentar von `_duties.py` versprach, jeder Zufluss melde die AKTUELLE
Pflicht „und niemals angehäufte vergangene"; `H113` nannte genau das als Begrenzung. Gemessen war
beides falsch.

**Gemessen (der ausgelieferte `session_status.py` als Prozess, Wegwerf-Projekt außerhalb des
Repos):** Archiv mit einem Jahresordner je Geschäftsjahr seit 2005 unter EINER Regel
(`retention: "8y"`), dazu eine monatliche Voranmeldung.

```
vorher : 15 Pflichten, 13 davon Vergangenheits-Jahresordner derselben Regel;
         der Absatz nennt 2005…2010 und bricht ab. Die Voranmeldung steht NICHT darin.
nachher: 3 Pflichten, darunter EINE Aufbewahrungspflicht ("13 year folder(s) … oldest being 2005");
         der Absatz nennt die Voranmeldung UND die Aufbewahrungspflicht.
```

**Fix, zwei Hälften.**
1. `retention_duties` fasst je REGEL zu einer Prüfpflicht zusammen — ältestes Jahr und ANZAHL
   wandern in den Text, damit das Zusammenfassen keine Untermeldung wird. Eine Regel ist eine
   Pflicht: „prüfe diese Schublade".
2. `briefing` vergibt seine Plätze über `_named_fairly` reihum je QUELLE statt streng nach Datum.
   Die Arithmetik dahinter (`MAX_NAMED >= len(FEEDS)`) wird im Test zugesichert, nicht angenommen.

**`receivable_duties` auf dieselbe Anhäufung geprüft.** Es häuft keine Vergangenheit an: jede offene
Rechnung ist ein eigener, heute offener Posten. Was es kann, ist VIELE davon melden — und genau
dagegen ist die Reihum-Vergabe gebaut. Der Kopfkommentar sagt jetzt diese Unterscheidung, statt
„niemals angehäufte" zu behaupten.

**Rote Tests** (Mutationen im Klon `_round-scratch/TSK-0113/mutants/tree`, danach zurückgesetzt):

| Fall | NEU | ALT (Mutation) | Ergebnis |
|---|---|---|---|
| Ende-zu-Ende: Absatz nennt die Steuerfrist | `test_a_decade_of_archive_years_does_not_push_the_due_tax_deadline_out_of_the_briefing` | unrepariert vorgefundener Baum (beide Hälften fehlen) | **failed**, am Baum selbst gesehen |
| eine Pflicht je Regel | `test_a_rule_with_many_years_past_retention_is_one_duty_that_names_the_oldest_and_the_count` | Sammeln je Regel → eine Pflicht je Jahr | **failed** |
| kein Zufluss verdrängt einen anderen | `test_no_feed_can_take_every_slot_of_the_briefing_from_another` | `_named_fairly` → `duties[:MAX_NAMED]` | **failed** |

**Ehrlich dazu:** jede Hälfte für sich lässt die Ende-zu-Ende-Messung wieder grün werden (je
einzeln mutiert: **passed**). Rot war sie am vorgefundenen Baum, wo beide fehlten. Die beiden
Eigenschaftstests decken je ihre Hälfte, und das ist der Grund, warum sie neben der
Ende-zu-Ende-Messung stehen und nicht statt ihrer.

`H113` trägt jetzt die gemessene Begrenzung statt der widerlegten (Abschnitt 8).

## 2. P2 (blockierend) — unlesbare Aufbewahrungsangaben in der ausgelieferten Vorlage

**Vorgefunden.** `FP-900` (`"until classified — …"`) und `FP-901` (`"the original class's span — …"`)
tragen keine Jahreszahl. `_retention_years` gibt `None`, der Zufluss meldet sie als unlesbar, und
jedes Projekt, das dem Beispielblock folgt, liest bei JEDEM Sitzungsstart „DEADLINE REGISTER
INCOMPLETE". Eine Warnung, die im Normalfall feuert, liest niemand mehr.

**Fix.** `retention: null` mit dem Grund daneben — für `FP-900` (Ablage, keine Frist), `FP-901`
(die Frist der Ursprungsklasse gilt) und `FP-002` (die Frist beginnt mit dem Ende eines
Produktlebens). Der Aufbewahrungs-Block der Vorlage nennt jetzt beide erlaubten Formen und sagt,
was eine Prosa-Spanne kostet.

**Roter Test.** `tools/test_office_duties.py::test_every_retention_the_filing_plan_template_ships_is_readable_or_deliberately_empty`
— am unreparierten Baum **failed** (beide Regeln benannt). Er liest die Vorlage so, wie ein Nutzer
sie benutzt: der Beispielblock wird ENTKOMMENTIERT und als YAML GEPARST, dann geht jeder Wert durch
den ausgelieferten `_retention_years`. Zweites Ende: mindestens eine Regel muss noch eine lesbare
Spanne zeigen. Gegenprobe mit gepflanzter Prosa-Spanne: **failed**.

**`add-filing-rule` / `apply-proposal` geprüft.** `kernel/filing.py` übernimmt `retention` als
Freitext aus dem Vorschlag und prüft es nicht; `apply-proposal` fügt nur hinzu. Beide können also
weiterhin eine unlesbare Angabe in einen Aktenplan schreiben — **Kernel, außerhalb meines
Bereichs**, als Naht F6 unten benannt. Was dieser Strom schließen konnte, ist die Vorlage.

## 3. P3 (blockierend) — ein Absolutsatz über eine Wand, die weniger kann

**Gemessen** (installierter Office-Projekt-Klon mit einem echten Dokument unter
`archive/finance/2026/invoice.pdf`, jede Zeile als PreToolUse-Nutzlast an den ausgelieferten
`guard_fs_tripwire.py`, Rig `_round-scratch/TSK-0113/tripwire.py`):

```
rc=2  rm -f archive/finance/2026/invoice.pdf
rc=2  mv archive/finance/2026/invoice.pdf ../x.pdf
rc=0  eine Suche, die mit einer Lösch-FLAGGE statt eines Verbs löscht
rc=0  eine Löschung innerhalb eines anderen Programms
rc=0  ein Archivierer mit quelllöschender Flagge
Dokument danach noch da: True   (ein PreToolUse-Hook entscheidet, er führt nichts aus)
```

**Fix.** Die Vorlage sagt jetzt, was die Regel des TEAMS ist („niemand auf dem Team leert die
Quarantäne"), und schickt für die WAND an den Kopf des Wächters, statt dessen Grenzliste ein
zweites Mal zu führen — ausdrücklich mit der Begründung, dass eine zweite Kopie weiterspricht,
wenn die erste aufhört zu decken. Derselbe Griff im F4-Block und im Docstring von
`retention_duties`.

**P12** (Lösch-Flagge in keiner Aufzählung): eine Zeile im Kopf des Wächters unter „WHAT THIS DOES
NOT SEE", mit dieser Messung und mit dem Grund, warum sie nicht geschlossen wird. Kein neuer
Mechanismus. Als Rest für die Merge-Runde in Abschnitt 9.

**Naht E2 neu gefasst** (Abschnitt 7).

## 4. P5, P6, P7, P10 — vier Sätze und ein Loch

* **P5.** Der Kommentar an `MAX_LEDGER_YEARS` sagte, ein stilles Senken der Zahl werde rot.
  Gemessen: Zahl 12 → 11 **passed** (der Test misst sein Ledger an der Konstante),
  `years[:MAX_LEDGER_YEARS]` → `years[:2]` **failed**. Der Kommentar sagt jetzt genau das und
  trägt das Argument für die Zahl selbst, weil kein Test ihr widerspricht.
* **P6 (Loch, geschlossen).** `_literal_prefix` verwarf einen Laufwerksbuchstaben nur in der ERSTEN
  Komponente; `os.path.join` lässt eine spätere gewinnen — `a/b/D:/<year>/` → `D:`, also ein
  `listdir` auf einem fremden Laufwerk bei jedem Sitzungsstart. Ersetzt durch `_project_directory`,
  das AUFLÖST und gegen die Projektwurzel hält. Roter Test:
  `tools/test_office_duties.py::test_a_filing_plan_that_names_a_place_outside_the_project_is_not_walked`,
  am unreparierten Baum **failed**; er fährt jede Klasse (Klettern, absolut, Laufwerk vorn,
  Laufwerk hinten, UNC, gemischt) plus die Kontrolle, dass eine gewöhnliche Regel auflöst.
* **P7.** Korpus von `test_the_office_kit_ships_nothing_that_could_send` = **44** Kit-Module,
  0 erreichende Importe. Ein INSTALLIERTES Projekt trägt **68**, darunter `.claude/kernel/lock.py`
  mit `import socket` für `gethostname()`. Der Docstring benennt den Kernel jetzt als gemessenen,
  ungeprüften Rest und sagt, warum der Korpus NICHT erweitert wurde. **Bewusste Abweichung vom
  Auftrag:** die beiden Zahlen stehen hier und im Messdokument, nicht im Kommentar — eine Zahl in
  einem zweiten Kommentar ist genau die Fassung, die rottet (Hausregel 4). Der Kommentar nennt die
  Datei.
* **P10.** `session_status.py` schluckte jeden Fehler beim Laden des Registers. Mit weggenommenem
  `_duties.py` erschien der Absatz einfach nicht. Jetzt: „DUTY REGISTER UNAVAILABLE (…)". Roter
  Test: `tools/test_office_duties.py::test_a_missing_duty_register_is_a_line_in_the_briefing_rather_than_silence`,
  am unreparierten Baum **failed**; er fährt eine KOPIE des ausgelieferten Hooks, der das
  Nachbarmodul fehlt.

## 5. P8 + I3 — Neutralität, definiert

**Was der Test jetzt fragt**, in zwei Klassen, jede mit ihrer eigenen Ableitung:

1. **Eine Handelsplattform beim Namen.** Rollentexte wie bisher (quotierte Spanne ausgenommen: in
   Prosa ist ein Name in Anführungszeichen der Gegenstand des Satzes). **Vorlagen als ROHE
   ZEILEN, ohne jede Ausnahme** — eine Vorlage ist keine Prosa, sie wird in das Repository des
   Geschäfts kopiert, wo ein quotierter Beispielwert der Wert ist, mit dem das Feld ankommt. Genau
   daran war P8 unsichtbar: der Fund stand in einem YAML-Kommentar UND in Anführungszeichen.
2. **Der Pilotbetrieb**, aus dem dieses Kit erhoben wurde — aus der Erhebung selbst gelesen
   (`docs/office-kit-from-field.md`) statt hier getippt, und in keinem ausgelieferten Text erlaubt.

**Gefunden und neutralisiert** (drei Stellen, alle in `templates/project_memory/`): eine
Beispielliste von Verkaufskanälen mit zwei Marktplatznamen, ein Beispielwert für die Herkunft der
Umsatzdaten mit einem Shopsystem-Namen, ein Beispiel für Namensvereinheitlichung, das aus einer
echten Marktplatz-Tochter gebaut war (samt der Steuerbemerkung, die sich darauf bezog). Danach:
**0 Treffer über 36 Vorlagendateien**, ohne Ausnahmeliste.

**Rote Tests** (je Mutation im Klon): gepflanzter Plattformname in einem Vorlagenkommentar
**failed**; gepflanzter Pilotname in einer Vorlage **failed**; gepflanzter Pilotname in einem
Rollentext **failed**. Boden:
`tools/test_kit_neutrality.py::test_the_raw_template_reader_reads_what_the_prose_reader_is_allowed_to_skip`
zeigt, dass der neue Leser genau dort feuert, wo der Prosa-Leser bewusst schweigt.

**Grenze, benannt statt behauptet.** „Ist dieses Wort eine PRODUKTGRUPPE" ist Weltwissen und in
diesem Repo nicht ableitbar: die Erhebung nennt keine Sortimentsbegriffe des Piloten, also gibt es
nichts abzuleiten, und das Kit liefert heute keine aus. Ein Rollentext, der eine Produktgruppe in
eigener Prosa nennt, ohne einen der bekannten Plattformnamen und ohne den Pilotnamen zu benutzen,
wird von diesem Test **nicht** gefunden. Das steht so und wird nirgends als Deckung ausgegeben.

## 6. P9, P11, P13 und die zwei Zusätze

* **P9.** STEP 5 der Rückruf-Messung prüfte ein Literal, das `session_status.py` in JEDEM
  Office-Projekt druckt. Gemessen an einem Projekt, dem nichts beigebracht wurde: das Literal steht
  auch dort (**JA**). Der Schritt ist aus der Belegkette **gestrichen**. Nicht umgehängt, weil die
  zweite Messung zeigt, dass es keine zweite Fläche gibt: der erzeugte `session_brief.yaml` nennt
  das gelehrte `PROC-0001` **NEIN** — `kernel.report.generate_session_brief` baut gar keinen
  PROC-Abschnitt (Naht F, kein Befund gegen dieses Kit). Die übrigen Schritte (0/1/2/3/4/6/7/8) sind
  neu gefahren und unverändert; kein Schritt der Kette kann jetzt noch nicht scheitern.
* **P11.** Sechs Messungen am Stichtag selbst, je ein Zufluss, je eine Mutation im Klon, **alle
  rot**: `is_overdue`; Steuer-Zufluss (der 31. schließt den Monat nicht); Aufbewahrung (am 31.12.
  läuft sie noch); Forderungen (am letzten Tag des Ziels wird nicht gemahnt); Wiedervorlage;
  Routine (ISO-Woche statt sieben Tagen). Damit ist P11 geschlossen, nicht nur benannt — was als
  Rest bleibt, steht in Abschnitt 9.
* **P13.** `project_memory/.audit/hook_events.jsonl` bleibt aus dem Patch. Unverändert übernommen.
* **Zusatz (a) — der Dashboard-Auslöser.** Der Codeblock der Naht (Abschnitt 7, I2a) prüft
  `repo_kit_owned.txt` jetzt IM BLOCK und nicht in der Prosa daneben.
* **Zusatz (b) — Budget ohne Frühausstieg.** 200 Regeln × 10 Jahresordner, 200 Registereinträge,
  jedes erlaubte Ledgerjahr voll, der ausgelieferte Hook als Prozess:
  alle Ordner ÜBER der Frist **0,84 s**, kein Ordner über der Frist (0 Pflichten, gar kein Ausstieg
  möglich) **0,92 s**, gegen `_compat.HOOK_DEADLINE_SECONDS = 60`. Durch das Sammeln je Regel ist
  die teure Richtung jetzt der Normalfall: 200 Regeln ergeben höchstens 200 Pflichten, die Kappe
  greift also frühestens bei der letzten Regel, und jede Regel wird wirklich aufgelistet.

## 7. Nähte — wörtlich, nicht geschrieben

Alle Dateien unten liegen außerhalb des `allowed_scope`. **Nichts davon wurde geändert.** E1, E3,
E4, E5, E6, F1, F3, F4, F5 und I1 gelten unverändert aus dem Protokoll zu `TSK-0107`; hier steht,
was diese Runde ändert oder hinzufügt.

**E2 (neu gefasst nach P3) — `team-kits/office-team/skills/records-clerk/SKILL.md:82`.** Vorschlag,
wörtlich: »Ein Dokument, das überholt, beschädigt oder doppelt ist, wandert mit protokolliertem
Grund nach `archive/_quarantine/<Jahr>/` (Regel `FP-901` im Aktenplan). Aus dem Archiv heraus
bewegt niemand etwas — das ist die Regel des Teams. Was der Wächter `guard_fs_tripwire` davon
wirklich verweigert und was er nachweislich NICHT sieht, steht in seinem eigenen Kopf; lies das
dort, bevor du dich auf die Wand verlässt. Der einzige Weg durch sie ist eine Freigabe, die der
Nutzer für genau ein Dokument erteilt.« (Die frühere Fassung behauptete die Wand absolut.)

**E7 (neu, aus V2) — `team-kits/office-team/constitution/AGENTS.md:141` behauptet dieselbe Wand
absolut.** Der Satz lautet dort: »`guard_fs_tripwire` refuses every delete under `inbox/`/`archive/`
and every move OUT of `archive/`«. Gemessen am installierten Piloten
(`_round-scratch/TSK-0113/tripwire.py`, echtes Dokument unter `archive/finance/2026/invoice.pdf`):

```
rc=0  eine Löschung innerhalb eines anderen Programms
rc=0  eine Suche, die ihre Treffer mit einer Lösch-FLAGGE statt eines Verbs entfernt
rc=0  ein Archivierer mit quelllöschender Flagge
```

Die Verfassung liegt im `forbidden_scope`; sie wurde **nicht** angefasst. Ironie und Beleg
zugleich: fünf Zeilen weiter (`:147`) sagt dieselbe Datei schon »That is about the DOOR, not the
wall: what the guard never saw it still never sees« — der Absolutsatz oben widerspricht dem
Nachsatz unten.

Vorschlag, wörtlich, als Ersatz für `:141` (Zeigerform wie E2): »`guard_fs_tripwire` refuses shell
deletes under `inbox/`/`archive/` and shell moves OUT of `archive/`; what it does NOT see is listed
at its own head (`hooks/guard_fs_tripwire.py`, ‚WHAT THIS DOES NOT SEE‘) — read that there rather
than trusting a summary here. That wall has ONE door: ...« (Rest des Absatzes unverändert.)

**Geprüft und gemeldet: die anderen beiden Verfassungen tragen den Satz NICHT.** `guard_fs_tripwire`
kommt in `dev-team/constitution/AGENTS.md` und `research-team/constitution/AGENTS.md` **null**mal
vor; ihre `archive/`-Nennungen meinen das Item-Archiv des Kernels und nicht die Ablage. Der Wächter
ist office-spezifisch (`hooks/guard_fs_tripwire.py` liegt nur im Office-Kit), also gibt es dort
nichts zu korrigieren.

**F6 (neu) — `kernel/filing.py`: `retention` wird als Freitext übernommen.** `add-filing-rule` und
`apply-proposal` können eine Aufbewahrungsangabe in einen Aktenplan schreiben, die
`_duties._retention_years` nicht lesen kann; das Projekt meldet dann bei jedem Sitzungsstart ein
unvollständiges Register. Vorschlag: die Frage beim Minten stellen (»eine Spanne in Jahren, oder
ausdrücklich keine«) und `null` als gültige Antwort führen — dieselben zwei Formen, die die Vorlage
seit dieser Runde nennt.

**I2 (a) — Auslöser für `templates/repo/tools/finance_dashboard.py` in
`gate_ledger_valid.handle_post_tool_use`. ENTSCHEIDUNG unverändert: NICHT verdrahtet, als Naht
gemeldet** — der Generator liegt nicht in meinem Baum, also kann ich nicht messen, dass die Zeile
etwas tut. Der Block trägt die zweite Bedingung jetzt IM CODE:

```python
    # THE VIEW FOLLOWS THE LEDGER, and only a VALID one: this runs after the verdict above, so a
    # ledger that does not validate never produces a dashboard that looks authoritative.
    # TWO CONDITIONS, BOTH IN THE CODE: the generator must exist, and the path must be one the KIT
    # owns (`repo_kit_owned.txt`) -- a hook that ran whatever lay at that path would execute a file
    # the project itself wrote. FAIL-SOFT BY CONSTRUCTION: a PostToolUse hook that refused here
    # would turn a missing generator into a refused write. Nothing here is the source of truth.
    generator = os.path.join(root, "tools", "finance_dashboard.py")
    if os.path.isfile(generator) and _kernel.kit_owns(root, "tools/finance_dashboard.py"):
        try:
            subprocess.run([sys.executable, "-B", generator], cwd=root,
                           capture_output=True, timeout=DASHBOARD_BUDGET_SECONDS)
        except Exception:
            pass
```

Was der Strom, der das verdrahtet, mitliefern muss und ich nicht liefern kann: (1) eine Messung,
die den Generator als Prozess laufen sieht und die erzeugte Datei prüft; (2) den Leser hinter
`kit_owns` — `repo_kit_owned.txt` existiert, ein Kernel-Prädikat dafür habe ich in `_kernel` NICHT
gefunden, das ist also selbst Teil der Naht und kein fertiger Aufruf; (3) eine Entscheidung zu
`DEC-0028` — ein Hook startet hier einen PROZESS. Das ist kein Modellprozess, also nicht der Fall,
den `DEC-0028` verbietet; gesagt werden muss es trotzdem, weil `_duties` und `_routine` daneben
ausdrücklich gar keinen Prozess starten.

**I3 (neu, aus dem Nahtvorrat des Koordinators) — `founding_year` in `business_profile.yaml`.
ENTSCHEIDUNG: NICHT angelegt, als Rest benannt.** Drei Gründe, alle nachprüfbar: (1) In diesem Baum
existiert kein Leser — `templates/repo/tools/` gibt es nicht, der Dashboard-Generator ist nicht
ausgeliefert, und `templates/repo/tools/**` steht in meinem `forbidden_scope`; ich könnte also nicht
messen, dass das Feld etwas tut. (2) Seine FORM ist die Frage des Dashboard-Stroms (Jahr? Datum?
erstes Wirtschaftsjahr?), und ein Feld in der falschen Form ist eine zweite Wahrheit über dieselbe
Sache. (3) Anders als bei `tax.filings` geht ohne das Feld in meinem Bereich nichts blind. **Wer es
anlegt, muss den Onboarding-Satz im selben Paket mitliefern** (Strom E, `skills/office-manager/
SKILL.md`), sonst liefert das Kit ein Feld aus, das nach der Installation niemand mehr füllen kann.
Zu `tax.kleinunternehmer`: das Feld existiert und wird als `null` ausgeliefert; dass ein Generator
alles außer `true`/`false` als „unbekannt" liest, ist die richtige Richtung und in meinem Bereich
nichts zu ändern — gemessen liest heute **kein** ausgeliefertes Modul dieses Kits das Feld.

## 8. Löcher

**Keine neue Nummer.** `H111` und `H112` unverändert im Urteil; ihre Prosa zeigt jetzt auf
`_routine` statt `_duties` (Abschnitt 10) und ihre Testnennungen auf
`tools/test_routine_feed.py` — sonst wäre
`tools/test_repo_hygiene.py::test_every_test_pointer_this_repo_writes_resolves` rot geworden, und
genau das hat der Draht auch getan, bis die drei Zeiger nachgezogen waren.

**`H113` korrigiert.** Die alte Begrenzung („das Register meldet nur die AKTUELLE Pflicht und
sammelt keine Vergangenheit") ist als widerlegt benannt, mit der Messung aus Abschnitt 1, und durch
die zwei Eigenschaften ersetzt, die jetzt GEBAUT sind — je mit dem Test, der sie hält. Das Urteil
bleibt „Rest, benannt": Über-Meldung, nie Schweigen.

## 9. Reste für die Merge-Runde (ohne Nummer, mit Mechanismus und gemessener Kette)

1. **P4 → `TSK-0112`, in dieser Runde erledigt.** Abschnitt 10.
2. **P12 — eine Löschung, die eine FLAGGE statt eines Verbs benutzt.** Mechanismus: beide Lesungen
   von `guard_fs_tripwire` schlagen auf `DELETE_VERBS` an; eine Suche, die ihre Treffer selbst
   löscht, hat keines dieser Verben in der Zeile. Gemessene Kette: rc 0 gegen ein installiertes
   Projekt mit einem echten Dokument unter `archive/` (Abschnitt 3). Nicht geschlossen, weil
   `find` in die Verbliste zu setzen jede reine Suche verweigern würde und das Lesen seiner Flaggen
   ein zweiter Parser für die Grammatik EINES Befehls wäre. Begrenzt durch: die Zeile steht jetzt
   im Kopf des Wächters, und die Vorlage behauptet die Wand nicht mehr absolut. **Die Merge-Runde
   nummeriert das.**
3. **P11 — was nach den sechs Grenztests bleibt.** Die Tagesgrenze ist gemessen; ungemessen bleibt
   die UHR: `briefing()` liest `datetime.date.today()` der lokalen Maschine einmal je
   Sitzungsstart. Eine Sitzung, die über Mitternacht läuft, behält die Antwort von gestern, und
   zwei Maschinen in verschiedenen Zonen antworten am selben Moment verschieden. Kein Angriff, kein
   Datenverlust — eine Meldung, die einen Tag zu früh oder zu spät wechselt. Nicht geschlossen,
   weil eine Zeitzone eine Eigenschaft des Geschäfts ist und in keinem Feld dieses Kits steht.
4. **P9-Nebenbefund — `generated/session_brief.yaml` trägt keinen PROC-Abschnitt.** Gemessen
   (Abschnitt 6). Das ist Naht F1 und keine Lücke dieses Kits; hier nur, damit die Merge-Runde
   entscheidet, ob sie es nummeriert.
5. **P2-Rest — `add-filing-rule`/`apply-proposal` prüfen `retention` nicht.** Naht F6, Abschnitt 7.

## 10. TSK-0112 — der Routine-Zufluss, kit-unabhängig

**Vorgefunden (Befund P4 des Prüfers, nachgemessen).** FR-0038 war in 1 von 3 Kits geliefert,
während nichts daran eine Office-Frage ist: alle drei Kits liefern einen `project-auditor`, alle
drei Verfassungen reiten ihn auf einem Wochentakt, `notify_agent_events.py` und `_audit.py` sind
byte-identisch ×3, und der Zufluss liest ausschließlich kit-unabhängige Dateien
(`project_memory/.audit`).

**Schnitt.** `hooks/_routine.py`, **byte-identisch in allen drei Kits** (SHA-256 der drei Kopien
identisch, 9 714 Bytes), nach dem Vorbild von `_audit.py`. Es trägt `AUDIT_ROLE`, die
Ereignisfelder, `duty`, `audit_period_id`, `last_run`, `routine_duties` und `notice`.

* **Office** erreicht es durch sein Register: `_duties.FEEDS` nennt `_routine.routine_duties`, und
  `_duties._duty` IST `_routine.duty` — die Form einer Pflicht steht damit an genau einer Stelle.
* **dev und research** rufen `_routine.notice(cwd)` direkt aus ihrem `session_status.py`, mit
  derselben „UNAVAILABLE"-Ausfallzeile, die P10 im Office-Kit gebracht hat.
* **Bewusste Abweichung vom Wortlaut** („called from every kit's session_status.py"): das
  Office-`session_status.py` ruft `_routine` NICHT zusätzlich auf, sonst stünde derselbe Lauf
  zweimal im Briefing — genau die Doppelung, gegen die das Register gebaut wurde. Gemessen und
  festgenagelt: `tools/test_routine_feed.py::test_the_office_briefing_names_the_routine_exactly_once`.

**`session_status.py` bleibt kit-spezifisch** (`KIT_SPECIFIC_HOOKS`, Grund unverändert). Das ist die
Ausnahme aus I2 und älter als das Item.

**Gemessen als PROZESS auf wirklich gescaffoldeten Projekten** (`_round-scratch/TSK-0112/pilot.py`;
Home-Klon dieses Baums, `init_project_memory.ps1` + `scaffold_team.ps1`, dann die eigenen Haken des
Projekts):

```
=== dev-team       init rc=0  scaffold rc=0   _routine.py installiert: True
    vor jedem Lauf : ROUTINE DUE (2026-08-31): the project-auditor has not run in 2026-W36 …
    notify rc=0
    nach dem Lauf  : keine Routine-Zeile
=== research-team  init rc=0  scaffold rc=0   _routine.py installiert: True
    vor jedem Lauf : ROUTINE DUE (2026-08-31): the project-auditor has not run in 2026-W36 …
    notify rc=0
    nach dem Lauf  : keine Routine-Zeile
```

(Der erste Lauf des Piloten scheiterte am Scaffold, weil der Kit-Stempel noch nicht nachgezogen
war — „Could not record the installed hook bundle". Nach `bump_kit_version.py` rc 0. Das ist
Hausregel 7, hier als Messung.)

**Rote Tests** (Mutationen im Klon `_round-scratch/TSK-0112/mutants/tree`, danach zurückgesetzt):

| Fall | NEU | ALT (Mutation) | Ergebnis |
|---|---|---|---|
| der Zufluss fehlt zwei Kits (Stand vor TSK-0112) | `tools/test_routine_feed.py::test_the_routine_notice_appears_and_clears_in_every_kit_that_ships_it` | `_routine.py` aus dev und research entfernt | **2 failed** (dev, research) |
| das Briefing erreicht das Modul nicht | dieselbe + `…::test_every_kit_briefing_reaches_the_shared_module` | Import in dev-`session_status.py` entfernt | **2 failed** |
| Spiegel, Ende 1: eine Kopie läuft auseinander | `tools/test_hooks.py::test_shared_kit_files_identical` | eine Zeile nur in der research-Kopie geändert | **1 failed** |
| Spiegel, Ende 2: Ausnahme ohne Unterschied | derselbe | `_routine.py` in `KIT_SPECIFIC_HOOKS` eingetragen | **1 failed** |

Kontrolllauf ohne Mutation davor und danach: **3 passed**.

**Was aus `tools/test_office_duties.py` weggezogen ist**, nichts verloren: die sechs
Routine-Messungen stehen jetzt in `tools/test_routine_feed.py` und laufen **je Kit** statt einmal
(28 Tests). Im Office-Suite blieb, was eine Office-Frage ist.

**Nähte aus TSK-0112** (nicht geschrieben): die Verfassungssätze und die drei
`project-auditor`-Rollentexte sagen weiterhin „läuft wöchentlich", während der Takt jetzt in
`_routine.audit_period_id` steht — das ist E3 aus dem Vorgängerprotokoll, jetzt für alle drei Kits
statt nur für Office. Keine neue Lochnummer für dieses Item.

**Zahl, die sich dadurch bewegt hat:** die Emissionszählung des dev-`session_status.py` in
`docs/reviews/phase0-disposition.md` steigt von 22 auf **24** (die Meldung und ihre
UNAVAILABLE-Zeile). Nachgezogen samt Begründung; `test_shortening_net.py` liest die Zahl aus dem
Syntaxbaum und hätte sie sonst rot gemeldet — was sie auch getan hat, bevor ich sie nachzog.

## 10a. Nacharbeit 2 — vier Textpunkte der Nachprüfung (V1, V2, V3, T112-1)

Die Nachprüfung gab `TSK-0112` **PASS** und `TSK-0113` **FAIL**, ausdrücklich nicht wegen des Baus:
alle elf Befunde waren gemessen behoben. Vier Textpunkte blieben.

**V1 (blockierend, Hausregel 3) — der Docstring behauptete mehr, als der Test misst.** Er sagte
„Both halves of the fix are measured here". Nachgemessen (Mutationen im Klon): nur `_named_fairly`
zurück → **grün**; nur die Aggregation zurück → **grün**; beide zurück → **rot**. Der Test misst
das ERGEBNIS in den Worten des Managers, nicht die Hälften. Der Docstring sagt das jetzt, nennt die
beiden Halter der Hälften und schreibt die Folge hin, statt sie zu verschweigen.

**Benannter Rest dazu:** die Deckung ist DISJUNKTIV. Der Ende-zu-Ende-Test ist für keine der beiden
Hälften ein Regressionsnetz — wer eine Hälfte samt ihrem Unit-Test entfernt, bekommt alle drei
grün. Nicht geschlossen, weil ein Test, der beide Hälften einzeln erzwingt, den Absatz auf eine
bestimmte Auswahlmechanik festnägeln würde statt auf sein Ergebnis; die Merge-Runde entscheidet, ob
sie das will.

**V2 (blockierend, `expected_outputs` 7) — die Verfassung behauptet die Wand weiter absolut.**
Als Naht **E7** in Abschnitt 7 aufgeschrieben, mit den drei gemessenen rc-0-Zeilen, dem wörtlichen
Ersatzvorschlag und der Gegenprobe, dass die beiden anderen Verfassungen den Satz nicht tragen. Die
Datei selbst blieb unberührt (`forbidden_scope`).

**V3 — der Wurzelvergleich verglich Zeichenketten.** Gemessen am ausgelieferten Modul:

```
'....//<year>/'  -> prefix '....'  -> candidate = die Projektwurzel MIT einem angehängten Trennzeichen,
                    also derselbe Ort und eine andere Zeichenkette: `candidate == base` war False,
                    und der Gang lief weiter.
```

Folge: der Aufbewahrungs-Zufluss listet die PROJEKTWURZEL und liest jedes vierstellige Verzeichnis
darin als Archivjahr — kein Ausbruch, aber eine Meldung über etwas, das nie beobachtet wurde.
Fix: ein Helfer `_same_place` (absolut, normalisiert, gross/klein-gefaltet) für BEIDE Vergleiche.
Roter Test: `tools/test_office_duties.py::test_a_filing_plan_that_resolves_to_the_project_ROOT_is_not_walked`
— vor dem Fix **failed** (`'....//<year>/' was placed at the project root`), danach grün. Er misst
beide Enden: der Auflöser verweigert die drei Schreibweisen, die auf die Wurzel zeigen, UND ein
Projekt mit einem echten `2010/` im Wurzelverzeichnis erzeugt keine Pflicht.

**T112-1 — ein Zeiger, der eine Hälfte nicht misst.** `test_a_missing_routine_module_is_a_line_in_the_briefing_rather_than_silence`
kopierte nur das dev-Kit, während BEIDE `session_status.py` (kit-spezifisch, also zwei Dateien) je
eine eigene Kopie des Ausfallzweigs tragen und beide auf diesen Test zeigen. Jetzt über die zwei
direkten Aufrufer parametrisiert. Rot gemessen: den Zweig nur in der research-Fassung entfernt
→ `…[research-team]` **failed**, `…[dev-team]` **passed**, Kontrolle davor und danach **2 passed**.
Das Office-Kit bleibt aussen vor, weil es das Modul über sein Register erreicht — seine Hälfte ist
`tools/test_office_duties.py::test_a_missing_duty_register_is_a_line_in_the_briefing_rather_than_silence`.

**Stempel dieser Nacharbeit.** V3 berührt `team-kits/office-team/hooks/_duties.py` → **office
`2026.09.02-16`**. V1 und T112-1 berühren ausschliesslich `tools/`, V2 gar keine Datei — **dev und
research bleiben `2026.09.02-12`**, und das ist nicht angenommen, sondern mit
`bump_kit_version.py` geprüft (Meldung `unchanged` für beide).

## 11. Läufe

Testumfang nach `DEC-0050`: die Suiten, die die geänderten Dateien LESEN. Die volle Suite läuft
**nicht** in dieser Runde.

| Lauf | Ergebnis |
|---|---|
| `pytest tools/test_office_duties.py tools/test_routine_feed.py` | **62 passed** (Nacharbeit 2: **64**, plus `test_repo_hygiene` **75 passed**) |
| `pytest tools/test_kit_neutrality.py tools/test_office_duties.py tools/test_repo_hygiene.py` | **57 passed** (Zwischenstand nach dem Abbruch) |
| `pytest tools/test_hooks_v2.py -k "office or filing or ledger or gitignore or session_status or template or reaching or could_send or legal_form"` | **734 passed** (3:14) |
| `pytest tools/test_hooks.py -k "office or mirror or shared or trays or tripwire or session_status or enforcement"` | **71 passed** (10:45) |
| `pytest tools/test_hooks.py -k "office or mirror or shared or routine or session_status"` (Nacharbeit 2) | **40 passed** (3:35) |
| `pytest tools/test_disposition.py tools/test_repo_hygiene.py` | **19 passed** |
| `pytest tools/test_shortening_net.py tools/test_context_budget.py` | erst **1 failed** (Emissionszahl 22 statt 24), nach dem Nachziehen **78 passed** |
| `pytest tools/test_gaplog.py tools/test_disposition.py` | **18 passed** |
| `pytest .claude/hooks/test_gates.py -k "hole or measurement or reference"` | **8 passed** (6:42) |
| dieselbe Auswahl nach Nacharbeit 2 | **8 passed** (2:47) |
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | erst **3 Fehler** (die drei neuen `_routine.py` waren nicht git-getrackt), nach `git add -N` **all structural checks passed** |

Mutationsläufe: 17 Fälle, alle in Kopien außerhalb des Repos, alle zurückgesetzt; die Tabellen
stehen in Abschnitt 1, 5, 6 und 10. Kontrollläufe ohne Mutation vor und nach jeder Batterie grün.

## 12. Stempel

Drei Stempelläufe, alle protokolliert:

1. `office-team: 2026.09.02-14`, `dev-team`/`research-team: 2026.09.02-11` — nach dem Schnitt aus
   `TSK-0112`. Nötig, weil der Scaffold des Piloten ohne nachgezogenen Stempel abbrach
   („Could not record the installed hook bundle"); danach rc 0.
2. `office-team: 2026.09.02-15`, `dev-team`/`research-team: 2026.09.02-12` — nach der letzten
   Änderung, die drei Kommentare betraf (Abschnitt 12a). Der Pilot ist gegen diesen zweiten Stand
   erneut gefahren, mit demselben Ergebnis.

3. `office-team: 2026.09.02-16`, `dev-team`/`research-team` **unverändert `2026.09.02-12`** —
   Nacharbeit 2. Nur `_duties.py` ist eine berührte Kit-Datei (V3); V1 und T112-1 liegen in
   `tools/`, V2 hat keine Datei geändert. Der Lauf meldet für dev und research ausdrücklich
   `unchanged` — geprüft, nicht angenommen.

**Provisorisch** — die Merge-Runde stempelt neu.

## 12a. Zwei Entscheidungen zur Form eines Zeigers

Beide betreffen Hausregel 4(b) — eine Eigenschaftsbehauptung wird ein Test, und der Kommentar nennt
ihn — und beide sind bewusst getroffen, nicht vergessen:

* **Ein AUSGELIEFERTES, vom Nutzer bearbeitetes Dokument nennt keinen Test dieses Repos.** In einem
  Projekt des Nutzers gibt es `tools/` nicht; der Zeiger wäre dort tot — dieselbe Begründung, mit
  der der Vorgänger einen `docs/`-Verweis aus der Aktenplan-Vorlage genommen hat. Meine erste
  Fassung des Aufbewahrungs-Blocks hatte so einen Zeiger; er ist wieder raus. Die Bindung läuft
  stattdessen in der Gegenrichtung: der Test NENNT die Vorlagendatei und liest ihren Satz zuerst,
  also fällt er um, wenn der Satz verschwindet. Dasselbe gilt für den `legal_form`-Absatz in
  `business_profile.yaml` und
  `tools/test_hooks_v2.py::test_no_shipped_office_module_decides_anything_on_the_legal_form`.
* **Ein ausgeliefertes HAKEN-MODUL darf einen nennen** und tut es — das ist die bestehende Praxis
  dieses Repos, und `tools/test_repo_hygiene.py::test_every_test_pointer_this_repo_writes_resolves`
  liest `team-kits/` genau deswegen. Alle neuen Zeiger in `_duties.py`, `_routine.py` und
  `session_status.py` lösen auf (Lauf in Abschnitt 11).

## 13. Übergabe

* Patch: `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0113/stream-office.patch` (`git add -N`
  für die neuen Dateien, `git diff HEAD`, **ohne** `project_memory/.audit/hook_events.jsonl`).
* Status: `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0113/git-status.txt`.
* Messungen: `docs/reviews/2026-09-02-tsk0107-office-duties-measurements.md`, Abschnitt 6 ist diese
  Runde.

**Welche Datei zu welchem Item gehört:**

| Datei | Item |
|---|---|
| `team-kits/office-team/hooks/_duties.py` | TSK-0113 (P1, P5, P6) + TSK-0112 (der Schnitt) |
| `team-kits/office-team/hooks/session_status.py` | TSK-0113 (P10) |
| `team-kits/office-team/hooks/guard_fs_tripwire.py` | TSK-0113 (P3/P12) |
| `team-kits/office-team/templates/project_memory/filing_plan.yaml` | TSK-0113 (P2, P3) |
| `team-kits/office-team/templates/project_memory/business_profile.yaml` | TSK-0113 (P8, FR-0076) |
| `team-kits/office-team/templates/project_memory/master_data.yaml` | TSK-0113 (P8) |
| `team-kits/office-team/templates/project_memory/compliance_register.yaml` | TSK-0107 (unverändert übernommen) |
| `team-kits/{dev,office,research}-team/hooks/_routine.py` | TSK-0112 |
| `team-kits/{dev,research}-team/hooks/session_status.py` | TSK-0112 |
| `tools/test_office_duties.py` | TSK-0113 (+ die sechs weggezogenen Tests: TSK-0112) |
| `tools/test_routine_feed.py` | TSK-0112 |
| `tools/test_kit_neutrality.py` | TSK-0113 (P8/I3) |
| `tools/test_hooks_v2.py` | TSK-0113 (P7, FR-0076) |
| `tools/test_repo_hygiene.py` | TSK-0107 (unverändert übernommen) |
| `docs/POST_V2_WISHLIST.md` | TSK-0113 (H113) + TSK-0112 (H111/H112-Zeiger) |
| `docs/reviews/2026-09-02-tsk0107-office-duties-measurements.md` | TSK-0113 |
| `docs/reviews/phase0-disposition.md` | TSK-0112 (Emissionszahl) |
| `docs/office-kit-from-field.md` | TSK-0107 (unverändert übernommen) |
| `team-kits/*/VERSION` | beide |

## 14. Was offen bleibt, benannt

1. **Die fünf Reste aus Abschnitt 9**, jeder mit Mechanismus und gemessener Kette.
2. **Die Nähte aus Abschnitt 7** — E1–E6, F1–F6, I1–I3. Nichts davon wurde geschrieben.
3. **Der Neutralitätstest deckt Plattform-NAMEN und den Pilotnamen**, nicht jede Form von
   Produktgruppen-Bindung (Abschnitt 5).
4. **`_routine.AUDIT_ROLE` deckt nur eine Richtung.** Eine ZWEITE prüfende Rolle träte unbemerkt
   daneben; „ist diese Rolle ein Prüfer" ist keine Eigenschaft, die eine ausgelieferte Datei trägt.
   Steht so im Kommentar.
5. **Der Rückruf-Nachweis ist ein Apparat-Nachweis.** Dass ein Modell dem beigebrachten Verfahren
   inhaltlich folgt, ist nicht gezeigt und gehört in einen `DEC-0025`-Piloten.
6. **`F7`/`F8` von `FR-0002`** — eigene Pakete, unverändert offen.
