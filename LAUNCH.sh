#!/bin/bash
# Quick Launch Script - Run this after container build completes

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║              ORANOLIO RAT - QUICK LAUNCH                      ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "[!] Python not found. The dev container is still building."
    echo "[!] Please wait for the build to complete and try again."
    echo ""
    echo "You can check the build status in the terminal."
    exit 1
fi

echo "[✓] Python found: $(python3 --version)"
echo ""

# Check if setup has been run
if [ ! -f "data/main.db" ]; then
    echo "[*] First time setup required..."
    echo "[*] Running complete setup..."
    echo ""
    bash complete_setup.sh
    if [ $? -ne 0 ]; then
        echo "[✗] Setup failed. Please check the errors above."
        exit 1
    fi
    echo ""
fi

# Start the application
echo "[*] Starting Oranolio RAT..."
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                  APPLICATION STARTING                         ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Access the web interface at: http://localhost:5000"
echo "Default admin email: admin@oranolio.local"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 production_start.py
