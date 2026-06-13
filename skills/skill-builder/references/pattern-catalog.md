# Pattern Catalog

Behavioral patterns for skills that *do* multi-step work, with the one-line rule
for when each applies. Source: Anthropic, "Building Effective Agents"; OpenAI,
"A Practical Guide to Building Agents." **Default to the simplest pattern that
works** and only escalate with a reason.

## Workflows (predictable, orchestrated paths)

| Pattern | Use when | Cost |
|---------|----------|------|
| **None (single prompt / tool loop)** | The task fits one well-scoped pass, optionally with tools. | Lowest. The right answer for most skills. |
| **Prompt chaining** | The task decomposes into *fixed sequential steps*, each building on the last (e.g. outline → draft → polish). Add a gate-check between steps. | Low. Adds latency per step. |
| **Routing** | Inputs fall into *distinct categories better handled separately*, and classification is reliable (e.g. refund vs. tech-support vs. sales). | Low. Mis-routing is the main risk. |
| **Parallelization** | Subtasks are independent and can run *simultaneously* for speed, or multiple votes/perspectives raise confidence. | Medium. More tokens; needs aggregation. |
| **Evaluator-optimizer** | There are *clear evaluation criteria* and iterative refinement measurably helps (generate → critique → revise). | Medium. Needs a stop condition. |

## Agents (model-directed paths)

| Pattern | Use when | Cost |
|---------|----------|------|
| **Orchestrator-workers** | A lead step *dynamically decides* the subtasks because they can't be predicted up front, then delegates each to a worker (often a subagent). | High. Coordination + token cost. |
| **Autonomous agent** | Open-ended problems where the *number of steps can't be predicted* and the model can be trusted to drive a tool loop until done, with guardrails and a stop condition. | Highest. Hardest to make reliable. |

## How to choose

1. Start at "None." Can one good pass do it? Ship that.
2. Fixed steps? → prompt chaining. Distinct input types? → routing.
3. Need speed or consensus across independent subtasks? → parallelization.
4. Quality bar with a checkable rubric? → evaluator-optimizer.
5. Subtasks genuinely unknowable in advance? → orchestrator-workers, then
   autonomous as a last resort.

Every step right of "None" buys capability with latency, cost, and new failure
modes. Record *why* you moved right in the skill spec. For agentic patterns,
always define guardrails and an explicit stop condition.
