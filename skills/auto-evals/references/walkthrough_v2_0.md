# Auto-Evals Walkthrough Mode — v2.0 Contract

**Version:** 2.0 (additive to v1.5 — see VERSION.json + SKILL.md)
**Governing artifacts:** current walkthrough-mode contract and lane templates
**Reference:** `references/walkthrough_mode_phase_a_e_reference.md`

> **PCB terminology note:** v2.0 walkthrough-mode content uses "PCB" (Phase Contract Brief). v1.3 doctrine references (`principles_v1_3.md`, `playbook_v1_3.md`) preserve "PRB" (Phase Review Brief) for archival fidelity. The two terms are aliases. When referencing the middle authority layer in v2.0 prose, prefer "PCB (formerly PRB)" at first reference, "PCB" thereafter.

---

## 1. Subcommand contract

```
/auto-evals walkthrough <target> [--chain=<artifact>] [--scope=<level>] [--scenarios=N-M]
```

### Parameters

| Parameter | Required | Shape | Description |
|---|---|---|---|
| `<target>` | yes | positional, path or glob | The DIB/PCB/spec stack to be validated. Walkthrough mode reads the target's governing law and derives scenarios from intent. |
| `--chain=<artifact>` | no (opt-in) | path or glob to realization artifact(s) | If provided, triggers Lane 1b walkthrough against the named realization artifacts after Lane 1a scenarios emit. Without `--chain`, scenarios-only mode terminates after Lane 1a. **`--chain` MUST trigger Lane 1b** — it is not a passive metadata field. **The named artifacts ARE the realization/spec-side stack being validated against intent** — `--chain` targets the spec/realization layer, consistent with Lane 1b's spec-centric read-set (`governing_spec_sections` in the `walkthrough-{NN}.json` schema). Walkthrough of non-spec implementation artifacts (code, configs) is out of scope for v2.0 (see §15). |
| `--scope=<level>` | no | scoped-run enum when available; until then `--scope` documents the composition contract without enum-validation | Narrows the activation overlay across ALL lanes uniformly (generator-level). Lane 1a still gets full intent for holdout-discipline; the narrowing is in chunk-list construction + downstream lane prompts. |
| `--scenarios=N-M` | no (default 12-15) | range like `12-15` or single integer | Lane 1a scenario count; not hardcoded. |

### Agent-Suggestion Refinement

When the invoking agent (orchestrator, validator, implementation) judges that chaining into Lane 1b would be helpful AND `--chain` is not explicitly specified, the agent SHOULD proactively surface the option:

> *"I can chain Lane 1b walkthrough against `<artifacts>` to validate against the generated scenarios. Want me to add `--chain=<artifacts>`?"*

Examples of when surfacing is appropriate:
- Scenarios reference specific realization artifacts that already exist
- The current task framing is "validate implementation X against intent", not just "generate scenarios for review"
- Phase C meta-synthesis is anticipated as a downstream deliverable

This preserves opt-in default while reducing the "I forgot to ask for chaining" failure mode.

### Composition with `--scope`

`--scope` and `--chain` compose:
```
/auto-evals walkthrough <target> --scope=feature --chain=<artifact>
```

`--scope` narrows the chunk-list + lane prompts uniformly; Lane 1a still reads full intent (holdout discipline preserved even under scoped runs).

---

## 2. Lane architecture (summary; full detail in `walkthrough_mode_phase_a_e_reference.md` §2)

```
Phase A — chunking (parallel; 1-N agents per source file; "move briskly" prompt)
   ↓
Phase B Lane 1a — scenario design (ONE capable model, holdout: DIBs + concepts ONLY; FORBIDDEN: the resolved spec set)
   ↓ (fan-out: per-scenario template substitution)
Phase B Lane 1b — walkthrough (N parallel capable models, one per scenario, batched waves of 5-7 — tunable, see §11)
   ↕ (parallel; do not depend on Lane 1b)
Phase B Lane 2 — downward DIB→Spec (capable model, batched 5 chunks/agent — tunable, see §11)
   ↕ (parallel)
Phase B Lane 3 — upward Spec→DIB (capable model, batched 10 chunks/agent — tunable, see §11)
   ↓ (sink: after ALL Phase B drains)
Phase C — meta-synthesis (ONE capable long-context model; reads all lane outputs + DIBs + specs)
```

