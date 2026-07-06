---
name: completeness-map
description: "Derive `derived/completeness-map.md` Zone 3 sidecar from a DIB's `What Complete Looks Like` section + governing law (DIB + companion specifications + decision artifacts + design artifacts). Produces an exhaustive implication map (NOT a todo list) enumerating closure dimensions in the canonical 7-section schema. Use when a DIB has a completion boundary and downstream consumers need explicit completion-accounting beyond the qualitative prose, especially when consumers are literalist execution agents or closure dimensions are heterogeneous enough that prose alone cannot carry them. Also the enforcement point for the completion-claim gate: blocks any governing-DIB completion claim that lacks a DIB-level closure map, and carries the DIB Residual-Obligations reporting contract."
version: 1.2
---

# /completeness-map

Generates the `derived/completeness-map.md` Zone 3 derived sidecar. The canonical sidecar pattern was previously defined without a generation mechanism; this skill provides it.

## Architecture (v1.1)

Thin umbrella with lazy-loaded references:

| File | Loads when |
|---|---|
| `references/schema.md` | Authoring — the canonical 7-section schema + how to derive each section |
| `references/eligibility.md` | Step 0 — the 15-H/I eligibility gate decision tree |
| `references/anti-patterns.md` | Step 1 — *implication map, not todo list* (load-bearing authoring rule) + drift recovery |
| `references/enums.md` | Step 4 — status + completion-effect enums + load-bearing-deferral shape |
| `references/nested-handling.md` | Step 5 — per-`.dib/` rules; parent-vs-child completion scope |

Load relevant references on demand — don't bulk-read. These 5 references are the **canonical substrate** — the 7-section schema, the v2.0 enums, the 15-H/I eligibility gate, the load-bearing anti-pattern, nested-handling. v1.0 left all 5 **byte-identical to v0.2** (see *v1.0 release record*); the promotion refined the generation mechanism around them, not the substrate.

## Sub-commands

| R/W | Cmd | What it does |
|---|---|---|
| W | `new <dib>` | Derive fresh map; eligibility gate must pass |
| R | `check <dib>` | Re-derive in memory, diff against the existing map, report drift — including **string-level** drift (dates / paths / hashes / filenames / version strings), not only section-presence |
| W | `refresh <dib>` | Re-derive + overwrite existing map (drift acknowledged, intentional) |
| R | `validate <dib>` | Inspect existing map for the todo-list anti-pattern + missing sections + enum compliance **+ the §10/§11 completion-claim gate** |
| W | `residual-obligations <dib>` | Emit the **course-corrections-§10** DIB Residual-Obligations wave-close block for `<dib>`; refuses a `claimed: yes` block when no DIB-level closure map exists (course-corrections-§11 hard gate) |

All write sub-commands default `--dry-run` (print proposed). Add `--apply` to commit. The 4 derivation verbs (`new` / `check` / `refresh` / `validate`) are the design-validated map-generation surface. `migrate` / `compare` / `merge` stay deferred until there is a demonstrated need. **v1.1 adds one enforcement verb — `residual-obligations`** — the reporting half of the completion-claim gate (see *Completion-claim gate*); it is not a map-generation verb.

## When to invoke

- **Manually:** User invokes `/completeness-map <subcommand> <dib>` directly.
- **Inside an orchestrator flow (the de-facto invocation trigger):** orchestrator-prompt templates name `/completeness-map new <governing-DIB> --apply` as Step 1 of every work-unit procedure. The derived map becomes the explicit closure-dimension enumeration for `/auto-evals` + audit lanes. This Step-1 convention IS v1.0's invocation trigger — see *Orchestration conventions*.
- **At downstream consumer time:** PCB generators, `/auto-evals` runs, audit lanes invoke `check <dib>` (read-only drift check) before consuming the map.

## Completion-claim Gate

This skill is the enforcement point for two completion-claim guardrails. They are
**GATES, not advisories** — when a consumer
asks this skill to certify or report governing-DIB completion, apply them and BLOCK on failure.
Never silently upgrade a child/work-unit-completion claim into a DIB-completion claim.

> **Terminology note.** The completion-claim gate is the requirement: no governing-DIB
> completion claim without a DIB-level closure map plus a reconciled Residual-Obligations block.
> The template's optional closure-accounting record is only an aid for recording that evidence.

### Anti-shortcut Completion Rule

> **Do NOT infer governing-DIB completion from child / work-unit completion unless a
> DIB-LEVEL closure map exists.**

