#!/bin/bash
# Start Scanner Client Node 1
# Run this on Raspberry Pi #1

NODE_CONFIG="../configs/node1_config.yml"

echo "======================================"
echo "Starting Scanner Node 1"
echo "======================================"

# Check if config exists
if [ ! -f "$NODE_CONFIG" ]; then
    echo "Error: Configuration file not found: $NODE_CONFIG"
    echo "Please create the config file first"
    exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Check for root privileges (needed for WiFi/Bluetooth scanning)
if [ "$EUID" -ne 0 ]; then
    echo ""
    echo "WARNING: This script needs sudo privileges for WiFi/Bluetooth scanning"
    echo "Restarting with sudo..."
    echo ""
    sudo -E env PATH=$PATH $0
    exit $?
fi

# Start the client
echo ""
echo "======================================"
echo "Starting Node 1 Scanner"
echo "Configuration: $NODE_CONFIG"
echo "======================================"
echo ""

cd client
python3 scanner.py "$NODE_CONFIG"
