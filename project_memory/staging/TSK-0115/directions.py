"""Three visual directions for the board (TSK-0115 phase 1b, DEC-0065 (6)).

The MARKUP of make_mockups.py is untouched: every direction is the phase-1 layout CSS with its
`:root` token block, its dark block and a short set of character rules swapped in. What the three
share is the structure; what they must not share -- with each other, with the finance dashboard of
TSK-0109 and with the AI default look -- is measured in contrast.py and listed in 06-directions.md.
"""
import re

import make_mockups

# --------------------------------------------------------------------------- A: Werkstatt
A_TOKENS = """
:root {
  color-scheme: light dark;
  --board: #33423e;        /* enamel of the workshop planning board */
  --slot: #40524f;         /* the rail a T-card sits in */
  --ink: #e8e3d8;          /* chalk on the board: every text that stands ON the board */
  --ink-2: #bcc5bf;
  --rule: #55665f;
  --card: #ead9b5;         /* manila card stock */
  --card-ink: #241d14;
  --card-ink-2: #6b5d48;
  --card-head: #d7c397;    /* the head of a plain card: the same stock, one shade deeper */
  --card-stop: #f0b3ad;    /* red card stock: blocked */
  --head-stop: #a1281f;
  --card-you: #f3d67a;     /* yellow card stock: your turn */
  --head-you: #6a5300;
  --you: #f5d76e;          /* on the board: the number, the focus ring */
  --you-ink: #241d14;
  --stop: #f2998d;         /* on the board: the number */
  --stop-ink: #241d14;
  --link-on-card: #5a3e00;
  --font-head: "Franklin Gothic Medium", "Gill Sans", "Trebuchet MS", sans-serif;
  --font-body: "Trebuchet MS", "Gill Sans", "Lucida Grande", sans-serif;
  --font-mono: "Courier New", Courier, "Nimbus Mono", monospace;
  --s1: .5rem; --s2: 1rem; --s3: 1.5rem; --s4: 2.5rem;
}
@media (prefers-color-scheme: dark) {
  :root { --board: #1b2422; --slot: #253230; --ink: #e8e3d8; --ink-2: #a9b3ad; --rule: #3a4844;
          --card: #4a3f2e; --card-ink: #f1e8d6; --card-ink-2: #cdbfa5; --card-head: #5d5040;
          --card-stop: #6a2a25; --head-stop: #b0301f; --card-you: #5f4d14; --head-you: #d2ab2c;
          --you: #f5d76e; --you-ink: #241d14; --stop: #f2998d; --stop-ink: #241d14; --link-on-card: #f5d76e; }
}
"""
A_RULES = """
.card { background: var(--card); color: var(--card-ink); border-radius: 0; box-shadow: none; }
.card .head { background: var(--card-head); color: var(--card-ink); font-weight: 700; border-radius: 0; }
.card.blocked { background: var(--card-stop); }
.card.blocked .head { background: var(--head-stop); color: #ffffff; }
.card.you { background: var(--card-you); }
.card.you .head { background: var(--head-you); color: #ffffff; }
@media (prefers-color-scheme: dark) { .card.you .head { color: #241d14; } }
.card .title { color: var(--card-ink); }
.card .title em, .node-face .kind, .node-face .id, .rec .id, .detail .id, .detail dt, .detail .kind,
.records-type .rec .id { color: var(--card-ink-2); }
.slot { border-radius: 0; }
.slot h3, .slot.empty h3 { color: var(--ink); opacity: .9; }
.figure .num { font-family: var(--font-mono); font-weight: 700; }
.figure[aria-pressed="true"] { background: var(--card); color: var(--card-ink); }
.node-face, .dialog, .focus-list .rec, .records .rec { background: var(--card); color: var(--card-ink); border-radius: 0; box-shadow: none; }
.records .rec { background: transparent; color: var(--ink); }
.records .rec .id { color: var(--ink-2); }
.node-face .badge, .detail .badge, .rec .badge { border-color: var(--card-ink-2); }
.dialog .ref, .goals .ref, .focus-list .rec .note { color: var(--link-on-card); }
/* ids in the focus lists sit on card stock, so they take the HEAD colours, not the board numbers'
   (sighted 1b-2: salmon on manila was unreadable) */
[data-focus-list="blocked"] .rec .id { color: var(--head-stop); }
[data-focus-list="you"] .rec .id { color: var(--head-you); }
@media (prefers-color-scheme: dark) {
  [data-focus-list="blocked"] .rec .id { color: var(--stop); }
  [data-focus-list="you"] .rec .id { color: var(--you); }
}
.dialog .close { background: var(--card-head); color: var(--card-ink); border-radius: 0; }
.tab { border-radius: 0; }
.first { border-top-color: var(--ink); }
.warnings { border-left-color: var(--stop); }
"""

