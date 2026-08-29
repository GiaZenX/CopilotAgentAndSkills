# /cd-Sofortbindung (Claude Code 2.1.246) — Recherche zu FR-0059

Sonnet-Recherche 2026-08-29, Anlass: Nutzer-Hinweis auf den Changelog-Eintrag. Item: `FR-0059`.
Quellen: offizielles `CHANGELOG.md` (Kopie lag unter `_round-scratch/FR-0059/`), Doku
`code.claude.com/docs/en/permissions` §"Move the session to another directory",
`docs/en/settings-reference` Eintrag `agent`. Was hier steht, ist BELEGT, ABGELEITET oder
UNBEKANNT — je markiert; nichts davon ist gemessen, der Messplan steht unten.

## Belegte Fakten

- **Changelog 2.1.246** (wörtlich): "Improved `/cd`: the new directory's project settings,
  hooks, `.mcp.json` servers (behind the usual approval prompt), skills, and agents now take
  effect right after the move instead of on `--resume`". `/cd` selbst existiert seit 2.1.169.
- **Der Wechsel ist vollständig**: die Doku sagt ausdrücklich, dass die MCP-Server und Hooks des
  ALTEN Verzeichnisses abgehängt werden — `/cd` ergänzt nicht, es tauscht.
- **`${CLAUDE_PROJECT_DIR}` bleibt beim Startort stehen** (Doku wörtlich: "Hooks the move
  activates still receive `${CLAUDE_PROJECT_DIR}` set to the project root where the session
  started"), während das `cwd`-Feld im Hook-Input dem aktuellen Verzeichnis folgt. Beides
  nebeneinander, kein Widerspruch.
- **`/cd` ist KEIN Modell-Werkzeug** (Doku wörtlich: "`Cd` is not a model-invocable tool:
  Claude can't call it, and the rules apply only when you run `/cd` yourself"). Nur die tippende
  Person kann es auslösen — kein Prompt-Injection-Pfad erreicht es.
- **Trust-Dialog**: interaktiv listet er vor der Aktivierung die Hooks/Regeln des Zielverzeich-
  nisses auf; Ablehnung lässt die Sitzung, wo sie ist. In `claude -p`/SDK-Läufen erscheint er
  NIE — und die Doku-Tabelle führt Hooks dort als "Used" auch für nie-vertraute Verzeichnisse.
- **Vorher/Nachher ausdrücklich bestätigt**: "Before v2.1.246, `/cd` didn't apply the new
  directory's settings, hooks, MCP servers, or skills until you resumed" — die Annahme unserer
  Neustart-Zeremonie GALT und gilt für `/cd` seit 2.1.246 nicht mehr.
- **Dieser Host lief zur Recherche auf 2.1.239** — das neue Verhalten ist hier noch nicht aktiv;
  jede Messung braucht erst ein CLI-Update.
- **Ein `cd` im Bash-Werkzeug ist etwas anderes** und löst keine Neubindung aus.

## Abgeleitet / unsicher

- Die `/cd`-Bulletliste nennt "its subagents" — das sind nach Wortlaut die im Zielverzeichnis
  VERFÜGBAREN Subagenten, nicht die `agent:`-Bindung der laufenden Sitzung (deren Doku-Eintrag
  sagt "Start every session as…", eine Sitzungsstart-Aussage). Das ist SCHLUSSFOLGERUNG, nicht
  Zitat — und die wichtigste offene Frage für die Zeremonie.
- Die Aussage "`/cd` in `-p` verfügbar ab 2.1.205" stammt aus einer Modell-Zusammenfassung,
  nicht aus direkt gelesenem Doku-Text — vor einer Messung gegenprüfen.
- Statuszeilen-Verhalten bei `/cd`: keine Quelle gefunden.

## Einordnung für unsere Gates und die Neustart-Zeremonie

1. **Entwarnung für die Angriffsflanke**: Eine Sitzung kann sich nicht selbst per Tool-Call in
   ein präpariertes Verzeichnis bewegen und unsere Gates abstreifen — `/cd` verlangt den
   Menschen am Terminal. Interaktiv steht zusätzlich der Trust-Dialog davor.
2. **Die dokumentierte Restsorge**: In `-p`/SDK-Läufen gibt es keinen Trust-Dialog und Hooks
   nie-vertrauter Verzeichnisse laufen trotzdem — relevant nur, FALLS `/cd` dort überhaupt
   auslösbar ist (unbekannt, Messplan Punkt 6).
3. **Für die Zeremonie**: Hooks, Settings, MCP, Skills bräuchten nach einem `/cd` keinen
   Neustart mehr — ob die `agent:`-Bindung (die den PM aktiviert) mitwechselt, ist unbelegt.
   KEINE Änderung am Install-/Update-Fluss ohne die Messung; die Doku allein trägt sie nicht.
4. **`CLAUDE.md`-Satz dieses Repos** ("was beim Sitzungsstart bindet, ist die Registrierung"):
   bleibt wahr für alles außer `/cd`; sobald dieser Host ≥ 2.1.246 läuft, verdient der Satz die
   Fußnote, dass `/cd` die Registrierung mitten in der Sitzung tauscht — mit Trust-Dialog davor.

## Messplan (für eine spätere Umsetzer-Runde, Scratch unter `_round-scratch/<TSK-ID>/`)

1. CLI aktualisieren, `claude --version` ≥ 2.1.246 bestätigen (Host lag bei 2.1.239).
2. Zwei Test-Verzeichnisse A/B: je ein log-schreibender PreToolUse-Hook, je eine eigene
   `agent:`-Bindung auf unterscheidbare Test-Agenten.
3. Interaktiv in A starten, A-Hooks/Agent A bestätigen; `/cd` nach B; ohne Neustart messen:
   feuern B-Hooks, und antwortet die Sitzung als B oder weiter als A? (Die zentrale Frage.)
4. `${CLAUDE_PROJECT_DIR}` nach dem Wechsel loggen — steht dort wirklich der A-Pfad?
5. Trust-Dialog-Wortlaut bei nicht-vertrautem B protokollieren.
6. `-p`/SDK: ist `/cd` dort überhaupt auslösbar? Falls nein, festhalten — dann entfällt die
   Restsorge aus Punkt 2 oben von selbst.
7. Falls Agent B in Schritt 3 NICHT sofort greift: `--resume` aus B fahren und bestätigen, dass
   genau der `agent:`-Teil den Neustart weiterhin braucht.
8. Statuszeile nebenher beobachten.
9. Erst mit diesen Messungen über eine Zeremonie-Änderung entscheiden — eigene Runde, eigenes
   Item.

## Offen

Agent-Bindungs-Timing (Kernfrage); `/cd`-Auslösbarkeit in `-p`/SDK; programmatische Trigger
jenseits des Modells (Hook/MCP — nicht geprüft); Statuszeile; stille Verhaltensänderungen nach
2.1.246 ohne Changelog-Eintrag (bis 2.1.251 keiner gefunden).
