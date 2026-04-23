# session-handoff

Agent skill for creating and resuming project-local session handoffs. Lets a fresh agent pick up exactly where the last one left off.

## Install

```bash
npx skills add https://github.com/TheBeardNerd/skills --skill session-handoff
```

For non-interactive usage:

```bash
npx skills add https://github.com/TheBeardNerd/skills --skill session-handoff -y
```

## Usage

Once installed, trigger the skill with natural language:

| Intent | Example prompt |
|--------|---------------|
| Save current progress | `"Create a session handoff for this work"` |
| Save with a label | `"Save state as auth-refactor"` |
| Resume later | `"Resume from the last handoff"` |
| Resume a specific one | `"Load the auth-refactor handoff"` |

The agent will also proactively suggest creating a handoff after substantial work (debugging sessions, architecture decisions, large refactors).

## How It Works

### Creating a Handoff

The agent runs `create_handoff.py <slug>`, which scaffolds a timestamped markdown file at `.ai/handoffs/<timestamp>-<slug>.md` inside your project. The agent then fills in all required sections and validates the document before reporting back.

Handoff files contain:

| Section | What goes here |
|---------|---------------|
| **Session Metadata** | Timestamp, project path, git branch |
| **Current State Summary** | One-paragraph status snapshot |
| **Important Context** | Architecture discoveries, blockers, constraints |
| **Immediate Next Steps** | Ordered action items for the next agent |
| **Decisions Made** | Key decisions and their rationale |
| **Critical Files** | Project-relative paths to files that matter |

`validate_handoff.py` checks that all sections are present, no `[TODO:]` placeholders remain, and no secrets (AWS keys, GitHub tokens, API keys) were accidentally included.

### Resuming a Handoff

The agent runs `list_handoffs.py` (newest first), reads the most relevant handoff completely, then runs `check_staleness.py` to verify the files referenced in **Critical Files** still exist on disk. It works through a resume checklist before taking any action.

`check_staleness.py` flags:
- Missing files referenced in Critical Files
- Absolute paths (blocked by default; use `--allow-absolute-paths` to opt in)
- Add `--fail-on-stale` to make CI/automation gates strict

## Package Layout

```text
session-handoff/
├── SKILL.md
├── scripts/
│   ├── create_handoff.py       # scaffold timestamped handoff file
│   ├── list_handoffs.py        # list handoffs newest-first
│   ├── validate_handoff.py     # check completeness + no secrets
│   └── check_staleness.py      # verify Critical Files still exist
├── references/
│   └── resume-checklist.md     # checklist the agent runs before acting
├── templates/
│   └── handoff-template.md     # handoff document template
├── tests/
│   └── test_handoff_scripts.py
└── evals/
    ├── pressure-scenarios.md
    ├── baseline-without-skill.md
    └── green-with-skill.md
```

## Running the Tests

```bash
python3 -m unittest tests/test_handoff_scripts.py
```
