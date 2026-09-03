# TSK-0107 (Strom G, Office) — Nahtstellen an andere Ströme

Jede Zeile ist gemessen, nicht gelesen. Kein Punkt hier wurde von diesem Strom geändert; die
Dateien gehören anderen Strömen.

## An Strom E (Rollentexte, Skills, Verfassungen)

**E1 — `team-kits/office-team/agents/shop-curator.md` bindet die Rolle an eine Plattform (FR-0028).**
Die Routing-`description` endet mit „…, audit, Shopify.". Eine `description` ist das, woran die
Plattform eine Anfrage misst; damit ist die Shop-Rolle für den Router die SHOPIFY-Rolle. Gemessen:
`tools/test_kit_neutrality.py` liest 59 Rollentexte (Verfassungen, geparste Agent-Frontmatter,
Skills) und findet **genau diese eine** Stelle. Sie steht dort in `KNOWN_BINDINGS` mit Grund und
Eigentümer; wird das Wort entfernt, meldet derselbe Test, dass der Eintrag zu löschen ist (beide
Richtungen rot gemessen, M11/M12).

**E2 — Der Löschquarantäne-Knoten im `records-clerk`-Skill ist für ein archiviertes Dokument
unerreichbar (FR-0002 F5).** `team-kits/office-team/skills/records-clerk/SKILL.md:82` nennt
`0-Inbox/Prüfen/Löschen/`. Gemessen gegen den ausgelieferten `guard_fs_tripwire` in einem
Wegwerf-Projekt außerhalb des Repos:

```
mv archive/finance/old.pdf "0-Inbox/Pruefen/Loeschen/old.pdf"   rc 2  VERWEIGERT ("out of archive")
mv archive/finance/old.pdf "inbox/Pruefen/Loeschen/old.pdf"     rc 2  VERWEIGERT (dieselbe Regel)
mv archive/finance/old.pdf archive/_quarantine/2026/old.pdf     rc 0  DURCHGELASSEN
rm archive/finance/old.pdf                                      rc 2  VERWEIGERT
```

Dazu: `0-Inbox` ist gar keine Ablage dieses Kits — `hooks/document_trays.txt` führt `archive`,
`inbox`, `outbox`. Die Vorlage `filing_plan.yaml` trägt seit dieser Runde die Definition und die
zwei Beispielregeln (`archive/_unsorted/`, `archive/_quarantine/`); der Skill-Satz muss darauf
zeigen, sonst schickt er den Clerk in eine Verweigerung.

**E3 — Der Audit-Takt steht ab jetzt an zwei Stellen.** `_duties.audit_period_id` legt ihn als
ISO-Woche fest (mit `FR-0038` daneben); die drei Verfassungen und die drei `project-auditor`-Texte
sagen weiterhin „läuft wöchentlich oder ereignisgetrieben". Der Verfassungssatz sollte auf die
Code-Stelle zeigen statt die Zahl ein zweites Mal zu schreiben. Im selben Satz steht die Behauptung,
der Dispatch reite auf einer `APR.kind: routine` oder `analysis` — die es laut Messung nicht anlegen
lässt (`H111`); entweder sagt der Satz das, oder Strom F baut den Weg.

**E4 — Kein Rollentext kennt das Fristenregister.** Die Sitzungsstart-Meldung sagt dem Manager,
dass das Register VORSCHLÄGT und nichts tut; kein Text des `office-manager` sagt, was er damit tun
soll (in den ersten Absatz an den Nutzer, Entscheidung beim Nutzer). Dieser Strom durfte die
Rollentexte nicht anfassen und hat es nicht getan.

## An Strom F (Kernel)

**F1 — `generated/session_brief.yaml` trägt keine Fristen.** FR-0034 nennt den Sitzungs-Brief als
den natürlichen Träger. Geliefert ist die Office-Seite: `_duties.register()` gibt die Fristen als
`{what, due, source}` zurück, `_duties.briefing()` den Absatz, den der SessionStart-Hook injiziert.
Für den Brief selbst braucht es `kernel/report.generate_session_brief` plus einen Abschnitt im
Schema `kernel/schemas/session_brief.yaml` — beides Strom F.

**F2 — `routine`- und `analysis`-Freigaben haben keinen Erzeuger** (`H111`, gemessen:
`approvals.item_derived_kinds()` = scope/delivery/acceptance; `request-approval` bietet neun Arten
an, keine der beiden). Solange das so ist, NENNT das Register Rolle und Takt der Auditor-Routine im
Code. `tools/test_office_duties.py::test_no_routine_approval_can_be_minted_in_this_kit_today` wird
rot, sobald ein Weg dazukommt — dann gehört die Ableitung an die Freigabe.

**F3 — `dispatch.last_completed` / `next_due` haben weiterhin keinen Erzeuger** (der Ursprungsbefund
von FR-0038). Dieser Strom leitet den Lauf stattdessen aus dem Ereignis-Log ab (`H112` trägt die
zwei Grenzen). Bekommt der Kernel einen Erzeuger, sollte `_duties.last_run` ihn lesen.

**F4 — Es gibt kein „erledigt"** (`H113`): kein Datensatz hält fest, dass eine Voranmeldung
abgegeben oder ein Aufbewahrungsjahr geprüft wurde. Das ist kanonischer Zustand und eine offene
Entscheidung über die FORM, keine Implementierungsfrage.

## An Strom I (Dashboard)

**I1 — Das Finanz-Dashboard kann die Fristen zeigen, ohne sie zweimal abzuleiten.**
`_duties.register(root, today)` ist der eine Leser und gibt Liste + Unlesbares zurück; FR-0034 nennt
diese Anzeige ausdrücklich als optional. Nicht gebaut hier — `dashboards/` gehört Strom I.
