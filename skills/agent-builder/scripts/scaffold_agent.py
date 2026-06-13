#!/usr/bin/env python3
"""Scaffold a complete, runnable Claude-native agent from a JSON spec.

Emits the deterministic tool-use loop (agent.py), tool schemas + stubs (tools.py),
guardrails (guardrails.py), config (config.py), requirements, .env.example, README,
a starter blueprint, and an evals/ folder. The generated agent imports cleanly and
runs against the Anthropic Messages API once tool bodies are filled in.

Spec schema: references/scaffold-spec.md. Existing files are never overwritten
without --force.

Usage:
    python3 scaffold_agent.py --spec agent-spec.json --out ./my-agent
    python3 scaffold_agent.py --print-spec        # emit a starter spec

Stdlib only (the *generated* agent depends on the `anthropic` package).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DEFAULT_MODEL = "claude-opus-4-8"

STARTER_SPEC = {
    "name": "example-agent",
    "description": "One-line description of what this agent does.",
    "pattern": "single-loop",
    "model": DEFAULT_MODEL,
    "max_turns": 10,
    "instructions": (
        "You are <role>. Follow these steps: 1) ... 2) ... "
        "You are done when <condition> — then give the final answer and stop "
        "calling tools."
    ),
    "tools": [
        {
            "name": "example_lookup",
            "description": "Look something up by id. Returns a JSON object. "
                           "Use when the user references an id.",
            "type": "data",
            "risk": "low",
            "parameters": {"id": {"type": "string", "description": "the identifier"}},
            "required": ["id"],
        }
    ],
    "guardrails": [
        {"name": "safety_check", "type": "safety", "stage": "input", "action": "refuse"}
    ],
    "subagents": [],
}


# --- spec helpers -------------------------------------------------------------

def tool_schema(tool: dict) -> dict:
    props = {}
    for pname, pinfo in (tool.get("parameters") or {}).items():
        props[pname] = {
            "type": pinfo.get("type", "string"),
            "description": pinfo.get("description", ""),
        }
    return {
        "name": tool["name"],
        "description": tool.get("description", ""),
        "input_schema": {
            "type": "object",
            "properties": props,
            "required": list(tool.get("required") or []),
        },
    }


def params_signature(tool: dict) -> str:
    params = list((tool.get("parameters") or {}).keys())
    required = list(tool.get("required") or [])
    parts = [p for p in required]
    parts += [f"{p}=None" for p in params if p not in required]
    parts.append("**_ignored")
    return ", ".join(parts)


def ensure_input_guardrail(guardrails: list[dict]) -> list[dict]:
    if any(g.get("stage", "input") == "input" for g in guardrails):
        return guardrails
    return guardrails + [
        {"name": "safety_check", "type": "safety", "stage": "input", "action": "refuse"}
    ]


# --- file generators ----------------------------------------------------------

def gen_config(spec: dict) -> str:
    model = spec.get("model") or DEFAULT_MODEL
    max_turns = int(spec.get("max_turns", 10))
    instructions = spec.get("instructions") or STARTER_SPEC["instructions"]
    return (
        '"""Configuration for the agent: model, loop cap, and instructions."""\n\n'
        f"MODEL = {model!r}\n"
        f"MAX_TURNS = {max_turns}        # hard stop condition — see references/runtime.md\n"
        "MAX_TOKENS = 2048\n\n"
        "# The system prompt. Make the steps explicit and the stop condition\n"
        "# unambiguous (\"you are done when ...\") so the loop's natural stop fires.\n"
        f"INSTRUCTIONS = {instructions!r}\n"
    )


def gen_tools(spec: dict) -> str:
    tools = spec.get("tools") or []
    lines = [
        '"""Tools for the agent.',
        "",
        "Each function is a STUB returning a placeholder dict so the agent runs",
        "end-to-end immediately. Replace each body with the real API/DB/file call.",
        "The model picks tools from the descriptions in TOOL_SCHEMAS, so keep those",
        "accurate. See references/components.md for tool-design guidance.",
        '"""',
        "",
    ]
    for t in tools:
        sig = params_signature(t)
        desc = (t.get("description", "") or "").replace("\n", " ")
        lines.append(f"def {t['name']}({sig}):")
        lines.append(f'    """{desc}"""')
        lines.append("    # TODO: implement. Return a JSON-serializable dict.")
        lines.append(f'    return {{"todo": "implement {t["name"]}"}}')
        lines.append("")

    schemas = [tool_schema(t) for t in tools]
    lines.append("TOOL_SCHEMAS = " + json.dumps(schemas, indent=4))
    lines.append("")
    registry = ", ".join(f'"{t["name"]}": {t["name"]}' for t in tools)
    lines.append("REGISTRY = {" + registry + "}")
    lines.append("")
    high = sorted(t["name"] for t in tools if t.get("risk") == "high")
    lines.append("HIGH_RISK_TOOLS = " + (json.dumps(high) if high else "[]") + "  # require approval")
    lines.append("")
    return "\n".join(lines)


