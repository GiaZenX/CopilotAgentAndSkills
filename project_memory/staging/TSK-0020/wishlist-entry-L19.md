# Löcherlisten-Eintrag aus TSK-0020 — noch nicht abgelegt

`docs/POST_V2_WISHLIST.md` war für `TSK-0020` verbotener Bereich (dort schreibt `TSK-0021`). Der
Umsetzer hat den Eintrag fertig formuliert übergeben und **bewusst keinen Stolperdraht gebaut**, um
die Datei zu umgehen — ein Test ohne Eintrag ist genau das, was der Kopplungstest verhindert.

**Einzuarbeiten, sobald `TSK-0021` gelandet ist.** Der genannte Stolperdraht existiert bereits; beim
Einarbeiten muss die Referenz auch in seinen Docstring, sonst bleibt das Paar offen.

---

> ### L19 — Ein V1-Speicher außerhalb der Domäne des Suchlaufs wird benannt und blockiert nicht
>
> **Mechanismus:** der SR-0001-Scan durchsucht die YAML-Dokumente des Zustandsverzeichnisses. Was
> kein YAML-Dokument ist, unter `staging/` oder unter einem gepunkteten Pfad liegt, wird seit
> TSK-0020 von beiden Lesern **benannt** (`migrate.search_coverage`, `report.record_scan_coverage`),
> aber nicht als Befund geführt — also verweigert kein Gate.
>
> **Kette (gemessen 2026-08-07):** Zustand mit gültigem Wurzel-Item + `project_memory/old_procs.yaml.bak`
> mit `PROC-0001` (`status: ACTIVE`) → `validate` druckt `NOT SEARCHED old_procs.yaml.bak: …`,
> `gate_memory_complete` auf `git merge` **rc 0**. Dieselbe Datei als `old_procs.yaml`: rc 2.
>
> **Urteil: OFFEN, nicht schließbar ohne einen neuen Fehlklang.** Ein Befund über diese Klasse wäre
> in jedem Projekt dauerhaft und unauflösbar: das Forschungs-Kit liefert 27 nicht-YAML-Dateien unter
> `project_memory/` aus (`README.md`, `product/masterplan.md`, `reports/assets/**`), Dev und Office je
> zwei. Als `error` ein Merge, den kein Projekt je besteht; als `warning` ein Alarm über einen Zustand,
> den niemand verlassen kann.
>
> **Was stattdessen begrenzt:** die Datei ist nicht mehr stumm — `validate` druckt sie pro Datei mit
> Grund, `doctor` trägt sie unter `record_scan_coverage`, der Trockenlauf der Migration nennt sie unter
> `NOT SEARCHED`. Und der eigentliche SR-0001-Fall (das zurückkopierte Monolith) trägt seinen V1-Namen
> und liegt damit *in* der Domäne; unter dieses Loch fällt nur eine Datei, die jemand zusätzlich
> umbenannt oder verschoben hat.
>
> **Stolperdraht:** `test_migrate.test_the_dry_run_and_the_validator_answer_the_same_about_every_file`
> (letzter Block) — er misst rc 0 und wird rot, sobald der Merge dafür verweigert.

---

## Zwei Nachzüge, die dazugehören

**`L17` zitiert die Validator-Meldung** als `error … NOT SEARCHED for V1 backlog records`. Durch die
Umrahmung dieser Runde steht die Wendung jetzt in der Mitte der Meldung statt am Anfang. Mit den
Auslassungspunkten nicht falsch, aber schief — eine Zeile Nachzug.

**Restfall des Vorlaufs:** eine Datei unter gepunktetem Pfad, die kein YAML-Dokument ist, gilt als
`machinery` — weder durchsucht noch genannt. Das hält `.kernel.lock`, `.audit/hook_events.jsonl` und
ein `.gitkeep` je Item-Verzeichnis aus beiden Berichten; ein dort versteckter V1-Datensatz steht in
keinem. Gemessen in `test_every_file_under_the_state_root_gets_exactly_one_search_verdict`, im
Docstring von `search_coverage` als Restfall hingeschrieben.
