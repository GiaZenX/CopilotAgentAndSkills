# Zeilenenden in diesem Repo — die Ursache, was durchgesetzt wird, und was ausdrücklich nicht

Betrifft `BUG-0025` / `PR-0007` AC-2. Gemessen am 2026-09-04 im Arbeitsbaum
`C:\Offline Repos\AgentAndSkills`.

## Die Ursache liegt in der Git-Konfiguration, und dieses Repo repariert sie nicht

```
git config --get core.autocrlf            -> true    (LOKALE Konfiguration dieses Klons)
git config --system --get core.autocrlf   -> true    (Konfiguration des Hosts)
git config --global --get core.autocrlf   -> (nicht gesetzt)
```

`core.autocrlf=true` ist der Git-for-Windows-Standard. Er sagt: beim Auschecken CRLF schreiben,
beim Einchecken auf LF zurückrechnen. `.gitattributes` sagt seit BUG-0025 `* text=auto eol=lf`, und
**`eol=lf` schlägt `core.autocrlf`** — ein frischer Klon ist deshalb auf jeder Plattform LF, und ein
frischer Arbeitsbaum dieses Repos ist es auch (gemessen: der Worktree `g4-hygiene` trägt null
CRLF-Dateien, der Haupt-Checkout 53).

**Dieses Repo ändert die Git-Konfiguration des Nutzers nicht.** Kein Skript, kein Hook und kein
Installer schreibt `core.autocrlf`, und das ist eine Entscheidung, keine Lücke: die Einstellung gilt
für jedes Repo auf dieser Maschine, und ein Werkzeug, das sie umstellt, greift in Projekte ein, über
die es nichts weiß. Was hier durchgesetzt wird, endet an der Grenze dieses Repos.

## Warum die Zeilenenden hier überhaupt etwas entscheiden

Zwei Prüfungen lesen **rohe Bytes von der Platte**, nicht normalisierten Text:

* `lead_package.size` gegen `tools/lead_package_sizes.json` (`tools/validate.py`, Schritt 9) — eine
  CRLF-Datei wächst um ein Byte je Zeile, und das Lead-Paket reißt sein aufgezeichnetes Maß.
  `install.sh` ruft `validate.py` **vor** der Installation auf und bricht dann mit `exit 1` ab: ein
  solcher Klon installiert gar nichts, auch keinen Hook. Das ist BUG-0025 von Anfang bis Ende.
* der Spiegelvergleich in `tools/validate.py` (Schritt 10) — zwei inhaltsgleiche Dateien mit
  verschiedenen Zeilenenden sind ihm zwei verschiedene Dateien.

Der Kit-Hash ist **nicht** betroffen: `kernel.hashing.kit_hash` normalisiert CRLF, bevor er
digestiert. Deshalb kann eine CRLF-Datei grün durch den Versionsstempel gehen und trotzdem die
Größenprüfung reißen.

## Was `.gitattributes` festlegt, und wie „binär" entschieden wird

`* text=auto eol=lf` ist eine **Definition**, keine Aufzählung von Endungen: git entscheidet
Text gegen Binär **an den Bytes** — ein NUL in den ersten 8000. Dass diese Heuristik und ein reiner
NUL-Scan über diesen Baum übereinstimmen, und dass die Pin-Zeile wirklich wirkt, misst
`tools/test_repo_hygiene.py::test_git_decides_binary_by_bytes_and_pins_every_text_file_to_lf`; es
fragt `git check-attr` nach der **Wirkung** statt die Datei zu durchsuchen. Ein Normalisierer, der
nach Endung ginge oder einfach jedes `\r\n` ersetzte, würde die Binärdateien beschädigen, die
CRLF-Bytepaare im Inhalt tragen — wie viele das gerade sind, steht im Rundenprotokoll und nicht
hier, damit die Zahl nur an einer Stelle altert.

Die `binary`-Zeilen daneben (`*.woff2`, `*.png`) sind der Gurt neben dem Hosenträger, für die eine
teure Richtung: eine Binärdatei, deren erste 8000 Bytes zufällig kein NUL tragen, würde sonst
konvertiert. Sie sind eine Aufzählung und tragen darum einen Stolperdraht, der **beide** Enden misst
— ein Eintrag, der nichts mehr trifft, und eine Binärart, die kein Eintrag nennt:
`tools/test_repo_hygiene.py::test_every_binary_pin_names_a_kind_the_tree_has_and_every_kind_is_pinned`.

## Was passiert, wenn doch eine CRLF-Datei entsteht

`.gitattributes` regelt das **Auschecken**. Es hindert niemanden daran, danach CRLF in eine
verfolgte Datei zu schreiben — ein Editor, ein Generator, eine Shell-Umleitung auf diesem Host tun
das. Genau dafür gibt es die Prüfung und das Werkzeug:

* `tools/test_repo_hygiene.py::test_no_tracked_text_file_checks_out_with_crlf` wird rot und **nennt
  jede Datei**. Ausgenommen ist allein der kanonische Teil von `project_memory/`, weil dorthin kein
  Werkzeugschreibzugriff reicht (Gate 1); diese Dateien werden gemeldet, nicht verschwiegen.
* `python tools/normalise_line_endings.py` sagt, was es täte; `--apply` schreibt.
  **Vorbedingung je Datei:** die CRLF-normalisierten Bytes müssen dem Blob in `HEAD` **byteweise**
  gleichen. Wo nicht, wird die Datei verweigert und benannt, nie stillschweigend übersprungen — und
  die Verweigerung nennt, **was** sie vor sich hat. Zwei Dinge können falsch sein, und sie schließen
  einander **nicht** aus; darum werden sie getrennt gefragt, und der Vergleich läuft gegen den
  **normalisierten** Blob:
  * der Blob in `HEAD` ist LF und die Datei weicht darüber hinaus ab → sie trägt eine echte, nicht
    eingecheckte Änderung, und eine Zeilenenden-Reparatur darf keine verschlucken;
  * der Blob in `HEAD` trägt **selbst** CRLF → dann ist der Arbeitsbaum nicht das Problem,
    `git status` meldet auf diesem Grund nichts, und was neu geschrieben werden muss, ist der Index:
    `git add --renormalize -- <datei>`. Dieses Werkzeug ist dafür nicht zuständig und sagt es;
  * **beides zugleich** — ein CRLF-Blob **und** eine Handänderung. Dann meldet `git status` die
    Datei sehr wohl, und `git add --renormalize` nähme die fremde Änderung mit in den Index. Das
    Werkzeug nennt in diesem Fall **beide** Gründe und empfiehlt **keinen** der zwei Befehle
    allein: erst die inhaltliche Änderung entscheiden, dann renormalisieren.
  * Ausgenommen ist der kanonische Teil von `project_memory/`: er wird **aufgelistet** und nicht
    angefasst, mit demselben Prädikat (`normalise_line_endings.repairable`), mit dem die Prüfung
    ihn ausnimmt.

Wie viele solcher Dateien ein Checkout gerade trägt, sagt das Werkzeug selbst im Trockenlauf —
eine Zahl an dieser Stelle wäre eine zweite, die altert. Die Normalisierung des Haupt-Checkouts ist
ein **Merge-Schritt**: sie gehört in den Baum, in dem committet wird, nicht in einen
Stream-Worktree, der ohnehin schon LF ist; die Messung des Tages steht im Rundenprotokoll unter
`project_memory/staging/TSK-0125/`.
