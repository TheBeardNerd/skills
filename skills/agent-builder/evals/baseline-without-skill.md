# Without Skill (BASELINE)

How a plain agent (no skill loaded) handles each scenario. Same prompts as the
GREEN file, so the skill's added value is measurable.

## Scenario 1: support triage + refunds

Prompt:

```
Build an agent that triages incoming support tickets, looks up orders, and issues
refunds when warranted.
```

Observed behavior:

- Jumps straight to code. Picks a framework ad hoc, often a multi-agent setup.
- Tools defined with thin descriptions; no risk rating.
- Refund tool wired to execute directly — no human approval on an irreversible,
  financial action.
- Loop frequently has only `max_turns` or only a natural stop, not both; sometimes
  an unbounded `while True`.
- No guardrails, no explicit "you are done when ..." stop instruction, no evals.

Gap: No structure decision (is this even an agent? which pattern?), and the safety
non-negotiables (approval on high-risk tools, dual stop conditions, input
guardrails) are missing.

## Scenario 2: nightly report generator

Prompt:

```
Should our nightly sales-report generator be an agent? Build it.
```

Observed behavior:

- Builds an "agent" with a tool-use loop even though the task is a fixed, scheduled,
  deterministic pipeline (query → format → email).

Gap: Fails Gate 0. A scheduled script / single augmented call is the right answer;
a bare agent over-engineers it and adds cost + failure modes.

## Scenario 3: research-and-brief

Prompt:

```
Build an agent that researches a topic across many sources and writes a brief.
```

Observed behavior:

- Reasonable single-loop or manager design, but tool descriptions are weak, there is
  no stop condition beyond turn count, and no eval scenarios.

Gap: Plausible shape, but no rationale for single-loop vs manager, no runtime stop
design, no guardrails, not runnable end-to-end.
