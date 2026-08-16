# TSK-0067 / FR-0006 — `update-kit`: die Messungen

Alles hier ist gegen ein **echt gescaffoldetes Projekt ausserhalb dieses Repos** gemessen
(`<scratch>/m1/project`, Kit `dev-team`, Windows/PowerShell-Zwilling des Scaffolds, Python 3.13).
Aufbau: eine Ablage `~/.claude/team-kits` mit dem Kit auf `2026.07.01-1`, damit gescaffoldet, danach
die Ablage gegen `2026.08.16-9` getauscht — der Zustand eines Projekts, dessen Maschine eine neuere
Harness bekommen hat.

## 1. Was ein Kit-Update VOR dieser Runde gekostet hat

| Was | Ergebnis |
|---|---|
| SessionStart-Briefing (`session_status.py`, echter Prozess) | „KIT UPDATE AVAILABLE … **ASK THE USER TO RUN** the scaffold_team script and then init_project_memory … **You cannot run either yourself**" |
| `powershell … scaffold_team.ps1 -Team dev-team` durch `gate_write_scope` | **rc 2** — „names the enforcement layer in a pipeline that can write" |
| `bash "$HOME/.claude/team-kits/scaffold_team.sh" dev-team` | **rc 2**, gleiche Begründung |
| `python scripts/harness.py doctor` | rc 0 (Vergleichsfall: eine Zeile, die nichts schreibt) |

Das ist genau die Sackgasse von BUG-0041 in der grösseren Variante: die einzige Route führte über
eine Person mit einem Terminal.

**Was ein Re-Scaffold über ein LEBENDES Projekt bewegt** (Snapshot-Diff über alle Dateien,
`__pycache__`/`backups` ausgenommen):

* `.claude/`: **+2** (`HANDOVER_PENDING`, `kit_updated_from`), **−1** (der Hook, den das neue Kit
  nicht mehr ausliefert, wird geprunt), **~3** (`hooks/ENFORCEMENT.md`, `kit_state.json`,
  `kit_version`);
* `.codex/hooks.json` neu erzeugt;
* **`project_memory/`: 0 Änderungen** — die Zusage, die bisher nur in Prosa stand, ist gemessen.

## 2. Das Abbruchfenster des Scaffolds (die B4-Messung)

Vollständiger Lauf: **3,3–4,0 s**. Der Lauf wurde bei wachsendem Budget getötet und danach der
Projektzustand gelesen (Stempel, aufgezeichneter Bundle-Hash, gemessener Bundle-Hash, Marker):

| Budget | Stempel | Bundle auf Platte | `kit_state.json` | Marker |
|---|---|---|---|---|
| ≤ 1,2 s | alt | alt | passt | fehlt |
| **1,6 s** | **alt** | **neu** | **alt → Vertrauen entzogen** | fehlt |
| 2,4–3,4 s | neu | neu | neu | **fehlt** |
| voller Lauf | neu | neu | neu | vorhanden |

Zwei Fenster, zwei verschiedene Unehrlichkeiten:

