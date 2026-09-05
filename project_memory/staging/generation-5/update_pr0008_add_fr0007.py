"""User 2026-09-05: FR-0007 (the comment discipline of DEC-0008 / SR-0008 into the kits' constitutions
and role definitions -- the user assumed it was there because this repo works like a kit) joins G5-1.
PR-0008 is DRAFT and updatable: the acceptance list is REPLACED with the existing six plus AC-7.
Body on stdin to `kernel.cli update PR-0008`."""
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
KERNEL = [sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory", "update", "PR-0008"]

ACS = [
    {"id": "AC-1", "text": "FR-0058 (survey): Given the 89 active BUGs, When each is measured against the running code (its observed line re-run or its test executed), Then each carries one of three verdicts in the state -- VERIFIED and archived through the kernel with an Evidence item naming the test/measurement; still OPEN with the re-measured chain and date; or CANCELLED/superseded with the item that absorbed it -- and the round's protocol lists all 89 with verdict and measured line; no verdict without a measurement"},
    {"id": "AC-2", "text": "FR-0058 (wishes): Given the 21 active FRs, When each is triaged against what ships, Then delivered ones are MERGED with resulting_item, absorbed ones point at their goal, the deferred block (FR-0024, FR-0019, FR-0022, FR-0023, FR-0025, FR-0020) stays TRIAGED with the user's 'needs planning' note, and no FR remains whose source section describes something already built"},
    {"id": "AC-3", "text": "FR-0058 (the derivable 'done'): Given an item that stands OPEN while its confirming evidence or named regression test exists and passes, When validate runs, Then it names the item as 'stock lies upward' with the evidence/test it found -- a property derived from the items and the evidence store, not a list; red-first"},
    {"id": "AC-4", "text": "BUG-0023: create-task and capture TSK refuse an empty expected_outputs list naming the field (both entrances, one rule); existing items with an empty list are named by the validator; red-first"},
    {"id": "AC-5", "text": "BUG-0022: the CR type is either reached in a measured run (a change to something built produces a CR item through its automaton, and the PM texts say WHEN a CR applies instead of a PR replacement, with a test on the text-to-behaviour path) or removed with the reasons recorded -- no dead contract; the PR-replacement path stays for real re-orientations and records the replacement"},
    {"id": "AC-6", "text": "Generation-4 leftovers closed through the kernel: BUG-0025, BUG-0033, BUG-0069, BUG-0088, BUG-0090, BUG-0091 VERIFIED against the merged tree with their evidence lines; BUG-0083..0086 and BUG-0089 archived; the seven G4 stream items archived"},
    {"id": "AC-7", "text": "FR-0007 (comment discipline into the kits): the rule of DEC-0008 / SR-0008 -- a comment carries the WHY and points at items; a property claim becomes a test the comment names; a named test must resolve; no sentence claims a check the code does not build -- stands in the three constitutions and in every implementing role definition (developer, bookkeeper, researcher roles as the kit's contract names them) as a duty with its measured case, byte-identical where shared; the kits ship the mechanical half this repo has (a pointer sweep over the project's own code and role texts: a named test or item that does not resolve is red), scaffolded and measured on a pilot per kit; what stays human (a claim naming no test) is said so in the text"},
]

env = dict(os.environ, PYTHONPATH="team-kits")
result = subprocess.run(KERNEL, cwd=ROOT, env=env, input=json.dumps({"acceptance_criteria": ACS}),
                        capture_output=True, text=True, encoding="utf-8")
sys.stdout.write(result.stdout)
sys.stderr.write(result.stderr)
sys.exit(result.returncode)
