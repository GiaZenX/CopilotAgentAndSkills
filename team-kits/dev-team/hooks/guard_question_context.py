#!/usr/bin/env python3
"""
PreToolUse(AskUserQuestion) guard — a question must never point at INVISIBLE context.

A real PM asked "Kategorien-Set freigeben (wie oben zusammengefasst)?" — but the whole turn
before the question was thinking + tool calls, no visible text: the summary the question
referenced existed only in the model's (hidden) thinking, so the user got a bare dialog
deciding about content they never saw. This guard blocks question/option text that refers to
"above"/"as summarized" style context. The rule it enforces (PM skill): the full decision
context is either visible TEXT in the SAME message before the question, or lives inside the
question and its option descriptions — thinking does not count, and "oben" is never a place.

Any uncertainty -> exit 0 (never block legitimate questions).

TWO WARN HEURISTICS ride along (parity risks R2 and R13, user decision "maximal haerten"
2026-07-24). They share this hook's trigger and would otherwise be two more process spawns per
question. Both are WARNINGS and exit 0 -- the decision text is explicit that heuristics warn and
are never fail-closed, "faellt eine Heuristik in der Praxis durch, bleibt die Regel Prosa-Rest":

  R2  a question to the USER that is full of technical vocabulary. The constitution's boundary is
      product questions to the user, technical ones to the team (rows 8/9); asking the user to
      pick a database is how a project acquires decisions nobody owns.
  R13 a MASTERPLAN approval question with no risks/criticism among its options. "Masterplan
      kritisch pruefen" means the plan is presented WITH its objections; an approval dialog that
      offers only agreement has already made the decision.

HOW A WARNING REACHES ANYONE, honestly: exit 0 with stderr, plus an audit note. On PreToolUse only
exit 2 is guaranteed to put text in front of the model, so a warning's visibility is weaker by
construction -- which is the price of not blocking, and the reason both of these stay heuristics
rather than becoming rules.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _audit
import _compat

# References to context OUTSIDE the question itself (German + English variants seen in real
# transcripts). Deliberately narrow: "wie besprochen" (the user SAW that dialogue) stays legal,
# and "oben dargestellt WERDEN" (UI placement, not a reference) is exempted via lookahead; the
# guard targets references to PM-produced artifacts ("wie zusammengefasst", inflected forms
# too — "das oben beschriebene Set") and spatial "above" references — the question dialog
# renders detached from prose, so a question must be self-contained.
_INVISIBLE_REF_RX = re.compile(
    r"\bwie\s+oben\b"
    r"|\bsiehe\s+oben\b"
    r"|\bvgl\.\s?oben\b"
    r"|\bs\.\s?o\.\B"
    r"|\bo\.\s?g\.\B"
    r"|\bobige[mnrs]?\b"
    r"|\bobenstehend\w*\b"
    r"|\boben\s+(?:zusammengefasst|beschrieben|genannt|erwähnt|dargestellt|erläutert|"
    r"skizziert)(?:e[mnrs]?)?\b(?!\s+(?:werden|wird|anzeigen|angezeigt))"
    r"|\bwie\s+(?:gerade\s+|eben\s+|zuvor\s+)?(?:zusammengefasst|dargestellt|skizziert)\b"
    r"|\bwie\s+(?:gerade|eben|zuvor)\s+beschrieben\b"
    r"|\bsee\s+above\b"
    r"|\bas\s+(?:discussed|summarized|summarised|described|outlined|explained|shown|"
    r"mentioned|noted|stated|listed)\s+above\b"
    r"|\bas\s+per\s+the\s+above\b"
    r"|\bthe\s+above\s+(?:summary|proposal|list|plan|analysis|points|options|categories)\b"
    r"|\bthe\s+(?:summary|proposal|list|plan|analysis|points|options|categories)\s+above\b",
    re.IGNORECASE)


# R2: vocabulary that belongs in a decision the TEAM makes. Deliberately narrow and
# proper-noun-heavy -- "database" alone appears in perfectly good product questions ("should
# customers see their order history?"), while "Postgres oder MySQL" cannot be anything but a
# technical choice.
#
# TWO distinct hits, and the number is the comment's own example rather than a guess about
# clusters. It said "Postgres oder MySQL" and the threshold was three, so the sentence the
# paragraph is built on measured SILENT -- a comment claiming a protection the code did not build,
# in the guard whose whole subject is questions that point at something that is not there.
# Two is the smallest number that can be a CHOICE; one is a mention. The direction is affordable
# because this is a warning that exits 0 and its own text ends with "If it really is a product
# question (cost, hosting, data location), ignore this" -- the cost of a false alarm is a line of
# stderr, the cost of silence is the decision nobody on the team owns.
_TECH_VOCAB_MIN = 2
_TECH_VOCAB_RX = re.compile(
    r"\b(?:postgres(?:ql)?|mysql|mariadb|sqlite|mongodb|redis|kafka|rabbitmq"
    r"|react|vue|svelte|angular|next\.js|nuxt|django|flask|fastapi|rails|spring"
    r"|docker|kubernetes|k8s|terraform|nginx|apache"
    r"|rest|graphql|grpc|websocket|microservice[sn]?|monolith"
    r"|orm|migration[en]?|schema|index(?:ierung)?|sharding|caching"
    r"|typescript|python|rust|golang|java\b|c\+\+"
    r"|framework|architektur|architecture|tech[- ]?stack|repository[- ]?pattern)\b",
    re.IGNORECASE)
# R13: an approval question about the PLAN itself.
_MASTERPLAN_RX = re.compile(r"\bmasterplan\b|\bgesamtplan\b|\bplan\s+freigeben\b",
                            re.IGNORECASE)
# ...and the shapes that show the plan was presented WITH its objections.
_CRITIQUE_RX = re.compile(
    r"\brisik|\brisk|\bkritik|\bcritique|\beinwand|\bobjection|\bbedenken|\bconcern"
    r"|\boffene\s+frage|\bopen\s+question|\bannahme|\bassumption|\btrade-?off"
    r"|\bunsicher|\buncertain", re.IGNORECASE)


def _warn(kind, message):
    """Say it and get out of the way. Exit 0 stays exit 0."""
    _audit.record("guard_question_context", "%s: %s" % (kind, message[:160]))
    sys.stderr.write("[team-kit note] %s\n" % message)


def _advisory_checks(texts):
    joined = "\n".join(texts)
    tech = sorted({m.group(0).lower() for m in _TECH_VOCAB_RX.finditer(joined)})
    if len(tech) >= _TECH_VOCAB_MIN:
        _warn("R2", "this question asks the USER about technical choices (%s). The constitution's "
                    "boundary is product questions to the user, technical ones to the team — a "
                    "user picking a database acquires a decision nobody on the team owns. If it "
                    "really is a product question (cost, hosting, data location), ignore this."
              % ", ".join(tech[:5]))
    if _MASTERPLAN_RX.search(joined) and not _CRITIQUE_RX.search(joined):
        _warn("R13", "this masterplan approval offers no risks, open questions or objections. "
                     "\"Masterplan kritisch prüfen\" means presenting the plan WITH what argues "
                     "against it; a dialog that offers only agreement has already decided.")


def main():
    data = _compat.load()  # bytes-level UTF-8 stdin decode — Windows cp1252 stdin turned the
    if data.get("tool_name") != "AskUserQuestion":  # umlaut patterns into dead code (audit)
        sys.exit(0)
    ti = data.get("tool_input") or {}
    texts = []
    for q in (ti.get("questions") or []):
        if not isinstance(q, dict):
            continue
        texts.append(str(q.get("question") or ""))
        texts.append(str(q.get("header") or ""))
        for o in (q.get("options") or []):
            if isinstance(o, dict):
                texts.append(str(o.get("label") or ""))
                texts.append(str(o.get("description") or ""))
    hits = sorted({m.group(0) for t in texts for m in _INVISIBLE_REF_RX.finditer(t)})
    if not hits:
        _advisory_checks(texts)      # warnings only, and only when nothing is being blocked
        sys.exit(0)
    _audit.record("guard_question_context", "; ".join(hits)[:200])
    _compat.stop(
        "[team-kit guard] Blocked AskUserQuestion: it references context the user CANNOT see "
        "(%s). Your thinking and earlier tool calls are invisible — a real PM once asked for "
        "sign-off on a summary that was never printed. Fix: put the full decision context as "
        "visible TEXT in this same message BEFORE the question, or make the question "
        "self-contained (details into the question text and option descriptions), then ask "
        "again without the reference.\n" % ", ".join("'%s'" % h for h in hits[:4]),
        "PreToolUse")


if __name__ == "__main__":
    main()