The five lane prompts are shipped as parameterized templates in `references/lane-templates/` — the orchestrator fills the `{...}` placeholders and dispatches. See `references/lane-templates/README.md`.

### Lane purposes (concise)

| Lane | Reads | Writes | Catches |
|---|---|---|---|
| 1a | DIBs + concepts + Phase A **DIB** chunk list | `lane-1a-scenarios.json` (+ `holdout_integrity` field) | Intent-not-spec'd-anywhere gaps; spec-says-but-DIB-didn't-intend |
| 1b | DIBs + specs + ONE assigned scenario | `walkthrough-{NN}.json` | Spec-stack-can't-produce-DIB-consistent-outcome for concrete scenarios |
| 2 | DIB chunks + DIBs + specs | `L2-batch-NNN-results.json` | DIB intents with no spec realization (downward) |
| 3 | Spec chunks + DIBs + decision artifacts | `L3-batch-NNN-results.json` | Scope creep — spec content with no DIB backing (upward) |
| C | All lane outputs + DIBs + specs | `meta-synthesis.{json,md}` | Cross-lane patterns; absence-as-corroboration |

---

## 3. Holdout discipline — LOAD-BEARING

The asymmetric-knowledge holdout is the load-bearing architectural commitment of walkthrough mode. Per Phase A-E reference §6:

> *Single-lane validation produces correlated noise: an agent doing "check the specs against the DIBs" reasons in one consistent frame and tends to flag (or miss) things in patterns. Triangulation across orthogonal framings catches different error classes.*

### Enforcement (separate agents, not the same agent at different times)

- **Lane 1a** reads DIBs + concepts + Phase A DIB chunk list **only**
- **Lane 1b** reads DIBs + specs + the assigned scenario
- **Phase C** reads all lane outputs + DIBs + specs as needed
- **Implementation agents** stay blind to the full test set (operate downstream of synthesis output)

### Lane 1a prompt MUST include the parametric forbidden read-set clause

The forbidden read-set is **resolved from `<target>`**, NOT a hardcoded literal. The orchestrator identifies which files in the target stack constitute the *realization* being validated (the spec set) — for the conventional `synthesis/spec_*.md` corpus this resolves to that glob, but for any target whose specs are differently named it resolves to the actual spec paths. The Lane 1a prompt embeds the resolved set:

```
FORBIDDEN reads: Do NOT read any file in the resolved spec set:
  <resolved spec paths/globs>
Also forbidden: the Phase A spec chunk list (`unified-spec-chunks.json` or its
target-specific equivalent). The specs are the realization being validated; if
you read them, the holdout is broken.
```

If the spec set cannot be unambiguously resolved from `<target>`, the orchestrator MUST surface that before dispatching Lane 1a — do NOT silently fall back to a literal glob. See `references/lane-templates/lane-1a-scenario-design-template.md` for the full parameterized prompt.

### Lane 1a output MUST include the parametric `holdout_integrity` field

```json
"holdout_integrity": "Files read: <enumerate every file path you Read>. No files from the resolved spec set were read. Resolved spec set checked against: <resolved spec paths/globs>"
```

Phase C audits the holdout by **set-intersection** of Lane 1a's enumerated `files_read` against the resolved spec set: empty intersection → `holdout_integrity_verdict: PRESERVED`; non-empty → `BREACHED`; field missing or unparseable → `UNVERIFIED`. The audit is corpus-agnostic because it compares against the *resolved* set, not a literal `spec_*.md` pattern — closing the silent-breach risk for targets whose specs are not named `spec_*.md`.

### Why this is load-bearing — the F01 example

The reference run's only BLOCKING finding (F01 cross-provider partial-failure semantics) was **structurally invisible** to Lane 2 (REALIZED at principle level — couldn't see the partial-failure dimension), to Lane 3 (zero of 509 spec chunks addressed partial-failure — couldn't flag what wasn't there), and would have been invisible to any agent that had read specs first (spec-reading bias toward mirroring spec structure).

