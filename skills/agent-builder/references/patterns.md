# Pattern Catalog (Claude-native)

Each pattern with when-to-use and a minimal Claude-native sketch. All build on the
**augmented LLM** — a model with tools, retrieval, and memory — looping via the
Anthropic Messages API (`client.messages.create`, `stop_reason == "tool_use"`). See
[runtime.md](./runtime.md) for the loop mechanics. **Default to the simplest pattern
that works.**

## Building block — the augmented LLM call

```python
resp = client.messages.create(
    model="claude-opus-4-8",
    max_tokens=1024,
    system=INSTRUCTIONS,
    tools=TOOLS,                 # JSON-schema tool defs
    messages=[{"role": "user", "content": user_input}],
)
```

If a single such call (optionally with retrieval/one tool) answers the task, you do
not have an agent — and that is the right outcome. Ship it.

## Workflows

### Prompt chaining
Fixed sequential steps, each consuming the last; add a gate between steps to catch
errors early.
```python
outline = call(model, "Outline: " + topic)
if not gate_ok(outline):
    raise ValueError("outline failed gate")
draft = call(model, "Write from outline:\n" + outline)
final = call(model, "Polish:\n" + draft)
```
Use for: outline→draft→polish, generate→translate, extract→format.

### Routing
Classify the input, then dispatch to a specialized prompt/tool/model. Mis-routing is
the main risk — keep categories distinct and classification reliable.
```python
route = call(small_model, CLASSIFY_PROMPT + query)   # -> "billing" | "tech" | "sales"
handler = HANDLERS[route]
answer = handler(query)
```
Use for: customer-service triage, easy→small-model / hard→large-model.

### Parallelization
- **Sectioning**: split into independent subtasks, run concurrently, aggregate.
- **Voting**: run the same task N times, take consensus/majority.
```python
import concurrent.futures as cf
with cf.ThreadPoolExecutor() as ex:
    parts = list(ex.map(work, subtasks))
result = aggregate(parts)
```
Use for: independent sub-analyses for speed; multiple safety checks at once; voting
for higher confidence.

### Evaluator-optimizer
Generator produces; evaluator critiques against a rubric; loop until it passes or a
cap is hit (always set a stop condition).
```python
draft = generate(task)
for _ in range(MAX_ROUNDS):
    verdict = evaluate(draft)        # {pass: bool, feedback: str}
    if verdict["pass"]:
        break
    draft = generate(task, feedback=verdict["feedback"])
```
Use for: literary translation, code that must pass criteria, iterative search.

## Agents

### Single-loop agent (the default agent)
One agent with tools runs the deterministic loop until it stops calling tools or
hits `max_turns`. This is the standard agent and what `scaffold_agent.py` emits by
default. See [runtime.md](./runtime.md).
```python
while turns < MAX_TURNS:
    resp = client.messages.create(model=..., system=..., tools=TOOLS, messages=messages)
    messages.append({"role": "assistant", "content": resp.content})
    if resp.stop_reason != "tool_use":
        break                        # natural stop: a final answer
    results = run_tools(resp.content)
    messages.append({"role": "user", "content": results})
```

### Orchestrator-workers / manager (agents-as-tools)
A manager agent decides subtasks *dynamically* and calls specialized sub-agents
exposed as tools, then synthesizes. The manager keeps control and the user-facing
thread. Use when subtasks can't be predicted up front, or one agent's tools/prompt
overflow.
```python
# Each sub-agent is wrapped as a tool the manager can call:
TOOLS = [as_tool(research_agent), as_tool(writer_agent), as_tool(review_agent)]
# Manager runs the single-loop above over these "tools".
```

### Decentralized / handoff
Peer agents transfer *full control* (and conversation state) to one another by
specialization. A handoff is a tool that swaps the active agent. Use when no single
agent needs to stay in control or synthesize — e.g. triage → specialist who takes
over.
```python
active = triage_agent
while not done:
    resp = run_one_turn(active, messages)
    if handoff := detect_handoff(resp):     # e.g. "transfer_to_orders"
        active = AGENTS[handoff]             # new agent owns the thread now
```

### Autonomous agent
Open-ended; the model drives the loop with broad tools until the task is done.
Highest risk. Mandatory: tight guardrails, sandboxed tools, human approval on
irreversible actions, and a hard `max_turns` / budget stop. Only when the step
count is genuinely unpredictable and the model can be trusted in the domain.

## Escalation discipline

Every row below "single augmented call" buys capability with latency, cost, and new
failure modes. Move down only with a written reason in the blueprint. For any agentic
pattern, define guardrails and an explicit stop condition before scaffolding.
