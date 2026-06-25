#!/usr/bin/env bash
# xe-gpu-watch — alert on Intel xe (Panther Lake / Arc) GPU hangs & resets.
# Installed while testing linux-cachyos-rc (7.1) for GPU stability.
# Tails the kernel journal, logs matches, and fires a desktop notification.
set -uo pipefail

LOG="${XDG_STATE_HOME:-$HOME/.local/state}/xe-gpu-watch.log"
mkdir -p "$(dirname "$LOG")"

# Serious GPU events worth interrupting for.
PATTERN='GPU HANG|engine reset|GT[0-9]+: reset|gpu hang|guc.*(crash|fail|timeout)|\bwedged\b|reset device|drm.*\bhang\b|xe .*\*ERROR\*'

# Known-benign noise on 7.1-rc7 (transient race / cosmetic) — do not alert on these.
EXCLUDE='GSC proxy component not bound|Selective fetch area calculation failed'

echo "$(date -Is) xe-gpu-watch started (kernel: $(uname -r))" >> "$LOG"

journalctl -kf -n0 -o short-iso 2>/dev/null | while IFS= read -r line; do
    if grep -qiE "$PATTERN" <<<"$line" && ! grep -qiE "$EXCLUDE" <<<"$line"; then
        echo "$line" >> "$LOG"
        notify-send -u critical -a "GPU Watch" "⚠️ Intel xe GPU event" "$line" 2>/dev/null || true
    fi
done
