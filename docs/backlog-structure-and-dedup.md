# Backlog-Gliederung und Dubletten-Schutz — Diskussion + Anforderungen

Zwei Wünsche des Nutzers (2026-08-12), erst diskutiert, dann als FR erfasst. Der gemessene
Ist-Zustand: das Backlog hat heute nur die Eltern-Hierarchie (PR → SR → TSK) und ein `class`-Feld;
Dubletten werden nur über die **Id** erkannt (`duplicate-id`), NICHT über den Inhalt.

## 1. Gliederung durch inhaltslose Ordnungsknoten (Azure-DevOps-Vorbild)

**Idee:** reine Gliederungsebenen ohne Inhalt (kein Titel-Body, keine Beschreibung), nur zur
thematischen Blockbildung (z. B. „Frontend", „Backend").
- **Heading** = Parent von Requirements. **Document** = Parent von Headings. Beide inhaltslos.
- Gilt auf **beiden** Backlogs — Produkt (PR) UND System (SR).
- **Über-Fragmentierung vermeiden:** kein Wildwuchs (nicht 1000 Headings / 300 Documents — dann
  sind sie wertlos). Sauber gliedern; ein **neues** Heading nur, wenn ein Requirement thematisch
  wirklich nicht in ein bestehendes passt.
- **Keine Vorlage** vorgeben.

Offene Design-Frage (Recherche): echter inhaltsloser Heading-Knoten als Parent — oder ein
Attribut/Tag (Area-Path-artig) am Requirement? Beides gruppiert; der Knoten ist näher am
Azure-Vorbild, das Attribut ist chirurgischer.

## 2. Dubletten-Schutz für Requirements — ohne Fehlalarm-Flut

**Problem:** Läuft der Kontext eines Agenten über und wird ein schon existierendes Requirement
erneut angefragt, könnte es doppelt angelegt werden (doppelte Implementierung). Heute gibt es
dagegen **keinen** mechanischen Riegel — nur die Id-Dublette wird erkannt, nicht der Inhalt.

**Wichtige Nutzer-Nuance:** Ein harter Riegel würde zu oft fehlfeuern, weil Requirements sich
oft ähneln. Und die **Rollenkette** (PM → Architekt → Umsetzer/Designer/Backend) erkennt eine
echte Dublette ohnehin meist — wir sind also schon ziemlich sicher. Gewünscht ist deshalb nur ein
**weicher Hinweis** auf die nächsten Treffer beim Anlegen („ähnliche gefunden: …, trotzdem
anlegen?"), **kein** harter Block, und nur, wenn er gut greift, ohne bei jedem Anlegen zu nerven.

## Rechercheergebnis (Sonnet-Recherche 2026-08-12, wie andere Werkzeuge es lösen)

### Thema 1 — Gliederung
Azure DevOps trennt **zwei** Achsen: die Work-Item-Hierarchie (Epic → Feature → PBI → Task, jeder
Knoten **inhaltlich** mit Titel/Beschreibung) UND **Area/Iteration Paths** = „Classification Nodes",
eine **inhaltslose Tag-Hierarchie** (ein `TreePath`-Feld, nur Name, kein Content) — aber als
**Attribut** am Item, NICHT als Parent-Knoten im Baum. Jira genauso: Epics (inhaltlich),
**Components** (inhaltslose technische Klassifikation), Labels (flache Tags). GitHub: Milestones,
Labels. **Ergebnis über alle drei:** die inhaltslose Gliederung existiert überall, aber **nirgends
als hierarchischer Parent-Knoten im selben Baum** — immer als Attribut/Tag. Ein echter,
inhaltsloser Parent-Knoten (unser „Heading/Document") ist in den Referenzsystemen NICHT das gewählte
Muster.
- **Über-Fragmentierung:** keine harten Zahlen in der Branche; reguliert über Struktursignale —
  Tiefenlimit **2–3 Ebenen**, das „Sammelbecken-Symptom" (ein Heading, dessen Kinder keinen
  gemeinsamen fachlichen Nenner mehr teilen), und „vertikal statt horizontal schneiden" (nicht nach
  Technik-Schicht gruppieren — das wird zum ziellosen Container).
- **Empfehlung des Rechercheurs für UNSEREN Fall:** ein inhaltsloser **Heading-Knoten als echter
  Parent** (nicht ein Tag/Attribut), weil unser Kernel schon eine echte Parent-Child-Hierarchie hat
  (PR→SR→TSK) — ein Tag wäre ein zweiter, paralleler Mechanismus daneben. ABER: ein inhaltsloser
  Knoten bricht „ein Item = ein Typ, ein Automat" (er hat keinen Lifecycle) und ist ein Sonderfall.
  **Offene Design-Entscheidung fürs Bauen:** Knoten (passt zum Baum, aber Sonderfall) vs. Attribut
  (Branchenstandard, aber zweiter Mechanismus). Gegen Wildwuchs: Tiefenlimit 2–3 + Sammelbecken-Regel
  als Architekten-Richtlinie.

### Thema 2 — Dubletten-Hinweis
**Konsens aller modernen Systeme: weicher Inline-Vorschlag beim Anlegen, KEIN harter Block.**
- **GitHub** (2026): schlägt beim Anlegen bis zu **3** mögliche Duplikate vor, rein informativ.
  **Linear:** LLM-Embeddings, proaktiver Vorschlag, kein Block. **Jira:** nativ NICHTS (seit Jahren
  offener Feature-Request), nur Marketplace-Apps. **ServiceNow:** ML-Ähnlichkeit mit konfigurierbarem
  Schwellenwert (~75 %).
- **Methoden:** TF-IDF + Cosinus (günstig, keine Infrastruktur, aber „einige False Positives") →
  guter Einstieg; Embeddings (besser, aber Vektor-DB/API nötig) als späterer Schritt. Der
  **Schwellenwert** ist der Haupthebel gegen Fehlalarme; **Top-N** (GitHub: 3) statt aller Treffer;
  **nur beim Anlegen**, kein Hintergrund-Abgleich.
- **Empfehlung (deckt sich mit deiner Nuance):** weicher Hinweis nur beim `capture` eines PR/SR,
  Top-3, **konservativer** Schwellenwert (lieber zu wenige als zu viele Treffer — hohe Toleranz für
  False Negatives, weil die Rollenkette das meiste fängt, niedrige Toleranz für nervige False
  Positives), TF-IDF auf Titel + Ziel/Beschreibung zum Start, **kein Block**.

**Quellen:** Microsoft Learn (Area/Iteration Paths, work items), Atlassian (Epics/Components/Labels,
JRASERVER-1633/4951), GitHub Docs + Changelog (Duplicate Detection 2026), Linear (Similar Issues,
Embeddings), ServiceNow (Similarity Framework), Stack-Overflow-/Near-Duplicate-Forschung. Volle
URLs im Recherchebericht (Task aa356771).
