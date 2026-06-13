---
name: agent-builder
description: Use when the user wants to build, design, or structure an AI agent — e.g. "build an agent that triages support tickets", "should this be an agent or a workflow?", "how should this agent be structured?", or "turn this workflow into an agent". Decides workflow-vs-agent and the right orchestration pattern, then scaffolds a complete, runnable Claude-native agent (deterministic tool-use loop, tools, guardrails, evals) plus a design blueprint.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Agent Builder

## Overview

This skill turns a task description into a **complete, runnable AI agent**. Its
edge is **deciding the correct structure first** — whether the job even needs an
agent, and if so which pattern — then generating a Claude-native deterministic
tool-use loop with tools, guardrails, and evals around that decision.

The structure decision is the whole point. A wrong structure (an autonomous agent
where a single prompt would do, or a single prompt where the job genuinely needs a
loop) is the most expensive mistake you can make. Work the phases in order; do not
jump to scaffolding before the structure is settled in Phase 2.

## When to Use

- "Build / design / make an agent that ...", "turn this workflow into an agent"
- "Should this be an agent or a workflow?", "how should I structure this agent?"
- "Is an agent overkill here?", "what pattern should this use?"
- Restructuring or reviewing the design of an existing agent

**When NOT to use:** Building a *Claude Skill* (use `skill-builder`); wiring a tool
that fires automatically on an event (that is a hook); a one-off prompt that needs
no loop or tools (just write the prompt — say so and stop). If a single augmented
LLM call answers the need, the honest deliverable is *not* an agent; Phase 2 will
catch this.

## Phase 1 — Intake (adaptive)

Gather the signals that drive the structure decision. If the brief already covers
them, proceed; otherwise ask only for the missing ones — targeted questions, not a
survey.

- **Goal / workflow**: the outcome, and the steps a human would take to get there.
- **Decision character**: rule-based and predictable, or nuanced judgment over
  unstructured input? (This is the agent-vs-deterministic test.)
- **Step predictability**: are the steps fixed and known up front, or discovered as
  the task unfolds?
- **Inputs / outputs**: what comes in, what the agent must produce.
- **Tools / systems**: what it must read from and act on (APIs, DBs, files, web).
- **Autonomy & risk**: how many turns unattended; any irreversible/high-risk
  actions (writes, payments, emails) needing human approval.
- **Constraints**: latency, cost, where it runs.
- 2–3 realistic example prompts the finished agent must handle.

## Phase 2 — Decide structure (the core)

Work [decision-framework.md](./references/decision-framework.md) top to bottom:

1. **Gate 0 — does this even need an agent?** Run the agent-vs-deterministic test.
   If a single augmented LLM call (model + retrieval + tools) suffices, say so and
   stop — recommend that instead. Build an agent only for workflows with nuanced
   decisions, unwieldy rulesets, or heavy unstructured-data interpretation.
2. **Gate 1 — pick the pattern.** Encode the signals from Phase 1 as JSON and run
   the recommender for a reproducible verdict:

   ```bash
   SKILL_DIR="${SKILL_DIR:-$HOME/.claude/skills/agent-builder}"
   python3 "$SKILL_DIR/scripts/recommend_structure.py" --signals signals.json
   ```

   It returns a recommended pattern (single-loop, prompt-chaining, routing,
   parallelization, evaluator-optimizer, orchestrator-workers/manager, or
   decentralized) with a rationale. Treat it as a strong prior, not gospel — read
   [patterns.md](./references/patterns.md) and confirm it fits. **Bias to the
   simplest pattern that works**; every step toward multi-agent buys capability
   with latency, cost, and new failure modes, so record *why* you escalated.
3. **Gate 2 — design the components.** Per [components.md](./references/components.md):
   model (start capable, downgrade where evals allow), tools (data / action /
   orchestration, each documented and poka-yoke'd), and instructions (explicit
   steps, edge cases, stop behavior).
4. **Gate 3 — guardrails & human-in-the-loop.** Per
   [guardrails.md](./references/guardrails.md): layered defense (relevance, safety,
   PII, moderation, rules-based, output validation) and approval gates on
   high-risk tools.

Then write the **blueprint** to the user using
[templates/blueprint.md](./templates/blueprint.md) and show it before scaffolding.
The blueprint records the verdict, the pattern + rationale, components, the runtime
loop (state, stop conditions, max turns — see [runtime.md](./references/runtime.md)),
guardrails, and an eval plan.

## Phase 3 — Scaffold

Encode the blueprint as a spec JSON (schema in
[scaffold-spec.md](./references/scaffold-spec.md)) and generate the project:

```bash
SKILL_DIR="${SKILL_DIR:-$HOME/.claude/skills/agent-builder}"
python3 "$SKILL_DIR/scripts/scaffold_agent.py" --spec agent-spec.json --out ./<agent-name>
```

This emits a complete Claude-native agent: `agent.py` (the deterministic tool-use
loop), `tools.py` (Anthropic tool schemas + implementation stubs + registry),
`guardrails.py`, `config.py`, `requirements.txt`, `.env.example`, `README.md`, the
filled `blueprint.md`, and an `evals/` starter. It never overwrites without
`--force`.

## Phase 4 — Populate

Fill in the real logic the scaffold left as stubs:

- **Tool bodies** in `tools.py` — each tool's actual API/DB/file call. Keep the
  docstring and JSON schema accurate; the model picks tools from those descriptions.
- **Instructions** in `config.py` — turn the workflow into explicit numbered steps
  with edge-case branches and a clear "you are done when ..." stop instruction.
- **Guardrails** in `guardrails.py` — implement the checks the blueprint named.
- **Sub-agents** (manager/decentralized only) — fill each sub-agent's instructions
  and tools.

Follow the writing principles in [components.md](./references/components.md): clear
tool descriptions beat clever prompting.

## Phase 5 — Validate (hard gate)

```bash
python3 "$SKILL_DIR/scripts/validate_agent.py" ./<agent-name>
```

Fix every `FAIL` and re-run until it prints `RESULT: PASS`. The gate enforces the
non-negotiables of a sound agent: the loop has **both** a natural stop condition
**and** a `max_turns` cap, every tool has a description and JSON schema, at least
one guardrail exists, and high-risk tools have an approval path. Then smoke-test
that the project imports cleanly and the bundled `tests/` pass.

## Phase 6 — Report

Report: the structure verdict (and *why* this pattern, not a simpler one), the file
tree, the validation result, how to run the agent
(`pip install -r requirements.txt`, set `ANTHROPIC_API_KEY`, run `agent.py`), and
the first next step (usually: implement one real tool end-to-end, then run the
evals). Do not commit or push unless the user asks.

## Output

The primary artifact is a generated agent project plus a `blueprint.md`. Report it
to the user as:

```
Structure verdict: <agent | not-an-agent> — <pattern> because <one-line reason>
Generated: ./<agent-name>/  (agent.py, tools.py, guardrails.py, config.py, ...)
Validation: RESULT: PASS
Run it: pip install -r requirements.txt && export ANTHROPIC_API_KEY=... && python agent.py
Next: implement the <X> tool body, then run evals/
```
