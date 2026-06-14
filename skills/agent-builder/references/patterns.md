# Subagent Topology Catalog

How many subagents, and who drives them. Each topology with when-to-use and how it
runs inside Claude Code. **Default to a single subagent.** Every step up buys
capability with coordination cost, more returned context, and new failure modes —
escalate only with a written reason in the blueprint. See
[execution-model.md](./execution-model.md) for how the harness runs each.

## Building block — one focused subagent

A single `.claude/agents/<name>.md`: a system prompt + a least-privilege tool set,
running in its own context and returning a summary. This is the right answer most of
the time. Reach for more subagents only when one genuinely can't hold the job.

```markdown
---
name: code-reviewer
description: Expert code review specialist. Use proactively after writing or modifying code.
tools: Read, Grep, Glob, Bash
model: inherit
---
You are a senior code reviewer. When invoked: 1) run git diff, 2) review changed
files, 3) report issues by priority. Return only the findings; do not paste full files.
```

If one well-scoped subagent answers the need, ship it — that is the right outcome.

## Single subagent (the default)

One subagent, invoked by description match or by name. Use for: isolating verbose
side-work (tests, doc fetches, log triage), enforcing a capability wall (read-only
reviewer), or any self-contained job that returns a summary.

## Parallel subagents (main thread orchestrates)

The **main conversation** spawns several subagents at once for independent
investigations, then synthesizes. You usually build **one** reusable subagent
definition and the main thread invokes it N times over different inputs.

> "Research the authentication, database, and API modules in parallel using
> separate subagents."

Use when: independent areas can be explored concurrently and the paths don't depend
on each other. Caution: each subagent's summary returns to the main context — many
detailed returns can themselves bloat it. Keep each return lean.

## Chained subagents (main thread orchestrates)

The main conversation runs subagents **in sequence**, passing relevant context from
one to the next. Often two focused definitions, not one.

> "Use the code-reviewer subagent to find performance issues, then use the optimizer
> subagent to fix them."

Use when: stages are distinct and ordered (review → fix, research → draft → check),
and a capability split helps (a read-only finder, then a writer).

## Coordinator with nested subagents (advanced)

A subagent that itself lists `Agent` in its `tools` spawns **nested** worker
subagents — e.g. a reviewer that dispatches a verifier per finding. Only the
coordinator's summary returns to the main conversation; the workers' intermediate
output never reaches it. Requires Claude Code v2.1.172+.

Use only when **both**: the delegated task fans out into parallel subtasks, **and**
the intermediate output must stay out of the main conversation. Otherwise let the
main thread spawn the workers (parallel topology) — it is simpler and just as
capable. Background subagents past a fixed depth stop receiving the `Agent` tool, so
nesting is self-limiting.

## Escalation discipline

| Topology | Use when | Cost |
|----------|----------|------|
| **Single subagent** | One focused job, isolated context or tool wall. | Lowest |
| **Parallel (main-driven)** | Independent investigations at once. | Medium |
| **Chained (main-driven)** | Ordered stages, often a capability split. | Medium |
| **Coordinator + nested** | A delegated task fans out *and* its noise must stay hidden. | High |

Maximize a single subagent first. Split only when one definition with a good
description and the right tools *fails* to do the job. Record *why* you escalated.
