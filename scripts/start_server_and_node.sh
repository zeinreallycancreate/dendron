#!/bin/bash
# Start both Server and Scanner Client on the same Raspberry Pi
# This allows one Pi to act as both the coordinator and a scanning node

echo "=========================================="
echo "Starting Server + Scanner Node on Same Pi"
echo "=========================================="
echo ""

# Check which node config to use
NODE_CONFIG="${1:-../configs/node1_config.yml}"

if [ ! -f "$NODE_CONFIG" ]; then
    echo "Error: Configuration file not found: $NODE_CONFIG"
    echo "Usage: $0 [path_to_node_config.yml]"
    echo "Example: $0 ../configs/node1_config.yml"
    exit 1
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script needs sudo privileges for WiFi/Bluetooth scanning"
    echo "Restarting with sudo..."
    sudo -E env PATH=$PATH $0 "$NODE_CONFIG"
    exit $?
fi

# Get the real user (before sudo)
REAL_USER=${SUDO_USER:-$USER}
REAL_HOME=$(eval echo ~$REAL_USER)

cd "$(dirname "$0")/.."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    sudo -u $REAL_USER python3 -m venv venv
fi

# Install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install -q -r requirements.txt

echo ""
echo "=========================================="
echo "Starting SERVER in background..."
echo "=========================================="

# Start server in background
cd server
python3 app.py > ../server.log 2>&1 &
SERVER_PID=$!
cd ..

# Wait for server to start
echo "Waiting for server to initialize (5 seconds)..."
sleep 5

# Check if server is running
if ps -p $SERVER_PID > /dev/null; then
    echo "✓ Server started successfully (PID: $SERVER_PID)"
    echo "  Access at: http://localhost:5000"
else
    echo "✗ Server failed to start. Check server.log"
    exit 1
fi

echo ""
echo "=========================================="
echo "Starting SCANNER CLIENT..."
echo "=========================================="
echo "Configuration: $NODE_CONFIG"
echo ""
echo "This Pi is now both:"
echo "  1. Running the server (http://localhost:5000)"
echo "  2. Scanning as a client node"
echo ""
echo "Press Ctrl+C to stop both services"
echo "=========================================="
echo ""

# Trap Ctrl+C to kill both processes
trap "echo ''; echo 'Stopping server and scanner...'; kill $SERVER_PID 2>/dev/null; exit" INT TERM

# Start scanner in foreground (so Ctrl+C works)
cd client
python3 scanner.py "$NODE_CONFIG"

# If scanner exits, kill server
kill $SERVER_PID 2>/dev/null
