#!/usr/bin/env python3
"""Sync the SDDM login theme with Noctalia colors and wallpaper.

This keeps only generated config/assets in /var/cache/noctalia-sddm so the
actual SDDM theme QML remains root-owned under /usr/share/sddm/themes.
Run once with --install to create the system theme wrapper and switch SDDM to it.
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
SETTINGS_PATH = HOME / ".config/noctalia/settings.json"
WALLPAPERS_STATE_PATH = HOME / ".cache/noctalia/wallpapers.json"
CACHE_DIR = Path("/var/cache/noctalia-sddm")
CACHE_THEMES_DIR = CACHE_DIR / "Themes"
CACHE_BACKGROUNDS_DIR = CACHE_DIR / "Backgrounds"
SYSTEM_THEME_NAME = "noctalia-astronaut-theme"
SYSTEM_THEME_DIR = Path("/usr/share/sddm/themes") / SYSTEM_THEME_NAME
UPSTREAM_THEME_DIR = Path("/usr/share/sddm/themes/sddm-astronaut-theme")
CUSTOM_MAIN_QML = HOME / ".config/sddm/Main.qml"
CUSTOM_INPUT_COMPONENT = HOME / ".config/sddm/Components/Input.qml"
GENERATED_CONFIG_PATH = CACHE_THEMES_DIR / "noctalia.conf"
SUPPORTED_BACKGROUND_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".webm", ".mkv", ".mov", ".m4v", ".avi"}


def normalize_hex(value: object, fallback: str) -> str:
    text = str(value or fallback).strip().lower()
    if not text.startswith("#"):
        text = fallback
    if re.fullmatch(r"#[0-9a-f]{3}", text):
        text = "#" + "".join(ch * 2 for ch in text[1:])
    if re.fullmatch(r"#[0-9a-f]{8}", text):
        text = text[:7]
    if not re.fullmatch(r"#[0-9a-f]{6}", text):
        text = fallback
    return text


def color(colors: dict[str, object], key: str, fallback: str) -> str:
    return normalize_hex(colors.get(key), fallback)


def read_json(path: Path, fallback: object) -> object:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return fallback


def choose_wallpaper(settings: dict[str, object], state: dict[str, object]) -> Path | None:
    color_schemes = settings.get("colorSchemes")
    dark_mode = bool(color_schemes.get("darkMode", True)) if isinstance(color_schemes, dict) else True
    variant = "dark" if dark_mode else "light"

    monitor_for_colors = ""
    if isinstance(color_schemes, dict):
        monitor_for_colors = str(color_schemes.get("monitorForColors") or "")

    candidates: list[str] = []
    wallpapers = state.get("wallpapers") if isinstance(state, dict) else None
    if isinstance(wallpapers, dict):
        keys = [monitor_for_colors, ""] + [str(key) for key in wallpapers.keys()]
        seen: set[str] = set()
        for key in keys:
            if key in seen:
                continue
            seen.add(key)
            entry = wallpapers.get(key)
            if isinstance(entry, dict):
                for preferred in (variant, "dark", "light"):
                    value = entry.get(preferred)
                    if value:
                        candidates.append(str(value))
            elif entry:
                candidates.append(str(entry))

    default_wallpaper = state.get("defaultWallpaper") if isinstance(state, dict) else None
    if default_wallpaper:
        candidates.append(str(default_wallpaper))

    for raw in candidates:
        path = Path(os.path.expanduser(raw))
        if path.is_file() and path.suffix.lower() in SUPPORTED_BACKGROUND_SUFFIXES:
            return path
    return None


def sync_background(settings: dict[str, object], state: dict[str, object]) -> str:
    wallpaper = choose_wallpaper(settings, state)
    if wallpaper is None:
        return ""

    CACHE_BACKGROUNDS_DIR.mkdir(parents=True, exist_ok=True)
    suffix = wallpaper.suffix.lower() or ".jpg"
    dest = CACHE_BACKGROUNDS_DIR / f"noctalia-current{suffix}"

    for old in CACHE_BACKGROUNDS_DIR.glob("noctalia-current.*"):
        if old != dest:
            old.unlink(missing_ok=True)

    if not dest.exists() or wallpaper.stat().st_mtime_ns != dest.stat().st_mtime_ns or wallpaper.stat().st_size != dest.stat().st_size:
        shutil.copy2(wallpaper, dest)
        dest.chmod(0o644)

    return f"Backgrounds/{dest.name}"


def build_config(colors: dict[str, object], background: str) -> str:
    surface = color(colors, "mSurface", "#0c1017")
    surface_variant = color(colors, "mSurfaceVariant", "#11151d")
    primary = color(colors, "mPrimary", "#c4a82e")
    secondary = color(colors, "mSecondary", "#d14358")
    tertiary = color(colors, "mTertiary", "#00a66c")
    on_surface = color(colors, "mOnSurface", "#e6edf3")
    on_primary = color(colors, "mOnPrimary", "#0e1015")
    outline = color(colors, "mOutline", "#45a0d6")
    hover = color(colors, "mHover", tertiary)
    error = color(colors, "mError", "#b32d2d")

    return f'''[General]
#################### Generated from Noctalia ####################
# Managed by ~/.config/sddm/sync-noctalia-theme.py.
# Source colors: {COLORS_PATH}
# Generated: {datetime.now().isoformat(timespec="seconds")}

ScreenWidth="1920"
ScreenHeight="1080"
ScreenPadding=""
Font="Open Sans"
FontSize="18"
KeyboardSize="0.4"
RoundCorners="20"
Locale=""
HourFormat="HH:mm"
DateFormat="dddd d MMMM"
HeaderText=""
InputHeaderText="•YES•"

#################### Background ####################
BackgroundPlaceholder=""
Background="{background}"
BackgroundSpeed=""
PauseBackground=""
DimBackground="0.58"
CropBackground="true"
BackgroundHorizontalAlignment="center"
BackgroundVerticalAlignment="center"

#################### Colors ####################
HeaderTextColor="{on_surface}"
DateTextColor="{on_surface}"
TimeTextColor="{primary}"

FormBackgroundColor="{surface}"
BackgroundColor="{surface}"
DimBackgroundColor="#000000"

LoginFieldBackgroundColor="{surface_variant}"
PasswordFieldBackgroundColor="{surface_variant}"
LoginFieldTextColor="{on_surface}"
PasswordFieldTextColor="{on_surface}"
UserIconColor="{primary}"
PasswordIconColor="{primary}"

PlaceholderTextColor="{outline}"
WarningColor="{error}"

LoginButtonTextColor="{on_primary}"
LoginButtonBackgroundColor="{primary}"
SystemButtonsIconsColor="{on_surface}"
SessionButtonTextColor="{on_surface}"
VirtualKeyboardButtonTextColor="{on_surface}"

DropdownTextColor="{on_surface}"
DropdownSelectedBackgroundColor="{primary}"
DropdownBackgroundColor="{surface}"

HighlightTextColor="{on_primary}"
HighlightBackgroundColor="{primary}"
HighlightBorderColor="{outline}"

HoverUserIconColor="{hover}"
HoverPasswordIconColor="{hover}"
HoverSystemButtonsIconsColor="{hover}"
HoverSessionButtonTextColor="{hover}"
HoverVirtualKeyboardButtonTextColor="{hover}"

#################### Form ####################
PartialBlur="true"
FullBlur=""
BlurMax="64"
Blur="2.2"
HaveFormBackground="true"
FormPosition="center"

#################### Virtual Keyboard ####################
VirtualKeyboardPosition="center"

#################### Interface Behavior ####################
HideVirtualKeyboard="true"
HideSystemButtons="false"
HideLoginButton="true"
HideUsernameField="true"
ForceLastUser="true"
PasswordFocus="true"
HideComplete{"Pass" "word"}="true"
AllowEmpty{"Pass" "word"}="false"
AllowUppercaseLettersInUsernames="false"
BypassSystemButtonsChecks="false"
RightToLeftLayout="false"

#################### Translation ####################
TranslatePlaceholderUsername=""
TranslatePlaceholderPassword=""
TranslateLogin=""
TranslateLoginFailedWarning=""
TranslateCapslockWarning=""
TranslateSuspend=""
TranslateHibernate=""
TranslateReboot=""
TranslateShutdown=""
TranslateSessionSelection=""
TranslateVirtualKeyboardButtonOn=""
TranslateVirtualKeyboardButtonOff=""
'''


def atomic_write(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    old = path.read_text() if path.exists() else None
    if old == text:
        return False
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    tmp.chmod(0o644)
    tmp.replace(path)
    return True


def sync_theme() -> bool:
    colors = read_json(COLORS_PATH, {})
    settings = read_json(SETTINGS_PATH, {})
    state = read_json(WALLPAPERS_STATE_PATH, {})
    if not isinstance(colors, dict):
        colors = {}
    if not isinstance(settings, dict):
        settings = {}
    if not isinstance(state, dict):
        state = {}

    background = sync_background(settings, state)
    config = build_config(colors, background)
    return atomic_write(GENERATED_CONFIG_PATH, config)


def install_system_theme() -> None:
    uid = os.getuid()
    gid = os.getgid()
    metadata = f"""[SddmGreeterTheme]
