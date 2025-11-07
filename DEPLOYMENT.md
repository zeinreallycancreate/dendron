# Deployment Checklist

Use this checklist to deploy your WiFi/Bluetooth triangulation system.

## Pre-Deployment Checklist

### Hardware Setup
- [ ] 3 Raspberry Pi units (Ubuntu 25.10 ARM64) powered on
- [ ] 1 Server machine ready (can be another Pi or regular computer)
- [ ] All devices connected to same network
- [ ] Power supplies stable and reliable

### Network Configuration
- [ ] Server has static IP address (recommended)
- [ ] Note server IP address: `___________________`
- [ ] All Raspberry Pis can ping server
- [ ] Firewall allows port 5000 (if applicable)

### Physical Placement
- [ ] Raspberry Pis arranged in triangle formation
- [ ] Measured and recorded node positions:
  - Node 1: X=_____ Y=_____ Z=_____
  - Node 2: X=_____ Y=_____ Z=_____
  - Node 3: X=_____ Y=_____ Z=_____
- [ ] Nodes mounted at consistent heights
- [ ] Minimal obstacles between nodes

## Server Deployment

### Step 1: Server Setup
```bash
cd /path/to/server
git clone https://github.com/zeinreallycancreate/dendron.git
cd dendron
```

- [ ] Repository cloned
- [ ] `cd dendron` successful

### Step 2: Start Server
```bash
cd scripts
chmod +x start_server.sh
./start_server.sh
```

- [ ] Script executed without errors
- [ ] Server shows: "Server starting on http://0.0.0.0:5000"
- [ ] Server accessible at `http://YOUR_IP:5000`

### Step 3: Verify Server
```bash
# In another terminal
curl http://localhost:5000/api/nodes
curl http://localhost:5000/api/devices
```

- [ ] API endpoints respond with JSON
- [ ] Web interface loads in browser

## Client Deployment (Repeat for Each Raspberry Pi)

### Raspberry Pi #1

#### Setup
```bash
git clone https://github.com/zeinreallycancreate/dendron.git
cd dendron/scripts
sudo ./setup_ubuntu.sh
```

- [ ] Dependencies installed successfully
- [ ] No error messages

#### Configuration
```bash
cd ../configs
nano node1_config.yml
```

Update these fields:
- [ ] `server_url: "http://YOUR_SERVER_IP:5000"`
- [ ] `position: x, y, z` (actual measurements)

#### Start Client
```bash
cd ../scripts
./start_node1.sh
```

- [ ] Client shows: "Starting Node 1 Scanner"
- [ ] Scans begin: "Starting WiFi scan..."
- [ ] Data sent: "Successfully sent X scan results to server"

#### Verify
- [ ] Check server web UI shows Node 1 as ACTIVE
- [ ] Node 1 appears on the map at correct position

---

### Raspberry Pi #2

Repeat same steps as Pi #1, but:
- [ ] Use `node2_config.yml`
- [ ] Run `./start_node2.sh`
- [ ] Verify Node 2 appears on web UI

---

### Raspberry Pi #3

Repeat same steps as Pi #1, but:
- [ ] Use `node3_config.yml`
- [ ] Run `./start_node3.sh`
- [ ] Verify Node 3 appears on web UI

## Post-Deployment Verification

### System Health Check
- [ ] Web UI shows 3 active scanner nodes
- [ ] All 3 nodes show "ACTIVE" status in sidebar
- [ ] Nodes appear on map at correct positions
- [ ] Devices start appearing within 30-60 seconds

### Functional Tests
- [ ] Walk with a phone - position updates on map
- [ ] Multiple devices show up with different colors
- [ ] Device confidence bars display (green progress bars)
- [ ] Real-time updates occur (device positions change)

### Performance Tests
- [ ] Server CPU usage < 50%
- [ ] Client CPU usage < 30%
- [ ] No error messages in logs
- [ ] Updates occur every 5 seconds

## Troubleshooting

### No devices detected?
```bash
# On each Raspberry Pi, check scanning:
sudo iwlist wlan0 scan | grep -E "Cell|ESSID|Signal"

# Check Bluetooth:
sudo hcitool scan
```

- [ ] WiFi scan shows nearby networks
- [ ] Bluetooth scan shows devices
- [ ] If yes, check server connectivity

### Nodes offline?
```bash
# On Raspberry Pi:
ping YOUR_SERVER_IP

# Check if client is running:
ps aux | grep scanner.py
```

- [ ] Ping successful (< 50ms latency)
- [ ] Scanner process is running
- [ ] If not, restart with `./start_nodeX.sh`

### Inaccurate positions?
- [ ] Verify node positions in configs match physical setup
- [ ] Ensure triangle is well-formed (not too narrow)
- [ ] Let system run 10 minutes to build history
- [ ] Check for metal obstacles between nodes and devices

## Maintenance

### Daily
- [ ] Check all nodes are ACTIVE
- [ ] Verify device detection working
- [ ] Review for any error messages

### Weekly
- [ ] Clean database if needed: `rm server/triangulation.db`
- [ ] Restart server and clients
- [ ] Update repository: `git pull`

### Monthly
- [ ] Review node positions (if physical changes)
- [ ] Update system packages: `sudo apt update && sudo apt upgrade`
- [ ] Check disk space on server

## Running as System Service

To make the system start automatically on boot:

### Server Service
```bash
sudo nano /etc/systemd/system/dendron-server.service
```

```ini
[Unit]
Description=Dendron Triangulation Server
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/dendron/scripts
ExecStart=/path/to/dendron/scripts/start_server.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable dendron-server
sudo systemctl start dendron-server
```

- [ ] Service enabled
- [ ] Service started
- [ ] Service status shows "active (running)"

### Client Services
Create similar services for each node:
- [ ] `dendron-node1.service` on Pi #1
- [ ] `dendron-node2.service` on Pi #2
- [ ] `dendron-node3.service` on Pi #3

## Success Criteria

Your system is fully deployed when:
- ✅ Server web UI accessible
- ✅ 3 nodes showing as ACTIVE
- ✅ Devices being detected and tracked
- ✅ Positions updating in real-time
- ✅ No errors in any logs
- ✅ System runs for 24+ hours without issues

## Performance Benchmarks

Typical performance:
- **Device Detection**: 5-30 seconds for new device
- **Position Accuracy**: 2-5 meters (depends on environment)
- **Update Frequency**: 5 seconds per scan
- **Concurrent Devices**: 50+ devices tracked simultaneously
- **Server Resources**: < 500MB RAM, < 25% CPU

## Support

If issues persist after following this checklist:
1. Run tests: `python3 -m unittest tests.test_basic -v`
2. Check logs in each terminal window
3. Review SETUP.md and QUICKSTART.md
4. Verify Ubuntu 25.10 ARM64 compatibility

---

**Deployment Date**: _____________

**Deployed By**: _____________

**Notes**: 
_____________________________________________
_____________________________________________
_____________________________________________
