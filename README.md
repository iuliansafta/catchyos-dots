# Chezmoi desktop notes

This chezmoi repo is the reproducible source for this CachyOS niri + Noctalia desktop.

## What is managed directly

Home-directory config that chezmoi can apply normally, including:

- `~/.config/niri/` — modular niri config, keybinds, outputs, rules, scripts
- `~/.local/bin/setup-coding-tools` — development bootstrap for Rust, Go, Python, Docker, lazygit/lazydocker, Terraform, Ansible, and AI coding tools
- `~/.local/bin/update-ai-coding-tools` — wrapper to update only Claude Code, Pi, and OpenCode
- `~/.local/bin/niri-capture-screenshot` — Satty/grim/slurp screenshot workflow used by niri keybinds
- Nautilus Space preview support via `sushi` (`org.gnome.NautilusPreviewer`) and floating niri rules
- `~/.config/noctalia/` — Noctalia settings, colors, and local plugins
- `~/.config/brave-flags.conf` — Brave flags, including PipeWire camera support
- `~/.config/zed/` — Zed settings/themes

## What is managed by a helper script

System-level changes are **not** automatically live-synced by chezmoi. They are documented and re-applied by helper scripts.

Desktop extras:

```sh
~/.local/bin/apply-cachyos-desktop-extras
```

Source file in this repo:

```text
private_dot_local/bin/executable_apply-cachyos-desktop-extras
```

That script currently installs screenshot, preview, and desktop app dependencies:

- `grim`
- `slurp`
- `satty`
- `imv`
- `jq`
- `libnotify`
- `sushi` — Nautilus Space preview, like macOS Quick Look
- `wl-clipboard`
- `flatpak`
- `obs-studio`
- `xdg-desktop-portal`, `xdg-desktop-portal-gnome`, `xdg-desktop-portal-gtk` for Wayland/PipeWire screen recording on niri

It also configures Flathub for the user, installs user Flatpak apps, makes their `.desktop` files visible to launchers, and sets image MIME defaults:

- Pinta: `com.github.PintaProject.Pinta`
- Obsidian: `md.obsidian.Obsidian`
- Spotify: `com.spotify.Client`
- Pinta is the default app for common image types (`png`, `jpeg`, `webp`, `bmp`, `tiff`, `gif`, `svg`, OpenRaster)

Flatpak desktop launchers are symlinked into `~/.local/share/applications` because this session's `XDG_DATA_DIRS` may not include the user Flatpak export path.

Dell XPS / Studio Display / camera fixes:

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

For development tooling:

```sh
~/.local/bin/setup-coding-tools
```

Useful options:

```sh
~/.local/bin/setup-coding-tools --no-upgrade
~/.local/bin/setup-coding-tools --skip-ai
~/.local/bin/update-ai-coding-tools
```

The dev tools script installs/enables Docker and adds the user to the `docker` group. Log out and back in before running Docker without `sudo`.

For desktop package extras, including screenshot dependencies:

```sh
~/.local/bin/apply-cachyos-desktop-extras
```

For system-level Dell XPS / Studio Display / camera fixes:

```sh
~/.local/bin/apply-dell-xps-omarchy-hardware-fixes
```

Recommended fresh-machine flow:

```sh
chezmoi init <repo>
chezmoi apply
~/.local/bin/setup-coding-tools
~/.local/bin/apply-cachyos-desktop-extras
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
2. Update the relevant helper script instead:
   - desktop package/tooling extras: `private_dot_local/bin/executable_apply-cachyos-desktop-extras`
   - Dell XPS / hardware fixes: `private_dot_local/bin/executable_apply-dell-xps-omarchy-hardware-fixes`
3. Update the relevant note in `notes/` when useful.

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
