# With Skill Applied (GREEN)

Passing behavior with the skill active. Same prompts as BASELINE.

## Scenario 1: Simple CSV → table

Prompt:

```
Convert this to a Markdown table:
name,role
Ada,Engineer
Grace,Admiral
```

Observed output:

```
| name | role |
| --- | --- |
| Ada | Engineer |
| Grace | Admiral |
```

Result: PASS — header + separator + rows, valid GFM.

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

Observed output:

```
| name | role | note |
| --- | --- | --- |
| Ada | Engineer | loves, commas |
| Grace | Admiral | two<br>lines |
| Pipe | Test | a\|b |
```

Result: PASS — quoted comma preserved, embedded newline → `<br>`, pipe escaped
(`\|`) so the table doesn't break. These are exactly the cases a hand-written
table gets wrong.
