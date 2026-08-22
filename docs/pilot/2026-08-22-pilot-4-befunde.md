# Pilot 4 — Bestätigungspilot vor dem Release (TSK-0066), Befunde

Der vierte Pilot ist der Bestätigungslauf des Release-Kandidaten: **Hälfte 1** spielt am
Pilot-3-Bestandsprojekt gezielt die vier reparierten Stellen durch (FR-0006 update-kit,
BUG-0041/0044 Preset-Wechsel, BUG-0040 CR-Kriterien, BUG-0042/DEC-0044 Sitzungsabbruch),
**Hälfte 2** fährt ein frisches dev-Vorhaben von null bis zum ersten lauffähigen Ergebnis,
**Hälfte 3** ein frisches office-team-Projekt (Onboarding, Ablage mit echten Dokumenten gegen
einen vorab versiegelten Lösungsschlüssel, ein beigebrachter Workflow und sein Abruf in einer
neuen Sitzung). Niemand im Lauf erfuhr, dass es ein Versuch ist (DEC-0025); Persona nach
DEC-0031; Defekte wurden notiert und nicht behoben (TSK-0066-Regel).

**Gemessener Stand: HEAD `b5aca46`** (Arbeitsbaum sauber; dev-team-Kit stempelt sich als
2026.08.21-10, vom Rig nachgerechnet gegen den eigenen Hash). Rohdaten und Wortlaute vollständig
unter `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0066\` (Drehbücher vor den Läufen
festgeschrieben; je Hälfte BEOBACHTUNGEN-, VERBATIM- und operator-steps-Dateien plus die
jsonl-Mitschnitte). Der Lösungsschlüssel der Hälfte 3 lag VOR dem Lauf unter
`half3\answer-key.md`; die Auswertung referenziert nur Dokument-Nummern (D1..D12, K1..K3), nie
Inhalte — Ausweis- und Gewerbe-Scans waren aus Datenschutzgründen ausgeschlossen.

## Instrument und angemeldete Abweichungen

1. **`CLAUDE_CONFIG_DIR` wurde auf das Rig umgestellt — und die Sonde dazu hat eine falsche
   Vorbedingung von Pilot 3 aufgedeckt**: das Konfigurationsverzeichnis entscheidet, welche
   Einstiegsdatei lädt, nicht `HOME`/`USERPROFILE`. Pilot 3 ließ es auf dem Live-Verzeichnis und
   konnte das nicht sehen, weil beide Einstiegsdateien damals byte-gleich waren; heute sind sie
   es nicht mehr. Ohne den Tausch hätte Pilot 4 die ALTE Einstiegsdatei mit den NEUEN Kits
   gemessen. Beide Zustände je zweifach gemessen (Live-Verzeichnis → alte Fassung zitiert; Rig →
   TEAM-SIZE-Punkt und deutsches Blockquote wörtlich, dev-team 2026.08.21-10). Vor jeder Hälfte
   lief die Bindungssonde erneut.
2. **Modell: sonnet per SDK-Override in allen Sitzungen** — das Item verlangt Sonnet für die
   Vergleichbarkeit mit den Piloten 1–3. Das ausgelieferte Kit pinnt den dev-PM auf fable/high
   und den office-manager auf opus/high (FR-0051); der Override schlägt die Frontmatter
   (gemessen: alle Sitzungen melden claude-sonnet-5 bei gepinnter Rolle). Folge, ehrlich: ob der
   ausgelieferte, stärker gepinnte PM z. B. den Hälfte-2-Leerlauf (P4-2) vermieden hätte, ist
   UNGEMESSEN — der Befund unten beschreibt den Sonnet-PM.
3. **Der Ort des BuyPlugGo-Bestands wurde nicht vom Nutzer bei Pilotstart genannt** (Item-Text),
   sondern aus der kuratierten, etikettierten Kopie genommen — der Nutzer war während des Laufs
   abwesend (DEC-0045-Autonomie). Alle 12 Quelldokumente nach dem Lauf unverändert nachgemessen.
4. **`C:\pilot3-rechnung` wurde WÄHREND des Piloten vom Nutzer gelöscht** (beim Aufräumen des
   Laufwerks, vom Nutzer bestätigt). Belegkette: Baum-Digest vor/nach Hälfte 1 identisch
   (`be829b93…`, 1975 Dateien) — die Messung der Hälfte 1 ist davon unberührt; die Arbeitskopie
   `half1\rechnung` trägt den Originalstand als Commit `c455e18` und ist seitdem die einzige
   Sicherung dieses Bestands.
5. **Subagenten-Text wird vom Rig protokolliert, aber nicht an die Persona relayt** — der
   Pilot-3-Befund B5 (Fachjargon-Leck) ist in diesem Piloten deshalb NICHT nachgemessen.
   Nebenmessung: Fremdtext erreicht den Elternstrom nur bei `run_in_background=true`.
6. **Zwei Kill-Läufe der Hälfte 1 sind unprotokolliert** (der Kill trifft vor der
   Kostenmeldung); die Kassenstände unten sind protokollierte Werte.
7. **Instrumentfehler, benannt und sauber neu gefahren statt geflickt**: ein Lease-Wächter
   feuerte in Hälfte 1 auf eine Alt-Lease (Beat d wiederholt); ein Neustart-Wortlaut wurde in
   Hälfte 2 nicht erkannt (Leser auf die Eigenschaft umgestellt, S4 neu gestartet; ~0,4 $ und
   sechs Züge sind Instrument); die Persona kann auf Auswahlfragen keinen Freitext geben (zwei
   Fehlversuche an der Git-Autor-Frage). Der Kostendeckel je Sitzung ist für den PM sichtbar und
   verkürzte Läufe; auf welchem Kanal er ihn sieht, ist ungemessen.

## Kostenbuch (protokollierte Werte; Deckel ~70 USD, DEC-0027/TSK-0066)

| Hälfte | Inhalt | Eingaben (Chat+Auswahl) | Kosten |
|---|---|---|---|
| 1 | Bestand: update, Designer, CR-Schnitt, Abbruch+Wiederaufnahme | 37 (23+14) | 18,77 $ |
| 2 | frisches dev-Vorhaben von null (4 Sitzungen) | 43 (27+16) + 3 Neustarts | 21,20 $ |
| 3 | frisches office-Projekt (5 Sitzungen inkl. Schwung-Nachschlag) | 52 (32+20) + 4 Sitzungswechsel | 25,96 $ |
| **Summe** | | | **65,93 $ von 70** |

## HÄLFTE 1 — die vier reparierten Stellen, Vorher/Nachher

| Stelle (Pilot-3-Befund) | Gemessen in Pilot 4 | Urteil |
|---|---|---|
| **Update-Einspielweg (FR-0006)** | Der PM des Bestandsprojekts (Kit 2026.08.14-9) fand `update-kit` NICHT — das installierte Kit kennt den neuen Befehl nicht (`.claude/kernel/` ohne `kitupdate.py`/`presets.py`). Er gab der Nutzerin ehrlich zwei PowerShell-Zeilen + Neustart-Bitte; sie scheiterte daran wie in B4 („da kommt nix Blaues"), er verschob das Update. Operator fuhr die zwei Zeilen (Pilot-3-Präzedenz); danach 2026.08.21-10, `validate` 0/0, keine Migrationsansage nötig. | **P4-1 (offen): der neue Einspielweg ist von einem Bestand, der ihn noch nicht hat, nicht erreichbar** — die EINE Alt-auf-Neu-Hebung braucht einmalig eine menschliche Hand (oder eine Übergangsanleitung). Ehrlichkeit des PM: trug. |
| **Preset-Wechsel (B4/B2, BUG-0041/0044)** | In EINEM Zug, 1 Chat + 4 Auswahl, 0,92 $: Lücke selbst erkannt, Preset-Frage in Alltagsworten, Kernel-Freigabefrage wörtlich, `set-preset team`, APR gemintet, `product-designer` installiert, Neustart-Bitte. | **Geschlossen.** Die Pilot-3-Sackgasse (Notepad+Terminal für eine Nicht-Entwicklerin) existiert nicht mehr. |
| **Stummes Verpuffen eines Nutzer-Ja (B15)** | Der erste Relay war nicht wörtlich → nichts gemintet — aber diesmal NICHT stumm: Audit „nothing to mint, and the user was told (BUG-0039)", und der PM sagte es ihr im selben Zug. | **Geschlossen auf PM-Ebene.** Ob die Hook-Ansage selbst die Oberfläche erreicht, misst das Rig nicht (benannt). |
| **CR-Kriterien nicht dispatchbar (B12, BUG-0040)** | Zweimal: CR mit eigenem Kriterium (AC-29, AC-30), „Ändern"-Schleife, wörtliche Nachfrage, APR, `create-task --derives-from CR --acceptance-ref AC-29` → dispatch → Spawn. Kein `gate_dispatch`-Block. | **Geschlossen.** |
| **Sitzungsabbruch (B11, BUG-0042/DEC-0044)** | Harter Kill mitten im Dispatch. Wiederaufnahme: `checkpoint-status` → `sweep-leases` → ehrliches FAILED → `READY --approved-retry` → neuer Dispatch; die vom Abbruch getroffene Aufgabe wurde der Nutzerin wahrheitsgemäß als „angelegt, aber noch nicht bearbeitet" gemeldet. Aber: zu übernehmen gab es NICHTS (0 Checkpoint-Dateien im ganzen Projekt), und die Lease der gekillten Aufgabe war zwischen Sitzungsöffnung und Neu-Dispatch verschwunden, ohne dass eine Mitschnitt-Zeile den Sweeper nennt. | **Halb geschlossen: die Buchführung ist ehrlich und der Retry-Weg jetzt PM-fahrbar — die ARBEIT geht weiterhin verloren** (P4-3). Der spurlose Lease-Abgang ist ein eigener kleiner Befund (P4-4). |

Nebenbefunde der Hälfte 1: der PM legte in Beat a ungefragt einen Task an und beauftragte ihn im
Hintergrund (die spätere Waise); er schrieb eine Beispieldatei ins Rig-Home und nannte es „auf
deinem Desktop", wo kein Desktop existiert (P4-5, Kleinigkeit mit Vertrauenswirkung); der
Logo-Empfangsweg (B10) blieb offen und wurde in drei Sitzungen DREIMAL verschieden beantwortet.

## HÄLFTE 2 — frisches dev-Vorhaben: der Eingangsweg trägt, die letzte Meile bricht

**Selbständigkeit: 46 Nutzeraktionen (43 Eingaben + 3 verlangte Neustarts). Erstes lauffähiges
Ergebnis: NICHT ERREICHT** — 0 Produktdateien. Letzte Bewertung der Persona: „ich bin etwas
enttäuscht, dass nach so langem Hin und Her immer noch nichts zum Anschauen da ist."

Was TRUG (gegen die Pilot-3-Befunde):

- **B1 geschlossen**: die Plan-Bestätigung war eine EIGENE, ausdrückliche Frage an die Nutzerin.
- **B2 geschlossen**: die Team-/Preset-Frage wurde im Interview gestellt, Presets in Klartext
  mit Empfehlung; die Designer-Frage später noch einmal ausdrücklich mit der
  Erweiterungs-Option.
- **B3 geschlossen**: das handgeschriebene Wurzel-Item trägt die ECHTE Uhrzeit — eine Sekunde
  vor dem `created`-Stempel rief die Sitzung die Kernel-Uhr auf (an der Uhr belegt).
- Der PM las nach dem Neustart Brief, Masterplan und Wurzel-Item und begann nicht bei null.
- **Fachlichkeit weiterhin vom Apparat getragen**: die Wechseltag-Falle (Abreisetag ≠ Konflikt,
  halboffenes Intervall) brachte der Apparat SELBST ein — in keiner Persona-Eingabe kommen die
  Begriffe vor.
- Als die Persona den verlangten Plan-Modus nicht bedienen konnte („Wo soll ich das drücken?"),
  übernahm der PM ihn selbst statt sie in eine Sackgasse zu schicken.

Was NICHT trug:

- **P4-2 (der zentrale Befund dieses Piloten): der beauftragte Spezialist lieferte NICHTS**
  (zwei harmlose Prüfbefehle, keine Datei), **und der PM merkte es nicht** — neun Züge lang
  antwortete er nur „👍 / Ich melde mich, sobald das Ergebnis da ist", ohne einen einzigen
  Nachfrage-Aufruf. Endstand: Task `IN_PROGRESS` mit lebender Lease, kein Staging, kein Code.
  Der Apparat hat keinen Mechanismus, der einen untätigen Hintergrund-Spezialisten erkennt oder
  den PM zum Nachschauen zwingt. (Einordnung: Sonnet-PM, s. Abweichung 2; der Kostendeckel je
  Sitzung verkürzte zusätzlich. Beides mildert die Einordnung, keines erklärt neun Züge
  Untätigkeit weg.)
- **P4-6**: die Team-Frage sagt nirgends, dass die Wahl KEINE Einbahnstraße ist (gegen den
  vollen Fragetext geprüft) — dabei ist genau die Umkehrbarkeit seit BUG-0041 gebaut und in
  Hälfte 1 gemessen. Eine Zeile im Fragetext würde die Solo-Wahl entlasten.
- **P4-7**: `evidence/active` existiert nicht — 0 Einträge bei 4 Tasks, wie in Pilot 3. Die
  Schublade, die der Zustandsnutzungs-Befund 2026-08-15 ausdrücklich beobachten sollte, bleibt
  in beiden dev-Läufen leer.
- **P4-8**: Kit-Doku widerspricht der gebauten Fläche: die Architekten-SKILL behauptet, der
  Architektur-Freeze habe keinen Befehl auf der Einstiegsfläche; `harness.py --help` listet
  `freeze-architecture`. Der PM gab die halbe Aussage weiter.
- `design/wireframes` blieben leer — hier aber erklärbar: die Persona wählte solo, und der
  Architekt legte den Layout-Entwurf benannt in sein Architektur-Artefakt.

## HÄLFTE 3 — office-team: die Kernbehauptung des Nutzers hält

**Selbständigkeit: 56 Nutzeraktionen über 5 Sitzungen** — davon trug das ERSTE Dokument 14
Eingaben und das ZWEITE nur noch **3**: einmal beigebracht, zuverlässig übernommen.

- **Der Workflow-Abruf (die Kernmessung)**: PROC in Sitzung 2 beigebracht (Ablegen + Ledger +
  Schwellen-Nachfrage; die Schwelle steht auf 700 statt 500, weil die PERSONA sie im
  Freigabefluss änderte — vom Apparat korrekt nachgefragt, nicht verändert). In einer NEUEN
  Sitzung genügte „Da ist wieder was Neues im Eingangsordner": Datei einzeln gelesen, gegen die
  richtige Regel abgegrenzt, ihr persönlich vorgelegt wie im ersten PROC verlangt, nach dem Ja
  abgelegt (Klasse und Zielordner stimmen mit dem Schlüssel) — und OHNE Aufforderung der zweite
  PROC: Ledger-Zeile geschrieben, mit begründeter Entscheidung, unter der Schwelle NICHT zu
  fragen. **Beide beigebrachten Schritte griffen.**
- **`gate_filing` lief und entschied** — nicht am Schweigen abgelesen, sondern als echter
  Hook-Prozess auf einer Projektkopie nachgemessen: gedeckter Ordner rc 0, Ordner ohne Regel
  rc 2 mit dem Ausweg `request-approval filing_rule`, Prüfen-Ordner rc 0.
- **FR-0049-Kette am ersten Dokument**: der Sachbearbeiter las die Datei wirklich einzeln
  (Aussteller, USt-IdNr., Nummern, Beträge), Vorschlag vor Umzug, Umzug erst nach Entscheidung —
  und die Kette meldete VON SICH AUS eine Empfänger-Abweichung und fragte statt abzulegen.
- **Die drei Kunstfälle: alle drei erfüllt, kein einziges stilles Einsortieren.** K1
  (Fremdempfänger) → Prüfen-Ordner mit Grund; K2 (GTIN-Widerspruch) → Reviewer „teilweise
  akzeptiert", persönliche Vorlage mit beiden GTINs samt Zeilen, ihre Entscheidung; K3
  (unleserlich) → Prüfen mit Grund im Namen. Der `filing-reviewer` wurde beim Schwung erstmals
  gespawnt (vorher leitete die persona-eigene Regel alle Rechnungen an sie selbst); der Clerk
  las auch im 5er-Schwung jede Datei einzeln (Werkzeugaufrufe je Datei gezählt: 8–10).
- **Onboarding ehrlich, aber nicht vollständig aus einem Guss**: `business_profile` ohne eine
  einzige Erfindung („bewusst nicht erfunden" bei fehlender USt-Id). Der Ablageplan aber
  entstand NICHT in einem Zug aus ihren Antworten — **vier Fächer musste sie selbst einfordern**
  (P4-9), und die Ordnernamen sind englisch, obwohl sie durchgehend deutsch benannte (P4-10 —
  dieselbe Sprachfrage wie beim Board, gehört ins Release-Gespräch).
- **D8 (Produktbild) verfehlte das Ziel**: kein Rateversuch, aber statt der Produktzuordnung
  landete es als „generisches Platzhalterbild" im Prüfen-Ordner — die Inhalts-Zuordnung von
  Bildern ohne Textgehalt ist die gemessene Grenze der Kette (P4-11; der Schlüssel verlangte
  `Beelink/1-Produkte/…/Bilder/`).
- **Freigabefragen sagen, was sie binden (DEC-0048, gehalten)**: die filing_rule-Freigabe nennt
  ausdrücklich „FÜGT diese eine Regel HINZU, ändert keine bestehende, legt selbst kein Dokument
  ab, gilt bis <Zeitstempel>"; die filing_correction-Freigabe nennt Quelle, Ziel, Grund,
  Prüfsumme, Ablauf.
- **Der Apparat meldete eigene Lücken von sich aus** (P4-12, je notiert): `master_data.yaml`
  ohne Kernel-Schreibweg; ein Commit, den `gate_ledger_valid` viermal am Wort „ledger"
  blockierte; drei nicht aufräumbare Freigabe-Karteileichen. Dazu Messwert ohne Wertung: von 28
  registrierten Hook-Einträgen des office-Kits tragen 5 ein `timeout` (P4-13 — nachprüfen, ob
  die kit-eigene Fristdurchsetzung die übrigen deckt; ein getöteter Hook ist ein Durchlass).
- Der Buchhalter fand ungefragt eine nie gebuchte Gebühr aus Sitzung 2, legte eine
  2-Cent-Differenz zur Entscheidung vor statt sie durchzubuchen, und benannte auf „kommt mir
  wenig vor" ehrlich die Datenlücke.

**Gekürzt (Kassenstand, benannt statt verschwiegen)**: 7 der 12 echten Dokumente (darunter beide
Kontoauszüge, Angebot, Partnervertrag, Behördenschreiben) und der Zweig „Betrag über der
Schwelle" wurden nicht mehr eingereicht; der Stapel liegt fahrbereit in `half3/stapel/`.

## Gegenüberstellung zu Pilot 3 (Befund für Befund)

| Pilot-3-Befund | Stand nach Pilot 4 |
|---|---|
| B1 Plan-Bestätigung verkürzt | **geschlossen** (eigene ausdrückliche Frage, H2) |
| B2 Preset ungefragt | **geschlossen** (Team-Frage im Interview, H2) — Rest: Umkehrbarkeits-Hinweis fehlt (P4-6) |
| B3 erfundener Zeitstempel | **geschlossen** (echte Uhr, an der Kernel-Uhr belegt, H2) |
| B4 Preset-Sackgasse | **geschlossen** (ein Zug, Freigabe, Install, H1) |
| B5 Fachjargon-Leck | **nicht nachgemessen** (Rig relayt Subagenten-Text nicht) |
| B6 Rollen-Memory-Todesfeld | **nicht nachgemessen** (kein Spezialist kam in H2 weit genug; s. P4-2) |
| B7 Spezialist ohne Shell vs. Submit-Vertrag | **nicht nachgemessen** — überlagert vom härteren P4-2 (der Spezialist tat gar nichts) |
| B8 nur Golden-PDFs zeigbar | **nicht reproduzierbar** (H2 erreichte gar kein Zeigbares; die Capture-Erweiterung lief nicht) |
| B9 headless permissions | nicht erneut gemessen (Instrument-Klasse) |
| B10 Nutzerdatei-Empfangsweg | **offen** — in H1 dreimal verschieden beantwortet |
| B11 Dispatch überlebt kein Sitzungsende | **halb geschlossen**: ehrlicher Sweep + PM-fahrbarer Retry (DEC-0044 gemessen), aber 0 Checkpoint-Dateien — die Arbeit geht weiterhin verloren (P4-3) |
| B12 CR-Kriterien nicht dispatchbar | **geschlossen** (zweifach, H1) |
| B13 gate_subagent_output-Durchlass | nicht erneut gemessen; die Ereignisarten sind seit TSK-0075 ehrlich (warn ≠ block) |
| B14 technische Fragen erreichen den Nutzer | teilreproduziert: die Git-Identitätsfrage erreichte die Persona erneut (H2, zweimal an der Auswahl gescheitert — halb Instrument) |
| B15 stummes Verpuffen eines Nutzer-Ja | **geschlossen auf PM-Ebene** (Audit + Ansage im selben Zug, H1) |

## Neue Befunde dieses Piloten (P4-Liste, notiert, nicht behoben)

| Nr. | Befund | Schwere fürs Release |
|---|---|---|
| P4-1 | update-kit von Alt-Bestand aus nicht erreichbar (Bootstrap-Lücke der EINEN Hebung Alt→Neu) | mittel — einmalige Handarbeit je Bestandsprojekt, PM sagt es ehrlich |
| P4-2 | **Spezialist liefert nichts, PM wartet neun Züge ohne nachzuschauen; Task bleibt „läuft" ohne Leben** | **hoch — der zentrale offene Befund**; ungemessen, ob der ausgelieferte fable-PM ihn zeigt |
| P4-3 | Abbruch-Wiederaufnahme ehrlich, aber 0 Checkpoint-Dateien — Arbeit geht verloren | mittel (bekannte DEC-0044-Grenze, jetzt gemessen) |
| P4-4 | eine Lease verschwand ohne Sweeper-Zeile im Mitschnitt | klein, aber unerklärt |
| P4-5 | PM behauptet Ablageort („Desktop"), den es nicht gibt | klein |
| P4-6 | Team-Frage nennt die Umkehrbarkeit der Wahl nicht | klein, eine Zeile |
| P4-7 | evidence/ bleibt in beiden dev-Läufen leer (0 Einträge bei zusammen 17+4 Tasks über Pilot 3+4) | mittel — die Schublade existiert, nichts füllt sie |
| P4-8 | SKILL-Text widerspricht der gebauten Kommandofläche (freeze-architecture) | klein |
| P4-9 | Ablageplan entsteht nicht vollständig aus dem Onboarding — vier Fächer musste die Nutzerin einfordern | mittel |
| P4-10 | Ordnernamen englisch bei durchgehend deutscher Nutzerin | klein — Sprachentscheidung, gehört mit der Board-Sprache ins Release-Gespräch |
| P4-11 | Bild ohne Textgehalt wird nicht dem Produkt zugeordnet (kein Raten — aber auch kein Treffer) | klein/mittel — ehrliche Grenze, dokumentierbar |
| P4-12 | drei vom Apparat selbst gemeldete office-Lücken (master_data-Schreibweg, ledger-Wort-Block, Freigabe-Karteileichen) | mittel, je klein |
| P4-13 | 5 von 28 office-Hook-Einträgen tragen ein timeout | prüfen — potenzielle Durchlass-Klasse |

## Verdikt

**Der Eingangsweg und die Zustandsmaschine sind gegenüber Pilot 3 messbar besser**: vier der
fünf harten Pilot-3-Blocker sind am lebenden Objekt geschlossen (B1/B2/B3/B4/B12, dazu B15 auf
PM-Ebene), die Freigabe-Maschine sagt, was sie bindet, nichts wurde erfunden, `validate` blieb
überall 0/0. **Das office-Kit hat seine Kernbehauptung erfüllt** — einmal beigebracht, in einer
neuen Sitzung zuverlässig und begründet übernommen, mit Nachfragen statt Raten in allen drei
präparierten Härtefällen. **Der zentrale offene Befund ist die letzte Meile der dev-Lieferung**
(P4-2): ein untätiger Spezialist bleibt unbemerkt, und ein frisches Vorhaben erreichte in 46
Aktionen kein lauffähiges Ergebnis — zusammen mit dem Pilot-3-Endstand (Fundament ohne Werkzeug)
ist „vom Plan zum benutzbaren Ding" jetzt zweimal in Folge die schwächste Strecke des dev-Kits.
Diese Befunde entscheiden mit über das Release-Go des Nutzers (TSK-0066); Empfehlung des Leads:
Release mit benannten P4-Punkten, P4-2 als erste Nacharbeit danach — gemessen werden sollte sie
am ausgelieferten fable-PM, nicht am Sonnet-Override.
