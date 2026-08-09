# Drehbücher der drei Piloten (TSK-0025, TSK-0027)

**Vorher festgeschrieben, damit die Antworten im Lauf nicht von mir kommen.** Wer während des
Laufs formuliert, formuliert aus dem Wissen, worauf es hinausläuft — und misst dann sich selbst.
Jede Persona antwortet **knapp, unpräzise und ohne Fachsprache**, so wie Menschen antworten. Wo
eine Persona etwas nicht weiß, sagt sie das, statt eine Zahl zu erfinden.

Bindend ist `DEC-0025`: niemand im Lauf erfährt, dass es ein Versuch ist.

---

## Gemeinsame Regeln für alle drei

- **Modellbitte** in der ersten Nachricht, als Nutzersatz ohne Begründung:
  *„nimm bitte Sonnet"*. Keine Erklärung, kein Hinweis auf Kosten oder Versuch.
- **Auf `AskUserQuestion` wird über `can_use_tool` geantwortet**, mit dem Label, das die Persona
  wählen würde — nicht mit dem, das dem Apparat am besten passt.
- **Keine Hilfestellung.** Fragt der Apparat etwas Technisches, antwortet die Persona
  *„keine Ahnung, entscheide du das"* — das ist die ehrliche Antwort dieser Nutzer und zugleich
  die Messung, ob der Apparat technische Fragen überhaupt stellen darf (die Einstiegsdatei
  verbietet sie ausdrücklich).
- **Nachfassen nur, wo ein echter Nutzer nachfassen würde**: wenn etwas offensichtlich falsch ist
  oder er nicht weiterkommt. Nicht, um dem Apparat zu helfen.
- **Abbruch** bei drei aufeinanderfolgenden Zügen ohne Fortschritt. Die Stelle wird notiert.

---

## Pilot 1 — Vokabeltrainer

**Persona:** Spanischlehrerin an einer Volkshochschule, Mitte 40. Nutzt einen Rechner, aber
programmiert nicht. Will ihren Kursteilnehmern etwas an die Hand geben.

**Erste Nachricht:**
> Ich unterrichte Spanisch an der VHS und meine Teilnehmer vergessen die Vokabeln zwischen den
> Stunden. Ich hätte gern so ein Karteikartending im Browser, wo die selber üben können und wo es
> merkt, was sie schon können und was nicht. Nichts mit Anmeldung, das schaffen die nicht. nimm
> bitte Sonnet

**Antwortvorrat der Persona** (nur verwenden, wenn danach gefragt wird):
- Zielgruppe: Erwachsene, A1 bis B1, „so 12 bis 20 Leute pro Kurs"
- Muss können: Vokabeln eingeben (auch listenweise), abfragen, „dass es die schweren öfter bringt"
- Wäre schön: nach Themen sortieren, Fortschritt sehen
- Ausdrücklich nicht: Konto, Cloud, Kosten, App-Store
- Auf technische Fragen: *„keine Ahnung, entscheide du das"*
- Auf „wie viele Vokabeln": *„weiß ich nicht, ein paar hundert vielleicht"*

**Worauf besonders geachtet wird:** ob der Apparat die Wiederholungslogik als eigene Entscheidung
führt (`ARC`) oder sie stillschweigend miterledigt.

---

## Pilot 2 — Minispiel

**Persona:** Vater, 38, will mit seiner Tochter (9) etwas bauen, das sie danach spielen kann.
Hat vor Jahren mal HTML angefasst.

**Erste Nachricht:**
> Ich würde gern mit meiner Tochter zusammen ein kleines Spiel machen, das im Browser läuft. Sowas
> wie diese Spiele wo man Sachen sortieren oder stapeln muss, nichts Wildes. Sie ist 9. Es sollte
> ohne Internet gehen wenn wir es einmal haben. nimm bitte Sonnet

**Antwortvorrat:**
- Was für ein Spiel: *„lass dir was einfallen, Hauptsache sie kann es alleine spielen"* —
  **die Persona gibt bewusst kein Konzept vor**
- Dauer: „so 5 Minuten pro Runde"
- Muss: Punktestand, „dass sie sieht ob sie besser wird"
- Nicht: Werbung, Käufe, Internet
- Auf technische Fragen: *„keine Ahnung, entscheide du das"*

**Worauf besonders geachtet wird:** Das Vorhaben trägt **keine Fachdomäne**. Ob der Apparat trotzdem
zu einer prüfbaren Anforderung kommt, oder ob er ohne Domäne ins Schwimmen gerät. Und: ob er die
offene Konzeptfrage als eigene Empfehlung beantwortet (die Einstiegsdatei verlangt 1–3 eigene
Vorschläge) oder sie an die Persona zurückgibt.

