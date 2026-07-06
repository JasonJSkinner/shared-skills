# /completeness-map — Eligibility Gate

The sidecar is **opt-in**. Don't generate when not warranted.

## The gate (decision tree)

```
1. Does the DIB have a "What Complete Looks Like" section?
   YES → continue to 2
   NO  → continue to 1a

   1a. Does the DIB otherwise clearly define a completion boundary
       (e.g., a deliverable, capability, workflow, system, integration surface)?
       YES → continue to 2
       NO  → STOP. Sidecar NOT eligible.
             Report: "DIB does not define a completion boundary;
                      sidecar is not appropriate."
             (Constitutional DIBs / principle DIBs typically fall here.)

2. Are the intended consumers heterogeneous enough that the prose
   "What Complete Looks Like" section alone cannot carry the implication map?
   Or are the consumers literalist execution agents?

   YES, either → FIRE. Generate the sidecar.
   NO, neither → STOP. Sidecar NOT necessary.
                 Report: "Prose section suffices for this DIB's consumer profile;
                          sidecar not pre-emptively scaffolded
                          by policy)."
```

---

## Heuristic refinements

| DIB type | Eligibility | Why |
|---|---|---|
| **Constitutional / timeless DIBs** (Root v2.5, DIB-System v2.5) | ❌ Typically NOT eligible | They define principles, not deliverables. No completion boundary |
| **Skill-build DIBs** (e.g., `/auto-evals` v2.x) | ✅ Eligible | Heterogeneous consumers + literalist execution agent maintainers |
| **Phase-Contract-Brief-equivalent DIBs** (deliver feature X by Y) | ✅ Eligible | Has explicit completion boundary |
| **Single-consumer one-shot tools** (personal-use script) | ⚠️ Probably skip | Homogeneous consumers + qualitative prose usually sufficient |
| **Parent umbrella DIBs** with N child DIBs | ✅ Eligible IF the umbrella has its own subject + child-aggregation rules | Parent maps enumerate own subject + child aggregate (not transitive descendants) |
| **Child DIBs within a nested suite** | ✅ Eligible per their own local completion | Each `.dib/` has its own map (see `nested-handling.md`) |

---

## When uncertain

Surface the uncertainty to the user:

> *"DIB X has [WCLL section / completion boundary], but I'm uncertain whether the consumer profile is heterogeneous enough to warrant the sidecar. Heuristic suggests [emit / skip]. Override?"*

**Default if no override:** skip (per Root v2.4 P14 "minimum-included" anti-fragility).

---

## Sprint-mode override

Orchestrator-prompt templates may explicitly name `/completeness-map new <governing-DIB> --apply` as Step 1 of every work-unit procedure. In that mode:

- The eligibility check is **satisfied by the explicit invocation** — the orchestrator has decided the map is wanted
- **Skip the gate**; proceed to Step 1 (anti-pattern read) directly
- Report `eligibility_check: skipped (sprint-mode override)` in the generated map's header

This avoids friction without violating the gate — the orchestrator-template author bears the responsibility for eligibility judgment when the gate is overridden.

---

## Re-eligibility

A DIB that didn't qualify initially MAY qualify later (e.g., the DIB grows a `What Complete Looks Like` section + named consumers). Re-run the gate when the DIB changes.

The skill is idempotent on eligibility:
- Calling `new` on a now-eligible DIB generates the map normally
- Calling it on a still-ineligible DIB declines with the appropriate report
- Calling `new` on an already-mapped DIB declines (use `refresh` instead)

---

## Edge case: DIB has WCLL but trivial implications

If a DIB has a "What Complete Looks Like" section but the implications are trivial (e.g., single consumer, single surface, single deliverable), the prose section IS the implication map. Don't duplicate. Skip with:

> *"WCLL section is sufficient as implication map for this scope; sidecar would duplicate, not add value."*

---

## Edge case: DIB has nested `.dib/` but no own WCLL

A parent DIB with N child DIBs but no own completion boundary (rare) may still get a map IF the orchestrator wants explicit `covered_by_child` aggregation. In that case:

- Override the gate (sprint-mode or explicit `--force`)
- Map is sparse — mostly §6 (children own their scope) and `covered_by_child` aggregation
- Honest framing: "parent's completion = aggregate of children's completions per the nested-handling rule"
