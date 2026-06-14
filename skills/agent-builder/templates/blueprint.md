# Subagent Blueprint: <name>

> Filled during Phase 2 and shown to the user before scaffolding. Each section
> records a decision and its rationale. The deliverable is one
> `.claude/agents/<name>.md` file — a Claude Code subagent, not a program.

## 1. Verdict — is this a subagent?

- **Decision:** <subagent | NOT a subagent → CLAUDE.md / hook / skill / main-conversation / MCP>
- **Why:** <which Gate-0 signal applies: verbose side-work / capability wall /
  self-contained / reusable worker — or, if not a subagent, which simpler artifact
  fits and why>

> If "NOT a subagent", stop here and recommend the simpler artifact.

## 2. Topology

- **Topology:** <single | parallel (main-driven) | chained (main-driven) | coordinator + nested>
- **Why this and not something simpler:** <one line; the recommender's rationale + your confirmation>
- **Recommender output:** <paste `recommend_structure.py` verdict>

## 3. Components

### Identity
- **name:** <kebab-case>
- **description:** <trigger-first; what it does + WHEN to delegate; "use proactively" if it should auto-fire>
- **scope:** <project (`.claude/agents/`) | user (`~/.claude/agents/`)>

### Model
- **model:** <haiku | sonnet | opus | inherit> — <why: volume vs judgment vs match-main>

### Tools (least privilege)
| Tool | Why it's needed |
|------|-----------------|
| <Read/Grep/...> | <reason> |

- **Deliberately withheld:** <e.g. Edit/Write — this is a read-only worker>

### System prompt (sketch)
<role + "When invoked" numbered steps + edge cases + output format + the explicit
"you are done when …" stop line>

## 4. Guardrails (configuration, not code)

- **Tool wall:** <the allowlist above is the primary guardrail>
- **permissionMode:** <default (keep approvals) | plan | other — and why>
- **PreToolUse hook:** <only if you must allow part of a tool and block the rest, e.g. read-only SQL>

## 5. Eval plan

- **Scenarios:** <2–3 realistic tasks the subagent must handle>
- **Success criteria:** <what a correct return looks like — including that it returns
  a tight summary, not raw dumps>
- **Pressure cases:** <off-topic delegation, ambiguous task, a request to do
  something its tools forbid (it should decline / not be able to)>
