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
- Noctalia brightness patch:
  - external displays without DDC/asdbctl must not fall back to the laptop `intel_backlight`
- Browser camera flag:
  - `--enable-features=PipeWireCamera`

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
```
