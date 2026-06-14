#!/usr/bin/env bash
set -euo pipefail

action="${1:-}"
step="${BRIGHTNESS_STEP:-5}"

if [[ "$action" != "up" && "$action" != "down" ]]; then
	echo "Usage: $0 up|down" >&2
	exit 2
fi

focused_output="$(niri msg -j focused-output 2>/dev/null | python -c 'import json,sys; print(json.load(sys.stdin).get("name", ""))' 2>/dev/null || true)"

notify_unavailable() {
	if command -v notify-send >/dev/null 2>&1; then
		notify-send "Brightness" "$1"
	else
		echo "$1" >&2
	fi
}

case "$focused_output" in
eDP-* | LVDS-*)
	if [[ "$action" == "up" ]]; then
		brightnessctl -d intel_backlight s "+${step}%" -n
	else
		brightnessctl -d intel_backlight s "${step}%-" -n
	fi
	;;
DP-* | HDMI-* | *)
	if command -v asdbctl >/dev/null 2>&1 && asdbctl get >/dev/null 2>&1; then
		if [[ "$action" == "up" ]]; then
			asdbctl up --step "$step"
		else
			asdbctl down --step "$step"
		fi
	else
		notify_unavailable "Apple Studio Display brightness needs the display USB/HID connection. Try a direct Thunderbolt/USB-C connection or reconnect the monitor."
		exit 1
	fi
	;;
esac
