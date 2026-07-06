# Auto Evals

`auto-evals` turns a governing DIB / PCB / spec set into a compact, executable eval package that judges an implementation *from the outside in*. It exists to increase confidence in ways the implementation's own tests cannot — by translating governing intent into scenarios, running them under an independent verifier, and handing failures off for structured repair.

This is the operating reference for the skill: what it produces, how to invoke it, and the doctrine it enforces. For the semantics of a *claim* — what it means for a scenario to assert something about an implementation — see the `/auto-evals` intro; this document does not re-derive that.

This skill is provider-neutral. The doctrine, package shape, and lane architecture below are provider-independent. Provider-specific mechanics (invocation syntax, how separate agents are spawned, large-context binding) are isolated in the **Provider notes** subsection so they can be swapped without touching the doctrine.

## What It Produces

The default deliverable is an **eval package**, not "more tests." A package contains:

1. **Eval design brief** — objective, material assumptions (including any observed cross-layer contradictions), scenario families, coverage matrix, proposed executable suite.
2. **Generated eval / scenario pack** — the harness or scripts, concrete scenarios, holdouts, and adversarial cases.
3. **Critique memo** — initial weaknesses, strengthening decisions, residual blind spots.
4. **Verifier report** — commands run, suite executed, results, detailed findings, an explicit *proved vs. not-proved* split, and a recommendation.
5. **Repair queue / structured `/root-cause` handoff** — clustered failure families, structured repair packets, returned action buckets, next targets.

The final output should let a human quickly decide whether the workflow is worth repeating or generalizing.

## Authority Hierarchy

Governing law is read top-down. When layers disagree, later items yield to earlier items:

1. **DIB(s)** — Design Intent Brief(s). Define what good looks like and the durable intent. Highest authority.
2. **PCB(s)** — Phase Contract Brief(s). Translate DIB intent into review-grade phase contracts. Override specs, defer to DIBs.
3. **Specs** — per-phase implementation specs. Concrete but lowest authority; a spec that drifts from its PCB or governing DIB is *wrong*, not authoritative.

Read all three layers before deriving scenarios. **A lower layer that contradicts a higher one is itself a candidate eval scenario, not a bug in the reading** — the highest-value contract edges often live in that gap. Every scenario should carry an explicit anchor line (`DIB §… / PCB §… / Spec §…`) naming its primary governing-law source. Prefer DIB-level anchors; a pack heavy with spec-only anchors is a signal it is mirroring the implementation rather than testing intent.

## Doctrine

**Externally meaningful behavior over implementation mirroring.** Focus on contract satisfaction, behavioral truth, operational surfaces, migration outcomes, stale/corrupt-state handling, and human-relevant failure modes. Do not rename the shipped tests and call that a new eval suite.

**Designer / critique / verifier separation.** Keep four logical roles distinct even when the run is lightweight:

- **Orchestrator** — gathers governing inputs across all three layers, reports material assumptions, keeps artifact paths coherent.
- **Scenario designer** — derives scenario families and the coverage matrix, proposes concrete executable evals, includes at least one scenario per observed cross-layer contradiction.
- **Critique** — hunts for leakage from existing tests, hardens weak assertions, identifies blind spots and missing holdouts.
- **Verifier** — runs the suite, collects evidence, writes the report.

**Independent verification by default.** Spawn a *separate* verifier (a subagent or a clearly separate invocation) and give it the minimum context to evaluate the suite rather than echo the orchestrator's conclusions — the governing law, the target under test, and the artifacts it needs, *not* your findings. If independent verification is genuinely blocked, the orchestrator may verify as a fallback, but the report must state that independence was unavailable and a fallback topology was used.

**Scenario classification stays explicit.** Classify every scenario *before* implementing it, and keep that class visible in both design and verification artifacts:

| Class | Meaning |
|---|---|
| `strict contract gate` | Must pass for the system to satisfy the governing contract. |
| `evidence probe` | High-signal stressor whose output may expose gaps; not a binary acceptance gate. |
| `corpus scan` | Integrity or authority scan over real data / canonical artifacts. |
| `ergonomics warning` | Friction or risk probe that may not map cleanly to pass/fail. |

Result vocabulary mirrors this: `pass` for satisfied checks, `fail` for meaningful contract/behavior gaps, `warning` for probes that expose friction without a clean binary failure. Never blur the categories in reporting.

**Holdout discipline.** Keep some scenarios (or exact assertion shapes) protected from implementation-time tuning. Do not expose all evaluator logic to the repair side unless necessary. Changing a holdout is *evaluator-maintainer* work with a recorded reason — not routine repair churn.

**External law stays external.** Once a package is established for a run, the governing law, harness, verifier logic, and holdouts are frozen. The repair side must not casually rewrite failing scenarios to regain green. Maintain **one** canonical harness path, **one** verifier report, and **one** evidence bundle per run; later phases update or supersede, never silently fork a second authoritative artifact.

**Evidence-first reporting.** The verifier report must separate what was proved, what failed, and what remains unknown, and state plainly whether the suite added confidence beyond the existing tests.

