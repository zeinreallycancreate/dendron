#!/bin/bash
# Setup script for Raspberry Pi running Ubuntu 25.10 ARM 64-bit
# This installs all system dependencies needed for the scanner nodes

echo "======================================"
echo "Ubuntu 25.10 ARM64 Setup for Scanner Node"
echo "======================================"
echo ""

# Check if running Ubuntu
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$ID" != "ubuntu" ]]; then
        echo "Warning: This script is designed for Ubuntu 25.10 ARM64"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check architecture
    ARCH=$(uname -m)
    if [[ "$ARCH" != "aarch64" ]] && [[ "$ARCH" != "arm64" ]]; then
        echo "Warning: This system appears to be $ARCH, not ARM64"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

# Check for sudo
if [ "$EUID" -ne 0 ]; then
    echo "This script needs to be run with sudo"
    echo "Please run: sudo ./setup_ubuntu.sh"
    exit 1
fi

echo "System: Ubuntu $VERSION_ID on $ARCH"
echo ""

echo "Updating package lists..."
apt update

echo ""
echo "Installing Python and build dependencies..."
apt install -y python3-pip python3-venv python3-full \
    build-essential python3-dev

echo ""
echo "Installing WiFi scanning tools..."
apt install -y wireless-tools aircrack-ng iw net-tools \
    wpasupplicant network-manager

echo ""
echo "Installing Bluetooth tools..."
apt install -y bluetooth bluez bluez-tools

echo ""
echo "Installing network libraries..."
apt install -y libpcap-dev libglib2.0-dev libbluetooth-dev

echo ""
echo "Configuring Bluetooth service..."
systemctl enable bluetooth
systemctl start bluetooth

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "System Information:"
echo "  OS: Ubuntu $VERSION_ID"
echo "  Architecture: $ARCH"
echo "  Python: $(python3 --version)"
echo ""
echo "Next steps:"
echo "1. Edit your node config file: configs/nodeX_config.yml"
echo "2. Update the server_url with your server's IP address"
echo "3. Run the client: ./scripts/start_nodeX.sh"
echo ""
echo "Note: You may need to reboot for all changes to take effect"
echo ""
