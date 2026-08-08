# Prüfverdikt TSK-0022, Runde 3 (2026-08-08) — FAIL, Schwere weiter gefallen

## Bestätigt (unabhängig gemessen)

- **Kern-Fix unangetastet und intakt**: 12 Schreibweisen, echte `bash` als Schiedsrichter,
  Stellvertreterprojekt außerhalb `~` — `holes: none`.
- **F1 vollständig reproduziert**, beide Lagen: `x=~+/…` rc 0 außerhalb `~` / rc 2 darunter;
  `~\+/…` ebenso. Mechanismus stimmt gegen den laufenden Code (`_harness.py:916`,
  `_PATHISH = [A-Za-z0-9_.\-/\\:~]+` trägt weder `=` noch `+`).
- **Die Achse `_tilde_leads` deckt die Klasse**, nicht nur das Alphabet — `x` (von `_PATHISH`
  getragen) und `=` (nicht getragen) liegen auf verschiedenen Seiten der Frage; `x=` fügt gegenüber
  `=` nichts hinzu. Roter Test reproduziert: genau elf Vorläufe, unabhängig nachgerechnet.
- **Wachliste total, beide Richtungen**: 445 = 445, „protected but NOT watched: 0",
  „watched but NOT protected: 0". Der zunächst vermutete Widerspruch 457/445 ist keiner —
  Befund vom Prüfer zurückgezogen.
- **H38-Test ist ein echter Stolperdraht**: Heredoc-Entfernung raus → 2 failed. H38s Mechanismus
  stimmt gegen `gate_write_scope._HEREDOC_RX` wie es im Kit steht.
- `_removed` räumt wirklich auf (kein `C:\harness-gates-*` überlebt);
  `_base_outside_the_home_directory` fällt nicht still zurück, sondern wirft.
- **Suite 143 grün** (1181 s im eigenen Klon), Spiegelauswahl 25 grün.
- **Messdisziplin: 445 Dateien vor/nach jedem Lauf gehasht, durchgehend unverändert. Kein vierter
  Schaden.** Basisordner des Prüfers gelöscht, nichts überlebt.
- **Frage (g) beantwortet:** der `.audit`-Schreibzugriff ist **kein Scope-Verstoß des Pakets** —
  er kommt aus einem Kit-Hook-Unterprozess über `find_repo_root()`, nicht aus einem Werkzeugaufruf;
  Gate 1 sieht ihn nie. Defekt der Kits, den das Item nicht verbieten konnte.

## Blockierend

- **B1** (`_sandbox.py:38-45`, `:65-72`, `:76-83`; H37:2142; Protokoll:458): `pin()` setzt `HOME`
  und `CDPATH` nicht, beide erbt eine Kind-Shell und beide steuern Wort-Erweiterung. Gemessen:
  `~/…` schreibt den Köder (rc 0), `cd decoy && sed -i … team-kits/kernel/state.py` schreibt ihn
  über `CDPATH` (rc 0); `~+` zeigt korrekt in die Sandbox (rc 2). `DIRSTACK` dagegen ist Theater —
  keine Shell liest es aus der Umgebung. Der als Stolperdraht benannte Test misst **nur** `OLDPWD`:
  Mutation „PWD nicht mehr gesetzt" → grün. **Keine Angriffskette ins echte Repo an diesem Tag**
  (`HOME` = `C:\Users\zenti`, Repo unter `C:\Offline Repos`; `CDPATH` ungesetzt) — blockierend ist
  die **Behauptung** „setzt jede Verzeichnisangabe", nicht die Kette. Minimalfix: zwei Zeilen
  (`out["HOME"] = here`, `out.pop("CDPATH", None)`) — billiger richtig gebaut als richtig
  beschrieben.
- **B2** (`docs/POST_V2_WISHLIST.md:2160-2174`, Zahl auf `:2166-2167`): H37 Rest 2 nennt 43
  Ereignisse; der Baum trägt 46 — **diese Runde hat die Kette am eigenen Abnahmelauf ausgelöst**.
  Das Protokoll sagt es ehrlich (`:594-601`), die Löcherliste nicht; sie liest sich als Altbestand.
  Minimalfix: Zählung durch Eigenschaft ersetzen, den Satz aus Protokoll-Abschnitt 14 dorthin.

## Benannte Reste (Löcherliste, blockieren nicht)

- **R1** (`_sandbox.py:149-176`): `watch` friert die Pfadliste beim Betreten ein und vergleicht nur
  Digests — eine im geschützten Baum **angelegte** Datei ist unsichtbar. Gemessen: ein
  handgeschriebenes `EVD-9999.yaml` unter `project_memory/evidence/active/` passierte still,
  während die Kontrolle (Änderung an `state.py`) korrekt anschlug. Genau die Schreibklasse, mit der
  `ProtectedArea` begründet, warum `project_memory/` jedem verweigert wird. Fix: Mengen vergleichen,
  nicht nur Digests.
- **R2** (`_sandbox.py:56-63`, `:86-88`, `:190`): „Sandbox im Repo wird verweigert" ist ein
  Pfadvergleich über `realpath`, der die Win32-Device-/UNC-Namensräume nicht kanonisiert.
  Groß-/Kleinschreibung, 8.3-Kurznamen und `..` greifen; `\\?\C:\…`, `\\localhost\C$\…` und
  `\\?\C:\…\SANDBO~1` werden **akzeptiert**. Kette innerhalb der Vorrichtung: so buchstabiert wird
  gepinnt, und `restore_from_index` prüft gegen dieselbe Funktion. Fix: jeden Pfad verweigern, für
  den `os.path.splitdrive` keinen schlichten Laufwerksbuchstaben liefert.
- **R3** (`test_gates.py:2878-2904`): der Syntaxbaum-Test sieht nur `modul._X_RX.sub(...)`. Eine
  dritte Entfernung über einen lokalen Namen → Test bleibt grün. Ebenso unsichtbar: eine Entfernung
  in einer gerufenen Hilfsfunktion, und jeder Name ohne `_RX`-Endung. H38 stützt sich auf diesen
  Test. Fix: die **Laufzeit** messen (zählende Stellvertreter für jedes `*_RX` des Kit-Moduls).

## Ungemessen

`pytest tools/` vollständig (bewusst nicht — der Lauf schreibt erneut nach `.audit`); ruff;
`validate.py`; PowerShell-Hälfte (Runde 1 bestätigt, Leser unverändert); der dritte Kandidat von
`_base_outside_the_home_directory`; Laufzeit gegen das Budget (Leser unverändert); Byte-Identität
Klon ↔ Arbeitsbaum; H22, H34, H35, H36.
