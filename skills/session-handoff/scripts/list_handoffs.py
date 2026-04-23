#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


def main() -> int:
    handoff_dir = Path.cwd() / ".ai" / "handoffs"
    if not handoff_dir.exists():
        print("No handoffs found in .ai/handoffs")
        return 0

    for handoff_file in sorted(handoff_dir.glob("*.md"), reverse=True):
        print(handoff_file.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
