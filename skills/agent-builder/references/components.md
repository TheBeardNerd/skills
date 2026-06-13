# Components: Model, Tools, Instructions

Every agent reduces to three components (OpenAI). Design each deliberately — most
agent failures trace to a weak tool description or a vague instruction, not a weak
model.

## Model

Different models trade off capability, latency, and cost. Not every step needs the
smartest model — classification or retrieval can run on a small fast one; a refund
decision wants a capable one. You may mix models across steps.

Principled approach:
1. **Set up evals** to establish a performance baseline.
2. **Prototype with the most capable model** (default `claude-opus-4-8`) for every
   step to hit the accuracy target first — don't prematurely limit ability.
3. **Then downgrade** individual steps to smaller/faster models (e.g. Haiku) where
   evals show no loss. This diagnoses where small models succeed or fail.

Record the model per step in the blueprint.

## Tools

Tools extend the agent to read context and take action. Three types (OpenAI):

| Type | Purpose | Examples |
|------|---------|----------|
| **Data** | Retrieve context to execute the workflow | query a DB/CRM, read a PDF, web search |
| **Action** | Change state / interact with systems | send email, update a record, file a ticket |
| **Orchestration** | Other agents exposed as tools | research agent, writer agent (manager pattern) |

### Tool design (the agent-computer interface)

The tool description is how the model decides *whether and how* to call it — treat
it like a function signature you're documenting for a careful but literal colleague.
Anthropic calls this the ACI, and says invest in it as much as the human-facing UX.

- **Standardize the definition**: clear name, typed parameters, a description that
  states what it does, when to use it, and what it returns.
- **Include example usage and edge cases**; state boundaries explicitly.
- **Pick a format natural to the model.** Avoid formats that demand bookkeeping the
  model is bad at (counting lines, escaping). Give it room to "think" before
  committing to a rigid structure.
- **Poka-yoke** (mistake-proof) the interface: design parameters so wrong calls are
  hard — e.g. require an absolute path instead of a relative one; use enums for
  fixed choices; make destructive params explicit.
- **Reusable, many-to-many**: one well-documented tool shared across agents beats
  redundant near-duplicates. Overlapping/duplicative tools cause wrong-tool errors —
  the real trigger for splitting into multiple agents (not raw tool count; some
  agents handle 15+ distinct tools, others struggle below 10 overlapping ones).
- **Test extensively.** Run many example inputs through each tool in isolation.

Claude-native tool definition shape:
```python
{
  "name": "get_order",
  "description": "Look up an order by its ID. Use when the user references an "
                 "order number. Returns status, items, and ship date as JSON. "
                 "Returns {\"error\": \"not_found\"} if the ID is unknown.",
  "input_schema": {
    "type": "object",
    "properties": {"order_id": {"type": "string", "description": "e.g. 'A-10423'"}},
    "required": ["order_id"],
  },
}
```

## Instructions

Clear instructions reduce ambiguity and cut errors more than any other lever.

- **Use existing docs**: derive routines from current SOPs, support scripts, policy
  docs, or KB articles — don't invent procedure from scratch.
- **Break tasks into explicit numbered steps**; each step maps to a concrete action
  or output (ask for the order number; call `get_order`; ...). Specify even the
  wording of user-facing messages where it matters.
- **Capture edge cases**: anticipate missing info, unexpected questions, and add
  conditional branches ("if no order number, ask for it before continuing").
- **State the stop condition in prose**: "You are done when ... — then give the
  final answer without calling more tools." The model's natural stop (no tool call)
  is your loop's exit; instructions must make "done" unambiguous.
- **Template over proliferation**: a single base prompt with policy variables
  (`{{user_tier}}`, `{{allowed_actions}}`) scales better than many bespoke prompts.
- You can use a capable model to *generate* a first-draft instruction set from a
  policy document, then refine.

## Putting it together

The scaffold wires these into `config.py` (model + instructions), `tools.py` (tool
schemas + bodies + registry), and `guardrails.py`. Keep each component legible and
independently testable — that is what makes the agent maintainable.
