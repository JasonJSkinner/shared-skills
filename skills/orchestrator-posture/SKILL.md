---
name: orchestrator-posture
description: "Lead-agent stance for a Fable 5.1 (or Opus-high) session running a multi-part task: the lead owns the outcome and routes each piece of work by its cost to the lead's own context (act directly when cheaper; a subagent when its brief and return hide more than they expose; a sub-orchestrator to absorb many dispatches), chooses model/provider/effort per task, dispatches independent verifiers, and does the final acceptance pass itself. Use on '/orchestrator-posture', 'act as lead orchestrator', 'orchestrate this, don't build it', 'delegate and own the result', or when authoring a run prompt for a delegating Fable session. Modes: apply, review, check. v0.4 — benchmark-informed, not validated (see body)."
version: "0.4"
argument-hint: "[review|check] [--fable-points N] [--gpt-points M] [--run-dir PATH]"
---

# Orchestrator Posture (v0.4)

**Status (v0.4, 2026-09-09):** the stance text is unchanged from v0.3.1 except one
instrumentation sentence (`note` before dispatch, `accept` at the delivery gate); v0.4 adds instrumentation
so real runs produce evidence instead of impressions. `scripts/posture_run.py` is a
**descriptive recorder**, not a scorer: it records what a run did, tags every measured field with the
evidence behind it (`observed` | `proxy` | `manual` | `unknown`) — identity, completion
and collector metadata are untagged — and refuses to turn counts
into causes. The evaluation plan is to test on real multi-wave work
rather than a synthetic round two; the logging is part of this skill; `review` is a mode, not
a second skill. Astra's standing constraints, which the recorder enforces: missing evidence is
`unknown` and never zero; brief bytes / return bytes / wake-ups are three fields and are never
summed; the Stop collector never executes a manifest check command; estimates are recorded
before dispatch and append-only; coverage is reported beside accuracy. Still
benchmark-informed, not validated — the ledger is how that changes.

**Evidence limit:** benchmark-informed, not validated. A bounded pilot found that an earlier
category-first stance could lose deliverables on single-wave tasks and add lead-side overhead.
That motivated the applicability and delivery gates here. The intended multi-wave benefit and
the context-cost rule remain untested; treat the ledger as descriptive evidence, not validation.

## What this is

A stance block, a routing pointer, and three rules nobody else in the harness states.
Everything mechanical is a pointer:

[PROVIDER:CLAUDE]
- If your environment provides orchestration, dispatch-brief, model-routing, or long-run
  verification skills, use them for their mechanics. Otherwise apply the bounded fan-out,
  concise-brief, fresh-context verifier, and checkpoint rules in this skill directly.
[/PROVIDER:CLAUDE]
[PROVIDER:CODEX]
- Fan-out, brief discipline, and verifier gates have no slash-skill equivalents here:
  dispatch bounded work to child `codex exec` sessions and apply the moves inline.
[/PROVIDER:CODEX]
[PROVIDER:GEMINI]
- Use the host's available child-agent or isolated-session mechanism for bounded fan-out;
  when none exists, preserve the same role separation through separate file-backed phases.
[/PROVIDER:GEMINI]

The three rules original to this skill: (1) route by main-thread context cost, not task category; (2) the verifier is a different model identity in fresh context and never sees the builder's completion narrative; (3) a failed lane is re-dispatched or escalated unless a bounded direct repair is scoped and cost-estimated first (silent absorption is how the posture collapses).

## Modes

One skill, three modes. `apply` is the default when no mode word is given.

| mode | what it does | when |
|---|---|---|
| `apply` | Adopt or paste the stance (Procedure below) and run the conductor duties. | Starting or authoring a run. |
| `review` | `posture_run.py review` — a capped cross-run table plus recurrence counts, and on request a STAGED investigation draft (it writes the draft and the read-only Sol command; the conductor runs the lane, the owner ratifies). Eligible runs are those with `complete: true` and no `instrumentation-incomplete`; an eligible run without a given failure is a counterexample to it. | After a run, or when asking what the ledger shows. |
| `check` | `posture_run.py check` — self-test the recorder against labeled fixtures. | Before trusting a ledger line; after any edit to the scripts. |

