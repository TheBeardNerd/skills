#!/usr/bin/env python3
"""Recommend the correct agent structure from a JSON of signals.

Encodes the decision framework (Anthropic "Building Effective Agents" + OpenAI
"Practical Guide to Building Agents") as a deterministic decision tree, so the
workflow-vs-agent verdict and pattern choice are reproducible rather than vibes.

Treat the output as a strong prior to confirm against references/patterns.md — not
a final answer. Bias is always toward the simplest structure that fits.

Usage:
    python3 recommend_structure.py --signals signals.json
    python3 recommend_structure.py --signals -          # read JSON from stdin
    python3 recommend_structure.py --print-template      # emit a blank signals file
    python3 recommend_structure.py --signals s.json --json

Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# All signals are booleans, default False. Grouped by the gate they inform.
SIGNAL_KEYS = [
    # Gate 0 — does this need an agent at all?
    "complex_decision",          # nuanced judgment, exceptions, context-sensitivity
    "brittle_rules",             # sprawling/unwieldy rulesets, costly to maintain
    "unstructured_data",         # interpreting language/documents/dialogue
    # Control-flow character
    "one_pass",                  # a single well-scoped LLM pass answers it
    "steps_predictable",         # the sequence of steps is known up front
    "dynamic_tool_loop",         # the model decides tool calls at runtime (not fixed)
    # Workflow shape
    "fixed_sequential_steps",    # outline -> draft -> polish style
    "distinct_input_categories", # inputs fall into separable buckets
    "independent_parallel_subtasks",  # subtasks run independently / need voting
    "quality_rubric_iterative",  # checkable rubric + refinement helps
    # Agent shape
    "subtasks_unpredictable",    # subtasks can't be enumerated in advance
    "needs_central_synthesis",   # one agent must keep control and synthesize
    "specialist_handoff",        # full control transfers to a specialist peer
    "tool_overload",             # too many overlapping tools for one agent
    "many_branches",             # prompt has many if-then-else branches
    "steps_unbounded",           # number of steps genuinely unpredictable
    "high_trust",                # model can be trusted to drive autonomously
]


def _b(signals: dict, key: str) -> bool:
    return bool(signals.get(key, False))


def recommend(signals: dict) -> dict:
    """Pure decision function. Returns recommendation, category, and rationale."""
    why: list[str] = []
    ruled_out: list[str] = []
    escalation: list[str] = []

    agent_needed = (
        _b(signals, "complex_decision")
        or _b(signals, "brittle_rules")
        or _b(signals, "unstructured_data")
    )

    # Gate 0 -------------------------------------------------------------------
    if not agent_needed:
        return {
            "recommendation": "not-an-agent (deterministic solution)",
            "category": "not-an-agent",
            "why": [
                "No Gate-0 signal is set: the task lacks complex decision-making, "
                "unwieldy rules, or heavy unstructured-data interpretation.",
                "A rules engine / conventional code is cheaper, faster, and more "
                "reliable here. Building an agent would add cost and failure modes "
                "for no gain.",
            ],
            "ruled_out": ["All agent and workflow patterns — none is warranted."],
            "escalation": [],
        }
    why.append(
        "Gate 0 passed: "
        + ", ".join(
            k for k in ("complex_decision", "brittle_rules", "unstructured_data")
            if _b(signals, k)
        )
        + " → an LLM-driven approach can add value."
    )

    workflowish = _b(signals, "steps_predictable") and not _b(signals, "dynamic_tool_loop")

    # Workflow branch (predefined paths) --------------------------------------
    if workflowish:
        why.append(
            "Steps are predictable and control flow is not model-directed → a "
            "workflow (predefined path) beats a dynamic agent."
        )
        if _b(signals, "one_pass"):
            rec, cat = "single augmented call (NOT an agent)", "workflow"
            why.append("A single well-scoped pass answers it — no loop needed.")
        elif _b(signals, "distinct_input_categories"):
            rec, cat = "routing", "workflow"
            why.append("Inputs fall into distinct categories better handled separately.")
            escalation.append("Watch mis-routing; keep categories distinct and classification reliable.")
        elif _b(signals, "independent_parallel_subtasks"):
            rec, cat = "parallelization", "workflow"
            why.append("Independent subtasks can run at once (sectioning) or vote for confidence.")
        elif _b(signals, "quality_rubric_iterative"):
            rec, cat = "evaluator-optimizer", "workflow"
            why.append("A checkable rubric plus iterative refinement measurably helps.")
            escalation.append("Define a stop condition for the refine loop.")
        elif _b(signals, "fixed_sequential_steps"):
            rec, cat = "prompt-chaining", "workflow"
            why.append("Fixed sequential steps, each building on the last.")
        else:
            rec, cat = "prompt-chaining", "workflow"
            why.append("Default for a known multi-step path; add a gate between steps.")
        ruled_out.append("Agentic patterns — control flow is predictable, so a workflow is simpler.")
        return {"recommendation": rec, "category": cat, "why": why,
                "ruled_out": ruled_out, "escalation": escalation}

    # Agent branch (model-directed paths) -------------------------------------
    why.append(
        "Control flow is dynamic / steps aren't fully predictable → a model-directed "
        "agent is warranted."
    )

    if _b(signals, "specialist_handoff") and not _b(signals, "needs_central_synthesis"):
        rec, cat = "decentralized (handoff)", "agent"
        why.append("Full control should transfer to a specialist peer; no central synthesis needed.")
        escalation.append("Multi-agent: more failure modes. Confirm a single-loop agent can't do it first.")
    elif _b(signals, "subtasks_unpredictable") and (
        _b(signals, "needs_central_synthesis")
        or _b(signals, "tool_overload")
        or _b(signals, "many_branches")
    ):
        rec, cat = "manager (orchestrator-workers)", "agent"
        why.append("Subtasks can't be predicted up front; a lead agent must delegate and synthesize.")
        escalation.append("Multi-agent adds coordination + token cost. Maximize a single agent first.")
    elif _b(signals, "tool_overload") or _b(signals, "many_branches"):
        rec, cat = "single-loop (consider splitting)", "agent"
        why.append("Tool overlap / branchy prompt strains one agent.")
        escalation.append(
            "First improve tool names/params/descriptions and prompt structure. "
            "Split into a manager only if clarity fixes don't help."
        )
    elif _b(signals, "steps_unbounded") and _b(signals, "high_trust"):
        rec, cat = "autonomous", "agent"
        why.append("Step count is genuinely unpredictable and the model can be trusted to drive.")
        escalation.append(
            "Highest risk. Mandatory: sandboxed tools, hard max_turns/budget, "
            "human approval on irreversible actions."
        )
    else:
        rec, cat = "single-loop", "agent"
        why.append("One agent with tools running a tool-use loop covers it — the standard agent.")
        ruled_out.append("Multi-agent / autonomous — not justified; start simple.")

    return {"recommendation": rec, "category": cat, "why": why,
            "ruled_out": ruled_out, "escalation": escalation}


def render(result: dict) -> str:
    lines = [
        f"RECOMMENDATION: {result['recommendation']}  (category: {result['category']})",
        "",
        "WHY:",
    ]
    lines += [f"  - {w}" for w in result["why"]]
    if result["ruled_out"]:
        lines += ["", "RULED OUT:"] + [f"  - {r}" for r in result["ruled_out"]]
    if result["escalation"]:
        lines += ["", "ESCALATION NOTES:"] + [f"  - {e}" for e in result["escalation"]]
    return "\n".join(lines)


def template() -> str:
    return json.dumps({k: False for k in SIGNAL_KEYS}, indent=2) + "\n"


def load_signals(arg: str) -> dict:
    text = sys.stdin.read() if arg == "-" else Path(arg).read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("signals must be a JSON object of booleans.")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Recommend an agent structure from signals.")
    parser.add_argument("--signals", help="path to signals JSON ('-' for stdin)")
    parser.add_argument("--print-template", action="store_true", help="emit a blank signals JSON")
    parser.add_argument("--json", action="store_true", help="emit JSON result")
    args = parser.parse_args(argv)

    if args.print_template:
        sys.stdout.write(template())
        return 0
    if not args.signals:
        parser.error("provide --signals <file|-> or --print-template")

    signals = load_signals(args.signals)
    result = recommend(signals)
    print(json.dumps(result, indent=2) if args.json else render(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
