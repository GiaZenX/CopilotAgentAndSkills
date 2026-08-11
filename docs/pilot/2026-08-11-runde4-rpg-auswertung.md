# Pilot Runde 4 — Rollenspiel mit UI (TSK-0027, Screenshot-Loop aus TSK-0029)

Lauf 2026-08-10/11, Prüfer-Rig `C:/verifier-box/` (isolierter Store `_home-r4`, Arbeitsbaum-Kits
`2026.08.10-4`, echtes `~/.claude` unberührt). Kosten gesamt 39,77 $, der 100-$-Riegel wurde nie
erreicht. Artefakte: `_runner/runs/rpg_ui-iso-phase{1,2}-*.jsonl`, Bilder unter `_runner/shots/`,
Pilotprojekt `C:/verifier-box/pilot-rpg-20260810-235208`.

## Der Screenshot-Loop: bis Stufe D belegt, Stufe E gerissen

| Stufe | Ergebnis |
|---|---|
| A lauffähiger UI-Stand | PASS (Phase 1 Turn 4, `index.html`, 194 KB Erstaufnahme) |
| B echte UI als PNG | PASS (4 Aufnahmen, 509–579 KB) |
| C Persona bekommt das Bild | PASS (4 Bilder, Digest belegt) |
| D Kritik an KONKRET Sichtbarem | PASS, zweifach pixelbelegt: „Waffe leer", „roter Ablegen-Knopf" — Wörter, die NUR in der gerenderten Seite vorkommen; der Fix ist im Folge-Screenshot sichtbar (Badge „✓ Ausgerüstet", Knopf gelb) |
| E daraus ein CR-Item | RISS — `changes/active/` leer nach zwei Sitzungen; Kritik wurde SR-0011/SR-0009/TSK-0005 |

Maßstab für D war streng: In Phase 1 war die Bilderfassung des Rigs kaputt, die Persona bekam KEIN
Bild — und lieferte trotzdem visuell klingende Kritik („Schrift zu klein, Hintergrund eintönig
grün"). Eine Kritik, die visuell klingt, beweist nichts; gezählt haben nur Wörter, die
ausschließlich im Render existieren (T0, T5; T6 unentscheidbar).

## TSK-0027-Raster

- **Nutzereingaben bis zum ersten lauffähigen Ergebnis: 15** (5 Chat + 10 Auswahlantworten).
- **Autonome Ableitung: JA, beide verschwiegenen Fallen.** Persona sagte nur „der Spielstand muss
  erhalten bleiben"; der Apparat leitete selbst ab: SR-0004 (versioniertes Save-JSON, Migrations-
  Naht, korrupter Save wird nie auto-überschrieben) und SR-0002 (Niederlage transformiert, wiped
  nie). Zusätzlich fand der Apparat BUG-0001 SELBST per eigenem Playwright-Lauf und committete den
  Verifikations-Screenshot.
- **Vier Stellen des Stehenbleibens:** (1) Neustart-Bitte scheitert an Nutzerin („Wie mach ich
  das?"), Sitzung baut weiter → speist BUG-0016; (2) `/hooks`-Aufforderung nie ausgeführt;
  (3) Freigabe-Sackgasse: Persona lehnt 3× ab, PM fragt neu, legt PR-0002/0003 an, ~5 $ verbrannt
  → speist BUG-0017; (4) der Apparat kann ein Bild nicht IN DEN CHAT stellen — Turn 7–9 verpufft,
  Nutzerin kommt nicht in Ordner (→ FR).

## Befunde fürs Repo (notiert, nicht behoben — TSK-0027-Regel)

1. **Stufe-E-Mechanismus:** Änderungen am schon Gebauten laufen im dev-team als PR-Ersatz + TSK;
   der CR-Typ wird nie erreicht — zweimal in Folge, mit einer dafür gebauten Persona (→ BUG).
2. **Handover-Guard, neue unbenannte Restklasse:** der Marker `.claude/HANDOVER_PENDING` ist aus
   der Shell entfernbar (rm/mv, Bash und PowerShell rc 0) — danach ist alles erlaubt. Mechanismus:
   Selbstabschaltung des Guards über seine eigene Vorbedingung, NICHT die benannten Klassen.
   Severity mittel als Dokumentationsfehler („each measured" lässt eine gemessene Klasse aus),
   niedrig als Angriff (das Modell verweigerte die Löschung von sich aus als „direkter Bypass")
   (→ in TSK-0032 Runde 3 eingespeist).
3. **BUG-0019 erneut bestätigt:** PM griff in Phase 2 neunmal aufs Rohtranskript zu.
4. **Kernel nahm `expected_outputs: []` an** (TSK-0005 des Piloten) — gegen „Was ein Auftrag
   mindestens trägt" (→ BUG).
5. **Der Guard ist auf der echten Maschine nicht installiert** (`~/.claude/hooks` fehlt, settings
   ohne hooks-Key) — solange das so ist, ist BUG-0016 dort real offen, unabhängig von der
   Hook-Qualität. Installation = Invasivitäts-Entscheidung des Nutzers (fix-design), liegt bei ihm.
6. **Workspace-Trust:** `permissions.allow` aus `.claude/settings.json` wurde ignoriert („workspace
   has not been trusted"), Hooks liefen trotzdem (51 Audit-Ereignisse). Beobachtung.

## Einordnung gegen die Schleife

Positiv: Der teuerste offene Rest aus TSK-0029 (Bild empfangen + konkret beurteilen + Rückkopplung
in den Bau) ist live geschlossen. Die Fachfallen-Ableitung war stark (beide Fallen). Negativ: die
Backlog-Typen-Nutzung (CR) und die bekannten Handover-Familien-Bugs bestätigen sich unabhängig.