**Gap-finding failures are success.** A scenario that fails for a *real* contract reason is valuable output. Do not optimize for a green-only suite; if the suite is green only because the hard scenarios were excluded, the run failed.

**Lightweight over sprawl.** Prefer a focused, contract-derived pilot over a universal always-on framework. Prefer local execution and free/open-source tooling; avoid Docker, paid services, or a large framework unless explicitly requested.

## Structured Repair Handoff

After verification, cluster failures into probable root-cause *families* rather than thrashing one failure at a time, then hand each family to `/root-cause`. Do not hand off a shallow "these tests failed" summary — each packet must carry:

- failing scenarios and evidence paths (with canonical harness/report/evidence references)
- explicit symptom set (concrete discrepant behaviors, fixtures, versions, artifacts)
- suspected reusable layer (lowest shared helper / rail / contract / migration path)
- initial discrepancy-matrix seed (use `unknown` placeholders rather than omitting fields)
- required blast-radius check (which helpers, rails, contracts, validators, consumers must be inspected before repair)
- requested action-bucket decision (ask `/root-cause` to pick exactly one bucket)
- **authority-layer diagnosis** — name the layer actually violated (DIB / PCB / spec) and whether a lower layer silently drifted from a higher one; this separates implementation bugs from governance bugs.

Normalize the `/root-cause` result back into the repair queue — family id, linked scenarios/evidence, confirmed reusable family, chosen action bucket, blast-radius summary, recommended next sequence, what not to touch yet, authority-layer diagnosis. If the result cannot populate those fields, the handoff is incomplete and must not be treated as closed. Preserve the frozen eval package while repair happens.

## Stop Conditions

Stop deliberately when one becomes true — escalate rather than grinding past:

1. all strict gates pass;
2. remaining issues are accepted non-blocking warnings;
3. repeated repair attempts are converging too slowly;
4. evaluator drift or loss of independence is suspected.

## Success Bar

A run is good enough if the generated suite is materially distinct from the implementation-authored tests, is executable, and either catches at least one meaningful gap/ambiguity/weak-spot, or convincingly expands coverage in at least one major contract area.

---

## Walkthrough Mode (Subcommand)

Walkthrough mode is an opt-in, multi-lane variant for high-assurance validation of whether an implementation realizes its governing intent. It runs several agents with **asymmetric knowledge** so that no single agent both designs the test *and* knows the answer.

```
/auto-evals walkthrough <target> [--chain=<artifact>] [--scope=<level>] [--scenarios=N-M]
```

- **Without `--chain`:** only scenario design runs; it emits a scenarios file and returns to the caller.
- **With `--chain`:** the full pipeline runs through meta-synthesis, emitting a synthesis artifact plus a canonization verdict (`yes | yes-with-surgical | no-blocking-found`). The orchestrator should proactively suggest `--chain` when chaining against a realization artifact would help and was not specified.
- `--scope=<level>` composes uniformly across all lanes as an activation overlay; the scenario-design lane still receives full intent so its holdout discipline is not weakened.

### Lane architecture

```
Phase A — chunking (parallel; 1-N agents per source file)
   ↓
Phase B  Lane 1a — scenario design    (holdout: DIBs + concepts ONLY; the resolved spec set is FORBIDDEN)
   ↓ (fan-out per scenario; only when --chain is provided)
         Lane 1b — walkthrough         (one agent per scenario, batched in tunable waves)
   ↕     Lane 2  — downward DIB→Spec    (realization mapping)
   ↕     Lane 3  — upward Spec→DIB      (justification tracing)
   ↓ (sink: after ALL of Phase B drains)
Phase C — meta-synthesis (one large-context agent; applies absence-as-corroboration)
```

Batch sizes, wave sizes, and scenario counts are run-empirical defaults, **not** baked in — they are exposed as tuning parameters or auto-tuned, never hardcoded.

### Two load-bearing commitments

**Asymmetric-knowledge holdout.** This is the architectural core of the mode. If one agent both designs a scenario *and* walks it through the specs, the mode's error-detection capability is destroyed. The scenario-design lane receives DIBs + concepts only; the walkthrough lane additionally reads specs + its one assigned scenario; meta-synthesis reads everything. The forbidden read-set is **parametric** — the spec set resolved from `<target>`, never a hardcoded filename pattern — so the discipline holds for arbitrarily-named corpora. Each design-lane agent emits a `holdout_integrity` field enumerating the files it read; meta-synthesis audits it by set-intersection against the resolved spec set and reports a holdout verdict (`PRESERVED | BREACHED | UNVERIFIED`).

**Absence-as-corroboration.** Meta-synthesis is not mere aggregation. When a walkthrough finding is single-lane, the synthesizer searches the upward-trace lane for chunks addressing the same topic. **Zero matching chunks *strengthens* the finding** — the topic being structurally absent is itself evidence — promoting it from "single-lane" to "single-lane + structural confirmation."

### Verdict vocabularies (compatibility surface — do not rename)

These strings are a load-bearing interop surface between lanes and downstream consumers; treat them as fixed identifiers.

