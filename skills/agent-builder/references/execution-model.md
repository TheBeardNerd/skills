# Execution Model: How Claude Code Runs a Subagent

A Claude Code subagent is **not a program and not a loop you write**. It is a
Markdown file (`.claude/agents/<name>.md`) that Claude Code loads and runs for you.
The harness owns the loop, the tools, and the permission prompts. Your job is to
define *who the subagent is* (system prompt), *what it may touch* (tools), and
*which model* it uses. Understanding what the harness does — and does not — hand the
subagent is what makes one behave.

## What a subagent is

> "Each subagent runs in its own context window with a custom system prompt,
> specific tool access, and independent permissions. When Claude encounters a task
> that matches a subagent's description, it delegates to that subagent, which works
> independently and returns results."

So a subagent buys you three things:

1. **Context isolation** — verbose work (search results, logs, file dumps) happens
   in the subagent's own window; only its final summary returns to the main thread.
2. **Capability walls** — the `tools`/`disallowedTools` fields fence off what it can
   do (e.g. a read-only reviewer with no `Edit`/`Write`).
3. **Model/cost control** — route cheap, high-volume work to `haiku`; reserve
   `opus` for judgment-heavy work.

## What loads into a subagent (and what doesn't)

A non-fork subagent starts with a **fresh, isolated context**. It does **not** see
your conversation history, the files Claude already read, or skills already invoked.
Its initial context is:

- **System prompt** — *your markdown body*, plus environment details the harness
  appends (working directory, etc.). **Not** the full Claude Code system prompt.
- **Task message** — the delegation prompt Claude writes when handing off.
- **CLAUDE.md + memory hierarchy** — loaded (every level the main session loads).
- **Git status** — a snapshot from session start (if in a repo).
- **Preloaded skills** — only those named in the `skills` field.

Implications for the system prompt you write:

- It must be **self-contained**: the subagent has no memory of the conversation. Say
  what to do from a cold start ("When invoked: 1. run `git diff` ...").
- A rule that must reach the subagent (e.g. "ignore `vendor/`") has to be **in the
  prompt** — don't assume it inherits conversational context.
- It returns **only a summary**. Tell it explicitly what to return and what to leave
  behind, or it will flood the main context (defeating the point).

## Invocation

- **Automatic delegation** — Claude reads each subagent's `description` and delegates
  when a task matches. This is why the `description` is the single biggest lever:
  write it trigger-first and add "use proactively" to encourage it.
- **Explicit** — the user names it ("use the code-reviewer subagent"), `@`-mentions
  it (`@agent-<name>`, guarantees that one runs), or runs the whole session as it
  via `claude --agent <name>`.

## Stop conditions

You generally do **not** hand-build stop conditions — the harness ends the run when
the subagent stops acting (returns its summary). Two optional guards:

- `maxTurns` in frontmatter caps agentic turns.
- A clear "**You are done when …**" line in the system prompt makes the natural stop
  fire cleanly instead of the subagent puttering.

## Permissions & approvals (this replaces hand-written guardrails)

The harness enforces permissions; you do not write approval code. See
[guardrails.md](./guardrails.md). In short: the `tools` allowlist is the primary
wall, `permissionMode` controls whether risky calls prompt, and `PreToolUse` hooks
add conditional rules (e.g. block non-`SELECT` SQL).

## Nesting (multi-subagent topologies)

As of Claude Code v2.1.172, a subagent that lists `Agent` in its `tools` can spawn
**nested subagents** — useful when a delegated task itself fans out into parallel
subtasks and the intermediate output should stay out of the main conversation. Most
multi-subagent work, though, is just the **main conversation** spawning several
subagents (parallel) or chaining them (sequential) — see [patterns.md](./patterns.md).
Prefer that over nesting; reach for `Agent`-in-tools only with a written reason.
