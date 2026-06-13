# Antipatterns

Common ways skills fail. The builder should actively avoid these and flag them when
improving an existing skill.

## Triggering

- **Vague description.** "Helps with X" with no trigger cues — the model never
  picks it up. Fix per [description-patterns.md](./description-patterns.md).
- **First-person description.** "I help you ..." reads as narration, not a trigger,
  and fails the gate.
- **Over-pushy description.** Fires on everything adjacent. Add a "When NOT to use"
  boundary and a should-not-trigger pressure scenario.

## Structure

- **Everything in SKILL.md.** A 900-line SKILL.md burns tokens every fire. Push
  depth into `references/` (progressive disclosure).
- **Skill that should be a hook.** "Run this automatically after every edit" is a
  hook, not a skill — a skill only fires when the model chooses to invoke it.
- **Skill that should be a prompt.** A one-off instruction doesn't need the
  packaging overhead.
- **Premature multi-agent.** Reaching for orchestrator-workers when a single pass
  works. Adds latency, cost, and failure modes for no gain.

## Content

- **ALL-CAPS rule stacking.** Walls of ALWAYS/NEVER without rationale. Explain the
  *why*; reserve hard imperatives for safety rails.
- **Undefined output.** No example, no format spec → inconsistent results. Always
  show the exact output shape.
- **Prose where a script belongs.** Asking the model to re-derive a deterministic
  transform each time invites drift. Encode it in `scripts/`.
- **Dead links.** Referencing files that don't exist. The validator fails on this.

## Process

- **No evals.** Shipping with no evidence the skill beats a bare agent. Fill the
  trio.
- **Skipping the gate.** Declaring done while `validate_skill.py` is red.
- **Secrets in files.** API keys / tokens committed into the skill. The validator
  scans for these; never paste real credentials into examples.
- **Third-party pip deps in scripts.** Keep scripts stdlib-only so they run
  anywhere without setup.
