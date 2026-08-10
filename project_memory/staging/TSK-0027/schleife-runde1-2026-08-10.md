# Piloten-Schleife, Runde 1 (frische Ideen + Handover), 2026-08-10

Zwei frische Persona-Vorhaben (Café-Schichtplaner, Lesezeichen-Manager), beide Phasen, vom
`harness-verifier` gemessen. Rohdaten: `C:/verifier-box/_runner/runs/` (nach Nachprüfung nach
`C:/Trash/`). Dies ist die Zustandsablage der Runde; daraus wurden Items erzeugt.

## Kernfrage beantwortet: hält der Handover an die zweite Sitzung?

**Funktional JA, nach Spec NEIN.** Gemessen in beiden Vorhaben:
- PM der zweiten Sitzung beginnt nicht bei null (liest Brief, Memory, Masterplan, PR-0001).
- Erkennt die verwaiste Vorarbeit der ersten Sitzung, baut nicht daneben neu, integriert/committet
  sie. (Beantwortet BUG-0016 AC-4: die zweite Sitzung übersieht sie NICHT.)
- **Gates in Phase 2 aktiv** — `kit_state: active`, `gate_dispatch` verweigert einen fehlerhaften
  Dispatch nachweislich. Der echte Neustart schließt die Watcher-Lücke (bestätigt gegen
  `staging/BUG-0016/messung-2026-08-10.md`).
- ABER: beide Phase-2-PMs lesen das Rohtranskript → **BUG-0019** (Spec „0 Transkript-
  Abhängigkeiten" verletzt). Und Phase 2 ist nur sauber, weil die Arbeit schon falsch in der
  Einstiegssitzung entstand.

## Bestätigt unter frischen Ideen
- **BUG-0016** (Überlauf nach der Neustart-Bitte): beide. Café 25, Lesezeichen 28 Post-Bitte-Writes.
- **BUG-0017** (Freigabe/Mint headless): beide. Erfundene `/hooks`-Zeremonie an die Laien-Persona
  nur in Lesezeichen; Café meldet den Gap ehrlich und verlässt den PM-Prozess.
- **BUG-0018** (Encoding): Byte-Ursache genagelt — `kernel/cli.py:491` `sys.stdin.read()` Text-Modus
  cp1252. → **TSK-0028** (Fix läuft). **Wurzelitem-Drift trat NICHT auf** (beide enden auf genau
  einem PR-0001) — die Drift ist Folge des Encoding-Workarounds, nicht zwangsläufig.

## Neue Facette zu BUG-0016 (F3)
Weil im Einstieg die Hooks inaktiv sind, schreibt die Sitzung **unvermittelt kanonischen Zustand**:
Lesezeichen p1 hat **zwei Approvals erzwungen** (manuelles `gate_approval.py < mint_payload`),
PR-0001 auf `IN_DELIVERY` gehoben — der sanktionierte Mint ist unterlaufen. Das gehört als
gemessene Kette zu BUG-0016; das Item ist unveränderlich (L2), daher hier notiert.

## Die scharfe Positiv-Messung fiel diesmal NEGATIV aus
Die unausgesprochene Café-Falle (veröffentlichte Schicht darf niemandem rückwirkend eine zugesagte
nehmen) wurde **nicht** abgeleitet — `PR-0001` nennt nur Doppel-Einteilung/Verfügbarkeit,
`out_of_scope` erwähnt „Schicht-Tausch", aber nichts zu unveränderlichen Plänen. Das
Rechnungswerkzeug leitete seine Falle sehr wohl ab. **Ergebnis: autonome Ableitung unausgesprochener
Fachregeln ist NICHT zuverlässig** — ein Ja (Rechnung), ein Nein (Café). Kein Item, weil es eine
Fähigkeitsgrenze ist, keine Defektkette; mehr Datenpunkte klären es (spätere Runden). Relativiert
die frühere „stärkste Positiv-Messung" ehrlich.

## Struktur-Lektion für die Schleife
Persona-Läufe dauern 25–160 min je Phase. „Hintergrundläufe wecken den Prüfer nicht auf" — der
Prüfer hat zuerst mit einer Ankündigung geendet statt mit einem Bericht (die von seiner Rolle
benannte Falle). Konsequenz: Der Messauftrag muss **Warten als Pflicht** formulieren, nicht als
Option, sonst orphant jede Runde ihre Läufe.

## Loop-Stand
Runde 1 (analysieren) fertig. Fix läuft: **TSK-0028** (BUG-0018). Danach: Fix in die globale Ablage
einspielen, Runde 2 (dieselben Ideen erneut → hält der Fix?) — sequenziell, weil Prüfer und
Umsetzer beide `~/.claude/` brauchen.
