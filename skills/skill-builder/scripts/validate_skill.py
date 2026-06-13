#!/usr/bin/env python3
"""Hard-gate validator for a Claude Skill directory.

Exit code 0 means the skill passed every required check (PASS). Any required
failure exits non-zero and prints a checklist so the issues can be fixed and the
gate re-run. Warnings never fail the gate on their own.

Usage:
    python3 validate_skill.py <skill-dir> [--json] [--strict]

`--strict` promotes warnings to failures (useful in CI). `--json` prints a
machine-readable report instead of the human checklist.

Stdlib only, no third-party dependencies.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import py_compile
from dataclasses import dataclass, field
from pathlib import Path

# --- Tunables -----------------------------------------------------------------

MAX_SKILL_LINES = 500          # SKILL.md progressive-disclosure budget
MAX_DESCRIPTION_CHARS = 1024   # frontmatter description ceiling
MIN_DESCRIPTION_CHARS = 30     # anything shorter cannot describe real triggers
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")  # kebab-case
TRIGGER_HINTS = ("use when", "use this", "when the user", "when a user", "when you")
FIRST_PERSON_RE = re.compile(r"\b(I|I'?ll|I'?m|I'?ve|my|me)\b", re.IGNORECASE)

# Markdown relative links: ](./foo) or ](references/foo.md) but not http(s)/anchors/mailto
LINK_RE = re.compile(r"\]\((?!https?://|#|mailto:)([^)]+)\)")

SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
]

TEXT_SUFFIXES = {".md", ".py", ".txt", ".json", ".yaml", ".yml", ".template", ".sh", ".toml", ".cfg"}
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}


# --- Report plumbing ----------------------------------------------------------

@dataclass
class Report:
    skill_dir: Path
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    passes: list[str] = field(default_factory=list)

    def fail(self, msg: str) -> None:
        self.failures.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def ok(self, msg: str) -> None:
        self.passes.append(msg)

    def passed(self, strict: bool = False) -> bool:
        if self.failures:
            return False
        if strict and self.warnings:
            return False
        return True


# --- Frontmatter parsing (minimal YAML, no dependency) ------------------------

def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Return (frontmatter dict, body). Only top-level `key: value` scalars are
    parsed, which is all a SKILL.md frontmatter needs."""
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    if lines[0].strip() != "---":
        return {}, text
    fm: dict[str, str] = {}
    body_start = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            body_start = i + 1
            break
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip().strip('"').strip("'")
    if body_start is None:
        return {}, text  # unterminated frontmatter
    return fm, "\n".join(lines[body_start:])


# --- Individual checks --------------------------------------------------------

def check_skill_md(report: Report, skill_dir: Path) -> tuple[dict, str]:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        report.fail("SKILL.md is missing (required).")
        return {}, ""
    text = skill_md.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    if not fm:
        report.fail("SKILL.md has no parseable YAML frontmatter block.")
        return fm, body
    report.ok("SKILL.md present with frontmatter.")

    # name
    name = fm.get("name", "")
    if not name:
        report.fail("frontmatter `name` is missing.")
    elif not NAME_RE.match(name):
        report.fail(f"frontmatter `name` ('{name}') must be kebab-case (lowercase, hyphens).")
    elif name != skill_dir.name:
        report.fail(f"frontmatter `name` ('{name}') must equal the directory name ('{skill_dir.name}').")
    else:
        report.ok(f"name '{name}' is kebab-case and matches the directory.")

    # description
    desc = fm.get("description", "")
    check_description(report, desc)

    # line budget
    n_lines = len(text.splitlines())
    if n_lines > MAX_SKILL_LINES:
        report.fail(f"SKILL.md is {n_lines} lines (> {MAX_SKILL_LINES}). Move detail into references/.")
    else:
        report.ok(f"SKILL.md is {n_lines} lines (<= {MAX_SKILL_LINES}).")

    return fm, body


