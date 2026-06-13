# With Skill Applied (GREEN)

Passing behavior with skill-builder active. Same prompts as BASELINE.

## Scenario 1: "Build a skill that converts CSV files to Markdown tables"

Prompt:

```
Build me a skill that converts CSV files into Markdown tables.
```

Observed output (abridged):

```
Skill spec:
  name: csv-to-markdown
  description: Use when the user wants to convert a CSV file to a Markdown table,
    asks "turn this CSV into a table", or pastes CSV needing rendering. Produces a
    GitHub-flavored Markdown table.
  archetype: tool-wrapper
  pattern: none
  files: SKILL.md, scripts/csv_to_md.py, tests/, evals/
  allowed-tools: Bash, Read

$ python3 scripts/scaffold_skill.py csv-to-markdown --description "..."
$ python3 scripts/validate_skill.py ~/Projects/skills/skills/csv-to-markdown
RESULT: PASS — skill clears the hard gate.
Install: npx skills add https://github.com/TheBeardNerd/skills --skill csv-to-markdown
```

Result: PASS — chose a deterministic script (right for CSV parsing), landed in the
repo, wrote a trigger-first description, and cleared the validator.

## Scenario 2: "Should this be a skill?" — automatic formatting on save

Prompt:

```
I want my code auto-formatted every time I save a file. Make a skill for it.
```

Observed output:

```
That's a hook, not a skill — a skill only runs when the model chooses to invoke
it, so it can't fire automatically on save. The right tool is a PostToolUse hook
in settings.json. Want that instead? (I can still make a formatting *skill* you
invoke on demand if you'd like both.)
```

Result: PASS — Gate 0 caught the artifact mismatch and routed to a hook.

## Scenario 3: Vague request needing intake

Prompt:

```
Make a skill for my PDFs.
```

Observed output:

```
Quick intake before I build:
1. What should it DO with PDFs (extract text? tables? fields? summarize?)
2. What will you say to trigger it?
3. Output format (JSON? Markdown? plain text?)
4. One example PDF + the result you'd want.
```

Result: PASS — ran adaptive intake (asked only the missing pieces) instead of
guessing.
