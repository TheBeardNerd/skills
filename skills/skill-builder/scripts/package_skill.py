#!/usr/bin/env python3
"""Finalize a skill: verify metadata consistency, print the install command, and
optionally emit a Claude Code plugin manifest.

Usage:
    python3 package_skill.py <skill-dir> [--repo URL] [--plugin] [--zip]

- Checks that package.json `name` agrees with the SKILL.md `name`.
- Prints the `npx skills add ...` install line for the repo.
- `--plugin` writes `.claude-plugin/plugin.json` so the skill can ship as a
  distributable Claude Code plugin.
- `--zip` writes `<name>.zip` of the skill directory for manual distribution.

Stdlib only. Run validate_skill.py first — this does not re-run the hard gate.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

DEFAULT_REPO = "https://github.com/TheBeardNerd/skills"
FM_NAME_RE = re.compile(r"^name:\s*(.+?)\s*$", re.MULTILINE)
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}


def read_skill_name(skill_dir: Path) -> str:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    m = FM_NAME_RE.search(text)
    if not m:
        raise ValueError("could not read `name` from SKILL.md frontmatter.")
    return m.group(1).strip()


def check_metadata(skill_dir: Path, name: str) -> list[str]:
    problems = []
    pkg_path = skill_dir / "package.json"
    if pkg_path.is_file():
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
        pkg_name = pkg.get("name", "")
        if name not in pkg_name:
            problems.append(f"package.json name '{pkg_name}' does not contain skill name '{name}'.")
    if name != skill_dir.name:
        problems.append(f"directory '{skill_dir.name}' does not match skill name '{name}'.")
    return problems


def write_plugin_manifest(skill_dir: Path, name: str, repo: str) -> Path:
    desc = ""
    pkg_path = skill_dir / "package.json"
    if pkg_path.is_file():
        desc = json.loads(pkg_path.read_text(encoding="utf-8")).get("description", "")
    manifest = {
        "name": name,
        "version": "0.1.0",
        "description": desc,
        "author": "TheBeardNerd",
        "homepage": repo,
        "skills": [f"./{name}"],
    }
    out_dir = skill_dir / ".claude-plugin"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "plugin.json"
    out_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return out_path


def write_zip(skill_dir: Path, name: str) -> Path:
    out_path = skill_dir.parent / f"{name}.zip"
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(skill_dir.rglob("*")):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.is_file():
                zf.write(path, path.relative_to(skill_dir.parent).as_posix())
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Package and verify a Claude Skill.")
    parser.add_argument("skill_dir", type=Path)
    parser.add_argument("--repo", default=DEFAULT_REPO, help="git repo URL for the install command")
    parser.add_argument("--plugin", action="store_true", help="write .claude-plugin/plugin.json")
    parser.add_argument("--zip", action="store_true", help="write <name>.zip of the skill")
    args = parser.parse_args(argv)

    skill_dir = args.skill_dir.resolve()
    name = read_skill_name(skill_dir)

    problems = check_metadata(skill_dir, name)
    for p in problems:
        print(f"WARN  {p}")

    print(f"Install:\n  npx skills add {args.repo} --skill {name}")

    if args.plugin:
        path = write_plugin_manifest(skill_dir, name, args.repo)
        print(f"Wrote plugin manifest: {path}")
    if args.zip:
        path = write_zip(skill_dir, name)
        print(f"Wrote archive: {path}")

    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
