# session-handoff

Installable agent skill package for creating and resuming project-local session handoffs.

## Package Layout

```text
session-handoff/
|-- SKILL.md
|-- scripts/
|   |-- create_handoff.py
|   |-- list_handoffs.py
|   |-- validate_handoff.py
|   `-- check_staleness.py
|-- references/
|   `-- resume-checklist.md
|-- templates/
|   `-- handoff-template.md
|-- tests/
|   `-- test_handoff_scripts.py
`-- evals/
    |-- pressure-scenarios.md
    |-- baseline-without-skill.md
    `-- green-with-skill.md
```

## Install

```bash
npx skills add https://github.com/TheBeardNerd/skills --skill session-handoff
```

For non-interactive usage:

```bash
npx skills add https://github.com/TheBeardNerd/skills --skill session-handoff -y
```

## Verify the Skill

1. Ensure the skill appears in your agent's skill list command.
2. Trigger with a prompt like: `Create a session handoff for this work.`
3. Confirm the skill loads and uses scripts from `./scripts`.

## Script Test Verification

From the repository root, run:

```bash
python3 -m unittest tests/test_handoff_scripts.py
```
