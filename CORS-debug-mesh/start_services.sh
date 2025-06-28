#!/bin/bash

# Make kill_ports.sh executable
chmod +x kill_ports.sh

# Run the kill script to clear any running services
./kill_ports.sh 5000 5001 5010

# Activate the virtual environment
source ../.venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the services in the background
echo "Starting services..."
python echo_service.py &
python videostream_service.py &
python proxy_server.py &

echo "Services started."