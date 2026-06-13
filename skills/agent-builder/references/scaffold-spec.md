# Scaffold Spec Schema

`scaffold_agent.py` consumes a JSON spec describing the agent. Below is the full
schema with an example. Only `name` is strictly required; everything else has sane
defaults, but a real agent fills in tools, instructions, and guardrails.

## Fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `name` | string (kebab-case) | — | **required**; becomes the package/dir feel |
| `description` | string | "" | one line; goes in README/blueprint |
| `pattern` | string | `single-loop` | one of: `single-loop`, `prompt-chaining`, `routing`, `parallelization`, `evaluator-optimizer`, `manager`, `decentralized`, `autonomous` |
| `model` | string | `claude-opus-4-8` | default model for the main agent |
| `max_turns` | int | 10 | hard loop cap (required stop condition) |
| `instructions` | string | placeholder | the system prompt; numbered steps + stop condition |
| `tools` | array | `[]` | see Tool below |
| `guardrails` | array | one input-safety stub | see Guardrail below |
| `subagents` | array | `[]` | used by `manager` / `decentralized` patterns |

### Tool object

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | snake_case; the function name |
| `description` | string | what it does, when to use it, what it returns |
| `type` | string | `data` \| `action` \| `orchestration` |
| `risk` | string | `low` \| `medium` \| `high` (drives approval gating) |
| `parameters` | object | `{param_name: {"type": ..., "description": ...}}` |
| `required` | array | required parameter names |

### Guardrail object

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | snake_case function name |
| `type` | string | `relevance` \| `safety` \| `pii` \| `moderation` \| `rules` \| `output` |
| `stage` | string | `input` \| `output` |
| `action` | string | what happens on trip (e.g. `refuse`, `redact`, `escalate`) |

### Subagent object (manager / decentralized)

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | snake_case |
| `description` | string | when the manager should delegate to it |
| `instructions` | string | its own system prompt |
| `tools` | array | tool names it owns (defined in `tools`) |

## Example spec

```json
{
  "name": "support-triage-agent",
  "description": "Triages inbound support tickets and resolves or routes them.",
  "pattern": "single-loop",
  "model": "claude-opus-4-8",
  "max_turns": 8,
  "instructions": "You are a support triage agent. 1) Classify the ticket. 2) Look up the order if one is referenced. 3) Resolve simple issues; for refunds over $100, request human approval. You are done when the ticket is resolved or routed — then summarize and stop.",
  "tools": [
    {"name": "get_order", "description": "Look up an order by ID; returns status/items/ship date as JSON.", "type": "data", "risk": "low",
     "parameters": {"order_id": {"type": "string", "description": "e.g. 'A-10423'"}}, "required": ["order_id"]},
    {"name": "issue_refund", "description": "Refund an order. High-risk; needs approval over $100.", "type": "action", "risk": "high",
     "parameters": {"order_id": {"type": "string"}, "amount": {"type": "number"}}, "required": ["order_id", "amount"]}
  ],
  "guardrails": [
    {"name": "safety_check", "type": "safety", "stage": "input", "action": "refuse"},
    {"name": "pii_redact", "type": "pii", "stage": "output", "action": "redact"}
  ],
  "subagents": []
}
```

The scaffolder emits `agent.py`, `tools.py`, `guardrails.py`, `config.py`,
`requirements.txt`, `.env.example`, `README.md`, `blueprint.md`, and `evals/`. Then
populate tool bodies and run `validate_agent.py`.
