# Without Skill (BASELINE)

How a plain agent handles skill-building requests without skill-builder loaded.
Control for measuring the skill's value. Same prompts as the GREEN file.

## Scenario 1: "Build a skill that converts CSV files to Markdown tables"

Prompt:

```
Build me a skill that converts CSV files into Markdown tables.
```

Observed behavior:

- Writes a single SKILL.md, usually in the current directory, not the skills repo.
- Often inlines everything; no references/ split, no evals, no validation.
- Description tends to be vague ("Converts CSV to Markdown") with no trigger cues.

Gap: No structure decision (script vs prose), no hard validation, wrong location,
weak trigger, no evals — the skill may never fire and isn't repo-installable.

## Scenario 2: "Should this be a skill?" — automatic formatting on save

Prompt:

```
I want my code auto-formatted every time I save a file. Make a skill for it.
```

Observed behavior:

- Tends to start building a skill as asked.

Gap: This is a **hook**, not a skill (a skill only fires when the model chooses to
invoke it). A bare agent often doesn't catch the artifact mismatch.

## Scenario 3: Vague request needing intake

Prompt:

```
Make a skill for my PDFs.
```

Observed behavior:

- Guesses an interpretation and produces something, or asks one broad question.

Gap: No structured intake (purpose, triggers, inputs/outputs, examples), so the
result rarely matches intent.
