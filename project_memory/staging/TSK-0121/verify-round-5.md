# TSK-0121 (PR-0004, G4-1) — Prüfbericht Runde 5 (nur N1) und Schlussurteil

Rolle: `harness-verifier`. Read-only im Repo. Gemessen in einer **frischen** Kopie ohne `.git`
(`…/verify/wt5`) unter `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0121/verify/`.
Abschluss: `rig/integrity2.py` → *differing: NONE / missing: NONE (0)*.

## N1 — **PASS**

Der Befund aus Runde 4 war: der Test, der die tragende Zusage der F10-Verengung absichert, legte
seine Junction wegen `prd_repo is tmp_path` **innerhalb** des Projekts an und blieb darum grün,
während dieselbe Mutation die echte Kit-Hälfte aufriss.

**Die entscheidende Messung — meine Runde-4-Mutation gegen den neuen Test:**

```
$ python -B rig/r5_mut.py kit-outside-first        # `if placeable(here): return False, None`
                                                   # VOR `if under(target, here)`
$ python -B -m pytest tools/test_hooks.py -k "still_sees_a_link_from_outside or lies_outside_the_project"
FAILED tools/test_hooks.py::test_gate_test_scope_still_sees_a_link_from_outside_into_the_declared_surface
E  AssertionError: a junction from outside INTO the surface was allowed
E  assert 0 == 2   (returncode=0 aus …/wt5/team-kits/dev-team/hooks/gate_test_scope.py)
1 failed, 1 passed
```

In Runde 4 war genau dieser Lauf **2 passed**. Der Wächter greift jetzt.

**Der Repo-Zwilling ebenfalls rot** unter derselben Änderung:
```
$ python -B rig/r5_mut.py repo-outside-first
FAILED .claude/hooks/test_gates.py::test_gate5_still_sees_a_link_from_outside_into_the_declared_surface
E  assert 0 == 2
```

**Der Helfer landet wirklich draussen** — Pfade gedruckt und die Nicht-Enthaltung nachgerechnet
(`rig/r5_paths.py`, `_provably_outside` direkt aufgerufen):
```
project : …\verify\r5-e__453gz\test_something0
outside : …\verify\r5-e__453gz\elsewhere              -> inside? False
project : …\verify\r5-e__453gz\test_something0
outside : …\verify\r5-e__453gz\outside-the-project    -> inside? False
```
`os.path.commonpath` ist der reale Projektpfad **nicht**, also ist die Zusicherung im Helfer
(`tools/test_hooks.py:18383-18399`) eine echte und keine Formsache; sie wird bei jedem Aufruf
gefahren und schlägt zu, wenn jemand den Ort wieder nach innen legt.

**Der Rig-ausserhalb-Test hängt nicht mehr an seinem vierten Fall.** Mit abgeschalteter Verengung
scheitert er auf dem **ersten** Ziel, und das ist der wirklich aussenliegende Ort:
```
$ python -B rig/r5_mut.py kit-no-narrowing
FAILED tools/test_hooks.py::test_gate_test_scope_lets_a_rig_run_a_suite_that_lies_outside_the_project
E  AssertionError: a run outside the project was refused
   ('C:\…\pytest-of-zenti\pytest-10650\elsewhere\suite')      ← Fall 1, nicht `tests/../../tests`
```
(Projekt ist `…\pytest-10650\test_gate_test_scope_lets_a_r0`, das Ziel liegt daneben.)

**Die neutralisierende Variante bleibt grün — und ist zu Recht als unbrauchbar protokolliert:**
```
$ python -B rig/r5_mut.py kit-outside-first-neutralised   # … and not under(here, project_root)
1 passed
```
`under(here, project_root)` löst die Junction selbst auf und hebt damit den gepflanzten Defekt
wieder auf; die Mutation misst nichts. Das ist genau der Fehlgriff, den ich in Runde 4 selbst
gemacht habe und der mich N1 fast hätte übersehen lassen — dass er im Protokoll als unbrauchbar
steht, ist die richtige Buchführung.

**Ungemutiert grün:** `tools/test_hooks.py -k "test_scope or reader_and_the_workshops or
lies_outside or link_from_outside"` → **39 passed** (34 s);
`.claude/hooks/test_gates.py -k "gate5 or …"` → **51 passed** (61 s).

## Paket

* **Patch:** 336 024 B, **24 Dateien**, `git apply --check` **rc 0** und `--3way` rc 0 gegen einen
  aus 75a00d1 materialisierten Baum, 5101 +/15 −, **0 CR-Bytes**, **0 VERSION-Hunks**.
