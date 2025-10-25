#!/bin/bash
# Build script for Oranolio RAT on Render

echo "Building Oranolio RAT C2 Framework..."

# Install Python dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Create necessary directories
mkdir -p data logs uploads downloads

# Set up environment
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "Build completed successfully!"