# Quick Start Guide

## 1-Minute Setup Overview

### What You're Building
A triangulation system with:
- **1 Server** (running the web interface and AI processing)
- **3 Raspberry Pi clients** (Ubuntu 25.10 ARM64) arranged in a triangle

### System Architecture

```
                    Internet/LAN
                         |
                    [SERVER]
                  (Port 5000)
              Web UI + AI Engine
                    /  |  \
                   /   |   \
                  /    |    \
        [Node 1]    [Node 2]   [Node 3]
       (Pi #1)      (Pi #2)     (Pi #3)
    WiFi Scanner  WiFi Scanner WiFi Scanner
    BT Scanner    BT Scanner    BT Scanner
         \           |            /
          \          |           /
           \         |          /
            \        |         /
          [Detected Devices Area]
        (WiFi phones, laptops, etc.)
```

## Step-by-Step Installation

### Server Setup (5 minutes)

**On your server computer:**

```bash
# 1. Clone the repo
git clone https://github.com/zeinreallycancreate/dendron.git
cd dendron

# 2. Start the server (it will auto-install dependencies)
cd scripts
chmod +x start_server.sh
./start_server.sh

# 3. Get your server IP
# The script will show it, or run:
hostname -I
# Example: 192.168.1.100
```

**Server is now running at `http://YOUR_IP:5000`**

---

### Raspberry Pi Setup (10 minutes per Pi)

**Do this on EACH of your 3 Raspberry Pis:**

#### Step 1: Initial Setup
```bash
# Clone the repo on the Raspberry Pi
git clone https://github.com/zeinreallycancreate/dendron.git
cd dendron

# Install dependencies
cd scripts
chmod +x setup_ubuntu.sh
sudo ./setup_ubuntu.sh

# Wait for installation to complete (~5 minutes)
```

#### Step 2: Configure Node Position

**For Raspberry Pi #1:**
```bash
cd dendron
nano configs/node1_config.yml
```

Update the `server_url`:
```yaml
server_url: "http://192.168.1.100:5000"  # <- Use YOUR server IP
```

Save and exit (Ctrl+X, Y, Enter)

**For Raspberry Pi #2:**
```bash
nano configs/node2_config.yml
```
Update server_url (same as above)

**For Raspberry Pi #3:**
```bash
nano configs/node3_config.yml
```
Update server_url (same as above)

#### Step 3: Start the Client

**On Raspberry Pi #1:**
```bash
cd scripts
./start_node1.sh
```

**On Raspberry Pi #2:**
```bash
cd scripts
./start_node2.sh
```

**On Raspberry Pi #3:**
```bash
cd scripts
./start_node3.sh
```

---

## Verify It's Working

1. **Open the web interface:** `http://YOUR_SERVER_IP:5000`

2. **Check the dashboard:**
   - You should see "3" under "Scanner Nodes"
   - Within 30 seconds, you should see WiFi/Bluetooth devices appearing

3. **Check node logs:**
   - Each Pi should show: "Starting WiFi scan..." and "Scanned X WiFi and Y Bluetooth devices"

---

## Physical Setup

### Place Your Raspberry Pis in a Triangle

```
     Your Room/Area
  ┌─────────────────────┐
  │                     │
  │      Node 3         │
  │        *            │
  │       / \           │
  │      /   \          │
  │     /     \         │
  │    /       \        │
  │   /         \       │
  │  *-----------*      │
  │Node 1     Node 2    │
  │                     │
  └─────────────────────┘
```

**Tips:**
- Place nodes 5-20 meters apart (adjust based on room size)
- Mount at consistent heights (~1.5m works well)
- Minimize walls between nodes
- Form as close to an equilateral triangle as possible

### Update Node Positions

Measure the actual positions of your Pis and update the config files:

```yaml
# Example for a 10m x 8.7m room

# node1_config.yml (bottom-left corner)
position:
  x: 0
  y: 0
  z: 1.5

# node2_config.yml (bottom-right corner)
position:
  x: 10
  y: 0
  z: 1.5

# node3_config.yml (top-center)
position:
  x: 5
  y: 8.7
  z: 1.5
```

**After updating, restart the clients.**

---

## Troubleshooting

### No devices showing up?
- Ensure all 3 nodes are running
- Check that devices are connecting: `./start_nodeX.sh` should show scan results
- Verify nodes can reach server: `ping YOUR_SERVER_IP`

### "Permission denied" errors?
- Clients need sudo: `sudo ./start_nodeX.sh`

### Server not accessible?
- Check firewall: `sudo ufw allow 5000`
- Verify server is running: `ps aux | grep python`

### Positions are inaccurate?
- Verify node positions in config match physical setup
- Let system run for 5-10 minutes to build history
- Ensure triangle is well-formed (not too narrow)

---

## What's Next?

### Advanced Configuration

Edit `configs/nodeX_config.yml`:

```yaml
# Scan more frequently
scan_interval: 3

# Enable MAC anonymization
anonymize_mac: true

# Use different WiFi interface
wifi_interface: "wlan1"
```

### Run as System Service

Create `/etc/systemd/system/dendron-node1.service`:

```ini
[Unit]
Description=Dendron Scanner Node 1
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/ubuntu/dendron/scripts
ExecStart=/home/ubuntu/dendron/scripts/start_node1.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable dendron-node1
sudo systemctl start dendron-node1
```

---

## Command Reference

### Server
```bash
./scripts/start_server.sh          # Start server
curl http://localhost:5000/api/devices  # Check API
```

### Clients
```bash
./scripts/start_node1.sh           # Start node 1
sudo ./scripts/start_node1.sh      # With sudo if needed
```

### System
```bash
hostname -I                        # Get IP address
ps aux | grep python               # Check running processes
sudo systemctl status bluetooth    # Check Bluetooth
iwconfig                          # Check WiFi
```

---

## Support

For issues, check:
1. [SETUP.md](SETUP.md) - Complete documentation
2. [README.md](README.md) - Project overview
3. Test your setup: `python3 -m unittest tests.test_basic -v`

---

**Happy Tracking! 🎯**
