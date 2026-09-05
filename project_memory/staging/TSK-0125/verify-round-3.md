# TSK-0125 — Prüfbericht Runde 3 (`harness-verifier`)

Kurze Runde: **nur** die drei Befunde aus `verify-round-2.md`. Alles andere steht aus Runde 2.
Frische Kopien unter `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0125\verify\`:
`r3base` = pristine `75a00d1` (Klon des Worktree-Branches), `r3` = `r3base` + Patch (echter Klon
mit `.git`), `r3tree` = gestempelte Worktree-Kopie ohne `.git`, `r3lab` = Wegwerf-Repo für den
echten Werkzeugpfad. **Das Lastfenster blieb geschlossen** — keine Fensterdatei, kein Brenner,
kein Lastlauf (geprüft: unter `_round-scratch/TSK-0125/` liegt weder `LOAD_WINDOW_OPEN` noch
`LOAD_BURNER_PIDS`).

**Urteil: PASS.** Alle drei Befunde sind geschlossen und einzeln nachgemessen, jeder mit einem
Rot-Zuerst, den ich selbst hergestellt habe. Ein einziger Wortlaut-Kratzer bleibt (N1, unten) —
kein Befund, der eine Runde rechtfertigt.

---

## R2-1 — die beiden Binär-Prüfungen widersprachen sich: **PASS**

`tools/test_repo_hygiene.py:196-198` nimmt jetzt gits eigene Inhaltsantwort (`w/`-Spalte) **vor**
der ersten Zusicherung von der Textseite ab, und genau diese Pfade sind am Ende die gemeldete
Menge (`:217-221`). Mit der Fixture `assets/wide.bin` (8508 Füllbytes, dann NUL, in den Index
gelegt):

```
$ git ls-files --eol assets/wide.bin
i/-text w/-text attr/text=auto eol=lf   assets/wide.bin

OHNE Pin  -> die alte Prüfung ROT und fordert ihn:
  E AssertionError: git reads these files as binary by their bytes, but no `binary` line in
    .gitattributes covers them ... ['assets/wide.bin']        tools\test_repo_hygiene.py:420
  die NEUE Prüfung GRÜN, und sie MELDET die Datei:
  UserWarning: git treats these as binary although their first 8000 bytes carry no NUL ...
    ['assets/wide.bin']                                       tools\test_repo_hygiene.py:218
  -> 1 failed, 1 passed, 1 warning

MIT dem Pin `assets/wide.bin binary` (der, den die alte Prüfung fordert):
$ git check-attr text eol -- assets/wide.bin   ->  text: unset / eol: lf
$ git ls-files --eol assets/wide.bin           ->  i/-text w/-text attr/-text
  -> 2 passed, 29 deselected, 1 warning   (die Warnung nennt weiterhin die Datei)
```

Damit ist der Widerspruch weg: es gibt jetzt einen Zustand von `.gitattributes`, in dem beide
Prüfungen grün sind, und er ist genau der, den die alte Prüfung verlangt. Die Klasse, für die die
`binary`-Zeilen existieren, wird **gemeldet statt asserted** — was der Docstring immer schon sagte.

**Die beiden F1-Mutationen bleiben rot**, beide bei 1278:

```
Pin gelöscht:      E AssertionError: 1278 tracked file(s) carry no NUL in their first 8000 bytes
                   ... `* text=auto eol=lf` ...            tools\test_repo_hygiene.py:206
