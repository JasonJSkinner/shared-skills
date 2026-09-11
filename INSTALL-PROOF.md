# Install Proof

This records a real dry-run of the Shared Skills installer. A dry-run prints the
actions the installer would take and writes nothing to install targets.

## Reproduce

From the repository root:

```bash
./install.sh --dry-run
```

Useful flags include `--create-provider=<name>` and `--target=<dir>`.

## Recorded Result

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
