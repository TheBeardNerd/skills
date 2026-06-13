#!/usr/bin/env python3
"""Hard-gate validator for a generated agent project.

Enforces the non-negotiables of a sound agent (see references/runtime.md and
references/guardrails.md):
  - the loop has BOTH a natural stop condition AND a max_turns cap
  - every tool has a non-empty description and a JSON input schema
  - REGISTRY matches the declared tools
  - at least one input guardrail exists
  - every high-risk tool has a human-approval path
  - no secret-like strings are committed

Exit 0 = PASS. Any FAIL exits non-zero. Warnings never fail the gate unless
--strict. Stdlib only.

Usage:
    python3 validate_agent.py ./my-agent [--strict] [--json]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import py_compile
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REQUIRED_FILES = ("agent.py", "tools.py", "guardrails.py", "config.py",
                  "requirements.txt", "README.md")
MIN_TOOL_DESC = 20

SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]
TEXT_SUFFIXES = {".py", ".md", ".txt", ".json", ".env", ".example", ".cfg"}
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules"}


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


def load_module(path: Path):
    """Import a stdlib-only module from a file path without polluting sys.modules."""
    spec = importlib.util.spec_from_file_location(f"_agent_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # may raise
    return module


def check_required(report: Report, d: Path) -> None:
    for rel in REQUIRED_FILES:
        if (d / rel).is_file():
            report.ok(f"{rel} present.")
        else:
            report.fail(f"{rel} is missing.")


def check_compile(report: Report, d: Path) -> None:
    bad = []
    for py in sorted(d.glob("*.py")):
        try:
            py_compile.compile(str(py), doraise=True)
        except py_compile.PyCompileError as exc:
            bad.append(f"{py.name}: {exc.msg}")
    if bad:
        report.fail("scripts failed to compile: " + "; ".join(bad))
    else:
        report.ok("all top-level .py files compile.")


def check_config(report: Report, d: Path) -> None:
    cfg_path = d / "config.py"
    if not cfg_path.is_file():
        return
    try:
        cfg = load_module(cfg_path)
    except Exception as exc:
        report.fail(f"config.py could not be imported: {exc}")
        return
    mt = getattr(cfg, "MAX_TURNS", None)
    if not isinstance(mt, int) or mt <= 0:
        report.fail("config.MAX_TURNS must be a positive int (the hard stop cap).")
    else:
        report.ok(f"config.MAX_TURNS = {mt} (hard stop present).")
    if not getattr(cfg, "MODEL", ""):
        report.fail("config.MODEL is missing/empty.")
    else:
        report.ok(f"config.MODEL = {cfg.MODEL!r}.")
    instr = getattr(cfg, "INSTRUCTIONS", "") or ""
    if not instr.strip():
        report.fail("config.INSTRUCTIONS is empty.")
    elif "you are done when" not in instr.lower():
        report.warn("INSTRUCTIONS lack an explicit stop instruction ('you are done when ...').")
    else:
        report.ok("INSTRUCTIONS present with a stop instruction.")


def check_agent_loop(report: Report, d: Path) -> set:
    """Returns the set of high-risk tool names referenced, for cross-checks."""
    agent_path = d / "agent.py"
    if not agent_path.is_file():
        return set()
    src = agent_path.read_text(encoding="utf-8")
    if "stop_reason" not in src:
        report.fail("agent.py has no `stop_reason` check (no natural stop condition).")
    else:
        report.ok("agent.py checks stop_reason (natural stop present).")
    if "MAX_TURNS" not in src:
        report.fail("agent.py never references MAX_TURNS (no hard loop cap).")
    else:
        report.ok("agent.py references MAX_TURNS (hard cap wired).")
    if "tool_result" not in src:
        report.fail("agent.py never builds tool_result blocks (tool loop incomplete).")
    else:
        report.ok("agent.py returns tool_result blocks to the model.")
    if "request_human_approval" not in src:
        report.warn("agent.py does not call request_human_approval; high-risk tools won't gate.")
    return set()


def check_tools(report: Report, d: Path) -> set:
    tools_path = d / "tools.py"
    if not tools_path.is_file():
        return set()
    try:
        mod = load_module(tools_path)
    except Exception as exc:
        report.fail(f"tools.py could not be imported: {exc}")
        return set()
    schemas = getattr(mod, "TOOL_SCHEMAS", None)
    registry = getattr(mod, "REGISTRY", {}) or {}
    high = set(getattr(mod, "HIGH_RISK_TOOLS", []) or [])
    if schemas is None:
        report.fail("tools.py defines no TOOL_SCHEMAS.")
        return high
    if not isinstance(schemas, list):
        report.fail("TOOL_SCHEMAS must be a list.")
        return high
    if not schemas:
        report.warn("TOOL_SCHEMAS is empty — an agent with no tools is unusual.")
    names = []
    for s in schemas:
        n = s.get("name", "<unnamed>")
        names.append(n)
        desc = (s.get("description") or "").strip()
        if not desc:
            report.fail(f"tool '{n}' has an empty description (the model picks tools from it).")
        elif len(desc) < MIN_TOOL_DESC:
            report.warn(f"tool '{n}' description is short ({len(desc)} chars).")
        if "input_schema" not in s:
            report.fail(f"tool '{n}' has no input_schema.")
    missing = [n for n in names if n not in registry]
    if missing:
        report.fail("tools missing from REGISTRY: " + ", ".join(missing))
    bad_high = [n for n in high if n not in names]
    if bad_high:
        report.fail("HIGH_RISK_TOOLS names not in TOOL_SCHEMAS: " + ", ".join(bad_high))
    if schemas and not missing and not bad_high:
        report.ok(f"{len(schemas)} tool(s) declared, registered, and schema-checked.")
    return high


def check_guardrails(report: Report, d: Path, high: set) -> None:
    g_path = d / "guardrails.py"
    if not g_path.is_file():
        return
    try:
        mod = load_module(g_path)
    except Exception as exc:
        report.fail(f"guardrails.py could not be imported: {exc}")
        return
    inputs = getattr(mod, "INPUT_GUARDRAILS", None)
    if not inputs:
        report.fail("no INPUT_GUARDRAILS defined (need at least one).")
    else:
        report.ok(f"{len(inputs)} input guardrail(s) defined.")
    if not callable(getattr(mod, "run_input_guardrails", None)):
        report.fail("guardrails.run_input_guardrails is missing.")
    if high:
        ok = callable(getattr(mod, "requires_approval", None)) and \
             callable(getattr(mod, "request_human_approval", None))
        if ok:
            report.ok(f"high-risk tools ({', '.join(sorted(high))}) have an approval path.")
        else:
            report.fail("high-risk tools exist but no requires_approval/request_human_approval.")


def check_secrets(report: Report, d: Path) -> None:
    hits = []
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            p = Path(root) / f
            if p.suffix.lower() not in TEXT_SUFFIXES and p.name != ".env.example":
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if any(pat.search(text) for pat in SECRET_PATTERNS):
                hits.append(p.name)
    if hits:
        report.fail("possible secrets in: " + ", ".join(sorted(set(hits))))
    else:
        report.ok("no secret-like strings detected.")


def validate(d: Path) -> Report:
    report = Report(target=d)
    if not d.is_dir():
        report.fail(f"'{d}' is not a directory.")
        return report
    check_required(report, d)
    check_compile(report, d)
    check_config(report, d)
    check_agent_loop(report, d)
    high = check_tools(report, d)
    check_guardrails(report, d, high)
    check_secrets(report, d)
    return report


def render(report: Report, strict: bool) -> str:
    lines = [f"Validating agent: {report.target}"]
    lines += [f"  PASS  {m}" for m in report.passes]
    lines += [f"  WARN  {m}" for m in report.warnings]
    lines += [f"  FAIL  {m}" for m in report.failures]
    lines.append("")
    if report.passed(strict):
        lines.append("RESULT: PASS — agent clears the hard gate.")
    else:
        n = len(report.failures) + (len(report.warnings) if strict else 0)
        lines.append(f"RESULT: FAIL — {n} issue(s) must be fixed.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a generated agent project.")
    parser.add_argument("target", type=Path, help="path to the agent directory")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    report = validate(args.target.resolve())
    if args.json:
        print(json.dumps({
            "target": str(report.target),
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
