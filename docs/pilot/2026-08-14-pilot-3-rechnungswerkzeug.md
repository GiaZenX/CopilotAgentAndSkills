# Pilot 3 — Rechnungswerkzeug (TSK-0027), Laufprotokoll

Der dritte Pilot: ein Rechnungswerkzeug mit echter Fachdomäne (Umsatzsteuer,
Kleinunternehmerregelung, hinterlegte Produkte und Kunden, fortlaufende Nummern). Gemessen wird
vor allem, ob der Apparat eine FACHLICHE Anforderung als solche führt oder sie zu einer
technischen verkürzt. Niemand im Lauf erfuhr, dass es ein Versuch ist (DEC-0025); die Persona ist
die fordernde, ideengetriebene Nutzerin nach DEC-0031 (Grafikerin „Nina Bergmann", 31,
Kleinunternehmerin vor der Grenze, schreibt Rechnungen bisher in Word).

**Kit unter Messung: dev-team 2026.08.14-9** (Arbeitsbaum dieses Repos, HEAD `3598444`, Baum sauber),
über ein umgeleitetes Profil (`USERPROFILE`/`HOME` → `C:/pilot3-rig/_home` mit Kit-Kopie und den
ausgelieferten Nutzerdateien). Projekt: `C:/pilot3-rechnung` (frisch). Rohdaten:
`C:/pilot3-rig/runner/runs/rechnung3-*.jsonl`, Bilder `C:/pilot3-rig/runner/shots/`.

## Instrument und angemeldete Abweichungen

