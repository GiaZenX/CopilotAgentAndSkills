# TSK-0112 (Strom G) — Stromprotokoll

Dieses Item wurde im selben Arbeitsbaum und im selben Lauf wie `TSK-0113` abgearbeitet
(`C:/Offline Repos/v2-testbed/_worktrees/g2-office`, Branch `g2/office`, Basis `6d18407`).
Arbeitsverzeichnis: `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0112/`.

**Das vollständige Protokoll steht in `project_memory/staging/TSK-0113/stream-protocol.md`,
Abschnitt 10** — Schnitt, Spiegel, die Prozessmessung auf gescaffoldeten dev- und
research-Projekten, die vier roten Tests und die Nähte. Abschnitt 13 dort sagt, welche Datei des
Patches zu welchem Item gehört; Abschnitt 11 trägt die Läufe, Abschnitt 12 die Stempel.

Kurzfassung:

* `hooks/_routine.py`, byte-identisch in allen drei Kits (gleiche SHA-256, 9 714 Bytes), nach dem
  Vorbild von `_audit.py`. Es trägt den Laufdatensatz, die ISO-Wochenperiode, die Pflichtform und
  die Meldung.
* Office erreicht es durch `_duties.FEEDS`; dev und research rufen `_routine.notice(cwd)` direkt aus
  ihrem `session_status.py`, mit einer sichtbaren Ausfallzeile statt eines geschluckten Fehlers.
  Bewusste Abweichung vom Wortlaut des Items: das Office-`session_status.py` ruft `_routine` NICHT
  zusätzlich auf — sonst stünde derselbe Lauf zweimal im Briefing. Festgenagelt durch
  `tools/test_routine_feed.py::test_the_office_briefing_names_the_routine_exactly_once`.
* Gemessen als Prozess auf wirklich gescaffoldeten dev- und research-Projekten: die Meldung
  erscheint beim Sitzungsstart und verschwindet nach einem aufgezeichneten Auditor-Lauf, je Kit.
* Vier rote Messungen im Klon außerhalb des Repos, darunter beide Enden des Spiegel-Stolperdrahts
  für das neue Modul.
* Keine neue Lochnummer. `H111`/`H112` zeigen jetzt auf `_routine` statt `_duties`; ihre
  Testnennungen wurden auf `tools/test_routine_feed.py` nachgezogen.
* **Nacharbeit 2 (T112-1):** `test_a_missing_routine_module_is_a_line_in_the_briefing_rather_than_silence`
  maß nur das dev-Kit, während beide `session_status.py` je eine eigene Kopie des
  Ausfallzweigs tragen und beide auf den Test zeigen. Jetzt über die zwei direkten Aufrufer
  parametrisiert; rot gemessen mit entferntem Zweig in der research-Fassung
  (`[research-team]` failed, `[dev-team]` passed, Kontrolle 2 passed). Einzelheiten in
  `TSK-0113`, Abschnitt 10a.
* Stempel provisorisch, drei Läufe: `dev-team` und `research-team` stehen auf
  `2026.09.02-12` — von Nacharbeit 2 **nicht** berührt, mit `bump_kit_version.py` als
  `unchanged` geprüft —, `office-team` auf `2026.09.02-16`.
