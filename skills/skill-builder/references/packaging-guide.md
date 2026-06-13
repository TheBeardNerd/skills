# Packaging Guide

Generated skills live in the `~/Projects/skills` repo
(`github.com/TheBeardNerd/skills`) and are installable from there.

## Repo layout

```
skills/
  <name>/
    SKILL.md  README.md  package.json  .gitignore
    references/  scripts/  templates/  tests/  evals/
```

One directory per skill under `skills/`. The directory name **is** the skill name
and must match `SKILL.md`'s `name`.

## Install line (put it in the README)

```bash
npx skills add https://github.com/TheBeardNerd/skills --skill <name>
```

Add `-y` for non-interactive installs. This is the primary distribution path —
users install straight from the repo.

## package.json

```json
{
  "name": "@twc/<name>-skill",
  "version": "0.1.0",
  "description": "<one line>",
  "license": "MIT",
  "scripts": { "test": "python3 -m unittest discover -s tests" }
}
```

`package_skill.py` warns if `name` here doesn't contain the skill name.

## As a Claude Code plugin (optional)

```bash
python3 scripts/package_skill.py ~/Projects/skills/skills/<name> --plugin
```

Writes `.claude-plugin/plugin.json` so the skill can ship as a distributable
plugin (name, version, description, homepage, and the skill path). Use `--zip` to
also produce `<name>.zip` for manual sharing.

## Before declaring done

1. `validate_skill.py <dir>` prints `RESULT: PASS`.
2. `python3 -m unittest discover -s tests` passes (if scripts exist).
3. README's install line names the correct skill.
4. Do **not** commit or push unless the user asks. When they do: stage the new
   skill dir, commit with a clear message, and push to `origin`.
