#!/usr/bin/env bash
set -euo pipefail

# locate context.txt relative to this script

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
context_path="context_rewrite.txt"
ctx_file="$script_dir/$context_path"
# fallback: check common locations
if [[ ! -f $ctx_file ]]; then
    if [[ -f "$script_dir/../$context_path" ]]; then
        ctx_file="$script_dir/../$context_path"
    elif [[ -f "./$context_path" ]]; then
        ctx_file="./$context_path"
    fi
fi

if [[ ! -f $ctx_file ]]; then
    echo "context.txt not found. Checked: $script_dir/$context_path, $script_dir/../$context_path, ./$context_path" >&2
    exit 1
fi

content=$(<"$ctx_file")
echo "Using context from: $ctx_file"
echo "generating video content..."
python video_tool.py "$content" -p douyin -f caption -t energetic -l 2_min -n 1 --similarity 50