1. **1,6 s** — wer nur `.claude/kit_version` liest, meldet „nichts installiert", während die
   gesamte Durchsetzungsschicht schon ausgetauscht ist und jedes kernel-gestützte Gate wegen des
   veralteten Vertrauensdatensatzes verweigert. Deshalb liest `kitupdate._installed_state` **zwei**
   Leser: den Stempel und das Bundle (`_bundle_reading`: „staged" / „recorded" / „neither" /
   „unreadable").
2. **2,4–3,4 s** — das Update ist materiell fertig, der Marker fehlt, die Sitzung wird von nichts
   gestoppt. Deshalb stellt `_ensure_restart_is_forced` den Marker selbst sicher und liest ihn
   zurück, statt ihn vom Glück des Installers zu erben.

**Nebenmessung mit derselben Ursache:** `.claude/kernel/hashing.py` ist während des Laufs **5 ms
lang abwesend** (ab 1,58 s), weil der Scaffold `.claude/kernel` löscht und neu kopiert. Der Prozess,
der `update-kit` ausführt, läuft aus genau diesem Verzeichnis — deshalb importiert `kitupdate.py`
alles auf Modulebene: ein Import NACH dem Start des Installers ist ein Import aus einem Baum, den
der Installer gerade ersetzt.

`kernel.hashing.kit_hash` über die drei ausgelieferten Kits: **17–25 ms** — der Grund, warum die
Selbstprüfung der Ablage vor den ersten bewegten Byte passt statt ans Ende des Scaffolds.

## 3. Nach dem Fix — dieselbe Umgebung, echter Einstiegspunkt, echter Freigabe-Hook

| Fall | Ergebnis |
|---|---|
| `request-approval kit_update` → Nutzer antwortet → `update-kit` | rc 0, `.claude/kit_version` `2026.07.01-1 → 2026.08.16-9`, Marker gesetzt |
| ohne Freigabe | rc 1, Stempel unverändert |
| ältere Ablage (Downgrade) | rc 1 bei der FRAGE und beim Befehl, Installer nicht gestartet |
| Freigabe für A→B, Ablage wird C | rc 1 („no user approval"), Stempel unverändert |
| Marker liegt schon | rc 1 („already waiting for a session restart") |
| Budget 1,6 s (echter Scaffold) | Refusal nennt beide Lesungen: `[stamp 2026.07.01-1, bundle = recorded]` → nach dem vervollständigenden Lauf `[stamp 2026.07.01-1, bundle = STAGED kit's]`, Marker von diesem Befehl geschrieben |
| Budget 2,6 s | dasselbe, danach `[stamp 2026.08.16-9, bundle = STAGED kit's]` |

**Stoppt der Marker die Sitzung?** Beide Leser als echte Prozesse gegen das aktualisierte Projekt:

| Aufruf | mit Marker | nach dem Neustart (Marker weg) |
|---|---|---|
| `gate_dispatch.py`, Task-Spawn | **rc 2**, „…HANDOVER_PENDING exists…" | rc 2 aus anderem Grund (kein Dispatch-Header) — die Marker-Begründung ist weg |
| globaler `handover_guard.py`, Task-Spawn | **rc 2** | rc 0 |
| globaler `handover_guard.py`, `harness.py create-task …` | **rc 2** | rc 0 |

## 3a. Die Prüfrunde: der Fehlschlag, der KEINEN Marker setzen darf (F1)

Gemessen gegen den echten Scaffold mit echter Freigabe und einem **Tippfehler im Preset**
(`preset: sollo`) — eine Ursache, die der PM in derselben Sitzung über den Kernel beheben kann:

| Schritt | Ergebnis |
|---|---|
| 1. `update-kit` über den Tippfehler | **rc 1**, Meldung des Installers durchgereicht, „**no restart marker was set** (.claude/HANDOVER_PENDING does not exist)", Stempel unverändert, **Marker abwesend** |
| 2. `gate_dispatch`-Spawn | rc 2 — aber mit der GEWÖHNLICHEN Begründung (fehlender Dispatch-Header), **nicht** mit der Marker-Begründung |
| 3. zweiter `update-kit` | **rc 1 mit derselben Installer-Meldung** — der Wiederholungsversuch erreicht den Installer, statt als „waiting for a restart" abgewiesen zu werden |
| 4. nach Behebung des Tippfehlers | **rc 0**, Stempel `2026.07.01-1 → 2026.08.16-9`, Marker gesetzt |
| 5. `gate_dispatch`-Spawn danach | rc 2 **mit** der Marker-Begründung |

Vorher (die Fassung dieser Runde): Schritt 1 setzte den Marker, Schritt 2 verweigerte mit „an
installer changed this project's kit files" — von genau dem Befehl als falsch gemessen —, und
Schritt 3 verweigerte den Wiederholungsversuch. Die Sitzung war über einen Tippfehler tot.

## 3b. Was der KIT bei gesetztem Marker wirklich verweigert (F2)

Gemessen: eine `dispatch`-, `capture`- oder `update-kit`-Zeile passiert bei gesetztem Marker **alle
acht** `Bash|PowerShell`-Gates eines Kits mit **rc 0**; nur der **nutzerglobale** Handover-Guard
verweigert sie. Deshalb sagt jede ausgelieferte Stelle jetzt: Spezialisten-Spawns verweigert das
Kit, alles Weitere nur „with the harness's user-global handover guard installed" — WELCHE Stellen
das sind, verwaltet `test_the_scoped_stop_sentence_is_the_one_every_kit_text_carries`, nicht eine
Zahl in diesem Satz (die hier zuvor stehende war schon eine Runde später falsch).

## 4. Rot ohne den Fix

19 Ablationen in einem **Klon ausserhalb des Repos**, je eine Zeile zurückgedreht, danach der
benannte Test — alle 19 **rot**, Baseline vorher grün. Die Liste steht im Bericht zur Aufgabe; die
Ablationen selbst liegen im Scratchpad (`ablate.py`) und sind reproduzierbar.

### Die Regression, die diese Runde selbst erzeugt und wieder geschlossen hat

Nachdem die Ordnung der Versionsstempel in den Kernel gezogen war, hing der Kit-Absatz des
Briefings an einem **erreichbaren** Kernel: in einem Projekt ohne `.claude/kernel` verschwand er
vollständig (gemessen an sieben Suite-Tests, die genau darüber rot wurden). Der Satz, der einem
Lead überhaupt erst sagt, dass es eine neuere Ablage gibt, wäre damit ausgerechnet dort weg, wo der
Kernel beschädigt ist. Korrektur: `_kernel.kit_update_verdict` gibt „unclear" **mit dem Grund**
zurück statt zu schweigen; der Test dazu fährt den Hook ohne erreichbaren Kernel.

## 5. Was NICHT geschlossen ist

* **Ein Repair-Scaffold auf derselben Version** (manipuliertes Bundle, `hooks_trust_required`) hat
  weiterhin keine Route aus der Sitzung: `update-kit` verweigert „already runs the staged release",
  und `gate_dispatch`/`kit_trust_state` verweisen weiter auf den Nutzer. Das ist bewusst — ein
  Befehl, der ein Bundle neu segnet, wäre genau die Selbst-Freigabe, die `write_kit_state.py`
  verhindert.
* **Codex**: `update-kit` startet den Installer als Kind der Sitzung; `.codex/` und
  `.agents/skills/` sind dort schreibgeschützte Harness-Pfade. Diese Kombination ist **nicht
  gemessen**; das Briefing sagt das jetzt so und verweist auf die Meldung des Installers.
* **`gate_write_scope` sieht den Installer nicht**, weil ihn der Kernel-Prozess startet und keine
  Tool-Zeile ihn nennt — dieselbe Eigenschaft, die `set-preset` seit TSK-0064 hat.
