"""Red-first: restore each defect in a COPY outside the repo, run the test, see it fail, revert.

House rule 5. Every entry is (test, file, the text the fix added, what stood there before it, why).
The script asserts the named test PASSES on the copy as it is, then applies the mutation, asserts it
FAILS, and puts the file back. A mutation that leaves the test green is reported as such -- that is
a test which cannot fail, which is worse than no test.

Usage: python red_first.py [substring of a test name]
"""
import os
import shutil
import subprocess
import sys

SCRATCH = "C:/Offline Repos/v2-testbed/_round-scratch/TSK-0115"
SRC = "C:/Offline Repos/v2-testbed/_worktrees/g3-board"
COPY = os.path.join(SCRATCH, "red")

BOARD = "team-kits/kernel/board.py"
TREE = "team-kits/kernel/backlog_tree.py"
DIAGRAM = "team-kits/kernel/plan_diagram.py"
DASH = "team-kits/dev-team/templates/repo/scripts/generate_dashboard.py"

# (test node id, file, text the FIX introduced, what it replaces = the defect, one-line reason)
MUTATIONS = [
    # ---------------- FR-0075: the board ----------------
    ("tools/test_board.py::test_the_first_strip_counts_blocked_waiting_and_in_flight_from_the_state",
     BOARD, "%(first)s\n<nav", "<nav",
     "the shipped board had no first strip at all"),
    ("tools/test_board.py::test_an_expired_approval_request_is_not_waiting_on_anyone",
     BOARD, "        if now is not None and now > expires:\n            continue\n", "",
     "without the expiry rule an unanswerable request still waits on the user"),
    ("tools/test_board.py::test_the_board_and_the_session_brief_agree_on_the_open_requests",
     BOARD, "    pending = os.path.join(state.root, \"approvals\", \"pending\")",
     "    return []\n    pending = os.path.join(state.root, \"approvals\", \"pending\")",
     "the board did not read the pending requests at all"),
    ("tools/test_board.py::test_the_board_and_the_session_brief_agree_on_the_open_requests",
     BOARD, "            subject = request[\"item\"] or request[\"kind\"]",
     "            continue\n            subject = request[\"item\"] or request[\"kind\"]",
     "a request whose item is archived under it is counted by the brief and not by the board"),
    ("tools/test_board.py::test_a_blocked_card_carries_its_blocker_on_its_face",
     BOARD, "        note = '<span class=\"flag\">blocked by %s</span>' % html.escape(blockers(row))",
     "        note = \"\"",
     "the blocker was only in the record behind the card"),
    ("tools/test_board.py::test_a_blocked_card_carries_its_blocker_on_its_face",
     BOARD, "        note = ('<span class=\"flag\">waiting on you: %s approval</span>'",
     "        note = ('<span class=\"nothing\">%s</span>'",
     "the second signal, what somebody owes an answer for, is not on the face"),
    ("tools/test_board.py::test_living_types_precede_records_and_no_type_is_lost",
     BOARD, "    return tuple(roots + rest), tuple(item_type for item_type in types if item_type not in AUTOMATA)",
     "    return tuple(roots + rest), ()",
     "record types dropped instead of filed"),
    ("tools/test_board.py::test_an_empty_end_state_is_named_not_drawn",
     BOARD, "            if column in terminals:\n                continue\n", "",
     "every empty end state drawn -- 32 empty against 13 filled slots"),
    ("tools/test_board.py::test_a_task_without_a_title_shows_its_work_on_the_face",
     BOARD, "    parts = []\n    if body.get(\"type\"):", "    return title\n    parts = []\n    if body.get(\"type\"):",
     "a task without a title was a bare id"),
    ("tools/test_board.py::test_every_deep_group_starts_hidden_and_every_root_open",
     BOARD, "FOLD_DEPTH = 1", "FOLD_DEPTH = 99",
     "nothing folded: the system view is 105 rows long"),
    ("tools/test_board.py::test_a_fold_control_states_what_it_hides",
     BOARD, '"false" if folded else "true"', '"true"',
     "the control claims expanded over a hidden branch"),
    ("tools/test_board.py::test_the_noscript_page_shows_every_group_and_no_fold_control",
     BOARD, ".tabs, .dialog .close, .interactive, .fold, .tree-tools, .figures, .focus-list {",
     ".tabs, .dialog .close, .interactive {",
     "controls that do nothing without a script are left standing"),
    ("tools/test_board.py::test_the_board_is_a_pure_function_of_the_state_and_the_stamp_it_is_handed",
     BOARD, "    now, today = _clock(generated_at)",
     "    now, today = time.time(), datetime.date.today()",
     "the renderer reads a clock of its own instead of the stamp"),
    ("tools/test_board.py::test_a_stamp_the_board_cannot_read_costs_the_today_marker_and_not_the_page",
     BOARD, "    except (TypeError, ValueError):\n        return None, None",
     "    except (TypeError, ValueError):\n        raise",
     "an unreadable stamp costs the whole page"),
    ("tools/test_board.py::test_an_item_not_under_a_goal_says_what_it_is_in_kit_language",
     TREE, 'NO_LINK: "{home} — not yet triaged"', 'NO_LINK: "unassigned"',
     "the board called a wish waiting for triage unassigned (DEC-0066 (5))"),
    ("tools/test_board.py::test_every_type_the_kernel_has_carries_a_plain_language_name",
     TREE, '    "EVD": ("evidence record", "evidence records"),\n', "",
     "a type the board heads a block with has no plain-language name"),
    ("tools/test_hooks.py::test_the_dashboard_carries_no_item_of_its_own_and_points_at_the_board",
     DASH, '        "active_items": len(rows),',
     '        "active_items": len(rows),\n        "items": rows,',
     "the dashboard renders the items a second time (the parity defect)"),
    # ---------------- rework 1: the verifier's B-1, B-2, M-1, M-2 ----------------
    ("tools/test_board.py::test_a_request_file_nothing_could_write_costs_neither_the_page_nor_the_write",
     BOARD, "        except (OSError, OverflowError, ValueError):",
     "        except ZeroDivisionError:",
     "an epoch no platform clock can express raises out of the renderer, so the board freezes"),
    ("tools/test_board.py::test_a_request_file_nothing_could_write_costs_neither_the_page_nor_the_write",
     BOARD, '            "item": _flat(request.get("item")),',
     '            "item": str(request.get("item") or ""),',
     "str() on an alias graph in a request field: a 504-byte file rendered a 107 MB page"),
    ("tools/test_board.py::test_a_request_file_nothing_could_write_costs_neither_the_page_nor_the_write",
     BOARD, '            "kind": _flat(request.get("kind")) or "?",',
     '            "kind": str(request.get("kind") or "") or "?",',
     "str() on the approval kind: a 107 MB page from a 500-byte request file"),
    ("tools/test_board.py::test_every_reason_a_tree_can_refuse_an_item_is_one_a_store_can_produce",
     TREE, '    MISSING_LINK: "required link missing",',
     '    "unassigned-nonesuch": "dead", MISSING_LINK: "required link missing",',
     "a word for a reason nothing can produce (dead entry end)"),
    ("tools/test_board.py::test_every_reason_a_tree_can_refuse_an_item_is_one_a_store_can_produce",
     TREE, '    OFF_VIEW: "linked outside this view",', "",
     "a reason the page must put a word on and cannot (missing entry end)"),
    ("tools/test_board_browser.py::test_a_title_that_is_one_long_word_does_not_widen_the_page",
     BOARD, ".node-face .title, .rec .title, .rec .note, .ms-face .title, .goals {",
     ".nothing-at-all {",
     "no break opportunity in a path title: the document stands 171 px wider than a 390 px window"),
    ("tools/test_plan_diagram.py::test_a_control_character_in_a_title_cannot_break_the_model",
     DIAGRAM, '    text = " ".join(_XML_FORBIDDEN.sub(_REPLACEMENT, str(text or "")).split())',
     '    text = " ".join(str(text or "").split())',
     "a control character reaches the file: neither diagram is well-formed XML"),
    ("tools/test_plan_diagram.py::test_a_control_character_in_a_title_cannot_break_the_model",
     DIAGRAM, 'canonical(entries).encode("utf-8", "replace")',
     'canonical(entries).encode("utf-8")',
     "a lone surrogate raises out of the digest, before any label is clipped"),
    # ---------------- FR-0079: milestones ----------------
    ("tools/test_board.py::test_a_milestone_stands_on_the_timeline_with_the_goals_it_names",
     BOARD, "    if milestones:\n", "    if False:\n",
     "milestones are captured and the board never shows them"),
    ("tools/test_board.py::test_a_milestone_past_its_date_and_not_reached_is_late",
     BOARD, "        late = date is not None and today is not None and date < today and not reached",
     "        late = date is not None and today is not None and date < today",
     "a reached milestone is reported as late for ever"),
    ("tools/test_board.py::test_two_milestones_a_day_apart_keep_both_labels",
     BOARD, "        level = 1 - level if previous is not None and place - previous < LABEL_BAND_GAP else 0",
     "        level = 0",
     "two labels a day apart stand on top of each other"),
    ("tools/test_board.py::test_a_milestone_with_an_unreadable_date_is_shown_with_no_date",
     BOARD, "    except (TypeError, ValueError):\n        return None\n\n\ndef _timeline_view",
     "    except (TypeError, ValueError):\n        raise\n\n\ndef _timeline_view",
     "a date nobody can read costs the state write"),
    ("tools/test_board.py::test_the_milestone_type_is_wired_completely_or_not_at_all",
     TREE, '    "TSK": ("task", "tasks"),', '    "TSK": ("task", "tasks"),\n    "MST": ("milestone", "milestones"),',
     "the seam applied in one place of five"),
    # ---------------- FR-0080: the diagrams ----------------
    ("tools/test_plan_diagram.py::test_the_diagram_is_a_pure_function_of_the_entries",
     DIAGRAM, 'GENERATOR = "kernel.plan_diagram"',
     'import time\nGENERATOR = "kernel.plan_diagram %s" % time.time()',
     "a clock in the file: no two renders are equal and no hand edit can be told"),
    ("tools/test_plan_diagram.py::test_a_hand_edit_is_told_from_a_stale_file",
     DIAGRAM, 'data-source-digest="%s" content="%s">',
     'data-source-digest="" content="%s">%.0s',
     "without the digest a hand edit and a stale file are one verdict"),
    ("tools/test_plan_diagram.py::test_the_file_is_well_formed_and_carries_a_drawio_model",
     DIAGRAM, 'content="%s">\\n', '>\\n%.0s',
     "the pilot's shape: valid XML, no model -- draw.io opens a flat image"),
    ("tools/test_plan_diagram.py::test_every_cell_names_an_item_the_entries_hold",
     DIAGRAM, "        if node is not root:\n            out.append((node, area))",
     "        if node is not root and node.depth < 2:\n            out.append((node, area))",
     "a level of the tree silently missing from both pictures"),
    ("tools/test_plan_diagram.py::test_status_is_never_carried_by_colour_alone",
     DIAGRAM, '    tail = "%s%s" % (suffix, (" — " + word) if word else "")',
     '    tail = "%s" % (suffix,)',
     "the lane is a fill and nothing else (WCAG 1.4.1)"),
    ("tools/test_plan_diagram.py::test_no_colour_outside_the_named_palette",
     DIAGRAM, 'FONT = "Segoe UI, system-ui, sans-serif"',
     'FONT = "Segoe UI, system-ui, sans-serif"\n_STRAY = "#ff00ff"',
     "a colour nobody chose, written at a call site"),
    ("tools/test_plan_diagram.py::test_a_project_over_the_budget_says_what_it_left_out",
     DIAGRAM, '    return rows[:CELL_BUDGET], ("%d of %d items shown — the board carries all of them"\n                                % (CELL_BUDGET, len(rows)))',
     '    return rows[:CELL_BUDGET], ""',
     "the bound drops work in silence"),
    # ---------------- FR-0075 phase 1d: the layout, in a browser ----------------
    ("tools/test_board_browser.py::test_no_two_cards_of_the_board_overlap_at_any_width",
     BOARD, ".card, .figure, .rec, .node-face, .ms-face, .fold, .tree-tools button { box-sizing: border-box; }",
     "/* box-sizing rule removed */",
     "`all: unset` puts box-sizing back to content-box: 110 overlapping pairs"),
    ("tools/test_board_browser.py::test_the_board_uses_the_width_it_is_given",
     BOARD, ".slot { background: transparent; padding: 0; border-radius: 0; flex: 1 1 15rem; min-width: 15rem; }",
     ".slot { background: transparent; padding: 0; border-radius: 0; flex: 0 0 15rem; }",
     "fixed slots: 115 px empty at 1280, 752 px at 1920"),
    ("tools/test_board_browser.py::test_a_fold_control_works_by_keyboard_and_shows_its_focus",
     BOARD, "'<button type=\"button\" class=\"fold\" data-fold=\"%s\" aria-expanded=\"%s\" '",
     "'<span class=\"fold\" data-fold=\"%s\" aria-expanded=\"%s\" '",
     "a fold control no keyboard can reach"),
    ("tools/test_board_browser.py::test_ruler_labels_share_no_band",
     BOARD, "        level = 1 - level if previous is not None and place - previous < LABEL_BAND_GAP else 0",
     "        level = 0",
     "one band: the labels of two near marks overlap (1 overlap at 390 px)"),
]


