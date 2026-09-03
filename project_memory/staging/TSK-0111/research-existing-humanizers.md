# Recherche: Gibt es schon gute Humanizer-Skills? (TSK-0111, FR-0072)

*Recherche-Datum: 2026-09-02. Read-only-Auftrag; keine Datei außer dieser wurde angefasst.*

**Kurz vorweg, für den Nutzer.** Du hattest gesagt, der Text, der aus unserem Skill kommt, gefällt
dir noch nicht. Diese Recherche beantwortet zwei Fragen: Gibt es im Internet schon einen fertigen
Skill, den wir stattdessen nehmen könnten — und wenn nicht, was genau ist an unserem Nachher-Text
das Problem? Abschnitt 3 und 4 sind die für dich wichtigsten: Abschnitt 3 sagt in Alltagssprache,
was am aktuellen Ergebnis stört, Abschnitt 4 zeigt drei andere Versionen desselben Flaschentexts
zum Vergleichen.

## 1. Bestand: existierende Humanizer-Skills, Stand September 2026

Alle Angaben zu Sternen, Größe und letzter Änderung stammen von der GitHub-API (`gh api
repos/<owner>/<repo>`), abgerufen am 2026-09-02. „Ansatz" unterscheidet **Phrasenliste** (eine
Sammlung verbotener/typischer Wörter und Wendungen), **gemessene Eigenschaften** (Zählungen wie
Satzlängen-Varianz, Gedankenstrich-Dichte) und **Hybrid** (beides gemischt). „Mitten in der Arbeit
anwendbar" heißt: kein Nutzerdialog nötig, ein Agent kann den Skill still auf einen Entwurf
anwenden, den er schon hat — das ist die Bedingung, die unsere Rollen erfüllen müssen, weil sie
keinen Nutzer zum Fragen haben.

