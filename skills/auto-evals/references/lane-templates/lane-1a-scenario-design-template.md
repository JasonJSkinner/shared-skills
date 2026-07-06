# Lane 1a — Scenario Design (Holdout) — Prompt Template

**Usage:** The walkthrough orchestrator fills the `{...}` placeholders and dispatches ONE Opus subagent (`run_in_background=true`). Lane 1a MUST finish before Lane 1b can start (Lane 1b prompts are templated from Lane 1a's scenario output).

**Parameterization note (F01+F02 holdout fix):** The forbidden read-set is NOT a hardcoded literal `synthesis/spec_*.md`. The orchestrator resolves the **spec set** from `{TARGET}` — the files in the target stack that constitute the *realization* being validated (as opposed to the DIB/PCB *intent*) — and substitutes the resolved paths into `{FORBIDDEN_SPEC_PATHS}`. For a target whose specs are not named `spec_*.md`, the resolved set still pins them correctly. If the spec set cannot be unambiguously resolved, the orchestrator MUST surface that before dispatching Lane 1a (do not silently fall back to the literal glob).

---

## PROMPT (substitute placeholders, then dispatch)

You are the Lane 1a scenario-design agent for an `/auto-evals walkthrough` run. You design intent-derived validation scenarios under a strict holdout discipline.

### Your inputs (read ONLY these)

- Governing DIB/PCB intent files: `{DIB_PCB_PATHS}`
- Concept files (orchestrator-selected, most-cited by the DIBs): `{CONCEPT_PATHS}`
- Phase A DIB chunk list: `{DIB_CHUNK_LIST_PATH}`
- This prompt.

### FORBIDDEN reads — holdout discipline (load-bearing)

Do NOT read any file in the resolved spec set:

```
{FORBIDDEN_SPEC_PATHS}
```

Also forbidden: `{SPEC_CHUNK_LIST_PATH}` (the Phase A spec chunk list — `unified-spec-chunks.json` or its target-specific equivalent). The specs are the *realization being validated*; if you read them, the holdout is broken and the F01-class error-detection capability of this run is destroyed.

If `{FORBIDDEN_SPEC_PATHS}` is empty or you are unsure whether a file is a spec, STOP and ask the orchestrator — do not guess.

### Your task

Design `{SCENARIO_COUNT}` validation scenarios (range, e.g. `12-15`) that test whether the governing intent is realized. Each scenario probes a tested intent — derived from the DIB/PCB chunks — WITHOUT mirroring spec structure (you have not read the specs, by design).

Classify each scenario on **two orthogonal axes**: `category` is the stress-profile (`common | edge | adversarial`); `scenario_classification` is the consequence-class carried from v1.3 doctrine (`strict contract gate` — should pass for the contract to hold; `evidence probe` — high-signal stressor, not a binary gate; `corpus scan` — integrity scan over real data; `ergonomics warning` — friction probe). Both are required fields.

### Output — write to `{OUTPUT_PATH}` (default `phase-b/lane-1a-scenarios.json`)

```json
{
  "agent_id": "{AGENT_ID}",
  "holdout_integrity": "Files read: <enumerate EVERY file path you Read, comma-separated>. No files from the resolved spec set were read. Resolved spec set checked against: {FORBIDDEN_SPEC_PATHS}",
  "scenarios": [
    {
      "scenario_id": "S01",
      "category": "common | edge | adversarial",
      "scenario_classification": "strict contract gate | evidence probe | corpus scan | ergonomics warning",
      "title": "<short title>",
      "narrative": "<scenario narrative>",
      "actors": ["<actor>"],
      "tested_intents": [{"chunk_id": "<DIB/PCB chunk id>", "claim": "<intent being tested>"}],
      "expected_specs_to_address": ["<spec section the realization SHOULD cover>"],
      "what_to_check_in_lane_1b": "<what Lane 1b should verify when walking this scenario>"
    }
  ],
  "coverage_notes": "<coverage gaps or notable design choices>"
}
```

### Holdout-integrity attestation contract

The `holdout_integrity` field MUST: (a) enumerate every file you Read; (b) state explicitly that no file from the resolved spec set was read; (c) echo `{FORBIDDEN_SPEC_PATHS}` so Phase C can audit by **set-intersection** of your `files_read` against the resolved spec set. A non-empty intersection = holdout BREACHED.

### Output discipline

Write the JSON to the file path — NOT to chat. Compaction-resistance requires file emission.
