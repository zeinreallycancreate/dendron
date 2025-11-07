# WiFi/Bluetooth Device Triangulation System

A FIND3-inspired triangulation system for tracking WiFi and Bluetooth devices using 3 Raspberry Pi nodes in a triangle formation. The system uses advanced fingerprinting technology, machine learning, and AI-powered location prediction.

## 🎯 Features

- **Universal WiFi Detection**: Works with ALL WiFi devices without requiring extra antennas
- **Bluetooth Support**: Detects and tracks Bluetooth and BLE devices
- **FIND3-Inspired Technology**: Uses proven fingerprinting algorithms for accuracy
- **Multiple Triangulation Methods**:
  - Trilateration (geometric)
  - Weighted centroid
  - Bayesian inference with historical data
- **Real-time Web Interface**: Live map showing device positions
- **AI-Powered Processing**: Machine learning for improved location accuracy
- **Easy Setup**: Simple scripts to run 1 server and 3 clients

## 📋 Hardware Requirements

### You Need:
- **3 Raspberry Pi** running **Ubuntu 25.10 ARM 64-bit** (Pi 3, 4, or 5 recommended)
- **1 Server** (can be another Raspberry Pi, or a regular computer on the same network)
- Power supplies for all Raspberry Pis
- Network connectivity (WiFi or Ethernet)

### NO Additional Hardware Needed:
- ❌ No extra WiFi antennas
- ❌ No special WiFi adapters
- ❌ No additional sensors
- ✅ Uses standard Raspberry Pi WiFi and Bluetooth

## 🚀 Quick Start

### Step 1: Setup the Server

The server can run on any computer (Raspberry Pi, Linux, Mac, or Windows).

1. **Clone this repository on your server machine**:
   ```bash
   git clone https://github.com/zeinreallycancreate/dendron.git
   cd dendron
   ```

2. **Find your server's IP address**:
   ```bash
   hostname -I
   # Example output: 192.168.1.100
   ```

3. **Start the server**:
   ```bash
   cd scripts
   chmod +x start_server.sh
   ./start_server.sh
   ```

4. **Access the web interface**:
   - Open browser: `http://YOUR_SERVER_IP:5000`
   - Example: `http://192.168.1.100:5000`

### Step 2: Setup Node 1 (Bottom-Left)

On your **first Raspberry Pi**:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/zeinreallycancreate/dendron.git
   cd dendron
   ```

2. **Edit the configuration**:
   ```bash
   nano configs/node1_config.yml
   ```
   
   Update the `server_url` with your actual server IP:
   ```yaml
   server_url: "http://192.168.1.100:5000"  # Replace with your server IP
   ```

3. **Install system dependencies** (Ubuntu 25.10 ARM64):
   ```bash
   sudo apt update
   sudo apt install -y python3-pip python3-venv python3-full \
       wireless-tools aircrack-ng iw net-tools \
       bluetooth bluez bluez-tools \
       libpcap-dev libglib2.0-dev libbluetooth-dev
   ```

4. **Start Node 1**:
   ```bash
   cd scripts
   chmod +x start_node1.sh
   ./start_node1.sh
   ```

### Step 3: Setup Node 2 (Bottom-Right)

On your **second Raspberry Pi**:

1. Follow the same steps as Node 1, but use:
   ```bash
   nano configs/node2_config.yml
   ```
   
   And start with:
   ```bash
   ./start_node2.sh
   ```

### Step 4: Setup Node 3 (Top-Center)

On your **third Raspberry Pi**:

1. Follow the same steps as Node 1, but use:
   ```bash
   nano configs/node3_config.yml
   ```
   
   And start with:
   ```bash
   ./start_node3.sh
   ```

## 📐 Node Positioning

**IMPORTANT**: Position your 3 Raspberry Pis in a triangle formation for best triangulation accuracy.

### Default Triangle Configuration (50m x 43.3m area):

```
         Node 3 (25, 43.3)
              *
             / \
            /   \
           /     \
          /       \
         /         \
        /           \
       *-------------*
   Node 1          Node 2
   (0, 0)         (50, 0)
```

### Adjusting for Your Space:

1. Measure your room/area dimensions
2. Place the 3 Raspberry Pis in the corners of a triangle
3. Update the `position` values in each config file:

Example for a smaller 10m x 8.7m room:
```yaml
# node1_config.yml
position:
  x: 0
  y: 0
  z: 1.5

# node2_config.yml
position:
  x: 10     # 10 meters to the right
  y: 0
  z: 1.5

# node3_config.yml
position:
  x: 5      # Center between node 1 and 2
  y: 8.7    # Height to form triangle
  z: 1.5
```

## 🖥️ How to Run

### Running the Server:
```bash
cd dendron/scripts
./start_server.sh
```

The server will:
- Start on `http://0.0.0.0:5000`
- Process data from all 3 nodes
- Run AI algorithms for location prediction
- Serve the live web interface

### Running Each Client Node:
```bash
# On Raspberry Pi #1
cd dendron/scripts
./start_node1.sh

# On Raspberry Pi #2
cd dendron/scripts
./start_node2.sh

# On Raspberry Pi #3
cd dendron/scripts
./start_node3.sh
```

