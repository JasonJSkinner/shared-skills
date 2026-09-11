# Deferrals

A lightweight "revisit-later" ticket system for agent work. When you are deliberately postponing something — a follow-up you noticed mid-task, a heuristic worth revisiting, an audit you can't run yet — you capture it as a small, stable ticket instead of trusting it to memory. The ticket carries enough context to survive being picked up later, in a different working session, by a different agent, and it gives downstream consumers a stable id to reference rather than losing the item to the churn of a long conversation.

The whole system is deliberately thin: one markdown file per project, mutated in place. There is no database, no scheduler, no notification layer. An agent that can read and write a file can operate it end to end. That thinness is the point — the value is in *not losing deferred work*, and that goal does not need machinery.

This document describes the provider-neutral core. Harness-specific mechanics (where the file lives, how the current working session is identified, how branch/fork lineage is tracked) are isolated in the **Provider notes** subsection so they can be swapped without touching the model.

## What it is

A deferral is a durable ticket for work you are *choosing* to do later. It exists to solve one failure mode: a good idea or a necessary follow-up surfaces in the middle of a long agent conversation, and then evaporates — compacted away, stranded in a session you never reopen, or dropped when work branches into a new line. A deferral pins that item down with a stable id and enough context that it can be acted on out of its original context.

Two properties make it more than a scratch note:

- **Stable identity.** Each item has a short unique id. Downstream work, other tickets, and later agents reference the item *by id* rather than re-describing it — so the item can be resolved, cross-referenced, or handed off without ambiguity.
- **Transferable context.** An item carries the context needed for someone *other than its author* to act on it competently. The bar is explicit (see the transfer test below), and it is the load-bearing design idea of the whole system.

## When to use it

Reach for a deferral when all of these hold:

- The work is **real** (worth doing) but **not now** (you are deliberately postponing it).
- It would otherwise be **lost** — it lives only in the current conversation, which will be compacted, closed, or branched before the work happens.
- Someone may need to **reference or act on it later**, possibly from a different session or as a different agent.

Typical triggers, in the user's words: "defer this", "come back to this later", "revisit X", "note this for later", "what's still open?", "what did I defer?", "mark that done", "resolve the deferral about Y". An agent should also self-invoke a *resolve* when it completes work that clearly closes an open deferral (see Lifecycle → Auto-cleanup).

## The ticket model

Every deferral is one entry in the per-project file. It carries:

| Field | Meaning |
|---|---|
| **id** | Short unique token (e.g. an 8-char hex string). Stable for the item's whole life. |
| **title** | One imperative line — what to do. |
| **status** | `open` · `resolved` · `abandoned`. |
| **context** | Free-form for lightweight items; a structured block for high-fidelity items (below). |
| **fidelity lane** | `L` (lightweight) or `H` (high-fidelity). How much situated context the item carries. |
| **priority** | `trivial` · `normal` · `important` · `blocking`. How much the item matters. |
| **verify pointer** | Optional, machine-checkable "is this still needed / already done?" signal (below). |
| **provenance** | Creation date and the working-session lineage the item belongs to. |

### Two orthogonal axes: fidelity and priority

Fidelity (how much context the item needs to carry) and priority (how much it matters) are **independent**. A `blocking` item can be mechanically obvious and need only a title; a `normal` item can require a paragraph of situated context. Do not conflate them — rating an item `important` does not automatically make it high-fidelity, and vice versa.

- **Fidelity lane** — `L` = title + one to three lines of context. `H` = a structured block (Background / Action when triggered / Trigger conditions / Cross-reference).
- **Priority** — a plain importance rating used for triage. `blocking` means the item explicitly blocks a larger unit of work; it is a flag for a human's attention, not a trigger for any automated escalation.

### The transfer test — how you pick the lane

The lane choice reduces to one falsifiable question:

> *If someone else — a different agent, in a different conversation — picked up this item, with access only to (a) this ticket and (b) the artifacts it cross-references, could they act on it competently without having to ask "what did the author mean here?"*

**Yes → `L` is enough. No, or uncertain → make it `H`.** Lean toward fidelity when in doubt: the cost of an over-rich `L` item is a few extra lines; the cost of an under-rich `H` item is a future agent stuck reconstructing context that no longer exists — or acting on a wrong guess.

The test is deliberately a *property* (transferability), not a *category*. There is no hardcoded "these situations are high-fidelity" list, because such a list drifts and invites box-ticking. You can literally run the test: read only the ticket plus its cross-references and ask whether you'd be stuck.

A useful default mapping (priority → lane) exists as a *starting point*, but the transfer test always wins:

