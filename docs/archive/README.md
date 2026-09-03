# docs/archive — was hier liegt, und warum es hier liegt

Diese Ablage nimmt Prosa auf, die **nichts mehr liest**. Gelöscht wird nichts; verschoben wird nur,
was gemessen keinen Draht mehr hat. Wer und was „liest" heißt, entscheidet nicht dieser Text,
sondern der laufende Leser in `tools/test_repo_hygiene.py` (`_wire_class`, `_wires_over`).

**Jede Datei unter `docs/archive/` steht in genau einem Index** — in diesem hier oder in dem des
Jahresordners über ihr (`docs/archive/<jahr>/README.md`), je nachdem, welcher näher liegt. Dass das
für jede Datei gilt **und** dass jede Zeile eine Datei nennt, **die das Repo trägt** (git, nicht
die Platte — eine Löschung fällt auf, sobald sie gestaged ist), misst
`test_every_archived_file_is_named_by_the_index_above_it`; ein neuer Ordner ohne eigenen Index
lässt diesen Test rot werden, statt still zu bleiben.

**Format:** Spalte 2 nennt die Datei in Backticks, relativ zu dem Verzeichnis, in dem der Index
liegt. Was sonst in der Zeile steht, liest der Test nicht.

| verschoben am | Datei | Grund |
|---|---|---|
| 2026-08-13 | `staging-of-archived-items/TSK-0018/wishlist-entries.md` | Staging-Prosa eines archivierten Vorgangs. Die Abschlussrunde `TSK-0055` (Commit `4e95930`) hat TSK-0018 archiviert und seine Staging-Ablage hierher gelegt — aufbewahrt, nicht gelöscht. |
| 2026-08-13 | `staging-of-archived-items/TSK-0020/wishlist-entry-L19.md` | Wie oben, für TSK-0020. |
| 2026-08-13 | `staging-of-archived-items/TSK-0021/verdict-2026-08-07.md` | Wie oben, für TSK-0021. |
| 2026-08-13 | `staging-of-archived-items/TSK-0029/ergebnis-2026-08-10.md` | Wie oben, für TSK-0029. |

## Der Fall, der die Regel gekauft hat

In derselben Runde zog die Staging-Ablage von **TSK-0022** mit hierher — und musste zurück: drei
Evidence-Datensätze führen ihre `artifact_refs` in dieses Verzeichnis, und ein EVD ist
unveränderlich. Der Hergang steht in `docs/reviews/2026-08-13-tsk0055-closure-round.md`. Deshalb
prüft `test_every_artifact_ref_still_resolves_where_it_points` bei jedem Lauf, dass kein
`artifact_ref` ins Leere zeigt. Diesen einen Fall hat die Runde 2026-09-02 selbst nachgemessen;
`FR-0036` hält einen zweiten fest, den sie nicht nachgemessen hat.

Vier Dateien lagen ab 2026-08-13 drei Wochen lang ohne jeden Eintrag in dieser Ablage; ihr Grund
musste 2026-09-02 aus einem Prüfprotokoll zurückgeholt werden. Genau das ist das Ende der
Aufzählung, das der Test oben mitmisst.
