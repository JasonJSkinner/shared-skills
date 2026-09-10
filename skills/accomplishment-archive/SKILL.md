---
name: accomplishment-archive
description: "Archive a completed work product (a skill, script, tool, or deliverable) into ~/Desktop/Accomplishments/<YYYYMMDD>_<name>/ as a human-readable REPORT.md (what it is / what it does / how it works / completion date) plus a verbatim, diff-verified copy of the artifact. Use when the user says 'archive this accomplishment', 'add this to Accomplishments', 'write an accomplishment report for X', 'save this to the Accomplishments folder', or asks for a report + copy of a finished piece of work on the Desktop. Supports --lite ('lite archive', 'lightweight archive'): curated-layer export (patch + exemplar sources + meta artifacts, ≤~15 files) sized for LLM ingestion instead of a full-tree copy."
version: "1.5.1"
argument-hint: "<artifact-name-or-path> [--name <folder-name>] [--lite]"
---

# accomplishment-archive

Preserve a finished piece of work as a self-contained Desktop record: one report a
human can read cold, plus a byte-exact copy of the artifact as it shipped.

## Dispatch standard

Default execution is OFF the invoking thread: dispatch a local custodian sub-session
that runs the workflow below end-to-end and returns a short digest (folder path,
verify result, report sections). The conductor's residual duty is one spot-check —
`ls` the archive folder and read REPORT.md's opening — before relaying the
confirmation. Run inline only when YOU are the dispatched custodian, when explicitly
asked, or when no sub-session mechanism is available.
[PROVIDER:CLAUDE]
Claude Code conductors: dispatch one bounded subagent or an available Codex lane
as archive custodian. Give it the artifact path, archive target, overrides, and
this workflow; require a digest containing folder, verification, secret-scan,
report-section, and version details. Use your environment's available launch
mechanism; no separately installed dispatch skill is required. If no sub-session
mechanism is available, run inline and report that fallback.
[/PROVIDER:CLAUDE]
[PROVIDER:CODEX]
Codex conductors: do NOT route through any Claude middleman or a separate synthesis
lane — you are already the report-synthesis model. Launch a child `codex exec`
session whose prompt is: "You are the archive custodian. Execute the
/accomplishment-archive skill INLINE for <artifact> [flags], full workflow +
diff-verify, then return the digest (folder, verify result, report sections)."
If a child session cannot be launched, run inline yourself.
[/PROVIDER:CODEX]

## Workflow

1. **Resolve the artifact.** From the argument or conversation, identify the source
   path (a skill folder under `~/.claude/skills/<name>/`, a script, a project folder,
   or a document). If genuinely ambiguous, ask one question.
2. **Create the folder:** `~/Desktop/Accomplishments/<YYYYMMDD>_<name>/` (folder
   name = artifact name unless `--name` overrides, prefixed with the local date of
   creation — `date +%Y%m%d`; no HHMM in the folder name). If a folder with that `<name>` suffix already exists
   (`~/Desktop/Accomplishments/*_<name>/`), do NOT silently overwrite — ask whether to
   refresh it (replace REPORT.md + copy) or archive under an ordinal-suffixed folder —
   `<YYYYMMDD>_<name>_2` (`_3`, …; still no HHMM).
3. **Write `REPORT.md`** — this report is deliberately **human-audience** (the user
   reads it cold, possibly years later). Cover, in order:
   - **What it is** — one-paragraph identity and purpose.
   - **What it does** — the end-to-end behavior, in plain language.
   - **How it works** — architecture/mechanism at whatever depth the artifact warrants.
   - **Completion date** — stated explicitly, near the top and in a version-history
     table when versions exist.
   - For skills, also include: subcommand/usage table, version history with dates,
     audit/verification summary (from AUDIT.json / VERSION.json when present), and a
     quickstart.
   - **Provenance footer** — generation date, generating thread(s) — the invoking
     conductor and, when dispatched, the custodian + synthesis-lane ids — source path,
     the artifact's content hash when one exists, and a note that the copy is inert
     (it sits outside any skill-discovery location; Claude Code does not load skills
     from the Desktop).
4. **Copy the artifact verbatim:** `cp -R <source> <folder>/<copy-name>/` (for a skill,
   `skill-copy/`; for a single file, keep its filename). Include internal `_archive/`
   history when present — the copy documents the artifact's full shipped state.
5. **Verify:** `diff -r <source> <copy>` must be clean; report the verification result.
   For a single file, `cmp` or a sha256 comparison. In sanitized mode (see Guardrails),
   verify against the approved sanitized staging copy instead of the original source.
   **On a failed verify:** delete the incomplete copy and re-copy once; if it fails
   again, report the diff/cmp output and stop — never confirm an archive whose
   verification did not pass.
6. **Confirm** to the user: folder path, report sections, copy-verification result.
   - **Seal gate:** before confirming, verify REPORT.md's load-bearing claims against the archived artifact and the exchanges the archive rests on; a confirmed hallucination blocks the seal until fixed or owner-waived.
[CLAUDE][CRITICAL]   - Claude conductors verify claims against the archived files and source exchanges; an installed claim-checking tool may assist, but is not required.

## Lite mode (`--lite`)

For large multi-commit programs (a feature branch, a migration, a fleet run) where a
full-tree copy would be huge and the intended reader is an LLM with a bounded context
window: archive curated LAYERS instead of the artifact tree. Target **≤ ~15 files**; the
reader infers the underlying codebase from the report + patch — never copy the broad
source tree.

- Root: `REPORT.md` per step 3, plus a **"Journey: fixes and mitigations along the way"**
  section when the run surfaced notable repairs (pre-existing bugs found/ticketed,
  infrastructure/process mitigations).
- `artifacts/` — the meta layer: program report, governing DR(s), learning log,
  run/stall records (long files may be section-extracts; name them `*-<section>.md`).
- `code/` — the material-change layer: the program `.patch` in full (text; binaries in it
  reduce to "Binary files differ" lines) + 1–3 exemplar sources that carry the core change.
- `planning/` — early-planning/decision excerpts when available.

Step 5 verification applies **per copied file** (diff/cmp against its source);
section-extracts are verified against their source section and labeled as extracts in
the manifest. Confirm with a one-line-per-file manifest (name, bytes, verified OK).

## Guardrails

- Read-only toward the source artifact — never mutate what you are archiving.
- Never silently overwrite an existing accomplishment folder (step 2).
- No secrets/credentials into the report or copy — scan the source BEFORE copying; on
  detection stop and ask the owner (sanitized archive only on explicit approval).
  **Sanitized mode:** on approval, build a sanitized staging copy, archive from it, and
  run step 5 against that staging copy — not the original. Mark the archive prominently
  (top of REPORT.md) as **sanitized / not byte-exact**, and list which files were
  sanitized — never the secret values.
- Write the report from verified facts (files, VERSION.json, AUDIT.json, transcript),
  not from memory — check claims against the artifact before asserting them.

## Relationship to other skills

- `claude-skill-versioning` / `skill-edit-audit` — upstream ceremony for skills; this
  skill archives the *result* and cites their VERSION.json/AUDIT.json rather than
  re-deriving version or audit state.
