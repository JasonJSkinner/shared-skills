# Completeness Map

A completeness map is a derived sidecar that answers one question for a governing design artifact: **what does "complete" actually mean for this thing, across everyone and everything that consumes it?** It takes a Durable Intent Brief (DIB) whose prose declares *what good looks like* and expands that declaration into an exhaustive, structured enumeration of the closure dimensions completion depends on — the consumers, the surfaces, the end-to-end shape of done, the surrounding layers that must also exist, and, critically, the shortcuts that would *falsely signal* completion.

The map is **regenerable and non-authoritative**. The governing DIB remains the source of truth; the map is a derived expansion of it, cheap to regenerate and expected to drift as the DIB and the built system change. It exists to be *read by downstream consumers* — validators, evaluation/scenario generators, audit passes — as the explicit closure-dimension enumeration they check an implementation against.

This skill is provider-neutral. The map *artifact* and the authoring doctrine below stand on their own. Agent-harness-specific mechanics (how the skill is invoked, how large-context derivation is configured) are isolated in the **Provider notes** subsection so they can be swapped without touching the doctrine.

## Why Completeness Maps Exist

A DIB's "what good looks like" is prose. Prose carries intent well for a human reading between the lines — but agent implementers increasingly favor *literal* execution over between-the-lines reading. A literalist executor compresses a qualitative completion statement into a handful of atomic, checkable items, and in the compression it silently drops the closure dimensions that were implied by structure rather than stated outright. The implementation then satisfies the checkable items, reports "done," and is wrong — not because it disobeyed, but because it obeyed a lossy reading.

The most damaging version of this failure is **written but not wired**. Code or documentation *exists* while the consumer-facing path that would actually invoke it is dead:

- A test suite goes green over an install that consumers cannot even import.
- A gate ships as prose only — described in a document, never enforced by anything that runs.
- Claim language describes a mechanism the delivered artifact does not contain.

Each of these passes a literal check and fails the real one. The completeness map is the countermeasure: it enumerates completion as *implications a downstream agent still has to think about*, and it carries an explicit anti-shortcut catalogue naming the written-but-not-wired traps for the specific artifact at hand. It is most valuable exactly when the intended consumers are literalist-execution models, or when the closure dimensions are heterogeneous enough that prose alone cannot carry them.

## The Load-Bearing Rule: Implication Map, Not Todo List

This is the single most important authoring rule, and the whole value of the artifact depends on it.

> **The sidecar is an exhaustive *implication map*, not an exhaustive *todo list*.** Each item enumerates a **closure dimension and its implications**, not a **checkable atom** or an **action to take**.

Collapsing the map into a checklist reproduces the exact failure the map is supposed to fix — one layer down. If the map is a list of `[ ] do X` items, a downstream agent can tick them off literally without ever reasoning about what would make the consumer actually satisfied. The implication framing forces that reasoning to happen: a validator or eval generator reading the map still has to think about *how* its scenarios and probes cover each dimension. It cannot short-circuit.

**The "satisfy literally" test.** Read each item and ask:

> *Could a downstream agent satisfy this literally — by performing the named action — without thinking about what would actually make the consumer happy?*

- **If yes** → it is a todo-list item. Reframe it as an implication.
- **If no** (the item demands reasoning about consumer outcome) → it is an implication-map item. Keep it.

**Bad vs. good (neutral domain — a CLI error-output component):**

| Todo-list (wrong) | Implication map (right) |
|---|---|
| `[ ] support humans` | "Humans hitting an error at the terminal — they need to classify the failure (their input vs. their environment vs. a tool bug) within seconds, without reading source, and get a next action when one is knowable." |
| `[ ] support scripts` | "Programmatic callers parsing exit codes and structured output — they need stable, documented codes and machine-readable fields; a wording change that shifts a code silently breaks them." |
| `[ ] CLI works` | "A user invoking any command that can fail receives output that names the failure class before the detail and stays consistent in voice across every command that produces it." |
| `[ ] wire up the classifier` | "*Written but not wired*: a classifier that exists in the codebase while no command path actually routes its errors through it — the mechanism is present and dead." |

