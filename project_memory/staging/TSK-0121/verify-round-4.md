# TSK-0121 (PR-0004, G4-1) — Prüfbericht Runde 4 (nur F10 und F11)

Rolle: `harness-verifier`. Read-only im Repo. Gemessen in einer **frischen** Kopie ohne `.git`
(`…/verify/wt4`) und auf einem **frisch gebauten** dev-Piloten (`…/verify/pilot4`), beides unter
`C:/Offline Repos/v2-testbed/_round-scratch/TSK-0121/verify/`. Abschluss: `rig/integrity2.py`
→ *differing: NONE / missing: NONE (0)*. Alles ausser F10/F11 steht aus Runde 3.

| Punkt | Urteil |
|---|---|
| **F11** (Docstring-Behauptung) | **PASS** |
| **F10** — Verhalten der Verengung (Repo- und Kit-Hälfte) | **PASS** |
| **F10** — der Test, auf dem die Verengung ruht (**Kit-Hälfte**) | **FAIL — N1** |
| Paket-Hygiene, Spiegel, Stempel, Läufe | **PASS** |

**Gesamturteil: FAIL, nicht blockierend, ein Befund (N1) — und er betrifft nicht den Code, sondern
seinen Wächter.** Der gebaute Code ist in beiden Hälften richtig; der Test, der die tragende
Behauptung der Verengung absichern soll, kann in der Kit-Hälfte nicht scheitern.

---

## N1 — Der Test, auf dem die F10-Verengung ruht, kann in der Kit-Hälfte nicht scheitern

`tools/test_hooks.py:18396` `test_gate_test_scope_still_sees_a_link_from_outside_into_the_declared_surface`

