# Cognitive Parallax

*The long-form companion to this skill's `SKILL.md` — why orthogonal stances beat repeated coverage.*

This essay expands the `SKILL.md` section "The Core
Insight — Cognitive Parallax": that section is the operative short form, this one is the reasoning
behind it. Where the two appear to differ, the `SKILL.md` governs.

---

## The coverage intuition, and why it is incomplete

"More eyes find more bugs" is a reliable intuition, and it is true: three readers catch more than
one. So when an audit is built from LLM lanes, the obvious way to harden it is to add lanes — more
passes, more coverage. That instinct is not wrong. It is incomplete, and the incompleteness is the
reason this skill exists.

Coverage counts one thing: how much of the artifact's surface has been examined. It is silent about
a second variable that matters as much — *what kind of question each lane asks*. Three lanes can
examine the whole artifact exhaustively and still all ask the same question. When they do, they do
not triangulate; they agree. Agreement among lanes that share a question is not confirmation. It is
an echo.

The failure has a precise shape. Lanes built from the same epistemic stance share that stance's
blind spots, so a defect the stance cannot see is invisible to all of them at once — not through
carelessness, but because the question that would expose it was never asked. Running the stance
again does not help: it raises confidence without raising fidelity, the worst direction to move.

## Parallax: the metaphor, made exact

The word comes from optics, where it is exact. Parallax is the apparent shift in an object's
position when you view it from two vantage points. Hold up a finger, close one eye, switch eyes:
the finger jumps against the background. Neither eye is wrong; the finger did not move. The *jump* —
the disparity between the two views — is real information that neither eye can produce alone. It is
depth. Two eyes see depth not because they see more of the scene than one eye would, but because
they read the difference between two positions. One eye, staring for an hour, never recovers depth.

Cognitive parallax is that mechanism applied to review. The "object" is a claim in the artifact.
The "vantage points" are epistemic stances — structurally different questions put to the same text.
A claim viewed from one stance has an apparent position: it reads as fine, or thin, or broken. From
a different stance the same claim may sit elsewhere. That disparity is the signal. A claim that
holds its position under every stance is solid; a claim that shifts — sound from here, falsifiable
from there — is exactly where a defect, or a hidden strength, hides.

This is why the metaphor is load-bearing, not decorative. Depth is recoverable from disparity
between vantage points, never from duration at one vantage point. Coverage is duration. Parallax is
disparity. Only one of them sees depth.

## Stance, not surface

The distinction the skill turns on is between a *surface* and a *stance*. A surface is which part
of the artifact you look at — this section, that file. A stance is the kind of question you bring
to whatever you look at. Coverage varies the surface and holds the stance fixed. Parallax varies
the stance, and can hold the surface fixed: three lanes, the same text, three irreconcilable
questions.

The skill's default triad is three stances:

- **Closed-universe** — *does every claim resolve against the artifact itself?* Treats the artifact
  as a self-contained world; satisfied by internal consistency.
- **Open-universe** — *do the claims about the outside world actually hold?* Treats the artifact as
  a set of bets on reality; satisfied only when those bets are checked.
- **Rubric-grade** — *against the quality bar, is this adequate?* Treats the artifact as a
  deliverable; satisfied by adequacy, not mere correctness.

Each can be pointed at the whole artifact. They are not a division of labour across surfaces; they
are three different things to *want* from one text. A line can be flawless under the
closed-universe stance — perfectly consistent with its neighbours — and false under the
open-universe stance, because the reality it asserts does not exist. The first stance has no
instrument that registers the falsehood; the second does. The line shifts between them, and the
shift is the finding.

The discipline that makes a triad real is *orthogonality of stance*. If all three lanes, however
differently worded, reason about the artifact the same way, the triad has collapsed into one stance
with three names — and you are back to coverage. Orthogonality is the precondition for parallax.

## The four principles

The `SKILL.md` states four principles. Each follows directly from taking parallax, not coverage, as
the goal.

### 1. Orthogonal framings create cognitive parallax

Build the lanes so each forces a structurally different stance, and adapt the triad to the work:
the default closed / open / rubric triad fits many artifacts; prose may want coherence /
factual-claims / voice-and-craft. What may never vary is that the stances be genuinely orthogonal.
The test is unforgiving — if you cannot name three framings that ask structurally different
questions, you do not have a parallax job, and the skill says to stop and report that rather than
stage a fake one.

### 2. Verification beats voting

