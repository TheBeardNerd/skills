"""Tests for csv_to_md.py. Run: python3 -m unittest discover -s tests"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import csv_to_md  # noqa: E402


class CsvToMdTest(unittest.TestCase):
    def test_basic_table(self):
        rows = [["name", "role"], ["Ada", "Engineer"]]
        out = csv_to_md.rows_to_markdown(rows)
        self.assertEqual(
            out,
            "| name | role |\n| --- | --- |\n| Ada | Engineer |\n",
        )

    def test_pipe_is_escaped(self):
        rows = [["a"], ["x|y"]]
        out = csv_to_md.rows_to_markdown(rows)
        self.assertIn("x\\|y", out)

    def test_newline_becomes_br(self):
        out = csv_to_md.rows_to_markdown([["h"], ["line1\nline2"]])
        self.assertIn("line1<br>line2", out)

    def test_ragged_rows_padded(self):
        out = csv_to_md.rows_to_markdown([["a", "b"], ["only"]])
        # the short data row gets an empty trailing cell
        self.assertIn("| only |  |", out)

    def test_alignment_separator(self):
        out = csv_to_md.rows_to_markdown([["a"], ["1"]], align="right")
        self.assertIn("| ---: |", out)

    def test_no_header_synthesizes_columns(self):
        out = csv_to_md.rows_to_markdown([["1", "2"]], has_header=False)
        self.assertIn("| Column 1 | Column 2 |", out)

    def test_empty_returns_empty(self):
        self.assertEqual(csv_to_md.rows_to_markdown([]), "")

    def test_quoted_newline_survives_parsing(self):
        # regression: splitlines() used to break quoted multi-line fields
        import io
        text = 'a,b\n"x","two\nlines"\n'
        parsed = list(csv_to_md.csv.reader(io.StringIO(text)))
        self.assertEqual(parsed, [["a", "b"], ["x", "two\nlines"]])
        out = csv_to_md.rows_to_markdown(parsed)
        self.assertIn("two<br>lines", out)


if __name__ == "__main__":
    unittest.main()
