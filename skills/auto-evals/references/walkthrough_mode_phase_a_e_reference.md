# Auto-Evals Walkthrough-Mode: High-Fidelity Reference

**Audience:** implementation agents building the `/auto-evals` skill v2.x walkthrough-mode upgrade.
**Source-priority basis:** process report, scoped-run primitive design, Phase C meta-synthesis, lane prompt templates, and Lane 1a/1b/2/C output samples.
**Run identity:** historical DIB-validation canonization gate.

---

## 1. Overview

The reference run was a canonization gate for a DIB/spec cycle. The user directed a **DIB-validation final pass**: a three-way orthogonal verification of the spec stack (5 specs) against the DIBs (3 DIBs) before declaring the cycle complete. The user explicitly framed this as *"auto-evals" thinking* and asked for autonomous execution.

The run produced **74 lane outputs** (1 Lane 1a + 13 Lane 1b + 9 Lane 2 batches + 51 Lane 3 batches). The Phase C meta-synthesizer consumed those and emitted **21 findings** (1 BLOCKING, 11 concerning, 9 minor), distributed across **13 SURGICAL_PATCH + 6 DEFER + 2 ARCHITECTURAL_REVIEW** recommendations. The meta-synthesizer issued the verdict **`yes-with-surgical`** for canonization readiness (note: this verdict label is the most important single artifact for downstream tooling and is taken verbatim from `meta-synthesis.json`'s `ready_for_canonization` field; the process report itself rounds this to "14 SURGICAL_PATCH" — a discrepancy with `meta-synthesis.json`'s **13** SURGICAL_PATCH plus the actual v3.4.3 land of **12 patches**; treat 13 as authoritative for the synthesis output and 12 as the actual landed-patches count).

What made it succeed: (a) orthogonal lane framing, not just multiple agents doing the same job differently; (b) **strict holdout discipline** on Lane 1's scenario design surfaced an error class the other lanes were structurally blind to; (c) batched chunk processing with prefix caching reduced wall-clock time; (d) outputs went to files rather than chat text, so mid-flight account interruption did not destroy in-flight work.

---

## 2. Lane Architecture

### Lane 1a — Scenario Design (Holdout)

- **Inputs (enumerated by the agent in its own `holdout_integrity` field):** 3 v2 DIB files + `concepts-index.md` + 5-10 selected concept .md files + Phase A `preflight-1-dibs.json` (DIB chunk list) + the Lane 1a prompt itself. 19 input files total per the meta-synthesis report.
- **Forbidden reads:** anything matching `synthesis/spec_*.md`. The prompt makes this explicit: *"if you see them, the holdout is broken."*
- **Output shape:** one JSON file `lane-1a-scenarios.json`. Required fields: `agent_id`, `holdout_integrity` (enumerated files-read string + verbatim *"No spec_\*.md files were read."*), `scenarios` (array of `{scenario_id, category, title, narrative, actors, tested_intents[{chunk_id, claim}], expected_specs_to_address, what_to_check_in_lane_1b}`), `coverage_notes`.
- **Verdict vocabulary:** none — Lane 1a does not adjudicate; it produces scenarios. The `category` enum is `common | edge | adversarial`. The actual run produced **13 scenarios** distributed 6 common / 5 edge / 2 adversarial (`S01-S06` common, `S07-S11` edge, `S12-S13` adversarial).
- **Agent class:** ONE capable model (`run_in_background=true`).
- **Batching:** 1 agent, no chunking — Lane 1a is a single synthesis pass.
- **What error class this catches:** *intent-not-spec'd-anywhere* and *spec-says-but-DIB-didn't-intend* gaps. The holdout discipline is what makes scenarios *test* intent rather than *mirror* spec structure.

### Lane 1b — Scenario Walkthrough