Items in the *open questions* section (below) may look more atomic, because they are explicit handoffs to a later planning phase — but even those should carry enough context that the downstream resolver knows what a good resolution looks like.

## The Seven-Section Schema

The map is organized into seven canonical sections. Each enumerates closure dimensions for one aspect of completion. The section numbers below (§1–§7) are the *artifact's own* schema — they are stable and part of the deliverable.

If a section has nothing to say, write `(none known at derivation time)` rather than omitting it. An empty signal is informative; an omission is ambiguous.

**§1 — Intended consumers.** Every consumer of the system, enumerated across buckets: human · agent · downstream artifact · runtime/install · downstream-verification (validators, eval generators). For each, note *what they consume* and *what "complete" means from their angle*. Omissions here propagate into every later section, so this is the highest-leverage section to get exhaustive.

**§2 — Intended surfaces and access paths.** Every interface a consumer might use — command-line entrypoint, API, UI, library import, file format, hook trigger. Surface and access path travel together because different paths to the same surface have different completion implications (an entrypoint invoked directly vs. chained from another tool are two items).

**§3 — End-to-end shape of done.** The synthesis section. It answers *"what does the world look like when this is shipped?"* Walk §1 × §2 and describe the consumer-visible end-state for each pairing, then aggregate. A list of artifacts produced is **not** an end-state — the end-state is what the consumer *experiences after* those artifacts ship.

**§4 — Implied surrounding layers.** What else must exist for §3 to be coherent: validation, error reporting, observability, documentation, migration, cross-reference resolution. Each governing-law cross-reference's downstream demands becomes an implied-layer item.

**§5 — What does NOT count as complete.** The anti-shortcut catalogue specific to this artifact — the shortcuts an implementation might take that would falsely signal completion. **Always include the written-but-not-wired entries**: for every implementation-bearing dimension, name the *documented-or-specified-but-not-wired* trap explicitly. This section is unusually high-value for literalist-execution consumers, because the anti-shortcut is precisely the failure mode they tend toward.

**§6 — Explicitly out of scope.** Sibling artifacts, future work, and orthogonal concerns this artifact intentionally does not cover — and who owns them instead. Keep it sharp: list only concerns that could *plausibly be confused with* this artifact's scope (mistaken claimants), not every conceivable orthogonal thing.

**§7 — Open completeness questions.** The handoff to the downstream planning / phase-shape layer: questions the DIB cannot answer that downstream work must resolve. Annotate each with a status (below) and, where possible, a tracker reference. Surface contradictions between governing sources here — never silently resolve them.

### Deriving the sections

Read the governing law the invocation specifies — the DIB, its supporting specifications, its cited decision records, and any referenced design artifacts — and apply their authority order (the DIB wins on conflict). Where sources contradict, put the contradiction in §7; the map is derived and non-authoritative, so it cannot resolve a conflict in its own sources. A single-artifact map is typically compact (on the order of tens to low-hundreds of lines); *minimum-included* is the governing anti-fragility principle — concise beats comprehensive, and a smaller true map beats a padded one.

## The Annotation Model

