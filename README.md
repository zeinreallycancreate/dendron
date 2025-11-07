# dendron

WiFi/Bluetooth Device Triangulation System for Raspberry Pi

## Overview

A FIND3-inspired triangulation system that tracks WiFi and Bluetooth devices using 3 Raspberry Pi nodes running Ubuntu 24.04.3. Features real-time tracking, AI-powered location prediction, and a live web interface.

## Quick Start

### Hardware Needed
- 3x Raspberry Pi (running Ubuntu 24.04.3)
- 1x Server (any computer on your network)

### Installation

**On Server:**
```bash
git clone https://github.com/zeinreallycancreate/dendron.git
cd dendron/scripts
chmod +x start_server.sh
./start_server.sh
```

**On Each Raspberry Pi (Ubuntu 24.04.3):**
```bash
git clone https://github.com/zeinreallycancreate/dendron.git
cd dendron/scripts
chmod +x setup_ubuntu.sh
sudo ./setup_ubuntu.sh  # Install dependencies
nano ../configs/node1_config.yml  # Update server_url
chmod +x start_node1.sh
./start_node1.sh
```

Repeat for node2 and node3 on the other Raspberry Pis.

### Access
Open `http://YOUR_SERVER_IP:5000` in a browser to view the live tracking map.

## Features

- ✅ Works with ALL WiFi devices (no extra hardware needed)
- ✅ Bluetooth and BLE device detection
- ✅ FIND3-inspired fingerprinting technology
- ✅ AI-powered triangulation (trilateration + ML + Bayesian)
- ✅ Real-time web interface with live map
- ✅ Easy setup with automated scripts
- ✅ Ubuntu 24.04.3 compatible

## Documentation

See [SETUP.md](SETUP.md) for complete setup instructions, configuration options, and troubleshooting.

## Architecture

- **Server**: Python Flask app with WebSocket, SQLite database, ML models
- **Clients**: 3 Raspberry Pi nodes scanning WiFi/Bluetooth devices
- **Web UI**: Real-time map visualization with device tracking

## Technology

- FIND3-inspired RSSI fingerprinting
- Multiple triangulation algorithms
- scikit-learn for machine learning
- Real-time updates via WebSocket
- Works with standard Raspberry Pi WiFi (no extra antennas)

## License

Open source - use and modify freely.