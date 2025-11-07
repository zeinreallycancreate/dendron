#!/bin/bash
# Start the Triangulation Server
# Run this on your server machine (can be a Raspberry Pi or regular computer)

echo "======================================"
echo "Starting Triangulation Server"
echo "======================================"

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

# Start the server
echo ""
echo "======================================"
echo "Server starting on http://0.0.0.0:5000"
echo "Access the web interface at:"
echo "  http://localhost:5000"
echo "  http://YOUR_IP:5000"
echo "======================================"
echo ""

cd server
python3 app.py
