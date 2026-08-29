# Die gehostete CI war auf jedem Push rot — Klassifikation und Entscheidungen

**Anlass:** `BUG-0069` / `TSK-0088`. Gemessene Läufe: **33202404872** (Push `8ddce26`, TSK-0086) und
**33225215675** (Push `d66525d`, TSK-0087) — beide `conclusion: failure`, beide tragen denselben Satz
Klassen; TSK-0087 hat keine neue hinzugefügt. Lokal war derselbe Baum grün (3856 passed / 14 skipped), die
gehosteten Läufe meldeten „All jobs have failed"; das ist der schlechteste Zustand, den eine Prüfung
erreichen kann, weil er dem Nutzer beibringt, das einzige externe Signal zu ignorieren.

Dieses Dokument existiert, damit der nächste rote CI-Lauf nicht wieder bei null anfängt.

## Die Bucket-Tabelle (AC-2)

Grundlage: `gh run view <id> --log-failed` für beide Plattformen, jede Zeile der
`short test summary info` einem Wurzelgrund zugeordnet. Die Buckets summieren sich **exakt** auf die
gemeldeten Zahlen — es bleibt nichts unklassifiziert.

| # | Wurzelgrund | win F | win E | ubu F | ubu E |
|---|---|---|---|---|---|
| A | Shallow Clone: `actions/checkout` nimmt Tiefe 1, `tools/test_migrate.py` baut seine V1-Fixture aus einem Commit 72 Schritte zurück | 3 | 96 | 3 | 96 |
| D | `sys.path` wächst unbegrenzt → `PYTHONPATH` überschreitet Linux' `MAX_ARG_STRLEN` → `OSError [Errno 7] Argument list too long: 'bash'` | 0 | 0 | 17 | 52 |
| F | kein Windows-PowerShell auf ubuntu, vier Aufrufstellen starten `powershell` ohne Frage | 0 | 0 | 4 | 0 |
| E1 | host-abhängige Shell-/Pfad-Erwartung in einer host-unabhängigen Tabelle (`2> NUL`, PowerShell-`/dev/null`, `\\?\Z:`) | 0 | 0 | 3 | 0 |
| E2 | Laufwerks-Präfix mit `os.path.splitdrive` gelesen — auf POSIX gar nicht als solches erkannt | 0 | 0 | 3 | 0 |
| C | Rekursions-Fixture gegen das Item-Budget, CPython 3.14 | 1 | 0 | 1 | 0 |
| I | `pip-audit` auf dem Runner nicht installiert → die Verfügbarkeitsprobe misst den Runner statt den Zweig | 1 | 0 | 1 | 0 |
| B | `os.path.relpath(tmp, ROOT)` über zwei Laufwerke (Workspace D:, tmp C:) | 1 | 0 | 0 | 0 |
| G | case-sensitives Dateisystem: der Case-Flip öffnet nichts | 0 | 0 | 1 | 0 |
| H | Lease-TTL 10 ms, `report.doctor` gewinnt das Rennen auf schnellem Host | 0 | 0 | 1 | 0 |
| | **Summe** | **6** | **96** | **34** | **148** |

**Die ~100 ERRORs je Plattform hatten genau eine Wurzel** — Klasse A, dieselbe wie drei der
Fehlschläge. Auf ubuntu kamen 52 weitere aus Klasse D. Die ubuntu-Mehrfehler (34 statt 6) sind
D, F, E1, E2, G, H — alle „POSIX liest ein Wort anders als Windows" oder „dieses Werkzeug gibt es
hier nicht", keiner ein Produktfehler im engeren Sinn außer E2.

## Entscheidung je Klasse, und warum

