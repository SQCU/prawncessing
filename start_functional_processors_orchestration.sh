#!/bin/bash

# Orchestration script to start functional processor services.
# This script first kills existing processes on the relevant ports using `kill_ports.sh`,
# which is the recommended way to terminate these services.
# then starts the services in the background using nohup.

# Define ports for functional processor services
IMAGE_INPUT_PORT=5001
DCT_PORT=5002
REFERENCE_FRAME_PORT=5003
DIFFERENCE_PORT=5004
ACCUMULATOR_PORT=5005
ORCHESTRATION_PORT=5006

# Kill any existing processes on these ports
echo "Stopping existing functional processor services..."
./kill_ports.sh $IMAGE_INPUT_PORT $DCT_PORT $REFERENCE_FRAME_PORT $DIFFERENCE_PORT $ACCUMULATOR_PORT $ORCHESTRATION_PORT

# Start the functional processor services
echo "Starting Image Input Service on port $IMAGE_INPUT_PORT..."
nohup python3 /home/bigboi/prawncessing/functional_processor/image_input_service.py > functional_processor/image_input_service.log 2>&1 &

echo "Starting DCT Service on port $DCT_PORT..."
nohup python3 /home/bigboi/prawncessing/functional_processor/dct_service.py > functional_processor/dct_service.log 2>&1 &

echo "Starting Reference Frame Service on port $REFERENCE_FRAME_PORT..."
nohup python3 /home/bigboi/prawncessing/functional_processor/reference_frame_service.py > functional_processor/reference_frame_service.log 2>&1 &

echo "Starting Difference Service on port $DIFFERENCE_PORT..."
nohup python3 /home/bigboi/prawncessing/functional_processor/difference_service.py > functional_processor/difference_service.log 2>&1 &

echo "Starting Accumulator Service on port $ACCUMULATOR_PORT..."
nohup python3 /home/bigboi/prawncessing/functional_processor/accumulator_service.py > functional_processor/accumulator_service.log 2>&1 &

echo "Starting Orchestration Service on port $ORCHESTRATION_PORT..."
nohup python3 /home/bigboi/prawncessing/functional_processor/orchestration_service.py > functional_processor/orchestration_service.log 2>&1 &

echo "Functional processor services started in the background."
