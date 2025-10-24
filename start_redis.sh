#!/bin/bash
# Start Redis server for session management

echo "[*] Starting Redis server..."

# Check if Redis is installed
if ! command -v redis-server &> /dev/null; then
    echo "[!] Redis not installed, application will use memory backend"
    exit 0
fi

# Create Redis directory
mkdir -p /tmp/redis

# Start Redis in background
redis-server --daemonize yes \
    --port 6379 \
    --bind 127.0.0.1 \
    --dir /tmp/redis \
    --save 900 1 \
    --save 300 10 \
    --save 60 10000 \
    --maxmemory 256mb \
    --maxmemory-policy allkeys-lru \
    --appendonly yes \
    --appendfsync everysec \
    --loglevel notice \
    --logfile /tmp/redis/redis.log

# Check if Redis started successfully
sleep 1
if redis-cli ping > /dev/null 2>&1; then
    echo "[✓] Redis server started successfully"
    exit 0
else
    echo "[!] Redis failed to start, application will use memory backend"
    exit 0
fi
