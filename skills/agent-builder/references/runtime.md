# The Runtime: A Deterministic Loop

An agent is not magic — it is a **deterministic loop** wrapped around a
non-deterministic model. The code that runs the loop is fully predictable: it sends
messages, reads the response, runs any requested tools, appends the results, and
repeats. The only stochastic part is what the model decides inside each turn. Keeping
that boundary clear is what makes an agent debuggable.

## The loop (perceive → reason → act → observe)

```
            ┌─────────────────────────────────────────────┐
            │                                             │
   user ──► messages ──► model.create(tools) ──► response │
            ▲                                       │      │
            │                          stop_reason? ┤      │
            │                                       │      │
   tool_results ◄── run_tools(tool_use blocks) ◄────┘ (tool_use)
            │                                       │
            │                          (end_turn) ──┴──► final answer ──► done
            └─────────────────────────────────────────────┘
```

1. **Perceive**: the current `messages` list is the agent's entire state.
2. **Reason**: `client.messages.create(...)` — the model thinks and may emit
   `tool_use` blocks.
3. **Act**: if `stop_reason == "tool_use"`, execute each requested tool.
4. **Observe**: append `tool_result` blocks to `messages` and loop.
5. **Stop**: if `stop_reason != "tool_use"` (a final answer), or a stop condition
   trips, exit.

## Claude-native loop (the canonical shape)

```python
messages = [{"role": "user", "content": user_input}]
for turn in range(MAX_TURNS):                      # hard cap — guardrail
    resp = client.messages.create(
        model=MODEL, max_tokens=2048,
        system=INSTRUCTIONS, tools=TOOL_SCHEMAS,
        messages=messages,
    )
    messages.append({"role": "assistant", "content": resp.content})

    if resp.stop_reason != "tool_use":             # natural stop: final answer
        return text_of(resp)

    tool_results = []
    for block in resp.content:
        if block.type == "tool_use":
            output = REGISTRY[block.name](**block.input)   # run the tool
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(output),
            })
    messages.append({"role": "user", "content": tool_results})

raise RuntimeError("max turns exceeded")           # the cap fired
```

## State

State **is** the `messages` list — an append-only transcript of user input,
assistant turns (text + tool_use), and tool_result turns. Two rules keep it valid:

- Every `tool_use` block **must** be answered by a `tool_result` with the matching
  `tool_use_id` in the very next user turn, or the API errors.
- Don't mutate past turns; only append. The transcript is the audit log.

For long runs, summarize or trim *old* turns (keeping the system prompt and recent
context) rather than letting the window blow up. Persist `messages` if the agent
needs to resume across sessions.

## Stop conditions (every agent needs at least two)

A loop without a hard stop is a runaway. Always combine:

1. **Natural stop** — the model returns a final answer (`stop_reason != "tool_use"`).
   The instructions must make "you are done when ..." unambiguous so this fires.
2. **Max turns** — a hard integer cap so a confused agent can't loop forever.

Add as needed:
3. **Budget cap** — max tokens/cost across the run.
4. **Error/failure threshold** — after N tool errors or no-progress turns, halt and
   hand back to a human (see [guardrails.md](./guardrails.md)).
5. **Explicit done-tool** — a `submit_final_answer` tool whose call ends the run
   (useful when you need a structured final output).

The validator fails any agent loop missing both a natural stop and a `max_turns`
cap — that pair is the non-negotiable minimum.

## Errors and resilience

- Wrap each tool call; on exception, return a `tool_result` with `is_error` /
  an error payload so the model can recover or retry, instead of crashing the loop.
- Make tools idempotent where possible so a retry is safe.
- Log every turn (model, tools called, results) — the loop's determinism means a log
  replays exactly what happened.
