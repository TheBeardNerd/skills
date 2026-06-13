# skills

A collection of installable [Agent Skills](https://www.anthropic.com/engineering)
for Claude. Each skill lives in its own directory under `skills/` with a `SKILL.md`,
supporting files, and an evals trio.

## Available skills

| Skill | What it does |
|-------|--------------|
| [skill-builder](skills/skill-builder) | Meta-skill that decides the correct structure for a new skill and builds it — scaffolds, populates, and enforces a hard validation gate before it's done. |
| [csv-to-markdown](skills/csv-to-markdown) | Converts CSV data into a GitHub-flavored Markdown table, handling quoted fields, embedded commas/newlines, and pipe characters. |
| [session-handoff](skills/session-handoff) | Creates and resumes project-local session handoffs so a fresh agent can pick up exactly where the last one left off. |

## Install

Install any skill straight from this repo:

```bash
npx skills add https://github.com/TheBeardNerd/skills --skill <name>
```

Add `-y` for a non-interactive install. For example:

```bash
npx skills add https://github.com/TheBeardNerd/skills --skill skill-builder
```

## Repository layout

```
skills/
  <name>/
    SKILL.md          # frontmatter (name, description) + operating procedure
    README.md         # install + usage
    package.json      # @twc/<name>-skill
    references/       # on-demand depth (progressive disclosure)
    scripts/          # stdlib-only Python helpers
    templates/        # artifact skeletons
    tests/            # unittest for the scripts
    evals/            # baseline / green / pressure trio
```

## Develop

Each skill's scripts are Python 3 (stdlib only) and tested with `unittest`:

```bash
cd skills/<name> && python3 -m unittest discover -s tests
```

New skills are built with **skill-builder**, which validates every skill against a
hard gate (frontmatter, trigger-quality description, token budget, file layout,
script compilation, link resolution, and a secret scan):

```bash
python3 skills/skill-builder/scripts/validate_skill.py skills/<name>
```

## License

[MIT](LICENSE)
