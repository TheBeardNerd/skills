# Skill Anatomy

## Directory layout (repo standard)

```
<name>/
  SKILL.md          # required: frontmatter + operating procedure
  README.md         # install + usage (human-facing)
  package.json      # @twc/<name>-skill, test script
  .gitignore        # ignores caches/secrets
  references/       # on-demand depth (loaded when a step needs it)
  scripts/          # stdlib-only Python, deterministic helpers
  templates/        # artifact skeletons the skill fills in
  tests/            # unittest for the scripts
  evals/            # baseline / green / pressure trio
```

## Frontmatter

```yaml
---
name: kebab-case-name          # MUST equal the directory name
description: Use when ...       # the trigger; see description-patterns.md
allowed-tools: Read, Bash       # OPTIONAL — omit to leave tools unrestricted
---
```

Only `name` and `description` are required. `name` must be kebab-case and match
the folder. Keep `description` under ~1024 chars.

## The three tiers (progressive disclosure)

1. **Metadata** — `name` + `description`. Always loaded across all skills, so keep
   it tight; this is what decides whether the skill triggers at all.
2. **SKILL.md body** — loaded when the skill fires. This is the *procedure*: what
   to do, in order, with the decision points. Target < 500 lines (hard cap in the
   validator), ideally < 200.
3. **Bundled files** — `references/`, `scripts/`, `templates/`. Loaded only when a
   step reaches for them. Unlimited size; this is where depth lives.

## Writing principles

- **Explain the why.** "Validate before reporting, because a silently broken
  artifact wastes the next agent's session" beats "ALWAYS VALIDATE." Reserve
  hard imperatives for genuine safety rails.
- **Imperative voice**, second person to the agent: "Run the validator", not "The
  skill runs the validator."
- **Be specific about output.** Define the exact format and show one example.
  Vague output instructions are the top cause of inconsistent skills.
- **Push detail down a tier** the moment SKILL.md gets long. A reader (the model)
  pays tokens for everything in SKILL.md every time the skill fires.
- **Scripts over prose for determinism.** If a step is "parse this, check that,
  format so" the same way every time, write a script and call it. Models drift;
  scripts don't.
- **Link, don't inline.** Reference files via relative markdown links
  (`[name](./references/x.md)`) so the validator can confirm they resolve.

## allowed-tools

Set it to constrain the skill's blast radius:

- Read-only knowledge skill → `allowed-tools: Read, Grep, Glob`
- Script-driver → `allowed-tools: Bash, Read`
- Leave unrestricted (omit the field) only when the skill genuinely needs the full
  toolset.

A tighter tool list is a feature: it makes the skill safer and its behavior more
predictable.