def check_description(report: Report, desc: str) -> None:
    if not desc:
        report.fail("frontmatter `description` is missing — this is the primary trigger.")
        return
    if len(desc) < MIN_DESCRIPTION_CHARS:
        report.fail(f"description is too short ({len(desc)} chars); name concrete triggers.")
    if len(desc) > MAX_DESCRIPTION_CHARS:
        report.fail(f"description is too long ({len(desc)} > {MAX_DESCRIPTION_CHARS} chars).")
    low = desc.lower()
    if not any(h in low for h in TRIGGER_HINTS):
        report.fail("description lacks an explicit trigger cue (e.g. 'Use when ...').")
    if FIRST_PERSON_RE.search(desc):
        report.fail("description uses first person; write it in third person about when to trigger.")
    if report.failures and report.failures[-1].startswith("description"):
        return
    report.ok("description has a trigger cue, third-person voice, and a sane length.")


def check_required_files(report: Report, skill_dir: Path) -> None:
    for rel in ("README.md", "package.json", ".gitignore"):
        if (skill_dir / rel).is_file():
            report.ok(f"{rel} present.")
        else:
            report.fail(f"{rel} is missing (repo convention requires it).")


def check_scripts_compile(report: Report, skill_dir: Path) -> None:
    scripts = sorted((skill_dir / "scripts").glob("*.py")) if (skill_dir / "scripts").is_dir() else []
    if not scripts:
        report.ok("no scripts to compile (or none present).")
        return
    bad = []
    for script in scripts:
        try:
            py_compile.compile(str(script), doraise=True)
        except py_compile.PyCompileError as exc:  # pragma: no cover - exercised via tests
            bad.append(f"{script.name}: {exc.msg}")
    if bad:
        report.fail("scripts failed to compile: " + "; ".join(bad))
    else:
        report.ok(f"all {len(scripts)} script(s) compile.")


def check_links_resolve(report: Report, skill_dir: Path, body: str) -> None:
    broken = []
    for match in LINK_RE.finditer(body):
        target = match.group(1).split("#", 1)[0].strip()
        if not target:
            continue
        if (skill_dir / target).exists():
            continue
        broken.append(target)
    if broken:
        report.fail("SKILL.md links to missing files: " + ", ".join(sorted(set(broken))))
    else:
        report.ok("all relative links in SKILL.md resolve.")


def check_no_secrets(report: Report, skill_dir: Path) -> None:
    hits = []
    for path in iter_text_files(skill_dir):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat in SECRET_PATTERNS:
            if pat.search(text):
                hits.append(path.relative_to(skill_dir).as_posix())
                break
    if hits:
        report.fail("possible secrets detected in: " + ", ".join(sorted(set(hits))))
    else:
        report.ok("no secret-like strings detected.")


def iter_text_files(skill_dir: Path):
    for root, dirs, files in os.walk(skill_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            p = Path(root) / fname
            if p.suffix.lower() in TEXT_SUFFIXES:
                yield p


# --- Orchestration ------------------------------------------------------------

def validate(skill_dir: Path) -> Report:
    report = Report(skill_dir=skill_dir)
    if not skill_dir.is_dir():
        report.fail(f"'{skill_dir}' is not a directory.")
        return report
    _, body = check_skill_md(report, skill_dir)
    check_required_files(report, skill_dir)
    check_scripts_compile(report, skill_dir)
    check_links_resolve(report, skill_dir, body)
    check_no_secrets(report, skill_dir)
    return report


def render(report: Report, strict: bool) -> str:
    lines = [f"Validating skill: {report.skill_dir}"]
    for msg in report.passes:
        lines.append(f"  PASS  {msg}")
    for msg in report.warnings:
        lines.append(f"  WARN  {msg}")
    for msg in report.failures:
        lines.append(f"  FAIL  {msg}")
    lines.append("")
    if report.passed(strict):
        lines.append("RESULT: PASS — skill clears the hard gate.")
    else:
        n = len(report.failures) + (len(report.warnings) if strict else 0)
        lines.append(f"RESULT: FAIL — {n} issue(s) must be fixed.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hard-gate validator for a Claude Skill.")
    parser.add_argument("skill_dir", type=Path, help="path to the skill directory")
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = parser.parse_args(argv)

    report = validate(args.skill_dir.resolve())
    if args.json:
        print(json.dumps({
            "skill_dir": str(report.skill_dir),
            "passed": report.passed(args.strict),
            "failures": report.failures,
            "warnings": report.warnings,
            "passes": report.passes,
        }, indent=2))
    else:
        print(render(report, args.strict))
    return 0 if report.passed(args.strict) else 1


if __name__ == "__main__":
    raise SystemExit(main())