**Only a holdout-disciplined Lane 1a could surface F01.** Any v2.x implementation that lets the same agent design scenarios AND walk them through specs (or gives the scenario-design agent spec context "for grounding") destroys this F01-class error-detection capability.

---

## 4. Phase C absence-as-corroboration — LOAD-BEARING inferential validation property

Phase C is NOT mere aggregation. It must apply **absence-as-corroboration** as a named meta-synthesis pattern.

### Mechanism

When a Lane 1b finding is single-lane (only one walkthrough flagged it), the meta-synthesizer searches Lane 3 for chunks addressing the topic. **Zero matching Lane 3 chunks does not weaken the finding — it strengthens it.**

In the reference run, one finding's confidence was upgraded from "single-lane" to "single-lane + structural confirmation" because Lane 3 found zero of 509 spec chunks addressing the topic. Another finding received the same upgrade for tool-side preflight.

### Phase C prompt MUST include the absence-as-corroboration instruction

```
Absence-as-corroboration: when a Lane 1b finding is single-lane, search Lane 3
for chunks addressing the topic. Zero matching Lane 3 chunks strengthens the
finding (single-lane → "single-lane + structural confirmation"); it does not
weaken it. The topic being structurally absent from the spec stack is itself
evidence that the spec doesn't address the issue.
```

### Anti-pattern explicitly named

Omitting Phase C absence-as-corroboration "because it feels inferential" downgrades Phase C from inferential validation to mere aggregation. v2.0 builds without it are incomplete.

---

## 5. Verdict vocabularies (inline; load-bearing for downstream tooling compatibility)

| Layer | Vocabulary | Source |
|---|---|---|
| **Lane 1b scenario verdict** | `ALIGNED \| PARTIAL \| CONTRADICTED \| SILENT \| AMBIGUOUS` | lane-1b template |
| **Lane 1b per-chunk status** | `REALIZED \| PARTIAL \| MISSING \| CONTRADICTED` | lane-1b template |
| **Lane 1b finding severity** | `blocking \| concerning \| minor` (lower-case, exact) | lane-1b template |
| **Lane 2 alignment** | `REALIZED \| PARTIAL \| MISSING \| CONTRADICTED \| OUT_OF_SCOPE` | lane-2 template |
| **Lane 2 site completeness** | `fully \| partially \| tangentially` | lane-2 template |
| **Lane 3 justification** | `JUSTIFIED \| DR_JUSTIFIED \| INDIRECT \| ORPHAN \| OVER_ENGINEERED` | lane-3 template |
| **Lane 3 trace path** | `Direct DIB principle \| Via decision artifact \| Via PCB pattern \| Implementation-discipline` | lane-3 template |
| **Lane 3 strength** | `strong \| moderate \| tenuous` | lane-3 template |
| **Phase C confidence** | `triple-confirmed \| double-confirmed \| single-lane \| single-lane-plus-structural-confirmation` | phase-c template |
| **Phase C recommendation** | `GO \| SURGICAL_PATCH \| VERSION_BUMP \| NEW_DR \| DEFER \| ARCHITECTURAL_REVIEW` | phase-c template |
| **Phase C canonization** | `yes \| yes-with-surgical \| no-blocking-found` | phase-c template |
| **Phase C holdout verdict** | `PRESERVED \| BREACHED \| UNVERIFIED` | phase-c template |

### Operational meaning of critical vocabularies

- **`REALIZED` (Lane 2) vs `JUSTIFIED` (Lane 3)** — intentionally distinct vocabularies; downward vs upward direction. Downstream tooling reading both lanes MUST NOT collapse them into a generic pass/fail.
- **`OUT_OF_SCOPE` (Lane 2)** — the DIB intent is meta-level (process commitment that does not need spec encoding); the agent must document why it's meta-level.
- **`INDIRECT` (Lane 3)** — the spec choice traces via implementation-discipline (validators, FMs) rather than directly. This is **not a finding** — it is legitimate implementation-discipline trace.
- **`OVER_ENGINEERED` (Lane 3)** — the design choice has DIB trace but goes beyond what the DIB strictly requires. Recommendation: `demote-to-DR`.
- **`yes-with-surgical`** — distinct from `yes` (clean) and `no-blocking-found` (incomplete validation). This verdict survived from Phase C straight into the run's actual disposition.
- **`single-lane-plus-structural-confirmation`** (Phase C confidence) — a single-lane finding upgraded because Lane 2/Lane 3 silence corroborates it (absence-as-corroboration, §4). A FORMAL confidence value an enum-strict downstream tool must accept — not a prose annotation.

