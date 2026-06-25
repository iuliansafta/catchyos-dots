# Dell XPS Panther Lake hardware fixes

This machine needs a few non-standard fixes for the current Linux desktop stack:

- Apple Studio Display brightness through the OWC Thunderbolt dock:
  - `asdbctl`
  - `bolt` enrollment/authorization
  - `i2c-dev` module loaded at boot
- Built-in Dell XPS IPU7 / OV08X40 camera:
  - Omarchy `intel-ipu7-camera` package
  - Omarchy `v4l2-relayd` package
  - `intel_cvs`, `intel_ipu7_psys`, `ov08x40`, `v4l2loopback`
  - camera exposed to browsers as `/dev/video50` / `Hardware ISP Camera`
  - **kernel >= 7.1 psys fix** (see below): DKMS `ipu7-drivers` 1.0.3 psys
    module patched to `bus_register()` its own `intel-ipu7-psys` bus

## Kernel >= 7.1 PSYS regression (camera "stuck"/black)

Symptom: camera frozen/black; `v4l2-relayd@ipu7` running but its `icamerasrc`
HAL logs `PSysDevice: Failed to open psys device No such file or directory`
and `failed to config streams`. Kernel log shows:

```text
bus_add_device: cannot add device 'ipu7-psys0' to unregistered bus 'intel-ipu7-psys'
intel-ipu7-psys ipu7-psys0: psys device_register failed
intel_ipu7_psys.psys: probe ... failed with error -22
```

Root cause: CachyOS kernel 7.1+ stopped shipping an in-tree IPU7 **psys**
module (only `intel-ipu7` + `intel-ipu7-isys` in-tree, plus IPU6). The
out-of-tree DKMS `ipu7-drivers` 1.0.3 source registers its psys char device
on a custom `intel-ipu7-psys` `bus_type` but never calls `bus_register()` for
it — it relied on the in-tree driver to register the bus. With no in-tree
psys, `device_register()` fails, `/dev/ipu7-psys0` is never created, and the
hardware-ISP pipeline can't start.

Fix (applied automatically by the hardware-fixes script,
`patch_ipu7_psys_bus_register`): patch
`/usr/src/ipu7-drivers-1.0.3/.../psys/ipu-psys.c` to replace
`module_auxiliary_driver(ipu7_psys_driver)` with explicit `module_init`/
`module_exit` that `bus_register(&ipu7_psys_bus)` before
`auxiliary_driver_register()` (and unregister on exit), then
`dkms autoinstall`. Idempotent; re-applied after `intel-ipu7-camera`
reinstalls or kernel updates. Verify `/dev/ipu7-psys0` exists and
`dmesg | grep psys` shows `IPU psys probe done.`

- Noctalia brightness patches:
  - external displays without DDC/asdbctl must not fall back to the laptop `intel_backlight`
  - `asdbctl get` output like `brightness 100` is parsed correctly for Apple display sliders
  - Apple display brightness is re-initialized after async detection
- Browser camera flag:
  - `--enable-features=PipeWireCamera`
- Omarchy Wi-Fi 7/EHT workaround for Intel BE200/BE211 on Dell XPS Panther Lake:
  - `/etc/modprobe.d/iwlwifi-disable-eht.conf`
  - `options iwlwifi disable_11be=Y`
  - falls back to Wi‑Fi 6/HE until Intel fixes the EHT RX path
- Panther Lake FRED:
  - `fred=on` added to the Limine kernel command line
  - takes effect after reboot; verify with `cat /proc/cmdline`
- Intel thermal management:
  - `thermald` enabled/running

Apply/re-apply with:

```bash
~/.local/bin/apply-dell-xps-omarchy-hardware-fixes
```

After applying, reboot once if browser camera lists do not refresh. In browser camera settings choose:

```text
Hardware ISP Camera
```

Quick checks:

```bash
asdbctl get
boltctl
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video50 --stream-mmap --stream-count=5
systemctl status v4l2-relayd@ipu7.service
systemctl status thermald
cat /etc/modprobe.d/iwlwifi-disable-eht.conf
cat /proc/cmdline | grep -o 'fred=on'
```

The Wi‑Fi 7/EHT workaround affects `iwlwifi` module load, so reboot or reload Wi‑Fi for it to take full effect.
