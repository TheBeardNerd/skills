# skill-builder

A meta-skill that builds Claude Skills. Given a brief (or a short interview), it
decides the *correct* structure, scaffolds the skill into this repo, and enforces a
hard validation gate before calling it done.

## Install

```bash
npx skills add https://github.com/TheBeardNerd/skills --skill skill-builder
```

Non-interactive:

```bash
npx skills add https://github.com/TheBeardNerd/skills --skill skill-builder -y
```

## Usage

Trigger it with natural language:

| Intent | Example prompt |
|--------|----------------|
| Build a new skill | `"Build a skill that converts CSV to Markdown tables"` |
| Decide structure | `"How should this skill be structured?"` |
| Sanity-check an idea | `"Should this be a skill or a hook?"` |
| Improve a skill | `"Tighten up the description on my pdf-parser skill"` |
| Package for sharing | `"Package skill-builder as a plugin"` |

## How It Works

Eight phases (see `SKILL.md`):

1. **Intake** — adaptive: one-shot from a rich brief, else ask only what's missing.
2. **Decide structure** — Gate 0 (is a skill even right?) → archetype → behavioral
   pattern → components → progressive-disclosure tiers. Emits a skill spec.
3. **Scaffold** — `scripts/scaffold_skill.py` lays down the repo-standard layout.
4. **Populate** — SKILL.md (< 500 lines), references, scripts, templates.
5. **Evals** — baseline / green / pressure trio.
6. **Validate (hard gate)** — `scripts/validate_skill.py` must print `PASS`.
7. **Package** — `scripts/package_skill.py` (+ optional `--plugin`).
8. **Report** — file tree, validation result, install command, next step.

## What's inside

- `references/` — the decision knowledge: structure-decision, skill-anatomy,
  description-patterns, component-guide, pattern-catalog, evaluation-guide,
  packaging-guide, antipatterns.
- `scripts/` — `scaffold_skill.py`, `validate_skill.py` (hard gate),
  `package_skill.py`. Python 3, stdlib only.
- `templates/` — skeletons for every generated file.
- `evals/` — the trio, dogfooded on skill-building scenarios.

## Develop

```bash
python3 -m unittest discover -s tests
python3 scripts/validate_skill.py .   # skill-builder passes its own gate
```