Because the lanes all read the same text, cross-lane *agreement* is correlated noise: three lanes
agreeing may mean a claim is sound, or may mean it reads the same way three times — lane outputs
alone cannot tell you which. So agreement promotes nothing. A finding becomes an issue only when
its cited evidence is *re-fetched* and confirmed; each finding carries a typed claim and an
evidence pointer for exactly that. Severity is assigned afterwards, on demonstrated impact — never
on lane count.

### 3. The reconciler sees less than the lanes

It is tempting to add a fourth agent that reads every lane's output and adjudicates. That agent is
dangerous: it sees *less* than the lanes did — their summaries, not the artifact and the evidence —
and an adjudicator with less information than its sources can only vote. The reconciler's job is
clerical: dedupe, group, order. A disagreement between lanes goes back to verification, where
evidence settles it, not to a majority.

### 4. Graceful degradation

One honest lane beats three padded lanes. If only one stance can be genuinely framed, run it,
report one lane's worth of findings, and say so plainly. The failure mode to fear is not too few
lanes but *fake* lanes — a second and third that are the first reworded and presented as parallax.
That is worse than one honest lane: it manufactures the appearance of disparity where there is
none, and a reader trusts a three-lane result more than a one-lane result.

## A worked example: the finding one stance could see and two could not

The clearest demonstration of cognitive parallax in practice comes from a validation
pass that took multiple Durable Intent Briefs and companion specifications through a canonization gate.
It ran three
orthogonal validation lanes — an adaptation of the default triad to the job of validating an
artifact stack:

- **Realization** (Lane 2) — walk downward: is every DIB intent realized somewhere in the spec
  stack? Treats the stack as a correspondence problem.
- **Justification** (Lane 3) — walk upward: is every spec chunk justified by a DIB intent? The
  mirror stance; nothing in the specs should exist without a traceable reason.
- **Scenario walkthrough** (Lane 1b) — take a concrete operational scenario and run it through the
  specs as if it were happening: what does the system actually do, step by step? Treats the stack
  as a dynamical system, not a static correspondence.

Those scenarios were designed beforehand under strict holdout — the scenario lane's design phase
(Lane 1a), feeding the walkthrough phase (Lane 1b) above; the scenario authors never read the
specs. That holdout is what keeps the walkthrough stance independent: a scenario written by someone
who had read the specs would unconsciously route around their gaps.

From the realization and justification stances, the spec stack looked flawless. Realization came
back **41 of 41** DIB chunks realized. Justification came back **509 of 509** spec chunks justified
— zero orphaned, zero over-engineered, zero contradictory. Two thorough, independent lanes, and
between them not one defect. From a coverage mindset the conclusion is plain: examined from two
directions by two large lanes, passed both — ship it.

Both lanes even looked straight at the relevant clause. The Shared-Skills DIB carries what the
meta-synthesis calls a WCL anti-shortcut clause — one of the clauses governing when the layer's
work counts as genuinely complete — requiring, in as many words, that *"cross-provider deploy must
be consumer-complete (not just one provider)."* Realization saw that clause and correctly marked it
realized at the principle level. Justification saw the spec text around it and correctly traced it
to intent. Neither lane was careless; neither missed a surface. From their stances, the clause *was*
satisfied.

Then the scenario-walkthrough stance asked a different kind of question. Scenario S05 walked the
publish pipeline across three providers — Claude, Codex, and Gemini — and asked: what happens when
one provider's publish succeeds and another's fails partway through? The specs had no answer. Spec
02's atomic-write guarantee (§5.3) is per-artifact — it makes one provider's write all-or-nothing
but says nothing about the *set* of providers. The edit-lease machinery (§8) covers the canonical
mutation cycle but is silent on cross-provider rollback, retry, or surfacing of a partial publish.
The system could leave two providers updated and one stale, with no specified detection, no
rollback, and no signal that it had happened. That finding — **F01** — was rated **BLOCKING**, the
only blocking finding in the pass.

Here is the parallax point. F01 is *not* something the realization and justification lanes missed.
They examined the same clause and were correct: "cross-provider deploy must be consumer-complete"
*is* present and *is* realized at the principle level. What the realization stance structurally
cannot ask is *"and what enforces it when a provider fails at 2 a.m.?"* That question does not
exist inside a correspondence frame — which is satisfied the moment intent maps to text. It exists
only inside a dynamical frame, where you run the scenario and watch the failure happen. The clause
shifted: from the realization stance it sat on "satisfied"; from the walkthrough stance, on "a
principle with no enforcing predicate at the partial-failure boundary." That disparity — two
stances, one identical clause, two positions — is the finding. Running the realization lane again
would never have produced it.

