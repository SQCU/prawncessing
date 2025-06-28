#!/bin/bash

# Make kill_ports.sh executable
chmod +x kill_ports.sh

# Run the kill script to clear any running services
./kill_ports.sh 8000 8080 5002 5003 5004 5005 5006

# Activate the virtual environment
source ../.venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Start the services in the background
echo "Starting services..."
nohup uv run python dct_service.py > logs/dct_service.log 2>&1 &
nohup uv run python reference_frame_service.py > logs/reference_frame_service.log 2>&1 &
nohup uv run python difference_service.py > logs/difference_service.log 2>&1 &
nohup uv run python accumulator_service.py > logs/accumulator_service.log 2>&1 &
nohup uv run python orchestration_service.py > logs/orchestration_service.log 2>&1 &
nohup uv run python proxy_server.py > logs/proxy_server.log 2>&1 &
# I will create this visualizer service next
nohup uv run python visualizer_service.py > logs/visualizer_service.log 2>&1 &


echo "Services started."
