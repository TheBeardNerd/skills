# Pressure Scenarios

Edge cases that should not break the skill or make it fire when it shouldn't.

## 1. Should-not-trigger: unrelated prompt

Prompt: `Summarize this CSV's trends for me`

Expected: this asks for analysis, not conversion — the skill may offer to render a
table but the core ask is summarization, so it should not just dump a table.

## 2. Ragged rows (uneven column counts)

Input: a CSV where some rows have fewer fields than the header.

Expected: short rows are padded with empty cells so the table stays rectangular and
valid (handled by `rows_to_markdown`).

## 3. Pipe / newline / quote injection in cells

Input: cells containing `|`, embedded newlines, and quoted commas.

Expected: `|` → `\|`, newline → `<br>`, quoted commas preserved. The table renders
correctly instead of breaking. (Covered by tests.)

## 4. Non-comma delimiter

Prompt: `Convert this semicolon-separated file to a table`

Expected: use `--delimiter ';'` rather than mis-splitting on commas.

## 5. Empty input

Input: empty file or no rows.

Expected: the script exits non-zero with `error: no rows found` instead of emitting
a malformed table.
