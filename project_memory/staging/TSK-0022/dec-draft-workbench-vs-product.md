# DEC-Entwurf — nach der Wiederherstellung über den Kernel zu capturen

**title:** Werkbank und Produkt tragen nicht dieselbe Beweislast

**context:**

Dieses Repo behandelt zwei ungleiche Dinge mit derselben Strenge. `team-kits/` (Kernel, drei
Kits, Migration) läuft in echten Projekten des Nutzers; ein Fehler dort kostet fremden Zustand.
`.claude/hooks/` bremst einen Agenten in genau diesem Repo; ein Fehler dort kostet eine Datei, die
jemand zurücksetzt.

Gemessen, Stand 2026-08-08: die Werkbank trägt eine Testdatei von **217 KB** für vier Hooks, eine
Kreuztabelle mit **1449 Zellen**, **7527** erzeugte Tilde-Subjekte und ~**17 Minuten** je
Suite-Lauf — gegen 2305 Tests für das gesamte Produkt. Drei aufeinanderfolgende Prüfrunden
(TSK-0021, TSK-0022 Runden 1–3) haben ~10 Stunden gekostet; **Runde 1 schloss ein echtes Loch**
(ein Werkzeugaufruf erreichte `project_memory/`, also den Beleg, mit dem Gate 3 urteilt), die
**Runden 2 und 3 fanden keine Angriffskette mehr** und scheiterten ausschließlich an Sätzen ÜBER
den Schutz.

Und die Kur ist teurer geworden als die Krankheit: **viermal in drei Tagen** hat das *Messen* der
Gates `team-kits/kernel/state.py` im echten Arbeitsbaum zerstört. Die Gates selbst haben in
derselben Zeit keinen Schaden verhindert.

Dazu ein Befund über das Bedrohungsmodell: gehärtet wird gegen Tilde-Verzeichnisstack-Referenzen
mit eingestreuter Quotierung, gegen Win32-Device-/UNC-Namensräume, gegen Heredoc-Rümpfe. Das sind
Wege, die ein Gegner mit Shell-Expertise **absichtlich** geht. Der einzige Akteur hier ist ein
Agent, der Anweisungen folgt; sein Irrtum nimmt den geradeaus naheliegenden Weg.

**decision:**

Die Beweislast richtet sich nach dem Schaden, den ein Fehler anrichtet, nicht nach dem Ort im
Baum.

1. **Produkt** — alles, was in ein fremdes Projekt ausgeliefert wird (`team-kits/`, Kernel,
   Migration, die Kits): **volle Strenge unverändert.** Jede Zusicherung gemessen, jeder Fix mit
   einem Test, der ohne ihn rot wird, Prüfer gegen den laufenden Code.
2. **Werkbank** — `.claude/hooks/` und was nur diese Sitzung bindet: **Fixes nur bei gemessenem
   Schaden oder einer Angriffskette, die innerhalb einer Sitzung durchläuft.** Eine Lücke ohne
   solche Kette wird als Löcherlisten-Eintrag geführt und **nicht** gebaut. Keine Härtungsrunde
   ohne einen Befund dieser Art.
3. **Prosa über die Werkbank wird gekürzt, nicht gemessen ausgebaut.** Ein Satz, der nicht da ist,
   kann nicht lügen. `CLAUDE.md` sagt es bereits selbst — *„Was das konkret trifft, sagt das Gate,
   nicht dieser Absatz"* —, und genau daran hat sich dieses Repo nicht gehalten: zwei Prüfrunden
   sind an Beschreibungen gescheitert, die es nicht hätte geben müssen. Die Verweigerung des
   Gates ist die Autorität; die Datei verweist darauf.

Die Hausregel „kein Kommentar darf Schutz behaupten, den der Code nicht baut" bleibt in Kraft und
gilt für beide. Für die Werkbank ist die Abhilfe aber **Streichen** statt Messen.

**consequences:**

TSK-0022 wird nach dem Prüfverdikt der Runde 3 geschlossen — der PASS wird für den Commit
gebraucht (Gate 3), nicht für die Vollständigkeit der Werkbank. Alle offenen Reste (H37 Rest 1–5,
H38, R1–R3) bleiben als dokumentierte Löcher stehen; es gibt keine Runde 4.

Was diese Entscheidung **nicht** aufweicht: die Zwei-Agenten-Schleife, Gate 3, und die Strenge für
TSK-0023 (Migration) und jede weitere Produktarbeit. Die Schleife hat sich bewährt — sie hat das
echte Loch der Runde 1 gefunden und mehrfach Prosa erwischt, die log.

**source:** Nutzerentscheidung 2026-08-08 auf die Frage, ob dieses Projekt over-engineert;
Prüfverdikte TSK-0022 Runden 1–3; die vier Messschäden vom 2026-08-06 bis 2026-08-08