- **Inputs:** 3 DIBs (re-read for tested-intent grounding) + 5 specs + the single Lane 1a scenario assigned to that agent (substituted into the template via `{NN}`, `{TITLE}`, `{NARRATIVE}`, `{ACTORS}`, `{TESTED_INTENTS}`, `{WHAT_TO_CHECK}` placeholders).
- **Output shape:** one JSON file per scenario, `walkthrough-S{NN}.json`. Required fields: `agent_id`, `scenario_id`, `verdict`, `walkthrough_steps[{step_number, what_happens, governing_spec_sections[{spec, section, what_it_says}], verdict_for_step, rationale}]`, `overall_verdict_rationale`, `tested_intent_status[{chunk_id, status, evidence}]`, `findings[{severity, title, description, affected_specs, suggested_action}]`.
- **Verdict vocabulary (prompt-defined, exact strings):**
  - `ALIGNED` — specs handle the scenario consistently with all tested DIB intents.
  - `PARTIAL` — specs handle most aspects but ≥1 tested intent is partially missed.
  - `CONTRADICTED` — a spec section actively contradicts a DIB intent.
  - `SILENT` — a tested DIB intent has no spec realization.
  - `AMBIGUOUS` — specs are unclear; a reasonable agent could go either way.
- **Tested-intent status vocabulary:** `REALIZED | PARTIAL | MISSING | CONTRADICTED` (per-chunk, distinct from the scenario-level verdict above).
- **Finding severity:** `blocking | concerning | minor` (lower-case, exact strings in the JSON). `suggested_action`: free-form string starting with `surgical patch` / `needs-judgment` / `architectural-review`.
- **Agent class:** ONE capable model per scenario.
- **Batching:** *"batched in waves of 5-7"*. With 13 scenarios, this is ~2-3 waves.
- **What error class this catches:** spec-stack-can't-produce-DIB-consistent-outcome for a concrete scenario. Captures *gap-in-realization* errors that downward-lane and upward-lane miss when the topic is structurally absent from spec.

### Lane 2 — DIB → Spec (Downward)

- **Inputs:** the batch file `phase-b-lane-2/batches/batch-{N}.json` (containing 5 DIB chunk records) + 3 DIB source files + 5 spec files.
- **Output shape:** one JSON file per batch, `L2-batch-{NNN}-results.json`. Required fields: `agent_id`, `batch_id`, `reports[]` array of 5 `{chunk_id, chunk_title, alignment_status, realization_sites[{spec, section, realization_summary, verbatim_quote, completeness}], missing_aspects[{aspect, severity}], contradictions[{spec, section, what_contradicts, severity}], overall_verdict, suggested_action}`.
- **Verdict vocabulary (exact, from prompt):**
  - `REALIZED` — specs fully address the DIB intent.
  - `PARTIAL` — specs address most but miss aspects.
  - `MISSING` — no spec realization found.
  - `CONTRADICTED` — some spec actively conflicts.
  - `OUT_OF_SCOPE` — the intent is meta-level and doesn't need spec encoding (document why).
- **Per-site completeness:** `fully | partially | tangentially`.
- **Agent class:** capable long-context model.
- **Batching strategy:** **5 chunks per agent.** 41 DIB chunks → **9 batches** (confirmed by directory listing `L2-batch-001-results.json` through `L2-batch-009-results.json` and 9 input batch files). The prompt instructs *"Move briskly per chunk. You have 5 chunks; allocate effort accordingly."*
- **What error class this catches:** DIB intents with **no spec realization** anywhere. Run result: 41/41 REALIZED, zero MISSING/CONTRADICTED/OUT_OF_SCOPE.

### Lane 3 — Spec → DIB (Upward)

- **Inputs:** the batch file `phase-b-lane-3/batches/batch-{N}.json` (containing 10 spec chunk records) + 3 DIB source files + decision records (read selectively as needed).
- **Output shape:** one JSON file per batch, `L3-batch-{NNN}-results.json`. Required fields: `agent_id`, `batch_id`, `reports[]` array of 10 `{chunk_id, chunk_title, justification_status, primary_justification{dib_intent, dib_section, trace_path, strength}, supporting_drs, orphan_aspects, over_engineering_signals, overall_verdict, suggested_action}`.
- **Verdict vocabulary (exact, from prompt):**
  - `JUSTIFIED` — direct trace to a DIB intent (principle, WCL, acceptance criterion).
  - `DR_JUSTIFIED` — traces via a DR that itself ties to DIB intent.
  - `INDIRECT` — traces via implementation discipline (validators, FMs) emerging from DIB intent.
  - `ORPHAN` — no clear DIB tie. Possibly scope creep.
  - `OVER_ENGINEERED` — formally justified but goes beyond what DIB requires.
