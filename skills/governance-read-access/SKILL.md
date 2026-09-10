---
name: governance-read-access
version: 0.1
description: Read Decision Records, deferral tickets, and deferral companion artifacts across Claude, Codex, and Gemini with projection-and-range discipline. Use when a lane needs governance context or when a non-owning provider must propose, but never directly apply, a governance mutation.
argument-hint: "dr <slug> [--project <root>] | deferrals [--root <path>] [--project-key <slug>] <list|digest|check> | ticket <ddf_id> [--root <path>] --project-key <slug>"
---

# Governance Read Access

## Prerequisites

This skill is an adapter for an existing governance installation. Decision Record
projection requires the separately installed `decisions/scripts/state.sh`; it is
not bundled in this suite. Script-backed deferral reads require this suite's
`deferrals` CLI. Resolve `<installed-deferrals-dir>` to the deferrals skill folder
for your provider; its default shared record store is `~/.claude/deferrals/`
unless `DEFERRALS_ROOT` is configured or `--root` is supplied. Resolve
`<deferrals-root>` to that selected data directory before reading ticket paths. Mutation
routing requires a separately configured governance applier. If a required component is unavailable, report the
missing dependency and stop that operation; a missing guard is not permission to
read an entire index or mutate governance directly.

[SHARED]
Provide cross-provider read parity for Decision Records (DRs), deferral tickets, and
deferral companion artifacts. Within this adapter, Codex and Gemini are read/proposal-only:
they emit request artifacts, and the configured governance applier validates and applies them.

## Read a Decision Record

1. Project it before reading any prose:

   ```bash
   bash ~/.claude/skills/decisions/scripts/state.sh <slug> [--project <root>]
   ```

2. Use the decision-file path printed in the projection header and select the smallest
   relevant region from the emitted `line=N` anchors.
[/SHARED]

[PROVIDER:CODEX]
3. Read only that range:

   ```bash
   sed -n 'M,Np' <decision-file>
   ```
[/PROVIDER:CODEX]

[PROVIDER:CLAUDE]
3. Read only that range with `Read(offset=M, limit=<count>)`.
[/PROVIDER:CLAUDE]
[PROVIDER:GEMINI]
3. Read only that range with the host's ranged-file primitive, or with:

   ```bash
   sed -n 'M,Np' <decision-file>
   ```
[/PROVIDER:GEMINI]

[SHARED]
Never read a `decision-*.md` whole. The read path is always projection, then ranged read.

## Read Deferrals

Use only the read verbs of the installed script:

```bash
python3 <installed-deferrals-dir>/scripts/deferrals.py [--root <path>] [--project-key <slug>] list [--all-projects|--thread <id>|--inactive]
python3 <installed-deferrals-dir>/scripts/deferrals.py [--root <path>] [--project-key <slug>] digest
python3 <installed-deferrals-dir>/scripts/deferrals.py [--root <path>] [--project-key <slug>] check
```

For one ticket body:

1. Locate its top-level anchor with
   `grep -nF '**<ddf_id>**' <deferrals-root>/<project-key>.md`.
2. Read a small forward slice (for example 40 lines) with the provider's ranged-read
   primitive; extend only until the next top-level ticket header.
3. If the entry points to `<deferrals-root>/<ddf_id>-<slug>.md`, read that
   companion freely; companion files are plain prose.

Never `cat` or broadly grep an entire governance index when a projection, script view,
or ranged read serves.
[/SHARED]

[SHARED]
## Governance Update Request Vocabulary

A governance proposal uses one Markdown file per proposed mutation with this schema:

```yaml
request_type: GOVERNANCE_UPDATE_REQUEST
target_system: decisions | deferrals
target_record: <DR slug/id or ddf_id>
target_anchor: <DR decision/section or deferral field/status; none if record-wide>
target_scope: "<--project /absolute/root or --project-key slug>"
requested_verb: <exact target-system verb; include arguments when they encode the change>
requesting_lane_id: <lane id>
change_confidence: high | medium | low
rationale: <why the current evidence warrants the change>
exact_payload_text: |
  <verbatim text to add or apply; empty only when the verb fully encodes the change>
evidence_pointers:
  - </absolute/file:line>
```

