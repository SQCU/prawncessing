#!/bin/bash

# Orchestration script to start visualizer-related services.
# This script first kills existing processes on the relevant ports,
# then starts the services in the background using nohup.
#
# To run: `./start_visualizer_services.sh`
# To stop: Use the generic `./kill_ports.sh 5007 8003 5008 5010` or other specific `interrupt_*.sh` scripts.
# This script is designed to be used with the corresponding kill scripts for proper shutdown.

# Define ports for visualizer and mock video stream
MOCK_VIDEO_PORT=8003
PROXY_PORT=5008
ECHO_PORT=5010

# Kill any existing processes on these ports
echo "Stopping existing visualizer and mock video stream services..."
./kill_ports.sh $MOCK_VIDEO_PORT $PROXY_PORT $ECHO_PORT

# Start the video stream mock server
echo "Starting video stream mock server on port $MOCK_VIDEO_PORT..."
nohup uv run python /home/bigboi/prawncessing/videostream_mock_server.py > videostream_mock_server.log 2>&1 &

# Start the proxy server
echo "Starting proxy server on port $PROXY_PORT..."
nohup uv run python /home/bigboi/prawncessing/proxy_server.py > proxy_server.log 2>&1 &

# Start the echo server
echo "Starting echo server on port $ECHO_PORT..."
nohup uv run python /home/bigboi/prawncessing/CORS-debug-mesh/echo_service.py > echo_service.log 2>&1 &


echo "Visualizer services started in the background."

