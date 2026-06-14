#!/usr/bin/env python3
"""Hard-gate validator for a Claude Code subagent file.

Enforces the non-negotiables that decide whether a `.claude/agents/<name>.md`
subagent even loads and behaves (see references/scaffold-spec.md and the docs at
https://code.claude.com/docs/en/sub-agents):

  - the file has parseable YAML frontmatter delimited by `---`
  - `name` is present and kebab-case (Claude Code requires lowercase + hyphens)
  - `description` is present and non-empty (Claude delegates off of it)
  - the body (system prompt) is non-empty (it IS the subagent's behavior)
  - `model`, if set, is a valid alias / full id / `inherit`
  - no UI-only tools that never work inside a subagent are listed
  - no secret-like strings are committed

Target may be a single `.md` file OR a directory (validates every `*.md` under it).
Exit 0 = PASS. Any FAIL exits non-zero. Warnings never fail the gate unless
--strict. Stdlib only.

Usage:
    python3 validate_agent.py ./.claude/agents/code-reviewer.md [--strict] [--json]
    python3 validate_agent.py ./.claude/agents
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MODEL_ALIASES = {"sonnet", "opus", "haiku", "fable", "inherit"}
FULL_MODEL_RE = re.compile(r"^claude-[a-z0-9][a-z0-9.\-]*$")
MIN_DESC = 30
TRIGGER_CUES = ("use", "when", "after", "before", "proactively", "for ", "to ")

# UI/session-bound tools that never function inside a subagent (hard fail).
FORBIDDEN_TOOLS = {"AskUserQuestion", "EnterPlanMode", "ScheduleWakeup", "WaitForMcpServers"}
# Works only when permissionMode is `plan` (warn).
CONDITIONAL_TOOLS = {"ExitPlanMode"}
# Known built-in internal tools (a generous superset; unknowns -> warning only).
KNOWN_TOOLS = {
    "Bash", "BashOutput", "KillShell", "KillBash", "Read", "Write", "Edit",
    "MultiEdit", "NotebookEdit", "Glob", "Grep", "WebFetch", "WebSearch",
    "TodoWrite", "Task", "Agent", "Skill", "SlashCommand", "NotebookRead",
} | FORBIDDEN_TOOLS | CONDITIONAL_TOOLS

SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]


@dataclass
class Report:
    target: Path
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    passes: list[str] = field(default_factory=list)

    def fail(self, m): self.failures.append(m)
    def warn(self, m): self.warnings.append(m)
    def ok(self, m): self.passes.append(m)

    def passed(self, strict=False):
        return not self.failures and not (strict and self.warnings)


# --- minimal frontmatter parser (no third-party YAML) -------------------------

def parse_frontmatter(text: str):
    """Return (meta: dict, body: str) or (None, None) if no frontmatter.

    Handles `key: value` scalars, `key: a, b, c` comma lists, and simple
    block sequences (`- item`). Enough for subagent frontmatter.
    """
    if not text.startswith("---"):
        return None, None
    # split on the closing delimiter line
    parts = re.split(r"(?m)^---[ \t]*$", text, maxsplit=2)
    # parts[0] is "" (before first ---), parts[1] is frontmatter, parts[2] body
    if len(parts) < 3:
        return None, None
    raw, body = parts[1], parts[2]

    meta: dict = {}
    current_key = None
    for line in raw.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        seq = re.match(r"^[ \t]+-[ \t]+(.*)$", line)
        if seq and current_key is not None:
            meta.setdefault(current_key, [])
            if isinstance(meta[current_key], list):
                meta[current_key].append(seq.group(1).strip())
            continue
        kv = re.match(r"^([A-Za-z0-9_]+):[ \t]*(.*)$", line)
        if kv:
            key, val = kv.group(1), kv.group(2).strip()
            current_key = key
            if val == "":
                meta[key] = []          # may become a block list on following lines
            else:
                meta[key] = val
    return meta, body


def as_tool_list(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        items = [str(v).strip() for v in value]
    else:
        items = [p.strip() for p in str(value).split(",")]
    return [p for p in items if p]


def base_tool_name(tool: str) -> str:
    """`Agent(worker, x)` -> `Agent`; leaves plain names and mcp__* untouched."""
    return tool.split("(", 1)[0].strip()


# --- checks -------------------------------------------------------------------

def validate_file(path: Path) -> Report:
    report = Report(target=path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        report.fail(f"could not read file: {exc}")
        return report

    meta, body = parse_frontmatter(text)
    if meta is None:
        report.fail("no YAML frontmatter found (file must start with a `---` block).")
        return report
    report.ok("frontmatter block parsed.")

    # name -------------------------------------------------------------------
    name = meta.get("name")
    if not name or not isinstance(name, str):
        report.fail("`name` is missing (required).")
    elif not NAME_RE.match(name):
        report.fail(f"`name` '{name}' must be kebab-case (lowercase letters, digits, hyphens).")
    else:
        report.ok(f"name = {name!r} (kebab-case).")
        if name != path.stem:
            report.warn(f"name {name!r} != filename {path.stem!r}; loads fine but the convention is to match.")

    # description ------------------------------------------------------------
    desc = (meta.get("description") or "")
    desc = desc if isinstance(desc, str) else ""
    if not desc.strip():
        report.fail("`description` is missing/empty (Claude delegates based on it).")
    else:
        report.ok("description present.")
        if len(desc) < MIN_DESC:
            report.warn(f"description is short ({len(desc)} chars) — say WHAT it does and WHEN to use it.")
        if not any(cue in desc.lower() for cue in TRIGGER_CUES):
            report.warn("description has no trigger cue (use/when/after/proactively) — auto-delegation may not fire.")

    # body / system prompt ---------------------------------------------------
    if not (body or "").strip():
        report.fail("system prompt body is empty (it defines the subagent's behavior).")
    else:
        report.ok("system prompt body present.")
        if "when invoked" not in body.lower() and not re.search(r"(?m)^\s*1\.", body):
            report.warn("system prompt has no 'When invoked' steps — focused, stepwise prompts delegate better.")

    # model ------------------------------------------------------------------
    model = meta.get("model")
    if model is not None:
        model = str(model).strip()
        if model in MODEL_ALIASES or FULL_MODEL_RE.match(model):
            report.ok(f"model = {model!r}.")
        else:
            report.fail(f"`model` {model!r} is invalid (use sonnet/opus/haiku/fable, a claude-* id, or inherit).")

    # tools ------------------------------------------------------------------
    tools = as_tool_list(meta.get("tools"))
    disallowed = as_tool_list(meta.get("disallowedTools"))
    if "tools" not in meta:
        report.warn("no `tools` field — subagent inherits ALL tools. Prefer a least-privilege allowlist.")
    else:
        bad = sorted({base_tool_name(t) for t in tools} & FORBIDDEN_TOOLS)
        if bad:
            report.fail("tools list UI-only tools that never work in a subagent: " + ", ".join(bad))
        cond = sorted({base_tool_name(t) for t in tools} & CONDITIONAL_TOOLS)
        if cond:
            report.warn(f"{', '.join(cond)} only works with permissionMode: plan.")
        unknown = sorted(
            t for t in tools
            if base_tool_name(t) not in KNOWN_TOOLS and not t.startswith("mcp__")
        )
        if unknown:
            report.warn("unrecognized tool name(s) (typo? MCP/new tool?): " + ", ".join(unknown))
        if not report.failures:
            report.ok(f"{len(tools)} tool(s) declared (least-privilege allowlist).")
    if disallowed and tools:
        report.warn("both `tools` and `disallowedTools` set — disallowedTools applies first, then tools.")

    # secrets ----------------------------------------------------------------
    if any(pat.search(text) for pat in SECRET_PATTERNS):
        report.fail("possible secret/credential string committed in the file.")
    else:
        report.ok("no secret-like strings detected.")

    return report


def collect_targets(target: Path) -> list[Path]:
    if target.is_dir():
        return sorted(p for p in target.rglob("*.md") if p.name.lower() != "readme.md")
    return [target]


def render(reports: list[Report], strict: bool) -> str:
    lines: list[str] = []
    all_pass = True
    for r in reports:
        lines.append(f"Validating subagent: {r.target}")
        lines += [f"  PASS  {m}" for m in r.passes]
        lines += [f"  WARN  {m}" for m in r.warnings]
        lines += [f"  FAIL  {m}" for m in r.failures]
        lines.append("")
        all_pass = all_pass and r.passed(strict)
    if all_pass:
        lines.append(f"RESULT: PASS — {len(reports)} subagent(s) clear the hard gate.")
    else:
        n = sum(len(r.failures) + (len(r.warnings) if strict else 0) for r in reports)
        lines.append(f"RESULT: FAIL — {n} issue(s) must be fixed.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Claude Code subagent file or directory.")
    parser.add_argument("target", type=Path, help="path to a .md subagent or a directory of them")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    target = args.target.resolve()
    if not target.exists():
        print(f"RESULT: FAIL — '{target}' does not exist.")
        return 1
    targets = collect_targets(target)
    if not targets:
        print(f"RESULT: FAIL — no .md subagent files found under '{target}'.")
        return 1

    reports = [validate_file(p) for p in targets]
    all_pass = all(r.passed(args.strict) for r in reports)
    if args.json:
        print(json.dumps([{
            "target": str(r.target),
            "passed": r.passed(args.strict),
            "failures": r.failures,
            "warnings": r.warnings,
            "passes": r.passes,
        } for r in reports], indent=2))
    else:
        print(render(reports, args.strict))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
