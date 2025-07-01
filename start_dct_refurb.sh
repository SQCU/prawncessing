#!/bin/bash

# This script automates the process of stopping, updating, and restarting the dct_refurb service.

# Step 1: Kill any existing services
echo "--- Stopping any existing dct_refurb services... ---"
# Use pkill to find and kill the process running the main script.
pkill -f "dct_refurb/main.py"
# Add a small delay to allow processes to terminate gracefully.
sleep 2

# Step 2: Install/update dependencies
echo "--- Installing/updating dependencies... ---"
# Activate the virtual environment
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment. Aborting."
    exit 1
fi
# Install dependencies using uv
uv pip install -r dct_refurb/requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies. Aborting."
    exit 1
fi

# Step 3: Start the service in the background
echo "--- Starting the dct_refurb service in the background... ---"
# Clear the old log file before starting
> dct_refurb/service.log
# Run the main script with nohup to detach it from the terminal
# and redirect all output to the log file.
nohup python -u dct_refurb/main.py >> dct_refurb/service.log 2>&1 &
# Add a small delay to allow the services to initialize.
sleep 3

# Step 4: Inform the user
echo "--- Service started successfully! ---"
echo
echo "The web interface should be available at:"
echo "  => http://127.0.0.1:8000"
echo
echo "You can monitor the service logs with the command:"
echo "  tail -f dct_refurb/service.log"
echo