blanket `* binary`: dieselbe Zusicherung, dieselben 1278
```

**Die Selbstkorrektur des Umsetzers ist richtig, und meine Runde-1-Formulierung war es nicht.**
Gemessen unter `* binary`:

```
$ git check-attr text eol -- README.md   ->  text: unset / eol: lf
$ git ls-files --eol README.md           ->  i/lf  w/lf  attr/-text
```

Ein `binary`-Attribut nimmt die `eol`-Antwort **nicht** weg, und weil die `w/`-Spalte den Inhalt
liest, bleibt `README.md` im Subjekt — die Mutation wird von der `text: auto`-Hälfte gefangen, nicht
von einer geleerten Menge. In meinem Runde-1-Bericht stand zu dieser Mutation, „der Sweep sieht gar
nichts mehr"; das war zu weit gegriffen (der Sweep liest `w/`, und das blieb `lf`). Der Satz im
Code steht jetzt gemessen richtig da (`tools/test_repo_hygiene.py:179-182`), und die falsche
Fassung ist weg — `grep` über `test_repo_hygiene.py`, `.gitattributes`, `docs/line-endings.md` und
`normalise_line_endings.py` nach „empties that answer" / „empties the subject": **kein Treffer**.

---

## R2-2 — die beiden Verweigerungsgründe schließen einander nicht aus: **PASS**

`tools/normalise_line_endings.py::_verdict` stellt jetzt zwei getrennte Fragen
(`blob_carries_crlf`, `diverges`), und `diverges` vergleicht gegen `committed.replace(CRLF, LF)`.

**Durch den echten Pfad gemessen** (`verify/r3lab.py`: eigenes Repo, echte Blobs, echtes
`git show HEAD:<pfad>`, das ausgelieferte Skript als **Prozess** — kein Monkeypatch). Vier
verfolgte Dateien, alle im Arbeitsbaum auf CRLF, zwei davon zusätzlich von Hand geändert:

```
blobs as HEAD holds them:
   plain.md     b'one\ntwo\n'
   edited.md    b'x\ny\n'
   keepcrlf.md  b'k1\r\nk2\r\n'
   both.md      b'b1\r\nb2\r\n'

git status --short:     M both.md     M edited.md     M plain.md      (keepcrlf.md fehlt hier)

1 file(s) would be normalised (run with --apply):
  plain.md
3 file(s) REFUSED -- each one is named with what stopped it:
  both.md: TWO things are wrong at once: the blob HEAD holds carries CRLF itself, AND this file
    differs from it beyond its line endings (21 bytes normalised against 6 in the blob). So
    `git status` DOES report it, and `git add --renormalize` would take that other change into the
    index with it -- neither command is the answer on its own. Decide the content change first,
    then renormalise
  edited.md: normalised it is 18 bytes and HEAD holds 4 -- it carries a real uncommitted change ...
  keepcrlf.md: the blob HEAD holds carries CRLF itself, so the working tree is not what is wrong
    here and `git status` says nothing about this file. The index is what needs rewriting:
    `git add --renormalize -- keepcrlf.md`
```

Jeder der vier Sätze ist gegen git selbst geprüft: `both.md` steht in `git status` — und der Satz
sagt „`git status` DOES report it"; `keepcrlf.md` steht **nicht** darin — und der Satz sagt
„says nothing about this file". Genau das war in Runde 2 falsch. Die drei Einzelfälle sind
unverändert richtig.

**Rot-Zuerst, von mir hergestellt** (alte Reihenfolge zurück, `if blob_carries_crlf and diverges:`
→ `if False:`):

```
E AssertionError: the combination is answered with one of the two single reasons: the blob HEAD
  holds carries CRLF itself, so the working tree is not what is wrong here and `git status` says
  nothing about this file. ...                              tools\test_repo_hygiene.py:349
