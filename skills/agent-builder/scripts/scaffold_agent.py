#!/usr/bin/env python3
"""Scaffold a Claude Code subagent from a JSON spec.

Emits ONE Markdown file — `<name>.md` — with YAML frontmatter (name, description,
tool permissions, model) and the system prompt as the body. This is a native
Claude Code subagent: drop it in `.claude/agents/` (project) or `~/.claude/agents/`
(user) and Claude delegates to it inside an existing session, using its built-in
file/shell/web tools. There is NO separate program to run.

Spec schema: references/scaffold-spec.md. The output format is the one documented
at https://code.claude.com/docs/en/sub-agents. Existing files are never overwritten
without --force.

Usage:
    python3 scaffold_agent.py --spec agent-spec.json            # -> ~/.claude/agents/<name>.md
    python3 scaffold_agent.py --spec agent-spec.json --scope project   # -> ./.claude/agents/
    python3 scaffold_agent.py --spec agent-spec.json --out ./somewhere
    python3 scaffold_agent.py --print-spec                       # emit a starter spec

Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DEFAULT_MODEL = "inherit"

# Tools that never function inside a subagent even if listed (UI/session-bound).
FORBIDDEN_TOOLS = {
    "AskUserQuestion", "EnterPlanMode", "ScheduleWakeup", "WaitForMcpServers",
}

STARTER_SPEC = {
    "name": "example-reviewer",
    "description": (
        "<Trigger-first: what this subagent does and WHEN Claude should delegate "
        "to it. e.g. 'Expert X specialist. Use proactively after Y to do Z.'>"
    ),
    "tools": ["Read", "Grep", "Glob", "Bash"],
    "disallowedTools": [],
    "model": "inherit",
    "permissionMode": None,
    "maxTurns": None,
    "memory": None,
    "color": None,
    "scope": "user",
    "system_prompt": (
        "You are <role>, specialized in <domain>.\n\n"
        "When invoked:\n"
        "1. <first concrete step>\n"
        "2. <next step>\n"
        "3. <final step>\n\n"
        "How you work:\n"
        "- <key practice or constraint>\n"
        "- <edge case: what to do when X is missing/ambiguous>\n\n"
        "Output format:\n"
        "- <exactly what you return to the main conversation, and how it is structured>\n\n"
        "You are done when <condition>. Return a concise summary; do not dump raw "
        "logs or file contents the main conversation does not need."
    ),
}


# --- frontmatter emission -----------------------------------------------------

def _tool_list(value) -> list[str]:
    """Normalize a tools field (list or comma string) to a clean list."""
    if not value:
        return []
    if isinstance(value, str):
        items = [p.strip() for p in value.split(",")]
    else:
        items = [str(p).strip() for p in value]
    return [p for p in items if p]


def gen_frontmatter(spec: dict) -> str:
    lines = ["---", f"name: {spec['name']}"]
    desc = (spec.get("description") or "").strip().replace("\n", " ")
    lines.append(f"description: {desc}")

    tools = _tool_list(spec.get("tools"))
    if tools:
        lines.append("tools: " + ", ".join(tools))
    disallowed = _tool_list(spec.get("disallowedTools"))
    if disallowed:
        lines.append("disallowedTools: " + ", ".join(disallowed))

    model = (spec.get("model") or DEFAULT_MODEL).strip()
    lines.append(f"model: {model}")

    pm = spec.get("permissionMode")
    if pm:
        lines.append(f"permissionMode: {pm}")
    mt = spec.get("maxTurns")
    if isinstance(mt, int) and mt > 0:
        lines.append(f"maxTurns: {mt}")
    mem = spec.get("memory")
    if mem:
        lines.append(f"memory: {mem}")
    color = spec.get("color")
    if color:
        lines.append(f"color: {color}")

    lines.append("---")
    return "\n".join(lines)


def gen_body(spec: dict) -> str:
    body = (spec.get("system_prompt") or "").strip()
    if not body:
        body = STARTER_SPEC["system_prompt"]
    return body


def render_agent(spec: dict) -> str:
    return gen_frontmatter(spec) + "\n\n" + gen_body(spec) + "\n"


# --- output location ----------------------------------------------------------

def default_out_dir(scope: str) -> Path:
    if scope == "project":
        return Path(".claude") / "agents"  # project scope, relative to cwd
    return Path.home() / ".claude" / "agents"  # user scope (default)


# --- orchestration ------------------------------------------------------------

def scaffold(spec: dict, out_dir: Path, force: bool = False) -> Path:
    """Write the subagent file and return its path. Raises on a bad name."""
    name = spec.get("name", "")
    if not NAME_RE.match(name or ""):
        raise ValueError(f"spec.name '{name}' must be kebab-case (lowercase letters, digits, hyphens).")

    bad = sorted(set(_tool_list(spec.get("tools"))) & FORBIDDEN_TOOLS)
    if bad:
        raise ValueError(
            "these tools never work inside a subagent and must be removed: "
            + ", ".join(bad)
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.md"
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists (use --force to overwrite).")
    path.write_text(render_agent(spec), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scaffold a Claude Code subagent (.claude/agents/<name>.md).")
    parser.add_argument("--spec", help="path to the spec JSON ('-' for stdin)")
    parser.add_argument("--out", type=Path, help="output directory (overrides --scope default)")
    parser.add_argument("--scope", choices=("project", "user"), help="user (default) -> ~/.claude/agents, project -> ./.claude/agents")
    parser.add_argument("--print-spec", action="store_true", help="emit a starter spec JSON")
    parser.add_argument("--force", action="store_true", help="overwrite an existing file")
    args = parser.parse_args(argv)

    if args.print_spec:
        print(json.dumps(STARTER_SPEC, indent=2))
        return 0
    if not args.spec:
        parser.error("provide --spec <file|-> (or --print-spec)")

    text = sys.stdin.read() if args.spec == "-" else Path(args.spec).read_text(encoding="utf-8")
    spec = json.loads(text)

    scope = args.scope or spec.get("scope") or "user"
    out_dir = (args.out or default_out_dir(scope)).resolve()

    path = scaffold(spec, out_dir, force=args.force)
    print(str(path))
    print(f"scope: {scope}  |  invoke: \"use the {spec['name']} subagent\" or @agent-{spec['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