def prepare():
    if os.path.isdir(COPY):
        shutil.rmtree(COPY)
    shutil.copytree(SRC, COPY, ignore=shutil.ignore_patterns(
        ".git", "__pycache__", ".pytest_cache", ".codex", ".github"))
    git_file = os.path.join(COPY, ".git")
    if os.path.isfile(git_file):
        os.remove(git_file)                      # a verifier copy carries no worktree pointer
    print("[copy] %s" % COPY)


def run(node):
    return subprocess.run([sys.executable, "-B", "-m", "pytest", node, "-q", "--no-header",
                           "-p", "no:cacheprovider"],
                          cwd=COPY, capture_output=True, text=True, timeout=900)


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    prepare()
    verdicts = []
    for node, rel, fixed, defect, why in MUTATIONS:
        if only and only not in node:
            continue
        path = os.path.join(COPY, rel.replace("/", os.sep))
        original = open(path, encoding="utf-8").read()
        name = node.split("::")[-1]
        green = run(node)
        if green.returncode != 0:
            verdicts.append(("NOT GREEN BEFORE", name, why))
            print("!! %s does not pass on the untouched copy\n%s" % (name, green.stdout[-1500:]))
            continue
        if fixed not in original:
            verdicts.append(("ANCHOR MISSING", name, why))
            print("!! anchor not found in %s for %s" % (rel, name))
            continue
        open(path, "w", encoding="utf-8", newline="\n").write(
            original.replace(fixed, defect, 1))
        red = run(node)
        open(path, "w", encoding="utf-8", newline="\n").write(original)
        verdict = "RED" if red.returncode != 0 else "STILL GREEN"
        verdicts.append((verdict, name, why))
        print("%-11s %s  (%s)" % (verdict, name, why))
        if verdict == "STILL GREEN":
            print(red.stdout[-800:])
    print("\n---- summary ----")
    for verdict, name, why in verdicts:
        print("%-11s %s" % (verdict, name))
    bad = [one for one in verdicts if one[0] != "RED"]
    print("\n%d mutation(s), %d red, %d NOT red" % (len(verdicts), len(verdicts) - len(bad),
                                                    len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
