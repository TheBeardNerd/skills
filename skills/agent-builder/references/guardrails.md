# Guardrails & Human-in-the-Loop

Guardrails manage privacy, safety, and reputational risk. No single guardrail
suffices — think **layered defense**: stack specialized checks so a miss in one is
caught by another. Combine LLM-based judges, rules-based filters (regex/blocklist),
and a moderation pass. Pair guardrails with real auth, access control, and standard
software security; guardrails are not a substitute for those.

## Types of guardrails

| Guardrail | Catches | How |
|-----------|---------|-----|
| **Relevance classifier** | Off-topic / out-of-scope input | LLM judge flags inputs outside the agent's remit |
| **Safety classifier** | Jailbreaks, prompt injection | LLM/fine-tuned classifier marks unsafe attempts to extract the prompt or hijack the agent |
| **PII filter** | Leaking personal data | Vet model output for PII before returning it |
| **Moderation** | Hate, harassment, violence | Moderation API on inputs/outputs |
| **Tool safeguards** | Risky tool calls | Rate each tool low/med/high (read-only vs write, reversibility, permissions, financial impact); gate high-risk ones |
| **Rules-based** | Known threats | Blocklists, input length caps, regex (e.g. SQL-injection patterns) |
| **Output validation** | Off-brand / unsafe responses | Prompt + content checks before the response ships |

## Where guardrails run

- **Input guardrails** run *before* the agent acts on user input (relevance,
  safety, moderation, length). On a tripwire, short-circuit with a safe refusal
  ("We cannot process this message").
- **Output guardrails** run *before* a response or a high-risk tool call is
  committed (PII, output validation, brand).
- **Optimistic execution** (OpenAI's pattern): let the agent generate while
  guardrails run concurrently; raise/halt if a tripwire fires. Faster than fully
  serial checks.

A guardrail can be a function (regex, length, blocklist) or an LLM call (a small
classifier agent returning a structured `{flagged: bool, reason: str}`).

## Tool risk ratings → automated actions

Assign each action tool a risk rating and wire the consequence:

| Rating | Examples | Action |
|--------|----------|--------|
| Low | read-only lookups | run freely |
| Medium | reversible writes | log; optional confirmation |
| High | payments, deletes, external emails, irreversible writes | **pause for guardrail check and/or human approval before executing** |

## Human-in-the-loop

A human checkpoint is a first-class safeguard, not an afterthought. Trigger it on:
- **Exceeding failure/retry thresholds** — if the agent can't make progress or keeps
  mis-parsing, hand control back to a human rather than looping.
- **High-risk actions** — irreversible or high-impact tool calls (refunds, cancels,
  large transactions, external comms) require explicit approval.

The agent must be able to **halt and transfer control back to the user** on failure
or low confidence. Build this into the loop's stop conditions, not just the prompt.

## Building guardrails (heuristic)

1. Start with **data privacy and content safety** guardrails.
2. **Add new ones from real edge cases and failures** you observe — guardrails grow
   with the agent.
3. **Balance security and UX**: tune so legitimate users aren't blocked while
   threats are.

## Minimum bar for this skill's gate

The validator requires: at least one input guardrail present, and every tool marked
`high` risk having an `approval`/human-in-the-loop path. An agent that can take
irreversible action with no guardrail and no checkpoint fails the gate.
