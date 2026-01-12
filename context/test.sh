#!/usr/bin/env bash
set -euo pipefail

# locate context.txt relative to this script
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ctx_file="$script_dir/context.txt"

# fallback: check common locations
if [[ ! -f $ctx_file ]]; then
    if [[ -f "$script_dir/../context.txt" ]]; then
        ctx_file="$script_dir/../context.txt"
    elif [[ -f "./context.txt" ]]; then
        ctx_file="./context.txt"
    fi
fi

if [[ ! -f $ctx_file ]]; then
    echo "context.txt not found. Checked: $script_dir/context.txt, $script_dir/../context.txt, ./context.txt" >&2
    exit 1
fi

content=$(<"$ctx_file")
python video_tool.py "$content" -p douyin -f caption -t energetic -l 2_min -n 1