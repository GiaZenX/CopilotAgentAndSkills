---
name: frontend-design
description: >
  REFERENCE skill (no role owns it): how to give a UI a distinctive, intentional visual identity —
  aesthetic direction, typography, motion, restraint, and UX writing. Open it when a work order
  names it. Adapted from anthropics/skills `frontend-design`. NOT loaded at session start and named
  by no role's `skills:` frontmatter — open it with `/frontend-design`. On Codex the generated
  mirror carries every skill directory, so it is also at `.agents/skills/frontend-design/SKILL.md`.
license: Apache-2.0 — complete terms in LICENSE.txt beside this file
source: https://github.com/anthropics/skills/tree/main/skills/frontend-design
source_commit: 2235be7c60b551f5de82ade908fd3816455afcda
source_blob_sha1: decdff43d05908b4c1fc2cfd2d80fc5743440934
modified: true
# WHICH ORDERS NAME THIS SKILL (FR-0071) -- read by `kernel.references.for_task`, which requires a
# match on BOTH axes, so a `docs` task for the designer does not arrive carrying it. The frontend
# is here because it inherits the frozen DSN and writes the CSS the last two sections are about.
reference_for:
  roles: [product-designer, frontend-developer]
  task_types: [design, ui]
---

# Frontend Design

> **Modified from the upstream file.** Copyright the original authors, Apache-2.0 (`LICENSE.txt`
> beside this file). The changes are marked inline as `[MOD-n]` and listed under "Modifications" at
> the end, and those two are held to each other by
> `tools/test_reference_skills.py::test_every_modification_mark_is_listed_and_every_listed_one_is_marked`.
> What that CANNOT see is an edit carrying no mark at all: no test here reaches the network. What
> makes such an edit findable is the provenance in the frontmatter — `source_commit` and
> `source_blob_sha1` identify the exact upstream bytes, so a later round re-fetches and diffs
> instead of trusting this banner.

Approach this as the design lead at a small studio known for giving every client a visual identity that could not be mistaken for anyone else's. This client has already rejected proposals that felt templated, and is paying for a distinctive point of view: make deliberate, opinionated choices about palette, typography, and layout that are specific to this brief, and take one real aesthetic risk you can justify.

## Ground it in the subject

If the brief does not pin down what the product or subject is, pin it yourself before designing: name one concrete subject, its audience, and the page's single job, and state your choice. The subject's own world, its materials, instruments, artifacts, and vernacular, is where distinctive choices come from. Build with the brief's real content and subject matter throughout.

> **[MOD-1] Where the brief comes from, and what to do when it is thin.** The upstream sentence
> continued "If there's any information in your memory about the human's preferences, context about
> what they're building, or designs you've made before – use that as a hint." In this kit the brief
> is the work order plus the items it names (`required_inputs`), and the constitution's memory
> boundary (§0) forbids project state in an agent's own memory — a preference remembered privately is one nobody
> can review. Read the design-brief Decision item (ambition, what it must achieve and for whom, tone,
> what it must not become) and the root's acceptance criteria instead. If
> what you need is genuinely missing, say so in `followups` and hand back: the manager asks the
> user, you do not.

## Design principles

For web designs, the hero is a thesis. Open with the most characteristic thing in the subject's world, in whatever form makes sense for it: a headline, an image, an animation, a live demo, an interactive moment. Be deliberate with your choice: a big number with a small label, supporting stats, and a gradient accent is the template answer, only use if that's truly the best option.

Typography carries the personality of the page. Pair the display and body faces deliberately, not the same families you would reach for on any other project, and set a clear type scale with intentional weights, widths, and spacing. Make the type treatment itself a memorable part of the design, not a neutral delivery vehicle for the content.

Structure is information. Structural devices, numbering, eyebrows, dividers, labels, should encode something true about the content, not decorate it. Many generic designs use numbered markers (01 / 02 / 03), but that's only appropriate if the content actually is a sequence - like a real process or a typed timeline where order carries information the reader needs. Question if choices like numbered markers actually make sense before incorporating them.

Leverage motion deliberately. Think about where and if animation can serve the subject: a page-load sequence, a scroll-triggered reveal, hover micro-interactions, ambient atmosphere. An orchestrated moment usually lands harder than scattered effects; choose what the direction calls for. However, sometimes less is more, and extra animation contributes to the feeling that the design is AI-generated.

Match complexity to the vision. Maximalist directions need elaborate execution; minimal directions need precision in spacing, type, and detail. Elegance is executing the chosen vision well.

Consider written content carefully. Often a design brief may not contain real content, and it's up to you to come up with copy. Copy can make a design feel as templated as the design itself. See the below section on writing for more guidance.

## Process: brainstorm, explore, plan, critique, build, critique again

For calibration: AI-generated design right now clusters around three looks: (1) a warm cream background (near #F4F1EA) with a high-contrast serif display and a terracotta accent; (2) a near-black background with a single bright acid-green or vermilion accent; (3) a broadsheet-style layout with hairline rules, zero border-radius, and dense newspaper-like columns. All three are legitimate for some briefs, but they are defaults rather than choices, and they appear regardless of subject. Where the brief pins down a visual direction, follow it exactly — the brief's own words always win, including when it asks for one of these looks. Where it leaves an axis free, don't spend that freedom on one of these defaults. Just like a human designer who's hired, there's often a careful balance between doing what you're good at and taking each project as a chance to experiment and learn.

Work in two passes. First, brainstorm a short design plan based on the human's design brief: create a compact token system with color, type, layout, and signature. Color: describe the palette as 4–6 named hex values. Type: the typefaces for 2+ roles (a characterful display face that's used with restraint, a complementary body face, and a utility face for captions or data if needed). Layout: a layout concept, using one-sentence prose descriptions and ASCII wireframes to ideate and compare. Signature: the single unique element this page will be remembered by that embodies the brief in an appropriate way.

