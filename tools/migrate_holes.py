#!/usr/bin/env python3
"""Migrate the H-numbered hole list of `docs/POST_V2_WISHLIST.md` into typed items -- ONCE.

A THIN CALLER SINCE TSK-0126. The migration writes canonical state, so its door belongs to the
kernel and its one writing run belongs on the route gate 1 sanctions:

    PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory migrate-holes \
        --related-pr PR-nnnn --apply

This command line still works and does the same thing -- it is the same door, called from here --
but a session cannot take it: gate 1 refuses a tool write into `project_memory/`. Everything the
migration IS lives in `kernel/holes.py`, including the argument this docstring used to carry.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.dont_write_bytecode = True

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "team-kits"))

from kernel import holes  # noqa: E402
from kernel.state import ProjectState  # noqa: E402

# The names the suite and the gate tests import from here, so re-pointing them is not part of
# every round that touches the migration: this module IS the tool's command line and nothing else.
DEFAULT_HOLES_DIR = holes.DEFAULT_HOLES_DIR
VERDICT_STATUS = holes.VERDICT_STATUS
read_section = holes.read_section
parse_entries = holes.parse_entries
parse_rows = holes.parse_rows
cited_tests = holes.cited_tests
item_body = holes.item_body
index_rows = holes.index_rows
render_index = holes.render_index
migrate = holes.migrate
_write_index = holes._write_index
_index_row_count = holes._index_row_count
reindex = holes.reindex


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", required=True, help="the state directory (project_memory)")
    parser.add_argument("--doc")
    parser.add_argument("--related-pr",
                        help="the product goal these holes are filed under (required unless "
                             "--reindex, which writes no item)")
    parser.add_argument("--holes-dir", default=holes.DEFAULT_HOLES_DIR,
                        help="where the full text of each entry goes, relative to the repo")
    parser.add_argument("--apply", action="store_true",
                        help="write; without it nothing is written and the plan is printed")
    parser.add_argument("--reindex", action="store_true",
                        help="rewrite the document's generated pointer index from the store and "
                             "nothing else -- what a hole captured through `capture --hole` needs")
    args = parser.parse_args(argv)
    if not args.reindex and not args.related_pr:
        parser.error("--related-pr is required unless --reindex is given")
    state = ProjectState(args.root)
    doc = args.doc or holes.document_for(state)
    if args.reindex:
        print(holes.reindex(state, doc, args.holes_dir))
        return 0
    report = holes.migrate(state, doc, args.related_pr, args.holes_dir, apply=args.apply)
    for line in holes.render_report(report):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