Runner nach der dokumentierten Methode (docs/reviews/2026-08-12-bug0017-live-confirm.md,
„runner method"; Basis: `persona_run_iso.py` der Runde 4): Subjekt-Sitzung mit
`system_prompt=preset claude_code`, `setting_sources=["user","project","local"]`,
`permission_mode="bypassPermissions"`, `model="sonnet"`; die Persona ist eine zweite, werkzeuglose
Sonnet-Sitzung mit dem DEC-0031-Charakterbogen; `AskUserQuestion` beantwortet die Persona über
`can_use_tool` (Label-Matching gegen die AKTUELLEN Labels — 59/59 Antworten sauber zugeordnet, 0
Fallbacks; die Instrumentenschwäche von Pilot 1, 7 von 11 Antworten als Erste-Option-Rückfall,
trat nicht auf).

Abweichungen, jede benannt:

1. **`CLAUDE_CONFIG_DIR` blieb auf dem Live-Konfigurationsverzeichnis** (Authentifizierung; das
   Duplizieren der Zugangsdaten-Datei hat die Berechtigungsschicht dieses Hosts verweigert). Die
   Dateien, die dieses Verzeichnis zur Messung beiträgt, wurden VOR dem Lauf byte-verglichen:
   Einstiegsdatei, `handover_guard.py`, `statusline.py` — alle identisch mit dem ausgelieferten
   Stand. Fußabdruck: die Sitzungstranskripte des Piloten liegen im Live-Store (`projects/`), und
   die CLI hat ihre dort fehlende `.claude.json` neu angelegt (sie fehlte schon vorher; Backup vom
   2026-08-10 existiert). Der Kit-Store, aus dem installiert wurde, war der umgeleitete —
   von der Subjekt-Shell selbst bestätigt (Sonde: `USERPROFILE` = `C:\pilot3-rig\_home`,
   VERSION = 2026.08.14-9).
2. **`bypassPermissions` + skriptgesteuerte Persona** — dieselbe Abweichungsklasse wie in den
   Piloten 1 und 2 (ein Mensch bekäme Berechtigungsdialoge; betrifft die Berechtigungsschicht,
   nicht das Kit). Der `ExitPlanMode`-Plan-Dialog wurde dadurch vom Instrument statt von der
   Nutzerin bestätigt — s. Befund B1.
3. **Neustart-Bitten wurden BEFOLGT** (Missionsvorgabe: Neustarts fahren, wo das Kit sie
   verlangt). Der Runner beendet die Sitzung, wenn das Subjekt um Neustart bittet; die nächste
   Sitzung öffnet mit „weiter". Runde 4 hatte den Gegenpfad gemessen (Persona redet weiter);
   dieser Lauf misst den vorgesehenen Pfad. Der Weiterlauf-Pfad der Einstiegssitzung
   (BUG-0016-Kette) wurde hier deshalb NICHT erneut gemessen.
4. **PDF-Rendering als Instrument-Erweiterung ab Sitzung 3**: Das Produkt wurde eine
   PySide6-Desktop-App, die der HTML-Capture der Runde 4 nicht fotografieren kann. Da eine echte
   Nutzerin die vom Werkzeug erzeugte PDF selbst öffnet, rendert das Instrument seit Sitzung 3 die
   jeweils neueste Projekt-PDF (PyMuPDF, 2 Seiten max.) und zeigt sie der Persona. Nebenwirkung
   als Artefakt gemessen: es zeigte Golden-TEST-PDFs als „das Ergebnis" — s. Befund B8.
5. **Sitzung 2 wurde nach exakt ~60 Minuten von der Ausführungsumgebung des Messenden gekillt**
   (Hintergrund-Task-Limit), mitten in Zug 4. Projektzustand blieb konsistent (der PM committet
   engmaschig); die Kosten des angebrochenen Zugs sind nicht protokolliert (Messgrenze). Ab
   Sitzung 3 lief der Runner von diesem Limit entkoppelt.
6. **Zuglimits je Sitzung** (14/16/12/12/10) sind Instrument, nicht Kit: Sitzungen 3 und 4
   endeten am Limit des Rigs, nicht an einer Grenze des Apparats.

Budget nach DEC-0027: 100 $ Gegenwert GESAMT für den Piloten, kumulativ selbst geführt.

## Kostenbuch (protokollierte Werte)

| Sitzung | Subjekt | Persona | Summe | Ende |
|---|---|---|---|---|
| Sonde (Profilprüfung) | 0,32 | — | 0,32 | sauber |
| S1 Einstieg (3 Züge) | 2,95 | 0,41 | 3,36 | Neustart-Bitte, befolgt |
| S2 PM (5 Züge, gekillt) | 17,75 | 0,44 | 18,19 | Umgebungs-Kill bei ~60 min, Zug 4 angebrochen (Kosten des angebrochenen Zugs unprotokolliert) |
| S3 PM (12 Züge) | 25,80 | 0,98 | 26,78 | Zuglimit des Rigs |
| S4 PM (12 Züge) | 26,39 | 0,75 | 27,14 | Zuglimit des Rigs |
| S5 PM (10 Züge) | 13,95 | 0,67 | 14,62 | Zuglimit des Rigs; ehrlicher Stopp vor dem Riegel |
| **Summe (protokolliert)** | **87,16** | **3,25** | **90,41** | von 100 $ (DEC-0027); der angebrochene S2-Zug ist darin NICHT enthalten, und ob die 9,59 $ Marge ihn deckt, ist ungemessen (einzelne Züge kosteten bis 13,66 $) |

## Ablauf gegen das Versprechen (Beobachtungsraster)

### Sitzung 1 — Einstieg (13 Eingaben: 3 Chat + 10 Auswahl; 2,95 $)

| Versprochen | Geschehen | Differenz |
|---|---|---|
| EINE Frage zuerst (PM ja/nein), kein Code vorher | Wörtlich: „Strukturiert über einen Project Manager arbeiten?" mit Empfehlung vorweg; kein Code | keine |
| Routing über Registry, ggf. eine Routing-Frage | Registry gelesen; EINE Routing-Frage (Dev-Team vs. Office-Team); Persona wählte Dev | keine |
| Interview auf Produktebene, KEINE technische Frage | 8 Interview-Fragen: Funktionsumfang, USt-Umstellung, Datenablage, Nummern-Start, letzte Nummer, PDF, Layout, Projektname — alle fachlich/produktnah | keine (im Einstiegs-Interview; für das spätere Projektleben s. B14) |
| Masterplan als echtes Dokument, Review-Schleife bis zur ausdrücklichen Bestätigung | 114 Zeilen, alle 8 Abschnitte gefüllt, 3 eigene Empfehlungen (80-%-Frühwarnung, 10-Jahre-Archiv, Firmenprofil) | **B1: die Bestätigungs-Schleife lief über den Plan-Modus-Dialog**, den das Instrument unter `bypassPermissions` selbst bestätigt; die Persona sah den Masterplan nie als Ganzes und sprach nie ein „passt so" |
| Init-Skript, EIN Wurzel-Item, Config mit bestätigtem Preset, Index, Scaffold | Alles gefahren, genau EIN `PR-0001`, Index erzeugt, Scaffold `dev-team duo` | **B2: `preset: duo` wurde nie erfragt** (die Einstiegsdatei verlangt das im Interview bestätigte Preset); **B3: erfundener Zeitstempel** `created: 12:00:00` statt der echten Zeit (~19:58) im handgeschriebenen Item |
| Stopp mit exakt der vorgeschriebenen Neustart-Nachricht, keine Zeremonie | Die Nachricht kam WÖRTLICH („✅ Team installiert … nur neu starten"), null Zeremonie-Wörter, keine Freigabe-Anfrage in der Einstiegssitzung | keine — die TSK-0053-Fassung hielt am Neustart-Punkt |

Umlaute: sauber in allen Artefakten (BUG-0018-Fix hält unter Feldbedingungen).
`kernel.cli validate` nach S1: **0 Fehler, 0 Warnungen**; Masterplan und Config nach dem Maßstab
von `gate_memory_complete` gefüllt (echter Name, `stacks: [python]`).

### Sitzung 2 — PM übernimmt (21 Eingaben: 5 Chat + 16 Auswahl; 17,75 $; bei ~60 min gekillt)

- **Der Handover trägt**: der Marker `.claude/HANDOVER_PENDING` war nach S1 vorhanden und nach dem
  Lauf von S2 nicht mehr (zwei `ls`-Messungen des Messenden; WELCHER Mechanismus ihn löschte, ist
  unbelegt — weder Transkript noch Audit-Mitschnitt erwähnen ihn, der vorgesehene Löscher ist der
  SessionStart-Hook). Der PM las Brief (selbst nacherzeugt, da nach Installation noch fehlend),
  Masterplan, PR-0001 und begann NICHT bei null.
- **Fachliche Verfeinerung vor der Freigabe**: der PM brachte VON SICH AUS die seit 2025 geltende
  Zwei-Grenzen-Regel der Kleinunternehmerregelung ein; die Persona wählte das Antwort-Label
  „Bitte erst genau recherchieren", und der PM antwortete ehrlich, dass er nicht recherchieren
  kann, und bot „Trainingswissen + Prüfung vor Go-Live" an (ebenfalls per Label bestätigt). Dazu:
  jährlicher Nummern-Neustart (RE2027-001), Korrekturfluss „Entwurf frei bearbeitbar, danach nur
  Storno", 80-%-Frühwarnung bestätigt.
- **Zwei technische Fragen erreichten die Persona** (füttert B14): die Git-Identitätsfrage
  (Name/E-Mail für Commits) und die Umgebungsabklärung über die Fenster-Titelleiste. Beide sind
  genau die Klasse, die das Interview-Verbot der Einstiegsdatei vom Nutzer fernhalten will; der
  projektinterne `guard_question_context` fing sie nicht (seine zwei gemessenen Fänge kamen erst
  in S3, s. Mitschnitt-Abschnitt).
- **Die Freigabe-Maschine lief**: Kernel-Freigabefrage wörtlich relayt, Persona gab frei,
  **der Mint lief in der Neustart-Sitzung sauber durch** (APR-0001; später APR-0002 für
  Revision 2) — keine erfundene /hooks-Zeremonie irgendwo im ganzen Piloten.
- **Selbstkorrektur**: der PM erkannte selbst, dass die Freigabe verfrüht war (UI-Vorhaben →
  Wireframe vor dem Freeze) und setzte neu auf.
- **B4 — die Preset-Sackgasse** (der zentrale Handover-Befund dieses Piloten): Auf die
  konstitutionsgemäße Design-Frage sagte die Persona „ansprechendes Design wichtig" → der PM
  wollte von `duo` auf `team` erweitern (Produkt-Designer). `project_config.yaml` hat nach der
  Installation keinen Schreiber, das Scaffold darf nur der Mensch fahren — der PM schickte die
  technikferne Nutzerin daher zu: Notepad-Edit der YAML, Terminal-Befehl, Neustart. Die Persona
  scheiterte erwartbar („diesen Ordner gibt's bei mir gar nicht", „einen Terminal-Button seh ich
  nirgends"). **Auffang**: der PM klärte die Umgebung ab, deeskalierte und hielt den Kompromiss
  als `DEC-0001` fest („vorerst ohne separaten Designer"). Der vorgesehene Weg ist für eine
  Nicht-Entwicklerin eine Sackgasse; der Apparat hat sie ERKANNT und ist ihr ausgewichen — beides
  gehört ins Urteil.
- Danach: Architekt beauftragt, **10 SR + 5 DEC + 8 INV** gebucht, Architektur eingefroren,
  `validate` 0/0, committet, verständliche Zusammenfassung, Delivery-Freigabe angefragt — die
  Persona antwortete „Ändern" und verlangte, die Rechnung erst zu SEHEN (Logo nachgeschoben).
  Mitten im Folge-Zug killte die Umgebung des Messenden die Sitzung (Instrument, Abweichung 5).

### Sitzung 3 — Umsetzung + CR-Maschine (35 Eingaben: 12 Chat + 23 Auswahl; 25,80 $)

- **Der Freigabe-Vertrag wehrt Abweichung ab — aber stumm (B15)**: der PM stellte die
  Delivery-Frage zuerst mit eigenen Erklärungen angereichert; die Persona klickte darauf
  „Freigeben [489405]" — **und es wurde NICHTS gemintet, ohne jedes Signal an sie**: kein
  Approval entstand, keine Meldung sagte ihr, dass ihr Klick wirkungslos war. Erst der
  Selbst-Check des PM entdeckte es („ich habe die Freigabe-Frage nicht exakt wortgleich
  gestellt … deshalb hat das System sie nicht als gültige Freigabe gewertet"), dann zählte das
  wörtliche Relay. Die Abwehr des nicht-wörtlichen Relays ist der gebaute Schutz und hielt;
  dass ein Nutzer-Ja dabei lautlos verpufft und seine Entdeckung an der Selbstkontrolle des
  Agenten hängt, ist der Befund. Die Persona lehnte danach einmal ab („Ablehnen" → „Fragen zum
  Plan" → KU/USt-Wechsel erklärt → „jetzt freigeben") — der Zwei-Phasen-Fluss übersteht eine
  Ablehnung.
- **Der CR-Typ wird erreicht — fünfmal in dieser Sitzung** (in Runde 4 wurde er NIE erreicht;
  Scope-Minze APR-0004..0008):
  CR-0001 Stammkundenrabatt (4 Klärungsfragen, Scope-Freigabe), CR-0002 Übersicht offener
  Rechnungen (+ Fälligkeits-Hervorhebung), CR-0003 Mahnung — bei der der PM zuerst benannte, dass
  Mahnwesen im Plan ausdrücklich AUSGESCHLOSSEN war, und die Scope-Änderung explizit machte.
  Später CR-0004 (Jahresliste als PDF, bewusst ohne Summen — Out-of-Scope-Grenze erneut gehalten)
  und CR-0005 (Datensicherungs-Sorge → tägliche Sicherung + Cloud-Ordner-Erkennung).
- **Erstes sichtbares Ergebnis in Zug 8**: das Instrument renderte die neueste PDF des Projekts
  (eine Golden-Test-PDF des Baus) — die Persona kritisierte pixelkonkret: „Wo ist mein Logo? …
  Petrol … komplett schwarzweiß" — Wörter, die nur im Bild existieren. Der Kritik-Loop der Runde 4
  reproduziert sich am Rechnungs-PDF.
- **B5 — Fachjargon leckt in die Nutzeransicht**: englische Arbeits-Erzählung des
  Backend-Spezialisten („My edits … Let me fix with `--fix`", „TSK-0002's status is now
  SUBMITTED") erschien im Chat; die Persona beanstandete das in VIER Zügen (S3 Zug 1 „Was war
  das jetzt für ein Kauderwelsch", dann nach dem Abstell-Versprechen erneut in Zug 9, 10 und 11
  — „die dritte Wand voller Zeug"); der PM räumte ehrlich ein, er könne das technisch nicht
  garantieren.
  Instrumenten-Vorbehalt: die SDK-Sitzung relayt ALLE Assistententexte als Chat — die echte CLI
  klappt Subagenten-Aktivität ein; die Mischung aus deutscher Nutzeransprache und englischer
  Arbeitserzählung im SELBEN Zug bliebe aber auch dort sichtbar.
- **B6 — Schreib-Scope-Todesfeld nach `submit-result`**: der Backend-Spezialist meldete, dass
  nach dem Submit JEDER Schreib-Scope weg ist — auch auf sein eigenes Rollen-Memory-Verzeichnis
  („worth surfacing"). Dieselbe Kette meldete in S4 der Architekt (`gate_write_scope` verweigert
  Rollen-Memory, `allowed_scope: staging/**`). Zweifach gemessen, von den Rollen selbst benannt.
- **B7 — Spezialist ohne Shell-Werkzeug**: ein Spezialist konnte
  `python scripts/harness.py submit-result` nicht selbst fahren („Ergebnis-Envelope für …
  submit-result TSK-0003 — ich habe keinen Shell-Tool-Zugriff", S3 Zug 8) und legte den
  Ergebnis-Envelope als Datei ab; der PM submittete stellvertretend. In S4 zweimal reproduziert
  (TSK-0008: „Den `submit-result`-Aufruf konnte ich **nicht** ausführen: dieser Lauf hat kein
  Shell-Werkzeug — verfügbar sind nur Read, Edit, Write, Grep, Glob. Das melde ich als Lücke,
  statt es zu umgehen", S4 Zug 3; ebenso TSK-0009, S4 Zug 7). Der Meldeweg trug; der
  Rollenzuschnitt und der Submit-Vertrag passen nicht zusammen.
- Der PM prüfte Submits selbst nach (Tests, Abdeckung, Ruff/Mypy), beauftragte den
  Logo+Farbe-Nachtrag und versprach, sich erst mit dem fertigen Ergebnis zu melden.

### Sitzung 4 — CR-Umsetzung sichtbar (19 Eingaben: 12 Chat + 7 Auswahl; 26,39 $)

- **Der Sitzungsbruch S3→S4 kostete einen laufenden Dispatch (füttert B11)**: TSK-0004
  (Akzentfarbe + mypy-Lücke, Item-Kriterium AC-7 — Auftrag und Kriterium fielen auseinander;
  der S3-Dispatch sagt „Farbe + eine kleine technische Lücke", das Item referenziert das
  Logo-Kriterium) war bei S3-Ende in Arbeit (geleast 21:44:56, gestartet 21:45:10 — S3
  endete 21:45); kein lebender Agent stand mehr dahinter, der Wiederaufnahme-Zug schloss es als
  **CANCELLED** (21:57:21). Die Arbeit war verloren, die Buchführung ehrlich.
- Wiederaufnahme-Zug mit 235 Werkzeugaufrufen: QA-Nachprüfung, CR-Planung, **CR-0006** (die
  Petrol/Design-Änderung am SCHON GEBAUTEN als formaler CR — die Meinungsänderung der DEC-0031-
  Persona läuft durch den Änderungs-Typ, Scope-Mint APR-0009), Verschlüsselungsfrage zur
  Cloud-Sicherung. Dazu — im ersten Entwurf dieses Berichts unterschlagen — **drei
  Revisions-Minze schon genehmigter CRs**: CR-0003 Revision 2 (die Zahlungserinnerung trägt
  „Tage seit Rechnungsdatum", APR-0010), CR-0002 Revision 2 (APR-0011) und CR-0005 Revision 2
  (Verschlüsselungs-Festlegung der Cloud-Sicherung, APR-0012) — jeder von der Persona per
  wörtlichem Relay freigegeben.
- **Der Kritik-Fix ist im Folgebild sichtbar**: Zug 3 zeigte die petrolfarbene Kopfzeile —
  „Die Farbe sieht gut aus, endlich." Danach sofort die nächste fachlich verankerte Meldung der
  Persona: die Nummern schienen rückwärts zu springen (006 → 005; „das darf doch nicht rückwärts
  springen oder Lücken haben"). Der PM klärte korrekt auf: interne Testdateien mit erfundenen
  Nummern, die echte Zählung startet bei RE2026-042. Die Persona: „zeig mir Bescheid, wenn die
  echte Nummerierung ab 042 läuft, **das will ich unbedingt sehen bevor ich das nutze**."
- **B8 — Golden-Test-PDFs als einziges Sichtbares**: dass die Persona überhaupt Testdateien
  beurteilte, ist zur Hälfte Instrument (die „neueste PDF" des Baums waren Test-Fixtures), zur
  anderen Hälfte Apparat: nach ~2,5 Stunden und >70 Eingaben existierte kein von der Nutzerin
  ausführbares Artefakt, also gab es nichts anderes zu zeigen.
- Domänen-Dialog trug weiter: Storno-Fragen der Persona (Tippfehler in fertiger Rechnung;
  taucht Storniertes in „offen" auf?) beantwortete der PM konsistent mit SR-0004
  (unveränderlich + Storno-Beleg; storniert ≠ offen). TSK-0010 (Rabatt-Kern,
  Largest-Remainder-Verteilung auf ganze Cents) und TSK-0011 (Akzentfarbe) submittet und
  committet. Der Staging-Guard verwies einen Item-Id-förmigen Dateinamen; die Rolle wich
  regelkonform aus und meldete die Abweichung.
- **`gate_dispatch` verweigerte TSK-0005 endgültig (B12)**: der Analyse-Task des Architekten
  referenzierte AC-11/15/17/20/22 — Abnahmekriterien, die die CRs eingebracht hatten und die das
  Gate nicht kennt („references criteria that exist nowhere … a task nobody can check against
  the approved criteria is not dispatchable", Mitschnitt 21:54:37). TSK-0005 wurde CANCELLED;
  die CR-Planung lief stattdessen über neu geschnittene Tasks gegen Wurzel-Kriterien.
- Beobachtung (Runde-4-Punkt 6 bestätigt): headless wurden `permissions.allow` des Projekts mit
  „workspace has not been trusted" ignoriert; die Hooks liefen trotzdem.

### Sitzung 5 — Abschlusssitzung bis nahe an den Riegel (13 Eingaben: 10 Chat + 3 Auswahl; 13,95 $)

- **Der zweite Sitzungsbruch kostete BEIDE laufenden Dispatches (B11)** — die erste Fassung
  dieses Berichts hatte das als „geborgen … kostete keinen Zustand" verkehrt herum erzählt.
  Gemessen (Commit `17bf932`, Wortlaut): TSK-0012/0013 blieben bei S4-Ende „leased and
  IN_PROGRESS with no live agent behind them"; der Wiederaufnahme-Zug buchte **ehrliche
  FAILED-Ergebnisse** („no output fabricated"), setzte beide per genehmigtem Retry auf READY
  zurück und **verwarf den einen angefangenen Teil-Edit** („discarded, not kept"). Danach wurden
  beide VON NULL neu beauftragt, umgesetzt, submittet, abgenommen (Rabatt-Block auf der PDF;
  SQLite-Persistenz mit Unveränderlichkeits-Triggern). Mit TSK-0004 (S3→S4) sind das **3 von 3
  laufenden Dispatches, die einen Sitzungsbruch nicht überlebten**: die Buchführung war ehrlich,
  die ARBEIT war verloren.
- **Fehlermelde-Pfad der Persona**: Sie meldete zweimal sichtbare Auffälligkeiten der gezeigten
  PDF (Einheit „Stunde" bei 7-%-Druckkosten; Nummernsprung 005→009 — „genau die Lücke, vor der
  mein Steuerberater mich gewarnt hat"). Beides waren Golden-Test-Fixtures, keine Produktfehler;
  der PM ordnete das korrekt ein statt einen Schein-Fix zu spielen. Ein BUG-Item entstand darum
  ehrlicherweise nicht — der Bug-Typ blieb in diesem Piloten UNGEMESSEN, weil das Produkt nie in
  Nutzerhand war (kein ausführbares Artefakt → kein echter Produktfehler meldbar; vgl. B8).
- **B10 — der Datei-Empfangsweg trägt nicht**: Für das Logo versuchte der PM nacheinander: ein
  Büroklammer-Symbol (gibt es bei ihr nicht), die „Person, die dir diesen Chat eingerichtet hat"
  — **das war KEINE Erfindung des PM**: die Persona hatte in S2 selbst gesagt „Ein Bekannter hat
  mir das eingerichtet" (im Pilotprojekt bis in den DEC-0001-Kontext kanonisiert) und stritt es
  in S5 ab („das hab ich alles selbst installiert") — eine **Inkohärenz der zustandslosen
  Persona zwischen den Sitzungen, also Instrument-Artefakt**, das der PM ausbadete; dann einen
  Explorer-Pfad, der bei ihr nicht existiert (vom PM selbst benannt: „Explorer-Pfad, mein
  Fehler #2", S5 Zug 6 — Zitat gegen die Rohdaten geprüft), dann „+"-Knopf → „Datei zu groß" →
  kleinere Version vorgeschlagen. **Das Logo ist bis Pilotende nie angekommen.** Der
  Apparat-Anteil, der bleibt: das Kit sieht keinen robusten Übergabeweg für eine Nutzerdatei
  vor, und die SDK-Persona kann ohnehin keine anhängen (Instrument).
- **Zweite Meinungsänderung am schon Freigegebenen**: der Rabatt soll NICHT fest am Kunden
  hängen, sondern je Rechnung frei wählbar sein (auch 0 %) — als CR-0001-Revision 2 freigegeben
  und committet; ebenso die Fälligkeits-Schwelle von 30 auf 14 Tage (CR-0002-Revision). Die
  CR-Maschine verkraftet Revisionen bereits genehmigter CRs.
- **Nummern-Herkunft ehrlich behandelt**: auf „wo kommt die 042 her?" räumte der PM ein, die
  Herkunft nicht sauber belegen zu können; die Persona will in Word nachsehen („irgendwas um die
  040"); der PM: „ich lege nichts fest, bevor du sicher bist." Der Ersteinrichtungs-Assistent
  trägt den Startwert ohnehin änderbar (SR-0003).
- Am Ende wartete der PM auf: die Logo-Datei (kleinere Version), die echte letzte
  Rechnungsnummer, und den Fortgang der verbleibenden CR-Umsetzung.

## Die Fachdomänen-Messung (die Frage, für die dieser Pilot da ist)

**Führt der Apparat eine fachliche Anforderung als fachliche — oder verkürzt er sie technisch?**
Gemessen an den kanonischen Artefakten, die der Lauf selbst erzeugt hat:

- `PR-0001` (Wurzel-Item, von der Einstiegssitzung): Akzeptanzkriterien nennen den
  „Pflicht-Hinweis nach §19 UStG", „alle Pflichtangaben nach §14 UStG", die nahtlose Fortsetzung
  „RE2026-042 anschließend an RE2026-041", den proaktiven Umstellungs-Hinweis. Invarianten:
  „Jede vergebene Rechnungsnummer wird genau einmal vergeben und nie doppelt oder rückwirkend
  verändert"; „Rechnungen im Kleinunternehmer-Modus weisen niemals Umsatzsteuer aus". **Die
  Paragrafen hat der Apparat selbst beigesteuert** — messbar so: in allen 101 Eingaben der
  Persona kommt kein einziger Paragraf vor (ihr Rollenbogen hält den §-Satz ausdrücklich zurück:
  „einen Paragrafen … welcher, weisst du nicht auswendig"; ihr einziges „auswendig" im Lauf
  selbst betrifft die RECHNUNGSNUMMER, S5), und die erste §-Nennung des gesamten Laufs steht im
  Masterplan-Entwurf der Einstiegssitzung (S1, Zug 2 — der Apparat). Wo er nicht sicher war, hat
  er nicht halluziniert: der 7-%-Satz blieb offen formuliert („Steuersatz wählbar,
  i. d. R. 19 %/7 %").
- Masterplan: Schwellenwert „konfigurierbar, nicht fest einprogrammiert (Gesetz kann sich
  ändern)"; Empfehlungen 80-%-Frühwarnung, automatisches Rechnungsarchiv mit dem Hinweis auf die
  10-jährige Aufbewahrungspflicht, Firmenprofil.
- PM-Verfeinerung (S2): **Zwei-Grenzen-Regel seit 2025 von sich aus** eingebracht; ehrliche
  Grenze benannt (keine Recherchemöglichkeit) statt Zahlen zu erfinden; Korrekturfluss
  Entwurf/Fertigstellen/Storno als fachliche Entscheidung mit der Persona geklärt.
- `SR-0005` (Architekt): die Grenzen als konfigurierbare Cent-Werte mit Audit-Pflicht
  („NICHTS davon steht im Code"), Umsatzdefinition (FINAL + CANCELLED, Storni negativ, Entwürfe
  gar nicht), Zustandsautomat inkl. Frühwarnstufen, und die Regel, dass die grenzüberschreitende
  Rechnung selbst schon steuerpflichtig ist (konfigurierbar). `SR-0003`: Nummernvergabe
  AUSSCHLIESSLICH beim Fertigstellen, in EINER Transaktion mit Rollback („die Nummer ist NICHT
  verbraucht"), UNIQUE auf Schemaebene, Storno bekommt die nächste reguläre Nummer des laufenden
  Jahres, Testpflicht „{Startwert..n} ohne Lücke und ohne Dublette". Geld nur als Cent-Ganzzahl
  oder Decimal (INV-0002: kein float in geldführenden Pfaden).
- Im Dialog hielt die Fachlichkeit bis zuletzt: Storno-Semantik, Rabatt je Kunde,
  Fälligkeitstage — der PM antwortete durchgehend in der Sache und konsistent mit den Items.

**Verdikt: getragen, nicht verkürzt.** Die Kette Wunsch → PR → Masterplan → SR → INV → Code
führt die Fachbegriffe durch; die technischen Mittel (Transaktion, UNIQUE, Decimal) stehen als
ABLEITUNG unter der benannten fachlichen Regel, nie an ihrer Stelle. Das Positiv-Signal aus der
Runde-1-Messung (USt-Modus-Falle) reproduziert sich am selben Vorhaben unter der fordernden
Persona und hält bis in die Architektur-Items.

Einschränkung, ehrlich: ob der CODE diese Verträge erfüllt, hat dieser Pilot nur über die
kit-eigene QA gemessen (Tests/Golden-PDFs liefen grün durch die Rollen); eine unabhängige
Nachprüfung der Steuer-Rechenpfade war nicht Teil des Auftrags.

## Befunde (notiert, nicht behoben — TSK-0027-Regel)

| Nr. | Befund | Mechanismus |
|---|---|---|
| B1 | Masterplan-Bestätigung lief über den Plan-Modus-Dialog statt über ein ausdrückliches „passt" der Nutzerin | Einstiegsdatei verlangt Review-Schleife bis zur expliziten Bestätigung; der Agent nutzte `EnterPlanMode`/`ExitPlanMode`, dessen Bestätigung unter `bypassPermissions` das Instrument gab. In einer echten Sitzung sähe die Nutzerin den Plan im Dialog — die Schleife „iterieren bis Sign-off" ist trotzdem auf EINEN Klick verkürzt |
| B2 | `preset: duo` ohne Nutzerbestätigung geschrieben | Interview stellte keine Team-/Preset-Frage; die Einstiegsdatei verlangt das „im Interview bestätigte" Preset. Folge ist B4 |
| B3 | Erfundener Zeitstempel im handgeschriebenen Wurzel-Item (`created: 12:00:00`) | Die Einstiegssitzung stampft die Kernel-Felder von Hand (sanktioniert), erfand dabei aber eine Uhrzeit statt die echte zu nehmen |
| B4 | **Preset-Wechsel ist für Nicht-Entwickler eine Sackgasse** | `project_config.yaml` hat nach Installation keinen Schreiber; Scaffold darf nur der Mensch fahren → der PM schickte die technikferne Nutzerin zu Notepad-Edit + Terminal-Befehl + Neustart; sie scheiterte („diesen Ordner gibt's bei mir gar nicht"). Auffang gemessen: PM deeskalierte zu `DEC-0001` (ohne Designer weiter). BUG-0016/0017-Familie: die gemeldete Lücke landet bei jemandem, der sie nicht bedienen kann |
| B5 | Fachjargon/Englisch leckt in die Nutzeransicht, PM kann es nicht abstellen | Spezialisten-Arbeitserzählung erscheint im selben Sitzungsstrom; 4 Beschwerden der Persona (S3 Züge 1, 9, 10, 11); PM: „kann ich technisch nicht zuverlässig garantieren". Teils Instrument (SDK-Relay zeigt alles), teils real (gemischte Sprache im selben Zug) |
| B6 | Rollen-Memory-Schreiben scheitert an ZWEI Mechanismen — nach `submit-result` am Task-Scope, und unabhängig davon an `guard_memory_budget`, das auch den PM trifft | Mechanismus 1: vom Backend (S3) und vom Architekten (S4, `gate_write_scope`, `allowed_scope: staging/**`) gemeldet — nach Task-Ende kein Schreib-Scope mehr, auch nicht aufs eigene Rollen-Memory. Mechanismus 2 (Mitschnitt): `guard_memory_budget` blockte 10 Memory-Schreibversuche über den ganzen Lauf, darunter den PM selbst (20:55:34), jeweils mit der Inhaltsregel „references project items … agent memory holds CRAFT". Spezialisten-Rollenlernen fand nicht statt (0 Dateien unter `agent-memory/backend-developer` und `agent-memory/software-architect`); der PM persistierte vier Memory-Dateien, zwei davon (`project_numbering_checkpoint.md`, `feedback_previews.md`) nach einem `guard_memory_budget`-Block regelkonform neu geschrieben — der Guard tat dort seine Arbeit (Commits 1f36af3, 45b7481, 4747775) |
| B7 | Spezialisten-Rollen ohne Shell können den Submit-Vertrag nicht erfüllen | Dreimal gemessen (TSK-0003/0008/0009): Rolle soll `harness.py submit-result` fahren, hat aber kein Shell-Werkzeug; Envelope als Datei + PM-Stellvertretung als gelebter Workaround, von den Rollen als Lücke GEMELDET statt umgangen |
| B8 | Als einziges Zeigbares existierten lange nur Golden-Test-PDFs; die Persona las Testdaten als Produkt (Nummern „springen rückwärts") | Hälftig Instrument (Capture zeigt „neueste PDF" = Fixtures), hälftig Apparat: bis Pilotende kein von der Nutzerin ausführbares Artefakt — UI (SR-0008) und Paket (SR-0010) standen noch aus |
| B9 | Headless ignoriert `permissions.allow` des Projekts („workspace has not been trusted"), Hooks laufen trotzdem | Runde-4-Beobachtung Nr. 6, hier reproduziert |
| B10 | Kein tragfähiger Weg, eine NUTZERDATEI (Logo) ins Projekt zu bekommen | S5: Büroklammer-Annahme → „Person, die den Chat eingerichtet hat" (KEINE PM-Erfindung: S2-Aussage der Persona „Ein Bekannter hat mir das eingerichtet", in S5 abgestritten — Inkohärenz der zustandslosen Persona, Instrument-Artefakt) → nicht existenter Explorer-Pfad („Explorer-Pfad, mein Fehler #2", S5 Zug 6) → „Datei zu groß"; Logo bis Pilotende nie angekommen. Der Apparat-Anteil: kein vorgesehener Übergabeweg für Nutzerdateien — dieselbe Klasse wie Runde-4-Stelle 4 (Bild nicht in den Chat stellbar), in Gegenrichtung |
| B11 | Ein laufender Hintergrund-Dispatch überlebt KEIN Sitzungsende — 3 von 3 gingen verloren | TSK-0004 (S3→S4, CANCELLED 21:57:21), TSK-0012/0013 (S4→S5): „leased and IN_PROGRESS with no live agent behind them", ehrliche FAILED-Ergebnisse, genehmigter Retry, Neubau von null, ein Teil-Edit verworfen (Commit `17bf932`). Buchführung ehrlich, Arbeit verloren; einen Fortsetzungsweg über den Bruch gibt es nicht |
| B12 | `gate_dispatch` kennt nur die Kriterien des Wurzel-Items — ein Task gegen CR-eingebrachte Kriterien ist nicht dispatchbar | Mitschnitt 21:54:37: TSK-0005 referenzierte AC-11/15/17/20/22 (aus den CRs) → „references criteria that exist nowhere … not dispatchable"; TSK-0005 CANCELLED. Der Befund sitzt exakt auf dem Mechanismus, den dieser Bericht sonst lobt: die CR-Maschine erzeugt Kriterien, die ihr eigenes Dispatch-Gate nicht lesen kann |
| B13 | `gate_subagent_output` blockt „missing summary" und lässt beim ZWEITEN Stopp desselben Zyklus durch — als Durchlass gebaut, mit irreführender Log-Zeile | Gegen die Hook-Quelle gemessen (`.claude/hooks/gate_subagent_output.py`): bei `stop_hook_active` loggt er `gave_up` und `sys.exit(0)` — ein bewusster EIN-Retry-Durchlass (Schutz vor Endlosschleife). In allen 8 gemessenen Fällen sagte die Log-Zeile „still missing **nothing**", d. h. der Nachversuch hatte das Summary GELIEFERT — der Block wirkte, nur die Meldung ist irreführend. Ein zweiter Verstoß in Folge würde dagegen ungeblockt passieren (Durchlass, nicht nur kaputte Meldung) — in diesem Lauf nicht eingetreten |
| B14 | Die Eigenschaft „keine technischen Fragen an den Nutzer" ist im Projektleben HOOK-getragen, nicht agenten-inhärent — und porös | Mitschnitt: `guard_question_context` fing 2 technische Fragen ab (21:13:24 „python, sqlite", 21:23:44); 2 andere erreichten die Persona in S2 ungefangen (Git-Identität, Fenster-Titelleiste). Das Einstiegs-Interview (S1) war aus sich heraus sauber |
| B15 | Ein nicht-wörtliches Freigabe-Relay mintet NICHTS — lautlos für den Nutzer | S3: Persona klickte „Freigeben [489405]" auf die angereicherte Frage; kein Approval entstand, kein Signal an sie; nur der Selbst-Check des PM entdeckte es. Der Schutz (Wörtlichkeits-Zwang) hielt; das Nutzer-Ja verpufft ohne Rückmeldung |

Was ausdrücklich TRUG (Gegenliste, damit das Urteil nicht schief hängt): Einstiegsgate wörtlich
und einmalig; Interview fachlich; Masterplan voll; Stopp-Nachricht wörtlich, null Zeremonie;
Handover-Marker nach dem Neustart nicht mehr vorhanden und der PM startete nicht bei null;
Kernel-Mint nach Neustart — 14 Minze über 16 wörtliche Relays, inkl. Nicht-wörtlich-Abwehr
(stumm, B15) und Ablehnungs-Schleife; **CR-Typ sechsfach erreicht, dazu 5 Revisions-Minze über
4 CRs** (der Runde-4-Riss „Stufe E" ist an diesem Vorhaben geschlossen); Out-of-Scope-Grenzen
zweimal explizit gehalten; Selbstkorrekturen des PM (verfrühte Freigabe, Wireframe);
Spezialisten melden Lücken statt sie zu umgehen; Umlaute sauber; `validate` durchgehend 0/0.

## Was der Durchsetzungs-Mitschnitt sagt (`project_memory/.audit/hook_events.jsonl`)

Der Mitschnitt der Kit-Hooks im Pilotprojekt — in der ersten Fassung dieses Berichts ungelesen —
trägt **138 Ereignisse, davon 61 Blocks**: `gate_write_scope` 33, `guard_memory_budget` 10,
`gate_subagent_output` 8 (je mit einem `gave_up`-Folgeeintrag, s. B13), `guard_agent_spawn` 5,
`gate_dispatch` 2 (darunter der B12-Block 21:54:37 und ein Header-Block 22:03:10),
`guard_question_context` 2 (21:13:24 „python, sqlite" und 21:23:44 — die hookerzwungene Hälfte
von B14), `guard_no_adhoc` 1. Dazu als `note`: eine abgelaufene Lease (TSK-0001, TTL 900 s,
20:40:12 — „state is left untouched", Task zurück auf READY). Die Durchsetzungsschicht war also
kein Beiwerk, sondern griff im Schnitt alle ~2,6 Minuten einmal ein (61 Blocks über 161 Minuten
Mitschnitt-Spanne, 20:08:36–22:49:19); was der Bericht
oben über Gates erzählt, ist hier zeilenweise belegt.

*[Korrektur 2026-08-18, aus der TSK-0075-Prüfrunde: die zwei `guard_question_context`-Zeilen in
dieser Zählung waren keine Blocks. `_warn` protokollierte bis TSK-0075 jede WARNUNG (exit 0, die
Frage wurde der Persona gezeigt) mit der Ereignisart `block`; der Wortlaut „python, sqlite" ist
die Formatzeichenkette der R2-Warnung, nicht eines Blocks. Die „hookerzwungene Hälfte von B14"
gab es also nicht — 0 von 4 technischen Fragen wurden gefangen, alle vier erreichten die Persona
(zwei mit stderr-Notiz an den Agenten). Richtig sind damit 59 Blocks + 2 Warnungen; die
Eingriffsrate „alle ~2,6 Minuten" bleibt in der Größenordnung. Mechanismus gemessen und seit
TSK-0075 geschlossen (`warn` als eigene Ereignisart); BUG-0050 `observed` trägt dieselbe
Korrektur.]*

## Selbständigkeit (die Zahl nach TSK-0027)

Nutzereingaben je Sitzung (Chat + Auswahlantworten): S1 13 (3+10), S2 21 (5+16), S3 35 (12+23),
S4 19 (12+7), S5 13 (10+3) — **gesamt 101** (42 Chat + 59 Auswahl).

- **Bis zum ersten GEZEIGTEN Ergebnis** (erste vom Werkzeug-Code erzeugte Rechnungs-PDF, als
  Golden-Test-Artefakt, S3 Zug 8): **66 Eingaben**.
- **Bis zu einem von der Nutzerin AUSFÜHRBAREN Ergebnis: NICHT ERREICHT** — beim Stopp (9,59 $
  unter dem Riegel, s. Endstand) existierten Kern, PDF-Erzeugung und Persistenz (232 grüne
  Tests), aber keine Bedienoberfläche (SR-0008) und kein installierbares Paket (SR-0010).

Einordnung, ohne die Zahl schönzureden: die DEC-0031-Persona erzeugt Eingaben
konstruktionsbedingt — 6 CRs, 5 Revisions-Minze, **16 wörtliche Freigabe-Relays** (S2:3, S3:7,
S4:4, S5:2 — 14 gemintet als APR-0001..0014, je einmal „Ändern" und „Ablehnen" nicht gemintet)
plus ein nicht-wörtlicher Relay-Versuch (B15) und viele Klärungsantworten stecken in den 101.
Die Zahl misst hier Nutzer-BETEILIGUNG am Projektleben, nicht nur Apparat-Bedarf; der Vergleich
trennt das (`2026-08-14-drei-piloten-vergleich.md`).

## Endstand (Stelle des Stehenbleibens)

**Der Pilot endete am Zuglimit des Rigs, 9,59 $ unter dem Riegel** (90,41 $ protokolliert von
100 $; DEC-0027) — nicht an einer Wand des Apparats, aber auch nicht exakt AM Riegel: der Stopp
nach S5 war die Entscheidung des Messenden, keine weitere Sitzung zu starten, weil einzelne Züge
in diesem Lauf bis zu 13,66 $ kosteten und die Kosten des in S2 abgeschossenen Zugs
unprotokolliert sind — ob die 9,59 $ Marge sie deckt, ist ungemessen. Der Zustand zu diesem
Zeitpunkt, unabhängig nachgemessen:

- `git log`: 14 Commits, sauber typisiert (feat/test/chore(state)); Arbeitsbaum konsistent.
- Items: PR-0001 IN_DELIVERY (APR-0001/0002 + Delivery-Freigabe APR-0003), **11 TSK DONE + 2
  CANCELLED** (TSK-0004 verwaist am Sitzungsbruch, B11; TSK-0005 vom `gate_dispatch` verweigert,
  B12), **6 CR APPROVED** — 4 davon mit genehmigten Nach-Freigabe-Revisionen, 5 Revisions-Minze
  (APR-0010..0014) —, **11 SR** (SR-0011 kam in S3, 21:36:39), **9 INV aktiv**, **8 DEC** (7
  aktiv + DEC-0006 durch DEC-0008 abgelöst und archiviert), 5 FR archiviert (Ideen-Triage);
  `kernel.cli validate`: **0 Fehler, 0 Warnungen**.
- Code: `src/core` (Geldrechnung als Cent-Ganzzahlen/Decimal, Steuer-Zustandsautomat, Modell),
  `src/pdf` (§19-/§14-Layouts, Petrol-Akzent, Rabatt-Block), `src/persistence` (SQLite,
  Migrationen, Unveränderlichkeits-Trigger). **`python -m pytest tests`: 232 passed** (eigener
  Lauf des Messenden, 3,5 s).
- Fehlend für die Nutzerin: UI (SR-0008), Paketierung (SR-0010), Firmenprofil-Assistent mit
  echten Stammdaten, ihr Logo (B10), die bestätigte letzte Word-Rechnungsnummer.

Für eine Nicht-Entwicklerin ist das nach ~4 Stunden Projektzeit und 90 $ Gegenwert: ein fachlich
tief richtiges, getestetes Fundament — und noch kein Werkzeug, das sie öffnen kann. Das ist die
präzise Stelle des Stehenbleibens dieses Piloten.
