# Nachtrag zu FR-0012 — der Auslöser, geschärft

Liegt in `staging/`, weil ein Item unveränderlich ist (`L2`) und dies ein **Vorschlag** ist, kein
Zustand. Wer FR-0012 umsetzt, liest das hier mit.

## Was im Item steht — und warum es so allein nicht trägt

FR-0012 nennt als Auslöser: *„eine Zahl oder ein benannter Schwellwert steht in einer docs-Datei
und in keinem aktiven Item."*

**Gemessen ist das zu breit.** Die Dokumente dieses Repos bestehen zu großen Teilen aus Messwerten:
`2332 bestanden`, `457 geschützte Dateien`, `221 Remedy-Zeichenketten`, `0,47 $ für fünf Züge`.
Keiner davon ist eine Festlegung. Ein Wächter, der bei jedem Messwert anschlägt, wird ignoriert —
und ein ignorierter Wächter ist teurer als keiner, weil er Deckung behauptet.

## Die Hausregel sagt mehr, als das Item zitiert

Vollständig lautet sie (`CLAUDE.md`, Hausregeln):

> „Eine **Zahl** steht an genau einem Ort; **wird sie im Code gebraucht**, steht sie in einem Item
> und der Kommentar verweist."

Der zweite Halbsatz ist der Unterschied, und er ist mechanisch: **eine Festlegung wird später
ausgeführt, ein Messwert nicht.**

## Der geschärfte Auslöser

> Feuere, wenn dasselbe Zahlenliteral **in Prosa** *und* **in etwas, das läuft** vorkommt — und in
> **keinem** aktiven Item.

Gegen die vier Fälle dieses Tages gehalten:

| Zahl | Prosa | laufender Code | Item | feuert |
|---|---|---|---|---|
| `25` (Quotenriegel, der Fehlerfall) | ja | ja (`max_budget_usd`) | **nein** | **ja** |
| `2332` (Suite) | ja | nein | nein | nein |
| `457` (geschützte Menge) | ja | nein | nein | nein |
| `120` (Hook-Frist) | ja | ja (`settings.json`) | ja | nein |

Die Falschmelder-Klasse verschwindet vollständig, weil ein Messwert nie in ausgeführten Code
wandert. Der Auslöser bleibt eine Mengenoperation ohne jedes Textverständnis.

## Die Grenze, vor dem Bauen benannt

**Eine Festlegung ohne Zahl fällt durch.** Zwei echte Entscheidungen dieses Tages standen zuerst in
Prosa und tragen keine Zahl: *„kopieren statt verschieben"* (heute `DEC-0024`) und *„kein
V1-Vergleichslauf"* (heute `DEC-0025`). Dieser Auslöser hätte **beide nicht** gefangen.

Er deckt also die Klasse **bindender Wert**, nicht die Klasse **bindende Regel**. Das ist kein
Einwand gegen ihn, sondern gegen jede Formulierung, die behauptet, er löse FR-0012 ganz. Wer ihn
baut, schreibt diese Grenze in seinen Docstring, sonst entsteht genau die Deckungsbehauptung, gegen
die dieses Repo gebaut ist.

## Was das für die zweite Hälfte heißt

Für die Klasse „bindende Regel ohne Zahl" gibt es nach heutigem Stand **keinen** mechanischen
Auslöser. Die ehrlichen Optionen sind zwei, und beide gehören dem Nutzer:

