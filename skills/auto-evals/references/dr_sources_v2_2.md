# DR-Sourced Governing Law (v2.2)

Use this reference whenever Decision Records (DRs) are among the governing inputs. It extends the existing DIB/PCB/spec flow; role separation, holdout protection, verifier independence, and repair handling do not change.

## Authority and disposition gate

Apply governing authority in this order:

1. DIB
2. accepted DR
3. PCB
4. spec

A DR-only input is sufficient governing law. Do not decline eval generation merely because no DIB or PCB exists.

Read the DR's exact `Disposition` before deriving scenarios:

| Disposition class | Scenario effect |
|---|---|
| `Accepted as Implementation Choice` or `Incorporated [date]` | The DR's decisions may produce binding strict-contract scenarios. |
| `Greenlit — scope locked` | Binding strict-contract scenarios WITHIN the locked scope; anything the DR discusses outside that scope yields probe-class only. |
| Proposed/pre-acceptance (`Pending Review`, `Pending Human Approval`, or `Incorporation Candidate`) | Produce probe-class scenarios only. They must not fail a strict gate. |
| Any disposition string not listed here | Treat as pre-acceptance: probe-class only. The gate is fail-closed over unknown vocabulary. |
| `Rejected` or `Superseded by <DR-id>` | Do not treat the DR as current governing law; follow the accepted/superseding record if available. |

`PolicyReviewDisposition` is orthogonal and does not replace the disposition gate. Preserve the DR's author-locked `Decision`, `Rationale`, and `Alternatives Considered` meaning; do not silently promote a proposal or rewrite its reasoning while generating evals.

## Step 1 — affected-surface resolution

Before scenario design or walkthrough lane dispatch, map each DR to the surfaces it governs:

1. Collect the files, skills, systems, and interfaces cited in the DR's governing-artifact citations, Decision, Consequences, and Cross-references.
2. Record each surface with the DR identifier and the citation that connects it to the decision.
3. Aim DR-derived scenarios at those surfaces. Do not spray scenarios across unrelated code merely because it is nearby.
4. If a cited surface cannot be resolved, keep that uncertainty explicit and create a probe rather than guessing a binding target.

Minimum map shape:

```yaml
dr_id: DR-YYYY-MM-DD-NNN
disposition: Accepted as Implementation Choice
affected_surfaces:
  - kind: file | skill | system | interface
    target: <cited path or name>
    citation: <DR field or decision clause>
```

For walkthrough mode, give governing DRs to the law-reading lanes that already receive DIB context. DRs do not join the resolved spec set and do not relax the Lane 1a spec-read prohibition.

## Scenario family — `dr-derived`

Generate only scenarios supported by the DR text and its affected-surface map:

- **`decision-holds`:** exercise an affected surface and assert the accepted decision's observable outcome. Binding only for accepted dispositions.
- **`alternatives-rejected`:** adversarially recreate the failure mode that caused an alternative in `Alternatives Considered` to lose, then assert that failure does not occur. This is binding only when the accepted decision and recorded rejection reason entail the outcome; otherwise classify it as a probe.
- **`rationale-invariant`:** attempt to falsify a causal assumption or invariant stated in `Rationale`. Always classify this as an evidence probe unless the invariant is also explicit in the accepted Decision.

For proposed/pre-acceptance DRs, all three variants remain non-binding probes regardless of their apparent strength.

## Holdout discipline

Apply the existing protected-holdout rules unchanged. DR-derived scenarios may be held out from the repair side, and the agent that designs walkthrough scenarios must still be separate from the agents that inspect the resolved spec set. The affected-surface map identifies targets; it does not leak verifier conclusions or implementation answers.