Each client will:
- Scan for WiFi devices every 5 seconds
- Scan for Bluetooth devices every 5 seconds
- Send RSSI (signal strength) data to the server
- Automatically reconnect if connection is lost

## 🌐 Web Interface

Access the web interface at `http://YOUR_SERVER_IP:5000`

The interface shows:
- **Live Map**: Real-time visualization of detected devices
- **Device List**: All tracked devices with signal confidence
- **Node Status**: Status of all 3 scanner nodes
- **Statistics**: Number of active devices and nodes

### Device Colors:
- 🟢 **Green**: WiFi devices
- 🔵 **Blue**: Bluetooth devices
- 🟠 **Orange**: Scanner nodes (your Raspberry Pis)

## 🧠 How It Works (FIND3-Inspired)

### 1. **Fingerprinting Technology**
Each node continuously scans for WiFi and Bluetooth devices, measuring RSSI (Received Signal Strength Indicator).

### 2. **Multiple Location Methods**
The server combines three approaches for maximum accuracy:

**A. Trilateration**: 
- Uses distance calculations from RSSI values
- Geometric triangulation with all 3 nodes
- Most accurate with strong signals

**B. Weighted Centroid**:
- Weights node positions by signal strength
- Fallback when trilateration fails
- Fast and reliable

**C. Bayesian Inference**:
- Uses historical location data
- Predicts future positions
- Improves accuracy over time

### 3. **AI Processing**
- Machine learning models process signal patterns
- Adapts to environmental changes
- Filters out noise and outliers

## 📝 Configuration Options

### Client Configuration (`configs/nodeX_config.yml`):

```yaml
node_id: "node_1"                    # Unique identifier for this node

position:                             # Physical position in meters
  x: 0                               # Horizontal position
  y: 0                               # Vertical position
  z: 1.5                             # Height above ground

server_url: "http://192.168.1.100:5000"  # Server address

wifi_interface: "wlan0"              # WiFi interface name

scan_interval: 5                     # Seconds between scans

anonymize_mac: false                 # Hash MAC addresses for privacy
```

## 🔧 Troubleshooting

### Issue: "Permission denied" when starting client
**Solution**: The scripts need sudo for WiFi/Bluetooth access:
```bash
sudo ./start_node1.sh
```

### Issue: "Monitor mode failed"
**Solution**: The system will automatically fall back to managed mode scanning. This still works!

### Issue: No devices detected
**Checks**:
1. Ensure all 3 nodes are running
2. Check nodes can reach the server
3. Verify WiFi devices are nearby and active
4. Check Bluetooth is enabled on devices

### Issue: Inaccurate positions
**Solutions**:
1. Verify node positions in config files match physical positions
2. Ensure nodes are spread out (not too close together)
3. Let system run for a few minutes to build history
4. Reduce obstacles between nodes and devices

## 🎛️ Advanced Features

### Enable MAC Address Anonymization:
```yaml
anonymize_mac: true
```

### Adjust Scan Frequency:
```yaml
scan_interval: 3  # Faster scanning (more CPU)
# or
scan_interval: 10  # Slower scanning (less CPU)
```

### Custom Map Area:
Edit `web/templates/index.html`:
```javascript
const MAP_WIDTH = 100;  // Your area width in meters
const MAP_HEIGHT = 100; // Your area height in meters
```

## 📊 API Endpoints

The server provides REST API endpoints:

- `GET /api/devices` - Get all tracked devices
- `GET /api/nodes` - Get all scanner nodes
- `POST /api/scan` - Submit scan data (used by clients)

WebSocket endpoint for real-time updates:
- `ws://SERVER_IP:5000/socket.io/`

## 🔐 Security Notes

- System designed for local network use
- MAC addresses can be anonymized
- No data leaves your local network
- All processing happens on your server

## 📦 Dependencies

Automatically installed by the startup scripts:
- **Python 3.7+**
- Flask, Flask-SocketIO (web server)
- scikit-learn, numpy, scipy (machine learning)
- scapy (WiFi packet sniffing)
- bluepy (Bluetooth scanning)
- SQLAlchemy (database)

System packages (install manually on Raspberry Pi with Ubuntu 25.10 ARM64):
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv python3-full \
    wireless-tools aircrack-ng iw net-tools \
    bluetooth bluez bluez-tools \
    libpcap-dev libglib2.0-dev libbluetooth-dev
```

## 🤝 Contributing

Contributions welcome! This project uses FIND3's proven concepts as inspiration.

## 📄 License

Open source - feel free to use and modify for your needs.

## 🙏 Credits

- Inspired by [FIND3](https://www.internalpositioning.com/) fingerprinting technology
- Built for Raspberry Pi enthusiasts
- Designed for easy setup and accurate tracking

## 💡 Tips for Best Results

1. **Placement**: Position nodes at equal distances for an equilateral triangle
2. **Height**: Mount Pis at consistent heights (1-2 meters high)
3. **Obstacles**: Minimize walls/metal between nodes and target area
4. **Power**: Use good quality power supplies to avoid WiFi interference
5. **Network**: Connect server via Ethernet if possible
6. **Time**: Let system run 10-15 minutes to build accurate models

## 📞 Support

Having issues? Check:
1. All nodes are connected to the server
2. Config files have correct server IP
3. Nodes are positioned correctly
4. System dependencies are installed

---

**Enjoy tracking! 🎉**
