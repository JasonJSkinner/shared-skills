# Release Notes - v0.1.0

**Release:** Shared Skills

**Date:** 2026-07-06

**Suite update:** 2026-09-09

The v0.1.0 publication established the Shared Skills repository. As of the
suite update above, it ships eight provider-neutral skills that can be installed
independently of the DIB System substrate.

## What Ships

| Component | What it is |
|---|---|
| `accomplishment-archive` | Verified archival of completed artifacts, with full and curated lite modes. |
| `auto-evals` | Eval/scenario package doctrine with verifier separation, holdout discipline, walkthrough mode, and structured repair handoff. |
| `completeness-map` | Completion-boundary expansion into a derived implication map. |
| `deferrals` | v0.5.3 script-backed postponed-work tickets with stable ids, atomic transactions, integrity checks, and guarded repair. |
| `governance-read-access` | Projection-and-range reads for decisions and deferrals, with proposal-only mutation routing. |
| `orchestrator-posture` | Context-cost routing, independent verification, lead-owned acceptance, and optional descriptive run instrumentation. |
| `orthogonal-audit-review` | Cognitive-parallax audit doctrine for non-trivial work products. |
| `root-cause` | Systemic root-cause workflow for verified issue-family diagnosis and blast-radius analysis. |
| Standalone installer | `install.sh`, publishing provider-specific skill artifacts with `publish-skill.py`, deriving installed metadata, and copying supporting assets. |
| Public docs | Suite overview and one public doc per skill under `docs/`. |

## Split-Repo Scope

The DIB authoring skill is not included here. It ships in the companion DIB
System repository with the optional substrate. These shared skills remain useful
without that repo when supplied with any equivalent governing artifact, symptom
set, or review target.

## License and Usage

Licensed under the PolyForm Noncommercial License 1.0.0. This project is
**source-available / public-source**, not OSI-approved "open source."
Noncommercial use is permitted under the license; commercial use requires a
separate written commercial license. See `LICENSE.md`.

## Patent Caveat

Public disclosure may affect future patent rights, especially outside the U.S.
This publication is a reputation and adoption choice, not a patent-preservation
strategy. Final license and patent language should be reviewed by IP counsel.

## Honest Scope

- This release ships the shared skills, docs, publisher, support library, and
  standalone installer.
- Provider integration notes are intentionally generic; invocation mechanics
  still depend on the host agent platform.
- The install proof is a recorded dry-run, not a live install on your machine.
- Generated `SKILL.md` retains canonical-source provenance, while installed
  `VERSION.json` hashes the rendered artifact and preserves its other source
  metadata. Metadata writes are atomic, unchanged installs preserve bytes and
  modification times, and `REFRESH.md` remains source-only.
- The current standalone regression command is `python3 tests/test_install.py`.
- Final 2026-09-09 verification passed 24 skill/provider installs, three
  malformed-support-tag negative cases, all three provider payload checks, five
  checked-in deferrals regressions, all 27 orchestrator fixtures with no private
  pilot fixtures, shell syntax checks, and `git diff --check`.
- Separately, 22 isolated upstream deferrals tests passed during source sync;
  those are additional validation, not tests shipped in this repository.
- Decision projection and governance-update application used by
  `governance-read-access` remain explicit external prerequisites; their absence
  stops that operation. The bundled deferrals CLI covers deferral reads.
- The core deferrals CLI is Python-standard-library-only on macOS/Linux and uses
  POSIX `fcntl`; its optional Claude digest integration requires Bash and `jq`.
- `orchestrator-posture` does not install a provider hook during the main suite
  install. Its optional provider integration has a separate, explicit installer;
  its current self-check covers 27 labeled fixtures, and isolated source-sync
  verification exercised hook installation, status, and removal.
- The suite includes script-backed support tools where the skill requires them.
  The main installer copies those tools but does not execute skill-local
  installers, register provider hooks, or start background services.
