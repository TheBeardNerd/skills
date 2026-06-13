# csv-to-markdown

Convert CSV data into a GitHub-flavored Markdown table. Handles quoted fields,
embedded commas/newlines, and pipe characters correctly — the cases hand-rendering
gets wrong.

## Install

```bash
npx skills add https://github.com/TheBeardNerd/skills --skill csv-to-markdown
```

## Usage

| Intent | Example prompt |
|--------|----------------|
| Convert a CSV file | `"Convert data.csv to a Markdown table"` |
| Convert pasted CSV | `"Turn this CSV into a table: ..."` |
| Right-align numbers | `"Convert sales.csv, right-aligned"` |

Directly:

```bash
python3 scripts/csv_to_md.py data.csv --align left
cat data.csv | python3 scripts/csv_to_md.py
```

Flags: `--align left|right|center`, `--no-header`, `--delimiter ';'`.

## How It Works

The conversion is deterministic, so it runs through `scripts/csv_to_md.py` (Python
3, stdlib only) rather than being done by hand. The script parses with the `csv`
module, pads ragged rows, escapes `|` as `\|`, and turns embedded newlines into
`<br>` so the table always renders.

## Develop

```bash
python3 -m unittest discover -s tests
```
