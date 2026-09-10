# Governance Read Access

`governance-read-access` provides a bounded way to inspect Decision Records,
deferral indexes, and deferral companion artifacts without loading whole
governance corpora or silently mutating authoritative records.

## When To Use

Use it when an execution or review lane needs durable decision context, a
deferral summary, or one ticket body. It is also the handoff contract for a
provider that may propose a governance change but may not apply it directly.

## Read Discipline

Decision Records are read in two stages:

1. Run the separately installed decisions `scripts/state.sh <slug>` projection
   command to obtain its operative summary and line anchors.
2. Read only the smallest anchored range needed for the task.

Deferral indexes use the read verbs of the CLI bundled with the installed
`deferrals` skill:

```bash
python3 <installed-deferrals-dir>/scripts/deferrals.py [--root <path>] [--project-key <slug>] list [--all-projects|--thread <id>|--inactive]
python3 <installed-deferrals-dir>/scripts/deferrals.py [--root <path>] [--project-key <slug>] digest
python3 <installed-deferrals-dir>/scripts/deferrals.py [--root <path>] [--project-key <slug>] check
```

One ticket is located by its stable identifier and read as a bounded slice;
plain companion prose may then be read directly. If the decisions projection
tool or deferrals CLI is absent, stop that read rather than bypassing it with a
broad file read.

Provider installations use their own installed CLI path. Record-root precedence
is explicit `--root`, then `DEFERRALS_ROOT`, then the established shared default
`~/.claude/deferrals`. Preserving that home-relative default keeps existing
records visible across providers after migration. Set one of the first two only
for an intentional alternate store; do not infer a data root from the CLI
location.

This projection-and-range pattern keeps unrelated governance context out of the
working window and reduces the chance of acting on a stale or misidentified
record.

## Mutation Boundary

Read-only providers do not edit governance records or invoke mutation verbs.
When evidence warrants a change, they emit a structured governance update
request in their assigned output area. The request names the target, exact verb
and payload, scope, rationale, confidence, and evidence pointers.

An authorized governance tool re-reads current state, validates the request
against the live vocabulary and scope, and then applies, blocks, or rejects it.
A proposal is never reported as an applied change.

## Partial Adoption

Deferral reads work with the bundled CLI alone. Decision reads additionally
require the separate projection tool. The update-request route is needed only
when a read-only lane discovers a warranted mutation, and applying that request
requires the separately configured authorized updater.

## Provider Notes

Providers may use different ranged-read primitives and enforcement mechanisms.
The invariant is the same: targeted reads first, and no direct governance write
from a lane whose contract is read-only.
