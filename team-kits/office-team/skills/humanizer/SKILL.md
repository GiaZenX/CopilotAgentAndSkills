---
name: humanizer
description: >
  REFERENCE skill (no role owns it): how to make a text written FOR A PERSON — product copy, a
  letter, a report section, a reply in the chat, the words in a UI — read as written by one. Not a
  detector and not a phrase list: measured PROPERTIES of machine prose (sentence-length variance,
  dash and colon density, hedging depth, discourse-marker frequency, structural reflexes) plus a
  German layer, each with the check you make on your own draft and the move that changes
  it. Open it when a work order names it, on the draft you already have; it asks nobody anything.
  NOT loaded at session start and named by no role's `skills:` frontmatter — open it with
  `/humanizer`. On Codex the generated mirror carries every skill directory, so it is also at
  `.agents/skills/humanizer/SKILL.md`.
# WHICH ORDERS NAME THIS SKILL (FR-0071) -- read by `kernel.references.for_task`, which requires a
# match on BOTH axes, so a `test` task for the designer does not arrive carrying it.
#
# ROLES: the ones whose deliverable is prose a person reads -- office product copy and posts,
# the research report, the designer's UI-text table. The two kit LEADS are named for their
# replies to the user, which is the one text no work order carries: a lead is not dispatched by
# the constitution's loop, so in practice only its own text sends it here.
#
# TASK TYPES: the closed vocabulary is `kernel.backlog_types.TASK_TYPES`, and which of its
# values a TEXT task gets is the lead's judgement at routing time, so the declaration covers every
# type under which such a deliverable can arrive -- the document type, the two design types, the
# research kit's execution type, and `implementation`, because nothing stops a lead from typing a
# copy task with it. Both ends are held by `tools/test_shared_skill_contract.py`: a role here that
# no kit ships and a type outside the vocabulary each go red.
reference_for:
  roles: [product-editor, marketing-planner, report-writer, product-designer, project-manager,
          office-manager]
  task_types: [docs, ui, design, research, implementation]
---

# Humanizer — prose a person could have written

> **Own text, not a vendored file.** Learned from four MIT-licensed skills and two CC BY-SA
> catalogues, and none of their wording is here: harshaneel/humanize (MIT; the nine detection
> properties as a frame), Aboudjem/humanizer-skill (MIT; the self-audit pass and the burstiness
> arithmetic), jurigis/avoid-ai-writing-multilingual (MIT; `SKILL-DE.md`, the German-native
> patterns and the Schaaff/Schlippe/Mindner 2023 finding that the tells are language-specific),
> marmbiz/humanizer-de (code MIT, but its pattern catalogue is CC BY-SA 4.0 and Wikipedia-derived
> — read for orientation, like Wikipedia's "Signs of AI writing" itself, which is CC BY-SA). All
> four are built for a user who pastes a text and answers for it — a voice flag, a tone option, a
> writer profile, a second pass on request — and the roles in these kits have no user to ask,
> which is why this is written rather than vendored (FR-0072 triage). No `LICENSE.txt` sits
> beside this file because no licensed text is in it; nothing in the suite compares this file to
> those sources, so "none of their wording" is a statement of how it was written, not a measured
> property.

## What this is for, and what it is not

You open this **mid-task, on a draft you already have**, and apply it silently. It asks nobody
which voice to use: the voice is in the brief you were already told to read, and this skill only
says where —

- **office roles:** the content guidelines document your own procedure skill lists under *Read
  first* (its `tone`, `language`, `structure` and claims policy). That file is the voice; if it
  says "ohne Superlative", a superlative is a defect before it is a style question.
- **product-designer:** the design brief — the Decision item holding the design ambition and the
  frozen design revision's UI-text table (your procedure skill, *Read first*). The `frontend-design`
  reference already carries the UX-writing rules for controls, errors and empty states; this skill
  is for the sentences around them.
- **report-writer:** the report template and the `EXP` item; a scientific register is the brief,
  and most of the German layer below is switched OFF by it (see the register note there).
- **the lead, replying to the user:** the constitution's rule that the user hears plain German
  without jargon. That rule says WHAT; this skill is the craft half of HOW.

Three things it is not. It is **not a detector**: it produces no score and claims nothing about
who wrote a text. It is **not a linter**: no script runs, on purpose (DEC-0056 — a prose skill
for a prose error; the error it answers is the user reading his own shop copy and hearing a
machine, and the test of it is his: a before/after on his real copy, judged by him). And it **does
not touch facts**: numbers, names, attributes, mandatory fields, compliance claims and the claims
policy stay exactly what the brief and the catalogue make them. A rewrite that changes what a
sentence asserts has left this skill's scope.

**Restraint is part of the job.** A short, specific, correct text needs nothing from here; varying
for variety's sake is the same reflex in the other direction, and it launders the brief's voice.
Stop when the text says its facts in the reader's words.

## The procedure — measure, rewrite, re-measure

1. **Read the brief** (above). Where it pins a spelling, a form of address or a word, the brief
   wins over anything below.
2. **Measure the draft once**, per paragraph, before changing a word. The properties in the next
   section each say what to check — often a count, otherwise the definition read against the text;
   write the answers down for yourself (a note, not the text). A draft is not "AI-sounding" —
   it has a shortest and a longest sentence, N dashes, N stacked qualifiers, N marker openers, N
   triplets, N adjectives with no attribute behind them.
3. **Rewrite from the content, not from the phrasing.** For each check that stands out, apply the
   move named beside the property. Re-derive the sentence from what it has to say; do not swap a
   flagged word for its nearest synonym, which keeps the pattern and hides it.
4. **Re-measure.** The pass ends when the checks moved, not when the text feels better. If a check
   did not move, the rewrite was cosmetic.
5. **Leave one line of trace, outside the text:** in your envelope's `evidence` (or, as the lead,
   nowhere — the reply itself is the trace), which properties you measured and what changed. No
   tallies in the delivered text, and no sentence in it that says it was checked.

