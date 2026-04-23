---
name: session-handoff
description: Use when a user wants to save session state, create a handoff, resume from a previous handoff, continue work from saved context, or when substantial progress suggests preserving project context for a future agent.
---

# Session Handoff

## Overview

Create or resume project-local handoff documents so a fresh agent can continue work with minimal ambiguity.

## When to Use

- User says "create handoff", "save state", "pause here", or similar
- User says "resume from the last handoff", "load handoff", or similar
- Significant progress, debugging, or architecture work suggests preserving context

**When NOT to use:** Do not create a handoff automatically — only suggest one after substantial work. Do not resume a handoff without reading it fully first.

## CREATE Workflow

1. Use `.ai/handoffs/` in the active project.
2. Set `SKILL_DIR="${SKILL_DIR:-$HOME/.claude/skills/session-handoff}"`.
3. Run `python3 "$SKILL_DIR/scripts/create_handoff.py" <slug>`.
4. Fill in the required sections from [Handoff Template](./templates/handoff-template.md), using project-relative paths in `Critical Files`.
5. Run `python3 "$SKILL_DIR/scripts/validate_handoff.py" <handoff-file>`.
6. Report the saved path, validation result, and first next step.

## RESUME Workflow

1. Set `SKILL_DIR="${SKILL_DIR:-$HOME/.claude/skills/session-handoff}"`.
2. Run `python3 "$SKILL_DIR/scripts/list_handoffs.py"`.
3. Read the most relevant handoff completely.
4. Run `python3 "$SKILL_DIR/scripts/check_staleness.py" <handoff-file>` (add `--fail-on-stale` for strict automation gates). Absolute paths are blocked by default; use `--allow-absolute-paths` only when intentionally needed.
5. Follow [Resume Checklist](./references/resume-checklist.md) before acting.
6. Start from `Immediate Next Steps` item 1 unless redirected.
