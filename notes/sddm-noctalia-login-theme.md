# SDDM Noctalia login theme

This machine uses SDDM with a local wrapper theme named `noctalia-astronaut-theme`.

- Live sync script: `~/.config/sddm/sync-noctalia-theme.py`
- System theme wrapper: `/usr/share/sddm/themes/noctalia-astronaut-theme`
- Generated SDDM config/assets: `/var/cache/noctalia-sddm/`
- SDDM selection: `/etc/sddm.conf` → `[Theme] Current=noctalia-astronaut-theme`
- SDDM virtual keyboard is disabled via `/etc/sddm.conf.d/virtualkbd.conf` and
  `/etc/sddm.conf.d/zz-noctalia-no-virtualkbd.conf` with empty `InputMethod=`.

The wrapper uses a local Omarchy-inspired `Main.qml`: centered larger `•YES•`
text, a larger password-only field, bullet indicators, last-user login, a
strong transparent black wallpaper overlay, and no on-screen virtual keyboard.
It still reads
`Themes/noctalia.conf` and `Backgrounds/noctalia-current.*` from
`/var/cache/noctalia-sddm`, which is owned by the desktop user so Noctalia hooks
can update colors/wallpaper without repeated privilege prompts.

Run or repair with:

```sh
~/.config/sddm/sync-noctalia-theme.py --install
```

Noctalia's existing hook target, `~/.config/niri/scripts/sync-noctalia-theme.py`,
also calls this SDDM sync script unless started with `--no-sddm`.

Do not restart SDDM from inside the graphical session; changes appear at the next
logout/reboot and restarting the display manager can kill the active session.