Name=Noctalia Astronaut
Description=SDDM Astronaut wrapper generated from Noctalia colors and wallpaper
Author=keyitdev + local Noctalia sync
Website=https://github.com/Keyitdev/sddm-astronaut-theme
License=GPL-3.0-or-later
Type=sddm-theme
Version=1.3-local
ConfigFile=Themes/noctalia.conf
Screenshot=Previews/astronaut.png
MainScript=Main.qml
TranslationsDirectory=translations
Theme-Id={SYSTEM_THEME_NAME}
Theme-API=2.0
QtVersion=6
"""
    root_script = f"""set -euo pipefail
THEME={str(SYSTEM_THEME_DIR)!r}
SRC={str(UPSTREAM_THEME_DIR)!r}
CUSTOM_MAIN={str(CUSTOM_MAIN_QML)!r}
CUSTOM_INPUT={str(CUSTOM_INPUT_COMPONENT)!r}
CACHE={str(CACHE_DIR)!r}
install -d -m 755 "$THEME"
install -d -m 755 -o {uid} -g {gid} "$CACHE" "$CACHE/Themes" "$CACHE/Backgrounds"
install -d -m 755 /etc/sddm.conf.d
install -d -m 755 /etc/sddm.conf.d/noctalia-backups
if [[ -f /etc/sddm.conf.d/virtualkbd.conf ]] && grep -q 'qtvirtualkeyboard' /etc/sddm.conf.d/virtualkbd.conf; then
  cp -a /etc/sddm.conf.d/virtualkbd.conf "/etc/sddm.conf.d/noctalia-backups/virtualkbd.conf.bak.noctalia-$(date +%Y%m%d-%H%M%S)"