# --------------------------------------------------------------------------- B: Blueprint
B_TOKENS = """
:root {
  color-scheme: light dark;
  --board: #f4f7fa;        /* drafting paper, cool white */
  --slot: transparent;     /* a drawn frame, no fill */
  --card: #f4f7fa;
  --ink: #143a66;          /* Prussian blue: the only ink */
  --ink-2: #4c6a8a;
  --rule: #143a66;
  --you: #f2c14e;          /* revision ochre */
  --you-ink: #1f1a05;
  --stop: #a8321c;         /* red pencil */
  --stop-ink: #ffffff;
  --hatch: rgba(168, 50, 28, .16);
  --font-head: "Candara", "Corbel", "Gill Sans", "Trebuchet MS", sans-serif;
  --font-body: "Candara", "Corbel", "Gill Sans", "Trebuchet MS", sans-serif;
  --font-mono: "Lucida Console", "Lucida Sans Typewriter", Menlo, monospace;
  --s1: .5rem; --s2: 1rem; --s3: 1.5rem; --s4: 2.5rem;
}
@media (prefers-color-scheme: dark) {
  :root { --board: #0f2a4a; --slot: transparent; --card: #0f2a4a; --ink: #e8f0f8; --ink-2: #a9bdd3; --rule: #e8f0f8;
          --you: #f2c14e; --you-ink: #1f1a05; --stop: #ff8a70; --stop-ink: #2a0b05; --hatch: rgba(255, 138, 112, .22); }
}
"""
B_RULES = """
h1, h2, .figure .word, .figure .num { font-family: var(--font-head); text-transform: uppercase; letter-spacing: .04em; }
h3, h4, .eyebrow, .slot h3 { font-family: var(--font-mono); letter-spacing: .12em; }
.slot { background: transparent; border: 1px solid var(--rule); border-radius: 0; }
.slot.empty { border-style: dashed; }
.slot.terminal { opacity: .7; }
.card { background: var(--card); border-radius: 0; box-shadow: 0 0 0 1px var(--ink); }
.card .head { background: var(--card); color: var(--ink); box-shadow: 0 0 0 1px var(--ink); border-radius: 0;
              text-transform: uppercase; letter-spacing: .06em; margin: 0 -.25rem .45rem; }
.card.blocked { box-shadow: 0 0 0 2px var(--stop);
                background-image: repeating-linear-gradient(135deg, transparent 0 7px, var(--hatch) 7px 8px); }
.card.blocked .head { background: var(--stop); color: var(--stop-ink); box-shadow: 0 0 0 2px var(--stop); }
.card.you { box-shadow: 0 0 0 2px var(--you); }
.card.you .head { background: var(--you); color: var(--you-ink); box-shadow: 0 0 0 2px var(--you); }
.card .head .flag { font-family: var(--font-body); text-transform: none; letter-spacing: 0; }
.first { border-top: 2px solid var(--ink); border-bottom: 1px solid var(--ink); padding-bottom: var(--s1); }
.figure[data-focus="you"] .num { color: #8a5a00; }
@media (prefers-color-scheme: dark) { .figure[data-focus="you"] .num { color: var(--you); } }
.figure[aria-pressed="true"] { background: var(--ink); color: var(--board); }
.tabs { border-bottom: 1px solid var(--ink); }
.tab { border-radius: 0; }
.node-face, .dialog { border-radius: 0; box-shadow: 0 0 0 1px var(--ink); }
.focus-list { background: transparent; border: 1px solid var(--ink); }
.warnings { background: transparent; border: 1px solid var(--stop); border-left-width: 3px; }
.dialog .close { border-radius: 0; background: transparent; box-shadow: 0 0 0 1px var(--ink); }
.node-face .badge, .detail .badge, .rec .badge { border-radius: 0; border-color: var(--ink); }
.ref { color: var(--ink); }
"""