Every enumerated item carries two coupled annotations: a **status** (what state this closure dimension is in) and a **completion-effect** (what that state means for the parent artifact's overall completion verdict).

**Status enum:**

| Status | Meaning |
|---|---|
| `done` | Satisfied by the artifact's own implementation. |
| `covered_by_child` | Delegated to a direct child artifact whose own map owns it. |
| `covered_by_deferral` | Covered by an explicit external deferral reference — not yet done, but accounted for. |
| `parent_owned_open` | The artifact explicitly owns this item and has not done it yet (visible, uncovered-but-owned work). |
| `uncovered` | Not done, not delegated, not deferred, not owned — a genuine gap. |

**Completion-effect enum:**

| Completion-effect | Meaning |
|---|---|
| `complete` | Contributes positively to the completion verdict. |
| `conditionally_accounted_for` | Accounted for (e.g., deferred) but its completion is conditional on resolution. |
| `incomplete` | A gap; the artifact cannot be reported complete while this item is in this state. |

**The meaningful pairings:**

| Status | Completion-effect | Reading |
|---|---|---|
| `done` | `complete` | Fully complete. |
| `covered_by_child` | `complete` | Delegated; child is done. |
| `covered_by_child` | `incomplete` | Child is not done; parent inherits the incompleteness. |
| `covered_by_deferral` | `conditionally_accounted_for` | *"Coverage complete, completion blocked"* — accounted-for, not done. |
| `parent_owned_open` | `incomplete` | A visible gap the artifact still owns. |
| `uncovered` | `incomplete` | A hidden gap — re-derive it, or file a deferral for it. |

Two disciplines make the annotations trustworthy:

- **At freeze / pre-implementation**, a dimension the work explicitly owns but has not yet built is `parent_owned_open + incomplete`, **not** `uncovered`. Reserve `uncovered` for genuinely unaccounted gaps. Owned-but-open work transitions to `done + complete` at close.
- **A deferral whose tracker cannot be resolved has `unknown` status**, and unknown/open deferrals **must not** be counted as completed work in a strict or canonization pass. Such a map reports *"Coverage complete, completion blocked"* until the tracker resolves or the item is reclassified.

### Load-bearing deferrals

When an item is `covered_by_deferral` *and* the deferred work is load-bearing (the artifact cannot be considered fully complete until it resolves), record the full shape rather than a bare annotation:

```yaml
- description: <human-readable closure dimension>
  status: covered_by_deferral
  completion_effect: conditionally_accounted_for
  blocks_full_completion: true      # load-bearing flag
  automation_blocking: false        # can automation proceed without it?
  reference:
    scheme: <tracker scheme, e.g. github:// | file:// | manual://>
    id: <provider-stable ID>
    label: <human-readable handle, optional>
    context: <project / tracker context>
```

The deferral's *live status* is resolved from its tracker at evaluation time — **do not mirror the tracker's status into the map.** Mirroring creates a stale second ledger. The durable part is the reference (stable ID + context + label); the status is not, so leave it to the source of truth.

## The Completion-Claim Gate

The map is also the enforcement point for a completion-claim gate with two parts. Both are *gates, not advice*: when a consumer asks whether a whole artifact is complete, apply them and block on failure.

**Part 1 — the anti-shortcut completion rule (hard gate).**

> Do **not** infer whole-artifact completion from child / work-unit completion unless a **whole-artifact map exists**.

"All the scoped child pieces are done" is a different claim from "the governing artifact is complete." A governing artifact carries its own subject plus parent-owned obligations plus sibling- and publisher-scope that *no child map covers*. A whole-artifact map is this seven-section map derived for the **governing artifact itself** — not the union of its children's maps.

Enforcement: if asked to certify whole-artifact completion when no whole-artifact map exists, **stop and report** — "cannot certify completion; only child/work-unit maps exist; derive a map for the governing artifact first." The honest fallback claim is the narrower *"all scoped child work is complete."*

Distinguish evidence states for any implementation-bearing dimension: **documented** (text exists) → **specified** (behavior defined) → **implemented** (code/config exists) → **wired** (real entrypoints, templates, hooks, or install paths invoke it) → **installed** (present where consumers actually read it) → **exercised** (a test or dogfood path proves it runs) → **derivable** (the completion claim legally follows). Documented or specified behavior that is not wired into an invoked runtime, install, template, hook, or consumer path does **not** count as complete.

**Part 2 — the residual-obligations reporting contract.**

Every wave-close or completion report that touches a governing artifact carries a **residual-obligations block**. A report may declare full completion **only when** a whole-artifact map exists *and* every governing obligation is accounted for in one of four buckets:

```markdown
## Residual Obligations — <artifact name>

Full completion claimed: yes | no

Satisfied in this wave:
- ...

Intentionally out of scope:
- ...

Deferred / future:
- ... (cite deferral references)

Known parent-owned or sibling-owned obligations:
- ...
```

Acceptance gate: no report may say "complete" unless (1) a whole-artifact map exists and (2) the block declares `Full completion claimed: yes` with every bucket reconciled. Otherwise the strongest honest claim is "all scoped child work is complete."

## Operations

The map supports a small verb surface. The four derivation verbs are the core; the reporting verb enforces the completion-claim gate.

| R/W | Verb | What it does |
|---|---|---|
| W | `new` | Derive a fresh map. The eligibility gate (below) must pass. |
| R | `check` | Re-derive in memory and diff against the existing map — report drift, including **string-level** drift (dates, paths, hashes, filenames, version strings), not only section presence. |
| W | `refresh` | Re-derive and overwrite the existing map (drift acknowledged, intentional). |
| R | `validate` | Inspect the existing map for the todo-list anti-pattern, missing sections, enum compliance, **and** the completion-claim gate. |
| W | `residual-obligations` | Emit the residual-obligations block for the artifact; refuse a `claimed: yes` block when no whole-artifact map exists. |

Write verbs default to a dry run (print the proposed content); committing is a deliberate, explicit step.

### Nested artifacts

When a governing artifact has nested child artifacts, generate a map **per child** — a parent map does **not** enumerate a child's internal closure dimensions transitively (that produces "descendant checklist sprawl" and double-tracks work the child already owns). Instead, a parent map references each direct child via `covered_by_child` and describes the child's *role*, not its internals. Completion aggregates **structurally, not transitively**: the parent reads its direct children's verdicts; each child's verdict already folds in its own descendants. The scope boundary is bidirectional — a parent map does not reach down into a child's internals, and a child map does not reach up into the parent's surfaces or sideways into a sibling's. A child that believes the parent's map is missing a delegation surfaces it through the parent's authority chain (file a deferral, or note it in the child's §7); it does not edit the parent's map directly.

