# Scaffold Spec Schema

`scaffold_agent.py` consumes a JSON spec and emits ONE Markdown file —
`<name>.md` — a native Claude Code subagent (YAML frontmatter + system-prompt
body). It is dropped into `~/.claude/agents/` (user, the default) or `.claude/agents/`
(project); Claude delegates to it inside a session. There is no program to run.

Only `name` and `description` are strictly required. Everything else has sane
defaults, but a real subagent fills in `tools` (least privilege), `model`, and a
structured `system_prompt`.

## Fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `name` | string (kebab-case) | — | **required**; the subagent's identity and how it's invoked (`@agent-<name>`). Lowercase letters, digits, hyphens. |
| `description` | string | — | **required**; trigger-first — what it does and *when* Claude should delegate. Add "use proactively" to encourage auto-delegation. |
| `tools` | array of strings | (omitted) | least-privilege allowlist of built-in/MCP tools. **Omit to inherit ALL tools** — prefer an explicit list. |
| `disallowedTools` | array of strings | `[]` | denylist; removed from the inherited/allowed set. Applied before `tools`. |
| `model` | string | `inherit` | `sonnet` \| `opus` \| `haiku` \| `fable` \| a full id (`claude-opus-4-8`) \| `inherit`. |
| `permissionMode` | string | (omitted) | `default` \| `acceptEdits` \| `auto` \| `dontAsk` \| `bypassPermissions` \| `plan`. |
| `maxTurns` | int | (omitted) | hard cap on agentic turns before the subagent stops. |
| `memory` | string | (omitted) | `user` \| `project` \| `local` — persistent cross-session memory dir. |
| `color` | string | (omitted) | UI color: red/blue/green/yellow/purple/orange/pink/cyan. |
| `scope` | string | `user` | `user` → `~/.claude/agents/` (default), `project` → `./.claude/agents/` (checked-in). Sets the default output dir. |
| `system_prompt` | string | placeholder | the **body** — role, "When invoked" steps, edge cases, output format, stop condition. |

## Tool names

Use built-in tool names exactly: `Read`, `Write`, `Edit`, `MultiEdit`, `Bash`,
`Glob`, `Grep`, `WebFetch`, `WebSearch`, `NotebookEdit`, `TodoWrite`, `Skill`,
`SlashCommand`, `Agent` (spawns nested subagents; formerly `Task`). MCP tools are
`mcp__<server>__<tool>`.

**Never list** `AskUserQuestion`, `EnterPlanMode`, `ScheduleWakeup`, or
`WaitForMcpServers` — they are UI/session-bound and never work inside a subagent
(the scaffolder rejects them). `ExitPlanMode` only works with `permissionMode: plan`.

## Example spec

```json
{
  "name": "test-runner",
  "description": "Runs the test suite and reports only failures with their error messages. Use proactively after code changes that could affect tests.",
  "tools": ["Bash", "Read", "Grep", "Glob"],
  "model": "haiku",
  "scope": "project",
  "system_prompt": "You are a test-running specialist. When invoked:\n1. Detect the test command (package.json scripts, pytest, go test, etc.).\n2. Run the full suite.\n3. Parse the output.\n\nHow you work:\n- Do not modify code or tests.\n- If the suite cannot run (missing deps, no test command), say so and stop.\n\nOutput format:\n- A short summary line (N passed / M failed).\n- For each failure: the test name, the file:line, and the assertion/error message — nothing else.\n\nYou are done when results are summarized. Do NOT paste full passing output back to the main conversation."
}
```

Generated file (`./.claude/agents/test-runner.md`):

```markdown
---
name: test-runner
description: Runs the test suite and reports only failures with their error messages. Use proactively after code changes that could affect tests.
tools: Bash, Read, Grep, Glob
model: haiku
---

You are a test-running specialist. When invoked:
1. Detect the test command ...
```

Then refine the `system_prompt`, run `validate_agent.py`, and try it:
`"use the test-runner subagent"`.
