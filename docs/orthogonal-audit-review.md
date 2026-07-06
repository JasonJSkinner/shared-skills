# Orthogonal Audit Review

A lightweight conceptual guardrail for reviewing a non-trivial work product — a batch of edits made under heavy context, a multi-file refactor, long-form prose, a drift check on a governing document, or any artifact where a single reviewer's blind spot would be expensive to discover later. It is a *principle*, not a piece of machinery: no scripts, no scheduling, no metadata write-back. Its job is to make you — the reviewer or orchestrating agent — apply the orthogonal-framing discipline explicitly to the artifact in front of you.

The technique reviews one artifact from several *independent, orthogonal stances* so that different failure modes are caught by different lenses, rather than all of them slipping past one reviewer's single point of view.

This skill is provider-neutral. The core is the doctrine; anything specific to how a given assistant platform invokes it, runs its lanes, or selects models is isolated in the **Provider notes** subsection so it can be swapped without touching the doctrine.

## When to Use

Reach for orthogonal audit review when the *cost of a single-stance miss* is high — not merely when the work is large. Good triggers:

- A batch of edits landed under very high context, where the editor's own stance is fatigued and narrowed.
- A multi-file refactor, where local correctness can hide a global inconsistency.
- Long-form prose or a governing document being checked for drift.
- Work that crosses categories (e.g. a definition plus a spec plus prose) so that no single domain-specific reviewer covers it.
- Anyone asks to "audit", "review for hallucinations", "sanity-check", or "second-pass" a non-trivial artifact and no narrower, domain-specific review applies.

If a domain-specific audit adapter clearly fits the work (see **Partial adoption**), prefer that. This skill is the fallback and the principle-teacher.

## The Core Insight — Cognitive Parallax

**Orthogonal framings do not just widen coverage. They create cognitive parallax.**

Coverage counts one thing: how much of the artifact's surface has been examined. It is silent about a second variable that matters as much — *what kind of question each lane asks*. Several lanes can examine the whole artifact exhaustively and still all ask the same question. When they do, they do not triangulate; they agree. Agreement among lanes that share a question is not confirmation. It is an echo. Running the same stance again raises confidence without raising fidelity — the worst direction to move.

The word *parallax* is borrowed from optics, where it is exact: the apparent shift in an object's position when viewed from two vantage points. Hold up a finger, close one eye, switch eyes — the finger jumps against the background. Neither eye is wrong; the finger did not move. The *jump* is real information neither eye can produce alone. That is depth, and depth is recoverable from the disparity between two vantage points, never from staring longer at one.

Cognitive parallax applies that mechanism to review. The "object" is a claim in the artifact. The "vantage points" are *epistemic stances* — structurally different questions put to the same text. A claim that holds its position under every stance is solid; a claim that shifts — sound from here, falsifiable from there — is exactly where a defect (or a hidden strength) hides. **Some defects only collapse under a stance they were not written to satisfy.** A line that reads as "part of a coherent internal document" fractures the moment it is re-framed as "a claim about reality that must cash out elsewhere."

**Stance, not surface.** A *surface* is which part of the artifact you look at. A *stance* is the kind of question you bring to whatever you look at. Coverage varies the surface and holds the stance fixed. Parallax varies the stance, and can hold the surface fixed: several lanes, the same text, several irreconcilable questions.

## The Orthogonal-Lanes Model

Run the artifact through a small number of lanes, each forcing a structurally different stance. A useful default triad:

- **Closed-universe** — *does every claim resolve against the artifact itself?* Treat the artifact as a self-contained world, satisfied by internal consistency. Catches internal inconsistency, stale references, dead pointers.
- **Open-universe** — *do the claims about the outside world actually hold?* Treat the artifact as a set of bets on reality, satisfied only when those bets are checked. Catches invented paths, non-existent symbols, external state that has drifted.
- **Rubric-grade** — *against the quality bar, is this adequate?* Treat the artifact as a deliverable against a standard, satisfied by adequacy rather than mere correctness. Catches thin reasoning, missing edge cases, clarity gaps.

Adapt the triad to the work — prose may want *coherence / factual-claims / voice-and-craft*. What may never vary is that the stances be genuinely **orthogonal of stance**, not merely of surface. The test is unforgiving: if you cannot name three framings that ask structurally different questions, you do not have a parallax job — stop and say so, rather than staging a fake one.

The teaching case, in the abstract: a clause can read as fully *satisfied* under a correspondence stance ("the required principle is present and maps to text") and yet, under a dynamical stance that runs a concrete failure scenario, turn out to be *unenforced* ("stated, but nothing makes it hold when things go wrong"). Same clause, two positions. That disparity is the finding — and no amount of re-running the first stance would ever surface it.

### The Four Principles

Each follows directly from taking parallax, not coverage, as the goal.

