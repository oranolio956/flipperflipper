#!/bin/bash
# Stitch Elite RAT System - Replit Startup Script

echo "🚀 Starting Stitch Elite RAT System on Replit..."
echo "================================================"

# Set environment variables
export STITCH_DEBUG=true
export STITCH_REDIS_URL=memory://
export FLASK_ENV=development
export FLASK_DEBUG=true

# Run the main application
python3 main.py