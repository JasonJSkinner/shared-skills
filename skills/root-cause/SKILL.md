---
name: root-cause
version: "1.2"
description: Systemic root-cause analysis — classify discrepancies as reusable issue families instead of patching surface symptoms. Use when the user invokes /root-cause, or asks to "find the root cause," "look past the surface," "avoid ad-hoc fixes," or "find the broader bug family." For natural-language triggers, confirm invocation before proceeding.
---

# Systemic Root-Cause Analysis

Analyze problems by looking past surface discrepancies to find underlying reusable issue families, contract ambiguities, helper overreach, and blast radius.

## When to use

- `/root-cause` — always invoke immediately
- Natural language ("find the root cause", "what's really going on here", "avoid ad-hoc fixes", "find the broader bug family") — **confirm with the user first**: "This looks like it calls for a systemic root-cause analysis. Want me to run the full /root-cause workflow, or just a quick investigation?"

## Core stance

- Prefer reusable bug families over per-entry patching.
- Treat a failing test, swarm report, or broken fixture as a **clue**, not as proof of the root cause.
- Do not propose changes until the root cause is verified in code.

## Classification taxonomy

Every discrepancy goes into exactly one bucket:

| Bucket | Meaning |
|--------|---------|
| `contract_ambiguity` | Export/API contract doesn't specify behavior clearly enough |
| `native_vs_derived_rail_split` | Issue lives in a shared data rail, not the feature consuming it |
| `helper_overreach` | Helper does more than its contract promises |
| `helper_under_modeling` | Helper omits a case it should handle |
| `taxonomy_or_catalog_drift` | Code, catalog, and validator disagree on definitions |
| `evidence_closure_drift` | Evidence rail produces incomplete or stale data |
| `missing_rule_family` | Entire category of rules not yet implemented |
| `policy_or_semantic_choice` | Not a bug — a design decision that needs explicit ratification |
| `swarm_interpretation_drift` | External validator/swarm misreads the contract |

## Workflow

### Step 1 — Define the symptom set

List the concrete discrepant entries, failing tests, fixtures, or artifacts. For each, note:
- Current status: `detected`, `not_detected`, `citation_incomplete`, `PARTIAL`, `DISAGREE`
- Which module/feature surfaces the symptom

### Step 2 — Verify code paths (MANDATORY)

Before classifying anything, trace the actual code:

**Use LSP first:**
- `goToDefinition` on the symbol producing the symptom
- `findReferences` to see all consumers of the suspected root-cause symbol
- `hover` for type information when the data flow is unclear

**Grep/Glob fallback** for config values, string constants, comment-level contracts, or when LSP doesn't cover the pattern.

**Use project context** from CLAUDE.md and ORIENTATION.md to inform which invariants and conventions apply.

Do not classify a discrepancy without having read the relevant code path.

### Step 3 — Build a discrepancy matrix

For each candidate issue, identify:
- Current feature / detector path
- Current evidence rail
- Current export contract relied on
- Likely reusable helper family
- Whether the symptom is isolated or shared across features/fixtures

### Step 4 — Classify into taxonomy

Assign exactly one bucket from the taxonomy above. If uncertain between two, note both and explain the ambiguity.

### Step 5 — Find the lowest reusable layer

Ask and verify:
- Is this really one feature-level issue, or is it a shared helper / data rail / export object?
- If fixed at the lower layer, what other features or fixtures benefit?
- If "fixed" only at the feature level, what broader bug remains hidden?

### Step 6 — Blast-radius analysis

Find all consumers of the affected helper / rail / export object.

**For complex cases** (multiple modules, deep dependency chains): consider spawning parallel Explore subagents — one per suspected consumer module — to check exposure without bloating main context. When those subagents will read large source trees or multi-file context bundles, default to a capable long-context model. Use custom subagent definitions or team config files when applicable.

**For simpler cases** (single module, shallow deps): `findReferences` from the main context is sufficient.

Distinguish:
- Direct consumers (will break or change behavior)
- Secondary exposure (downstream of a consumer, may see changed data)
- Explicitly note what should **not** be changed yet

### Step 7 — Decide the action bucket

Assign exactly one:

| Action | When |
|--------|------|
| `fix_in_code_now` | Clear bug with bounded blast radius |
| `clarify_catalog_or_validator` | Taxonomy/catalog drift needs reconciliation |
| `defer_as_policy_decision` | Requires human judgment on semantics |
| `leave_as_missing_rule_family` | New rule family needed — not a fix to existing code |
| `leave_as_verifier_layer_judgment` | External validator/swarm issue, not engine issue |

## What to avoid

- Do not accept the first apparent root cause without code-path verification (Step 2).
- Do not assume a failing fixture proves a foundational bug.
- Do not broaden scope just because nearby features mention related concepts.
- Do not quietly rewrite catalog semantics to hide a real engine mismatch.
- Do not treat "detected in findings" as "correctly detected" if external review disputes it.
- Do not propose tightening/widening detection unless the root cause truly requires it.

## Output contract

Produce these sections in your response:

```
## Executive Summary
<2-3 sentences: what's actually wrong and at what layer>

## Confirmed Reusable Issue Families
<For each: bucket classification, affected symbol/rail, evidence from code>

## Likely Validator/Catalog Misreads
<Issues that look like bugs but are actually external misinterpretation>

## Likely Policy/Semantic Decisions
<Issues requiring human judgment, not code fixes>

## Blast Radius
<Direct consumers, secondary exposure, what NOT to touch>

## Recommended Next Sequence
<Ordered list of fixes/clarifications, with rationale for ordering>

## What Not To Touch Yet
<Explicitly protected areas and why>
```

When useful, explicitly state:
- which issues are **real bugs**
- which are **missing-rule families**
- which are **communication/contract problems**
- which are **not bugs under the current canonical definition**

## Memory workflow

When findings are worth preserving across sessions:

**Contextual findings** (tied to specific repo/version/artifact):
- Save as `type: project` memory
- Name: `root-cause-<slug>.md`
- Include: repo/branch context, confirmed issue families, blast radius, recommended sequence

**Portable principles** (reusable debugging lessons):
- Save as `type: feedback` memory
- Name: `root-cause-principle-<slug>.md`
- Include: the principle, when it applies, the common false explanation it prevents

Group all root-cause memories under a `## Root-Cause Findings` header in MEMORY.md.

Only save memories when:
- The user explicitly asks to remember findings
- A principle is clearly reusable and non-obvious (would save significant time if recalled later)

Do not save memories for routine findings that are obvious from the code.
