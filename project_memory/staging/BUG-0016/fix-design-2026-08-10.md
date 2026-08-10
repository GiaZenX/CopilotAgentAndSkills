# Fix-Design für BUG-0016 (Handover-Überlauf), 2026-08-10

Belegt durch einen Design-Scan (claude-code-guide, Sonnet), gegen unsere eigenen Messungen
(`messung-2026-08-10.md`, `reload-recherche-2026-08-10.md`) gehalten. Liegt in `staging/`, weil
BUG-0016 unveränderlich ist (L2) und dies der Entwurf ist, aus dem ein Fix-Auftrag entsteht — nach
einer Nutzerentscheidung über die Invasivität (siehe unten).

## Der einzig tragfähige Mechanismus

Ein **globaler** `PreToolUse`-Hook in `~/.claude/settings.json` + eine **Marker-Datei** +
ein **projekteigener `SessionStart`-Cleanup-Hook** (Matcher `startup`).

- Nur ein globaler Hook ist in der **Einstiegssitzung** aktiv, bevor irgendein Projekt-Hook lädt.
  Von der Watcher-Lücke **nicht** betroffen (er existiert per Definition schon vor Sitzungsstart).
  `/clear` umgeht ihn nicht (gemessen: `/clear` lädt keinen frisch installierten Hook, also bleibt
  der globale Block korrekt stehen).
- **Marker-Gate macht ihn außerhalb von Kit-Projekten unsichtbar:** fehlt `.claude/HANDOVER_PENDING`
  im `cwd` → sofort `exit 0`. Nur mit Marker prüft er `tool_name`/`tool_input` und verweigert
  Produkt-Writes/Ableitung. Dasselbe Muster wie die Kit-Gates hier.
- Das Scaffold setzt den Marker; der projekteigene `SessionStart(startup)`-Hook löscht ihn — und
  der feuert gemessen **nur bei echtem Prozess-Neustart**, ist also ein fälschungssicheres Signal
  „ein Neustart hat stattgefunden".

## Der Haken, der dem Nutzer gehört

Ein globaler Hook läuft als Prozess bei **jedem** Write/Edit/Bash/Task in **jeder** Claude-Code-
Sitzung des Nutzers, **für immer** — auch außerhalb von Kit-Projekten. Verhaltensrisiko gering
(No-op ohne Marker), aber ein dauerhafter Prozessstart-/Latenztarif auf die gesamte Nutzung.
**Invasivität ist eine Nutzerentscheidung, keine reine Bausache.**

## Zwingende Voraussetzung, aus dem Quellcode gelesen

`user/merge_settings.py:85-89`: außer bei `permissions` (Union) gewinnt bei jedem Top-Level-Key der
**bestehende** Wert des Nutzers. Ein neuer `hooks`-Key würde also nur übernommen, wenn die
`~/.claude/settings.json` des Nutzers **noch keinen** `hooks`-Key hat. Wer schon eigene globale
Hooks führt, bekäme unseren Handover-Hook beim Merge **stillschweigend übersprungen**.
`merge_settings.py` braucht darum für `hooks` dieselbe Array-Union-Sonderbehandlung wie heute für
`permissions.allow/deny` — sonst installiert sich der Fix bei genau den Power-Usern nicht.

## BUG-0017 ist ein SEPARATER Fix

Dieselbe Durchsetzungsstelle löst BUG-0017 **nicht**: der Freigabe-/Mint-Weg bricht **während** der
Scope-Freigabe im Auto-Init, also **vor** Marker/Installation — der globale Gate-Hook ist dort noch
nicht scharf. BUG-0017 ist ein eigenes Problem (AskUserQuestion-Identität im Headless/SDK-Betrieb)
und braucht einen eigenen Fix. Nicht bündeln.

## Vor dem Bau zu MESSEN (DEC-0030), nicht anzunehmen

1. Feuert ein **User-Scope**-`PreToolUse`-Hook unter `bypassPermissions` genauso wie ein Projekt-Hook?
   (Projekt-Scope bestätigt, User-Scope nicht.)
2. Überspringt `merge_settings.py` wirklich, wenn das Ziel schon einen `hooks`-Key trägt?
   (aus dem Quellcode plausibel, an einer echten Fremd-Hook-`settings.json` nicht durchgespielt.)
3. Feuert der `SessionStart(startup)`-Cleanup-Hook **nur** bei echtem Neustart, nicht bei
   IDE-Reconnect / Terminal-Reattach?
4. Spürbare Latenz des globalen No-op-Hooks über eine normale Nicht-Kit-Sitzung.

## Ergänzend, nicht tragend

Die Neustart-Bitte **vor** Masterplan/Wurzelitem ziehen verkleinert nur das Ableitungsfenster vor
dem ersten Stopp — löst das Loch nicht (gemessen: alle vier Läufe lieferten die Bitte schon
wörtlich und schrieben trotzdem danach). Als Zusatz sinnvoll, als Ersatz nicht.