# --------------------------------------------------------------------------- C: Leitsystem
C_TOKENS = """
:root {
  color-scheme: light dark;
  --board: #e6e3dc;        /* the grey wall a sign hangs on */
  --slot: #dcd8cf;
  --card: #ffffff;         /* the white panel */
  --ink: #111111;
  --ink-2: #4d4d4a;
  --rule: #b9b5ab;
  --you: #f2c200;          /* caution yellow: black type */
  --you-ink: #111111;
  --stop: #b3261e;         /* stop red: white type */
  --stop-ink: #ffffff;
  --go: #0b6e4f;           /* direction green: white type */
  --go-ink: #ffffff;
  --font-head: Verdana, Tahoma, "Helvetica Neue", "DejaVu Sans", sans-serif;
  --font-body: Verdana, Tahoma, "Helvetica Neue", "DejaVu Sans", sans-serif;
  --font-mono: Verdana, Tahoma, "Helvetica Neue", "DejaVu Sans", sans-serif;
  --s1: .5rem; --s2: 1rem; --s3: 1.5rem; --s4: 2.5rem;
}
@media (prefers-color-scheme: dark) {
  :root { --board: #1c1c1a; --slot: #262624; --card: #2e2e2b; --ink: #f2f2ee; --ink-2: #b5b5ae; --rule: #4a4a46;
          --you: #f2c200; --you-ink: #111111; --stop: #c2372b; --stop-ink: #ffffff; --go: #167a57; --go-ink: #ffffff; }
}
"""
C_RULES = """
body { font-size: 14px; }
h1 { font-weight: 700; letter-spacing: -.01em; }
h2 { font-weight: 700; }
.first { border-top: 0; padding-top: 0; }
.figures { gap: .6rem; }
.figure { border-radius: 0; padding: .7rem .9rem .8rem; color: var(--ink); background: var(--slot);
          grid-template-columns: auto 1fr; }
.figure .num { font-size: 3.2rem; font-weight: 700; color: inherit; }
/* the base sheet colours the red and yellow NUMBER; on a red or yellow FIELD that made it vanish
   (sighted 1b-1: the 3 and the 1 were invisible) -- same specificity, later rule wins */
.figure[data-focus="blocked"] .num, .figure[data-focus="you"] .num { color: inherit; }
.figure .word { font-weight: 700; font-size: 1.05rem; color: inherit; }
@media (max-width: 720px) {
  .figures { grid-template-columns: 1fr; }
  .figure { grid-template-columns: auto 1fr; padding: .5rem .8rem; }
  .figure .num { grid-row: 1; font-size: 2.4rem; }
  .figure .ex { display: block; }
}
.figure .ex { color: inherit; opacity: .85; }
.figure[data-focus="blocked"]:not(.zero) { background: var(--stop); color: var(--stop-ink); }
.figure[data-focus="you"]:not(.zero) { background: var(--you); color: var(--you-ink); }
.figure[data-focus="flight"]:not(.zero) { background: var(--go); color: var(--go-ink); }
.figure.zero .num { color: var(--ink-2); }
.figure:hover, .figure:focus-visible { outline: 3px solid var(--ink); outline-offset: 2px; }
.figure[aria-pressed="true"] { outline: 4px solid var(--ink); outline-offset: 2px; }
.tab { border-radius: 0; font-weight: 700; }
.slot { border-radius: 0; padding-top: 0; }
.slot h3 { background: var(--ink); color: var(--board); margin: 0 -.45rem .5rem; padding: .35rem .6rem;
           letter-spacing: .1em; font-weight: 700; opacity: 1; }
.slot.empty h3 { background: var(--rule); color: var(--ink); opacity: 1; font-weight: 700; }
.card { border-radius: 0; box-shadow: none; border-left: 10px solid var(--rule); }
.card .head { background: transparent; color: var(--ink-2); margin: 0; padding: .4rem .5rem 0; font-family: var(--font-body);
              font-weight: 700; font-size: .78rem; }
.card .head .flag { display: inline-block; margin: .2rem 0 0; padding: .05rem .35rem; font-family: var(--font-body); letter-spacing: 0; }
.card.blocked { border-left-color: var(--stop); }
.card.blocked .head .flag { background: var(--stop); color: var(--stop-ink); }
.card.you { border-left-color: var(--you); }
.card.you .head .flag { background: var(--you); color: var(--you-ink); }
.card .title { font-size: .95rem; padding-top: .1rem; }
.node-face, .dialog, .rec, .badge, .dialog .close, .tab, .focus-list { border-radius: 0; }
.node-face { box-shadow: none; border-left: 6px solid var(--rule); }
.node-face .badge, .detail .badge, .rec .badge { border: 2px solid var(--ink); font-weight: 700; }
.ref { font-family: var(--font-body); font-weight: 700; }
.warnings { border-left: 10px solid var(--stop); }
.unassigned { border-top: 6px solid var(--stop); }
.id, .rec .id, .node-face .id, .detail .id { font-family: var(--font-body); font-variant-numeric: tabular-nums; }
/* caution yellow carries no type on a grey wall (sighted 1b-2): the id gets the field, not the colour */
[data-focus-list="you"] .rec .id { color: var(--you-ink); background: var(--you); padding: 0 .25rem; }
[data-focus-list="blocked"] .rec .id { color: var(--stop-ink); background: var(--stop); padding: 0 .25rem; }
"""

