# Shared Skills

This repository ships five provider-neutral skills for intent-driven agent work:
`auto-evals`, `completeness-map`, `deferrals`, `orthogonal-audit-review`, and
`root-cause`.

Each skill is a self-contained doctrine document. The installable source lives in
`skills/<name>/`; public explanatory docs live in `docs/`. The doctrine is
vendor-independent, with provider-specific mechanics kept in each skill's
provider notes.

The DIB authoring skill is **not** in this repo. It ships in the companion
`dib-system` repository with the optional substrate and `/dib` lifecycle tools.
These shared skills can still read a DIB or any equivalent governing artifact as
input when a workflow needs design intent.

## The Skills

| Skill | Purpose |
|---|---|
| `completeness-map` | Expands a governing artifact's completion boundary into a derived implication map: consumers, surfaces, done-state, implied layers, anti-shortcuts, scope, and open questions. |
| `auto-evals` | Builds an eval/scenario package from governing intent, runs verification from the outside in, and hands failures to structured repair. |
| `root-cause` | Classifies discrepancies as reusable issue families with code-path verification and blast-radius analysis before repair. |
| `deferrals` | Captures "revisit later" work in durable, transferable tickets so deferred work survives new sessions or branched work. |
| `orthogonal-audit-review` | Reviews non-trivial work products from genuinely different stances, then keeps only findings whose evidence is re-verified. |

## Install

Inspect first:

```bash
./install.sh --dry-run
```

The installer publishes each skill's `SKILL.md` through `publish-skill.py` for
each opted-in provider, then copies non-`SKILL.md` assets such as `references/`,
`templates/`, and `VERSION.json`. It never installs `REFRESH.md` into provider
targets.

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

## Partial Adoption

Every skill stands alone. Install the suite and invoke only the skill you need,
or copy a single skill folder into another provider workflow. Natural companion
edges exist, but they are not hidden requirements: `auto-evals` can run without
`root-cause` and manually populate its repair handoff, while `root-cause` can be
used on ordinary bug families without any eval package.

## Docs

Start with `docs/README-suite.md` for the suite map, then read the skill doc you
need:

| Doc | Covers |
|---|---|
| `docs/auto-evals.md` | Eval package doctrine, verifier separation, walkthrough mode, and repair handoff. |
| `docs/completeness-map.md` | Completion-boundary derivation and the implication-map schema. |
| `docs/deferrals.md` | Durable deferred-work tickets and the transfer test. |
| `docs/orthogonal-audit-review.md` | Cognitive parallax review doctrine. |
| `docs/root-cause.md` | Systemic root-cause workflow, taxonomy, and output contract. |

## License

This project is **source-available / public-source** under the PolyForm
Noncommercial License 1.0.0, **not** OSI-approved "open source." Noncommercial
use is permitted under the license. Commercial use requires a separate written
commercial license. See `LICENSE.md`.