Scripts live beside this installed skill under `scripts/`; resolve them relative to this
`SKILL.md`, not through a user-specific shared-source path.

Verb-level detail is in `scripts/posture_run.py --help` (and `--help` on each verb); this
file does not restate it. Data lives centrally in `~/.claude/state/orchestrator-posture/`
(sentinel per session, `runs.jsonl` one line per run, `investigations/`); per-run events live
in `<RUN_DIR>/.posture/events.jsonl`.

[PROVIDER:CODEX]
There is no Stop hook and no run-log capture skill here: the collector cannot run itself. Use the
verbs as plain CLI calls, and `--session <id>` is REQUIRED on every one of them: Codex has
no `$CLAUDE_CODE_SESSION_ID`, so `start` errors (exit 2) without it. Pass any stable run
identifier — `python3 scripts/posture_run.py start --session <id> --run-dir <RUN_DIR>
--objective-file <objective>`, then `note` / `accept`, then one explicit
`ledger --session <id> --transcript <log> --complete` at the end of the run, then `review`. Record in-flight misses in the run report instead of a learning log. Automatic
Stop-hook collection is Claude-only.

**The parser reads Claude Code transcript shape only.** Codex rollouts are NOT parsed: point
`--transcript` at one and every transcript-derived field comes back `unknown` with an
`instrumentation-incomplete` failure — which is the honest result, not a defect. Here the
recorder is useful for what you tell it: the manifest, `note` estimates and `accept` results.
[/PROVIDER:CODEX]
[PROVIDER:GEMINI]
There is no automatic Stop-hook collector for Gemini. Use the recorder as explicit CLI
instrumentation and pass `--session <id>` to every verb. Start with a stable run identifier,
record `note` before dispatch and `accept` at the delivery gate, then call
`ledger --session <id> --complete`. The parser understands Claude Code transcript shape
only, so omit `--transcript` unless the supplied file has that shape; unsupported streams
must remain `unknown`, never be treated as zero evidence.
[/PROVIDER:GEMINI]

## Procedure (mode `apply`)

1. Resolve the parameters: `<N>` Fable points, `<M>` GPT points (percentage points of the
   weekly buckets), `<RUN_DIR>`. Defaults when the owner gives none: N=20, M=20,
   RUN_DIR=cwd. Unattended run (no owner available)? Insert the unattended paragraph from
   `references/stance.md` just before the objective line.
2. Read `references/stance.md`, substitute the parameters, and place the block before
   the objective. When authoring a run prompt for another session, paste it verbatim;
   when applying to the current session, adopt it as your operating stance for the
   rest of the run.
3. Open the run: `posture_run.py start --run-dir <RUN_DIR> --objective-file <objective>`.
   One line of output; it preserves the ORIGINAL objective text so the manifest can later be
   reconciled against it rather than against the lead's own summary. **Run this BEFORE the
   first dispatch**: a session transcript holds everything the session ever did, including
   any abandoned branches[PROVIDER:CLAUDE] left behind by `/rewind`[/PROVIDER:CLAUDE], so `start` marks the byte boundary
   that scopes the run.
   Dispatches made before it fall outside the window and are reported as an
   `instrumentation-incomplete` gap, never back-dated into the counts.
4. Do what the block says: for multi-wave work invoke the fan-out posture, read the
   remaining provider allowance, and write `<RUN_DIR>/routing.md` only when its
   coordination value exceeds its context overhead; then dispatch.
5. At run end, close the run: `posture_run.py ledger --session <id> --complete`. Until this
   runs, every Stop collection is a checkpoint and no deliverable is reported lost; after it,
   the run stops collecting and the sentinel is retired at the next collector
   invocation after 1 h (every invocation sweeps all sentinels, so an idle session's
   sentinel retires too).
