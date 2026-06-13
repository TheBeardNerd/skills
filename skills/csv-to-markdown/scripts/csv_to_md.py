#!/usr/bin/env python3
"""Convert CSV to a GitHub-flavored Markdown table.

Usage:
    python3 csv_to_md.py input.csv
    cat data.csv | python3 csv_to_md.py            # reads stdin
    python3 csv_to_md.py input.csv --align right
    python3 csv_to_md.py input.csv --no-header     # synthesize Column 1..N headers

Handles quoted fields, embedded commas/newlines, and pipe characters (escaped so
they don't break the table). Stdlib only.
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

ALIGN_SEP = {
    "left": ":---",
    "right": "---:",
    "center": ":--:",
    "none": "---",
}


def escape_cell(value: str) -> str:
    """Make a cell safe inside a Markdown table."""
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\r\n", "\n").replace("\n", "<br>")


def rows_to_markdown(rows: list[list[str]], align: str = "none", has_header: bool = True) -> str:
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]  # pad ragged rows

    if has_header:
        header, body = rows[0], rows[1:]
    else:
        header = [f"Column {i + 1}" for i in range(width)]
        body = rows

    sep = ALIGN_SEP.get(align, "---")
    lines = [
        "| " + " | ".join(escape_cell(c) for c in header) + " |",
        "| " + " | ".join(sep for _ in header) + " |",
    ]
    for row in body:
        lines.append("| " + " | ".join(escape_cell(c) for c in row) + " |")
    return "\n".join(lines) + "\n"


def read_rows(source: str | None, delimiter: str) -> list[list[str]]:
    if source and source != "-":
        text = Path(source).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()
    # Use StringIO (not splitlines) so quoted fields containing newlines survive.
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    return [row for row in reader if row != []]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert CSV to a Markdown table.")
    parser.add_argument("input", nargs="?", default="-", help="CSV file path, or '-' for stdin")
    parser.add_argument("--align", choices=sorted(ALIGN_SEP), default="none", help="column alignment")
    parser.add_argument("--no-header", action="store_true", help="treat the first row as data")
    parser.add_argument("--delimiter", default=",", help="field delimiter (default ',')")
    args = parser.parse_args(argv)

    rows = read_rows(args.input, args.delimiter)
    if not rows:
        print("error: no rows found in input", file=sys.stderr)
        return 1
    sys.stdout.write(rows_to_markdown(rows, align=args.align, has_header=not args.no_header))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
