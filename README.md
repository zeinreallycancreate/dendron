# dendron

WiFi/Bluetooth Device Triangulation System for Raspberry Pi

## Overview

A FIND3-inspired triangulation system that tracks WiFi and Bluetooth devices using **1 to N** Raspberry Pi nodes running Ubuntu 25.10 ARM 64-bit. Features real-time tracking, AI-powered location prediction with automatic geometry adaptation, and a live web interface.

**Works with any number of nodes!** System automatically detects node configuration and adapts triangulation math accordingly.

## Quick Start

### Hardware Needed
- **1+ Raspberry Pi** (running Ubuntu 25.10 ARM 64-bit) - Use as many as you want!
- **1x Server** (any computer on your network)

**Note**: More nodes = better accuracy. Recommended: 3+ for optimal triangulation.

### Installation

**On Server:**
```bash
git clone https://github.com/zeinreallycancreate/dendron.git
cd dendron/scripts
chmod +x setup_server.sh
sudo ./setup_server.sh  # Install server dependencies
chmod +x start_server.sh
./start_server.sh
```

**On Each Raspberry Pi (Ubuntu 25.10 ARM64):**
```bash
git clone https://github.com/zeinreallycancreate/dendron.git
cd dendron/scripts
chmod +x setup_ubuntu.sh
sudo ./setup_ubuntu.sh  # Install dependencies
nano ../configs/node1_config.yml  # Update server_url
chmod +x start_node1.sh
./start_node1.sh
```

Repeat for each additional node (node2, node3, node4, etc.).

### Access
Open `http://YOUR_SERVER_IP:5000` in a browser to view the live tracking map.

## Features

- ✅ **Flexible node count** - Works with 1, 2, 3, 4, or more nodes
- ✅ **Auto-geometry detection** - Automatically maps node configuration
- ✅ **Adaptive triangulation** - Math adjusts to your setup
- ✅ Works with ALL WiFi devices (no extra hardware needed)
- ✅ Bluetooth and BLE device detection
- ✅ FIND3-inspired fingerprinting technology
- ✅ AI-powered positioning (multiple algorithms)
- ✅ Real-time web interface with live map
- ✅ Easy setup with automated scripts
- ✅ Ubuntu 25.10 ARM64 compatible

## Documentation

See [SETUP.md](SETUP.md) for complete setup instructions, configuration options, and troubleshooting.

## Architecture

- **Server**: Python Flask app with WebSocket, SQLite database, ML models, auto-geometry detection
- **Clients**: 1+ Raspberry Pi nodes scanning WiFi/Bluetooth devices
- **Web UI**: Real-time map visualization with device tracking

## Technology

- FIND3-inspired RSSI fingerprinting
- Adaptive multi-node positioning algorithms
- Auto-detection of node geometry (single, line, triangle, polygon)
- scikit-learn for machine learning
- Real-time updates via WebSocket
- Works with standard Raspberry Pi WiFi (no extra antennas)

## License

Open source - use and modify freely.