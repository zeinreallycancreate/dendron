#!/bin/bash
# Setup script for Triangulation Server
# Run this on your server machine (can be a Raspberry Pi or regular computer)

# Check if we're being run from the correct location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -f "$SCRIPT_DIR/setup_server.sh" ]]; then
    echo "❌ ERROR: Script not found in expected location"
    echo ""
    echo "Make sure you're running this from the scripts/ directory:"
    echo "  cd ~/dendron/scripts"
    echo "  sudo ./setup_server.sh"
    echo ""
    echo "Or from the project root:"
    echo "  cd ~/dendron"
    echo "  sudo ./scripts/setup_server.sh"
    echo ""
    echo "See TROUBLESHOOTING.md for more help"
    exit 1
fi

echo "======================================"
echo "Server Setup for Triangulation System"
echo "======================================"
echo ""

# Ask if this is a dual-role setup
echo "Is this machine also running as a scanner node?"
echo "  1) Server only (no scanning)"
echo "  2) Server + Scanner (dual-role)"
echo ""
read -p "Choose setup type (1 or 2): " SERVER_TYPE
echo ""

IS_DUAL_ROLE=false
if [[ "$SERVER_TYPE" == "2" ]]; then
    IS_DUAL_ROLE=true
    echo "Selected: Server + Scanner (dual-role)"
    echo "Note: Also run setup_ubuntu.sh for client dependencies"
else
    echo "Selected: Server only"
fi

echo ""

# Check if running as root (not recommended for server)
if [ "$EUID" -eq 0 ]; then
    echo "Warning: Running as root. Consider running as a regular user."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "Detected OS: $ID $VERSION_ID"
    echo ""
fi

echo "Updating package lists..."
if command -v apt &> /dev/null; then
    sudo apt update
elif command -v yum &> /dev/null; then
    sudo yum update
elif command -v dnf &> /dev/null; then
    sudo dnf update
fi

echo ""
echo "Installing Python and build dependencies..."
if command -v apt &> /dev/null; then
    sudo apt install -y python3-pip python3-venv python3-full build-essential python3-dev
elif command -v yum &> /dev/null; then
    sudo yum install -y python3-pip python3-devel gcc
elif command -v dnf &> /dev/null; then
    sudo dnf install -y python3-pip python3-devel gcc
fi

echo ""
echo "Installing system dependencies..."
if command -v apt &> /dev/null; then
    sudo apt install -y libsqlite3-dev
fi

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "System Information:"
echo "  OS: $ID $VERSION_ID"
echo "  Python: $(python3 --version)"
echo ""

# Get server IP
if command -v hostname &> /dev/null; then
    SERVER_IP=$(hostname -I | awk '{print $1}')
    echo "Server IP Address: $SERVER_IP"
    echo ""
fi

if [[ "$IS_DUAL_ROLE" == "true" ]]; then
    echo "Next steps for DUAL-ROLE setup:"
    echo "1. Run client setup: sudo ./scripts/setup_ubuntu.sh"
    echo "   (Choose option 2: Server + Client)"
    echo "2. Start both: sudo ./scripts/start_server_and_node.sh configs/node1_config.yml"
    echo "3. Access web interface: http://localhost:5000"
else
    echo "Next steps for SERVER ONLY setup:"
    echo "1. Start the server: ./scripts/start_server.sh"
    echo "2. Access web interface: http://$SERVER_IP:5000"
    echo "3. Configure firewall if needed: sudo ufw allow 5000"
    echo "4. Configure client nodes to connect to: http://$SERVER_IP:5000"
fi

echo ""
