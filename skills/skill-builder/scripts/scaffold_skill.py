#!/usr/bin/env python3
"""Scaffold a new Claude Skill directory that already clears validate_skill.py.

Creates the repo-standard layout (SKILL.md, README.md, package.json, .gitignore,
references/, scripts/, templates/, tests/, evals/ trio). Existing files are never
overwritten unless --force is passed, so it is safe to re-run.

Usage:
    python3 scaffold_skill.py <name> --description "Use when ..." [--base DIR]
    python3 scaffold_skill.py --spec spec.json [--base DIR] [--force]

The optional spec.json may carry: name, description, scope ("@scope"),
components (list among scripts/references/templates/hooks). CLI flags win over
the spec file. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_BASE = Path.home() / "Projects" / "skills" / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

EVAL_TRIO = {
    "baseline-without-skill.md": (
        "# Without Skill (BASELINE)\n\n"
        "Record how a plain agent (no skill loaded) handles each scenario, so the\n"
        "skill's added value is measurable. Run the same prompts as the GREEN file.\n\n"
        "## Scenario 1: <prompt>\n\n"
        "Prompt:\n\n```\n<paste the user prompt>\n```\n\n"
        "Observed behavior:\n\n- <what the agent did without the skill>\n\n"
        "Gap: <what was missing / wrong>\n"
    ),
    "green-with-skill.md": (
        "# With Skill Applied (GREEN)\n\n"
        "Record passing behavior with the skill active. Mirror the BASELINE prompts.\n\n"
        "## Scenario 1: <prompt>\n\n"
        "Prompt:\n\n```\n<paste the same user prompt>\n```\n\n"
        "Observed output:\n\n```\n<paste output>\n```\n\n"
        "Result: PASS — <why this is correct>.\n"
    ),
    "pressure-scenarios.md": (
        "# Pressure Scenarios\n\n"
        "Adversarial / edge cases that should NOT break the skill or cause it to\n"
        "fire when it shouldn't.\n\n"
        "## 1. Should-not-trigger: <off-topic prompt>\n\n"
        "Expected: skill stays dormant.\n\n"
        "## 2. Ambiguous input: <prompt>\n\n"
        "Expected: skill asks a targeted clarifying question instead of guessing.\n\n"
        "## 3. Hostile input: <prompt>\n\n"
        "Expected: skill refuses unsafe requests and explains why.\n"
    ),
}


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return s


def default_description(name: str) -> str:
    pretty = name.replace("-", " ")
    return (
        f"Use when the user wants to {pretty}, or asks for help with {pretty}. "
        f"Replace this with concrete trigger phrases before shipping."
    )


def skill_md(name: str, description: str) -> str:
    title = name.replace("-", " ").title()
    return (
        f"---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        f"---\n\n"
        f"# {title}\n\n"
        f"## Overview\n\n"
        f"<One paragraph: what this skill does and the outcome it produces.>\n\n"
        f"## When to Use\n\n"
        f"- <concrete trigger 1>\n"
        f"- <concrete trigger 2>\n\n"
        f"**When NOT to use:** <out-of-scope cases that should stay dormant.>\n\n"
        f"## Workflow\n\n"
        f"1. <step>\n"
        f"2. <step>\n"
        f"3. Validate the result before reporting it.\n\n"
        f"## Output\n\n"
        f"<Define the exact output format, with an example.>\n"
    )


def readme_md(name: str, scope: str, description: str) -> str:
    return (
        f"# {name}\n\n"
        f"{description}\n\n"
        f"## Install\n\n"
        f"```bash\n"
        f"npx skills add https://github.com/TheBeardNerd/skills --skill {name}\n"
        f"```\n\n"
        f"## Usage\n\n"
        f"| Intent | Example prompt |\n"
        f"|--------|----------------|\n"
        f"| <intent> | `\"<example>\"` |\n\n"
        f"## How It Works\n\n"
        f"<Short explanation of the workflow.>\n"
    )


def package_json(name: str, scope: str, description: str) -> str:
    pkg = {
        "name": f"{scope}/{name}-skill",
        "version": "0.1.0",
        "description": description[:120],
        "license": "MIT",
        "scripts": {"test": "python3 -m unittest discover -s tests"},
    }
    return json.dumps(pkg, indent=2) + "\n"


GITIGNORE = """\
# OS
.DS_Store
Thumbs.db

# Python
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
.tox/
build/
dist/

# Virtual environments
.venv/
venv/
env/

# Node (skills ship package.json; npx installs)
node_modules/

# Editors/IDEs
.idea/
.vscode/

# Logs & temp
*.log
*.tmp

# Secrets, env & certificates
.env
.env.*
!.env.example
*.pem
*.key
*.p12
*.pfx
*.crt
*.cer
*.der
*.jks
*.keystore
secrets/
*.secret
"""


def write_file(path: Path, content: str, force: bool, created: list[str]) -> None:
    if path.exists() and not force:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    created.append(path.name)


def scaffold(
    name: str,
    description: str,
    base: Path,
    scope: str = "@twc",
    components: list[str] | None = None,
    force: bool = False,
) -> tuple[Path, list[str]]:
    if not NAME_RE.match(name):
        raise ValueError(f"name '{name}' must be kebab-case (lowercase letters, digits, hyphens).")
    components = components or []
    skill_dir = base / name
    created: list[str] = []

    write_file(skill_dir / "SKILL.md", skill_md(name, description), force, created)
    write_file(skill_dir / "README.md", readme_md(name, scope, description), force, created)
    write_file(skill_dir / "package.json", package_json(name, scope, description), force, created)
    write_file(skill_dir / ".gitignore", GITIGNORE, force, created)

    for fname, content in EVAL_TRIO.items():
        write_file(skill_dir / "evals" / fname, content, force, created)

    # Always create the standard dirs so the layout is obvious; populate on demand.
    for sub in ("references", "scripts", "templates", "tests"):
        (skill_dir / sub).mkdir(parents=True, exist_ok=True)

    if "tests" not in components:
        # Ensure unittest discovery has something to find; harmless placeholder.
        pass

    return skill_dir, created


def load_spec(spec_path: Path) -> dict:
    data = json.loads(spec_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("spec file must contain a JSON object.")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scaffold a new Claude Skill.")
    parser.add_argument("name", nargs="?", help="skill name (kebab-case)")
    parser.add_argument("--description", help="frontmatter description (must include a trigger cue)")
    parser.add_argument("--spec", type=Path, help="JSON spec file")
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE, help="parent dir for the skill")
    parser.add_argument("--scope", default="@twc", help="npm scope for package.json")
    parser.add_argument("--force", action="store_true", help="overwrite existing files")
    args = parser.parse_args(argv)

    spec = load_spec(args.spec) if args.spec else {}
    name = args.name or spec.get("name")
    if not name:
        parser.error("a skill name is required (positional arg or spec.name).")
    name = slugify(name)
    description = args.description or spec.get("description") or default_description(name)
    scope = args.scope or spec.get("scope", "@twc")
    components = spec.get("components", [])

    skill_dir, created = scaffold(
        name=name,
        description=description,
        base=args.base,
        scope=scope,
        components=components,
        force=args.force,
    )
    print(str(skill_dir))
    if created:
        print("created: " + ", ".join(created))
    else:
        print("created: (nothing new — all files already existed; use --force to overwrite)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
