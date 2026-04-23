#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


ANY_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+.+$")
CRITICAL_FILES_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+Critical Files\s*$", re.IGNORECASE)
FILE_BULLET = re.compile(r"^\s*[-*]\s+`([^`]+)`(?:\s*:.*)?$")


def extract_critical_file_refs(text: str) -> list[str]:
    refs: list[str] = []
    in_critical_files = False

    for line in text.splitlines():
        if CRITICAL_FILES_HEADING.match(line):
            in_critical_files = True
            continue

        if ANY_HEADING.match(line):
            in_critical_files = False
            continue

        if not in_critical_files:
            continue

        match = FILE_BULLET.match(line)
        if match:
            refs.append(match.group(1))

    return refs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-on-stale", action="store_true")
    parser.add_argument(
        "--allow-absolute-paths",
        action="store_true",
        help="Allow checking absolute paths from handoff files",
    )
    parser.add_argument("handoff_file")
    args = parser.parse_args()

    handoff = Path(args.handoff_file).resolve()
    project = Path.cwd()
    try:
        text = handoff.read_text()
    except Exception as e:
        print(f"FAIL: Cannot read file: {e}")
        return 1

    missing: list[str] = []
    blocked_absolute: list[str] = []

    for item in extract_critical_file_refs(text):
        reference = Path(item)

        if reference.is_absolute() and not args.allow_absolute_paths:
            blocked_absolute.append(item)
            continue

        candidate = reference if reference.is_absolute() else (project / reference)
        if not candidate.exists():
            missing.append(item)

    if blocked_absolute:
        print("BLOCKED: absolute path references are disabled by default")
        for item in blocked_absolute:
            print(f"- {item}")
        print("Re-run with --allow-absolute-paths to opt in.")
        return 1

    if missing:
        print("STALE: missing referenced files")
        for item in missing:
            print(f"- {item}")
        return 1 if args.fail_on_stale else 0

    print("FRESH: no missing referenced files detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