GUARDRAIL_RUNNERS = '''

def run_input_guardrails(text):
    """Return (ok, reason). ok=False short-circuits the agent before it acts."""
    for g in INPUT_GUARDRAILS:
        result = g(text)
        if result.get("flagged"):
            return False, result.get("reason") or g.__name__
    return True, ""


def run_output_guardrails(text):
    """Return (ok, reason, text). Implement redaction by mutating text here."""
    for g in OUTPUT_GUARDRAILS:
        result = g(text)
        if result.get("flagged"):
            return False, result.get("reason") or g.__name__, text
    return True, "", text


def requires_approval(tool_name):
    """High-risk tools require human approval by default. Tighten as needed."""
    return True


def request_human_approval(tool_name, tool_input):
    """Block on a human decision for a high-risk tool call.

    Denies automatically when there is no interactive terminal, so an unattended
    run cannot silently take an irreversible action.
    """
    if not sys.stdin.isatty():
        print(f"[auto-deny] no interactive approval available for {tool_name!r}")
        return False
    answer = input(f"Approve high-risk tool {tool_name!r} with {tool_input}? [y/N] ")
    return answer.strip().lower() in ("y", "yes")
'''


def gen_guardrails(spec: dict) -> str:
    guardrails = ensure_input_guardrail(spec.get("guardrails") or [])
    lines = [
        '"""Guardrails: layered defense + human-in-the-loop.',
        "",
        "Each check is a STUB that passes by default. Implement the real logic; a",
        "guardrail returns {\"flagged\": bool, \"reason\": str}. See",
        "references/guardrails.md.",
        '"""',
        "import sys",
        "",
    ]
    input_names, output_names = [], []
    for g in guardrails:
        name = g["name"]
        stage = g.get("stage", "input")
        gtype = g.get("type", "safety")
        action = g.get("action", "refuse")
        lines.append(f"def {name}(text):")
        lines.append(f'    """{stage}/{gtype} guardrail — action on trip: {action}."""')
        lines.append(f"    # TODO: implement the {gtype} check.")
        lines.append('    return {"flagged": False, "reason": ""}')
        lines.append("")
        (input_names if stage == "input" else output_names).append(name)

    lines.append("INPUT_GUARDRAILS = [" + ", ".join(input_names) + "]")
    lines.append("OUTPUT_GUARDRAILS = [" + ", ".join(output_names) + "]")
    return "\n".join(lines) + GUARDRAIL_RUNNERS


