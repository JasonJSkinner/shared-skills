# Deferrals Lane Model — v0.2 Reference

Lazy-loaded sidecar for `/deferrals` v0.2. Load this
when authoring or enriching an H-lane item, or when you need the worked detail
behind the SKILL.md spine. The spine carries the contract + decision flow; this
file carries the bulk model.

---

## 1. The transfer test — elaboration

The lane choice (`L` vs `H`) reduces to one falsifiable question:

> *If another agent in a different chat picked up this item — with access only to
> (a) this deferral entry + (b) the artifacts named in its cross-references — could
> they tend to it competently without asking "what did the user mean here?"*

**Why it is falsifiable, not vibes:** it names a concrete counterfactual reader (a
different-chat agent), a concrete information set (the entry + its cross-refs), and
a concrete failure mode (having to ask "what did the user mean?"). You can
actually run it: read only the entry + cross-refs, and ask whether you'd be stuck.

**Why a static scenario list was rejected:** a hardcoded "these situations are
high-fidelity" list drifts as use cases evolve and invites box-ticking. The
transfer test is durable because it tests the *property* (transferability), not a
*category*.

**Transfer-test supremacy over the default table:** the priority→lane table
sets *defaults*, not verdicts. A `normal`-priority item whose context would leave a
different-chat agent guessing becomes `H` — regardless of what the table says.
Never reduce lane selection to the table alone. The table is the starting point;
the transfer test is the tiebreaker that decides.

**Lean toward fidelity in doubt.** The cost of an over-rich L-should-have-been
item is a few extra lines. The cost of an under-rich H-should-have-been item is a
future agent stuck reconstructing vanished chat context — or worse, acting wrong.

---

## 2. L-lane shape — worked

`L` (lightweight) is for items that pass the transfer test from the title plus a
short pointer. Shape: title + 1-3 lines + optional `verify:`.

```markdown
- [ ] **ddf_4d0e2a91** — Refresh stale README badge
  - threads: 93d4dac5 | created: <YYYY-MM-DD> by 93d4dac5 | lane: L | priority: trivial
  - verify: file-exists `README.md`
  - Badge target URL moved; update when docs are next touched.
```

This is complete as `L`: a different-chat agent can act on "refresh the stale
badge in README.md" without further context. Do not pad it into `H`.

---

## 3. H-lane shape — the full skeleton

`H` (high-fidelity) is for items where transfer requires situated context. The
recommended skeleton (recommended, not mandatory — see §6):

```markdown
- [ ] **ddf_ab12cd34** — <imperative title>
  - threads: <short-ids> | created: <YYYY-MM-DD> by <short-id> | lane: H | priority: <p>
  - verify: <pointer — symbol-exists | file-exists | test-passes | url-200 | custom>
  - **Background:** 50-300 words. The situation, why it was deferred, what makes it
    non-obvious. Enough that a different-chat agent understands the *why*, not just
    the *what*.
  - **Action when triggered:**
    1. <numbered, concrete step>
    2. <step>
    3. <step>
  - **Trigger conditions:** (a) <condition> (b) <condition> (c) <condition>
  - **Bundling:** <co-landing notes — optional; which other work this should land with>
  - **(YYYY-MM-DD)** <inline update as understanding evolves — optional, repeatable>
  - **Cross-reference:** <decision artifacts / specs / sibling deferrals / artifact paths>
```

### Worked H-lane example

```markdown
- [ ] **ddf_ab12cd34** — File eval-artifact fallback deferral when /auto-evals cannot run the expected tool
  - threads: 93d4dac5 | created: <YYYY-MM-DD> by 93d4dac5 | lane: H | priority: important
  - verify: custom — auto-evals fallback path records a deferral instead of silently skipping the artifact
  - **Background:** The `/auto-evals` fallback path is a named H-lane
    consumer for `/deferrals` v0.2. If the expected eval tool is unavailable,
    the downstream agent must preserve the gap as
    actionable deferred work rather than letting the run appear complete.
  - **Action when triggered:**
    1. Identify the unavailable-tool condition and the affected eval scope.
    2. File an H-lane deferral with the failed command, expected artifact, and recovery path.
    3. Cross-reference the governing auto-evals artifact and the run evidence path.
  - **Trigger conditions:** (a) expected command missing (b) command fails before usable
    output (c) policy blocks execution.
  - **Bundling:** Co-land with any change to the `/auto-evals` fallback behavior itself.
  - **Cross-reference:** governing auto-evals artifact; skill version-fallback pattern.
```

This item passes the transfer test: a different-chat agent has the why
(Background), the how (Action), the when (Trigger), and the provenance
(Cross-reference) — no vanished-chat reconstruction needed.

