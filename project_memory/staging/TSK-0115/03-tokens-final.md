# 03-final — Das Blatt für Phase 2: E (Modern, Fläche) plus Layoutregeln

Werte stehen genau einmal, im Code: `directions.M_TOKENS_LIGHT`, `M_TOKENS_DARK`, `M_FONTS`, `M_RULES`,
`E_RULES` und die Basis in `make_mockups.STYLE`/`NOSCRIPT_STYLE`/`SCRIPT`. Phase 2 trägt sie nach
`kernel/board.py` (`_STYLE`, `_NOSCRIPT_STYLE`, `_SCRIPT`); danach ist **das** der eine Ort. Dieses Blatt
trägt Namen, Rolle, Grund — und die Regeln, die Phase 1d dazu gemessen hat. Der Nutzer hat E gewählt
(Phase 1d); Kontraste: `contrast-result.md`, Abschnitt E.

## Token (E, unverändert aus `03-tokens-e.md`)

| Token | Rolle | Grund |
|---|---|---|
| `--board` | ruhiger Neutralgrund, hell `#f5f5f7` / dunkel `#0f1115` | Produktoberfläche von heute; der dunkle Modus ist ein echter |
| `--card` | Karte, Fokus-Liste, Akte, Baumknoten — `#ffffff` / `#171a1f` | eine Karte ist eine Zeile mit Kante (Haarlinie, kein Schatten) |
| `--slot` | leere Zahl oben, Records-Grund — `#ebecef` / `#1b1e24` | eine Stufe vom Grund |
| `--ink`, `--ink-2` | Text, Reiter-Unterstrich, Fokusring, Links, Falt-Knopf | Tinte trägt alles Chrom; **kein Akzent für Klickbares** |
| `--rule` | Haarlinien — `#e2e4e8` / `#2a2f37` | Kartenrand, Reiterlinie, Trennlinien |
| `--stop`, `--stop-ink`, `--stop-text`, `--stop-tint` | **blockiert**: Feld `#d92d20` mit Weiß; als Text `#b42318` / `#f97066`; Tönung `#fee4e2` / `#3a1715` | Rot heißt hängt — Konvention, Wert neu |
| `--you`, `--you-ink`, `--you-text`, `--you-tint` | **wartet auf dich**: Feld `#b54708` mit Weiß; Text `#b54708` / `#fdb022`; Tönung `#fef0c7` / `#3a2810` | Bernstein statt Gelb: trägt weiße Schrift bei 5,4:1 |
| `--go`, `--go-ink`, `--go-text`, `--go-tint` | **in flight**: Feld `#107569` mit Weiß; Text `#107569` / `#2ed3b7`; Tönung ungenutzt | Petrol — kein Blau (Finanz-Stempel), kein Violett (altes Template) |
| `--font-display` | `h1`, `h2`, die drei Zahlen | `Segoe UI Variable Display` / `Inter` / `SF Pro Display`, Laufweite −0,02/−0,03 em |
| `--font-body`, `--font-mono` | alles andere, auch Ids (Tabellenziffern, Gewicht 500) | `Segoe UI Variable Text` / `Inter` / `SF Pro Text`; **keine Festbreite** |
| Radius | 4 px (Karte, Zahl, Akte, Falt-Knopf), 3 px (Etikett, Badge), 0 (Reiter) | minimal und begründet — die Kante einer Zeile |
| Schatten, Verlauf, Pill | keine | — |

## Charakter E

Die drei Zahlen oben sind volle Farbfelder mit weißer Schrift; eine Null ist ein graues Feld mit
gedämpfter Zahl. Eine blockierte oder wartende Karte ist **getönt** (`--*-tint`), Rand in der
Signalfarbe, die Flagge ein kleines gefülltes Etikett (3 px Radius, rechteckig). Alles andere ist neutral:
Farbe ist Signal, nie Dekor. Fokus-Listen: Zeilen in der Tönung, Id in `--*-text`.

## Layoutregeln (Phase 1d, gemessen)

| Regel | Wert | Messung |
|---|---|---|
| Box-Modell nach `all: unset` | `box-sizing: border-box` auf `.card`, `.figure`, `.rec`, `.node-face`, `.ms-face`, `.fold`, `.tree-tools button` | vorher 110 überlappende Kartenpaare bei 1280/1920, 333 bei 390; nachher 0 (`layout-before/after.md`) |
| Slot mit Karten | `flex: 1 1 15rem; min-width: 15rem` | rechter Rand der Tafel: vorher 115 px (1280) / 752 px (1920) leer, nachher 0 |
| leerer Kettenslot | `flex: 0 0 7rem; min-width: 0` | bleibt schmal, die Kette bleibt lesbar |
| gestapelt (≤ 720 px) | `.slot { flex: 0 0 auto; width: 100% }` | vorher 327 vertikale Überlappungen bei 390, nachher 0 |
| Slot-Kopf | Name und Zahl nebeneinander (`justify-content: flex-start; gap: .4rem`) | die Zahl stand sonst neben dem Kopf der nächsten Spalte |
| Zeilen mit mehr Slots, als passen | `overflow-x: auto` bleibt | keine scrollende Zeile auf den Fixtures; auf einer breiten TSK-Kette scrollt sie |
| Falt-Knopf | `1.7rem × 1.9rem`, Pfeil ▾/▸ aus `aria-expanded`, `:focus-visible` 2 px Tinte | `healthy-system-1280-keyboard-open.png` |
| Standard der Bäume | Wurzeln offen, Gruppen ab Tiefe 1 zu (`FOLD_DEPTH = 1`); „Expand all"/„Collapse all" je Sicht | `healthy-system-1280.png`, `-expanded`, `-collapsed` |
| Lineal der Zeitleiste | drei Bänder: Heute oben allein, Marken unten/mitte im Wechsel unter 9 % Abstand; Höhe 4,2 rem | vorher 1 Überlappung bei 390, nachher 0 |
| Seitenbreite | keine `max-width` an Tafel oder Zahlen; Fließtext (`.meta`, `.lead`) bleibt auf 62 rem | `blocked-board-1920.png`, `empty-board-1920.png` |

## Was dieses Blatt nicht behauptet

- Drei der sieben Finanz-Token bleiben in der Klasse (Textschriftfamilie, heller Neutralgrund, Tinte) —
  benannt in `07-modern.md`.
- Die Schriftstapel sind auf diesem Windows-11-Host gesichtet (Segoe UI Variable); anderswo greift der
  nächste Name des Stapels, ungesichtet.
- Keine `page.on("request")`-Messung; die Seite lädt keine externe Ressource (Systemschriften, Inline-Skript)
  — Phase 2 misst es wie TSK-0079.
