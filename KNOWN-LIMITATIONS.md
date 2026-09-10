# Known Limitations

This is the plain account of what the Shared Skills v0.1.0 release does not do,
or does only partially.

## 1. `/dib` Is Not Included

The DIB authoring skill and optional substrate live in the companion DIB System
repository. This repo can consume a DIB or equivalent governing artifact, but it
does not install the `/dib` lifecycle tooling.

## 2. Installed Packages Can Include Executable Support Tools

The installable artifacts include provider-rendered Markdown, references,
templates, and—in script-backed skills such as `deferrals` and
`orchestrator-posture`—executable support tools. The main suite installer copies
those files but never runs a skill-local integration installer, registers a
provider hook, or starts a daemon, scheduler, service, or always-on layer.

## 3. Provider Mechanics Still Depend On The Host Platform

The core doctrine is provider-neutral. Invocation syntax, subagent fan-out,
session identity, large-context handling, and where provider skill directories
are read from remain platform-specific concerns.

## 4. The Installer Is Opt-In By Directory

`install.sh` writes to a provider only when that provider's skill directory
already exists or the user passes `--create-provider=<name>`. A missing provider
directory is a skip, not a failure. For an opted-in provider it installs both
the rendered skill and matching metadata; no manual metadata repair is needed.
The operation is additive and does not prune destination files. Excluding
`REFRESH.md` and `_archive/` means they are not copied from source; it does not
delete a pre-existing destination entry with either name.

## 5. The Install Proof Is A Dry-Run Record

`INSTALL-PROOF.md` records a real dry-run of the installer and the final success
line as historical evidence. It also records the separate current regression
command, `python3 tests/test_install.py`. Neither is a substitute for running
`./install.sh --dry-run` in your own environment before installing.

## 6. Some Optional Operations Have Explicit Prerequisites

`governance-read-access` can read bundled deferrals through the shipped CLI.
Decision projection requires a separately installed decisions `state.sh`, and
applying a governance update request requires an authorized provider-side
updater. If either prerequisite is missing, that operation stops; direct record
editing is not a fallback.

`orchestrator-posture` ships its recorder and provider-integration scripts, but
the main suite installer does not install a Stop hook. That optional integration
requires a separate, explicit invocation of the skill's own installer. The
recorder uses Python 3 and POSIX `fcntl` on macOS/Linux; its wrappers use Bash.

The bundled `deferrals` CLI works without hook registration. Its optional
session-start digest likewise requires a separate, explicit invocation of the
deferrals integration installer and requires Bash plus `jq`. The core CLI is
Python-standard-library-only, uses POSIX `fcntl`, and supports macOS/Linux; Git
is optional and used only for automatic project-key discovery. Record-root
precedence is `--root`, then `DEFERRALS_ROOT`, then the established shared
default `~/.claude/deferrals`, preserving existing records across migration.

## 7. License And Patent Language Should Be Reviewed

The repo is source-available under PolyForm Noncommercial 1.0.0, not
OSI-approved "open source." Commercial use requires a separate written license.
Patent and license language should be reviewed by qualified counsel before you
rely on it for publication or commercial planning.
