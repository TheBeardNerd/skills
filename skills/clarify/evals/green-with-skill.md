# With Skill (GREEN)

Expected behavior once the `clarify` skill is loaded. Same prompts as the
BASELINE file.

## Scenario 1: Vague feature request

Prompt:

```
Make the dashboard better.
```

Expected behavior:

- Skill fires. One `AskUserQuestion` call with 2–3 questions: which dimension
  ("Performance / Visual design / Add metrics"), who the audience is, and what
  "better" should achieve — each with concrete options and a recommended default.
- Produces a `Sharpened request:` block naming the concrete change, scope, and
  success criteria.
- Confirms, then proceeds with the work.

Result: PASS — scopes intent before building; no wrong-thing guess.

## Scenario 2: Under-specified technical task

Prompt:

```
Add auth.
```

Expected behavior:

- Skill first checks the codebase for an existing user model / auth pattern.
- Asks only the decisions that remain (method, which routes, new vs existing
  users) via multiple-choice, ≤3 questions.
- Rewrites into a precise spec, confirms, implements.

Result: PASS — decisions are made by the user, not silently assumed.

## Scenario 3: Clear, trivial request

Prompt:

```
Fix the typo on line 4 of README.md.
```

Expected behavior:

- Skill assesses, finds a single clear interpretation, and **stays dormant**.
  Agent fixes the typo directly with no interview.

Result: PASS — equal behavior to baseline, proving the skill adds no friction on
clear prompts (the high-bar requirement).
