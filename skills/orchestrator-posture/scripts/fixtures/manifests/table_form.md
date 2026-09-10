# DELIVERABLES — example orchestrated build

| # | deliverable | required path | check command |
|---|---|---|---|
| 1 | prior snapshot | ./archive/*previous*/entry.md | `test -f archive/example/entry.md` |
| 2 | skill entrypoint | ./skills/example/SKILL.md | `test -f skills/example/SKILL.md` |
| 3 | recorder verbs | ./scripts/posture_run.py | `python3 scripts/posture_run.py --help` |
| 4 | hook trio | ./scripts/{install,status,uninstall}.sh | `bash scripts/status.sh` |
| 5 | fixture check | ./scripts/posture_run.py check | `python3 scripts/posture_run.py check --allow-missing-pilot` |
| 6 | provider renders | ./out/claude/SKILL.md, ./out/codex/SKILL.md | `test -f out/claude/SKILL.md` |