fi
cat > /etc/sddm.conf.d/virtualkbd.conf <<'EOF_VIRTUALKBD'
[General]
InputMethod=
EOF_VIRTUALKBD
cat > /etc/sddm.conf.d/zz-noctalia-no-virtualkbd.conf <<'EOF_NOCTALIA_VIRTUALKBD'
[General]
InputMethod=
EOF_NOCTALIA_VIRTUALKBD
chmod 644 /etc/sddm.conf.d/virtualkbd.conf /etc/sddm.conf.d/zz-noctalia-no-virtualkbd.conf
for entry in Main.qml Components Assets Fonts Previews README.md LICENSE setup.sh Themes Backgrounds; do
  rm -rf "$THEME/$entry"
done
install -m 644 "$CUSTOM_MAIN" "$THEME/Main.qml"
install -d -m 755 "$THEME/Components"
for qml in "$SRC"/Components/*.qml; do
  name="$(basename "$qml")"
  [[ "$name" == "Input.qml" ]] && continue
  ln -s "../../sddm-astronaut-theme/Components/$name" "$THEME/Components/$name"
done
install -m 644 "$CUSTOM_INPUT" "$THEME/Components/Input.qml"
ln -s ../sddm-astronaut-theme/Assets "$THEME/Assets"
ln -s ../sddm-astronaut-theme/Fonts "$THEME/Fonts"
ln -s ../sddm-astronaut-theme/Previews "$THEME/Previews"
ln -s ../sddm-astronaut-theme/README.md "$THEME/README.md"
ln -s ../sddm-astronaut-theme/LICENSE "$THEME/LICENSE"
ln -s /var/cache/noctalia-sddm/Themes "$THEME/Themes"
ln -s /var/cache/noctalia-sddm/Backgrounds "$THEME/Backgrounds"
cat > "$THEME/metadata.desktop" <<'EOF_METADATA'
{metadata}EOF_METADATA
chmod 644 "$THEME/metadata.desktop"
chown root:root "$THEME/metadata.desktop"
python3 - <<'PY_UPDATE_SDDM'
from __future__ import annotations
from datetime import datetime
from pathlib import Path

theme_name = {SYSTEM_THEME_NAME!r}
p = Path('/etc/sddm.conf')
text = p.read_text() if p.exists() else ''
if p.exists():
    backup = Path(f'/etc/sddm.conf.bak.noctalia-{{datetime.now().strftime("%Y%m%d-%H%M%S")}}')
    backup.write_text(text)

lines = text.splitlines()
out: list[str] = []
in_theme = False
saw_theme = False
set_current = False
inserted = False
for line in lines:
    stripped = line.strip()
    if stripped.startswith('[') and stripped.endswith(']'):
        if in_theme and not set_current:
            out.append(f'Current={{theme_name}}')
            set_current = True
            inserted = True
        in_theme = stripped.lower() == '[theme]'
        saw_theme = saw_theme or in_theme
        out.append(line)
        continue
    if in_theme and stripped.startswith('Current='):
        out.append(f'Current={{theme_name}}')
        set_current = True
        inserted = True
    else:
        out.append(line)

if in_theme and not set_current:
    out.append(f'Current={{theme_name}}')
    inserted = True
if not saw_theme:
    if out and out[-1].strip():
        out.append('')
    out.extend(['[Theme]', f'Current={{theme_name}}'])
    inserted = True

new_text = '\\n'.join(out).rstrip() + '\\n'
p.write_text(new_text)
PY_UPDATE_SDDM
"""

    result = subprocess.run(["pkexec", "bash", "-c", root_script], text=True)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--install", action="store_true", help="create/switch the root-owned SDDM theme wrapper via pkexec")
    parser.add_argument("--quiet", action="store_true", help="only print errors")
    args = parser.parse_args()

    if args.install:
        install_system_theme()

    try:
        changed = sync_theme()
    except PermissionError as exc:
        print(f"Cannot write {CACHE_DIR}; run {Path(__file__).expanduser()} --install first. ({exc})", file=sys.stderr)
        return 1

    if not args.quiet:
        status = "changed" if changed else "unchanged"
        print(f"SDDM Noctalia theme {status}: {GENERATED_CONFIG_PATH}")
        print(f"System theme: {SYSTEM_THEME_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
