# derived/completeness-map.md — <DIB-name>

> **Status:** derived, regenerable, non-authoritative.
> **Authority:** the DIB's own `What Complete Looks Like` section wins on conflict; this sidecar is a derived expansion.
> **Authoring rule:** **implication map, NOT todo list.** Each item enumerates a closure dimension or implication, not a checkable atom.
> **Generated:** <YYYY-MM-DD> by `/completeness-map new <dib> --apply`.
> **Eligibility:** <gate-result OR `sprint-mode override`>
> **Governing law (sources read for this derivation):**
> - <DIB-name> — the DIB this map derives from
> - <Companion specifications cited>
> - <Decision artifacts cited>
> - <design artifacts cited, e.g., `dib-write-gate-doctrine-v4.md`>

---

## §1 — Intended consumers

Every consumer of the system: internal AND public AND downstream tools AND validators AND eval generators.

- <consumer> — what they consume + what *"complete"* means from their angle. *(status: X, completion-effect: Y)*
- <consumer 2> — ...
- ...

---

## §2 — Intended surfaces + access paths

Every interface a consumer might use: CLI, API, UI, library import, file format, hook trigger, etc.

- <surface> via <access path> — completion implication. *(status: X, completion-effect: Y)*
- <surface 2> via <access path 2> — ...
- ...

---

## §3 — End-to-end shape of done

What the consumer-visible state looks like when the system is shipped.

- <consumer-visible end-state element> — ...
- <element 2> — ...
- ...

---

## §4 — Implied surrounding layers

What other layers must also be present for §3 to be coherent: validation / error reporting / observability / docs / migration / cross-tree refs.

- <implied layer> — why it's required. *(status: X, completion-effect: Y)*
- <layer 2> — ...
- ...

---

## §5 — What does NOT count as complete

Anti-shortcut catalogue specific to this DIB. Unusually high-value for literalist-execution-model consumers.

- <anti-shortcut> — what the implementation might do that would falsely signal completion
- <anti-shortcut 2> — ...
- ...

---

## §6 — Explicitly out of scope

Sibling DIBs / future work / orthogonal concerns this DIB intentionally does not cover.

- <out-of-scope item> — who owns it instead (sibling DIB / future work / orthogonal concern)
- <item 2> — ...
- ...

---

## §7 — Open completeness questions (handoff to phase-shape layer)

Questions the DIB can't answer that downstream planning must.

- <question> — *(status: covered_by_deferral, conditionally_accounted_for; ref: deferrals://ddf_xxxxxxxx)*

For load-bearing deferrals, use the full YAML form:

```yaml
- description: <closure dimension>
  status: covered_by_deferral
  completion_effect: conditionally_accounted_for
  blocks_full_completion: true
  automation_blocking: false
  reference:
    scheme: deferrals://
    id: ddf_xxxxxxxx
    label: <human handle>
    context: <project context>
```

If no open questions are known at derivation time, write: `(none known at derivation time)` — empty signal is informative; omission is ambiguous.

---

## §8 — Closure-dimensions summary table (optional)

An optional accounting aid for orchestrated multi-work-unit runs — a consolidated one-row-per-dimension view of the §1–§7 annotations. It **layers on top of** the 7 canonical sections; it is NOT an 8th schema section. Omit it for simple single-DIB maps.

| # | Closure dimension | item_status | completion_effect | Evidence anchor |
|---|---|---|---|---|
| 1 | <dimension> | <status enum> | <completion-effect enum> | <commit / artifact / `TBD`> |
| ... | ... | ... | ... | ... |

---

## §9 — Map-authoring parallax synthesis summary (optional)

Include this only when a parallax derivation was run (SKILL.md *Orchestration conventions*). Record per-axis provenance — first-pass / parallax / both / rejected — and the net-additivity assessment. Like §8 and §10, an optional accounting aid layered on top of the canonical 7 sections — NOT a schema section.

---

## Derivation notes (optional, for the orchestrator/auditor)

Any context that helps a future agent re-derive or compare maps:

- Contradictions surfaced between sources: <surface them here, not silently resolved>
- Open questions queued to §7: <which sources flagged them>
- Items where enum assignment was ambiguous: <briefly note>

---

## Re-derivation

```bash
/completeness-map check <dib>           # diff against this map (read-only)
/completeness-map refresh <dib> --apply # overwrite this map with fresh derivation
/completeness-map validate <dib>        # check for anti-pattern + missing sections + enum compliance
```

This sidecar regenerates from the canonical DIB + governing law. Treat its current state as **last-derivation, not source-of-truth**. The canonical sources are authoritative.

---

## §10 — Closure accounting (optional — append-only, added at work-unit close)

An optional append-only close record for orchestrated runs. The frozen §1–§9 content above stays **byte-unchanged**; §10 is appended at work-unit close and records validation outcomes + the final per-dimension status. Cite the freeze SHA. Omit it outside an orchestrated close cycle.

> **Aid, not the gate.** This template **§10** is a *closure-accounting record* — an aid. It is distinct from the ENFORCED completion-claim gate (SKILL.md *Completion-claim gate*). It's a convenient place to capture that gate's DIB Residual-Obligations buckets at close, but it does not by itself satisfy the gate; a DIB-level closure map + a reconciled Residual-Obligations block does.

- **§10.1 — Validation outcomes** — per-channel verdicts + evidence paths
- **§10.2 — Findings + disposition** — each finding + how it was resolved
- **§10.3 — Closure-dimensions final status** — the transitions from the freeze snapshot (`parent_owned_open` → `done`, etc.)
- **§10.4 — Stopping condition** — the explicit statement that the work unit's stopping condition is met
