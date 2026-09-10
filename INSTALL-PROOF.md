# Install Proof

This records a real dry-run of the Shared Skills installer. A dry-run prints the
actions the installer would take and writes nothing to install targets.

## Reproduce

From the repository root:

```bash
./install.sh --dry-run
```

Useful flags include `--create-provider=<name>` and `--target=<dir>`.

## Historical Recorded Result

The following is the original dry-run record. It is retained as historical
evidence, not presented as a new result for the current installer.

The installer dry-run completed successfully:

- Exit code: `0`
- Providers observed in this environment: `2`
- Skill publish previews: `10`
- Asset copy previews: `46`
- Total dry-run action lines: `68`
- Skip lines: `19`
- Final line: `DRY-RUN complete. No filesystem changes performed.`

The run previewed:

1. Discovery of the canonical skill source directory.
2. Provider-specific rendering with this command shape:

   ```bash
   python3 publish-skill.py <skill-dir>/SKILL.md --provider <provider> > <target>/<skill>/SKILL.md
   ```

3. Copying supporting assets such as `references/`, `templates/`, and
   `VERSION.json`, while excluding `SKILL.md` and `REFRESH.md` from provider
   targets.
4. Skipping a missing provider directory because it had not been opted in.

The proof is intentionally path-generic. Exact paths and provider counts depend
on the user's environment and should be inspected by running the dry-run locally.

## Current Installer Regression

From the repository root:

```bash
python3 tests/test_install.py
```

A successful run prints a single `PASS:` summary. The standard-library test
installs every bundled skill for Claude, Codex, and Gemini. It verifies
source-tree integrity, provider rendering of `SKILL.md` and tagged Markdown
support files, exclusion of source-only `REFRESH.md` and archives, provider
opt-in, dry-run non-mutation, and unchanged re-install bytes and modification
times.

“Exclusion” here means the source entry is not copied during the clean
throwaway install. The additive installer does not delete pre-existing files in
a destination.

It also verifies two distinct hashes:

- Generated `SKILL.md` keeps a `Source version/hash:` provenance value for the
  canonical source `SKILL.md` used to render it.
- Installed `VERSION.json` preserves the source metadata fields, but its
  `content_hash_sha256` hashes the rendered installed `SKILL.md` beside it.

The installer writes installed metadata atomically; no manual installation or
post-install metadata edit is part of this verification path.

### Recorded current result — 2026-09-09

```text
python3 tests/test_install.py                 PASS: 24 skill/provider installs; 3 malformed-support-tag negative cases
python3 tests/test_provider_payloads.py       PASS: 3/3 provider payload checks
python3 skills/deferrals/tests/test_deferrals.py
                                               PASS: 5/5 checked-in deferrals regressions
python3 skills/orchestrator-posture/scripts/posture_run.py check
                                               PASS: 27/27 fixtures; 0 private pilot fixtures
bash -n <all shipped shell scripts>           PASS
git diff --check                              PASS
```

The five deferrals tests above are the checked-in public regression set. A
separate source-sync validation also passed 22 isolated upstream deferrals
tests; those additional tests are not presented as files shipped in this repo.
