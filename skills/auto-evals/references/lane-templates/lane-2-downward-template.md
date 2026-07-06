# Lane 2 — Downward (DIB → Spec) — Prompt Template

**Usage:** The orchestrator batches DIB chunks (default 5 chunks/agent — tunable, not hardcoded) and dispatches one Opus agent per batch. Lane 2 runs in parallel with Lane 1b + Lane 3 (it consumes Phase A chunk lists directly; it does NOT depend on Lane 1a output).

---

## PROMPT (substitute placeholders, then dispatch)

You are a Lane 2 downward-alignment agent for an `/auto-evals walkthrough` run. You check, for each assigned DIB/PCB intent chunk, whether the spec stack realizes it.

### Your inputs

- Your batch file (contains `{BATCH_CHUNK_COUNT}` DIB/PCB chunk records): `{BATCH_FILE_PATH}`
- DIB/PCB source files: `{DIB_PCB_PATHS}`
- Spec stack: `{SPEC_PATHS}`

Each chunk record carries `{chunk_id, source, section, title, summary, verbatim_anchor}`. Use `verbatim_anchor` to locate the chunk's intent in its full DIB/PCB context.

### Your task

For each of your `{BATCH_CHUNK_COUNT}` chunks: find where (if anywhere) the spec stack realizes the intent. Move briskly — allocate effort per chunk.

### Output — write to `{OUTPUT_PATH}` (default `phase-b/L2-batch-{BATCH_ID}-results.json`)

```json
{
  "agent_id": "{AGENT_ID}",
  "batch_id": "{BATCH_ID}",
  "reports": [
    {
      "chunk_id": "<DIB/PCB chunk id>",
      "chunk_title": "<title>",
      "alignment_status": "REALIZED | PARTIAL | MISSING | CONTRADICTED | OUT_OF_SCOPE",
      "realization_sites": [
        {"spec": "<spec>", "section": "<ref>", "realization_summary": "<summary>", "verbatim_quote": "<quote>", "completeness": "fully | partially | tangentially"}
      ],
      "missing_aspects": [{"aspect": "<aspect>", "severity": "blocking | concerning | minor"}],
      "contradictions": [{"spec": "<spec>", "section": "<ref>", "what_contradicts": "<what>", "severity": "blocking | concerning | minor"}],
      "overall_verdict": "<one of the alignment_status enums>",
      "suggested_action": "<action>"
    }
  ]
}
```

### Verdict vocabulary (exact strings — DO NOT rename; downward-direction — distinct from Lane 3)

- `REALIZED` — specs fully address the DIB/PCB intent.
- `PARTIAL` — specs address most but miss aspects.
- `MISSING` — no spec realization found.
- `CONTRADICTED` — some spec actively conflicts.
- `OUT_OF_SCOPE` — the intent is meta-level and doesn't need spec encoding (document WHY it's meta-level).

Per-site completeness: `fully | partially | tangentially`.

### Output discipline

Write the JSON to the file path — NOT to chat.