| Priority | Default lane | Rationale |
|---|---|---|
| `trivial` | `L` | Mechanical; the title alone transfers. |
| `normal` | `L` if the transfer test passes, else `H` | Judgment call; default to `H` when uncertain. |
| `important` | `H` | Load-bearing for downstream work. |
| `blocking` | `H` | Blocks a larger unit; carry full context. |

Never reduce the lane decision to this table alone. A `normal` item whose context would leave a different-conversation agent guessing becomes `H` regardless of what the table says.

### Item shapes

**Lightweight (`L`)** — title, one to three lines of context, optional verify pointer:

```markdown
- [ ] **a1b2c3d4** — Refresh the stale README badge
  - lineage: <session-id> | created: 2026-05-20 | lane: L | priority: trivial
  - verify: file-exists `README.md`
  - Badge target URL moved; update when docs are next touched.
```

This is complete as `L`: a different-conversation agent can act on "refresh the stale badge in README.md" with nothing more. Do not pad it into `H`.

**High-fidelity (`H`)** — a structured block. The fields are *recommended, not mandatory*; the real requirement is passing the transfer test:

```markdown
- [ ] **ab12cd34** — <imperative title>
  - lineage: <session-ids> | created: <YYYY-MM-DD> | lane: H | priority: important
  - verify: <optional pointer>
  - **Background:** ~50–300 words. The situation, why it was deferred, what makes it
    non-obvious — enough that a different-conversation agent understands the *why*, not
    just the *what*.
  - **Action when triggered:** 1. <concrete step> 2. <step> 3. <step>
  - **Trigger conditions:** (a) <condition> (b) <condition>
  - **Bundling:** <optional — other work this should land alongside>
  - **Cross-reference:** <related artifacts / sibling deferrals / governing docs>
```

Two edge cases clarify what "complete" means for an `H` item:

- An `H` item that omits some recommended fields but **passes** the transfer test is complete. Don't pad it to tick every field.
- An `H` item that has **every** field but still **fails** the transfer test is *not* complete — field-completeness is not the goal, transferability is. The Background is usually too thin, or a load-bearing cross-reference is missing.

### Verify pointers

An optional one-line, machine-checkable signal of whether the item is still needed. Common forms: "symbol exists", "file exists", "test passes", "URL returns 200", or a free-form custom check. A verify pointer is an *aid to triage*, never an authority to auto-resolve — an agent reviewing items still confirms with the user before closing anything, even when a pointer reports the work looks done.

## Lifecycle

An item moves through three states, driven by a small verb set. No verb requires anything beyond reading and rewriting the markdown file.

