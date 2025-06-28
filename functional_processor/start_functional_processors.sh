#!/bin/bash

# This script starts all individual functional processor services in the background.
# It first calls the interrupt script to ensure a clean slate, preventing hung processes.
#
# To run: `./start_functional_processors.sh`
# To stop: Use the `interrupt_functional_processors.sh` script.

# Navigate to the script's directory
cd "$(dirname "$0")"

echo "Interrupting any existing services to ensure a clean start..."
./interrupt_functional_processors.sh
echo "Services interrupted."

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