- **Trace-path vocabulary:** `Direct DIB principle | Via decision artifact | Via PCB pattern | Implementation-discipline`. Strength: `strong | moderate | tenuous`.
- **Note on `CONTRADICTORY`:** the Phase C meta-synthesis report tallies "0 CONTRADICTORY" for Lane 3, even though the Lane 3 prompt enum does not include CONTRADICTORY as one of the five base verdicts. This appears to be a meta-synthesizer-side reclassification dimension — Phase C is implicitly checking for spec-DIB contradiction within Lane 3 chunks. **Surface this conflict explicitly:** if walkthrough-mode v2.x intends to reuse the Lane 3 verdict enum verbatim, it should pick either (a) extend the enum to include CONTRADICTORY, or (b) keep CONTRADICTORY as a Phase-C-only meta-tag.
- **Agent class:** capable model.
- **Batching strategy:** **10 chunks per agent.** 509 spec chunks → **51 batches** (confirmed). The prompt instructs *"Move briskly per chunk. 10 chunks per batch — keep per-chunk analysis crisp"* and *"Be tough on orphans — if no DIB tie, flag it. Better to over-flag and let Phase C synthesize than miss scope creep."*
- **What error class this catches:** **scope creep** — spec content with no DIB intent backing it. Run result: 509/509 JUSTIFIED/INDIRECT/DR_JUSTIFIED, zero ORPHAN, zero OVER_ENGINEERED.

### Phase C — Meta-Synthesis

- **Inputs:** all Lane 1a + Lane 1b + Lane 2 + Lane 3 output files + Phase A chunk lists + 3 DIBs + 5 specs (consulted selectively). The prompt instructs *"Use Glob + Read to enumerate the lane output files; don't assume an exact count."*
- **Output shape:** TWO files — `meta-synthesis.json` (structured) and `meta-synthesis.md` (human-readable). JSON required fields: `agent_id`, `lane_outputs_consumed{lane_1a, lane_1b_count, lane_2_count, lane_3_count}`, `holdout_integrity_verdict` (`PRESERVED | BREACHED | UNVERIFIED`), `findings[]`, `systemic_patterns[]`, `canonization_summary{total_findings, blocking, concerning, minor, recommendation_distribution{GO, SURGICAL_PATCH, VERSION_BUMP, NEW_DR, DEFER, ARCHITECTURAL_REVIEW}, ready_for_canonization, summary}`.
- **Finding confidence vocabulary:** `triple-confirmed | double-confirmed | single-lane`.
- **Recommendation vocabulary:** `GO | SURGICAL_PATCH | VERSION_BUMP | NEW_DR | DEFER | ARCHITECTURAL_REVIEW`.
- **Canonization-readiness verdicts:** `yes | yes-with-surgical | no-blocking-found`.
- **Agent class:** ONE capable long-context model; Phase C consumed many files and re-read DIBs + specs as needed, so long context is load-bearing.
- **What error class this catches:** cross-lane patterns. Reclassifies single-lane findings as "single-lane + structural confirmation" when Lane 2 or Lane 3 corroborates by absence.

---

## 3. Orchestration Flow

The actual run sequenced as follows:

1. **Phase A (chunking) — parallel.** Three capable long-context agents in parallel chunked artifacts: DIBs and the spec bundle. One agent stalled on a single-large-write; mitigation split that work into smaller batches with tightened "move briskly" instructions. All three eventually succeeded. Outputs merged into `unified-dib-chunks.json` (41 chunks) and `unified-spec-chunks.json` (509 chunks).

2. **Phase B Lane 1a — single agent.** Spawned with `run_in_background=true`. Wrote `lane-1a-scenarios.json` with 13 scenarios. Lane 1a *must finish* before Lane 1b can start (Lane 1b prompts are templates that need the Lane 1a scenarios substituted in).

3. **Phase B Lane 1b — chain-fanout from Lane 1a.** Once Lane 1a's output was available, the orchestrator extracted each scenario's fields and substituted them into the per-scenario walkthrough template. 13 walkthrough agents were dispatched, batched in waves of 5-7 — so ~2-3 dispatch waves.

4. **Phase B Lanes 2 + 3 — parallel with Lane 1b.** These do not depend on Lane 1a output; they consume Phase A chunk lists directly. Lane 2's 9 batches and Lane 3's 51 batches dispatched in waves. The mid-flight account outage hit during *Lane 3 wave 7-8*, implying Lane 3 dispatched in roughly 7-8 wave units (51 batches / ~7 waves ≈ 7-8 batches per wave; see §8 below).

