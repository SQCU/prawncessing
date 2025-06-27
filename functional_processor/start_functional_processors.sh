#!/bin/bash

# This script starts all individual functional processor services in the background
# using nohup. This ensures they continue to run even if the terminal session is closed.
# Their output will be redirected to nohup.out in their respective directories.
#
# To run: `./start_functional_processors.sh`
# To stop: Use the generic `../kill_ports.sh 5002 5003 5004 5005 5006` or `../interrupt_functional_processors.sh`.
# This script is designed to be used with the corresponding kill scripts for proper shutdown.
#
# Usage: ./start_functional_processors.sh

# Navigate to the functional_processor directory
cd "$(dirname "$0")"

echo "Starting DCT Service (port 5002)..."
nohup uv run python dct_service.py > logs/dct_service.log 2>&1 &

echo "Starting Reference Frame Service (port 5003)..."
nohup uv run python reference_frame_service.py > logs/reference_frame_service.log 2>&1 &

echo "Starting Difference Service (port 5004)..."
nohup uv run python difference_service.py > logs/difference_service.log 2>&1 &

echo "Starting Accumulator Service (port 5005)..."
nohup uv run python accumulator_service.py > logs/accumulator_service.log 2>&1 &

echo "Starting Orchestration Service (port 5006)..."
nohup uv run python orchestration_service.py > logs/orchestration_service.log 2>&1 &

echo "All functional processor services have been launched in the background."
echo "Check their respective .log files in the 'logs/' directory for output."