6. Then note (in `<RUN_DIR>/routing.md` if it exists, else in the run report) what the stance got wrong or missed. That
   note is the input to the next version.

### Conductor duties (the only additions in v0.4)

- **At decomposition:** write `<RUN_DIR>/DELIVERABLES.md` — one list line per required
  deliverable, `- \`path\` — check: \`command\``, optionally `baseline-sha256: <hex>` for an
  output that must CHANGE. The collector records the check command and inspects the path; it
  never runs the command.
- **Before each dispatch:** one `posture_run.py note` — decision id, route
  (`direct|subagent|suborch`), the context-cost estimate you are about to act on, and for a
  codex lane its `--lane-id`, `--model` and `--brief-file` (bytes + sha256 are captured then,
  because the transcript sees only a pointer). Estimates recorded afterwards are worthless.
- **At the delivery gate:** one `posture_run.py accept` per deliverable with the result of
  the check you actually ran. A lane's "done" is still not delivery.
- **Misses observed in flight** (the stance told you to do something and you did not, or it
  told you something unhelpful) → record a line in the run report immediately, not batched.
- `routing.md` stays conditional (v0.3.1 rule). Events go to `<RUN_DIR>/.posture/events.jsonl`
  regardless; do not create a routing artifact just to have one.

Context budget for the whole apparatus, honestly: reading this skill and `references/stance.md`
costs ≈220 lines before anything runs. Then the run costs 2 + D + A CLI calls — `start`
plus the closing `ledger --complete`, one `note` per delegation D, one `accept` per
deliverable A — plus R more if you record `--actual` costs, plus `review`, plus authoring
`DELIVERABLES.md` — and manifest and check-command authoring consume reasoning that their
final line count does not show. Stop-hook collection is the cheap part: zero output on the
ordinary path (exit 0, no stdout — verified against 1194 recorded `stop_hook_summary`
entries, all with `hookErrors: []` and `hasOutput: false`), bounded by a cooperative 8 s
deadline on the scan, event, manifest and lock steps; the hook's own hard timeout is 15 s. `review` = a table capped at 40 lines.

[PROVIDER:CLAUDE]
Install the collector once per machine: `bash scripts/install.sh` (idempotent; adds one Stop
hook; `status.sh` reports, `uninstall.sh` reverts and reports byte-identity against its
pre-install backup). The hook returns immediately for any session without a sentinel, so it
costs nothing outside an instrumented run.
[/PROVIDER:CLAUDE]

## Design principle (why the block is short)

For a frontier lead, keep only (a) harness facts the model cannot infer and (b) nudges
Anthropic measured as helping 5.1 (batch independent calls in one response; keep
working while subagents run). Cut anything the model already judges: an inline-grep
floor, a retry ladder, a brief-field checklist were all removed on that basis. Add a
line only with evidence from the benchmark.

## Known open questions (from the Astra review, unresolved by design)

- Does the posture pay off on multi-wave work? Untested; the pilot only covered
  single-wave tasks.
- Does the v0.3 cost rule reduce lead-visible delegation cost at equal delivery? Untested;
  the ledger records the three transport fields separately so a later comparison can be made
  on comparable runs — the ledger itself never asserts one.
- Whether the ceilings are hard limits or best-effort: manual readings cannot guarantee
  a cap. The block says best-effort with reserved headroom.
- Whether "different model identity" alone buys independence: the block adds fresh
  context and no completion narrative, which the review judged necessary.
- Sonnet/Opus tier prescriptions were dropped so the lead chooses; the benchmark should
  show whether the lead's choices beat a fixed table.
- **The ledger's own biggest risk** (Astra): a self-reported, incomplete ledger looks
  objective and turns measurement artifacts into standing guidance. That is why every field
  is evidence-tagged, coverage is reported beside accuracy, and a recurrence only ever
  stages an investigation for the owner — never an automatic stance edit.
