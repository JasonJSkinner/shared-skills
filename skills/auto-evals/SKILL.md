---
name: auto-evals
description: "Generate autonomous evals from governing DIB/DR/PCB/spec law, with separate designer/critique/verifier roles, holdout contract coverage, executable local harnesses, evidence-first reports, and structured /root-cause repair-loop handoffs. v2.0 adds a `walkthrough` subcommand implementing multi-lane orthogonal validation (Lane 1a scenario design / Lane 1b walkthrough / Lane 2 downward / Lane 3 upward + Phase C meta-synthesis) with asymmetric-knowledge holdout enforced by separate agents. Use when the user invokes /auto-evals, or asks for autonomous evals, scenario generation, contract-based verification, verifier harnesses, holdout tests, or to assess whether an implementation satisfies DIB/DR/PCB/spec law beyond its built-in tests."
version: "2.6.2"
---

# Auto Evals

Current doctrine version: `v2.6.0` (blind-lane input contract = DIB + accepted DRs only; T3 = four initial lanes + adjudicated loop-until-dry) over baseline `v1.3` (preserved for non-walkthrough invocations).

This skill turns governing DIB/DR/PCB/spec law into a compact, executable eval package that tests an implementation from the outside in.

Originally derived from the executed `FEATURE-049` autonomous eval pilot on the Codex side. v1.3 added PCBs (Phase Contract Briefs) as a first-class authority layer between DIBs and specs. v2.0 adds a `walkthrough` subcommand implementing the multi-lane orthogonal validation pattern from the 2026-05-06 Phase A-E DIB-validation run. v2.2 adds DRs as governing law.

> **Terminology history:** Before the 2026-08-20 completion pass, this skill used PRB (Phase Review Brief) alongside PCB (Phase Contract Brief). PCB is canonical in live prose. The v1.3 doctrine references (`references/principles_v1_3.md`, `references/playbook_v1_3.md`) preserve PRB for archival fidelity.

## Authority Hierarchy

When governing documents disagree, later items yield to earlier items:

1. **DIB(s)** — Durable Intent Brief(s). Define what good looks like. Highest authority.
2. **Accepted DR(s)** — Decision Records whose accepted disposition makes their decisions binding. Defer to DIBs; override PCBs and specs.
3. **PCB(s)** — Phase Contract Brief(s). Translate DIB intent into review-grade phase contracts. Override specs but defer to DIBs and accepted DRs.
4. **Specs** — per-phase implementation specs. Concrete but lowest authority; a spec that drifts from higher governing law is wrong, not authoritative.

Proposed DRs contribute non-binding probes only. See [references/dr_sources_v2_2.md](references/dr_sources_v2_2.md) for disposition gating, affected-surface resolution, and the `dr-derived` scenario family.

A lower layer that contradicts a higher one is itself a candidate eval scenario, not a bug in the reading.

## First Read

- For **walkthrough mode (`/auto-evals walkthrough`)**: read [references/walkthrough_v2_0.md](references/walkthrough_v2_0.md) before dispatching lanes. The 2026-05-06 Phase A-E reference [references/walkthrough_mode_phase_a_e_reference.md](references/walkthrough_mode_phase_a_e_reference.md) is the canonical provenance source for v2.x. Load it only when researching v2.x design history/provenance — it is historical and never needed to run any mode (current contract: `references/walkthrough_v2_0.md`).
- For **non-walkthrough invocations** (scenarios-only, scoped runs, traditional eval generation): read [references/principles_v1_3.md](references/principles_v1_3.md) before planning the suite, [references/playbook_v1_3.md](references/playbook_v1_3.md) when you need the concrete workflow, role split, scenario families, or deliverable structure.
- For **any invocation with DR inputs**: also read [references/dr_sources_v2_2.md](references/dr_sources_v2_2.md) before target resolution or lane dispatch.

## Use This Skill When

- The user asks for autonomous evals, scenario generation, holdout tests, verifier harnesses, or evidence-oriented validation.
- The user wants to judge an implementation against DIB/DR/PCB/spec law rather than just rerun its built-in tests.
- The user wants to know whether a workflow is worth generalizing into a reusable eval capability later.
- The user invokes `/auto-evals walkthrough <target>` for multi-lane orthogonal validation with asymmetric-knowledge holdout.

