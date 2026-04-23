# Baseline Without Skill (RED)

This file records observed failing behavior before applying the structured session-handoff workflow.

## Scenario 1: Create from a normal project directory with a repo-relative script guess

Command:

```bash
python3 scripts/create_handoff.py "baseline-relative-path"
```

Observed output:

```text
python3: can't open file '<PROJECT_ROOT>/scripts/create_handoff.py': [Errno 2] No such file or directory
```

Result: FAIL. The command is ambiguous unless the skill gives an explicit global script location.

## Scenario 2: Ad hoc quick note instead of a structured handoff

Command:

```bash
SKILL_DIR="${SKILL_DIR:-$HOME/.agents/skills/session-handoff}"
python3 -c "from pathlib import Path; Path('quick-note.md').write_text('# Quick note\n\nThis should be enough for the next agent.\n')"
python3 "$SKILL_DIR/scripts/validate_handoff.py" quick-note.md
```

Observed output:

```text
FAIL: Missing required section: ## Current State Summary
FAIL: Missing required section: ## Important Context
FAIL: Missing required section: ## Immediate Next Steps
FAIL: Missing required section: ## Decisions Made
FAIL: Missing required section: ## Critical Files
```

Result: FAIL. Informal notes do not satisfy required handoff structure.

## Baseline Rationalizations Confirmed

- "A quick summary in chat is enough."
- "I can probably run scripts/create_handoff.py from here."
- "Resume can rely on memory without checking the repo."
