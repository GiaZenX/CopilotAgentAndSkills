#!/usr/bin/env python3
"""TSK-0074 / BUG-0046, STEP 1: who spoke the text the pilot user read.

THE QUESTION. Pilot 3 (finding B5) recorded four complaints about English technical chatter in the
user's stream, and the report split the cause into "partly instrument, partly real" WITHOUT a
measurement. The split is decidable, because the provider itself files each assistant message: the
session's own messages land in `<store>/<session>.jsonl`, and a subagent's land in a transcript
UNDER `<store>/<session>/` beside a `.meta.json` naming its `agentType`. Origin is therefore read
from where the message was FILED -- never from its wording. Judging language or intent out of free
text is the rejected direction here, and the shipped reference for it is the R2 heuristic in
`team-kits/dev-team/hooks/guard_question_context.py` (a warning that never blocks, by the user
decision its docstring records) together with pilot-3 finding B14, which measured how porous it is.
(An earlier draft of this file cited DEC-0029 for that; DEC-0029 is a different decision -- the
static wire against a second reader -- and the misattribution is corrected here and in the report.)

WHAT IT JOINS. The rig's protocol (`persona_run3.py`) records every assistant TextBlock it relayed
to the persona. Matching those texts against the filed messages answers both halves in one table:
how much of the user-visible stream the session itself spoke, and how much of it belonged to a
dispatched specialist.

WHICH TRANSCRIPT BELONGS TO WHICH RUN is derived, not configured: the session whose filed texts
the relay log actually carries is the session that produced it, and a tie is reported instead of
picked.

    python docs/reviews/2026-08-17-tsk0074-relay-origin.py --store <dir> --relay <run.jsonl> ...

The numbers this prints belong in the round's report, not in a second copy inside some comment.
"""
import argparse
import io
import json
import os


def _texts(path):
    """Every assistant TEXT block of one transcript, in order."""
    out = []
    with io.open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if record.get("type") != "assistant":
                continue
            for block in (record.get("message") or {}).get("content") or []:
                if isinstance(block, dict) and block.get("type") == "text":
                    out.append((block.get("text") or "").strip())
    return [text for text in out if text]


def _speaker(path, session_dir):
    """The name the provider filed this transcript under -- its `agentType`, else the file stem."""
    meta = os.path.splitext(path)[0] + ".meta.json"
    if os.path.isfile(meta):
        try:
            with io.open(meta, encoding="utf-8") as handle:
                agent_type = (json.load(handle) or {}).get("agentType")
            if agent_type:
                return str(agent_type)
        except ValueError:
            pass
    return os.path.relpath(path, session_dir).replace(os.sep, "/")


def session_voices(store, session):
    """[(speaker, [text, ...])] -- the session's own voice first, then every voice filed under it.

    "Under it" is a walk rather than a known directory name: what makes a transcript a subagent's
    is that the provider filed it INSIDE the session's own directory, and the layer that names
    that directory is not ours to predict.
    """
    voices = [("(session)", _texts(os.path.join(store, session + ".jsonl")))]
    session_dir = os.path.join(store, session)
    for root, _dirs, files in os.walk(session_dir):
        for name in sorted(files):
            if not name.endswith(".jsonl"):
                continue
            path = os.path.join(root, name)
            voices.append((_speaker(path, session_dir), _texts(path)))
    return voices


def relayed_texts(path):
    """Every string the relay log carried under a `text` key, at any depth."""
    found = set()

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "text" and isinstance(value, str) and value.strip():
                    found.add(value.strip())
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    with io.open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                walk(json.loads(line))
            except ValueError:
                continue
    return found


def sessions(store):
    return sorted(name[:-len(".jsonl")] for name in os.listdir(store)
                  if name.endswith(".jsonl") and os.path.isfile(os.path.join(store, name)))


def match_session(store, relay, candidates):
    """The session whose filed texts this relay log carries -- highest coverage, ties reported."""
    said = relayed_texts(relay)
    scored = []
    for session in candidates:
        hits = sum(1 for _speaker, texts in session_voices(store, session)
                   for text in texts if text in said)
        scored.append((hits, session))
    scored.sort(reverse=True)
    if not scored or scored[0][0] == 0:
        return None, 0
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        raise SystemExit("ambiguous: %s and %s cover this relay log equally"
                         % (scored[0][1], scored[1][1]))
    return scored[0][1], scored[0][0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", required=True,
                        help="the provider's transcript directory for the pilot project")
    parser.add_argument("--relay", nargs="+", required=True,
                        help="one or more rig protocols (the persona's stream)")
    args = parser.parse_args()

    candidates = sessions(args.store)
    print("| relay log | session | speaker | filed | relayed |")
    print("|---|---|---|---|---|")
    totals = {}
    for relay in args.relay:
        session, _hits = match_session(args.store, relay, candidates)
        if session is None:
            print("| %s | (no session in this store carries its texts) | | | |"
                  % os.path.basename(relay))
            continue
        said = relayed_texts(relay)
        for speaker, texts in session_voices(args.store, session):
            if not texts:
                continue
            shown = sum(1 for text in texts if text in said)
            print("| %s | %s | %s | %d | %d |"
                  % (os.path.basename(relay), session[:8], speaker, len(texts), shown))
            filed, relayed = totals.get(speaker, (0, 0))
            totals[speaker] = (filed + len(texts), relayed + shown)

    print()
    print("| speaker | filed | relayed |")
    print("|---|---|---|")
    for speaker in sorted(totals):
        print("| %s | %d | %d |" % (speaker, totals[speaker][0], totals[speaker][1]))
    own = totals.get("(session)", (0, 0))[1]
    other = sum(relayed for speaker, (_filed, relayed) in totals.items() if speaker != "(session)")
    print()
    print("relayed by the session itself: %d; relayed on behalf of a dispatched role: %d"
          % (own, other))


if __name__ == "__main__":
    main()
