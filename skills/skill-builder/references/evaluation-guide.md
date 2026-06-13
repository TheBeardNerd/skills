# Evaluation Guide

A skill is only "done" when there is evidence it changes behavior for the better
and survives abuse. The repo uses a three-file evals trio.

## The trio

### `baseline-without-skill.md`
What a plain agent (skill not loaded) does with each scenario prompt. This is the
control. Record the prompt, the observed behavior, and the **gap** — what was
missing or wrong. If a bare agent already nails the task, the skill may not be
needed (revisit Gate 0 in [structure-decision.md](./structure-decision.md)).

### `green-with-skill.md`
The *same* prompts with the skill active, showing passing behavior. Record the
prompt, the observed output, and why it is correct. The delta between this and the
baseline is the skill's value — make it visible.

### `pressure-scenarios.md`
Adversarial and edge cases:
- **Should-not-trigger**: off-topic prompts where the skill must stay dormant
  (guards against an over-pushy description).
- **Ambiguous input**: the skill should ask a targeted question, not guess.
- **Hostile input**: the skill refuses unsafe requests and explains why.

## Method

1. Draft 2–3 realistic scenario prompts during Phase 1 intake.
2. Write them into baseline and green with the *same* prompts so the comparison is
   honest.
3. Prefer **programmatic assertions** where possible (exit codes, presence of
   required sections, valid JSON) over eyeballing — they don't rot.
4. Improve the skill against *patterns* you see across scenarios, not by overfitting
   to a single example.
5. Re-run after each change; keep the green file truthful (paste real output, not
   aspirational output).

## When scripts are involved

Back the evals with `tests/` (unittest) so the hard gate's compile check is
matched by behavior checks. A green eval that cites script output should be
reproducible by running that script.
