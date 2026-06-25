#!/usr/bin/env python3
"""Sync niri colors and make Kitty follow Noctalia's generated theme.

Reads ~/.config/noctalia/colors.json and updates niri focus-ring colors in
~/.config/niri/cfg/layout.kdl.

For Kitty, Noctalia already generates ~/.config/kitty/themes/noctalia.conf and
~/.config/kitty/current-theme.conf. This script keeps kitty.conf pointed at that
Noctalia template and adds local-only Kitty options such as padding and opacity.

For Brave, this generates an unpacked browser theme extension from Noctalia
colors and ensures Brave loads it via ~/.config/brave-flags.conf.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
COLORS_PATH = HOME / ".config/noctalia/colors.json"
LAYOUT_PATH = HOME / ".config/niri/cfg/layout.kdl"
NIRI_CONFIG_PATH = HOME / ".config/niri/config.kdl"
KITTY_DIR = HOME / ".config/kitty"
KITTY_CONF_PATH = KITTY_DIR / "kitty.conf"
KITTY_THEME_INCLUDE = "current-theme.conf"
KITTY_THEME_PATH = KITTY_DIR / KITTY_THEME_INCLUDE
KITTY_NOCTALIA_THEME_PATH = KITTY_DIR / "themes/noctalia.conf"
BRAVE_THEME_DIR = HOME / ".config/brave-noctalia-theme"
BRAVE_THEME_MANIFEST_PATH = BRAVE_THEME_DIR / "manifest.json"
BRAVE_FLAGS_PATH = HOME / ".config/brave-flags.conf"
BRAVE_THEME_FLAG = f"--load-extension={BRAVE_THEME_DIR}"
SDDM_SYNC_SCRIPT = HOME / ".config/sddm/sync-noctalia-theme.py"

BEGIN = "// BEGIN noctalia-theme-colors"
END = "// END noctalia-theme-colors"
KITTY_MANAGED_BEGIN = "# BEGIN noctalia-kitty-local-options"
KITTY_MANAGED_END = "# END noctalia-kitty-local-options"
KITTY_CURRENT_INCLUDE_RE = re.compile(r"^\s*include\s+(?:\./)?current-theme\.conf\s*$")
KITTY_OLD_INCLUDE_RE = re.compile(r"^\s*include\s+(?:\./)?noctalia-theme\.conf\s*$")
BRAVE_OLD_THEME_FLAG_RE = re.compile(r"^--load-extension=.*brave-noctalia-theme/?\s*$")


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


def theme_color(colors: dict[str, str], key: str, fallback: str) -> str:
    return normalize_hex(colors.get(key, ""), fallback)


def with_alpha(hex_rgb: str, alpha: str) -> str:
    alpha = alpha.strip().lower().lstrip("#")
    if not re.fullmatch(r"[0-9a-f]{2}", alpha):
        raise ValueError(f"Invalid alpha value: {alpha!r}")
    return f"{hex_rgb}{alpha}"


def build_generated_block(colors: dict[str, str]) -> list[str]:
    primary = theme_color(colors, "mPrimary", "#ebbcba")
    outline = theme_color(colors, "mOutline", "#403d52")
    error = theme_color(colors, "mError", "#eb6f92")

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


def strip_managed_kitty_block(lines: list[str]) -> list[str]:
    stripped: list[str] = []
    in_managed = False
    for line in lines:
        if line.strip() == KITTY_MANAGED_BEGIN:
            in_managed = True
            continue
        if line.strip() == KITTY_MANAGED_END:
            in_managed = False
            continue
        if not in_managed:
            stripped.append(line)
    return stripped


def ensure_kitty_theme_link() -> bool:
    if KITTY_THEME_PATH.exists() or KITTY_THEME_PATH.is_symlink():
        return False
    if not KITTY_NOCTALIA_THEME_PATH.exists():
        return False
    KITTY_THEME_PATH.symlink_to(Path("themes/noctalia.conf"))
    return True


def build_kitty_managed_block(include_needed: bool) -> list[str]:
    padding = os.environ.get("KITTY_WINDOW_PADDING", "14")
    opacity = os.environ.get("KITTY_BACKGROUND_OPACITY", "0.93")
    lines: list[str] = []
    if include_needed:
        lines.extend([
            "# Theme generated by Noctalia's Kitty template.\n",
            f"include {KITTY_THEME_INCLUDE}\n",
            "\n",
        ])
    lines.extend([
        f"{KITTY_MANAGED_BEGIN}\n",
        "# Match Ghostty spacing and transparency.\n",
        f"window_padding_width {padding}\n",
        f"background_opacity {opacity}\n",
        "dynamic_background_opacity yes\n",
        f"{KITTY_MANAGED_END}\n",
    ])
    return lines


def update_kitty() -> bool:
    KITTY_DIR.mkdir(parents=True, exist_ok=True)
    link_changed = ensure_kitty_theme_link()

    original = KITTY_CONF_PATH.read_text().splitlines(keepends=True) if KITTY_CONF_PATH.exists() else []
    lines = strip_managed_kitty_block(original)

    # Remove the custom generated theme include from the previous approach.
    lines = [
        line
        for line in lines
        if not KITTY_OLD_INCLUDE_RE.match(line)
        and "Theme generated from Noctalia by niri/scripts/sync-noctalia-theme.py" not in line
        and "Local Kitty config. Theme is generated from Noctalia." not in line
    ]

    has_current_include = any(KITTY_CURRENT_INCLUDE_RE.match(line) for line in lines)
    while lines and not lines[-1].strip():
        lines.pop()

    if lines:
        lines.append("\n")
        lines.append("\n")
    lines.extend(build_kitty_managed_block(include_needed=not has_current_include))

    updated = "".join(lines)
    old = KITTY_CONF_PATH.read_text() if KITTY_CONF_PATH.exists() else None
    if old != updated:
        KITTY_CONF_PATH.write_text(updated)
        return True
    return link_changed


def hex_to_rgb(hex_rgb: str) -> list[int]:
    color = normalize_hex(hex_rgb, "#000000").lstrip("#")
    return [int(color[i : i + 2], 16) for i in (0, 2, 4)]


def build_brave_theme_manifest(colors: dict[str, str]) -> dict[str, object]:
    surface = theme_color(colors, "mSurface", "#0c1017")
    surface_variant = theme_color(colors, "mSurfaceVariant", "#11151d")
    shadow = theme_color(colors, "mShadow", "#090d13")
    primary = theme_color(colors, "mPrimary", "#c4a82e")
    secondary = theme_color(colors, "mSecondary", "#d14358")
    tertiary = theme_color(colors, "mTertiary", "#00a66c")
    outline = theme_color(colors, "mOutline", "#45a0d6")
    on_surface = theme_color(colors, "mOnSurface", "#d8e0ff")
    on_surface_variant = theme_color(colors, "mOnSurfaceVariant", "#9b6bc1")
    on_primary = theme_color(colors, "mOnPrimary", surface)

    return {
        "manifest_version": 3,
        "version": "1.0.0",
        "name": "Noctalia Theme",
        "description": "Generated from Noctalia colors by sync-noctalia-theme.py",
        "theme": {
            "colors": {
                "frame": hex_to_rgb(surface),
                "frame_inactive": hex_to_rgb(shadow),
                "toolbar": hex_to_rgb(surface_variant),
                "tab_text": hex_to_rgb(on_primary),
                "tab_background_text": hex_to_rgb(on_surface_variant),
                "bookmark_text": hex_to_rgb(on_surface),
                "ntp_background": hex_to_rgb(surface),
                "ntp_text": hex_to_rgb(on_surface),
                "button_background": hex_to_rgb(primary),
                "toolbar_button_icon": hex_to_rgb(primary),
                "toolbar_text": hex_to_rgb(on_surface),
                "toolbar_field": hex_to_rgb(surface),
                "toolbar_field_text": hex_to_rgb(on_surface),
                "toolbar_field_border": hex_to_rgb(outline),
                "toolbar_field_focus": hex_to_rgb(surface_variant),
                "toolbar_field_text_focus": hex_to_rgb(on_surface),
                "toolbar_field_border_focus": hex_to_rgb(primary),
            },
            "tints": {
                "buttons": hex_to_rgb(primary),
                "frame": hex_to_rgb(surface),
                "frame_inactive": hex_to_rgb(shadow),
            },
            "properties": {
                "color_scheme": "dark",
            },
        },
        "noctalia": {
            "primary": primary,
            "secondary": secondary,
            "tertiary": tertiary,
            "surface": surface,
        },
    }


def update_brave(colors: dict[str, str]) -> bool:
    BRAVE_THEME_DIR.mkdir(parents=True, exist_ok=True)
    generated = json.dumps(build_brave_theme_manifest(colors), indent=2) + "\n"
    old_manifest = BRAVE_THEME_MANIFEST_PATH.read_text() if BRAVE_THEME_MANIFEST_PATH.exists() else None
    manifest_changed = old_manifest != generated
    if manifest_changed:
        BRAVE_THEME_MANIFEST_PATH.write_text(generated)

    old_flags = BRAVE_FLAGS_PATH.read_text().splitlines(keepends=True) if BRAVE_FLAGS_PATH.exists() else []
    filtered_flags = [line for line in old_flags if not BRAVE_OLD_THEME_FLAG_RE.match(line.strip())]
    has_theme_flag = any(line.strip() == BRAVE_THEME_FLAG for line in filtered_flags)
    if not has_theme_flag:
        if filtered_flags and not filtered_flags[-1].endswith("\n"):
            filtered_flags[-1] += "\n"
        filtered_flags.append(f"{BRAVE_THEME_FLAG}\n")

    updated_flags = "".join(filtered_flags)
    old_flags_text = "".join(old_flags)
    flags_changed = old_flags_text != updated_flags
    if flags_changed:
        BRAVE_FLAGS_PATH.write_text(updated_flags)

    return manifest_changed or flags_changed


def reload_niri() -> None:
    result = subprocess.run(
        ["niri", "msg", "action", "load-config-file"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode != 0:
        print("niri reload skipped/failed:", result.stdout.strip(), file=sys.stderr)


def reload_kitty() -> None:
    result = subprocess.run(
        ["pgrep", "-x", "kitty"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        return

    for raw_pid in result.stdout.splitlines():
        try:
            os.kill(int(raw_pid), signal.SIGUSR1)
        except (ProcessLookupError, PermissionError, ValueError) as exc:
            print(f"kitty reload skipped for pid {raw_pid}: {exc}", file=sys.stderr)


def sync_sddm() -> str:
    if not SDDM_SYNC_SCRIPT.exists():
        return "missing"

    result = subprocess.run(
        [str(SDDM_SYNC_SCRIPT), "--quiet"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode != 0:
        output = result.stdout.strip()
        print(f"sddm theme sync failed: {output}", file=sys.stderr)
        return "failed"
    return "synced"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-reload", action="store_true", help="update files only; do not reload niri or kitty")
    parser.add_argument("--no-kitty", action="store_true", help="skip Kitty config management")
    parser.add_argument("--no-brave", action="store_true", help="skip Brave theme extension generation")
    parser.add_argument("--no-sddm", action="store_true", help="skip SDDM login theme generation")
    args = parser.parse_args()

    colors = json.loads(COLORS_PATH.read_text())
    generated = build_generated_block(colors)
    layout_changed = update_layout(generated)
    kitty_changed = False if args.no_kitty else update_kitty()
    brave_changed = False if args.no_brave else update_brave(colors)
    sddm_status = "skipped" if args.no_sddm else sync_sddm()

    if not args.no_reload:
        reload_niri()
        if not args.no_kitty:
            reload_kitty()

    stamp = datetime.now().isoformat(timespec="seconds")
    kitty_status = "skipped" if args.no_kitty else ("changed" if kitty_changed else "configured")
    brave_status = "skipped" if args.no_brave else ("changed" if brave_changed else "configured")
    print(
        f"[{stamp}] synced colors from {COLORS_PATH} "
        f"(niri {'changed' if layout_changed else 'unchanged'}, kitty {kitty_status}, "
        f"brave {brave_status}, sddm {sddm_status})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