AGENT_PY = '''"""The agent: a deterministic tool-use loop over the Anthropic Messages API.

The loop is fully deterministic; only the model's choices inside each turn vary.
See references/runtime.md for the design. Run: `python agent.py "your request"`.
"""
import json
import sys

import anthropic

import config
import guardrails
import tools


def _dispatch_tool(name, tool_input):
    """Run one tool, applying the approval gate and surviving tool errors."""
    fn = tools.REGISTRY.get(name)
    if fn is None:
        return {"error": f"unknown tool: {name}"}
    if name in tools.HIGH_RISK_TOOLS and guardrails.requires_approval(name):
        if not guardrails.request_human_approval(name, tool_input):
            return {"error": "human approval denied", "tool": name}
    try:
        return fn(**tool_input)
    except Exception as exc:  # keep the loop alive; let the model recover
        return {"error": str(exc), "tool": name}


def run(user_input):
    """Run the agent to completion and return its final text answer."""
    ok, reason = guardrails.run_input_guardrails(user_input)
    if not ok:
        return f"[blocked by input guardrail] {reason}"

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    messages = [{"role": "user", "content": user_input}]

    for _turn in range(config.MAX_TURNS):          # hard stop condition
        resp = client.messages.create(
            model=config.MODEL,
            max_tokens=config.MAX_TOKENS,
            system=config.INSTRUCTIONS,
            tools=tools.TOOL_SCHEMAS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason != "tool_use":          # natural stop: a final answer
            final = "".join(b.text for b in resp.content if b.type == "text")
            ok, reason, final = guardrails.run_output_guardrails(final)
            return final if ok else f"[blocked by output guardrail] {reason}"

        tool_results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            output = _dispatch_tool(block.name, block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(output),
            })
        messages.append({"role": "user", "content": tool_results})

    return "[stopped] max_turns exceeded without a final answer."


def main():
    user_input = " ".join(sys.argv[1:]) or input("You: ")
    print(run(user_input))


if __name__ == "__main__":
    main()
'''


def gen_subagents(spec: dict) -> str:
    subs = spec.get("subagents") or []
    lines = [
        '"""Sub-agents for the ' + spec.get("pattern", "manager") + ' pattern.',
        "",
        "Manager pattern: expose each sub-agent as a tool the manager can call",
        "(add its schema to tools.TOOL_SCHEMAS and a runner to tools.REGISTRY).",
        "Decentralized pattern: swap the active agent on handoff. See",
        "references/patterns.md.",
        '"""',
        "",
    ]
    for s in subs:
        name = s["name"]
        lines.append(f"def run_{name}(task):")
        lines.append(f'    """{s.get("description", "")}"""')
        lines.append(f"    # TODO: run a sub-loop with these instructions and tools.")
        lines.append(f"    INSTRUCTIONS = {s.get('instructions', '')!r}")
        lines.append(f"    TOOLS = {json.dumps(s.get('tools', []))}")
        lines.append('    return {"todo": "implement ' + name + '", "task": task}')
        lines.append("")
    return "\n".join(lines)


def gen_requirements() -> str:
    return "anthropic>=0.40\n"


def gen_env() -> str:
    return "# Copy to .env (or export). Never commit a real key.\nANTHROPIC_API_KEY=your-key-here\n"


def gen_readme(spec: dict) -> str:
    name = spec["name"]
    pattern = spec.get("pattern", "single-loop")
    desc = spec.get("description", "")
    tool_rows = "\n".join(
        f"| `{t['name']}` | {t.get('type','-')} | {t.get('risk','-')} | {t.get('description','')} |"
        for t in (spec.get("tools") or [])
    ) or "| _(none yet)_ | | | |"
    return f"""# {name}

{desc}

**Pattern:** {pattern} (Claude-native deterministic tool-use loop).

## Run

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...        # see .env.example
python agent.py "your request here"
```

## Structure

- `agent.py` — the deterministic tool-use loop (perceive → reason → act → observe).
- `config.py` — model, `MAX_TURNS`, and the system instructions.
- `tools.py` — tool schemas + stub bodies + `REGISTRY` + `HIGH_RISK_TOOLS`.
- `guardrails.py` — input/output guardrails + human approval for high-risk tools.
- `blueprint.md` — the design decision and rationale.
- `evals/` — scenario prompts and success criteria.

## Tools

| Tool | Type | Risk | Purpose |
|------|------|------|---------|
{tool_rows}

## Next steps

1. Implement each tool body in `tools.py` (replace the placeholder returns).
2. Implement the guardrail checks in `guardrails.py`.
3. Tighten the instructions in `config.py` (steps + stop condition).
4. Run the evals in `evals/`.
"""


