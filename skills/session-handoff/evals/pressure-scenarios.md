# Session Handoff Pressure Scenarios

## Scenario 1: Create under time pressure
Prompt: "We're out of time. Create a handoff right now so another agent can continue later."
Pass criteria:
- Uses `.ai/handoffs/` in the active project
- Includes current state, important context, decisions, next steps, and critical files
- Checks the handoff for required sections and placeholder content before declaring it done

## Scenario 2: Resume in a stale repo
Prompt: "Load the last handoff and continue."
Pass criteria:
- Lists available handoffs first
- Checks freshness before acting
- Checks that the referenced branch, files, and working tree state still match the current repo

## Scenario 3: Proactive suggestion after substantial work
Prompt: "We just finished a multi-file change and cleared the blocking issue."
Pass criteria:
- Suggests creating a handoff
- Does not write one automatically without user intent

## Evidence Files

- RED baseline evidence: `evals/baseline-without-skill.md`
- GREEN passing evidence: `evals/green-with-skill.md`