| Klasse | Entscheidung | Warum diese und nicht eine andere |
|---|---|---|
| **A** | Umgebung liefern: `fetch-depth: 0` | Die Historie **ist** das Fixture-Material. Ein Skip hätte die größte Testgruppe der Suite stillgelegt, um eine Workflow-Zeile zu sparen. Tiefe `0` statt einer Zahl, weil eine Zahl eine Behauptung darüber wäre, wie tief der Commit bleibt. |
| **D** | Ursache statt Symptom: kein Test hinterlässt dem nächsten einen `sys.path`-Eintrag | Fünfzehn Leser der Liste zu deduplizieren hätte das Symptom an fünfzehn Stellen behandelt; das Wachstum ist der Defekt und hat genau einen Ort. |
| **F** | Launcher erfragen (`powershell_or_skip`) + Sweep über `tools/` | Die vier Stellen ohne Frage waren die Ausnahme, nicht die Regel — die älteren tragen ihre eigene `shutil.which`/`os.name`-Klausel. Deshalb prüft ein Sweep die **Eigenschaft** („irgendwo auf dem Weg wird gefragt") statt eine Regel über einen Helfer aufzustellen. |
| **E1** | Erwartung aus `os.devnull` ableiten, je ein eigener Test | Das Gate ist bereits host-bewusst und auf beiden Hosts **richtig**; falsch war die Tabelle, die eine host-abhängige Zeile neben host-unabhängige stellte. Eine Tabelle kann nicht sagen, warum eine Zeile anders ist. |
| **E2** | **Produktänderung**: `state.names_a_drive`, ein Leser für jeden Host | Drei Docstrings versprachen „kein Laufwerksbuchstabe", der Code baute das nur auf Windows. Der Zustandsbaum reist (auf Windows geschrieben, auf Linux gelesen), und eine geprägte Freigabe für `C:/elsewhere` trifft nichts, was das Gate je erzeugt — genau der Fehlermodus von Befund F5. Verhalten auf Windows unverändert, auf POSIX strikt strenger; alte Freigaben lösen weiter auf. |
| **C** | Suchraum vom Budget begrenzen, sonst gezählter Skip + neuer Test für den Arm | Ein Body, der tief genug ist, passt auf CPython 3.14 nicht mehr ins Item-Budget. Das ist eine Tatsache über den Interpreter, kein Defekt — sie gehört als Skip mit Grund ins Log, nicht als Rot. |
| **I** | Verfügbarkeitsprobe stubben | Der Test behauptet, „die Kommandozeile zu prüfen, die der Check ausführen WÜRDE". Ob `pip-audit` installiert ist, ist ein anderes Subjekt; es dem Host zu überlassen machte den Host zum Subjekt. |
| **B** | Datei relativ zu **ihrem eigenen Kit** benennen | `_pinned_files` setzt jeden Pfad aus `kit` zusammen, dieser Start ist also immer ausdrückbar — `relpath(path, ROOT)` ist es nicht, sobald beide auf verschiedenen Windows-Mounts liegen. |
| **G** | Case-Empfindlichkeit an der gerade geschriebenen Datei messen | Die Prämisse des Tests („der Case-Flip öffnet dieselbe Datei") ist eine Eigenschaft des Dateisystems. Gefragt wird die Datei, nicht `os.name`. |
| **H** | Auf genau das Prädikat warten, das `report.doctor` liest | Eine TTL von 10 ms plus sofortiger Aufruf ist ein Rennen; der Lease sagt selbst, wann er abläuft. |

Zusätzlich, weil AC-1 verlangt, dass ein Skip **seinen Grund nennt**: der Testschritt läuft jetzt mit
`-rs`. Unter `-q` allein stand im Log nur die Zahl, und ein ehrlicher Skip war von einem verstummten
Test nicht zu unterscheiden.

## Was gemessen wurde

- **POSIX-Rig** (WSL Ubuntu 24.04, CPython 3.12.3, pytest 9.1.1, Klon des Arbeitsbaums außerhalb des
  Repos): vorher 33 failed / 3777 passed / 32 skipped / **52 errors** — Test für Test deckungsgleich
  mit der ubuntu-Liste. Nachher **2 failed / 3858 passed / 39 skipped / 0 errors**; die zwei Reste
  sind Rig-Artefakte (kein importierbares `ruff`; der Klon kann `project_memory/` nicht enthalten,
  weil Gate 1 das Kopieren kanonischen Zustands verweigert) und beide auf dem gehosteten ubuntu grün.
- **Shallow Clone** (`git clone --depth 1`): `tools/test_migrate.py` 3 failed / 42 passed /
  **96 errors** — identisch zu beiden Runnern. Mit voller Historie: 141 passed.
- **Cross-Mount** (dieser Host hat nur C:; `subst` scheidet aus, weil `Path.resolve()` die Zuordnung
  auflöst — genommen wurde ein echter zweiter Mount über `--basetemp=//localhost/C$/…`): vorher
  `ValueError: path is on mount '\\localhost\C$', start on mount 'C:'`, nachher grün.
- **`sys.path`-Wachstum**: über 211 Tests 166 Einträge, davon 14 verschieden, 11 049 Bytes verbunden
  — rund 0,7 Einträge je Test; Linux' `MAX_ARG_STRLEN` liegt bei 131 072.
- **Windows, ganze Suite**: 3885 passed / 14 skipped — dieselbe Skip-Zahl wie vor der Runde, auf
  diesem Host geht also keine Messung verloren.

## Offene Reste, benannt statt geschlossen

1. **Der eigentliche Beweis ist der nächste Push.** Kein lokales Rig **ist** der gehostete Runner:
   das POSIX-Rig fährt CPython 3.12 auf Ubuntu 24.04, nicht 3.14.7 auf `ubuntu-latest`, und für den
   Windows-Runner mit Workspace auf D: gibt es hier nur den UNC-Ersatz. Der Lauf nach dem Push ist,
   was zählt.
2. **Deckungsverlust bei Klasse C.** `test_cli_capture_survives_a_body_no_parser_can_bound` **skippt
   auf beiden Runnern** — CPython 3.14 rekursiert innerhalb des 12 288-Byte-Budgets nicht. Der
   `RecursionError`-Arm bleibt überall gemessen
   (`test_the_too_deep_refusal_is_what_the_parser_giving_up_produces`), aber die Hälfte „ein echter
   tiefer Body erreicht ihn" läuft nur noch dort, wo der Interpreter innerhalb des Budgets aufgibt.
   Heute ist das ein Entwicklerhost mit CPython 3.13; mit dessen nächstem Upgrade fällt auch das weg.
3. **Der Interpreter bleibt absichtlich ungepinnt** (`python-version: "3.x"`), und Klasse C ist der
   Preis dafür. Die Entscheidung steht jetzt im Workflow neben dem Knopf: die Kits laufen im Feld auf
   dem Interpreter, den die Maschine mitbringt, und `PYTHONUTF8: "0"` existiert, um dem nächsten
   früh zu begegnen. Wer das umdreht, tauscht diesen Deckungsverlust gegen ein spätes Erwachen.
4. **Milder Rest derselben Familie wie H:** `tools/test_report.py:224-227` setzt `ttl_seconds=0.01`
   und schläft 0,05 s. Das ist **nicht** dasselbe Rennen wie H — der Schlaf ist eine untere Schranke
   auf echte verstrichene Zeit, während der `doctor`-Test überhaupt nicht wartete. Die Marge ist
   geraten statt abgeleitet; das bleibt offen und ist hier benannt, nicht in dieser Runde geändert.
5. **Grenze des PowerShell-Sweeps:** er liest das Programm aus der Quelle — als Literal oder als
   Name, den derselbe Geltungsbereich an genau einen Wert bindet. Ein zur Laufzeit
   zusammengesetzter Launcher ist kein Subjekt, und der Sweep sagt darüber nichts. Der Boden unter
   dem Leser (`_POWERSHELL_LAUNCH_FLOOR`) fängt ab, dass er die Form ganz verlernt.
6. **`names_a_drive` überverweigert auf POSIX bewusst**: jedes Wort mit Doppelpunkt an zweiter
   Stelle (`a:b`, `1:x`) gilt als Laufwerksangabe. Ein POSIX-Projekt mit einem solchen Namen an der
   Wurzel bekommt eine meldbare Verweigerung; die Gegenrichtung prägt eine Freigabe, die nichts
   trifft.
