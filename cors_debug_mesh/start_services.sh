#!/bin/bash

# Make kill_ports.sh and log_filter.sh executable
chmod +x cors_debug_mesh/kill_ports.sh
chmod +x cors_debug_mesh/log_filter.sh

# Run the kill script to clear any running services
./cors_debug_mesh/kill_ports.sh 5000 5001 5010

# Install dependencies
uv pip install -r cors_debug_mesh/requirements.txt

# Start the services in the background, piping their output through the log filter
echo "Starting services with filtered logging..."
uv run python cors_debug_mesh/echo_service.py 2>&1 | ./cors_debug_mesh/log_filter.sh &
uv run python cors_debug_mesh/videostream_service.py 2>&1 | ./cors_debug_mesh/log_filter.sh &
uv run python cors_debug_mesh/proxy_server.py 2>&1 | ./cors_debug_mesh/log_filter.sh &

echo "Services started."