# Auto Evals Playbook v1.3

Use this when you need the concrete operating pattern behind `/auto-evals`.

v1.3 adds Phase Review Briefs (PRBs) as a first-class input layer between DIBs and specs. See `principles_v1_3.md` for the full authority hierarchy.

## Inputs

Start with:

- **governing DIB(s)** — highest-authority intent
- **governing PRB(s)** when present — phase review brief contracts; override specs, defer to DIBs
- **relevant spec docs** — per-phase implementation specs and invariant docs
- current implementation/worktree
- current tests/eval artifacts
- real corpus or live canonical data when available
- repo-local or product-local operational docs defining expected command/agent surfaces

When reading: start at the DIB layer, descend through PRBs, then into specs. Flag any point where a lower layer contradicts a higher one — those contradictions are candidate scenarios, not bugs in the reading.

## Default Role Split

1. Orchestrator
   - gathers governing inputs across all three layers (DIB → PRB → spec)
   - reports material assumptions, including any observed cross-layer contradictions
   - keeps artifact paths coherent
2. Scenario designer
   - derives scenario families and coverage matrix
   - proposes concrete executable evals
   - includes at least one scenario probing each observed cross-layer contradiction
3. Critique role
   - looks for leakage from existing tests
   - hardens weak assertions
   - identifies blind spots and missing holdouts
4. Verifier
   - runs the final suite
   - collects evidence
   - writes the final report
   - should be independent from the orchestrator/designer by default

## Verification Independence Rule

- Default: spawn a separate verifier subagent via the Agent tool or use a clearly separate invocation.
- Give the verifier the minimum necessary context and artifacts so it can evaluate the suite rather than echo the orchestrator's conclusion.
- Fallback: if the environment blocks independent verification, the orchestrator may verify directly, but the report must say that independence was unavailable and that verification used a fallback topology.

## Scenario Family Patterns

Use only the families that match the governing law:

- Contract holdouts
  - stale-state behavior
  - corrupt-state behavior
  - combined-option semantics
  - alias/identity immutability
  - incremental continuity
- Real-corpus integrity
  - required files/fields/summary placement
  - path validity
  - duplicate-editable-artifact detection
- Operational surface checks
  - CLI/skill presence
  - non-UI flows
  - degradation when optional derived layers are absent or bad
- Concurrency / ergonomics probes
  - multi-worktree merge behavior
  - same-entity edit friction
  - localized conflict surfaces
- **Cross-layer coherence probes (v1.3)**
  - spec-vs-PRB contradictions — does the implementation follow the PRB contract or silently track spec drift?
  - PRB-vs-DIB contradictions — does the phase deliverable satisfy the governing DIB intent or only the phase-local PRB?
  - silent reinterpretation — did a spec narrow a PRB/DIB clause without an explicit PRB update?

## Scenario Classification Rule

Classify each scenario before implementation:

- `strict contract gate`
  - should pass for the system to satisfy the governing contract
- `evidence probe`
  - useful high-signal stressor whose output may expose gaps without serving as a binary acceptance gate
- `corpus scan`
  - integrity or authority scan over real data/canonical artifacts
- `ergonomics warning`
  - friction or risk probe that may not map cleanly to pass/fail acceptance

Keep this classification visible in design and verification artifacts.

## Distinctness Test

Before implementing a scenario, ask:

1. Is this materially different from a shipped test?
2. Does it exercise a contract edge rather than a happy path already covered?
3. Would a human reviewer feel that this scenario adds confidence?

If the answer is no, cut it or redesign it.

## External-Law / Frozen-Eval Rule

- Keep the governing DIB/PRB/spec law external and authoritative.
- Once the eval package is established for a run, treat the harness, verifier logic, and protected holdouts as frozen unless a separate evaluator-maintainer decision changes them.
- Do not let the repair side casually patch failing scenarios just to regain green status.

## Holdout Protection Rule

- Keep some scenarios or exact assertion shapes protected from implementation-time tuning when feasible.
- Do not expose all evaluator logic to the repair side unless necessary.
- If a holdout changes, record why and treat that as evaluator maintenance, not ordinary repair work.

## Canonical Artifact Path Rule

Per eval run, maintain:

- one canonical harness path
- one canonical verifier report
- one canonical evidence bundle

