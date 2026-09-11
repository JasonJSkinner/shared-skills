# Release Manifest

## Release Identity

| Field | Value |
|---|---|
| Release | Shared Skills |
| Version | 0.1.0 |
| Date | 2026-07-06 |
| License | PolyForm Noncommercial 1.0.0 - source-available (see `LICENSE.md`) |
| Scope | Installable provider-neutral skill suite: `auto-evals`, `completeness-map`, `deferrals`, `orthogonal-audit-review`, and `root-cause`. |

This manifest inventories this repository only. The DIB authoring skill and
optional substrate ship in the companion DIB System repository.

## Root Surfaces

| Path | Status | Purpose |
|---|---|---|
| `README.md` | shipped | Repo front door and install orientation. |
| `LICENSE.md` | shipped | Source-available license terms and commercial-use reservation. |
| `RELEASE-NOTES.md` | shipped | v0.1.0 release notes. |
| `KNOWN-LIMITATIONS.md` | shipped | Known release boundaries. |
| `MANIFEST.md` | shipped | This inventory. |
| `INSTALL-PROOF.md` | shipped | Recorded installer dry-run result. |
| `install.sh` | shipped | Standalone installer for provider skill directories. |
| `publish-skill.py` | shipped | Provider renderer for generated `SKILL.md` artifacts. |
| `lib/provider_blocks.py` | shipped | Provider-block renderer support. |

## Public Docs

| Path | Status | Purpose |
|---|---|---|
| `docs/README-suite.md` | shipped | Suite map and partial-adoption guide. |
| `docs/auto-evals.md` | shipped | Auto-evals doctrine reference. |
| `docs/completeness-map.md` | shipped | Completeness-map doctrine reference. |
| `docs/deferrals.md` | shipped | Deferrals doctrine reference. |
| `docs/orthogonal-audit-review.md` | shipped | Orthogonal audit doctrine reference. |
| `docs/root-cause.md` | shipped | Root-cause doctrine reference. |

## Skill Source Inventory

| Path | Status | Purpose |
|---|---|---|
| `skills/auto-evals/SKILL.md` | shipped | Canonical `auto-evals` skill source. |
| `skills/auto-evals/REFRESH.md` | shipped | Recovery and refresh sidecar. |
| `skills/auto-evals/VERSION.json` | shipped | Version metadata and content hash. |
| `skills/auto-evals/references/playbook_v1_3.md` | shipped | Auto-evals playbook reference. |
| `skills/auto-evals/references/principles_v1_3.md` | shipped | Auto-evals principles reference. |
| `skills/auto-evals/references/walkthrough_mode_phase_a_e_reference.md` | shipped | Walkthrough reference. |
| `skills/auto-evals/references/walkthrough_v2_0.md` | shipped | Walkthrough mode reference. |
| `skills/auto-evals/references/lane-templates/README.md` | shipped | Lane template orientation. |
| `skills/auto-evals/references/lane-templates/lane-1a-scenario-design-template.md` | shipped | Scenario-design lane template. |
| `skills/auto-evals/references/lane-templates/lane-1b-walkthrough-template.md` | shipped | Walkthrough lane template. |
| `skills/auto-evals/references/lane-templates/lane-2-downward-template.md` | shipped | Downward-trace lane template. |
| `skills/auto-evals/references/lane-templates/lane-3-upward-template.md` | shipped | Upward-trace lane template. |
| `skills/auto-evals/references/lane-templates/phase-c-meta-synthesis-template.md` | shipped | Meta-synthesis lane template. |
| `skills/completeness-map/SKILL.md` | shipped | Canonical `completeness-map` skill source. |
| `skills/completeness-map/REFRESH.md` | shipped | Recovery and refresh sidecar. |
| `skills/completeness-map/VERSION.json` | shipped | Version metadata and content hash. |
| `skills/completeness-map/references/anti-patterns.md` | shipped | Completeness anti-pattern reference. |
| `skills/completeness-map/references/eligibility.md` | shipped | Eligibility reference. |
| `skills/completeness-map/references/enums.md` | shipped | Enum reference. |
| `skills/completeness-map/references/nested-handling.md` | shipped | Nested-artifact handling reference. |
| `skills/completeness-map/references/schema.md` | shipped | Schema reference. |
| `skills/completeness-map/templates/completeness-map-template.md` | shipped | Map template. |
| `skills/deferrals/SKILL.md` | shipped | Canonical `deferrals` skill source. |
| `skills/deferrals/REFRESH.md` | shipped | Recovery and refresh sidecar. |
| `skills/deferrals/VERSION.json` | shipped | Version metadata and content hash. |
| `skills/deferrals/references/lane-model.md` | shipped | Deferral lane-model reference. |
| `skills/orthogonal-audit-review/SKILL.md` | shipped | Canonical `orthogonal-audit-review` skill source. |
| `skills/orthogonal-audit-review/REFRESH.md` | shipped | Recovery and refresh sidecar. |
| `skills/orthogonal-audit-review/VERSION.json` | shipped | Version metadata and content hash. |
| `skills/orthogonal-audit-review/references/cognitive_parallax.md` | shipped | Cognitive parallax reference. |
| `skills/root-cause/SKILL.md` | shipped | Canonical `root-cause` skill source. |
| `skills/root-cause/VERSION.json` | shipped | Version metadata and content hash. |

## Not Shipped Here

- The `/dib` skill and optional substrate. Install those from the companion DIB
  System repository.
- Provider runtime directories. `install.sh` writes to provider skill
  directories only when the target already exists or the user passes
  `--create-provider=<name>`.
- A background service, daemon, or provider settings hook. The installed skills
  are generated Markdown artifacts plus supporting assets.

## Integrity Notes

- Release files are source-available, not OSI-approved "open source."
- Internal relative Markdown links are expected to resolve within this repo.
- Installer behavior is previewed in `INSTALL-PROOF.md`; run `./install.sh
  --dry-run` in your own environment before installing.
