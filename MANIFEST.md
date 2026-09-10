# Release Manifest

## Release Identity

| Field | Value |
|---|---|
| Release | Shared Skills |
| Version | 0.1.0 |
| Date | 2026-07-06 |
| License | PolyForm Noncommercial 1.0.0 - source-available (see `LICENSE.md`) |
| Scope | Eight-skill provider-neutral suite: `accomplishment-archive`, `auto-evals`, `completeness-map`, `deferrals`, `governance-read-access`, `orchestrator-posture`, `orthogonal-audit-review`, and `root-cause`. |

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
| `INSTALL-PROOF.md` | shipped | Historical dry-run record and current standalone regression command. |
| `install.sh` | shipped | Standalone installer for provider skill directories and installed metadata. |
| `publish-skill.py` | shipped | Provider renderer for generated `SKILL.md` artifacts. |
| `lib/provider_blocks.py` | shipped | Provider-block renderer support. |
| `tests/test_install.py` | shipped | Standard-library installer regression across every bundled skill and three providers. |

## Public Docs

| Path | Status | Purpose |
|---|---|---|
| `docs/accomplishment-archive.md` | shipped | Verified archive workflow and lite-mode boundary. |
| `docs/README-suite.md` | shipped | Suite map and partial-adoption guide. |
| `docs/auto-evals.md` | shipped | Auto-evals doctrine reference. |
| `docs/completeness-map.md` | shipped | Completeness-map doctrine reference. |
| `docs/deferrals.md` | shipped | Deferrals doctrine reference. |
| `docs/governance-read-access.md` | shipped | Bounded governance reads and proposal-only mutation boundary. |
| `docs/orchestrator-posture.md` | shipped | Context-cost routing, lead acceptance, and instrumentation boundary. |
| `docs/orthogonal-audit-review.md` | shipped | Orthogonal audit doctrine reference. |
| `docs/root-cause.md` | shipped | Root-cause doctrine reference. |

## Skill Source Inventory

| Path | Status | Purpose |
|---|---|---|
| `skills/accomplishment-archive/SKILL.md` | shipped | Canonical `accomplishment-archive` skill source (v1.5.1). |
| `skills/accomplishment-archive/VERSION.json` | shipped | Version metadata and content hash. |
| `skills/auto-evals/SKILL.md` | shipped | Canonical `auto-evals` skill source. |
| `skills/auto-evals/REFRESH.md` | shipped | Recovery and refresh sidecar. |
| `skills/auto-evals/VERSION.json` | shipped | Version metadata and content hash. |
| `skills/auto-evals/references/dr_sources_v2_2.md` | shipped | Decision-source reference for current eval doctrine. |
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
| `skills/deferrals/SKILL.md` | shipped | Canonical `deferrals` skill source (v0.5.3). |
| `skills/deferrals/REFRESH.md` | shipped | Recovery and refresh sidecar. |
| `skills/deferrals/VERSION.json` | shipped | Version metadata and content hash. |
| `skills/deferrals/references/lane-model.md` | shipped | Deferral lane-model reference. |
| `skills/deferrals/references/v04-spec.md` | shipped | Script-backed record grammar and transaction contract. |
| `skills/deferrals/scripts/deferrals.py` | shipped | Authoritative Python-stdlib deferral CLI; root precedence is `--root`, `DEFERRALS_ROOT`, then the established `~/.claude/deferrals`. |
| `skills/deferrals/scripts/deferrals_digest.sh` | shipped | Optional session-start digest hook command. |
| `skills/deferrals/scripts/install.sh` | shipped | Explicit optional digest-integration installer. |
| `skills/deferrals/scripts/status.sh` | shipped | Optional digest-integration status check. |
| `skills/deferrals/scripts/uninstall.sh` | shipped | Optional digest-integration removal. |
| `skills/governance-read-access/SKILL.md` | shipped | Canonical `governance-read-access` skill source (v0.1). |
| `skills/governance-read-access/VERSION.json` | shipped | Version metadata and content hash. |
| `skills/orchestrator-posture/SKILL.md` | shipped | Canonical `orchestrator-posture` skill source (v0.4). |
| `skills/orchestrator-posture/VERSION.json` | shipped | Version metadata and content hash. |
| `skills/orchestrator-posture/references/stance.md` | shipped | Provider-rendered lead-agent stance template. |
| `skills/orchestrator-posture/scripts/posture_run.py` | shipped | Optional descriptive run recorder and review/check CLI. |
| `skills/orchestrator-posture/scripts/install.sh` | shipped | Explicit optional provider-integration installer. |
| `skills/orchestrator-posture/scripts/status.sh` | shipped | Optional integration status check. |
| `skills/orchestrator-posture/scripts/uninstall.sh` | shipped | Optional integration removal. |
| `skills/orchestrator-posture/scripts/_settings_hook.py` | shipped | Settings update helper for the optional integration. |
| `skills/orchestrator-posture/scripts/fixtures/` | shipped | Twenty-seven non-private labeled fixtures for recorder self-checks. |
| `skills/orthogonal-audit-review/SKILL.md` | shipped | Canonical `orthogonal-audit-review` skill source. |
| `skills/orthogonal-audit-review/REFRESH.md` | shipped | Recovery and refresh sidecar. |
| `skills/orthogonal-audit-review/VERSION.json` | shipped | Version metadata and content hash. |
| `skills/orthogonal-audit-review/references/cognitive_parallax.md` | shipped | Cognitive parallax reference. |
| `skills/root-cause/SKILL.md` | shipped | Canonical `root-cause` skill source. |
| `skills/root-cause/VERSION.json` | shipped | Version metadata and content hash. |
| `skills/*/_archive/` | shipped | Source version history; retained in the repository and excluded from provider targets. |

## Not Shipped Here

- The `/dib` skill and optional substrate. Install those from the companion DIB
  System repository.
- Provider runtime directories. `install.sh` writes to provider skill
  directories only when the target already exists or the user passes
  `--create-provider=<name>`.
- Source `REFRESH.md` files and `_archive/` histories are retained in this
  repository but excluded from provider targets.
- The decisions projection tool and authorized governance updater required by
  optional `governance-read-access` operations.
- Automatic installation of the optional `orchestrator-posture` provider hook;
  its own explicit installer controls that integration.
- A background service, daemon, or automatically registered provider hook. The
  installed packages can include support scripts, but the main installer does
  not execute or register them.

## Integrity Notes

- Release files are source-available, not OSI-approved "open source."
- Internal relative Markdown links are expected to resolve within this repo.
- Installed `SKILL.md` records canonical-source provenance; installed
  `VERSION.json` hashes the rendered artifact beside it. `INSTALL-PROOF.md`
  separates its historical dry-run from the current `python3
  tests/test_install.py` regression check; run `./install.sh --dry-run` in your
  own environment before installing.
