"""The three states the mockups show, built as rigs under the scratch directory.

  empty    -- the dev-team template tree, no item captured (the kernel's index has 0 rows)
  healthy  -- REAL items of the main repo, a subset: two roots with their SRs, three open wishes,
              four bugs, three tasks, the newest three decisions; no blocked flag, no open request.
              Two status fields are edited in the copy (named in README) so the picture carries
              work in flight: TSK-0116 -> IN_PROGRESS, FR-0080 -> TRIAGED.
  blocked  -- the full real copy PLUS an overlay the real store does not have (measured 2026-09-03:
              0 rows carry blocked_by): TSK-0117 blocked by TSK-0115, TSK-0118 blocked by APR-0004,
              BUG-0088 blocked by TSK-0116; the open scope request on BUG-0083 is REAL.

Every rig gets its index and board from the kernel itself (rig.kernel_index), so the mockup reads
exactly what a project would hold.
"""
import os
import shutil
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
# rig.py lives beside this file in the staging copy and one directory up in the scratch layout
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import rig  # noqa: E402

FIX = os.path.join(rig.SCRATCH, "fixtures")
REAL = os.path.join(rig.SCRATCH, "rig", "project_memory")   # the copy parity.py built
TEMPLATE_PM = os.path.join(rig.TEAM_KITS, "dev-team", "templates", "project_memory")

HEALTHY_IDS = ("PR-0002", "PR-0003", "SR-0008", "SR-0009", "FR-0075", "FR-0079", "FR-0080",
               "BUG-0086", "BUG-0087", "BUG-0088", "BUG-0089", "TSK-0115", "TSK-0116", "TSK-0117",
               "DEC-0061", "DEC-0062", "DEC-0063")
# Edits in the COPY, all named: two statuses so the picture carries work in flight, and the bindings
# re-pointed at items the subset holds, so the trees place them (the real bindings point at FRs
# and at archived items, which is what the real store's own Unassigned warnings say).
HEALTHY_EDITS = {
    "TSK-0116": {"status": "IN_PROGRESS", "product_requirement": "PR-0003", "derives_from": "SR-0008"},
    "TSK-0115": {"product_requirement": "PR-0003", "derives_from": "SR-0009"},
    "TSK-0117": {"product_requirement": "PR-0003", "derives_from": "PR-0003"},
    "FR-0080": {"status": "TRIAGED", "related_pr": "PR-0003"},
    "FR-0075": {"related_pr": "PR-0003"},
    "FR-0079": {"related_pr": "PR-0002"},
    "BUG-0086": {"related_pr": "PR-0003"},
    "BUG-0087": {"related_pr": "PR-0003"},
    "BUG-0088": {"related_pr": "PR-0002"},
    "BUG-0089": {"related_pr": "PR-0003", "related_sr": "SR-0009"},
}
BLOCKED_OVERLAY = {"TSK-0117": "TSK-0115", "TSK-0118": "APR-0004", "BUG-0088": "TSK-0116"}


def _edit(path, fields):
    with open(path, encoding="utf-8") as fh:
        body = yaml.safe_load(fh)
    body.update(fields)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(body, fh, allow_unicode=True, sort_keys=False)


def _find(pm, item_id):
    for dirpath, _dirs, files in os.walk(pm):
        if "archive" in dirpath.replace("\\", "/").split("/"):
            continue
        if item_id + ".yaml" in files:
            return os.path.join(dirpath, item_id + ".yaml")
    raise SystemExit("no %s under %s" % (item_id, pm))


def build_empty():
    target = os.path.join(FIX, "empty")
    pm = rig.build(target, None)
    shutil.rmtree(pm)
    shutil.copytree(TEMPLATE_PM, pm)
    rig.kernel_index(pm)
    return target


def build_healthy():
    target = os.path.join(FIX, "healthy")
    pm = rig.build(target, None)
    shutil.rmtree(pm)
    shutil.copytree(TEMPLATE_PM, pm)
    for item_id in HEALTHY_IDS:
        src = _find(REAL, item_id)
        rel = os.path.relpath(src, REAL)
        dst = os.path.join(pm, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(src, dst)
        if item_id in HEALTHY_EDITS:
            _edit(dst, HEALTHY_EDITS[item_id])
    # a little history, so the archive line is not empty: five real archived tasks
    src_arch = os.path.join(REAL, "archive", "TSK", "2026")
    dst_arch = os.path.join(pm, "archive", "TSK", "2026")
    os.makedirs(dst_arch, exist_ok=True)
    for name in sorted(os.listdir(src_arch))[-5:]:
        shutil.copy(os.path.join(src_arch, name), os.path.join(dst_arch, name))
    shutil.copy(os.path.join(REAL, "project_config.yaml"), os.path.join(pm, "project_config.yaml"))
    rig.kernel_index(pm)
    return target


def build_blocked():
    target = os.path.join(FIX, "blocked")
    pm = rig.build(target, REAL)
    for item_id, blocker in BLOCKED_OVERLAY.items():
        _edit(_find(pm, item_id), {"blocked_by": blocker})
    rig.kernel_index(pm)
    return target


if __name__ == "__main__":
    for builder in (build_empty, build_healthy, build_blocked):
        print("[fixture]", builder())