| Skill | URL | Lizenz (wörtlich) | Ansatz | Deutsch? | Sterne / Größe | Letzte Änderung | Mitten in der Arbeit anwendbar? |
|---|---|---|---|---|---|---|---|
| blader/humanizer | https://github.com/blader/humanizer | `MIT` (GitHub-API `license.spdx_id`) | Phrasenliste, 35 Muster, explizit „based on Wikipedia's 'Signs of AI writing'" | Nein | 40.064 / 149 KB | 2026-08-19 | Ja |
| harshaneel/humanize | https://github.com/harshaneel/humanize | `MIT` | Hybrid — „nine levers" (Perplexity-Injektion, Burstiness, Hedge-Chirurgie, Interpunktions-Normalisierung u. a.) als Eigenschafts-Rahmen, dahinter Wortlisten | Nein | 410 / 153 KB | 2026-07-10 | Ja |
| Aboudjem/humanizer-skill | https://github.com/Aboudjem/humanizer-skill | `MIT` | Hybrid — 55 Muster + eigenes CLI (`score`), misst u. a. Burstiness als 0–100-Wert | Nein (EN, ZH, JA, ES, FR) | 213 / 3.446 KB | 2026-09-02 | Teilweise — Scan ja, Rewrite braucht eine `--voice`-Angabe |
| jurigis/avoid-ai-writing-multilingual — `SKILL-DE.md` | https://github.com/jurigis/avoid-ai-writing-multilingual | `MIT` (Repo-Klassifizierung der GitHub-API zeigt `NOASSERTION`, der tatsächliche `LICENSE`-Text ist jedoch wortgleicher MIT-Lizenztext — s. Abschnitt 6) | Hybrid — Wortstufen + gemessene Struktur (Satzlängen, Dash-Dichte, Hedge-Stacking) + deutsche Grammatik-Muster (Nominalstil, Kopula-Vermeidung) | **Ja** — eigene Datei `SKILL-DE.md` v2.1.0, eine von fünf Sprachen (DE, RO, IT, FR, SV; ES geplant) | 13 / 93 KB | 2026-08-05 | Ja |
| marmbiz/humanizer-de | https://github.com/marmbiz/humanizer-de | Code `MIT`, Muster-Katalog `CC BY-SA 4.0` (laut eigener `NOTICE`-Datei — s. Abschnitt 6) | Hybrid **plus deterministische Linter-Skripte** (`unicode_lint.py`, `rhythm_lint.py`, `german_pattern_lint.py` u. a.) als Kernmechanismus, nicht nur Prosa-Anleitung | **Ja** — 72 deutsche KI-Tell-Muster, fünf Durchgänge | 133 / 3.895 KB | 2026-09-02 | Ja, aber nur mit Skriptausführung — kein reiner Prosa-Skill |
| theclaymethod/unslop | https://github.com/theclaymethod/unslop | README behauptet „Licensed MIT", **es existiert aber keine `LICENSE`-Datei im Repo** (GitHub-API: 404 auf `/license`) — Lizenz damit ungeklärt | Hybrid — 16 Phrasen-Trigger + 36+ Struktur-Merkmale + „Silhouette"-Scan der Gedankenordnung | Nein — „English only", andere Sprachen bekommen nur eine grobe Erkennung | 328 / 1.086 KB | 2026-08-05 | Nein für Kernfunktionen — `teach` und `calibrate` verlangen ausdrücklich Nutzerfreigabe von Textproben |
| conorbronsdon/avoid-ai-writing | https://github.com/conorbronsdon/avoid-ai-writing | `MIT` | Hybrid — gemessene Eigenschaften + dreistufiger Wortkatalog; Ursprungs-Repo, aus dem `jurigis` seine mehrsprachige Fassung ableitet | Nein | 3.970 / 611 KB | 2026-08-30 | Teilweise — Stimm- und Kontextprofile (`linkedin`, `investor-email` …) sind zentrales Feature |
| jooray/humanizer | https://github.com/jooray/humanizer | `MIT` | Hybrid, 100+ Muster über sechs Kategorien | Nein (aber Slowakisch/Tschechisch, §45–54) | 44 / 198 KB | 2026-09-01 | Ja — eigener „embedded mode" ausdrücklich für „prose, not ceremony" |
| Iampattanayak/Claude-Humanizer | https://github.com/Iampattanayak/Claude-Humanizer | `MIT` | Phrasenliste, 24 Muster, plus interner Zwei-Pass-Selbstkritik-Durchgang | Nein | 2 / 16 KB | 2026-06-18 | Ja |
| walterwritesai/no-slop-ai-humanizer-rewriter | https://github.com/walterwritesai/no-slop-ai-humanizer-rewriter | Repo-Klassifizierung `NOASSERTION` | nicht inhaltlich geprüft (nur Metadaten; 5 Sterne, 18 KB — sehr kleines Projekt, geringe Priorität) | unbekannt | 5 / 18 KB | 2026-05-26 | unbekannt |

Zusätzlich geprüft und **ohne eigenen Beitrag**: Der offizielle Katalog `anthropics/skills` (17
Skills, Stand der Web-Recherche) enthält nichts zu Schreibstimme/Prosa außer dem
UX-Text-Absatz, den unser `frontend-design`-Skill bereits übernommen hat — das deckt sich mit
dem, was `FR-0072` schon bei der ersten Triage gefunden hatte. Die Marktplätze `LobeHub`,
`Shyft`, `mcpmarket`, `OneAway` und `claudemarketplaces` sind reine Weiterverbreitungs-Seiten für
`blader/humanizer` — keine eigenen Implementierungen, keine zusätzliche Lizenz- oder Sprachlage.