## The properties — what to check, what the answer means, what to do

Each property is stated as a definition, a check and a move, with as many illustrations as the class
needs and no more: for some of them the check is a count, for the rest it is the definition itself
read against the text, the examples are illustrations, and a text can be free of every example on
this page and still fail the check (the last section says the same from the other side). What this
is NOT is a closed list of phrases to forbid — that is the shape the sources take, and a list ages
with the next model while the property survives it. Where a number is quoted it carries its source;
the numbers are there to show the tell is measured, not to set a threshold you tune the text to.

**1. Sentence-length variance ("burstiness").** Count words per sentence. Machine prose parks
every sentence in one band — the same length, the same shape, paragraph after paragraph — while a
person writes a long sentence that carries a qualification and then a short one. Three
sentences in a row within a few words of each other is the tell; a paragraph with no short
sentence in it at all is the tell. Measured: The Economist (2026, 55,940 sentences, 1.2 M
words, its own articles against ChatGPT, Claude, Gemini and Grok) found the models' sentences
longer than its writers', with fewer commas and semicolons and hardly any parentheses. *Move:*
merge two even sentences into one that subordinates, cut one to a fragment that lands the point,
let one run where the thought runs.

**2. Dash and colon density.** Count every dash that suspends a sentence to insert a second
thought, and every colon that announces a reveal rather than introducing something enumerable.
The tell is not the mark, it is the mark doing a comma's, a full stop's or a relative clause's
job. The density is model-dependent and ages, which is why this is a property and not a ban:
GPT-4.1 was measured at 3.28× the human em-dash frequency in standard essays (Freeburg, cited by
McGill's Office for Science and Society, May 2026), while The Economist's 2026 comparison found only
Claude above its human baseline and ChatGPT markedly below it. *Move:* for each mark, ask what the
sentence loses without it; usually nothing, and the two halves become two sentences or one with a
relative clause. In German a further tell rides on the glyph itself (see the German layer).

**3. Hedging stack depth.** For each claim, count the qualifiers on it (could, possibly, to some
extent, in many cases). One is a position; two on the same claim cancel each other and assert
nothing; a stack on a claim the catalogue makes flatly is a claim you did not check. *Move:* if the
thing is uncertain, say WHAT is uncertain and why, in one qualifier; if it is not, delete them all.

**4. Discourse-marker frequency.** Count the sentences that open with a connective adverb which
announces a relation instead of making it — a "moreover" or "furthermore", an "in conclusion".
People carry the relation in the content, in "und"/"aber"/"weil", or in nothing at all. *Move:*
delete the marker. If the sentence then has no reason to follow the one before it, the paragraph
has a structure problem, and that is the real finding.

**5. Structural reflexes.** Two counts. (a) The **rule of three**: adjectives, examples and items
arriving in exactly three regardless of how many the content has. Ask whether there ARE three;
if there are two, write two. (b) **"Not X but Y"** as a default connector — a negated
assumption nobody held, followed by the expansion: "not just a bottle, but a companion". Barron's
counted this construction in US company filings: 49 documents in 2023, 100 in 2024, 208 in 2025
(reported April 2026). *Move:* ask who claimed X. Nobody did; state Y.

**6. The closing-summary reflex.** Read the last paragraph and ask what is lost if it goes. A
paragraph that restates the text, a rhetorical question to the reader, or a hopeful sentence
about the future carries nothing. *Move:* a product text ends on its last fact or the call to
action the guidelines name; a report on the conclusion its template names; a reply on the thing
the user has to decide. Delete the rest.

**7. Empty intensifiers and significance inflation.** For each evaluative adjective and each
"plays a central role"-shaped framing, name the attribute in the catalogue, the evidence or the
brief that backs it. "Hochwertig" with no material behind it, "innovativ" with no difference
named, "einzigartig" with nothing it is compared to. *Move:* replace the adjective by the
attribute (the steel grade, the weight, the number) or cut it. The office product-editor's own
text standard (its procedure skill) makes the same point from the product's side.

**8. Elegant variation.** One referent, rotating names — the product, the article, the model, the
solution — so the reader re-identifies it each time. People reuse the name. *Move:* one name per
thing, and a pronoun where the name would be heavy.

**9. Assistant register.** Sentences addressed to a chat partner rather than to the reader of the
text: an eager opener, a meta-remark about the text itself, an offer of further help, an apology.
None of them exists in a product page or a letter. *Move:* delete; if the sentence carried a fact,
keep the fact.

**10. Predictable vocabulary.** A word that appears in every text of the genre regardless of
subject names nothing about this subject — the statistically likeliest word is the one a model
reaches for and the one a reader has stopped seeing. The check is not a banned list but a question
per word: would this word be here if the product were a different one? *Move:* the subject's own
vocabulary — its materials, its trade's terms, what the buyer calls it — which the brief and the
catalogue already hold.

## The German layer

German has tells English does not, and the register decides which apply: a product page, a post, a
letter and a chat reply speak TO a person and carry the particles and the verbs below; a
scientific report does not, and there items G3 and G5 are off by design.

**G1. Nominalstil against Verbalstil.** Count the sentences whose main verb is a light verb
(Funktionsverb) carrying a noun that used to be a verb: "die Reinigung erfolgt", "eine Prüfung
vornehmen", "zur Anwendung kommen", "dient als", "stellt dar". A person says what someone does:
"Sie reinigen es", "prüfen", "ist". *Move:* find the person and the action hidden in the noun and
make them subject and verb.

**G2. Anglicisms and calques.** Count the words and structures that are English underneath: a
marketing word German has its own word for, and a phrase translated whole so that it is
grammatical German nobody says. The test per item is the one property 10 asks, turned on the
language: would the trade, or the buyer, say it in German? An English word the trade itself uses (a
"Display", a "Laptop") is the subject's vocabulary and stays; a word that arrived with the
model's English default is the tell. Of the first kind: "seamless"/"nahtlos", "Ecosystem",
"Best Practices"; of the second: "macht Sinn", "am Ende des Tages", "Herausforderung" where the
thing is a Problem, and "nicht nur … sondern auch" as the reflex of property 5b. *Move:* the
word the guidelines or the catalogue use; where they use none, the German one.

**G3. Modal particles — MISSING is the tell.** German addressed to a person carries modal
particles that hold the speaker's stance — "schon", "mal", "ja", "doch", "eben", "eigentlich",
"wohl". Machine German is scrubbed of them: a page of copy that speaks to the reader with none is
a text nobody stands behind. The opposite failure exists too — particles sprinkled in to sound
casual — and both are the same property read in two directions: a particle carries a stance, so it
belongs where the writer has one. *Move:* where the text takes a position ("das reicht für einen
Tag" → "das reicht schon für einen Tag"), let the particle carry it; nowhere else. OFF in a report.

**G4. The dash glyph.** German typography sets the Gedankenstrich as a spaced en dash (" – ");
an unspaced em dash ("—") inside German text is an English import and a tell by itself, before
any density is counted. *Move:* property 2 first (does the sentence need the dash at all), then
the glyph.

**G5. "kann" as the absorbing modal.** Count "kann"/"können" where the product simply does the
thing: "kann bis zu 750 ml fassen" for a bottle that holds 750 ml. The modal takes the commitment
out of a fact the catalogue makes. *Move:* the indicative. Keep "kann" where a capability really
is conditional, and then say on what. OFF in a report, where the modal is the honest form.

**G6. Openers and closers that fit any text.** An opening sentence that could open a text about
anything ("In der heutigen digitalen Welt …", "Tauchen Sie ein in …", "Entdecken Sie …") and a
closing one that could close anything ("Zusammenfassend lässt sich sagen …", "Abschließend …", a
question to the reader). These are properties 4 and 6 in German dress; they are named here because
the German forms are the ones the users' texts carry. *Move:* open on the fact the reader came
for; close as property 6 says.

**G7. Form of address and register drift.** "Sie" or "du" is the brief's decision (the guidelines'
`tone`), and a text that switches mid-page, or pairs a formal "Sie" with a slangy particle, has
drifted. *Move:* one form, the brief's, throughout.

## What this skill does not do, said here so nobody reads it in

Nothing measures whether a role applied it: the trace is the one envelope line the procedure asks
for, and that is a duty with no gate, on purpose. It carries no list of words to forbid, so a text
can be free of every example above and still read as machine prose — the checks decide, the
examples illustrate. It does not know your product: the vocabulary that replaces the
predictable one comes from the brief and the catalogue, and a draft written without them has a
missing input, which you hand back, not a style problem.
