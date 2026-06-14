---
name: agent-builder
description: 'Use when the user wants to build, design, or structure a Claude Code subagent — e.g. "build a subagent that reviews code changes", "make a test-runner agent", "should this be a subagent or a skill?", or "turn this workflow into a .claude/agents agent". Decides subagent-vs-other-artifact and the right topology, then scaffolds a native Claude Code subagent (a .claude/agents/<name>.md file: system prompt + tool permissions + model) that runs inside Claude Code using its built-in tools — plus a design blueprint. No standalone program.'
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Agent Builder

## Overview

This skill turns a task description into a **native Claude Code subagent** — a single
`.claude/agents/<name>.md` file with a system prompt, a least-privilege tool list, and
a model. Claude Code *delegates* to it during a session; it runs in its own context
using the **built-in file/shell/web tools**. There is **no separate program to run,
no SDK, no API key, no loop to write** — the harness owns all of that.

The edge of this skill is **deciding the correct structure first** — whether the job
even wants a subagent (vs. CLAUDE.md, a hook, a skill, or just the main conversation),
and if so which topology — then generating a focused subagent around that decision.
Work the phases in order; do not jump to scaffolding before the structure is settled
in Phase 2.

## When to Use

- "Build / design / make a subagent (or `.claude/agents` agent) that ..."
- "Turn this workflow into a subagent", "make a reusable reviewer/test-runner agent"
- "Should this be a subagent or a skill/hook?", "how should I structure this agent?"
- Restructuring or reviewing the design of an existing subagent

**When NOT to use** (route elsewhere — Phase 2 Gate 0 catches these):
- An **always-on rule** for every session → CLAUDE.md.
- Something that **fires automatically on an event** (after edit, on commit) → a hook.
- A reusable prompt/workflow that should run in the **main thread** → a *Skill* (use
  `skill-builder`) or a slash command.
- A task with heavy **back-and-forth** / shared context → just the main conversation.
- New **external data/API** access → an MCP server.

This skill builds Claude Code subagents specifically. It does **not** build standalone
agent apps (Anthropic SDK loops, etc.).

## Phase 1 — Intake (adaptive)

Gather the signals that drive the decision. If the brief already covers them, proceed;
otherwise ask only for the missing ones — targeted questions, not a survey.

- **Job**: the outcome, and the steps a careful colleague would take from a cold start.
- **Why isolate it**: does it flood the main context with output (logs/search/tests),
  need a capability wall, return a clean summary, or get reused often? (the
  subagent-vs-alternatives test).
- **Tools/systems**: what built-in tools it must touch (Read, Bash, web, MCP) — and
  what it must **not** be able to do.
- **Risk**: any irreversible/high-impact actions (writes, deletes, network, payments)?
- **Model**: high-volume/cheap (haiku), balanced (sonnet), or judgment-heavy (opus)?
- **Scope**: personal (`~/.claude/agents/`, the default, available in all your
  projects) or project (`.claude/agents/`, checked in and shared with the team).
- 2–3 realistic example tasks the finished subagent must handle.

## Phase 2 — Decide structure (the core)

Work [decision-framework.md](./references/decision-framework.md) top to bottom:

1. **Gate 0 — is a subagent the right artifact?** Run the routing table. If the need
   is an always-on rule / event trigger / main-thread workflow / chatty task, **say so
   and recommend the simpler artifact** instead. Continue only when isolation or a tool
   wall genuinely earns its keep.
2. **Gate 1 — pick the topology.** Encode the signals as JSON and run the recommender
   for a reproducible verdict:

   ```bash
   SKILL_DIR="${SKILL_DIR:-$HOME/.claude/skills/agent-builder}"
   python3 "$SKILL_DIR/scripts/recommend_structure.py" --print-template > signals.json
   # edit signals.json, then:
   python3 "$SKILL_DIR/scripts/recommend_structure.py" --signals signals.json
   ```

   It returns an artifact verdict and (if a subagent) a topology — single, parallel
   (main-driven), chained (main-driven), or coordinator+nested. Read
   [patterns.md](./references/patterns.md) and confirm. **Bias to a single subagent**;
   record *why* if you escalate to multiple or nested.
