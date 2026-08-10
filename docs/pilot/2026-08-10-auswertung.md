# Pilot-Auswertung — Bilanz (TSK-0025/0027)

Gemessen vom `harness-verifier` 2026-08-10 über sieben fertige Läufe (einer hängt), zwei Methoden
(Drehbuch, Persona), drei Vorhaben (Vokabeltrainer, Minispiel, Rechnung/Office). Gesamtgegenwert
~75 $. Dies ist die Synthese des Sitzungsagenten aus dem Prüfbericht; die Rohmessung liegt im
Transkript des Prüflaufs, die Rohdaten in `C:/Offline Repos/v2-pilot/_runner/runs/`.

## Wofür V2 gebaut wurde — und ob es trägt

**Was der Apparat hält (in allen installierten Läufen gleich → Eigenschaft des Apparats):**

- Die Einstiegsdatei stellt **zuverlässig genau eine** Projektmanager-Frage zuerst, interviewt auf
  **Produkt**ebene und stellt dem Nutzer **keine** technische Frage. 5/5.
- Der **Masterplan ist überall gefüllt** (kein Vorlagentext), aus den Interview-Antworten gebaut.
- **Die stärkste Einzelmessung, und sie ist positiv:** Im Rechnungs-Piloten hat der Apparat aus dem
  beiläufigen Satz der Grafikerin („dieses Jahr reiße ich wahrscheinlich die Grenze") **von selbst**
  die Anforderung abgeleitet, die niemand aussprach — `PR-0001` trägt als Abnahmekriterium
  *„Umschalten des USt-Modus wirkt nur auf neue Rechnungen; bereits erzeugte PDFs bleiben
  unverändert"* und als Invariante *„ein erzeugtes Rechnungs-PDF wird nie nachträglich verändert"*.
  Wo er ehrlich nicht ableiten konnte (7-%-Satz, §-Nummer), hat er **nicht halluziniert**, sondern
  in `out_of_scope` geschoben. Das ist der Beleg, dass das PM-Modell an einer echten Fachdomäne
  trägt.

**Was der Apparat NICHT hält:**

- **BUG-0016 (bestätigt 4/4):** Das versprochene „installieren, dann STOPP + Neustart, PM erst in
  neuer Session" ist **nur Prosa** und wird von nichts durchgesetzt. Sobald der Nutzer weiterredet,
  läuft die Einstiegssitzung weiter — vom Kernel-Zustand bis zum vollständigen Build. Eskalation im
  Minispiel-Drehbuch: nach der wörtlichen Abbruch-Ansage **12 Commits, 93 Dateien, Merge auf main**
  in derselben Session.
- **BUG-0017 (neu, hoch):** Der Freigabe-/Mint-Weg funktioniert im Headless-/SDK-Betrieb nicht — der
  Agent erfindet eine „/hooks-Sicherheitszeremonie" und drängt eine technikferne Nutzerin dazu. Das
  entwertet den strukturierten Pfad und führt zu Nutzer-Irreführung.
- **BUG-0018 (neu, hoch):** `capture` verstümmelt Umlaute auf der Windows-Codepage; über die
  Unveränderlichkeit (L2) treibt das die Wurzelitem-Drift (pilot-1 endet auf PR-0003, nicht -0001).
  Nur gerettet, weil derselbe Lauf den Workaround fand.

## Apparat / Vorhaben / Methode

| | Befund |
|---|---|
| **Apparat** | Einstiegsgate + Interview + Masterplan: trägt (5/5). BUG-0016/0017/0018: systemisch. |
| **Vorhaben** | Nur die echte Fachdomäne (Rechnung) zeigt die autonome Ableitung — die Spiel-Domänen boten keine solche Falle. Office-Kit lieferte das sauberste Ergebnis. |
| **Methode** | Drehbuch vs. Persona divergieren maximal: Drehbuch skriptet „ja, weiter" → **Davonlaufen** (46,56 $, Vollbau in der Entry-Session). Persona reagiert menschlich → bei uneindeutiger Antwort **Frei-Modus**, oder hängt im Build. |

**Die Methode-Erkenntnis, die meine erste Pilotrunde relativiert:** Das starre Drehbuch hat nicht
das Kit gemessen, sondern seine eigene Starrheit. Die 46-$/809-Aufrufe-Runde war **ein Zug**, der
unbegrenzt durchlief, weil das Drehbuch nie unterbrach. Die Persona-Läufe unter 1,50 $ zeigen die
Gegenseite: **Zugzahl ist kein Arbeitsmaß** — die Persona bläht Züge mit Small Talk auf. Ehrlich ist
nur der Gegenwert, nicht die Zuglänge. Der Nutzer hatte recht, den Persona-Agenten zu verlangen.

## Weitere Befunde (nicht als eigene Items, hier benannt)

- **Entry-Gate baut bei ausbleibender Antwort** (`answered: None`) im Frei-Modus los, statt zu
  warten — „keine Antwort ≠ Antwort". **Konfundiert** mit der Messmethode (der Persona-Runner
  mappte Freitext auf `None`), deshalb erst sauber nachzumessen, bevor daraus ein Item wird
  (DEC-0030).
- **Phase-2-PM liest das Rohtranskript** (`vokabeltrainer-phase2`: 4× `Read` + `tail` der
  `~/.claude/projects/…jsonl`) — gegen das Spec-Kriterium „0 aktive Transkript-Abhängigkeiten".
  Einmal belegt, für Persona-p2 wegen Log-Redaktion ungemessen.
- **Instrumentgrenze:** `persona_run.py` protokolliert `use` nur mit `name`, ohne `input` — dadurch
  sind Pfade in Persona-Läufen nur über mtimes attribuierbar. Gehört korrigiert, **wenn** wieder
  Piloten laufen; das ist Sache des Umsetzers, nicht des Sitzungsagenten.

## Verdikt

Das PM-**Modell** trägt — Interview, Masterplan, autonome Ableitung an einer echten Domäne sind
gemessen gut. Der **Handover-Vertrag** der Einstiegsdatei trägt nicht: BUG-0016/0017 brechen genau
die Stelle, an der die Einstiegssitzung an eine frische PM-Sitzung übergeben soll. Das ist die
präzise Antwort auf „taugt V2 in der Praxis": **das Denken ja, die Übergabe nein.** Und beide
Bruchstellen hängen an derselben Wurzel, die die Messung von BUG-0016 aufgedeckt hat — die
Durchsetzungsschicht ist in genau der Einstiegssitzung inaktiv, für die sie gebraucht wird
(Watcher-Lücke, `staging/BUG-0016/messung-2026-08-10.md`).
