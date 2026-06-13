# With Skill Applied (GREEN)

Same prompts as BASELINE, with agent-builder active. The delta is the value.

## Scenario 1: support triage + refunds

Prompt:

```
Build an agent that triages incoming support tickets, looks up orders, and issues
refunds when warranted.
```

Observed output:

```
recommend_structure.py ({complex_decision, unstructured_data, dynamic_tool_loop})
  -> RECOMMENDATION: single-loop (category: agent)

Blueprint: single-loop agent; tools get_order (data, low), issue_refund (action,
HIGH); guardrails safety_check (input), pii_redact (output); human approval on
issue_refund; stop = natural + MAX_TURNS=8.

scaffold_agent.py --spec ... --out ./support-triage-agent
validate_agent.py ./support-triage-agent  ->  RESULT: PASS
  PASS high-risk tools (issue_refund) have an approval path.
```

Result: PASS — structure decided before code; refund gated behind human approval;
loop has both stop conditions; runnable project that clears the hard gate.

## Scenario 2: nightly report generator

Prompt:

```
Should our nightly sales-report generator be an agent? Build it.
```

Observed output:

```
recommend_structure.py ({}) -> RECOMMENDATION: not-an-agent (deterministic solution)
Verdict: This fails Gate 0 — fixed, scheduled, rule-based pipeline. Recommend a
cron-scheduled script (query -> format -> email), optionally one augmented LLM call
for the narrative summary. No agent built.
```

Result: PASS — the skill correctly refuses to build an agent and recommends the
simpler artifact, saving cost and failure modes. (This is the highest-value case:
not building.)

## Scenario 3: research-and-brief

Prompt:

```
Build an agent that researches a topic across many sources and writes a brief.
```

Observed output:

```
recommend_structure.py ({unstructured_data, dynamic_tool_loop}) -> single-loop
Note: escalate to manager only if sub-research can't be enumerated and needs
synthesis. Blueprint records the rationale for single-loop over manager.
scaffold_agent.py ...  ->  validate_agent.py  ->  RESULT: PASS
```

Result: PASS — explicit single-loop-vs-manager rationale, runtime stop design,
guardrails, and an evals starter; runnable end-to-end.