```

Zurückgesetzt `2 passed`. `docs/line-endings.md` führt jetzt drei Fälle plus die Ausnahme für
kanonischen Zustand und sagt ausdrücklich, dass die beiden sich **nicht** ausschließen.

---

## R2-3 — die Begründung nannte einen Test, der dafür nicht fallen kann: **PASS**

Die Klausel ist gestrichen. Der Kommentar (`tools/normalise_line_endings.py`, direkt vor `ROOT =`)
trägt jetzt den echten Grund und sagt zusätzlich, dass **absichtlich kein** Stolperdraht genannt
wird:

> „No test is named here as a tripwire for that: an earlier version of this comment named one, and
> the flag was measured to make that test's assertion EASIER, never red -- a named check that
> cannot fall is worse than none."

Das ist die richtige Auflösung: lieber keine Nennung als eine, die nicht fallen kann. Dass der
Umsetzer `assert not sys.dont_write_bytecode` **nicht** in `tools/test_hooks.py` gesetzt hat, ist
sauber begründet (Naht dieses Schnitts) und von mir per Hash bestätigt: `tools/test_hooks.py` ist
gegenüber `75a00d1` **unberührt**. Notiert, nicht angelastet.

---

## Nahtprüfung: was sich in Runde 3 überhaupt bewegt hat

Per SHA-256 über die drei Stände (`verify/r3seam.py`):

| Datei | 75a00d1 | Runde 2 | Runde 3 | |
|---|---|---|---|---|
| `.claude/hooks/test_gates.py` | 5d7882febbc3 | 0952765f9ec0 | 0952765f9ec0 | unverändert seit Runde 2 |
| `.gitattributes` | 328a8a6385fb | ff8d28ab5fc5 | ff8d28ab5fc5 | unverändert seit Runde 2 |
| `docs/POST_V2_WISHLIST.md` | 6d3232d49b91 | 31e7ef0202b3 | 31e7ef0202b3 | unverändert seit Runde 2 |
| `team-kits/kernel/kitupdate.py` | b7706f8eba83 | 6a012738abf9 | 6a012738abf9 | unverändert seit Runde 2 |
| `tools/test_kitupdate.py` | 5c3706012e59 | e76468f48566 | e76468f48566 | unverändert seit Runde 2 |
| `tools/test_office_duties.py` | e934499bfbdf | 9161f7a14f62 | 9161f7a14f62 | unverändert seit Runde 2 |
| `tools/test_reference_skills.py` | e6b4ed3b9312 | 275463900b6f | 275463900b6f | unverändert seit Runde 2 |
| `docs/line-endings.md` | — | 3978df041065 | fa680b75ebbb | **geändert** |
| `tools/normalise_line_endings.py` | — | 4490fdb5798d | 6ea72e46da82 | **geändert** |
| `tools/test_repo_hygiene.py` | 4176f48354cb | 27ebf37d64c4 | a012a0af87b3 | **geändert** |
| `tools/test_hooks.py` | c6f953bc9b58 | c6f953bc9b58 | c6f953bc9b58 | vom Strom **nie** angefasst |
| `tools/validate.py` | d5e86bd9fd2b | d5e86bd9fd2b | d5e86bd9fd2b | vom Strom nie angefasst |
| `.github/workflows/ci.yml` | 1bb333bc684f | 1bb333bc684f | 1bb333bc684f | vom Strom nie angefasst |

Genau die drei Dateien, die meine drei Befunde nannten, und keine weitere. `test_gates.py` trägt
per `ast` weiterhin **genau eine** geänderte Definition
(`test_gate3_answers_before_its_registration_however_costly_the_line_is_to_judge`; `added: []`,
`removed: []`). Löchernummern im Patch: nur `H160`, `H161`, `H162`.

**Patch:** 10 Dateien, alle im `allowed_scope`, **88 355 B**, **0 CR**, **keine VERSION-Hunks**,
`git apply --check` gegen einen frischen `75a00d1`-Klon → `rc 0`.

---

## Läufe

| Lauf | Ergebnis |
|---|---|
| `tools/test_repo_hygiene.py` (Klon **mit** `.git`) | **31 passed** (108,7 s) |
| die AC-2-Gruppe einzeln (`binary_by_bytes`, `binary_pin`, `crlf`, `line_ending`, `remedy`) | 6 passed |
| `python -m ruff check .` | `All checks passed!` |
| `tools/bump_kit_version.py` im gestempelten Worktree-Abzug | alle drei `unchanged` (`2026.09.04-2 / -4 / -2`) |
| `tools/validate.py` im gestempelten Worktree-Abzug | `all structural checks passed` |

**Eine Beobachtung, die keine ist:** `tools/validate.py` scheitert im **patch-applizierten Klon**
(`office-team`/`research-team`: „kit files changed but VERSION not bumped"). Das ist die gewollte
Form des Patches — er trägt bewusst keine VERSION-Hunks (DEC-0070), also fällt der Stempel im Klon
auseinander. Im Worktree, der den Stempel trägt, ist `validate.py` grün. Kein Befund.

---

## N1 — ein Wortlaut-Kratzer, kein Befund

`tools/test_repo_hygiene.py:218-221`: die Meldung lautet „that is a `binary` line doing work the
heuristic alone would not do" — sie feuert aber auch, wenn **noch gar keine** `binary`-Zeile für die
Datei existiert (gemessen oben im ungepinnten Fall, wo `.gitattributes` die Fixture nicht nennt).
In diesem Moment ist die alte Prüfung ohnehin rot und schickt den Leser genau zu dieser Zeile, also
richtet der Satz keinen Schaden an; er beschreibt nur den gepinnten Fall. Wenn der Umsetzer ihn
ohnehin anfasst: „…that is either a `binary` line doing work the heuristic alone would not do, or a
file that still needs one". Nichts, wofür eine Runde zu öffnen wäre.

---

## Nicht gemessen

Die Last-Hälfte von AC-4 (`H162`) — Fenster zu, keine Brenner, keine Zahlen. Alles übrige steht
unverändert aus Runde 2 (dort gemessen): AC-1 auf drei Wegen, AC-3 am echten Piloten, die
Solo-Hälfte von AC-4, die sechs Rig-Verweigerungen, die geerbten Zwei-Fehler-ohne-`.git`.
Die volle Suite gehört dem Merge (DEC-0050); die Nachher-Richtung von AC-1 dem Push des Nutzers.

---

## Urteil

**PASS — die drei Befunde aus Runde 2 sind geschlossen, und zwar an der Stelle, an der sie
entstanden sind.** Der Widerspruch zwischen den beiden Binär-Prüfungen ist aufgelöst, nicht
zugedeckt: mit meiner eigenen Fixture existiert jetzt ein `.gitattributes`-Zustand, in dem beide
grün sind, die Datei wird gemeldet statt behauptet, und beide Mutationen der Pin-Zeile fallen
weiterhin mit 1278 benannten Dateien; die Selbstkorrektur des Umsetzers zum blanken `* binary` ist
richtig und meine Runde-1-Formulierung dazu war zu weit gegriffen — gemessen bleibt `eol: lf` unter
`binary` stehen, und gefangen wird die Mutation von der `text: auto`-Hälfte. Der Doppelfall des
Normalisierers antwortet jetzt mit beiden Gründen und empfiehlt keinen der zwei Befehle allein, und
das habe ich nicht am Monkeypatch, sondern an einem echten Repo mit echten CRLF-Blobs und dem
Skript als Prozess gegen `git status` gegengeprüft — Satz für Satz. Die falsche Testnennung ist
ersatzlos gestrichen, mit dem Satz dazu, warum hier absichtlich keine steht; dass der Umsetzer
dafür `tools/test_hooks.py` als Naht nicht angefasst hat, ist per Hash bestätigt und richtig. Die
Runde hat genau drei Dateien bewegt und keine vierte. Damit ist der Strom aus meiner Sicht
abnahmefähig; offen bleibt allein die Last-Hälfte von AC-4 als `H162`, die auf das Fenster des
Leads wartet, plus die Merge-Vorbedingung (`normalise_line_endings.py --apply` im Haupt-Checkout)
und der Push für die Nachher-Richtung von AC-1.
