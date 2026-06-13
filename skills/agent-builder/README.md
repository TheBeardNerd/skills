# agent-builder

Decides the **correct structure** of an AI agent — whether the job even needs an
agent, and if so which pattern — then scaffolds a complete, runnable Claude-native
agent (deterministic tool-use loop, tools, guardrails, evals) plus a design
blueprint. Grounded in Anthropic's "Building Effective Agents" and OpenAI's
"Practical Guide to Building Agents."

## Install

```bash
npx skills add https://github.com/TheBeardNerd/skills --skill agent-builder
```

## Usage

| Intent | Example prompt |
|--------|----------------|
| Build an agent | `"Build an agent that triages support tickets and issues refunds"` |
| Decide structure | `"Should this be an agent or a workflow?"` |
| Right-size a design | `"Is a multi-agent setup overkill for answering FAQ from our docs?"` |
| Convert a workflow | `"Turn this manual review process into an agent"` |

## How It Works

Six phases, structure-first:

1. **Intake** — gather the signals that drive the decision (decision character, step
   predictability, tools, autonomy/risk).
2. **Decide structure** — Gate 0 (does it even need an agent?) → pattern selection
   via `recommend_structure.py` (a deterministic encoding of the decision tables) →
   components → guardrails. Output: a blueprint shown before any code.
3. **Scaffold** — `scaffold_agent.py` emits a runnable project: `agent.py` (the
   deterministic tool-use loop), `tools.py`, `guardrails.py`, `config.py`, plus
   requirements, README, blueprint, and evals.
4. **Populate** — fill tool bodies, instructions, and guardrail logic.
5. **Validate** — `validate_agent.py` is a hard gate: the loop must have both a
   natural stop and a `max_turns` cap, every tool needs a description + schema, at
   least one input guardrail, and high-risk tools must have a human-approval path.
6. **Report** — verdict, file tree, validation result, run instructions.

The generated agent targets Claude's Messages API natively
(`client.messages.create`, looping on `stop_reason == "tool_use"`).

## Scripts

```bash
SKILL_DIR=~/.claude/skills/agent-builder

# Reproducible structure verdict from a signals JSON
python3 "$SKILL_DIR/scripts/recommend_structure.py" --print-template > signals.json
python3 "$SKILL_DIR/scripts/recommend_structure.py" --signals signals.json

# Generate a complete agent
python3 "$SKILL_DIR/scripts/scaffold_agent.py" --print-spec > agent-spec.json
python3 "$SKILL_DIR/scripts/scaffold_agent.py" --spec agent-spec.json --out ./my-agent

# Hard gate
python3 "$SKILL_DIR/scripts/validate_agent.py" ./my-agent
```

## Tests

```bash
python3 -m unittest discover -s tests
```