## Do Not Use This Skill When

- The user only wants normal implementation tests, bug fixing, or code review.
- There is no governing DIB/DR/PCB/spec law and the user has not asked for eval framing yet.
- The main request is to build a general always-on orchestration framework rather than a focused eval package.

If governing law is missing, suggest creating a DIB first (or a DIB + PCB pair if the work is phased) or ask for the specific DR/spec set to treat as law. A DR alone is sufficient governing-law input.

---

## Walkthrough Mode (v2.0) — Subcommand

```
/auto-evals walkthrough <target> [--chain=<artifact>] [--scope=<level>] [--scenarios=N-M]
```

### Locked design decisions

- **D1-c-3:** Subcommand pattern (NOT `--mode=walkthrough` flag, NOT sub-skill `/auto-evals-walkthrough`).
- **D2-c-1:** Opt-in `--chain=<artifact>` flag triggers Lane 1b walkthrough against named realization artifacts. Invoking agents SHOULD proactively surface `--chain` as a suggested inclusion when chaining would be helpful and not explicitly specified (refinement per D2-c-1).
- **D3:** Holdout enforced by **separate agents with asymmetric knowledge** (NOT filesystem-level isolation). Lane 1a reads DIBs + concepts; Lane 1b reads DIBs + specs + assigned scenario; Phase C reads everything.
- **D4-c-1:** `--scope=<level>` composes uniformly across ALL lanes (generator-level activation overlay, per Spec 03 §7.3). Lane 1a still gets full intent for holdout-discipline.

### Lane architecture

```
Phase A — chunking (parallel; 1-N agents per source file)
   ↓
Phase B Lane 1a — scenario design (ONE capable model; holdout: DIBs + concepts ONLY; FORBIDDEN: the resolved spec set)
   ↓ (fan-out per scenario; only if --chain provided)
Phase B Lane 1b — walkthrough (N parallel capable models, one per scenario, batched waves of 5-7 — tunable)
   ↕ (parallel with Lane 1b)
Phase B Lane 2 — downward DIB→Spec (capable model, batched 5 chunks/agent — tunable)
   ↕ (parallel)
Phase B Lane 3 — upward Spec→DIB (capable model, batched 10 chunks/agent — tunable)
   ↓ (sink: after ALL Phase B drains)
Phase C — meta-synthesis (ONE capable long-context model; applies absence-as-corroboration)
```

Batch sizes / wave sizes / scenario count in the diagram are run-empirical defaults, NOT baked — exposed as tuning parameters or auto-tuned (see [references/walkthrough_v2_0.md](references/walkthrough_v2_0.md) §11). The 5 lane prompts are shipped as parameterized `{...}`-placeholder templates in [references/lane-templates/](references/lane-templates/) — the orchestrator fills placeholders at dispatch time.

**Without `--chain`:** Lane 1a runs only; emits `phase-b/lane-1a-scenarios.json`; returns to caller.
**With `--chain`:** Full pipeline through Phase C; emits `phase-c/meta-synthesis.{json,md}` + verdict (`yes | yes-with-surgical | no-blocking-found`).

### Verdict vocabularies (load-bearing compatibility surface — DO NOT rename)

| Layer | Vocabulary |
|---|---|
| Lane 1b scenario verdict | `ALIGNED \| PARTIAL \| CONTRADICTED \| SILENT \| AMBIGUOUS` |
| Lane 1b per-chunk status | `REALIZED \| PARTIAL \| MISSING \| CONTRADICTED` |
| Lane 1b finding severity | `blocking \| concerning \| minor` (lower-case) |
| Lane 2 alignment | `REALIZED \| PARTIAL \| MISSING \| CONTRADICTED \| OUT_OF_SCOPE` |
| Lane 2 site completeness | `fully \| partially \| tangentially` |
| Lane 3 justification | `JUSTIFIED \| DR_JUSTIFIED \| INDIRECT \| ORPHAN \| OVER_ENGINEERED` |
| Lane 3 trace path | `Direct DIB principle \| Via DR-XXXX \| Via PCB pattern \| Implementation-discipline` |
| Lane 3 strength | `strong \| moderate \| tenuous` |
| Phase C confidence | `triple-confirmed \| double-confirmed \| single-lane \| single-lane-plus-structural-confirmation` |
| Phase C recommendation | `GO \| SURGICAL_PATCH \| VERSION_BUMP \| NEW_DR \| DEFER \| ARCHITECTURAL_REVIEW` |
| Phase C canonization | `yes \| yes-with-surgical \| no-blocking-found` |
| Phase C holdout verdict | `PRESERVED \| BREACHED \| UNVERIFIED` |

