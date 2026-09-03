# Prompt für die nächste Session

Kopiere den Block unten als erste Nachricht in die neue Session. Er zeigt nur; die Autorität ist der
Zustand auf der Platte.

---

Weiter nach Generation 2. Stand: Der Merge der sieben Ströme (TSK-0114) ist geprüft und committet
(Commit `dc930cc` auf `feat/harness-v2`, Beweismittel EVD-0077; Kits dev/office `2026.09.02-12`,
research `2026.09.02-11`; NICHT gepusht — Push nur auf Wort des Nutzers). Lies in dieser Reihenfolge,
bevor du etwas tust:

1. `project_memory/staging/generation-2-streams.md` — das Rundenlogbuch; die letzten Einträge tragen
   das Merge-Urteil, die Nahttabelle und die (g)-Tabelle für DEC-0060.
2. `project_memory/decisions/active/DEC-0062.yaml` — Ströme werden nach DATEIBESITZ geschnitten,
   Wünsche mit überlappenden Dateien in EINEN Strom gebündelt, ein Strom gedeckelt durch eine Runde
   Aufmerksamkeit; Nähte vorab benannt.
3. `project_memory/inbox/active/FR-0084.yaml` — Rückschau als Ereignis (Phasenende, Merge, wiederholte
   Befundklasse, veränderte Entscheidungsgrundlage), vier Messfragen, drei Zeilen an den Nutzer; plus
   „jeder Auftragsplan nennt den verworfenen Weg".
4. `project_memory/generated/session_brief.yaml` und `generated/index.yaml` — der Zustand.

Was zuerst ansteht (die Entscheidung des Nutzers steht noch aus — FRAGE ihn mit dieser Liste, bevor du
schneidest):

- **Generation 3, Vorschlag fünf Ströme nach DEC-0062:**
  - A Board & Plan = FR-0075 + FR-0079 + FR-0080 (Design-Pass zuerst, Fable; Bau Opus) — Besitz:
    dev-team `templates/repo/scripts/generate_dashboard.py` + Template, `kernel/board.py`,
    `kernel/backlog_tree.py`; Meilenstein-Typ (MST) als Naht an C oder per Design-Entscheidung „Feld".
  - B Büro-Finanzen = FR-0076 (FR-0081 bewusst später) + die Büro-Nähte aus Generation 2
    (`founding_year` + Interviewfrage zum Steuerstatus, `kleinunternehmer: null` als Auslieferung, Kernel
    prüft `retention` nicht = F6) — Besitz: `office-team/templates/project_memory/**`,
    `templates/repo/scripts/euer_report.py`, EÜR-Reiter in `templates/repo/tools/finance_dashboard.py`.
  - C Freigaben & Beweismittel = FR-0074 + FR-0082 + FR-0083 + BUG-0089 — Besitz: `kernel/approvals.py`,
    `documents.py`, `state.py`, `backlog_types.py`, `cli.py`; Verfassungssätze als Naht.
  - D Parallele Spezialisten = FR-0021 (+ FR-0084 Rückschau, falls der Nutzer sie hier will) — Besitz:
    dev-team Verfassung, `skills/project-manager/**`, ein Verfahrens-Skill; Leases/Dispatch als Naht an C.
  - E Design-Gates = FR-0077 + FR-0078 — Besitz: dev-team `hooks/**`, `skills/frontend-design/**`,
    `skills/product-designer/**`, `tools/test_*` dazu.
  - Nähte, vorab zu benennen: Löcherliste (H125 ist vergeben — Lösch-Verben außerhalb des Tupels
    `DELETE_VERBS`, offen, Bau in B; Nummern je Strom reservieren: A H126–128, B H129–131,
    C H132–134, D H135–137, E H138–140), drei Verfassungen (nur D und C liefern Sätze; D schreibt sie,
    C meldet; D fixt auch die `description`-Zeile der drei `project-auditor.md` gegen ihren Rumpfsatz —
    Rest N2 der Merge-Prüfung), `tools/test_hooks.py` (Spiegel-Tests, A und B), `backlog_types.py`
    (nur C). Strom B nimmt H125 mit: `DELETE_VERBS` durch eine Eigenschaft ersetzen (`unlink`,
    `git clean -fdx`, `Clear-Content` liefen an allen acht Office-Haken vorbei; DEC-0056-Ausnahme
    für Unumkehrbares).
  - Stufen (DEC-0059): Umsetzer Opus als Boden, Prüfer Opus, Fable nur für den Design-Pass in A.
- **Generation 4 danach:** FR-0072-Nachrunde (wartet auf das Geschmacksurteil des Nutzers zu den drei
  Fassungen in `staging/TSK-0111/research-existing-humanizers.md` §4), FR-0057 (Kit-Hooks ohne
  `timeout`), BUG-0088, Beweismittel-Pfade normalisieren (F5), BUG-0077…0087 nach Sichtung, FR-0081,
  die spätere Liste des Nutzers (FR-0024, 0022, 0023, 0025, 0019, 0033, 0005, 0010, 0004, 0043).

Regeln, die diese Generation gemessen hat und die im nächsten Auftrag stehen müssen: jede neue
Eigenschaftsbehauptung wird gemessen, bevor sie steht (der häufigste Befund aller Ströme); Kopien von
Worktrees OHNE die `.git`-Datei; Scratch nur unter `_round-scratch/<TSK>/`; volle Suite einmal im Merge;
ein Stempel im Merge; Testnamen in der Löcherliste mit Präfix; `forbidden_scope: project_memory/**`
nimmt `staging/<id>/` aus (im Item sagen).

Abgeschlossen im Zustand: TSK-0105–0114 CANCELLED (= über dc930cc geliefert) und archiviert; die
gelieferten FRs MERGED und archiviert; `DEC-0063` = Urteil der Generation 2 (Parallelität behalten,
Merge-Runde ist eigene Prüfung, Deckel 4–5 Ströme, Stufen-Lesart, DEC-0050-Lesart); `DEC-0062`
Schnittregel; `FR-0084` Rückschau; H122–H125 offen mit Ketten.

Offen beim Nutzer, ohne Eile: Geschmacksurteil Humanizer-Paar (drei Fassungen); Push der Generation 2
(ja/nein); Antwort auf die Fünf-Ströme-Frage; vier Ein-Klick-Freigaben für BUG-0083–0086 (in dc930cc
behoben und geprüft; der Kernel lässt TRIAGED → APPROVED nur auf eine vom Nutzer geprägte Freigabe zu —
`request-approval scope BUG-00xx` stellt die Frage; für BUG-0083 ist sie schon gestellt).
