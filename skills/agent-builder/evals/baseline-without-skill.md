# Without Skill (BASELINE)

How a plain agent (no `agent-builder` skill) handles each scenario. Same prompts as
the GREEN file, so the skill's added value is measurable. Run each in a fresh session
without the skill and note the failure mode.

## Scenario 1: code-review subagent

Prompt:

```
Build a subagent that reviews my code for quality and security issues.
```

Observed behavior:

- Jumps to writing a `.md` (or, worse, a standalone script) without checking whether
  a subagent is even the right artifact.
- Omits the `tools` field, so the "reviewer" inherits `Edit`/`Write` and *can modify
  code* — the read-only intent isn't enforced.
- Vague `description` ("reviews code") with no trigger cue → Claude rarely
  auto-delegates to it.
- System prompt assumes conversation context instead of writing for a cold start, and
  doesn't define what the subagent returns.

Gap: no artifact decision, no least-privilege tool wall, weak delegation trigger, and
a prompt that won't behave from a fresh context.

## Scenario 2: test-runner subagent

Prompt:

```
Make an agent that runs our tests and tells me only what failed.
```

Observed behavior:

- Builds a single subagent on the default/inherited model (expensive for high-volume
  test output) with no instruction to return *only* failures — so it dumps the full
  test log back into the main context, defeating the reason to isolate it.

Gap: wrong model for the workload, and no output-format discipline, so the context
isolation buys nothing.

## Scenario 3: changelog reminder

Prompt:

```
I want an agent that reminds me to update the changelog every time I commit.
```

Observed behavior:

- Builds a subagent. **Wrong artifact** — "every time I commit" is an *event trigger*,
  which is a hook, not a subagent (a subagent only runs when Claude delegates to it).
  A bare agent ships something that never fires.

Gap: fails Gate 0 — never recognizes that the need is a hook, not a subagent.
