# Chezmoi desktop notes

This chezmoi repo is the reproducible source for this CachyOS niri + Noctalia desktop.

## What is managed directly

Home-directory config that chezmoi can apply normally, including:

- `~/.config/niri/` — modular niri config, keybinds, outputs, rules, scripts
- `~/.config/noctalia/` — Noctalia settings, colors, and local plugins
- `~/.config/brave-flags.conf` — Brave flags, including PipeWire camera support
- `~/.config/zed/` — Zed settings/themes

## What is managed by a helper script

System-level changes are **not** automatically live-synced by chezmoi. They are documented and re-applied by:

```sh
~/.local/bin/apply-dell-xps-omarchy-hardware-fixes
```

Source file in this repo:

```text
private_dot_local/bin/executable_apply-dell-xps-omarchy-hardware-fixes
```

That script currently handles:

- Apple Studio Display brightness support (`asdbctl`, DDC/i2c/Thunderbolt packages)
- Thunderbolt authorization/enrollment where possible
- IPU7/OV08X40 laptop camera stack from Omarchy packages
- `v4l2-relayd@ipu7` service/drop-in config
- IPU7 module ordering and PSYS availability fixes
- Noctalia brightness patches:
  - external displays must not fall back to laptop `intel_backlight`
  - Apple Studio Display slider parses `asdbctl get` output like `brightness 100`
- Brave PipeWire camera flag
- Intel BE200/BE211 Wi‑Fi 7/EHT workaround:
  - `/etc/modprobe.d/iwlwifi-disable-eht.conf`
  - `options iwlwifi disable_11be=Y`
- `thermald` install and enablement

Extra hardware details live in:

```text
notes/dell-xps-panther-lake-hardware-fixes.md
notes/owc-dock-freeze-fix.md
```

## Applying on this machine

For normal home config:

```sh
chezmoi apply
```

For system-level Dell XPS / Studio Display / camera fixes:

```sh
~/.local/bin/apply-dell-xps-omarchy-hardware-fixes
```

Recommended fresh-machine flow:

```sh
chezmoi init <repo>
chezmoi apply
~/.local/bin/apply-dell-xps-omarchy-hardware-fixes
```

Some changes require a reboot or module reload, especially camera and Wi‑Fi module options.

## After making live changes

Chezmoi does not automatically capture manual edits. After changing the live system, preserve it here.

For home files:

```sh
chezmoi add ~/.config/niri/cfg/display.kdl
chezmoi add ~/.config/niri/cfg/keybinds.kdl
chezmoi add ~/.config/noctalia/settings.json
```

For system-level changes under `/etc`, package installs, kernel modules, or systemd services:

1. Do **not** add `/etc` files directly unless intentionally changing that policy.
2. Update `private_dot_local/bin/executable_apply-dell-xps-omarchy-hardware-fixes` instead.
3. Update the relevant note in `notes/`.

Always review before committing:

```sh
cd "$(chezmoi source-path)"
git status --short
git diff
```

Then commit:

```sh
git add .
git commit -m "Update desktop configuration"
```

## Rule of thumb

If a change should survive reinstalling the laptop, it must be captured in this repo:

- user/home config: `chezmoi add ...`
- system config/services/packages: update the helper script + notes
