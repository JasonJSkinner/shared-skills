# Auto Evals Principles v1.3

This is the durable doctrine distilled from the `FEATURE-049` autonomous eval pilot DIB (originating on the Codex side), revised in v1.3 to make Phase Review Briefs (PRBs) a first-class authority layer between DIBs and specs.

Treat these principles as the default intent of `/auto-evals` unless a later governing DIB explicitly overrides them.

## Core Intent

The goal is not to generate "more tests."

The goal is to generate a compact, autonomous, reviewable eval package that judges an implementation from the outside in and increases confidence in ways the implementation's own tests may not.

## Authority Hierarchy

When governing documents disagree, later items yield to earlier items:

1. **DIB(s)** — Design Intent Brief(s). Define what good looks like and the durable intent. Highest authority.
2. **PRB(s)** — Phase Review Brief(s). Translate DIB intent into review-grade phase contracts. Override specs but defer to DIBs.
3. **Specs** — per-phase implementation specs. Concrete but lowest authority; a spec that drifts from its PRB or governing DIB is wrong, not authoritative.

Read all three layers before deriving scenarios. A spec that contradicts its PRB, or a PRB that contradicts the governing DIB, is itself a candidate eval scenario — the contract edge often lives in that gap.

**Anchor each scenario explicitly.** Every scenario in the pack should carry a `DIB §... / PRB §... / Spec §...` anchor line identifying its primary governing-law source. Prefer DIB-level claims as the primary anchor wherever one exists — DIB evaluation dimensions, non-negotiable quality bars, and guiding principles usually map directly to high-value scenarios. Use PRB §Promotion Gate clauses where a phase contract is the relevant authority. A Spec-only anchor is acceptable for implementation-surface probes but is weaker evidence — if a pack has many Spec-only scenarios and few DIB-anchored ones, that's a signal the pack may be mirroring the impl rather than testing against intent. Re-anchoring after initial design is cheap; not doing it quietly lets the pack drift toward Spec-bias.

## Governing Principles

1. DIB/PRB/spec law, not paraphrase.
   - Treat the governing DIB/PRB/spec set as law, applying the authority hierarchy above when the layers disagree.
   - Translate that law into scenario families, concrete scenarios, adversarial/edge cases, protected holdouts, executable verifier logic, and evidence-oriented reports.
2. Externally meaningful behavior over implementation mirroring.
   - Focus on contract satisfaction, behavioral truth, operational surfaces, migration outcomes, stale/corrupt-state handling, and human-relevant failure modes.
   - Do not simply restate or rerun the built-in tests.
3. Distinct roles, even when lightweight.
   - Keep scenario design, critique, and verification logically separate.
   - Prefer an independent verifier by default.
   - Use subagents (via the Agent tool) or separate invocations when available; otherwise preserve role separation through explicit phases and separate artifacts.
   - If the orchestrator must verify as fallback, say so explicitly in the verifier report.
4. External law stays external.
   - Governing DIB/PRB/spec law and the frozen evaluator package should not be casually rewritten by the repair side.
   - Failing scenarios, holdouts, and verifier logic must not drift just because they are inconvenient.
5. Scenario classes must stay explicit.
   - Classify each scenario as a strict contract gate, evidence probe, corpus scan, or ergonomics warning.
   - Do not blur those categories in reporting.
6. Holdouts are protected assets.
   - Keep some scenarios protected from implementation-time tuning when feasible.
   - Changing holdouts requires evaluator-maintainer intent, not routine repair churn.
7. Lightweight over orchestration sprawl.
   - Prefer a contained pilot or focused eval package over a universal always-on framework.
   - Prefer modular/skill-based composition over brittle glue-script sprawl.
8. Local-first and practical.
   - Prefer local execution, free/open-source tooling, and no Docker or paid services unless explicitly requested.
9. Material assumptions only.
   - Surface only non-obvious assumptions that matter.
   - Ask questions only when an assumption is too risky to make alone.
10. Evidence-first reporting.
    - The verifier report must clearly separate what was proved, what failed, what remains unknown, and whether the suite adds real confidence.
11. Gap-finding failures are success for the eval workflow.
    - An eval scenario that fails for a real contract reason is valuable.
    - Do not optimize for a green-only suite.
12. Repair should be clustered, not thrashed.
    - After verification, cluster failures into root-cause families and hand them off cleanly.
13. Root-cause handoff must be structured.
    - Each post-verification failure family handed to `/root-cause` must include:
      - failing scenarios and evidence paths
      - explicit symptom set
      - suspected reusable layer
      - initial discrepancy-matrix seed
      - required blast-radius check
      - requested action-bucket decision
      - authority-layer diagnosis (which of DIB/PRB/spec was violated; which drifted)
    - Root-cause output must be normalized back into the eval repair queue rather than left as a disconnected memo.
14. Cross-layer contradictions are first-class scenarios.
    - When a spec contradicts its PRB, or a PRB contradicts the governing DIB, treat the contradiction itself as testable surface.
    - Generate at least one scenario that asks: does the implementation follow the higher-authority layer, or has it drifted toward the lower one?

## Default Priority Contracts

When the governing DIB/PRB/spec set does not provide a more specific priority order, bias toward:

1. Stable identity / invariants / merge safety
2. Canonical-vs-derived authority
3. Migration correctness and artifact authority
4. Required human-readable artifact structure
5. Non-UI operational usability
6. Concurrency / worktree / conflict ergonomics

## Anti-Patterns

- Renaming existing tests and calling them autonomous evals
- Building a giant framework before proving focused value
- Hiding hard failing scenarios to keep the run green
- Treating the verifier as the designer and critique role at the same time without clear separation
- Letting the orchestrator silently self-certify when an independent verifier was practical
- Letting the implementation side rewrite failing evaluator logic without a separate evaluator decision
- Handing `/root-cause` a lightweight failure summary without the required packet fields
- Forking multiple authoritative harness/report/evidence paths for the same run
- Letting repair loops keep grinding after convergence has clearly flattened or evaluator drift is suspected
- Treating a spec as authoritative when it visibly contradicts its PRB or governing DIB
- Reading only the spec layer and ignoring the PRB and DIB above it

## Success Standard

The workflow is strong when it is executable, materially distinct from implementation-authored tests, and either:

- finds a meaningful gap, ambiguity, or weak spot, or
- meaningfully broadens coverage in at least one major contract area
