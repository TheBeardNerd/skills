# Subagent Structure Decision Framework

Source: the Claude Code subagents documentation
(https://code.claude.com/docs/en/sub-agents). Work the gates top to bottom. The goal
is to choose the *correct artifact* before writing any Markdown — a subagent is one
of several Claude Code building blocks, and it is the wrong choice surprisingly
often.

## Gate 0 — Is a subagent even the right artifact?

A **subagent** is a Markdown file Claude *delegates to* during a session; it runs in
an isolated context with its own tools and returns a summary. That isolation is the
whole value — and the whole limitation. Spend a subagent only where isolation or a
tool wall earns its keep.

### Route elsewhere if a simpler artifact fits

| The need is… | Deliver instead | Why |
|--------------|-----------------|-----|
| A rule that must apply to **every** session unprompted | **CLAUDE.md** | Subagents only run when delegated to; a standing rule belongs in project memory |
| Something that fires **automatically on an event** (after edit, on commit) | a **hook** | The harness fires hooks; subagent delegation is model-driven, not event-driven |
| A reusable prompt/workflow that should run in the **main thread's context** | a **Skill** (or slash command) | A skill loads into the current conversation; a subagent would needlessly start fresh and lose context |
| A task with heavy **back-and-forth** / shared context across phases | the **main conversation** | A subagent starts cold and returns only a summary — isolation works against you |
| External data/API access for the main thread | an **MCP server** | Subagents consume tools; they don't expose new ones to the session |

### A subagent earns its keep when at least one holds

| Signal | Example |
|--------|---------|
| **Verbose side-work** — floods the main context with output you won't reuse | running tests, fetching docs, triaging logs |
| **Capability wall** — you want to constrain what it can do | a read-only code reviewer (no Edit/Write) |
| **Self-contained** — the work returns a clean summary, little iteration | "research module X and report findings" |
| **Reusable worker** — you keep spawning the same kind of worker | a standard reviewer/test-runner you invoke often |

If none apply, do the work in the main conversation (or write a Skill). Don't ship a
subagent for a one-off inline task. The deterministic recommender encodes this gate:
`recommend_structure.py`.

## Gate 1 — Topology (how many subagents, who drives)

Once a subagent is warranted, pick the **simplest** topology. Full sketches in
[patterns.md](./patterns.md); the recommender encodes this table.

| Topology | Use when | Cost |
|----------|----------|------|
| **Single subagent** | One focused job; isolated context or a tool wall. | Lowest |
| **Parallel (main-driven)** | Independent investigations run at once; main thread synthesizes. | Medium |
| **Chained (main-driven)** | Ordered stages, often with a capability split (review → fix). | Medium |
| **Coordinator + nested** | A delegated task fans out *and* its intermediate noise must stay hidden. | High |

**Maximize a single subagent first.** Most "multi-agent" needs are just the main
conversation spawning one reusable subagent several times, or chaining two. Reach for
nested (`Agent` in the subagent's tools) only with a written reason.

## Gate 2 — Components

Design the three parts per [components.md](./components.md): the **system prompt**
(role + "When invoked" steps + output format + stop condition), the **tools**
(least-privilege allowlist), and the **model** (haiku for volume, opus for judgment,
inherit otherwise).

## Gate 3 — Guardrails & human-in-the-loop

You configure, not code, guardrails per [guardrails.md](./guardrails.md): the tool
wall first, then `permissionMode` (keep `default` so risky actions still prompt the
user), then `PreToolUse` hooks for conditional rules. The prompt explains the
boundaries; it does not enforce them.

## Output of this phase

A short **blueprint** ([templates/blueprint.md](../templates/blueprint.md)): the
Gate-0 verdict (subagent or route-elsewhere), the topology with a one-line rationale,
the components (system-prompt sketch, tool list, model), the guardrail config, and an
eval plan. Show it before scaffolding.
