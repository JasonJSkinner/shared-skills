# /completeness-map — Anti-patterns (READ FIRST)

> **The single most important authoring rule, load-bearing across the whole skill:**
>
> **The sidecar is an exhaustive *implication map*, not an exhaustive *todo list*.**
>
> (This is the governing authoring rule for this skill.)

---

## Why this rule matters

Collapsing the map into a checklist recreates **failure mode 7** (PCB-generator requirements reversion) one layer down. The exact failure the sidecar is supposed to *fix* — literalist execution models compressing intent into atomic checkable items, losing structure-implicit closure dimensions — gets reproduced *inside* the sidecar.

The implication-map framing means downstream agents (PCB generators, validators, eval generators) **still have to think** about how phases / scenarios / probes cover each closure dimension. They can't short-circuit by ticking off items.

The map's *trigger* is exactly this failure: literalist execution agents compress intent into atomic tasks and miss structure-implicit completion dimensions. The sidecar pattern fixes that only if the sidecar itself does not collapse to a checklist.

---

## Bad vs. good — concrete examples

### §1 (Intended consumers)

| ❌ Todo-list | ✅ Implication map |
|---|---|
| `[ ] support humans` | "Humans invoking the skill directly — they need a slash-command entrypoint, a one-paragraph mental model on read, and output they can hand to a downstream agent without inventing glue" |
| `[ ] support agents` | "Orchestrator agents chaining the output into validation passes — they need machine-parseable output, deterministic invocation, contract-grade verdicts; non-determinism breaks chaining" |

### §3 (End-to-end shape of done)

| ❌ Bad | ✅ Good |
|---|---|
| `[ ] CLI works` | "A consumer invoking the CLI receives back a materially-distinct (vs. implementation tests) executable suite that either catches at least one meaningful gap or convincingly expands coverage in at least one major contract area" |
| `[ ] tests pass` | "The skill's self-tests for the v2.x build pass against the new lane architecture (Lanes 1a/1b/2/3 + Phase C meta-synthesis), and external consumers can reproduce those tests" |

### §5 (What does NOT count as complete)

| ❌ Bad | ✅ Good |
|---|---|
| `[ ] avoid excluding tests` | "A green test suite achieved by excluding hard scenarios — the suite is green only because the contract probes were left out, not because the implementation passes them" |
| `[ ] don't fake completeness` | "Self-verification by the same agent that built the implementation, when an independent verifier was practically available — the holdout discipline relies on independence at delivery time" |
| `[ ] wire up the validators` | "Written but not wired — code or docs that exist while the consumer-facing path is dead: a validator that never imports from the live install, a gate that ships as prose only, claim language describing a mechanism the delivery doesn't contain. The *canonical* written-but-not-wired instance; documented/specified ≠ wired for any implementation-bearing dimension (see SKILL §11 evidence ladder)" |

---

## How to spot drift toward todo-list mode

If you find yourself writing items as:

- `[ ] do X`
- `[ ] add Y`
- `[ ] support Z`
- `- implement <component>`
- `- write tests for <function>`

…you've drifted. Each item should describe **a closure dimension and its implications**, not **an action to take**.

### The "satisfy literally" test

Read each item aloud and ask:

> *"Could a downstream agent satisfy this **literally** — by performing the named action — without thinking about what would actually make the consumer happy?"*

- **If yes** → todo-list item. Reframe as implication.
- **If no** (the item demands thinking about consumer outcome) → implication map item. Keep.

---

## When drift is acceptable

Items in **§7 (Open completeness questions PCBs must resolve)** MAY look more atomic, because they're explicitly handoff questions to a later phase. But even §7 items should have *enough context* that the downstream resolver knows what good resolution looks like.

> ❌ "What's the file-naming convention?"
> ✅ "What's the file-naming convention for lane artifacts? Existing examples use both `lane-{N}-*.json` and `L{N}-batch-{NNN}-results.json`. Resolution: pin one; document the discrepancy in the skill docs."

---

## Recovery from drift (the `validate` sub-command's role)

If `/completeness-map validate <dib>` reports drift toward todo-list mode:

1. **Re-read this anti-pattern reference.**
2. **Re-run `/completeness-map new --dry-run <dib>`** to see what fresh derivation looks like.
3. **Compare item-by-item:** for each todo-list item in the old map, reframe as implication.
4. **`/completeness-map refresh <dib> --apply`** once the new shape looks right.

The map is regenerable Zone 3 derived — refreshing it is cheap and expected. Stale or drifted maps are a Zone 3 normal failure mode, not a crisis.

---

## Other anti-patterns

### Mirror the provider's deferral status

❌ The sidecar stores `status: open` or `status: closed` for each deferred item, mirroring the deferral provider's state.

✅ The sidecar references the deferral via URI (`deferrals://ddf_xxxxxxxx`) and lets the *provider* be the source of truth at evaluation time. Mirroring creates a stale second ledger.

### Enumerate descendant closure transitively

❌ Parent DIB's sidecar lists every grandchild's closure items.

✅ Parent DIB's sidecar references children via `covered_by_child` and the child's *role*, not the child's internal closure dimensions. See `nested-handling.md`.

### Silently resolve DIB-vs-Spec contradictions

❌ DIB says X, Spec says Y; sidecar picks Y silently.

✅ Sidecar surfaces the contradiction in §7 (open completeness questions). The sidecar is derived-non-authoritative; it cannot resolve canonical-source contradictions.

### Pre-emptive scaffolding

❌ Generate the sidecar for every DIB by default.

✅ Honor the 15-H/I eligibility gate (`eligibility.md`). DIBs without completion boundaries don't get sidecars. Constitutional DIBs don't either.

### Over-completion of §6 (out of scope)

❌ §6 lists every conceivable orthogonal concern (creates negative-space bloat).

✅ §6 lists only orthogonal concerns that could plausibly be confused with this DIB's scope (mistaken claimants).
