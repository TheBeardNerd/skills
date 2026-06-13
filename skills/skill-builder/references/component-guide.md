# Component Guide

For each component, the question is "does it earn its place?" Adding files the
skill doesn't need is a cost: more to load, more to maintain, more to drift.

## scripts/

**Add when** the same deterministic transform repeats: parsing a format,
validating structure, computing something, formatting output. Scripts don't drift
the way model reasoning does — encode the boring repeatable parts.

**Skip when** the step is genuinely a judgment call each time (the model should
reason, not run a fixed algorithm).

Conventions: Python 3, **stdlib only** (no pip installs), each script runnable
standalone with `argparse`, and importable (logic in functions, `main()` guarded by
`if __name__ == "__main__"`). Make scripts findable via
`SKILL_DIR="${SKILL_DIR:-$HOME/.claude/skills/<name>}"`.

## references/

**Add when** supporting detail (decision tables, format specs, long examples)
would push SKILL.md over budget. Reference files are loaded only when a step points
to them, so they can be large.

**Skip when** the content is short enough to live inline without crowding the
procedure.

Link to them from SKILL.md with relative markdown links so the validator confirms
they resolve.

## templates/

**Add when** the skill emits an artifact with a fixed shape (a document, a config,
a code file). A template keeps output consistent and makes the skill's intent
legible.

**Skip when** output is freeform or varies every time.

## allowed-tools

**Set it** to constrain the skill. Read-only skills should list only read tools;
script-drivers usually need just `Bash, Read`. Tighter is safer and more
predictable. **Omit it** only when the full toolset is genuinely required.

## hooks

A skill cannot make itself fire automatically — that is a hook (configured in
`settings.json`, run by the harness). If the user wants "every time X, do Y",
the deliverable is a hook, not (or in addition to) a skill. A skill *may ship*
recommended hook config in a reference file for the user to install.

## subagents / orchestration

**Add when** Gate 2 in [structure-decision.md](./structure-decision.md) showed the
work needs isolated contexts or unpredictable fan-out (orchestrator-workers,
parallel evaluation). The skill spawns subagents via the Task tool from its
procedure.

**Skip by default.** Multi-agent adds latency, token cost, and coordination
failure modes. Single-context is the right answer for most skills; escalate only
with a written reason in the skill spec.

## tests/

Any skill with `scripts/` should have `tests/` (unittest) covering them, so the
hard gate's compile check is backed by behavior checks. Run via
`python3 -m unittest discover -s tests`.
