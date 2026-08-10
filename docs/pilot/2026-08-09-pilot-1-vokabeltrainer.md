# Pilot 1 — Vokabeltrainer (TSK-0025), Befundbericht

Zwei SDK-Sitzungen, wie ein Nutzer sie bekommt: Phase 1 die Einstiegssitzung, Phase 2 die
Sitzung danach. Niemand im Lauf erfuhr, dass es ein Versuch ist (`DEC-0025`). Persona: eine
VHS-Spanischdozentin; alle Antworten standen vor dem Lauf im Drehbuch.

**Kosten:** 3,95 $ + 3,04 $ = **6,99 $ Gegenwert** (Sonnet, 8 Nutzereingaben).
Rohdaten: `C:\Offline Repos\v2-pilot\_runner\runs\vokabeltrainer-phase{1,2}.jsonl`.

## Was getragen hat

- Die Einstiegsdatei feuerte **wörtlich** und stellte genau eine Frage, bevor irgendetwas geschrieben
  wurde. Interview auf **Produkt**ebene, keine technische Frage an die Persona.
- **Masterplan gefüllt** (81 Zeilen, kein Platzhalter), `project_config.yaml` mit Projektname,
  `repo_mode`, `local_first: true`, Stack.
- Kit vollständig installiert: `.claude/` (Agenten, Hooks, Kernel, Settings), `.codex/`,
  `AGENTS.md`, `CLAUDE.md`, `project_memory/` mit Index, Sitzungsbrief und Dashboard.
- **Der Projektmanager der zweiten Sitzung begann nicht bei null.** Er las Sitzungsbrief,
  Masterplan, alle drei Wurzelitems, `project_config.yaml`, `DEC-0001`, die Presets und seine
  eigene Rollendefinition. Das ist genau, was die Einstiegsdatei verspricht.

## Befunde

### P1 — Der Nutzer wird zweimal aus dem Gespräch geschickt, um Technisches zu tun

**Phase 1**, an eine VHS-Dozentin, dreimal hintereinander:

> „Tippe in das Chatfeld: `/hooks` und drücke Enter … Ohne diesen einen Schritt kann ich die
> Freigabe nicht speichern, **das System blockt es aktiv**."

**Phase 2**, als letzte Aussage der Sitzung:

> „…führe bitte jetzt in einem Terminal aus:
> `powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.claude\team-kits\scaffold_team.ps1" -Team dev-team -Preset team`
> Danach, falls ein `/hooks`-Bestätigungsdialog erscheint: bestätigen — und dann **diese Session
> neu starten**."

Der Lauf **bleibt stehen**, statt zur vorgesehenen Neustart-Bitte zu kommen. Die Trust-Lücke ist als
`L5` bekannt; als **Nutzererlebnis** war sie nie gemessen. Nach acht Nutzereingaben existiert
**keine Zeile Produktcode**.

### P2 — Der Kernel kodierte Umlaute doppelt, und daraus wurden drei Wurzelitems

Der Agent bemerkte es selbst: *„…dass eine interne Systemfunktion Umlaute auf diesem Rechner falsch
kodiert hat. Ich habe das erkannt, korrigiert und den betroffenen Entwurf sauber neu angelegt."*

Rohbytes: `PR-0002` trägt `f\xc3\x83\xc2\xbcr` (doppelt kodiert), `PR-0001` und `PR-0003` sind
sauberes UTF-8. Die Einstiegsdatei verlangt **genau ein** Wurzelitem, nummeriert `-0001`; entstanden
sind drei, zwei davon `SUPERSEDED`.

**Die Kette ist Kodierungsfehler + Unveränderlichkeit (`L2`):** ein Feld korrigieren geht nicht,
also wird ein neues Item geprägt. Ein Nutzerprojekt startet mit zwei toten Items.

### P3 — Der Projektmanager las das Sitzungstranskript

Unter den gelesenen Dateien steht `55b6f61b-…-…jsonl` — die Transkriptdatei der Sitzung.
`docs/HARNESS_V2_SPEC.md` führt **„0 aktive Transkript-Abhängigkeiten"** als modusunabhängiges
Abnahmekriterium. Ob es eine Abhängigkeit oder nur Neugier war, ist aus dem Protokoll nicht zu
entscheiden — gemessen ist nur, dass er sie gelesen hat.

### P4 — Das Preset steht auf der Vorlage, und die Korrektur kostet ein zweites Scaffold

`project_config.yaml` trägt `preset: solo` — den Vorlagenwert. Die Einstiegsdatei verlangt
ausdrücklich das **im Interview bestätigte** Preset, „sonst startet jedes Projekt still als solo".
Der Projektmanager der zweiten Sitzung will `team` und verlangt dafür einen **zweiten
Scaffold-Lauf** von Hand.

**Anteil meines Apparats daran, offen gesagt:** mein Drehbuch deckte die gestellten Fragen nur
teilweise — **7 von 11 Antworten waren Rückfall auf die erste Option**. Ob die Persona nach der
Teamgröße gefragt wurde und meine Sonde falsch antwortete, oder ob nie gefragt wurde, ist damit
**nicht** entscheidbar. Das ist eine Grenze der Messung und wird als solche geführt.

## Die Zahl, nach der TSK-0025 fragt

**Nutzereingaben bis zum ersten lauffähigen Ergebnis: 8 — und es gibt keines.**
Der Ablauf blieb zweimal an derselben Wand stehen: einer Berechtigung, die nur der Mensch außerhalb
des Gesprächs erteilen kann.

## Was dieser Pilot NICHT gemessen hat

Ob der Ablauf nach einer echten `/hooks`-Bestätigung durchläuft — im Stapelbetrieb ist der Dialog
nicht bedienbar. Das gehört in einen interaktiven Lauf und ist die erste offene Frage für Pilot 2.