3. **Gate 2 — design the components.** Per [components.md](./references/components.md):
   the **system prompt** (role + "When invoked" steps + output format + stop line), the
   **tools** (least-privilege allowlist — see [execution-model.md](./references/execution-model.md)
   for what the subagent does and doesn't inherit), and the **model**.
4. **Gate 3 — guardrails.** Per [guardrails.md](./references/guardrails.md): the tool
   wall first, then `permissionMode` (keep `default` so risky actions still prompt the
   user), then a `PreToolUse` hook only if you must allow part of a tool and block the
   rest. You *configure* guardrails; you don't code them.

Then write the **blueprint** to the user using
[templates/blueprint.md](./templates/blueprint.md) and show it before scaffolding.

## Phase 3 — Scaffold

Encode the blueprint as a spec JSON (schema in
[scaffold-spec.md](./references/scaffold-spec.md)) and generate the file:

```bash
SKILL_DIR="${SKILL_DIR:-$HOME/.claude/skills/agent-builder}"
python3 "$SKILL_DIR/scripts/scaffold_agent.py" --print-spec > agent-spec.json
# fill in agent-spec.json, then (default user scope -> ~/.claude/agents/<name>.md):
python3 "$SKILL_DIR/scripts/scaffold_agent.py" --spec agent-spec.json
# or --scope project (-> ./.claude/agents/, checked in), or --out <dir> to override.
```

This emits one Markdown file: YAML frontmatter (`name`, `description`, `tools`,
`model`, …) plus the system prompt as the body. It refuses tools that never work in a
subagent and never overwrites without `--force`.

## Phase 4 — Populate

Refine the generated file into a sharp subagent (full detail in
[components.md](./references/components.md)):

- **`description`** — trigger-first; what it does *and when to delegate*. This is the
  single biggest lever for whether the subagent ever fires. Add "use proactively" to
  encourage auto-delegation.
- **System prompt body** — it runs from a **cold start** (the subagent sees none of the
  conversation). Make it self-contained: role, numbered "When invoked" steps, edge
  cases (it can't ask the user mid-run), an explicit **output format**, and a clear
  "you are done when …" stop line. Tell it to return a tight summary, not raw dumps.
- **`tools`** — tighten to least privilege; remove anything the job doesn't need.
- **Guardrails** — set `permissionMode` / add a `PreToolUse` hook only if Phase 2 called
  for it.

## Phase 5 — Validate (hard gate)

```bash
python3 "$SKILL_DIR/scripts/validate_agent.py" ./.claude/agents/<name>.md
```

Fix every `FAIL` and re-run until it prints `RESULT: PASS`. The gate enforces what
makes a subagent load and behave: parseable frontmatter, a kebab-case `name`, a
non-empty `description`, a non-empty system prompt, a valid `model`, and no UI-only
tools (`AskUserQuestion`, `EnterPlanMode`, …) that never work in a subagent. Use
`--strict` to also clear warnings (e.g. missing tool allowlist, weak description).

## Phase 6 — Report

Report: the structure verdict (and *why* this artifact + topology, not a simpler one),
the generated file path, the validation result, and how to use it. Do not commit or
push unless the user asks.

## Output

The primary artifact is one `.claude/agents/<name>.md` file plus a blueprint shown in
chat. Report it as:

```
Structure verdict: <subagent | route-elsewhere> — <topology> because <one-line reason>
Generated: ~/.claude/agents/<name>.md  (system prompt + tools: <list> + model: <model>)
Validation: RESULT: PASS
Use it: "use the <name> subagent" / @agent-<name>  (restart the session to load a hand-added file)
Next: run the Phase-1 example tasks against it; use --scope project to check it into a repo.
```
