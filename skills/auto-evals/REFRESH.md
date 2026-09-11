# auto-evals REFRESH

Post-compaction recovery surface for `/auto-evals`.

## Read Policy

1. **Fresh session / first use:** read the skill `README.md` or `SKILL.md` for full orientation.
2. **Post-compaction / first high-stakes use:** read this `REFRESH.md` before acting.
3. **Stale-suspect / editing this skill:** reread `SKILL.md` and the relevant reference file before changing canonical bytes.

## Load-Bearing Invariants

- Authority order is DIB(s) first, then PCB(s), then implementation specs; lower layers do not override higher intent.
- Walkthrough mode depends on asymmetric-knowledge holdout: scenario design and walkthrough lanes must be separate agents with explicit forbidden read sets.
- Phase C is not a vote counter; it verifies findings, treats structural absence as evidence when applicable, and preserves the documented verdict vocabularies.
- Worktree fallback and deferral behavior are path-conscious; do not auto-mutate canonical deferral state from a temp validation install.

## Verify Current State

- For walkthrough mode, reload `references/walkthrough_v2_0.md` and only the lane templates being dispatched.
- For non-walkthrough eval generation, reload `references/principles_v1_3.md`; load `playbook_v1_3.md` only when concrete workflow details are needed.
- If this file conflicts with `SKILL.md` or the loaded reference, trust the canonical skill/reference and refresh this recovery note.
