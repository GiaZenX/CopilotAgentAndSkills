# TSK-0084 — Abnahmeprotokoll (BUG-0066 und die ganze Familie darum herum)

Umsetzer, 2026-08-24, zwei Durchgänge. Alle Messungen an echten Hook-Prozessen gegen Projekte, die
mit `scaffold_team.sh` **außerhalb** des Repos aufgesetzt wurden
(`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0084\{dev,office,research}_{before,after}`),
Quellbäume `src_before` (Stand vor der Runde) und `src_after` (Stand nach der Runde).

Durchgang 1 schloss `BUG-0066` (Abschnitte „Expected output 1–5") und benannte zwei Reste.
Durchgang 2 schließt **beide Reste** (Abschnitt „Durchgang 2" am Ende).

## Der Fix (Durchgang 1)

`team-kits/*/hooks/_compat.py` — `join_line_continuations` erledigt **beide** Umschreibungen in
einem Aufruf, damit kein Aufrufer die eine ohne die andere bekommen kann:

    continuation = _CONTINUATION_BY_TOOL.get(gated_shell(tool), _CONTINUATION_RX)
    return _STATEMENT_BREAK_RX.sub("\n", continuation.sub("", text or ""))

(Die erste Zeile kam in Durchgang 2 dazu; in Durchgang 1 stand dort fest `_CONTINUATION_RX`.)
`_STATEMENT_BREAK_RX = re.compile(r"\r\n?")`, angewandt **nach** dem Fortsetzungs-Join.
`gate_ledger_valid.py` (nur office) hat seine eigene Kopie (`_CARRIAGE_RETURN_RX`) abgegeben.

## Expected output 1 — die CR-Kette ist in allen drei Kits zu, mit Dateizeuge

`m_cr.py` (Gate-Kette), `m_chain_witness.py` (Kette + echte `powershell.exe` + Bytes von
`.claude/settings.json`).

| Zeile (tool_name) | vorher | nachher |
|---|---|---|
| `tee .claude/settings.json` (Bash) | rc 2 | rc 2 |
| `echo hello ; tee …` / `&&` / `<LF>` (Bash) | rc 2 | rc 2 |
| `echo hello<CR>tee .claude/settings.json` (Bash) | **rc 0** | **rc 2** |
| `echo hello<CRLF>tee …` (Bash) | rc 2 | rc 2 |
| `Get-Content README.md<CR>Set-Content -Path .claude/settings.json -Value x` (PowerShell) | **rc 0** | **rc 2** |

Identisch in `dev_before/after`, `office_before/after`, `research_before/after`.

Dateizeuge, volle Kette, tool_name `PowerShell`:

- vorher, alle drei Kits: Gate rc 0 → `powershell.exe` rc 0 → `.claude/settings.json` von
  11 360 / 12 022 / 11 125 Bytes auf **31 Bytes** `POISONED BY A CARRIAGE RETURN`
  (sha256-Präfix `a7a64e705738`). Danach wiederhergestellt und geprüft.
- nachher, alle drei Kits: Gate rc 2, die Shell läuft nicht, Digest vor = Digest nach
  (`cbd4591a5b6b` / `62933f4d671a` / `d246c3cb5e33`), `POISONED=False`.

## Expected output 2 — die Trennung folgt der Eigenschaft, gegen echte Shells gemessen

`m_separators.py`: `echo one<CH>echo two` gegen `bash.exe` (Git für Windows) und
`powershell.exe` 5.1, Urteil auf den **Rohbytes** — die zweite Anweisung lief genau dann, wenn das
Wort `echo` aus der Ausgabe verschwunden ist. Kandidatenklasse: **alle** C0-Steuerzeichen
(U+0001–U+001F), DEL, U+0085, U+2028, U+2029, gegen `;`, `&&`, `||`, `|`, `&`, Leerzeichen.

Ergebnis — Anweisungstrenner ist genau:

| Zeichen | bash | PowerShell |
|---|---|---|
| U+000A (LF) | trennt | trennt |
| U+000D (CR) | — | **trennt** |
| alles andere der Klasse | — | — |

Tab, U+000B, U+000C, U+0085, U+2028, U+2029 trennen unter PowerShell nur **Wörter**: die Ausgabe
ist `one` / `echo` / `two`, also ein `echo` mit drei Argumenten. Der erste Lauf dieser Messung hat
sie deshalb fälschlich als Trenner gelesen (Python `str.splitlines()` trennt selbst an
`\x1c`–`\x1e`, `\x0b`, `\x0c`, `\x85`, `\u2028`, `\u2029`) — deshalb das Byte-Kriterium.

Daraus die Regel: **ein Zeichen, das EINE der beiden Zielshells honoriert, wird honoriert**, weil
`tool_name` die Wahl des Aufrufers ist. Als Test: `_BREAK_PROBE` in
`tools/test_hooks_v2.py::test_the_shared_preparation_spells_every_statement_break_as_a_newline`
misst beide Enden — die Trenner werden zu `\n`, die Nicht-Trenner bleiben unverändert.

Reihenfolge, ebenfalls gemessen (`m_continuation.py`, `m_order_probe.py`): PowerShell setzt eine
Zeile **nicht** über `\`+blankes CR fort (es druckt `one\` und `two`, zwei Anweisungen). Deshalb
zuerst der Fortsetzungs-Join, dann die Normalisierung. Mit vertauschten Umschreibungen fällt
`echo hello\<CR>Set-Content -Path .claude/settings.json -Value x` von **rc 2 auf rc 0** — und
`echo poison > project_mem\<CR>ory/approvals/APR-0001.yaml` steigt im selben Atemzug von rc 0 auf
rc 2. Das war zum Stand von Durchgang 1 ein **Tausch** zwischen zwei unvereinbaren Lesarten.
**Ueberholt:** nach Durchgang 2 kostet die Reihenfolge kein Urteil mehr (Abschnitt „Was die
Reihenfolge … heute noch kostet“).

## Expected output 3 — Rot gesehen, plus die Gegenrichtung

Mutationsklon `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0084\redrepo` (Spiegel des
Arbeitsbaums ohne `.git`), Mutationen von `mut.py` gesetzt, Tests gefahren, zurückgesetzt.

| Mutation | rot |
|---|---|
| `the-break-rule-removed` (die Vorbereitung joint wieder nur Fortsetzungen) | 23 rot, u. a. `test_a_carriage_return_does_not_hide_a_write_from_the_scope_gate` (3 Kits × 2 Werkzeuge), `test_the_shared_preparation_spells_every_statement_break_as_a_newline[\r-CR-True]`, `test_a_carriage_return_is_read_as_the_newline_it_replaces_and_no_more[a write behind the break]`, `test_every_registered_shell_gate_answers_a_carriage_return_as_it_answers_a_newline` (3 Kits × 2 Werkzeuge), die sechs bestehenden `test_a_carriage_return_ends_a_stage_the_way_powershell_ends_a_statement` |
| `order-swapped` (Normalisierung vor dem Join) | 3 rot: `test_a_continuation_is_joined_before_a_break_is_normalised[\\]` und `[`]`, `test_the_bash_tool_eats_a_bare_carriage_return_before_bash_ever_parses_it` (der `known_hole`-Test von Durchgang 1; in Durchgang 2 entfernt, weil die Luecke geschlossen ist) |
| `cr-as-a-separator-case` (die naive Variante aus TSK-0083 F3-M2: CR als Fall in der Trennerklasse des Gates statt in die Zeilenschaltung umgeschrieben) | 10 rot |
| `a-second-copy-in-a-caller` (`_CARRIAGE_RETURN_RX` wieder in `gate_ledger_valid`) | 1 rot: `test_no_caller_of_the_preparation_keeps_a_second_copy_of_the_break_rule[office-team]` |

**Gegenrichtung** (kein Befehl wird von seinem eigenen Flag getrennt),
`test_a_carriage_return_is_read_as_the_newline_it_replaces_and_no_more`: für jede Zeile müssen
`\n`, `\r` und `\r\n` **dasselbe** Urteil ergeben — `rm<BRK> -rf project_memory/decisions` rc 2,
`git log<BRK> --oneline` rc 0, `git status<BRK>git diff` rc 0. Zusätzlich `m_counter.py` gegen die
aufgesetzten Projekte: `find ledger<BRK> -delete && git commit -m x` bleibt in office für alle drei
Schreibweisen rc 2 (das ist die Zeile, die die naive Variante in TSK-0083 auf rc 0 fallen ließ).

## Expected output 4 — dieselbe Frage für die anderen Aufrufer, als Eigenschaft

`m_callers.py`: jedes **registrierte** Shell-Gate jedes Kits einzeln, neun Zeilen, jeweils mit
`\n` und mit `\r` getrennt, vorher und nachher.

- dev: `gate_git`, `gate_test_coverage`, `gate_memory_complete`, `gate_packaging_decision`,
  `gate_pipeline`, `gate_write_scope`, `gate_push_token`, `gate_shell_hygiene`
- office: `guard_fs_tripwire`, `gate_ledger_valid`, `gate_write_scope`, `gate_push_token`,
  `gate_shell_hygiene`, `gate_filing`
- research: `gate_git`, `gate_memory_complete`, `gate_pipeline`, `gate_write_scope`,
  `gate_push_token`, `gate_shell_hygiene`

**Vorher wich genau ein Gate ab: `gate_write_scope`**, in allen drei Kits identisch
(`protected write` LF=2/CR=0, `ps protected write` LF=2/CR=0, `rm -rf state` LF=2/CR=0).
`gate_ledger_valid` (in TSK-0083 geschlossen), `gate_filing`, `gate_git` und `gate_push_token`
waren nicht betroffen. **Nachher weicht keines mehr ab.**

Die **Eigenschaft**, die das erklärt, statt der Liste: betroffen ist ein Gate genau dann, wenn sein
Urteil davon abhängt, in **welchem Segment** ein Wort steht. Gates, die eine Frage über die ganze
Zeile beantworten (`gate_git`, `gate_push_token`, `gate_filing`), sehen den Trenner gar nicht.

**Stolperdraht, zwei Hälften:**

1. **Baulich.** Die Normalisierung sitzt **in** der Vorbereitung. Ein später hinzukommendes Gate
   kann den Join nicht ohne sie bekommen; es gibt keine zweite, unnormalisierte Ausgabe.
2. **Gemessen.**
   `test_every_registered_shell_gate_answers_every_spelling_of_a_break_alike` leitet die
   Gate-Menge aus der ausgelieferten `settings.json` ab (`_registered_shell_gates`, der bereits
   vorhandene eine Leser dieser Datei) und vergleicht für jedes Gate jede Schreibweise des
   Umbruchs gegen die erste **derselben** Zeile. Ein neu registriertes Gate fällt darunter am Tag
   seiner Registrierung. Was der Test **nicht** misst, steht in seinem Docstring: ein Gate, das die
   Zeile gar nicht verweigert, wird 0 gegen 0 verglichen.
   `test_no_caller_of_the_preparation_keeps_a_second_copy_of_the_break_rule` leitet die Aufrufer aus
   dem geparsten Quelltext ab und verbietet ihnen eine eigene kompilierte Kopie der Regel; auch
   dieser Test nennt seine blinden Flecken selbst (`_names_a_carriage_return`).

## Expected output 5 — Spiegel, Bump, Suiten

- `md5sum` über `team-kits/*/hooks/_compat.py`, `_kernel.py` und `gate_write_scope.py`: je ein Hash
  für alle drei Kits. `gate_ledger_valid.py` liegt nur im office-Kit, fällt also nicht unter die
  Spiegelregel; `KIT_SPECIFIC_HOOKS` brauchte keinen neuen Eintrag.
- `python tools/gen_known_holes.py`, **danach** `python tools/bump_kit_version.py`. Der Sidecar
  liegt unter `team-kits/kernel/`, geht also in den Kit-Hash ein — das ist der Mechanismus, aus dem
  die Reihenfolge folgt. **Richtigstellung (Runde 3):** in dieser Runde hat er sich inhaltlich
  **nicht** geändert; `known_holes.json` und `known_holes_digest.py` sind byte-identisch zum HEAD
  (nachgemessen mit `git show HEAD:… | cmp`). Die neun roten Tests des ersten Suitenlaufs kamen
  also **nicht** vom Sidecar, sondern von einer Kit-Datei (`_compat.py`), die ich nach dem Stempel
  noch angefasst hatte — Hausregel 7, nicht der Sidecar. Die Konsolenzeile
  „`state_write_protection.shell` 5 → 4 test(s)" von `gen_known_holes.py` ist eine **Test-Zählung**,
  keine Änderung an der Datei; meine frühere Formulierung „Sidecar 5 → 4" war falsch.
- `python -m ruff check .` → all checks passed. `python tools/validate.py` → all structural
  checks passed.
- Betroffene Suiten nach Durchgang 1: `python -B -m pytest tools/test_hooks_v2.py
  tools/test_hooks.py tools/test_repo_hygiene.py` → **2888 passed, 13 skipped** in 28:29.
  Der **volle** Lauf gehört nach `DEC-0050` dem Lead zum Lieferzeitpunkt und wurde hier nicht
  gefahren.
- Nicht committet, nicht gepusht.

## Durchgang 2 — beide Reste geschlossen

### REST 1 — das Bash-Werkzeug frisst ein blankes CR (Verschweißung über die Wortgrenze)

**Messung, die die Regel trägt** (`m_transport.py`): jede Shell schreibt eine Zeichenkette zurück,
verglichen werden die **Bytes**, über jedes C0-Steuerzeichen, DEL, U+0085, U+2028 und U+2029.
Ergebnis: **genau ein Zeichen der Klasse überlebt den Weg vom Werkzeug zur Shell nicht — U+000D auf
der `Bash`-Schiene**, auf beiden Wegen (`bash -c <zeile>` und die Zeile auf stdin). PowerShell
behält alle. Ein CR **innerhalb eines CRLF** ist harmlos: gemessen kommt `A<CRLF>B` als `A<LF>B` an,
der Umbruch bleibt also der, den auch das Gate liest.

**Gebaut, fail-closed:** `_kernel._EATEN_IN_FLIGHT` nennt pro Werkzeug die Zeichen, die auf dem Weg
zu dessen Shell verloren gehen, und `_kernel.payload` — die eine Tür, durch die jedes
**blockierende** Gate geht (**16 der 20** registrierten Shell-Gates der drei Kits; nicht darunter:
`gate_test_coverage`, `gate_pipeline` ×2, `guard_fs_tripwire`; `gate_write_scope` in jedem Kit) —
verweigert eine Zeile, die eines davon trägt. Die Meldung nennt das Zeichen und sagt dem Nutzer,
wie er die Zeile ohne es schreibt. **Nicht** repariert (also nicht „CR löschen"), weil das bash'
Lesart erzwingen und PowerShells verlieren würde, und weil eine Verschweißung eine Wortgrenze
überquert — die zweite Lesart wäre eine zweite Tokenisierung der ganzen Zeile, also eine Änderung
im Gate, nicht in der Vorbereitung.

**Vorher → nachher**, echtes dev-Projekt, mit Dateizeuge (`m_weld_witness.py`):

| Zeile (tool Bash) | vorher | nachher |
|---|---|---|
| `echo poison > project_mem\<CR>ory/approvals/APR-0001.yaml` | Gate rc 0 → bash rc 0 → Item enthält `poison` | **Gate rc 2**, Item unverändert |

**Kosten, gemessen** (`m_cost.py`, AST über 111 Dateien: alle 22 Test-Module plus alle Hook-Dateien
der drei Kits): **null** legitime Befehlszeilen mit blankem CR. Acht Zeichenketten tragen eines,
alle acht sind Angriffsformen, die schon rc 2 erwarten (`test_hooks.py` `_LAUNDERING_FORMS`
`carriage_return`, die CR-Tests dieser Runde, der Ledger-CR-Test); die übrigen 20 Treffer sind
Zeichenklassen im Code (`' \t\n\r\x0b\x0c'`) oder Trenner-Parameter. Gegenrichtung steht im Test:
CRLF unter Bash bleibt rc 0, ein blankes LF bleibt rc 0, und **dasselbe** blanke CR unter
**PowerShell** bleibt rc 0, weil PowerShell es wirklich bekommt.

### REST 2 — die Fortsetzung war die Vereinigung beider Shells

**Messung** (`m_continuation.py`, `m_family_witness.py`): `echo one<PAAR>echo two` gegen echte
Prozesse, gezählt wird, ob **ein** Befehl lief oder zwei.

| Paar | bash | PowerShell |
|---|---|---|
| Backslash + LF | setzt fort | **nein** — druckt `one\` und `two` |
| Backslash + CRLF | setzt fort | **nein** |
| Backtick + LF | öffnet eine Substitution, Fehler | setzt fort |
| Backtick + CRLF | Fehler | **nein** — der Backtick escapt das CR, der LF beendet die Anweisung |

**Gebaut:** `_compat._CONTINUATION_BY_TOOL` (Bash → Backslash + Umbruch, PowerShell → Backtick +
LF), ausgewählt über `_compat.gated_shell(tool)` — das Wort des Aufrufers, sonst der Werkzeugname
der Nutzlast, die dieser Prozess gelesen hat (`_compat.last_tool()`, neu neben dem schon
vorhandenen `last_command()`). Das ist **dieselbe** Antwort auf „nicht durch neun Aufrufstellen
fädeln", die `_LAST_PAYLOAD` für die Befehlszeile schon gibt. `gate_write_scope` reicht seinen
Werkzeugnamen zusätzlich ausdrücklich durch.

**Aufrufstellen ohne eigenen Werkzeugnamen** — gefragt und beantwortet statt geraten:
`_compat._fed_to_a_command_parser`, `_compat._shell_normalised` (und damit die ganze git-Leser-Kette
bis `git_invocations`), `_filing._walk` und `gate_ledger_valid._normalise_pipeline` tragen keinen.
Alle vier laufen in einem Prozess, der die Nutzlast durch `_compat.load()` gelesen hat, bekommen
ihn also über die Voreinstellung. Die **einzige** Stelle, die wirklich in die Vereinigung fällt,
ist ein Prozess ganz ohne Nutzlast (ein Test, eine CLI).

**Vorher → nachher**, volle Familie mit Dateizeugen (`m_family_witness.py`: 9 Schreibweisen × 2
Werkzeuge × dev und office = 36 Zeilen):

| Zeile (tool PowerShell) | vorher | nachher |
|---|---|---|
| `Get-Content README.md \<LF>Set-Content -Path .claude/settings.json -Value POISONED` | Gate rc 0 → `powershell.exe` rc 0 → **Datei überschrieben** | **Gate rc 2**, Datei unverändert |
| dieselbe mit Backslash + CRLF | Gate rc 0 → rc 0 → **Datei überschrieben** | **Gate rc 2** |
| dieselbe mit Backtick + CRLF | Gate rc 0 → rc 1, Datei unberührt (kein Loch) | **Gate rc 2** |

Nachher steht in allen 36 Zeilen **kein einziges** `POISONED=True`. Die drei rc-0-Zeilen, die
bleiben, sind die echten Fortsetzungen der jeweiligen Shell — und für jede ist gemessen, dass die
**Shell dann nichts schreibt**: bash führt `echo hello tee .claude/settings.json` als einen Befehl
aus (rc 0, keine Datei), PowerShell antwortet auf Backtick + LF mit rc 1.

### Was die Reihenfolge der zwei Umschreibungen heute noch kostet: nichts

In Durchgang 1 war sie ein **Tausch** (eine Kette zu, die andere auf). Nach Durchgang 2 nicht mehr:
gemessen an einem echten Gate-Prozess (`m_order_probe2.py`) antworten **beide** Reihenfolgen auf
alle vier Trennzeilen rc 2. Der Kommentar im Code sagt das jetzt so — die Reihenfolge bleibt, weil
sie die Shell abbildet, nicht weil ohne sie etwas umfällt. Das steht ausdrücklich hier, weil die
frühere Fassung des Kommentars einen Schutz behauptete, den er nicht mehr baut.

### Rot gesehen (Klon `…/TSK-0084/redrepo`, außerhalb des Repos)

| Mutation | rot |
|---|---|
| `the-in-flight-refusal-removed` (`_EATEN_IN_FLIGHT = {}`) | 6 — `test_a_line_carrying_a_character_its_shell_never_sees_is_refused` |
| `the-continuation-union-restored` (fest `_CONTINUATION_RX` statt der Tabelle) | 15 — `test_a_continuation_the_named_shell_does_not_honour_is_not_joined` |
| `a-gated-tool-without-a-continuation-rule` (ein gegatetes Werkzeug ohne Eintrag) | 10 — zusätzlich `test_every_gated_shell_tool_has_its_own_continuation_rule` |
| `the-break-rule-removed` (Durchgang 1) | 14 |
| `order-swapped` | 5 |
| `cr-as-a-separator-case` (die naive Variante aus TSK-0083 F3-M2) | 7 |
| `a-second-copy-in-a-caller` | 1 — `test_no_caller_of_the_preparation_keeps_a_second_copy_of_the_break_rule[office-team]` |

### Abschluss Durchgang 2

Spiegel: je ein Hash über die drei Kits für `_compat.py`, `_kernel.py`, `gate_write_scope.py`.
`gen_known_holes.py`, **dann** `bump_kit_version.py`. ruff grün, `tools/validate.py` grün.
`docs/POST_V2_WISHLIST.md` L44 steht als **GESCHLOSSEN** mit beiden Ketten und beiden Messungen;
der `known_hole`-Marker dafür ist weg.

Betroffene Suiten nach Durchgang 2: `python -B -m pytest tools/test_hooks_v2.py tools/test_hooks.py
tools/test_repo_hygiene.py` → **2930 passed, 13 skipped** in 29:10, rc 0. Der **volle** Lauf gehört
nach `DEC-0050` dem Lead. Nicht committet, nicht gepusht.

## Benannte Reste (keine gemessene offene Kette)

1. **Der Name `join_line_continuations` untertreibt**, seit die Funktion auch die Umbruch-Regel und
   die werkzeugabhängige Fortsetzung trägt. Umbenannt wird sie **nicht**:
   `.claude/hooks/_harness.py:1556` ruft sie beim Namen, und `.claude/**` ist für den Umsetzer
   verbotener Bereich — ein `AttributeError` dort wäre ein **stiller Durchlass** der vier Gates
   dieses Repos, weil der Provider jeden Code außer 2 als „hook error, carry on" liest. Das ist
   eine Entscheidung, kein Versehen.
2. **Die vier Gates dieses Repos** erben die werkzeugabhängige Fortsetzung (ihr `_harness` liest die
   Nutzlast durch dasselbe `_compat`), die CR-**Verweigerung** aber nicht: die sitzt in
   `_kernel.payload`, und `_harness` ruft `_compat.load` direkt. Auch das ist die Bereichsgrenze;
   gemessen wird es read-only vom Prüfer.
3. **Was der Sweep-Test nicht misst**, in seinem eigenen Docstring benannt: ein Gate, das die
   Testzeile gar nicht verweigert, wird 0 gegen 0 verglichen.

## Durchgang 3 — Nacharbeit aus der Prüfung (F-A, F-B, F-C und zwei Zahlen)

### F-A — wer das CR löscht, und die Plattformbindung

`_kernel.py` sagte, das **Werkzeug** fresse den CR. Gemessen ohne jedes Werkzeug (`rework2/m_fa.py`,
vier Routen in dieselbe bash):

| Route | Ausgabe von `printf %s 'A<CR>B'` |
|---|---|
| `bash -c <zeile>` | `AB` |
| stdin mit `-s` | `AB` |
| stdin ohne `-s` | `AB` |
| eine Skriptdatei | `AB` |
| ein CR, den bash **selbst baut** (`$(printf '\r')`) | `A<CR>B` |

Also: der **Eingabeleser dieser bash** löscht ihn, nicht das Werkzeug — msys bash 5.2.37 auf
Windows. Der Kommentar sagt das jetzt so und nennt die **Bindung**: das Scaffold installiert auch
auf macOS/Linux, wo eine POSIX-bash ein blankes CR als gewöhnliches Zeichen behält. Die Verweigerung
bleibt dort richtig, aber aus dem **anderen** Grund (das Gate beendet eine Anweisung, die Shell
nicht) und ist dann eine Über-Verweigerung statt einer geschlossenen Verschweißung. Nur der erste
Grund ist hier gemessen; der zweite steht als Ableitung im Kommentar und nicht als Messung.

### F-B — wer wirklich im Vereinigungszweig landet

`_compat.py` behauptete „nur außerhalb der Kits erreichbar". Falsch: **jede** Nutzlast, deren
Werkzeug nicht `Bash` oder `PowerShell` ist, nimmt diesen Zweig — `Edit`, `Write`, `Task`, ein
`apply_patch` des Providers — dazu ein Prozess ohne Nutzlast (Test, CLI, `.claude/hooks/_harness.py`).
Ohne Folge, weil solche Nutzlasten kein `command` für diese Leser tragen; der Kommentar sagt jetzt
beides, statt die Reichweite kleiner zu behaupten als sie ist.

### F-C — die zwei wachsenden Zahlen aus dem Test-Docstring

„111 Module" und „die acht" sind aus
`test_a_line_carrying_a_character_its_shell_never_sees_is_refused` gestrichen; der Docstring nennt
die Aussage ohne Zahl und zeigt für das *Wer/Wo* auf `_kernel._EATEN_IN_FLIGHT`. Die gemessene Zahl
steht in diesem Protokoll (Abschnitt REST 1), also an einem Ort im Code-Baum. **Benannt, nicht
erledigt:** `docs/POST_V2_WISHLIST.md` L44 trägt dieselbe Zahl ebenfalls; die Löcherliste ist in
dieser Runde ausdrücklich nicht meine Baustelle.

### Zwei Zahlen, richtiggestellt (`rework2/m_numbers.py`, beides per AST bzw. `git show | cmp`)

- **16 von 20** registrierten Shell-Gates fragen `_kernel.payload`, nicht 15 — dev 6/8 (ohne
  `gate_test_coverage`, `gate_pipeline`), office 5/6 (ohne `guard_fs_tripwire`), research 5/6 (ohne
  `gate_pipeline`). Im Protokoll oben korrigiert.
- **`known_holes.json` und `known_holes_digest.py` sind byte-identisch zum HEAD.** Es gab kein
  „5 → 4" in der Datei; das war die Konsolenzählung von `gen_known_holes.py`. Im Protokoll oben
  korrigiert, samt der falschen Ursachenzuschreibung für die neun roten Tests.

### Abschluss Durchgang 3

Spiegel: je ein Hash über die drei Kits für `_compat.py` und `_kernel.py` (`gate_write_scope.py`
unverändert). `gen_known_holes.py`, **dann** `bump_kit_version.py` → dev `2026.08.24-6`,
office `2026.08.24-15`, research `2026.08.24-6`. ruff grün, `tools/validate.py` grün.
Betroffene Suiten `tools/test_hooks_v2.py + test_hooks.py + test_repo_hygiene.py` →
**2930 passed, 13 skipped** in 29:01, rc 0 — dieselbe Zahl wie nach Durchgang 2, also hat die
Erweiterung des Lesers keinen Falschalarm erzeugt. Der **volle** Lauf gehört nach `DEC-0050` dem
Lead. Nicht committet, nicht gepusht.

## Durchgang 4 — Nacharbeit aus der zweiten Prüfung (F-D2, F-B1, F-C1)

### F-D2 — die Nicht-Gelesen-Liste war wieder zu klein (blockierend)

Der Prüfer widerlegt die Klasse „ein Muster, dessen NAMEN der Quelltext nicht enthält" mit der
**Kreuzung** der beiden Formen, die Durchgang 3 gerade erst aufgenommen hatte: ein modulweites
Tupel von **Prädikats-Funktionen**. Beide Namen stehen im Quelltext, der Container hält kein
Muster, sein Name ist kein Funktionsrumpf — der namensfolgende Leser endet dort.

**Gewählt: (b), definitorisch** — und zusätzlich, nicht als Ersatz. `_patterns_called_by`
instrumentiert jedes modulweite `re.Pattern` (auch die in Containern) mit einem aufzeichnenden
Stellvertreter und lässt die Ausnahme über einen Sondenkorpus laufen; gezählt wird, welche Muster
wirklich **gefragt** werden. Der Test nimmt die **Vereinigung** beider Leser. Begründung, warum
beide: der namensfolgende sieht alle Pfade, aber nur auflösbare Namen; der laufende löst nichts auf,
sieht aber nur die Pfade der Sonden. Ihre blinden Flecken überschneiden sich nicht.

Gemessen (`rework3/m_fd2.py`, beide Leser aus der ausgelieferten Datei **geparst**, nicht kopiert;
Verb `deno`, das das Verhaltenskorpus **nicht** aufzählt — die Selbstkorrektur des Prüfers
übernommen):

| Konstruktion | Namensleser | laufender Leser | Vereinigung | befreit die Stufe |
|---|---|---|---|---|
| Kontrolle: ausgelieferte Quelle | grün | grün | grün | nein |
| V1 direkt benannt | ROT | ROT | ROT | ja |
| V2 Tupel von MUSTERN | ROT | ROT | ROT | ja |
| V3 modulweites Lambda | ROT | ROT | ROT | ja |
| V4 über `globals()` | **grün** | **ROT** | ROT | ja |
| V10 Tupel von FUNKTIONEN (der Befund) | **grün** | **ROT** | ROT | ja |
| V5 definiert, nie gelesen | grün | grün | grün | nein (korrekt) |
| V6 ganz ohne Regex (`startswith`) | grün | grün | **grün** | **ja** |

Also: der Befund ist zu, und der in Durchgang 3 **benannte** Rest (`globals()`) fällt mit.

**Kosten des laufenden Lesers: 0,0004 s für 12 Sonden** — die Instrumentierung ist billig.

**Rot gesehen mit echtem pytest im Klon** (`rework3/mut_fd2.py`, echte Pflanzung in `redrepo`,
Ziel `test_every_vouching_run_pattern_is_named_here`, danach zurückgesetzt):

| Pflanzung | rc |
|---|---|
| V1 / V2 / V3 / **V4** / **V10** | je **1 failed** |
| V5 (definiert, nie gelesen) | 1 passed — korrekt |
| V6 (ganz ohne Regex) | 1 passed — der benannte Rest |

**Der verbleibende Rest, gemessen statt vermutet:** eine Ausnahme, die **gar kein** `re.Pattern`
befragt (`stage.strip().startswith("deno ")`), befreit die Stufe, und beide Leser bleiben grün.
Das steht so im Docstring von `_patterns_called_by`, samt dem Grund (es ist der Preis dafür, die
Frage über *Muster* zu stellen) und dem Zeiger auf die Frage, die es fangen müsste (welche Stufe
wird frei — was die Verhaltenstests für die von ihnen aufgezählten Verben tun). Dazu ein Muster,
das nur bei einer Eingabe außerhalb der Sonden gefragt wird; deshalb enthalten die Sonden Stufen,
die auf **nichts** passen, damit eine `or`-Kette bis zum Ende gelaufen wird statt beim ersten Treffer
abzubrechen. Und der Test prüft ausdrücklich, dass der laufende Leser **etwas** aufgezeichnet hat —
eine stumme Instrumentierung ließe die Vereinigung still auf den anderen Leser zusammenfallen.

### F-B1 — der über-alarmierende Satz über `_harness`

`_compat.py` zählte `.claude/hooks/_harness.py` unter „ein Prozess, der gar keine Nutzlast gelesen
hat". Falsch, und zwar in der Richtung, die dem eigenen Durchsetzungsapparat eine Schwäche
andichtet: `_harness.payload()` ruft `_compat.load()`, also ist `_LAST_PAYLOAD` gefüllt und die vier
Repo-Gates nehmen den Pro-Shell-Zweig. Der Kommentar sagt das jetzt mit der Messung des Prüfers
(PowerShell: zwei Anweisungen rc 2, `\`+LF rc 2, Backtick+LF rc 0; Bash spiegelbildlich) und nennt
als payload-lose Aufrufer nur noch, was es wirklich ist: ein Test oder die CLI.

### F-C1 — der falsche Mechanismus

„the one door every blocking gate goes through" ist raus. Der Docstring sagt jetzt: die Regel sitzt
an der **geteilten** Nutzlast-Tür, nicht in einem Gate; vier registrierte Shell-Gates erreichen die
Nutzlast anders und mindestens zwei davon können blockieren; was die Verweigerung trotzdem für den
ganzen **Aufruf** trägt, ist `gate_write_scope` auf demselben Ereignis in jedem Kit plus die Regel,
dass eine Kette bei der ersten Verweigerung endet. Ohne Zahl im Docstring — die steht in diesem
Protokoll.

### Abschluss Durchgang 4

Spiegel: ein Hash über die drei Kits für `_compat.py` (nur diese Kit-Datei geändert; `_kernel.py`
und `gate_write_scope.py` unverändert). `gen_known_holes.py`, **dann** `bump_kit_version.py` →
dev `2026.08.24-7`, office `2026.08.24-16`, research `2026.08.24-7`. ruff grün,
`tools/validate.py` grün. Betroffene Suiten `tools/test_hooks_v2.py + test_hooks.py +
test_repo_hygiene.py` → **2930 passed, 13 skipped** in 34:58, rc 0 — dieselbe Zahl wie nach den
Durchgängen 2 und 3, der zweite Leser erzeugt also keinen Falschalarm. Der **volle** Lauf gehört
nach `DEC-0050` dem Lead; **er wird von dieser Runde ungültig gemacht** (Testcode in
`tools/test_hooks_v2.py` und ein Kommentar in `team-kits/*/hooks/_compat.py`, also ein neuer
Stempel). Nicht committet, nicht gepusht.

## Benannter Rest (nicht geschlossen): der Parallel-Schalter von pytest fällt in die H19-Familie

**Nicht meine Messung** — vom Lead beim Versuch des vollen Lieferlaufs beobachtet und hier auf
seine Bitte festgehalten, damit sie nicht mit der Sitzung stirbt. Von mir **nicht** nachgefahren,
und sie ist rollenabhängig: `gate_lead_write_scope` verweigert dem **Sitzungsagenten**, nicht dem
Umsetzer, also sagt ein Lauf von mir über diesen Fall nichts aus.

Beobachtet: beide Schreibweisen des Parallel-Schalters hinter `pytest tools/` enden mit **rc 2**
und der Meldung, der Sitzungsagent dürfe `tools/` nicht schreiben —

```
python -B -m pytest tools/ -q -n 8
python -B -m pytest tools/ -q --numprocesses 8
```

— während **dieselbe Zeile ohne den Schalter rc 0** ist. Also keine Aussage über `tools/`, sondern
über das Wort dahinter: eine Über-Verweigerung derselben Familie wie `H19`
(`docs/POST_V2_WISHLIST.md`), wo ein Kandidat, der einen Vorfahren eines geschützten Baums nennt,
als Schreibzugriff auf alles darunter gelesen wird. Praktische Folge, ebenfalls vom Lead
beobachtet: der volle Lauf ist für ihn weder parallel (rc 2) noch im Vordergrund (Zeitgrenze des
Werkzeugs; `test_hooks_v2.py` allein war nach 590 s bei 43 %) erreichbar, und zwei
Hintergrundläufe wurden von außen beendet.

**Nicht geschlossen, nur benannt.** Was stattdessen begrenzt: der Lauf ist als serieller
Hintergrundlauf durch einen Umsetzer erreichbar (dieses Protokoll, Abschnitt „Voller Lieferlauf").
Ob der Schalter wirklich als Pfad gelesen wird und an welcher Stelle, ist **nicht** gemessen — das
gehört in die Löcherliste des Repos und damit zum Lead, nicht in dieses Item.