5. **Phase C — meta-synthesis.** Single capable long-context agent dispatched after all Phase B lanes drained. Read all 74 lane outputs (1 + 13 + 9 + 51) plus DIBs and specs as needed.

6. **Phase D / Phase E — patch landing (out of scope for v2.x walkthrough mode).** The patch-landing phase applied surgical patches autonomously per user pre-authorization, then routed architectural review items to user judgment.

**Chain shape (manually orchestrated):** Lane 1a → Lane 1b is a hard chain (Lane 1b waits on Lane 1a output to populate per-scenario prompts). Lane 2 + Lane 3 + Lane 1a all start in parallel against Phase A's chunk artifacts. Phase C is a hard sink — it cannot start until all Phase B lanes are done.

---

## 4. Phase A Chunking

The 5 spec files yielded **509 spec chunks**; the 3 DIB files yielded **41 DIB chunks** (Root 16 + DIB-System 13 + Shared-Skills 12 per the process report). Average spec-chunk-to-spec ratio: ~102 chunks/spec.

**Chunk record shape (confirmed from `preflight-1-dibs.json`):** `{chunk_id, source, section, title, summary, verbatim_anchor}`. The `verbatim_anchor` is a short verbatim string from the source document used to locate the chunk in its full original context (the Lane 2/3 prompts instruct the agent to "re-read the chunk's intent in its DIB's full context (use the `verbatim_anchor` to locate)"). For the inspected first chunk (`ROOT-WCL`), `verbatim_anchor` length was 163 characters — i.e., chunks reference anchors rather than carrying the full chunk body, keeping the chunk-list file compact.

**Stall mitigation (the "move briskly" pattern):** Phase A initially ran three parallel agents (one per DIB, one for Specs 00+01+04, one for Specs 02+03). The Specs-00+01+04 agent stalled at 600 seconds with the message *"Now I'll write the chunked JSON file..."* — a known failure mode where the agent has computed the output internally but is blocked on the single large write. Mitigation pattern, documented in the process report:

- Split the stalling agent into smaller agents (2a, 2b, 2c — one per spec).
- Add a "move briskly" directive to the prompt to discourage over-elaboration.

**Recommendation for walkthrough-mode v2.x:** Phase A chunk-size and overlap conventions are not pinned by the prompts — they are agent-discretion. The orchestrator validates only that chunks have the required schema fields. Walkthrough-mode v2.x should not pin specific chunk counts; it should pin the **chunk-record schema** and the **stall-recovery split pattern**.

---

## 5. Verdict Vocabularies (consolidated reference)

| Layer | Vocabulary | Source |
|---|---|---|
| **Lane 1b scenario verdict** | `ALIGNED \| PARTIAL \| CONTRADICTED \| SILENT \| AMBIGUOUS` | `lane-1b-scenario-walkthrough-template.md` |
| **Lane 1b per-chunk status** | `REALIZED \| PARTIAL \| MISSING \| CONTRADICTED` | same |
| **Lane 1b finding severity** | `blocking \| concerning \| minor` | same |
| **Lane 2 alignment** | `REALIZED \| PARTIAL \| MISSING \| CONTRADICTED \| OUT_OF_SCOPE` | `lane-2-batched-template.md` |
| **Lane 2 site completeness** | `fully \| partially \| tangentially` | same |
| **Lane 3 justification** | `JUSTIFIED \| DR_JUSTIFIED \| INDIRECT \| ORPHAN \| OVER_ENGINEERED` | `lane-3-batched-template.md` |
| **Lane 3 trace path** | `Direct DIB principle \| Via decision artifact \| Via PCB pattern \| Implementation-discipline` | same |
| **Lane 3 strength** | `strong \| moderate \| tenuous` | same |
| **Phase C confidence** | `triple-confirmed \| double-confirmed \| single-lane` | `phase-c-meta-opus-template.md` |
| **Phase C recommendation** | `GO \| SURGICAL_PATCH \| VERSION_BUMP \| NEW_DR \| DEFER \| ARCHITECTURAL_REVIEW` | same |
| **Phase C canonization** | `yes \| yes-with-surgical \| no-blocking-found` | same |
| **Phase C holdout verdict** | `PRESERVED \| BREACHED \| UNVERIFIED` | same |

