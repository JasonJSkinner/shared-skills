# Known Limitations

This is the plain account of what the Shared Skills v0.1.0 release does not do,
or does only partially.

## 1. `/dib` Is Not Included

The DIB authoring skill and optional substrate live in the companion DIB System
repository. This repo can consume a DIB or equivalent governing artifact, but it
does not install the `/dib` lifecycle tooling.

## 2. The Skills Are Doctrine-First

The installable artifacts are provider-rendered Markdown skills plus supporting
references and templates. They do not install a daemon, scheduler, service,
provider settings hook, or always-on automation layer.

## 3. Provider Mechanics Still Depend On The Host Platform

The core doctrine is provider-neutral. Invocation syntax, subagent fan-out,
session identity, large-context handling, and where provider skill directories
are read from remain platform-specific concerns.

## 4. The Installer Is Opt-In By Directory

`install.sh` writes to a provider only when that provider's skill directory
already exists or the user passes `--create-provider=<name>`. A missing provider
directory is a skip, not a failure.

## 5. The Install Proof Is A Dry-Run Record

`INSTALL-PROOF.md` records a real dry-run of the installer and the final success
line. It is evidence that the install path was exercised, not a substitute for
running `./install.sh --dry-run` in your own environment before installing.

## 6. License And Patent Language Should Be Reviewed

The repo is source-available under PolyForm Noncommercial 1.0.0, not
OSI-approved "open source." Commercial use requires a separate written license.
Patent and license language should be reviewed by qualified counsel before you
rely on it for publication or commercial planning.
