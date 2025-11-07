# Running Server + Client on Same Raspberry Pi

## Overview

You can run both the server and a scanner client on the same Raspberry Pi. This is useful when:
- You want one Pi to act as both the coordinator and a scanning node
- You have limited hardware and want to maximize efficiency
- You need the server close to the scanning area

## Architecture

```
┌─────────────────────────────────────┐
│     Raspberry Pi (Server + Node)    │
│                                     │
│  ┌─────────────┐  ┌──────────────┐ │
│  │   Server    │  │   Scanner    │ │
│  │  (Port 5000)│  │   Client     │ │
│  │  Web UI     │  │  WiFi/BT     │ │
│  │  AI Engine  │◄─┤  Scanning    │ │
│  └─────────────┘  └──────────────┘ │
│         ▲                           │
└─────────┼───────────────────────────┘
          │
          │ Network
          │
    ┌─────┴─────┐
    │           │
 [Node 2]   [Node 3]
  (Pi 2)     (Pi 3)
```

## Installation

### Step 1: Initial Setup

On your Raspberry Pi that will run both roles:

```bash
git clone https://github.com/zeinreallycancreate/dendron.git
cd dendron/scripts

# Install all dependencies (server + client)
sudo ./setup_ubuntu.sh
sudo ./setup_server.sh
```

### Step 2: Configure This Node

Edit the node configuration to point to localhost:

```bash
cd ..
nano configs/node1_config.yml
```

Update the server URL to use `localhost` since the server is on the same Pi:

```yaml
node_id: "node_1"
server_url: "http://localhost:5000"  # Server on same Pi

# Set the physical position of this Pi
position:
  x: 0
  y: 0
  z: 1.5
  
# Other settings
wifi_interface: "wlan0"
bluetooth_adapter: "hci0"
scan_interval: 5
anonymize_mac: false
```

### Step 3: Start Both Services

Use the combined startup script:

```bash
cd scripts
sudo ./start_server_and_node.sh ../configs/node1_config.yml
```

This will:
1. Start the server in the background
2. Start the scanner client in the foreground
3. Handle both processes together

**Output you'll see:**
```
==========================================
Starting Server + Scanner Node on Same Pi
==========================================

Installing dependencies...
==========================================
Starting SERVER in background...
==========================================
Waiting for server to initialize (5 seconds)...
✓ Server started successfully (PID: 12345)
  Access at: http://localhost:5000

==========================================
Starting SCANNER CLIENT...
==========================================
Configuration: ../configs/node1_config.yml

This Pi is now both:
  1. Running the server (http://localhost:5000)
  2. Scanning as a client node

Press Ctrl+C to stop both services
==========================================
```

### Step 4: Configure Other Nodes

On your other Raspberry Pis (node 2, node 3, etc.), configure them to point to this Pi's IP:

```bash
# On Raspberry Pi #2
nano configs/node2_config.yml
```

Update server_url to point to the first Pi:

```yaml
server_url: "http://192.168.1.100:5000"  # IP of Pi running server
```

Then start the client:

```bash
sudo ./start_node2.sh
```

## Accessing the System

### On the Server Pi

- **Web Interface**: `http://localhost:5000`
- **View Logs**: `tail -f server.log` (in the project root)

### From Other Devices

- **Web Interface**: `http://192.168.1.100:5000` (use the Pi's actual IP)

To find the Pi's IP:
```bash
hostname -I
```

## Managing the Services

### Check if Services are Running

```bash
# Check server
ps aux | grep "python3 app.py"

# Check scanner
ps aux | grep "python3 scanner.py"
```

### View Logs

```bash
# Server logs
tail -f server.log

# Scanner logs (shown in terminal)
# Just look at the terminal where you started the combined script
```

### Stop Both Services

Press `Ctrl+C` in the terminal where you started the combined script.

This will gracefully stop both the server and scanner.

### Restart After Reboot

To run automatically after reboot, create a systemd service:

```bash
sudo nano /etc/systemd/system/triangulation.service
```

Add:

```ini
[Unit]
Description=Triangulation Server and Scanner
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/pi/dendron/scripts
ExecStart=/home/pi/dendron/scripts/start_server_and_node.sh /home/pi/dendron/configs/node1_config.yml
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable triangulation.service
sudo systemctl start triangulation.service

# Check status
sudo systemctl status triangulation.service
```

## Advantages

✅ **Resource Efficient**: One Pi does double duty
✅ **Lower Latency**: Server and client communicate via localhost
✅ **Simplified Setup**: One device to manage for server functionality
✅ **Cost Effective**: Need fewer Raspberry Pis

## Considerations

⚠️ **Performance**: Server uses CPU/RAM, may slightly impact scanning
⚠️ **Single Point of Failure**: If this Pi fails, server goes down
⚠️ **Network Access**: Other devices need network access to this Pi

## Recommended Setup

For **2 Raspberry Pis total**:
- **Pi 1**: Server + Scanner (this guide)
- **Pi 2**: Scanner only

For **3 Raspberry Pis total** (optimal triangulation):
- **Pi 1**: Server + Scanner (this guide)
- **Pi 2**: Scanner only
- **Pi 3**: Scanner only

For **4+ Raspberry Pis**:
- **Pi 1**: Server + Scanner (this guide)
- **Pi 2-N**: Scanners only

## Troubleshooting

### Server Won't Start

Check server.log:
```bash
cat server.log
```

Common issues:
- Port 5000 already in use: `sudo lsof -i :5000`
- Dependencies not installed: Run `sudo ./setup_server.sh` again

### Scanner Can't Connect to Server

Check the node config file has correct server URL:
```bash
grep server_url configs/node1_config.yml
```

Should show: `server_url: "http://localhost:5000"`

### WiFi Scanning Not Working

Make sure you're running with sudo:
```bash
sudo ./start_server_and_node.sh ../configs/node1_config.yml
```

Check WiFi interface:
```bash
iwconfig  # Should show wlan0 or similar
```

## Performance Tips

1. **Use a Raspberry Pi 4** or newer for best performance when running both roles
2. **Increase swap space** if experiencing memory issues:
   ```bash
   sudo dphys-swapfile swapoff
   sudo nano /etc/dphys-swapfile  # Set CONF_SWAPSIZE=2048
   sudo dphys-swapfile setup
   sudo dphys-swapfile swapon
   ```
3. **Use a quality SD card** (UHS-I or better) for the Pi running the server
4. **Monitor resources**: `htop` to check CPU/RAM usage

## Alternative: Separate Processes

If you prefer to manage server and scanner separately (not recommended):

**Terminal 1:**
```bash
./start_server.sh
```

**Terminal 2:**
```bash
sudo ./start_node1.sh
```

This gives you more control but requires managing two terminal sessions.

---

**You're all set!** Your Raspberry Pi is now both the server and a scanning node. 🎉