### Compatibility surface (no rename)

Verdict vocabularies are a **compatibility surface**. Renaming or normalizing the exact lane enums would break downstream synthesis even if the prose still sounds equivalent. Treat these strings as API contract.

---

## 6. Lane 3 `CONTRADICTORY` handling (Q2 resolved)

**Resolution:** Phase-C-only meta-tag (option b). The Phase C meta-synthesis reports CONTRADICTORY findings across lane outputs even though no individual lane enum (including Lane 3) explicitly includes `CONTRADICTORY` as one of its base verdicts.

### Rationale

Extending the Lane 3 enum to include `CONTRADICTORY` would conflate justification-status (Lane 3's question: "is this spec chunk justified by intent?") with contradiction-detection (Phase C's job: "does this contradict another lane's finding?"). Keeping CONTRADICTORY as Phase-C-only preserves the load-bearing direction-distinct vocabularies (REALIZED downward / JUSTIFIED upward) while letting Phase C cross-correlate.

### Documentation in Lane 3 template

The Lane 3 prompt enum stays:
```
JUSTIFIED | DR_JUSTIFIED | INDIRECT | ORPHAN | OVER_ENGINEERED
```

The Phase C prompt has an additional cross-lane analysis instruction:
```
Phase C may identify CONTRADICTORY findings by cross-correlating Lane 1b, Lane 2,
and Lane 3 outputs. CONTRADICTORY is a Phase-C-only meta-tag and is not present
in the Lane 3 base enum.
```

---

## 7. `SURGICAL_PATCH` count source-of-truth (Q1 resolved)

**Resolution:** `meta-synthesis.json`'s `canonization_summary.recommendation_distribution.SURGICAL_PATCH` field is authoritative for the Phase C synthesis output. Downstream tooling reads JSON, not the markdown report.

### When counts diverge

The reference run had a 3-way count discrepancy:
- Process report: "14 SURGICAL_PATCH"
- `meta-synthesis.json`: 13 SURGICAL_PATCH
- Actual landed patches in v3.4.3: 12 patches (some findings folded into one patch)

**Authoritative for synthesis output:** `meta-synthesis.json` (13).
**Annotate in `meta-synthesis.md` companion:** the actual-landed count (e.g., "12 patches landed; some findings folded") with explicit source-of-truth note.

This avoids the "is the count 14, 13, or 12?" ambiguity downstream tooling encounters when only one number is reported.

---

## 8. Output file paths convention (Q3 resolved)

**Pinned naming:**

| File | Pattern | Where |
|---|---|---|
| Phase A chunk lists | `phase-a/unified-dib-chunks.json`, `phase-a/unified-spec-chunks.json` | Phase A output |
| Lane 1a | `phase-b/lane-1a-scenarios.json` | Lane 1a output |
| Lane 1b | `phase-b/walkthrough-{NN}.json` (one per scenario; `{NN}` is the full scenario ID, e.g. `S01`) | Lane 1b outputs |
| Lane 2 | `phase-b/L2-batch-NNN-results.json` (NNN is 3-digit batch ID) | Lane 2 batched outputs |
| Lane 3 | `phase-b/L3-batch-NNN-results.json` | Lane 3 batched outputs |
| Phase C | `phase-c/meta-synthesis.json` + `phase-c/meta-synthesis.md` | Phase C output (sink) |

**Rationale:** `L2-batch-NNN-results.json` matches reference artifacts AND the per-batch ID is informationally richer for Phase C correlation. Phase C prompt's `Glob+Read` instruction stays compatible (the prompt already says "Use Glob + Read to enumerate the lane output files; don't assume an exact count").

