# Live-Testlauf 2026-08-23 — Befunde (drei Läufe auf HEAD 297a649, Kits 2026.08.23-3)

Auftraggeber: harness-lead. Ausführung: Pilot-Mechaniker (derselbe wie Pilot 4), echte
`claude.exe`-Sitzungen, DEC-0031-Persona (kritisch, nicht technikfundiert), **ohne
Modell-Override** — jeder Mitschnitt hält das als eigenen Datensatz fest. Rig aus
`git archive 297a649` neu gebaut, Kit-Hashes gegen die eigenen Stempel nachgerechnet (alle drei
OK), Brücke und Ansage eingebaut wie der Installer es täte. Kasse: 23,35 $ von 30 (Sonde 0,47 ·
Lauf 1 14,02 · Lauf 2 3,32 · Lauf 3 5,54). Daten:
`C:\Offline Repos\v2-testbed\_round-scratch\LIVE-TEST\` (operator-steps.md; je Lauf DREHBUCH,
BEOBACHTUNGEN, VERBATIM, jsonl-Mitschnitte; Hook-Messungen unter `_hookprobe`/`_covprobe`/
`_oldprobe`). Alle fünf Mitschnitte vollständig (je ein `end`-Datensatz, 0 defekte Zeilen).

## Verdikt

Die drei Fix-Runden nach Pilot 4 (TSK-0080/0081/0082) halten dem Live-Betrieb stand, soweit
der Live-Betrieb ihre Bedingungen erreicht hat. **Kein neuer Defekt.** Drei Messpunkte, die nur
der Provider beantworten kann, bleiben offen und stehen unten einzeln.

## Lauf 1 — Baustrecke, frisches dev-Projekt auf dem ausgelieferten fable-Pin (14,02 $)

- **Modellregime gemessen:** S1 (Einstiegsgate, Kit noch nicht installiert) `claude-opus-5[1m]`;
  S2/S3 ab der ersten PM-Sitzung `claude-fable-5` — der Frontmatter-Pin regiert ohne Override.
  Damit ist die BUG-0058-Randbedingung „Nachmessung auf dem ausgelieferten Pin" erfüllt.
- **FR-0056 Umkehrbarkeits-Klausel: bestätigt, wörtlich.** Die Team-Frage trug „Diese Wahl ist
  nicht endgültig: fehlt später eine Rolle, fragt der Project Manager dich erneut und passt das
  Team an." Die Lücke aus beiden Pilot-4-Hälften ist zu.
- **BUG-0058 (P4-2): der Live-Fall trat nicht ein** — der Architekt lief im Vordergrund und
  lieferte 13 Dateien; es gab keinen stillen Hintergrund-Spezialisten. Am Hook im Rig gemessen:
  frische Lease → rc 0; abgelaufenes Bindefenster ohne Kind → **rc 2** mit Befund und Remedy;
  derselbe Befund ein zweites Mal → rc 0 („höchstens einmal je Befund" hält); `stop_hook_active`
  → rc 0; Zustand unverändert. **Ungemessen bleibt AC-2: ob der Provider `exit 2` auf dem
  `Stop`-Ereignis honoriert, der Befundtext also das Modell erreicht.** Ebenso H53
  (Lebensdauer von `stop_hook_active`).
- **BUG-0060 (H59-Hälfte): der Briefing-Satz existiert** — am Hook gemessen mit Gegenprobe
  (vorher keine Zeile, nachher wörtlich „WORK BOOKED AS FINISHED THAT NOTHING MEASURED: …").
  **Ob der Satz den PM bewegt, ist ungemessen** — der Lauf kam nicht bis dorthin.
- **Zeit bis zum benutzbaren Ergebnis: weiter offen, aber anders als in Pilot 4.** 21 Eingaben +
  2 Neustarts ohne benutzbares Ergebnis — der Lauf endete an der Geldschiene (14,49 $ von 15),
  nicht an einem stillen Spezialisten. Positiv: `design/wireframes/` gefüllt (WFR-0001
  eingefroren), und die Restcent-Falle warf der Apparat **ungefragt in seiner ersten
  Interviewfrage** auf. Das ist kein neuer Defekt-Eintrag: der Pilot-4-Mechanismus (P4-2) trat
  nicht auf, und eine Schiene, die den Lauf schneidet, misst Geld, nicht das Kit. Der Punkt
  bleibt als Beobachtung stehen, nicht als Bug.

## Lauf 2 — Update-Durchstich auf echtem Altbestand (3,32 $) — BUG-0059 bestätigt

Echter Altbestand aus `git archive 3598444` + Scaffold jener Zeit → `2026.08.14-9`
(`--help` ohne `update-kit`). Alle drei Messpunkte beantwortet:

- **L10/Ansage: die user-globale SessionStart-Ansage erreicht den PM auch dort, wo das Projekt
  eigene SessionStart-Hooks registriert** — er bot das Update selbst an, nannte beide Versionen,
  und rief später exakt den Pfad auf, den nur diese Ansage nennt.
- **Er fragte vorher — zweimal.** Die Persona sagte erst „Nein, erst planen", das wurde befolgt;
  erst nach erneuter Frage lief die Hebung. Vorarbeit vorher als PR-0001 gesichert.
- **Keine Nutzer-Shell-Zeile.** `2026.08.14-9` → `2026.08.23-3` durch die Brücke; danach
  schweigt die Ansage, und der Bootstrap verweigert sich selbst (rc 2 mit Verweis auf
  `request-approval kit_update` + `update-kit`).

Damit ist das Abnahmekriterium von BUG-0059 live erfüllt: ein Bestand eine Generation zurück
erreicht das aktuelle Kit, ohne dass der Nutzer eine Shell bedient.

## Lauf 3 — Büro-Onboarding, nur Sitzung 1 (5,54 $) — BUG-0061 bestätigt

- **Richtungsfragen: ja** — Verkaufswege, „Was kommt bei dir tatsächlich an", „Was geht bei dir
  RAUS", Firma/Verträge, Unklares; der Apparat fing sogar eine eigene Auslassung der Persona
  (Kontoauszüge genannt, nicht angekreuzt).
- **`business_profile.document_sources`: vorhanden, 10 Einträge, `what` in ihren Worten.**
- **Deckung ohne Nachforderung: erreicht.** 10 Regeln über Finanzen, Lieferanten/Einkauf,
  Vertrieb, Firma, Prüfen — in Pilot 4 Hälfte 3 musste die Persona vier Fächer selbst
  einfordern, hier null; die Retouren-Schublade brachte der Apparat von sich aus ein.
- **`filing_coverage_briefing`: beide Richtungen gemessen** — volle Deckung → schweigt; eine
  Regel entfernt → spricht und nennt die unbedeckte Quelle in ihren Worten plus
  `add-filing-rule`.

Damit ist das Abnahmekriterium von BUG-0061 live erfüllt (derselbe Antwortsatz wie Hälfte 3,
Plan deckt ohne Nutzer-Nachforderung).

## BUG-0062 (Timeouts), beiläufig mitgemessen

Kein Hook-Kill in fünf Sitzungen; alle Gates antworteten innerhalb ihrer Fenster. Die
eigentliche Messung steht seit TSK-0082 in `tools/provider_observations.json`
(`hook_deadlines`) und im Eigenschaftstest; der Live-Lauf widerspricht ihr nicht.

## Benannt, nicht geschönt (Protokoll des Mechanikers)

- Die wörtlich übernommene Lauf-3-Eröffnung trug „nimm bitte Sonnet" mit; gemessene Folge: kein
  Override übergeben, das Kit wies den Wunsch zurück — die Modellmessung ist unbeschädigt.
- Zwei Sonden-Artefakte („KIT DOWNGRADE OFFERED", „PROJECT PATH CHANGED") gehören der Sonde,
  nicht dem Projekt.
- Abschnitt 1 der Lauf-2-Wortlaute war zunächst eine Überschrift ohne Inhalt; statt aus dem
  Gedächtnis gefüllt, wurde die Ansage in einem Wegwerf-Altbestand frisch als Prozess gemessen.
- Repo unverändert (HEAD 297a649); die acht unverfolgten office-Vorlagen unter
  `project_memory/` lagen schon vorher dort (TSK-0082 close-out, Löschung Sache des Nutzers).

## Offen nach diesem Lauf

1. **BUG-0058 AC-2** — honoriert der Provider `exit 2` auf `Stop` in einer echten Sitzung? Nur
   messbar, wenn der Fall live eintritt; die Hook-Seite ist vollständig belegt.
2. **H53** — Lebensdauer von `stop_hook_active` (hängt an demselben Live-Fall).
3. **H59-Wirkung** — bewegt der gesagte Leerstand den PM in Richtung QA? Der Satz existiert
   gemessen; seine Wirkung braucht einen Lauf, der Phase 5 überschreitet.

Alle drei sind Beobachtungspunkte für den nächsten echten Projektlauf, keine Blocker: die
Ketten, die in einer Sitzung durchlaufen, sind geschlossen oder in `docs/POST_V2_WISHLIST.md`
mit Begrenzung benannt.