**States:** `open` → `resolved` (done) or `abandoned` (won't revisit). Both terminal states are reversible via `reopen`.

**Core verbs:**

| Verb | What it does |
|---|---|
| `list` (default) | Show open items for the current working session. `--all` shows every open item; other filters narrow by lineage or resolved-here. |
| `add <title>` | Create an item. The agent infers a default lane + priority from the conversation, confirms in one line ("Adding [H, important] — <title>. Confirm or override?"), then writes it — populating the `H` block from conversation history when the lane is `H`. |
| `enrich <id>` | Upgrade an `L` item to `H` **in place** — same id, lineage, provenance, and title are retained; the existing one-line context seeds the new Background. Priority is left unchanged unless context clearly warrants a re-rating. |
| `resolve <id>` | Mark done; record who resolved it and when. |
| `reopen <id>` | Undo an incorrect resolve/abandon. |
| `abandon <id>` | Mark as won't-revisit. |
| `claim` | Attach the current working session to items inherited from a parent session (see Provider notes → lineage). |
| `tend` | Walk the open items, re-check any verify pointers, and prompt the user per item (resolve / abandon / keep / edit / enrich), applying choices in a batch. Never auto-resolves. |
| `prune` | Move old resolved/abandoned items to an archive file, keeping the active file lean. |
| `forget <id>` | Hard-delete an item from active and archive files. The *only* destructive verb. |

**Auto-cleanup standing instruction.** When an agent completes work that directly closes an open deferral, it should resolve that item as part of the same turn — not leave it for later. Matching is a judgment call: compare the deferral's title and context against what was just done; resolve when the match is clear, leave open when ambiguous (the user can catch it during `tend`).

**Backward compatibility.** Items written before the two-axis model (no lane/priority) are read as `L` / `normal` by default. This is a *read-time* default, not a rewrite — old items are left untouched. `enrich` is the explicit, per-item upgrade path; there is no bulk migration.

**Corruption vs. legacy.** A *missing* lane or priority is valid legacy — default it silently. A *malformed* value (a lane or priority outside its allowed set, duplicate conflicting keys, broken item structure) is corruption — surface it to the user, never silently rewrite it. The rule: absent keys are legacy; broken or ambiguous keys are corruption.

## When NOT to use it

- **Work you'll do this session.** If you're going to handle it before the conversation ends, just handle it. A deferral is for things that would otherwise be *lost across a boundary*.
- **A task tracker or sprint board.** Deferrals have no scheduling, no assignment, no due dates, no notifications, no team-visible queue. If you need those, use a real issue tracker. `blocking` priority is a flag for a human, not an escalation engine.
- **Durable design rationale.** If the thing to preserve is *why a decision was made* (alternatives weighed, tradeoffs, a ruling that should outlive the chat), that belongs in a decision-record system, not a revisit-later ticket.
- **Team-visible bugs or shared work.** Deferrals are private, per-project, agent-facing scratch. Anything a teammate needs to see belongs in your shared tracker.
- **A note you'll never reference by id.** If the item doesn't need stable identity or transferable context — a passing thought — a plain comment or a line in your notes is lighter.

## Partial adoption

The system degrades gracefully; you can adopt a subset and the rest simply doesn't fire.

**Hard dependency (the irreducible core):** a place to store one markdown file per project, and the ability to read and rewrite it. With only this, capture / list / resolve / abandon all work. Everything else is a layer on top.

**Optional, degrades cleanly if absent:**

- **Session/lineage scoping.** The default `list` filters to the current working session's lineage, which needs the host harness to expose a stable session identifier. Without one, drop the scoping and treat the file as a single shared list — every other verb still works.
- **Fork/branch inheritance (`claim`).** Requires the harness to expose a parent-session link when work branches. Without it, inheritance is manual (attach lineage by hand) or simply unused.
- **Verify pointers.** Each pointer kind needs its checking capability — code intelligence for "symbol exists", filesystem for "file exists", a test runner for "test passes", network for "URL 200". Items work fine with no pointer; an unavailable checker just means that item isn't auto-triaged during `tend`.
- **The two-axis fidelity model.** You can run `L`-only and ignore lanes and priority entirely; untagged items read as `L` / `normal`. Adopt `H` and the transfer test when an item genuinely needs situated context.
- **`--orphaned` filtering.** Flagging items whose creating session has gone stale needs access to session-record timestamps. Skip it if the harness doesn't expose them.
- **Companion shortcuts.** A fast-add helper and a post-fork claim helper are conveniences that route into the core verbs; the core works without them.

**What breaks if you take *only* a piece:** thread-scoped `list` is meaningless without session-id discovery (it collapses to `--all`). Verify-driven triage in `tend` is inert without the relevant checkers. Neither breaks capture or resolution — those need nothing but the file.

## Provider notes

Everything above is harness-neutral. The mechanics below are where a specific agent harness plugs in; another harness swaps them without touching the model.

**Storage.** One markdown file per project, kept in the agent harness's per-user configuration area, with a sibling archive file for pruned items. The filename is a *project slug* derived deterministically so every session for the same project resolves to the same file: take the repository's common directory (so multiple worktrees of one repo share a file) or fall back to the working directory, then normalize it into a filename-safe token. Empty section headers (Open / Resolved / Abandoned) are kept present even when a section is empty, so the file shape is stable.

**Working-session identity (Claude Code).** Each item carries a *lineage* — a list of session identifiers describing which conversation(s) it belongs to. The skill discovers the current session id from the harness's session records (the most-recently-active record for this project) and caches it for the invocation. When a conversation was branched or forked from a parent, the harness also exposes the parent's id; that link is what `claim` uses to let a new branch inherit the parent's open items. The default `list` shows only items whose lineage includes the current session, so a long-lived project file doesn't drown each conversation in unrelated tickets.

**Other harnesses (e.g. Codex or any without a session concept).** If the harness has no notion of a per-conversation session id, run without lineage scoping: the file becomes a single shared list, `list` shows everything open, and `claim` / `--orphaned` are simply unused. Storage maps to whatever per-user configuration area that harness provides.

**Concurrent writes.** If the configuration area is synced across machines (cloud drive, etc.), two sessions writing the file at once is a known, accepted hazard — the design intentionally adds no locking, favoring thinness. Keep writes small and prefer one mutation per invocation.

## Out of scope

By design, this system does **not** include: a parsing/validation program (markdown handled directly by the agent is the approach), a third "medium" fidelity lane, priority-only or fidelity-only single-axis models, automated escalation or notification for `blocking` items, cross-project aggregate views, session-start auto-surfacing, integration with a host task-list feature, or any bulk backfill of old items (per-item `enrich` is the only upgrade path).
