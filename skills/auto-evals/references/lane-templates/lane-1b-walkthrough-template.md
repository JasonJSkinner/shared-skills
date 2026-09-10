# Lane 1b — Scenario Walkthrough — Prompt Template

**Usage:** Once Lane 1a emits `lane-1a-scenarios.json`, the orchestrator extracts each scenario's fields and substitutes them into this template — ONE dispatch per scenario. Lane 1b agents are batched in waves (default 5-7 per wave; tune to dispatch stability). Lane 1b runs only when `--chain=<artifact>` is provided.

**Placeholder ↔ Lane 1a JSON field mapping** (for F03 + Issue 3 clarity):

| Template placeholder | Source: `lane-1a-scenarios.json` field |
|---|---|
| `{NN}` | `scenarios[i].scenario_id` (e.g. `S01`) |
| `{TITLE}` | `scenarios[i].title` |
| `{NARRATIVE}` | `scenarios[i].narrative` |
| `{ACTORS}` | `scenarios[i].actors` (JSON array, rendered inline) |
| `{TESTED_INTENTS}` | `scenarios[i].tested_intents` (JSON array of `{chunk_id, claim}`) |
| `{WHAT_TO_CHECK}` | `scenarios[i].what_to_check_in_lane_1b` |

---

## PROMPT (substitute placeholders, then dispatch)

You are a Lane 1b walkthrough agent for an `/auto-evals walkthrough` run. You walk ONE scenario through the realization artifacts and adjudicate whether the specs handle it consistently with the tested DIB/PCB intent.

### Your inputs

- Governing DIB/PCB intent files (re-read for tested-intent grounding): `{DIB_PCB_PATHS}`
- Realization artifacts named by `--chain`: `{CHAIN_ARTIFACTS}`
- Spec stack: `{SPEC_PATHS}`
- Your assigned scenario:
  - **scenario_id:** `{NN}`
  - **title:** `{TITLE}`
  - **narrative:** `{NARRATIVE}`
  - **actors:** `{ACTORS}`
  - **tested_intents:** `{TESTED_INTENTS}`
  - **what to check:** `{WHAT_TO_CHECK}`

You do NOT inherit Lane 1a's hidden test-design state — you receive only the assigned scenario above.

### Your task

Walk the scenario step-by-step through the realization artifacts + spec stack. For each step, cite the governing spec section(s) and adjudicate. Then issue an overall verdict + per-tested-intent status + findings.

### Output — write to `{OUTPUT_PATH}` (default `phase-b/walkthrough-{NN}.json`)

```json
{
  "agent_id": "{AGENT_ID}",
  "scenario_id": "{NN}",
  "verdict": "ALIGNED | PARTIAL | CONTRADICTED | SILENT | AMBIGUOUS",
  "walkthrough_steps": [
    {
      "step_number": 1,
      "what_happens": "<step description>",
      "governing_spec_sections": [{"spec": "<spec>", "section": "<ref>", "what_it_says": "<quote/paraphrase>"}],
      "verdict_for_step": "ALIGNED | PARTIAL | CONTRADICTED | SILENT | AMBIGUOUS",
      "rationale": "<why>"
    }
  ],
  "overall_verdict_rationale": "<paragraph>",
  "tested_intent_status": [
    {"chunk_id": "<id>", "status": "REALIZED | PARTIAL | MISSING | CONTRADICTED", "evidence": "<evidence>"}
  ],
  "findings": [
    {"severity": "blocking | concerning | minor", "title": "<title>", "description": "<para>", "affected_specs": ["<section>"], "suggested_action": "surgical patch ... | needs-judgment ... | architectural-review ..."}
  ]
}
```

### Verdict vocabulary (exact strings — DO NOT rename)

- `ALIGNED` — specs handle the scenario consistently with all tested intents.
- `PARTIAL` — specs handle most aspects but ≥1 tested intent partially missed.
- `CONTRADICTED` — a spec section actively contradicts a DIB/PCB intent.
- `SILENT` — a tested intent has no spec realization.
- `AMBIGUOUS` — specs unclear; a reasonable agent could go either way.

### Output discipline

Write the JSON to the file path — NOT to chat.
