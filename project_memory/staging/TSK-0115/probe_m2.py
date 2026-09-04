"""M-2 before/after: a control character in a title against the generated .drawio.svg."""
import os
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
WT = os.environ.get("PROBE_TREE", "C:/Offline Repos/v2-testbed/_worktrees/g3-board")
sys.path.insert(0, os.path.join(WT, "team-kits"))
from kernel import plan_diagram                            # noqa: E402

TITLE = "\x00\x01 NUL first"
TSK = {"product_requirement": "PR-0001", "root_revision": 1, "derives_from": "PR-0001",
       "type": "implementation", "assigned_role": "backend-developer", "acceptance_refs": ["AC-1"],
       "required_inputs": [], "allowed_scope": ["src/**"], "forbidden_scope": [],
       "expected_outputs": ["code"], "dependencies": []}
entries = [
    ({"id": "PR-0001", "type": "PR", "title": TITLE, "status": "APPROVED"},
     {"id": "PR-0001", "title": TITLE, "status": "APPROVED"}),
    ({"id": "TSK-0001", "type": "TSK", "title": TITLE, "status": "DRAFT"},
     dict(TSK, id="TSK-0001", title=TITLE, status="DRAFT")),
]
out = "C:/Offline Repos/v2-testbed/_round-scratch/TSK-0115/rework1/m2"
os.makedirs(out, exist_ok=True)
bad = 0
for name, text in plan_diagram.render_all(entries):
    path = os.path.join(out, name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    try:
        root = ET.parse(path).getroot()
        ET.fromstring(root.get("content") or "<x/>")
        print("%-22s well-formed: yes" % name)
    except ET.ParseError as exc:
        bad += 1
        print("%-22s well-formed: NO  (%s)" % (name, exc))
    print("   is_pristine says: %s" % (plan_diagram.is_pristine(path, entries),))
sys.exit(1 if bad else 0)
