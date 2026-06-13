---
name: csv-to-markdown
description: Use when the user wants to convert a CSV file to a Markdown table, asks to turn a CSV into a table, or pastes CSV that needs rendering as Markdown. Produces a GitHub-flavored Markdown table.
allowed-tools: Bash, Read
---

# Csv To Markdown

## Overview

Convert CSV data into a clean GitHub-flavored Markdown table. The conversion is
deterministic, so it runs through `scripts/csv_to_md.py` rather than being done by
hand — that keeps quoting, embedded commas/newlines, and pipe-escaping correct
every time.

## When to Use

- "Convert this CSV to a Markdown table", "turn this CSV into a table"
- A `.csv` file or pasted CSV that should be rendered as Markdown
- Building docs/READMEs from tabular data

**When NOT to use:** Non-tabular data; spreadsheets that need formulas; or output
formats other than Markdown (HTML, JSON). For those, use the appropriate tool.

## Workflow

1. Locate the CSV — a file path the user gave, or text they pasted.
2. Run the converter:

   ```bash
   SKILL_DIR="${SKILL_DIR:-$HOME/.claude/skills/csv-to-markdown}"
   # from a file:
   python3 "$SKILL_DIR/scripts/csv_to_md.py" path/to/data.csv
   # from pasted text:
   printf '%s' "$CSV_TEXT" | python3 "$SKILL_DIR/scripts/csv_to_md.py"
   ```

   Useful flags: `--align left|right|center`, `--no-header` (synthesize column
   names), `--delimiter ';'`.
3. Return the rendered table.

## Output

A GitHub-flavored Markdown table — header row, a separator row, then data rows.
Pipes inside cells are escaped (`\|`) and newlines become `<br>`. Example:

```
| name | role |
| --- | --- |
| Ada | Engineer |
```