Full operational meaning + load-bearing rationale: see [references/walkthrough_v2_0.md](references/walkthrough_v2_0.md) §5.

### Holdout discipline — LOAD-BEARING

The asymmetric-knowledge holdout is the load-bearing architectural commitment of walkthrough mode. **Any v2.x implementation that lets the same agent design scenarios AND walk them through specs destroys the F01-class error-detection capability.** Lane 1a MUST receive a **parametric** forbidden read-set clause — the spec set resolved from `<target>`, NOT a hardcoded `synthesis/spec_*.md` literal — and MUST emit a `holdout_integrity` field enumerating files-read; Phase C audits via set-intersection of files-read against the resolved spec set (corpus-agnostic — closes the silent-breach risk for non-`spec_*.md`-named corpora). See [references/walkthrough_v2_0.md](references/walkthrough_v2_0.md) §3 for the full discipline.

### Phase C absence-as-corroboration — LOAD-BEARING

Phase C is NOT mere aggregation. When a Lane 1b finding is single-lane, the meta-synthesizer searches Lane 3 for chunks addressing the topic. **Zero matching Lane 3 chunks STRENGTHENS the finding** (single-lane → "single-lane + structural confirmation"); the topic being structurally absent is itself evidence. See [references/walkthrough_v2_0.md](references/walkthrough_v2_0.md) §4.

### Build-time decisions resolved (v2.0)

- **SURGICAL_PATCH count source-of-truth:** `meta-synthesis.json`'s `canonization_summary.recommendation_distribution.SURGICAL_PATCH` field is authoritative for Phase C synthesis output. Companion `.md` annotates actual-landed count separately. (Per WU 3.1 §7-Q1.)
- **Lane 3 `CONTRADICTORY` handling:** Phase-C-only meta-tag (not in Lane 3 base enum). Phase C cross-correlates lane outputs to identify CONTRADICTORY findings. (Per WU 3.1 §7-Q2.)
- **Lane file-naming convention:** `phase-b/lane-1a-scenarios.json`, `phase-b/walkthrough-{NN}.json`, `phase-b/L2-batch-NNN-results.json`, `phase-b/L3-batch-NNN-results.json`, `phase-c/meta-synthesis.{json,md}`. (Per WU 3.1 §7-Q3.)

### Output JSON schemas (5 schemas)

See [references/walkthrough_v2_0.md](references/walkthrough_v2_0.md) §9 for full schema definitions.

### Outputs-to-files (NOT chat) — compaction-resistance

Every lane agent writes its output JSON to a deterministic path. Chat-only emission is forbidden — the 2026-05-06 run survived a 30-min Claude account outage because outputs were going to files.

### Tuning parameters NOT to bake

Batch sizes (5/10 chunks), scenario count (12-15), wave sizes (5-7), concept-file enumeration are run-empirical and EXPOSED as tuning parameters or auto-tuned, NOT hardcoded. See [references/walkthrough_v2_0.md](references/walkthrough_v2_0.md) §11.

---

## Workflow (non-walkthrough invocations preserve v1.3)

1. Gather the governing law.
   - Read the DIB(s), DR(s), PCB(s) if present, invariant/spec docs, relevant operational docs, current implementation, and current test/eval artifacts.
   - Apply the authority hierarchy (DIB > accepted DR > PCB > spec) when layers disagree. Note any observed cross-layer contradictions — those are candidate eval scenarios.
   - For each DR, resolve its cited files, skills, and systems into an affected-surface map before designing scenarios; use [references/dr_sources_v2_2.md](references/dr_sources_v2_2.md).
   - Treat those documents as law, not as inspiration.
