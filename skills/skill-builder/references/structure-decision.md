# Structure Decision Framework

The job of this phase is to choose the *correct shape* before writing anything.
Work the gates top to bottom.

## Gate 0 — Is a skill even the right artifact?

A **skill** is reusable procedure or knowledge the agent pulls into context *on
demand, when it decides the moment fits*. If that is not what is needed, route
elsewhere:

| The need is... | Use instead | Why |
|----------------|-------------|-----|
| An always-on rule for one repo | `CLAUDE.md` | Loaded every turn; no trigger needed |
| Fires automatically on an event (post-edit, pre-commit) | a **hook** | The harness runs hooks; a skill only fires when the model chooses to invoke it |
| Live external data or an API | an **MCP server** | Skills are static files, not connections |
| A heavy sub-job that needs its own clean context | a **subagent** | Isolates tokens; a skill can *spawn* one but isn't one |
| A single throwaway instruction | just a **prompt** | Packaging overhead isn't worth it |

Continue only if the answer is "a reusable capability the agent should reach for
when it recognizes the situation."

## Gate 1 — Pick the archetype

| Archetype | The skill mostly... | Typical components |
|-----------|---------------------|--------------------|
| **Knowledge** | Supplies facts/standards/conventions | SKILL.md + references/ |
| **Workflow** | Walks a fixed multi-step procedure | SKILL.md + templates/ + maybe scripts/ |
| **Tool-wrapper** | Drives a CLI/API/script deterministically | SKILL.md + scripts/ + allowed-tools |
| **Generator** | Produces an artifact from a spec | SKILL.md + templates/ + scripts/ + validator |
| **Orchestration** | Coordinates sub-jobs / multiple passes | SKILL.md + scripts/ + (subagents) |

A skill can blend archetypes, but name the dominant one — it drives the file plan.

## Gate 2 — Behavioral pattern (only for skills that *do* work)

If the skill performs multi-step reasoning or action, choose a pattern from
[pattern-catalog.md](./pattern-catalog.md). **Bias to the simplest thing that
works.** Order of preference:

1. Single prompt / tool loop (no pattern) — most skills.
2. Prompt chaining — fixed sequential steps.
3. Routing — distinct input categories handled differently.
4. Parallelization / evaluator-optimizer — when speed or quality clearly benefits.
5. Orchestrator-workers / autonomous — only when sub-steps can't be predicted up
   front. Requires a written justification; multi-agent adds latency, cost, and
   failure modes.

## Gate 3 — Components

For each candidate component ask "does it earn its place?" Details in
[component-guide.md](./component-guide.md). Defaults:

- **scripts/** — yes when the same deterministic transform repeats (parsing,
  validating, formatting). No for things the model reasons about freshly each time.
- **references/** — yes when supporting detail would blow the SKILL.md budget.
- **templates/** — yes when the skill emits artifacts with a fixed shape.
- **allowed-tools** — set it when the skill should be constrained (e.g. read-only,
  or only Bash+Read). Omit to leave tools unrestricted.
- **hooks/subagents** — only when Gate 2 demanded them.

## Gate 4 — Progressive-disclosure tiers

Three tiers, cheapest to most expensive to load:

1. **Metadata** (name + description) — always in context. Must trigger correctly.
2. **SKILL.md body** — loaded when the skill fires. Keep it the *operating
   procedure*, under 500 lines.
3. **references/ + scripts/** — pulled only when that step needs them.

Put a thing in the cheapest tier that still works. If SKILL.md is creeping past
~400 lines, move detail down a tier.

## Output of this phase

A short skill spec (see SKILL.md Phase 2) plus a one-line rationale for any
non-obvious choice (especially escalating to multi-agent). Show it to the user
before scaffolding.