---

## 9. Output JSON schemas (5 schemas)

### 9.1 — `lane-1a-scenarios.json`

```json
{
  "agent_id": "<agent identifier>",
  "holdout_integrity": "Files read: <enumerated paths>. No files from the resolved spec set were read. Resolved spec set checked against: <resolved spec paths/globs>",
  "scenarios": [
    {
      "scenario_id": "S01",
      "category": "common | edge | adversarial",
      "scenario_classification": "strict contract gate | evidence probe | corpus scan | ergonomics warning",
      "title": "<short title>",
      "narrative": "<scenario narrative>",
      "actors": ["<actor 1>", "<actor 2>"],
      "tested_intents": [
        {"chunk_id": "<DIB chunk id>", "claim": "<what intent is being tested>"}
      ],
      "expected_specs_to_address": ["<spec section>"],
      "what_to_check_in_lane_1b": "<what Lane 1b should look for when walking this scenario>"
    }
  ],
  "coverage_notes": "<any coverage gaps or notable choices>"
}
```

**Two orthogonal scenario axes:** `category` is the *stress-profile* axis (`common | edge | adversarial` — how hard the scenario pushes); `scenario_classification` is the *consequence-class* axis carried verbatim from v1.3 doctrine (`strict contract gate | evidence probe | corpus scan | ergonomics warning` — how a failure should be weighed). Both are recorded; Phase C + `/root-cause` routing consume `scenario_classification` to weigh findings. This is how walkthrough mode preserves v1.3's scenario classification (see §14).

### 9.2 — `walkthrough-{NN}.json`

```json
{
  "agent_id": "<agent identifier>",
  "scenario_id": "S01",
  "verdict": "ALIGNED | PARTIAL | CONTRADICTED | SILENT | AMBIGUOUS",
  "walkthrough_steps": [
    {
      "step_number": 1,
      "what_happens": "<step description>",
      "governing_spec_sections": [
        {"spec": "<spec name>", "section": "<section ref>", "what_it_says": "<verbatim or paraphrase>"}
      ],
      "verdict_for_step": "ALIGNED | PARTIAL | CONTRADICTED | SILENT | AMBIGUOUS",
      "rationale": "<why this verdict>"
    }
  ],
  "overall_verdict_rationale": "<paragraph>",
  "tested_intent_status": [
    {"chunk_id": "<DIB chunk id>", "status": "REALIZED | PARTIAL | MISSING | CONTRADICTED", "evidence": "<evidence>"}
  ],
  "findings": [
    {
      "severity": "blocking | concerning | minor",
      "title": "<short title>",
      "description": "<paragraph>",
      "affected_specs": ["<spec section>"],
      "suggested_action": "surgical patch ... | needs-judgment ... | architectural-review ..."
    }
  ]
}
```

### 9.3 — `L2-batch-NNN-results.json` (Lane 2 downward)

```json
{
  "agent_id": "<agent identifier>",
  "batch_id": "NNN",
  "reports": [
    {
      "chunk_id": "<DIB chunk id>",
      "chunk_title": "<title>",
      "alignment_status": "REALIZED | PARTIAL | MISSING | CONTRADICTED | OUT_OF_SCOPE",
      "realization_sites": [
        {"spec": "<spec>", "section": "<section>", "realization_summary": "<summary>", "verbatim_quote": "<quote>", "completeness": "fully | partially | tangentially"}
      ],
      "missing_aspects": [{"aspect": "<aspect>", "severity": "blocking | concerning | minor"}],
      "contradictions": [{"spec": "<spec>", "section": "<section>", "what_contradicts": "<what>", "severity": "..."}],
      "overall_verdict": "<one of the alignment_status enums>",
      "suggested_action": "<action>"
    }
  ]
}
```

### 9.4 — `L3-batch-NNN-results.json` (Lane 3 upward)

