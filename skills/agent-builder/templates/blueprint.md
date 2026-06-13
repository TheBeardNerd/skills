# Agent Blueprint: <agent-name>

> Filled during Phase 2 and shown to the user before scaffolding. Each section
> records a decision and its rationale.

## 1. Verdict — is this an agent?

- **Decision:** <agent | workflow | single augmented call — NOT an agent>
- **Why:** <which Gate-0 signal applies: complex decision-making /
  difficult-to-maintain rules / heavy unstructured data — or, if not an agent, why a
  simpler shape suffices>

> If "NOT an agent", stop here and recommend the simpler solution.

## 2. Pattern

- **Pattern:** <single-loop | prompt-chaining | routing | parallelization |
  evaluator-optimizer | manager | decentralized | autonomous>
- **Why this and not something simpler:** <one line; the recommender's rationale +
  your confirmation>
- **Recommender output:** <paste `recommend_structure.py` verdict>

## 3. Components

### Model
- **Default:** claude-opus-4-8 (baseline) → <downgrade plan per step, if any>

### Tools
| Tool | Type | Risk | Purpose |
|------|------|------|---------|
| <name> | data/action/orchestration | low/med/high | <what it does> |

### Instructions (sketch)
<numbered steps the agent follows, with edge-case branches and the explicit
"you are done when ..." stop condition>

## 4. Runtime loop

- **Loop:** Claude-native tool-use loop (`stop_reason == "tool_use"`).
- **State:** append-only `messages` transcript.
- **Stop conditions:** natural stop (final answer) + `max_turns = <N>`
  + <budget / failure-threshold / done-tool, if any>.

## 5. Guardrails & human-in-the-loop

| Guardrail | Stage | Type | Action on trip |
|-----------|-------|------|----------------|
| <name> | input/output | relevance/safety/pii/moderation/rules/output | refuse/redact/escalate |

- **Human approval required for:** <high-risk tools / actions>

## 6. Sub-agents (manager / decentralized only)

| Sub-agent | Delegated when | Tools |
|-----------|----------------|-------|
| <name> | <condition> | <tools> |

## 7. Eval plan

- **Scenarios:** <2–3 realistic prompts the agent must handle>
- **Success criteria:** <what "correct" looks like per scenario>
- **Pressure cases:** <off-topic input, ambiguous input, hostile/jailbreak input>
