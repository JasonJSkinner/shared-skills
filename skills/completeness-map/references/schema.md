# /completeness-map — Canonical 7-Section Schema

The `derived/completeness-map.md` sidecar is an **exhaustive implication map** organized into 7 canonical sections. Each section enumerates closure dimensions for one aspect of completion.

> **Load-bearing authoring rule (read `anti-patterns.md` first):**
> Each section is an *implication map*, not a *todo list*. Items enumerate *closure dimensions and implications*, not *checkable atoms*.

---

## §1 — Intended consumers

Every consumer of the system: internal AND public AND downstream tools AND validators AND eval generators.

**How to derive:**
- Read the DIB's purpose statement + governing-law downstream-consumer references.
- For each named consumer, note: what they consume (artifact / output / interface) and what *"complete"* means from their angle.

**Bad vs. good:**

| ❌ Todo-list | ✅ Implication map |
|---|---|
| `[ ] support humans` | "Humans invoking the skill directly via slash command — they need a one-paragraph mental model on read, a deterministic invocation, and output they can hand to a downstream agent" |
| `[ ] support agents` | "Orchestrator agents chaining the output into validation passes — they need machine-parseable output, deterministic invocation, contract-grade verdicts" |

---

## §2 — Intended surfaces + access paths

Every interface a consumer might use: CLI, API, UI, library import, file format, hook trigger, etc. Surface + access path together because different access paths to the same surface have different completion implications.

**How to derive:**
- Read the DIB's interaction model + any decision artifacts about CLI surface, flags, sub-commands.
- Each surface-access-path pair becomes one item with its own completion implication.

**Example items:**
- CLI sub-command entrypoint with `<arg>` semantics
- Optional flag composition (`--chain`, `--scope`)
- Output artifacts (file paths, schema)
- Input artifact contracts (file types, schema)

---

## §3 — End-to-end shape of done

What the consumer-visible state looks like when the system is shipped. This is the **synthesis** section — it answers *"what does the world look like when this is done?"*

**How to derive:**
- Walk §1 (consumers) × §2 (surfaces) and describe the end-state for each pair.
- Then aggregate.

**Bad vs. good:**

| ❌ Bad | ✅ Good |
|---|---|
| `[ ] CLI works` | "A consumer invoking the CLI receives back a materially-distinct (vs. implementation tests) executable suite that either catches at least one meaningful gap or convincingly expands coverage in at least one major contract area" |
| `[ ] tests pass` | "The skill's self-tests for the v2.x build pass against the new lane architecture (Lanes 1a/1b/2/3 + Phase C meta-synthesis), and external consumers can reproduce those tests" |

**Anti-pattern:** A list of artifacts produced. Artifacts ≠ end-state — the end-state is what the consumer experiences after the artifacts are shipped.

---

## §4 — Implied surrounding layers

What other layers must also be present for §3 to be coherent: validation / error reporting / observability / docs / migration.

**How to derive:**
- Walk the governing-law cross-references.
- Each cited spec/DR's downstream-consumer demands becomes an implied-layer item.

**Example items:**
- Validator failure-mode compliance (named FMs + repair clauses)
- Reporting verdict shape (named enums from `enums.md`)
- Skill-version-fallback support
- Documentation surface (README, in-skill SKILL.md self-doc)
- Cross-tree reference resolution (per `forests.yaml`)

---

## §5 — What does NOT count as complete

Anti-shortcut catalogue specific to this DIB. Calls out shortcuts the implementation might be tempted to take that would falsely signal completion.

**How to derive:**
- Read the DIB's anti-completion patterns (if present in `What Complete Looks Like`).
- Read the governing-law's documented anti-patterns.
- Each anti-shortcut becomes one item.

**Bad vs. good:**

| ❌ Bad | ✅ Good |
|---|---|
| `[ ] avoid excluding tests` | "A green test suite achieved by excluding hard scenarios — the suite is green only because the contract probes were left out, not because the implementation passes them" |
| `[ ] don't fake completeness` | "Self-verification by the same agent that built the implementation, when an independent verifier was practically available — the holdout discipline relies on independence at delivery time" |

**This section is unusually high-value for literalist-execution-model consumers** because the anti-shortcut is exactly the failure mode they tend toward.

---

## §6 — Explicitly out of scope

Sibling DIBs / future work / orthogonal concerns this DIB intentionally does not cover. Reduces scope creep + clarifies hand-offs.

**How to derive:**
- Read the DIB's scope statement.
- Read the parent DIB's child-set (sibling DIBs own their own scope).
- Read any `covered_by_child` delegations.

**Example items:**
- Sibling skill's domain (e.g., for `/auto-evals`: PCB authoring is out-of-scope; `/dib gate-cleanup` is `/dib`'s domain)
- Future-phase work (e.g., Phase 2 install sprint is out-of-scope for Phase 1 skill builds)
- Cross-cutting concerns owned elsewhere (e.g., `authorship.yaml` hygiene is `/dib`'s domain)
- Forward-deferred work tracked via `/deferrals` v0.2

---

## §7 — Open completeness questions PCBs must resolve

Handoff to phase-shape layer. Questions the DIB can't answer that downstream planning must.

**How to derive:**
- Read build-time-choice sections in the governing artifacts.
- Read any `[synthesis-deferred]` entries in the governing law.
- Read any "this is an implementation choice" notes.

**Example items:**
- "What's the file-naming convention for lane artifacts?" (build-time choice)
- "Does the holdout discipline extend across sub-skill boundaries?" (synthesis-deferred)
- "What's the cross-skill drift-detection mechanism?" (open question)

Each item should be annotated with `status: covered_by_deferral` or `parent_owned_open` (see `enums.md`) and, if possible, a deferral URI.

---

## Length guidance

Total map is typically **~50–150 lines per single-DIB scope**. Larger if the DIB spans multiple Companion Specs. Smaller is fine — minimum-included is a Root v2.4 P14 anti-fragility principle.

## When NOT to emit a section

If a section has nothing to say — e.g., §7 with no open questions — write `(none known at derivation time)` rather than omit. Empty signal is informative; omission is ambiguous.

## Authority order when sources contradict

If the DIB says X and a Companion Spec or DR says Y:

1. **DIB wins on conflict.**
2. Surface the contradiction in §7 (open completeness questions); do NOT silently choose.
3. The sidecar is derived-non-authoritative; it cannot resolve contradictions in the canonical sources.