```json
{
  "agent_id": "<agent identifier>",
  "batch_id": "NNN",
  "reports": [
    {
      "chunk_id": "<spec chunk id>",
      "chunk_title": "<title>",
      "justification_status": "JUSTIFIED | DR_JUSTIFIED | INDIRECT | ORPHAN | OVER_ENGINEERED",
      "primary_justification": {
        "dib_intent": "<DIB intent referenced>",
        "dib_section": "<section ref>",
        "trace_path": "Direct DIB principle | Via decision artifact | Via PCB pattern | Implementation-discipline",
        "strength": "strong | moderate | tenuous"
      },
      "supporting_drs": ["<DR ref>"],
      "orphan_aspects": ["<aspect>"],
      "over_engineering_signals": ["<signal>"],
      "overall_verdict": "<one of the justification_status enums>",
      "suggested_action": "<action>"
    }
  ]
}
```

### 9.5 — `meta-synthesis.json` (Phase C sink)

```json
{
  "agent_id": "<agent identifier>",
  "lane_outputs_consumed": {
    "lane_1a": "<path>",
    "lane_1b_count": N,
    "lane_2_count": N,
    "lane_3_count": N
  },
  "holdout_integrity_verdict": "PRESERVED | BREACHED | UNVERIFIED",
  "findings": [
    {
      "finding_id": "F01",
      "severity": "blocking | concerning | minor",
      "title": "<title>",
      "confidence": "triple-confirmed | double-confirmed | single-lane | single-lane-plus-structural-confirmation",
      "recommendation": "GO | SURGICAL_PATCH | VERSION_BUMP | NEW_DR | DEFER | ARCHITECTURAL_REVIEW",
      "evidence_paths": ["<path>"]
    }
  ],
  "systemic_patterns": [{"pattern_id": "P1", "description": "<>", "drives_findings": ["F01", "F11"]}],
  "canonization_summary": {
    "total_findings": N,
    "blocking": N,
    "concerning": N,
    "minor": N,
    "recommendation_distribution": {
      "GO": N, "SURGICAL_PATCH": N, "VERSION_BUMP": N, "NEW_DR": N, "DEFER": N, "ARCHITECTURAL_REVIEW": N
    },
    "ready_for_canonization": "yes | yes-with-surgical | no-blocking-found",
    "summary": "<paragraph>"
  }
}
```

Companion `meta-synthesis.md` is a human-readable Markdown report covering the same content with additional narrative + the actual-landed count annotation (per Q1).

---

## 10. Compaction-resistance: outputs-to-files (NOT chat)

Every lane agent writes its output JSON to a deterministic path. **Outputs-to-chat-only emission is forbidden** because long runs must survive session interruption. Chat-only emission destroys outage recoverability for runs that exceed a session lifetime.

---

## 11. Tuning parameters NOT to bake (per Phase A-E §10)

These were reference-run-specific empirical choices; the skill exposes them as tuning parameters or auto-tunes:

- **Batch sizes** — 5 chunks/agent for Lane 2; 10 chunks/agent for Lane 3 (run-specific; expose as parameter or auto-tune from chunk count + agent context budget)
- **Scenario count** — 13 in the reference run (range 12-15 prompt-defined); expose as `--scenarios=N-M`
- **Wave sizes** — 5-7 per wave for Lane 1b; 6-8 per wave for Lane 3 (operational comfort range; let orchestrator set based on observed dispatch stability)
- **Concept-file enumeration** — Lane 1a's "5-10 concepts most cited by the DIBs" was domain-specific; make concept-source directory configurable
- **Chunking ratios** — 41 DIB chunks + 509 spec chunks were Phase A's output for the specific 3-DIB + 5-spec stack; document chunk-record schema + stall-mitigation pattern, NOT the counts

---

## 12. Temp-Install vs Live-Install Deferral-Mutation Discipline

**Load-bearing:** Auto-defer is **live-install activation behavior only**. When v2.0 is staged in a temp install root, temp-build validation MUST NOT auto-mutate canonical deferral state. Only first invocation under the live provider skill path may execute the mutation.

This avoids the failure mode where a temp-build validation pass either:
(a) prematurely mutates canonical deferral state (corruption hazard), or
(b) documents a fallback path that doesn't correspond to the staged artifact being reviewed (misdirection hazard).