**Operational meaning of the critical ones:**

- `REALIZED` (Lane 2) vs `JUSTIFIED` (Lane 3) are intentionally distinct vocabularies — one is downward-direction, one upward. Tooling reading both lanes should NOT collapse them.
- `OUT_OF_SCOPE` (Lane 2): the DIB intent is meta-level (e.g., a process commitment that does not need spec encoding); the agent must document why it's meta-level.
- `INDIRECT` (Lane 3): the spec choice traces via implementation-discipline (validators, FMs) rather than directly. This is **not a finding** — it is legitimate implementation-discipline trace, as the meta-synthesis report flags explicitly.
- `OVER_ENGINEERED` (Lane 3): the design choice has a DIB trace but goes beyond what the DIB strictly requires. Recommendation: `demote-to-DR`.
- `yes-with-surgical`: the canonization-readiness verdict that produced the 13-patch cleanup pass. Distinct from `yes` (clean) and `no-blocking-found` (incomplete validation).

---

## 6. The Holdout Discipline That Worked

This is the load-bearing architectural commitment of the run. The process report names it as the motivating principle for the entire validation architecture:

> *Single-lane validation produces correlated noise: an agent doing "check the specs against the DIBs" reasons in one consistent frame and tends to flag (or miss) things in patterns. Triangulation across orthogonal framings catches different error classes.*

**Asymmetric-knowledge enforcement (separate agents, not the same agent at different times):**

- Lane 1a (scenario design) reads DIBs + concepts + Phase A DIB chunk list only.
- Lane 1b (scenario walkthrough) reads DIBs + specs + the assigned scenario.
- Phase C meta-synthesizer reads all lane outputs + DIBs + specs as needed.
- Implementation agents (the ones that landed the 12 patches in Phase E) are out of scope for the walkthrough loop — they operate downstream of the synthesis output.

The Lane 1a prompt enforces this by:

1. Listing the forbidden file glob (`synthesis/spec_*.md`) explicitly: *"FORBIDDEN reads: Do NOT read any file in `synthesis/spec_*.md`. The specs are the realization being validated; if you see them, the holdout is broken."*
2. Requiring the agent to self-attest in its output via the `holdout_integrity` field: *"Files read: <enumerate every file path you Read>. No spec_\*.md files were read."*

Phase C then **verifies the holdout** by parsing the `holdout_integrity` field and checking that no spec file path appears in it. In the reference run, the meta-synthesizer's `holdout_integrity_verdict` was `PRESERVED`, and the enumerated input files (visible in the actual `lane-1a-scenarios.json`) confirmed it: 3 DIB files + `concepts-index.md` + 5 concept files + `preflight-1-dibs.json` + the prompt — no spec paths.

### Why this was load-bearing: F01 was structurally invisible without it

**F01 — Cross-provider partial-failure semantics in publish pipeline are unspecified.** This was the only BLOCKING finding. The scenario `S05` walked through the publish pipeline (Claude + Codex + Gemini) and asked: *what happens when one provider succeeds and another fails?*

- **Lane 2** marked SHARED-SKILLS-WCL as REALIZED at the principle level — the WCL anti-shortcut clause exists. Lane 2 had no way to detect the partial-failure dimension because Lane 2 only checks "is the intent realized somewhere?", not "does the realization stress under specific operational failure modes?"
- **Lane 3** found zero spec chunks addressing partial-failure semantics across all 509 chunks. The topic was structurally missing from the spec stack, not misplaced. Lane 3 cannot flag this — it only flags chunks that *exist*.
- **Only Lane 1a** could surface this, and **only because it didn't read the specs first**. A non-holdout Lane 1a would have mirrored spec structure: it would have generated a scenario *"agent runs publish-skill.py and atomic-write completes"* — exactly the case the spec covers — not the orthogonal *"what if one provider's atomic-write completes and another's fails?"*

The process report makes this the explicit justification:

> *Lane 1's BLOCKING finding (cross-provider partial-failure semantics) was structurally invisible to Lane 2 and Lane 3 because the topic was genuinely missing from the spec stack — Lane 2 saw SHARED-SKILLS-WCL realized at the principle level; Lane 3 found zero spec chunks addressing partial-failure. Only a holdout-disciplined Lane 1 scenario could ask "OK, suppose Codex publish fails mid-run while Claude+Gemini succeeded — what does the spec say?" and notice the spec didn't say.*

