# Lane Prompt Templates — `/auto-evals walkthrough` v2.0

Five parameterized prompt templates the walkthrough orchestrator fills with `{...}` placeholder values and dispatches to lane subagents.

| Template | Lane | Dispatch shape |
|---|---|---|
| `lane-1a-scenario-design-template.md` | Lane 1a — scenario design (holdout) | ONE Opus agent; must finish before Lane 1b |
| `lane-1b-walkthrough-template.md` | Lane 1b — per-scenario walkthrough | ONE Opus agent per scenario; batched waves of 5-7; only if `--chain` |
| `lane-2-downward-template.md` | Lane 2 — downward DIB→Spec | ONE Opus agent per batch; default 5 chunks/agent |
| `lane-3-upward-template.md` | Lane 3 — upward Spec→DIB | ONE Opus agent per batch; default 10 chunks/agent |
| `phase-c-meta-synthesis-template.md` | Phase C — meta-synthesis | ONE Opus 1M agent; sink after all Phase B drains |

## Parameterization discipline

The `{...}` placeholders ARE the "tuning parameters not to bake" mechanism (per Phase A-E reference §10): batch sizes, scenario counts, file paths, the resolved spec set, and concept-source paths are all orchestrator-supplied at dispatch time, NOT hardcoded into the templates. A template with filled placeholders is a complete, reproducible prompt — two orchestrators running the same invocation with the same placeholder values produce the same prompts.

## Holdout parameterization (F01+F02)

The Lane 1a template's `{FORBIDDEN_SPEC_PATHS}` placeholder is resolved by the orchestrator from `{TARGET}` — it is NOT a hardcoded `synthesis/spec_*.md` literal. This preserves the holdout for any target whose specs are not named `spec_*.md`. Phase C audits the holdout by set-intersection of Lane 1a's `files_read` against the same resolved spec set. See `lane-1a-scenario-design-template.md` §"FORBIDDEN reads" and `phase-c-meta-synthesis-template.md` task 1.

## Cross-references

- `../walkthrough_v2_0.md` — the v2.0 walkthrough-mode contract (lane architecture §2, holdout §3, absence-as-corroboration §4, verdict vocabularies §5, output schemas §9)
- `../walkthrough_mode_phase_a_e_reference.md` — the 2026-05-06 Phase A-E run reference (provenance; §2 lane architecture, §5 verdict vocabulary table, §6 holdout discipline)
