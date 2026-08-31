# TSK-0097 / FR-0058 Stufe 2 — Rundenprotokoll (Umsetzer)

Datum: 2026-08-30 · Rolle: `harness-implementer` · Arbeitsverzeichnis ausserhalb des Repos:
`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0097\`

Auftrag: DEC-0051 Stufe 2 — „den Freigabe-Weg in der Werkstatt nachruesten". Der Auftrag traegt
eine Vermutung des Leads („der Mint ist reiner Kernel und schon erreichbar; es fehlt nur die
Weiterreichung") mit der Anweisung, sie zu MESSEN statt zu glauben. Sie ist zur Haelfte falsch, und
die andere Haelfte ist schlimmer als vermutet.

## 1. Die Messung des Muenzweges (Auftragspunkt 1)

Gemessen an den laufenden Prozessen, nicht am Quelltext allein. Wegwerf-Projekt ausserhalb des
Repos, `probe_selfmint.py` im Arbeitsverzeichnis.

| Stufe | Traeger | in dieser Werkstatt |
|---|---|---|
| `request-approval` (Anfrage anlegen, Frage drucken) | reiner Kernel (`kernel/cli.py` → `approvals.create_pending_request`) | **laeuft**, rc 0 |
| Frage wortgleich weiterreichen | Kit-Haken `gate_approval.py` auf `PreToolUse(AskUserQuestion)` | **nicht registriert** — nichts prueft die Weiterreichung |
| Antwort des Nutzers lesen und muenzen | Kit-Haken `gate_approval.py` auf `PostToolUse(AskUserQuestion)` | **nicht registriert** — nichts liest die Antwort |
| `approvals.mint` selbst | akzeptiert NUR den Freigabe-Haken, als sich selbst gestartet (`_assert_minting_caller`) | erreichbar, s. u. |

`.claude/settings.json` fuehrt vier `PreToolUse`-Eintraege und **keinen einzigen `PostToolUse`**.
`report.approval_mint_is_wired("C:/Offline Repos/AgentAndSkills")` = `False` (gemessen).

**Der Befund, der die Runde dreht.** Der Muenzweg fehlt nicht — er bindet nur an keine
Nutzerantwort. Drei Zeilen, alle rc 0 unter den vier Gates dieses Repos, ohne Kit, ohne Haken,
ohne Nutzer:

1. `request-approval scope BUG-0001` → `approvals/pending/<id>.yaml`, rc 0
2. die Datei lesen — der Muenz-Code steht im Klartext (`mint_code: '1edc5a'`);
   `gate_lead_write_scope` rc 0 (fuer `harness-lead` **und** fuer einen Umsetzer-Subagenten
   gemessen, `probe_gate1.py`)
3. `python team-kits/dev-team/hooks/gate_approval.py < forged.json`, Nutzlast allein aus (1)+(2)
   gebaut → `gate_lead_write_scope` rc 0, Haken antwortet
   `[team-kit gate_approval] approval APR-0001 recorded for BUG-0001`, Item steht danach auf
   `APPROVED` mit `approval_ref: APR-0001`.

Das ist kein exotischer Bau: `tools/conftest.py::mint_via_hook` fuehrt genau diesen Aufruf als
Vorrichtung der Suite.

**Gegenmessung im Kit** (`probe_kitgate.py`, dieselbe Zeile aus (3) gegen die ausgelieferten
Hooks): `gate_write_scope.py` → **rc 2**, „this command names the enforcement layer in a pipeline
that can write". `guard_harness_selfmod` und `gate_shell_hygiene` rc 0. Die Wand steht also im
Produkt an genau einer Stelle — und die Werkstatt hat sie nicht.

## 2. Sicherheitsabwaegung (Auftragspunkt 3) — die Entscheidung dieser Runde

Die Frage des Auftrags war: oeffnet ein freigabegetriebener Uebergang ohne Dispatch hier ein
Selbstfreigabe-Loch? **Antwort: es ist bereits offen, und zwar unabhaengig vom Dispatch.** Leases
und Dispatch spielen keine Rolle — die Kette laeuft ueber den Freigabe-Haken, nicht ueber einen
Auftrag.

Daraus folgt die Entscheidung, die diese Runde getroffen hat und die den Auftragspunkten 1 und 2
ihre Form gibt:

> **Es wird KEIN Werkstatt-Muenzweg gebaut.** Jedes Kommando, jede Bruecke, jeder Relais-Befehl,
> der in dieser Werkstatt eine Freigabe erzeugen wuerde, waere das selbst ausgestellte Ja, das
> `assert_transition_approved` woertlich verbietet — und er waere ueberfluessig, weil der
> unehrliche Weg schon laeuft. Gebaut wird stattdessen (a) die Wahrheit an der Stelle, an der eine
> Rolle auf die Wand trifft, und (b) die Gegenprobe, die eine Behauptung im Datensatz gegen die
> Messung haelt.

Warum kein Kryptographie-Ausweg existiert, gemessen und nicht vermutet: der Muenz-Code muss dem
Nutzer gezeigt werden, gezeigt wird er ueber die Sitzung, und die Sitzung ist der beaufsichtigte
Teil. Es gibt keinen Kanal, den der Lead nicht liest. Die Kits loesen das nicht durch Arithmetik,
sondern durch den **Provider**: die `answers` schreibt die Plattform, und nur ein registrierter
Haken bekommt sie. Ohne Registrierung gibt es diesen Kanal nicht, und ohne diesen Kanal gibt es
kein ehrliches Ja.

**Was das fuer den Nutzer heisst** (der Punkt, der ihm gehoert): der einzige ehrliche Weg zu Stufe
2 ist, dass **er** den Freigabe-Haken dieses Repos registriert — eine Aenderung an
`.claude/settings.json` aus einer Shell ausserhalb von Claude Code, plus Sitzungsneustart. Danach
ist die Werkstatt genau so stark wie ein ausgeliefertes Kit und traegt genau dessen benannten Rest
(`approval_provenance: unverified`). Vorher ist sie **schwaecher** als das Produkt, und das steht
als **H80** in `docs/POST_V2_WISHLIST.md` — offen, blockierend, benannte Ausnahme, Abnahme durch
den Nutzer offen. Der Weg dorthin ist nicht Teil dieser Runde: `.claude/**` ist ihr
`forbidden_scope`.

## 3. Was gebaut wurde

### 3.1 Die Verweigerung verspricht keinen Mint mehr, den das Projekt nicht machen kann

`kernel/approvals.py`: `_unwired_mint_note(state)` haengt an die Verweigerung von
`assert_transition_approved` einen Satz an, wenn dieses Projekt den Freigabe-Haken **nicht** auf
dem muenzenden Ereignis registriert. Die erste Haelfte der Abhilfe bleibt stehen, weil sie ueberall
laeuft (`request-approval` ist reiner Kernel); konditional ist nur das Versprechen, dass die
Antwort des Nutzers die Sache abschliesst.

Vorher (dieses Repo, `probe_message.py`):

> … Remedy: run `python scripts/harness.py request-approval scope BUG-0001` and relay the printed
> question to the user VERBATIM — **their answer mints the approval AND walks this transition, so
> there is nothing left to transition by hand afterwards.**

Nachher, unveraendert in einem Projekt MIT Registrierung; in einem ohne kommt hinzu:

> **THAT ROUTE DOES NOT REACH ITS END HERE: this project registers no gate_approval.py on
> PostToolUse(AskUserQuestion), so the user's answer is read by nothing and mints nothing** — the
> request opens and the question prints, and that is all. Report the gap instead of walking the
> item by hand; what a delivery has already closed is derived from the Evidence (DEC-0051).

Der Satz behauptet ausdruecklich NICHT, dass hier nichts muenzen kann — das waere falsch (Kapitel
1). Er sagt, was die Registrierung sagt: keine ANTWORT des Nutzers muenzt.

Neu daneben, damit drei Namen einmal buchstabiert sind: `approvals.APPROVAL_QUESTION_TOOL`,
`APPROVAL_QUESTION_EVENT`, `APPROVAL_MINT_EVENT`. `report.capability_matrix` liest sie jetzt
ebenfalls, statt `"gate_approval.py"`, `"PreToolUse"`, `"PostToolUse"`, `"AskUserQuestion"` ein
zweites Mal hinzuschreiben.

`report.approval_mint_is_wired(repo_root)` ist der eine Leser: er fragt die **Registrierung**
(`_wired_hooks` — Matcher, Hook-Typ, Existenz der Datei, verschluckter Exit-Code,
`disableAllHooks`), nie die blosse Anwesenheit der Datei.

### 3.2 Die Gegenprobe auf `closed_by_delivery` (Auftragspunkt 4)

`report.contradicted_confirmations(state, active_items)` + `_check_confirmations_agree_with_the_
verdicts` in `validate_state` (Schwere: **error**).

Definition, dreifach abgeleitet, ohne eine einzige Aufzaehlung:

* **Welcher Status „bestaetigt" heisst**: `backlog_types.confirming_edge` — der Endzustand, den ein
  Typ nur erreicht, wenn er seine ganze Kette geht. Ausdruecklich nicht „das Item steht in
  irgendeinem Endzustand": `REJECTED`/`DUPLICATE`/`CANCELLED`/`SUPERSEDED` heissen *verworfen*, und
  ein fehlgeschlagenes Urteil daneben widerspricht dem Datensatz nicht, es bestaetigt ihn.
* **Was als Urteil zaehlt**: `closed_by_delivery`s eigene Definition, in einem Atemzug aus
  derselben Gruppierung gefragt — die Gegenprobe kann die Nachweise also nicht anders lesen als die
  Ableitung, die sie prueft.
* **Schweigen ist kein Widerspruch**: ein Item, das nie jemand beurteilt hat, steht nicht drin.
  `state.CONFIRMING_EVIDENCE` bewacht diese Kante nur fuer `BUG` und sagt im eigenen Kommentar,
  dass die uebrigen bestaetigenden Kanten Politik der Rollen sind und keine Kernel-Regel. Fuer jedes
  bestaetigte Item einen Nachweis zu fordern hiesse, diese Politik im Kernel zu erfinden.

Kosten auf dem heissen Pfad: **null**, wo nichts zu pruefen ist. Das Evidence-Verzeichnis wird nur
gelesen, wenn ueberhaupt ein aktives Item in einem bestaetigenden Endzustand steht (im Normalfall
keins — ein bestaetigtes Item wird archiviert). `closed_by_delivery` nimmt dafuer jetzt die schon
bezahlte Gruppierung entgegen (`by_subject=`), damit es bei einem Treffer bei EINEM Scan bleibt.

Gegen den echten Speicher dieses Repos gemessen: `contradicted_confirmations` = `{}`,
`validate_state` unveraendert 34 Befunde / 0 Fehler. Die Gegenprobe schlaegt nicht blind an.

## 3.3 Nacharbeit nach dem Pruefbericht (F1-F8)

**F1 (blockierend) — der Leser beantwortete die falsche Frage.** `approval_mint_is_wired` las durch
`_fires_for(_wired_hooks(...))`, und das beantwortet „koennte diese Registrierung BLOCKIEREN". Ein
Mint ist aber eine NEBENWIRKUNG — der Haken schreibt die APR-Datei auf dem Weg hinaus —, also
passiert er unabhaengig vom Exit-Code und unabhaengig davon, wo die Datei liegt. Selbst
nachgemessen (`probe_f1_f2.py`, echte Hook-Prozesse, Wegwerf-Projekte):

| Registrierung | alter Leser | Haken | Item danach |
|---|---|---|---|
| `python -B ".../gate_approval.py" ; exit 0` | `wired=False` | rc 0, `approval APR-0001 recorded` | **APPROVED** |
| Haken unter `tools/approval/` registriert | `wired=False` | rc 0 | **APPROVED** |
| gewoehnliche Kit-Form (Kontrolle) | `wired=True` | rc 0 | APPROVED |

Beides haette der Rolle das Falsche gesagt, und zwar in die **unsichere** Richtung: die Werkstatt
schwaecher darstellen, als sie ist. Kein ausgeliefertes Kit betroffen — selbst gemessen, alle drei
`settings/settings.json` gegen ihre eigenen `hooks/`-Baeume: `approval_mint_is_wired = True` fuer
dev-, office- und research-team.

Gebaut ist jetzt ein **eigener Mint-Leser** (kein umgedrehter Satz): derselbe Gang durch die
Einstellungs-Ebenen, aber ohne die drei Bedingungen, die zur Blockier-Frage gehoeren
(`_swallows_exit_code`, die `.claude/hooks/`-Bindung, die Datei-Existenz). Was bleibt, entscheidet
wirklich, ob der Provider den Haken startet: Kill-Switch, Ereignis, Matcher, Hook-Typ und ob die
Zeile den Haken **faehrt** statt ihn nur zu nennen (`_invoked_scripts`). Jeder verbleibende Zweifel
faellt bewusst nach `True` — zu weit gefasst, siehe N3 in Kapitel 3.4: beide Richtungen sind
gemessen widerlegt, die ausgelieferten Saetze beschraenken sich auf das Gebaute. Der Satz selbst ist mitgeschaerft: er behauptet jetzt die
Registrierung und ihre Folge fuer die Nutzerantwort, nicht mehr „mints nothing".

**F2 — zwei falsche Zitate, an beiden Stellen korrigiert.** Selbst nachgemessen
(`probe_f2_f7.py`, echter `gate_memory_complete`-Prozess gegen ein Projekt mit einem gepflanzten
Widerspruch): `ls -la` rc 0 still, `git commit -m x` rc 0 still, `git push origin main` rc 2,
`git merge feat/x` rc 2. Der Haken startet auf jedem Bash-Aufruf, `validate_state` laeuft nur auf
einer Merge-/Push-Zeile. Und der zitierte Datensatz steht in `_delivery_evidence`, nicht in
`_check_approval_expiry_agrees`. Beide Stellen tragen jetzt dieselbe Formulierung, und die
kopierte Zeile in `accepted_without_a_verdict` nennt den Fehler, damit die Kopie nicht wieder
entsteht (SR-0008).

**F3** — `docs/POST_V2_WISHLIST.md` Abschnitt 10 trug die von H80 widerlegte Praemisse
(„da `gate_approval` **nur** aus einer echten Antwort praegt …"). Korrigiert mit Verweis auf H80:
headless unerreichbar ist der ehrliche Weg, nicht der Mechanismus.

**F4** — die Typ-Allgemeinheit der Gegenprobe hatte keinen Test, der scheitern kann. Jetzt zweiter
Positivfall im bestehenden Test: eine `PR`, die ihre ganze Kette bis `ACCEPTED` geht (mit echten
Mints), plus ein spaeteres `review: fail` → gemeldet. Die Verengung auf `BUG` ist als M6 rot.

**F5/F6** — die Zahl „four gates" ist raus (sie veraltet durch die eigene Empfehlung); der
Konstanten-Kommentar sagt jetzt, dass die Kits den Haken auf **zwei** Paaren registrieren und nur
das eine muenzt.

**F8 — messend entschieden: Hinweis an den Einstieg.** Gemessen: `request-approval` druckte in der
Werkstatt nur die Frage, und die einzige Flaeche, die die Wahrheit sagt, war die
Transition-Verweigerung — die kommt, **nachdem** der Nutzer gefragt und geklickt hat. Das ist genau
die Form, die BUG-0039 aufgeschrieben hat. Der Hinweis geht auf **stderr** (stdout traegt nur, was
wortgleich weitergereicht wird — dieselbe Regel, die der `dispatch`-Zweig eine Ebene tiefer schon
befolgt) und liest **denselben** Mint-Leser, keine zweite Ableitung.

## 3.4 Zweite Nacharbeit (N1-N4)

**N1 — die KLASSE statt der zwei Stellen.** Gegrept nach jeder Fassung von „`gate_memory_complete`
führt `validate_state` auf jedem Bash-Aufruf": vier Vorkommen in `report.py`, nicht zwei
(Zeilen 755, 1115, 1365, 1484). Die erste trug zusätzlich eine falsche Kostenerzählung
(„a minute and a half of a frozen session per command"). Alle vier korrigiert; die MESSUNG steht
jetzt an **einer** Stelle (`_check_dispatch_approval_presented`, mit den vier eigenen
Hook-Läufen), die drei anderen zeigen dorthin statt sie nachzuerzählen (SR-0008). Die gemessenen
Sekundenzahlen bleiben, nur ihr Bezug wird richtig: „vor jedem Merge und jedem Push" statt „pro
Befehl". Nicht angefasst: `_delivery_evidence` und `state.py` sagen „auf demselben Tool-Aufruf wie
`gate_memory_complete`" — das ist die Merge-Pfad-Aussage und war nie falsch. Kontrollgrep danach:
**in `report.py`** nennt nur noch die Korrektur-Notiz selbst die alte Formulierung. Vier weitere
Fassungen leben in datierten Messdokumenten (`docs/reviews/2026-08-25-tsk0085-measurements.md:36`,
`docs/reviews/phase0-disposition.md:113/:256/:341`) — dort steht seit 2026-08-31 je eine datierte
Korrekturnotiz, der Wortlaut der damaligen Messung bleibt (Prüfer-Nit R1, Lead-Entscheidung).

**N2 — drei Gegengewichte im selben Test.** `test_a_registration_that_could_not_block_still_mints`
behauptet zweimal `is True`; ohne Gegengewicht befriedigt ein Leser, der immer `True` sagt, den
ganzen Test. Neu und je verhaltenswirksam: Kill-Switch → `False`, Matcher ohne `AskUserQuestion`
(`"Bash|Edit"`) → `False`, eine Zeile die den Haken nur NENNT (`echo "see gate_approval.py"`) →
`False`. Alle drei versagen in die **beruhigende** Richtung (Warnung unterdrückt, wo nichts
münzt) — die Richtung, in der eine Warnung nicht still danebenliegen darf. Rot als W1/W2/W6.

**N3 — beide Richtungen gemessen, Sätze auf das Gebaute beschränkt.** `probe_n3.py`, echte
Hook-Prozesse:

| Registrierung | `_invoked_scripts` | Leser | was wirklich passiert |
|---|---|---|---|
| Kit-Form über `$CLAUDE_PROJECT_DIR` | `['gate_approval.py']` | `True` | münzt |
| quotierter absoluter Pfad **mit Leerzeichen** | `[]` | **`False`** | **münzt trotzdem** |
| auflösbarer Pfad, Datei **fehlt** | `['gate_approval.py']` | **`True`** | nichts läuft |
| `echo "see gate_approval.py"` | `[]` | `False` | nichts läuft (richtig) |

Damit sind „jeder Zweifel fällt nach `True`" und „eine zweifelhafte Registrierung zählt als
verdrahtet" beide widerlegt — der Zweifel fällt bei einer unzerlegbaren Zeile nach `False`.
**Entscheidung: Sätze beschränken, Mechanik NICHT nachziehen**, und zwar messend begründet:
`_invoked_scripts` trägt auch `_wired_hooks` → `capability_matrix` → `doctor` und die
Bündel-Vertrauensprüfung, also verschiebt jede Erweiterung dort, was `doctor` für **jedes** Projekt
meldet — eigene Runde, eigene rote Tests an diesen Lesern. Ein zweiter Zerleger nur für den
Mint-Leser wäre die zweite Antwort auf „was fährt diese Zeile", also genau die Drift, gegen die
`_invoked_scripts` als einzige Antwort existiert.
**Abwägung für Nutzerprojekte, wie verlangt:** die Kits sind nicht betroffen (`$CLAUDE_PROJECT_DIR`
steht leerzeichenfrei in der Zeile — für alle drei gemessen `True`). Betroffen wäre ein
ausgeschriebener Pfad — und genau den hätte die H80-Empfehlung erzeugt, weil dieses Repo unter
`C:\Offline Repos\AgentAndSkills` liegt. Deshalb schreibt H80 jetzt die leerzeichenfreie
Registrierung vor, und die beiden Fehlrichtungen stehen als **H81** mit Kette, Urteil und
Begrenzung. Beide erzeugen keine Freigabe: die eine hält eine Runde an, die andere schweigt.

**N4** — die Zahl im Testdocstring ist raus.

**V4-Anker (kein Befund, notiert):** vertauschte Provider-Ereignisnamen in den neuen Konstanten
fangen erst `pytest tools/test_hooks.py -k "approval or mint or verdict"` (5 failed) — ausserhalb
der Rundensuiten. Der Anker steht als Satz im Konstanten-Kommentar in `approvals.py`.

## 4. Rote Tests (Auftragspunkt: jeder Fix mit einem Test, der ohne ihn rot wird)

Alle sechs in `tools/test_report.py`. Mutation im Klon **ausserhalb** des Repos
(`_round-scratch/TSK-0097/mut/`, `mutate.py` setzt den Defekt, faehrt den Test, setzt zurueck):

| Defekt wiederhergestellt | roter Test | Lauf |
|---|---|---|
| M1: `validate_state` fragt die Gegenprobe nicht | `test_a_failing_verdict_contradicts_a_confirmed_item` | 1 failed |
| M2: „steht in irgendeinem Endzustand" statt `confirming_edge` | `test_a_terminal_that_does_not_mean_confirmed_is_no_contradiction` | 1 failed |
| M3: `_unwired_mint_note` gibt immer `""` zurueck | `test_the_approval_remedy_does_not_promise_a_mint_the_project_cannot_make` | 1 failed |
| M4: die DATEI zaehlt als Verdrahtung statt der Registrierung | `test_the_mint_is_wired_by_the_registration_and_not_by_the_file_lying_there` | 1 failed |
| **M5: „kann blockieren" beantwortet „kann muenzen" (der F1-Defekt)** | `test_a_registration_that_could_not_block_still_mints` | 1 failed |
| **M6: Gegenprobe auf `BUG` verengt (die F4-Luecke)** | `test_a_failing_verdict_contradicts_a_confirmed_item` | 1 failed |
| **M7: der Einstieg reicht weiter, ohne die Unlesbarkeit zu sagen** | `test_the_entry_point_warns_before_the_question_is_put_to_the_user` | 1 failed |
| **W1: der Kill-Switch wird nicht gelesen** | `test_a_registration_that_could_not_block_still_mints` | 1 failed |
| **W2: der Matcher wird nicht gelesen** | `test_a_registration_that_could_not_block_still_mints` | 1 failed |
| **W6: den Haken NENNEN zaehlt als ihn FAHREN** | `test_a_registration_that_could_not_block_still_mints` | 1 failed |
| zurueckgesetzt | `tools/test_report.py` ganz | 99 passed, 2 failed |

Die zwei roten im Klon sind Klon-Artefakte und keine Regression:
`test_parent_fields_holds_every_binding_the_spec_declares_for_a_captured_type` und
`test_the_spec_state_tuple_is_measured_against_the_spec_and_the_hook` lesen `HARNESS_V2_SPEC.md`,
das ausserhalb von `team-kits/` und `tools/` liegt und im Klon fehlt. Im Repo laeuft dieselbe Datei
**101 passed**.

## 5. Was gemessen wurde und NICHT gebaut wird (Auftragspunkt 2: `test`-Nachweise)

Die Frage war, ob die Pflicht `BUG FIXED → VERIFIED` mit dem erfuellbar ist, was diese Werkstatt
ohnehin aufschreibt. **Nein — und das ist kein Kernel-Defekt, sondern eine Buchungsluecke.**

Gemessen im Speicher dieses Repos (71 aktive Evidence-Items): `review` 66, `acceptance` 3,
`audit` 1, **`test` 1**. `state.CONFIRMING_EVIDENCE = {"BUG": "test"}` verlangt genau die eine
Art, die hier fast nie geschrieben wird — und die Regel ist richtig: sie ist die Kernel-Fassung
derselben Hausregel, die dieses Repo ohnehin faehrt („jeder Fix braucht einen Test, der ohne ihn
rot wird").

Konkret an BUG-0075: `report.qa_verdicts(state, "BUG-0075")` = `{"review": EVD-0071 pass}` —
erreicht ueber den Referenzgraph, aber von der falschen Art. `closed_by_delivery` nennt BUG-0075
**gar nicht**, weil kein Nachweis seine Id SCHREIBT (EVD-0070 nennt TSK-0096, EVD-0071 den Bug nur
ueber den Graphen). Der Auftrag sagt „EVD-0070 nennt die Lieferung" — im Sinn der Ableitung tut sie
das nicht.

Der fehlende Link ist also kein Bauteil, sondern eine Zeile, die die Runde ohnehin schuldet: den
`test`-Nachweis mit der Bug-Id in `related`. Siehe Kapitel 6.

## 6. Nachtrag-Kommandozeilen fuer den Lead (Auftragspunkt 5)

Alle Zeilen gegen `gate_lead_write_scope` **und** `gate_commit_evidence` gefahren
(`probe_backfill_lines.py`): **rc 0**. Praefix ueberall:
`PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory`

**Klasse A — gelieferte Wuensche (`FR`) → `MERGED`.** Kein Mint noetig; Route in einem
Wegwerf-Projekt Ende zu Ende gefahren (`probe_fr_route.py`, jede Stufe rc 0, danach `validate`
0 Fehler und Archivierung):

```
echo '{"triage_result": "<was die Sichtung ergab, mit der Nummer die es geliefert hat>"}' \
  | PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory update FR-nnnn
PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory transition FR-nnnn TRIAGED
echo '{"resulting_item": "<PR-/TSK-/FR-Nummer, in der der Wunsch aufging>"}' \
  | PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory update FR-nnnn
PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory transition FR-nnnn MERGED
PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory archive FR-nnnn
```

`triage_result` ist ab `TRIAGED` Pflicht, `resulting_item` ab `MERGED`/`CONVERTED` — beide werden
vom Validator eingefordert, also VOR dem jeweiligen Uebergang schreiben. `CONVERTED` statt `MERGED`,
wenn der Wunsch zu einem eigenen Item wurde; `REJECTED` nur, wenn er wirklich verworfen ist (dann
ohne `resulting_item`).

**Klasse B — reparierte Fehler (`BUG`).** Der ehrliche Endzustand bleibt bis H80/H39 unerreichbar.
Was JETZT geht und was die Ableitung ehrlich macht — den geschuldeten `test`-Nachweis mit der
Bug-Id:

```
PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory evidence \
  --kind test --result pass --related BUG-0075 \
  --summary "<welcher Test ohne den Fix rot wird, und wo der Lauf steht>" \
  --artifact-ref staging/TSK-0096/round-protocol.md
```

Danach nennt `closed_by_delivery` den Bug, `delivery_closure_rollup` zeigt ihn als geliefert mit
seiner Route, und das Statusfeld bleibt ehrlich auf `TRIAGED` stehen statt mit `REJECTED` zu
luegen. **Nicht** faelschen: der Nachweis darf nur geschrieben werden, wo der rote Test wirklich
existiert und benannt ist.

Der Uebergang `TRIAGED → APPROVED` bleibt verweigert, und die Verweigerung sagt jetzt selbst,
warum. Wenn der Nutzer den Freigabe-Haken registriert hat und die Sitzung neu gestartet ist, ist
die Fortsetzung:

```
PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory request-approval scope BUG-0075
# die gedruckte Frage WORTGLEICH per AskUserQuestion weiterreichen; die Antwort des Nutzers
# muenzt und geht die Kante selbst -- danach ist nichts von Hand zu transitionieren
PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory transition BUG-0075 FIXED
PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory transition BUG-0075 VERIFIED
PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory archive BUG-0075
```

`VERIFIED` verlangt dann noch den `test`-Nachweis aus dem Block darueber — er ist die eigentliche
Bedingung und nicht die Freigabe.

**Klasse C — Arbeitsauftraege (`TSK`).** Unveraendert: `DONE`/`VALIDATED` haengen an einem echten
Dispatch-Lease, das diese Werkstatt nicht faehrt (H39, erste Haelfte). `DEC-0041` gilt weiter,
erledigte Auftraege schliessen als `CANCELLED`.

## 7. Ausdruecklich NICHT geschlossen, aber benannt

1. **H80 (neu, blockierend, Abnahme durch den Nutzer offen).** Der Freigabe-Haken laesst sich hier
   von Hand fahren; im Kit ist dieselbe Zeile rc 2. Der Schluss liegt in
   `.claude/hooks/gate_lead_write_scope.py` — `forbidden_scope` dieser Runde. Kette, Gegenmessung
   und der benannte Schluss stehen im Eintrag.
2. **H39 war falsch und ist korrigiert, nicht geschlossen.** Der Satz „`VERIFIED` ist damit fuer
   jeden Bug unerreichbar, solange kein Muenzweg existiert" ist mit drei rc-0-Zeilen widerlegt. Der
   Eintrag behaelt die Buchfuehrungshaelfte; die Angriffshaelfte ist H80. Die
   „Wodurch-es-auffiele"-Bedingung ist praezisiert: sie fragt jetzt nach einem EHRLICHEN Muenzweg
   (`approval_mint_is_wired` = `True`).
3. **Der Rollup sagt die Unerreichbarkeit nicht.** `report.delivery_closure_rollup` druckt pro Item
   die Route mit ihren Waechtern („needs a 'scope' approval"), aber nicht, dass dieses Projekt
   diesen Waechter nicht bedienen kann. Zwei Flaechen sagen es jetzt (der Einstieg vor der Frage,
   die Verweigerung an der Wand), der Rollup als dritte bewusst nicht; `doctor` traegt die Aussage
   ausserdem als `approval_provenance`.
3a. **Die neue `error`-Schwere ist ein Push-/Merge-Blocker in allen drei Kits.** Selbst gemessen
   (`probe_f2_f7.py`, echter `gate_memory_complete`-Prozess): mit einem bestaetigten Item und einem
   nicht zurueckgenommenen `fail` sind `git push` und `git merge` rc 2, `ls` und `git commit`
   rc 0 still. Das ist die gewollte Wirkung — ein Datensatz, der eine Bestaetigung behauptet, die
   seine eigenen Nachweise widerlegen, darf nicht gemergt werden —, aber es ist eine **Folge fuer
   Bestandsspeicher**: ein Projekt, das heute so dasteht, kann nach dem Kit-Update nicht mehr
   pushen, bis es den Widerspruch aufloest (Neulauf aufzeichnen oder das ueberholte Urteil
   archivieren). Der Befund nennt beide Wege in seinem Remedy.
4. **Die Gegenprobe liest nur AKTIVE Items.** Ein archiviertes Item mit widersprechendem Urteil
   faellt niemandem auf — geerbt von `validate_state`, das die aktiven Items beurteilt, und hier
   nicht geaendert.
5. **Die Gegenprobe hat nur eine Richtung.** „Status sagt bestaetigt, Urteil sagt gescheitert" ist
   gebaut. Die Gegenrichtung „Status sagt verworfen, Lieferung sagt geliefert" ist NICHT gebaut,
   weil kein Automat weiss, welcher Endzustand „verworfen" heisst — `MERGED` bei einem `FR` ist ein
   ehrlicher Lieferausgang, `REJECTED` nicht, und die beiden auseinanderzuhalten braeuchte eine
   Aufzaehlung. Genau die Luege, vor der FR-0058 warnt (einen reparierten Bug als `REJECTED`
   schliessen), faengt diese Runde also NICHT ab.
6. **Der Mint-Leser irrt in beide Richtungen (H81).** Eine Registrierung, deren Zeile er nicht
   zerlegen kann — der erreichbare Fall ist ein quotierter Pfad mit Leerzeichen — liest als
   „nicht verdrahtet" und warnt, obwohl sie muenzt; ein auflösbarer Pfad mit fehlender Datei liest
   als verdrahtet und schweigt, obwohl nichts laeuft. Nicht geschlossen, weil `_invoked_scripts`
   auch `doctor` traegt; H81 traegt Kette, Urteil und Begrenzung, und H80 schreibt deshalb die
   leerzeichenfreie Registrierung vor.
7. **Der `test`-Nachweis wird von nichts erzwungen.** Kapitel 5 misst, dass die Werkstatt `review`
   schreibt und `test` schuldet; eine Regel, die den `test`-Nachweis pro repariertem Bug einfordert,
   waere eine eigene Entscheidung (und im Kernel waere sie erfundene Politik, s. 3.2).

## 8. Laeufe

* `python -m ruff check .` → All checks passed
* `python tools/bump_kit_version.py` → nach der letzten Nacharbeit dev-team `2026.08.30-19`,
  office-team `2026.08.30-20`, research-team `2026.08.30-20`
* `python tools/validate.py` → all structural checks passed
* `pytest tools/test_report.py tools/test_kernel.py tools/test_state.py
  tools/test_approvals_dispatch.py` → 440 passed
* `pytest tools/test_kitupdate.py tools/test_presets.py tools/test_board.py
  tools/test_staging_cli.py tools/test_repo_hygiene.py tools/test_disposition.py
  tools/test_shortening_net.py` → 270 passed, 1 skipped. (In der ersten Runde waren hier vor dem
  Versions-Stempel 10 rot, alle aus dem fehlenden Stempel — Hausregel 7 wortwoertlich bestaetigt.)
* `pytest tools/test_hooks_v2.py -k "approval or transition or mint or doctor or capability"`
  → 235 passed
* `pytest tools/test_hooks.py -k "approval or mint or verdict or evidence or transition or
  validate or memory_complete"` → 66 passed (enthaelt den V4-Anker aus dem Pruefbericht)
* Gegen den echten Speicher nach der Nacharbeit: `approval_mint_is_wired` = `False`,
  `contradicted_confirmations` = `{}`, `validate_state` 34 Befunde / 0 Fehler — unveraendert
* `pytest .claude/hooks/test_gates.py` → 244 passed, 1 failed:
  `test_gate3_answers_before_its_registration_however_costly_the_line_is_to_judge`, 4.60–4.69 s
  gegen eine 4.50-s-Registrierung. **Flatternd, nicht regressiv**: drei Solo-Wiederholungen ergaben
  2× passed / 1× failed, und der Test nennt diese Klasse in seinem eigenen Docstring (BUG-0033,
  Sichtkosten der Suite gegen die Reserve). Von dieser Runde nicht erreichbar: Gate 3
  (`gate_commit_evidence.py`) importiert `os`, `sys` und `_harness` — keines davon liest den Kernel,
  und die Runde hat keine Datei unter `.claude/` angefasst. Der Test faehrt ausserdem gegen ein
  Wegwerf-Projekt (`shutil.copytree`), nicht gegen den Arbeitsbaum, also hat auch der gewachsene
  Diff dieser Runde keinen Anteil.
* `pytest tools/test_repo_hygiene.py tools/test_disposition.py tools/test_shortening_net.py`
  → 52 passed (die Suiten, die `docs/` lesen)
* Volle Suite: **nicht** gefahren — Lieferschritt des Leads (DEC-0050).

## 9. Geaenderte Dateien

* `team-kits/kernel/approvals.py` — drei Protokoll-Konstanten, `_unwired_mint_note`, ein Zusatz an
  der Verweigerung von `assert_transition_approved`
* `team-kits/kernel/report.py` — `approval_mint_is_wired` (eigener Mint-Leser),
  `contradicted_confirmations`, `_check_confirmations_agree_with_the_verdicts` in `validate_state`,
  `closed_by_delivery` nimmt `by_subject`, `capability_matrix` liest die Konstanten
* `team-kits/kernel/cli.py` — `request-approval` warnt auf stderr, wenn nichts die Antwort liest
* `tools/test_report.py` — sechs neue Tests plus `_register_approval_hook`
* `docs/POST_V2_WISHLIST.md` — H39 korrigiert, H80 neu (Zeile in der Tabelle, Eintrag,
  Herkunftszeile)
* `team-kits/*/VERSION` — Stempel

Keine gespiegelte Datei beruehrt (der Kernel liegt einmal unter `team-kits/kernel/`; die
Kit-Hook-Baeume sind unveraendert).
