# Recherche zum Neustart-/Reload-Verhalten (zu BUG-0016), 2026-08-10

Belegt aus der Claude-Code-Doku durch einen claude-code-guide-Agenten (Sonnet). Quellen unten.
Liegt in `staging/`, weil BUG-0016 unveränderlich ist (L2) und dies der Kontext ist, den ein
späterer Umsetzer erbt.

## Der Kern: unsere Annahme ist zu pauschal

`~/.claude/CLAUDE.md` und BUG-0016 nehmen an: „Hooks und Rollenbindung sind erst nach einem
Neustart aktiv." Die Doku sagt etwas Genaueres:

- **`hooks` und `permissions` werden LIVE nachgeladen** (File-Watcher + `ConfigChange`-Event),
  ohne Neustart. (`settings.md`, „When edits take effect")
- **ABER der Watcher deckt nur Verzeichnisse, die beim Sitzungsstart schon existierten.**
  (`sub-agents.md`: „the watcher covers only directories that existed when the session started,
  so after creating a scope's first agent file in a new `agents` directory, restart to load it.")

Auto-Init legt `.claude/` **frisch** an — in einer Sitzung, in der es das Verzeichnis vorher nicht
gab. Damit greift genau diese Watcher-Lücke. Das ist eine **präzisere, messbare** Erklärung des
gemessenen Bugs als „Reload gibt es nicht".

- Für das **`agent:`-Feld** (Bindung des Hauptthreads an die PM-Rolle) sagt die Doku **nichts** —
  weder Live-Reload noch Restart-only. `--agent` ist ein Session-Start-Flag; das legt „session-
  konstituierend" nahe, ist aber nicht belegt. **Das ist die eigentliche offene Frage.**

## Die drei konkreten Fragen des Nutzers

1. **Neustart aus der interaktiven Sitzung erzwingen?** **Nein.** `SessionStart`/`SessionEnd`-Hooks
   sind laut `hooks.md` ausdrücklich **nicht blockierend** — sie können den Nutzer nicht anhalten.
   `claude respawn` existiert, aber nur für **Hintergrund-Sitzungen** (Daemon), nicht für die
   interaktive Vordergrund-Sitzung. Kein unterstützter Weg, aus einem Hook den Prozess neu zu
   starten.
2. **Slash-Kommando automatisch auslösen?** Nur aus dem **steuernden SDK-Code** (man sendet
   `/clear` als Prompt-String). **Nicht** aus einem Hook, nicht in der interaktiven CLI ohne
   Tastatureingabe des Nutzers.
3. **`/clear` als Ersatz?** Zwiespältig. `/clear` ist **kein** Blindgänger — es feuert
   `SessionStart` erneut (`hooks.md`, Trigger `"clear"`) und baut den System-Prompt neu auf. **Aber
   ob es die `agent:`-Bindung neu auflöst, ist nicht dokumentiert.** Ein automatisch ausgelöstes
   `/clear`, das die Bindung NICHT neu lädt, wäre schlimmer als nichts — es täuscht einen Neustart
   vor.

## Was daraus folgt

- **BUG-0016 bleibt gültig, aber sein Mechanismus ist zu schärfen:** nicht „Reload existiert
  nicht", sondern „der Watcher sah `.claude/` beim Start nicht, und für `agent:` ist der Reload-
  Status unbekannt". Das gehört in den Fix-Auftrag.
- **Der eigentliche Fix von BUG-0016 ist Verhalten, nicht Neustart-Erzwingung:** Nach der Neustart-
  Bitte darf die Einstiegssitzung nichts mehr am Produkt ableiten oder schreiben — unabhängig davon,
  ob ein Neustart erzwingbar ist. Ein erzwungener Neustart würde das Fenster nur verkleinern, nicht
  schließen.
- **Zwei Dinge sind vor jedem Fix EMPIRISCH zu messen** (der Guide-Agent schlägt es selbst vor, und
  ich bin heute fünfmal an Vermutung gescheitert):
  1. Lädt ein frisch in einem neuen `.claude/` angelegtes `settings.json` seine `hooks` in der
     laufenden Sitzung nach — oder greift die Watcher-Lücke?
  2. Löst `/clear` die `agent:`-Bindung neu auf?
  Beides ist mit einem echten SDK-Lauf messbar (Sonde: `.claude/` frisch anlegen → `/clear` senden
  → prüfen, ob Hook/Bindung aktiv). Erst danach lohnt eine Designentscheidung.

## Quellen
- settings.md · hooks.md · sub-agents.md · commands.md · cli-reference.md
- agent-sdk/claude-code-features.md · agent-sdk/slash-commands.md
- (schwächer, GitHub-Issue) `reloadSkills` — nicht offiziell verifiziert