**Der deutsche Befund in einem Satz:** Von zehn geprüften Kandidaten decken **genau zwei** Deutsch
ab (`jurigis`, `marmbiz`), beide klein (13 bzw. 133 Sterne) gegenüber den großen englischen
Projekten (`blader` 40.064, `conorbronsdon` 3.970 Sterne). Niemand außer `jurigis` — und dort nur
in der Quellen-Unterdatei `sources/DE-sources.md`, nicht im eigentlichen `SKILL-DE.md` — zitiert
die einschlägige Forschung (Schaaff/Schlippe/Mindner, ICNLSP 2023, „Classification of Human- and
AI-Generated Texts for English, French, German, and Spanish", IU International University of
Applied Sciences — bestätigt per Zitat-Prüfung). `marmbiz` stützt seine 72 Muster stattdessen auf
kommerzielle Marketing-Analysefirmen (ContentConsultants, mindtwo, Ströer, ki-im-marketing.at,
Eology) als „bestätigt durch" — keine akademische Quelle.

## 2. Vergleich mit unserem Skill

**Was der Feld-Befund bestätigt, was FR-0072 schon vermutet hatte:** Fast jeder externe Skill mit
nennenswerter Verbreitung (`Aboudjem`, `conorbronsdon`, `unslop`) baut auf einem Dialog mit einem
Nutzer, der da ist und antwortet — eine Stimme wählen, eine Textprobe zum Lernen freigeben, ein
Kalibrierungs-Spiel spielen. Unsere Rollen haben diesen Nutzer nicht: eine Rolle bekommt einen
Arbeitsauftrag, schreibt den Text, gibt ihn ab — niemand sitzt daneben und beantwortet
Rückfragen. Von den zehn Kandidaten laufen nur `blader`, `harshaneel`, `jurigis`-`SKILL-DE`,
`jooray` und mit Einschränkung `Iampattanayak` und `marmbiz` wirklich ohne diesen Dialog — und
selbst `marmbiz` braucht dafür etwas, das unser Skill absichtlich nicht hat: laufenden Code.