A note on confidence, which sharpens the example rather than weakening it. F01 was **single-lane**:
only S05 surfaced it, and the meta-synthesis is explicit that no finding in the pass was
triple-confirmed. It did not need to be. What it had instead was **corroboration by absence**: the
justification lane, scanning all 509 spec chunks, found zero addressing cross-provider
partial-failure in any form. Had the topic been handled somewhere, justification would have traced
a chunk to it; its silence is structural confirmation that the gap is real, not merely filed
elsewhere. F01 is best described as single-lane *plus structural confirmation* — itself a form of
parallax: an absence in one stance corroborating a presence in another.

Two things make F01 the right teaching example. First, it is a *surgical* gap, not a broken stack:
41 of 41, 509 of 509, zero contradictions — by every static measure the architecture was sound, and
F01 is a hairline crack in a sound wall. A coverage mindset misvalues that — two big lanes passed,
so the residual risk reads as negligible. The parallax mindset reads it the other way: two stances
agreeing is *correlated comfort*, and the one stance that asked a structurally different question
found the one defect that blocks. The lesson is not that the specs were bad; it is that breadth of
agreement among similar stances is evidence of similarity, not of soundness. Second, F01 is a
genuine anti-shortcut violation: the clause was present and principle-level-realized yet unenforced
at the partial-failure boundary, and a principle with no validator predicate is a closure envelope
drawn wide enough to permit drift — the artifact can claim the principle and still behave as if it
did not hold. The meta-synthesis names this as the canonical anti-shortcut the Root DIB's own WCL
clause exists to forbid. Parallax is the instrument that tells *"the principle is stated"* apart
from *"the principle is enforced"* — readings that coincide under a correspondence stance and
diverge only under a dynamical one.

The essay stops there. F01's repair is a genuine architectural decision, and the validation pass
routed it to human judgment with three candidate strategies: full cross-provider transactional
atomicity; bounded retry with explicit surfacing of partial state; or independent per-provider
publish plus a parity-check validator that loudly flags drift. Which to choose is a question of
cost and risk tolerance, not of audit technique. The example's point is upstream of the fix:
parallax made an invisible gap visible while there was still time to choose.

## Verification: what confirms what parallax exposes

Parallax and verification are a matched pair; the skill insists on both because each fails alone.
Parallax widens the surface of *candidate* findings — its purpose, and its hazard. Three
structurally different questions surface more candidate problems than one: more real ones, and more
false ones. Unchecked, parallax degrades into a longer list of maybes, which is not fidelity, only
noise. Verification is the counterweight: every candidate carries an evidence pointer, and
verification follows it, re-fetches the cited evidence, and keeps the finding only if the evidence
holds.

Neither substitutes for the other. Verification without parallax is a fast, confident pass over a
narrow view — it confirms what one stance already believed, blind spots intact. Parallax without
verification is a broad, anxious list of unconfirmed suspicions. Fidelity is the product of the
two: parallax exposes, verification confirms.

## When to reach for parallax

Parallax is not free. Three genuine stances and a verification pass cost real time and tokens, and
the skill is explicit that the technique is not for every edit. Run it on a trivial change and you
waste effort — worse, you dull the instrument by habituating to a heavy process that usually finds
nothing.

The test is not the size of the work but the *cost of a single-stance miss*. Reach for parallax
when a miss from one angle would be expensive to discover later: edits made at very high context,
where the editor's own stance is fatigued and narrowed; multi-file refactors; long-form prose;
drift checks on governing documents; anything constitutional. F01 is the cautionary case — a
single-stance pass over those specs, however thorough, would have certified a blocking gap into a
canonized artifact set, to surface next as a real partial-publish failure in production. Parallax
bought the chance to see it while it was still a line in a report.

## Sources and cross-references

This essay is the long-form companion to this skill's `SKILL.md`; it explains the principle, it
does not extend it. Where the two appear to differ, the `SKILL.md` governs.

- **`SKILL.md`** (this skill) — §"The Core Insight — Cognitive Parallax" and §"The Principles": the
  short form, the four principles stated operatively, and the workflow for running an orthogonal
  audit.
- **Skill architecture note** — the spine-versus-adapter architecture clarification for this skill.
  It identifies the substrate for the worked example.
- **The Phase C meta-synthesis** — the final-pass report of the DIB-consolidation
  canonization gate; the source of the worked-example figures and the
  single-lane-plus-absence confidence reading.
