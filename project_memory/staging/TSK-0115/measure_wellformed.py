"""Measure: do the generated .drawio.svg files pass the ONE check the kernel applies to a
.drawio.svg today (`kernel.staging._assert_xml_wellformed`), and does the pilot's real
ARC-0001.drawio.svg carry a draw.io `content` attribute at all?"""
import os
import sys
import xml.etree.ElementTree as ET

TEAM_KITS = "C:/Offline Repos/v2-testbed/_worktrees/g3-board/team-kits"
sys.path.insert(0, TEAM_KITS)
sys.dont_write_bytecode = True
from kernel import staging  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PILOT = "C:/Offline Repos/v2-testbed/dev-app/project_memory/architecture/active/ARC-0001.drawio.svg"

for path in (os.path.join(HERE, "diagrams", "plan.drawio.svg"),
             os.path.join(HERE, "diagrams", "mindmap.drawio.svg"),
             os.path.join(HERE, "diagrams", "plan-hand-edited.drawio.svg"), PILOT):
    try:
        staging._assert_xml_wellformed(path)
        verdict = "well-formed (kernel check passes)"
    except Exception as exc:  # noqa: BLE001
        verdict = "REFUSED: %s" % exc
    root = ET.parse(path).getroot()
    has_content = "content" in root.attrib
    mx = None
    if has_content:
        try:
            mx = ET.fromstring(root.get("content")).tag
        except ET.ParseError as exc:
            mx = "content not XML: %s" % exc
    print("%-90s %s; content attribute: %s; root of content: %s" % (os.path.basename(path), verdict, has_content, mx))
