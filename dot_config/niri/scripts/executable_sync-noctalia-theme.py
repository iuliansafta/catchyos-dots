#!/usr/bin/env python3
"""Sync niri focus-ring colors from Noctalia's current theme.

Reads ~/.config/noctalia/colors.json and updates the focus-ring color lines in
~/.config/niri/cfg/layout.kdl. Intended for Noctalia hooks.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
COLORS_PATH = HOME / ".config/noctalia/colors.json"
LAYOUT_PATH = HOME / ".config/niri/cfg/layout.kdl"
NIRI_CONFIG_PATH = HOME / ".config/niri/config.kdl"

BEGIN = "// BEGIN noctalia-theme-colors"
END = "// END noctalia-theme-colors"


def normalize_hex(value: str, fallback: str) -> str:
    value = str(value or fallback).strip()
    if not value.startswith("#"):
        value = fallback
    value = value.lower()
    if re.fullmatch(r"#[0-9a-f]{3}", value):
        value = "#" + "".join(ch * 2 for ch in value[1:])
    if re.fullmatch(r"#[0-9a-f]{8}", value):
        value = value[:7]
    if not re.fullmatch(r"#[0-9a-f]{6}", value):
        value = fallback
    return value


def with_alpha(hex_rgb: str, alpha: str) -> str:
    alpha = alpha.strip().lower().lstrip("#")
    if not re.fullmatch(r"[0-9a-f]{2}", alpha):
        raise ValueError(f"Invalid alpha value: {alpha!r}")
    return f"{hex_rgb}{alpha}"


def build_generated_block(colors: dict[str, str]) -> list[str]:
    primary = normalize_hex(colors.get("mPrimary", ""), "#ebbcba")
    outline = normalize_hex(colors.get("mOutline", ""), "#403d52")
    error = normalize_hex(colors.get("mError", ""), "#eb6f92")

    active = with_alpha(primary, os.environ.get("NIRI_FOCUS_ACTIVE_ALPHA", "80"))
    inactive = with_alpha(outline, os.environ.get("NIRI_FOCUS_INACTIVE_ALPHA", "55"))
    urgent = with_alpha(error, os.environ.get("NIRI_FOCUS_URGENT_ALPHA", "80"))

    indent = "            "
    return [
        f"{indent}{BEGIN}\n",
        f'{indent}active-color "{active}" // from Noctalia mPrimary\n',
        f'{indent}inactive-color "{inactive}" // from Noctalia mOutline\n',
        f'{indent}urgent-color "{urgent}" // from Noctalia mError\n',
        f"{indent}{END}\n",
    ]


def find_focus_ring(lines: list[str]) -> tuple[int, int]:
    start = None
    depth = 0
    for i, line in enumerate(lines):
        if start is None and re.match(r"\s*focus-ring\s*\{", line):
            start = i
            depth = line.count("{") - line.count("}")
            if depth <= 0:
                return i, i
            continue
        if start is not None:
            depth += line.count("{") - line.count("}")
            if depth <= 0:
                return start, i
    raise RuntimeError(f"Could not find focus-ring block in {LAYOUT_PATH}")


def update_layout(generated: list[str]) -> bool:
    original = LAYOUT_PATH.read_text().splitlines(keepends=True)
    start, end = find_focus_ring(original)
    block = original[start : end + 1]

    begin_idx = next((i for i, line in enumerate(block) if BEGIN in line), None)
    end_idx = next((i for i, line in enumerate(block) if END in line), None)

    if begin_idx is not None and end_idx is not None and begin_idx < end_idx:
        new_block = block[:begin_idx] + generated + block[end_idx + 1 :]
    else:
        # Remove old hand-written color lines to avoid duplicate keys.
        stripped = [
            line
            for line in block
            if not re.match(r"\s*(active-color|inactive-color|urgent-color)\b", line)
        ]
        insert_at = next((i + 1 for i, line in enumerate(stripped) if re.match(r"\s*width\b", line)), 2)
        new_block = stripped[:insert_at] + generated + stripped[insert_at:]

    updated = original[:start] + new_block + original[end + 1 :]
    if updated == original:
        return False

    backup = LAYOUT_PATH.with_suffix(LAYOUT_PATH.suffix + ".pre-theme-sync")
    shutil.copy2(LAYOUT_PATH, backup)
    LAYOUT_PATH.write_text("".join(updated))

    result = subprocess.run(
        ["niri", "validate", "-c", str(NIRI_CONFIG_PATH)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode != 0:
        shutil.copy2(backup, LAYOUT_PATH)
        print(result.stdout, file=sys.stderr)
        raise RuntimeError("niri config validation failed; restored previous layout.kdl")
    return True


def reload_niri() -> None:
    result = subprocess.run(
        ["niri", "msg", "action", "load-config-file"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode != 0:
        print("niri reload skipped/failed:", result.stdout.strip(), file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-reload", action="store_true", help="update file only; do not reload niri")
    args = parser.parse_args()

    colors = json.loads(COLORS_PATH.read_text())
    generated = build_generated_block(colors)
    changed = update_layout(generated)

    if not args.no_reload:
        reload_niri()

    stamp = datetime.now().isoformat(timespec="seconds")
    print(f"[{stamp}] synced niri focus-ring colors from {COLORS_PATH} ({'changed' if changed else 'unchanged'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