# --------------------------------------------------------------------------- phase 1c: modern
# The user's brief after A/B/C: keep C's strong colour signal, drop every material metaphor, set it
# like a product UI of today. What separates "modern" from the AI default is written in 07-modern.md
# and built here as three rules: colour only as signal, a card is a row with an edge, hierarchy by type
# and space. D and E differ in ONE dimension: D signals with a 4 px bar at the edge on a neutral
# surface, E signals with fully coloured surfaces.
M_FONTS = """
  --font-display: "Segoe UI Variable Display", "Segoe UI Variable", Inter, "SF Pro Display", -apple-system, "Helvetica Neue", Arial, sans-serif;
  --font-head: "Segoe UI Variable Display", "Segoe UI Variable", Inter, "SF Pro Display", -apple-system, "Helvetica Neue", Arial, sans-serif;
  --font-body: "Segoe UI Variable Text", "Segoe UI Variable", Inter, "SF Pro Text", -apple-system, "Helvetica Neue", Arial, sans-serif;
  --font-mono: "Segoe UI Variable Text", "Segoe UI Variable", Inter, "SF Pro Text", -apple-system, "Helvetica Neue", Arial, sans-serif;
  --s1: .5rem; --s2: 1rem; --s3: 1.5rem; --s4: 2.5rem;
"""
M_TOKENS_LIGHT = """
  --board: #f5f5f7;        /* quiet neutral ground */
  --slot: #ebecef;         /* the empty figure, the record list ground */
  --card: #ffffff;
  --ink: #0f1115;
  --ink-2: #5b616e;
  --rule: #e2e4e8;         /* hairline */
  --stop: #d92d20;         /* blocked: field colour */
  --stop-text: #b42318;    /* blocked: as text on white */
  --stop-tint: #fee4e2;
  --stop-ink: #ffffff;
  --you: #b54708;          /* waiting on you: field colour (amber, dark enough for white type) */
  --you-text: #b54708;
  --you-tint: #fef0c7;
  --you-ink: #ffffff;
  --go: #107569;           /* in flight: field colour (teal) */
  --go-text: #107569;
  --go-tint: #d5f5ef;
  --go-ink: #ffffff;
"""
M_TOKENS_DARK = """
  :root { --board: #0f1115; --slot: #1b1e24; --card: #171a1f; --ink: #f3f4f6; --ink-2: #9aa1ad; --rule: #2a2f37;
          --stop: #d92d20; --stop-text: #f97066; --stop-tint: #3a1715; --stop-ink: #ffffff;
          --you: #b54708; --you-text: #fdb022; --you-tint: #3a2810; --you-ink: #ffffff;
          --go: #107569; --go-text: #2ed3b7; --go-tint: #0f2e2a; --go-ink: #ffffff; }
"""
M_RULES = """
body { font-size: 14px; line-height: 1.5; }
h1 { font: 600 1.75rem/1.2 var(--font-display); letter-spacing: -.02em; margin: .1rem 0 .5rem; }
h2 { font: 600 1.05rem/1.3 var(--font-display); letter-spacing: -.01em; }
h3, h4 { text-transform: none; letter-spacing: 0; font: 500 .8rem/1.3 var(--font-body); color: var(--ink-2); }
.eyebrow { text-transform: uppercase; letter-spacing: .08em; font: 600 .68rem/1 var(--font-body); }
.meta, .lead { font-size: .875rem; }
.code, .id, .rec .id, .node-face .id, .detail .id { font-family: var(--font-body); font-variant-numeric: tabular-nums; font-weight: 500; }
.count { font: 500 .8em/1 var(--font-body); }
.first { border-top: 0; padding-top: 0; margin: var(--s3) 0 var(--s2); }
.figures { gap: var(--s2); }
.figure { border-radius: 4px; padding: .7rem .9rem .8rem; column-gap: .7rem; }
.figure .num { font: 600 2.4rem/1 var(--font-display); letter-spacing: -.03em; font-variant-numeric: tabular-nums; }
.figure .word { font: 600 .95rem/1.2 var(--font-body); }
.figure .ex { font-size: .8rem; }
.tabs { border-bottom: 1px solid var(--rule); gap: .1rem; padding-bottom: 0; }
.tab { font: 500 .9rem var(--font-body); padding: .5rem .8rem; border-bottom: 2px solid transparent; border-radius: 0; margin-bottom: -1px; }
.tab[aria-selected="true"] { border-bottom-color: var(--ink); color: var(--ink); }
.tab:hover, .tab:focus-visible { border-bottom-color: var(--ink-2); }
.archived { font-size: .8rem; }
.type { margin-top: var(--s4); }
/* fluid: a slot with cards grows into the width the window has; an empty chain slot stays narrow.
   Rows with more slots than fit still scroll (min-width holds the column readable). */
.slot { background: transparent; padding: 0; border-radius: 0; flex: 1 1 15rem; min-width: 15rem; }
.slot.empty { flex: 0 0 7rem; min-width: 0; }
/* in the stacked (column) layout a 15rem flex-basis becomes a HEIGHT and the slot shrinks under its
   cards -- measured phase 1d: 327 vertical overlaps at 390 px; the basis goes back to auto there */
@media (max-width: 720px) { .slot { flex: 0 0 auto; min-width: 0; width: 100%; } }
.slot h3 { padding: 0 .1rem .5rem; justify-content: flex-start; gap: .4rem; }
.slot.empty { flex-basis: 7rem; }
.slot.empty h3 { opacity: .6; font-weight: 500; }
.slot.terminal { opacity: .7; }
.card { border-radius: 4px; box-shadow: none; border: 1px solid var(--rule); background: var(--card);
        margin-bottom: .5rem; padding: .6rem .75rem .7rem; }
.card .head { margin: 0 0 .25rem; padding: 0; background: transparent; color: var(--ink-2); font: 500 .75rem/1.3 var(--font-body);
              display: flex; flex-wrap: wrap; gap: .2rem .6rem; align-items: baseline; border-radius: 0; }
.card .head .flag { margin: 0; font: 600 .75rem/1.3 var(--font-body); letter-spacing: 0; }
/* the phase-1 sheet fills the head of a signalled card; modern signals by bar (D) or tint (E), never
   by a solid band across the card (sighted 1c-1: BUG-0083 carried an amber band in both) */
.card.blocked .head, .card.you .head { background: transparent; box-shadow: none; }
.card .title { padding: 0; font-size: .9rem; line-height: 1.4; }
.card:hover, .card:focus-visible, .node-face:hover, .rec:hover { box-shadow: 0 0 0 2px var(--ink); }
.node-face, .dialog, .focus-list, .rec { border-radius: 4px; }
.node-face { box-shadow: none; border: 1px solid var(--rule); }
.node-face .kind { text-transform: none; letter-spacing: 0; font: 500 .72rem var(--font-body); }
.badge, .node-face .badge, .detail .badge, .rec .badge { border-radius: 3px; border: 1px solid var(--rule); font: 500 .72rem var(--font-body); }
.focus-list { background: var(--card); border: 1px solid var(--rule); }
.dialog { box-shadow: none; border: 1px solid var(--rule); }
.dialog .close { border-radius: 4px; font: 500 .85rem var(--font-body); }
.detail header { border-bottom: 1px solid var(--rule); }
.detail .kind { text-transform: none; letter-spacing: 0; font: 500 .75rem var(--font-body); }
.detail dt { text-transform: none; letter-spacing: 0; font: 500 .8rem/1.6 var(--font-body); }
.records { border-top: 1px solid var(--rule); }
.records summary { font: 600 1rem var(--font-display); }
.records summary .sum { font: .8rem var(--font-body); }
.warnings { border-radius: 4px; background: var(--card); border: 1px solid var(--rule); border-left: 3px solid var(--stop); font-size: .85rem; }
.unassigned { border-top: 0; border-left: 3px solid var(--stop); border-radius: 0; padding: 0 0 0 var(--s2); }
.ref { color: var(--ink); font-family: var(--font-body); }
.empties, .silent { font-size: .8rem; }
.ruler .tick .id, .ruler .today span { font-family: var(--font-body); }
@media (max-width: 720px) {
  .figures { grid-template-columns: 1fr; gap: .5rem; }
  .figure { grid-template-columns: auto 1fr; padding: .5rem .8rem; }
  .figure .num { grid-row: 1 / span 2; font-size: 2rem; }
  .figure .ex { display: block; }
}
"""

