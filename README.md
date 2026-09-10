# Shared Skills

This repository ships eight provider-neutral skills for intent-driven agent
work: `accomplishment-archive`, `auto-evals`, `completeness-map`, `deferrals`,
`governance-read-access`, `orchestrator-posture`, `orthogonal-audit-review`, and
`root-cause`.

Installable source lives in `skills/<name>/`; public explanatory docs live in
`docs/`. Core doctrine is vendor-independent, with provider-specific mechanics
kept in provider notes. Some optional operations declare external prerequisites
rather than silently substituting another workflow.

The DIB authoring skill is **not** in this repo. It ships in the companion
`dib-system` repository with the optional substrate and `/dib` lifecycle tools.
These shared skills can still read a DIB or any equivalent governing artifact as
input when a workflow needs design intent.

## The Skills

| Skill | Purpose |
|---|---|
| `accomplishment-archive` | Preserves a completed artifact as a human-readable report plus a verified copy, with a curated lite mode for large programs. |
| `completeness-map` | Expands a governing artifact's completion boundary into a derived implication map: consumers, surfaces, done-state, implied layers, anti-shortcuts, scope, and open questions. |
| `auto-evals` | Builds an eval/scenario package from governing intent, runs verification from the outside in, and hands failures to structured repair. |
| `root-cause` | Classifies discrepancies as reusable issue families with code-path verification and blast-radius analysis before repair. |
| `deferrals` | Captures "revisit later" work in durable, transferable tickets so deferred work survives new sessions or branched work. |
| `governance-read-access` | Reads decisions and deferrals with projection-and-range discipline and routes write requests without direct governance mutation. |
| `orchestrator-posture` | Gives a lead agent a context-cost routing rule, independent verification, and a lead-owned delivery gate for multi-part work. |
| `orthogonal-audit-review` | Reviews non-trivial work products from genuinely different stances, then keeps only findings whose evidence is re-verified. |

## Install

Inspect first:

```bash
./install.sh --dry-run
```

The installer publishes each skill's `SKILL.md` through `publish-skill.py` for
each opted-in provider, provider-renders tagged Markdown support files, copies
other supporting assets, and atomically writes the matching installed
`VERSION.json`. No manual metadata repair is required. `REFRESH.md` remains
source-only, and source archives are not installed into provider targets.
The main installer copies skill-local integration scripts but never executes
them or registers provider hooks; those optional integrations require an
explicit invocation of the relevant skill's installer.

Installation is additive: excluded or removed source entries are not copied,
but the installer does not delete files already present in a provider target.

Provider directories are opt-in by existence:

| Provider | Default target |
|---|---|
| Claude | `$HOME/.claude/skills` |
| Codex | `$HOME/.codex/skills` |
| Gemini | `$HOME/.gemini/skills` |

If a provider target does not exist, it is skipped unless you pass
`--create-provider=<name>`. For sandboxed testing, `--target=<dir>` uses
`<dir>/<provider>` as the provider target.

Useful flags:

| Flag | Meaning |
|---|---|
| `--dry-run` | Print every action; write nothing. |
| `--create-provider=<name>` | Create and install to a missing provider target (`claude`, `codex`, or `gemini`). |
| `--target=<dir>` | Use a sandbox base where provider targets become `<dir>/<provider>`. |

Installed skills intentionally carry two different hashes. The
`Source version/hash:` line in generated `SKILL.md` identifies its canonical
source `SKILL.md`; `VERSION.json` preserves the source version metadata while
its `content_hash_sha256` hashes the rendered, installed `SKILL.md` beside it.
An unchanged re-install preserves installed bytes and modification times.

Run the standalone installer regression check with:

```bash
python3 tests/test_install.py
```

## Partial Adoption

Install the suite and invoke only the skill you need, using the
installer-generated provider output. Each skill is selectively adoptable within
the prerequisites it declares. Natural companion edges are not hidden
requirements: `auto-evals` can run without `root-cause` and manually populate
its repair handoff, while `root-cause` can be used on ordinary bug families
without any eval package.

## Docs

Start with `docs/README-suite.md` for the suite map, then read the skill doc you
need:

| Doc | Covers |
|---|---|
| `docs/accomplishment-archive.md` | Verified full and lite archives of completed work. |
| `docs/auto-evals.md` | Eval package doctrine, verifier separation, walkthrough mode, and repair handoff. |
| `docs/completeness-map.md` | Completion-boundary derivation and the implication-map schema. |
| `docs/deferrals.md` | Durable deferred-work tickets and the transfer test. |
| `docs/governance-read-access.md` | Bounded governance reads and proposal-only mutation handoff. |
| `docs/orchestrator-posture.md` | Context-cost routing, delivery ownership, and optional run instrumentation. |
| `docs/orthogonal-audit-review.md` | Cognitive parallax review doctrine. |
| `docs/root-cause.md` | Systemic root-cause workflow, taxonomy, and output contract. |

## License

This project is **source-available / public-source** under the PolyForm
Noncommercial License 1.0.0, **not** OSI-approved "open source." Noncommercial
use is permitted under the license. Commercial use requires a separate written
commercial license. See `LICENSE.md`.