2. Report only material non-obvious assumptions.
   - Ask direct questions only when an assumption is too risky to make unilaterally.
3. Establish logically distinct roles.
   - Default roles: orchestrator, scenario designer, critique, verifier.
   - Prefer an independent verifier by default. Use a spawned verifier subagent (via the Agent tool) or a separate invocation when the environment supports it.
   - Minimize answer leakage into the verifier. Give it the governing law, target under test, and artifacts it needs, not your conclusions.
   - If independent verification is unavailable or blocked, keep the roles separate via explicit phases and separate artifacts, and state clearly that the orchestrator verified as a fallback.
   - **Subagent context window:** When the verifier must read a full DIB + DR + PCB + spec + implementation + evidence bundle, use a model/context tier large enough for that evidence or split the evidence into cited file-backed batches.
4. Design the suite from the law.
   - Derive scenario families, coverage matrix, concrete scenarios, adversarial cases, protected holdouts, and executable verifier logic. Include `dr-derived` scenarios when DRs govern the target.
   - Favor externally meaningful behavior and contract satisfaction over implementation mirroring.
   - Classify each scenario up front as one of: strict contract gate, evidence probe, corpus scan, ergonomics warning.
   - **Scenario-design dispatch tiers** (blind and preferably cross-model or cross-provider). Choose by the governing DIB's scope, complexity, and importance; state the tier and a one-line justification at dispatch. Designer lanes are blind to each other and read binding intent-law only — governing DIB context plus accepted governing DRs, never PCB, spec, implementation, or completeness map:
     - **T1 light:** one blind capable designer; no synthesizer.
     - **T2 standard:** three blind designers, including at least one higher-reasoning lane, followed by one synthesizer.
     - **T3 thorough:** T2 plus a fourth independent designer from a different model or provider, then loop with fresh blind designers until two consecutive rounds surface nothing materially new. Obtain user authorization before dispatching any lane that adds external cost or requires a separately controlled provider. Set an adjudication threshold from scope, nuance, blast radius, and impact; after that many rounds, the un-blind synthesizer may count materially redundant output as a dry round or declare the loop dry.
   - **Synthesizer guards:** the synthesizer is the one un-blind agent. It merges true duplicates and adds gap-fill scenarios (labeled synthesizer-origin); it never rewrites a blind scenario, and per-lane provenance survives into the final pack.
   - **Scenario-vs-map diff** (runs when a completeness map exists for the target): diff the blind-scenario union against the map's closure dimensions, both directions. Blind-only scenarios are candidate map omissions. Unreached map dimensions become map-derived standard checks in a separate lane, never retrofitted "holistic" scenarios.
5. Protect distinctness.
   - Do not rename or lightly wrap the shipped tests and call that a new eval suite.
   - Push into contract edges, real-corpus checks, operational surfaces, stale/corrupt-state behavior, and friction probes.
6. Freeze the external law and eval package.
   - Governing DIB/DR/PCB/spec law stays external and authoritative.
   - The repair side must not casually rewrite failing scenarios, holdouts, or verifier logic during implementation.
   - Use one canonical harness path, one canonical verifier report, and one canonical evidence bundle per run. Later phases should update or supersede, not silently fork.
7. Keep holdouts protected.
   - Keep some scenarios protected from implementation-time tuning when feasible.
   - Do not expose all evaluator logic to the repair side unless necessary.
   - Treat holdout changes as evaluator-maintainer work, not routine implementation drift.
8. Keep the system lightweight.
   - Prefer local, free/open-source, modular tooling.
   - Avoid Docker, paid services, or a giant framework unless the user explicitly asks.
9. Execute and analyze.
   - Gap-finding failures are valid outcomes.
   - A FAIL against a frozen scenario/oracle gets an oracle-vs-law adjudication
     before it is treated as an implementation defect: governing law may have
     legitimately moved since the pack froze (accepted governing changes supersede
     stale oracles). Record the adjudication with cited law; never silently
     edit the frozen pack or its historical results. (Origin: dib-to-done C1R
     AE-3, 2026-08-20.)
   - Separate strict contract failures from warning/probe scenarios.
   - Report what was proved, what failed, what remains unknown, and whether the suite added confidence beyond existing tests.
