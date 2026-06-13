# clarify — companion hook

`clarify-rule.md` is the lightweight rule injected on every prompt by a
`UserPromptSubmit` hook. The hook prints this file to stdout; Claude Code adds
the text to the prompt context, where it tells the agent to invoke the `clarify`
skill **only** when a prompt is genuinely ambiguous (high bar — see the skill).

## Wiring (global, all projects)

Add to `~/.claude/settings.json` under `hooks`:

```json
"UserPromptSubmit": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "cat /Users/twc/Projects/skills/skills/clarify/hook/clarify-rule.md"
      }
    ]
  }
]
```

The rule is intentionally short — it runs on *every* prompt, so keep its token
cost minimal. Edit `clarify-rule.md` to tune the trigger sensitivity; no settings
change needed.
