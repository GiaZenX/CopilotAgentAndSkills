# Nach der Wiederherstellung als Items anzulegen (Kernel liegt, deshalb hier)

## 1. FR — die kanonische Schreibnutzlast nennt einen Pfad, der im echten Repo existiert

`related_pr: PR-0002`

Viermal in drei Tagen (2026-08-06; 08-07 zweimal; 08-08) hat eine Gate-Messung
`team-kits/kernel/state.py` im **echten** Arbeitsbaum zerschrieben, jedes Mal über eine andere
Ursache: falsches Arbeitsverzeichnis; geerbtes `OLDPWD` bei korrektem cwd; zuletzt eine
**Rotmessung**, die den Pin absichtlich ausbaut und `OLDPWD` aus ihrem Startbefehl
(`cd <sandbox> && python …`) erbte. Jede Einzelursache wurde geschlossen, und der nächste Weg war
jedes Mal ein anderer.

**Das Problem, nicht die Lösung:** Die Messungen brauchen einen echten Schreibzugriff durch eine
echte Shell auf einen **geschützten** Pfad — ein Rückgabecode ist in diesem Repo kein Beleg.
Zugleich sind die Messungen ihrem Wesen nach Versuche darüber, **wo ein Wort landet**, und ein Teil
von ihnen (die Rotmessungen) baut den Schutz absichtlich aus. Eine Vorrichtung kann sich also nicht
selbst bewachen — das ist H37 Rest 1, und es ist keine Nachlässigkeit, sondern die Gattung.

Was dabei den **Schaden** trägt, ist eine dritte Eigenschaft, die mit dem Messgegenstand nichts zu
tun hat: die Nutzlast nennt einen relativen Pfad, der im echten Repo eine **echte, wertvolle**
Datei benennt. Landet die Zeile daneben, trifft sie Arbeit. Wählte die Nutzlast einen Pfad, den die
geschützte Menge zwar **per Muster** deckt, den es im echten Repo aber **nicht gibt**, dann erzeugt
eine danebengelandete Messung eine **Streudatei statt eines Verlusts** — und die fällt beim
nächsten Statuslauf auf.

Wer das baut, prüft zuerst, ob `_harness.ProtectedArea` (abgeleitet aus
`tools/bump_kit_version.py` + `kernel.hashing.kit_hash_inputs`) einen solchen Pfad wirklich per
Muster deckt und nicht per Existenz, und misst beide Enden: dass die Messungen weiter dasselbe
messen, und dass ein absichtlich danebengelenkter Lauf nichts Wertvolles mehr trifft.
`.claude/hooks/` ist geschützter Bereich — Item für den Umsetzer, nicht für den Sitzungsagenten.

## 2. Evidence-Lage für den Commit

TSK-0022 Runde 3 ist gebaut, aber **nicht** abgenommen: eine grüne volle Suite im Arbeitsbaum
existiert nicht, solange `state.py` beschädigt ist. Nach der Wiederherstellung muss der Prüfer
Runde 3 messen; erst sein PASS erlaubt `kernel.cli evidence` und damit den Commit (Gate 3).

## 3. Vom Umsetzer gemeldete Reste dieser Runde (schon in der Löcherliste)

- **H37 Rest 3** — `BASH_ENV` führt in `bash -c true` eine Datei aus und schrieb den Köder
  außerhalb der Sandbox **mit** der neuen Umgebung davor (`ENV` nicht).
- **H37 Rest 1** — Rotmessungen sind die Gattung, die den Pin absichtlich ausbaut.
- **H37 Rest 4/5** und der **H38-Absatz** (R1/R2/R3 des Prüfverdikts).
