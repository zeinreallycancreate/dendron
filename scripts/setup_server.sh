#!/bin/bash
# Setup script for Triangulation Server
# Run this on your server machine (can be a Raspberry Pi or regular computer)

echo "======================================"
echo "Server Setup for Triangulation System"
echo "======================================"
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
echo "Next steps:"
echo "1. Start the server: ./scripts/start_server.sh"
echo "2. Access web interface: http://YOUR_IP:5000"
echo "3. Configure firewall if needed: sudo ufw allow 5000"
echo ""