10. Cluster failures and perform a structured `/root-cause` handoff.
    - After verification, cluster failures into probable root-cause families.
    - Generate a repair queue.
    - For every family handed to `/root-cause`, build a packet that includes:
      - failing scenarios and evidence paths
      - explicit symptom set
      - suspected reusable layer
      - initial discrepancy-matrix seed
      - required blast-radius check
      - requested action-bucket decision
      - authority-layer diagnosis (which of DIB / DR / PCB / spec was violated; which drifted)
    - Invoke `/root-cause` with that packet, not just a lightweight summary.
    - Feed the `/root-cause` result back into the eval repair queue with:
      - family identifier/title
      - confirmed reusable issue family
      - chosen action bucket
      - blast-radius summary
      - recommended next sequence
      - what not to touch yet
      - linked failing scenarios and evidence paths
    - Preserve the frozen eval package while repair happens.
11. Stop deliberately.
    - Stop when all strict gates pass, or when remaining issues are accepted non-blocking warnings, or when repair attempts are converging too slowly or evaluator drift is suspected.
12. Deliver the standard package.
    - Eval design brief
    - Generated eval/scenario pack
    - Critique memo
    - Verifier report
    - Repair queue / `/root-cause` handoff record
    - Recommendation on whether the approach is worth repeating or generalizing

## Guardrails

- Stay faithful to the governing law's intent, decisions, and guiding principles; do not casually broaden or reframe the mission.
- Translate the law into scenarios; do not merely restate the law.
- Prefer an independent verifier. Primary-agent self-verification is fallback only, not the normal topology.
- Keep external law external. Do not let the implementation side casually rewrite the evaluator to make failures disappear.
- Classify scenarios explicitly so strict gates, probes, corpus scans, and ergonomics warnings do not get conflated.
- Preserve protected holdouts unless there is a separate evaluator-maintainer reason to change them.
- Prefer a focused pilot over a sprawling universal framework.
- Keep the verifier report evidence-first and explicit about proved vs unproved.
- When overlapping same-task artifacts already exist, consolidate into one canonical harness/report path or explicitly disambiguate. Do not silently fork duplicate authoritative artifacts.
- Do not hand `/root-cause` a shallow failure summary. Use the full handoff contract and feed the result back into the repair queue.
- After verification, default to clustered repair handoff rather than ad hoc one-failure-at-a-time thrash.
- If the suite is green only because hard scenarios were excluded, the skill failed.
- Do not treat a spec as authoritative when it visibly contradicts its PCB, an accepted governing DR, or its governing DIB.
- **For walkthrough mode (v2.0):** do not collapse Lane 1a + Lane 1b into one agent; do not give Lane 1a "for grounding" access to specs; do not treat `--chain` as passive metadata; do not implement `--scope` as post-hoc filter; do not rename verdict vocabulary strings; do not auto-land Phase C `SURGICAL_PATCH` recommendations without orchestrator/human approval; do not omit Phase C absence-as-corroboration; do not mutate live deferral state from temporary validation installs.

## Default Success Bar

The run is good enough if the generated suite is materially distinct from the implementation-authored tests, is executable, and either:

- catches at least one meaningful gap, ambiguity, or weak spot, or
- convincingly expands coverage in at least one major contract area

The final output should let a human quickly decide whether the workflow is worth repeating.

For walkthrough mode (v2.0), the bar additionally requires:

- holdout discipline preserved (Lane 1a `holdout_integrity` field clean; Phase C `holdout_integrity_verdict: PRESERVED`)
- absence-as-corroboration applied (single-lane findings strengthened by Lane 2/3 silence where applicable)
- outputs-to-files (every lane wrote deterministic-path JSON, surviving any in-flight outage)
- verdict vocabularies preserved verbatim (no renaming)
- `meta-synthesis.json` `canonization_summary.recommendation_distribution.SURGICAL_PATCH` is the authoritative count source

---

## Compatibility Notes

Current walkthrough doctrine uses PCB terminology. The v1.3 references retain the
older PRB term for historical fidelity; treat PRB and PCB as aliases when reading
those references. Public release archives are not shipped.

---

*End of SKILL.md.*