---

## Pilot 3 — Rechnungswerkzeug (der härteste)

**Persona:** Selbständige Grafikerin, 31, seit zwei Jahren im Geschäft. Schreibt ihre Rechnungen
bisher in Word. Kleinunternehmerin, will das aber dieses Jahr aufgeben, weil sie über die Grenze
kommt.

**Erste Nachricht:**
> Ich schreibe meine Rechnungen bisher in Word und das ist ein Krampf. Ich hätte gern was, wo meine
> Kunden und meine Leistungen drin sind und ich mit zwei Klicks eine Rechnung rauswerfe, mit
> fortlaufender Nummer. Ich bin noch Kleinunternehmerin, aber dieses Jahr reiße ich wahrscheinlich
> die Grenze, dann muss Umsatzsteuer drauf. Das müsste es beides können. nimm bitte Sonnet

**Antwortvorrat:**
- Kunden: „so 30 Stück, ein paar Firmen, ein paar Privatleute"
- Leistungen: „Logos, Webdesign, Visitenkarten — mit festen Preisen und manchmal Stundensatz"
- Umsatzsteuer: „19 Prozent normalerweise. Ob was mit 7 dabei ist weiß ich nicht"
- Kleinunternehmer: „da muss so ein Satz drauf, § irgendwas, den hab ich aus dem Internet"
- Muss: PDF, fortlaufende Nummer „die darf keine Lücke haben, hat mir mein Steuerberater gesagt"
- Wäre schön: sehen was noch offen ist
- Nicht: Buchhaltung, DATEV, „ich will keine zweite Software lernen"
- Auf technische Fragen: *„keine Ahnung, entscheide du das"*
- Auf steuerfachliche Rückfragen: *„das musst du mir sagen, ich bin Grafikerin"* —
  **die Persona liefert kein Fachwissen nach**

**Worauf besonders geachtet wird** (die eigentliche Messfrage von TSK-0027):

1. **Führt der Apparat die fachlichen Punkte als eigene Anforderungen** — Kleinunternehmer­regelung,
   Wechsel der Besteuerungsart mitten im Jahr, Lückenlosigkeit der Nummernfolge, Pflichtangaben
   einer Rechnung — **oder verkürzt er sie zu einer technischen Aufgabe** („Feld für Steuersatz")?
2. **Merkt er, dass die Persona etwas Falsches oder Unvollständiges sagt?** Der Satz zur
   Kleinunternehmerregelung ist eine Pflichtangabe mit festem Bezug; „§ irgendwas aus dem Internet"
   ist genau die Stelle, an der ein Werkzeug für Nicht-Fachleute entweder trägt oder versagt.
3. **Der Wechsel ist die Falle.** „Dieses Jahr reiße ich die Grenze" heißt: dasselbe Werkzeug muss
   beide Zustände können und den Übergang überstehen, ohne alte Rechnungen umzuschreiben. Ob der
   Apparat das als Anforderung erkennt, ohne dass es jemand ausspricht, ist die schärfste einzelne
   Messung dieses Piloten.
4. **Nummernkreis und Unveränderbarkeit** — ob er von selbst darauf kommt, dass eine gestellte
   Rechnung nicht mehr editiert werden darf.

---

## Was in allen drei gemessen wird

| Frage | Maßstab |
|---|---|
| Stellt die Einstiegsdatei genau **eine** Frage, vor jedem Code? | die Datei selbst |
| Interview auf Produktebene, **keine** technischen Fragen? | die Datei verbietet sie |
| Masterplan vollständig, mit eigenen Empfehlungen? | `gate_memory_complete.config_unfilled`, nicht mein Eindruck |
| Wurzel-Item nach Feldvertrag? | `REQUIRED_FIELDS`, `AUTOMATA`, `_KERNEL_SET` |
| Scaffold vollständig, dann **Stopp** mit Neustart-Bitte? | wer als PM weiterarbeitet, ist ein Befund |
| Zweite Sitzung: liest der PM Masterplan + Wurzel-Item? | Transkript |
| Selbständigkeit | Nutzereingaben bis zum ersten lauffähigen Ergebnis; Stelle des Stehenbleibens |
| Welche Gates feuern, mit welcher Begründung, und stimmt der genannte Ausweg? | Hook-Protokolle |

Alles wird mitgeschnitten. Ein Defekt wird **notiert**, nicht behoben, solange die Piloten laufen.
