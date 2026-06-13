# Agent Structure Decision Framework

Sources: Anthropic, "Building Effective Agents"; OpenAI, "A Practical Guide to
Building Agents." Work the gates top to bottom. The goal is to choose the *correct
shape* before any code is written.

## Gate 0 — Does this even need an agent?

An **agent** is a system where an LLM *dynamically directs its own process and tool
use* over multiple turns to accomplish a task. That power costs latency, tokens, and
reliability. Most "AI feature" needs are met by something simpler. Spend an agent
only where it earns its keep.

### The agent-vs-deterministic test

Build an agent when the workflow has **at least one** of these (OpenAI's criteria):

| Signal | Example |
|--------|---------|
| **Complex decision-making** — nuanced judgment, exceptions, context | refund approval, fraud triage |
| **Difficult-to-maintain rules** — brittle, sprawling rulesets | vendor security reviews |
| **Heavy unstructured-data reliance** — language, documents, dialogue | processing an insurance claim |

If none apply — the logic is a clean checklist a rules engine handles — **say so and
recommend the deterministic solution**. Do not ship an agent for a `if/else`.

### The "is it even an agent?" ladder (route elsewhere if simpler fits)

| The need is... | Deliver instead | Why |
|----------------|-----------------|-----|
| One LLM call, maybe with retrieval/a tool | an **augmented LLM call** | No loop needed; lowest latency/cost |
| Fixed, known sequence of LLM steps | a **workflow** (prompt chaining/routing) | Predefined code paths beat dynamic control when the path is known |
| Dynamic, unpredictable control over many turns | an **agent** | Only here does model-directed looping pay off |

Anthropic's rule: **find the simplest solution possible, and only increase
complexity when it demonstrably improves outcomes.** Continue past this gate only
when the dynamic, multi-turn, tool-using shape is genuinely required.

## Gate 1 — Pick the pattern

Workflows (predefined paths) vs agents (model-directed paths). Prefer the highest
row that satisfies the task. Full sketches in [patterns.md](./patterns.md); the
deterministic recommender encodes this table.

### Workflows — predictable, orchestrated

| Pattern | Use when | Cost |
|---------|----------|------|
| **Single augmented call** | One well-scoped pass (+ optional retrieval/tool) answers it. | Lowest |
| **Prompt chaining** | Fixed sequential steps, each building on the last; gate-check between. | Low |
| **Routing** | Inputs fall into distinct categories handled separately; classification is reliable. | Low |
| **Parallelization** | Independent subtasks run at once (sectioning), or repeated votes raise confidence (voting). | Medium |
| **Evaluator-optimizer** | Clear eval criteria + iterative refinement measurably helps (generate→critique→revise). | Medium |

### Agents — model-directed

| Pattern | Use when | Cost |
|---------|----------|------|
| **Single-loop agent** | One agent + tools runs a loop until an exit condition; the standard agent. | Medium |
| **Orchestrator-workers / manager** | A lead agent *dynamically* decides subtasks (unknown up front) and delegates to specialized agents (agents-as-tools). | High |
| **Decentralized / handoff** | Peer agents hand off full control to one another by specialization (triage → specialist). | High |
| **Autonomous agent** | Open-ended; step count unpredictable; model trusted to drive until done, with guardrails + stop condition. | Highest |

### How to choose

1. Start at "single augmented call." Can one good pass do it? Ship that, not an agent.
2. Fixed known steps? → prompt chaining. Distinct input types? → routing.
3. Need speed across independent subtasks, or consensus? → parallelization.
4. Checkable quality rubric + refinement helps? → evaluator-optimizer.
5. Genuinely needs dynamic multi-turn tool control? → **single-loop agent first.**
6. One agent's prompt/tools overflow (many if-then branches, >10–15 overlapping
   tools, wrong-tool errors)? → split into manager or decentralized.
7. Steps truly unknowable and high trust warranted? → autonomous, as a last resort.

**Maximize a single agent first.** OpenAI: more agents give intuitive separation but
add complexity and overhead; split only when a single agent with well-named tools
*fails* to follow the logic or pick the right tool. Record *why* you escalated.

## Gate 2 — Components

Every agent reduces to three components (OpenAI): **model**, **tools**,
**instructions**. Design each per [components.md](./components.md).

## Gate 3 — Guardrails & human-in-the-loop

Layered defense plus approval gates on risky actions. See
[guardrails.md](./guardrails.md). An agent that can take irreversible actions
without a guardrail or human checkpoint is not done.

## Output of this phase

A short **blueprint** ([templates/blueprint.md](../templates/blueprint.md)): the
Gate 0 verdict, the chosen pattern with a one-line rationale (and why not a simpler
one), the components, the runtime loop, guardrails, and an eval plan. Show it before
scaffolding.
