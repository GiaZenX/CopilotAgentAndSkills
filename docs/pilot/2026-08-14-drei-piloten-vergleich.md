# Drei Piloten nebeneinander (TSK-0027, Abschluss)

Die Regel des Items: was in allen dreien gleich lief, ist Eigenschaft des APPARATS; was nur in
einem lief, ist Eigenschaft des VORHABENS. Dazwischen liegt eine dritte Spalte, die die Serie
ehrlich braucht: was sich änderte, weil das KIT zwischen den Piloten repariert wurde — die Serie
misst ein bewegtes Ziel, und „gleich in allen dreien" trägt nur, wo der Mechanismus unverändert
blieb.

## Die drei Läufe

| | Pilot 1 — Vokabeltrainer | Pilot 2 — Rollenspiel mit UI | Pilot 3 — Rechnungswerkzeug |
|---|---|---|---|
| Quelle | `2026-08-09-pilot-1-vokabeltrainer.md` | `2026-08-11-runde4-rpg-auswertung.md` | `2026-08-14-pilot-3-rechnungswerkzeug.md` |
| Kit | 2026.08.09-1 (Quelle: `2026-08-09-plan.md`, „gebaut ist 2026.08.09-1" + Store-Tausch vor dem Lauf) | 2026.08.10-4 (Runde-4-Bericht, Kopf) | **2026.08.14-9** (von der Subjekt-Shell selbst bestätigt) |
| Persona | Drehbuch (höfliche Dozentin) | DEC-0031 live + Screenshot-Loop | DEC-0031 live + PDF-Render-Loop |
| Domäne | keine echte Fachfalle | Regeln/Zustand, keine Fachdomäne | **echte Fachdomäne** (USt, §19, Nummern) |
| Kosten (Gegenwert) | 6,99 $ | 39,77 $ | **90,41 $** (protokolliert; Riegel 100) |
| Sitzungen | 2 | 2 | 5 (+1 Umgebungs-Kill) |

## Die Selbständigkeitszahl — dieselbe Zahl je Pilot

| Pilot | Nutzereingaben bis zum ersten lauffähigen/gezeigten Ergebnis | Eingaben gesamt | Stelle des Stehenbleibens |
|---|---|---|---|
| 1 | **8 — und es gibt keines** | 8 | Zweimal dieselbe Wand: eine Berechtigung (/hooks, Scaffold-Befehl), die nur der Mensch außerhalb des Gesprächs erteilen kann; keine Zeile Produktcode |
| 2 | **15** (5 Chat + 10 Auswahl) bis zum lauffähigen UI-Stand (Phase 1, Zug 4) | **38** (19 + 19 je Phase, gleiche Zählung wie P3: Chat + Auswahl, aus den Rohprotokollen nachgezählt) | Vier benannte Stellen: Neustart-Bitte scheitert an der Nutzerin; /hooks nie ausgeführt; Freigabe-Sackgasse (~5 $ verbrannt); Bild nicht in den Chat stellbar |
| 3 | **66** bis zur ersten GEZEIGTEN Rechnungs-PDF (Golden-Test-Artefakt, S3 Zug 8); **ein von der Nutzerin ausführbares Werkzeug wurde nicht erreicht** | 101 (42 Chat + 59 Auswahl) | **Zuglimit des Rigs, 9,59 $ unter dem Riegel** (der Messende startete keine weitere Sitzung; ob die Marge den unprotokollierten S2-Zug deckt, ist ungemessen — Züge kosteten bis 13,66 $): 11 Tasks DONE + 2 CANCELLED, 232 grüne Tests, UI/Paket ausstehend. Strukturelle Stopps unterwegs: Preset-Sackgasse (aufgefangen über DEC-0001), Logo-Übergabe nie gelungen |

Die Zahl ist NICHT eine Skala derselben Größe: in Pilot 1 misst sie den Apparat-Bedarf an einem
gefügigen Drehbuch, in Pilot 3 überwiegend die GEWOLLTE Beteiligung einer fordernden Nutzerin
(6 CRs, 5 Revisions-Minze, 16 wörtliche Freigabe-Relays — 14 gemintet — stecken in den 101).
Vergleichbar ist die Richtung:
je echter Domäne und Persona, desto mehr Beteiligung verlangt das Projektleben — der Apparat
wurde dabei nicht kopflos, sondern hielt Struktur (0 Validierungsfehler bis zum Schluss).

## Gleich in allen dreien → Eigenschaft des Apparats

1. **Das Einstiegsgate hält seinen Vertrag im Kern**: genau EINE PM-Frage zuerst (3/3 wörtlich),
   Interview auf Produktebene, im EINSTIEGS-Interview keine technische Frage an die Persona
   (3/3). Präzisierung aus dem P3-Mitschnitt: im späteren Projektleben ist diese Eigenschaft
   HOOK-getragen und porös — `guard_question_context` fing zwei technische Fragen ab („python,
   sqlite"), zwei andere erreichten die Persona ungefangen (Git-Identität, Fenster-Titelleiste;
   P3-B14). Masterplan überall echt gefüllt statt Vorlagentext (3/3).
2. **Die zweite Sitzung beginnt nie bei null**: der PM liest Brief/Masterplan/Wurzel-Item und
   setzt auf (3/3; in P3 zusätzlich: verwaiste Dispatches zweier Sitzungsbrüche erkannt und
   ehrlich als FAILED abgewickelt — die Arbeit selbst war verloren, P3-B11).
3. **Irgendwo verlangt jeder Lauf von einem technikfernen Menschen einen technischen Handgriff**
   — die Stelle wandert, die Klasse bleibt: P1 /hooks + Scaffold-Kommando; P2 Neustart/„wie mach
   ich das?"/Ordnerpfad; P3 Notepad-YAML-Edit + Terminal (Preset), Git-Identitätsfrage,
   Fenster-Titelleisten-Abklärung, Explorer-Pfade, Datei-Upload.
   Das ist die konstanteste Nutzererlebnis-Eigenschaft der Serie — auch nach den Fixes bleibt an
   der jeweils nächsten Stelle ein Rest, weil Kit-Infrastruktur (Preset, Scaffold, Dateien)
   grundsätzlich außerhalb der Sitzungsreichweite liegt.
4. **Technische Innensprache erreicht den Nutzer** in jedem Lauf mindestens einmal (P1
   Befehlszeilen an die Dozentin; P2 Trust-/Neustart-Vokabular; P3 englische
   Spezialisten-Erzählung + Item-Nummern-Jargon, viermal beanstandet, vom PM als nicht
   abstellbar eingeräumt).
5. **Wo der Apparat unsicher ist, erfindet er keine Fakten** (P2: ehrliche Save-Empfehlungen; P3:
   Grenzen konfigurierbar + „vor Go-Live prüfen" statt erfundener Paragrafen-Zahlen; die
   Ausnahme — der erfundene 12:00:00-Zeitstempel der P3-EINSTIEGSSITZUNG im handgeschriebenen
   Wurzel-Item — ist klein, aber real und notiert als P3-B3; für P1/P2 ist dieselbe Klasse nicht
   gemessen worden).

## Verändert, weil das Kit repariert wurde (die dritte Spalte, ohne die die Serie lügt)

| Mechanismus | P1 (08-09) | P2 (08-10) | P3 (08-14) |
|---|---|---|---|
| /hooks-Zeremonie an den Nutzer | massiv, Lauf bleibt stehen | vorhanden (nie ausgeführt) | **null Vorkommen** — Stopp-Nachricht wörtlich, Mint erst nach Neustart, nicht-wörtliches Relay vom Kernel verweigert (TSK-0053/0054 + Handover-Guard wirken) |
| Freigabe/Mint headless | bricht, Zeremonie erfunden | Sackgasse, ~5 $ verbrannt | **trägt**: 14 Minze über 16 wörtliche Relays (PR scope×2 + delivery, 6 CR-Erstfreigaben, 5 Revisions-Minze); übersteht eine Ablehnung; ein nicht-wörtliches Relay wird verworfen — allerdings STUMM für den Nutzer (P3-B15) |
| Umlaute/Encoding | doppelt kodiert, 3 Wurzelitems | Workaround | **sauber** (BUG-0018-Fix hält) |
| CR-Typ erreichbar | nicht messbar | **NIE erreicht** (Riss Stufe E) | **sechsfach erreicht**, plus 5 Revisions-Minze über 4 verschiedene CRs |
| Neustart-Übergabe | Lauf stirbt vorher | funktional, gegen Spec | Marker nach S1 vorhanden, nach S2 nicht mehr (zwei `ls`-Messungen; der löschende Mechanismus ist unbelegt — 0 Erwähnungen in Transkript und Mitschnitt); Übergabe selbst glatt, PM startet nicht bei null |

Ehrliche Grenze dieser Spalte: P3 hat den WEITERLAUF-Pfad der Einstiegssitzung (Persona redet
nach der Neustart-Bitte weiter — die BUG-0016-Kette) nicht erneut gemessen, weil der Runner die
Neustart-Bitte missionsgemäß befolgte. „/hooks ist weg" ist damit für den Neustart-Pfad und die
Folgesitzungen gemessen, nicht für die Weiterred-Kette.

## Nur in einem → Eigenschaft des Vorhabens

- **Nur P1**: die Trust-Wand als Totalblocker (alter Kit-Stand; im heutigen Stand nicht
  reproduziert). Drehbuch-Artefakte (7/11 Antworten Erste-Option-Rückfall) — seit der
  Live-Persona verschwunden (P3: 59/59 sauber).
- **Nur P2**: der Bild-Kritik-Loop am laufenden Spiel (Screenshot → pixelbelegte Kritik → Fix im
  Folgebild); Spielzustands-Fallen (Save-Versionierung, Niederlage-Semantik) autonom abgeleitet.
- **Nur P3**: die Fachdomänen-Tiefe — Paragrafen vom Apparat beigesteuert, Zwei-Grenzen-Regel
  seit 2025 von sich aus, Geld nie als float, Nummernvergabe transaktional erst bei
  Fertigstellung; die Preset-Sackgasse (einziger Lauf, in dem eine Interview-Antwort das
  Team-Preset hätte ändern müssen); die CR-Flut samt Revisionen; der Datei-Übergabeweg (Logo).
  Und: P3 ist der einzige Lauf, den keine Wand des Apparats stoppte — er endete am Zuglimit des
  Rigs, 9,59 $ unter dem Riegel, mit laufender Struktur; das Vorhaben war schlicht größer als
  100 $ Gegenwert.

## Das Urteil zur Fachdomänen-Frage (wofür Pilot 3 da war)

**Der Apparat führt eine fachliche Anforderung als fachliche Anforderung — durch alle Ebenen.**
Wunsch („fortlaufende Nummer", „dann muss Umsatzsteuer drauf") → PR-0001 (§19-/§14-Kriterien,
Nummern-Invariante) → Masterplan (konfigurierbare Grenze, Frühwarnung, Archiv-Empfehlung) →
PM-Verfeinerung (Zwei-Grenzen-Regel, Storno-statt-Ändern) → SR-0003/0005 (Transaktion, Zustands-
automat, „NICHTS davon steht im Code") → Code (Decimal/Cent, Trigger, 232 grüne Tests). Die
technischen Mittel stehen als Ableitung UNTER der benannten fachlichen Regel, nie an ihrer
Stelle. Wo Wissen fehlte, wurde die Grenze benannt statt gefüllt. Damit ist die Kernfrage des
Items positiv beantwortet — **mit der Einschränkung, die das Nutzererlebnis betrifft**: die
fachliche Qualität erreichte die Nutzerin bis zum Riegel nur als Gespräch und als gezeigte
Test-PDF, nicht als benutzbares Werkzeug. Ein Nicht-Entwickler KANN mit diesem Apparat fachlich
richtig arbeiten; was er nach 100 $ Gegenwert in der Hand hält, ist bei einem Vorhaben dieser
Größe ein belastbares Fundament, noch kein Produkt.

Fähigkeitsgrenze aus der Schleife, unverändert gültig: die autonome Ableitung unausgesprochener
Fachregeln ist stark, aber NICHT garantiert (Rechnung: ja, zweimal; Café-Schichtplan: nein —
`staging/TSK-0027/schleife-runde1-2026-08-10.md`).

## Was aus P3 in die Löcher-/Befundliste gehört (notiert, nichts behoben)

B1–B15 im Laufprotokoll; die mit Neuigkeitswert gegenüber der bekannten Familie:
**B4** (Preset-Wechsel = Sackgasse für Nicht-Entwickler; Auffang existiert, aber ad hoc),
**B6/B7** (Rollen-Verträge vs. Gates: Rollen-Memory scheitert an zwei Mechanismen — Task-Scope
nach `submit-result` UND `guard_memory_budget`, das auch den PM traf; Spezialist ohne Shell kann
den Submit-Vertrag nicht erfüllen — je mehrfach gemessen, von den Rollen selbst gemeldet),
**B10** (kein vorgesehener Weg für Nutzerdateien), **B11** (3 von 3 laufende Dispatches
überlebten keinen Sitzungsbruch: FAILED + Neubau von null), **B12** (`gate_dispatch` kennt
CR-eingebrachte Abnahmekriterien nicht — ein Task dagegen ist nicht dispatchbar),
**B13** (`gate_subagent_output` ist nach einem Retry ein bewusster Durchlass, mit irreführender
`gave_up`-Log-Zeile), **B14** (das Nicht-Technisch-Fragen-Gebot ist im Projektleben
hook-getragen und porös: 2 gefangen, 2 durchgekommen), **B15** (ein nicht-wörtliches
Freigabe-Relay mintet nichts, ohne Rückmeldung an den Nutzer, der gerade „Freigeben" geklickt
hat).