| Layer | Vocabulary |
|---|---|
| Walkthrough scenario verdict | `ALIGNED \| PARTIAL \| CONTRADICTED \| SILENT \| AMBIGUOUS` |
| Walkthrough per-chunk status | `REALIZED \| PARTIAL \| MISSING \| CONTRADICTED` |
| Walkthrough finding severity | `blocking \| concerning \| minor` |
| Downward-lane alignment | `REALIZED \| PARTIAL \| MISSING \| CONTRADICTED \| OUT_OF_SCOPE` |
| Downward-lane site completeness | `fully \| partially \| tangentially` |
| Upward-lane justification | `JUSTIFIED \| DR_JUSTIFIED \| INDIRECT \| ORPHAN \| OVER_ENGINEERED` |
| Upward-lane strength | `strong \| moderate \| tenuous` |
| Meta-synthesis confidence | `triple-confirmed \| double-confirmed \| single-lane \| single-lane-plus-structural-confirmation` |
| Meta-synthesis recommendation | `GO \| SURGICAL_PATCH \| VERSION_BUMP \| NEW_DR \| DEFER \| ARCHITECTURAL_REVIEW` |
| Meta-synthesis canonization | `yes \| yes-with-surgical \| no-blocking-found` |
| Holdout verdict | `PRESERVED \| BREACHED \| UNVERIFIED` |

### Outputs-to-files

Every lane agent writes its output to a deterministic path; chat-only emission is forbidden. This is a compaction- and outage-resistance property — a run whose outputs are already on disk survives an in-flight tool or account outage.

### Walkthrough success bar (in addition to the base bar)

- holdout discipline preserved (design-lane `holdout_integrity` clean; meta-synthesis holdout verdict `PRESERVED`);
- absence-as-corroboration applied where single-lane findings meet lane silence;
- outputs-to-files honored (every lane wrote deterministic-path output);
- verdict vocabularies preserved verbatim.

### Walkthrough guardrails

Do not collapse the scenario-design and walkthrough lanes into one agent. Do not give the design lane spec access "for grounding." Do not treat `--chain` as passive metadata or implement `--scope` as a post-hoc filter. Do not auto-land a `SURGICAL_PATCH` recommendation without orchestrator/human approval. Do not omit absence-as-corroboration.

---

## When NOT to Use

- The user only wants normal implementation tests, bug fixing, or code review.
- There is no governing DIB / PCB / spec law and the user has not asked for eval framing. (If law is missing, suggest authoring a DIB first — or a DIB + PCB pair for phased work — or ask which spec set to treat as law.)
- The main request is to build a general always-on orchestration framework rather than a focused eval package.

## Partial Adoption

The base mode is largely self-contained; walkthrough mode adds coordination dependencies.

**Hard dependency — for the structured repair handoff only.** Base scenario generation, running, and verdicting are standalone. The structured repair handoff targets `/root-cause`. Without it you can still generate and run a package, but the handoff contract degrades to an unstructured failure list — the anti-pattern this skill exists to prevent. If `/root-cause` is unavailable, still cluster failures into families and populate the packet fields manually.

**Optional, safe to omit.**
- **Walkthrough mode** is entirely optional. Base scenario-generation runs standalone; nothing in the base package requires the lane architecture.
- **`--chain`** is optional within walkthrough mode — omitting it yields scenario design only.
- **Independent verifier** is the default but has a defined fallback (orchestrator self-verifies, disclosed in the report). Prefer independence; the fallback exists so a constrained environment does not block the run.

**Breaks if adopted alone.**
- The **asymmetric-knowledge holdout** requires genuinely separate agents. Running all walkthrough lanes as one agent (or letting the design lane see specs) silently destroys the mode's error-detection value while still producing plausible output — the most dangerous partial adoption. If you cannot spawn separate agents, do not claim walkthrough-mode assurance; run base mode instead.
- The **frozen-package / holdout** discipline assumes the eval side and the repair side stay separated. Adopting the scenario pack without preserving that separation lets the implementation tune the evaluator to green and forfeits the confidence the package was meant to provide.

---

## Provider notes

The doctrine above is provider-neutral. These are the provider-specific mechanics.

**Claude.** Invoked as the `/auto-evals` slash command (`/auto-evals walkthrough <target> …` for walkthrough mode). Separate roles and lanes are spawned as subagents via the Agent tool. When a verifier or a meta-synthesis lane must read a full DIB + PCB + spec + implementation + evidence bundle, bind a **large-context (1M) model variant**: the Agent tool's `model` alias enum selects default-context (≈200K) profiles, so a 1M variant must be bound explicitly via the model-ID string in a custom subagent definition (or an equivalent team-config entry). Walkthrough meta-synthesis in particular should run on a large-context agent because it reads all lane outputs plus the full governing corpus.

**Codex.** The skill's doctrine originated from an autonomous eval pilot executed on the Codex side, and the base mode ports cleanly to a Codex/GPT execution lane — the role split, scenario classification, and repair-handoff contract are provider-independent. The main portability constraint is walkthrough mode's requirement for genuinely separate agents with asymmetric read-sets; any provider lane that cannot enforce that separation should run base mode and not advertise walkthrough-mode holdout assurance.
