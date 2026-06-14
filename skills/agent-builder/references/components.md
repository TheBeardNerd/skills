# Components: System Prompt, Tools, Model

A Claude Code subagent reduces to three design choices, all expressed in one
Markdown file: the **system prompt** (the body), the **tool permissions**
(`tools`/`disallowedTools`), and the **model**. Most subagent failures trace to a
vague system prompt or the wrong tool wall — not the model. Design each
deliberately.

## System prompt (the body)

The body *is* the subagent's behavior. It runs from a **cold start** — the subagent
sees none of your conversation (see [execution-model.md](./execution-model.md)) — so
it must be self-contained. Follow the shape the official examples use:

- **Open with role + domain**: "You are a senior code reviewer ensuring high
  standards of quality and security."
- **"When invoked:" numbered steps** — the first concrete actions from a cold start
  ("1. Run `git diff` to see recent changes. 2. Focus on modified files. 3. ...").
- **A checklist or process** the subagent applies (what to look for, how to work).
- **Edge cases**: what to do when input is missing or ambiguous ("if there is no
  diff, say so and stop") — the subagent can't ask the user mid-run
  (`AskUserQuestion` is unavailable to subagents), so bake decisions in.
- **Output format**: state *exactly* what it returns to the main conversation and how
  it's structured. This is critical — the whole point is returning a tight summary,
  not dumping raw logs/files back into the main context.
- **Stop condition in prose**: "You are done when … — then return the summary."

Derive steps from real SOPs/policies where they exist; don't invent procedure. Keep
it focused: one subagent, one job. A sprawling prompt is a sign you want two
subagents (see [patterns.md](./patterns.md)).

## Tools = permissions (least privilege)

The `tools` field is the capability wall. **Omitting it inherits ALL tools**
(including MCP) — almost never what you want. List the minimum:

- **Read-only worker** (reviewer, researcher): `Read, Grep, Glob, Bash` — no `Edit`,
  no `Write`.
- **Worker that fixes things** (debugger): add `Edit` (and `Write` if it creates
  files).
- **Two ways to scope**: `tools` is an allowlist; `disallowedTools` is a denylist
  removed from the inherited set (`disallowedTools: Write, Edit`). If both are set,
  `disallowedTools` applies first, then `tools` resolves against the remainder.

Built-in tool names (exact): `Read`, `Write`, `Edit`, `MultiEdit`, `Bash`, `Glob`,
`Grep`, `WebFetch`, `WebSearch`, `NotebookEdit`, `TodoWrite`, `Skill`,
`SlashCommand`, `Agent` (spawns nested subagents). MCP tools: `mcp__<server>__<tool>`.

**Never list** `AskUserQuestion`, `EnterPlanMode`, `ScheduleWakeup`,
`WaitForMcpServers` — UI/session-bound, never function in a subagent.
`ExitPlanMode` only with `permissionMode: plan`. To preload a skill's content use the
`skills` field, not `Skill` in `tools`.

The tool wall is poka-yoke for capability: a reviewer that *cannot* write can't
accidentally edit your code, no matter what the prompt says. Prefer a tighter tool
list over prompt instructions like "don't edit files."

## Model

`model`: `sonnet` | `opus` | `haiku` | `fable` | a full id (`claude-opus-4-8`) |
`inherit` (default). Match capability to the work:

- **`haiku`** — high-volume, low-judgment work: running tests, searching, triaging
  logs. Cheap and fast; the cost lever.
- **`sonnet`** — balanced default for analysis (code review, data work).
- **`opus`** — judgment-heavy or high-stakes reasoning.
- **`inherit`** — use the main conversation's model; good when the subagent's work is
  as demanding as the main thread's.

Principled approach: start capable enough to hit the quality bar, then downgrade
high-volume steps to `haiku` where quality holds.

## Putting it together

These three map straight onto the spec consumed by `scaffold_agent.py`:
`system_prompt` → body, `tools`/`disallowedTools` → permissions, `model` → model.
Keep the prompt focused and the tool list tight — that is what makes a subagent both
safe and good at its one job.
