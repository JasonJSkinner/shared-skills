# Orchestrator Posture

`orchestrator-posture` is a lead-agent stance for multi-part work. The lead owns
the delivered outcome and routes each piece by its expected cost to the lead's
working context, rather than delegating by task category alone.

**Status:** version 0.4 is benchmark-informed and instrumented, but its intended
benefit on multi-wave programs is not yet validated.

## When To Use

Use it for work with enough independent pieces, waves, or verification needs
that routing can protect the lead's context. A single bounded deliverable may be
cheaper to build directly and verify independently.

## Core Rules

1. Compare direct context cost with the full delegation cost: brief, return,
   wake-up, and evidence read-back.
2. Re-estimate at checkpoints; routing is not permanent.
3. Use an independent verifier with a different model identity, fresh context,
   and no builder completion narrative.
4. Treat a lane's “done” as input to the delivery gate, not as delivery itself.
   The lead runs the final acceptance check.
5. Re-dispatch or escalate failed work unless a bounded direct repair is first
   scoped and cost-estimated.

## Modes

| Mode | Purpose |
|---|---|
| `apply` | Adopt the stance and run the lead duties for a multi-part task. |
| `review` | Summarize eligible recorded runs and surface recurring observations for investigation. |
| `check` | Self-test the optional recorder against labeled fixtures. |

## Instrumentation Boundary

The optional recorder describes what a run did; it does not score the run or
infer causes from counts. Missing evidence remains unknown, estimates are
recorded before dispatch, and observed, proxy, manual, and unknown values stay
distinguishable. Recurrence can stage an investigation, but cannot automatically
rewrite the stance.

The bundled `check` mode currently exercises 27 labeled fixtures. Source-sync
verification also exercised the optional hook install, status, and removal path
inside an isolated sandbox; the main suite installer still does not activate
that integration. The recorder uses Python 3 and POSIX `fcntl`, so its supported
platforms are macOS and Linux; the optional integration wrappers use Bash.

## Partial Adoption

The routing rule, independent-verifier invariant, and lead-owned delivery gate
stand on their own. Run recording is optional and may require provider-specific
hooks or explicit commands.

## Provider Notes

Dispatch, transcript capture, hooks, and model selection are platform-specific.
Platforms without automatic collection can use explicit lifecycle commands or
apply the stance without instrumentation.