Use the target system's live vocabulary; do not invent aliases. Examples include
`requested_verb: "add-ref"` for a DR and
`requested_verb: "rate ddf_12345678 --confidence 4"` for a deferral. The
configured receiver revalidates the verb and scope against the installed target.

A request is a proposal, never a commitment.
[/SHARED]

[PROVIDER:CODEX]
## Codex Boundary: Read Only

Claude uses `dr_gate` and transcript-guard hooks plus the script-only deferrals
contract. Codex has no equivalent enforcement; these instructions are the only
guardrail. Treat every write-shaped urge as out of bounds.

HARD RULE: never mutate a governance record from Codex. This includes:

- no DR edits, index/archive edits, companion edits, or Decision Record write verbs;
- no `deferrals.py` mutation verbs, including `add`, `edit`, `rate`, `claim`,
  `transition`, or `forget`;
- no direct “safe,” mechanical, cleanup, migration, or repair write.

The only permitted write is a proposal artifact in the lane's own run/output folder.
It is not a governance write.

## Emit a Governance Update Request

When evidence warrants a mutation, write one request per mutation as
`GOVERNANCE_UPDATE_REQUEST-<n>.md` in the lane's assigned run/output folder. Never
write it inside a provider configuration directory or governance source/store. Report its absolute
path to the dispatching conductor in the lane result. Do not report the governance
record as changed until the Claude-side applier confirms application.
[/PROVIDER:CODEX]

[PROVIDER:GEMINI]
## Gemini Boundary: Read and Propose Only

Gemini has no mutation authority under this adapter. Never edit a DR, deferral index,
archive, or companion directly, and never invoke a deferrals mutation, migration,
reconciliation, repair, or deletion verb. Missing enforcement tooling is not permission.

When evidence warrants a change, write one `GOVERNANCE_UPDATE_REQUEST-<n>.md` in the
lane's assigned run/output folder using the shared schema above. Do not place proposals
inside a governance store. Report the absolute proposal path to the conductor and treat
the target as unchanged until the configured applier confirms it. The applier may accept,
reject, or narrow the request according to its own current contract; this adapter does not
pre-authorize application.
[/PROVIDER:GEMINI]

[PROVIDER:CLAUDE]
## Route Governance Requests

Claude-side enforcement and the existing `/decisions` and `/deferrals` skills remain
authoritative; do not duplicate their mutation workflows here.

When the dispatching conductor receives the reported path to
`GOVERNANCE_UPDATE_REQUEST-<n>.md`:

1. Validate the target, `target_scope`, live verb vocabulary, exact payload, every
   `file:line` evidence pointer, lane identity, and confidence.
2. Re-read current state through `state.sh` or `deferrals.py list` before applying.
3. Dispatch the configured governance applier with the request-file path and instruct it to
   map `target_system` → target family, `target_record` → record,
   `exact_payload_text` → content, and `target_anchor` → anchors. That agent applies
   only operations inside its current contract and verifies the result.
4. Escalate operations it hard-excludes, including DR `flip`, new-DR authoring,
   deferral `tend`, and deferral `forget`; never widen the request silently.
5. Return `applied`, `blocked`, or `rejected`, the reason, verification evidence,
   and the record path when the target resolved.

If the applier performs an independently governed follow-up, report that verified action
separately from the requested mutation.
[/PROVIDER:CLAUDE]


[PROVIDER:CODEX]
This skill supersedes older direct-governance-write guidance when adopted for a
Codex lane. Governance changes remain proposals for the configured applier.
[/PROVIDER:CODEX]

[PROVIDER:GEMINI]
This skill supersedes older direct-governance-write guidance when adopted for a Gemini
lane. Governance changes remain proposals for the configured applier.
[/PROVIDER:GEMINI]
