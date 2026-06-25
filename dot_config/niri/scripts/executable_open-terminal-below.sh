#!/usr/bin/env bash
set -euo pipefail

before_id=""
before_id=$(niri msg -j focused-window 2>/dev/null | jq -r '.id // empty' 2>/dev/null || true)

# Open Ghostty normally. niri will focus the new window when it appears.
niri msg action spawn ghostty >/dev/null

changed_id=""

# Wait until the newly spawned terminal receives focus, then pull it into the
# column on the left so it lands below the window that was focused before.
for _ in {1..40}; do
    focused_json=$(niri msg -j focused-window 2>/dev/null || true)
    focused_id=$(jq -r '.id // empty' <<<"$focused_json" 2>/dev/null || true)
    app_id=$(jq -r '.app_id // empty' <<<"$focused_json" 2>/dev/null || true)

    if [[ -n "$focused_id" && "$focused_id" != "$before_id" ]]; then
        changed_id="$focused_id"
        if [[ "$app_id" =~ ([Gg]hostty|com\.mitchellh\.ghostty) ]]; then
            niri msg action consume-or-expel-window-left >/dev/null
            exit 0
        fi
    fi

    sleep 0.05
done

# Fallback: if focus changed but app-id matching failed, assume the spawned
# window is focused and still perform the left consume action.
if [[ -n "$changed_id" ]]; then
    niri msg action consume-or-expel-window-left >/dev/null
fi
