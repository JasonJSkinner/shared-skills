# Shared Skills Suite

A small suite of **provider-neutral** skills for intent-driven development,
verification, repair, audit, governance reading, orchestration, archival, and
follow-up capture. The suite assumes a governing artifact can exist upstream,
often a Durable Intent Brief, but the DIB authoring skill itself is not part of
this repo; it ships in the companion `dib-system` repository.

Each package carries its own doctrine and supporting assets. None is tied to a
single agent platform, though explicitly optional operations can require a
separate governance tool or provider integration. Provider-specific mechanics
live in each doc's **Provider notes** section.

## The Eight Skills

| Skill | What it is |
|---|---|
| `accomplishment-archive` | A completion workflow that writes a human-readable report and preserves a verified full or curated copy of the shipped artifact. |
| `completeness-map` | A derived, regenerable sidecar that expands a governing artifact's completion boundary into an exhaustive **implication map** of closure dimensions: consumers, surfaces, done-state, implied layers, anti-shortcuts, scope, and open questions. |
| `auto-evals` | A package-generation workflow that turns governing law into executable scenarios, independent verification, explicit verdicts, and a structured repair queue. |
| `root-cause` | A systemic debugging workflow that verifies code paths, classifies discrepancies into reusable issue families, analyzes blast radius, and chooses the right repair action bucket. |
| `deferrals` | A script-backed, project-scoped ticket system for "revisit later" work, with stable ids, transferable context, atomic writes, and integrity checks. |
| `governance-read-access` | A bounded read workflow for decisions and deferrals, plus a structured request boundary for lanes that may propose but not apply governance changes. |
| `orchestrator-posture` | A lead-agent stance that routes work by context cost, requires independent verification, and keeps final acceptance with the lead. |
| `orthogonal-audit-review` | A principles-only review guardrail: inspect one non-trivial artifact from genuinely orthogonal stances, then keep only findings whose cited evidence is re-verified. |

Roughly, the suite splits into **completion expansion** (`completeness-map`),
**verification and repair** (`auto-evals`, `root-cause`), **audit**
(`orthogonal-audit-review`), **follow-up and governance** (`deferrals`,
`governance-read-access`), **execution leadership** (`orchestrator-posture`),
and **completion archival** (`accomplishment-archive`).

## Partial Adoption

**Every skill is adoptable on its own.** You can take exactly one, and the rest
simply do not fire. The dependencies below are the real edges; a skill's own
"Partial Adoption" section is the fuller account.

| Skill | Hard dependency | Natural companions |
|---|---|---|
| `accomplishment-archive` | A completed source artifact, an archive destination, and a byte/diff verification mechanism. | Version and audit metadata improve the report when present. |
| `completeness-map` | An upstream governing artifact that declares a completion boundary: a DIB, or any equivalent intent document with a "what complete looks like" statement. | `deferrals` supplies tracker references for accounted-but-open completion dimensions. |
| `auto-evals` | Governing law to derive scenarios from. For its structured repair handoff, `root-cause` is the in-repo companion workflow; without invoking it, the handoff can still be populated manually. | `completeness-map` is a strong upstream input because it names the closure dimensions scenarios should cover. |
| `root-cause` | A concrete symptom set and access to the code paths, contracts, catalogs, or evidence rails that may explain it. | `auto-evals` is a natural caller after verification finds failure families. |
| `deferrals` | The bundled Python CLI, a writable project store, and Python 3. Index and archive mutation must use the CLI. | Any skill can hand postponed work to it. |
| `governance-read-access` | Deferral reads use the bundled deferrals CLI. Decision projection requires the separate decisions `state.sh`; applying a proposed governance update requires an authorized provider-side updater. A missing prerequisite stops that operation rather than enabling a bypass. | `deferrals` supplies the bundled ticket substrate. |
| `orchestrator-posture` | A lead-owned multi-part task and a way to run acceptance checks. Optional recording needs the bundled scripts plus provider-specific lifecycle integration. | Independent build and verification lanes. |
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
- Governance reads without projection and bounded ranges can pull stale or
  unrelated authority into the task; a missing mutation prerequisite is a stop,
  not permission to edit directly.
- Orchestration without a lead-owned acceptance pass mistakes lane completion
  for delivery.
- An accomplishment archive without copy verification is only a report, not a
  reliable record of what shipped.

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
Invoke `root-cause`. Need a bounded governance read, a context-protecting lead
stance, or a verified completion record? Use `governance-read-access`,
`orchestrator-posture`, or `accomplishment-archive` respectively.

The whole suite compounds when work is governed by durable intent and must be
verified honestly: a governing artifact declares intent; a completeness map
makes the completion boundary explicit; auto-evals checks behavior from the
outside in; root-cause turns failures into reusable repair families; orthogonal
audit checks reasoning from different stances; deferrals catches what is
intentionally postponed; governance access reads durable authority safely;
orchestrator posture coordinates multi-part execution; accomplishment archive
preserves the verified result.