* **Spiegel unverändert** gegenüber Runde 4 — also hat diese Runde wirklich nur Testcode angefasst:
  `gate_test_scope.py` sha256 `8e5c8dff65a6afd8…` ×3, `_kernel.py` `13e47244d9aa2eea…` ×3.
* **Stempel:** dev/office/research je `2026.09.05-5`. Protokoll 834 Zeilen.

---

# Schlussurteil TSK-0121

**PASS.** Nach fünf Runden ist jeder Befund geschlossen und von mir gegen den laufenden Code
nachgemessen; kein blockierender Rest, keine unaufgeschriebene gemessene Lücke.

**Je Kriterium:** AC-1 **PASS** — der Volllauf ist als *Eigenschaft* gebaut und hält gegen alles,
was fünf Runden gefunden haben: die Läufer-Erkennung über den Verb-/`-m`-Rand, die Optionslesung
auf dem **Wert** und der **letzten** Angabe, und der Ort als **Identität** (`_harness.under`), nicht
als Text — Junction, Gross-/Kleinschreibung, laufwerksrelativ, `\\?\`, Bezugsbasis und doppelte
Option sind zu, in beiden Hälften, während Auswahl, Junction auf ein Unterverzeichnis und
`-k "" -k alpha` durchgehen. AC-2 **PASS** unter der Lesart des Leads: der Fristenleser leitet aus
dem gemessenen Vorgabefenster ab, verweigert ein Fenster, das er nicht halten kann, und der
Wachhund steht ausserhalb der Entscheidung; die QS-Prozedur ist gehoben und ausgeführt. AC-3
**PASS** — C1/C2/C3 laufen mit echtem Chromium gegen die wirklich bediente `frontend/dist`, sechs
Verletzungen je auf ihrer Regel rot, Spiegel byte-gleich. AC-4 **PASS** — Kosten selbst gemessen
(0,12–0,26 s gewöhnlich, 2,86 s der eine teure Fall einer toten UNC-Freigabe, gegen registrierte
120 s), Schwelle als Datenwert wirksam, Projekt ohne UI zahlt nichts. Pflichten 5–7 **PASS**:
rot-zuerst je Zweig (ich habe über die Runden 16 eigene Mutationen gefahren), jede
Eigenschaftsbehauptung gegen den Code geprüft, H151–H153 im aktuellen Format mit Mechanismus,
gemessener Kette und Urteil, Naht an G4-3 wörtlich mit zwei wirklich roten Tests, Patch sauber.

**Was diese fünf Runden ausmacht**, und es gehört ins Protokoll der Runde: jede Nacharbeit hat den
Befund nicht geflickt, sondern die Frage dahinter neu gestellt — die Aufzählung wurde ein
Stolperdraht, der den **Läufer** fragt; der Pfadvergleich wurde der Identitätsleser, den dieses
Repo seit TSK-0008 schon besass, statt eines zweiten Normierers; die Über-Verweigerung wurde eine
Eigenschaft („der tiefste **existierende** Vorfahr, und eine Dateisystem-Wurzel zählt nicht"), statt
eine Ausnahmeliste zu bekommen. Und der letzte Befund war kein Codefehler, sondern ein Wächter, der
nicht scheitern konnte — die teurere der beiden Defektarten, hier gefunden, bewiesen und behoben.

**Offen bleibt, benannt und begrenzt:** H151 (die Erklärung liegt ausserhalb des geschützten
Bereichs — Insider, nicht Irrtum), H152 (eine erklärte Option mit wohlgeformtem Wert, der nichts
trifft — braucht eine Sammlung, also genau die Kosten des Gates), H153 (ein Läufername, den erst
die Shell herstellt, plus der nicht platzierbare Ort). Alle drei mit gemessener Kette und Urteil.

**Nicht gemessen (unverändert offen benannt):** die volle Suite — sie ist Lieferkriterium des
Merges (DEC-0050) und gehört ausdrücklich nicht in die Prüfung; office- und research-Piloten (nur
dev gebaut, die drei Gates und `_kernel.py` sind byte-gleich); `.codex/hooks.json`; ein archiviertes
`EVD` gegen den zweiten Volllauf; ein zweites offenes Item als Präfix; der PowerShell-Zweig der
QS-Rollenzeile; ein case-sensitives Dateisystem; Laufzeit unter echter Parallel-Last (BUG-0033);
ein UNC-Host, der gar nicht antwortet.

**Empfehlung an den Lead:** abnehmen und stempeln. Vor Commit fehlt nur, was ohnehin dem Merge
gehört — der volle Lauf als Lieferkriterium und `python tools/bump_kit_version.py` auf den
endgültigen Stempel.