### Optional accounting aids

For orchestrated, multi-work-unit runs, a map *may* carry a few optional aids **layered on top of** the seven canonical sections — they are aids, not additional schema sections:

- a **closure-dimensions summary table** (one row per dimension: section · dimension · status · completion-effect · evidence anchor);
- a **parallax-synthesis summary**, recorded only when the map was derived twice independently (ideally by different model families) and the two passes were reconciled with per-axis provenance;
- an append-only **closure-accounting record** added at work-unit close, recording validation outcomes and the final per-dimension status while the frozen sections stay byte-unchanged.

The closure-accounting record is a convenient place to capture the residual-obligations buckets at close, but it does **not** by itself satisfy the completion-claim gate — a whole-artifact map plus a reconciled residual-obligations block does.

## When NOT to Use

The map is opt-in. Do not generate one when it is not warranted — pre-emptive scaffolding is itself an anti-pattern. Run this eligibility gate first:

```
1. Does the DIB declare a completion boundary — an outcome/quality-bar
   section, or an otherwise-defined deliverable, capability, workflow,
   system, or integration surface?
     NO  → STOP. Not eligible. "This artifact does not define a
           completion boundary; a map is not appropriate."
           (Constitutional / principle artifacts typically fall here.)
     YES → continue.

2. Are the intended consumers heterogeneous enough that the prose
   completion boundary alone cannot carry the implication map — OR are
   the consumers literalist-execution models?
     NEITHER → STOP. Not necessary. "The prose boundary suffices for
               this consumer profile; a map is not pre-emptively
               scaffolded."
     EITHER  → generate the map.
```

Specifically, do **not** produce a map for:

