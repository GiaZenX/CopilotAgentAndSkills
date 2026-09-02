# Third-party material in this repository

One line per piece of third-party work this repository carries and redistributes. A kit is copied
into other repositories by `scaffold_team.sh` / `.ps1`, which is redistribution, so the duties are
the ones the source licence puts on a redistributor and not the lighter ones for private use.

| Source | What | Licence | State |
|---|---|---|---|
| `anthropics/skills` | `frontend-design` → `team-kits/dev-team/skills/frontend-design/` | Apache-2.0 | modified |
| `anthropics/skills` | `webapp-testing` → `team-kits/dev-team/skills/webapp-testing/` | Apache-2.0 | modified |

**What travels with the file and what stays here.** Apache-2.0 §4 asks a redistributor for three
things, and two of them have to reach the *installed project*, not just this repository: the
licence copy (`LICENSE.txt` sits inside each skill directory, so the scaffold copies it along with
the skill) and the notice that the file was changed (each `SKILL.md` says so in its own header, its
frontmatter names the upstream commit and blob hash it was adapted from, and every change is marked
inline). This table is the third thing and is a bookkeeping convenience for readers of THIS
repository — it is not what discharges the duty, and a project that has the kit installed will not
have it. §4(d) does not apply: the upstream skill folders ship no `NOTICE` file (measured 2026-07-27
and again 2026-08-31, `docs/research/2026-07-27-adoption-anthropic.md` §4).

**What is deliberately absent.** The four document skills (`pdf`, `docx`, `xlsx`, `pptx`) of the
same upstream repository are proprietary and forbid derivative works; `doc-coauthoring` carries no
licence at all. None of them is adopted, paraphrased or referenced as a source of rules anywhere in
this tree. The same measurement lists the community collections that were rejected for having no
licence.

The pair of properties this table has to keep — every vendored skill listed, and every listed skill
still present and still carrying its licence copy — is checked in
`tools/test_reference_skills.py::test_every_vendored_skill_is_listed_here_and_every_listing_resolves`
rather than trusted, because a table nobody reads is where an attribution rots first.
