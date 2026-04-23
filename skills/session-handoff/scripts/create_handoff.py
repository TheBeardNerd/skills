#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
from datetime import datetime
from pathlib import Path


DEFAULT_TEMPLATE = """# Handoff: [TASK_TITLE]\n\n## Session Metadata\n- Created: [TIMESTAMP]\n- Project: [PROJECT_PATH]\n- Branch: [GIT_BRANCH]\n\n## Current State Summary\n[TODO: summarize the current state]\n\n## Important Context\n[TODO: capture the critical context]\n\n## Immediate Next Steps\n1. [TODO: first next step]\n\n## Decisions Made\n- [TODO: key decision]\n\n## Critical Files\n- [TODO: path]: why it matters\n"""


def detect_branch(project: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=project,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return "(no git branch)"
    if result.returncode == 0:
        return result.stdout.strip()
    return "(no git branch)"


def sanitize_slug(slug: str) -> str:
    safe_slug = Path(slug).name
    safe_slug = re.sub(r"[^A-Za-z0-9._-]+", "-", safe_slug)
    safe_slug = safe_slug.strip(".-_")
    return safe_slug or "handoff"


def load_template() -> str:
    template_path = Path(__file__).resolve().parents[1] / "templates" / "handoff-template.md"
    if template_path.exists():
        return template_path.read_text()
    return DEFAULT_TEMPLATE


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("slug")
    args = parser.parse_args()

    project = Path.cwd()
    handoff_dir = project / ".ai" / "handoffs"
    handoff_dir.mkdir(parents=True, exist_ok=True)
    slug = sanitize_slug(args.slug)

    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    handoff_file = handoff_dir / f"{timestamp}-{slug}.md"
    handoff_text = (
        load_template()
        .replace("[TASK_TITLE]", slug)
        .replace("[TIMESTAMP]", timestamp)
        .replace("[PROJECT_PATH]", str(project))
        .replace("[GIT_BRANCH]", detect_branch(project))
    )
    handoff_file.write_text(handoff_text)
    print(handoff_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