**Der zentrale Unterschied zu `marmbiz/humanizer-de`** (dem einzigen ernstzunehmenden deutschen
Konkurrenten) ist ein Architektur-Entscheid, keine Qualitätsfrage: `marmbiz` führt seine 72 Muster
über fünf Python-Skripte aus (`unicode_lint.py`, `rhythm_lint.py`, `german_pattern_lint.py`,
`register_lint.py`, `evidence_lint.py`) — das ist ein Linter, kein Prosa-Skill. Dieses Projekt hat
sich in `DEC-0056` bewusst dagegen entschieden („ein Prosa-Skill für einen Prosa-Fehler … kein
Linter"). Wer `marmbiz` vollständig übernehmen wollte, würde damit `DEC-0056` widersprechen — das
ist keine Lizenzfrage, sondern eine, die zuerst der Nutzer und die Konstitution entscheiden müssten.

**Was ein externer Skill hat, das unserer nicht hat:**
- **Automatisierte Zählung statt Handzählung.** `marmbiz`s Linter, `Aboudjem`s `score`-CLI und
  `harshaneel`s `ai-check` liefern die Zahlen, die unser Skill von der anwendenden Rolle von Hand
  verlangt („Measure the draft once … write the answers down for yourself"). Das ist der größte
  reale Vorteil der Konkurrenz — und der, den `DEC-0056` bewusst aufgegeben hat.
- **Stimm-/Kalibrierungs-Systeme**, die einen persönlichen Schreibstil aus Textproben lernen
  (`unslop`, `Aboudjem`, `conorbronsdon`). Für unsere Rollen ungeeignet — es gibt niemanden, der
  Proben freigibt.
- **Ein Erkennungs-/Score-Modus** (`Aboudjem` 0–100, `harshaneel`s `ai-check`). Unser Skill lehnt
  das ausdrücklich ab: „It is not a detector … produces no score."
- **Deutlich größere, community-getestete Musterkataloge** (55–150+ Einträge gegenüber unseren 17
  Eigenschaften). Diese Kataloge veralten mit dem nächsten Modell — das ist genau der Grund, den
  unser Skill selbst nennt, warum er keine Liste sein wollte —, sind aber im Moment eine breitere
  Fundgrube an Einzelbeispielen.
- **Sprachlayer über Deutsch hinaus** (Slowakisch/Tschechisch bei `jooray`, Rumänisch/
  Italienisch/Französisch/Schwedisch bei `jurigis`) — falls ein anderes Kit dieses Projekts einmal
  eine weitere Sprache braucht, sind das fertige Vorlagen für die Struktur „eine Sprachdatei pro
  Sprache", nicht für den Inhalt.

**Was unser Skill hat, das keiner der zehn hat:**
- **Zurückhaltung als eigener Grundsatz** — „a short, specific, correct text needs nothing from
  here." Kein externer Skill bremst sich selbst; ihr Geschäftsmodell ist Eingreifen.
- **Einbettung in den Arbeitsauftrag**: der Skill verweist auf die Content-Richtlinie, den
  Design-Entwurf, die Reportvorlage — und die gewinnt, wenn sie etwas anders will. Keiner der
  externen Skills ist für ein System gebaut, in dem eine andere Instanz die Stimme schon
  festgelegt hat.
- **Faktentreue als ausdrücklich erster Grundsatz**, nicht als Nebenfolge einer Stilregel — „it
  does not touch facts … A rewrite that changes what a sentence asserts has left this skill's
  scope." Kein externes README nennt das als eigenen, vorrangigen Programmpunkt.
- **Kein Laufzeit-Code** — geringste Angriffs- und Wartungsfläche, im Gegenzug für mehr Handarbeit
  pro Anwendung.

## 3. Warum das Ergebnis nicht gefallen könnte

Der Nachher-Text ist fachlich korrekt umgesetzt — die Zähltabelle im Vorher/Nachher-Dokument zeigt,
dass alle zehn allgemeinen und alle sieben deutschen Eigenschaften sich in die richtige Richtung
bewegt haben. Trotzdem liest er sich, als Käufer gelesen, nicht wie ein Text, der zum Kaufen
einlädt. Fünf konkrete Eigenschaften, mit Zitat:

1. **Die Reinigungszeile ist keine Prosa mehr, sondern eine Packungsbeilage.** „Deckel in die
   Spülmaschine, die Flasche von Hand." — beide Verben sind weg, der Satz ist eine Stichwortliste,
   keine Aussage mehr. Das ist die konsequente Anwendung der Regeln (G1, G5), liest sich aber wie
   eine Bedienungsanleitung, nicht wie jemand, der einem Freund erklärt, wie man die Flasche
   pflegt.
2. **Der Text hat keinen Anfang und kein Ende mehr, nur eine Mitte.** Er beginnt mit der
   trockensten möglichen Tatsachenaussage („Die Isolierflasche fasst 750 ml.") und hört nach der
   letzten Zahl auf („… und sie wiegt 380 g."). Kein Satz sagt, warum man die Flasche will — nur,
   was sie kann. Ein Produkttext ohne Einladung am Anfang und ohne Fazit am Ende liest sich wie
   eine abgeschnittene Aufzählung.
3. **Fast keine Wärme bleibt übrig.** Von den ursprünglich null Modalpartikeln kam genau eines
   dazu („schon" in „Das reicht schon für einen ganzen Arbeitstag") — das ist der einzige Satz im
   ganzen Text, der noch klingt, als würde jemand zu einem Käufer sprechen. Der Rest ist neutrale
   Aufzählung von Eigenschaften.
4. **Die Kürzung hat nicht nur KI-Ticks entfernt, sondern auch die einzigen Verkaufsargumente.**
   Die gestrichenen Sätze (Opener „ein echter Begleiter für jeden Tag", Closer „leicht, kompakt und
   stilvoll") waren gleichzeitig die einzigen Stellen, an denen der Vorher-Text ein Gefühl oder
   einen Nutzen anstelle einer reinen Eigenschaft benannte. Weil in diesem Text die KI-Ticks und
   die Verkaufssprache in denselben Sätzen steckten, hat das chirurgische Entfernen der Ticks die
   Verkaufssprache gleich mit entfernt — kein Fehler des Skills, aber eine Lücke, die er selbst
   benennt: „it does not know your product: the vocabulary that replaces the predictable one comes
   from the brief and the catalogue" — und für diesen Testtext gab es keinen Katalog, aus dem neue
   Verkaufssprache hätte kommen können.
5. **Aus „bis zu 750 ml" wurde „750 ml"** — eine kleine, aber echte Abweichung vom Vorher-Text (im
   Dokument selbst als Punkt 1 benannt), die zeigt: die Spannen-Auflösung nach Regel G5 setzt
   voraus, dass ein Produktkatalog dahintersteht, der die feste Zahl bestätigt. Ohne Katalog ist das
   eine Zusicherung, die der Vorher-Text so nicht macht.

**Kurz gesagt:** Der Skill hat sein Handwerk richtig gemacht — er hat gemessen, was er messen
sollte, und die Zahlen haben sich bewegt. Was fehlt, ist kein KI-Tell, sondern der Rest eines
Produkttexts: ein Grund zu kaufen, am Anfang und am Ende, in eigenen Worten statt in gestrichenen.

## 4. Drei Fassungen desselben Vorher-Texts

**Wichtig:** Alle drei Fassungen sind **meine eigene Demonstration** für diese Recherche — nicht
das Ergebnis eines Kit-Skills, nicht offiziell. Sie sollen dir beim Vergleichen helfen; du
entscheidest per Geschmack. Ich habe jede Fassung gegen den Vorher-Text geprüft: Kapazität
(bis zu 750 ml), Isolierdauer (bis zu 12 Std. warm / bis zu 24 Std. kalt), die drei Einsatzorte
(Büro, Sport, Reise), Material (Edelstahl 18/8, Deckel BPA-frei mit Silikondichtung),
Reinigungshinweis (Deckel Spülmaschine, Flasche von Hand — als Empfehlung, nicht als Befehl,
außer wo unten anders vermerkt), Durchmesser (7,3 cm, „nahezu jeden gängigen Getränkehalter"),
Gewicht (380 g). Nichts davon wurde erfunden oder ausgelassen; wo eine Unsicherheit im
Vorher-Text stand (die Haltbarkeits-Aussage war ein Hedge, kein fester Fakt), habe ich sie als
Hedge belassen (per „soll") statt sie zu einer festen Zusicherung zu machen.

### (a) Nach den Regeln von harshaneel/humanize — die „neun Hebel"

> Diese Isolierflasche fasst bis zu 750 ml – genug für einen ganzen Arbeitstag, ohne dass sie
> sperrig wirkt. Eine doppelwandige Vakuumisolierung hält Ihre Getränke bis zu 12 Stunden warm und
> bis zu 24 Stunden kalt, im Büro, beim Sport und auf Reisen. Der Korpus besteht aus Edelstahl
> 18/8, der auch intensiver Nutzung standhalten soll. Der Deckel ist BPA-frei, dichtet mit Silikon
> ab, und die Flasche läuft nicht aus – Ihre Tasche bleibt trocken. Den Deckel stellen Sie in die
> Spülmaschine, die Flasche waschen Sie von Hand. Mit 7,3 cm Durchmesser passt sie in nahezu jeden
> gängigen Getränkehalter, bei einem Gewicht von nur 380 g. Klein genug für die Tasche, robust
> genug für den Alltag.

*Was anders ist:* `harshaneel/humanize` erlaubt ausdrücklich einen der neun Hebel „voice and
register" — eine direkte Anrede und einen pointierten Schlusssatz, solange er an schon genannte
Fakten gebunden bleibt. Der letzte Satz („Klein genug … robust genug …") ist dabei absichtlich kein
Zusammenfassungs-Reflex (unsere Eigenschaft 6 würde ihn streichen), sondern eine Zwei-Glied-Pointe,
die ausschließlich schon genannte Fakten (Gewicht/Größe, Material/Isolierung) zuspitzt — kein neues
Versprechen. 114 Wörter.

### (b) „Guter deutscher Shop-Text" nach Wortliga (Verbalstil-Regel)

> Sie füllen bis zu 750 ml ein – das reicht locker für einen ganzen Arbeitstag, ohne dass die
> Flasche sperrig wirkt. Ihre doppelwandige Vakuumisolierung hält Getränke bis zu 12 Stunden warm
> und bis zu 24 Stunden kalt, egal ob im Büro, beim Sport oder auf Reisen. Der Edelstahl 18/8 soll
> auch intensiver Nutzung lange standhalten. Der BPA-freie Deckel mit Silikondichtung schließt
> zuverlässig, Ihre Tasche bleibt trocken. Den Deckel räumen Sie in die Spülmaschine, die Flasche
> spülen Sie von Hand. Mit 7,3 cm Durchmesser passt sie in nahezu jeden gängigen Getränkehalter,
> bei einem Gewicht von nur 380 g trägt sie sich kaum spürbar mit.

*Was anders ist:* Wortliga (`wortliga.de/glossar/verbalstil`) empfiehlt Verbalstil statt
Nominalstil und durchgehende Sie-Anrede als Handlungsträger („Sie füllen ein", „Sie räumen",
„Sie spülen") statt Passiv- oder Funktionsverb-Konstruktionen. Das ist derselbe Zug wie unser G1,
aber konsequenter zu Ende gedacht: nicht nur die KI-typischen Funktionsverben weg, sondern jeder
Satz bekommt den Leser als grammatisches Subjekt, wo es passt. 103 Wörter.

### (c) Unser Skill angewendet, aber ohne die Kürzung

> Diese Isolierflasche ist so gebaut, dass sie durch einen ganzen Tag mitkommt. Ihre doppelwandige
> Vakuumisolierung hält Getränke bis zu 12 Stunden warm und bis zu 24 Stunden kalt – im Büro, beim
> Sport und auf Reisen. Mit einem Fassungsvermögen von bis zu 750 ml reicht sie schon für einen
> ganzen Arbeitstag, und dabei wirkt sie nicht sperrig. Der Korpus besteht aus Edelstahl 18/8; auch
> bei intensiver Nutzung soll das Material lange halten. Der Deckel ist BPA-frei und trägt eine
> Silikondichtung, die zuverlässig abdichtet: Die Flasche läuft nicht aus, und Ihre Tasche bleibt
> trocken. Bei der Reinigung dürfen Sie den Deckel einfach in die Spülmaschine stellen; die Flasche
> selbst waschen Sie besser von Hand. Mit einem Durchmesser von 7,3 cm passt sie außerdem in
> nahezu jeden gängigen Getränkehalter, und mit einem Gewicht von nur 380 g bleibt sie dabei leicht
> und kompakt genug, um sie überallhin mitzunehmen. So haben Sie bei jedem Griff zur Flasche das
> Richtige zur Hand: die passende Temperatur, ein Format, das in den Alltag passt, und ein
> Material, auf das Sie sich verlassen können.

*Was anders ist:* Alle Eigenschaften aus unserem Skill sind angewendet (keine Funktionsverben,
kein Diskursmarker, keine leeren Intensivierer, „bis zu" bei beiden Spannen erhalten, der
Reinigungshinweis bleibt eine Empfehlung — „die Flasche selbst waschen Sie besser von Hand", genau
die Formulierung, die das Vorher/Nachher-Dokument selbst unter Punkt 5 als die faktentreue
Alternative nennt, die der ausgelieferte Nachher-Text nicht gewählt hatte). Was NICHT angewendet
ist: die maximale Kürzung. Sätze werden nicht auf Stichworte zusammengestrichen, sondern bleiben
ganze Sätze mit Verben; der Schluss bindet drei schon genannte Fakten zu einem Satz zusammen statt
zu verschwinden. 177 Wörter — 85 % der Vorher-Länge (209 Wörter), gegenüber 46 % beim
ausgelieferten Nachher-Text (97 Wörter).

## 5. Empfehlung

**Option 1 — externen Skill übernehmen.** MIT erlaubt das bei `jurigis` und (für den Code-Anteil)
bei `marmbiz`. Beide Übernahmen kosten mehr, als sie bringen: `jurigis`s `SKILL-DE.md` trägt zwei
Copyright-Zeilen (Conor Bronsdon + Jürgen Kraus), die bei einer Übernahme mitgeführt werden müssten,
und ihr Ansatz deckt sich inhaltlich weitgehend mit dem, was unser G1–G7 schon hat. `marmbiz`s
72-Muster-Katalog ist als **Muster-Katalog** CC BY-SA 4.0 (laut eigener `NOTICE`-Datei) — eine
Übernahme müsste Wikipedia-Herkunft und Weitergabe-Pflicht mitführen, genau das, was unser Skill
heute bewusst vermeidet (er zitiert zur Orientierung, kopiert aber nichts). Und `marmbiz`s
eigentlicher Mechanismus — fünf Python-Linter als Kernstück — widerspricht `DEC-0056` direkt; eine
Übernahme wäre zuerst eine Entscheidung gegen `DEC-0056`, keine Lizenzfrage. **Aufwand: hoch**
(Zuschreibungspflicht, Grundsatzkonflikt), **Nutzen: gering** (die Eigenschaften sind größtenteils
schon abgedeckt).

**Option 2 — unseren Skill behalten und gezielt ergänzen.** Der in Abschnitt 3 gefundene Fehler ist
eng und benennbar: die Eigenschaften 6 und 9 sagen heute nur „streichen", ohne zu unterscheiden,
ob der gestrichene Satz zufällig der einzige mit einem Kaufgrund war. Eine kurze Ergänzung an genau
dieser Stelle — sinngemäß: „Bevor ein Satz nach Eigenschaft 6 oder 9 gestrichen wird: trägt er als
einziger einen Nutzen oder ein Kaufmotiv aus der Richtlinie? Dann wird er nicht gestrichen, sondern
umgeschrieben — der Tick raus, der Nutzen bleibt." — behebt den gemessenen Fehler, ohne
Lizenzfragen, ohne `DEC-0056` anzutasten. **Aufwand: niedrig.**

**Option 3 — Mischform.** Option 2 plus ein einmaliger Abgleich unserer 17 Eigenschaften gegen die
72 Muster von `marmbiz` und die 42 Muster von `jurigis` — nicht zum Übernehmen, sondern um zu
prüfen, ob eine deutsche KI-Marotte existiert, die keine unserer Eigenschaften als Beispiel nennt
(die Beispiele im Skill sind ausdrücklich Illustration, kein geschlossener Katalog — das erlaubt so
einen Abgleich, ohne die Lizenz der fremden Kataloge zu berühren, solange kein Wortlaut kopiert
wird). **Aufwand: niedrig bis mittel.**

**Meine Empfehlung: Option 3.** Der Feld-Befund bestätigt die ursprüngliche `FR-0072`-Triage
unabhängig: kein externer Skill ist für ein System gebaut, in dem eine Rolle mitten in der Arbeit
schreibt, ohne Nutzer zum Fragen, mit einer Richtlinie, die schon feststeht. Unser Ansatz —
Eigenschaften statt Liste, kein Laufzeit-Code, Zurückhaltung als Grundsatz, Fakten unantastbar — ist
für genau diesen Fall richtig gebaut, und das test-Ergebnis zeigt es: alle 17 Eigenschaften haben
sich korrekt bewegt (siehe Zähltabelle im Vorher/Nachher-Dokument). Das eigentliche Problem ist
nicht „nicht menschlich genug nach fremdem Maßstab", sondern eine Lücke in genau zwei Regeln des
eigenen Skills, die sich in einem Absatz schließen lässt. Einen fremden Mechanismus zu importieren
(Linter, Stimmprofile, Score) würde diese eine Lücke nicht zielgenauer schließen als die
Ein-Absatz-Ergänzung — und würde neue Fragen aufwerfen (Lizenz, `DEC-0056`), die mit dem
eigentlichen Befund nichts zu tun haben.

## 6. Quellen

- `jurigis/avoid-ai-writing-multilingual`, `LICENSE`: „MIT License / Original work: avoid-ai-writing
  (https://github.com/conorbronsdon/avoid-ai-writing) / Copyright (c) Conor Bronsdon /
  Multilingual adaptations: Copyright (c) 2025 Jürgen Kraus" — abgerufen per GitHub-API
  (`repos/jurigis/avoid-ai-writing-multilingual/license`), Base64-dekodiert, 2026-09-02.
- `jurigis/avoid-ai-writing-multilingual`, `sources/DE-sources.md`: zitiert Kristina Schaaff, Tim
  Schlippe, Lorenz Mindner (IU International University of Applied Sciences), „Classification of
  Human- and AI-Generated Texts for English, French, German, and Spanish", ICNLSP 2023 — per
  WebFetch geprüft, 2026-09-02.
- `marmbiz/humanizer-de`, `LICENSE`: MIT-Text, Copyright Martin Moeller (2026) und Siqi Chen (2025,
  für von `blader/humanizer` übernommene Anteile) — per WebFetch geprüft, 2026-09-02.
- `marmbiz/humanizer-de`, `NOTICE`: „Creative Commons Attribution-ShareAlike 4.0 International
  license (CC BY-SA 4.0)" für die von Wikipedia übernommenen Musterbeschreibungen; „All other
  project code and original material use the MIT License unless a specific file states
  otherwise" — per WebFetch geprüft, 2026-09-02.
- `theclaymethod/unslop`, README: „Licensed MIT" — bei fehlender `LICENSE`-Datei (GitHub-API:
  404 auf `/license`, kein `LICENSE` in der Root-Auflistung) — per gh-api und WebFetch geprüft,
  2026-09-02.
- Metadaten (Sterne, Größe, Lizenz-Feld, Datum letzter Push) für alle zehn Repos: `gh api
  repos/<owner>/<repo>`, abgerufen 2026-09-02.
- Inhaltliche Zusammenfassungen der SKILL.md/README-Dateien von `blader/humanizer`,
  `harshaneel/humanize`, `Aboudjem/humanizer-skill`, `jurigis/avoid-ai-writing-multilingual`
  (`SKILL-DE.md`), `marmbiz/humanizer-de`, `theclaymethod/unslop`, `conorbronsdon/avoid-ai-writing`,
  `jooray/humanizer`, `Iampattanayak/Claude-Humanizer`: WebFetch auf die jeweilige `raw.
  githubusercontent.com`- bzw. `github.com`-Seite, 2026-09-02.
- Deutsches Pendant zu „Signs of AI writing": Wikipedia, „Wikipedia:Anzeichen für KI-generierte
  Inhalte", https://de.wikipedia.org/wiki/Wikipedia:Anzeichen_f%C3%BCr_KI-generierte_Inhalte —
  CC BY-SA 4.0 wie das englische Original, per WebSearch gefunden, 2026-09-02.
- Verbalstil-Empfehlung für Fassung (b): Wortliga, „Verbalstil", https://wortliga.de/glossar/
  verbalstil/, per WebSearch gefunden, 2026-09-02.
- Interne Referenzen: `C:\Offline Repos\v2-testbed\_worktrees\g2-humanizer\team-kits\dev-team\
  skills\humanizer\SKILL.md` (unser Skill, Zeilen 35–47 für die Quellen-Zuschreibung);
  `project_memory\staging\TSK-0111\humanizer-before-after.md` (Vorher/Nachher-Paar und Zähltabelle);
  `project_memory\inbox\active\FR-0072.yaml` (ursprünglicher Wunsch und erste Triage).

Weitere im Feld gefundene, aber nicht tabellarisch erfasste Kandidaten (per WebSearch identifiziert,
nicht einzeln inhaltlich geprüft): `walterwritesai/no-slop-ai-humanizer-rewriter` (s. Tabelle).