"All scoped child/work-unit maps are done" ≠ "the governing DIB is complete." They are different
claims: a governing DIB carries its own subject + parent-owned obligations + sibling/publisher
scope that no child map covers. A **DIB-level closure map** = this skill's §1–§7 map derived for
the **governing DIB itself**, not the union of its children's maps.

**Enforcement:** if asked to assert "DIB complete" (or emit `Full governing-DIB completion
claimed: yes`) and no DIB-level closure map exists for that DIB, STOP and report:
*"Cannot certify DIB completion — no DIB-level closure map for `<dib>`; only child/work-unit maps exist.
Run `/completeness-map new <governing-dib>` first."* The honest fallback claim is the narrower
*"all scoped child/work-unit work complete."*

**Written ≠ wired.** For implementation-bearing dimensions, distinguish evidence states:
*documented* (text exists) → *specified* (behavior defined) → *implemented* (code/config
exists) → *wired* (real entrypoints/templates/hooks/install paths invoke it) → *installed*
(present where consumers actually read it) → *exercised* (a test/dogfood path proves it runs)
→ *derivable* (the completion claim legally follows). Documented or specified behavior that is
not wired into an invoked runtime, install, template, hook, or consumer path does NOT count as
complete for an implementation-bearing dimension.

### Residual-Obligations Reporting Contract

Every completion report that touches a governing DIB MUST carry a **DIB Residual
Obligations** block. The `residual-obligations <dib>` sub-command emits it. A report may state
`Full governing-DIB completion claimed: yes` ONLY when a DIB-level closure map exists AND every
governing obligation is accounted for in one of the four buckets:

```markdown
## DIB Residual Obligations — <DIB name>

Full governing-DIB completion claimed: yes | no

Satisfied in this wave:
- ...

Intentionally out of scope:
- ...

Deferred / future:
- ... (cite deferral IDs)

Known parent-owned or sibling-owned obligations:
- ...
```

**Acceptance gate:** no report may say "DIB complete" unless (1) a DIB-level closure map exists
and (2) the Residual-Obligations block declares `Full governing-DIB completion claimed: yes` with
every bucket reconciled. Otherwise the report claims at most "all scoped child/work-unit work complete."

The optional closure-accounting record in `templates/` (the *Orchestration conventions*
append-only close record) is a convenient place to capture the satisfied/deferred buckets at
work-unit close — but it is an aid, not a substitute: the gate above is satisfied by the
Residual-Obligations block + a DIB-level closure map, not by the template section per se.

## Procedure (for `new` / `refresh`)

### Step 0 — Eligibility gate

Load `references/eligibility.md`. Run the decision tree. If the DIB doesn't qualify, stop and report: *"DIB does not define a completion boundary; sidecar is not appropriate"* OR *"Prose section suffices for this DIB's consumer profile."* Do NOT pre-emptively scaffold.

**Sprint-mode override:** If invoked from an orchestrator-prompt-template flow that explicitly names this skill, the eligibility check is satisfied by the explicit invocation — skip the gate.

### Step 1 — Read the anti-pattern callout FIRST

Load `references/anti-patterns.md`. Internalize *"implication map, not todo list"* before generating any content. **This is the single most important authoring rule** — collapsing the map into a checklist recreates the failure mode one layer down.

If you find yourself tempted to write items as `[ ] do X`, you've drifted — re-read the anti-patterns reference.

### Step 2 — Gather governing law

Read the DIB(s) + companion specifications + decision artifacts + design artifacts the orchestrator specified. Specifically:
- The DIB's `What Complete Looks Like` section (if present)
- Cited companion specifications
- Cited decision artifacts (with Accepted or Incorporated dispositions)
- Cited design artifacts (`dib-write-gate-doctrine-v4.md` / `forests-yaml-schema-v4.md` / `dib-skill-v2.1-requirements.md` / etc.)
- The `edit-lease` concept and bidirectional `.dib/` lease invariant (apply at boundary edges)

Apply authority hierarchy: DIB > companion specifications > decision artifacts > design artifacts. **Surface contradictions explicitly; do NOT silently resolve them in the map.**

**Subagent context window:** When the governing-law set is large, use a model and context window large enough to read the full design corpus without truncation.

### Step 3 — Derive the 7 sections

Load `references/schema.md`. Walk each section in order — §1 through §7. For each, enumerate **closure dimensions and implications**, not checkable atoms.

