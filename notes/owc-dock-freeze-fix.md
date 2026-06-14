# OWC Thunderbolt Dock / Apple Studio Display unplug freeze fix

Symptoms:
- Laptop froze when unplugging OWC Thunderbolt Dock with Apple Studio Display.
- Kernel logs showed xHCI / PCI hotplug problems and then UCSI/typec cleanup crash:
  - `xhci_hcd ... Controller not ready at resume -19`
  - `xhci_hcd ... PCI post-resume error -19`
  - `kernfs: can not remove 'typec', no directory`
  - `typec_unregister_partner`
  - `ucsi_unregister_partner`
  - `BUG: kernel NULL pointer dereference`

Working kernel parameters:

```text
pci=hpbussize=0x33,hpmemsize=256M usbcore.quirks=0bda:8153:bjkm module_blacklist=ucsi_acpi
```

Apply script:

```bash
~/.local/bin/apply-dock-kernel-workarounds
```

Manual apply on CachyOS with Limine:

```bash
sudo cp /etc/default/limine /etc/default/limine.bak.$(date +%F-%H%M%S)

grep -q 'pci=hpbussize=0x33,hpmemsize=256M' /etc/default/limine || \
  sudo sed -i '/^KERNEL_CMDLINE\[default\]+="/ s/"$/ pci=hpbussize=0x33,hpmemsize=256M"/' /etc/default/limine

grep -q 'usbcore.quirks=0bda:8153:bjkm' /etc/default/limine || \
  sudo sed -i '/^KERNEL_CMDLINE\[default\]+="/ s/"$/ usbcore.quirks=0bda:8153:bjkm"/' /etc/default/limine

grep -q 'module_blacklist=ucsi_acpi' /etc/default/limine || \
  sudo sed -i '/^KERNEL_CMDLINE\[default\]+="/ s/"$/ module_blacklist=ucsi_acpi"/' /etc/default/limine

sudo limine-update
sudo reboot
```

Verify after reboot:

```bash
cat /proc/cmdline
lsmod | grep ucsi || echo 'ucsi disabled'
```

Expected:
- `/proc/cmdline` contains all three parameters.
- `lsmod | grep ucsi` returns nothing.

If needed, revert by removing `module_blacklist=ucsi_acpi` from `/etc/default/limine`, then run `sudo limine-update` and reboot.