D_TOKENS = ":root {\n  color-scheme: light dark;\n" + M_TOKENS_LIGHT + M_FONTS + "}\n@media (prefers-color-scheme: dark) {\n" + M_TOKENS_DARK + "}\n"
D_RULES = M_RULES + """
/* D: the signal is a 4 px bar at the edge; every surface stays neutral */
.figure { border-left: 4px solid var(--rule); border-radius: 0 4px 4px 0; background: transparent; padding-left: .9rem; }
.figure[data-focus="blocked"]:not(.zero) { border-left-color: var(--stop); }
.figure[data-focus="you"]:not(.zero) { border-left-color: var(--you); }
.figure[data-focus="flight"]:not(.zero) { border-left-color: var(--go); }
.figure[data-focus="blocked"] .num { color: var(--stop-text); }
.figure[data-focus="you"] .num { color: var(--you-text); }
.figure[data-focus="flight"] .num { color: var(--go-text); }
.figure.zero .num { color: var(--ink-2); }
.figure:hover, .figure:focus-visible { background: var(--card); outline: 0; box-shadow: 0 0 0 1px var(--rule); }
.figure[aria-pressed="true"] { background: var(--ink); color: var(--board); border-left-color: var(--ink); }
.figure[aria-pressed="true"] .num, .figure[aria-pressed="true"] .ex { color: inherit; }
.card { border-left-width: 4px; }
.card.blocked { border-left-color: var(--stop); }
.card.blocked .head, .card.you .head { color: var(--ink-2); }
.card.blocked .head .flag { color: var(--stop-text); }
.card.you { border-left-color: var(--you); }
.card.you .head .flag { color: var(--you-text); }
[data-focus-list="blocked"] .rec { border-left: 3px solid var(--stop); border-radius: 0; }
[data-focus-list="you"] .rec { border-left: 3px solid var(--you); border-radius: 0; }
[data-focus-list="flight"] .rec { border-left: 3px solid var(--go); border-radius: 0; }
[data-focus-list="blocked"] .rec .id { color: var(--stop-text); }
[data-focus-list="you"] .rec .id { color: var(--you-text); }
.node-face { border-left-width: 3px; }
"""

