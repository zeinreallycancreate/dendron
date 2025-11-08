# Troubleshooting Guide

This guide covers common issues you might encounter during setup and operation.

## Installation Issues

### Script Not Found Error

**Problem:**
```bash
goober@goober:~/dendron/scripts$ sudo ./scripts/setup_server.sh
sudo-rs: './scripts/setup_server.sh': command not found
```

**Cause:** You're already in the `scripts/` directory, so `./scripts/` tries to look for another `scripts` subdirectory that doesn't exist.

**Solution:** When you're in the `scripts/` directory, just use `./` to run scripts:
```bash
cd ~/dendron/scripts
sudo ./setup_ubuntu.sh        # ✅ Correct
sudo ./setup_server.sh        # ✅ Correct
sudo ./start_server_and_node.sh ../configs/node1_config.yml  # ✅ Correct
```

**Alternative:** Run from the project root:
```bash
cd ~/dendron
sudo ./scripts/setup_ubuntu.sh    # ✅ Also correct
sudo ./scripts/setup_server.sh    # ✅ Also correct
```

### Permission Denied

**Problem:**
```bash
bash: ./setup_server.sh: Permission denied
```

**Solution:** Make the script executable first:
```bash
chmod +x setup_server.sh
chmod +x setup_ubuntu.sh
chmod +x start_*.sh
```

Or make all scripts executable at once:
```bash
cd ~/dendron/scripts
chmod +x *.sh
```

### sudo-rs vs sudo

Ubuntu 25.10 uses `sudo-rs` (a Rust-based sudo) by default. Both work the same way with these scripts. If you encounter issues with `sudo-rs`, the traditional `sudo` should also be available.

### Python/Pip Issues

**Problem:**
```
E: Unable to locate package python3-pip
```

**Solution:** Update package lists first:
```bash
sudo apt update
sudo apt upgrade -y
```

Then retry the installation.

## WiFi Scanning Issues

### Monitor Mode Not Working

**Problem:** WiFi adapter won't enter monitor mode.

**Solution 1:** Check if your WiFi is managed by NetworkManager:
```bash
sudo rfkill unblock wifi
sudo iw dev wlan0 set type monitor
```

**Solution 2:** Temporarily disable NetworkManager:
```bash
sudo systemctl stop NetworkManager
sudo iw dev wlan0 set type monitor
# When done, restart:
sudo systemctl start NetworkManager
```

**Solution 3:** The scanner automatically falls back to managed mode scanning if monitor mode fails. This is less powerful but still works.

### No WiFi Devices Detected

**Problem:** Scanner runs but doesn't detect any devices.

**Checks:**
1. Make sure WiFi is enabled:
   ```bash
   rfkill list
   # Should show WiFi as "unblocked"
   ```

2. Check if you can see networks manually:
   ```bash
   sudo iw dev wlan0 scan | grep SSID
   ```

3. Verify the scanner is running:
   ```bash
   ps aux | grep scanner
   ```

### wireless-tools Not Available

**Problem:**
```
E: Package 'wireless-tools' has no installation candidate
```

**Solution:** This is expected on Ubuntu 25.10+. The system has been updated to use modern `iw` commands instead. The setup scripts no longer try to install `wireless-tools`. If you have old scripts, make sure you're using the latest version:
```bash
cd ~/dendron
git pull
```

## Bluetooth Issues

### Bluetooth Not Working

**Problem:** Scanner doesn't detect Bluetooth devices.

**Solution 1:** Enable Bluetooth:
```bash
sudo systemctl start bluetooth
sudo systemctl enable bluetooth
```

**Solution 2:** Check Bluetooth status:
```bash
sudo hciconfig hci0 up
hcitool scan
```

**Solution 3:** Install bluepy dependencies:
```bash
sudo apt install -y bluetooth bluez bluez-tools python3-bluez
```

## Server Issues

### Port 5000 Already in Use

**Problem:**
```
OSError: [Errno 98] Address already in use
```

**Solution 1:** Kill the existing process:
```bash
sudo lsof -i :5000
sudo kill -9 <PID>
```

**Solution 2:** Use a different port by editing `server/app.py`:
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)  # Changed from 5000
```

Then update all node configs to use the new port.

### Can't Access Web Dashboard

**Problem:** Browser shows "Can't reach this page" at `http://SERVER_IP:5000`

**Checks:**
1. Server is running:
   ```bash
   ps aux | grep "python.*server"
   ```

2. Firewall allows port 5000:
   ```bash
   sudo ufw allow 5000
   ```

3. Server is bound to 0.0.0.0 (not just localhost):
   ```bash
   sudo netstat -tuln | grep 5000
   # Should show: 0.0.0.0:5000 (not 127.0.0.1:5000)
   ```

4. Use correct IP:
   ```bash
   hostname -I  # Get your actual IP
   ```

## Client Connection Issues

### Client Can't Connect to Server

