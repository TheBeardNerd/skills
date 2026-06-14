# agent-builder

Decides the **correct structure** for a Claude Code subagent — whether the job even
wants a subagent (vs. CLAUDE.md, a hook, a skill, or the main conversation), and if so
which topology — then scaffolds a native **`.claude/agents/<name>.md`** file (system
prompt + tool permissions + model) that runs *inside* Claude Code using its built-in
file/shell/web tools. No standalone program, no SDK, no API key. Grounded in the
[Claude Code subagents docs](https://code.claude.com/docs/en/sub-agents).

## Install

```bash
npx skills add https://github.com/TheBeardNerd/skills --skill agent-builder
```

## Usage

| Intent | Example prompt |
|--------|----------------|
| Build a subagent | `"Build a subagent that reviews my code for security issues"` |
| Decide the artifact | `"Should this be a subagent or a skill?"` |
| Right-size a design | `"Is a swarm of nested subagents overkill for FAQ from our docs?"` |
| Convert a workflow | `"Turn this manual review process into a reusable subagent"` |

## How It Works

Six phases, structure-first:

1. **Intake** — gather the signals that drive the decision (why isolate it, tools it
   needs / must not have, risk, model, scope).
2. **Decide structure** — Gate 0 (is a subagent the right artifact, or does a hook /
   CLAUDE.md / skill / the main conversation fit better?) → topology via
   `recommend_structure.py` → components → guardrail config. Output: a blueprint shown
   before any file is written.
3. **Scaffold** — `scaffold_agent.py` emits one `.claude/agents/<name>.md`: YAML
   frontmatter (`name`, `description`, `tools`, `model`, …) + the system prompt body.
4. **Populate** — sharpen the trigger-first description, the cold-start system prompt
   (role → "When invoked" steps → output format → stop line), and the tool wall.
5. **Validate** — `validate_agent.py` is a hard gate: parseable frontmatter,
   kebab-case `name`, non-empty `description` + body, a valid `model`, and no UI-only
   tools that never work in a subagent.
6. **Report** — verdict, file path, validation result, how to invoke it.

The output is a native Claude Code subagent: invoke with `"use the <name> subagent"`
or `@agent-<name>`. By default it's written user-scope to `~/.claude/agents/`
(available in all your projects); use `--scope project` for a checked-in
`.claude/agents/` file shared with the team.

## Scripts

```bash
SKILL_DIR=~/.claude/skills/agent-builder

# Reproducible artifact + topology verdict from a signals JSON
python3 "$SKILL_DIR/scripts/recommend_structure.py" --print-template > signals.json
python3 "$SKILL_DIR/scripts/recommend_structure.py" --signals signals.json

# Generate a subagent file
python3 "$SKILL_DIR/scripts/scaffold_agent.py" --print-spec > agent-spec.json
python3 "$SKILL_DIR/scripts/scaffold_agent.py" --spec agent-spec.json             # default user -> ~/.claude/agents/<name>.md
python3 "$SKILL_DIR/scripts/scaffold_agent.py" --spec agent-spec.json --scope project   # -> ./.claude/agents/

# Hard gate (a file or a whole directory)
python3 "$SKILL_DIR/scripts/validate_agent.py" ./.claude/agents/<name>.md
python3 "$SKILL_DIR/scripts/validate_agent.py" ./.claude/agents --strict
```

## Tests

```bash
python3 -m unittest discover -s tests
```