E_TOKENS = D_TOKENS
E_RULES = M_RULES + """
/* E: the signal is the surface itself -- the three figures are colour fields, a signalled card is tinted */
.figure { background: var(--slot); color: var(--ink); }
.figure[data-focus="blocked"]:not(.zero) { background: var(--stop); color: var(--stop-ink); }
.figure[data-focus="you"]:not(.zero) { background: var(--you); color: var(--you-ink); }
.figure[data-focus="flight"]:not(.zero) { background: var(--go); color: var(--go-ink); }
.figure[data-focus="blocked"] .num, .figure[data-focus="you"] .num, .figure[data-focus="flight"] .num,
.figure .word, .figure .ex { color: inherit; }
.figure.zero .num { color: var(--ink-2); }
.figure:hover, .figure:focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; background: var(--slot); }
.figure[data-focus="blocked"]:not(.zero):hover, .figure[data-focus="blocked"]:not(.zero):focus-visible { background: var(--stop); }
.figure[data-focus="you"]:not(.zero):hover, .figure[data-focus="you"]:not(.zero):focus-visible { background: var(--you); }
.figure[data-focus="flight"]:not(.zero):hover, .figure[data-focus="flight"]:not(.zero):focus-visible { background: var(--go); }
.figure[aria-pressed="true"] { outline: 3px solid var(--ink); outline-offset: 2px; }
.card.blocked { background: var(--stop-tint); border-color: var(--stop); }
.card.blocked .head { color: var(--stop-text); }
.card.blocked .head .flag { background: var(--stop); color: var(--stop-ink); padding: .05rem .4rem; border-radius: 3px; }
.card.you { background: var(--you-tint); border-color: var(--you); }
.card.you .head { color: var(--you-text); }
.card.you .head .flag { background: var(--you); color: var(--you-ink); padding: .05rem .4rem; border-radius: 3px; }
[data-focus-list="blocked"] .rec { background: var(--stop-tint); }
[data-focus-list="you"] .rec { background: var(--you-tint); }
[data-focus-list="flight"] .rec { background: var(--go-tint); }
[data-focus-list="blocked"] .rec .id { color: var(--stop-text); }
[data-focus-list="you"] .rec .id { color: var(--you-text); }
[data-focus-list="flight"] .rec .id { color: var(--go-text); }
.records .rec { background: transparent; }
"""

DIRECTIONS = {
    "a": ("A — Werkstatt", A_TOKENS, A_RULES),
    "b": ("B — Blueprint", B_TOKENS, B_RULES),
    "c": ("C — Leitsystem", C_TOKENS, C_RULES),
    "d": ("D — Modern, Kante", D_TOKENS, D_RULES),
    "e": ("E — Modern, Fläche", E_TOKENS, E_RULES),
}

_ROOT = re.compile(r":root \{.*?\n\}\n", re.DOTALL)
_DARK = re.compile(r"@media \(prefers-color-scheme: dark\) \{\n  :root \{.*?\}\n\}\n", re.DOTALL)


def build(key):
    """The phase-1 layout CSS with this direction's tokens and character rules."""
    name, tokens, rules = DIRECTIONS[key]
    base = make_mockups.STYLE
    assert _ROOT.search(base) and _DARK.search(base), "phase-1 STYLE changed shape"
    base = _DARK.sub("", _ROOT.sub("", base, count=1), count=1)
    return name, tokens + base + rules
