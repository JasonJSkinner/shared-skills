---
name: orthogonal-audit-review
description: Lightweight conceptual guardrail for reviewing non-trivial work products (edits made at high context, multi-file refactors, long-form prose, DIB drift checks, skill edits outside of skill-edit-audit's scope). Auto-invoke when the user asks to "audit", "review for hallucinations", "sanity-check", "second-pass", or after a large batch of edits lands and no domain-specific audit skill applies. Applies the orthogonal-framing principle — multi-lane reframing creates cognitive parallax (not just wider coverage) + finding-verification — as guidance, not machinery. Defer to skill-edit-audit (or future adapters like code-edit-audit) when one fits; this skill is the fallback and the principle-teacher. Formerly named triangulated-audit.
version: 0.3
---

# Orthogonal Audit Review (v0.3, principles-only)

## What this skill is

A **conceptual** audit harness. No scripts, no machinery, no metadata write-back.
Its job is to remind you — the orchestrator — of the orthogonal-framing principles
and make you apply them explicitly to the task at hand.

If a domain-specific adapter exists (e.g. `skill-edit-audit` for Claude skills,
future `code-edit-audit` for source code), **prefer that**. This skill is the
fallback when no adapter fits.

## When to invoke

- User asks to audit, review, sanity-check, or second-pass a non-trivial edit or document.
- A batch of edits landed at high context (>300K) and nothing domain-specific applies.
- Work crosses categories (e.g., skill + spec + prose) where no single adapter covers it.
- User explicitly invokes `/orthogonal-audit-review`.

Skip and defer if a domain-specific audit skill clearly fits the work product.

## The Core Insight — Cognitive Parallax

**Orthogonal framings do not just widen coverage. They create cognitive parallax.**

Three agents running the same framing produce correlated noise — they all read
the artifact from the same epistemic stance, so they share blind spots. Running
that single framing more times does not close the gap; it amplifies one angle.

The win from orthogonality is not merely that each lane looks at different
*surfaces*. It is that each lane forces a different *stance*:

- **Some hallucinations only collapse under a stance they were not written to satisfy.**
- A line that reads as "part of a coherent internal document" fractures when
  re-framed as "a claim about reality that must cash out elsewhere."
- The artifact is internally self-consistent from one angle and falsifiable
  from another. Only the second angle perturbs the reviewer's reasoning
  enough to break the local coherence illusion.

**Verification is what confirms what parallax exposes.** Finding-verification
prevents the expanded surface from bloating with false positives. Parallax +
verification together raise fidelity; neither alone does.

See `references/cognitive_parallax.md` for the long form (human-facing essay).

## The Principles

### 1. Orthogonal framings → cognitive parallax

Three lanes, each with a structurally different epistemic stance. Default triad:

- **Closed-universe** — "Does every claim resolve against the artifact itself?"
  Stance: treat the artifact as a self-contained document. Catches internal
  inconsistency, stale hashes, dead pointers.
- **Open-universe** — "Do the claims about the outside world actually hold?"
  Stance: treat the artifact as a set of externally-verifiable claims. Catches
  hallucinated paths, invented symbols, drifted external state.
- **Rubric-grade** — "Against the quality bar, is this adequate?"
  Stance: treat the artifact as a deliverable against a standard. Catches
  thin reasoning, missing edge cases, clarity gaps.

Adapt the triad when the work calls for it (prose: coherence / factual claims /
voice & craft). The triad must hold **orthogonality of stance**, not just of
surface — if all three lanes reason the same way about the artifact, you have
collapsed back to single-framing-repeated.

### 2. Verification beats voting

Cross-lane agreement is correlated noise (the lanes share the artifact text).
A finding is only promoted from "observation" to "issue" after its cited
evidence is **re-fetched** and confirmed.

- Typed `claim_kind` + evidence pointer per finding.
- Verification re-fetches the evidence and either confirms or drops.
- Severity is assigned **post-verification**, based on impact — not on how
  many lanes surfaced the same item.

### 3. The reconciler sees less than the lanes

No fourth synthesis agent that votes across lane outputs without evidence.
The reconciler dedupes, groups, and orders. Disputes go back for
verification, not a vote.

### 4. Graceful degradation

One honest lane beats three padded lanes. If only one framing is feasible,
run it and say so. Do not fabricate the others.

## Workflow (when invoked)

1. **Name the artifact and the three lane framings** in one short paragraph.
   If you cannot name three framings that force *orthogonal stances*, stop and
   tell the user — this work may not benefit from parallax.
2. **Run the lanes.** Each lane outputs observations with typed claim_kinds and
   evidence pointers. Use a capable synthesis model when judgment dominates and
   a lighter model only for purely mechanical checks.
3. **Verify.** For each observation, re-fetch the cited evidence. Keep only
   confirmed findings.
4. **Report.** Grouped by severity, with evidence pointers. No metadata write-back,
   no VERSION.json touching, no archiving. Plain markdown or inline summary.

## What this skill deliberately does NOT do

- No sidecar files, no VERSION.json writes, no audit metadata persistence.
- No scheduling, no heartbeat, no auto-bootstrap, no batch/sweep mode.
- No domain-specific rubrics — those belong in adapters.
- No severity engine beyond "issue / nit / false-positive-dropped".

Keep it conceptual. This is the principle, not the product.

## Relationship to other skills

- **`skill-edit-audit`** (v0.1, first adapter): domain adapter for Claude
  skill edits. Adds skill-specific rubric, lane checklists, AUDIT.json
  write-back, and recurring-pattern memory surfacing. Prefer when auditing a skill.
- **`code-edit-audit`** (planned): a future adapter
  for source code edits. Will adapt the stance triad for code: closed-universe =
  function-level coherence; open-universe = call sites, types, tests; rubric =
  code-review standards.
- **`artifact-alignment-check`** (planned): future
  adapter for **pair-wise artifact alignment** — auditing whether two artifacts
  in an authority chain agree (DIB↔PCB, PCB↔Spec, Spec↔Impl). Distinct from
  `skill-edit-audit`: that adapter runs error-class lanes on a *single*
  artifact, whereas this one runs direction-of-alignment lanes on an artifact
  *pair*. Unbuilt — the spine names it; the adapter itself is post-v4-sprint work.
- **`hallucination-check`** (existing): narrower — verifies assistant claims
  in JSONL against filesystem. Conversation-scope, not work-product-scope.
- Future adapters: DIB drift (`dib-alignment-check` — the DIB-specific
  narrowing of the general `artifact-alignment-check` above), prose manuscript
  audit, prompt audit — each applies the principle with domain-specific rubrics.

## Guardrails

- Do not grow machinery. If you feel the urge to add metadata write-back,
  scheduling, or severity engines, that belongs in an adapter.
- Do not run this skill in parallel with a domain adapter — pick one.
- Do not invoke on trivial edits. Parallax has overhead; reserve it for work
  where a single-stance miss would hurt.

## Rename note

This skill was previously named `triangulated-audit`. It was renamed
to `orthogonal-audit-review` when the core insight was sharpened:
orthogonality's win is **cognitive parallax** (different epistemic stances
exposing stance-specific hallucinations), not just broader coverage across
surfaces. The old framing understated what makes this technique powerful.
