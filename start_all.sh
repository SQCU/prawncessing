#!/bin/bash

# This script starts all services required for the application,
# including the functional processors and the proxy server.
# It first calls an interrupt script to ensure a clean slate.

# Navigate to the script's directory to ensure relative paths work
cd "$(dirname "$0")"

echo "Starting all services..."

# Start the functional processors
./functional_processor/start_functional_processors.sh

# Start the proxy server
echo "Starting Proxy Server (port 5008)..."
nohup uv run python proxy_server.py > proxy_server.log 2>&1 &

echo "All services have been launched."
