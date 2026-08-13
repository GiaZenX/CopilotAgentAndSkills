# Löcherlisten-Einträge aus TSK-0018 — noch nicht abgelegt

Der Umsetzer von `TSK-0018` durfte `docs/POST_V2_WISHLIST.md` nicht anfassen: `TSK-0019` schreibt
parallel darin. Er hat die Einträge stattdessen fertig formuliert übergeben, und sie liegen hier,
damit sie nicht in einem Sitzungsprotokoll verschwinden.

**Einzuarbeiten, sobald `TSK-0019` gelandet ist.** Alle Zahlen sind an diesem Tag gemessen; wer sie
einarbeitet, prüft sie nicht neu, sondern übernimmt sie mit dem Datum.

---

## (a) Korrektur und Ergänzung an `L17`

Die dort notierte Kurve steht unter einer Bibliothek, die dieser Leser nicht benutzt, und die
Feldzahl fehlt.

> **Korrektur 2026-08-07:** die früher hier notierte Kurve war unter „PyYAML with libyaml" gemessen;
> dieser Pfad ruft `yaml.safe_load` und damit den **reinen Python-Loader** (`yaml.SafeLoader`),
> obwohl `yaml.__with_libyaml__` True ist. Nachgemessen mit
> `report._check_no_v1_records_outside_the_archive` direkt (bester von 3, ein büroartiges
> `filing_log.yaml`): 1 MB 1,85 s · 2 MB 2,90 s · 4 MB 6,36 s · 8 MB 18,01 s; die erste, kalte
> Lesung jeder Größe liegt Faktor 1,7–2,7 darüber (2,9–4,2 s je MB). Das Gesamtbudget von 8 MB
> kostet damit **~18 s warm und ~31 s kalt** — ein Drittel bis die Hälfte der 60 s, die ein
> `PreToolUse`-Hook für **alles** hat.
>
> **Feldzahl (gemessen 2026-08-07, dieselbe Auswahl, die der Scan trifft):** `synaipse` hält 20
> Kit-Dokumente mit zusammen 5 114 314 B = **63,9 % des Gesamtbudgets**, seine größte Datei
> `design.yaml` 1 015 193 B = **50,8 % der Einzelgrenze**; `portfoliomanaigement` liegt bei 12,2 %
> bzw. 6,3 %. Die Antwort auf „trifft ein echtes Projekt die Grenze?" lautet damit nicht *nein*,
> sondern **noch nicht** — und die Abhilfe („nimm die Datei außerhalb der Sitzung heraus") ist genau
> der Griff, den `gate_write_scope` innerhalb der Sitzung verbietet.

## (b) `L21` — Die Prosa-Regel entscheidet Wort-Kovorkommen, nicht Paarung

> **Mechanismus:** `test_migrate.test_no_shipped_text_says_an_import_arrives_at_its_initial_status_full_stop`
> fragt drei Wortlisten an einem Satz ab: ein Import-Wort, ein Anfangsstatus-Wort, kein Wort der
> anderen Tür. Ob der Satz die Hälfte **behauptet** oder sie **verneint**, sieht keine der drei.
>
> **Kette (gemessen 2026-08-07 an den ausgelieferten Regexen, je eine Probe):**
> `Imports arrive at their INITIAL status, never at the mapped one.` — falsch über dieses Harness,
> **geht durch**; `A record the table calls unfinished is imported at its initial status.` — wahr und
> harmlos, **wird abgelehnt**; `Importierte Items kommen im Anfangsstatus an und tragen keine
> Freigabe.` — dieselbe Behauptung auf Deutsch, **geht durch**; `Every imported PROC arrives in DRAFT
> and carries no approval.` — dieselbe Behauptung mit **benanntem** Status, **geht durch**. Deckung
> über das abgeleitete Korpus: 2704 Sätze in 70 Dokumenten, 56 mit Import-Wort, 2 mit
> Anfangsstatus-Wort, **genau einer** wird angesehen.
>
> **Urteil: NICHT SCHLIESSBAR mit dem Instrument.** Die Paarung zu entscheiden ist eine Lesart; ein
> Prüfer, der einen richtigen Satz meldet, ist schlechter als keiner — die zweite Probe ist bereits
> dieser Fall und ist der Preis der ersten.
>
> **Was stattdessen begrenzt:** der Docstring behauptet die Paarung nicht mehr, sondern nennt alle
> vier Proben; und der Test **fällt**, sobald die Zahl der angesehenen Sätze null erreicht — eine
> Prüfung, die nichts ansieht, ist kein grünes Licht.
>
> **Stolperdraht:** derselbe Test (die Vakuum-Zusicherung), rot gesehen, indem der eine angesehene
> Satz in `README.md` umformuliert wurde.

## (c) `L22` — Der Plan-Digest deckt den Plan, nicht das Harness

> **Mechanismus:** `migrate.plan_digest` ist über das Plan-Objekt genommen. Eine Kit-Änderung, die den
> **Inhalt** des Plans bewegt, invalidiert einen vorgelegten Plan (gemessen: ein zusätzlicher Eintrag
> in `backlog_types.OPTIONAL_FIELDS` bewegt den Digest bei byte-identischem `state_fingerprint`,
> unveränderten Flaggen und unveränderter Registrierung). Eine Kit-Änderung **unterhalb** des Plans —
> wie `execute` schreibt, was der Plan beschreibt — bewegt ihn nicht.
>
> **Kette:** Trockenlauf lesen → Kit-Update, das nur die Schreibhälfte ändert → `--plan <digest>`
> läuft durch, weil der Digest stimmt, und schreibt anders, als der gelesene Trockenlauf beschrieb.
>
> **Urteil: OFFEN, nicht blockierend innerhalb einer Sitzung** — die Kette braucht eine
> Neuinstallation zwischen den beiden Hälften.
>
> **Was stattdessen begrenzt:** die Verweigerungsmeldung nennt Code und Tabellen jetzt als dritte Art
> von Eingabe und schickt an `doctor`, das die `kit_version` berichtet; und die Gegenrichtung ist
> gemessen (`test_moving_the_kernels_own_contract_table_alone_moves_the_digest`, zweite Hälfte): eine
> Konstante ohne Verdikt bewegt den Digest nicht — der Digest ist also kein Versionsstempel und darf
> nicht als einer gelesen werden.

## (d) `L23` — Zitate außerhalb der II.10-Nachträge prüft nichts

> **Mechanismus:** `test_disposition.test_every_citation_in_the_migration_addenda_carries_the_wording_it_cites`
> prüft nur die Nachträge, weil nur dort die Konvention „Zitat in Anführungszeichen, Paraphrase
> kursiv" gilt.
>
> **Kette (gezählt 2026-08-07 mit dem Leser derselben Datei):** 35 zitatförmige Spannen in der Spec,
> 7 in den Nachträgen (alle auflösbar), 28 außerhalb, davon **17 unauflösbar**. Die frühere
> Begründung („zitieren die Welt außerhalb dieses Repos") hält für die Mehrzahl und **nicht** für
> drei: `Prefer Mermaid over draw.io` (eigenes früheres Kit-Ruling), `je <=150 Zeilen` (eigene frühere
> Zeilengrenze), `Derived 1:1 from … v1.11` (Kopfzeile des eigenen V1-Ablageplans) — Artefakte dieses
> Repos, die keine Zeile hier mehr trägt.
>
> **Urteil: OFFEN.** Ein Zitat zurückgezogenen Textes liest sich genau wie ein falsch abgeschriebenes;
> das zu trennen braucht die Paarung Regel↔Abschnitt, also eine Lesart.
>
> **Was stattdessen begrenzt:** die Konvention gilt in den Nachträgen, dort sind alle sieben Zitate
> geprüft, und der Test fällt, wenn die Nachträge fast keine Zitate mehr tragen.
