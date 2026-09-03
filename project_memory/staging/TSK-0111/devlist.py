# -*- coding: utf-8 -*-
"""Rechnet nach, dass die Abweichungstabelle in `humanizer-before-after.md` vollstaendig ist.

Das Dokument behauptet, seine Tabelle zerlege die Vorlage vollstaendig und stelle jedem Abschnitt
seinen Platz in der Nachher-Fassung gegenueber. Genau das wird hier gemessen, und zwar an dem
Dokument selbst -- die Vorlage, die Nachher-Fassung und die Tabelle werden alle drei aus derselben
Datei gelesen, damit die Pruefung das liest, was der Nutzer liest.

Rot wird das Skript bei:
  * einer Zelle, die im zugehoerigen Text nicht woertlich (und ueberschneidungsfrei) vorkommt,
  * einem Zeichen der Vorlage oder der Nachher-Fassung, das in keiner Zelle steht,
  * einem Wert in der Spalte "Art", der nicht "unveraendert", "Abweichung -> n" oder
    "gestrichen -> n" ist, oder der nicht zur Nachher-Zelle passt,
  * einem Verweis auf einen nummerierten Punkt, den es nicht gibt,
  * einem nummerierten Punkt, den keine Zeile nennt (die Gegenrichtung: ein toter Eintrag).

Was das Skript NICHT entscheidet: ob das Urteil in der Spalte "Art" stimmt. Das liest der Nutzer
an den beiden Zellen nebeneinander ab; dafuer stehen sie nebeneinander.

Aufruf:  python devlist.py [pfad/zu/humanizer-before-after.md]
"""
import io
import os
import re
import sys

STRUCK = "(nichts)"
DOC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "humanizer-before-after.md")


def _blockquote(lines, heading, stop):
    """Der Text eines Zitatblocks unter einer Ueberschrift, zu einer Zeile zusammengezogen."""
    start = next(i for i, line in enumerate(lines) if line.startswith(heading))
    end = next((i for i, line in enumerate(lines[start + 1:], start + 1) if line.startswith(stop)),
               len(lines))
    body = [line[1:].strip() for line in lines[start:end] if line.startswith(">")]
    return re.sub(r"\s+", " ", " ".join(body)).strip()


def _rows(lines):
    """Die Zeilen der Abweichungstabelle: (Nr., Vorlage, Nachher, Art)."""
    head = next(i for i, line in enumerate(lines)
                if line.startswith("| Nr. | Vorlage | Nachher | Art |"))
    out = []
    for line in lines[head + 2:]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 4:
            out.append(cells)
    return out


def _points(text):
    """{Nummer: erste Zeile des Punktes} der nummerierten Liste unter der Tabelle."""
    return {int(number): line
            for number, line in re.findall(r"^(\d+)\. (.+)$", text, re.M)}


def _cover(text, fragments, label, problems):
    """Legt jede Zelle ueberschneidungsfrei auf den Text und meldet, was uebrig bleibt."""
    mask = [False] * len(text)
    for number, fragment in fragments:
        if not fragment:
            continue
        start, placed = 0, False
        while True:
            at = text.find(fragment, start)
            if at < 0:
                break
            if not any(mask[at:at + len(fragment)]):
                for index in range(at, at + len(fragment)):
                    mask[index] = True
                placed = True
                break
            start = at + 1
        if not placed:
            problems.append("Zeile %s: die %s-Zelle steht so nicht (mehr) im Text: %r"
                            % (number, label, fragment))
    left = [(index, char) for index, (char, seen) in enumerate(zip(text, mask))
            if not seen and not char.isspace()]
    if left:
        gaps, run = [], ""
        last = None
        for index, char in left:
            if last is not None and index != last + 1:
                gaps.append(run)
                run = ""
            run += char
            last = index
        gaps.append(run)
        problems.append("%s: %d Zeichen stehen in keiner Zelle -- %s"
                        % (label, len(left), " | ".join(gaps)))
    return mask


def main():
    raw = io.open(DOC, encoding="utf-8").read()
    lines = raw.split("\n")
    before = _blockquote(lines, "## Vorher", "## Nachher")
    after = _blockquote(lines, "## Nachher", "---")
    rows = _rows(lines)
    points = _points(raw[raw.index("| Nr. | Vorlage | Nachher | Art |"):])
    problems = []

    if [row[0] for row in rows] != [str(n) for n in range(1, len(rows) + 1)]:
        problems.append("die Nummern der Tabelle laufen nicht 1..%d durch" % len(rows))

    named = set()
    for number, vorlage, nachher, art in rows:
        if art == "unverändert":
            kind, refs = "unverändert", []
        else:
            found = re.match(r"^(Abweichung|gestrichen) → ([\d, ]+)$", art)
            if not found:
                problems.append("Zeile %s: die Art %r ist keiner der drei Werte" % (number, art))
                continue
            kind, refs = found.group(1), [int(x) for x in re.findall(r"\d+", found.group(2))]
        if (nachher == STRUCK) != (kind == "gestrichen"):
            problems.append("Zeile %s: Art %r und Nachher-Zelle %r passen nicht zusammen"
                            % (number, art, nachher))
        for ref in refs:
            named.add(ref)
            if ref not in points:
                problems.append("Zeile %s verweist auf Punkt %d, den es nicht gibt" % (number, ref))
    for number in sorted(set(points) - named):
        problems.append("Punkt %d nennt keine Zeile -- toter Eintrag" % number)

    _cover(before, [(row[0], row[1]) for row in rows], "Vorlage", problems)
    _cover(after, [(row[0], "" if row[2] == STRUCK else row[2]) for row in rows], "Nachher",
           problems)

    # Der Bericht, den das Dokument zusagt: jedes Wort der Vorlage, das die Nachher-Fassung nicht
    # fuehrt, mit der Zeile, in der es steht. Die Zeile ist durch die Deckung oben eindeutig.
    def words(text):
        return [w for w in re.findall(r"[^\W\d_]+[\w/,.-]*|\d[\w/,.-]*", text.lower()) if w]

    carried = set(words(after))
    row_of, pots = {}, {}
    for number, vorlage, _nachher, art in rows:
        for word in words(vorlage):
            row_of.setdefault(word, (number, art))
    lost = [w for w in words(before) if w not in carried]
    without = [w for w in lost if w not in row_of]
    for word in lost:
        art = row_of.get(word, (None, "OHNE ZEILE"))[1]
        pots[art.split(" → ")[0]] = pots.get(art.split(" → ")[0], 0) + 1

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("Dokument      : %s" % DOC)
    print("Tabellenzeilen: %d, nummerierte Punkte: %d" % (len(rows), len(points)))
    print("Wortmarken (Buchstaben-/Ziffernfolgen, nicht die Whitespace-Token der Zaehltabelle):"
          " Vorlage %d / Nachher %d; in der Vorlage und nicht im Nachher-Text: %d"
          % (len(words(before)), len(words(after)), len(lost)))
    print("davon nach Topf: %s" % ", ".join("%s %d" % (k, v) for k, v in sorted(pots.items())))
    print("ohne Zeile: %d %s" % (len(without), without if without else ""))
    if problems:
        print("\nROT (%d):" % len(problems))
        for problem in problems:
            print("  * %s" % problem)
        return 1
    print("\nGRUEN: die Tabelle enthaelt beide Fassungen vollstaendig, jede Art ist einer der drei"
          " Werte, jeder Verweis loest auf, und jeder Punkt wird genannt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