---

## 13. Minimum Self-Verification Fixture

For `/auto-evals` users wanting to verify a v2.x build, the minimum demonstrating fixture is:

- **Use a small real DIB** (e.g., Shared-Skills DIB v2.3 itself, or a minimal synthetic DIB+spec set)
- **`--scenarios=3-5`** for speed (smaller scenario count than the 12-15 default)
- **Verify ALL load-bearing properties** are exercised:
  - Holdout breach detection (Lane 1a's forbidden-glob clause + Phase C's `holdout_integrity_verdict`)
  - Chain fanout (`--chain` triggers Lane 1b walkthrough; NOT passive metadata)
  - Scope composition (`--scope` narrows uniformly across all lanes; Lane 1a still reads full intent)
  - Lane 3 CONTRADICTORY handling (Phase-C-only meta-tag; not in Lane 3 base enum)
  - Phase C absence-as-corroboration (single-lane finding strengthened by Lane 2/3 silence)
  - Output-to-files (every lane output written to deterministic path)

### Future enhancement (deferred)

Build a synthetic minimal DIB+spec fixture at `references/test-fixtures/` that exercises ALL load-bearing properties in a tightly-controlled corpus. Track it as a `/deferrals` item for v2.1 or later.

---

## 14. v1.3 doctrine preservation

v1.3 doctrine (Authority Hierarchy, anchoring discipline, scenario classification, root-cause handoff contract) is PRESERVED VERBATIM in `references/principles_v1_3.md` and `references/playbook_v1_3.md`. Walkthrough mode is **additive** — it does not replace v1.3; it supplements `/auto-evals` with a new sub-capability.

### What walkthrough mode adds beyond v1.3

- Multi-lane orthogonal validation (1a / 1b / 2 / 3 + Phase C)
- Asymmetric-knowledge holdout enforced by separate agents
- 12-vocabulary verdict surface (specific to lane direction)
- Phase C absence-as-corroboration meta-synthesis
- Compaction-resistant outputs-to-files

### What walkthrough mode preserves from v1.3

- Authority Hierarchy: DIB > PCB (formerly PRB) > Spec
- Anchoring discipline: every scenario carries a DIB/PCB/Spec anchor line
- Scenario classification: strict contract gate / evidence probe / corpus scan / ergonomics warning — carried into walkthrough mode via the `scenario_classification` field on each Lane 1a scenario (§9.1); the consequence-class axis, orthogonal to the `category` stress-profile axis
- Result classification: pass / fail / warning (for non-walkthrough invocations)
- Root-cause handoff contract: 7-field packet (failing scenarios + symptoms + reusable layer + discrepancy seed + blast-radius + action bucket + authority-layer diagnosis)
- Verification independence rule
- Holdout protection rule
- Stop conditions

---

## 15. Explicitly out of scope (v2.0)

- **Phase D / Phase E patch-landing** — walkthrough mode emits meta-synthesis as terminal output; auto-land is orchestrator-level decision
- **`--mode=walkthrough` flag form** — locked to subcommand
- **Sub-skill `/auto-evals-walkthrough`** — rejected
- **Scoped-run primitive implementation** — `--scope` composition contract documented; enum-validation defers to scoped-run support
- **Cross-provider publish** — Claude-side canonical
- **Schema changes to v1.3 result classification** — preserved verbatim
- **Building general always-on orchestration framework** — focused eval/walkthrough capability only

---

## 16. Cross-references

- **`references/lane-templates/`** — the 5 parameterized lane prompt templates (`lane-1a-scenario-design-template.md`, `lane-1b-walkthrough-template.md`, `lane-2-downward-template.md`, `lane-3-upward-template.md`, `phase-c-meta-synthesis-template.md`) + `README.md`
- **`references/walkthrough_mode_phase_a_e_reference.md`** — high-fidelity walkthrough reference
- **`references/principles_v1_3.md` + `references/playbook_v1_3.md`** — preserved v1.3 doctrine (authority hierarchy, anchoring, scenario classification, root-cause handoff)

---

*End of walkthrough-mode v2.0 contract.*
