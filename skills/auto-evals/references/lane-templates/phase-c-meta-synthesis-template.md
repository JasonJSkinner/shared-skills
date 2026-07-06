# Phase C — Meta-Synthesis — Prompt Template

**Usage:** The orchestrator dispatches ONE Opus 1M agent after ALL Phase B lanes drain. Phase C is the single sink — it reads all lane outputs + DIBs/PCBs + specs as needed and emits both structured JSON and human-readable Markdown.

---

## PROMPT (substitute placeholders, then dispatch)

You are the Phase C meta-synthesis agent for an `/auto-evals walkthrough` run. You consume every lane output, audit the holdout, apply absence-as-corroboration, and emit a canonization verdict.

### Your inputs

- All Lane 1a / 1b / 2 / 3 output files under: `{PHASE_B_OUTPUT_DIR}` — use **Glob + Read** to enumerate; do NOT assume an exact count.
- Phase A chunk lists: `{DIB_CHUNK_LIST_PATH}`, `{SPEC_CHUNK_LIST_PATH}`
- DIB/PCB source files: `{DIB_PCB_PATHS}`
- Spec stack (consult selectively): `{SPEC_PATHS}`
- Resolved spec set for holdout audit: `{FORBIDDEN_SPEC_PATHS}`

### Your tasks

1. **Holdout audit.** Read Lane 1a's `holdout_integrity` field. Compute the **set-intersection** of Lane 1a's enumerated `files_read` against `{FORBIDDEN_SPEC_PATHS}` (the resolved spec set). Empty intersection → `PRESERVED`. Non-empty → `BREACHED`. Field missing or unparseable → `UNVERIFIED`.

2. **Cluster findings** across all lanes. Assign each a confidence label (see vocabulary). Identify `CONTRADICTORY` findings by cross-correlating Lane 1b / Lane 2 / Lane 3 outputs — `CONTRADICTORY` is a Phase-C-only meta-tag, not present in any lane's base enum.

3. **Apply absence-as-corroboration (LOAD-BEARING).** When a Lane 1b finding is single-lane (only one walkthrough flagged it), search Lane 3 for chunks addressing the topic. **Zero matching Lane 3 chunks STRENGTHENS the finding** — upgrade its confidence from `single-lane` to `single-lane-plus-structural-confirmation`. The topic being structurally absent from the spec stack is itself evidence that the spec doesn't address the issue. Do NOT treat Lane 2/Lane 3 silence as neutral.

4. **Surface systemic patterns** — cross-lane patterns that cluster findings (these are not findings themselves; they inform recommendation strategy).

5. **Emit the canonization verdict.**

### Output — write TWO files

`{OUTPUT_JSON_PATH}` (default `phase-c/meta-synthesis.json`):

```json
{
  "agent_id": "{AGENT_ID}",
  "lane_outputs_consumed": {"lane_1a": "<path>", "lane_1b_count": 0, "lane_2_count": 0, "lane_3_count": 0},
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
  "systemic_patterns": [{"pattern_id": "P1", "description": "<desc>", "drives_findings": ["F01"]}],
  "canonization_summary": {
    "total_findings": 0,
    "blocking": 0,
    "concerning": 0,
    "minor": 0,
    "recommendation_distribution": {"GO": 0, "SURGICAL_PATCH": 0, "VERSION_BUMP": 0, "NEW_DR": 0, "DEFER": 0, "ARCHITECTURAL_REVIEW": 0},
    "ready_for_canonization": "yes | yes-with-surgical | no-blocking-found",
    "summary": "<paragraph>"
  }
}
```

`{OUTPUT_MD_PATH}` (default `phase-c/meta-synthesis.md`): human-readable companion covering the same content + narrative. **Annotate the actual-landed patch count separately from the synthesis count** (see SURGICAL_PATCH source-of-truth below).

### Confidence vocabulary (exact strings — DO NOT rename)

- `triple-confirmed` — flagged by 3 channels.
- `double-confirmed` — flagged by 2 channels.
- `single-lane` — flagged by 1 lane, no structural corroboration.
- `single-lane-plus-structural-confirmation` — single-lane finding upgraded because Lane 2/Lane 3 silence corroborates it (absence-as-corroboration). This is a FORMAL confidence value, not an annotation.

### Recommendation vocabulary (exact strings)

`GO | SURGICAL_PATCH | VERSION_BUMP | NEW_DR | DEFER | ARCHITECTURAL_REVIEW`. `ARCHITECTURAL_REVIEW` pauses autonomous execution and routes to human judgment — it does NOT auto-author a DR (distinct from `NEW_DR`).

### Canonization verdict (exact strings)

`yes` (clean) | `yes-with-surgical` (ready with bounded surgical cleanup) | `no-blocking-found` (incomplete validation).

### SURGICAL_PATCH count source-of-truth

`meta-synthesis.json`'s `canonization_summary.recommendation_distribution.SURGICAL_PATCH` is authoritative for the synthesis output. The companion `.md` annotates the actual-landed patch count separately (some findings may fold into one patch) with an explicit source-of-truth note.

### Output discipline

Write both files to their paths — NOT to chat. Phase C is the compaction-resistant sink for the whole run.
