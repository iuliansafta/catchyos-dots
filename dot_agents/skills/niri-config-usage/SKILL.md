---
name: niri-config-usage
description: Configure and maintain this CachyOS niri + Noctalia Wayland desktop. Use proactively for niri config, keybinds, outputs, input, layout, window/layer rules, startup, Noctalia shell integration, quickshell IPC, screenshots, portals, hardware fixes, and debugging. Local config is modular at ~/.config/niri/config.kdl with cfg/*.kdl includes; Noctalia runs via qs -c noctalia-shell and stores settings under ~/.config/noctalia/. Always preserve lasting changes in chezmoi source.
compatibility: CachyOS/Arch Linux, niri 26.04+, Noctalia quickshell via qs/noctalia-qs.
metadata:
  adapted-from: https://github.com/FelipeCabelloE/agent-skills/blob/master/niri-config-usage/SKILL.md
  adapted-for: CachyOS with niri and Noctalia
  local-owner: iulian
---

# niri Configuration & Usage — CachyOS + Noctalia

This skill is adapted from FelipeCabelloE's `niri-config-usage` skill for this machine's current desktop stack:

- OS: CachyOS Linux (`ID=cachyos`, Arch-like rolling system)
- Compositor/session: `niri-session` launching `niri --session`
- niri version observed during setup: `niri 26.04 (8ed0da4)`
- Shell/bar/launcher/OSD/lock/session UI: Noctalia via `qs -c noctalia-shell`
- Config root: `~/.config/niri/config.kdl`
- Noctalia settings: `~/.config/noctalia/settings.json`, colors in `~/.config/noctalia/colors.json`

## Mandatory workflow before editing

1. Inspect the current file(s) first. This system uses modular niri config files; do not assume upstream defaults.
2. Make a timestamped backup before non-trivial edits:
   ```sh
   cp -a ~/.config/niri ~/.config/niri.bak.$(date +%Y%m%d-%H%M%S)
   cp -a ~/.config/noctalia ~/.config/noctalia.bak.$(date +%Y%m%d-%H%M%S)
   ```
3. Edit the smallest relevant file.
4. Validate niri before reload:
   ```sh
   niri validate -c ~/.config/niri/config.kdl
   ```
5. If valid, apply without logging out:
   ```sh
   niri msg action load-config-file
   ```
6. If Noctalia IPC/shell behavior changed, inspect/restart carefully:
   ```sh
   qs list
   qs -c noctalia-shell ipc show
   # Last resort restart:
   qs kill -c noctalia-shell && qs -c noctalia-shell &
   ```
7. Preserve every lasting change in chezmoi before finishing. Home config should be added with `chezmoi add ...`; system-level changes under `/etc`, packages, kernel module options, or systemd services should be represented in the chezmoi helper script and notes instead of unmanaged manual edits.

## Chezmoi persistence rule

This machine uses chezmoi source at:

```sh
chezmoi source-path
# /home/iulian/.local/share/chezmoi
```

Before reporting desktop or hardware work as done, check whether the live change is captured there.

- For home-directory files (`~/.config/niri`, `~/.config/noctalia`, `~/.config/brave-flags.conf`, `~/.config/zed`), run `chezmoi add <path>` or edit the corresponding file under `$(chezmoi source-path)`.
- For system-level changes (`/etc`, package installs, kernel module options, systemd services, Thunderbolt/camera/Wi‑Fi/thermal fixes), update:
  ```text
  $(chezmoi source-path)/private_dot_local/bin/executable_apply-dell-xps-omarchy-hardware-fixes
  ```
  and update notes under:
  ```text
  $(chezmoi source-path)/notes/
  ```
- Do not add raw `/etc` files to chezmoi unless the user explicitly changes that policy; this user prefers reproducible system fixes as a script.
- Review with:
  ```sh
  cd "$(chezmoi source-path)"
  git status --short
  git diff
  ```

The repo README documents what is managed and how to apply it:

```text
$(chezmoi source-path)/README.md
```

## Local config map

`~/.config/niri/config.kdl` is only an include file:

```kdl
include "./cfg/animation.kdl"
include "./cfg/autostart.kdl"
include "./cfg/keybinds.kdl"
include "./cfg/input.kdl"
include "./cfg/display.kdl"
include "./cfg/layout.kdl"
include "./cfg/rules.kdl"
include "./cfg/misc.kdl"
```

Use these files:

| File | Purpose |
| --- | --- |
| `cfg/autostart.kdl` | Startup apps. Currently starts Noctalia with `spawn-sh-at-startup "qs -c noctalia-shell"`. |
| `cfg/keybinds.kdl` | All niri binds and Noctalia IPC keybinds. |
| `cfg/input.kdl` | Keyboard, touchpad, mouse, focus-follows-mouse, workspace auto back/forth. |
| `cfg/display.kdl` | Output names, modes, scale, position. Use `niri msg outputs`. |
| `cfg/layout.kdl` | Gaps, column widths, struts, background. Keep `background-color "transparent"` for Noctalia wallpaper. |
| `cfg/rules.kdl` | Window rules and layer rules, including Noctalia wallpaper layer handling. |
| `cfg/animation.kdl` | Animation timings/springs. |
| `cfg/misc.kdl` | Environment, cursor, debug, hotkey overlay, CSD preference. |

## niri concepts and commands

- Scrollable tiling: windows live in columns; workspaces scroll horizontally.
- Dynamic workspaces: created on demand; referenced by 1-based index or name.
- Floating: local keybind uses `Mod+T` for `toggle-window-floating`.
- Tabbed column mode: local keybind uses `Mod+W`.
- Overview: local keybind uses `Mod+O`.
- Mod key: normally `Super` in a session; `Alt` in windowed dev mode.

Useful IPC:

```sh
niri msg outputs               # outputs and modes
niri msg windows               # windows, app-id/title for rules
niri msg focused-window        # current app-id/title
niri msg layers                # layer-shell surfaces, useful for Noctalia
niri msg workspaces            # workspace state
niri msg action <action-name>  # run any action
niri msg action load-config-file
niri msg version
```

## Noctalia integration on this machine

Noctalia is a quickshell config, not a separate `noctalia` binary here. Use `qs`/`quickshell`:

```sh
qs -c noctalia-shell                 # start Noctalia shell
qs list                              # running quickshell instances
qs -c noctalia-shell ipc show        # available IPC targets/functions
qs -c noctalia-shell ipc call launcher toggle
qs -c noctalia-shell ipc call lockScreen lock
qs -c noctalia-shell ipc call sessionMenu toggle
qs -c noctalia-shell ipc call volume increase
qs -c noctalia-shell ipc call volume decrease
qs -c noctalia-shell ipc call volume muteOutput
qs -c noctalia-shell ipc call volume muteInput
qs -c noctalia-shell ipc call media next
qs -c noctalia-shell ipc call media previous
qs -c noctalia-shell ipc call media playPause
qs -c noctalia-shell ipc call brightness increase
qs -c noctalia-shell ipc call brightness decrease
```

Important local details:

- `cfg/autostart.kdl` starts Noctalia; avoid also starting Waybar/mako/swaync unless the user explicitly wants competing components.
- `cfg/layout.kdl` uses transparent background so Noctalia can set/show the wallpaper.
- `cfg/misc.kdl` includes `honor-xdg-activation-with-invalid-serial` so Noctalia notification actions and activation can work.
- `cfg/keybinds.kdl` routes media, brightness, launcher, lock, and session menu through Noctalia IPC.
- Noctalia settings are JSON. Prefer changing them through Noctalia UI if possible; if editing JSON, validate with `python -m json.tool ~/.config/noctalia/settings.json >/dev/null`.

## Local keybind patterns

Application/Noctalia binds currently include:

```kdl
Mod+Return       { spawn "ghostty"; }
Mod+CTRL+Return  { spawn-sh "qs -c noctalia-shell ipc call launcher toggle"; }
Mod+B            { spawn "firefox"; }
Mod+ALT+L        { spawn-sh "qs -c noctalia-shell ipc call lockScreen lock"; }
Mod+Shift+Q      { spawn-sh "qs -c noctalia-shell ipc call sessionMenu toggle"; }
Mod+E            { spawn "nautilus"; }
```

Navigation follows:

- `Mod+H/J/K/L` and arrows focus left/down/up/right.
- `Mod+Ctrl+H/J/K/L` and arrows move columns/windows.
- `Mod+Shift+Arrow` focuses monitors.
- `Mod+Shift+Ctrl+Arrow` moves columns to monitors.
- `Mod+1..9` focuses workspace by index.
- `Mod+Ctrl+1..9` moves column to workspace.
- `Mod+WheelScroll*` handles workspace/column scrolling.
- `Ctrl+Shift+1/2/3` triggers screenshot UI/screen/window.
- `Mod+Escape` disables an active keyboard shortcut inhibitor.

When adding binds:

```kdl
Mod+X hotkey-overlay-title="Description" { spawn "command"; }
Mod+Shift+X allow-when-locked=true { spawn-sh "shell command"; }
```

Keep Noctalia-related commands as `spawn-sh "qs -c noctalia-shell ipc call ..."`.

## Common edits

### Add a launcher/session/action keybind

Edit `~/.config/niri/cfg/keybinds.kdl` inside `binds { ... }`:

```kdl
Mod+Space hotkey-overlay-title="Open Launcher: Noctalia" { spawn-sh "qs -c noctalia-shell ipc call launcher toggle"; }
```

Then run validation/reload.

### Configure an output

1. Discover names/modes:
   ```sh
   niri msg outputs
   ```
2. Edit `~/.config/niri/cfg/display.kdl`:
   ```kdl
   output "DP-1" {
       mode "2560x1440@359.979"
       scale 1
       position x=0 y=0
   }
   ```
3. Validate/reload.

### Add a floating/window rule

Use `niri msg windows` or `niri msg focused-window` to get `app-id` and `title`, then edit `cfg/rules.kdl`:

```kdl
window-rule {
    match app-id=r#"^firefox$"# title="^Picture-in-Picture$"
    open-floating true
}
```

Multiple `match` lines in one rule are OR'd. Use regex raw strings (`r#"..."#`) for complex titles.

### Keep Noctalia wallpaper/layers working

Do not remove this local pattern from `cfg/rules.kdl` unless replacing Noctalia wallpaper behavior:

```kdl
layer-rule {
    match namespace="^noctalia-wallpaper*"
    place-within-backdrop true
}
```

Keep this in `cfg/layout.kdl`:

```kdl
background-color "transparent"
```

## Local theme-sync helper

This system has a helper that keeps niri focus-ring colors aligned with Noctalia's current theme:

```sh
~/.config/niri/scripts/sync-noctalia-theme.py
```

It reads `~/.config/noctalia/colors.json`, updates the generated color block in `~/.config/niri/cfg/layout.kdl`, validates niri, and reloads niri. Noctalia hooks in `~/.config/noctalia/settings.json` call it for `startup`, `colorGeneration`, `darkModeChange`, and `wallpaperChange`.

Optional alpha overrides for manual runs:

```sh
NIRI_FOCUS_ACTIVE_ALPHA=70 NIRI_FOCUS_INACTIVE_ALPHA=40 ~/.config/niri/scripts/sync-noctalia-theme.py
```

## Troubleshooting checklist

- Config syntax: `niri validate -c ~/.config/niri/config.kdl`
- Reload live config: `niri msg action load-config-file`
- Check niri logs: `journalctl --user -u niri -b --no-pager | tail -200`
- Check Noctalia process: `qs list` and `ps -eo comm,args | grep -Ei 'qs|quickshell|noctalia'`
- Check Noctalia IPC: `qs -c noctalia-shell ipc show`
- Check portals/screencast: `ps -eo comm,args | grep xdg-desktop-portal`
- Running portals observed: `xdg-desktop-portal`, `xdg-desktop-portal-gnome`, `xdg-desktop-portal-gtk`.
- For NVIDIA/black-screen issues, verify kernel modeset and consult niri docs before changing `debug { render-drm-device ... }`.

## Up-to-date references

- niri docs: https://niri-wm.github.io/niri/
- niri wiki source/docs: https://github.com/YaLTeR/niri/tree/main/docs/wiki
- Noctalia docs: https://docs.noctalia.dev/
- Original skill source: https://github.com/FelipeCabelloE/agent-skills/blob/master/niri-config-usage/SKILL.md

For fresh niri syntax, fetch the current docs before making large changes, because this is a rolling CachyOS system and niri evolves quickly.