- **Constitutional or principle artifacts** that declare timeless values rather than a deliverable — they have no completion boundary to map.
- **Single-consumer, one-shot tools** with homogeneous consumers, where qualitative prose is already sufficient.
- **Artifacts whose completion implications are genuinely trivial** (single consumer, single surface, single deliverable) — the prose boundary *is* the implication map; a sidecar would duplicate, not add.

When uncertain, surface the uncertainty and default to *skip*. Re-run the gate later if the artifact grows a completion boundary and heterogeneous consumers — eligibility can change.

## Provider notes

The doctrine above is provider-neutral. These mechanics are agent-harness-specific.

- **Invocation.** In harnesses that support slash commands, the map is produced through a `/completeness-map <verb> <artifact>` command surface (`new`, `check`, `refresh`, `validate`, `residual-obligations`). In harnesses without that surface, the same verbs are performed manually against the artifact shape described above.
- **Orchestrator convention.** In orchestrated multi-step runs, `new <governing-artifact>` is commonly wired as an early step of each work-unit procedure, so the derived map becomes the explicit closure-dimension enumeration that downstream evaluation and audit passes consume. Downstream consumers run `check` (read-only) before relying on a map, to catch drift.
- **Large-context derivation.** Deriving a map reads the full governing-law set — the DIB plus its supporting specs, decision records, and design artifacts — and its accuracy depends on reading that set without truncation. When the set is large, configure the deriving agent with a large-context window; do not truncate the design corpus. Some harnesses default a model *alias* to a smaller context than the underlying model supports — bind the explicit large-context configuration when that applies.
- **Consumers are model-agnostic.** The map is authored to be legible to validator and evaluation agents of any family; it is not tuned to one model. Its highest value, though, is with literalist-execution consumers, which is why the anti-shortcut section is mandatory rather than optional.

## Partial Adoption

You can adopt the completeness-map *artifact and authoring doctrine* independently of any surrounding pipeline.

**Minimum viable adoption (dependencies).** The map derives *from* a governing design artifact that declares a completion boundary — that upstream artifact (a DIB, or any equivalent intent document with a "what complete looks like" statement) is the one hard dependency. Given such an artifact, you can author a completeness map as a single standalone Markdown file using the seven-section schema, the status/completion-effect annotations, and the completion-claim gate, with nothing else installed. The map is then consumable by any human, validator, or evaluation agent you point at it.

**What is optional (add only if you need it):**

- **The deferral-reference machinery** (`covered_by_deferral` items with a tracker scheme) — add when some closure dimensions are genuinely deferred to an external tracker. Without a tracker, use `parent_owned_open` for owned-but-open work and keep the map self-contained.
- **The nested / per-child generation rules** — add only when the governing artifact has child artifacts. A flat, single artifact needs none of the parent/child aggregation machinery.
- **The optional accounting aids** (summary table, parallax-synthesis record, closure-accounting close record) — add only inside an orchestrated multi-work-unit run. A single-artifact map needs none of them.
- **The orchestrator wiring** (auto-invoking the map as a work-unit step) — add when a pipeline consumes maps mechanically. On its own, the map is produced and read on demand.

**What breaks if you take only part of it:**

- **Dropping the eligibility gate** and generating a map for every artifact reproduces the scaffolding anti-pattern: maps for constitutional/principle artifacts have no completion boundary to enumerate and become noise. Keep the gate.
- **Collapsing the implication map into a todo list** breaks the entire value proposition — a checklist can be satisfied literally, which is the exact failure the map exists to prevent. If you keep only one rule, keep *implication map, not todo list*.
- **Mirroring a deferral's live status into the map** breaks freshness: the map becomes a stale second ledger that disagrees with the tracker. Store the reference, resolve the status at evaluation time.
- **Using the completion-claim gate without a whole-artifact map** cannot certify whole-artifact completion — the gate is defined *in terms of* that map. Without it, the strongest honest claim is "all scoped child work is complete," and the gate correctly refuses anything stronger.