---

## 4. L → H enrichment — worked

`enrich <id>` upgrades an L item to H *in place*. Identity is preserved: same
`ddf_` ID, `threads:` list, `created:` metadata, `verify:` pointer, title.

**Before:**

```markdown
- [ ] **ddf_9cb129e3** — Revisit Phase A-E inline update
  - threads: 93d4dac5 | created: <YYYY-MM-DD> by 93d4dac5 | lane: L | priority: normal
  - Recovery transcript has paste-ready language.
```

**After `/deferrals enrich ddf_9cb129e3`:**

```markdown
- [ ] **ddf_9cb129e3** — Revisit Phase A-E inline update
  - threads: 93d4dac5 | created: <YYYY-MM-DD> by 93d4dac5 | lane: H | priority: normal
  - **Background:** The existing one-line context ("recovery transcript has
    paste-ready language") is retained and expanded so the update can be applied
    without recovering the original chat. <expanded situation here>
  - **Action when triggered:** 1. <...> 2. <...>
  - **Trigger conditions:** (a) <...>
  - **Cross-reference:** recovery transcript grep result; relevant Phase A-E artifact.
```

Note: the ID, thread, created-by, and title are unchanged. The existing L context
seeds the `Background`. `priority` stays `normal` — `enrich`'s job is the *fidelity*
upgrade, not a re-rating (re-rate priority separately only if context clearly warrants).

---

## 5. The agent-led `add` inference loop — worked

v0.2's `add` is agent-led, not title-only. Worked exchange:

```text
User: Defer the auto-evals fallback gap from this run.
Agent: Adding ddf_ab12cd34 [H, important] — File eval-artifact fallback deferral when
       /auto-evals cannot run the expected tool. Confirm or override?
User: Confirm.
Agent: Added ddf_ab12cd34 [H, important].
```

The agent inferred `H` (transfer test: a different-chat agent would need the
why/how/when) + `important` (load-bearing for a downstream run). The one-line
confirm lets the user override before the write. For `H`, the agent populates
Background/Action/Trigger/Cross-reference from chat history without further prompting.

---

## 6. H-lane validation — what "complete" means

The H-lane skeleton fields are **recommended, not mandatory**. The actual
requirement is **passing the transfer test**. Two edge cases:

- **An H item that omits some recommended fields but PASSES the transfer test** —
  acceptable. If a different-chat agent can act from what's there, the item is
  complete. Do not pad it to tick every field.
- **An H item that has ALL fields but still FAILS the transfer test** — NOT
  complete. Field-completeness is not the goal; transferability is. Add the
  missing situated context (usually the Background is too thin, or a load-bearing
  Cross-reference is absent).

When in doubt, run the test literally: read only the entry + its cross-refs, and
ask whether you'd be stuck.

---

## 7. Anti-patterns

- **Padding an L item into H** to look thorough. If it passed the transfer test as
  L, leave it L. Ceremony is not fidelity.
- **Hardcoding a "high-fidelity scenarios" list** as the decision rule. The
  transfer test is the rule; scenario lists only illustrate.
- **`enrich` that creates a new item** instead of upgrading in place. This loses
  the ID, thread lineage, and created-by metadata. Always upgrade in place.
- **Treating the default table as the verdict.** It sets defaults; the transfer test
  decides. A `normal` item still goes `H` when transfer would fail.
- **Making H-lane fields mandatory.** A transfer-test-passing H item with a thin
  Bundling field (or no Bundling at all) is fine.
- **A fast-create shortcut keeping a title-only path.** Fast-create can be
  concise, but it must route through the `add` inference loop — a title-only
  bypass defeats the add contract.
- **Auto-rewriting genuinely-corrupt metadata** as if it were valid legacy.
  Missing `lane:`/`priority:` keys = valid legacy (default L/normal). Malformed
  metadata (e.g. `lane: Q`, broken metadata-line structure) = corrupt → surface it.
- **Conflating fidelity and priority.** They are orthogonal axes. A `blocking`
  item can be mechanically obvious (L-shaped content, H-defaulted by the table); a
  `trivial` item rarely needs H but could if its setup is genuinely nuanced.
- **Treating `blocking` as an escalation workflow.** The default says "H always +
  escalation candidate" — "candidate", not a notification system.

---

## 8. Cross-references

- `../SKILL.md` — the v0.2 spine: contract, verb table, transfer test, default mapping
- `../SKILL.md` — `/deferrals` v0.2 design
- The thin-umbrella + lazy-load structure this sidecar mirrors — bulk reference
  content lives here so the main `SKILL.md` stays lean
- Skill version-fallback pattern (the `/auto-evals` fallback example is the
  canonical first H-lane consumer)
