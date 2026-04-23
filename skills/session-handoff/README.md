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

## Install (GitHub Distribution - Recommended)

1. Clone this repo to your local projects directory:

```bash
git clone <REPO_URL> ~/Projects/session-handoff
```

2. Install links for OpenCode/Codex and Claude Code:

```bash
cd ~/Projects/session-handoff
bash ./scripts/install-skill.sh
```

3. For automation/non-interactive usage:

```bash
bash ./scripts/install-skill.sh --yes
```

## Install (Manual Local Copy)

```bash
cp -R ~/Projects/session-handoff ~/.agents/skills/session-handoff
bash ~/.agents/skills/session-handoff/scripts/install-skill.sh
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
