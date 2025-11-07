# Migration from wireless-tools to iw

## Overview

Ubuntu 25.10 and newer versions no longer include the deprecated `wireless-tools` package (which provided `iwconfig`, `iwlist`, etc.). This system has been updated to use the modern `iw` command instead.

## What Changed

### Removed Package
- ❌ `wireless-tools` - No longer available in Ubuntu 25.10

### Modern Replacement
- ✅ `iw` - Modern wireless configuration tool
- ✅ `rfkill` - Radio kill switch control

## Command Equivalents

If you're familiar with the old commands, here are the modern equivalents:

### Check WiFi Interface
**Old:**
```bash
iwconfig
```

**New:**
```bash
iw dev
# Or for more details:
iw dev wlan0 info
```

### Scan for Networks
**Old:**
```bash
sudo iwlist wlan0 scan
```

**New:**
```bash
sudo iw dev wlan0 scan
# Or with formatted output:
sudo iw dev wlan0 scan | grep -E "BSS|SSID|signal"
```

### Set Monitor Mode
**Old:**
```bash
sudo ifconfig wlan0 down
sudo iwconfig wlan0 mode monitor
sudo ifconfig wlan0 up
```

**New:**
```bash
sudo ip link set wlan0 down
sudo iw wlan0 set type monitor
sudo ip link set wlan0 up
```

### Check Monitor Mode Status
**Old:**
```bash
iwconfig wlan0 | grep Mode
```

**New:**
```bash
iw dev wlan0 info | grep type
```

## Code Changes

### scanner.py Updates

The scanner client (`client/scanner.py`) has been updated to:

1. **Monitor Mode Setup** - Now uses `iw` commands instead of `iwconfig`
2. **Fallback Scanning** - Uses `iw dev wlan0 scan` instead of `iwlist wlan0 scan`
3. **Better Parsing** - Updated to parse `iw` output format (BSS lines instead of Cell/Address lines)

### Key Differences in Output Parsing

**Old iwlist output:**
```
Cell 01 - Address: AA:BB:CC:DD:EE:FF
          Signal level=-45 dBm
```

**New iw output:**
```
BSS aa:bb:cc:dd:ee:ff(on wlan0)
        signal: -45.00 dBm
```

## Installation

The setup script (`scripts/setup_ubuntu.sh`) now installs:

```bash
sudo apt install -y aircrack-ng iw net-tools rfkill \
    wpasupplicant network-manager
```

No action needed - the deprecated `wireless-tools` line has been removed.

## Troubleshooting

### "command not found: iwconfig"
✅ **This is expected!** The system now uses `iw` instead.

Use these alternatives:
- Instead of `iwconfig` → use `iw dev`
- Instead of `iwlist wlan0 scan` → use `iw dev wlan0 scan`

### Monitor Mode Not Working?
If you get permission errors or monitor mode fails:

```bash
# Check if rfkill is blocking:
sudo rfkill list
sudo rfkill unblock wifi

# Try manual setup:
sudo ip link set wlan0 down
sudo iw wlan0 set type monitor
sudo ip link set wlan0 up

# Verify:
iw dev wlan0 info
```

### Need to Use Old Tools?
If you absolutely need the old tools for debugging, you can try installing from source or using older Ubuntu versions. However, this is **not recommended** as they're deprecated.

## Benefits of Modern iw

1. **Active Development** - `iw` is actively maintained
2. **Better nl80211 Support** - Direct kernel interface
3. **More Features** - Supports newer WiFi standards
4. **Future Proof** - Won't be removed in future Ubuntu releases
5. **Cleaner Output** - Easier to parse programmatically

## References

- [iw Documentation](https://wireless.wiki.kernel.org/en/users/documentation/iw)
- [Ubuntu Network Configuration](https://ubuntu.com/server/docs/network-configuration)
- [nl80211 Interface](https://wireless.wiki.kernel.org/en/developers/documentation/nl80211)

---

**Note:** All documentation and scripts in this project have been updated to use `iw` commands. If you find any references to `iwconfig` or `iwlist`, please report them as they should be updated.