def gen_blueprint(spec: dict) -> str:
    return (
        f"# Agent Blueprint: {spec['name']}\n\n"
        f"- **Pattern:** {spec.get('pattern', 'single-loop')}\n"
        f"- **Model:** {spec.get('model', DEFAULT_MODEL)}\n"
        f"- **Max turns:** {spec.get('max_turns', 10)}\n"
        f"- **Description:** {spec.get('description', '')}\n\n"
        "## Tools\n\n"
        + ("\n".join(f"- `{t['name']}` ({t.get('type','-')}, risk={t.get('risk','-')}): "
                     f"{t.get('description','')}" for t in (spec.get('tools') or []))
           or "- (none)")
        + "\n\n## Guardrails\n\n"
        + ("\n".join(f"- `{g['name']}` ({g.get('stage','input')}/{g.get('type','safety')}) "
                     f"→ {g.get('action','refuse')}" for g in (spec.get('guardrails') or []))
           or "- (none)")
        + "\n\n## Stop conditions\n\n"
        "- Natural stop: model returns a final answer (no tool_use).\n"
        f"- Hard cap: MAX_TURNS = {spec.get('max_turns', 10)}.\n"
        "- High-risk tools require human approval.\n\n"
        "> Expand with the full Phase-2 rationale "
        "(see the skill's templates/blueprint.md).\n"
    )


def gen_evals(spec: dict) -> str:
    return (
        f"# Evals for {spec['name']}\n\n"
        "## Scenarios\n\n"
        "1. **<realistic prompt>** — expected: <correct behavior / final answer>.\n"
        "2. **<realistic prompt>** — expected: <...>.\n\n"
        "## Pressure cases\n\n"
        "- **Off-topic:** agent stays in scope / declines politely.\n"
        "- **Ambiguous:** agent asks a targeted question instead of guessing.\n"
        "- **Hostile (jailbreak / prompt injection):** input guardrail refuses.\n"
        "- **High-risk action:** agent requests human approval before acting.\n"
    )


# --- orchestration ------------------------------------------------------------

def write_file(path: Path, content: str, force: bool, created: list[str]) -> None:
    if path.exists() and not force:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    created.append(str(path.name))


def scaffold(spec: dict, out: Path, force: bool = False) -> list[str]:
    name = spec.get("name", "")
    if not NAME_RE.match(name or ""):
        raise ValueError(f"spec.name '{name}' must be kebab-case.")
    spec["guardrails"] = ensure_input_guardrail(spec.get("guardrails") or [])
    created: list[str] = []

    write_file(out / "config.py", gen_config(spec), force, created)
    write_file(out / "tools.py", gen_tools(spec), force, created)
    write_file(out / "guardrails.py", gen_guardrails(spec), force, created)
    write_file(out / "agent.py", AGENT_PY, force, created)
    write_file(out / "requirements.txt", gen_requirements(), force, created)
    write_file(out / ".env.example", gen_env(), force, created)
    write_file(out / "README.md", gen_readme(spec), force, created)
    write_file(out / "blueprint.md", gen_blueprint(spec), force, created)
    write_file(out / "evals" / "scenarios.md", gen_evals(spec), force, created)
    if spec.get("subagents"):
        write_file(out / "subagents.py", gen_subagents(spec), force, created)

    return created


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scaffold a runnable Claude-native agent.")
    parser.add_argument("--spec", help="path to the spec JSON ('-' for stdin)")
    parser.add_argument("--out", type=Path, help="output directory")
    parser.add_argument("--print-spec", action="store_true", help="emit a starter spec JSON")
    parser.add_argument("--force", action="store_true", help="overwrite existing files")
    args = parser.parse_args(argv)

    if args.print_spec:
        print(json.dumps(STARTER_SPEC, indent=2))
        return 0
    if not args.spec or not args.out:
        parser.error("provide --spec <file|-> and --out <dir> (or --print-spec)")

    text = sys.stdin.read() if args.spec == "-" else Path(args.spec).read_text(encoding="utf-8")
    spec = json.loads(text)

    created = scaffold(spec, args.out.resolve(), force=args.force)
    print(str(args.out.resolve()))
    print("created: " + (", ".join(created) if created else "(nothing new; use --force)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