Per-section derivation guidance is in `references/schema.md`. Critical reminders:
- §1 (consumers): every consumer + what *"complete"* means from their angle (enumerate across buckets: human · agent · artifact · runtime/install · downstream-verification consumers — omissions here propagate to every later section)
- §3 (end-to-end shape): synthesis section — walk §1 × §2 and describe end-state
- §5 (does-NOT-count-as-complete): anti-shortcut catalogue — unusually high-value for literalist consumers — always include the written-vs-wired entries: documented/specified-but-not-wired items for every implementation-bearing dimension (see §11)
- §7 (open completeness questions): explicit handoff to phase-shape layer; do NOT silently resolve

**Optional — parallax derivation for high-stakes or meta-circular maps.** When a map is high-stakes (it will gate validation) or meta-circular (it maps the very skill/DIB being changed), optionally run an independent second derivation — a parallax pass, ideally a different model family — and synthesize the two with per-axis provenance. See *Orchestration conventions*.

### Step 4 — Apply v2.0 enums

Load `references/enums.md`. Annotate each enumerated item with:
- **Status enum:** `done` / `covered_by_child` / `covered_by_deferral` / `parent_owned_open` / `uncovered`
- **Completion-effect enum:** `complete` / `conditionally_accounted_for` / `incomplete`

For `covered_by_deferral` items, include the load-bearing-deferral shape (description / status / completion_effect / blocks_full_completion / automation_blocking / reference URI).

**No-provider rule:** unresolved deferrals' status is `unknown` — these MUST NOT count as completed in strict/canonization mode.

**Freeze-time status:** at freeze / pre-implementation, a closure dimension the work-unit explicitly owns and has not yet done is `parent_owned_open + incomplete` — NOT `uncovered`. `uncovered` per `references/enums.md` is a *gap* (not done, not delegated, not deferred, **not parent-owned**); reserve it for genuine unaccounted gaps that should be re-derived or deferral-filed.

### Step 5 — Apply nested-handling rules (if applicable)

Load `references/nested-handling.md`. If the DIB has nested `*.dib/` child DIBs, ensure the map:
- Honors authority-vs-completion-scope (parent completion = own subject + direct-child aggregate + parent-owned/deferred — NOT transitive descendant checklist)
- Respects the bidirectional `.dib/` lease
- References children via `covered_by_child` with the child's *role*, not the child's internal closure dimensions

For each child `.dib/`, the child has its own map generated separately.

### Step 6 — Write or report

- `new` / `refresh` with `--apply`: write to `<dib>/derived/completeness-map.md`
- `check`: re-derive in memory, diff against existing, report
- `validate`: inspect existing for anti-pattern + missing sections + enum compliance **+ the completion-claim gate** (block any DIB-completion claim lacking a DIB-level closure map), report
- `residual-obligations` with `--apply`: emit the DIB Residual-Obligations block for `<dib>`; REFUSES a `claimed: yes` block when no DIB-level closure map exists
- Default `--dry-run`: print proposed content to stdout, no write

## Output shape

The output is markdown ~50–150 lines per single-DIB scope. Skeleton at `templates/completeness-map-template.md`. Concise beats comprehensive.

## Orchestration Conventions

These conventions refine *how* maps are produced and consumed in a multi-work-unit orchestrated run; they do not change the canonical 7-section schema or the enums.

- **Per-work-unit map files.** In a multi-work-unit run, name maps `derived/completeness-map-wu-<N>.md` — one per work unit — rather than one combined map. Per-work-unit files give cleaner freeze granularity.
- **The map-freeze cycle.** A map intended as a validation contract is reviewed and marked `frozen: true` before downstream consumption (`/auto-evals` + audit lanes). A later change to a frozen map is an explicit re-freeze, not a silent edit.
- **Map-authoring parallax (optional — high-stakes / meta-circular maps).** Derive a first pass, then an independent second derivation, then synthesize the two with per-axis provenance (first-pass / parallax / both). This is Step 3's optional parallax pass.
- **Pattern A string-level sync.** Before a frozen map is used to validate an as-built artifact, sync the map against the artifact at **string level** — dates, paths, hashes, filenames, version strings — not only section-presence. A dimension can be "present + covered" while its evidence-anchor string is stale.
- **Optional accounting aids — §8 / §9 / §10.** Layered on top of the canonical 7 sections, a map MAY carry: an optional **§8** closure-dimensions summary table (one row per dimension: section / dimension / status / completion-effect); an optional **§9** map-authoring parallax synthesis summary (per-axis provenance — when a parallax derivation was run); and, at work-unit close, an append-only **§10** closure-accounting record. All three are **optional aids** — NOT additional canonical schema sections; the 7-section schema is unchanged. Skeletons in `templates/completeness-map-template.md`. The §10 record is a convenient place to capture the gate's Residual-Obligations buckets at close, but it does not itself satisfy the gate; a DIB-level closure map + a reconciled Residual-Obligations block does.
- **Freeze-time status convention.** Pre-implementation owned dimensions are `parent_owned_open + incomplete` (see Step 4) — they transition to `done + complete` at close.
- **Cross-DIB conventions.** Sibling skill DIBs may share §6 (out-of-scope) content where their boundaries genuinely coincide — but a map MUST NOT enumerate a sibling's or descendant's internal closure dimensions (the no-transitive-enumeration rule, `references/nested-handling.md`). Reuse the *boundary statement*, never the internals.

