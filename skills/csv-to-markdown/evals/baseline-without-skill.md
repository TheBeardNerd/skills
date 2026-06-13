# Without Skill (BASELINE)

How a plain agent handles these prompts without csv-to-markdown loaded. Same
prompts as GREEN.

## Scenario 1: Simple CSV → table

Prompt:

```
Convert this to a Markdown table:
name,role
Ada,Engineer
Grace,Admiral
```

Observed behavior:

- Usually correct — simple cases are easy to hand-render.

Gap: Minimal for the trivial case; value shows up on the hard case below.

## Scenario 2: CSV with commas, quotes, newlines, and pipes

Prompt:

```
Turn this CSV into a table:
name,role,note
Ada,Engineer,"loves, commas"
Grace,Admiral,"two
lines"
Pipe,Test,a|b
```

Observed behavior:

- Hand-rendering frequently splits `"loves, commas"` on the comma, mishandles the
  quoted newline, and leaves the raw `|` in `a|b` — which silently breaks the
  Markdown table.

Gap: Quoting/escaping is exactly where manual conversion fails. The skill's script
handles all three deterministically.
