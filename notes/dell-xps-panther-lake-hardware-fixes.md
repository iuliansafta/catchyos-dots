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
```

The Wi‑Fi 7/EHT workaround affects `iwlwifi` module load, so reboot or reload Wi‑Fi for it to take full effect.