## What this skill deliberately does NOT do (v1.1)

- **No silent child→DIB completion upgrade.** Per the completion-claim gate (see *Completion-claim Gate*), this skill will NOT certify governing-DIB completion — and will not emit `Full governing-DIB completion claimed: yes` — from child/work-unit completion alone; it BLOCKS and reports when no DIB-level closure map exists. This is a hard gate, not an advisory.
- **No drift-detection automation.** `check` reports drift — including string-level drift — but it does not auto-refresh, and there is no file-watcher.
- **No file-watcher auto-trigger.** Invocation is manual or orchestrator-template-mediated; a file-watcher / git-hook remains out of scope because it would overlap `/dib gate-cleanup` hook territory.
- **No mandatory invocation.** The eligibility gate is honest; some DIBs don't need the sidecar.
- **No PCB-side coverage allocation.** That's `derived/completeness-coverage.md` (PCB folder), out of scope.
- **No subagent shim for deterministic paths.** Derivation is LLM-bearing judgment; the invoking agent IS the LLM. (See `feedback_skill_direct_bash_over_subagent_shim.md` user memory.)
- **No VERSION.json sidecar on the map itself.** The map's freshness is detected via `check`; the map's authority is non-authoritative-derived.

## Compatibility Notes

The canonical substrate is the 7-section schema, the status/completion-effect enums,
the eligibility gate, the load-bearing anti-pattern, and nested-handling. Current
changes refine the generation and validation mechanism around that substrate without
changing the canonical schema.

The completion-claim gate adds one enforcement verb, `residual-obligations`, and
teaches `validate` to block governing-DIB completion claims that lack a DIB-level
closure map. The optional template closure-accounting section remains an aid, not
the gate itself.

## Operational References

- `references/schema.md` — canonical 7-section schema.
- `references/enums.md` — status/completion-effect enums and deferral shape.
- `references/eligibility.md` — opt-in decision tree for sidecar generation.
- `references/anti-patterns.md` — implication-map authoring rule and drift recovery.
- `references/nested-handling.md` — parent/child `.dib/` completion boundaries.
- `templates/completeness-map-template.md` — output skeleton and optional accounting aids.

## Operating guardrails

- **Read `references/anti-patterns.md` BEFORE generating content.** Implication map, not todo list. The single load-bearing rule.
- **Honor the eligibility gate.** Don't pre-emptively scaffold for DIBs that don't qualify.
- **`--dry-run` is the default.** Orchestrators add `--apply` deliberately.
- **For nested DIBs, run the skill per-`.dib/`.** A parent DIB's map does NOT enumerate descendant closure dimensions transitively.
- **Use a large-enough context window for large governing-law reads.** The skill's accuracy depends on full-context reading of the design corpus; don't truncate.
- **Surface contradictions; don't silently resolve.** Conflicts between DIB and companion specifications belong in §7 (open completeness questions), not hidden inside a single-resolution item.
- **Completion-claim gate — ENFORCED, not advised.** Never infer governing-DIB completion from child/work-unit completion without a DIB-level closure map; BLOCK the claim and report the gap. Completion reports carry a DIB Residual-Obligations block (emit it via the `residual-obligations <dib>` sub-command); `claimed: yes` requires a DIB-level map with every obligation bucketed.
- **The §8 closure-dimensions summary table, the §9 parallax-synthesis summary, and the §10 close-record are optional accounting aids** (see `templates/`) — they layer on top of the canonical 7 sections; they are not additional schema sections.
