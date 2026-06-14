# Guardrails & Human-in-the-Loop (the Claude Code way)

You do **not** hand-write guardrail functions or approval prompts for a Claude Code
subagent — the harness already enforces permissions. Your guardrails are
*configuration*: which tools the subagent gets, how its permission prompts behave,
and (when you need finer control) hooks. Think in layers, tightest first.

## Layer 1 — the tool wall (your primary guardrail)

The `tools`/`disallowedTools` fields decide what the subagent *can do at all*. A
capability the subagent doesn't have can't be misused, regardless of the prompt.

- Read-only reviewer/researcher → `tools: Read, Grep, Glob, Bash` (no `Edit`/`Write`).
- A subagent that should never reach the network → omit `WebFetch`/`WebSearch`/MCP.
- Inherit-all-except → `disallowedTools: Write, Edit`.

This is poka-yoke: prefer removing the tool over instructing "please don't use it."

## Layer 2 — permission mode (how risky calls are gated)

`permissionMode` controls what happens when the subagent makes a call that needs
approval. **This is the human-in-the-loop** — you don't build it, you choose it:

| Mode | Behavior | Use for |
|------|----------|---------|
| `default` | Standard prompts; risky calls ask the user. | most subagents — keep the human checkpoint |
| `plan` | Read-only exploration. | research/planning subagents |
| `acceptEdits` | Auto-accept edits in the working dir. | trusted, scoped edit work |
| `auto` | A classifier reviews commands/protected writes. | semi-autonomous runs |
| `dontAsk` | Auto-deny anything that would prompt. | strict, allow-listed-only runs |
| `bypassPermissions` | Skip prompts entirely. | **dangerous — avoid**; only sandboxed, low-stakes work |

Default behavior already pauses for approval on irreversible/high-impact actions —
so for a subagent that can take risky actions, **stay on `default`** and let the
prompt reach the user. Reserve `bypassPermissions` for genuinely sandboxed contexts;
it lets the subagent write to `.git`, `.claude`, etc. without asking.

Note: background subagents auto-deny anything that would prompt; a high-risk action
that needs approval should run in the foreground.

## Layer 3 — conditional rules via hooks

When the tool wall is too coarse (allow *some* uses of a tool, block others), add a
`PreToolUse` hook in the subagent's frontmatter. The classic example is a DB reader
that may run `SELECT` but not `INSERT/UPDATE/DELETE`:

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-readonly-query.sh"
```

The hook reads the tool input as JSON on stdin and exits `2` to block (with a reason
on stderr). This is the only place you write guardrail *code*, and only when needed.

## Layer 4 — the system prompt (behavioral, not enforced)

Prompt instructions ("only return failing tests", "if asked to modify data, refuse —
you are read-only") shape behavior but are **not enforced** — a determined or
confused run can ignore them. Use them to *explain* the boundaries the tool wall and
hooks *enforce*. Never rely on the prompt alone for safety.

## Choosing guardrails (heuristic)

1. **Start at the tool wall** — give the least privilege the job needs.
2. **Keep `permissionMode: default`** unless you have a reason to change it, so risky
   actions still surface to the user.
3. **Add a `PreToolUse` hook** only when you must allow part of a tool and block the
   rest.
4. **Restate the boundary in the prompt** so the subagent understands its lane.

## Minimum bar for this skill's gate

The validator does not require guardrails (the harness enforces permissions by
default), but it **warns** when `tools` is omitted — inheriting every tool is the
opposite of least privilege. A subagent that takes irreversible actions should keep
`permissionMode: default` (or unset) so approvals reach the user; flag it in the
blueprint if you change that.
