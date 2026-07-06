# Release Notes - v0.1.0

**Release:** Shared Skills  
**Date:** 2026-07-06

This is the initial public release of the Shared Skills repository: five
provider-neutral skills that can be installed independently of the DIB System
substrate.

## What Ships

| Component | What it is |
|---|---|
| `auto-evals` | Eval/scenario package doctrine with verifier separation, holdout discipline, walkthrough mode, and structured repair handoff. |
| `completeness-map` | Completion-boundary expansion into a derived implication map. |
| `deferrals` | Durable postponed-work tickets with stable ids and transferable context. |
| `orthogonal-audit-review` | Cognitive-parallax audit doctrine for non-trivial work products. |
| `root-cause` | Systemic root-cause workflow for verified issue-family diagnosis and blast-radius analysis. |
| Standalone installer | `install.sh`, publishing provider-specific skill artifacts with `publish-skill.py` and copying supporting assets. |
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
- The suite is doctrine-first. It does not install background services,
  provider settings hooks, or a task runner.