1. Sie bleibt ungedeckt und wird als solche geführt.
2. Der Leser läuft ohne mechanischen Auslöser über die geänderten `docs/`-Dateien einer Sitzung —
   billig genug bei wenigen Dateien, aber ohne die Begrenzung, die FR-0005 ausdrücklich verlangt
   („ein Modellaufruf je Auftrag ist zu teuer als Pflicht").

Und die Messung, die über beidem steht: **der Nutzer hat beide Fälle gefangen, und das kostete
nichts.** Eine gebaute Vorrichtung muss besser sein als das.

---

# Wer liest — die Rolle existiert bereits (Nachtrag 2026-08-09)

Vorschlag des Nutzers: eine neue Rolle, die einmal lesend über die Schreibvorgänge des
Projektmanagers läuft.

**Gemessen: sie existiert in allen drei Kits als `project-auditor`** und ist in ihrer eigenen
Beschreibung genau das —
*„weekly / event-triggered READ-ONLY reviewer … **stateless by design — fresh eyes every run** …
hands back ONE audit Evidence item per run. Findings bind the PM via §13 (a follow-up item or a
recorded skip)."*

**Kein neuer Agent.** Und ausdrücklich **nicht** `bookkeeper` nennen: den Namen trägt im
office-Kit die Buchhaltung, eine zweite Bedeutung wäre die Drift, gegen die dieses Repo sonst baut.

## Was fehlt, ist die Taktung — nicht die Rolle

Heute: wöchentlich oder ereignisgesteuert, auf einer Freigabe. Gewünscht: nach jedem Schreibvorgang.

Diese Taktung hat **FR-0005 bereits gemessen abgelehnt**: *„ein Modellaufruf je Auftrag ist zu teuer
als Pflicht; der Auslöser begrenzt es auf die Fälle, in denen der Auftrag über seine Anforderungen
hinausgeht."* Der mechanische Auslöser oben ist genau diese Begrenzung — er entscheidet **wann**
gelesen wird.

## Zwei Auflagen, ohne die es Zierde wird

1. **Kein Urteil, ein Artefakt.** Die Ausfallart eines billigen Prüfers ist Abnicken, und ein
   Wächter, der nie widerspricht, ist wertlos — dieselbe Klasse wie ein Test, der nicht scheitern
   kann. Er gibt deshalb nicht „passt/falsch" zurück, sondern: *diese Absätze binden, hier ist je
   der DEC-Rumpf; diese habe ich geprüft und für nicht bindend gehalten.* Beide Enden sichtbar,
   und wer etwas Konkretes vorlegen muss, kann nicht billig abnicken.
2. **Ein Durchgang, und der Widerspruch wird protokolliert.** Der Nutzer nennt die Schleifengefahr
   richtig. Die Antwort der Kits ist besser als „korrigieren und fertig": **Folge-Item ODER
   protokollierter Verzicht.** Das deckt den Fall, den „korrigieren und fertig" offenlässt — dass
   der Prüfer sich irrt und ein Dokument auf einen Fehlbefund hin verschlimmbessert wird.

## Modellstufe

`project-auditor` steht auf `effort: high`, aber er auditiert ein ganzes Projekt gegen eine
Bewertungsmatrix. Für „lies die geänderten Absätze einer Sitzung" ist die Aufgabe eng begrenzt;
eine kleine Stufe reicht, **sofern Auflage 1 gilt**. Ohne sie ist die Stufe die falsche
Stellschraube — nicht der Aufwand entscheidet, sondern ob die Ausgabe widerlegbar ist.

## Zwei Takte in EINER Rolle geht nicht — und der Grund ist nicht das Modell

Vorschlag des Nutzers: derselbe Auditor feuert wöchentlich groß (`lead`/hoch) und nach jedem
Schreibvorgang klein (`worker`/niedrig).

**Gemessen, zwei Korrekturen an der Prämisse:**

1. Der Auditor ist **bereits `model: worker`** — und `team-kits/model_tiers.yaml` bildet
   `worker → sonnet` ab (`lead → opus`, `light → haiku`). „Opus für das Wochenaudit" wäre eine
   **Hochstufung** mit dem Fünffachen des Preises (Preisanker derselben Datei: Opus 15/75 $,
   Sonnet 3/15 $ je 1M) — eine Nutzerentscheidung, keine Fortschreibung.
2. **Der Blocker ist die Zuteilung, nicht die Stufe.** Der Auditor wird laut seiner Definition je
   Lauf auf einer Freigabe zugeteilt (`APR.kind: routine` oder `analysis`), und eine abgelaufene
   oder widerrufene blockiert den Spawn. Ein Check je Schreibvorgang müsste je Schreibvorgang eine
   Freigabe tragen. Das ist nicht teuer, das ist unmöglich.

Dazu formal: eine Rollendefinition trägt genau ein `model:` und ein `effort:`. Zwei Takte wären
zwei Definitionen — über drei Kits gespiegelt.

**Es sind auch zwei verschiedene Aufgaben, nicht eine in zwei Größen:** ganzes Projekt gegen
Matrix mit einem Audit-Evidence-Item als Ausgabe, gegen ein paar Absätze mit DEC-Rümpfen als
Ausgabe.

**Vorschlag: der kleine Check wird keine Rolle, sondern ein Hook auf dem mechanischen Auslöser,
der einen kleinen Leser ruft.** Der SDK-Weg ist am 2026-08-09 gemessen und trägt. Damit entfällt
die Freigabe-Maschinerie, Auslöser und Leser sind ein Mechanismus, und nichts wird dreimal
gespiegelt.

## Vor dem Bauen zu messen: die Asymmetrie Kit ↔ dieses Repo

In einem Kit-Projekt kann der PM `project_memory/` mit Werkzeugen **nicht** beschreiben
(`gate_write_scope`), und der Masterplan hat nach der Installation keinen Schreiber. Die Fläche,
auf der eine Entscheidung in Prosa versickern kann, ist dort deutlich kleiner als hier — dieses
Repo hält `docs/` bewusst frei, und genau dort sind beide gemessenen Fälle passiert.

**Daraus folgt eine Reihenfolge:** erst hier bauen und messen, ob es trägt; erst dann entscheiden,
ob es in die Kits gehört. Dreimal spiegeln, bevor der Nutzen gemessen ist, ist die teuerste
Variante von allen.
