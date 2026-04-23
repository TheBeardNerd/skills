#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENTS_SKILL_PATH="${HOME}/.agents/skills/session-handoff"
CLAUDE_SKILL_PATH="${HOME}/.claude/skills/session-handoff"
AUTO_CONFIRM=0

if [[ "${1:-}" == "--yes" ]]; then
  AUTO_CONFIRM=1
elif [[ -n "${1:-}" ]]; then
  echo "Usage: $0 [--yes]" >&2
  exit 2
fi

describe_target() {
  local path="$1"

  if [[ -L "$path" ]]; then
    echo "$path -> $(readlink "$path")"
    return
  fi

  if [[ -e "$path" ]]; then
    echo "$path (existing non-symlink path)"
    return
  fi

  echo "$path (missing)"
}

assert_linkable() {
  local path="$1"

  if [[ -e "$path" && ! -L "$path" ]]; then
    echo "Refusing to replace non-symlink path: $path" >&2
    exit 1
  fi
}

confirm_install() {
  echo "This will update skill links:"
  echo "  ${AGENTS_SKILL_PATH} -> ${REPO_ROOT}"
  echo "  ${CLAUDE_SKILL_PATH} -> ${AGENTS_SKILL_PATH}"
  echo "Current targets:"
  describe_target "${AGENTS_SKILL_PATH}"
  describe_target "${CLAUDE_SKILL_PATH}"

  if [[ "$AUTO_CONFIRM" -eq 1 ]]; then
    return
  fi

  if [[ ! -t 0 ]]; then
    echo "Refusing non-interactive install without --yes." >&2
    exit 1
  fi

  printf "Continue? [y/N] "
  read -r reply
  case "$reply" in
    y|Y|yes|YES)
      ;;
    *)
      echo "Aborted."
      exit 1
      ;;
  esac
}

mkdir -p "${HOME}/.agents/skills"
mkdir -p "${HOME}/.claude/skills"

confirm_install
assert_linkable "${AGENTS_SKILL_PATH}"
assert_linkable "${CLAUDE_SKILL_PATH}"

ln -sfn "${REPO_ROOT}" "${AGENTS_SKILL_PATH}"
ln -sfn "${AGENTS_SKILL_PATH}" "${CLAUDE_SKILL_PATH}"

echo "Installed session-handoff skill"
echo "  OpenCode/Codex: ${AGENTS_SKILL_PATH} -> ${REPO_ROOT}"
echo "  Claude Code:    ${CLAUDE_SKILL_PATH} -> ${AGENTS_SKILL_PATH}"