Later phases should update or supersede, not silently fork duplicate authoritative artifacts.

## Result Classification

Use:

- `pass` for satisfied contract checks
- `fail` for meaningful contract or behavior gaps
- `warning` for useful evidence probes that expose friction or risk but are not clean binary invariant failures

## Post-Verification Handoff

After the verifier run:

1. Cluster failures into probable root-cause families.
2. Produce a repair queue.
3. Hand each family to `/root-cause`.
4. Preserve the frozen eval package while repair happens.

## Root-Cause Handoff Contract

Every family handed to `/root-cause` must be packaged with enough context that it can classify the failure as a reusable issue family rather than patch a symptom.

For each failure family, include all of the following:

1. Failing scenarios and evidence paths
   - scenario ids/titles
   - verifier-report section or evidence-bundle paths
   - canonical harness/report/evidence references
2. Explicit symptom set
   - concrete discrepant behaviors, fixtures, versions, artifacts, or failing eval observations
   - use the root-cause vocabulary where possible (`detected`, `not_detected`, `citation_incomplete`, `PARTIAL`, `DISAGREE`)
   - if the eval uses a different local vocabulary, state it explicitly
3. Suspected reusable layer
   - likely shared helper, rail, contract, migration path, query path, catalog boundary, or other lowest reusable layer
4. Initial discrepancy-matrix seed
   - current feature/detector path
   - current evidence rail
   - current export/contract relied on
   - likely reusable helper family
   - whether the symptom seems isolated or shared
   - use `unknown` placeholders when needed; do not omit fields
5. Required blast-radius check
   - identify which helpers, rails, contracts, validators, or consumers must be inspected before repair
6. Requested action-bucket decision
   - ask `/root-cause` to choose exactly one:
     - `fix_in_code_now`
     - `clarify_catalog_or_validator`
     - `defer_as_policy_decision`
     - `leave_as_missing_rule_family`
     - `leave_as_verifier_layer_judgment`
7. **Authority-layer diagnosis (v1.3)**
   - name the layer that was actually violated: DIB, PRB, or spec
   - note whether a lower layer silently drifted from a higher one
   - this helps `/root-cause` distinguish implementation bugs from governance bugs

Do not hand off a family with only "these tests failed" or "please analyze this bug."

## Root-Cause Return Contract

After `/root-cause` completes, normalize its result back into the eval repair queue.

Each repair-queue entry should capture:

1. family id/title
2. linked failing scenarios and evidence paths
3. confirmed reusable issue family
4. chosen action bucket
5. blast-radius summary
6. recommended next sequence
7. what not to touch yet
8. authority-layer diagnosis (which layer was violated; which drifted)

If the `/root-cause` output does not provide enough information to populate these fields, the handoff is incomplete and should not be treated as closed.

## Stop Conditions

Stop when one of these becomes true:

1. all strict gates pass
2. remaining issues are accepted non-blocking warnings
3. repeated repair attempts are converging too slowly
4. evaluator drift or loss of independence is suspected

Escalate instead of grinding past those stop conditions.

## Default Deliverables

Produce these unless the user explicitly narrows the ask:

1. Eval design brief
   - objective
   - assumptions (including any observed DIB↔PRB or PRB↔spec contradictions)
   - scenario families
   - coverage matrix
   - proposed executable suite
2. Generated eval/scenario pack
   - harness or scripts
   - concrete scenarios
   - holdouts and adversarial cases
3. Critique memo
   - initial weaknesses
   - strengthening decisions
   - residual blind spots
4. Verifier report
   - commands run
   - suite executed
   - summary results
   - detailed findings
   - what was proved / not proved
   - recommendation
5. Repair queue / root-cause handoff
   - clustered failure families
   - structured `/root-cause` packets (including authority-layer diagnosis)
   - returned action buckets
   - next repair targets

## Lessons From FEATURE-049

The first pilot was high-signal because it went after contract edges the shipped tests did not cover, including:

- combined text-plus-filter semantics
- stale derived truth masking canonical updates
- corrupt derived similarity fallback
- duplicate alias integrity
- incremental migration map continuity
- real-corpus artifact-link authority
- same-ticket multi-worktree conflict localization

Carry that spirit forward: prefer focused, contract-derived pressure over bulk.