**Problem:** Scanner logs show connection errors.

**Checks:**
1. Ping the server:
   ```bash
   ping SERVER_IP
   ```

2. Test server connectivity:
   ```bash
   curl http://SERVER_IP:5000/api/nodes
   ```

3. Check config file:
   ```bash
   cat ~/dendron/configs/node1_config.yml
   # Verify server_url is correct
   ```

4. Verify server is accepting connections:
   ```bash
   # On server:
   sudo netstat -tuln | grep 5000
   ```

### Wrong Server IP in Config

**Problem:** You configured the wrong IP and need to change it.

**Solution:** Re-run the setup:
```bash
cd ~/dendron/scripts
sudo ./setup_ubuntu.sh
# Choose your node number
# Enter correct server IP
```

Or manually edit:
```bash
nano ~/dendron/configs/node1_config.yml
# Change server_url line
```

## Dual-Role Setup Issues

### Server and Client Conflict

**Problem:** Running both server and client on same Pi causes issues.

**Solution:** Make sure config uses localhost:
```bash
nano ~/dendron/configs/node1_config.yml
```
Set:
```yaml
server_url: "http://localhost:5000"
```

### Script Won't Start Both

**Problem:** `start_server_and_node.sh` fails.

**Check:** Script path is correct:
```bash
cd ~/dendron/scripts
sudo ./start_server_and_node.sh ../configs/node1_config.yml
```

**Alternative:** Start manually:
```bash
# Terminal 1:
cd ~/dendron/scripts
./start_server.sh

# Terminal 2:
cd ~/dendron/scripts
sudo ./start_node1.sh
```

## Performance Issues

### High CPU Usage

**Problem:** Scanner uses too much CPU.

**Solution:** Increase scan interval in config:
```yaml
scan_interval: 10  # Changed from 5 seconds
```

### High Memory Usage

**Problem:** System runs out of memory.

**Checks:**
1. Close unnecessary applications
2. Reduce concurrent device tracking in server
3. Clear old scan data:
   ```bash
   rm ~/dendron/scanner.db
   # Restart server
   ```

## Permission Issues

### Can't Run as Root

**Problem:** Script requires sudo but complains about root.

**Solution:** Run with `sudo` but keep user environment:
```bash
sudo -E ./start_node1.sh
```

### File Permission Errors

**Problem:**
```
PermissionError: [Errno 13] Permission denied: 'scanner.db'
```

**Solution:** Fix file ownership:
```bash
cd ~/dendron
sudo chown -R $USER:$USER .
chmod -R 755 .
```

## Database Issues

### Corrupt Database

**Problem:** Server won't start due to database errors.

**Solution:** Delete and recreate:
```bash
cd ~/dendron
rm scanner.db
# Restart server - will auto-create new database
```

## Node Position Issues

### Devices Show in Wrong Location

**Problem:** The triangulation shows devices in incorrect positions.

**Checks:**
1. Verify node positions are correct in configs
2. Check nodes are properly distributed (not in a line)
3. Verify all nodes are connected and sending data:
   ```bash
   # On server, check:
   curl http://localhost:5000/api/nodes
   ```

### Triangulation Not Working

**Problem:** System only shows approximate areas, not precise locations.

**Causes:**
- Only 1 or 2 nodes active (need 3+ for triangulation)
- Nodes arranged in a straight line (need triangle)
- Poor signal quality

**Solution:**
1. Check node geometry:
   ```bash
   curl http://SERVER_IP:5000/api/geometry
   ```
2. Ensure 3+ nodes are active
3. Rearrange nodes into better triangle

## Logging and Debugging

### Enable Debug Logging

Add to start of scanner or server scripts:
```bash
export DEBUG=1
```

### View Live Logs

**Scanner:**
```bash
tail -f ~/dendron/scanner.log
```

**Server:**
```bash
tail -f ~/dendron/server.log
```

### Check System Resources

```bash
# CPU and memory:
htop

# Disk space:
df -h

# Network:
ifconfig
```

## Getting More Help

If you're still stuck:

1. **Check the documentation:**
   - `README.md` - Overview
   - `SETUP.md` - Detailed setup
   - `QUICKSTART.md` - Fast setup
   - `DEPLOYMENT.md` - Production deployment

2. **Verify your setup:**
   ```bash
   # System info:
   uname -a
   
   # Python version:
   python3 --version
   
   # Network info:
   ip addr
   
   # Installed packages:
   pip3 list
   ```

3. **Common fixes that solve 80% of issues:**
   - Reboot the Raspberry Pi
   - Update the system: `sudo apt update && sudo apt upgrade`
   - Re-clone the repo to get latest fixes
   - Check file permissions
   - Verify network connectivity

4. **Create a GitHub issue** with:
   - Your Ubuntu version: `lsb_release -a`
   - Your Raspberry Pi model
   - Complete error messages
   - What you've already tried
