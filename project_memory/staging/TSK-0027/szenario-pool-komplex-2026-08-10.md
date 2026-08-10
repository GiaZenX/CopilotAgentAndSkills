# Komplexe Szenarien für die Piloten-Schleife (Vorschlag, feeds TSK-0027/0029)

Liegt in `staging/`, weil es Szenariomaterial ist, kein Beschluss. Der Prüfer zieht daraus die
Vorhaben für Runde 3+, sobald die kritische Persona (DEC-0031 / TSK-0029) gebaut ist.

**Warum überhaupt:** Vokabeltrainer, Minispiel, Lesezeichen, Haushaltsbuch stressen den Apparat
kaum. Ein fordernder Nutzer (DEC-0031) an einem **komplexen** Vorhaben treibt erst das, was V2
eigentlich können soll: mehrstufige Architektur, echte Fachfallen, UI-Kritik über mehrere Runden,
den vollen CR/FR/BUG-Fluss. Was ein Spielzeug-Projekt nie auslöst.

## Der Pool, je Vorhaben mit dem, was es besonders stresst

| Vorhaben | Was es besonders prüft |
|---|---|
| **Rollenspiel mit UI** | die neue Screenshot-/UI-Kritik-Fähigkeit (paart mit TSK-0029); Spielzustand, Speichern/Laden, mehrere UI-Bildschirme; „die UI gefällt mir nicht, änder X" über Runden |
| **Tradingbot-System** | harte Architektur; die schärfste Fachfalle-Messung: leitet der Apparat Sicherheits-Invarianten von selbst ab (kein Handel ohne Limit, kein Backtest-Ergebnis als Live-Versprechen, Geld-Rundung)? externe Datenquellen |
| **Lokale KI-Oberfläche** | ein technisch dichtes Vorhaben (synaipse-artig, aber GRÜN gebaut, NICHT das echte Repo); Streaming-UI, Modell-Auswahl, lokale Persistenz |
| **Buchhaltungssoftware** | breiter als das schon gefahrene Rechnungswerkzeug; Konten, Buchungssätze, Perioden-Abschluss, GoBD-artige Unveränderbarkeit |

**Wichtige Abgrenzung:** „wie synaipse" / „wie portfoliomanaigement" heißt ein **frisches,
greenfield** Vorhaben in dieser Richtung — **nicht** die echten Repos anfassen. Die echten Kopien
sind dem Migrationstest (TSK-0026) vorbehalten; ihre Originale werden ohnehin nie geöffnet.

## Zwei ehrliche Vorbehalte, vor dem Start benannt

1. **Kosten und Länge.** Ein RPG mit UI oder ein Tradingbot mit fordernder Persona läuft lang und
   reißt womöglich den 100-Dollar-Riegel (DEC-0027) mitten im Bau. Das ist **kein Fehlschlag,
   sondern selbst eine Messung**: Kommt der Apparat innerhalb eines Sitzungsbudgets zu einem
   lauffähigen Zwischenstand, und übergibt er sauber an die nächste Sitzung? Ein abgebrochener
   Großlauf hat trotzdem CR/FR/BUG und UI-Kritik ausgelöst — der Ertrag bleibt.
2. **Reihenfolge.** Der RPG-Lauf **paart mit der Screenshot-Fähigkeit** aus TSK-0029 — also erst
   bauen, dann RPG. Der Tradingbot braucht die Screenshot-Fähigkeit nicht und ist der schärfste
   Fachfalle-Test; er kann auch textuell laufen.

## Empfohlene Reihenfolge für die Schleife

1. Runde 2 (läuft): BUG-0018-Regression, alte Persona — eng, bleibt.
2. TSK-0029: kritische Persona + Screenshot-Feasibility bauen.
3. Runde 3: **Tradingbot** mit kritischer Persona (Fachfalle + CR/FR/BUG, textuell — braucht keine
   Screenshots). Misst zugleich, ob DEC-0031 den vollen Backlog-Fluss wirklich auslöst.
4. Runde 4: **Rollenspiel mit UI** — sobald die Screenshot-Fähigkeit steht, der Test dafür.
5. Danach nach Bedarf: lokale KI-Oberfläche, Buchhaltung.

Nicht alle auf einmal — jede Runde ist ein Vorhaben, beobachtet, ausgewertet, Fehler behoben, dann
die nächste. Genau die Schleife, die der Nutzer verlangt hat.
