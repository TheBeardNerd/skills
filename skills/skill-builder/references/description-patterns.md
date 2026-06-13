# Writing the `description` (the trigger)

The `description` is the only part of a skill (besides its name) that is always in
context. It is what the model reads to decide *whether to invoke the skill*. A
great skill with a weak description never fires. Treat this as the highest-leverage
sentence in the whole skill.

## Rules

1. **Lead with the trigger, not the mechanism.** Start with "Use when ..." and name
   the situations and phrasings that should fire it.
2. **Name concrete cues.** Include the words a user is likely to say, and the task
   shapes that apply. Models match on these.
3. **Be a little pushy.** It is better to fire and be dismissed than to never fire.
   But bound it — see the negative cue below.
4. **Third person, present tense.** Describe the situation, not yourself. No "I" /
   "my" / "me".
5. **State the payoff briefly.** End with what the skill produces, so the model
   knows it is the right tool.
6. **Keep it under ~1024 chars.** One or two dense sentences.

## Template

```
Use when <user goal / phrasings>, or when <task shape> — e.g. "<example prompt 1>",
"<example prompt 2>". Produces <the concrete output>.
```

## Good vs weak

**Weak:** `description: Helps with documents.`
- No trigger cues, no task shape, no output. Won't reliably fire.

**Good:** `description: Use when the user wants to extract tables or fields from a
PDF, asks "pull the data out of this PDF", or uploads a PDF to be parsed. Produces
structured JSON of the document's tables and key fields.`
- Trigger cues ("extract", "pull the data out", "PDF"), task shape, clear output.

## Optional: a negative cue

If a skill keeps mis-firing on adjacent tasks, add a short boundary inside the body
("When NOT to use") and, if needed, a clause in the description. Don't bloat the
description with every exclusion — handle most boundaries in the body.

## Validate it

`validate_skill.py` fails the gate if the description is missing, too short/long,
lacks a trigger cue, or uses first person. Passing the gate is necessary but not
sufficient — read it aloud and ask "would the model pick this up for the prompts in
the evals?"
