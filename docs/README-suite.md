# Shared Skills Suite

A small suite of **provider-neutral** skills for intent-driven development,
verification, repair, audit, and follow-up capture. The suite assumes a
governing artifact can exist upstream, often a Durable Intent Brief, but the DIB
authoring skill itself is not part of this repo; it ships in the companion
`dib-system` repository.

Each skill is a self-contained doctrine document. None is tied to a particular
agent platform. Provider-specific mechanics live only in each doc's
**Provider notes** section.

## The Five Skills

| Skill | What it is |
|---|---|
| `completeness-map` | A derived, regenerable sidecar that expands a governing artifact's completion boundary into an exhaustive **implication map** of closure dimensions: consumers, surfaces, done-state, implied layers, anti-shortcuts, scope, and open questions. |
| `auto-evals` | A package-generation workflow that turns governing law into executable scenarios, independent verification, explicit verdicts, and a structured repair queue. |
| `root-cause` | A systemic debugging workflow that verifies code paths, classifies discrepancies into reusable issue families, analyzes blast radius, and chooses the right repair action bucket. |
| `deferrals` | A thin, one-markdown-file-per-project ticket system for "revisit later" work, with stable ids and transferable context. |
| `orthogonal-audit-review` | A principles-only review guardrail: inspect one non-trivial artifact from genuinely orthogonal stances, then keep only findings whose cited evidence is re-verified. |

Roughly, the suite splits into **completion expansion** (`completeness-map`),
**verification and repair** (`auto-evals`, `root-cause`), **audit**
(`orthogonal-audit-review`), and **follow-up capture** (`deferrals`).

## Partial Adoption

**Every skill is adoptable on its own.** You can take exactly one, and the rest
simply do not fire. The dependencies below are the real edges; a skill's own
"Partial Adoption" section is the fuller account.

| Skill | Hard dependency | Natural companions |
|---|---|---|
| `completeness-map` | An upstream governing artifact that declares a completion boundary: a DIB, or any equivalent intent document with a "what complete looks like" statement. | `deferrals` supplies tracker references for accounted-but-open completion dimensions. |
| `auto-evals` | Governing law to derive scenarios from. For its structured repair handoff, `root-cause` is the in-repo companion workflow; without invoking it, the handoff can still be populated manually. | `completeness-map` is a strong upstream input because it names the closure dimensions scenarios should cover. |
| `root-cause` | A concrete symptom set and access to the code paths, contracts, catalogs, or evidence rails that may explain it. | `auto-evals` is a natural caller after verification finds failure families. |
| `deferrals` | A place to store one Markdown file per project, plus read/write access to it. | Any skill can hand postponed work to it. |
| `orthogonal-audit-review` | None beyond access to the artifact and cited evidence. | Domain-specific audit adapters can specialize its stance triad, but the general spine stands alone. |

## What Breaks When Adopted Poorly

- A completeness map collapsed into a todo list reproduces the exact failure it
  exists to prevent.
- Auto-evals walkthrough mode without genuinely separate agents silently
  forfeits holdout assurance while still producing plausible output.
- Root-cause without code-path verification becomes a dressed-up guess.
- Orthogonal audit needs both parallax and verification; either one alone is
  weak.
- Deferrals without transferable context becomes a scratch note that future
  agents cannot act on.

## Provider-Neutral Posture

The doctrine in every doc is written to be legible to capable agents of any
family. Platform-specific mechanics are quarantined in **Provider notes**: how a
skill is invoked, how separate lanes are spawned, how large-context reading is
handled, and where local state is stored. Adopting the suite on one platform
means maintaining only that platform's mechanics; the doctrine above that line
does not change.

## Use the Whole Suite, or One Skill

One skill is the right call for a point need. Want durable postponed-work
tickets? Adopt `deferrals`. Need a disciplined second pass over risky edits?
Use `orthogonal-audit-review`. Need to avoid patching symptoms one by one?
Invoke `root-cause`.

The whole suite compounds when work is governed by durable intent and must be
verified honestly: a governing artifact declares intent; a completeness map
makes the completion boundary explicit; auto-evals checks behavior from the
outside in; root-cause turns failures into reusable repair families; orthogonal
audit checks reasoning from different stances; deferrals catches what is
intentionally postponed.
