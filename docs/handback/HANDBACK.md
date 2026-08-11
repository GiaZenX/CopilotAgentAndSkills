# Deine Schlussrunde — was du selbst einspielst, in einfacher Sprache

Manche Reparaturen betreffen die **Sicherheitsregeln des Systems selbst**. Die darf das System aus
gutem Grund nicht von innen ändern (sonst könnte es seine eigenen Schutzregeln abschalten). Deshalb
sind sie hier als fertige Pakete vorbereitet — **du spielst sie mit wenigen Befehlen ein.** Alles
wurde gebaut UND von einem zweiten, unabhängigen Prüfer nachgemessen (kein neues Loch, keine
Regression, 146 Tests grün).

**Wann:** Am besten ganz am Ende, wenn alle automatischen Reparaturen durch sind — dann in einem
Rutsch. Es eilt nichts.

**Wo:** In einem normalen Terminal (PowerShell oder Git Bash) im Projektordner
`C:\Offline Repos\AgentAndSkills` — NICHT aus Claude Code heraus (von innen sperrt der Wächter
genau diese Änderungen).

---

## Schritt 1 — Die zwei Reparatur-Pakete einspielen

```
cd "C:\Offline Repos\AgentAndSkills"
git apply -p1 "docs\handback\gate-fixes.patch"
git apply -p1 "docs\handback\ci-gate-suite.patch"
```

Falls `git apply` wegen Zeilenumbrüchen meckert (die Dateien haben gemischte Zeilenenden), nimm:
```
git apply -p1 --ignore-whitespace "docs\handback\gate-fixes.patch"
```

**Was die Pakete reparieren, einfach gesagt:**
- **`gate-fixes.patch`** behebt zwei Dinge:
  1. Der Wächter war *übervorsichtig* — er hat sogar harmlose Befehle blockiert, nur weil sie in
     einer Schleife standen oder einen geschützten Ordnernamen erwähnten. Das hat die Arbeit
     ständig ausgebremst (das war „was mich blockiert hat"). Jetzt lässt er Harmloses durch und
     stoppt trotzdem alles Gefährliche. (Fehler **BUG-0012**)
  2. Ein interner Selbsttest hatte auf diesem Rechner still versagt, ohne dass es jemand merkte —
     er hat sich seine Prüf-Umgebung falsch ausgesucht. Jetzt sucht er sie richtig. (Fehler
     **BUG-0014**)
- **`ci-gate-suite.patch`** sorgt dafür, dass diese Selbsttests künftig **automatisch mitlaufen**,
  damit so ein stilles Versagen sofort auffällt.

## Schritt 2 — Die gelöschte Datei zurückholen

Heute Nacht ist durch das „Löschloch" eine wichtige Datei verschwunden (**DEC-0001**, eine
Entscheidungs-Notiz). Nichts ist endgültig weg — das Projekt hat sie in seiner Historie. Ein Befehl
holt sie zurück:

```
git checkout c188d5f -- "project_memory\decisions\active\DEC-0001.yaml"
```

## Schritt 3 — Neu starten

Danach Claude Code **neu starten** (Fenster schließen und neu öffnen). Erst dann greifen die
geänderten Sicherheitsregeln. Ohne Neustart läuft die alte Fassung weiter.

---

## Nur zur Info (du musst nichts tun)

Beim Reparieren kam heraus, dass zwei Fehler-Beschreibungen die **falsche Ursache** nannten — die
Reparaturen sind trotzdem richtig, nur die ursprüngliche Vermutung stimmte nicht:
- **BUG-0012** beschrieb eine Ursache, die längst behoben war; das echte Problem war die
  Übervorsicht bei Schleifen.
- **BUG-0020** vermutete, das Löschen sei gar nicht geschützt — in Wahrheit ist es geschützt, nur
  ein Trick mit Anführungszeichen hebelte es aus (genau das „Löschloch"). Das eigentliche Loch wird
  **automatisch** im System repariert (Fehler-Nr. **TSK-0043**), nicht hier von dir.

Fehler-Beschreibungen sind fest gespeichert und können nicht nachträglich geändert werden — deshalb
steht die Korrektur hier statt in den Fehlern selbst.
