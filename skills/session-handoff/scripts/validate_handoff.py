#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = [
    "Current State Summary",
    "Important Context",
    "Immediate Next Steps",
    "Decisions Made",
    "Critical Files",
]
LEVEL2_HEADING = re.compile(r"^\s{0,3}##\s+(.+?)\s*$", re.MULTILINE)
TODO_PLACEHOLDER = re.compile(r"\[TODO:[^\]]*\]", re.IGNORECASE)
SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
]


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: validate_handoff.py <handoff-file>")
        return 2

    path = Path(sys.argv[1])
    try:
        text = path.read_text()
    except Exception as e:
        print(f"FAIL: Cannot read file: {e}")
        return 1

    failures: list[str] = []
    section_headings = {match.group(1).strip() for match in LEVEL2_HEADING.finditer(text)}

    if TODO_PLACEHOLDER.search(text):
        failures.append("Found placeholder text")

    for section in REQUIRED_SECTIONS:
        if section not in section_headings:
            failures.append(f"Missing required section: ## {section}")

    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            failures.append("Found likely secret material")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("PASS: handoff looks complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
