# Accomplishment Archive

`accomplishment-archive` preserves a completed work product as a durable,
human-readable record: a factual `REPORT.md` plus a verified copy of the
artifact as it shipped.

## When To Use

Use it when a finished skill, script, tool, document, or project deliverable
deserves a self-contained archive that someone can understand later without the
original working conversation.

Do not use it as a live backup, source-control replacement, or place to archive
unverified work in progress.

## Archive Contract

A full archive contains:

- a report explaining what the artifact is, what it does, how it works, and
  when it was completed;
- the artifact copied without alteration;
- provenance and available version or audit metadata; and
- a clean recursive diff, byte comparison, or hash comparison between source
  and copy.

Existing archives are never silently overwritten. Sources are read-only, and a
secret scan must pass before material is copied. If sanitization is explicitly
approved, the report labels the result as sanitized rather than byte-exact.

## Lite Mode

`--lite` is for large programs where a full tree would be unwieldy. It archives
a small, curated evidence layer: the report, material patch, representative
sources, and the governing or run artifacts needed to infer the work. Each
copied file or extract still has its own verification record.

## Partial Adoption

The irreducible workflow is report, copy, and verification. Delegating the
archive to a separate execution lane is optional; a platform without that
capability can run the same workflow inline.

## Provider Notes

Provider mechanics determine whether the work runs in a child session or the
invoking session and where the archive is stored. Those mechanics do not change
the report, copy-integrity, overwrite, or secret-handling contracts.
