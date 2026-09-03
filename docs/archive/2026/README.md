# docs/archive/2026 — was hierher verschoben wurde, und warum

Diese Ablage ist das Ergebnis von `FR-0036` (Nutzerwunsch 2026-08-16: „MD-Dateien müllen das Repo
zu"). Nichts wird hier gelöscht — verschoben wird nur Prosa, die **nichts mehr liest**.

Was „liest" heißt, ist nicht dieser Text, sondern der laufende Leser: `tools/test_repo_hygiene.py`,
`_wire_class` und `_wires_over`. Fünf Arten von Verweis kennt er — **Code** unter `tools/` oder
`.claude/hooks/`, der den Namen nennt (ein Test ist davon nur ein Fall: auf diesem Baum verdanken
zwei Prüfprotokolle ihre Code-Klasse gar keinem Test, sondern `_harness.py`, dem gemeinsamen Rumpf
der Gates), die Löcherliste, der
kanonische Zustand (ein Evidence-`artifact_ref` oder das `source:` eines lebenden Items, auch einer
aktiven Entscheidung), eine ausgelieferte Kit-Datei, und sonstige Prosa. **Jede** davon hält eine
Datei aus dem Hinweis heraus, Prosa eingeschlossen; ein archivierter Vorgang zählt ausdrücklich
nicht — und genauso wenig ein Verweis aus einem Archiv heraus, auch aus dieser Datei hier
(`_is_a_record`); sonst hielte der Index seinen eigenen Gegenstand am Leben und nie wäre etwas
archivierbar. Ein Verzeichnis, das laufender Code betritt, zählt für alles darunter; das misst
`_joined_literals`. Und was er überhaupt sehen kann, ist das, was **git trägt** — eine Nennung in
einer ignorierten Datei sieht er nicht.

Der Melder derselben Datei nennt Kandidaten, er verschiebt nichts. Das Urteil je Datei fällt eine
Runde, und im Zweifel bleibt die Datei stehen.

**Format der Tabelle, und wer es prüft:** Spalte 2 nennt die Datei in Backticks, relativ zu diesem
Verzeichnis. Dass jede Datei unter `docs/archive/2026/` hier eine Zeile hat **und** jede Zeile eine
Datei nennt, **die das Repo trägt** (git, nicht die Platte — eine Löschung fällt auf, sobald sie
gestaged ist), misst `test_every_archived_file_is_named_by_the_index_above_it`;
dass kein Beweisverweis durch einen Umzug ins Leere zeigt, misst
`test_every_artifact_ref_still_resolves_where_it_points`. Beide stehen in
`tools/test_repo_hygiene.py`. Der übergeordnete Index ist `docs/archive/README.md`.

| verschoben am | Datei | Grund |
|---|---|---|
| 2026-09-02 | `pilot/2026-08-09-drehbuecher.md` (aus `docs/pilot/`) | Kein Verweis im ganzen Baum: kein Code, kein Löcherlisten-Eintrag, kein `artifact_ref`, kein Item, keine Kit-Datei, und auch keine andere Prosa nennt Datei oder Pfad. Gemessen 2026-09-02 über den ganzen Arbeitsbaum (ohne `.git`) und den kanonischen Zustand des Hauptbaums. |

## Was in derselben Runde gemessen wurde und ausdrücklich NICHT verschoben ist

Damit niemand die Prüfung zweimal macht, und damit die Abwesenheit kein Versehen zu sein scheint:

- **`docs/research/2026-07-27-*` (zwölf Dateien).** Zwei unabhängige Gründe. Erstens liest
  `tools/test_repo_hygiene.py` das Verzeichnis `docs/research` als Ganzes
  (`test_every_research_role_report_is_named_after_the_role_its_own_text_is_about`); ein Umzug
  daraus nimmt diesem Test seinen Gegenstand. Zweitens hält die Löcherliste in Abschnitt 1 fest,
  dass diese Dateien **Belege** sind und ein `git mv` daran eine Entscheidung des Nutzers ist.
- **`docs/handback/`.** Eine offene Handlungsanweisung an den Nutzer, die `BUG-0012` und `BUG-0014`
  nennt — beide stehen weiter auf `TRIAGED`. Was daran heute nicht mehr stimmt, steht im
  Rundenprotokoll, nicht hier.
- **`docs/archive/staging-of-archived-items/`.** Liegt bereits im Archiv. Ein zweiter Umzug
  innerhalb des Archivs ändert nichts und bricht die Verweise, die archivierte Items auf diese
  Dateien führen.