Then review that plan against the brief before building: if any part of it reads like the generic default you would produce for any similar page (work through a similar prompt to see if you arrive somewhere similar) rather than a choice made for this specific brief — revise that part, say what you changed and why. Only after you've confirmed the relative uniqueness of your design plan should you start to write the code, following the revised plan exactly and deriving every color and type decision from it.

> **[MOD-2] "Write the code" here means the staged draft, and it is where your work ENDS.** Upstream
> the designing agent is also the building agent. Here the artifact you write is the self-contained
> HTML preview / per-view mockup under `project_memory/staging/<your task-id>/`, which the kernel
> freezes as a `DSN` revision on the user's approval. That frozen file is a CONTRACT handed down —
> the frontend implements it and QA compares screenshots against it. You never touch `src/**` or
> `frontend/**`. So "deriving every color and type decision from the plan" is not a private tidiness
> rule here: whatever is not in the frozen file is invented downstream by somebody who never saw
> your plan (a real run "recolored" four slices for exactly that reason).

When writing the code, be careful of structuring your CSS selector specificities. It's easy to generate CSS classes that cancel each other out (especially with a type-based selector like .section and a element-based selector like .cta). This can happen often with paddings/margins between sections.

> **[MOD-3] The upstream line "Try to do a lot of this planning and iteration in your thinking, and
> only show ideas to the user when you have higher confidence it'll delight them" is REMOVED, not
> softened.** You do not talk to the user at all — the PM does — and this harness has the error
> measured in its own history: a real PM asked the user to sign off on a summary that existed only
> in its thinking ("wie oben zusammengefasst") and the user decided blind. What replaces it: the
> iteration happens in the staged file, and it is looked at (see the two marks below) before anyone
> is asked anything.

## Restraint and self-critique

Spend your boldness in one place. Let the signature element be the one memorable thing, keep everything around it quiet and disciplined, and cut any decoration that does not serve the brief. Not taking a risk can be a risk itself! Consider Chanel's advice: before leaving the house, take a look in the mirror and remove one accessory.

> **[MOD-4] "Build to a quality floor without announcing it: responsive down to mobile, visible
> keyboard focus, reduced motion respected" is REPLACED by naming the floor.** A floor nobody states
> is a floor nobody can check, and an unstated one is what this repo keeps finding a defect behind.
> The numbers live in exactly one place — the `product-designer` skill's quality bar and the
> standards section under it (contrast ratios per text size, motion durations, the perception
> limit, the pointer-target minimum) — and are not repeated here, because a second copy of a number
> outlives the first.

> **[MOD-5] "Critique your own work as you build, taking screenshots if your environment supports
> it" is REPLACED by a mandatory loop.** Optional self-inspection is the failure `BUG-0076` is: a
> design revision reached the user twice with nobody having rendered it, and both rejections were
> things only pixels show. The loop is `python scripts/kit_design_render.py <your task-id>`, then
> READ every PNG it wrote, then fix — stated once, in the `product-designer` skill's SIGHT loop, and
> `gate_design_sighted` refuses a presentation whose draft has no render record.

> **[MOD-6] "Human creators have memory … if you have a space to quickly jot down notes about what
> you've tried, it can help you in future passes" is REMOVED.** The constitution's memory boundary (§0)
> forbids project state in agent memory. What you tried and discarded belongs in the result envelope and in
> `staging/<your task-id>/`, where the next pass — possibly a different session — can actually read
> it. A note only you can see is a note the retry does not have.

## More on writing in design

Words appear in a design for one reason: to make it easier to understand, and therefore easier to use. They are design material, not decoration. Bring the same intentionality to copy that you would bring to spacing and color. Before writing anything, ask what the design needs to say, and how it can best be said to help the person navigate the experience.

Write from the end user's side of the screen. Name things by what people control and recognize, never by how the system is built. A person manages notifications, not webhook config. Describe what something does in plain terms rather than selling it. Being specific is always better than being clever.

Use active voice as default. A control should say exactly what happens when it's used: "Save changes," not "Submit." An action keeps the same name through the whole flow, so the button that says "Publish" produces a toast that says "Published." The vocabulary of an interface is the signposting for someone navigating the product. Cohesion and consistency are how people learn their way around.

Treat failure and emptiness as moments for direction, not mood. Explain what went wrong and how to fix it, in the interface's voice rather than a person's. Errors don't apologize, and they are never vague about what happened. An empty screen is an invitation to act.

Keep the register conversational and tuned: plain verbs, sentence case, no filler, with tone matched to the brand and the audience. Let each element do exactly one job. A label labels, an example demonstrates, and nothing quietly does double duty.

## Modifications from the upstream file (Apache-2.0 section 4(b))

Six changes, each marked at the place it applies. The first three follow from ONE structural
difference and the last three from the house rules; the reason for keeping the rest verbatim is in
`docs/research/2026-07-27-adoption-anthropic.md` section 1, which judged the file sentence by sentence.

- **[MOD-1]** the memory hint dropped; the brief is the work order, a gap is handed back
- **[MOD-2]** "write the code" narrowed to the staged draft, which is frozen and handed down
- **[MOD-3]** "plan in your thinking, then show the user" removed — you do not talk to the user
- **[MOD-4]** "quality floor without announcing it" replaced by a pointer to where it is announced
- **[MOD-5]** optional screenshots replaced by the mandatory render-and-look loop
- **[MOD-6]** the private notes hint removed — state lives in staging and in the envelope
