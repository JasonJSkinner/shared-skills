# Root Cause

`root-cause` is a systemic debugging workflow for problems that should not be
patched one symptom at a time. It treats a failing test, verifier report, broken
fixture, or discrepant artifact as a clue pointing to a reusable issue family:
an ambiguous contract, an overreaching helper, an under-modeled case, drift
between catalog and validator, or a policy choice that needs human ratification.

The skill's central rule is simple: **do not propose a fix until the relevant
code path or contract path has been verified.** A plausible explanation is not a
root cause. A root cause is the lowest reusable layer that explains the symptom
set and whose blast radius has been inspected.

This skill is provider-neutral. The taxonomy, workflow, and output contract
below do not depend on a particular agent platform. Provider-specific invocation
mechanics belong in provider notes or local harness configuration.

## When To Use

Use `root-cause` when the user asks to:

- find the root cause rather than the surface failure;
- avoid an ad-hoc or fixture-specific patch;
- identify the broader bug family behind several symptoms;
- decide whether a discrepancy is a bug, missing rule family, contract problem,
  external verifier misread, or policy decision.

It is especially useful after `auto-evals` finds failure families, because the
repair side needs to know *where* to fix and *what not to touch* before changing
implementation behavior.

## When Not To Use

Do not run the full workflow for:

- a trivial one-line defect with an obvious local cause;
- ordinary implementation work where no discrepancy or failure family is being
  investigated;
- a pure product or policy question with no code path to inspect;
- broad refactoring where the user has not asked for diagnosis.

For natural-language triggers, confirm whether the user wants the full
root-cause workflow or a quick investigation.

## Classification Taxonomy

Every discrepancy should land in one primary bucket:

| Bucket | Meaning |
|---|---|
| `contract_ambiguity` | Export or API contract does not specify behavior clearly enough. |
| `native_vs_derived_rail_split` | The issue lives in a shared data rail rather than the feature consuming it. |
| `helper_overreach` | A helper does more than its contract promises. |
| `helper_under_modeling` | A helper omits a case it should handle. |
| `taxonomy_or_catalog_drift` | Code, catalog, and validator disagree on definitions. |
| `evidence_closure_drift` | Evidence rail produces incomplete or stale data. |
| `missing_rule_family` | A whole category of rules is not implemented yet. |
| `policy_or_semantic_choice` | Not a bug; a design decision needs explicit ratification. |
| `swarm_interpretation_drift` | External validator or reviewer misreads the contract. |

If two buckets seem plausible, record the ambiguity and the evidence needed to
resolve it. Do not hide the uncertainty by choosing the more convenient repair.

## Workflow

1. **Define the symptom set.** List concrete discrepant entries, failing tests,
   fixtures, or artifacts. For each, note the observed status and which module,
   feature, or contract surface exposed it.
2. **Verify code paths or contract paths.** Trace the symbols, helpers,
   catalogs, validators, schemas, and evidence rails that could produce the
   symptom. Use language-server navigation when available; use targeted text
   search for constants, config, and prose contracts.
3. **Build a discrepancy matrix.** For each candidate issue, name the feature or
   detector path, evidence rail, export contract, likely reusable helper family,
   and whether the symptom is isolated or shared.
4. **Classify the issue family.** Assign one taxonomy bucket, with explicit
   uncertainty if the evidence is not decisive.
5. **Find the lowest reusable layer.** Ask whether a feature-level fix would
   leave a broader helper, data-rail, contract, or validator bug hidden.
6. **Analyze blast radius.** Identify direct consumers, secondary exposure, and
   areas that should not change yet.
7. **Choose the action bucket.** Decide whether to fix code now, clarify a
   catalog or validator, defer a policy decision, leave a missing rule family as
   future work, or treat the discrepancy as verifier-layer judgment.

## Action Buckets

| Action | Use when |
|---|---|
| `fix_in_code_now` | A clear bug has a bounded blast radius. |
| `clarify_catalog_or_validator` | Definitions or validators need reconciliation. |
| `defer_as_policy_decision` | Human judgment is needed on semantics. |
| `leave_as_missing_rule_family` | The issue is a new rule family, not a fix to existing behavior. |
| `leave_as_verifier_layer_judgment` | The external verifier or reviewer is wrong under the current contract. |

## Output Contract

A root-cause report should contain:

```markdown
## Executive Summary
<2-3 sentences: what is actually wrong and at what layer>

## Confirmed Reusable Issue Families
<For each: bucket classification, affected symbol or rail, evidence from code>

## Likely Validator/Catalog Misreads
<Issues that look like bugs but are external misinterpretation>

## Likely Policy/Semantic Decisions
<Issues requiring human judgment, not code fixes>

## Blast Radius
<Direct consumers, secondary exposure, what not to touch>

## Recommended Next Sequence
<Ordered fixes or clarifications, with rationale for ordering>

## What Not To Touch Yet
<Protected areas and why>
```

When useful, explicitly distinguish real bugs, missing-rule families,
communication or contract problems, and non-bugs under the current canonical
definition.

## Partial Adoption

The irreducible core is the verified-code-path discipline plus the taxonomy. You
can omit memory capture, subagent fan-out, or formal report storage and still get
value if the analysis names the reusable issue family and blast radius.

What breaks if adopted poorly:

- Skipping code-path verification turns the workflow into a plausible guess.
- Fixing at the first visible feature can leave the shared helper or rail broken.
- Treating policy decisions as bugs silently changes product semantics.
- Treating external verifier disagreement as proof can make the implementation
  chase the wrong contract.

## Provider Notes

Invocation is provider-specific: a slash command, explicit skill selection, or a
manual instruction can all enter the same workflow. Platforms with subagents can
parallelize blast-radius exploration by suspected consumer module; platforms
without subagents can run the same checks serially. Use a capable long-context
model or equivalent context strategy when a case requires reading large contract
and implementation surfaces together.
