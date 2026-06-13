---
name: clarify
description: Use when the user asks to clarify, sharpen, or de-vague a prompt, or when a request is genuinely ambiguous or under-specified. Interviews the user with structured multiple-choice questions to pin down intent, scope, and success criteria, rewrites the prompt, confirms it, then proceeds. Also invoked automatically by a UserPromptSubmit hook on ambiguous prompts.
---

# Clarify

## Overview

Turn a vague or low-effort request into a sharp, actionable one **before** doing
the work — then do the work. The skill runs a short structured interview to
resolve the ambiguity, rewrites the request into a precise prompt, gets a one-tap
confirmation, and proceeds on the sharpened version. The payoff is avoiding the
expensive failure mode where the agent confidently builds the wrong thing because
it guessed at an under-specified request.

This skill is triggered two ways:

1. **Automatically** — a `UserPromptSubmit` hook injects a rule that tells the
   agent to invoke this skill *only* when a prompt is genuinely ambiguous.
2. **Manually** — the user runs `/clarify` or asks to sharpen a prompt.

## When to Use

Fire when a request is **genuinely ambiguous or under-specified** — when you could
reasonably build two or more materially different things from it, or you can't
state what "done" looks like:

- "Make the dashboard better." (better how? for whom? which metrics?)
- "Add auth." (which method? which routes? new or existing user model?)
- "Clean up this code." (refactor structure? performance? naming? all of it?)
- "Help me with the API." (design it? debug it? document it? call it?)
- Explicit asks: "clarify my prompt", "this is vague, help me sharpen it",
  "what do you need to know before starting?"

**When NOT to use** — the bar is high. Stay dormant when:

- The request is **clear**, even if short: "fix the typo on line 4", "rename
  `getUser` to `fetchUser`", "run the tests".
- The ambiguity is **resolvable from context or the codebase** — read the file,
  check the conventions, infer the obvious intent. Investigate before interrupting.
- It's **trivial or exploratory**: "what does this function do?", "ls the dir".
- There's exactly **one sensible interpretation**, even if details are unstated —
  fill them with sensible defaults and mention them, don't interrogate.

The cost of a wrong interruption (nagging the user about an obvious request) is
real. When in doubt, prefer proceeding with stated assumptions over interviewing.

## Workflow

### 1. Assess — is clarification actually warranted?

Before asking anything, try to resolve the ambiguity yourself: read referenced
files, check existing conventions, look at recent work. If that resolves it,
**skip the interview** and proceed (noting any assumptions). Only continue if real,
outcome-changing ambiguity remains.

### 2. Interview — only the questions that change the outcome

Use the **`AskUserQuestion`** tool. Rules that keep it tight:

- Ask **only** questions whose answer would change what you build or how. If two
  answers lead to the same action, don't ask.
- Prefer **concrete multiple-choice options** over open-ended prompts. Give 2–4
  real choices per question, and make the most likely one the first option,
  labeled "(Recommended)".
- Batch related questions into a **single `AskUserQuestion` call** (it supports up
  to 4) rather than a back-and-forth.
- Cap it: aim for **1–3 questions**. If you need more than 4, the request is
  research, not a quick clarify — say so and ask the user to narrow scope first.

Target the dimensions that most often hide ambiguity: **intent** (what outcome),
**scope** (how much / which parts), **constraints** (stack, style, must-not-touch),
and **success criteria** (how we'll know it's done).

### 3. Rewrite — produce the sharpened prompt

Fold the answers into a single, precise restatement of the request. A good
rewrite names the concrete deliverable, the scope boundaries, the relevant
constraints, and the done-condition. Keep the user's voice and goal — sharpen, do
not inflate or add scope they didn't ask for.

### 4. Confirm — one quick check

Show the rewritten prompt and ask for a fast confirm (this can be a final
`AskUserQuestion` with "Looks good — proceed" / "Let me tweak it", or just a plain
question if a small edit is likely). Don't belabor it.

### 5. Proceed

Once confirmed, **carry out the sharpened request** using whatever tools the work
needs. Clarifying is the on-ramp, not the destination — don't stop at the rewrite
unless the user chose a rewrite-only mode or explicitly asked you to wait.

## Output

The skill produces, in order:

1. **(If interviewing)** one or more `AskUserQuestion` prompts with concrete options.
2. **A sharpened prompt**, shown in a fenced block so it's easy to read and reuse:

   ```
   Sharpened request:
   <one tight paragraph or a short bulleted spec: deliverable, scope,
    constraints, success criteria>
   ```

3. **A brief confirm**, then the **actual work** on the confirmed prompt.

If assessment in step 1 shows clarification isn't needed, the skill produces
nothing of its own — it silently yields and the agent proceeds normally. Staying
out of the way on clear prompts is a success, not a no-op to apologize for.
