#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
root="$PWD"

if [[ "${1:-}" == "--check" && $# == 1 ]]; then
    for cli in herdr codex opencode python3 git jq; do
        command -v "$cli"
        "$cli" --version
    done
    codex login status
    herdr workspace create --help
    herdr tab create --help
    herdr pane run --help
    codex exec --help
    opencode run --help
    exit
fi

if [[ $# != 3 || "${1:-}" != "--launch" ]]; then
    echo "Usage: $0 --check | --launch RUN_ID opencode/VERIFIED-MODEL-free"
    exit 2
fi

run_id=$2
model=$3
[[ "$run_id" =~ ^[a-zA-Z0-9_-]+$ ]] || { echo "Invalid run ID."; exit 2; }
[[ "$model" =~ ^opencode/[a-zA-Z0-9_.-]+-free$ ]] || {
    echo "Choose a confirmed free OpenCode model with an opencode/*-free ID."
    exit 2
}
[[ "${HERDR_ENV:-}" == 1 ]] || { echo "Run --launch from inside Herdr."; exit 2; }
[[ ! -e "tasks/$run_id" ]] || { echo "Run ID already exists."; exit 2; }
login=$(codex login status 2>&1)
[[ "$login" == *"Logged in using ChatGPT"* ]] || { echo "$login"; exit 2; }
herdr status

layout=$(herdr workspace create --label "Eventify $run_id" --cwd "$root" --no-focus)
workspace=$(jq -er '.result.workspace.workspace_id' <<< "$layout")
coordinator=$(jq -er '.result.root_pane.pane_id' <<< "$layout")
tab=$(jq -er '.result.tab.tab_id' <<< "$layout")
herdr tab rename "$tab" Coordinator
panes=()
for role in Logistics Budget Marketing Reviewer; do
    layout=$(herdr tab create --workspace "$workspace" --label "$role" --cwd "$root" --no-focus)
    panes+=("$(jq -er '.result.root_pane.pane_id' <<< "$layout")")
done

printf -v command '%q ' python3 scripts/workflow.py start "$run_id" "$model" "${panes[@]}"
herdr pane run "$coordinator" "$command"
herdr workspace focus "$workspace"
