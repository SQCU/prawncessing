#!/bin/bash

# Make kill_ports.sh executable
chmod +x kill_ports.sh

# Run the kill script to clear any running services
./kill_ports.sh 5000 5001 5010

# Install dependencies
uv pip install -r requirements.txt

# Start the services in the background
echo "Starting services..."
uv run python echo_service.py &
uv run python videostream_service.py &
uv run python proxy_server.py &

echo "Services started."