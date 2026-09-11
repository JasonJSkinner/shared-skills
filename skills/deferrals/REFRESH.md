# deferrals REFRESH

Post-compaction recovery surface for `/deferrals`.

## Read Policy

1. **Fresh session / first use:** read the skill `README.md` or `SKILL.md` for full orientation.
2. **Post-compaction / first high-stakes use:** read this `REFRESH.md` before acting.
3. **Stale-suspect / editing this skill:** reread `SKILL.md` and `references/lane-model.md` before changing canonical bytes.

## Load-Bearing Invariants

- Deferrals are lightweight, thread-aware project reminders stored in markdown under `~/.claude/deferrals/`.
- The lane/priority model is orthogonal: lane is fidelity (`L` or `H`), priority is importance.
- The transfer test governs lane choice: if a different-chat agent could not tend the item from the entry plus cross-references, use or enrich to `H`.
- This Codex repo run treats the referenced live deferrals file as read-only context; resolution happens in the owning Claude-side workflow.

## Verify Current State

- Before adding or enriching H-lane items, load `references/lane-model.md`.
- For list/resolve/tend operations, confirm the project slug and thread lineage before changing the live deferrals file.
- If this file conflicts with `SKILL.md`, trust `SKILL.md` and refresh this recovery note.

