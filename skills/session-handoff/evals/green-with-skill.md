# With Skill Applied (GREEN)

This file records observed passing behavior using the session-handoff workflow and explicit global script paths.

## Scenario 1: CREATE workflow from a normal project directory

Commands:

```bash
SKILL_DIR="${SKILL_DIR:-$HOME/.agents/skills/session-handoff}"
HANDOFF_FILE="$(python3 "$SKILL_DIR/scripts/create_handoff.py" "green-create")"
python3 "$SKILL_DIR/scripts/validate_handoff.py" "$HANDOFF_FILE"
```

Observed output:

```text
<PROJECT_ROOT>/.ai/handoffs/2026-04-22-163838-green-create.md
PASS: handoff looks complete
```

Result: PASS. Handoff file was created in `.ai/handoffs/` and passed validation after filling required sections.

## Scenario 2: RESUME workflow freshness and discovery checks

Commands:

```bash
python3 "$SKILL_DIR/scripts/check_staleness.py" "$HANDOFF_FILE"
python3 "$SKILL_DIR/scripts/list_handoffs.py"
```

Observed output:

```text
FRESH: no missing referenced files detected
2026-04-22-163838-green-create.md
2026-04-22-163225-green-create.md
```

Result: PASS. Freshness and handoff listing checks both succeeded.