Die Verengung („ein Ort, den der Leser finden kann und der nicht dieses Projekt ist, ist eine
Auswahl") öffnet genau dann eine Tür, wenn ein Wort **von aussen** die Fläche doch erreichen kann —
eine Junction. Dass das nicht passiert, weil der Identitätsleser **vor** der Aussen-Frage antwortet,
ist die Behauptung, auf der die ganze Lead-Entscheidung ruht. Der Test dazu legt seine Junction
aber **innerhalb** des Projekts an:

```python
def prd_repo(tmp_path):        # tools/test_hooks.py:918-920
    capture_root_item(tmp_path)
    return tmp_path            # ← das Projekt IST tmp_path

link = str(tmp_path / "into-the-surface")     # :18402 — also INNERHALB des Projekts
```

Damit misst er „von aussen" nicht. Gemessen mit einer Mutation, die die Aussen-Frage **vor** den
Identitätsleser zieht (`rig/r4_mut2.py`, in beiden Hälften dieselbe Änderung):

```
KIT, echtes Hook-Prozess-Rig auf pilot4 (Junction WIRKLICH ausserhalb des Projekts):
  rc=0  junction (outside) -> the declared root      ALLOWED     ← die Tür ist offen
  rc=0  junction (outside) -> a SUBDIR of the root   ALLOWED

zugleich:
$ python -B -m pytest tools/test_hooks.py -k "still_sees_a_link_from_outside or lets_a_rig_run_a_suite"
2 passed, 1015 deselected in 11.35s                              ← der Test bleibt GRÜN
```

Die Repo-Hälfte ist richtig gebaut und geht unter derselben Mutation rot — sie legt den Link unter
`outside_the_home_directory`, also über dem Projekt (`.claude/hooks/test_gates.py:7317-7326`):

```
$ python -B rig/r4_mut2.py repo ; pytest .claude/hooks/test_gates.py -k "still_sees_a_link_from_outside"
FAILED …::test_gate5_still_sees_a_link_from_outside_into_the_declared_surface
E  AssertionError: a junction from outside INTO the declared surface was allowed  (assert 0 == 2)
```

**Der ausgelieferte Code ist richtig** — die unmutierte Kit-Hälfte antwortet auf dieselbe Junction
mit `rc=2 FULL-RUN` (unten gemessen). Der Defekt ist der Wächter: „ein benannter Test, der nicht
scheitern kann, ist der teurere der beiden Defekte", und dies ist der Test für genau die eine
Zusage, mit der die Verengung begründet wurde.

**Minimaler Fix:** den Link ausserhalb des Projekts anlegen — `tmp_path` ist das Projekt, also z. B.
`tmp_path.parent / "into-the-surface"` oder ein zweites `tmp_path_factory`-Verzeichnis; danach die
Mutation oben einmal fahren und rot sehen.

**Nebenbeobachtung, kein eigener Befund:** `test_gate_test_scope_lets_a_rig_run_a_suite_that_lies_outside_the_project`
(`:18383`) legt seine „Suite ausserhalb" aus demselben Grund ebenfalls **innerhalb** des Projekts
an (`tmp_path / "elsewhere" / "suite"`); gerettet wird der Test allein durch seinen vierten Fall
`tests/../../tests`, der wirklich eine Ebene höher landet — mit `kit-no-narrowing` mutiert wird er
darum rot (gemessen, 1 failed). Die drei Fälle, die sein Docstring meint, messen nichts.

*(Eigener Fehlschlag, offen gesagt: meine erste Mutation für diese Frage — die Aussen-Frage
**nach** dem `under(here, repo_root)`-Zweig einzuhängen — war wirkungslos, weil `_harness.under`
den Link ohnehin auflöst; sie liess beide Hälften grün und hätte mich fast N1 übersehen lassen.
Erst die zweite, textuelle Fassung trennt die beiden Leser wirklich.)*

---

## F10 — Verhalten: PASS (Repo- und Kit-Hälfte, echte Prozesse)

**Das Rig ausserhalb des Repos läuft wieder** — die Zeile, die `CLAUDE.md` für jeden roten Test
vorschreibt:

```
REPO   rc=0  scratch suite, whole directory        ALLOWED     (Runde 3: rc 2)
REPO   rc=0  scratch suite, ONE file               ALLOWED     (Runde 3: rc 2)
REPO   rc=0  scratch suite, node id                ALLOWED
REPO   rc=0  a sibling directory of the copy       ALLOWED
KIT    rc=0  scratch suite outside the project     ALLOWED
KIT    rc=0  one file of it                        ALLOWED
```

**Nicht platzierbar bleibt, was der Leser wirklich nicht ausrechnen kann** — jedes Mal mit dem
eigenen Satz, nie mit dem Volllauf-Satz:

```
REPO rc=2 /c/ git-bash spelling of THIS root     UNPLACEABLE     KIT rc=2 UNPLACEABLE
REPO rc=2 dead UNC share            (2,860 s)    UNPLACEABLE     KIT rc=2 (2,835 s) UNPLACEABLE
REPO rc=2 drive letter Q: (not mounted)          UNPLACEABLE     KIT rc=2 UNPLACEABLE
REPO rc=2 drive-relative C:tools                 UNPLACEABLE     KIT rc=2 UNPLACEABLE
REPO rc=2 no cwd in the payload, relative        UNPLACEABLE     KIT rc=2 UNPLACEABLE
REPO rc=2 no cwd in the payload, absolute        FULL-RUN        (richtig: ein absolutes Wort braucht kein cwd)
```

**Die Vorfahren-Regel gewinnt weiterhin gegen die Verengung** — das war meine Hauptsorge, weil ein
Ort ausserhalb des Repos das Repo **enthalten** kann. Die Reihenfolge in `_covers`
(`.claude/hooks/gate_test_scope.py:233-262`) stellt `under(target, here)` vor `_placeable`, und das
ist gemessen:

```
REPO rc=2 ..                    FULL-RUN     REPO rc=2 ../..              FULL-RUN
REPO rc=2 absolute parent       FULL-RUN     REPO rc=2 .                  FULL-RUN
REPO rc=2 tools/..              FULL-RUN     REPO rc=2 tools/../..        FULL-RUN
KIT  rc=2 ..                    FULL-RUN     KIT  rc=2 ../..              FULL-RUN     KIT rc=2 tests/..  FULL-RUN
```

**Die tragende Behauptung, am ungebrochenen Code:** eine Junction, die WIRKLICH ausserhalb liegt und
in die erklärte Fläche zeigt, ist rc 2 in beiden Hälften; auf ein **Unterverzeichnis** der Fläche
zeigend ist sie rc 0 (Auswahl, nicht über-verweigert):

```
REPO rc=2 junction (outside) -> tools            FULL-RUN
REPO rc=0 junction (outside) -> tools/eval       ALLOWED
REPO rc=0 junction (outside) -> tools/probes     ALLOWED
KIT  rc=2 junction (outside) -> the declared root  FULL-RUN
KIT  rc=0 junction (outside) -> a SUBDIR of the root  ALLOWED
```

**`tools/../../tools` ist jetzt eine Auswahl — und das ist richtig.** Von der Repo-Wurzel aus
bezeichnet es `<Grosselternverzeichnis>/tools`, einen anderen Ort; auf diesem Host existiert er
nicht einmal (gemessen: `does <grandparent>/tools exist? False`), also läuft ohnehin nichts. Der
Unterschied zur Vorfahren-Regel ist sauber getrennt: `tools/../..` (= das Elternverzeichnis, das
das Repo **enthält**) ist rc 2 FULL-RUN, `../../tools` (= ein anderes `tools`) ist rc 0. Beide
Hälften gleich (`tests/../../tests` rc 0 im Kit).

**Die erklärte Fläche selbst ist unberührt:** `tools/` rc 2, `TOOLS` rc 2 (Identitätsleser),
Auswahl im Root rc 0; im Kit `tests/` rc 2, `TESTS` rc 2, Auswahl rc 0.

**Kostenseite:** 0,12–0,24 s für alles Gewöhnliche gegen registrierte 120 s. Die eine teure Frage
ist die tote UNC-Freigabe mit **2,86 s** (Repo) / **2,84 s** (Kit) — sie läuft über
`_harness._identity` → `probe(os.stat, …)` (`.claude/hooks/_harness.py:322-328`), also unter der
Frist des Gates; ein Host, der gar nicht antwortet, wird damit zur Verweigerung und nicht zum Kill.

**Rot zuerst, vier eigene Mutationen** (nur in meiner Kopie, danach zurückgesetzt):

| Mutation | Knoten | Ergebnis |
|---|---|---|
| `_placeable`-Zweig aus (Verengung rückgängig) | `test_gate5_lets_a_rig_run_a_suite_that_lies_outside_this_repository` | **rot** („a rig run outside this repo was refused") |
| Dateisystem-Wurzel zählt als Ort | `test_gate5_says_so_when_it_cannot_place_a_target_at_all` + `test_gate5_keeps_refusing_only_what_it_really_cannot_place` | **2 rot** (`/c/…` wurde durchgewinkt) |
| Aussen-Frage vor den Identitätsleser (Repo) | `test_gate5_still_sees_a_link_from_outside_into_the_declared_surface` | **rot** |
| Aussen-Frage vor den Identitätsleser (Kit) | `test_gate_test_scope_still_sees_a_link_from_outside_into_the_declared_surface` | **GRÜN → N1** |
| `placeable`-Zweig aus (Kit) | `test_gate_test_scope_lets_a_rig_run_a_suite_that_lies_outside_the_project` | **rot** (über den vierten Fall) |

**H153** trägt die Restklasse mit gemessener Kette je Schreibweise und begründet die Verengung
ausdrücklich mit der `CLAUDE.md`-Zeile für das Rot-zuerst-Rig — die Aufschreibpflicht aus Runde 3
ist erfüllt.

---

## F11 — PASS

`team-kits/*/hooks/gate_test_scope.py:270-274` lautet jetzt:

> WHAT IT IS NOT is the workshop's version in full: `_harness` puts every filesystem question under
> its gate's deadline (`probe`). Here the bound is the watchdog in `_kernel.start_the_deadline` …
> (The tail is case-folded in BOTH — an earlier version of this sentence named that as a difference
> and it is not one.)

Gegen den Code geprüft: `os.path.normcase` steht in **beiden** Lesern an denselben zwei Stellen
(`.claude/hooks/_harness.py:366-367`, `team-kits/dev-team/hooks/gate_test_scope.py:284-285`), und
die eine genannte Differenz — der `probe`-Mantel — ist die einzige echte
(`_harness._resolved` = `probe(os.path.realpath, …)` gegen `os.path.realpath(os.path.abspath(…))`).
`grep -rn "case-folds"` über den ganzen Baum findet **drei** Treffer, alle drei in
`team-kits/*/hooks/_compat.py:1499` und über Options-**Namen**, nicht über Pfad-Enden — Altbestand,
nicht dieser Satz. Die falsche Teilaussage ist weg.

---

## Paket-Hygiene, Spiegel, Läufe

* **Patch:** 334 627 B, **24 Dateien**, `git apply --check` **rc 0** und `--3way` rc 0 gegen einen
  aus 75a00d1 materialisierten Baum, 5077 +/15 −, **0 CR-Bytes**, **0 VERSION-Hunks**.
* **Spiegel, nachgemessen:** `gate_test_scope.py` sha256 `8e5c8dff65a6afd8…` ×3,
  `_kernel.py` `13e47244d9aa2eea…` ×3 — beide genau wie berichtet.
* **Stempel:** dev/office/research je `2026.09.05-5`.
* **Läufe (nur lesende Suiten, einer nach dem anderen):**
  `.claude/hooks/test_gates.py -k "gate5 or …"` → **51 passed** (59 s);
  `tools/test_hooks.py -k "gate_test_scope or … or kit_reader_and_the_workshops"` → **57 passed**
  (45 s). Volle Suite **nicht** gefahren (DEC-0050 — Lieferkriterium des Merges).

## Nicht gemessen (offen benannt)

Volle Suite; AC-3 (Datei seit Runde 1 byte-identisch); office- und research-Piloten (nur dev; die
drei Gates sind byte-gleich); `.codex/hooks.json`; archiviertes `EVD` gegen den zweiten Volllauf;
zweites offenes Item als Präfix; PowerShell-Zweig der QS-Rollenzeile; Verhalten auf einem
case-sensitiven Dateisystem; Laufzeit unter echter Parallel-Last (BUG-0033); ein UNC-Host, der
gar nicht antwortet (gemessen ist nur einer, der schnell „nein" sagt: 2,86 s).

## Abschlussurteil

**FAIL mit einem einzigen, nicht blockierenden Befund.** F11 ist erledigt und gegen den Code
geprüft. F10 ist als **Eigenschaft** verengt statt als Ausnahmeliste — der tiefste **existierende**
Vorfahr entscheidet, und eine Dateisystem-Wurzel zählt nicht als einer; damit läuft das
Rot-zuerst-Rig ausserhalb des Repos wieder (Verzeichnis, einzelne Datei und Knoten-Id je rc 0),
während `/c/…`, eine nicht gemountete Platte, eine tote UNC-Freigabe, ein laufwerksrelatives Wort
und ein Payload ohne `cwd` mit ihrem eigenen Satz rc 2 bleiben. Die gefährliche Gegenrichtung, an
der so eine Verengung kippt, ist zu: die Vorfahren-Regel steht **vor** der Aussen-Frage, also sind
`..`, `../..`, das absolute Elternverzeichnis und `tools/../..` weiterhin Volllauf, und eine
Junction von aussen IN die Fläche ist in beiden Hälften rc 2, während dieselbe Junction auf ein
Unterverzeichnis eine Auswahl bleibt. Was fehlt, ist nichts am Verhalten: der Test, der genau diese
tragende Zusage in der **Kit**-Hälfte absichert, legt seine Junction wegen `prd_repo is tmp_path`
innerhalb des Projekts an und bleibt darum grün, während dieselbe Mutation die echte Kit-Hälfte auf
dem Piloten aufreisst — ein benannter Test, der nicht scheitern kann, an der einen Stelle, wo die
Lead-Entscheidung auf ihm ruht. Eine Zeile (`tmp_path.parent`) plus einmal rot sehen, dann ist
diese Runde fertig; alles andere aus den Runden 1 bis 3 steht.
