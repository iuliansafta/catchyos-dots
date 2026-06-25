# Plymouth docked-boot hang (slow login + boot never completes)

## Symptom

After a reboot **while docked** (Apple Studio Display connected via Thunderbolt),
~20–30s elapsed between entering the password and seeing the niri + Noctalia
desktop. Undocked boots (laptop screen only) were fast.

## Root cause

`plymouth quit` hangs when an external display is attached at boot time (Plymouth
can't cleanly release the multi-display KMS/Thunderbolt state).

- `plymouth-quit.service` → **fails with timeout after 20s**.
- `sddm.service` is ordered `After=plymouth-quit.service`, so the **login screen
  is gated by that 20s timeout**.
- `plymouth-quit-wait.service` (`plymouth --wait`) then **hangs forever**, so
  `multi-user.target` / `graphical.target` are **never reached**. Consequences:
  - `tlp.service` (power management) never starts.
  - `intel-ipu7-camera.service` (camera stack) never starts — this is why the
    hardware-fix script enables the concrete camera units directly.
- The broken display teardown also stalls **Noctalia/quickshell ~28s** (vs ~5s
  on a clean boot).

### Evidence (journal comparison)

| Boot | Displays at boot | `plymouth quit` | niri→Noctalia |
|------|------------------|-----------------|---------------|
| undocked | laptop only | Finished OK | 4.6s |
| docked   | + Studio Display | timed out (20s) | ~28s |

## Fix

Remove the boot splash and the Plymouth initramfs hook entirely:

- `/etc/default/limine`: drop `splash` from `KERNEL_CMDLINE[default]`.
- `/etc/mkinitcpio.conf`: remove `plymouth` from `HOOKS=(...)`
  (`... sd-vconsole sd-encrypt filesystems`).
- Rebuild: `limine-mkinitcpio` (rebuilds all kernels) then `limine-update`.

LUKS unlock now uses the systemd text prompt (`sd-encrypt`) instead of Plymouth's
graphical prompt — same security/speed, just a plain `Enter passphrase` line.

Automated + made idempotent in
`private_dot_local/bin/executable_apply-dell-xps-omarchy-hardware-fixes`
(`disable_plymouth_splash`).

## Verify after reboot

```sh
systemd-analyze            # should now report a finished boot time
systemctl is-active tlp.service graphical.target   # both active
systemctl status plymouth-quit.service             # no longer exists/relevant
# niri start -> Noctalia theme hook gap should be ~5s, not ~28s:
journalctl --user -b -u niri.service -o short-unix | grep -E "starting version|loaded config"
```