1. **Orthogonal framings create cognitive parallax.** Build each lane to force a structurally different stance. Orthogonality of stance is the precondition for parallax; without it, three lanes are one stance with three names.

2. **Verification beats voting.** Because the lanes all read the same text, cross-lane *agreement* is correlated noise — it may mean a claim is sound, or may mean it read the same way three times. Agreement promotes nothing. Each finding carries a typed claim and an evidence pointer; a finding becomes an *issue* only when its cited evidence is re-fetched and confirmed. Severity is assigned afterwards, on demonstrated impact — never on lane count.

3. **The reconciler sees less than the lanes.** Do not add a synthesizing agent that reads every lane's *output* and votes. Such an agent sees less than the lanes did — their summaries, not the artifact and the evidence — and can only vote. The reconciler's job is clerical: dedupe, group, order. A disagreement between lanes goes back to verification, where evidence settles it.

4. **Graceful degradation.** One honest lane beats three padded lanes. If only one stance can be genuinely framed, run it, report one lane's worth of findings, and say so plainly. The failure mode to fear is not too few lanes but *fake* lanes — a second and third that are the first reworded and presented as parallax. That manufactures the appearance of disparity where there is none, and readers trust a three-lane result more than a one-lane result.

## Workflow (when invoked)

1. **Name the artifact and the lane framings** in one short paragraph. If you cannot name framings that force genuinely *orthogonal stances*, stop and tell the user — this work may not benefit from parallax.
2. **Run the lanes.** Each lane outputs observations, each with a typed claim kind and an evidence pointer.
3. **Verify.** For each observation, re-fetch the cited evidence. Keep only confirmed findings; drop the rest.
4. **Report.** Grouped by severity, with evidence pointers. Plain markdown or an inline summary — no metadata write-back, no sidecar files, no archiving.

## When NOT to Use

- **Trivial edits.** Parallax has overhead. Run it on a one-line change and you waste effort — worse, you dull the instrument by habituating to a heavy process that usually finds nothing.
- **When a domain-specific adapter fits.** If a narrower, domain-tuned review exists for exactly this kind of artifact, use that instead. Do not run this skill *in parallel* with an adapter — pick one.
- **When you cannot frame genuinely orthogonal stances.** If every candidate lane reasons about the artifact the same way, there is no parallax to be had. Report that rather than staging fake lanes.
- **Conversation-scope claim checks.** Verifying an assistant's own recent statements against reality is a narrower, different job; use a conversation-scope checker, not a work-product audit.

## Partial Adoption

- **Dependencies.** Essentially none. This is a principles-only guardrail with no tooling, machinery, scheduling, or persistence to install. It runs on nothing but the reviewer's discipline and access to the cited evidence.
- **Optional layer — domain adapters.** The skill is a *spine*. Domain-specific adapters specialize the stance triad for a particular artifact class (for example: source-code edits, where closed-universe becomes function-level coherence, open-universe becomes call sites / types / tests, and rubric becomes code-review standards; or pairwise artifact-alignment, checking whether two artifacts in an authority chain agree). When an adapter fits, prefer it; the spine is the fallback. Adapters are optional — the spine stands alone.
- **What breaks if adopted in half.** The two operative principles — parallax and verification — are a matched pair, and each fails alone:
  - *Parallax without verification* degrades into a long, anxious list of unconfirmed suspicions. More stances surface more candidate problems: more real ones and more false ones. Unchecked, that is noise, not fidelity.
  - *Verification without parallax* is a fast, confident pass over a narrow view — it confirms what one stance already believed, blind spots intact.
  Fidelity is the product of the two: parallax exposes, verification confirms. Drop either and the technique stops earning its overhead.

## Provider notes

The core above is provider-neutral. These notes cover mechanics that differ by assistant platform; nothing here changes the doctrine.

- **Invocation.** How the skill is triggered — a slash command, an auto-invoke on review-intent phrasing, or manual selection — is platform-specific. The doctrine is the same however it is entered.
- **Lane execution.** Where a platform supports agent fan-out (Claude, Codex, and similar), the lanes can run as independent parallel jobs or subagents, which reinforces stance-independence because each lane is a separate context that cannot see the others' reasoning. Where fan-out is unavailable, run the lanes as sequential passes in a single context — same stances, same verification, just serialized. Parallelism is a performance and independence convenience, not a correctness requirement.
- **Model selection (capability roles, not tiers).** Assign a capable default model to each lane; escalate to a stronger model on the lane where synthesis judgment dominates; reserve a cheap, fast model only for purely mechanical checks. The mapping from these roles to a specific vendor's model lineup is a provider detail and should not be hard-coded into the doctrine.
- **Adapters.** Some platforms ship domain-specific adapters (for instance, an adapter for auditing edits to an assistant's own skill definitions). Prefer a fitting adapter over this general spine; use the spine when none fits.
