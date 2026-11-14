#!/usr/bin/env bash
# PreToolUse guard: `canvas deploy` ships aj-cafm only from the pushed `canvas` branch.
# Canvas cannot pull from GitHub (it is on the corporate network), so the GitHub `canvas`
# branch is kept as the exact source of every deploy by refusing any other state here.
set -u
cmd=$(jq -r '.tool_input.command // ""')
case "$cmd" in
  *"canvas deploy"*) ;;
  *) exit 0 ;;
esac

repo="${CLAUDE_PROJECT_DIR:-$(pwd)}"
deny() {
  jq -n --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'
  exit 0
}

branch=$(git -C "$repo" branch --show-current 2>/dev/null)
[ "$branch" = "canvas" ] || deny "canvas deploy runs only from the 'canvas' branch (current: ${branch:-detached}). Merge the work into canvas, push it, then deploy."

[ -z "$(git -C "$repo" status --porcelain 2>/dev/null)" ] || deny "Working tree has uncommitted changes. Commit and push to origin/canvas before deploying."

git -C "$repo" fetch -q origin canvas 2>/dev/null || deny "Could not fetch origin/canvas to confirm the deploy matches GitHub."
local_sha=$(git -C "$repo" rev-parse HEAD)
remote_sha=$(git -C "$repo" rev-parse origin/canvas 2>/dev/null)
[ "$local_sha" = "$remote_sha" ] || deny "Local canvas ($local_sha) differs from origin/canvas (${remote_sha:-missing}). Push first so the deploy matches GitHub."
exit 0
