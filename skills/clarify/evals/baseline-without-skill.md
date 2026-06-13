# Without Skill (BASELINE)

How a plain agent (no skill loaded) handles each scenario, so the skill's added
value is measurable. Run the same prompts as the GREEN file.

## Scenario 1: Vague feature request

Prompt:

```
Make the dashboard better.
```

Observed behavior:

- Agent picks one interpretation (often visual polish) and starts editing, or
  asks a single open-ended "what do you mean by better?" with no options.

Gap: Guesses at intent; may build the wrong thing. No structured scoping, no
success criteria, no reusable sharpened prompt.

## Scenario 2: Under-specified technical task

Prompt:

```
Add auth.
```

Observed behavior:

- Agent assumes a method (e.g. JWT) and a scope, scaffolds it, and proceeds.

Gap: Auth method, affected routes, and user-model decisions are all guessed.
High chance of rework.

## Scenario 3: Clear, trivial request (should NOT trigger)

Prompt:

```
Fix the typo on line 4 of README.md.
```

Observed behavior:

- Agent fixes the typo directly. Correct.

Gap: None — included to confirm the skill must NOT add friction here.