**This is THE load-bearing justification for keeping the discipline in walkthrough-mode v2.x.** Any v2.x implementation that lets the same agent design scenarios AND walk them through specs (or that gives the scenario-design agent spec context "for grounding") destroys the F01-class error-detection capability.

---

## 7. Meta-Synthesis Pattern

Phase C consumed all 74 Phase B outputs (1 + 13 + 9 + 51) and produced both structured JSON and human-readable markdown.

**The 21-finding categorization grid:**

- **By severity:** 1 BLOCKING (F01), 11 concerning (F02-F12 less the BLOCKING), 9 minor (F13-F21).
- **By recommendation:** 13 SURGICAL_PATCH, 6 DEFER, 2 ARCHITECTURAL_REVIEW, 0 VERSION_BUMP, 0 NEW_DR, 0 GO. (The process report says "14 SURGICAL_PATCH" — this is a 1-count discrepancy with `meta-synthesis.json`'s 13; treat `meta-synthesis.json` as authoritative for the synthesis output and note the v3.4.3 actual land was 12 patches because some findings folded into one patch.)
- **By confidence:** zero triple-confirmed; 2 double-confirmed (F02 via S01+S02; F09 via S08+S10); the rest single-lane, some strengthened by Lane 2/3 *absence-as-corroboration*.

### Absence-as-corroboration — the key meta-synthesis pattern

When a Lane 1b finding is single-lane (only one walkthrough flagged it), the meta-synthesizer searches Lane 3 for chunks addressing the topic. **Zero matching Lane 3 chunks does not weaken the finding — it strengthens it.** F01's confidence was upgraded from "single-lane" to "single-lane + structural confirmation" because Lane 3 found zero of 509 spec chunks addressing partial-failure semantics. F11 received the same upgrade for tool-side preflight: zero Lane 3 chunks bound a DIB-edit preflight, corroborating S12's concern.

This is named explicitly in the Phase C report: *"Single-lane via Lane 3 absence: F01 (S05 + zero Lane-3 chunks on partial-failure), F11 (S12 + zero Lane-3 chunks on tool-side preflight). Lane 3 absence-as-corroboration strengthens these from pure single-lane to 'single-lane + structural confirmation.'"*

**Systemic patterns (P1-P5) the meta-synthesizer surfaced:**

- **P1** — Asymmetric tool-side enforcement at high-authority layers (drives F11, F21).
- **P2** — Lineage Block schema asymmetry across DIB / Companion-Spec / PCB (drives F02, F04).
- **P3** — WCL anti-shortcut clauses with no validator predicate (drives F01, F06, F07).
- **P4** — Synthesis-deferred items that bear on tested scenarios (drives F05, F09, F10, F13, F15).
- **P5** — Cross-spec aggregation gaps (drives F02, F04, F20).

Patterns are not findings; they cluster findings to inform recommendation strategy (e.g., P2 + P5 jointly resolve via the "high-leverage cluster" of F02 + F03 + F04 + F20).

---

## 8. Performance Observations

**Wall-clock:** ~3 hours total (Phase A through Phase C, before patch landing). The process report says: *"Total wall-clock dropped from estimated ~6 hours to ~3 hours"* via batch parallelization and prefix-cache amortization.

**Batch sizes (Phase B):**

- Lane 2: **5 chunks per agent** → 9 batches across 41 DIB chunks.
- Lane 3: **10 chunks per agent** → 51 batches across 509 spec chunks.
- Lane 1b: **1 scenario per agent** → 13 agents.
- Lane 1a: **1 agent total** (no chunking).
- Phase C: **1 agent total** (the synthesis must be unified).

**Parallelism / wave sizes:**

- Lane 1b: *"batched in waves of 5-7"* (per prompt template).
- Lane 3: account-outage hit during *"wave 7-8"* (per process report), suggesting Lane 3 dispatched 51 batches across roughly 7-8 waves — so ~6-8 batches per wave.

**Stability ceiling for sub-agent dispatch:** the process report does not name a hard ceiling but the wave size of 5-7 (Lane 1b) and ~6-8 (Lane 3) suggests this as the operational comfort range during this run.

**Prefix-cache strategy:** **read the spec stack once per agent; emit multiple alignment reports.** Each agent's first read is cache-cold; subsequent reads within the same agent are cache-hit. The chosen batching (5 DIB chunks/agent for Lane 2; 10 spec chunks/agent for Lane 3) amortizes the 5-spec-file read across all chunks in the batch. **Specific prefix-cache hit-rate numbers: data not in sources.**

**Compaction-resistance / outage recovery:** during a later Lane 3 wave, the user's session lost account access briefly. **All 51 Lane 3 batches wrote their JSON outputs cleanly anyway** because agent outputs were going to files rather than chat. This is the critical design pattern: *"agent outputs were going to FILES, not just chat text."*

**Phase A stall:** one of three parallel chunking agents stalled at 600 seconds on a single-large-write. Mitigation: split into smaller agents with a "move briskly" directive. This is the only failure-mode-during-run documented in the report.

---

## 9. What Walkthrough-Mode v2.x SHOULD Inherit

Contracts the v2.x skill must preserve from this run (each item is evidence-backed against the Phase A-E run):

1. **Asymmetric-knowledge holdout enforced by separate agents.** Lane 1a (scenario design) reads DIBs + concepts + DIB chunk lists; Lane 1b (walkthrough) reads DIBs + specs + assigned scenario; Phase C reads everything. The implementation agent stays blind to the full test set. This is the load-bearing contract — F01 depends on it.

2. **Lane 1a output must enumerate read-files in a `holdout_integrity` field.** The exact verbatim phrase *"No spec_\*.md files were read"* (or its parametric equivalent for the v2.x file-class names) must appear in the output. Phase C parses this field to issue its `PRESERVED | BREACHED | UNVERIFIED` verdict.

3. **Verdict vocabularies remain stable for tooling compatibility.** See §5 above. The exact strings — `REALIZED`, `JUSTIFIED`, `ORPHAN`, `yes-with-surgical`, etc. — should not be renamed. Downstream agents (and human readers of the meta-synthesis) depend on these strings.

4. **Chunk-record schema is stable across lanes:** `{chunk_id, source, section, title, summary, verbatim_anchor}`. The `verbatim_anchor` enables lane agents to locate the chunk in full source context without bloating the chunk-list file.

5. **Phase A stall-mitigation pattern.** When a chunking agent stalls on a single large write, split it into smaller agents with a "move briskly" directive. The v2.x skill should document it as a known failure mode + recovery.

6. **Outputs-to-files (not chat).** Every lane agent writes its output JSON to a deterministic path. Mid-run compaction or account outages must not destroy in-flight work. This is non-negotiable for runs that exceed a session lifetime.

7. **Phase C consumes all lane outputs + DIBs + specs as needed.** This requires the meta-synthesizer to be a 1M-context agent (or to read files selectively via Glob+Read, as the Phase C prompt instructs). Phase C is the single sink that produces both structured JSON and human-readable Markdown.

8. **Absence-as-corroboration is a named meta-synthesis dimension.** When a Lane 1b finding is single-lane, Lane 2/Lane 3 silence on the same topic is *strengthening*, not neutral. The Phase C prompt should preserve this analytical mode.

9. **`yes-with-surgical` as a first-class canonization verdict.** Distinct from `yes` (clean) and `no-blocking-found` (incomplete validation). This verdict survived from Phase C straight into the run's actual disposition (12-patch cleanup pass).

10. **`ARCHITECTURAL_REVIEW` is a routable recommendation distinct from `NEW_DR`.** Architectural-review items pause autonomous execution and route to user judgment; they do not auto-author a decision record. The reference run paused specifically for this routing.

---

## 10. What Walkthrough-Mode v2.x Can RELAX

Things that were Phase-A-E-run-specific and should NOT be baked into the skill:

1. **Specific batch sizes (5 DIB chunks/agent; 10 spec chunks/agent).** These were chosen empirically for the v3.4 run's specific chunk-count + spec-stack-size profile. The skill should expose batch size as a tuning parameter (or auto-tune from chunk count + estimated context budget per agent), not hardcode 5/10.

2. **Specific number of scenarios (13).** The Lane 1a prompt asked for "12-15 scenarios"; the agent produced 13. The skill should pass scenario-count as a parameter (e.g., `--scenarios=12-15`), not hardcode.

3. **Specific spec/DIB stack composition (3 DIBs + 5 specs).** The skill should accept arbitrary DIB/spec file globs — the lane prompts already use file-paths as placeholders.

4. **Specific concept-file enumeration (5-10 concepts).** Lane 1a's instruction *"Then read 5-10 concepts most cited by the DIBs (your judgment)"* was domain-specific. The skill should make the concept-source directory configurable, not hardcode `concepts/`.

5. **Specific wave sizes (5-7 per wave for Lane 1b).** This was a parallelism comfort range during the run. The skill should let the orchestrator set wave size based on observed dispatch stability, not pin a number.

6. **Specific chunking ratios.** The 41 DIB chunks + 509 spec chunks were what Phase A produced for this specific 3-DIB + 5-spec stack. The skill should document the chunk-record schema and stall-mitigation pattern, but not pin a chunk-count target.

7. **The Phase A 3-vs-2-vs-1 agent split.** The initial dispatch (one agent per DIB, one for Specs 00+01+04, one for Specs 02+03) and the 2a/2b/2c re-split after the stall were context-specific. The skill should document the *pattern* (one chunking agent per source-file when stalls occur), not the specific grouping.

8. **The decision-artifact enumeration as "optional, read selectively as needed" for Lane 3.** The skill should let the lane prompt configure whether intermediate-justification artifacts (decision records, ADRs, design notes) are in the read-set, not hardcode.

9. **Wall-clock target (~3 hours).** Run-specific. Depends on chunk count, agent class, batch size, and prefix-cache effectiveness — emergent, not contractual.

10. **The post-Phase-E patch-landing flow.** Walkthrough-mode v2.x emits the meta-synthesis as its output and stops. Whether the caller auto-lands patches is an orchestrator-level decision.

---

## Pending Decisions Surfaced (Not Locked in This Report)

> **Supersession note:** This section is retained as historical context. For the current v2.0 contract see `walkthrough_v2_0.md`; do not treat older "locked/not-locked" statements as the current contract.

Per the user's explicit guidance captured in the historical reference:

- **Q2 (chain shape):** the run's chain was Lane 1a → Lane 1b fan-out + Lane 2 + Lane 3 parallel + Phase C sink. The v1 CLI surface for this chain is **not locked** by this report. Implementation agents should treat the chain as described in §3 and §9, but the CLI shape (single command, sub-commands per phase, declarative config file, etc.) remains a user decision.
- **Q4 (composition with `--scope` flag):** the scoped-run primitive defines level-bound revalidation. How `--mode=walkthrough` composes with `--scope` is **not locked**. The reference run was effectively `--mode=walkthrough --scope=<all DIBs + all specs>` (full-stack); whether scoped walkthroughs are a meaningful subset is open.
- **CLI surface (locked per user):** `--mode=walkthrough` is a flag on the existing `/auto-evals` skill, NOT a sub-skill or subcommand.
- **Holdout strictness (locked per user):** separate-agents-with-asymmetric-knowledge, as documented in §6.

---

## Source Conflicts Surfaced

1. **SURGICAL_PATCH count.** Process report says "14 SURGICAL_PATCH". `meta-synthesis.json` says 13. Actual v3.4.3 land was 12 patches (because some findings folded into one patch). Treat `meta-synthesis.json` as authoritative for the synthesis output; treat 12 as the actual landed-patches count.

2. **Lane 3 `CONTRADICTORY` verdict.** Phase C meta-synthesis report tallies "0 CONTRADICTORY" for Lane 3, but the Lane 3 prompt enum (`JUSTIFIED | DR_JUSTIFIED | INDIRECT | ORPHAN | OVER_ENGINEERED`) does not include CONTRADICTORY. Either (a) extend Lane 3 enum or (b) keep CONTRADICTORY as a Phase-C-only meta-tag. The reference run used (b) implicitly.

3. **Lane file naming.** Phase C prompt expects `lane-2-*.json` and `lane-3-*.json` globs; actual files used `L2-batch-NNN-results.json` and `L3-batch-NNN-results.json`. Phase C still found them (the prompt says *"Use Glob + Read to enumerate the lane output files; don't assume an exact count"*) but the v2.x skill should pin a single naming convention.

---

*End of report.*
