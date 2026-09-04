"""WCAG 2.x contrast ratios for the text/background pairs each direction puts on the page.

The pairs are read from the SAME token strings the mockups are built from (directions.py), so a
value changed there is measured here without a second list of hex numbers. A row states the
context, the ratio, and whether it meets 4.5:1 (normal text) or 3:1 (large text)."""
import re

import directions


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def lum(rgb):
    def ch(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg, bg):
    a, b = lum(hex_to_rgb(fg)), lum(hex_to_rgb(bg))
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def tokens(block):
    """({name: hex} light, {name: hex} dark) of one token string."""
    light_src, dark_src = block.split("@media (prefers-color-scheme: dark)")

    def read(src):
        return dict((m.group(1), m.group(2)) for m in re.finditer(r"--([a-z0-9-]+):\s*(#[0-9a-fA-F]{6})", src))
    return read(light_src), read(dark_src)


# (label, foreground token or literal or "light|dark" literals, background token, large text?)
PAIRS = {
    "a": [("text on the board", "ink", "board", False), ("muted text on the board", "ink-2", "board", False),
          ("title on a card", "card-ink", "card", False), ("muted on a card", "card-ink-2", "card", False),
          ("id on a card head", "card-ink", "card-head", False),
          ("title on a blocked card", "card-ink", "card-stop", False),
          ("white on a blocked head", "#ffffff", "head-stop", False),
          ("title on a your-turn card", "card-ink", "card-you", False),
          ("head of a your-turn card", "#ffffff|#241d14", "head-you", False),
          ("the red number", "stop", "board", True), ("the yellow number", "you", "board", True),
          ("id in the blocked list (light: head colour, dark: number colour)", "head-stop|stop", "card", False),
          ("id in the your-turn list (light: head colour, dark: number colour)", "head-you|you", "card", False)],
    "b": [("ink on paper", "ink", "board", False), ("muted ink on paper", "ink-2", "board", False),
          ("white on red pencil", "stop-ink", "stop", False), ("black on revision ochre", "you-ink", "you", False),
          ("the red number", "stop", "board", True),
          ("the ochre number (light: #8a5a00 override)", "#8a5a00|#f2c14e", "board", True)],
    "c": [("text on the wall", "ink", "board", False), ("muted text on the wall", "ink-2", "board", False),
          ("text on a panel", "ink", "card", False), ("muted text on a panel", "ink-2", "card", False),
          ("white on the stop field", "stop-ink", "stop", False), ("black on the caution field", "you-ink", "you", False),
          ("white on the go field", "go-ink", "go", False),
          ("slot header: wall colour on ink", "board", "ink", False)],
    "d": [("text on the ground", "ink", "board", False), ("muted text on the ground", "ink-2", "board", False),
          ("text on a card", "ink", "card", False), ("muted text on a card", "ink-2", "card", False),
          ("blocked as text (number, flag, list id)", "stop-text", "card", False),
          ("waiting-on-you as text", "you-text", "card", False), ("in-flight as text", "go-text", "card", False),
          ("the blocked number on the ground", "stop-text", "board", True),
          ("the amber number on the ground", "you-text", "board", True), ("the teal number on the ground", "go-text", "board", True)],
    "e": [("text on the ground", "ink", "board", False), ("muted text on the ground", "ink-2", "board", False),
          ("white on the blocked field", "stop-ink", "stop", False), ("white on the amber field", "you-ink", "you", False),
          ("white on the teal field", "go-ink", "go", False),
          ("blocked text on its tint", "stop-text", "stop-tint", False), ("amber text on its tint", "you-text", "you-tint", False),
          ("teal text on its tint", "go-text", "go-tint", False), ("ink on a tinted card", "ink", "stop-tint", False),
          ("ink on the amber tint", "ink", "you-tint", False)],
}


def main():
    for key, (name, block, _rules) in directions.DIRECTIONS.items():
        light, dark = tokens(block)
        print("\n### %s\n" % name)
        print("| Paar | hell | dunkel | Schwelle |")
        print("|---|---|---|---|")
        for label, fg, bg, large in PAIRS[key]:
            need = 3.0 if large else 4.5
            cells = []
            for mode, tok in (("light", light), ("dark", dark)):
                fg_val = fg.split("|")[0 if mode == "light" else 1] if "|" in fg else fg
                fg_hex = fg_val if fg_val.startswith("#") else tok[fg_val]
                bg_hex = bg if bg.startswith("#") else tok[bg]
                r = ratio(fg_hex, bg_hex)
                cells.append("%.1f:1 %s" % (r, "ok" if r >= need else "**zu wenig**"))
            print("| %s | %s | %s | %s |" % (label, cells[0], cells[1], "3:1 (groß)" if large else "4.5:1"))


if __name__ == "__main__":
    main()
