# With Skill Applied (GREEN)

Same prompts as BASELINE, with `agent-builder` active. The delta is the value.

## Scenario 1: code-review subagent

Prompt:

```
Build a subagent that reviews my code for quality and security issues.
```

Observed output:

```
recommend_structure.py ({needs_tool_restriction, reusable_worker, self_contained})
  -> RECOMMENDATION: single subagent (category: subagent)

Blueprint: single subagent `code-reviewer`; tools Read, Grep, Glob, Bash (NO
Edit/Write — read-only wall); model inherit; description trigger-first + "use
proactively"; system prompt has cold-start "When invoked" steps + priority-ranked
output format.

scaffold_agent.py --spec ...  ->  ./.claude/agents/code-reviewer.md
validate_agent.py ./.claude/agents/code-reviewer.md  ->  RESULT: PASS
```

Result: PASS — artifact decided first; read-only enforced by the tool wall (not just
a prompt plea); a description that actually triggers delegation; a cold-start prompt.

## Scenario 2: test-runner subagent

Prompt:

```
Make an agent that runs our tests and tells me only what failed.
```

Observed output:

```
recommend_structure.py ({verbose_side_work, reusable_worker}) -> single subagent
Blueprint: model haiku (high-volume, low-judgment); tools Bash, Read, Grep, Glob;
output format = summary line + per-failure (name, file:line, error) ONLY; explicit
"do not paste passing output back".
scaffold_agent.py ...  ->  validate_agent.py  ->  RESULT: PASS
```

Result: PASS — right model for the workload, and a strict summary-only contract so the
context isolation actually pays off.

## Scenario 3: changelog reminder

Prompt:

```
I want an agent that reminds me to update the changelog every time I commit.
```

Observed output:

```
recommend_structure.py ({event_triggered: true})
  -> RECOMMENDATION: NOT a subagent — use a hook (category: hook)
Verdict: "every time I commit" is an event trigger. A subagent only runs when Claude
delegates to it, so it would never fire here. Recommend a hook (PostToolUse / a git
post-commit hook) instead. No subagent built.
```

Result: PASS — the highest-value case is *not building the wrong thing*. The skill
routes to a hook and explains why.
