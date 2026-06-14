#!/usr/bin/env python3
"""Recommend the right artifact + topology for a Claude Code subagent request.

A Claude Code subagent is a Markdown file in `.claude/agents/` (system prompt +
tool permissions) that Claude delegates to inside an existing Claude Code session.
It is NOT a standalone program. Before scaffolding one, two questions need a
reproducible answer:

  1. Is a subagent even the right artifact? (vs. CLAUDE.md, a hook, a skill, or
     just doing the work in the main conversation.)
  2. If so, what topology? (single subagent, parallel/chained subagents
     orchestrated by the main thread, or a coordinator that spawns nested workers.)

This encodes the guidance in the Claude Code subagents docs as a deterministic
decision tree, so the verdict is reproducible rather than vibes. Treat the output
as a strong prior to confirm against references/decision-framework.md — not gospel.
Bias is always toward the simplest artifact that fits.

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

# All signals are booleans, default False. Grouped by the question they inform.
SIGNAL_KEYS = [
    # Gate 0a — disqualifiers: another artifact fits better than a subagent.
    "always_on_rule",        # must apply to EVERY session unprompted -> CLAUDE.md
    "event_triggered",       # must fire automatically on an event -> hook
    "reusable_prompt_main",  # reusable procedure that must run in the MAIN thread -> skill
    "needs_main_context",    # heavy back-and-forth / shared context across phases -> stay in main
    # Gate 0b — positive signals that a subagent earns its keep.
    "verbose_side_work",     # floods main context with output you won't reuse (logs, search)
    "needs_tool_restriction",# you want to constrain capabilities (e.g. read-only reviewer)
    "self_contained",        # the work returns a summary; little iteration needed
    "reusable_worker",       # you keep spawning the same kind of worker with the same prompt
    # Topology — only consulted once a subagent is warranted.
    "independent_subtasks",  # several independent investigations could run at once
    "sequential_stages",     # one stage's output feeds the next (review -> fix)
    "subtask_fans_out",      # the delegated task itself splits into parallel subtasks
    "intermediate_noise",    # intermediate results should stay out of the main conversation
]


def _b(signals: dict, key: str) -> bool:
    return bool(signals.get(key, False))


def recommend(signals: dict) -> dict:
    """Pure decision function. Returns recommendation, category, and rationale."""
    why: list[str] = []
    ruled_out: list[str] = []
    escalation: list[str] = []

    # --- Gate 0a: route elsewhere if another artifact clearly fits -----------
    if _b(signals, "always_on_rule"):
        return {
            "recommendation": "NOT a subagent — put this in CLAUDE.md",
            "category": "claude-md",
            "why": [
                "The need is an always-on rule that should shape every session "
                "without being asked. Subagents only run when delegated to, so a "
                "rule that must always apply belongs in CLAUDE.md (project memory).",
            ],
            "ruled_out": ["Subagent — it would not fire unless explicitly invoked."],
            "escalation": [],
        }
    if _b(signals, "event_triggered"):
        return {
            "recommendation": "NOT a subagent — use a hook",
            "category": "hook",
            "why": [
                "The need is to fire automatically on an event (after an edit, on "
                "commit, before a tool runs). The harness fires hooks; Claude must "
                "choose to delegate to a subagent. Configure a hook in settings.json.",
            ],
            "ruled_out": ["Subagent — delegation is model-driven, not event-driven."],
            "escalation": [],
        }
    if _b(signals, "reusable_prompt_main") and not (
        _b(signals, "verbose_side_work") or _b(signals, "needs_tool_restriction")
    ):
        return {
            "recommendation": "NOT a subagent — write a Skill (or slash command)",
            "category": "skill",
            "why": [
                "The need is a reusable prompt/workflow that should run in the MAIN "
                "conversation's context (no isolation, no tool walls). A Skill loads "
                "on demand into the current thread; a subagent would needlessly start "
                "fresh and lose the shared context.",
            ],
            "ruled_out": ["Subagent — isolation buys nothing here."],
            "escalation": [],
        }
    if _b(signals, "needs_main_context") and not (
        _b(signals, "verbose_side_work") or _b(signals, "needs_tool_restriction")
    ):
        return {
            "recommendation": "NOT a subagent — keep this in the main conversation",
            "category": "main-conversation",
            "why": [
                "The task needs frequent back-and-forth or shares significant context "
                "across phases. A subagent starts with a fresh, isolated context and "
                "returns only a summary, so it would lose the thread. Do it inline.",
            ],
            "ruled_out": ["Subagent — context isolation works against this task."],
            "escalation": [],
        }

    # --- Gate 0b: does a subagent earn its keep? -----------------------------
    fit = [
        k for k in (
            "verbose_side_work", "needs_tool_restriction",
            "self_contained", "reusable_worker",
        ) if _b(signals, k)
    ]
    if not fit:
        return {
            "recommendation": "Probably NOT a subagent — no clear isolation/restriction benefit",
            "category": "unclear",
            "why": [
                "None of the subagent payoffs are present: no verbose side-work to "
                "isolate, no need to restrict tools, not clearly self-contained, and "
                "not a repeated worker. Default to doing it in the main conversation, "
                "or a Skill if it is a reusable procedure.",
            ],
            "ruled_out": [],
            "escalation": [
                "If you DO expect to repeat this work, set reusable_worker and re-run.",
            ],
        }
    why.append("Subagent fit: " + ", ".join(fit) + " -> isolating this work pays off.")

    # --- Topology: simplest that fits ----------------------------------------
    if _b(signals, "subtask_fans_out") and _b(signals, "intermediate_noise"):
        rec, cat = "coordinator subagent (spawns nested workers)", "subagent"
        why.append(
            "The delegated task itself fans out into parallel subtasks, and the "
            "intermediate output should stay out of the main conversation -> a "
            "coordinator subagent (with the Agent tool) dispatches nested workers."
        )
        escalation.append(
            "Nesting adds depth + cost. Confirm a single subagent (or the main "
            "thread spawning the workers) can't do it first. Requires `Agent` in "
            "the coordinator's tools; needs Claude Code v2.1.172+."
        )
    elif _b(signals, "independent_subtasks"):
        rec, cat = "parallel subagents (orchestrated by the main thread)", "subagent"
        why.append(
            "Several independent investigations can run at once. Have the MAIN "
            "conversation spawn one subagent per area and synthesize the results — "
            "you usually build ONE reusable subagent definition and invoke it N times."
        )
        escalation.append("Each subagent's summary returns to the main context; keep them lean.")
    elif _b(signals, "sequential_stages"):
        rec, cat = "chained subagents (orchestrated by the main thread)", "subagent"
        why.append(
            "Stages run in sequence, each consuming the last (e.g. review -> fix). "
            "The MAIN conversation chains them, passing relevant context between. "
            "Often this is two focused subagent definitions, not one."
        )
    else:
        rec, cat = "single subagent", "subagent"
        why.append("One focused subagent covers it — the default and simplest shape.")
        ruled_out.append("Multi-/nested-subagent — not justified; start with one.")

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
    parser = argparse.ArgumentParser(description="Recommend a subagent artifact + topology from signals.")
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
