---
name: skill-builder
description: Use when the user wants to build, create, design, scaffold, or improve a Claude Skill (a SKILL.md and its supporting files), asks "make a skill that ...", "turn this into a skill", or needs help deciding how a skill should be structured. Produces a complete, validated skill in the skills repo.
---

# Skill Builder

## Overview

This is a meta-skill: it turns a request into a complete, production-grade Claude
Skill. Its edge over ad-hoc skill writing is **deciding the correct structure**
before writing anything, then enforcing a **hard validation gate** before the
skill is called done. Generated skills land in `~/Projects/skills/skills/<name>/`
and install via `npx skills add`.

Work the phases in order. Do not skip straight to writing `SKILL.md` — the value
is in the structure decision (Phase 2) and the validation gate (Phase 6).

## When to Use

- "Build/create/make a skill that ...", "turn this workflow into a skill"
- "How should this skill be structured?", "is this even a good skill?"
- Improving or restructuring an existing skill
- Packaging a skill for distribution

**When NOT to use:** Editing a non-skill file; writing a one-off prompt (use a
prompt, not a skill); configuring hooks/permissions (that is `settings.json`); or
building a standalone agent in an external framework. If the user wants automation
that fires without being asked, that is a hook — say so.

## Phase 1 — Intake (adaptive)

Gather: **purpose** (the outcome), **triggers** (what the user says/does that
should fire it), **inputs/outputs**, **tools/scripts** needed, and 2–3 realistic
example prompts. If the brief already contains these, proceed without asking.
Otherwise ask only for the missing pieces — targeted questions, not a survey.

## Phase 2 — Decide structure (the core)

Run [structure-decision.md](./references/structure-decision.md). Produce a short
**skill spec** and show it to the user before scaffolding:

- **Is a skill the right artifact?** A skill packages reusable procedure/knowledge
  the agent loads on demand. If the need is "always-on rule" → CLAUDE.md; "fires
  automatically on an event" → hook; "external data/API" → MCP; "separate context
  for a sub-job" → subagent. Only continue if a skill genuinely fits.
- **Archetype** (knowledge, workflow, tool-wrapper, generator, or orchestration) —
  see [structure-decision.md](./references/structure-decision.md).
- **Behavioral pattern** when the skill *does* multi-step work — pick from
  [pattern-catalog.md](./references/pattern-catalog.md). Default to the simplest
  pattern; escalate to multi-agent only with a written reason.
- **Components**: scripts? references? templates? `allowed-tools`? hooks/subagents?
  See [component-guide.md](./references/component-guide.md).
- **Progressive-disclosure tiers**: what stays in `SKILL.md` vs moves to
  `references/` vs lives as executable `scripts/`. See
  [skill-anatomy.md](./references/skill-anatomy.md).

Skill spec format:

```
name: <kebab-case>
description: <trigger-first sentence>
archetype: <knowledge|workflow|tool-wrapper|generator|orchestration>
pattern: <none|prompt-chaining|routing|parallelization|orchestrator-workers|evaluator-optimizer|autonomous>
files: SKILL.md, references/<...>, scripts/<...>, templates/<...>
allowed-tools: <list or "unrestricted (omit field)">
```

## Phase 3 — Scaffold

```bash
SKILL_DIR="${SKILL_DIR:-$HOME/.claude/skills/skill-builder}"
python3 "$SKILL_DIR/scripts/scaffold_skill.py" <name> --description "<description>"
```

This creates the repo-standard layout under `~/Projects/skills/skills/<name>/` and
never overwrites existing files without `--force`.

## Phase 4 — Populate

Write the real content into the scaffold, following these rules (full detail in
[skill-anatomy.md](./references/skill-anatomy.md)):

- Keep `SKILL.md` under 500 lines; push depth into `references/` (loaded on
  demand). Explain the *why* behind instructions rather than stacking ALWAYS/NEVER.
- Write the `description` to trigger reliably — see
  [description-patterns.md](./references/description-patterns.md). It is the single
  biggest determinant of whether the skill ever fires.
- Put repetitive deterministic work in `scripts/` (stdlib-only Python), not prose.
- Define the output format explicitly, with an example.
- Avoid the traps in [antipatterns.md](./references/antipatterns.md).

## Phase 5 — Evals

Fill the `evals/` trio (baseline-without-skill, green-with-skill,
pressure-scenarios) with the Phase 1 example prompts. The point is to show the
skill changes behavior versus a bare agent, and survives adversarial input. Method
in [evaluation-guide.md](./references/evaluation-guide.md).

## Phase 6 — Validate (hard gate)

```bash
python3 "$SKILL_DIR/scripts/validate_skill.py" ~/Projects/skills/skills/<name>
```

Fix every `FAIL` and re-run until it prints `RESULT: PASS`. Do not declare the
skill done while the gate is red. Smoke-test any bundled scripts (run them with
real input). Use `--strict` to also clear warnings.

## Phase 7 — Package

```bash
python3 "$SKILL_DIR/scripts/package_skill.py" ~/Projects/skills/skills/<name> [--plugin]
```

This verifies metadata consistency, prints the `npx skills add` line, and (with
`--plugin`) emits a distributable manifest. See
[packaging-guide.md](./references/packaging-guide.md).

## Phase 8 — Report

Report: the file tree, the validation result, the install command, and the first
suggested next step (usually: run the evals, then commit). Do not commit or push
unless the user asks.
